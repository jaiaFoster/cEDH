// A deliberately bounded Scryfall-style subset; unsupported syntax is an error.
// Static metadata is indexed once. Every request receives the selected published prices.
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import { catalog, eligibility } from "./legality.mjs";
import { normalizeName } from "./scoring.mjs";

export class SearchError extends Error {
  constructor(message, code = "invalid_query") {
    super(message);
    this.status = 400;
    this.code = code;
  }
}
const bad = (message, code = "invalid_filter") => {
  throw new SearchError(message, code);
};
const colors = "wubrg";
const canonicalNames = new Set(catalog.map((c) => normalizeName(c.name)));
const colorNames = {
  white: "w",
  blue: "u",
  black: "b",
  red: "r",
  green: "g",
  colorless: "",
  c: "",
};
const fields = {
  id: "identity",
  identity: "identity",
  c: "color",
  color: "color",
  t: "type",
  type: "type",
  o: "oracle",
  oracle: "oracle",
  mv: "mv",
  cmc: "mv",
};
export const SORTS = [
  "main_desc",
  "main_asc",
  "command_desc",
  "command_asc",
  "name_asc",
  "name_desc",
  "mv_asc",
  "mv_desc",
];

function colorValue(value) {
  const v = value.toLowerCase();
  if (["m", "multicolor", "multicolored"].includes(v)) return "multicolor";
  if (Object.hasOwn(colorNames, v)) return new Set(colorNames[v]);
  if (!v || [...v].some((x) => !colors.includes(x)))
    bad(
      "Use WUBRG letters, a color name, colorless, or multicolor.",
      "invalid_query",
    );
  return new Set(v);
}
function colorMatch(actual, requested, op) {
  if (requested === "multicolor") {
    if (![":", "=", "!="].includes(op))
      bad(
        "Multicolor supports : or = (or !=), not set comparisons.",
        "unsupported_query",
      );
    return op === "!=" ? actual.length < 2 : actual.length >= 2;
  }
  const a = new Set(actual.map((c) => c.toLowerCase()));
  const subset = [...a].every((x) => requested.has(x));
  const superset = [...requested].every((x) => a.has(x));
  switch (op) {
    case "=":
      return subset && superset;
    case "!=":
      return !(subset && superset);
    case "<=":
      return subset;
    case "<":
      return subset && a.size < requested.size;
    case ">=":
      return superset;
    case ">":
      return superset && a.size > requested.size;
  }
  return false;
}
const numeric = (v, name) => {
  if (
    typeof v !== "string" ||
    !/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(v) ||
    !Number.isFinite(Number(v))
  )
    bad(name + " must be a nonnegative number.");
  return Number(v);
};
const compare = (a, b, op) =>
  ({
    ":": a === b,
    "=": a === b,
    "!=": a !== b,
    "<": a < b,
    "<=": a <= b,
    ">": a > b,
    ">=": a >= b,
  })[op];

// Whitespace separates AND terms, except within double quotes. Apostrophes are names.
export function tokenize(query) {
  if (typeof query !== "string" || query.length > 2000)
    bad("Search must be text of at most 2,000 characters.", "invalid_query");
  const out = [];
  let token = "",
    quoted = false,
    escaped = false,
    literal = false;
  const push = () => {
    if (token || literal) out.push({ value: token, literal });
    token = "";
    literal = false;
  };
  for (const c of query) {
    if (escaped) {
      token += c;
      escaped = false;
      continue;
    }
    if (quoted && c === "\\") {
      escaped = true;
      continue;
    }
    if (c === '"') {
      if (!token) literal = true;
      quoted = !quoted;
      continue;
    }
    if (!quoted && /\s/.test(c)) {
      push();
      continue;
    }
    if (!quoted && /[()|]/.test(c))
      bad(
        "Boolean groups, OR, and regular expressions are not supported. Combine conditions with spaces or AND.",
        "unsupported_query",
      );
    token += c;
  }
  if (quoted || escaped)
    bad("Close the double-quoted search phrase.", "invalid_query");
  push();
  if (out.length > 64)
    bad("Use at most 64 search conditions.", "invalid_query");
  return out;
}

