import { test, expect } from "@playwright/test";
const textA = "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Sol Ring";
const textB = "COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n99 Forest";
// Independent local test actor; never send a synthetic proxy header to a hosted service.
test.beforeEach(async ({ context, baseURL }) => {
  if (["127.0.0.1", "localhost"].includes(new URL(baseURL).hostname))
    await context.setExtraHTTPHeaders({ "X-Forwarded-For": "192.0.2.60" });
});
async function seed(page) {
  const suffix = Date.now() + " " + Math.random().toString(36).slice(2, 7);
  async function create(letter) {
    const r = await page.request.post("/api/teams", { data: { name: `Association ${letter} ${suffix}`, players: [`${letter} one`, `${letter} two`] } });
    expect(r.status()).toBe(201);
    return r.json();
  }
  const a = await create("A"), b = await create("B");
  const saved = await page.request.post(`/api/teams/${a.id}/decks/1`, { data: { text: textA } });
  expect(saved.status()).toBe(201);
  return { a, b, saved: await saved.json() };
}
async function selected(page, id) {
  await expect(page.locator("#team-select")).toHaveValue(id);
  await expect(page.locator("#team-detail")).toHaveAttribute("data-team-id", id);
  await expect(page.locator("#team-detail")).toHaveAttribute("aria-busy", "false");
}
function gate() {
  let release;
  const wait = new Promise(resolve => { release = resolve; });
  return { wait, release };
}

test("creating a separate team starts empty and never inherits another team's decks", async ({ page }) => {
  const { a, saved } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  await expect(page.locator('.team-deck[data-slot="1"]')).toContainText("19");
  await page.getByRole("link", { name: "Create a new team →", exact: true }).click();
  await expect(page.getByLabel("Unique team name")).toBeFocused();
  await page.getByLabel("Unique team name").fill("Separate team " + Date.now());
  await page.getByLabel("Player one (optional)").fill("Separate one");
  await page.getByRole("button", { name: "Create team →", exact: true }).click();
  await expect(page.locator("#team-detail .empty strong").filter({ hasText: /^No deck submitted$/ })).toHaveCount(2);
  const b = await page.locator("#team-select").inputValue();
  expect(b).not.toBe(a.id);
  await selected(page, b);
  await expect(page.locator("#team-detail .result")).toHaveCount(0);
  await expect(page.locator("#link-1")).toHaveValue("");
  await page.locator("#upload-1").setInputFiles({ name: "own-deck.txt", mimeType: "text/plain", buffer: Buffer.from(textB) });
  await expect(page.locator("#export-1")).toHaveValue(textB);
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  await expect(page.locator('.team-deck[data-slot="1"] .saved-decklist')).toBeVisible();
  await page.locator('.team-deck[data-slot="1"] .saved-decklist summary').click();
  await expect(page.locator('.team-deck[data-slot="1"] pre')).toHaveText(textB);
  await page.reload();
  await selected(page, b);
  await expect(page.locator('.team-deck[data-slot="2"]')).toContainText("No deck submitted");
  const old = await (await page.request.get(`/api/teams/${a.id}`)).json();
  expect(old.decks[0].id).toBe(saved.id);
  const fresh = await (await page.request.get(`/api/teams/${b}`)).json();
  expect(fresh.decks[0].team_id).toBe(b);
  expect(fresh.decks[0].current_deck.cards.some(c => c.name === "Forest")).toBe(true);
  await page.setViewportSize({ width: 375, height: 812 });
  await page.locator('.team-deck[data-slot="1"] .saved-decklist summary').click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "reports/team-deck-association-mobile.png", fullPage: true });
});

test("late team responses cannot overwrite the selection even if the transport ignores abort", async ({ page }) => {
  const { a, b } = await seed(page);
  await page.addInitScript((id) => {
    const original = window.fetch;
    window.fetch = (input, options) => {
      if (String(input) === "/api/teams/" + id && options) {
        const { signal, ...rest } = options;
        return original(input, rest);
      }
      return original(input, options);
    };
  }, a.id);
  await page.goto(`/teams?team=${b.id}`);
  await selected(page, b.id);
  const hold = gate();
  await page.route(`**/api/teams/${a.id}`, async route => { await hold.wait; await route.continue(); });
  const oldRequest = page.waitForRequest(r => r.url().endsWith(`/api/teams/${a.id}`));
  await page.locator("#team-select").selectOption(a.id);
  await oldRequest;
  await expect(page.locator("#team-detail")).toContainText("Loading selected team");
  await expect(page.locator("#deck-1")).toHaveCount(0);
  await page.locator("#team-select").selectOption(b.id);
  await selected(page, b.id);
  const oldResponse = page.waitForResponse(r => r.url().endsWith(`/api/teams/${a.id}`));
  hold.release();
  await (await oldResponse).finished();
  await page.evaluate(() => new Promise(requestAnimationFrame));
  await selected(page, b.id);
  await expect(page.locator("#team-detail")).not.toContainText("Shorikai");
  await expect(page.locator("#team-detail .result")).toHaveCount(0);
});

