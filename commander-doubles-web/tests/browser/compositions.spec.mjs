import { test, expect } from "@playwright/test";
test.beforeEach(async ({ context, baseURL }) => {
  if (["localhost", "127.0.0.1"].includes(new URL(baseURL).hostname))
    await context.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.130" });
});
async function ready(page) {
  await expect(page.locator("#composition-results")).toHaveAttribute(
    "aria-busy",
    "false",
  );
}
test("compact gallery, complete partners, all 88 summaries, multiple disclosures and pagination", async ({
  page,
}) => {
  await page.goto("/compositions");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "Team Compositions", exact: true }),
  ).toBeVisible();
  await expect(page.locator("#composition-count")).toContainText(
    "88 published",
  );
  await expect(page.locator("#composition-advanced")).toBeHidden();
  await expect(page.locator(".composition-card")).toHaveCount(24);
  await expect(page.locator(".composition-card").first()).toHaveAttribute(
    "id",
    "composition-seed-10",
  );
  const a = page.locator("#composition-benchmark-a");
  for (const name of [
    "Tymna the Weaver",
    "Kraum, Ludevic's Opus",
    "Thrasios, Triton Hero",
    "Bruse Tarl, Boorish Herder",
  ])
    await expect(a.locator(":scope > summary")).toContainText(name);
  await page.locator("#composition-seed-10 > summary").click();
  await a.locator(":scope > summary").click();
  await expect(a).toHaveAttribute("open", "");
  await expect(page.locator("#composition-seed-10")).toHaveAttribute(
    "open",
    "",
  );
  await expect(a.locator(":scope > summary")).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(a).toContainText("462 / 120");
  await expect(a).toContainText("not certified budget-compliant");
  await page.getByRole("button", { name: "Load more compositions" }).click();
  await expect(page.locator(".composition-card")).toHaveCount(48);
  await expect(a).toHaveAttribute("open", "");
  await page.getByRole("button", { name: "Load more compositions" }).click();
  await expect(page.locator(".composition-card")).toHaveCount(72);
  await page.getByRole("button", { name: "Load more compositions" }).click();
  await expect(page.locator(".composition-card")).toHaveCount(88);
  await expect(
    page.getByRole("button", { name: "Load more compositions" }),
  ).toBeHidden();
  const ids = await page
    .locator(".composition-card")
    .evaluateAll((es) => es.map((e) => e.id));
  expect(new Set(ids).size).toBe(88);
  await a.locator(":scope > summary").focus();
  await page.keyboard.press("Enter");
  await expect(a).not.toHaveAttribute("open", "");
  await expect(a.locator(":scope > summary")).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});
