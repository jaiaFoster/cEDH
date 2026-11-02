import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
process.env.DATABASE_SCHEMA = "test_print_" + randomUUID().replaceAll("-", "");
process.env.ADMIN_PASSWORD = "printing-integration-only";
process.env.SESSION_SECRET = "printing-session-only";
process.env.ALLOW_MOCK = "true";
const { pool, migrate, q } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
const text =
  "COMMANDER\n1 Kenrith, the Returned King\nDECK\n98 Island\n1 Biblioteca silvana";
test("PostgreSQL pending references, consolidated review, preservation and isolation", async (t) => {
  await migrate();
  await migrate();
  let hits = 0;
  const server = createApp({
    moxfieldOptions: {
      fetcher: async () => {
        hits++;
        return { ok: false, status: 403 };
      },
    },
  }).listen(0, "127.0.0.1");
  await new Promise((r) => server.on("listening", r));
  const base = "http://127.0.0.1:" + server.address().port;
  let authHeaders = {};
  async function call(path, method = "GET", body, status = 200) {
    const r = await fetch(base + path, {
      method,
      headers: { "Content-Type": "application/json", ...authHeaders },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const data = await r.json();
    assert.equal(r.status, status, JSON.stringify(data));
    return data;
  }
  const create = (name) =>
    call("/api/teams", "POST", { name, players: ["One", "Two"] }, 201);
  try {
    const team = await create("Printing " + randomUUID()),
      other = await create("Other " + randomUUID());
    const path = `/api/teams/${team.id}/decks/1`;
    const saved = await call(path, "POST", { text }, 201);
    assert.equal(saved.score.points, 7);
    assert.equal(saved.state, "imported");
    assert.equal(saved.deck.cards.at(-1).submitted_name, "Biblioteca silvana");
    const old = await q("SELECT * FROM deck_versions WHERE id=$1", [saved.id]);
    await t.test(
      "blocked link saves a normalized reference, not a zero-point deck, and survives restart",
      async () => {
        const ref = await call(
          path,
          "POST",
          { link: "moxfield.com/decks/blockedref/primer?x=y" },
          201,
        );
        assert.equal(ref.state, "awaiting_decklist");
        assert.equal(ref.score, null);
        assert.equal(
          ref.import.source_url,
          "https://moxfield.com/decks/blockedref",
        );
        const details = await call("/api/teams/" + team.id);
        assert.equal(details.decks.length, 1);
        assert.equal(details.decks[0].id, saved.id);
        assert.equal(details.imports[0].state, "awaiting_decklist");
        assert.equal(details.team_score.checked, false);
        assert.equal(details.team_score.points, undefined);
        assert.equal((await call("/api/teams/" + other.id)).imports.length, 0);
        await call(
          path,
          "POST",
          { link: "https://moxfield.com/decks/blockedref" },
          201,
        );
        assert.equal(hits, 1, "cooldown prevents repeated refusal requests");
        const second = createApp().listen(0, "127.0.0.1");
        await new Promise((r) => second.on("listening", r));
        try {
          const r = await fetch(
            "http://127.0.0.1:" +
              second.address().port +
              "/api/teams/" +
              team.id,
          );
          assert.equal((await r.json()).imports[0].state, "awaiting_decklist");
        } finally {
          await new Promise((r) => second.close(r));
        }
      },
    );
    let event, frozen;
    await t.test(
      "pending reference cannot masquerade as the previous deck in an actual event",
      async () => {
        const login = await fetch(base + "/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: process.env.ADMIN_PASSWORD }),
        });
        const session = await login.json();
        authHeaders = {
          cookie: login.headers.get("set-cookie").split(";")[0],
          "x-csrf-token": session.csrf,
        };
        event = await call(
          "/api/admin/events",
          "POST",
          {
            name: "Pending import event",
            starts_at: "2026-12-01T18:00:00-07:00",
            provider: "mock",
          },
          201,
        );
        await call(`/api/teams/${team.id}/decks/2`, "POST", { text }, 201);
        await call(
          `/api/events/${event.id}/register`,
          "POST",
          { team_id: team.id },
          201,
        );
        const reg = (await call(`/api/events/${event.id}`)).registrations[0];
        assert.equal(reg.decks.length, 1);
        assert.equal(reg.decks[0].slot, 2);
        assert.equal(reg.score.checked, false);
        assert.equal(reg.score.within, false);
        frozen = structuredClone(reg);
      },
    );
    await t.test(
      "paste fallback preserves source and previous raw history",
      async () => {
        const result = await call(path, "POST", { text }, 201);
        assert.equal(result.state, "imported");
        assert.equal(result.score.points, 7);
        const current = await call("/api/teams/" + team.id);
        assert.deepEqual(
          (await call(`/api/events/${event.id}`)).registrations[0],
          frozen,
        );
        assert.equal(
          current.decks[0].source_url,
          "https://moxfield.com/decks/blockedref",
        );
        assert.equal(current.imports[0].state, "imported");
        assert.deepEqual(
          (await q("SELECT * FROM deck_versions WHERE id=$1", [saved.id]))
            .rows[0],
          old.rows[0],
        );
      },
    );
    let review;
    await t.test(
      "all uncertain names preserved together, no deck written until confirmed",
      async () => {
        const before = (await call("/api/teams/" + team.id)).decks[0].id;
        review = await call(
          path,
          "POST",
          {
            text: "COMMANDER\n1 Kenrith, the Returned King\nDECK\n97 Island\n1 Completely Unknown Fixture\n1 Another Unknown Fixture",
          },
          422,
        );
        assert.equal(review.issues.length, 2);
        assert.ok(review.review_id);
        assert.equal((await call("/api/teams/" + team.id)).decks[0].id, before);
        await call(
          `/api/teams/${other.id}/decks/1`,
          "POST",
          { review_id: review.review_id, choices: { 2: "Sylvan Library" } },
          404,
        );
        const confirmed = await call(
          path,
          "POST",
          {
            review_id: review.review_id,
            choices: { 2: "Sylvan Library", 3: "Sol Ring" },
          },
          201,
        );
        assert.equal(confirmed.score.points, 22);
        assert.equal(confirmed.score.count, 100);
        assert.equal(
          confirmed.deck.cards[2].submitted_name,
          "Completely Unknown Fixture",
        );
        assert.equal(confirmed.deck.cards[2].match_method, "confirmed");
        const reload = await call("/api/teams/" + team.id);
        assert.equal(reload.decks[0].current_score.points, 22);
        assert.equal(
          reload.decks[0].current_deck.cards[2].submitted_name,
          "Completely Unknown Fixture",
        );
        await call(
          path,
          "POST",
          {
            review_id: review.review_id,
            choices: { 2: "Sylvan Library", 3: "Sol Ring" },
          },
          409,
        );
      },
    );
    await t.test(
      "actual ambiguous Portuguese printing requires a whitelisted choice",
      async () => {
        const review = await call(
          path,
          "POST",
          {
            text: "COMMANDER\n1 Kenrith, the Returned King\nDECK\n98 Island\n1 Abafar",
          },
          422,
        );
        assert.deepEqual(
          review.issues[0].candidates.map((c) => c.name),
          ["Douse", "Swelter"],
        );
        await call(
          path,
          "POST",
          { review_id: review.review_id, choices: { 2: "Sol Ring" } },
          400,
        );
        const chosen = await call(
          path,
          "POST",
          { review_id: review.review_id, choices: { 2: "Douse" } },
          201,
        );
        assert.equal(chosen.deck.cards[2].name, "Douse");
        assert.equal(chosen.deck.cards[2].submitted_name, "Abafar");
        assert.equal(chosen.score.legal, true);
      },
    );
    await t.test(
      "cancel pending reference restores use of the last saved inventory, never deletes history",
      async () => {
        await call(
          path,
          "POST",
          { link: "https://moxfield.com/decks/cancelref" },
          201,
        );
        await call(path + "/cancel-import", "POST", {});
        assert.equal(
          (await call("/api/teams/" + team.id)).imports[0].state,
          "cancelled",
        );
        await call(
          path,
          "POST",
          { link: "https://evil.test/decks/abcdef" },
          400,
        );
        assert.equal(
          (await call("/api/teams/" + team.id)).imports[0].state,
          "cancelled",
        );
      },
    );
  } finally {
    await new Promise((r) => server.close(r));
    await q("DROP SCHEMA " + process.env.DATABASE_SCHEMA + " CASCADE");
    await pool.end();
  }
});
