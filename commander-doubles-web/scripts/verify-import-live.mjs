// Read-only integration probe: /api/score never saves teams, decks or tournaments.
import fs from "node:fs";
import { getMoxfield, deckIdFromURL } from "../scoring.mjs";
const base = process.argv[2],
  output = process.argv[3];
if (!base || !output)
  throw Error(
    "Usage: node scripts/verify-import-live.mjs local|https://HOST /path/report.json",
  );
const links = [
  "https://moxfield.com/decks/gvyGvOx0g0uJ7ultPy-pbw",
  "https://moxfield.com/decks/AOcIsMkjW0Kg4V6tkON-eQ",
  "https://moxfield.com/decks/Ar6aYd7qVkK6GoFD4f9P4Q",
];
const results = [];
for (const link of links) {
  const start = Date.now();
  let result;
  try {
    if (base === "local") {
      const d = await getMoxfield(deckIdFromURL(link));
      result = {
        success: true,
        name: d.name,
        count: d.cards.reduce((n, c) => n + c.count, 0),
      };
    } else {
      const r = await fetch(base + "/api/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decks: [{ link }] }),
        signal: AbortSignal.timeout(30000),
      });
      const d = await r.json();
      result = {
        http: r.status,
        success: r.ok,
        ...(r.ok
          ? {
              scores: d.decks.map((s) => ({
                name: s.name,
                count: s.count,
                points: s.points,
                legal: s.legal,
              })),
            }
          : { error: d.error }),
      };
    }
  } catch (e) {
    result = { success: false, error: e.message };
  }
  results.push({ link, ...result, elapsed_ms: Date.now() - start });
}
const report = {
  checked_at: new Date().toISOString(),
  base,
  method:
    base === "local"
      ? "public upstream API from local machine"
      : "read-only deployed /api/score",
  results,
};
fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report));
