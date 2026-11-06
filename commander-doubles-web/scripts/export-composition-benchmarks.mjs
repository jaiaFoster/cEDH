// Offline comparison against the bundled v3 CSV, never a claim about hosted live prices.
import fs from "node:fs";
import { compositionSeed, enrichComposition } from "../compositions.mjs";
import { PRICES } from "../scoring.mjs";
const prices = Object.fromEntries(
  [...new Set(PRICES.values())].map((x) => [
    x.name,
    { main: x.main, command: x.command },
  ]),
);
const version = {
  id: "bundled-v3",
  name: "Bundled v3 comparison; not a hosted-price claim",
  prices,
};
const enriched = compositionSeed.map((p) => enrichComposition(p, version));
const rows = enriched.map((p) => ({
  id: p.id,
  commander_a: p.commanders_a.map((c) => c.name).join("; "),
  commander_b: p.commanders_b.map((c) => c.name).join("; "),
  cz_a: p.command_zone_points.a,
  cz_b: p.command_zone_points.b,
  cz_team: p.command_zone_points.team,
  mana_values: [...p.commanders_a, ...p.commanders_b].reduce(
    (n, c) => n + c.mana_value,
    0,
  ),
  followup_priority: [
    "seed-10",
    "seed-17",
    "seed-19",
    "discovery-14",
    "discovery-30",
    "discovery-31",
    "discovery-47",
    "discovery-50",
  ].includes(p.id)
    ? "High"
    : "Normal",
  evidence: "Mechanics interpretation only; no competitive results",
  priority_basis: p.weaknesses[0],
}));
const keys = Object.keys(rows[0]),
  quote = (x) => '"' + String(x ?? "").replaceAll('"', '""') + '"';
const outputs = {
  "research/compositions/research-priorities.csv":
    [
      keys.join(","),
      ...rows.map((r) => keys.map((k) => quote(r[k])).join(",")),
    ].join("\n") + "\n",
  "research/compositions/benchmark-recomputation.json":
    JSON.stringify(
      enriched
        .filter((p) => p.deck_scores.length === 2)
        .map((p) => ({
          id: p.id,
          comparison_schedule: version.name,
          command_zone: p.command_zone_points,
          decks: p.deck_scores,
          team: p.full_team_score,
        })),
      null,
      2,
    ) + "\n",
};
for (const [path, body] of Object.entries(outputs)) {
  const file = new URL("../" + path, import.meta.url);
  if (process.argv.includes("--check")) {
    if (fs.readFileSync(file, "utf8") !== body)
      throw Error("Stale comparison export " + path);
  } else fs.writeFileSync(file, body);
}
console.log(
  JSON.stringify({
    comparative_command_zones: rows.length,
    archived_full_teams: enriched.filter((p) => p.deck_scores.length === 2)
      .length,
    price_source: "bundled v3, not hosted API",
  }),
);