test("failed and blank selections clear old forms rather than showing another team's decks", async ({ page }) => {
  const { a, b } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  await page.route(`**/api/teams/${b.id}`, route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: "Temporary team-load failure" }) }));
  await page.locator("#team-select").selectOption(b.id);
  await expect(page.locator("#team-detail")).toContainText("Unable to load this team");
  await expect(page.locator("#team-detail")).not.toContainText("Shorikai");
  await expect(page.locator("#deck-1")).toHaveCount(0);
  await page.locator("#team-select").selectOption("");
  await expect(page.locator("#team-detail")).toContainText("Pick your side");
  await expect(page.locator("#team-detail")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator("#edit-team")).toHaveCount(0);
});

test("an in-flight save stays bound to its original team and does not replace the next team's form", async ({ page }) => {
  const { a, b } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  // Represent another tab remembering B while this tab still explicitly edits A.
  await page.evaluate(id => localStorage.setItem("cd-team", id), b.id);
  await page.locator("#deck-1 summary").click();
  await page.locator("#export-1").fill(textB);
  const hold = gate();
  await page.route(`**/api/teams/${a.id}/decks/1`, async route => { await hold.wait; await route.continue(); });
  const saving = page.waitForRequest(r => r.method() === "POST" && r.url().endsWith(`/api/teams/${a.id}/decks/1`));
  await page.getByRole("button", { name: "Score & save player 1" }).click();
  const request = await saving;
  expect(request.postDataJSON().text).toBe(textB);
  await page.locator("#team-select").selectOption(b.id);
  await selected(page, b.id);
  const done = page.waitForResponse(r => r.request().method() === "POST" && r.url().endsWith(`/api/teams/${a.id}/decks/1`));
  hold.release();
  await (await done).finished();
  await page.evaluate(() => new Promise(requestAnimationFrame));
  await selected(page, b.id);
  await expect(page.locator("#team-detail .result")).toHaveCount(0);
  expect((await (await page.request.get(`/api/teams/${b.id}`)).json()).decks).toHaveLength(0);
  const original = await (await page.request.get(`/api/teams/${a.id}`)).json();
  expect(original.decks[0].current_deck.cards[0].name).toBe("Kenrith, the Returned King");
});

test("a late uploaded-file read cannot populate another team's new form", async ({ page }) => {
  const { a, b } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  await page.locator("#deck-1 summary").click();
  await page.evaluate(() => {
    const original = File.prototype.text;
    File.prototype.text = async function () {
      const text = await original.call(this);
      await new Promise(resolve => { window.releaseUpload = resolve; });
      return text;
    };
  });
  await page.locator("#upload-1").setInputFiles({ name: "late-deck.txt", mimeType: "text/plain", buffer: Buffer.from(textB) });
  await expect.poll(() => page.evaluate(() => typeof window.releaseUpload)).toBe("function");
  await page.locator("#team-select").selectOption(b.id);
  await selected(page, b.id);
  await page.evaluate(() => window.releaseUpload());
  await page.evaluate(() => new Promise(requestAnimationFrame));
  await expect(page.locator("#export-1")).toHaveValue("");
  await expect(page.locator("#team-detail .result")).toHaveCount(0);
});

test("organizer inspection shows full current decks without changing the remembered public team", async ({ page }) => {
  const { a, b } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  await page.goto("/admin");
  await page.getByLabel("Administrator password").fill(process.env.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in →" }).click();
  await page.getByRole("button", { name: "Teams", exact: true }).click();
  await page.locator("#admin-team").selectOption(a.id);
  await expect(page.locator("#admin-team-detail")).toContainText("Current saved decks");
  await page.locator('#admin-team-detail .team-deck[data-slot="1"] .saved-decklist summary').click();
  await expect(page.locator('#admin-team-detail .team-deck[data-slot="1"] pre')).toHaveText(textA);
  await page.locator("#admin-team").selectOption(b.id);
  await expect(page.locator("#admin-team-detail .empty strong").filter({ hasText: /^No deck submitted$/ })).toHaveCount(2);
  expect(await page.evaluate(() => localStorage.getItem("cd-team"))).toBe(a.id);
  await page.locator("#admin-team").selectOption("");
  await expect(page.locator("#admin-team-detail")).toContainText("Choose a team");
  await expect(page.locator("#admin-team-detail")).not.toContainText("Shorikai");
  await page.locator("#admin-team").selectOption(b.id);
  await page.getByRole("link", { name: "Edit team & decks", exact: true }).click();
  await selected(page, b.id);
  await expect(page).toHaveURL(new RegExp("/teams\\?team=" + b.id));
});

test("renaming a team requires explicit confirmation and preserves its own saved decks", async ({ page }) => {
  const { a, saved } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  const renamed = "Renamed " + a.name;
  await page.getByLabel("Team name", { exact: true }).fill(renamed);
  page.once("dialog", async dialog => { expect(dialog.message()).toContain("saved decks and registrations stay"); await dialog.dismiss(); });
  await page.getByRole("button", { name: "Save team details", exact: true }).click();
  expect((await (await page.request.get(`/api/teams/${a.id}`)).json()).name).toBe(a.name);
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Save team details", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Editing existing team: " + renamed })).toBeVisible();
  await expect(page.locator("#team-select option:checked")).toHaveText(renamed);
  const fresh = await (await page.request.get(`/api/teams/${a.id}`)).json();
  expect(fresh.decks[0].id).toBe(saved.id);
  expect(fresh.decks[0].team_id).toBe(a.id);
});

