import fs from "node:fs";
import { resolveCard } from "../legality.mjs";
const root = new URL("../", import.meta.url);
const inputs = JSON.parse(
  fs.readFileSync(new URL("research/winning-losing/faq-input.json", root)),
);
const entries = inputs.map((r) => ({
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
const data = JSON.stringify(entries, null, 2) + "\n",
  dest = new URL("data/rulings/winning-losing.json", root);
if (process.argv.includes("--check")) {
  if (fs.readFileSync(dest, "utf8") !== data)
    throw Error("Outdated win/loss seed");
} else fs.writeFileSync(dest, data);
console.log(
  JSON.stringify({
    winning_losing_questions: entries.length,
    card_identities: new Set(
      entries.flatMap((r) => r.cards.map((c) => c.oracle_id)),
    ).size,
  }),
);
