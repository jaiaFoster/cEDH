import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
process.env.DATABASE_SCHEMA = "test_win_" + randomUUID().replaceAll("-", "");
process.env.ADMIN_PASSWORD = "win-loss-local-only";
process.env.SESSION_SECRET = "win-loss-session-only";
process.env.ALLOW_MOCK = "true";
const { pool, q, migrate } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
const {
  winningLosingSeed,
  winningLosingTopics,
  winningLosingUpdates,
  officialRulesSources,
} = await import("../rulings.mjs");
test("win/loss FAQ upgrades insert-only, public filtering and source metadata preserve organizer versions", async (t) => {
  await migrate();
  const newIDs = winningLosingSeed.map((r) => r.id);
  // Recreate the original version for five targeted updates (isolated test schema only).
  for (const update of winningLosingUpdates) {
    await q(
      "UPDATE ruling_entries SET published_version_id=(SELECT id FROM ruling_versions WHERE ruling_id=$1 AND revision=1) WHERE id=$1",
      [update.id],
    );
    await q("DELETE FROM ruling_versions WHERE ruling_id=$1 AND revision>1", [
      update.id,
    ]);
  }
  // One pending organizer draft and one hidden record must block automatic updates.
  await q(
    `INSERT INTO ruling_versions(id,ruling_id,revision,content,actor,change_note)
    SELECT $1,ruling_id,2,content || '{"answer":"Organizer draft — keep it."}'::jsonb,'admin','Organizer draft' FROM ruling_versions WHERE ruling_id='oracle-own-library' AND revision=1`,
    [randomUUID()],
  );
  await q("UPDATE ruling_entries SET hidden=true WHERE id='rip-helm'");
  const skipped = ["oracle-own-library", "rip-helm"];
  const eligible = winningLosingUpdates
    .map((r) => r.id)
    .filter((id) => !skipped.includes(id));
  // Recreate a real pre-upgrade schema: only original seed entries, including an organizer-hidden ruling.
  await q(
    "UPDATE ruling_entries SET published_version_id=NULL WHERE id=ANY($1)",
    [newIDs],
  );
  await q("DELETE FROM ruling_versions WHERE ruling_id=ANY($1)", [newIDs]);
  await q("DELETE FROM ruling_entries WHERE id=ANY($1)", [newIDs]);
  await q("UPDATE ruling_entries SET hidden=true WHERE id='shared-resources'");
  // Persist historical sentinel rows, not just empty tables, before the upgrade.
  const team = randomUUID(),
    deck = randomUUID(),
    event = randomUUID(),
    registration = randomUUID();
  const price = (await q("SELECT id,prices FROM price_versions LIMIT 1"))
    .rows[0];
  await q(
    "INSERT INTO teams(id,name,name_key,players) VALUES($1,'History preservation fixture','history-preservation','[\"A\",\"B\"]')",
    [team],
  );
  await q(
    "INSERT INTO deck_versions(id,team_id,slot,source_text,deck,score,price_version_id,actor) VALUES($1,$2,1,'Retained historical source','{}','{\"total\":42}',$3,'test fixture')",
    [deck, team, price.id],
  );
  await q(
    "INSERT INTO events(id,name,starts_at,status,price_version_id,price_snapshot,provider,champion) VALUES($1,'Retained completed event',now(),'complete',$2,$3,'mock','History preservation fixture')",
    [event, price.id, price.prices],
  );
  await q(
    "INSERT INTO registrations(id,event_id,team_id,team_name,score) VALUES($1,$2,$3,'History preservation fixture','{\"total\":42}')",
    [registration, event, team],
  );
  await q(
    "INSERT INTO registration_versions(id,registration_id,decks,score,actor) VALUES($1,$2,'[]','{\"total\":42}','test fixture')",
    [randomUUID(), registration],
  );
  const retainedTables = [
    "teams",
    "deck_versions",
    "events",
    "registrations",
    "registration_versions",
  ];
  const historical = new Map();
  for (const table of retainedTables)
    historical.set(table, (await q(`SELECT * FROM ${table} ORDER BY id`)).rows);
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
        [[...newIDs, ...eligible]],
      )
    ).rows,
    originalEntries.filter((r) => !eligible.includes(r.id)),
  );
  assert.deepEqual(
    (
      await q(
        "SELECT * FROM ruling_versions WHERE NOT(ruling_id=ANY($1)) AND (NOT(ruling_id=ANY($2)) OR revision=1) ORDER BY id",
        [newIDs, eligible],
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
  for (const table of retainedTables)
    assert.deepEqual(
      (await q(`SELECT * FROM ${table} ORDER BY id`)).rows,
      historical.get(table),
      table + " unchanged",
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
      "public collection covers 32 topics with reused answers and six groups",
      async () => {
        const response = await get("/api/rulings?collection=winning-losing");
        assert.equal(response.total, 26); // rip-helm was deliberately hidden above
        assert.equal(response.winning_losing.topic_count, 32);
        assert.equal(response.winning_losing.groups.length, 6);
        assert.equal(
          new Set(response.rulings.map((r) => r.id)).size,
          response.total,
        );
        assert.deepEqual(response.official_sources, officialRulesSources);
        const mill = await get("/api/rulings/win-loss-mill");
        assert.ok(mill.rule_references.includes("704.5b"));
        assert.ok(mill.example.includes("30"));
        assert.equal(mill.verified_on, "2026-11-02");
        assert.equal(mill.rules_edition, "September 25, 2026");
        const byRef = await get(
          "/api/rulings?q=" + encodeURIComponent("CR 104.3c"),
        );
        assert.ok(byRef.rulings.some((r) => r.id === "win-loss-mill"));
        const filtered = await get(
          "/api/rulings?collection=winning-losing" +
            "&classification=" +
            encodeURIComponent("Doesn’t Work") +
            "&q=Oracle",
        );
        assert.equal(filtered.total, 1);
        assert.deepEqual(filtered.rulings.map((r) => r.id).sort(), [
          "oracle-own-library",
        ]);
        assert.deepEqual(
          (await get("/api/home")).officialRulesSources,
          officialRulesSources,
        );
        await get("/api/rulings/shared-resources", 404);
        await get("/api/rulings/commander-aggregation", 404);
        const byGroup = await get(
          "/api/rulings?collection=winning-losing&group=" +
            encodeURIComponent("Commander damage and poison"),
        );
        assert.ok(
          byGroup.rulings.every((r) =>
            r.winning_losing_groups.includes("Commander damage and poison"),
          ),
        );
        assert.ok(byGroup.rulings.some((r) => r.id === "commander-poison"));
        await get("/api/rulings?group=unknown", 400);
        await get("/api/rulings?collection=unknown", 400);
        for (const topic of winningLosingTopics.topics) {
          const search = await get(
            "/api/rulings?collection=winning-losing&q=" +
              encodeURIComponent(topic.question),
          );
          const expected = topic.ruling_ids.filter((id) => id !== "rip-helm");
          for (const id of expected)
            assert.ok(
              search.rulings.some((r) => r.id === id),
              topic.question,
            );
        }
        const changed = (
          await q(
            "SELECT * FROM ruling_versions WHERE ruling_id=ANY($1) AND revision=2",
            [eligible],
          )
        ).rows;
        assert.equal(changed.length, 3);
        assert.ok(changed.every((r) => r.actor === "research seed update"));
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
