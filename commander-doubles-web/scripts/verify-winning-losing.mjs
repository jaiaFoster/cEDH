// Offline audit/export of the new curated FAQ. Never stores the full CR text.
import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  winningLosingSeed,
  winningLosingTopics,
  winningLosingUpdates,
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
if (
  winningLosingTopics.topics.length !== 32 ||
  proof.full_rules_republished !== false
)
  throw Error("Expected 32 covered topics, no full rulebook mirror");
const updates = new Map(winningLosingUpdates.map((r) => [r.id, r]));
const reused = new Set(winningLosingTopics.topics.flatMap((t) => t.ruling_ids));
const reviewed = [
  ...winningLosingSeed,
  ...rulingSeed
    .filter((r) => reused.has(r.id))
    .map((r) => updates.get(r.id) || r),
];
for (const [index, t] of winningLosingTopics.topics.entries()) {
  if (
    t.number !== index + 1 ||
    !winningLosingTopics.groups.includes(t.group) ||
    !t.search_aliases.length
  )
    throw Error("Incomplete coverage manifest");
  if (t.ruling_ids.some((id) => !reviewed.some((r) => r.id === id)))
    throw Error("Uncovered topic " + t.number);
}
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
}
for (const r of reviewed) {
  validateRuling(r, { publishing: true });
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
const ledger = reviewed.map((r) => ({
  ruling_id: r.id,
  verified_on: r.verified_on,
  source_rechecked_on: proof.verified_on,
  rules_edition: r.rules_edition,
  rule_references: Object.fromEntries(
    r.rule_references.map((ref) => [ref, proof.rule_references[ref].sha256]),
  ),
  oracle_text_hashes: Object.fromEntries(
    r.cards.map((c) => [c.oracle_id, cards.get(c.oracle_id).sha256]),
  ),
  original_summary: true,
}));
const coverage =
  "# Required Winning & Losing coverage\n\nThe organizer’s supplied handoff is the authoritative 32-topic checklist. Related topics reuse the same maintained database identity; the collection renders each identity once. All topics have verified published coverage. Topic 11’s split-head aggregation subquestion remains in the unchanged private `commander-aggregation` review entry.\n\n| # | Group | Required question | Maintained ruling IDs |\n| --- | --- | --- | --- |\n" +
  winningLosingTopics.topics
    .map(
      (t) =>
        `| ${t.number} | ${t.group} | ${t.question} | ${t.ruling_ids.map((id) => "`" + id + "`").join(", ")} |`,
    )
    .join("\n") +
  "\n";
const outputs = {
  "research/winning-losing/QUESTIONS.md": coverage,
  "research/winning-losing/public-export.jsonl":
    reviewed.map((r) => JSON.stringify(r)).join("\n") + "\n",
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
    covered_topics: winningLosingTopics.topics.length,
    new_answers: winningLosingSeed.length,
    reviewed_answers: reviewed.length,
    rule_references: Object.keys(proof.rule_references).length,
    oracle_cards: cards.size,
    edition: proof.rules_edition,
    full_rules_republished: false,
  }),
);
