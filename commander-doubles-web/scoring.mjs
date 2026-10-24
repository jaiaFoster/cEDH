import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(ROOT, "public");
const PORT = Number(process.env.PORT || 3000);
const CACHE_MS = 60_000;
const cache = new Map();
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

export function normalizeName(value) {
  return String(value || "")
    .normalize("NFKC")
    .replace(/[’‘]/g, "'")
    .replace(/\s+/g, " ")
    .trim()
    .toLocaleLowerCase("en-US");
}
export function parseCSV(text) {
  const rows = [];
  let row = [],
    cell = "",
    quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") {
      row.push(cell);
      cell = "";
    } else if (c === "\n") {
      row.push(cell.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cell = "";
    } else cell += c;
  }
  if (row.length || cell) {
    row.push(cell.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows;
}
export function loadPrices(csvText) {
  const rows = parseCSV(csvText);
  if (rows[0]?.[0] !== "Card") throw Error("Unsupported points snapshot");
  const table = new Map();
  for (const row of rows.slice(1)) {
    if (row.length < 3 || !row[0]) continue;
    const main = Number(row[1]),
      command = row[2] === "" ? null : Number(row[2]);
    if (
      !Number.isInteger(main) ||
      main < 0 ||
      (command !== null && (!Number.isInteger(command) || command < 0))
    )
      throw Error("Invalid points for " + row[0]);
    const record = { name: row[0], main, command };
    const faces = row[0].split(" // ");
    for (const face of [row[0], ...faces]) {
      const key = normalizeName(face);
      if (table.has(key) && table.get(key).name !== row[0])
        throw Error("Ambiguous price alias: " + face);
      table.set(key, record);
    }
  }
  return table;
}
export const PRICES = loadPrices(
  fs.readFileSync(path.join(ROOT, "points.csv"), "utf8"),
);

export function deckIdFromURL(link) {
  let u;
  try {
    u = new URL(String(link).trim());
  } catch {
    throw Error("Use a complete https://moxfield.com/decks/... link");
  }
  if (
    u.protocol !== "https:" ||
    !["moxfield.com", "www.moxfield.com"].includes(u.hostname) ||
    u.username ||
    u.password ||
    u.port
  ) {
    throw Error("Only public HTTPS Moxfield deck links are accepted");
  }
  const parts = u.pathname.split("/").filter(Boolean);
  if (
    parts[0] !== "decks" ||
    !/^[A-Za-z0-9_-]{6,100}$/.test(parts[1] || "") ||
    parts.length > 2
  ) {
    throw Error(
      "Expected a Moxfield deck link like https://moxfield.com/decks/DECK_ID",
    );
  }
  return parts[1];
}
function entriesFromBoard(board, zone) {
  if (!board) return [];
  const collection = board.cards || board;
  const raw = Array.isArray(collection)
    ? collection
    : Object.entries(collection).map(([key, val]) => ({ _key: key, ...val }));
  if (!Array.isArray(raw)) throw Error("Unexpected deck data from Moxfield");
  return raw.map((entry) => {
    const name =
      entry.card?.name || entry.card?.nameWithFace || entry.name || entry._key;
    const count = Number(entry.quantity ?? entry.count ?? 1);
    if (!name || !Number.isInteger(count) || count < 1 || count > 100)
      throw Error("Unexpected card or count from Moxfield");
    return { name: String(name), count, zone };
  });
}
export function decodeMoxfield(data) {
  const decks = data?.boards;
  const main = entriesFromBoard(data?.mainboard || decks?.mainboard, "main");
  const command = entriesFromBoard(
    data?.commanders || decks?.commanders,
    "command",
  );
  if (!command.length || !main.length)
    throw Error(
      "Moxfield returned no mainboard or commander section. Check that the deck is public and Commander-format.",
    );
  return {
    name: String(data.name || "Moxfield deck").slice(0, 100),
    cards: [...main, ...command],
  };
}
export function parseExport(text) {
  if (typeof text !== "string" || text.length > 50_000)
    throw Error("Export is too large");
  let zone = "main",
    commandFound = false;
  const cards = [];
  for (const original of text.split(/\r?\n/)) {
    let line = original.trim();
    if (!line || line.startsWith("#") || line.startsWith("//")) continue;
    if (/^\[?(commander|commanders)\]?:?$/i.test(line)) {
      zone = "command";
      commandFound = true;
      continue;
    }
    if (/^\[?(mainboard|main|deck)\]?:?$/i.test(line)) {
      zone = "main";
      continue;
    }
    if (
      /^\[?(sideboard|maybeboard|considering|companion|tokens|attractions|stickers)\]?:?$/i.test(
        line,
      )
    ) {
      zone = "ignore";
      continue;
    }
    let inlineCommander = false;
    // Moxfield printing/foil tags can occur in either order.
    let marker;
    while ((marker = line.match(/\s+\*(CMDR|F|E)\*\s*$/i))) {
      if (marker[1].toUpperCase() === "CMDR") inlineCommander = commandFound = true;
      line = line.slice(0, marker.index).trim();
    }
    if (zone === "ignore" && !inlineCommander) continue;
    const match = line.match(
      /^(\d+)x?\s+(.+?)(?:\s+\([A-Za-z0-9_-]+\)(?:\s+[A-Za-z0-9★†*-]+)?)?$/i,
    );
    if (!match) throw Error("Could not read export line: " + line.slice(0, 80));
    const count = Number(match[1]);
    if (!Number.isInteger(count) || count < 1 || count > 100)
      throw Error("Invalid card count");
    cards.push({ name: match[2].trim(), count, zone: inlineCommander ? "command" : zone });
  }
  if (!commandFound)
    throw Error(
      "Export needs a COMMANDER section so command-zone points are counted correctly",
    );
  return { name: "Pasted Moxfield export", cards };
}
export function scoreDeck(deck, table = PRICES) {
  const pointed = [];
  let count = 0,
    commandCount = 0,
    points = 0;
  for (const card of deck.cards) {
    const zone = card.zone === "command" ? "command" : "main";
    const record = table.get(normalizeName(card.name));
    const price =
      zone === "command" ? (record?.command ?? 0) : (record?.main ?? 0);
    const subtotal = card.count * price;
    count += card.count;
    if (zone === "command") commandCount += card.count;
    points += subtotal;
    if (subtotal)
      pointed.push({
        name: record?.name || card.name,
        count: card.count,
        zone,
        each: price,
        points: subtotal,
      });
  }
  pointed.sort((a, b) => b.points - a.points || a.name.localeCompare(b.name));
  const complete = count === 100 && (commandCount === 1 || commandCount === 2);
  return {
    name: deck.name,
    points,
    count,
    commandCount,
    complete,
    pointed,
    warning: complete
      ? null
      : "Expected 100 cards including one commander (or two partners/background pair). Score shown, but deck inventory is incomplete.",
  };
}
export function scoreTeam(decks) {
  const scores = decks.map((d) => d.points);
  if (scores.length !== 2)
    return {
      checked: false,
      reason: "Add your teammate deck to check the combined 120-point budget.",
    };
  const transfer = Math.max(0, scores[0] - 60, scores[1] - 60);
  const other = scores[0] > 60 ? scores[1] : scores[0];
  const within =
    decks.every((x) => x.complete) &&
    scores.every((x) => x <= 72) &&
    scores[0] + scores[1] <= 120 &&
    transfer <= 12 &&
    (transfer === 0 || other + transfer <= 60);
  return {
    checked: true,
    points: scores[0] + scores[1],
    max: 120,
    transfer,
    within,
    complete: decks.every((x) => x.complete),
    label: within ? "Within points budget" : "Over budget or incomplete",
  };
}
export async function getMoxfield(
  id,
  { fetcher = fetch, timeout = 10000 } = {},
) {
  const current = cache.get(id);
  if (current && Date.now() - current.at < CACHE_MS) return current.value;
  const endpoint =
    "https://api2.moxfield.com/v3/decks/all/" + encodeURIComponent(id);
  let response;
  try {
    response = await fetcher(endpoint, {
      signal: AbortSignal.timeout(timeout),
      headers: {
        "User-Agent": "CommanderDoubles-Club-DeckScorer/0.1",
        Accept: "application/json",
      },
      redirect: "error",
    });
  } catch {
    throw Error("Moxfield is unavailable. Use the pasted export option below.");
  }
  if (
    response.status === 403 ||
    response.status === 429 ||
    response.status === 401
  )
    throw Error(
      "Moxfield blocked automated deck imports. Open your deck in Moxfield and paste its text export below.",
    );
  if (!response.ok)
    throw Error(
      "Moxfield returned HTTP " +
        response.status +
        ". Ensure the link is public.",
    );
  let json;
  try {
    json = await response.json();
  } catch {
    throw Error("Moxfield returned unreadable deck data. Use the pasted export option below.");
  }
  const value = decodeMoxfield(json);
  if (cache.size > 100) cache.clear();
  cache.set(id, { at: Date.now(), value });
  return value;
}
