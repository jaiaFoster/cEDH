// Research-only refresh. Never updates scoring cards, prices or published DB rows.
import fs from "node:fs";
import zlib from "node:zlib";
import crypto from "node:crypto";
const dir = new URL("../research/rulings/", import.meta.url);
const hash = (x) => crypto.createHash("sha256").update(x).digest("hex");
const headers = {
  "User-Agent": "CommanderDoubles-RulingsResearch/1.0",
  Accept: "application/json",
};
async function get(url) {
  const r = await fetch(url, { headers, signal: AbortSignal.timeout(60000) });
  if (!r.ok) throw Error(`${url}: HTTP ${r.status}`);
  return {
    bytes: Buffer.from(await r.arrayBuffer()),
    url,
    retrieved_at: new Date().toISOString(),
  };
}
const landing = await get("https://magic.wizards.com/en/rules");
const match = landing.bytes
  .toString()
  .match(/href="(https:[^"]+MagicCompRules[^\"]+\.txt)"/);
if (!match) throw Error("No official current CR link");
const cr = await get(new URL(match[1]).href);
fs.writeFileSync("/tmp/commander-rulings-current-cr.txt", cr.bytes);
const text = cr.bytes.toString();
const edition = text.match(/effective as of ([^.]+)\./)?.[1];
if (!edition) throw Error("Missing rules edition");
const rules = {};
for (const m of text.matchAll(
  /^(\d{3}\.\d+[a-z]?)[.]? ([^\r\n]+)(?:\r?\n(?!\d{3}\.)([^\r\n]+))?/gm,
))
  rules[m[1]] = { sha256: hash(m[0]) };
fs.writeFileSync(
  new URL("rule-index.json", dir),
  JSON.stringify({ edition, source_url: cr.url, rules }, null, 2) + "\n",
);
const metaResponse = await get("https://api.scryfall.com/bulk-data");
const meta = JSON.parse(metaResponse.bytes).data.find(
  (c) => c.type === "oracle_cards",
);
const download = meta.jsonl_download_uri || meta.download_uri;
if (!download) throw Error("Oracle bulk URL missing");
const bulk = await get(download);
let bytes = bulk.bytes;
if (bytes[0] === 31 && bytes[1] === 139) bytes = zlib.gunzipSync(bytes);
const s = bytes.toString();
const cards = s.trim().startsWith("[")
  ? JSON.parse(s)
  : s.trim().split("\n").map(JSON.parse);
fs.writeFileSync(
  "/tmp/commander-rulings-current-oracle.json",
  JSON.stringify(cards),
);
const format = await get(
  "https://magic.wizards.com/en/formats/two-headed-giant",
);
const apiDocs = await get(
  "https://spacecowmedia.github.io/commander-spellbook-backend/api.html",
);
const license = await get(
  "https://raw.githubusercontent.com/SpaceCowMedia/commander-spellbook-backend/master/LICENSE",
);
const manifest = {
  checked_at: new Date().toISOString(),
  rules_edition: edition,
  sources: [landing, cr, metaResponse, bulk, format, apiDocs, license].map(
    ({ bytes, ...m }) => ({ ...m, sha256: hash(bytes), bytes: bytes.length }),
  ),
  oracle_updated_at: meta.updated_at,
  oracle_card_count: cards.length,
  access: {
    spellbook:
      "Sparse named requests; public attribution/link required; MIT backend code does not establish blanket combo-data redistribution license.",
    runtime: "Local curated corpus; no live third-party dependency.",
  },
};
fs.writeFileSync(
  new URL("verification_manifest.json", dir),
  JSON.stringify(manifest, null, 2) + "\n",
);
console.log(
  JSON.stringify({
    edition,
    rules: Object.keys(rules).length,
    cards: cards.length,
    cr: cr.url,
  }),
);
