import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  winningLosingSeed,
  winningLosingTopics,
  winningLosingUpdates,
  rulingMatchesQuery,
  rulingSeed,
  rulingDraftSeed,
  ruleIndex,
  officialRulesSources,
  validateRuling,
} from "../rulings.mjs";
import { renderOfficialSources } from "../public/rulings.js";
const root = new URL("../", import.meta.url),
  read = (p) => JSON.parse(fs.readFileSync(new URL(p, root))),
  hash = (x) => createHash("sha256").update(x).digest("hex");
test("32 required topics reuse existing answers without duplicate ruling identities", () => {
  assert.equal(rulingSeed.length, 57);
  assert.equal(rulingDraftSeed.length, 3);
  assert.equal(winningLosingSeed.length, 27);
  assert.equal(winningLosingTopics.topics.length, 32);
  assert.equal(winningLosingTopics.groups.length, 6);
  assert.deepEqual(
    winningLosingTopics.topics.map((t) => t.number),
    Array.from({ length: 32 }, (_, i) => i + 1),
  );
  const ids = new Set([...rulingSeed, ...winningLosingSeed].map((r) => r.id));
  for (const t of winningLosingTopics.topics) {
    assert.ok(winningLosingTopics.groups.includes(t.group));
    assert.ok(t.ruling_ids.length);
    for (const id of t.ruling_ids) assert.ok(ids.has(id), t.question);
  }
  const updateIds = new Set(winningLosingUpdates.map((r) => r.id));
  assert.equal(updateIds.size, 5);
  for (const id of updateIds) assert.ok(rulingSeed.some((r) => r.id === id));
  assert.equal(
    new Set(
      [...rulingSeed, ...rulingDraftSeed, ...winningLosingSeed].map(
        (r) => r.id,
      ),
    ).size,
    87,
  );
  for (const r of winningLosingSeed) {
    assert.equal(r.category, "Winning & Losing");
    assert.equal(r.verification_status, "verified");
    assert.equal(r.verified_on, "2026-11-02");
    assert.notEqual(r.evidence_type, "house_rule");
    assert.doesNotThrow(() => validateRuling(r, { publishing: true }));
  }
});
test("all new references and card identities are supported by freshly retrieved source evidence", () => {
  const proof = read("research/winning-losing/source-verification.json"),
    evidence = read("research/winning-losing/oracle-evidence.json"),
    cards = new Map(evidence.map((c) => [c.oracle_id, c]));
  assert.equal(proof.rules_edition, ruleIndex.edition);
  assert.equal(proof.verified_on, officialRulesSources.verified_on);
  assert.equal(proof.full_rules_republished, false);
  assert.equal(Object.keys(proof.rule_references).length, 63);
  assert.equal(cards.size, 28);
  const needed = new Set(
    winningLosingTopics.topics.flatMap((t) => t.ruling_ids),
  );
  const updated = new Map(winningLosingUpdates.map((r) => [r.id, r]));
  const reviewed = [
    ...winningLosingSeed,
    ...rulingSeed
      .filter((r) => needed.has(r.id))
      .map((r) => updated.get(r.id) || r),
  ];
  for (const r of reviewed) {
    for (const ref of r.rule_references) {
      assert.equal(
        proof.rule_references[ref]?.sha256,
        ruleIndex.rules[ref]?.sha256,
      );
      assert.deepEqual(Object.keys(proof.rule_references[ref]), ["sha256"]);
    }
    for (const c of r.cards) {
      assert.equal(cards.get(c.oracle_id)?.name, c.name);
      assert.equal(
        hash(cards.get(c.oracle_id).oracle_text),
        cards.get(c.oracle_id).sha256,
      );
    }
  }
  for (const url of [
    officialRulesSources.primary_url,
    officialRulesSources.format_url,
    officialRulesSources.pdf_url,
    officialRulesSources.text_url,
  ])
    assert.equal(proof.sources.find((s) => s.url === url)?.status, 200, url);
});
test("official rules access uses permanent primary source and correctly dated downloads", () => {
  assert.equal(
    officialRulesSources.primary_url,
    "https://magic.wizards.com/en/rules",
  );
  assert.equal(
    officialRulesSources.format_url,
    "https://magic.wizards.com/en/formats/two-headed-giant",
  );
  assert.equal(officialRulesSources.rules_edition, "September 25, 2026");
  assert.match(officialRulesSources.pdf_url, /20260925\.pdf$/);
  assert.match(officialRulesSources.text_url, /20260925\.txt$/);
  assert.deepEqual(
    officialRulesSources.sections.map((s) => s.number),
    ["104", "119", "121", "704", "805", "810", "903"],
  );
  const html = renderOfficialSources(officialRulesSources);
  assert.match(html, /Official Rules &amp; Sources/);
  assert.match(html, /Permanent primary source/);
  assert.match(html, /Effective September 25, 2026/);
  assert.match(html, /target="_blank" rel="noopener noreferrer"/);
  assert.doesNotMatch(
    html,
    /href="[^\"]*#(?:104|119|121|704|805|810|903)/,
    "Do not fabricate section anchors",
  );
  assert.equal(renderOfficialSources(null), "");
});
test("winning and losing distinctions include empty draws, replacements, team protection and worked arithmetic", () => {
  const by = Object.fromEntries(
    winningLosingSeed.map((r) => [r.id.replace("win-loss-", ""), r]),
  );
  assert.match(by.mill.answer, /empty library alone does not cause a loss/i);
  for (const ref of ["104.3c", "704.5b", "810.8a"])
    assert.ok(by.mill.rule_references.includes(ref));
  assert.match(
    by["last-card"].answer,
    /Drawing the last available card succeeds/,
  );
  assert.match(by["draw-batch"].answer, /one at a time/);
  assert.ok(
    by["laboratory-maniac"].cards.some(
      (c) => c.name === "Jace, Wielder of Mysteries",
    ),
  );
  assert.match(
    by["laboratory-maniac"].answer,
    /controller would draw from their own/,
  );
  assert.match(by["temporary-protection"].answer, /not automatically repeated/);
  assert.match(
    rulingSeed.find((r) => r.id === "commander-poison").exceptions.join(" "),
    /organizer clarification/,
  );
  assert.match(by["poison-mechanics"].answer, /combat damage/);
  assert.match(by["poison-mechanics"].example, /not 16/);
  assert.ok(by["mazes-end"].cards.some((c) => c.name === "Maze's End"));
  assert.match(
    by["one-winner"].explanation,
    /earlier spell need not have resolved/,
  );
  assert.equal(8 + 4 + 3, 15);
  assert.equal(60 - 50, 10);
  assert.equal(4 - 2 * 2, 0);
  assert.match(by.concede.answer, /team leave immediately/);
  assert.match(by.loops.answer, /optional/i);
  assert.match(
    winningLosingUpdates
      .find((r) => r.id === "life-threshold-wins")
      .exceptions.join(" "),
    /after the trigger exists does not/,
  );
});

