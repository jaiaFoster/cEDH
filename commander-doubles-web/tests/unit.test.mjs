import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
  PRICES,
  normalizeName,
  loadPrices,
  parseExport,
  scoreDeck,
  scoreTeam,
  deckIdFromURL,
  decodeMoxfield,
  getMoxfield,
} from "../scoring.mjs";
import {
  catalog,
  resolveCard,
  evaluate,
  legalPair,
  priceTable,
  teamEvaluation,
} from "../legality.mjs";
import { Challonge, matchPlayers } from "../providers.mjs";
export const prices = Object.fromEntries(
  [...new Set(PRICES.values())].map((x) => [
    x.name,
    { main: x.main, command: x.command },
  ]),
);
const deck = (
  text = "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n99 Island",
) => parseExport(text);
test("canonical v3 is byte-identical and has 549 pointed identities", () => {
  assert.equal(new Set(PRICES.values()).size, 549);
  assert.equal(PRICES.get("sol ring").main, 15);
  assert.equal(PRICES.get("the gitrog monster").command, 6);
  assert.equal(PRICES.get("the gitrog monster").main, 1);
  const original = new URL(
    "../../commander-doubles-deck-benchmarks/recalibration/community_review/POINTS_v3.csv",
    import.meta.url,
  );
  if (fs.existsSync(original))
    assert.deepEqual(
      fs.readFileSync(new URL("../points.csv", import.meta.url)),
      fs.readFileSync(original),
    );
});
test("CSV quotes and both MDFC faces resolve to the same point record", () => {
  const t = loadPrices(
    'Card,Main,CZ\n"Glasspool Mimic // Glasspool Shore",1,\n"Talion, the Kindly Lord",5,8\n',
  );
  assert.equal(t.get("glasspool shore").main, 1);
  assert.equal(t.get("talion, the kindly lord").command, 8);
});
test("full pinned catalog recognizes free cards, face aliases, and curly apostrophes", () => {
  assert.ok(catalog.length > 38000);
  assert.equal(
    resolveCard("Acererak the Archlich").name,
    "Acererak the Archlich",
  );
  assert.equal(
    resolveCard("Malakir Mire").name,
    "Malakir Rebirth // Malakir Mire",
  );
  assert.equal(normalizeName("Urza’s Saga"), normalizeName("Urza's Saga"));
});
test("unknown card is an error rather than a zero score", () =>
  assert.throws(
    () =>
      evaluate(
        deck(
          "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Imaginary Unknown Card",
        ),
        prices,
      ),
    /Unknown/,
  ));
test("valid 100-card deck distinguishes legality and separate CZ price", () => {
  const s = evaluate(
    deck(
      "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Sol Ring",
    ),
    prices,
  ).score;
  assert.equal(s.legal, true);
  assert.equal(s.points, 19);
  assert.equal(s.commandCount, 1);
  assert.equal(
    s.pointed.find((c) => c.name === "Shorikai, Genesis Engine").each,
    4,
  );
});
test("known unpointed card stays free, but color identity is checked", () => {
  const s = evaluate(
    deck(
      "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Acererak the Archlich",
    ),
    prices,
  ).score;
  assert.equal(s.points, 4);
  assert.equal(s.legal, false);
  assert.ok(s.errors.some((x) => x.includes("color identity")));
});
test("singleton combines aliases across all zones", () => {
  const s = evaluate(
    deck(
      "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n97 Island\n2 Sol Ring",
    ),
    prices,
  ).score;
  assert.ok(s.errors.some((x) => x.includes("singleton")));
});
test("banned cards are flagged independently of point cost", () => {
  const s = evaluate(
    deck(
      "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Black Lotus",
    ),
    prices,
  ).score;
  assert.equal(s.legal, false);
  assert.ok(s.errors.some((x) => x.includes("not legal")));
});
test("incomplete inventory and zero commanders cannot pass", () => {
  assert.equal(
    evaluate(
      deck("COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island"),
      prices,
    ).score.legal,
    false,
  );
  assert.equal(
    evaluate(
      { name: "none", cards: [{ name: "Island", count: 100, zone: "main" }] },
      prices,
    ).score.legal,
    false,
  );
});
test("legal partners and invalid pair configuration", () => {
  assert.equal(
    legalPair(
      resolveCard("Tymna the Weaver"),
      resolveCard("Kraum, Ludevic's Opus"),
    ),
    true,
  );
  assert.equal(
    legalPair(
      resolveCard("Shorikai, Genesis Engine"),
      resolveCard("The Gitrog Monster"),
    ),
    false,
  );
  assert.equal(
    evaluate(
      deck(
        "COMMANDER\n1 Tymna the Weaver\n1 Kraum, Ludevic's Opus\nMAINBOARD\n98 Island",
      ),
      prices,
    ).score.legal,
    true,
  );
});
test("Background and Doctor companion pairs", () => {
  assert.equal(
    legalPair(
      resolveCard("Wilson, Refined Grizzly"),
      resolveCard("Agent of the Shadow Thieves"),
    ),
    true,
  );
  assert.equal(
    legalPair(resolveCard("The Tenth Doctor"), resolveCard("Rose Tyler")),
    true,
  );
});
test("noncommander and standalone Background rejected", () => {
  for (const name of ["Sol Ring", "Agent of the Shadow Thieves"])
    assert.equal(
      evaluate(deck(`COMMANDER\n1 ${name}\nMAINBOARD\n99 Swamp`), prices).score
        .legal,
      false,
    );
});
test("singleton exception allows any number of Relentless Rats", () =>
  assert.equal(
    evaluate(
      deck(
        "COMMANDER\n1 Marrow-Gnawer\nMAINBOARD\n60 Swamp\n39 Relentless Rats",
      ),
      prices,
    ).score.legal,
    true,
  ));
