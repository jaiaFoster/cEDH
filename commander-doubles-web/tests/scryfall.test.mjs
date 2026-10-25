import test from "node:test";
import assert from "node:assert/strict";
import { parseFilters, searchIndex } from "../card-search.mjs";
import {
  buildScryfallQuery,
  createScryfallClient,
  searchScryfall,
} from "../scryfall-search.mjs";
const sol = searchIndex.find((c) => c.name === "Sol Ring"),
  najeela = searchIndex.find((c) => c.name === "Najeela, the Blade-Blossom");
const card = (c) => ({
  name: c.name,
  oracle_id: c.oracle_id,
  color_identity: c.identity,
  colors: c.colors,
  type_line: c.typeLine,
  cmc: c.mv,
  legalities: { commander: c.legality },
  scryfall_uri: c.url,
});
const list = (cards = [card(sol)], extra = {}) => ({
  object: "list",
  total_cards: cards.length,
  has_more: false,
  data: cards,
  ...extra,
});
const f = (p = {}) => parseFilters({ source: "scryfall", ...p });
const fast = (fetchImpl) =>
  createScryfallClient({ fetchImpl, sleep: async () => {} });
test("live mode accepts native syntax, validates options and groups GUI conditions", () => {
  const x = f({
    q: "set:lea OR set:leb",
    identity: "wu",
    identityMode: "exact",
    colorCount: "multicolor",
    type: "artifact",
    mvMax: "3",
    legality: "legal",
    eligible: "1",
  });
  assert.equal(
    buildScryfallQuery(x),
    '(set:lea OR set:leb) id=wu id:m t:"artifact" mv<=3 legal:commander is:commander',
  );
  assert.equal(
    buildScryfallQuery(
      f({ q: '!"Sol Ring" include:extras', type: "artifact" }),
    ),
    '(!"Sol Ring") t:"artifact" include:extras',
  );
  assert.equal(
    buildScryfallQuery(f({ q: 'o:"include:extras"', type: "artifact" })),
    '(o:"include:extras") t:"artifact"',
  );
  assert.equal(
    buildScryfallQuery(
      f({ q: "o:/include:extras/ order:name", type: "artifact" }),
    ),
    '(o:/include:extras/) t:"artifact" order:name',
  );
  assert.equal(x.limit, 175);
  assert.equal(buildScryfallQuery(f()), "mv>=0");
  assert.throws(() => parseFilters({ q: "set:lea" }), /Unsupported/);
  assert.throws(() => f({ source: "invalid" }));
  assert.throws(() => f({ q: "x".repeat(2001) }));
});
test("Oracle identity joins only published league prices, cached metadata never caches prices", async () => {
  let count = 0;
  const newCard = {
    ...card(sol),
    name: "Sol Ring",
    oracle_id: "00000000-0000-4000-8000-000000000001",
  };
  const client = fast(async () => {
    count++;
    return Response.json(list([card(sol), card(najeela), newCard]));
  });
  const result = await searchScryfall(
    { "Sol Ring": { main: 37, command: 0 } },
    f(),
    client,
  );
  assert.equal(result.cards[0].main, 37);
  assert.equal(result.cards[0].priceKnown, true);
  assert.equal(result.cards[1].command, 0);
  assert.equal(result.cards[1].priceKnown, true);
  assert.equal(result.cards[1].commanderEligible, true);
  assert.equal(result.cards[2].main, null);
  assert.equal(result.cards[2].command, null);
  assert.equal(result.cards[2].priceKnown, false);
  assert.equal(result.cards[2].legal, true);
  const changed = await searchScryfall(
    { "Sol Ring": { main: 41, command: 0 } },
    f(),
    client,
  );
  assert.equal(changed.cards[0].main, 41);
  assert.equal(count, 1);
});
test("fixed upstream URL, named headers, no redirects, full-set sort and page parameters", async () => {
  let request;
  const client = fast(async (url, options) => {
    request = { url, options };
    return Response.json(list());
  });
  await searchScryfall(
    {},
    f({ q: '!"Sol Ring"', sort: "mv_desc", offset: "175" }),
    client,
  );
  assert.equal(request.url.origin, "https://api.scryfall.com");
  assert.equal(request.url.pathname, "/cards/search");
  assert.equal(request.url.searchParams.get("page"), "2");
  assert.equal(request.url.searchParams.get("order"), "cmc");
  assert.equal(request.url.searchParams.get("dir"), "desc");
  assert.equal(request.url.searchParams.get("include_extras"), "false");
  assert.equal(request.options.redirect, "error");
  assert.match(request.options.headers["User-Agent"], /CommanderDoubles/);
  assert.equal(request.options.headers.Accept, "application/json");
  for (const p of [
    { sort: "main_desc" },
    { points: "pointed" },
    { min: "1" },
    { offset: "1" },
    { limit: "50" },
  ])
    await assert.rejects(searchScryfall({}, f(p), client), /Live|Point/);
});
test("404 is an empty search; syntax, upstream errors and outages remain distinct", async () => {
  const empty = await searchScryfall(
    {},
    f(),
    fast(async () => Response.json({ code: "not_found" }, { status: 404 })),
  );
  assert.equal(empty.total, 0);
  await assert.rejects(
    searchScryfall(
      {},
      f(),
      fast(async () =>
        Response.json(
          { details: "Unknown Scryfall operator" },
          { status: 400 },
        ),
      ),
    ),
    (e) => e.status === 400 && e.code === "invalid_scryfall_query",
  );
  for (const response of [
    () => Response.json({}, { status: 503 }),
    () => Response.json({ object: "list", data: [] }),
    () => new Response("not json"),
    () => {
      throw Error("network");
    },
  ])
    await assert.rejects(
      searchScryfall(
        {},
        f(),
        fast(async () => response()),
      ),
      (e) => e.status === 503,
    );
});
test("rate limiting respects cooldown; successful inflight calls deduplicate and caching expires", async () => {
  let clock = 1000,
    calls = 0;
  const rate = createScryfallClient({
    now: () => clock,
    sleep: async () => {},
    fetchImpl: async () => {
      calls++;
      return Response.json(
        {},
        { status: 429, headers: { "retry-after": "2" } },
      );
    },
  });
  await assert.rejects(rate("a", "name_asc", 1), /rate limiting/);
  await assert.rejects(rate("b", "name_asc", 1), /rate limiting/);
  assert.equal(calls, 1);
  clock += 2001;
  await assert.rejects(rate("b", "name_asc", 1));
  assert.equal(calls, 2);
  let release;
  calls = 0;
  const shared = createScryfallClient({
    now: () => clock,
    sleep: async () => {},
    fetchImpl: async () => {
      calls++;
      if (calls === 1) await new Promise((r) => (release = r));
      return Response.json(list());
    },
  });
  const a = shared("same", "name_asc", 1),
    b = shared("same", "name_asc", 1);
  await new Promise((r) => setTimeout(r, 0));
  release();
  await Promise.all([a, b]);
  assert.equal(calls, 1);
  clock += 60001;
  await shared("same", "name_asc", 1);
  assert.equal(calls, 2);
});
test("upstream card URLs cannot introduce unsafe schemes or foreign targets", async () => {
  const client = fast(async () =>
    Response.json(
      list([{ ...card(sol), scryfall_uri: "javascript:alert(1)" }]),
    ),
  );
  const r = await searchScryfall({}, f(), client);
  assert.match(r.cards[0].url, /^https:\/\/scryfall.com\/search/);
});

test("global upstream starts are spaced and excessive pending searches fail fast", async () => {
  let clock = 0;
  const starts = [];
  const client = createScryfallClient({
    now: () => clock,
    sleep: async (ms) => {
      clock += ms;
    },
    fetchImpl: async () => {
      starts.push(clock);
      return Response.json(list());
    },
  });
  await Promise.all([
    client("a", "name_asc", 1),
    client("b", "name_asc", 1),
    client("c", "name_asc", 1),
  ]);
  assert.deepEqual(starts, [0, 200, 400]);
  let release;
  const gate = new Promise((r) => (release = r));
  const busy = createScryfallClient({
    sleep: async () => {},
    fetchImpl: async () => {
      await gate;
      return Response.json(list());
    },
  });
  const requests = Array.from({ length: 12 }, (_, i) =>
    busy(String(i), "name_asc", 1),
  );
  await assert.rejects(busy("overflow", "name_asc", 1), /busy/);
  release();
  await Promise.all(requests);
});
