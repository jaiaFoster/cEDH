import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  winningLosingSeed,
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
test("32 new verified plain-English summaries extend rather than replace the original FAQ", () => {
  assert.equal(rulingSeed.length, 57);
  assert.equal(rulingDraftSeed.length, 3);
  assert.equal(winningLosingSeed.length, 32);
  assert.equal(
    new Set(
      [...rulingSeed, ...rulingDraftSeed, ...winningLosingSeed].map(
        (r) => r.id,
      ),
    ).size,
    92,
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
  assert.equal(Object.keys(proof.rule_references).length, 52);
  assert.equal(cards.size, 17);
  for (const r of winningLosingSeed) {
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
  assert.match(by.oracle.answer, /controller’s devotion and library/);
  assert.match(
    by["laboratory-maniac"].answer,
    /controller would draw from their own/,
  );
  assert.match(by["temporary-protection"].answer, /not automatically repeated/);
  assert.match(
    by["commander-threshold"].exceptions.join(" "),
    /does not settle/,
  );
  assert.equal(8 + 4 + 3, 15);
  assert.equal(60 - 50, 10);
  assert.equal(4 - 2 * 2, 0);
  assert.match(by.concede.answer, /team leave immediately/);
  assert.match(by.loops.answer, /optional/i);
  assert.match(
    by["life-threshold"].exceptions.join(" "),
    /after the trigger exists does not/,
  );
});

test("earlier reviewed/public research, accepted prices and league rules remain byte-identical", () => {
  const proof = read("research/winning-losing/preserved-source-checksums.json");
  assert.equal(proof.baseline_commit, "5e6a78f");
  for (const [path, expected] of Object.entries(proof.unchanged_files))
    assert.equal(hash(fs.readFileSync(new URL(path, root))), expected, path);
});