test("Moxfield v2 and v3 boards exclude sideboards", () => {
  for (const modern of [false, true]) {
    const b = {
      mainboard: {
        cards: {
          a: { quantity: 98, card: { name: "Island" } },
          b: { quantity: 1, card: { name: "Sol Ring" } },
        },
      },
      commanders: {
        cards: {
          c: { quantity: 1, card: { name: "Shorikai, Genesis Engine" } },
        },
      },
      sideboard: {
        cards: { x: { quantity: 1, card: { name: "Force of Will" } } },
      },
    };
    const d = decodeMoxfield(modern ? { boards: b } : b);
    assert.equal(evaluate(d, prices).score.points, 19);
  }
});
test("export parser sections, set metadata, and malformed input", () => {
  const d = parseExport(
    "Commander\n1 Shorikai, Genesis Engine (NEC) 4\nDeck\n99 Island\nSideboard\n1 Force of Will",
  );
  assert.equal(evaluate(d, prices).score.points, 4);
  for (const bad of [
    "99 Island",
    "COMMANDER\n1 Shorikai, Genesis Engine\nDeck\nx Island",
    "COMMANDER\n0 Island",
  ])
    assert.throws(() => parseExport(bad));
});
test("Moxfield URL rejects SSRF and credentials", () => {
  assert.equal(
    deckIdFromURL("https://moxfield.com/decks/oEWXWHM5eEGMmopExLWRCA"),
    "oEWXWHM5eEGMmopExLWRCA",
  );
  for (const url of [
    "http://moxfield.com/decks/abcdef",
    "https://evil.com/decks/abcdef",
    "https://moxfield.com@evil.com/decks/abcdef",
    "https://moxfield.com:88/decks/abcdef",
    "https://moxfield.com/decks/abcdef/extra",
  ])
    assert.throws(() => deckIdFromURL(url));
});
test("72/48, 68/50, 60/60 pass; 73/47, 69/52 fail", () => {
  for (const [a, b, within] of [
    [72, 48, true],
    [68, 50, true],
    [60, 60, true],
    [73, 47, false],
    [69, 52, false],
  ])
    assert.equal(
      scoreTeam([
        { points: a, complete: true },
        { points: b, complete: true },
      ]).within,
      within,
    );
  assert.equal(
    teamEvaluation([
      { points: 4, complete: true, legal: false },
      { points: 4, complete: true, legal: true },
    ]).within,
    false,
  );
});
test("actual Challonge v2.1 participant schema maps to match players", () =>
  assert.deepEqual(
    matchPlayers({
      points_by_participant: [{ participant_id: 123 }, { participant_id: 456 }],
    }),
    ["123", "456"],
  ));
test("Challonge adapter caches no fake success on 429 or downtime", async () => {
  await assert.rejects(
    () =>
      new Challonge({
        key: "test",
        fetcher: async () => ({ ok: false, status: 429 }),
      }).snapshot("1"),
    /429/,
  );
  await assert.rejects(
    () =>
      new Challonge({
        key: "test",
        fetcher: async () => {
          throw Error("timeout");
        },
      }).snapshot("1"),
    /timed out/,
  );
});
test("Challonge pagination traverses full result sets", async () => {
  let calls = 0;
  const p = new Challonge({
    key: "test",
    fetcher: async () => ({
      ok: true,
      json: async () => ({
        data:
          ++calls === 1
            ? Array.from({ length: 100 }, (_, i) => ({
                id: i,
                attributes: { name: "A" },
              }))
            : [{ id: 101, attributes: { name: "B" } }],
      }),
    }),
  });
  const people = await p.participants("1");
  assert.equal(people.length, 101);
  assert.equal(calls, 2);
});

test("round robin request supplies the live API required format options", async () => {
  let body;
  const p = new Challonge({
    key: "test",
    fetcher: async (url, options) => {
      body = JSON.parse(options.body);
      return {
        ok: true,
        json: async () => ({ data: { id: "1", attributes: { url: "test" } } }),
      };
    },
  });
  await p.create("Test", "round robin");
  assert.deepEqual(body.data.attributes.round_robin_options, {
    iterations: 1,
    ranking: "match wins",
  });
});

test("Moxfield denied import and timeout never return a zero score", async () => {
  for (const status of [401, 403, 429])
    await assert.rejects(
      () =>
        getMoxfield("blocked-" + status, {
          fetcher: async () => ({ status, ok: false }),
        }),
      /blocked automated/,
    );
  await assert.rejects(
    () =>
      getMoxfield("timeout-test", {
        fetcher: async () => {
          throw Error("Timeout");
        },
      }),
    /unavailable/,
  );
});
test("invalid Moxfield body cannot silently become a successful empty deck", async () => {
  await assert.rejects(
    () =>
      getMoxfield("empty-test", {
        fetcher: async () => ({
          status: 200,
          ok: true,
          json: async () => ({}),
        }),
      }),
    /no mainboard/,
  );
});
