import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
if (!process.env.DATABASE_URL) throw Error("Disposable PostgreSQL required");
process.env.DATABASE_SCHEMA = "test_live_" + randomUUID().replaceAll("-", "");
process.env.ADMIN_PASSWORD = "live-search-test-only";
process.env.SESSION_SECRET = "live-search-test-session";
const { q, pool, migrate } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
const { searchIndex } = await import("../card-search.mjs");
await test("live discovery uses published prices and never modifies catalog or stored versions", async () => {
  await migrate();
  const sol = searchIndex.find((c) => c.name === "Sol Ring"),
    n = searchIndex.find((c) => c.name === "Najeela, the Blade-Blossom");
  let requests = [];
  const scryfallClient = async (query, sort, page) => {
    requests.push({ query, sort, page });
    return {
      total_cards: 3,
      has_more: false,
      warnings: [],
      data: [
        sol,
        n,
        {
          ...sol,
          name: "Synthetic unreviewed test card",
          oracle_id: "00000000-0000-4000-8000-000000000009",
        },
      ],
    };
  };
  const server = createApp({ scryfallClient }).listen(0, "127.0.0.1");
  await new Promise((r) => server.on("listening", r));
  const base = "http://127.0.0.1:" + server.address().port;
  async function get(params = {}, status = 200) {
    const r = await fetch(
      base +
        "/api/points?" +
        new URLSearchParams({ source: "scryfall", ...params }),
    );
    const d = await r.json();
    assert.equal(r.status, status, JSON.stringify(d));
    return d;
  }
  try {
    const old = (await q("SELECT * FROM price_versions")).rows[0];
    const first = await get({ q: "set:lea OR set:leb" });
    assert.equal(first.cards[0].main, old.prices["Sol Ring"].main);
    assert.equal(first.cards[1].command, 0);
    assert.equal(first.cards[2].main, null);
    assert.equal(first.cards[2].priceKnown, false);
    const id = randomUUID(),
      prices = { ...old.prices, "Sol Ring": { main: 41, command: 0 } };
    await q(
      "INSERT INTO price_versions(id,name,status,prices,published_at) VALUES($1,'Live search test','published',$2,now()+interval '1 second')",
      [id, prices],
    );
    assert.equal((await get()).cards[0].main, 41);
    assert.equal(
      (await get({ version: old.id })).cards[0].main,
      old.prices["Sol Ring"].main,
    );
    await get({ sort: "main_desc" }, 400);
    await get({ points: "zero" }, 400);
    await get({ offset: "175", sort: "mv_desc" });
    assert.equal(requests.at(-1).page, 2);
    assert.equal(requests.at(-1).sort, "mv_desc");
    assert.equal(searchIndex.length, 38940);
    assert.deepEqual(
      (await q("SELECT prices FROM price_versions WHERE id=$1", [old.id]))
        .rows[0].prices,
      old.prices,
    );
  } finally {
    await new Promise((r) => server.close(r));
    await q("DROP SCHEMA " + process.env.DATABASE_SCHEMA + " CASCADE");
    await pool.end();
  }
});
