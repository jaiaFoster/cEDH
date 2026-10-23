import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import fs from "node:fs";
if (!process.env.DATABASE_URL)
  throw Error("Integration tests require a real disposable PostgreSQL schema");
process.env.DATABASE_SCHEMA = "test_" + randomUUID().replaceAll("-", "");
process.env.ALLOW_MOCK = "true";
process.env.ADMIN_PASSWORD = "integration-password";
process.env.SESSION_SECRET = "integration-session-secret";
const { pool, migrate, q } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
const text =
  "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Sol Ring";
await test("PostgreSQL application acceptance: tournament one through tournament two", async (t) => {
  await migrate();
  await migrate();
  const server = createApp().listen(0, "127.0.0.1");
  await new Promise((r) => server.on("listening", r));
  const base = "http://127.0.0.1:" + server.address().port;
  let cookie = "",
    csrf = "",
    event,
    second,
    teams = [],
    originalSnapshot,
    oldPrice,
    history;
  async function call(
    p,
    m = "GET",
    body,
    admin = false,
    expected = 200,
    extra = {},
  ) {
    const r = await fetch(base + p, {
      method: m,
      headers: {
        "Content-Type": "application/json",
        ...(admin ? { cookie, "x-csrf-token": csrf } : {}),
        ...extra,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const d = await r.json();
    assert.equal(r.status, expected, JSON.stringify(d));
    return { data: d, response: r };
  }
  const get = async (p) => (await call(p)).data;
  const post = async (p, b = {}, adm = false, status = 200) =>
    (await call(p, "POST", b, adm, status)).data;
  try {
    await t.test(
      "clean migrations initialize accepted v3 and no fake events",
      async () => {
        const h = await get("/api/home");
        assert.equal(h.events.length, 0);
        assert.equal(h.teams.length, 0);
        assert.ok(h.price.name.includes("v3"));
        oldPrice = h.price.id;
        assert.equal((await get("/health")).ok, true);
      },
    );
    await t.test(
      "server-side admin authorization, password, secure session lifecycle",
      async () => {
        await call("/api/admin/dashboard", "GET", undefined, false, 401);
        await post("/api/login", { password: "wrong" }, false, 401);
        const x = await call("/api/login", "POST", {
          password: "integration-password",
        });
        cookie = x.response.headers.get("set-cookie").split(";")[0];
        csrf = x.data.csrf;
        assert.match(x.response.headers.get("set-cookie"), /HttpOnly/);
        await call("/api/admin/events", "POST", {}, false, 401);
        await call(
          "/api/admin/rules",
          "POST",
          { title: "x", body: "x" },
          true,
          403,
          { "x-csrf-token": "wrong" },
        );
        await call("/api/teams", "POST", { name: "cross" }, false, 403, {
          Origin: "https://evil.example",
        });
      },
    );
    await t.test(
      "public catalog searches combine operators and filters against published prices",
      async () => {
        const url = (p) => "/api/points?" + new URLSearchParams(p);
        const sol = await get(url({ q: '!"Sol Ring"' }));
        assert.equal(sol.total, 1);
        assert.equal(sol.cards[0].main, 15);
        assert.equal(sol.cards[0].command, 0);
        assert.equal(sol.cards[0].commanderEligible, false);
        assert.equal(
          (
            await get(
              url({
                q: '!"Acererak the Archlich"',
                points: "zero",
                zone: "main",
              }),
            )
          ).total,
          1,
        );
        const multi = await get(
          url({
            q: 'id:wu t:artifact o:"draw a card" mv<=3 "Mind Stone"',
            points: "all",
            type: "artifact",
            mvMax: "3",
            legality: "legal",
          }),
        );
        assert.ok(multi.cards.some((c) => c.name === "Mind Stone"));
        assert.ok(
          multi.cards.every(
            (c) =>
              c.identity.every((x) => "WU".includes(x)) &&
              c.mv <= 3 &&
              c.typeLine.includes("Artifact") &&
              c.legal,
          ),
        );
        assert.equal(
          (
            await get(
              url({
                q: '!"Dryad Arbor"',
                identity: "g",
                identityMode: "exact",
                colorCount: "any",
              }),
            )
          ).cards[0].colors[0],
          "G",
        );
        assert.equal(
          (
            await get(
              url({ q: '!"Sol Ring"', zone: "command", points: "zero" }),
            )
          ).total,
          0,
        );
        const unknown = await get(url({ q: '!"unknown audit card 123456"' }));
        assert.equal(unknown.total, 0);
        assert.deepEqual(unknown.cards, []);
        const invalid = await call(
          url({ q: "set:lea" }),
          "GET",
          undefined,
          false,
          400,
        );
        assert.equal(invalid.data.code, "unsupported_query");
        await call(url({ q: 'o:"unclosed' }), "GET", undefined, false, 400);
        await call(url({ sort: "unsupported" }), "GET", undefined, false, 400);
        await call(url({ min: "9", max: "2" }), "GET", undefined, false, 400);
        await call("/api/points?q=one&q=two", "GET", undefined, false, 400);
        await call(url({ offset: "-1" }), "GET", undefined, false, 400);
      },
    );
    await t.test(
      "all catalog sorts apply before pagination and public search remains compatible with admin picking",
      async () => {
        const sorts = [
          "main_desc",
          "main_asc",
          "command_desc",
          "command_asc",
          "name_asc",
          "name_desc",
          "mv_asc",
          "mv_desc",
        ];
        for (const sort of sorts) {
          const url = (limit, offset = 0) =>
            "/api/points?" +
            new URLSearchParams({
              sort,
              pointed: "1",
              limit: String(limit),
              offset: String(offset),
            });
          const all = await get(url(100)),
            a = await get(url(50)),
            b = await get(url(50, 50));
          assert.equal(all.total, 549);
          assert.equal(a.version.id, oldPrice);
          assert.deepEqual([...a.cards, ...b.cards], all.cards, sort);
          assert.equal(new Set(all.cards.map((c) => c.oracle_id)).size, 100);
        }
        // Existing admin searches omit the pointed flag and expect numeric command prices.
        const picked = await get("/api/points?q=Acererak");
        assert.equal(picked.cards[0].name, "Acererak the Archlich");
        assert.equal(picked.cards[0].main, 0);
        assert.equal(picked.cards[0].command, 0);
      },
    );
    await t.test(
      "admin creates event with Phoenix schedule and opens registration",
      async () => {
        event = await post(
          "/api/admin/events",
          {
            name: "Acceptance · First tournament",
            starts_at: "2026-11-07T18:00:00-07:00",
            provider: "mock",
          },
          true,
          201,
        );
        assert.equal(event.timezone, "America/Phoenix");
        await call(
          "/api/admin/events/" + event.id,
          "PATCH",
          { status: "registration" },
          true,
        );
      },
    );
    await t.test(
      "four persistent teams with two decks each, complete scores and event registration",
      async () => {
        for (let i = 1; i <= 4; i++) {
          const team = await post(
            "/api/teams",
            {
              name: "Team " + i,
              players: ["Player " + i + " A", "Player " + i + " B"],
            },
            false,
            201,
          );
          teams.push(team);
          for (const slot of [1, 2]) {
            const d = await post(
              `/api/teams/${team.id}/decks/${slot}`,
              { text },
              false,
              201,
            );
            assert.equal(d.score.points, 19);
            assert.equal(d.score.legal, true);
          }
          await post(
            "/api/events/" + event.id + "/register",
            { team_id: team.id },
            false,
            201,
          );
        }
        const e = await get("/api/events/" + event.id);
        assert.equal(e.registrations.length, 4);
        assert.ok(
          e.registrations.every((r) => r.score.points === 38 && r.score.within),
        );
      },
    );
    await t.test(
      "duplicate team names and duplicate registration cannot be created",
      async () => {
        await post("/api/teams", { name: "  TEAM 1  " }, false, 409);
        await post(
          "/api/events/" + event.id + "/register",
          { team_id: teams[0].id },
          false,
          409,
        );
      },
    );
    await t.test(
      "malformed and unknown decks fail with no zero-score save",
      async () => {
        await post(
          `/api/teams/${teams[0].id}/decks/1`,
          { text: "99 Island" },
          false,
          400,
        );
        await post(
          "/api/score",
          { decks: [{ text: "Commander\n1 Fake Card\nDeck\n99 Island" }] },
          false,
          400,
        );
        const before = (await get("/api/teams/" + teams[0].id)).decks.find(
          (d) => d.slot === 1,
        );
        assert.equal(before.score.points, 19);
      },
    );
    await t.test(
      "actual API flags over-budget legal deck, does not certify incomplete decks",
      async () => {
        const cards = [
          "Force of Will",
          "Mana Drain",
          "Cyclonic Rift",
          "Rhystic Study",
          "Mystic Remora",
          "Fierce Guardianship",
          "Force of Negation",
          "Sol Ring",
          "Time Warp",
          "Temporal Manipulation",
        ];
        const over =
          "Commander\n1 Shorikai, Genesis Engine\nDeck\n" +
          (99 - cards.length) +
          " Island\n" +
          cards.map((c) => "1 " + c).join("\n");
        const d = await post("/api/score", {
          decks: [{ text: over }, { text }],
        });
        assert.ok(d.decks[0].points > 72);
        assert.equal(d.team.within, false);
        const incomplete = await post("/api/score", {
          decks: [
            { text: "Commander\n1 Shorikai, Genesis Engine\nDeck\n98 Island" },
            { text },
          ],
        });
        assert.equal(incomplete.team.within, false);
      },
    );
    await t.test(
      "another unauthenticated browser may overwrite a general deck and admin can restore",
      async () => {
        const before = await get("/api/teams/" + teams[0].id);
        history = before.decks.find((d) => d.slot === 1).id;
        await post(
          `/api/teams/${teams[0].id}/decks/1`,
          { text: "Commander\n1 Shorikai, Genesis Engine\nDeck\n99 Island" },
          false,
          201,
        );
        assert.equal(
          (await get("/api/teams/" + teams[0].id)).decks.find(
            (d) => d.slot === 1,
          ).score.points,
          4,
        );
        await post("/api/admin/decks/" + history + "/restore", {}, true);
        assert.equal(
          (await get("/api/teams/" + teams[0].id)).decks.find(
            (d) => d.slot === 1,
          ).score.points,
          19,
        );
      },
    );
    await t.test(
      "draft pricing and publish do not affect frozen tournament scores",
      async () => {
        const draft = await post(
          "/api/admin/prices",
          {
            name: "Acceptance next prices",
            changes: [{ name: "Sol Ring", main: 16, command: 0 }],
          },
          true,
          201,
        );
        assert.equal((await get("/api/home")).price.id, oldPrice);
        await call(
          "/api/points?version=" + draft.id,
          "GET",
          undefined,
          false,
          404,
        );
        await call(
          "/api/admin/prices/" + draft.id,
          "PATCH",
          { changes: [{ name: "Acererak the Archlich", main: 1, command: 0 }] },
          true,
        );
        await post("/api/admin/prices/" + draft.id + "/publish", {}, true);
        await call(
          "/api/admin/prices/" + draft.id,
          "PATCH",
          { changes: [] },
          true,
          404,
        );
        assert.notEqual((await get("/api/home")).price.id, oldPrice);
        const query = encodeURIComponent('!"Sol Ring"');
        assert.equal((await get("/api/points?q=" + query)).cards[0].main, 16);
        assert.equal(
          (await get("/api/points?q=" + query + "&version=" + oldPrice))
            .cards[0].main,
          15,
        );
        assert.equal(
          (
            await get(
              "/api/points?q=" + encodeURIComponent('!"Acererak the Archlich"'),
            )
          ).cards[0].main,
          1,
        );
        assert.equal(
          (await get("/api/events/" + event.id)).registrations[0].score.points,
          38,
        );
        await post("/api/events/" + event.id + "/submission", {
          team_id: teams[0].id,
        });
        assert.equal(
          (await get("/api/events/" + event.id)).registrations[0].score.points,
          38,
        );
      },
    );
    await t.test(
      "draft and published rules have separate public states",
      async () => {
        const before = (await get("/api/home")).rules.body;
        const r = await post(
          "/api/admin/rules",
          { title: "Acceptance rules", body: before + "\nAcceptance test." },
          true,
          201,
        );
        assert.equal((await get("/api/home")).rules.body, before);
        await post("/api/admin/rules/" + r.id + "/publish", {}, true);
        assert.ok(
          (await get("/api/home")).rules.body.includes("Acceptance test."),
        );
      },
    );
    await t.test(
      "deadline locks submissions even before scheduled maintenance runs",
      async () => {
        await call(
          "/api/admin/events/" + event.id,
          "PATCH",
          { lock_at: "2020-01-01T00:00:00Z" },
          true,
        );
        await post(
          "/api/events/" + event.id + "/submission",
          { team_id: teams[0].id },
          false,
          423,
        );
        await call(
          "/api/admin/events/" + event.id,
          "PATCH",
          { lock_at: null },
          true,
        );
      },
    );
    await t.test(
      "close registration and freeze snapshots; general saved decks stay editable",
      async () => {
        await call(
          "/api/admin/events/" + event.id,
          "PATCH",
          { status: "scheduled" },
          true,
        );
        await post(
          "/api/admin/events/" + event.id + "/lock",
          { locked: true },
          true,
        );
        await post(
          "/api/events/" + event.id + "/submission",
          { team_id: teams[0].id },
          false,
          423,
        );
        const five = await post(
          "/api/teams",
          { name: "Fifth team" },
          false,
          201,
        );
        await post(
          "/api/events/" + event.id + "/register",
          { team_id: five.id },
          false,
          409,
        );
        await post(`/api/teams/${teams[0].id}/decks/1`, { text }, false, 201);
        originalSnapshot = (await get("/api/events/" + event.id)).registrations;
      },
    );
    await t.test(
      "publish participant mapping twice without duplicate remote participants",
      async () => {
        await post("/api/admin/events/" + event.id + "/tournament", {}, true);
        await post("/api/admin/events/" + event.id + "/participants", {}, true);
        await post("/api/admin/events/" + event.id + "/participants", {}, true);
        const e = await get("/api/events/" + event.id);
        assert.equal(
          new Set(e.registrations.map((r) => r.participant_id)).size,
          4,
        );
        const r = await q("SELECT state FROM mock_tournaments WHERE id=$1", [
          e.tournament_id,
        ]);
        assert.equal(r.rows[0].state.participants.length, 4);
      },
    );
    await t.test(
      "start tournament gets real provider pairings and rejects public edits",
      async () => {
        await post("/api/admin/events/" + event.id + "/start", {}, true);
        const e = await get("/api/events/" + event.id);
        assert.equal(e.status, "running");
        assert.equal(e.matches.filter((m) => m.state === "open").length, 2);
        assert.ok(e.matches[0].players.every(Boolean));
        await post(
          "/api/events/" + event.id + "/submission",
          { team_id: teams[0].id },
          false,
          423,
        );
      },
    );
    let semifinalWinners = [];
    await t.test(
      "two semifinals advance winners, excluding losing teams",
      async () => {
        let e = await get("/api/events/" + event.id);
        for (const m of e.matches.filter((m) => m.state === "open")) {
          const winner = m.players[0].id;
          semifinalWinners.push(winner);
          await post(
            "/api/admin/events/" + event.id + "/mock-result",
            {
              match_id: m.id,
              entries: m.players.map((p) => ({
                participant_id: p.id,
                score_set: p.id === winner ? "1" : "0",
                advancing: p.id === winner,
              })),
            },
            true,
          );
        }
        e = await get("/api/events/" + event.id);
        const final = e.matches.find((m) => m.round === 2);
        assert.equal(final.state, "open");
        assert.deepEqual(
          final.players.map((p) => p.id),
          semifinalWinners,
        );
      },
    );
    await t.test(
      "final and finalization archive champion and complete final standings",
      async () => {
        const e = await get("/api/events/" + event.id),
          m = e.matches.find((m) => m.state === "open");
        await post(
          "/api/admin/events/" + event.id + "/mock-result",
          {
            match_id: m.id,
            entries: m.players.map((p, i) => ({
              participant_id: p.id,
              score_set: i === 0 ? "1" : "0",
              advancing: i === 0,
            })),
          },
          true,
        );
        await post("/api/admin/events/" + event.id + "/finalize", {}, true);
        const done = await get("/api/events/" + event.id);
        assert.equal(done.status, "complete");
        assert.equal(done.champion, "Team 1");
        assert.equal(done.standings.length, 4);
        assert.deepEqual(
          done.registrations.map((r) => ({
            decks: r.decks,
            score: r.score,
            updated_at: r.updated_at,
          })),
          originalSnapshot.map((r) => ({
            decks: r.decks,
            score: r.score,
            updated_at: r.updated_at,
          })),
        );
      },
    );
    let firstArchive;
    await t.test(
      "second tournament reuses identities and preserves prior results and snapshots",
      async () => {
        firstArchive = await get("/api/events/" + event.id);
        second = await post(
          "/api/admin/events",
          {
            name: "Acceptance · Second tournament",
            starts_at: "2026-11-14T18:00:00-07:00",
            provider: "mock",
          },
          true,
          201,
        );
        await call(
          "/api/admin/events/" + second.id,
          "PATCH",
          { status: "registration" },
          true,
        );
        for (const t of teams)
          await post(
            "/api/events/" + second.id + "/register",
            { team_id: t.id },
            false,
            201,
          );
        await post("/api/admin/events/" + second.id + "/tournament", {}, true);
        await post(
          "/api/admin/events/" + second.id + "/participants",
          {},
          true,
        );
        await post("/api/admin/events/" + second.id + "/start", {}, true);
        assert.equal(
          (await get("/api/events/" + second.id)).matches.filter(
            (m) => m.state === "open",
          ).length,
          2,
        );
        assert.deepEqual(await get("/api/events/" + event.id), firstArchive);
      },
    );
    await t.test(
      "provider downtime preserves last synchronized pairings and records an error",
      async () => {
        const before = await get("/api/events/" + second.id);
        const record = (
          await q("SELECT * FROM mock_tournaments WHERE id=$1", [
            before.tournament_id,
          ])
        ).rows[0];
        await q("DELETE FROM mock_tournaments WHERE id=$1", [
          before.tournament_id,
        ]);
        await post("/api/admin/events/" + second.id + "/sync", {}, true, 400);
        const after = await get("/api/events/" + second.id);
        assert.deepEqual(after.sync_data, before.sync_data);
        assert.ok(after.sync_error.includes("missing"));
        await q("INSERT INTO mock_tournaments(id,state) VALUES($1,$2)", [
          record.id,
          JSON.stringify(record.state),
        ]);
        await post("/api/admin/events/" + second.id + "/sync", {}, true);
      },
    );
    await t.test(
      "event override and restore are audited and preserve submission versions",
      async () => {
        const e = await get("/api/events/" + second.id),
          r = e.registrations[0];
        await post(
          "/api/events/" + second.id + "/submission",
          { team_id: r.team_id, reason: "Acceptance correction" },
          true,
        );
        const versions = (
          await call(
            "/api/admin/registrations/" + r.id + "/history",
            "GET",
            undefined,
            true,
          )
        ).data;
        assert.ok(versions.length >= 2);
        await post(
          "/api/admin/registrations/" + r.id + "/restore",
          { version_id: versions.at(-1).id, reason: "Restore prior snapshot" },
          true,
        );
        const audit = (
          await call("/api/admin/dashboard", "GET", undefined, true)
        ).data.audits;
        assert.ok(audit.some((a) => a.action === "submission.restore"));
      },
    );
    await t.test(
      "data survives new application instance and new pool connection",
      async () => {
        const other = createApp().listen(0, "127.0.0.1");
        await new Promise((r) => other.on("listening", r));
        const response = await fetch(
          "http://127.0.0.1:" +
            other.address().port +
            "/api/events/" +
            event.id,
        );
        assert.deepEqual(await response.json(), firstArchive);
        await new Promise((r) => other.close(r));
        const c = await pool.connect();
        assert.equal(
          (await c.query("SELECT count(*)::int AS n FROM teams")).rows[0].n,
          5,
        );
        c.release();
      },
    );
    await t.test(
      "backup includes snapshots and prices but excludes sessions and secrets",
      async () => {
        const d = (await call("/api/admin/export", "GET", undefined, true))
          .data;
        assert.ok(d.deck_versions.length >= 8);
        assert.equal(d.events.length, 2);
        assert.ok(!d.sessions);
        assert.ok(!JSON.stringify(d).includes("integration-password"));
      },
    );
    await t.test("logout invalidates session server-side", async () => {
      await post("/api/logout", {}, true);
      await call("/api/admin/dashboard", "GET", undefined, true, 401);
    });
    await t.test(
      "login throttling is enforced in persistent database",
      async () => {
        for (let i = 0; i < 8; i++)
          await post("/api/login", { password: "incorrect" }, false, 401);
        await post("/api/login", { password: "incorrect" }, false, 429);
      },
    );
    fs.mkdirSync(new URL("../reports/", import.meta.url), { recursive: true });
    fs.writeFileSync(
      new URL("../reports/lifecycle.json", import.meta.url),
      JSON.stringify(
        {
          provider: "deterministic mock",
          database: "actual Railway PostgreSQL, disposable schema",
          first: firstArchive,
          second: await get("/api/events/" + second.id),
        },
        null,
        2,
      ),
    );
  } finally {
    await new Promise((r) => server.close(r));
    await q("DROP SCHEMA " + process.env.DATABASE_SCHEMA + " CASCADE");
    await pool.end();
  }
});
