import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { catalog, resolveCard, matchCard, evaluate, evaluateSavedDeck, priceTable } from "../legality.mjs";
import { PRICES, parseExport, decodeMoxfield, getMoxfield } from "../scoring.mjs";
import { createCardResolver } from "../card-resolution.mjs";
const prices = Object.fromEntries([...new Set(PRICES.values())].map((x) => [x.name, x]));
const fixture = (name) => fs.readFileSync(new URL("./fixtures/" + name, import.meta.url), "utf8");
const sample = (name, commander = "Kenrith, the Returned King") => parseExport(`COMMANDER\n1 ${commander}\nMAINBOARD\n98 Island\n1 ${name}`);
const incidentNames = ["Lotus Petal", "Strip Mine", "Bayou", "Cabal Ritual", "Putrid Imp", "Glacial Chasm", "City of Traitors", "Mox Diamond", "Savannah", "Scrubland", "Survival of the Fittest", "Tropical Island", "Tundra", "Underground Sea"];

test("all 14 reported legal cards pass independently of their digital representative printing", () => {
  for (const name of incidentNames) {
    const c = resolveCard(name);
    assert.equal(c.legalities.commander, "legal", name);
    assert.equal(c.digital, true, "regression fixture must exercise the actual cause");
    assert.equal(evaluate(sample(name), prices).score.legal, true, name);
  }
});
test("every legal identity with a nonpaper/digital representative remains legal", () => {
  const affected = catalog.filter(c => c.legalities?.commander === "legal" && (!c.games?.includes("paper") || c.digital));
  assert.equal(affected.length, 1047);
  for (const c of affected) assert.equal(evaluate(sample(c.name), prices).score.legal, true, c.name);
});
test("all Commander-legal and banned canonical identities survive token/face name collisions", () => {
  const aliases = JSON.parse(fs.readFileSync(new URL("../data/name_aliases.json", import.meta.url))).aliases;
  for (const c of catalog.filter(c => ["legal", "banned"].includes(c.legalities?.commander)))
    assert.equal(resolveCard(c.name)?.oracle_id, aliases[c.name] || c.oracle_id, c.name);
  assert.equal(resolveCard("Demonic Tutor").name, "Demonic Tutor");
  assert.equal(resolveCard("Emeritus of Woe").name, "Emeritus of Woe // Demonic Tutor");
  assert.equal(resolveCard("Sol Ring").name, "Sol Ring");
  assert.equal(resolveCard("Storm Crow").name, "Storm Crow");
  assert.equal(resolveCard("Malakir Mire").name, "Malakir Rebirth // Malakir Mire");
});
test("the reported original 100-card text export now passes construction and charges Demonic Tutor", () => {
  const { deck, score } = evaluate(parseExport(fixture("import-incident-100.txt")), prices);
  assert.equal(score.count, 100);
  assert.equal(score.commandCount, 2);
  assert.equal(score.legal, true, score.errors.join("; "));
  assert.equal(score.points, 507);
  assert.equal(score.withinIndividualBudget, false);
  assert.ok(deck.cards.some(c => c.name === "Demonic Tutor"));
  assert.equal(score.pointed.find(c => c.name === "Demonic Tutor").each, 15);
});
test("saved 98-card incident inventory remains 98 with an explicit diagnostic, never fabricated cards", () => {
  const input = JSON.parse(fixture("import-incident-98.json"));
  const before = JSON.stringify(input);
  const { score, deck } = evaluate(input, prices);
  assert.equal(JSON.stringify(input), before);
  assert.equal(deck.cards.length, input.cards.length);
  assert.equal(score.count, 98);
  assert.equal(score.commandCount, 1);
  assert.equal(score.points, 279);
  assert.equal(score.errors.length, 1);
  assert.match(score.errors[0], /97 main-deck cards \+ 1 command-zone cards = 98/);
  assert.equal(score.legal, false);
});
test("small unambiguous typos resolve with canonical pricing and visible persisted evidence", () => {
  for (const [typed, expected] of [["Lotus Petla", "Lotus Petal"], ["Mox Diamnod", "Mox Diamond"], ["Force of Wll", "Force of Will"], ["Vampiric Tutro", "Vampiric Tutor"]]) {
    assert.equal(matchCard(typed).card.name, expected);
    assert.equal(resolveCard(typed), undefined, "admin price editing stays exact");
    const result = evaluate(sample(typed), prices);
    assert.equal(result.score.legal, true);
    assert.equal(result.score.nameCorrections[0].submitted, typed);
    assert.equal(result.score.nameCorrections[0].canonical, expected);
    assert.equal(result.score.points, evaluate(sample(expected), prices).score.points);
    assert.match(result.score.warnings[0], /Review this match/);
    assert.deepEqual(evaluate(result.deck, prices).score.nameCorrections, result.score.nameCorrections);
  }
});
test("punctuation, accents, alternate faces and commander typos resolve without changing zone prices", () => {
  assert.equal(matchCard("Gaeas Cradle").card.name, "Gaea's Cradle");
  assert.equal(matchCard("Æther Vial").card.name, "Aether Vial");
  assert.equal(matchCard("Lim-Duls Vault").card.name, "Lim-Dûl's Vault");
  assert.equal(matchCard("Sink into Stupor/Soporific Springs").card.name, "Sink into Stupor // Soporific Springs");
  const s = evaluate(parseExport("1x Shorikai, Genesis Engin (NEC) 4 *CMDR* *F*\n99 Island"), prices).score;
  assert.equal(s.commandCount, 1);
  assert.equal(s.legal, true);
  assert.equal(s.points, prices["Shorikai, Genesis Engine"].command);
  assert.equal(s.nameCorrections[0].canonical, "Shorikai, Genesis Engine");
});
test("a misspelled banned card remains banned; singleton and identity checks follow corrected identities", () => {
  assert.ok(evaluate(sample("Mana Cryptt"), prices).score.errors.some(e => /banned/.test(e)));
  assert.ok(evaluate(sample("Bayou", "Shorikai, Genesis Engine"), prices).score.errors.some(e => /color identity/.test(e)));
  const s = evaluate(parseExport("COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n97 Island\n1 Lotus Petal\n1 Lotus Petla"), prices).score;
  assert.ok(s.errors.some(e => /singleton/.test(e)));
  const digitalOnly = catalog.find(c => c.name.startsWith("A-") && c.legalities?.commander === "not_legal");
  assert.ok(digitalOnly);
  assert.ok(evaluate(sample(digitalOnly.name), prices).score.errors.some(e => /not legal/.test(e)));
  assert.throws(() => matchCard("A-Delver of Secrets"), /Arena-rebalanced/);
  assert.ok(evaluate(sample("Black Lotus"), prices).score.errors.some(e => /banned/.test(e)));
});
test("ambiguous or distant names fail explicitly, including short ambiguous names", () => {
  const card = (name, id, legality = "legal") => ({ name, oracle_id: id, legalities: { commander: legality } });
  const r = createCardResolver([card("Mox Testa", "a"), card("Mox Testb", "b", "banned"), card("Alpha Mox", "c")]);
  assert.throws(() => r.match("Mox Testc"), /exact name: Mox Testa; Mox Testb/);
  assert.equal(r.match("Alpha Mxo").card.name, "Alpha Mox");
  for (const n of ["Bayo", "Mox", "Imaginary Unknown Card", "x".repeat(200)])
    assert.throws(() => matchCard(n), /Unknown or ambiguous/);
});
test("canonical price names cannot be overwritten by another priced card's face alias", () => {
  const p = priceTable({ "Demonic Tutor": { main: 15 }, "Emeritus of Woe // Demonic Tutor": { main: 2 } });
  assert.equal(p.get("demonic tutor").main, 15);
  assert.equal(p.get("emeritus of woe").main, 2);
});
test("sectioned and inline-commander text exports preserve every count and exclude only side/maybeboards", () => {
  for (const cmd of ["1 Kenrith, the Returned King (ELD) 303 *CMDR* *F*", "1 Kenrith, the Returned King (ELD) 303 *F* *CMDR*"]) {
    const s = evaluate(parseExport(`99 Island\nSideboard:\n1 Black Lotus\n${cmd}`), prices).score;
    assert.equal(s.count, 100);
    assert.equal(s.legal, true);
  }
  const d = parseExport("[Commander]\n1 Kenrith, the Returned King\nDeck:\n98 Island (M21) 310 *F*\n1 Bayou (LEA) 279\n[Sideboard]\n1 Black Lotus");
  assert.equal(evaluate(d, prices).score.legal, true);
});
test("URL data decoder keeps 100 or 98 cards exactly and never filters banned/unrecognized names", () => {
  for (const count of [99, 97]) {
    const d = decodeMoxfield({boards:{mainboard:{cards:{a:{quantity:count,card:{name:"Island"}}}},commanders:{cards:{b:{quantity:1,card:{name:"Shorikai, Genesis Engine"}}}},sideboard:{cards:{c:{quantity:1,card:{name:"Black Lotus"}}}}}});
    assert.equal(evaluate(d, prices).score.count, count + 1);
  }
  const d = decodeMoxfield({mainboard:{cards:{a:{quantity:98,card:{name:"Island"}},b:{quantity:1,card:{name:"Black Lotus"}}}},commanders:{cards:{c:{quantity:1,card:{name:"Kenrith, the Returned King"}}}}});
  assert.equal(d.cards.length, 3);
  assert.ok(evaluate(d, prices).score.errors.some(e => /banned/.test(e)));
  d.cards[1].name = "Imaginary Unknown Card";
  assert.throws(() => evaluate(d, prices), /Unknown/);
});

test("current views recover old face-resolution mistakes from retained text without rewriting history", () => {
  const source = "COMMANDER\n1 Kenrith, the Returned King\nMAINBOARD\n98 Island\n1 Demonic Tutor";
  const wrong = sample("Emeritus of Woe // Demonic Tutor");
  const record = { deck: wrong, source_text: source, score: { points: 0, legal: false } };
  const before = JSON.stringify(record);
  const v = evaluateSavedDeck(record, prices);
  assert.equal(v.score.points, 15);
  assert.equal(v.score.legal, true);
  assert.ok(v.deck.cards.some(c => c.name === "Demonic Tutor"));
  assert.equal(JSON.stringify(record), before);
  // A URL import with no retained source text cannot be guessed backwards.
  const urlOnly = { ...record, source_text: null };
  assert.equal(evaluateSavedDeck(urlOnly, prices).score.points, 0);
});

test("unreadable Moxfield success bodies produce an actionable fallback error", async () => {
  await assert.rejects(() => getMoxfield("unreadable-import-fixture", {
    fetcher: async () => ({ ok: true, status: 200, json: async () => { throw Error("HTML instead of JSON"); } })
  }), /Moxfield returned unreadable deck data.*pasted export/);
});
