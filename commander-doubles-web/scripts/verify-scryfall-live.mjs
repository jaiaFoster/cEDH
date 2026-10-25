// Optional read-only local smoke test against the real Scryfall service. Not a CI fixture.
import { chromium, expect } from "@playwright/test";
import fs from "node:fs";
const base = process.env.BASE_URL || "http://127.0.0.1:3340";
if (!["localhost", "127.0.0.1"].includes(new URL(base).hostname))
  throw Error("This smoke test is restricted to a local application.");
const browser = await chromium.launch({
  channel: process.env.CI ? undefined : "chrome",
});
const page = await browser.newPage({
  baseURL: base,
  viewport: { width: 1280, height: 1000 },
  extraHTTPHeaders: { "X-Forwarded-For": "192.0.2.90" },
});
page.setDefaultTimeout(20000);
try {
  await page.goto("/points");
  await expect(page.locator("#point-table")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await page.locator("#catalog-advanced > summary").click();
  await page.getByLabel("Find a card").fill('!"Sol Ring"');
  const wait = page.waitForResponse(
    (r) =>
      r.url().includes("/api/points?") &&
      new URL(r.url()).searchParams.get("source") === "scryfall",
  );
  await page.getByLabel("Search all Magic cards with Scryfall").check();
  const ring = await (await wait).json();
  await expect(page.locator("#point-table")).toHaveAttribute(
    "aria-busy",
    "false",
  );
  await expect(page.locator("tbody tr")).toHaveCount(1);
  const local = await (
    await page.request.get(
      "/api/points?" +
        new URLSearchParams({ q: '!"Sol Ring"', version: ring.version.id }),
    )
  ).json();
  await expect(page.locator("tbody tr td").nth(1)).toHaveText(
    String(local.cards[0].main),
  );
  const next = page.waitForResponse(
    (r) =>
      r.url().includes("/api/points?") &&
      new URL(r.url()).searchParams.get("q") === '!"Data, New Life"',
  );
  await page.getByLabel("Find a card").fill('!"Data, New Life"');
  const data = await (await next).json();
  await expect(page.locator("tbody tr td").nth(1)).toHaveText(
    data.cards[0].priceKnown ? String(data.cards[0].main) : "Pending",
  );
  await page.setViewportSize({ width: 375, height: 850 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  fs.mkdirSync("reports", { recursive: true });
  await page.screenshot({
    path: "reports/scryfall-live-mobile.png",
    fullPage: true,
  });
  const empty = await (
    await page.request.get(
      "/api/points?source=scryfall&q=this_card_name_does_not_exist_xyz123",
    )
  ).json();
  const page2 = await (
    await page.request.get(
      "/api/points?source=scryfall&q=set%3Alea%20OR%20set%3Aleb&offset=175",
    )
  ).json();
  expect(empty.total).toBe(0);
  expect(page2.cards.length).toBeGreaterThan(0);
  expect(page2.offset).toBe(175);
  const report = {
    verified_at: new Date().toISOString(),
    real_upstream: true,
    hosted_staging: false,
    ring: {
      total: ring.total,
      main: ring.cards[0].main,
      oracle_id: ring.cards[0].oracle_id,
    },
    new_card: {
      name: data.cards[0].name,
      main: data.cards[0].main,
      priceKnown: data.cards[0].priceKnown,
      legality: data.cards[0].legality,
    },
    empty: { total: empty.total },
    native_or_page2: {
      total: page2.total,
      offset: page2.offset,
      returned: page2.cards.length,
    },
    mobile_no_overflow: true,
  };
  fs.writeFileSync(
    "reports/scryfall-live-verification.json",
    JSON.stringify(report, null, 2) + "\n",
  );
  console.log(JSON.stringify(report));
} finally {
  await browser.close();
}
