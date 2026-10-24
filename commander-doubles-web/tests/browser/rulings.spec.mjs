import { test, expect } from "@playwright/test";
test.beforeEach(async ({ context, baseURL }) => {
  if (["127.0.0.1", "localhost"].includes(new URL(baseURL).hostname))
    await context.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.70" });
});
async function ready(page) {
  await expect(page.locator("#ruling-results")).toHaveAttribute(
    "aria-busy",
    "false",
  );
}
test("rulings search, combined filters, source links, conditions and reset", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/rules");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "2HG Rulings & Interactions" }),
  ).toBeVisible();
  await expect(page.locator(".ruling-card")).toHaveCount(57);
  await page.getByLabel("Search rulings or cards").fill("Pox");
  await expect(page.locator("#ruling-pox-bloodletter")).toBeVisible();
  await page
    .getByLabel("Category", { exact: true })
    .selectOption("Shared life");
  await page.getByLabel("Interaction", { exact: true }).selectOption("Works");
  await ready(page);
  await expect(page.locator(".ruling-card")).toHaveCount(1);
  await page.locator("#ruling-pox-bloodletter > summary").click();
  await expect(page.locator("#ruling-pox-bloodletter")).toContainText("−20");
  await expect(page.locator("#ruling-pox-bloodletter")).toContainText("810.9a");
  await expect(
    page.locator("#ruling-pox-bloodletter a").first(),
  ).toHaveAttribute("href", /^https:\/\/scryfall.com\//);
  await expect(
    page.getByRole("link", { name: "Comprehensive Rules", exact: false }),
  ).toHaveAttribute("href", /MagicCompRules/);
  await page
    .getByLabel("Search rulings or cards")
    .fill("invented-no-such-ruling");
  await expect(
    page.getByText("No matching rulings", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset rulings filters" }).click();
  await expect(page.locator(".ruling-card")).toHaveCount(57);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator("#rulings-reference").scrollIntoViewIfNeeded();
  await page.screenshot({ path: "reports/rulings-desktop.png" });
  expect(errors).toEqual([]);
});
test("mobile rulings are readable without overflow and uncertain research is private", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 850 });
  await page.goto("/rules#ruling-rip-helm");
  await ready(page);
  await expect(page.locator("#ruling-rip-helm")).toHaveAttribute("open", "");
  await expect(page.locator("#ruling-rip-helm")).toContainText(
    "Exiling the library is not itself a win",
  );
  await expect(page.locator("#ruling-commander-aggregation")).toHaveCount(0);
  await page.screenshot({ path: "reports/rulings-mobile.png" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.setViewportSize({ width: 320, height: 850 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
test("rulings loading failure and stale search response handling", async ({
  page,
}) => {
  await page.route("**/api/rulings?*", async (route) => {
    const q = new URL(route.request().url()).searchParams.get("q");
    if (q === "slow") {
      await new Promise((r) => setTimeout(r, 500));
      return route
        .fulfill({
          json: {
            total: 0,
            rulings: [],
            categories: [],
            classifications: [],
            rules_edition: "stale",
          },
        })
        .catch(() => {});
    }
    if (q === "fail")
      return route.fulfill({
        status: 503,
        json: { error: "Reference temporarily unavailable" },
      });
    await route.continue();
  });
  await page.goto("/rules");
  await ready(page);
  await page.getByLabel("Search rulings or cards").fill("slow");
  await page.waitForTimeout(230);
  await page.getByLabel("Search rulings or cards").fill("Yuriko");
  await expect(page.locator("#ruling-yuriko-two-opponents")).toBeVisible();
  await page.waitForTimeout(600);
  await expect(page.locator("#ruling-yuriko-two-opponents")).toBeVisible();
  await page.getByLabel("Search rulings or cards").fill("fail");
  await expect(
    page.getByText("Reference temporarily unavailable"),
  ).toBeVisible();
  await page.getByLabel("Search rulings or cards").fill("Silence");
  await expect(page.locator("#ruling-silence-chant")).toBeVisible();
});
test("organizer adds, reviews, publishes, edits, restores and hides a literal-text ruling", async ({
  page,
}) => {
  await page.goto("/admin");
  await page
    .getByLabel("Administrator password")
    .fill(process.env.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in →", exact: true }).click();
  await page.getByRole("button", { name: "Rulings", exact: true }).click();
  const id = "browser-reference-" + Date.now();
  const literal = '<img src=x onerror="window.__rulingXSS=true">';
  await page.getByLabel("Stable ruling ID").fill(id);
  await page.getByLabel("Question / title").fill("Browser test ruling");
  await page.getByLabel("Short answer", { exact: true }).fill(literal);
  await page.getByLabel("Expanded explanation").fill("Text-only safety check.");
  await page
    .getByLabel("Worked example / calculation")
    .fill("60 minus 50 equals 10.");
  await page
    .getByLabel("Comprehensive Rules references (comma separated)")
    .fill("810.5");
  await page
    .getByLabel("Source URLs (HTTPS, one per line)")
    .fill("https://magic.wizards.com/en/rules");
  await page
    .getByLabel("Reason for this revision (required)")
    .fill("Browser fixture first draft");
  await page
    .getByRole("button", { name: "Save ruling draft", exact: true })
    .click();
  await expect(page.locator("#notice")).toContainText("draft saved");
  await expect(
    page.getByRole("button", { name: "Publish reviewed latest version" }),
  ).toBeVisible();
  const response = await page.request.get("/api/rulings/" + id);
  expect(response.status()).toBe(404);
  await page
    .getByRole("button", { name: "Publish reviewed latest version" })
    .click();
  await expect(page.locator("#notice")).toContainText(
    "Publication requires verified",
  );
  await page.getByLabel("Review status").selectOption("verified");
  await page.getByLabel("Verification date").fill("2026-10-24");
  await page.getByLabel("Verified by").fill("Browser test reviewer");
  await page
    .getByLabel("Reason for this revision (required)")
    .fill("Verified browser fixture");
  await page
    .getByRole("button", { name: "Save ruling draft", exact: true })
    .click();
  await expect(page.locator("#r-history")).toContainText("Revision 2");
  await page
    .getByRole("button", { name: "Publish reviewed latest version" })
    .click();
  await expect(page.locator("#notice")).toContainText(
    "Verified ruling published",
  );
  const publicPage = await page.context().newPage();
  await publicPage.goto("/rules#ruling-" + id);
  await ready(publicPage);
  await expect(publicPage.locator("#ruling-" + id)).toContainText(literal);
  await expect(publicPage.locator("#ruling-" + id + " img")).toHaveCount(0);
  expect(await publicPage.evaluate(() => window.__rulingXSS)).toBeUndefined();
  await publicPage.close();
  await page
    .getByLabel("Reason for this revision (required)")
    .fill("Restore original draft for review");
  await page
    .locator("#r-history summary")
    .filter({ hasText: /^Revision 1 ·/ })
    .click();
  await page
    .getByRole("button", {
      name: "Restore revision 1 as review draft",
      exact: true,
    })
    .click();
  await expect(page.getByLabel("Review status")).toHaveValue("needs_review");
  await expect(page.locator("#r-history")).toContainText("Revision 3");
  await page
    .getByLabel("Reason for this revision (required)")
    .fill("Hide disposable browser fixture");
  await page.getByRole("button", { name: "Hide published ruling" }).click();
  await expect(page.locator("#notice")).toContainText("Ruling hidden");
  expect((await page.request.get("/api/rulings/" + id)).status()).toBe(404);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
});
