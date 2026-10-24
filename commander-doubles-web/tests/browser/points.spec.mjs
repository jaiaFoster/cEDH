import { test, expect } from "@playwright/test";

async function ready(page) {
  await expect(page.locator("#point-table")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await expect(page.locator("#point-status")).toContainText("cards");
}
async function query(page, value) {
  const response = page.waitForResponse(
    (r) =>
      r.url().includes("/api/points?") &&
      new URL(r.url()).searchParams.get("q") === value,
  );
  await page.getByLabel("Find a card").fill(value);
  const result = await response;
  await ready(page);
  return { data: await result.json(), url: new URL(result.url()) };
}
test("catalog searches, zero prices, command prices and unsupported queries", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/points");
  await ready(page);
  await query(page, '!"Sol Ring"');
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody tr td").nth(1)).toHaveText("15");
  await expect(page.locator("tbody tr td").nth(2)).toHaveText("—");
  await expect(page.locator("tbody a")).toHaveAttribute(
    "href",
    /^https:\/\/scryfall.com\/card\//,
  );
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.screenshot({ path: "reports/points-desktop.png", fullPage: true });
  await expect(page.locator("#catalog-advanced")).not.toHaveAttribute("open", "");
  await expect(page.getByLabel("Point values", { exact: true })).toBeHidden();
  await page.locator("#catalog-advanced > summary").click();
  await expect(page.getByLabel("Sort results")).toBeVisible();
  await page.getByLabel("Point values", { exact: true }).selectOption("zero");
  // The preserved admin lifecycle test intentionally publishes Acererak=1.
  // Use a different known free commander so this assertion is order-independent.
  await query(page, '!"Najeela, the Blade-Blossom"');
  await expect(page.locator("tbody tr td").nth(1)).toHaveText("0");
  await expect(page.locator("tbody tr td").nth(2)).toHaveText("0");
  await page.getByLabel("Point values", { exact: true }).selectOption("all");
  const { data: actual } = await query(page, '!"Thrasios, Triton Hero"');
  await expect(page.locator("tbody tr td").nth(1)).toHaveText(
    String(actual.cards[0].main),
  );
  await expect(page.locator("tbody tr td").nth(2)).toHaveText(
    String(actual.cards[0].command),
  );
  await page.getByLabel("Find a card").fill("set:lea");
  await expect(page.getByRole("alert")).toContainText(
    "Unsupported search syntax",
  );
  await expect(
    page.getByText("No matching cards", { exact: true }),
  ).toHaveCount(0);
  await query(page, 'o:"no such rules text 839284729"');
  await expect(
    page.getByText("No matching cards", { exact: true }),
  ).toBeVisible();
  await page.route("**/api/points?**", async (route) => {
    if (
      new URL(route.request().url()).searchParams.get("q") ===
      "rate-limit-fixture"
    )
      await route.fulfill({
        status: 429,
        contentType: "text/plain",
        body: "Too many requests",
      });
    else await route.continue();
  });
  await page.getByLabel("Find a card").fill("rate-limit-fixture");
  await expect(page.getByRole("alert")).toContainText("Too many searches");
  await expect(page.locator("tbody tr")).toHaveCount(0);
  expect(errors).toEqual([]);
});
test("identity, type, mana and price controls combine with the query and reset", async ({
  page,
}) => {
  await page.goto("/points");
  await ready(page);
  await page.locator("#catalog-advanced > summary").click();
  await page.getByLabel("Point values", { exact: true }).selectOption("all");
  await page.getByLabel("White", { exact: true }).check();
  await page.getByLabel("Blue", { exact: true }).check();
  await page.getByLabel("Card type", { exact: true }).selectOption("artifact");
  await page.getByLabel("Maximum mana value", { exact: true }).fill("3");
  await page
    .getByLabel("Commander legality", { exact: true })
    .selectOption("legal");
  const displayed = await query(page, 'o:"draw a card" "Mind Stone"');
  await expect(page.locator("tbody")).toContainText("Mind Stone");
  for (const [key, value] of Object.entries({
    identity: "wu",
    type: "artifact",
    mvMax: "3",
    legality: "legal",
    points: "all",
  }))
    expect(displayed.url.searchParams.get(key)).toBe(value);
  const ids = await page
    .locator("tbody tr")
    .evaluateAll((rows) => rows.map((r) => r.dataset.oracleId));
  expect(ids).toEqual(displayed.data.cards.map((c) => c.oracle_id));
  const exact = page.waitForResponse(
    (r) =>
      r.url().includes("/api/points?") &&
      new URL(r.url()).searchParams.get("identityMode") === "exact",
  );
  await page.getByLabel("Identity matching").selectOption("exact");
  await ready(page);
  const request = await (await exact).json();
  await expect(page.locator("#point-status")).toContainText(
    "of " + request.total.toLocaleString() + " cards",
  );
  await page.getByRole("button", { name: "Reset filters" }).click();
  await ready(page);
  await expect(page.getByLabel("Find a card")).toHaveValue("");
  await expect(page.getByLabel("White", { exact: true })).not.toBeChecked();
  await expect(page.getByLabel("Point values", { exact: true })).toHaveValue(
    "pointed",
  );
  await expect(page.getByLabel("Sort results")).toHaveValue("main_desc");
  await expect(page.getByLabel("Sort results")).toBeHidden();
});
test("both point sorts and every sort paginate over the full result set", async ({
  page,
}) => {
  await page.goto("/points");
  await ready(page);
  await page.locator("#catalog-advanced > summary").click();
  for (const sort of [
    "main_desc",
    "main_asc",
    "command_desc",
    "command_asc",
    "name_asc",
    "name_desc",
    "mv_asc",
    "mv_desc",
  ]) {
    const reset = page.waitForResponse(
      (r) =>
        r.url().includes("/api/points?") &&
        new URL(r.url()).searchParams.get("sort") === sort &&
        new URL(r.url()).searchParams.get("offset") === "0",
    );
    if ((await page.getByLabel("Sort results").inputValue()) === sort) {
      await page.getByRole("button", { name: "Search", exact: true }).click();
    } else await page.getByLabel("Sort results").selectOption(sort);
    const first = await (await reset).json();
    await ready(page);
    const next = page.waitForResponse(
      (r) =>
        r.url().includes("/api/points?") &&
        new URL(r.url()).searchParams.get("offset") === "50",
    );
    await page.getByRole("button", { name: "Next →", exact: true }).click();
    const second = await (await next).json();
    await ready(page);
    await expect(page.getByText(/^Page 2 of/)).toBeVisible();
    const joined = [...first.cards, ...second.cards];
    expect(joined).toHaveLength(100);
    expect(new Set(joined.map((c) => c.oracle_id)).size).toBe(100);
    expect(second.offset).toBe(50);
    expect(second.version.id).toBe(first.version.id);
    const [key, dir] = sort.split("_");
    const value = (c) =>
      key === "command"
        ? c.commanderEligible || c.command
          ? c.command
          : null
        : c[key];
    for (let i = 1; i < joined.length; i++) {
      const a = value(joined[i - 1]),
        b = value(joined[i]);
      if (a === null) {
        expect(b).toBe(null);
        continue;
      }
      if (b === null) continue;
      const difference = key === "name" ? a.localeCompare(b, "en") : a - b;
      expect(dir === "desc" ? -difference : difference).toBeLessThanOrEqual(0);
    }
    await expect(page.locator("tbody tr").first()).toHaveAttribute(
      "data-oracle-id",
      second.cards[0].oracle_id,
    );
  }
});
test("colorless and multicolor categories and valid numeric range errors", async ({
  page,
}) => {
  await page.goto("/points");
  await ready(page);
  await page.locator("#catalog-advanced > summary").click();
  await page.getByLabel("Identity category").selectOption("colorless");
  await query(page, '!"Sol Ring"');
  await expect(page.locator("tbody")).toContainText("Sol Ring");
  await page.getByLabel("Identity category").selectOption("multicolor");
  await ready(page);
  await expect(
    page.getByText("No matching cards", { exact: true }),
  ).toBeVisible();
  await query(page, '!"Thrasios, Triton Hero"');
  await expect(page.locator("tbody")).toContainText("Thrasios");
  await page.getByLabel("Minimum points", { exact: true }).fill("20");
  await page.getByLabel("Maximum points", { exact: true }).fill("2");
  await expect(page.getByRole("alert")).toContainText(
    "Minimum points cannot exceed maximum points",
  );
});
test("a slow obsolete response cannot overwrite a newer search", async ({
  page,
}) => {
  await page.goto("/points");
  await ready(page);
  let release;
  const blocked = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/points?**", async (route) => {
    if (new URL(route.request().url()).searchParams.get("q") === '!"Sol Ring"')
      await blocked;
    await route.continue().catch(() => {});
  });
  const old = page.waitForRequest(
    (r) =>
      r.url().includes("/api/points?") &&
      new URL(r.url()).searchParams.get("q") === '!"Sol Ring"',
  );
  await page.getByLabel("Find a card").fill('!"Sol Ring"');
  await old;
  await expect(page.locator("#point-status")).toHaveText("Searching…");
  await expect(page.locator("#point-table")).toHaveAttribute(
    "aria-busy",
    "true",
  );
  await query(page, '!"The One Ring"');
  release();
  await expect(page.locator("tbody")).toContainText("The One Ring");
  await expect(page.locator("tbody")).not.toContainText("Sol Ring");
  await expect(page.locator("tbody tr")).toHaveCount(1);
});
test("all five identity color controls and color-versus-identity search work", async ({
  page,
}) => {
  await page.goto("/points");
  await ready(page);
  await page.locator("#catalog-advanced > summary").click();
  await page.getByLabel("Point values", { exact: true }).selectOption("all");
  await page.getByLabel("Identity matching").selectOption("exact");
  const cases = [
    ["White", "Swords to Plowshares"],
    ["Blue", "Counterspell"],
    ["Black", "Demonic Tutor"],
    ["Red", "Lightning Bolt"],
    ["Green", "Dryad Arbor"],
  ];
  for (const [color, name] of cases) {
    for (const [label] of cases)
      await page.getByLabel(label, { exact: true }).uncheck();
    await page.getByLabel(color, { exact: true }).check();
    await query(page, '!"' + name + '"');
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator("tbody")).toContainText(name);
  }
  for (const [color] of cases)
    await page.getByLabel(color, { exact: true }).uncheck();
  await query(page, 'c:c id:ub !"Ulamog\'s Nullifier"');
  await expect(page.locator("tbody")).toContainText("Ulamog's Nullifier");
  await query(page, '!"Glasspool Shore"');
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText(
    "Glasspool Mimic // Glasspool Shore",
  );
});
test("mobile filters remain usable without document overflow", async ({
  browser,
  baseURL,
}) => {
  const context = await browser.newContext({
    viewport: { width: 375, height: 812 },
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(baseURL + "/points");
  await ready(page);
  await expect(page.getByLabel("Find a card")).toBeVisible();
  await expect(page.getByLabel("Green", { exact: true })).toBeHidden();
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.screenshot({ path: "reports/points-mobile-collapsed.png", fullPage: true });
  await page.locator("#catalog-advanced > summary").focus();
  await page.keyboard.press("Enter");
  await page.getByLabel("Green", { exact: true }).check();
  await page.getByLabel("Identity matching").selectOption("exact");
  await query(page, "t:creature");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.getByLabel("Maximum mana value", { exact: true }).fill("4");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await ready(page);
  for (const width of [375, 320]) {
    await page.setViewportSize({ width, height: 812 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    expect(
      await page
        .locator("#point-sort")
        .evaluate((e) => e.getBoundingClientRect().right <= window.innerWidth),
    ).toBe(true);
  }
  await page.setViewportSize({ width: 375, height: 812 });
  await page.screenshot({ path: "reports/points-mobile.png", fullPage: true });
  const count = await page.locator("#point-status").textContent();
  await page.locator("#catalog-advanced > summary").click();
  await expect(page.getByLabel("Maximum mana value", { exact: true })).toBeHidden();
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await expect(page.locator("#point-status")).toHaveText(count);
  await page.locator("#catalog-advanced > summary").click();
  await expect(page.getByLabel("Green", { exact: true })).toBeChecked();
  await expect(page.getByLabel("Maximum mana value", { exact: true })).toHaveValue("4");
  expect(errors).toEqual([]);
  await context.close();
});
