import { test, expect } from "@playwright/test";
import fs from "node:fs";
const fixture = fs.readFileSync(new URL("../fixtures/import-incident-100.txt", import.meta.url), "utf8");
const small = "COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n98 Island\n1 Lotus Petal";
// The local app trusts one proxy hop, matching Railway. Represent this new
// test actor with its own documentation-only IP instead of pooling the entire
// growing browser suite into one person's 240/min allowance. Never send this
// test proxy header to a hosted service; production rate limits are unchanged.
test.beforeEach(async ({ page, baseURL }) => {
  if (["127.0.0.1", "localhost"].includes(new URL(baseURL).hostname))
    await page.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.50" });
});
async function team(page) {
  await page.goto("/teams");
  await page.getByLabel("Unique team name").fill("Import regression " + Date.now() + " " + Math.random().toString(36).slice(2, 7));
  await page.getByRole("button", { name: "Create team →" }).click();
  await expect(page.locator("#deck-1")).toBeVisible();
}

test("reported 100-card list passes legality, retains official prices, and shows fuzzy matches on mobile", async ({ page }) => {
  await team(page);
  // New decks start with the fallback open.
  await page.locator("#deck-1").getByLabel("Deck export", { exact: true }).fill(fixture.replace("1 Lotus Petal", "1 Lotus Petla"));
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  const result = page.locator(".result").first();
  await expect(result).toContainText("Construction checks passed against the pinned catalog.");
  await expect(result.locator(".total")).toHaveText("507");
  await expect(result).toContainText("100/100 cards");
  await expect(result.locator(".error-list")).toHaveCount(0);
  await expect(result.locator(".import-notice")).toContainText("Lotus Petla");
  await expect(result.locator(".import-notice")).toContainText("Lotus Petal");
  await expect(result).toContainText("Above the individual 72-point cap.");
  await page.reload();
  await expect(page.locator(".import-notice")).toContainText("Lotus Petla");
  await page.setViewportSize({ width: 375, height: 812 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "reports/import-correction-mobile.png", fullPage: true });
});

test("blocked URL opens the export fallback and cannot erase a saved deck; unknown names do not save", async ({ page }) => {
  await team(page);
  await page.locator("#deck-1").getByLabel("Deck export", { exact: true }).fill(small);
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator(".result .total").first()).toHaveText("9");
  await expect(page.locator("#deck-1 details")).not.toHaveAttribute("open", "");
  const link = "https://moxfield.com/decks/blocked-test-fixture";
  await page.locator("#link-1").fill(link);
  // Simulate the application's real upstream-block response, not a claim of live Moxfield availability.
  const route = "**/api/teams/*/decks/1";
  await page.route(route, r => r.fulfill({ status: 400, contentType: "application/json", body: JSON.stringify({ error: "Moxfield blocked automated deck imports. Open your deck in Moxfield and paste its text export below." }) }));
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator("#notice")).toContainText("Moxfield blocked");
  await expect(page.locator("#deck-1 details")).toHaveAttribute("open", "");
  await expect(page.locator("#export-1")).toBeFocused();
  await expect(page.locator("#link-1")).toHaveValue(link);
  await expect(page.locator(".result .total").first()).toHaveText("9");
  await page.unroute(route);
  await page.locator("#export-1").fill(small.replace("Lotus Petal", "Imaginary Unknown Card"));
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator("#notice")).toContainText("Unknown or ambiguous card");
  await expect(page.locator(".result .total").first()).toHaveText("9");
  await page.locator("#export-1").fill(small);
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.getByText("Deck scored and saved.", { exact: false })).toBeVisible();
  await expect(page.locator(".result").first()).toContainText("100/100 cards");
  await expect(page.locator("#link-1")).toHaveValue(link);
});
