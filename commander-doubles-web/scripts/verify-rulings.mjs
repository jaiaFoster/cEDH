// Deterministic corpus audit/export; no database or network writes.
import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  rulingSeed,
  rulingDraftSeed,
  validateRuling,
  ruleIndex,
} from "../rulings.mjs";
const root = new URL("../", import.meta.url);
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, root)));
const evidence = read("research/rulings/oracle_evidence.json");
const cards = new Map(evidence.map((c) => [c.oracle_id, c]));
const hash = (s) => createHash("sha256").update(s).digest("hex");
const ids = new Set(),
  subjects = new Set();
for (const r of [...rulingSeed, ...rulingDraftSeed]) {
  validateRuling(r, { publishing: r.verification_status === "verified" });
  if (ids.has(r.id)) throw Error("Duplicate ruling ID: " + r.id);
  ids.add(r.id);
  for (const s of r.initial_subjects) subjects.add(s);
  for (const c of r.cards) {
    const v = cards.get(c.oracle_id);
    if (!v || v.name !== c.name || hash(v.oracle_text) !== v.sha256)
      throw Error("Missing/mismatched Oracle evidence: " + c.name);
  }
}
if (subjects.size !== 30) throw Error("Not all initial subjects reviewed");
const inputs = read("research/rulings/input_audit.json");
for (const s of inputs)
  if (hash(fs.readFileSync(new URL(s.path, root))) !== s.sha256)
    throw Error("Historical source changed: " + s.path);
const ledger = rulingSeed.map((r) => ({
  ruling_id: r.id,
  initial_subjects: r.initial_subjects,
  rule_references: Object.fromEntries(
    r.rule_references.map((ref) => [ref, ruleIndex.rules[ref].sha256]),
  ),
  oracle_text_hashes: Object.fromEntries(
    r.cards.map((c) => [c.oracle_id, cards.get(c.oracle_id).sha256]),
  ),
  verified_on: r.verified_on,
  interpretation_not_official_ruling:
    r.evidence_type === "verified_interpretation",
}));
const outputs = {
  "research/rulings/verification_ledger.json":
    JSON.stringify(ledger, null, 2) + "\n",
  "research/rulings/public_export.jsonl":
    rulingSeed.map((r) => JSON.stringify(r)).join("\n") + "\n",
};
for (const [p, data] of Object.entries(outputs)) {
  if (process.argv.includes("--check")) {
    if (fs.readFileSync(new URL(p, root), "utf8") !== data)
      throw Error("Outdated generated export: " + p);
  } else fs.writeFileSync(new URL(p, root), data);
}
console.log(
  JSON.stringify({
    published_seed: rulingSeed.length,
    draft_seed: rulingDraftSeed.length,
    initial_subjects: subjects.size,
    additional_entries: rulingSeed.filter((r) => !r.initial_subjects.length)
      .length,
    oracle_cards: cards.size,
    edition: ruleIndex.edition,
    review_queue: read("research/rulings/review_queue.json").length,
  }),
);
