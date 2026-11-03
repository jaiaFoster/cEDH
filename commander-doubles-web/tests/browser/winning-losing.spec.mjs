import { test, expect } from "@playwright/test";
const sources = {
  primary: "https://magic.wizards.com/en/rules",
  format: "https://magic.wizards.com/en/formats/two-headed-giant",
  pdf: "https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.pdf",
  txt: "https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt",
};
test.beforeEach(async ({ page, baseURL }) => {
  if (["localhost", "127.0.0.1"].includes(new URL(baseURL).hostname))
    await page.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.110" });
});
async function ready(page) {
  await expect(page.locator("#ruling-results")).toHaveAttribute(
    "aria-busy",
    "false",
  );
}
test("official rules section is prominent, dated, external and includes the seven priority sections", async ({
  page,
}) => {
  await page.goto("/rules");
  await ready(page);
  const official = page.locator("#official-rules-sources");
  await expect(
    official.getByRole("heading", { name: "Official Rules & Sources" }),
  ).toBeVisible();
  const labels = [
    ["Official Magic Rules", sources.primary],
    ["Official Two-Headed Giant Rules", sources.format],
    ["Comprehensive Rules PDF", sources.pdf],
    ["Searchable Comprehensive Rules TXT", sources.txt],
  ];
  for (const [label, url] of labels) {
    const link = official.getByRole("link", { name: label, exact: false });
    await expect(link).toHaveAttribute("href", url);
    await expect(link).toHaveAttribute("target", "_blank");
    await expect(link).toHaveAttribute("rel", "noopener noreferrer");
  }
  await expect(official).toContainText("Permanent primary source");
  await expect(official).toContainText("Effective September 25, 2026");
  await expect(official).toContainText("Checked 2026-11-02");
  const pos = await page.evaluate(() => ({
    source: document
      .querySelector("#official-rules-sources")
      .getBoundingClientRect().top,
    league: document.querySelector(".rule-text").getBoundingClientRect().top,
    faq: document.querySelector("#rulings-reference").getBoundingClientRect()
      .top,
  }));
  expect(pos.source).toBeLessThan(pos.league);
  expect(pos.source).toBeLessThan(pos.faq);
  await official.getByText("Useful rule sections", { exact: true }).click();
  for (const n of ["104", "119", "121", "704", "805", "810", "903"])
    await expect(
      official.getByRole("link", { name: new RegExp("CR " + n + " —") }),
    ).toBeVisible();
});
test("32-topic collection, milling distinction and clickable exact rules preserve the FAQ view", async ({
  page,
  context,
}) => {
  await page.goto("/rules");
  await ready(page);
  await page.getByRole("link", { name: "Winning & Losing FAQ ↓" }).click();
  await expect(page.locator("#ruling-count")).toContainText("27 rulings");
  await expect(page.locator(".ruling-card")).toHaveCount(27);
  await page.getByLabel("Search rulings or cards").fill("milling one opponent");
  await expect(page.locator(".ruling-card")).toHaveCount(2); // Milling and the related forced-draw answer.
  const mill = page.locator("#ruling-win-loss-mill");
  await mill.locator("summary").click();
  await expect(mill).toContainText("empty library alone does not cause a loss");
  await expect(mill).toContainText("30 cards");
  await expect(mill).toContainText("CR 104.3c");
  await expect(mill).toContainText("CR 704.5b");
  await expect(mill).toContainText("CR 810.8a");
  await expect(mill).toContainText("use Find");
  const ref = mill.getByRole("link", { name: "CR 704.5b", exact: false });
  await expect(ref).toHaveAttribute("href", sources.txt);
  // Only the browser navigation behavior is stubbed; live URL checks are retained in source-verification.json.
  await context.route(sources.txt, (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/plain",
      body: "Browser navigation fixture, not official rules text.",
    }),
  );
  const popupPromise = page.waitForEvent("popup");
  await ref.click();
  const popup = await popupPromise;
  await popup.waitForLoadState();
  expect(popup.url()).toBe(sources.txt);
  expect(page.url()).toMatch(/\/rules(?:#rulings-reference)?$/);
  await expect(page.getByLabel("Search rulings or cards")).toHaveValue(
    "milling one opponent",
  );
  await expect(mill).toHaveAttribute("open", "");
  await popup.close();
  await page.getByLabel("Search rulings or cards").fill("CR 704.5b");
  await expect(page.locator("#ruling-win-loss-mill")).toBeVisible();
  await page.getByRole("button", { name: "Reset rulings filters" }).click();
  await expect(page.locator(".ruling-card")).toHaveCount(84);
});
test("worked examples, protection caveats and source access remain usable at 320 and 375 pixels", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 850 });
  await page.goto("/rules");
  await ready(page);
  await page.screenshot({
    path: "reports/win-loss-official-mobile.png",
    fullPage: false,
  });
  await page.getByRole("button", { name: "Winning & Losing FAQ" }).click();
  await page.getByLabel("Search rulings or cards").fill("Aetherflux");
  await ready(page);
  const reservoir = page.locator("#ruling-reservoir-fifty");
  await expect(reservoir).toBeVisible();
  await reservoir.locator("summary").click();
  await expect(reservoir).toContainText("leaves your team at 10");
  await expect(reservoir).toContainText("team to 10");
  await expect(reservoir.locator(".tag")).toHaveText("Doesn’t Work");
  for (const width of [375, 320]) {
    await page.setViewportSize({ width, height: 850 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  await page.screenshot({
    path: "reports/win-loss-answer-mobile.png",
    fullPage: false,
  });
  await page
    .getByLabel("Search rulings or cards")
    .fill("How much commander damage?");
  await expect(page.locator("#ruling-commander-poison")).toBeVisible();
  await page.locator("#ruling-commander-poison > summary").click();
  await expect(page.locator("#ruling-commander-poison")).toContainText(
    "organizer clarification",
  );
});

test("Winning FAQ shortcut recovers an initial load failure without losing its category", async ({
  page,
}) => {
  await page.route("**/api/rulings?**", (r) =>
    r.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: "Temporary FAQ outage" }),
    }),
  );
  await page.goto("/rules");
  await expect(page.locator("#ruling-count")).toContainText(
    "Could not load rulings",
  );
  await expect(
    page.getByRole("heading", { name: "Official Rules & Sources" }),
  ).toBeVisible();
  await page.unroute("**/api/rulings?**");
  await page.getByRole("link", { name: "Winning & Losing FAQ ↓" }).click();
  await expect(page.locator(".ruling-card")).toHaveCount(27);
  await expect(page.getByLabel("Category", { exact: true })).toHaveValue("");
  await expect(page.locator("#winning-losing-filter")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("button", { name: "Reset rulings filters" }).click();
  await expect(page.locator(".ruling-card")).toHaveCount(84);
  await expect(page.getByLabel("Category", { exact: true })).toHaveValue("");
});

