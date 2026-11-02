// Verify compact index structure and deterministic sampled lookups without network.
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import {
  catalog,
  catalogManifest,
  printingAliases,
  printingCards,
} from "../card-catalog.mjs";
import { matchCard } from "../legality.mjs";
const root = new URL(
  "../data/catalogs/" + catalogManifest.version + "/",
  import.meta.url,
);
let report = {
  version: catalogManifest.version,
  oracle_cards: catalog.length,
  printings: catalogManifest.printings,
  alias_indexes: {},
};
for (const kind of ["exact", "folded"]) {
  const lines = gunzipSync(
    fs.readFileSync(new URL(`names-${kind}.bin.gz`, root)),
  )
    .toString()
    .trimEnd()
    .split("\n");
  let sampled = 0,
    ambiguous = 0,
    prior;
  for (let i = 0; i < lines.length; i++) {
    const [key, values] = lines[i].split("\t"),
      ids = values.split(",").map(Number);
    if (
      prior !== undefined &&
      Buffer.compare(Buffer.from(prior), Buffer.from(key)) >= 0
    )
      throw Error("Unsorted index");
    prior = key;
    if (ids.some((n) => !catalog[n])) throw Error("Unknown identity index");
    if (ids.length > 1) ambiguous++;
    if (i % 97 === 0 || i === lines.length - 1) {
      const got = printingAliases(key, kind === "folded").map(
        (c) => c.oracle_id,
      );
      if (
        JSON.stringify(got) !==
        JSON.stringify(ids.map((n) => catalog[n].oracle_id))
      )
        throw Error("Index lookup mismatch: " + key);
      sampled++;
    }
  }
  report.alias_indexes[kind] = {
    records: lines.length,
    multiple_identities: ambiguous,
    verified_lookups: sampled,
  };
}
const b = gunzipSync(fs.readFileSync(new URL("printings.bin.gz", root)));
let samples = 0;
for (let i = 0; i < b.length / 20; i++) {
  const off = i * 20;
  if (
    i &&
    Buffer.compare(b.subarray(off - 20, off - 4), b.subarray(off, off + 16)) >=
      0
  )
    throw Error("Duplicate or unsorted printing UUID");
  if (i % 251 === 0 || off + 20 === b.length) {
    const hex = b.toString("hex", off, off + 16),
      uuid =
        hex.slice(0, 8) +
        "-" +
        hex.slice(8, 12) +
        "-" +
        hex.slice(12, 16) +
        "-" +
        hex.slice(16, 20) +
        "-" +
        hex.slice(20);
    if (
      printingCards({ printing_id: uuid })[0]?.oracle_id !==
      catalog[b.readUInt32BE(off + 16)].oracle_id
    )
      throw Error("Printing mismatch");
    samples++;
  }
}
report.verified_printing_lookups = samples;
try {
  matchCard("Abafar");
  throw Error("Expected actual localized-name ambiguity");
} catch (e) {
  if (!e.candidates?.length) throw e;
  report.ambiguous_localized_example = {
    name: "Abafar",
    candidates: e.candidates,
  };
}
const output = process.argv[2];
if (output) fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report));
