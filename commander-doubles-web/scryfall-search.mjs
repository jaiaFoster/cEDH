// Optional discovery only. Never mutates the pinned catalog, prices or deck scoring.
import { searchIndex, SearchError } from "./card-search.mjs";
const known = new Map(searchIndex.map((c) => [c.oracle_id, c]));
export const SCRYFALL_PAGE_SIZE = 175;
const unavailable = (message) => Object.assign(Error(message), { status: 503 });
const pause = (ms) => new Promise((r) => setTimeout(r, ms));
export function createScryfallClient({
  fetchImpl = fetch,
  now = Date.now,
  sleep = pause,
} = {}) {
  const cache = new Map();
  let queue = Promise.resolve(),
    pending = 0,
    nextAt = 0,
    cooldown = 0;
  return async function request(query, sort, page) {
    const key = JSON.stringify([query, sort, page]),
      hit = cache.get(key);
    if (hit && hit.expires > now()) return hit.promise;
    if (cooldown > now())
      throw unavailable(
        "Scryfall is rate limiting searches. Please wait, or turn off Search all Magic cards.",
      );
    if (pending >= 12)
      throw unavailable(
        "Live search is busy. Please retry shortly or use the league catalog.",
      );
    const created = now();
    pending++;
    const promise = queue.then(async () => {
      if (now() - created > 5000)
        throw unavailable("Live search is busy. Please retry shortly.");
      if (cooldown > now())
        throw unavailable(
          "Scryfall is rate limiting searches. Please wait and retry.",
        );
      await sleep(Math.max(0, nextAt - now()));
      nextAt = now() + 200;
      const [field, dir] = sort.split("_");
      const url = new URL("https://api.scryfall.com/cards/search");
      url.search = new URLSearchParams({
        q: query,
        unique: "cards",
        order: field === "mv" ? "cmc" : "name",
        dir,
        page: String(page),
        include_extras: "false",
      }).toString();
      let response;
      try {
        response = await fetchImpl(url, {
          headers: {
            "User-Agent":
              "CommanderDoubles/1.0 (+https://github.com/jaiaFoster/cEDH)",
            Accept: "application/json",
          },
          redirect: "error",
          signal: AbortSignal.timeout(8000),
        });
      } catch {
        throw unavailable(
          "Scryfall could not be reached. Retry or turn off Search all Magic cards to search offline.",
        );
      }
      if (response.status === 429) {
        const header = response.headers.get("retry-after");
        const seconds = header === null ? NaN : Number(header);
        const date = Date.parse(header || "");
        const delay = Number.isFinite(seconds)
          ? seconds * 1000
          : Number.isFinite(date)
            ? date - now()
            : 10000;
        cooldown = now() + Math.max(1000, delay);
        throw unavailable(
          "Scryfall is rate limiting searches. Please wait and retry.",
        );
      }
      let data;
      try {
        data = await response.json();
      } catch {
        throw unavailable(
          "Scryfall returned an unreadable response. Please retry.",
        );
      }
      if (response.status === 404 && data.code === "not_found")
        return { data: [], total_cards: 0, has_more: false, warnings: [] };
      if ([400, 422].includes(response.status))
        throw new SearchError(
          typeof data.details === "string"
            ? data.details.slice(0, 1500)
            : "Check your Scryfall search syntax.",
          "invalid_scryfall_query",
        );
      if (!response.ok)
        throw unavailable(
          "Scryfall search is temporarily unavailable. Turn off Search all Magic cards to use the league catalog.",
        );
      if (
        data.object !== "list" ||
        !Array.isArray(data.data) ||
        data.data.length > 175 ||
        !Number.isInteger(data.total_cards) ||
        data.total_cards < 0 ||
        typeof data.has_more !== "boolean"
      )
        throw unavailable("Scryfall returned an unreadable card list.");
      // Retain only display metadata. Never cache monetary prices or league prices.
      return {
        total_cards: data.total_cards,
        has_more: data.has_more,
        warnings: Array.isArray(data.warnings)
          ? data.warnings.filter((w) => typeof w === "string").slice(0, 10)
          : [],
        data: data.data.map((c) => {
          if (typeof c.name !== "string" || !Array.isArray(c.color_identity))
            throw unavailable("Scryfall returned incomplete card metadata.");
          const url = typeof c.scryfall_uri === "string" ? c.scryfall_uri : "";
          return {
            name: c.name,
            oracle_id: typeof c.oracle_id === "string" ? c.oracle_id : null,
            identity: c.color_identity,
            colors: c.colors || [],
            typeLine: c.type_line || "",
            mv: Number(c.cmc || 0),
            legality: c.legalities?.commander || "not_legal",
            url: /^https:\/\/scryfall\.com\//.test(url)
              ? url
              : "https://scryfall.com/search?q=" +
                encodeURIComponent('!"' + c.name + '"'),
          };
        }),
      };
    });
    queue = promise.catch(() => {}); // Serial requests: at most five starts/second, bounded queue.
    const tracked = promise
      .catch((e) => {
        cache.delete(key);
        throw e;
      })
      .finally(() => pending--);
    cache.set(key, { promise: tracked, expires: now() + 60000 });
    while (cache.size > 64) cache.delete(cache.keys().next().value);
    return tracked;
  };
}
export const scryfallClient = createScryfallClient();
// Scryfall requires display options (e.g. include:extras) outside Boolean groups.
// Split only top-level tokens; quoted text, regexes and explicit groups stay intact.
function splitDisplayOptions(query) {
  const terms = [],
    options = [];
  let token = "",
    quoted = false,
    regex = false,
    escaped = false,
    depth = 0;
  const push = () => {
    if (token) {
      (/^(include|unique|order|direction|prefer|display|sort|dir):\S+$/i.test(
        token,
      )
        ? options
        : terms
      ).push(token);
      token = "";
    }
  };
  for (const c of query) {
    if (escaped) {
      token += c;
      escaped = false;
      continue;
    }
    if (c === "\\") {
      token += c;
      escaped = true;
      continue;
    }
    if (c === '"' && !regex) quoted = !quoted;
    if (c === "/" && !quoted && (regex || token.endsWith(":"))) regex = !regex;
    if (!quoted && !regex) {
      if (c === "(") depth++;
      if (c === ")") depth--;
      if (/\s/.test(c) && depth === 0) {
        push();
        continue;
      }
    }
    token += c;
  }
  push();
  return { condition: terms.join(" "), options };
}
export function buildScryfallQuery(f) {
  const { condition, options } = splitDisplayOptions(f.query.trim());
  const parts = [];
  if (f.identity)
    parts.push(
      "id" +
        (f.identityMode === "exact" ? "=" : "<=") +
        ([...f.identity].join("") || "c"),
    );
  if (f.colorCount === "colorless") parts.push("id=c");
  if (f.colorCount === "multicolor") parts.push("id:m");
  if (f.type) parts.push("t:" + JSON.stringify(f.type));
  if (f.mvMin !== undefined) parts.push("mv>=" + f.mvMin);
  if (f.mvMax !== undefined) parts.push("mv<=" + f.mvMax);
  if (f.legality === "legal") parts.push("legal:commander");
  if (f.legality === "banned") parts.push("banned:commander");
  if (f.legality === "not_legal") parts.push("-legal:commander");
  if (f.eligible === "1") parts.push("is:commander");
  if (condition)
    parts.unshift(parts.length ? "(" + condition + ")" : condition);
  if (!parts.length) parts.push("mv>=0");
  return [...parts, ...options].join(" ");
}
export async function searchScryfall(prices, f, client = scryfallClient) {
  if (!["name_asc", "name_desc", "mv_asc", "mv_desc"].includes(f.sort))
    throw new SearchError(
      "Live Scryfall searches support name and mana-value sorting. Use the league catalog for point sorting.",
      "invalid_filter",
    );
  if (f.points !== "all" || f.min !== undefined || f.max !== undefined)
    throw new SearchError(
      "Point filters are available in the league catalog, not live Scryfall discovery.",
      "invalid_filter",
    );
  if (f.limit !== 175 || f.offset % 175 !== 0)
    throw new SearchError(
      "Live Scryfall results use 175 cards per page.",
      "invalid_filter",
    );
  const data = await client(buildScryfallQuery(f), f.sort, 1 + f.offset / 175);
  return {
    source: "scryfall",
    total: data.total_cards,
    offset: f.offset,
    limit: 175,
    has_more: data.has_more,
    warnings: data.warnings,
    cards: data.data.map((c) => {
      const local = known.get(c.oracle_id),
        p = local ? prices[local.name] : null;
      return {
        ...c,
        legal: c.legality === "legal",
        commanderEligible: local?.commanderEligible ?? null,
        priceKnown: !!local,
        priceStatus: local ? "verified" : "unreviewed",
        main: local ? (p?.main ?? 0) : null,
        command: local ? (p?.command ?? 0) : null,
      };
    }),
  };
}
