import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import {
  catalog,
  catalogManifest,
  printingCards,
  printingAliases,
} from "../card-catalog.mjs";
import { matchCard, evaluate, resolveCard, priceTable } from "../legality.mjs";
import {
  PRICES,
  parseExport,
  deckIdFromURL,
  getMoxfield,
  decodeMoxfield,
} from "../scoring.mjs";
const prices = Object.fromEntries(
  [...new Set(PRICES.values())].map((p) => [p.name, p]),
);
const sample = (name) =>
  parseExport(
    `COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n98 Island\n1 ${name}`,
  );
const root = new URL(
  "../data/catalogs/" + catalogManifest.version + "/",
  import.meta.url,
);
const examples = JSON.parse(
  fs.readFileSync(new URL("printing-examples.json", root)),
);
test("active catalog checksums, complete printing count and all imported languages", () => {
  for (const [name, hash] of Object.entries(catalogManifest.files))
    assert.equal(
      createHash("sha256")
        .update(fs.readFileSync(new URL(name, root)))
        .digest("hex"),
      hash,
    );
  assert.equal(catalog.length, catalogManifest.cards);
  assert.ok(catalogManifest.printings > 500000);
  assert.ok(catalogManifest.aliases > 250000);
  for (const lang of [
    "en",
    "es",
    "ja",
    "fr",
    "de",
    "it",
    "pt",
    "ru",
    "ko",
    "zhs",
    "zht",
  ])
    assert.ok(catalogManifest.languages[lang] > 0, lang);
});
test("actual localized and flavor names inherit exact Oracle identity, legality and published price", () => {
  let checked = 0;
  for (const p of examples) {
    for (const name of [p.printed_name, p.flavor_name].filter(Boolean)) {
      const actual = matchCard(name).card;
      // Canonical English name precedence can disambiguate a translated/name collision.
      if (resolveCard(name)?.name === name && actual.oracle_id !== p.oracle_id)
        continue;
      assert.equal(actual.oracle_id, p.oracle_id, name);
      assert.equal(
        evaluate(sample(name), prices).score.points,
        evaluate(sample(actual.name), prices).score.points,
        name,
      );
      checked++;
    }
  }
  assert.ok(checked > 30);
  for (const name of ["Biblioteca silvana", "La abundancia de Yucahú"]) {
    const r = evaluate(sample(name), prices);
    assert.equal(r.deck.cards.at(-1).name, "Sylvan Library");
    assert.equal(r.score.points, 7);
    assert.equal(r.score.warnings.length, 0);
    assert.equal(r.deck.cards.at(-1).submitted_name, name);
  }
});
test("every binary printing entry sampled from real examples maps back to its Oracle card", () => {
  for (const p of examples)
    assert.equal(
      printingCards({ printing_id: p.id })[0]?.oracle_id,
      p.oracle_id,
    );
  assert.deepEqual(
    printingCards({ printing_id: "00000000-0000-0000-0000-000000000000" }),
    [],
  );
  const spanish = examples.find(
    (p) => p.name === "Sylvan Library" && p.lang === "es",
  );
  const row = parseExport(
    `1 Unknown printed name (${spanish.set}) ${spanish.collector_number} *F*\nCOMMANDER\n1 Kenrith, the Returned King`,
  ).cards[0];
  assert.equal(row.set_code, spanish.set);
  assert.equal(matchCard(row.name, row).card.name, "Sylvan Library");
  assert.equal(
    matchCard("Demonic Tutor", { printing_id: spanish.id }).card.name,
    "Demonic Tutor",
    "canonical name wins",
  );
});
test("UB/Within, flavor treatments and translated copies cannot evade singleton enforcement", () => {
  for (const [a, b] of [
    ["Rick, Steadfast Leader", "Greymond, Avacyn's Stalwart"],
    ["Chun-Li, Countless Kicks", "Zethi, Arcane Blademaster"],
    ["Godzilla, King of the Monsters", "Zilortha, Strength Incarnate"],
    ["Biblioteca silvana", "Sylvan Library"],
  ]) {
    assert.equal(matchCard(a).card.oracle_id, matchCard(b).card.oracle_id, a);
    const s = evaluate(
      parseExport(
        `COMMANDER\n1 Kenrith, the Returned King\nDECK\n97 Island\n1 ${a}\n1 ${b}`,
      ),
      prices,
    ).score;
    assert.ok(
      s.errors.some((e) => e.includes("singleton")),
      a,
    );
  }
  assert.notEqual(
    matchCard("Demonic Tutor").card.oracle_id,
    matchCard("Emeritus of Woe").card.oracle_id,
  );
  assert.equal(priceTable(prices).get("demonic tutor").main, 15);
});
test("current catalog recognizes actual new identities absent from original snapshot", () => {
  const legacy = new Set(
    gunzipSync(
      fs.readFileSync(new URL("../data/oracle.jsonl.gz", import.meta.url)),
    )
      .toString()
      .trim()
      .split("\n")
      .map((l) => JSON.parse(l).oracle_id),
  );
  const fresh = catalog.filter((c) => !legacy.has(c.oracle_id));
  assert.ok(fresh.length > 0);
  for (const c of fresh.slice(0, 10)) {
    assert.equal(matchCard(c.name).card.oracle_id, c.oracle_id);
    const evaluated = evaluate(sample(c.name), prices).score;
    assert.ok(Number.isInteger(evaluated.points));
    if (c.legalities.commander !== "legal")
      assert.equal(evaluated.legal, false);
  }
});
test("all unresolved rows are returned together and unknowns never receive a score", () => {
  assert.throws(
    () =>
      evaluate(
        parseExport(
          "COMMANDER\n1 Kenrith, the Returned King\nDECK\n97 Island\n1 This is not a Magic card\n1 Still not a Magic card",
        ),
        prices,
      ),
    (e) =>
      e.status === 422 &&
      e.issues.length === 2 &&
      e.issues.every((i) => i.candidates.length === 0),
  );
  const banned = evaluate(sample("Mana Crypt"), prices).score;
  assert.ok(banned.errors.some((e) => e.includes("banned")));
  assert.ok(evaluate(sample("太陽の指輪"), prices).score.legal);
});
test("safe URL normalization accepts shared/primer URLs but forbids unrelated hosts and paths", () => {
  for (const url of [
    "moxfield.com/decks/abcdef",
    "http://www.moxfield.com/decks/abcdef",
    "https://moxfield.com/decks/abcdef/?utm_source=test#cards",
    "https://moxfield.com/decks/abcdef/primer",
  ])
    assert.equal(deckIdFromURL(url), "abcdef");
  for (const url of [
    "https://moxfield.com.evil.test/decks/abcdef",
    "https://x@moxfield.com/decks/abcdef",
    "https://moxfield.com:999/decks/abcdef",
    "https://moxfield.com/decks/abcdef/export",
  ])
    assert.throws(() => deckIdFromURL(url));
});
test("Moxfield cache deduplicates concurrent fetches and returns isolated copies", async () => {
  let calls = 0;
  const fetcher = async () => {
    calls++;
    return {
      ok: true,
      json: async () => ({
        name: "fixture",
        mainboard: { a: { card: { name: "Island" }, quantity: 99 } },
        commanders: {
          b: { card: { name: "Shorikai, Genesis Engine" }, quantity: 1 },
        },
      }),
    };
  };
  const [a, b] = await Promise.all([
    getMoxfield("cacheref", { fetcher }),
    getMoxfield("cacheref", { fetcher }),
  ]);
  assert.equal(calls, 1);
  a.cards[0].count = 1;
  assert.equal(b.cards[0].count, 99);
});
for (const status of [401, 403, 429, 404, 500])
  test(
    "Moxfield HTTP " + status + " is actionable and briefly cached",
    async () => {
      let n = 0;
      const fetcher = async () => {
        n++;
        return { ok: false, status };
      };
      await assert.rejects(getMoxfield("deniedref", { fetcher }), /Moxfield/);
      await assert.rejects(getMoxfield("deniedref", { fetcher }), /Moxfield/);
      assert.equal(n, 1);
    },
  );