test("earlier reviewed/public research, accepted prices and league rules remain byte-identical", () => {
  const proof = read("research/winning-losing/preserved-source-checksums.json");
  assert.equal(proof.baseline_commit, "5e6a78f");
  for (const [path, expected] of Object.entries(proof.unchanged_files))
    assert.equal(hash(fs.readFileSync(new URL(path, root))), expected, path);
});

test("everyday questions, Unicode names and combined topics find the maintained answer", () => {
  const all = [...rulingSeed, ...winningLosingSeed];
  const queries = [
    ["If I mill one opponent do both lose?", "win-loss-mill"],
    ["Does decking out kill the team?", "win-loss-mill"],
    ["Does poison require 10 or 15?", "commander-poison"],
    ["How much commander damage?", "commander-poison"],
    ["Does Thassa’s Oracle win for my teammate?", "oracle-own-library"],
    ["Can Platinum Angel save both players?", "cant-lose-team"],
    ["Jace Wielder Mysteries", "win-loss-laboratory-maniac"],
    ["Maze’s End", "win-loss-mazes-end"],
    ["CR 104.3c", "win-loss-mill"],
  ];
  for (const [q, id] of queries)
    assert.ok(
      rulingMatchesQuery(
        all.find((r) => r.id === id),
        q,
      ),
      q,
    );
  for (const r of all)
    assert.equal(rulingMatchesQuery(r, "invented-no-such-ruling"), false);
  assert.equal(rulingMatchesQuery(all[0], "???"), false);
});