export function compileQuery(query = "") {
  const predicates = tokenize(query).map(({ value, literal }) => {
    if (!literal && /^and$/i.test(value)) return () => true;
    if (!literal && /^(or|not)$/i.test(value))
      bad(
        "OR and NOT are not supported. Use compatible conditions joined by spaces or AND.",
        "unsupported_query",
      );
    let negate = false;
    if (!literal && value.startsWith("-")) {
      negate = true;
      value = value.slice(1);
    }
    if (!value) bad("Enter a search condition after -.", "invalid_query");
    const m = !literal && value.match(/^([a-z_]+)(<=|>=|!=|:|=|<|>)(.*)$/i);
    let predicate;
    if (m) {
      let [, alias, rawOp, input] = m;
      const nestedComparison =
        rawOp === ":" && input.match(/^(<=|>=|!=|=|<|>)(.+)$/);
      if (nestedComparison) [, rawOp, input] = nestedComparison;
      const field = fields[alias.toLowerCase()];
      if (!field)
        bad(
          "Unsupported operator " +
            alias +
            ". Supported: id:, c:, t:, o:, mv:.",
          "unsupported_query",
        );
      if (!input) bad("Enter a value for " + alias + ".", "invalid_query");
      if (input.startsWith("/") || input.startsWith("'"))
        bad(
          "Use literal text in double quotes; regex and single-quoted values are not supported.",
          "unsupported_query",
        );
      if (field === "identity" || field === "color") {
        const request = colorValue(input);
        // Scryfall's id: is a deck-building subset; c: includes the named colors.
        const op =
          rawOp === ":"
            ? request === "multicolor"
              ? ":"
              : request.size === 0
                ? "="
                : field === "identity"
                  ? "<="
                  : ">="
            : rawOp;
        if (request === "multicolor" && ![":", "=", "!="].includes(op))
          bad("Multicolor supports : or = (or !=).", "unsupported_query");
        predicate = (row) =>
          field === "identity"
            ? colorMatch(row.identity, request, op)
            : (row.colorFaces || [row.colors]).some((face) =>
                colorMatch(face, request, op),
              );
      } else if (field === "mv") {
        const amount = numeric(input, "Mana value");
        predicate = (row) => compare(row.mv, amount, rawOp);
      } else {
        if (![":", "=", "!="].includes(rawOp))
          bad(
            alias + " supports literal text matching with :, =, or !=.",
            "unsupported_query",
          );
        const needle = normalizeName(input);
        predicate = (row) =>
          rawOp === "!="
            ? !row[field].includes(needle)
            : row[field].includes(needle);
      }
    } else {
      if (!literal && /[:<>=]/.test(value))
        bad(
          "Unsupported or malformed operator. Supported: id:, c:, t:, o:, mv:.",
          "unsupported_query",
        );
      const exact = !literal && value.startsWith("!");
      const needle = normalizeName(exact ? value.slice(1) : value);
      if (!needle) bad("Enter a card name.", "invalid_query");
      // Prefer a canonical name over a shadow face on a nonplayable art card.
      predicate = (row) =>
        exact
          ? row.nameKey === needle ||
            (!canonicalNames.has(needle) && (row.names || []).includes(needle))
          : row.nameKey.includes(needle);
    }
    return negate ? (row) => !predicate(row) : predicate;
  });
  return (row) => predicates.every((p) => p(row));
}

const metaBytes = gunzipSync(
  fs.readFileSync(new URL("./data/search-metadata.json.gz", import.meta.url)),
);
const metadata = JSON.parse(metaBytes);
const provenance = JSON.parse(
  fs.readFileSync(
    new URL("./data/search-metadata.provenance.json", import.meta.url),
  ),
);
const sha = (b) => createHash("sha256").update(b).digest("hex");
if (
  sha(fs.readFileSync(new URL("./data/oracle.jsonl.gz", import.meta.url))) !==
    metadata.catalog_sha256 ||
  sha(metaBytes) !== provenance.metadata_sha256
)
  throw Error(
    "Search metadata/catalog checksum mismatch. Rebuild the metadata for the pinned catalog.",
  );
export const searchIndex = catalog
  .filter((c) => c.oracle_id)
  .map((c) => {
    const meta = metadata.cards[c.oracle_id];
    if (!meta || !Array.isArray(meta.colors))
      throw Error("Missing verified search metadata: " + c.name);
    const oracle =
      c.oracle_text ||
      (c.card_faces || []).map((f) => f.oracle_text || "").join("\n");
    return Object.freeze({
      name: c.name,
      nameKey: normalizeName(c.name),
      names: [
        ...new Set(
          [
            c.name,
            ...c.name.split(" // "),
            ...(c.card_faces || []).map((f) => f.name),
          ].map(normalizeName),
        ),
      ],
      oracle_id: c.oracle_id,
      identity: c.color_identity || [],
      colors: meta.colors,
      colorFaces: meta.colorFaces || [meta.colors],
      type: normalizeName(c.type_line),
      oracle: normalizeName(oracle),
      typeLine: c.type_line,
      mv: Number(c.cmc || 0),
      legal: c.legalities?.commander === "legal",
      legality: c.legalities?.commander || "not_legal",
      commanderEligible: !!eligibility(c),
      url: meta.url,
    });
  });
if (new Set(searchIndex.map((c) => c.oracle_id)).size !== searchIndex.length)
  throw Error("Duplicate Oracle search identities");