test("changed, partial and unreadable upstream results are never scored as empty decks", async () => {
  for (const data of [
    {},
    { boards: { mainboard: { cards: [] }, commanders: { cards: [] } } },
    { mainboard: { x: { name: "Island", quantity: 99 } } },
  ])
    assert.throws(() => decodeMoxfield(data));
  await assert.rejects(
    getMoxfield("jsonref1", {
      fetcher: async () => ({
        ok: true,
        json: async () => {
          throw Error("HTML");
        },
      }),
    }),
    /unreadable/,
  );
  await assert.rejects(
    getMoxfield("timeoutr", {
      fetcher: async () => {
        throw Error("timeout");
      },
    }),
    /unavailable/,
  );
});

test("actual incident 100-card inventory with seven verified translated printings keeps exactly 507 points", () => {
  const text = fs.readFileSync(
    new URL("./fixtures/printing-incident-100.txt", import.meta.url),
    "utf8",
  );
  const original = fs.readFileSync(
    new URL("./fixtures/import-incident-100.txt", import.meta.url),
    "utf8",
  );
  const after = evaluate(parseExport(text), prices),
    before = evaluate(parseExport(original), prices);
  assert.equal(after.score.count, 100);
  assert.equal(after.score.points, 507);
  assert.equal(after.score.commandCount, 2);
  assert.equal(after.score.legal, true);
  assert.equal(after.score.warnings.length, 0);
  assert.deepEqual(
    after.deck.cards.map((c) => [c.oracle_id, c.count, c.zone]),
    before.deck.cards.map((c) => [c.oracle_id, c.count, c.zone]),
  );
  assert.ok(after.deck.cards.filter((c) => c.submitted_name).length >= 6);
});
