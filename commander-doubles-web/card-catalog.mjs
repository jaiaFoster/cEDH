// Immutable process-lifetime snapshot. Refresh builds a new directory and atomically
// switches the pointer; restart workers to activate. Prices live elsewhere.
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
const read = (p) => fs.readFileSync(new URL(p, import.meta.url));
const hash = (b) => createHash("sha256").update(b).digest("hex");
const pointer = JSON.parse(read("./data/active-catalog.json"));
if (!/^scryfall-[a-zA-Z0-9-]+$/.test(pointer.version))
  throw Error("Invalid catalog version");
const base = "./data/catalogs/" + pointer.version + "/";
const manifestBytes = read(base + "manifest.json");
if (hash(manifestBytes) !== pointer.manifest_sha256)
  throw Error("Catalog manifest checksum mismatch");
export const catalogManifest = JSON.parse(manifestBytes);
function checked(name) {
  const b = read(base + name);
  if (hash(b) !== catalogManifest.files[name])
    throw Error("Catalog checksum mismatch: " + name);
  return b;
}
const json = (name) => JSON.parse(gunzipSync(checked(name)));
export const catalog = gunzipSync(checked("oracle.jsonl.gz"))
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse);
const nameIndexes = new Map();
export function printingAliases(key, folded = false) {
  const name = folded ? "names-folded.bin.gz" : "names-exact.bin.gz";
  if (!nameIndexes.has(name)) nameIndexes.set(name, gunzipSync(checked(name)));
  const data = nameIndexes.get(name),
    target = Buffer.from(key);
  let lo = 0,
    hi = data.length;
  // Binary search sorted UTF-8 records without a many-hundred-thousand-object index.
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2),
      prior = mid === 0 ? -1 : data.lastIndexOf(10, mid - 1),
      start = prior < lo ? lo : prior + 1;
    const tab = data.indexOf(9, start),
      end = data.indexOf(10, tab);
    if (tab < 0 || end < 0) break;
    const d = Buffer.compare(target, data.subarray(start, tab));
    if (!d)
      return data
        .toString("utf8", tab + 1, end)
        .split(",")
        .map((i) => catalog[Number(i)]);
    if (d < 0) hi = start;
    else lo = end + 1;
  }
  return [];
}
const setCollector = json("set-collector.json.gz"),
  printings = gunzipSync(checked("printings.bin.gz"));
if (
  catalog.length !== catalogManifest.cards ||
  printings.length !== catalogManifest.printings * 20
)
  throw Error("Incomplete catalog");
export const equivalentNames = JSON.parse(checked("equivalent-names.json"));
export function printingCards(row) {
  if (row.printing_id) {
    if (!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(row.printing_id))
      return [];
    const key = Buffer.from(row.printing_id.replaceAll("-", ""), "hex");
    let lo = 0,
      hi = printings.length / 20 - 1;
    while (lo <= hi) {
      const m = Math.floor((lo + hi) / 2),
        d = Buffer.compare(key, printings.subarray(m * 20, m * 20 + 16));
      if (!d) return [catalog[printings.readUInt32BE(m * 20 + 16)]];
      if (d < 0) hi = m - 1;
      else lo = m + 1;
    }
    return [];
  }
  return (
    setCollector[(row.set_code + "/" + row.collector_number).toLowerCase()] ||
    []
  ).map((i) => catalog[i]);
}
export const currentSearchMetadata = {
  cards: Object.fromEntries(
    catalog.map((c) => [
      c.oracle_id,
      {
        colors: c.colors ?? [
          ...new Set((c.card_faces || []).flatMap((f) => f.colors || [])),
        ],
        url: c.scryfall_uri,
        ...(c.colors === undefined
          ? { colorFaces: (c.card_faces || []).map((f) => f.colors || []) }
          : {}),
      },
    ]),
  ),
};
