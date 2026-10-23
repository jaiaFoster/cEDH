import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import {
  searchCards,
  parseFilters,
  searchIndex,
  compileQuery,
  SearchError,
  SORTS,
} from "../card-search.mjs";
import { PRICES } from "../scoring.mjs";
const prices = Object.fromEntries(
  [...new Set(PRICES.values())].map((p) => [
    p.name,
    { main: p.main, command: p.command },
  ]),
);
const search = (params = {}) => searchCards(prices, parseFilters(params));
const one = (name) => searchIndex.find((c) => c.name === name);
const has = (q, name) => compileQuery(q)(one(name));

test("search metadata is complete, hash-verified and bound to the original scoring catalog", () => {
  const buf = gunzipSync(
    fs.readFileSync(
      new URL("../data/search-metadata.json.gz", import.meta.url),
    ),
  );
  const meta = JSON.parse(buf),
    proof = JSON.parse(
      fs.readFileSync(
        new URL("../data/search-metadata.provenance.json", import.meta.url),
      ),
    );
  const hash = (b) => createHash("sha256").update(b).digest("hex");
  assert.equal(searchIndex.length, 38940);
  assert.equal(
    new Set(searchIndex.map((c) => c.oracle_id)).size,
    searchIndex.length,
  );
  assert.equal(Object.keys(meta.cards).length, searchIndex.length);
  assert.equal(proof.records, searchIndex.length);
  assert.equal(hash(buf), proof.metadata_sha256);
  assert.equal(
    hash(fs.readFileSync(new URL("../data/oracle.jsonl.gz", import.meta.url))),
    meta.catalog_sha256,
  );
  for (const c of searchIndex) {
    assert.ok(Array.isArray(c.colors));
    assert.match(c.url, /^https:\/\/scryfall\.com\/card\//);
  }
});
test("ordinary name terms, quoted phrases, exact names, apostrophes and Unicode", () => {
  assert.ok(has("Sol Ring", "Sol Ring"));
  assert.ok(has('"Sol Ring"', "Sol Ring"));
  assert.equal(has('!"Sol Ring"', "Solemn Offering"), false);
  assert.equal(search({ q: '!"Sol Ring"' }).total, 1);
  assert.ok(has('"K’rrik, Son of Yawgmoth"', "K'rrik, Son of Yawgmoth"));
  assert.equal(
    search({ q: '"no such commander doubles research card"' }).total,
    0,
  );
});
test("type, literal Oracle text, comparisons, aliases and mixed simultaneous terms", () => {
  const q = 'id:wu t:artifact o:"draw a card" mv<=3';
  assert.ok(has(q, "Mind Stone"));
  assert.equal(has(q, "Arcane Signet"), false);
  assert.equal(has(q, "Thrasios, Triton Hero"), false);
  assert.ok(
    has('identity:wu type:artifact oracle:"draw a card" cmc<=3', "Mind Stone"),
  );
  assert.ok(has('t:artifact AND mv=2 -o:"draw a card"', "Arcane Signet"));
  assert.equal(has("t:artifact mv>2", "Arcane Signet"), false);
  for (const [q, expected] of [
    ["mv:2", true],
    ["mv!=2", false],
    ["mv<2", false],
    ["mv<=2", true],
    ["mv>2", false],
    ["mv>=2", true],
  ])
    assert.equal(has(q, "Arcane Signet"), expected, q);
});
test("id: uses contained deck identity whereas c: requires all named colors", () => {
  assert.ok(has("id:wu", "Sol Ring"));
  assert.ok(has("id:wu", "Swords to Plowshares"));
  assert.ok(has("id:wu", "Azorius Charm"));
  assert.equal(has("id:wu", "Thrasios, Triton Hero"), false);
  assert.equal(has("id=wu", "Sol Ring"), false);
  assert.ok(has("id=wu", "Azorius Charm"));
  assert.ok(has("c:wu", "Atraxa, Praetors' Voice"));
  assert.equal(has("c:wu", "Swords to Plowshares"), false);
  assert.ok(has("id>wu", "Atraxa, Praetors' Voice"));
  assert.equal(has("c=wu", "Atraxa, Praetors' Voice"), false);
});
test("color is explicit metadata: Dryad Arbor, devoid, land identity and DFCs", () => {
  assert.ok(has("c:g", "Dryad Arbor"));
  assert.equal(one("Dryad Arbor").mv, 0);
  assert.ok(has("c:c id:ub", "Ulamog's Nullifier"));
  assert.equal(has("c:u", "Ulamog's Nullifier"), false);
  assert.ok(has("c:c id:g", "Forest"));
  assert.ok(has("c:u", "Glasspool Mimic // Glasspool Shore"));
  const matches = search({ q: '!"Glasspool Mimic // Glasspool Shore"' });
  assert.equal(matches.total, 1);
  assert.equal(matches.cards[0].main, 1);
  assert.equal(search({ q: '"Glasspool Shore"' }).total, 1);
});
test("colorless and multicolor are different from having no identity filter", () => {
  assert.equal(search({ q: '!"Sol Ring"', colorCount: "colorless" }).total, 1);
  assert.equal(search({ q: '!"Sol Ring"', colorCount: "multicolor" }).total, 0);
  assert.ok(has("id:c c:colorless", "Sol Ring"));
  assert.ok(has("id:m c:m", "Thrasios, Triton Hero"));
  assert.equal(has("id:m", "Swords to Plowshares"), false);
  assert.equal(
    search({
      q: '!"Thrasios, Triton Hero"',
      identity: "gu",
      identityMode: "exact",
      colorCount: "multicolor",
    }).total,
    1,
  );
});
test("different DFC faces do not fabricate a multicolored face, and exact face names resolve once", () => {
  const name = "Archangel Avacyn // Avacyn, the Purifier";
  assert.ok(has("c=w", name));
  assert.ok(has("c=r", name));
  assert.equal(has("c:wr", name), false);
  assert.equal(has("c:m", name), false);
  assert.ok(has("c:w c:r", name));
  assert.ok(has("c:c", "Glasspool Mimic // Glasspool Shore"));
  assert.equal(search({ q: '!"Glasspool Shore"' }).total, 1);
  assert.equal(search({ q: '!"Archangel Avacyn"' }).total, 1);
  assert.ok(has("mv:<=3 id:<=wu", "Mind Stone"));
});
test("every one of 32 identity sets: exact and contained filters", () => {
  const letters = "WUBRG";
  const fixture = Array.from({ length: 32 }, (_, mask) => ({
    name: String(mask),
    nameKey: String(mask),
    oracle_id: String(mask),
    identity: [...letters].filter((_, i) => mask & (1 << i)),
    colors: [],
    type: "artifact",
    oracle: "",
    mv: 0,
    legal: true,
    legality: "legal",
    commanderEligible: false,
  }));
  for (let mask = 0; mask < 32; mask++) {
    const identity = fixture[mask].identity.join("").toLowerCase() || "c";
    const exact = searchCards(
      {},
      parseFilters({ identity, identityMode: "exact" }),
      fixture,
    );
    assert.deepEqual(
      exact.cards.map((c) => Number(c.name)),
      [mask],
    );
    const contained = searchCards(
      {},
      parseFilters({ identity, identityMode: "within" }),
      fixture,
    );
    const expected = Array.from({ length: 32 }, (_, i) => i)
      .filter((i) => (i & mask) === i)
      .sort((a, b) => String(a).localeCompare(String(b), "en"));
    assert.deepEqual(
      contained.cards.map((c) => Number(c.name)),
      expected,
    );
  }
});
test("GUI filters and query are ANDed, with inclusive numeric boundaries", () => {
  assert.equal(
    search({
      q: '!"Sol Ring" t:artifact',
      identity: "wu",
      identityMode: "within",
      colorCount: "colorless",
      zone: "main",
      points: "pointed",
      min: "15",
      max: "15",
      type: "artifact",
      mvMin: "1",
      mvMax: "1",
      legality: "legal",
    }).total,
    1,
  );
  assert.equal(search({ q: '!"Sol Ring"', mvMax: "0" }).total, 0);
  assert.equal(
    search({ q: '!"Sol Ring"', identity: "wu", identityMode: "exact" }).total,
    0,
  );
});
test("known zero cards, legacy pointed toggle and actual location prices", () => {
  assert.equal(
    search({ q: '!"Acererak the Archlich"', points: "zero", zone: "main" })
      .cards[0].main,
    0,
  );
  assert.equal(
    search({ q: '!"Acererak the Archlich"', points: "pointed", zone: "main" })
      .total,
    0,
  );
  assert.equal(search({ q: '!"Sol Ring"', pointed: "1" }).cards[0].main, 15);
  assert.equal(search({ q: '!"Sol Ring"', pointed: "0" }).total, 1);
  const p = { "Talion, the Kindly Lord": { main: 0, command: 4 } };
  const q = '!"Talion, the Kindly Lord"';
  assert.equal(
    searchCards(p, parseFilters({ q, zone: "main", points: "zero" })).total,
    1,
  );
  assert.equal(
    searchCards(p, parseFilters({ q, zone: "command", points: "pointed" }))
      .cards[0].command,
    4,
  );
  assert.equal(
    searchCards(p, parseFilters({ q, zone: "command", points: "zero" })).total,
    0,
  );
});
test("command-ineligible cards keep legacy numeric values but are excluded from command-zero/range filters", () => {
  assert.equal(search({ q: '!"Sol Ring"' }).cards[0].command, 0);
  assert.equal(search({ q: '!"Sol Ring"' }).cards[0].commanderEligible, false);
  assert.equal(
    search({ q: '!"Sol Ring"', zone: "command", points: "zero" }).total,
    0,
  );
  assert.equal(
    search({ q: '!"Sol Ring"', zone: "command", min: "0" }).total,
    0,
  );
  assert.equal(search({ q: '!"Sol Ring"', eligible: "1" }).total, 0);
  assert.equal(
    search({
      q: '!"Acererak the Archlich"',
      eligible: "1",
      zone: "command",
      points: "zero",
    }).total,
    1,
  );
});
test("Commander legality filter uses pinned status without changing prices", () => {
  assert.equal(search({ q: '!"Black Lotus"', legality: "legal" }).total, 0);
  assert.equal(search({ q: '!"Black Lotus"', legality: "banned" }).total, 1);
  assert.equal(search({ q: '!"Black Lotus"', legality: "not_legal" }).total, 1);
  assert.equal(search({ q: '!"Sol Ring"', legality: "not_legal" }).total, 0);
});
test("published schedule supplied per call, no static estimate/cached price substitution", () => {
  const a = { "Sol Ring": { main: 22, command: 0 } },
    b = { "Sol Ring": { main: 3, command: 0 } },
    query = parseFilters({ q: '!"Sol Ring"' });
  assert.equal(searchCards(a, query).cards[0].main, 22);
  assert.equal(searchCards(b, query).cards[0].main, 3);
  assert.equal(searchCards({}, query).cards[0].main, 0);
  assert.deepEqual(a, { "Sol Ring": { main: 22, command: 0 } });
  assert.equal(
    searchCards(a, parseFilters({ q: '!"unrecognized-name-123"' })).cards
      .length,
    0,
  );
});
test("all eight sorts are global, deterministic, with command-ineligible cards last", () => {
  const fixture = [
    ["Alpha", 0, 4, 2, true],
    ["Beta", 9, 0, 0, true],
    ["Gamma", 1, 3, 3, true],
    ["Delta", 5, 0, 1, false],
  ].map(([name, main, command, mv, commanderEligible]) => ({
    name,
    nameKey: name.toLowerCase(),
    oracle_id: name,
    identity: [],
    colors: [],
    type: "artifact",
    oracle: "",
    mv,
    legal: true,
    legality: "legal",
    commanderEligible,
    main,
    command,
  }));
  const pp = Object.fromEntries(
    fixture.map((c) => [c.name, { main: c.main, command: c.command }]),
  );
  const expected = {
    main_desc: ["Beta", "Delta", "Gamma", "Alpha"],
    main_asc: ["Alpha", "Gamma", "Delta", "Beta"],
    command_desc: ["Alpha", "Gamma", "Beta", "Delta"],
    command_asc: ["Beta", "Gamma", "Alpha", "Delta"],
    name_asc: ["Alpha", "Beta", "Delta", "Gamma"],
    name_desc: ["Gamma", "Delta", "Beta", "Alpha"],
    mv_asc: ["Beta", "Delta", "Alpha", "Gamma"],
    mv_desc: ["Gamma", "Alpha", "Delta", "Beta"],
  };
  for (const sort of SORTS) {
    const first = searchCards(pp, parseFilters({ sort, limit: "2" }), fixture),
      second = searchCards(
        pp,
        parseFilters({ sort, limit: "2", offset: "2" }),
        fixture,
      );
    assert.deepEqual(
      [...first.cards, ...second.cards].map((c) => c.name),
      expected[sort],
      sort,
    );
    assert.equal(first.total, 4);
    assert.equal(second.total, 4);
  }
});
test("real result sets sort completely before slicing, including page offsets above 100", () => {
  for (const sort of SORTS) {
    const whole = search({ sort, points: "pointed", limit: "100" });
    const first = search({ sort, points: "pointed", limit: "50" }),
      second = search({ sort, points: "pointed", offset: "50", limit: "50" });
    assert.deepEqual([...first.cards, ...second.cards], whole.cards, sort);
    const later = search({
      sort,
      points: "pointed",
      offset: "100",
      limit: "100",
    });
    assert.equal(
      new Set([...whole.cards, ...later.cards].map((c) => c.oracle_id)).size,
      200,
    );
  }
});
test("valid empty searches remain distinct from unsupported or malformed syntax", () => {
  assert.equal(search({ q: 'o:"impossible oracle phrase 928392"' }).total, 0);
  for (const q of [
    "foo:bar",
    "set:lea",
    "name OR land",
    "(t:land)",
    "o:/draw.*/",
    "o:",
    '"unclosed',
    "mv<NaN",
    "id:purple",
    "mv<=-1",
    "c>m",
  ]) {
    assert.throws(
      () => search({ q }),
      (e) => e instanceof SearchError && e.status === 400,
      q,
    );
  }
  assert.throws(
    () => search({ q: "set:lea" }),
    (e) => e.code === "unsupported_query",
  );
  assert.throws(
    () => search({ q: '"unclosed' }),
    (e) => e.code === "invalid_query",
  );
});
test("filter validation rejects arrays, invalid ranges, offsets, booleans, sorts and unknown keys", () => {
  for (const p of [
    { q: [] },
    { q: { o: "draw" } },
    { sort: "main-desc" },
    { bogus: "x" },
    { min: "1.2" },
    { min: "2", max: "1" },
    { mvMin: "5", mvMax: "3" },
    { limit: "0" },
    { limit: "101" },
    { offset: "-1" },
    { offset: "1.1" },
    { pointed: "no" },
    { zone: "graveyard" },
    { identityMode: "any" },
    { identity: "orange" },
    { q: "x".repeat(2001) },
  ])
    assert.throws(() => parseFilters(p), SearchError, JSON.stringify(p));
});
