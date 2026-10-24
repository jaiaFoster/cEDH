import { test, expect } from "@playwright/test";
test.beforeEach(async ({ context, baseURL }) => {
  if (["localhost", "127.0.0.1"].includes(new URL(baseURL).hostname))
    await context.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.80" });
});
const ready = async (p) =>
  expect(p.locator("#point-table")).toHaveAttribute("aria-busy", "false");
async function fixture(page) {
  const a = await (
    await page.request.get("/api/points?points=all&limit=100")
  ).json();
  const b = await (
    await page.request.get("/api/points?points=all&limit=100&offset=100")
  ).json();
  const rows = [...a.cards, ...b.cards].map((c) => ({
    ...c,
    priceKnown: true,
  }));
  rows[0] = {
    ...rows[0],
    name: "A New Fixture Card",
    oracle_id: "00000000-0000-4000-8000-000000000008",
    main: null,
    command: null,
    priceKnown: false,
    legal: true,
  };
  await page.route("**/api/points?*", async (route) => {
    const p = new URL(route.request().url()).searchParams;
    if (p.get("source") !== "scryfall") return route.continue();
    const offset = Number(p.get("offset")),
      sort = p.get("sort");
    const ordered = [...rows].sort((x, y) =>
      sort.startsWith("mv")
        ? (x.mv - y.mv) * (sort.endsWith("desc") ? -1 : 1) ||
          x.name.localeCompare(y.name)
        : x.name.localeCompare(y.name) * (sort.endsWith("desc") ? -1 : 1),
    );
    return route.fulfill({
      json: {
        source: "scryfall",
        version: a.version,
        total: 200,
        offset,
        limit: 175,
        cards: ordered.slice(offset, offset + 175),
        warnings: [],
        has_more: offset === 0,
      },
    });
  });
}
test("optional live discovery, pending prices, native syntax, global pagination and local reset", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await fixture(page);
  await page.goto("/points");
  await ready(page);
  await expect(
    page.getByLabel("Search all Magic cards with Scryfall"),
  ).toBeHidden();
  await page.locator("#catalog-advanced > summary").click();
  await page.getByLabel("Search all Magic cards with Scryfall").check();
  await ready(page);
  await expect(page.locator("#point-status")).toContainText("Live Scryfall");
  await expect(page.locator("#point-query-help")).toBeHidden();
  await expect(page.locator("#point-metadata-note")).toContainText(
    "live Scryfall",
  );
  await expect(page.locator("#point-status")).toContainText("200 cards");
  await expect(page.getByLabel("Point values", { exact: true })).toBeDisabled();
  await expect(page.getByLabel("Cards per page")).toHaveValue("175");
  await expect(page.getByLabel("Sort results")).toHaveValue("name_asc");
  const pending = page
    .locator("tbody tr")
    .filter({ hasText: "A New Fixture Card" });
  await expect(pending.locator("td").nth(1)).toHaveText("Pending");
  await expect(pending.locator("td").nth(2)).toHaveText("Pending");
  const response = page.waitForResponse(
    (r) =>
      r.url().includes("/api/points?") &&
      new URL(r.url()).searchParams.get("q") === "set:lea OR set:leb",
  );
  await page.getByLabel("Find a card").fill("set:lea OR set:leb");
  await response;
  await ready(page);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.getByRole("button", { name: "Next →", exact: true }).click();
  await ready(page);
  await expect(page.locator("tbody tr")).toHaveCount(25);
  await expect(page.locator("#point-status")).toContainText("176–200");
  await page.getByLabel("Sort results").selectOption("mv_desc");
  await ready(page);
  await expect(page.locator("tbody tr")).toHaveCount(175);
  await page.setViewportSize({ width: 375, height: 850 });
  await page.screenshot({
    path: "reports/scryfall-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByLabel("Find a card").fill("");
  await page.getByLabel("Search all Magic cards with Scryfall").uncheck();
  await ready(page);
  await expect(page.getByLabel("Point values", { exact: true })).toBeEnabled();
  await expect(page.getByLabel("Sort results")).toHaveValue("main_desc");
  await expect(page.getByLabel("Cards per page")).toHaveValue("50");
  expect(errors).toEqual([]);
});
test("live failures are explicit and delayed live results cannot replace offline mode", async ({
  page,
}) => {
  let release;
  const gate = new Promise((r) => (release = r));
  let requested;
  const started = new Promise((r) => (requested = r));
  await page.route("**/api/points?*", async (route) => {
    const p = new URL(route.request().url()).searchParams;
    if (p.get("source") !== "scryfall") return route.continue();
    requested();
    await gate;
    await route
      .fulfill({
        status: 503,
        json: { error: "Scryfall is temporarily unavailable" },
      })
      .catch(() => {});
  });
  await page.goto("/points");
  await ready(page);
  await page.locator("#catalog-advanced > summary").click();
  await page.getByLabel("Search all Magic cards with Scryfall").check();
  await started;
  await page.getByLabel("Search all Magic cards with Scryfall").uncheck();
  await ready(page);
  const offline = await page.locator("#point-status").textContent();
  release();
  await page.waitForTimeout(100);
  await expect(page.locator("#point-status")).toHaveText(offline);
  await page.getByLabel("Search all Magic cards with Scryfall").check();
  await expect(page.getByRole("alert")).toContainText(
    "Scryfall is temporarily unavailable",
  );
  await page.getByLabel("Search all Magic cards with Scryfall").uncheck();
  await ready(page);
  await expect(page.locator("tbody tr")).toHaveCount(50);
});
