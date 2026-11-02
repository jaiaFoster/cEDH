// Research refresh only. Downloaded CR text is held in memory, never mirrored.
import fs from "node:fs";
import { createHash } from "node:crypto";
import { catalogManifest } from "../card-catalog.mjs";
import { resolveCard } from "../legality.mjs";
const root = new URL("../", import.meta.url),
  read = (p) => JSON.parse(fs.readFileSync(new URL(p, root)));
const config = read("data/rulings/official-sources.json");
const hash = (b) => createHash("sha256").update(b).digest("hex");
const sources = [];
async function get(url, options = {}) {
  const r = await fetch(url, {
    ...options,
    headers: {
      "User-Agent":
        "CommanderDoubles-RulesVerification/1.0 (+https://github.com/jaiaFoster/cEDH)",
      Accept: "*/*",
      ...options.headers,
    },
    signal: AbortSignal.timeout(30000),
  });
  if (!r.ok) throw Error(`${url}: HTTP ${r.status}`);
  const bytes = Buffer.from(await r.arrayBuffer());
  sources.push({
    url,
    status: r.status,
    retrieved_at: new Date().toISOString(),
    sha256: hash(bytes),
    bytes: bytes.length,
  });
  return bytes;
}
const landing = (await get(config.primary_url)).toString();
for (const [type, key] of [
  ["txt", "text_url"],
  ["pdf", "pdf_url"],
]) {
  const found = landing.match(
    new RegExp('href="(https:[^"]+MagicCompRules[^"]+\\.' + type + ')"'),
  )?.[1];
  if (!found || new URL(found).href !== config[key])
    throw Error(
      "Current official " +
        type +
        " link changed. Review the new edition before publishing.",
    );
}
const cr = (await get(config.text_url)).toString();
if (!cr.includes("effective as of " + config.rules_edition + "."))
  throw Error("Edition mismatch");
const pdf = await get(config.pdf_url);
if (!pdf.subarray(0, 5).equals(Buffer.from("%PDF-"))) throw Error("Not a PDF");
await get(config.format_url);
const entries = read("data/rulings/winning-losing.json");
const wanted = [...new Set(entries.flatMap((r) => r.rule_references))];
const refs = {};
for (const m of cr.matchAll(
  /^(\d{3}\.\d+[a-z]?)[.]? ([^\r\n]+)(?:\r?\n(?!\d{3}\.)([^\r\n]+))?/gm,
))
  if (wanted.includes(m[1])) refs[m[1]] = { sha256: hash(m[0]) };
if (wanted.some((r) => !refs[r]))
  throw Error(
    "Missing official rule: " + wanted.filter((r) => !refs[r]).join(", "),
  );
const names = [
  ...new Set(
    entries.flatMap((r) =>
      r.cards.map((c) => (typeof c === "string" ? c : c.name)),
    ),
  ),
];
const payload = { identifiers: names.map((name) => ({ name })) };
const collection = JSON.parse(
  await get("https://api.scryfall.com/cards/collection", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  }),
);
if (collection.not_found?.length || collection.data?.length !== names.length)
  throw Error("Card lookup incomplete");
const evidence = collection.data
  .map((c) => {
    const local = resolveCard(c.name);
    if (!local || local.oracle_id !== c.oracle_id)
      throw Error("Local identity mismatch: " + c.name);
    const text =
      c.oracle_text ||
      (c.card_faces || []).map((f) => f.oracle_text || "").join("\n");
    return {
      oracle_id: c.oracle_id,
      name: c.name,
      type_line: c.type_line,
      oracle_text: text,
      sha256: hash(text),
      source_url: c.scryfall_uri,
      verified_on: config.verified_on,
    };
  })
  .sort((a, b) => a.name.localeCompare(b.name));
fs.writeFileSync(
  new URL("research/winning-losing/oracle-evidence.json", root),
  JSON.stringify(evidence, null, 2) + "\n",
);
const report = {
  verified_on: config.verified_on,
  rules_edition: config.rules_edition,
  full_rules_republished: false,
  catalog_version: catalogManifest.version,
  sources,
  rule_references: refs,
  oracle_cards: evidence.length,
};
fs.writeFileSync(
  new URL("research/winning-losing/source-verification.json", root),
  JSON.stringify(report, null, 2) + "\n",
);
console.log(
  JSON.stringify({
    sources: sources.length,
    verified_rules: wanted.length,
    oracle_cards: evidence.length,
    edition: config.rules_edition,
  }),
);
