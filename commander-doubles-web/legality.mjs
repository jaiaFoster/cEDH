import fs from "node:fs";
import zlib from "node:zlib";
import { normalizeName, scoreDeck, scoreTeam, parseExport } from "./scoring.mjs";
import { createCardResolver } from "./card-resolution.mjs";
export const catalog = zlib
  .gunzipSync(
    fs.readFileSync(new URL("./data/oracle.jsonl.gz", import.meta.url)),
  )
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse);
const named = JSON.parse(
  fs.readFileSync(new URL("./data/name_aliases.json", import.meta.url)),
).aliases;
const ids = new Map(catalog.map((c) => [c.oracle_id, c]));
const resolver = createCardResolver(catalog, named);
// Organizer price editing remains exact; tolerant resolution is for deck imports.
export const resolveCard = resolver.exact;
export const matchCard = resolver.match;
export const isCommanderLegal = (card) => card.legalities?.commander === "legal";
const text = (c) =>
  c.oracle_text ||
  (c.card_faces || []).map((f) => f.oracle_text || "").join("\n");
const front = (c) => c.card_faces?.[0] || c;
export function eligibility(c) {
  const t = front(c).type_line || c.type_line || "";
  if (/Legendary.*Enchantment.*Background/.test(t)) return "background";
  if (
    /can be your commander/i.test(text(c)) ||
    c.name === "Grist, the Hunger Tide"
  )
    return "commander";
  return /Legendary/.test(t) &&
    (/Creature|Vehicle/.test(t) ||
      (/Spacecraft/.test(t) && front(c).power !== undefined))
    ? "commander"
    : null;
}
export function legalPair(a, b) {
  const at = text(a),
    bt = text(b);
  if (!eligibility(a) || !eligibility(b)) return false;
  if (/^Partner(?:\s*\(|$)/m.test(at) && /^Partner(?:\s*\(|$)/m.test(bt))
    return true;
  const family = (t) =>
    [...t.matchAll(/Partner\s*[—–-]\s*([^(.\n]+)/gi)]
      .map((m) => normalizeName(m[1]))
      .concat(t.includes("Friends forever") ? ["friends forever"] : []);
  if (family(at).some((x) => family(bt).includes(x))) return true;
  if (
    at.includes("Partner with " + b.name.split(" // ")[0]) &&
    bt.includes("Partner with " + a.name.split(" // ")[0])
  )
    return true;
  if (
    (at.includes("Choose a Background") && eligibility(b) === "background") ||
    (bt.includes("Choose a Background") && eligibility(a) === "background")
  )
    return true;
  const doctor = (c) =>
    /Legendary.*Creature/.test(front(c).type_line || "") &&
    (front(c).type_line || "").split("—").at(-1).trim() === "Time Lord Doctor";
  return (
    (/Doctor['’]s companion/.test(at) && doctor(b)) ||
    (/Doctor['’]s companion/.test(bt) && doctor(a))
  );
}
export function priceTable(prices) {
  const out = new Map();
  for (const [name, p] of Object.entries(prices))
    out.set(normalizeName(name), { name, ...p });
  for (const [name, p] of Object.entries(prices))
    for (const n of name.split(" // "))
      if (!out.has(normalizeName(n))) out.set(normalizeName(n), { name, ...p });
  return out;
}
export function evaluate(deck, prices) {
  const errors = [],
    cards = [],
    counts = new Map(),
    nameCorrections = [];
  for (const row of deck.cards) {
    if (
      !Number.isInteger(row.count) ||
      row.count < 1 ||
      row.count > 100 ||
      !["main", "command"].includes(row.zone)
    )
      throw Error("Invalid deck inventory");
    const { card: c, method } = matchCard(row.name);
    const corrected = method !== "exact" || row.submitted_name;
    const submitted = row.submitted_name || row.name;
    const matchMethod = row.match_method || method;
    cards.push({ ...row, name: c.name, oracle_id: c.oracle_id,
      ...(corrected ? { submitted_name: submitted, match_method: matchMethod } : {}) });
    if (corrected) nameCorrections.push({ submitted, canonical: c.name,
      oracle_id: c.oracle_id, method: matchMethod });
    counts.set(c.oracle_id, (counts.get(c.oracle_id) || 0) + row.count);
    // Oracle bulk selects one representative printing per identity. Its games/digital
    // flags describe that printing, not whether this card has legal paper printings.
    if (!isCommanderLegal(c))
      errors.push(c.name + (c.legalities?.commander === "banned"
        ? ": banned in Commander; not legal in the pinned catalog"
        : ": not legal in Commander in the pinned catalog"));
  }
  const resolved = { ...deck, cards };
  const score = scoreDeck(resolved, priceTable(prices));
  const commanders = cards
    .filter((c) => c.zone === "command")
    .flatMap((r) => Array(r.count).fill(ids.get(r.oracle_id)));
  if (!score.complete)
    errors.push(
      `Imported ${score.count - score.commandCount} main-deck cards + ${score.commandCount} command-zone cards = ${score.count}. Deck must contain exactly 100 cards including one commander or a legal pair. Sideboards and maybeboards are excluded.`,
    );
  if (commanders.length === 1 && eligibility(commanders[0]) !== "commander")
    errors.push(commanders[0].name + " cannot be a standalone commander");
  if (commanders.length === 2 && !legalPair(...commanders))
    errors.push("These commanders are not a legal commander pair");
  const colors = new Set(commanders.flatMap((c) => c.color_identity || []));
  for (const [id, count] of counts) {
    const c = ids.get(id);
    const t = text(c);
    if ((c.color_identity || []).some((col) => !colors.has(col)))
      errors.push(c.name + ": outside commander color identity");
    let max =
      /\bBasic\b/.test(c.type_line || "") ||
      /any number of cards named/i.test(t)
        ? 100
        : 1;
    const m = t.match(/up to (seven|nine|\d+) cards named/i);
    if (m) max = { seven: 7, nine: 9 }[m[1]] || Number(m[1]);
    if (count > max) errors.push(c.name + ": singleton or copy limit exceeded");
  }
  return {
    deck: resolved,
    score: {
      ...score,
      legal: errors.length === 0,
      errors: [...new Set(errors)],
      nameCorrections,
      warnings: nameCorrections.map((c) => `Matched “${c.submitted}” to “${c.canonical}” (${c.method}). Review this match; points and legality use the canonical card.`),
      withinIndividualBudget: score.points <= 72,
      catalogVersion: "oracle-2026-10-20",
      resolutionVersion: "oracle-identity-v2",
      gameplayLegalityApproved: false,
    },
  };
}
// Recompute current views/new submissions from retained source text, without
// rewriting stored versions or any frozen tournament registration.
export function evaluateSavedDeck(record, prices) {
  const raw = record.source_text?.trim()
    ? { ...parseExport(record.source_text), name: record.deck.name }
    : record.deck;
  return evaluate(raw, prices);
}
export function teamEvaluation(scores) {
  const budget = scoreTeam(scores);
  return {
    ...budget,
    budgetWithin: budget.within,
    legal: scores.length === 2 && scores.every((d) => d.legal),
    within: budget.within && scores.every((d) => d.legal),
  };
}
