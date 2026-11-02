import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
process.env.DATABASE_SCHEMA = "test_win_" + randomUUID().replaceAll("-", "");
process.env.ADMIN_PASSWORD = "win-loss-local-only";
process.env.SESSION_SECRET = "win-loss-session-only";
process.env.ALLOW_MOCK = "true";
const { pool, q, migrate } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
const { winningLosingSeed, officialRulesSources } = await import(
  "../rulings.mjs"
);
test("win/loss FAQ upgrades insert-only, public filtering and source metadata preserve organizer versions", async (t) => {
  await migrate();
  const newIDs = winningLosingSeed.map((r) => r.id);
  // Recreate a real pre-upgrade schema: only original seed entries, including an organizer-hidden ruling.
  await q(
    "UPDATE ruling_entries SET published_version_id=NULL WHERE id=ANY($1)",
    [newIDs],
  );
  await q("DELETE FROM ruling_versions WHERE ruling_id=ANY($1)", [newIDs]);
  await q("DELETE FROM ruling_entries WHERE id=ANY($1)", [newIDs]);
  await q("UPDATE ruling_entries SET hidden=true WHERE id='shared-resources'");
  const originalEntries = (await q("SELECT * FROM ruling_entries ORDER BY id"))
      .rows,
    originalVersions = (await q("SELECT * FROM ruling_versions ORDER BY id"))
      .rows;
  const prices = (await q("SELECT * FROM price_versions ORDER BY id")).rows,
    rules = (await q("SELECT * FROM rules_versions ORDER BY id")).rows;
  await migrate();
  await migrate();
  assert.deepEqual(
    (
      await q(
        "SELECT * FROM ruling_entries WHERE NOT(id=ANY($1)) ORDER BY id",
        [newIDs],
      )
    ).rows,
    originalEntries,
  );
  assert.deepEqual(
    (
      await q(
        "SELECT * FROM ruling_versions WHERE NOT(ruling_id=ANY($1)) ORDER BY id",
        [newIDs],
      )
    ).rows,
    originalVersions,
  );
  assert.deepEqual(
    (await q("SELECT * FROM price_versions ORDER BY id")).rows,
    prices,
  );
  assert.deepEqual(
    (await q("SELECT * FROM rules_versions ORDER BY id")).rows,
    rules,
  );
  const server = createApp().listen(0, "127.0.0.1");
  await new Promise((r) => server.on("listening", r));
  const base = "http://127.0.0.1:" + server.address().port;
  async function get(path, status = 200) {
    const r = await fetch(base + path);
    const data = await r.json();
    assert.equal(r.status, status, JSON.stringify(data));
    return data;
  }
  try {
    await t.test(
      "public category contains 32 summaries with examples, references, dates and current-source access",
      async () => {
        const response = await get(
          "/api/rulings?category=" + encodeURIComponent("Winning & Losing"),
        );
        assert.equal(response.total, 32);
        assert.deepEqual(response.official_sources, officialRulesSources);
        const mill = await get("/api/rulings/win-loss-mill");
        assert.ok(mill.rule_references.includes("704.5b"));
        assert.ok(mill.example.includes("12"));
        assert.equal(mill.verified_on, "2026-11-02");
        assert.equal(mill.rules_edition, "September 25, 2026");
        const byRef = await get(
          "/api/rulings?q=" + encodeURIComponent("CR 104.3c"),
        );
        assert.ok(byRef.rulings.some((r) => r.id === "win-loss-mill"));
        const filtered = await get(
          "/api/rulings?category=" +
            encodeURIComponent("Winning & Losing") +
            "&classification=" +
            encodeURIComponent("Doesn’t Work") +
            "&q=Oracle",
        );
        assert.equal(filtered.total, 2);
        assert.deepEqual(filtered.rulings.map((r) => r.id).sort(), [
          "win-loss-opponent-wins",
          "win-loss-oracle",
        ]);
        assert.deepEqual(
          (await get("/api/home")).officialRulesSources,
          officialRulesSources,
        );
        await get("/api/rulings/shared-resources", 404);
        await get("/api/rulings/commander-aggregation", 404);
      },
    );
    await t.test(
      "new FAQ entries retain protected admin review, drafts, immutable history and seed safety",
      async () => {
        const denied = await fetch(base + "/api/admin/rulings");
        assert.equal(denied.status, 401);
        const login = await fetch(base + "/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: process.env.ADMIN_PASSWORD }),
        });
        const session = await login.json();
        const headers = {
          "Content-Type": "application/json",
          cookie: login.headers.get("set-cookie").split(";")[0],
          "x-csrf-token": session.csrf,
        };
        async function admin(path, body) {
          const r = await fetch(base + path, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
          });
          const data = await r.json();
          assert.equal(r.status, 200, JSON.stringify(data));
          return data;
        }
        const prior = await get("/api/rulings/win-loss-mill");
        const content = {
          ...prior,
          answer: "Organizer-reviewed empty-library example.",
          change_note: "Verify draft preservation in isolated tests.",
        };
        const draft = await admin("/api/admin/rulings/win-loss-mill/drafts", {
          content,
          base_version_id: prior.version_id,
        });
        assert.equal(
          (await get("/api/rulings/win-loss-mill")).answer,
          prior.answer,
        );
        await admin("/api/admin/rulings/win-loss-mill/publish", {
          version_id: draft.id,
        });
        assert.equal(
          (await get("/api/rulings/win-loss-mill")).answer,
          content.answer,
        );
        await admin("/api/admin/rulings/win-loss-mill/hide", {
          reason: "Seed safety regression.",
        });
        await migrate();
        await get("/api/rulings/win-loss-mill", 404);
        const count = (
          await q(
            "SELECT count(*)::int n FROM ruling_versions WHERE ruling_id='win-loss-mill'",
          )
        ).rows[0].n;
        assert.equal(count, 2);
      },
    );
  } finally {
    await new Promise((r) => server.close(r));
    await q("DROP SCHEMA " + process.env.DATABASE_SCHEMA + " CASCADE");
    await pool.end();
  }
});
