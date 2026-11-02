import { test, expect } from "@playwright/test";
const text =
  "COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n98 Island\n1 Biblioteca silvana";
test.beforeEach(async ({ page, baseURL }) => {
  if (["localhost", "127.0.0.1"].includes(new URL(baseURL).hostname))
    await page.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.100" });
});
async function team(page) {
  await page.goto("/teams");
  await page
    .getByLabel("Unique team name")
    .fill(
      "Printings " + Date.now() + " " + Math.random().toString(36).slice(2, 6),
    );
  await page.getByRole("button", { name: "Create team →" }).click();
  await expect(page.locator("#deck-1")).toBeVisible();
}
test("saved URL persists without zero score, text upload completes it on mobile and keeps team/slot", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await team(page);
  await page
    .locator("#link-1")
    .fill("moxfield.com/decks/browserblocked/primer?ref=shared");
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator('.team-deck[data-slot="1"]')).toContainText(
    "Saved, awaiting decklist",
  );
  await expect(page.locator('.team-deck[data-slot="1"] .total')).toHaveCount(0);
  await expect(page.locator("#link-1")).toHaveValue(
    "https://moxfield.com/decks/browserblocked",
  );
  await page.reload();
  await expect(page.locator('.team-deck[data-slot="1"]')).toContainText(
    "Saved, awaiting decklist",
  );
  await expect(page.locator("#deck-1 details")).toHaveAttribute("open", "");
  await page.locator("#upload-1").setInputFiles({
    name: "translated-deck.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(text),
  });
  await expect(page.locator("#export-1")).toHaveValue(text);
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator('.team-deck[data-slot="1"] .total')).toHaveText(
    "7",
  );
  await expect(page.locator('.team-deck[data-slot="1"]')).not.toContainText(
    "Saved, awaiting decklist",
  );
  await expect(page.locator("#link-1")).toHaveValue(
    "https://moxfield.com/decks/browserblocked",
  );
  await expect(
    page.locator('.team-deck[data-slot="1"] .import-notice'),
  ).toHaveCount(0);
  await expect(page.locator('.team-deck[data-slot="2"]')).toContainText(
    "No deck submitted",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "reports/printing-import-mobile.png",
    fullPage: true,
  });
});
test("multiple unresolved names can be confirmed together without editing the original export", async ({
  page,
}) => {
  await team(page);
  const source =
    "COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n97 Island\n1 Completely Unknown Fixture\n1 Another Unknown Fixture";
  await page.locator("#export-1").fill(source);
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(
    page.getByRole("heading", { name: "Review card names" }),
  ).toBeVisible();
  await expect(page.locator("[data-match-index]")).toHaveCount(2);
  await expect(page.locator('.team-deck[data-slot="1"] .total')).toHaveCount(0);
  await page.reload();
  await expect(page.locator("[data-match-index]")).toHaveCount(2);
  await page.locator('[data-match-index="2"]').fill("Sylvan Library");
  await page.locator('[data-match-index="3"]').fill("Sol Ring");
  await page.getByRole("button", { name: "Confirm names & save deck" }).click();
  await expect(page.locator('.team-deck[data-slot="1"] .total')).toHaveText(
    "22",
  );
  await page.reload();
  await expect(page.locator('.team-deck[data-slot="1"] .total')).toHaveText(
    "22",
  );
  await expect(page.locator("[data-match-index]")).toHaveCount(0);
});
test("pending replacement preserves previous scored inventory and can be cancelled", async ({
  page,
}) => {
  await team(page);
  await page.locator("#export-1").fill(text);
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator(".total").first()).toHaveText("7");
  await page
    .locator("#link-1")
    .fill("https://moxfield.com/decks/browsercancel");
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  const slot = page.locator('.team-deck[data-slot="1"]');
  await expect(slot).toContainText("Saved, awaiting decklist");
  await expect(slot.locator(".total")).toHaveText("7");
  await slot
    .getByRole("button", { name: "Cancel pending import & keep previous deck" })
    .click();
  await expect(slot).not.toContainText("Saved, awaiting decklist");
  await expect(slot.locator(".total")).toHaveText("7");
});

test("ambiguous legitimate localized name offers a card picker instead of a silent guess", async ({
  page,
}) => {
  await team(page);
  await page
    .locator("#export-1")
    .fill(
      "COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n98 Island\n1 Abafar",
    );
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  const picker = page.locator("select[data-match-index]");
  await expect(picker).toBeVisible();
  await expect(picker.locator("option")).toHaveText([
    "Choose the correct card",
    "Douse",
    "Swelter",
  ]);
  await picker.selectOption("Douse");
  await page.getByRole("button", { name: "Confirm names & save deck" }).click();
  await expect(page.locator('.team-deck[data-slot="1"] .result')).toContainText(
    "100/100 cards",
  );
  await expect(page.locator("select[data-match-index]")).toHaveCount(0);
});

test("organizer can inspect a saved reference even before an inventory exists", async ({
  page,
}) => {
  await team(page);
  const id = await page.locator("#team-select").inputValue();
  await page.locator("#link-1").fill("https://moxfield.com/decks/organizerref");
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator('.team-deck[data-slot="1"]')).toContainText(
    "Saved, awaiting decklist",
  );
  await page.goto("/admin");
  await page
    .getByLabel("Administrator password")
    .fill(process.env.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in →" }).click();
  await page.getByRole("button", { name: "Teams", exact: true }).click();
  await page.locator("#admin-team").selectOption(id);
  const slot = page.locator('#admin-team-detail .team-deck[data-slot="1"]');
  await expect(slot).toContainText("Saved, awaiting decklist");
  await expect(
    slot.getByRole("link", { name: "Open pending Moxfield reference ↗" }),
  ).toHaveAttribute("href", "https://moxfield.com/decks/organizerref");
  await expect(slot.locator(".total")).toHaveCount(0);
});
