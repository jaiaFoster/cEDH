// Explicit offline enrichment from the exact full bulk archive behind the scoring catalog.
import fs from "node:fs";
import { createHash } from "node:crypto";
import { gunzipSync, gzipSync } from "node:zlib";
const root = new URL("../", import.meta.url);
const hash = (b) => createHash("sha256").update(b).digest("hex");
const source = JSON.parse(
  fs.readFileSync(new URL("data/search-metadata-source.json", root)),
);
if (!process.argv[2])
  throw Error(
    "Usage: node scripts/build-search-metadata.mjs /path/to/pinned-oracle.jsonl.gz [--check]",
  );
const bulk = fs.readFileSync(process.argv[2]);
if (hash(bulk) !== source.bulk_sha256)
  throw Error(
    "Full Oracle source hash differs from pinned archive; explicit catalog-version review required",
  );
const cards = new Map(
  gunzipSync(bulk)
    .toString()
    .trim()
    .split("\n")
    .map((s) => {
      const c = JSON.parse(s);
      return [c.oracle_id, c];
    }),
);
const catalogBytes = fs.readFileSync(new URL("data/oracle.jsonl.gz", root));
const pinned = gunzipSync(catalogBytes)
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse);
const records = {};
for (const c of pinned.sort((a, b) => a.oracle_id.localeCompare(b.oracle_id))) {
  const full = cards.get(c.oracle_id);
  if (!full || full.name !== c.name)
    throw Error("Missing or renamed Oracle identity: " + c.name);
  const colors = full.colors ?? [
    ...new Set((full.card_faces || []).flatMap((f) => f.colors || [])),
  ];
  if (
    !Array.isArray(colors) ||
    colors.some((x) => !"WUBRG".includes(x) || x.length !== 1)
  )
    throw Error("Invalid color metadata: " + c.name);
  if (!full.scryfall_uri?.startsWith("https://scryfall.com/card/"))
    throw Error("Missing Scryfall card URL: " + c.name);
  records[c.oracle_id] = {
    colors: [...colors].sort(),
    ...(full.colors === undefined
      ? { colorFaces: (full.card_faces || []).map((f) => f.colors || []) }
      : {}),
    url: full.scryfall_uri,
  };
}
const content = Buffer.from(
  JSON.stringify({
    version: source.version,
    catalog_sha256: hash(catalogBytes),
    cards: records,
  }) + "\n",
);
const provenance =
  JSON.stringify(
    {
      ...source,
      catalog_sha256: hash(catalogBytes),
      metadata_sha256: hash(content),
      records: pinned.length,
      colors:
        "Use the full Oracle colors array, including [] for colorless/devoid. Without a top-level array, preserve individual face arrays for c: matching, plus their union for display. Never infer colors from color identity or mana cost.",
    },
    null,
    2,
  ) + "\n";
for (const [name, bytes] of [
  ["search-metadata.json.gz", gzipSync(content, { level: 9 })],
  ["search-metadata.provenance.json", Buffer.from(provenance)],
]) {
  const out = new URL("data/" + name, root);
  if (process.argv.includes("--check")) {
    if (!fs.readFileSync(out).equals(bytes))
      throw Error("Metadata does not reproduce: " + name);
  } else fs.writeFileSync(out, bytes);
}
console.log(
  `${pinned.length} Oracle identities: search metadata ${process.argv.includes("--check") ? "verified" : "generated"}; scoring catalog unchanged.`,
);
