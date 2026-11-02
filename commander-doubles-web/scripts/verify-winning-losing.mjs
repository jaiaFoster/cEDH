// Offline audit/export of the new curated FAQ. Never stores the full CR text.
import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  winningLosingSeed,
  rulingSeed,
  rulingDraftSeed,
  validateRuling,
  ruleIndex,
  officialRulesSources,
} from "../rulings.mjs";
const root = new URL("../", import.meta.url),
  read = (p) => JSON.parse(fs.readFileSync(new URL(p, root)));
const hash = (x) => createHash("sha256").update(x).digest("hex");
const proof = read("research/winning-losing/source-verification.json");
const evidence = read("research/winning-losing/oracle-evidence.json");
const cards = new Map(evidence.map((c) => [c.oracle_id, c]));
if (winningLosingSeed.length !== 32 || proof.full_rules_republished !== false)
  throw Error("Expected 32 curated summaries, no full rulebook mirror");
if (
  proof.rules_edition !== ruleIndex.edition ||
  officialRulesSources.rules_edition !== ruleIndex.edition
)
  throw Error("Rules edition mismatch");
const ids = new Set([...rulingSeed, ...rulingDraftSeed].map((r) => r.id));
for (const r of winningLosingSeed) {
  if (ids.has(r.id)) throw Error("Duplicate ruling ID");
  ids.add(r.id);
  validateRuling(r, { publishing: true });
  if (r.category !== "Winning & Losing") throw Error("Wrong FAQ category");
  for (const ref of r.rule_references) {
    if (
      Object.keys(proof.rule_references[ref] || {}).join(",") !== "sha256" ||
      proof.rule_references[ref].sha256 !== ruleIndex.rules[ref]?.sha256
    )
      throw Error("Missing or changed rule evidence " + ref);
  }
  for (const c of r.cards) {
    const e = cards.get(c.oracle_id);
    if (!e || e.name !== c.name || hash(e.oracle_text) !== e.sha256)
      throw Error("Missing Oracle evidence " + c.name);
  }
}
for (const s of proof.sources) {
  const u = new URL(s.url);
  if (
    u.protocol !== "https:" ||
    s.status !== 200 ||
    !/^[a-f0-9]{64}$/.test(s.sha256)
  )
    throw Error("Unverified source");
}
const ledger = winningLosingSeed.map((r) => ({
  ruling_id: r.id,
  verified_on: r.verified_on,
  rules_edition: r.rules_edition,
  rule_references: Object.fromEntries(
    r.rule_references.map((ref) => [ref, proof.rule_references[ref].sha256]),
  ),
  oracle_text_hashes: Object.fromEntries(
    r.cards.map((c) => [c.oracle_id, cards.get(c.oracle_id).sha256]),
  ),
  original_summary: true,
}));
const outputs = {
  "research/winning-losing/public-export.jsonl":
    winningLosingSeed.map((r) => JSON.stringify(r)).join("\n") + "\n",
  "research/winning-losing/verification-ledger.json":
    JSON.stringify(ledger, null, 2) + "\n",
};
for (const [path, data] of Object.entries(outputs)) {
  const dest = new URL(path, root);
  if (process.argv.includes("--check")) {
    if (fs.readFileSync(dest, "utf8") !== data)
      throw Error("Outdated export " + path);
  } else fs.writeFileSync(dest, data);
}
console.log(
  JSON.stringify({
    winning_losing_questions: winningLosingSeed.length,
    rule_references: Object.keys(proof.rule_references).length,
    oracle_cards: cards.size,
    edition: proof.rules_edition,
    full_rules_republished: false,
  }),
);
