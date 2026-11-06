import fs from "node:fs";
import { createHash } from "node:crypto";
import {
  compositionSeed,
  compositionDraftSeed,
  validateComposition,
  compositionCards,
} from "../compositions.mjs";
import { ruleIndex } from "../rulings.mjs";
const root = new URL("../", import.meta.url);
const read = (p) => fs.readFileSync(new URL(p, root));
const hash = (b) => createHash("sha256").update(b).digest("hex");
const manifest = JSON.parse(read("research/compositions/build-manifest.json"));
for (const [file, sha] of Object.entries(manifest.files))
  if (hash(read(file)) !== sha)
    throw Error("Research artifact changed; regenerate: " + file);
const ids = new Set(),
  pairs = new Set();
for (const p of [...compositionSeed, ...compositionDraftSeed]) {
  validateComposition(p, { publishing: p.verification_status === "verified" });
  if (ids.has(p.id) || pairs.has(p.pair_key))
    throw Error("Duplicate composition identity");
  ids.add(p.id);
  pairs.add(p.pair_key);
}
if (
  compositionSeed.length !== 88 ||
  compositionSeed.filter((p) => p.seed_id).length !== 38 ||
  compositionDraftSeed.length !== 14
)
  throw Error("Coverage mismatch");
const proof = JSON.parse(
  read("research/compositions/source-verification.json"),
);
for (const p of compositionSeed)
  for (const r of p.rule_references)
    if (proof.rule_references[r]?.sha256 !== ruleIndex.rules[r]?.sha256)
      throw Error("Missing exact rule evidence " + r);
if (proof.full_rules_republished !== false)
  throw Error("Do not mirror CR text");
for (const p of compositionSeed)
  for (const d of p.decklists) {
    const original = fs.readFileSync(
      new URL(
        "../../commander-doubles-deck-benchmarks/batch" +
          ("ABC".includes(d.id[0]) ? 1 : "DEF".includes(d.id[0]) ? 2 : 3) +
          "/decks/" +
          d.id +
          ".txt",
        import.meta.url,
      ),
    );
    if (
      hash(original) !== d.sha256 ||
      hash(read("data/compositions/decklists/" + d.id + ".txt")) !== d.sha256
    )
      throw Error("Historical deck altered");
  }
console.log(
  JSON.stringify({
    published_seed: compositionSeed.length,
    initial: 38,
    new_pairs: 50,
    private_rejections: compositionDraftSeed.length,
    card_metadata: Object.keys(compositionCards).length,
    cited_rules: Object.keys(proof.rule_references).length,
    rulebook_mirrored: false,
  }),
);
