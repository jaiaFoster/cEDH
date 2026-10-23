import fs from "node:fs";
import zlib from "node:zlib";
import { normalizeName, scoreDeck, scoreTeam } from "./scoring.mjs";
export const catalog = zlib
  .gunzipSync(
    fs.readFileSync(new URL("./data/oracle.jsonl.gz", import.meta.url)),
  )
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse);
const aliases = new Map();
for (const c of catalog) {
  for (const n of [
    c.name,
    ...c.name.split(" // "),
    ...(c.card_faces || []).map((f) => f.name),
  ]) {
    const k = normalizeName(n);
    const old = aliases.get(k);
    if (
      !old ||
      c.legalities?.commander === "legal" ||
      (old.legalities?.commander !== "legal" &&
        c.legalities?.commander === "banned")
    )
      aliases.set(k, c);
  }
}
const named = JSON.parse(
  fs.readFileSync(new URL("./data/name_aliases.json", import.meta.url)),
).aliases;
const ids = new Map(catalog.map((c) => [c.oracle_id, c]));
for (const [n, id] of Object.entries(named))
  if (ids.has(id)) aliases.set(normalizeName(n), ids.get(id));
export const resolveCard = (n) => aliases.get(normalizeName(n));
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
  for (const [name, p] of Object.entries(prices)) {
    for (const n of [name, ...name.split(" // ")])
      out.set(normalizeName(n), { name, ...p });
  }
  return out;
}
export function evaluate(deck, prices) {
  const errors = [],
    cards = [],
    counts = new Map();
  for (const row of deck.cards) {
    if (
      !Number.isInteger(row.count) ||
      row.count < 1 ||
      row.count > 100 ||
      !["main", "command"].includes(row.zone)
    )
      throw Error("Invalid deck inventory");
    const c = resolveCard(row.name);
    if (!c) throw Error("Unknown or ambiguous card: " + row.name);
    cards.push({ ...row, name: c.name, oracle_id: c.oracle_id });
    counts.set(c.oracle_id, (counts.get(c.oracle_id) || 0) + row.count);
    if (
      c.legalities?.commander !== "legal" ||
      !c.games?.includes("paper") ||
      c.digital
    )
      errors.push(c.name + ": not legal in the pinned paper Commander catalog");
  }
  const resolved = { ...deck, cards };
  const score = scoreDeck(resolved, priceTable(prices));
  const commanders = cards
    .filter((c) => c.zone === "command")
    .flatMap((r) => Array(r.count).fill(ids.get(r.oracle_id)));
  if (!score.complete)
    errors.push(
      "Deck must contain exactly 100 cards including one commander or a legal pair",
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
      withinIndividualBudget: score.points <= 72,
      catalogVersion: "oracle-2026-10-20",
      gameplayLegalityApproved: false,
    },
  };
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
