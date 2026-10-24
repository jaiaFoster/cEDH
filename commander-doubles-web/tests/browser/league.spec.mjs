import { test, expect } from "@playwright/test";
const text =
  "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Sol Ring";
const stamp = Date.now().toString(36),
  names = Array.from(
    { length: 4 },
    (_, i) => "Browser " + stamp + " · Team " + (i + 1),
  );
let firstId, secondId;
test("complete multi-tournament browser lifecycle on the actual application", async ({
  page,
  browser,
  baseURL,
}) => {
  await test.step("admin login and create event through actual interface", async () => {
    await page.goto("/admin");
    await page
      .getByLabel("Administrator password")
      .fill(process.env.ADMIN_PASSWORD);
    await page.getByRole("button", { name: "Sign in →" }).click();
    await expect(
      page.getByRole("heading", { name: "Keep things moving." }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Events", exact: true }).click();
    await page
      .getByLabel("Event name", { exact: true })
      .fill("Browser acceptance " + stamp + " · First");
    await page.getByLabel("Start time").fill("2026-11-08T18:00");
    await page.getByLabel("Tournament provider").selectOption("mock");
    await page.getByRole("button", { name: "Create event →" }).click();
    await expect(
      page.getByRole("button", { name: "Open registration", exact: true }),
    ).toBeVisible();
    firstId = await page.locator("#admin-event").inputValue();
    await page
      .getByRole("button", { name: "Open registration", exact: true })
      .click();
    await expect(
      page
        .locator("#event-editor > .actions > .tag")
        .filter({ hasText: /^registration$/ }),
    ).toBeVisible();
  });
  const publicContext = await browser.newContext();
  const player = await publicContext.newPage();
  await test.step("four public teams, two scored export decks each, event registration", async () => {
    for (const name of names) {
      await player.goto(baseURL + "/teams");
      await player.getByLabel("Unique team name").fill(name);
      await player.getByRole("button", { name: "Create team →" }).click();
      await expect(player.getByLabel("Team name", { exact: true })).toHaveValue(
        name,
      );
      for (const n of [1, 2]) {
        await player
          .getByLabel("Deck export", { exact: true })
          .nth(n - 1)
          .fill(text);
        await player
          .getByRole("button", { name: "Score & save player " + n })
          .click();
        await expect(
          player.getByRole("button", { name: "Score & save player " + n }),
        ).toBeEnabled();
        await expect(
          player.getByText("Deck scored and saved.", { exact: false }),
        ).toBeVisible();
      }
      await expect(player.getByText("Team total")).toContainText("38 / 120");
      await player.goto(baseURL + "/events/" + firstId);
      await player
        .getByRole("button", { name: "Register this team →" })
        .click();
      await expect(
        player
          .locator("#event-team-info")
          .getByText("Registered", { exact: true }),
      ).toBeVisible();
    }
  });
  await test.step("close, lock, publish participants twice, and start", async () => {
    await page
      .getByRole("button", { name: "Force refresh", exact: true })
      .count()
      .then(async (n) => {
        if (n)
          await page
            .getByRole("button", { name: "Force refresh", exact: true })
            .click();
      });
    await page.reload();
    await page.getByRole("button", { name: "Events", exact: true }).click();
    await page.getByLabel("Choose an event to manage").selectOption(firstId);
    await page
      .getByRole("button", { name: "Close registration", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Lock submissions", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Create tournament", exact: true })
      .click();
    await expect(
      page.getByRole("button", {
        name: "Publish registered teams",
        exact: true,
      }),
    ).toBeVisible();
    for (let i = 0; i < 2; i++) {
      await page
        .getByRole("button", { name: "Publish registered teams", exact: true })
        .click();
      await expect(
        page.getByRole("button", {
          name: "Publish registered teams",
          exact: true,
        }),
      ).toBeEnabled();
    }
    await page
      .getByRole("button", { name: "Start & lock tournament", exact: true })
      .click();
    await expect(
      page.locator("#event-editor").getByText("running", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: names[0] + " wins", exact: true }),
    ).toBeVisible();
  });
  await test.step("public next matches and locked submission state", async () => {
    await player.reload();
    await expect(
      player.getByText("These event decks are locked.", { exact: false }),
    ).toBeVisible();
    await expect(
      player.getByRole("heading", { name: "Pairings & next matches" }),
    ).toBeVisible();
    await expect(player.locator(".match").first()).toContainText(names[0]);
  });
  await test.step("play semifinals, verify final pair, complete final, archive champion", async () => {
    await page
      .getByRole("button", { name: names[0] + " wins", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: names[2] + " wins", exact: true }),
    ).toBeVisible();
    await page
      .getByRole("button", { name: names[2] + " wins", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: names[0] + " wins", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: names[1] + " wins", exact: true }),
    ).toHaveCount(0);
    await page
      .getByRole("button", { name: names[0] + " wins", exact: true })
      .click();
    await page
      .getByRole("button", {
        name: "Finalize completed tournament",
        exact: true,
      })
      .click();
    await expect(
      page.getByRole("heading", { name: "Archived · " + names[0] }),
    ).toBeVisible();
    await player.goto(baseURL + "/history");
    await expect(
      player.getByRole("heading", { name: names[0], exact: true }),
    ).toBeVisible();
  });
  let first;
  await test.step("create second event, reuse teams, preserve first archive", async () => {
    first = await (
      await player.request.get(baseURL + "/api/events/" + firstId)
    ).json();
    await page.getByLabel("Choose an event to manage").selectOption("");
    await page
      .getByLabel("Event name", { exact: true })
      .fill("Browser acceptance " + stamp + " · Second");
    await page.getByLabel("Start time").fill("2026-11-15T18:00");
    await page.getByLabel("Tournament provider").selectOption("mock");
    await page.getByRole("button", { name: "Create event →" }).click();
    await expect(
      page.getByRole("button", { name: "Open registration", exact: true }),
    ).toBeVisible();
    secondId = await page.locator("#admin-event").inputValue();
    await page
      .getByRole("button", { name: "Open registration", exact: true })
      .click();
    await player.goto(baseURL + "/events/" + secondId);
    await player.getByRole("button", { name: "Register this team →" }).click();
    await expect(
      player
        .locator("#event-team-info")
        .getByText("Registered", { exact: true }),
    ).toBeVisible();
    const after = await (
      await player.request.get(baseURL + "/api/events/" + firstId)
    ).json();
    expect(after).toEqual(first);
  });
  await test.step("public editing in another browser and browser selection persistence", async () => {
    const another = await browser.newContext(),
      p = await another.newPage();
    await p.goto(baseURL + "/teams");
    await p
      .getByLabel("Select a registered team")
      .selectOption({ label: names[3] });
    await expect(p.getByLabel("Team name", { exact: true })).toHaveValue(
      names[3],
    );
    await p.reload();
    await expect(p.getByLabel("Select a registered team")).toHaveValue(
      await p.evaluate(() => localStorage.getItem("cd-team")),
    );
    await another.close();
  });
  await test.step("admin logout denies subsequent admin page access", async () => {
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    await expect(page.getByLabel("Administrator password")).toBeVisible();
  });
  await publicContext.close();
});
test("mobile navigation, card search, keyboard access, and layout", async ({
  browser,
  baseURL,
}) => {
  const c = await browser.newContext({
      viewport: { width: 390, height: 844 },
      isMobile: true,
      hasTouch: true,
    }),
    p = await c.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto(baseURL + "/");
  await expect(
    p.getByRole("heading", { name: "Two decks. One winning team." }),
  ).toBeVisible();
  expect(
    await p.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await p.screenshot({ path: "reports/mobile-home.png", fullPage: true });
  await p.getByRole("link", { name: "Points", exact: true }).click();
  await p.getByLabel("Find a card").fill("Sol Ring");
  await expect(p.locator("tbody")).toContainText("Sol Ring");
  await expect(p.locator("tbody tr")).toHaveCount(1);
  expect(
    await p.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await p.keyboard.press("Tab");
  expect(errors).toEqual([]);
  await c.close();
});
test("admin pricing search, draft publish, rules preview, and audit UI", async ({
  page,
}) => {
  await page.goto("/admin");
  await page
    .getByLabel("Administrator password")
    .fill(process.env.ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in →" }).click();
  await expect(
    page.getByRole("heading", { name: "Keep things moving." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Prices", exact: true }).click();
  await page.getByLabel("Search complete catalog").fill("Acererak");
  await page.getByRole("button", { name: /^Acererak the Archlich ·/ }).click();
  await page.getByLabel("Main-deck points").fill("1");
  await page.getByLabel("Version name").fill("Browser price draft " + stamp);
  await page.getByRole("button", { name: "Save draft →" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Browser price draft " + stamp + " draft",
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Publish this version", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("Price version published.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Content", exact: true }).click();
  await page
    .getByRole("button", { name: "Preview changes", exact: true })
    .click();
  await expect(page.locator("#rules-preview")).toContainText(
    "Commander Doubles",
  );
  await page.getByRole("button", { name: "Audit", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Recent audit trail" }),
  ).toBeVisible();
  await expect(
    page.getByText("prices.publish", { exact: true }).first(),
  ).toBeVisible();
});