test("an unavailable explicit team link never falls back to remembered decks", async ({ page }) => {
  const { a } = await seed(page);
  await page.goto(`/teams?team=${a.id}`);
  await selected(page, a.id);
  await page.goto("/teams?team=00000000-0000-0000-0000-000000000000");
  await expect(page.locator("#team-select")).toHaveValue("");
  await expect(page.locator("#team-detail")).toContainText("Pick your side");
  await expect(page.locator("#team-detail .result")).toHaveCount(0);
  await expect(page.locator("#notice")).toContainText("team is unavailable");
});

test("late organizer history cannot replace another team's current deck view", async ({ page }) => {
  const { a, b } = await seed(page);
  await page.addInitScript((id) => {
    const original = window.fetch;
    window.fetch = (input, options) => {
      if (String(input).includes("/api/admin/teams/" + id + "/history") && options) {
        const { signal, ...rest } = options;
        return original(input, rest);
      }
      return original(input, options);
    };
  }, a.id);
  await page.goto("/admin");
  await page.getByLabel("Administrator password").fill(process.env.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in →" }).click();
  await page.getByRole("button", { name: "Teams", exact: true }).click();
  const hold = gate();
  await page.route(`**/api/admin/teams/${a.id}/history`, async route => { await hold.wait; await route.continue(); });
  const pending = page.waitForRequest(r => r.url().endsWith(`/api/admin/teams/${a.id}/history`));
  await page.locator("#admin-team").selectOption(a.id);
  await pending;
  await expect(page.locator("#admin-team-detail")).toContainText("Loading team decks");
  await page.locator("#admin-team").selectOption(b.id);
  await expect(page.locator("#admin-team-detail")).toContainText(b.name);
  const old = page.waitForResponse(r => r.url().endsWith(`/api/admin/teams/${a.id}/history`));
  hold.release();
  await (await old).finished();
  await page.evaluate(() => new Promise(requestAnimationFrame));
  await expect(page.locator("#admin-team-detail")).toContainText(b.name);
  await expect(page.locator("#admin-team-detail")).not.toContainText("Shorikai");
  await expect(page.locator("#admin-team-detail .empty strong").filter({ hasText: /^No deck submitted$/ })).toHaveCount(2);
});

test("event registration uses the visibly selected team even when another tab changes browser memory", async ({ page }) => {
  const { a, b } = await seed(page);
  const login = await page.request.post("/api/login", { data: { password: process.env.ADMIN_PASSWORD } });
  expect(login.status()).toBe(200);
  const { csrf } = await login.json();
  const headers = { "x-csrf-token": csrf };
  const created = await page.request.post("/api/admin/events", { headers, data: { name: "Association event " + Date.now(), starts_at: "2026-11-15T18:00:00-07:00", provider: "mock" } });
  expect(created.status()).toBe(201);
  const event = await created.json();
  const opened = await page.request.patch(`/api/admin/events/${event.id}`, { headers, data: { status: "registration" } });
  expect(opened.status()).toBe(200);
  await page.goto(`/events/${event.id}`);
  await page.locator("#event-team").selectOption(b.id);
  await expect(page.getByRole("button", { name: "Register this team →", exact: true })).toBeVisible();
  await page.evaluate(id => localStorage.setItem("cd-team", id), a.id);
  const register = page.waitForRequest(r => r.url().endsWith(`/api/events/${event.id}/register`));
  await page.getByRole("button", { name: "Register this team →", exact: true }).click();
  expect((await register).postDataJSON().team_id).toBe(b.id);
  await expect(page.locator("#event-team-info").getByText("Registered", { exact: true })).toBeVisible();
  await expect(page.locator("#event-team")).toHaveValue(b.id);
  const data = await (await page.request.get(`/api/events/${event.id}`)).json();
  expect(data.registrations).toHaveLength(1);
  expect(data.registrations[0].team_id).toBe(b.id);
  expect(data.registrations[0].decks).toEqual([]);
});