const allowed = new Set([
  "q",
  "offset",
  "limit",
  "version",
  "pointed",
  "points",
  "zone",
  "min",
  "max",
  "identity",
  "identityMode",
  "colorCount",
  "type",
  "mvMin",
  "mvMax",
  "legality",
  "eligible",
  "sort",
]);
const choice = (value, options, name) => {
  if (!options.includes(value)) bad("Unsupported " + name + ": " + value);
  return value;
};
const integer = (value, name, min, max) => {
  const n = numeric(value, name);
  if (!Number.isInteger(n) || n < min || n > max)
    bad(`${name} must be an integer from ${min} to ${max}.`);
  return n;
};
export function parseFilters(params = {}) {
  for (const [key, value] of Object.entries(params)) {
    if (!allowed.has(key)) bad("Unsupported filter: " + key);
    if (typeof value !== "string")
      bad("Supply one text value for " + key + ".");
  }
  if (
    params.pointed !== undefined &&
    !["0", "1", "true", "false"].includes(params.pointed)
  )
    bad("pointed must be 0 or 1.");
  const f = {
    predicate: compileQuery(params.q || ""),
    sort: choice(params.sort || "name_asc", SORTS, "sort"),
    offset: integer(params.offset ?? "0", "Offset", 0, 1000000),
    limit: integer(params.limit ?? "100", "Page size", 1, 100),
    points: choice(
      params.points ||
        (["1", "true"].includes(params.pointed) ? "pointed" : "all"),
      ["all", "pointed", "zero"],
      "point view",
    ),
    zone: choice(
      params.zone || "either",
      ["either", "main", "command"],
      "point location",
    ),
    identityMode: choice(
      params.identityMode || "within",
      ["within", "exact"],
      "identity matching",
    ),
    colorCount: choice(
      params.colorCount || "any",
      ["any", "colorless", "multicolor"],
      "color count",
    ),
    type: normalizeName(params.type || ""),
    legality: choice(
      params.legality || "any",
      ["any", "legal", "banned", "not_legal"],
      "Commander legality",
    ),
    eligible: choice(
      params.eligible || "any",
      ["any", "1"],
      "command eligibility",
    ),
  };
  if (params.identity !== undefined && params.identity !== "") {
    f.identity = colorValue(params.identity);
    if (f.identity === "multicolor")
      bad("Use colorCount=multicolor for the identity category.");
  }
  for (const field of ["min", "max", "mvMin", "mvMax"])
    if (params[field] !== undefined && params[field] !== "") {
      f[field] = numeric(params[field], field);
      if (["min", "max"].includes(field) && !Number.isInteger(f[field]))
        bad("Point ranges use whole numbers.");
    }
  if (f.min !== undefined && f.max !== undefined && f.min > f.max)
    bad("Minimum points cannot exceed maximum points.");
  if (f.mvMin !== undefined && f.mvMax !== undefined && f.mvMin > f.mvMax)
    bad("Minimum mana value cannot exceed maximum mana value.");
  return f;
}
const zonePoints = (r, zone) =>
  zone === "main"
    ? r.main
    : zone === "command"
      ? r.commanderEligible || r.command > 0
        ? r.command
        : null
      : Math.max(r.main, r.command);
export function searchCards(prices, f, index = searchIndex) {
  const matching = [];
  for (const c of index) {
    if (
      !f.predicate(c) ||
      (f.identity &&
        !colorMatch(
          c.identity,
          f.identity,
          f.identityMode === "exact" ? "=" : "<=",
        )) ||
      (f.colorCount === "colorless" && c.identity.length !== 0) ||
      (f.colorCount === "multicolor" && c.identity.length < 2) ||
      (f.type && !c.type.includes(f.type)) ||
      (f.mvMin !== undefined && c.mv < f.mvMin) ||
      (f.mvMax !== undefined && c.mv > f.mvMax) ||
      (f.legality === "legal" && !c.legal) ||
      (f.legality === "banned" && c.legality !== "banned") ||
      (f.legality === "not_legal" && c.legal) ||
      (f.eligible === "1" && !c.commanderEligible)
    )
      continue;
    // Only real, verified catalog identities receive the known-unlisted zero default.
    const p = prices[c.name];
    const row = { ...c, main: p?.main ?? 0, command: p?.command ?? 0 };
    const value = zonePoints(row, f.zone);
    if (
      (f.points !== "all" || f.min !== undefined || f.max !== undefined) &&
      value === null
    )
      continue;
    if (
      (f.points === "pointed" && value <= 0) ||
      (f.points === "zero" && value !== 0) ||
      (f.min !== undefined && value < f.min) ||
      (f.max !== undefined && value > f.max)
    )
      continue;
    matching.push(row);
  }
  const [key, direction] = f.sort.split("_");
  matching.sort((a, b) => {
    let order;
    if (key === "name") order = a.name.localeCompare(b.name, "en");
    else {
      const x = key === "command" ? zonePoints(a, "command") : a[key],
        y = key === "command" ? zonePoints(b, "command") : b[key];
      // Ineligible command-zone entries sort last, in both directions.
      if (x === null || y === null)
        return x === y
          ? a.name.localeCompare(b.name, "en")
          : x === null
            ? 1
            : -1;
      order = x - y;
    }
    return (
      (direction === "desc" ? -order : order) ||
      a.name.localeCompare(b.name, "en") ||
      a.oracle_id.localeCompare(b.oracle_id)
    );
  });
  return {
    total: matching.length,
    offset: f.offset,
    limit: f.limit,
    cards: matching
      .slice(f.offset, f.offset + f.limit)
      .map(({ nameKey, names, oracle, type, ...c }) => c),
  };
}