test("search covers partner names, duplicate Yuriko heads and the required research queries", async ({
  page,
}) => {
  await page.goto("/compositions");
  await ready(page);
  const query = page.getByRole("searchbox", { name: "Search compositions" });
  for (const [term, ids] of [
    ["Heartless", ["seed-10", "seed-12"]],
    ["Yuriko", ["benchmark-c"]],
    ["Tymna", ["benchmark-a", "benchmark-h", "seed-28"]],
    ["Arcum", ["seed-19", "seed-20"]],
    ["artifact tutors", ["seed-19"]],
    ["each opponent", ["seed-29"]],
  ]) {
    await query.fill(term);
    for (const id of ids)
      await expect(page.locator("#composition-" + id)).toBeVisible();
  }
  await query.fill("Yuriko");
  await expect(
    page.locator("#composition-benchmark-c summary .composition-names"),
  ).toHaveCount(2);
  await expect(page.locator("#composition-advanced")).toBeHidden();
  await query.fill("unfindable-composition-xyz");
  await expect(
    page.getByText("No matching compositions", { exact: true }),
  ).toBeVisible();
  await query.fill("");
  await ready(page);
  await page.getByRole("button", { name: "Advanced", exact: true }).click();
  await page.getByLabel("Commander name", { exact: true }).fill("Najeela");
  await page.getByLabel("Commander matching").selectOption("0");
  await ready(page);
  const expected = await page.request.get(
    "/api/compositions?commander=Najeela&limit=100",
  );
  const data = await expected.json();
  await expect(page.locator(".composition-card")).toHaveCount(data.total);
  for (const p of data.compositions)
    await expect(page.locator("#composition-" + p.id)).toBeVisible();
});
test("combined Advanced filters, price sorts across pages, clear and unsupported syntax", async ({
  page,
}) => {
  await page.goto("/compositions");
  await ready(page);
  await page.getByRole("button", { name: "Advanced", exact: true }).click();
  await page
    .getByLabel("Player A colors (WUBRG or C)", { exact: true })
    .fill("BG");
  await page
    .getByLabel("Color matching", { exact: true })
    .selectOption("exact");
  await page
    .getByRole("searchbox", { name: "Search compositions" })
    .fill("Heartless");
  await expect(page.locator(".composition-card")).toHaveCount(1);
  await expect(page.locator("#composition-seed-10")).toBeVisible();
  await page.getByRole("button", { name: "Advanced", exact: true }).click();
  await expect(page.locator("#composition-advanced")).toBeHidden();
  await expect(page.locator("#composition-seed-10")).toBeVisible();
  await page.getByRole("button", { name: "Advanced", exact: true }).click();
  await page.getByRole("button", { name: "Clear all filters" }).click();
  await expect(page.locator(".composition-card")).toHaveCount(24);
  await page
    .getByLabel("Decklist status", { exact: true })
    .selectOption("compliant");
  await expect(
    page.getByText("No matching compositions", { exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Decklist status", { exact: true })
    .selectOption("historical");
  await expect(page.locator(".composition-card")).toHaveCount(9);
  await page.getByRole("button", { name: "Clear all filters" }).click();
  await page.getByLabel("Sort", { exact: true }).selectOption("points_desc");
  await ready(page);
  const api = await page.request.get(
    "/api/compositions?sort=points_desc&limit=48",
  );
  const expected = (await api.json()).compositions.map(
    (p) => "composition-" + p.id,
  );
  await page.getByRole("button", { name: "Load more compositions" }).click();
  await expect(page.locator(".composition-card")).toHaveCount(48);
  expect(
    await page
      .locator(".composition-card")
      .evaluateAll((es) => es.map((e) => e.id)),
  ).toEqual(expected);
  await page
    .getByRole("searchbox", { name: "Search compositions" })
    .fill("o:win");
  await expect(page.locator("#composition-results")).toContainText(
    "Card operators are not composition syntax",
  );
  await page
    .getByRole("searchbox", { name: "Search compositions" })
    .fill("Ivy");
  await expect(page.locator("#composition-seed-34")).toBeVisible();
});
test("deep links retain filters, support history and open profiles outside the first page", async ({
  page,
}) => {
  await page.goto("/compositions?archetype=Combat#composition-seed-37");
  await ready(page);
  await expect(page.locator("#composition-seed-37")).toHaveAttribute(
    "open",
    "",
  );
  await page.getByRole("button", { name: "Advanced", exact: true }).click();
  await expect(page.getByLabel("Archetype", { exact: true })).toHaveValue(
    "Combat",
  );
  await page.goto("/compositions?q=Heartless#composition-discovery-50");
  await ready(page);
  await expect(page.locator("#composition-discovery-50")).toHaveAttribute(
    "open",
    "",
  );
  await expect(
    page.getByRole("searchbox", { name: "Search compositions" }),
  ).toHaveValue("Heartless");
  await expect(page.locator("#composition-results")).toContainText(
    "shown separately from the filtered results",
  );
  await page.goto("/compositions");
  await ready(page);
  await page.locator("#composition-seed-10 > summary").click();
  await page.locator("#composition-benchmark-a > summary").click();
  await page.goBack();
  await expect(page).toHaveURL(/#composition-seed-10$/);
  await expect(page.locator("#composition-seed-10")).toHaveAttribute(
    "open",
    "",
  );
  await page.goForward();
  await expect(page).toHaveURL(/#composition-benchmark-a$/);
});
test("mobile profiles, source actions and missing images remain usable at 320 and 375 pixels", async ({
  page,
  context,
}) => {
  await context.route("https://cards.scryfall.io/**", (r) => r.abort());
  await page.setViewportSize({ width: 375, height: 850 });
  await page.goto("/compositions#composition-seed-10");
  await ready(page);
  await expect(page.locator("#composition-seed-10")).toHaveAttribute(
    "open",
    "",
  );
  await expect(page.locator("#composition-seed-10")).toContainText(
    "one chosen active player",
  );
  await expect(page.locator("#composition-seed-10")).toContainText(
    "Arena of Glory",
  );
  const link = page
    .locator("#composition-seed-10")
    .getByRole("link", { name: "CR 805.9", exact: false });
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noopener noreferrer");
  for (const width of [375, 320]) {
    await page.setViewportSize({ width, height: 850 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Advanced", exact: true }).click();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Advanced", exact: true }).click();
  }
  await page.setViewportSize({ width: 375, height: 850 });
  await page.locator("#composition-seed-10").scrollIntoViewIfNeeded();
  await page.screenshot({ path: "reports/compositions-mobile.png" });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/compositions");
  await ready(page);
  await page.screenshot({ path: "reports/compositions-desktop.png" });
});
test("organizer composition editor retains drafts, publication and restored history with safe text", async ({
  page,
}) => {
  await page.goto("/admin");
  await page
    .getByLabel("Administrator password")
    .fill(process.env.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in →", exact: true }).click();
  await page.getByRole("button", { name: "Compositions", exact: true }).click();
  await page.getByLabel("Choose a composition").selectOption("seed-10");
  await expect(page.getByLabel("One-line hook")).toBeVisible();
  const literal = '<img src=x onerror="window.__compositionXSS=true">';
  await page.getByLabel("One-line hook").fill(literal);
  await page
    .getByLabel("Revision reason (required)")
    .fill("Browser text safety fixture");
  await page
    .getByRole("button", { name: "Save composition draft", exact: true })
    .click();
  await expect(page.locator("#notice")).toContainText("draft saved");
  await page
    .getByRole("button", { name: "Publish reviewed composition", exact: true })
    .click();
  await expect(page.locator("#notice")).toContainText("published");
  const pub = await page.context().newPage();
  await pub.goto("/compositions?q=Belbe");
  await ready(pub);
  await expect(pub.locator("#composition-seed-10 > summary")).toContainText(
    literal,
  );
  await expect(
    pub.locator("#composition-seed-10 .composition-hook img"),
  ).toHaveCount(0);
  expect(await pub.evaluate(() => window.__compositionXSS)).toBeUndefined();
  await pub.close();
  await page
    .getByLabel("Revision reason (required)")
    .fill("Recover source-reviewed original");
  await page
    .locator("#composition-history summary")
    .filter({ hasText: /^Revision 1 ·/ })
    .click();
  await page
    .getByRole("button", {
      name: "Restore revision 1 as review draft",
      exact: true,
    })
    .click();
  await expect(page.getByLabel("Mechanics review status")).toHaveValue(
    "needs_review",
  );
  await page
    .getByRole("button", { name: "Publish reviewed composition", exact: true })
    .click();
  await expect(page.locator("#notice")).toContainText(
    "Publication requires verified",
  );
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
});
