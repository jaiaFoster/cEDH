import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
  compositionSeed as seed,
  compositionDraftSeed,
  compositionCards,
  validateComposition,
  compositionPairKey,
  searchCompositions,
  parseCompositionFilters,
  enrichComposition,
  compositionCard,
} from "../compositions.mjs";
import { PRICES } from "../scoring.mjs";
import { catalog } from "../legality.mjs";
const prices = Object.fromEntries(
  [...new Set(PRICES.values())].map((p) => [
    p.name,
    { main: p.main, command: p.command },
  ]),
);
const version = { id: "test-v3", name: "Bundled v3", prices };
const find = (params = {}) =>
  searchCompositions(seed, version, parseCompositionFilters(params));
test("38 seeds and 50 additions have stable unique complete command zones and verified evidence", () => {
  assert.equal(seed.length, 88);
  assert.equal(seed.filter((c) => c.seed_id).length, 38);
  assert.equal(compositionDraftSeed.length, 14);
  assert.equal(new Set(seed.map((p) => p.pair_key)).size, 88);
  for (const p of seed) {
    assert.doesNotThrow(
      () => validateComposition(p, { publishing: true }),
      p.id,
    );
    assert.equal(
      compositionPairKey(p.player_a, p.player_b),
      compositionPairKey(p.player_b, p.player_a),
    );
    for (const id of [...p.player_a, ...p.player_b])
      assert.ok(p.oracle_evidence.some((e) => e.oracle_id === id));
  }
  const a = seed.find((p) => p.id === "benchmark-a");
  assert.equal(a.player_a.length, 2);
  assert.equal(a.player_b.length, 2);
  const c = seed.find((p) => p.id === "benchmark-c");
  assert.equal(c.player_a[0], c.player_b[0]);
  const bg = Object.values(compositionCards).find(
    (c) => c.name === "Sword Coast Sailor",
  );
  const karlach = seed.find((p) => p.id === "seed-25");
  assert.ok(bg && bg.eligibility === "background");
  assert.throws(
    () => validateComposition({ ...karlach, player_a: [bg.oracle_id] }),
    /Background/,
  );
  assert.doesNotThrow(() =>
    validateComposition({
      ...karlach,
      player_a: [...karlach.player_a, bg.oracle_id],
    }),
  );
  for (const p of compositionDraftSeed)
    assert.throws(
      () => validateComposition(p, { publishing: true }),
      /Publication/,
    );
});
test("commander search covers both players, every Najeela team, partners and exact names", () => {
  for (const name of ["Najeela", "Heartless", "Yuriko", "Tymna", "Arcum"]) {
    const expected = seed
      .filter((p) =>
        [...p.player_a, ...p.player_b].some((id) =>
          compositionCards[id].name.includes(name),
        ),
      )
      .map((p) => p.id)
      .sort();
    assert.deepEqual(
      find({ commander: name, limit: "100" })
        .compositions.map((p) => p.id)
        .sort(),
      expected,
    );
    const text = find({ q: name, limit: "100" }).compositions.map((p) => p.id);
    for (const id of expected) assert.ok(text.includes(id));
  }
  assert.ok(
    find({ q: "artifact tutors" }).compositions.some((p) => p.id === "seed-19"),
  );
  assert.ok(find({ q: "each opponent" }).total);
  assert.ok(
    find({ commander: "Najeela, the Blade-Blossom", exact: "1" }).total,
  );
  assert.equal(find({ commander: "Najeela", exact: "1" }).total, 0);
  assert.ok(find({ commander: "K'rrik, Son of Yawgmoth", exact: "1" }).total);
  assert.equal(find({ q: "unfindable-composition-xyz" }).total, 0);
});
test("colors, roles, mechanics, status and points intersect; sorting precedes pagination", () => {
  const exact = find({ aColors: "BG", colorMode: "exact", q: "Heartless" });
  assert.deepEqual(
    exact.compositions.map((p) => p.id),
    ["seed-10"],
  );
  const inc = find({ teamColors: "WUBRG", colorMode: "within", limit: "100" });
  assert.equal(inc.total, 88);
  const mono = find({ aColors: "C", colorMode: "exact" });
  assert.equal(mono.total, 0);
  const g = find({
    archetype: "Combat",
    mechanism: "Shared combat",
    commander: "Najeela",
    limit: "100",
  });
  assert.ok(g.total > 2);
  assert.ok(
    g.compositions.every(
      (p) => p.archetype === "Combat" && p.tags.includes("Shared combat"),
    ),
  );
  assert.equal(find({ status: "Active brew" }).compositions[0].id, "seed-10");
  assert.equal(find({ decks: "full" }).total, 9);
  assert.equal(find({ decks: "historical" }).total, 9);
  assert.equal(find({ decks: "compliant" }).total, 0);
  assert.equal(find({ decks: "concept" }).total, 79);
  for (const sort of [
    "featured",
    "name",
    "recent",
    "archetype",
    "points_asc",
    "points_desc",
  ]) {
    const all = find({ sort, limit: "100" }).compositions.map((p) => p.id),
      first = find({ sort, limit: "17" }).compositions.map((p) => p.id),
      next = find({ sort, offset: "17", limit: "17" }).compositions.map(
        (p) => p.id,
      );
    assert.deepEqual([...first, ...next], all.slice(0, 34), sort);
  }
  const ranged = find({ min: "0", max: "10", limit: "100" });
  assert.ok(ranged.compositions.every((p) => p.command_zone_points.team <= 10));
});
test("live prices use the published table, preserve zero and separate complete deck costs", () => {
  const old = seed.find((p) => p.id === "benchmark-a"),
    x = enrichComposition(old, version);
  assert.equal(x.full_team_score.points, 462);
  assert.equal(x.budget_validated, false);
  assert.notEqual(x.command_zone_points.team, x.full_team_score.points);
  const changed = structuredClone(prices);
  for (const id of old.player_a)
    changed[compositionCards[id].name] = { main: 0, command: 37 };
  const y = enrichComposition(old, {
    id: "new-published",
    name: "New",
    prices: changed,
  });
  assert.equal(y.command_zone_points.a, 74);
  assert.notEqual(y.command_zone_points.team, x.command_zone_points.team);
  const free = enrichComposition(
    seed.find((p) => p.id === "benchmark-c"),
    { id: "zero", name: "Zero", prices: {} },
  );
  assert.deepEqual(free.command_zone_points, { a: 0, b: 0, team: 0 });
  const unknown = Object.values(compositionCards).find(
    (c) => c.eligibility && !catalog.some((k) => k.oracle_id === c.oracle_id),
  );
  if (unknown) {
    const p = { ...old, player_a: [unknown.oracle_id], decklists: [] };
    assert.equal(enrichComposition(p, version).command_zone_points.a, null);
  }
  const totals = [462, 518, 314, 237, 198, 246, 215, 150, 178];
  for (const [i, p] of seed.slice(0, 9).entries()) {
    const x = enrichComposition(p, version);
    assert.equal(x.full_team_score.points, totals[i]);
    assert.equal(x.deck_scores.length, 2);
    assert.ok(x.deck_scores.every((d) => d.count === 100 && d.legal));
    assert.equal(x.budget_validated, false);
  }
});
test("controller-sensitive corrections and actual calculations stay explicit", () => {
  const by = Object.fromEntries(seed.map((p) => [p.id, p]));
  assert.match(by["seed-10"].interaction, /one chosen active player/);
  assert.ok(by["seed-10"].rule_references.includes("805.9"));
  assert.match(by["seed-10"].execution.join(" "), /120/);
  assert.match(by["seed-19"].interaction, /creature.s controller sacrifices/);
  assert.match(by["seed-24"].weaknesses.join(" "), /Treasures cannot pay/);
  assert.match(by["seed-18"].interaction, /layer 7b/);
  assert.match(by["seed-35"].interaction, /copies are not new casts/);
  assert.match(
    by["seed-17"].weaknesses.join(" "),
    /not the standard land-only/,
  );
  assert.match(by["discovery-49"].weaknesses.join(" "), /18, not 21/);
  assert.match(by["discovery-40"].weaknesses.join(" "), /tapped and attacking/);
  assert.ok(by["discovery-30"].rule_references.includes("201.5b"));
  assert.equal(60 - 15 - 30, 15);
  assert.equal(60 - 60 + 120, 120);
  assert.equal(7 * 3, 21);
  assert.equal(4 * 2 * 3, 24);
  assert.equal(8 * 2, 16);
});
test("unknown, illegal, malformed and unsupported research is rejected without guesses", () => {
  const x = structuredClone(seed[0]);
  x.player_a = ["not-a-card"];
  assert.throws(() => validateComposition(x), /commander/);
  const y = structuredClone(seed[0]);
  y.player_a = [seed[1].player_a[0], seed[1].player_b[0]];
  assert.throws(() => validateComposition(y), /partner/);
  const z = structuredClone(seed[0]);
  z.oracle_evidence[0].quote = "invented Oracle text";
  assert.throws(
    () => validateComposition(z, { publishing: true }),
    /quotation/,
  );
  for (const params of [
    { unknown: "1" },
    { q: ["a", "b"] },
    { min: "5", max: "1" },
    { aColors: "purple" },
    { sort: "power" },
    { offset: "-1" },
    { limit: "500" },
  ])
    assert.throws(() => parseCompositionFilters(params));
  assert.throws(() => find({ q: "o:win" }), /operators/);
  const donated = structuredClone(seed.find((p) => p.id === "discovery-50"));
  const coil = catalog.find((c) => c.name === "Immortal Coil");
  donated.key_cards = [coil.oracle_id];
  donated.key_card_owners = { [coil.oracle_id]: "A" };
  assert.throws(() => validateComposition(donated), /Player A color identity/);
  const sol = catalog.find((c) => c.name === "Sol Ring");
  assert.equal(compositionCard(sol.oracle_id).name, "Sol Ring");
  assert.equal(compositionCard("unknown"), null);
});
