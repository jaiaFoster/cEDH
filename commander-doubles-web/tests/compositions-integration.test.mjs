import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
process.env.DATABASE_SCHEMA = "test_comp_" + randomUUID().replaceAll("-", "");
process.env.ADMIN_PASSWORD = "composition-test-only";
process.env.SESSION_SECRET = "composition-test-session";
process.env.ALLOW_MOCK = "true";
const { pool, q, migrate } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
test("composition PostgreSQL publication, live prices, private drafts and safe migrations", async (t) => {
  await migrate();
  const initial = (await q("SELECT * FROM composition_versions ORDER BY id"))
    .rows;
  const prices = (await q("SELECT * FROM price_versions ORDER BY id")).rows;
  const rules = (await q("SELECT * FROM rules_versions ORDER BY id")).rows;
  await migrate();
  assert.deepEqual(
    (await q("SELECT * FROM composition_versions ORDER BY id")).rows,
    initial,
  );
  assert.equal(initial.length, 102);
  const server = createApp().listen(0, "127.0.0.1");
  await new Promise((r) => server.on("listening", r));
  const base = "http://127.0.0.1:" + server.address().port;
  let headers = {};
  async function call(path, method = "GET", body, status = 200, auth = false) {
    const r = await fetch(base + path, {
      method,
      headers: { "Content-Type": "application/json", ...(auth ? headers : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const v = await r.json();
    assert.equal(r.status, status, JSON.stringify(v));
    return v;
  }
  try {
    await t.test(
      "public list, pagination, live prices and private research boundaries",
      async () => {
        const x = await call("/api/compositions?limit=100");
        assert.equal(x.total, 88);
        assert.equal(x.published_total, 88);
        assert.equal(x.compositions[0].id, "seed-10");
        assert.equal(
          x.compositions.find((p) => p.id === "benchmark-a").full_team_score
            .points,
          462,
        );
        await call("/api/compositions/review-01", "GET", null, 404);
        await call("/api/admin/compositions", "GET", null, 401);
        const first = await call("/api/compositions?sort=points_desc&limit=24");
        const next = await call(
          "/api/compositions?sort=points_desc&limit=24&offset=24&version=" +
            first.price_version.id,
        );
        const all = await call("/api/compositions?sort=points_desc&limit=100");
        assert.deepEqual(
          [...first.compositions, ...next.compositions].map((p) => p.id),
          all.compositions.slice(0, 48).map((p) => p.id),
        );
        const r = await fetch(base + "/api/compositions/benchmark-a/decks/A1");
        assert.equal(r.status, 200);
        assert.match(await r.text(), /Tymna the Weaver/);
        assert.equal(
          (await fetch(base + "/api/compositions/seed-10/decks/A1")).status,
          404,
        );
      },
    );
    await t.test(
      "organizer drafts, stale writes, explicit verification, publish, hide and restore preserve originals",
      async () => {
        const login = await fetch(base + "/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: process.env.ADMIN_PASSWORD }),
        });
        const session = await login.json();
        headers = {
          cookie: login.headers.get("set-cookie").split(";")[0],
          "x-csrf-token": session.csrf,
        };
        const state = await call(
          "/api/admin/compositions",
          "GET",
          null,
          200,
          true,
        );
        assert.equal(state.compositions.length, 102);
        const old = state.compositions.find((c) => c.id === "seed-10");
        const content = {
          ...old.content,
          hook: "Organizer-edited Belbe profile.",
          change_note: "Fixture edit",
          verification_status: "needs_review",
        };
        const draft = await call(
          "/api/admin/compositions/seed-10/drafts",
          "POST",
          { content, base_version_id: old.latest_version_id },
          200,
          true,
        );
        assert.notEqual(
          (await call("/api/compositions/seed-10")).hook,
          content.hook,
        );
        await call(
          "/api/admin/compositions/seed-10/drafts",
          "POST",
          { content, base_version_id: old.latest_version_id },
          409,
          true,
        );
        await call(
          "/api/admin/compositions/seed-10/publish",
          "POST",
          { version_id: draft.id },
          400,
          true,
        );
        content.verification_status = "verified";
        const verified = await call(
          "/api/admin/compositions/seed-10/drafts",
          "POST",
          { content, base_version_id: draft.id },
          200,
          true,
        );
        await call(
          "/api/admin/compositions/seed-10/publish",
          "POST",
          { version_id: verified.id },
          200,
          true,
        );
        assert.equal(
          (await call("/api/compositions/seed-10")).hook,
          content.hook,
        );
        await migrate();
        assert.equal(
          (await call("/api/compositions/seed-10")).hook,
          content.hook,
        );
        await call(
          "/api/admin/compositions/seed-10/hide",
          "POST",
          { reason: "Fixture hide" },
          200,
          true,
        );
        await migrate();
        await call("/api/compositions/seed-10", "GET", null, 404);
        const restored = await call(
          "/api/admin/compositions/seed-10/restore",
          "POST",
          { version_id: old.latest_version_id, reason: "Historical recovery" },
          200,
          true,
        );
        assert.equal(restored.content.verification_status, "needs_review");
        await call(
          "/api/admin/compositions/seed-10/publish",
          "POST",
          { version_id: restored.id },
          400,
          true,
        );
        const history = await call(
          "/api/admin/compositions/seed-10/history",
          "GET",
          null,
          200,
          true,
        );
        assert.equal(history.length, 4);
        assert.equal(history.at(-1).content.hook, old.content.hook);
        const duplicate = {
          ...old.content,
          id: "duplicate-pair",
          change_note: "Duplicate test",
        };
        await call(
          "/api/admin/compositions",
          "POST",
          { content: duplicate },
          409,
          true,
        );
        const sol = await call(
          "/api/admin/compositions/card?name=Sol%20Ring",
          "GET",
          null,
          200,
          true,
        );
        assert.equal(sol.name, "Sol Ring");
      },
    );
    await t.test(
      "new compositions enter privately and cannot publish without evidence review",
      async () => {
        const state = await call(
          "/api/admin/compositions",
          "GET",
          null,
          200,
          true,
        );
        const cards = Object.values(state.cards);
        const a = cards.find((c) => c.name === "Lavinia, Azorius Renegade"),
          b = cards.find((c) => c.name === "Talion, the Kindly Lord");
        const original = state.compositions.find(
          (c) => c.id === "seed-10",
        ).content;
        const content = {
          ...original,
          id: "new-control-concept",
          player_a: [a.oracle_id],
          player_b: [b.oracle_id],
          key_cards: [],
          decklists: [],
          verification_status: "needs_review",
          research_status: "Research candidate",
          verified_on: "",
          verified_by: "",
          change_note: "New unpublished research fixture",
          oracle_evidence: [a, b].map((c) => ({
            oracle_id: c.oracle_id,
            quote: c.oracle_text,
            source_url: c.scryfall_url,
          })),
        };
        const draft = await call(
          "/api/admin/compositions",
          "POST",
          { content },
          201,
          true,
        );
        await call("/api/compositions/new-control-concept", "GET", null, 404);
        await call(
          "/api/admin/compositions/new-control-concept/publish",
          "POST",
          { version_id: draft.id },
          400,
          true,
        );
      },
    );
    await t.test(
      "current published CZ prices change without changing historical scores or old versions",
      async () => {
        const current = (await call("/api/compositions?limit=1")).price_version;
        const draft = await call(
          "/api/admin/prices",
          "POST",
          {
            name: "Composition test price",
            base_version_id: current.id,
            changes: [
              { name: "Najeela, the Blade-Blossom", main: 0, command: 31 },
            ],
          },
          201,
          true,
        );
        await call(
          "/api/admin/prices/" + draft.id + "/publish",
          "POST",
          {},
          200,
          true,
        );
        const x = await call("/api/compositions/benchmark-b");
        assert.equal(x.command_zone_points.a, 31);
        assert.equal(x.decklists[0].historical_team_points, 518);
        const old = await call(
          "/api/compositions/benchmark-b?version=" + current.id,
        );
        assert.notEqual(old.command_zone_points.a, 31);
        const backup = await call("/api/admin/export", "GET", null, 200, true);
        assert.equal(backup.composition_entries.length, 103);
        assert.ok(backup.composition_versions.length > 102);
      },
    );
    assert.deepEqual(
      (await q("SELECT * FROM rules_versions ORDER BY id")).rows,
      rules,
    );
    assert.deepEqual(
      (
        await q("SELECT * FROM price_versions WHERE id=ANY($1) ORDER BY id", [
          prices.map((p) => p.id),
        ])
      ).rows,
      prices,
    );
    assert.equal((await q("SELECT count(*)::int n FROM teams")).rows[0].n, 0);
    assert.equal((await q("SELECT count(*)::int n FROM events")).rows[0].n, 0);
  } finally {
    await new Promise((r) => server.close(r));
    await q("DROP SCHEMA " + process.env.DATABASE_SCHEMA + " CASCADE");
    await pool.end();
  }
});