test("all six groups and everyday winning/losing questions reuse maintained accordion answers", async ({
  page,
}) => {
  await page.goto("/rules");
  await ready(page);
  await expect(
    page.getByRole("heading", {
      name: "Winning & Losing in Two-Headed Giant",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "What happens when one player mills out, loses the game, gains poison counters, or satisfies an alternate win condition?",
      { exact: true },
    ),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Winning & Losing FAQ", exact: true })
    .click();
  await expect(page.locator(".ruling-group > h3")).toHaveCount(6);
  const groups = [
    "Shared wins and losses",
    "Milling and empty libraries",
    "Commander damage and poison",
    "Alternate win conditions",
    "Shared-life interactions",
    "Preventing losses and special cases",
  ];
  for (const group of groups) {
    await page
      .getByLabel("Winning & Losing group", { exact: true })
      .selectOption(group);
    await expect(page.locator(".ruling-group > h3")).toHaveCount(1);
    await expect(page.locator(".ruling-group > h3")).toHaveText(group);
  }
  await page
    .getByLabel("Winning & Losing group", { exact: true })
    .selectOption("");
  const queries = [
    ["If I mill one opponent do both lose?", "win-loss-mill"],
    ["Does decking out kill the team?", "win-loss-mill"],
    ["Does poison require 10 or 15?", "commander-poison"],
    ["How much commander damage?", "commander-poison"],
    ["Does Thassa’s Oracle win for my teammate?", "oracle-own-library"],
    ["Can Platinum Angel save both players?", "cant-lose-team"],
  ];
  for (const [query, id] of queries) {
    await page.getByLabel("Search rulings or cards").fill(query);
    const card = page.locator("#ruling-" + id);
    await expect(card).toBeVisible();
    await card.locator("summary").click();
    await expect(card).toHaveAttribute("open", "");
    await expect(card.locator(".ruling-rule-links")).toBeVisible();
    await card.locator("summary").click();
    await expect(card).not.toHaveAttribute("open", "");
  }
  await page.getByLabel("Search rulings or cards").fill("poison");
  await page.getByLabel("Interaction", { exact: true }).selectOption("Works");
  await expect(page.locator("#ruling-win-loss-poison-events")).toBeVisible();
  await expect(page.locator("#ruling-win-loss-poison-mechanics")).toHaveCount(
    0,
  );
  await page.getByRole("button", { name: "Reset rulings filters" }).click();
  await expect(page.locator(".ruling-card")).toHaveCount(84);
  const ids = await page
    .locator(".ruling-card")
    .evaluateAll((els) => els.map((el) => el.id));
  expect(new Set(ids).size).toBe(ids.length);
});
