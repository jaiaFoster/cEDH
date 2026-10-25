import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  rulingSeed,
  rulingDraftSeed,
  validateRuling,
  sourceURL,
  ruleIndex,
} from "../rulings.mjs";
const copy = (x) => structuredClone(x);
test("rulings corpus: all initial subjects, stable identities, references and verified-only seed", () => {
  assert.equal(rulingSeed.length, 57);
  assert.equal(
    new Set([...rulingSeed, ...rulingDraftSeed].map((r) => r.id)).size,
    60,
  );
  assert.deepEqual(
    [...new Set(rulingSeed.flatMap((r) => r.initial_subjects))].sort(
      (a, b) => a - b,
    ),
    Array.from({ length: 30 }, (_, i) => i + 1),
  );
  const ev = JSON.parse(
    fs.readFileSync(
      new URL("../research/rulings/oracle_evidence.json", import.meta.url),
    ),
  );
  const byID = new Map(ev.map((c) => [c.oracle_id, c]));
  for (const r of rulingSeed) {
    assert.doesNotThrow(() => validateRuling(r, { publishing: true }), r.id);
    for (const c of r.cards) {
      assert.equal(byID.get(c.oracle_id)?.name, c.name);
      assert.equal(
        createHash("sha256")
          .update(byID.get(c.oracle_id).oracle_text)
          .digest("hex"),
        byID.get(c.oracle_id).sha256,
      );
    }
    for (const ref of r.rule_references)
      assert.ok(ruleIndex.rules[ref]?.sha256);
  }
  for (const r of rulingDraftSeed)
    assert.throws(() => validateRuling(r, { publishing: true }), /verified/);
});
test("rulings input validation refuses invalid references, identity guesses and unsafe sources", () => {
  for (const patch of [
    { sources: ["javascript:alert(1)"] },
    { sources: ["http://example.com"] },
    { sources: ["https://user:pass@example.com"] },
    { rule_references: ["810.999"] },
    { cards: ["Mysterious invented card"] },
    { cards: [{ name: "Sol Ring", oracle_id: "wrong" }] },
    { verified_on: "2026-02-31" },
    { verification_status: "pending" },
    { category: "invented" },
  ])
    assert.throws(() =>
      validateRuling(
        { ...copy(rulingSeed[0]), ...patch },
        { publishing: true },
      ),
    );
  assert.doesNotThrow(() =>
    validateRuling({
      ...copy(rulingSeed[0]),
      rules_edition: "Older recorded edition",
      rule_references: ["810.999"],
      verification_status: "needs_review",
    }),
  );
  assert.equal(
    sourceURL("https://magic.wizards.com/en/rules"),
    "https://magic.wizards.com/en/rules",
  );
  assert.throws(() =>
    validateRuling(
      { ...copy(rulingSeed[0]), rules_edition: "invented" },
      { publishing: true },
    ),
  );
  assert.throws(() =>
    validateRuling(
      { ...copy(rulingSeed[0]), verified_by: "" },
      { publishing: true },
    ),
  );
});
test("rules-sensitive examples retain controller conditions and verified numerical calculations", () => {
  const by = Object.fromEntries(rulingSeed.map((x) => [x.id, x]));
  assert.match(by["bond-blood-split"].answer, /No/);
  assert.match(by["kinnan-basalt-split"].example, /no mana/);
  assert.match(by["time-sieve-cost"].answer, /they control/);
  assert.match(by["tymna-combat-count"].answer, /combat damage/);
  assert.match(by["silence-chant"].answer, /no creatures can attack/);
  assert.match(by["pox-bloodletter"].example, /−20/);
  assert.equal(60 - 2 * Math.ceil(60 / 3) * 2, -20);
  assert.equal(60 - 2 * 16, 28);
  assert.equal(60 - Math.ceil(60 / 2) - Math.ceil(30 / 2), 15);
  assert.equal(60 - 2 * Math.floor(60 / 2), 0);
  assert.equal(60 - 50, 10);
  assert.match(by["proliferate-poison"].answer, /only one/);
  assert.match(by["expropriate-votes"].example, /can be a land/);
  assert.match(by["aluren-acererak"].example, /119.*29/);
  assert.equal(3 + 29 * 4, 119);
});
