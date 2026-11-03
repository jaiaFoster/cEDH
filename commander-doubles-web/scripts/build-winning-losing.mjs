import fs from "node:fs";
import { resolveCard } from "../legality.mjs";
const root = new URL("../", import.meta.url);
const inputs = JSON.parse(
  fs.readFileSync(new URL("research/winning-losing/faq-input.json", root)),
);
function enrich(inputs) {
  return inputs.map((r) => ({
    ...r,
    cards: r.cards.map((name) => {
      const c = resolveCard(name);
      if (!c) throw Error("Unknown card " + name);
      return {
        oracle_id: c.oracle_id,
        name: c.name,
        url: "https://scryfall.com/search?q=oracleid%3A" + c.oracle_id,
      };
    }),
  }));
}
const entries = enrich(inputs);
const updates = enrich(
  JSON.parse(
    fs.readFileSync(new URL("research/winning-losing/update-input.json", root)),
  ),
);
for (const [path, rows] of [
  ["data/rulings/winning-losing.json", entries],
  ["data/rulings/winning-losing-updates.json", updates],
]) {
  const data = JSON.stringify(rows, null, 2) + "\n",
    dest = new URL(path, root);
  if (process.argv.includes("--check")) {
    if (fs.readFileSync(dest, "utf8") !== data)
      throw Error("Outdated win/loss seed");
  } else fs.writeFileSync(dest, data);
}
console.log(
  JSON.stringify({
    winning_losing_questions: entries.length,
    card_identities: new Set(
      entries.flatMap((r) => r.cards.map((c) => c.oracle_id)),
    ).size,
  }),
);
