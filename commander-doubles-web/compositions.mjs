// Curated research only. No point changes, team mutations or live discovery dependency.
import fs from "node:fs";
import { gunzipSync } from "node:zlib";
import { randomUUID, createHash } from "node:crypto";
import {
  catalog,
  legalPair,
  priceTable,
  resolveCard,
  evaluate,
  teamEvaluation,
} from "./legality.mjs";
import { normalizeName, parseExport } from "./scoring.mjs";
import { equivalentNames } from "./card-catalog.mjs";
import { tokenize, compileQuery } from "./card-search.mjs";
import { sourceURL, ruleIndex, normalizeRulingSearch } from "./rulings.mjs";
const read = (p) => fs.readFileSync(new URL(p, import.meta.url));
export const compositionCards = JSON.parse(
  gunzipSync(read("./data/compositions/cards.json.gz")),
);
export const compositionSeed = JSON.parse(
  read("./data/compositions/entries.json"),
);
export const compositionDraftSeed = JSON.parse(
  read("./data/compositions/drafts.json"),
);
export const compositionStatuses = [
  "Historical benchmark",
  "Active brew",
  "Verified synergy",
  "Research candidate",
  "Requires rules review",
];
export const compositionMechanisms = [
  "Each opponent",
  "Each player",
  "Opponent-trigger scaling",
  "Shared life",
  "Shared team turns",
  "Shared combat",
  "Controller-independent triggers",
  "Cross-player targeting",
  "Cross-deck tutoring",
  "Global effects",
  "Asymmetric restrictions",
  "Alternate win conditions",
  "Counter engines",
  "Borrowed abilities",
  "Public activated abilities",
  "Spell copying",
  "Equipment coordination",
  "Graveyard events",
  "Cross-deck assembly",
];
export const compositionArchetypes = [
  "Turbo combo",
  "Midrange",
  "Control",
  "Prison/stax",
  "Combat",
  "Graveyard",
  "Artifact combo",
  "Spell combo",
  "Resource engine",
  "Creature combo",
];
const localIds = new Map(catalog.map((c) => [c.oracle_id, c]));
export function compositionCard(id) {
  if (compositionCards[id]) return compositionCards[id];
  const c = localIds.get(id);
  if (!c) return null;
  return {
    oracle_id: c.oracle_id,
    name: c.name,
    aliases: (c.card_faces || []).map((f) => f.name),
    oracle_text:
      c.oracle_text ||
      (c.card_faces || []).map((f) => f.oracle_text || "").join("\n"),
    color_identity: c.color_identity || [],
    type_line: c.type_line,
    mana_value: c.cmc || 0,
    legality: c.legalities?.commander,
    eligibility: false,
    scryfall_url:
      c.scryfall_uri ||
      "https://scryfall.com/search?q=oracleid%3A" + c.oracle_id,
    image_url: null,
    source_updated_at: "League pinned catalog; see active catalog manifest",
  };
}

const fail = (s, status = 400) => Object.assign(Error(s), { status });
const hash = (s) => createHash("sha256").update(s).digest("hex");
function string(x, max = 6000, required = true) {
  if (typeof x !== "string" || x.length > max || (required && !x.trim()))
    throw fail("Invalid or missing composition text");
  return x.trim();
}
function strings(x, max = 40) {
  if (!Array.isArray(x) || x.length > max)
    throw fail("Invalid composition list");
  return x.map((v) => string(v));
}
export function compositionPairKey(a, b) {
  return [a.slice().sort().join("+"), b.slice().sort().join("+")]
    .sort()
    .join("|");
}
const knownDecks = new Map(
  compositionSeed.flatMap((p) => p.decklists.map((d) => [d.id, d])),
);
export function validateComposition(input, { publishing = false } = {}) {
  if (!input || typeof input !== "object")
    throw fail("Composition is required");
  const x = {};
  x.id = string(input.id, 80);
  if (!/^[a-z][a-z0-9-]{2,79}$/.test(x.id))
    throw fail("Use a stable lowercase hyphenated ID");
  for (const field of [
    "display_name",
    "archetype",
    "hook",
    "description",
    "overview",
    "interaction",
    "role_a",
    "role_b",
    "rules_edition",
    "catalog_version",
    "verification_notes",
    "change_note",
  ])
    x[field] = string(input[field], field === "display_name" ? 180 : 6000);
  if (!compositionArchetypes.includes(x.archetype))
    throw fail("Unsupported archetype");
  for (const side of ["player_a", "player_b"]) {
    x[side] = strings(input[side], 2);
    if (!x[side].length || new Set(x[side]).size !== x[side].length)
      throw fail("Each player needs one commander or a legal pair");
    const cards = x[side].map((id) => compositionCards[id]);
    if (cards.some((c) => !c?.eligibility || c.legality !== "legal"))
      throw fail("Unknown, banned or ineligible commander");
    if (
      publishing &&
      cards.some((c) =>
        /choose a color before the game begins/i.test(c.oracle_text),
      )
    )
      throw fail(
        "Record the pregame color choice in a reviewed configuration before publishing this commander",
      );
    if (cards.length === 1 && cards[0].eligibility === "background")
      throw fail("A Background requires a compatible commander");
    if (cards.length === 2 && !legalPair(...cards))
      throw fail("These commanders are not a legal partner configuration");
  }
  x.pair_key = compositionPairKey(x.player_a, x.player_b);
  for (const field of [
    "execution",
    "strengths",
    "weaknesses",
    "key_cards",
    "tags",
    "win_conditions",
    "counterplay",
    "rule_references",
    "sources",
  ])
    x[field] = strings(input[field]);
  if (!x.execution.length || x.strengths.length < 2 || x.weaknesses.length < 2)
    throw fail("Add execution, strengths and limitations");
  if (x.tags.some((t) => !compositionMechanisms.includes(t)))
    throw fail("Unsupported synergy mechanism");
  const colors = (side) =>
    new Set(x[side].flatMap((id) => compositionCards[id].color_identity));
  const ca = colors("player_a"),
    cb = colors("player_b");
  x.key_card_owners = {};
  for (const id of x.key_cards) {
    const c = compositionCard(id);
    if (!c || c.legality !== "legal") throw fail("Unknown or banned key card");
    const owner = input.key_card_owners?.[id] || "Either";
    if (!["A", "B", "Either"].includes(owner))
      throw fail("Invalid key-card owner");
    if (
      owner !== "Either" &&
      !c.color_identity.every((v) => (owner === "A" ? ca : cb).has(v))
    )
      throw fail("Key card does not fit Player " + owner + " color identity");
    x.key_card_owners[id] = owner;
    if (
      !c.color_identity.every((v) => ca.has(v)) &&
      !c.color_identity.every((v) => cb.has(v))
    )
      throw fail("Key card fits neither individual deck");
  }
  x.sources = x.sources.map(sourceURL);
  if (
    !x.sources.length ||
    !x.rule_references.length ||
    x.rule_references.some((r) => !ruleIndex.rules[r])
  )
    throw fail("Verified source and existing CR references are required");
  x.research_status = string(input.research_status, 100);
  if (!compositionStatuses.includes(x.research_status))
    throw fail("Unsupported research status");
  x.verification_status = input.verification_status;
  if (!["verified", "needs_review", "rejected"].includes(x.verification_status))
    throw fail("Unsupported verification status");
  x.verified_on = string(input.verified_on || "", 10, false);
  x.verified_by = string(input.verified_by || "", 160, false);
  if (
    x.verified_on &&
    (!/^\d{4}-\d{2}-\d{2}$/.test(x.verified_on) ||
      !Number.isFinite(Date.parse(x.verified_on)) ||
      new Date(x.verified_on).toISOString().slice(0, 10) !== x.verified_on ||
      x.verified_on > new Date().toISOString().slice(0, 10))
  )
    throw fail("Invalid verification date");
  if (
    !Array.isArray(input.oracle_evidence) ||
    input.oracle_evidence.length > 30
  )
    throw fail("Oracle evidence is required");
  x.oracle_evidence = input.oracle_evidence.map((e) => {
    const c = compositionCard(e.oracle_id);
    if (!c || !c.oracle_text.includes(string(e.quote, 3000)))
      throw fail("Oracle quotation does not match recorded text");
    return {
      oracle_id: c.oracle_id,
      quote: e.quote,
      source_url: c.scryfall_url,
    };
  });
  x.featured_order = input.featured_order ?? 100;
  if (
    !Number.isInteger(x.featured_order) ||
    x.featured_order < 0 ||
    x.featured_order > 100000
  )
    throw fail("Invalid featured order");
  if (!Array.isArray(input.decklists) || input.decklists.length > 10)
    throw fail("Invalid deck references");
  x.decklists = input.decklists.map((d) => {
    const url = sourceURL(d.source_url),
      known = knownDecks.get(d.id);
    if (!["a", "b"].includes(d.player)) throw fail("Identify the deck owner");
    if (known) {
      const raw = read("./data/compositions/decklists/" + known.id + ".txt");
      if (hash(raw) !== known.sha256)
        throw Error("Historical inventory checksum mismatch");
      const ids = parseExport(raw.toString())
        .cards.filter((c) => c.zone === "command")
        .map((c) => resolveCard(c.name)?.oracle_id)
        .sort();
      if (
        JSON.stringify(ids) !==
        JSON.stringify(x["player_" + d.player].slice().sort())
      )
        throw fail("Benchmark commanders do not match this player");
      return { ...known, player: d.player };
    }
    return {
      player: d.player,
      source_url: url,
      provenance: string(
        d.provenance || "Community reference; not locally validated.",
        1000,
      ),
    };
  });
  if (
    publishing &&
    (x.verification_status !== "verified" ||
      x.research_status === "Requires rules review" ||
      !x.verified_on ||
      !x.verified_by ||
      x.rules_edition !== ruleIndex.edition ||
      [...x.player_a, ...x.player_b].some(
        (id) => !x.oracle_evidence.some((e) => e.oracle_id === id),
      ))
  )
    throw fail(
      "Publication requires verified mechanics, current rules evidence, date and reviewer",
    );
  return x;
}
export async function seedCompositions(c) {
  for (const input of [...compositionSeed, ...compositionDraftSeed]) {
    const content = validateComposition(input, {
      publishing: input.verification_status === "verified",
    });
    const inserted = await c.query(
      "INSERT INTO composition_entries(id,pair_key,seed_hash) VALUES($1,$2,$3) ON CONFLICT DO NOTHING RETURNING id",
      [content.id, content.pair_key, hash(JSON.stringify(input))],
    );
    if (!inserted.rowCount) continue;
    const id = randomUUID();
    await c.query(
      "INSERT INTO composition_versions(id,composition_id,revision,content,actor,change_note) VALUES($1,$2,1,$3,'research seed',$4)",
      [id, content.id, content, content.change_note],
    );
    if (content.verification_status === "verified")
      await c.query(
        "UPDATE composition_entries SET published_version_id=$2 WHERE id=$1",
        [content.id, id],
      );
  }
}
const allowed = new Set([
  "q",
  "commander",
  "exact",
  "aColors",
  "bColors",
  "teamColors",
  "colorMode",
  "archetype",
  "mechanism",
  "status",
  "decks",
  "min",
  "max",
  "sort",
  "offset",
  "limit",
  "version",
]);
export function parseCompositionFilters(params = {}) {
  for (const [k, v] of Object.entries(params))
    if (!allowed.has(k) || typeof v !== "string")
      throw fail("Unsupported or repeated composition filter: " + k);
  const f = { ...params };
  f.q = string(f.q || "", 250, false);
  f.commander = string(f.commander || "", 160, false);
  const choice = (key, values, def) => {
    f[key] = f[key] || def;
    if (!values.includes(f[key])) throw fail("Unsupported " + key);
  };
  choice("exact", ["0", "1"], "0");
  choice("colorMode", ["within", "exact"], "within");
  choice(
    "sort",
    ["featured", "name", "recent", "archetype", "points_asc", "points_desc"],
    "featured",
  );
  choice("decks", ["any", "full", "concept", "compliant", "historical"], "any");
  for (const [k, values] of [
    ["archetype", compositionArchetypes],
    ["mechanism", compositionMechanisms],
    ["status", compositionStatuses],
  ])
    if (f[k] && !values.includes(f[k])) throw fail("Unsupported " + k);
  for (const k of ["aColors", "bColors", "teamColors"])
    if (f[k] && !/^(?:[wubrg]+|c)$/i.test(f[k]))
      throw fail("Use WUBRG or C for color identity");
  for (const k of ["min", "max", "offset", "limit"])
    if (
      f[k] !== undefined &&
      f[k] !== "" &&
      (!/^\d+$/.test(f[k]) || !Number.isSafeInteger(Number(f[k])))
    )
      throw fail("Use nonnegative integer ranges");
  f.offset = Number(f.offset || 0);
  f.limit = Number(f.limit || 24);
  if (f.offset > 100000 || f.limit < 1 || f.limit > 100)
    throw fail("Invalid composition page");
  f.min = f.min ? Number(f.min) : null;
  f.max = f.max ? Number(f.max) : null;
  if (f.min !== null && f.max !== null && f.min > f.max)
    throw fail("Minimum exceeds maximum");
  if (f.version && !/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(f.version))
    throw fail("Invalid published price version");
  return f;
}
function cz(ids, table) {
  return ids.map((id) => {
    const c = compositionCards[id],
      local = localIds.get(id);
    return {
      ...c,
      aliases: [...c.aliases, ...(equivalentNames[id] || [])],
      command_points: local
        ? (table.get(normalizeName(local.name))?.command ?? 0)
        : null,
      league_identity_known: !!local,
    };
  });
}
const cachedDecks = new Map();
export function enrichComposition(
  content,
  version,
  table = priceTable(version.prices),
) {
  const a = cz(content.player_a, table),
    b = cz(content.player_b, table);
  const sum = (cs) =>
    cs.some((c) => c.command_points === null)
      ? null
      : cs.reduce((v, c) => v + c.command_points, 0);
  const ap = sum(a),
    bp = sum(b);
  const deckScores = content.decklists
    .filter((d) => knownDecks.has(d.id))
    .map((d) => {
      const key = version.id + ":" + d.id;
      let score = cachedDecks.get(key);
      if (!score) {
        score = evaluate(
          parseExport(
            read("./data/compositions/decklists/" + d.id + ".txt").toString(),
          ),
          version.prices,
        ).score;
        if (cachedDecks.size > 200) cachedDecks.clear();
        cachedDecks.set(key, score);
      }
      return {
        id: d.id,
        player: d.player,
        points: score.points,
        count: score.count,
        legal: score.legal,
        errors: score.errors,
        withinIndividualBudget: score.withinIndividualBudget,
        complete: score.complete,
        commandCount: score.commandCount,
      };
    });
  const team = deckScores.length === 2 ? teamEvaluation(deckScores) : null;
  return {
    ...content,
    commanders_a: a,
    commanders_b: b,
    key_card_details: content.key_cards.map(compositionCard),
    colors_a: [...new Set(a.flatMap((c) => c.color_identity))].sort(),
    colors_b: [...new Set(b.flatMap((c) => c.color_identity))].sort(),
    command_zone_points: {
      a: ap,
      b: bp,
      team: ap === null || bp === null ? null : ap + bp,
    },
    deck_scores: deckScores,
    full_team_score: team,
    decklist_status:
      deckScores.length === 2
        ? "Historical benchmark requiring reconstruction"
        : content.decklists.length
          ? "External references; not locally validated"
          : "Concept only",
    budget_validated: !!team?.within,
    price_version: { id: version.id, name: version.name },
  };
}
export function searchCompositions(contents, version, f) {
  const terms = tokenize(f.q)
    .map((t) => {
      if (!t.literal && /[<>=:]/.test(t.value))
        throw fail(
          "Card operators are not composition syntax; use Advanced filters.",
        );
      return normalizeRulingSearch(t.value);
    })
    .filter((t) => t && t !== "and");
  const exact = resolveCard(f.commander);
  const commanderNeedle = normalizeRulingSearch(f.commander);
  const color = (colors, v) =>
    !v ||
    compileQuery("id" + (f.colorMode === "exact" ? "=" : ":") + v)({
      identity: colors,
    });
  const table = priceTable(version.prices);
  let rows = contents
    .map((p) => enrichComposition(p, version, table))
    .filter((p) => {
      const cs = [...p.commanders_a, ...p.commanders_b];
      const blob = normalizeRulingSearch(
        [
          p.display_name,
          p.archetype,
          p.hook,
          p.overview,
          p.interaction,
          p.description,
          p.role_a,
          p.role_b,
          ...p.execution,
          ...p.weaknesses,
          ...p.strengths,
          ...p.win_conditions,
          ...p.tags,
          ...(p.win_conditions.length ? ["win condition"] : []),
          ...(cs.some((c) =>
            /additional combat|extra turn/i.test(c.oracle_text),
          )
            ? ["extra combat extra combats additional combats"]
            : []),
          ...p.oracle_evidence.map((e) => e.quote),
          ...cs.flatMap((c) => [c.name, ...c.aliases]),
          ...p.key_card_details.map((c) => c.name),
        ].join(" "),
      );
      return (
        terms.every((t) => blob.includes(t)) &&
        (!f.commander ||
          cs.some((c) =>
            f.exact === "1"
              ? exact?.oracle_id === c.oracle_id ||
                [c.name, ...c.aliases].some(
                  (n) => normalizeRulingSearch(n) === commanderNeedle,
                )
              : [c.name, ...c.aliases].some((n) =>
                  normalizeRulingSearch(n).includes(commanderNeedle),
                ),
          )) &&
        color(p.colors_a, f.aColors) &&
        color(p.colors_b, f.bColors) &&
        color([...new Set([...p.colors_a, ...p.colors_b])], f.teamColors) &&
        (!f.archetype || p.archetype === f.archetype) &&
        (!f.mechanism || p.tags.includes(f.mechanism)) &&
        (!f.status || p.research_status === f.status) &&
        (f.decks === "any" ||
          (f.decks === "full" && p.deck_scores.length === 2) ||
          (f.decks === "concept" && !p.decklists.length) ||
          (f.decks === "historical" &&
            p.deck_scores.length === 2 &&
            !p.budget_validated) ||
          (f.decks === "compliant" && p.budget_validated)) &&
        (f.min === null ||
          (p.command_zone_points.team !== null &&
            p.command_zone_points.team >= f.min)) &&
        (f.max === null ||
          (p.command_zone_points.team !== null &&
            p.command_zone_points.team <= f.max))
      );
    });
  const compare = (a, b) => {
    if (f.sort.startsWith("points_")) {
      const x = a.command_zone_points.team,
        y = b.command_zone_points.team;
      if (x === null || y === null) return x === y ? 0 : x === null ? 1 : -1;
      return f.sort === "points_asc" ? x - y : y - x;
    }
    if (f.sort === "featured") return a.featured_order - b.featured_order;
    if (f.sort === "recent") return b.verified_on.localeCompare(a.verified_on);
    if (f.sort === "archetype") return a.archetype.localeCompare(b.archetype);
    return a.display_name.localeCompare(b.display_name);
  };
  rows.sort(
    (a, b) =>
      compare(a, b) ||
      a.display_name.localeCompare(b.display_name) ||
      a.id.localeCompare(b.id),
  );
  return {
    total: rows.length,
    offset: f.offset,
    limit: f.limit,
    compositions: rows.slice(f.offset, f.offset + f.limit),
    price_version: { id: version.id, name: version.name },
    archetypes: compositionArchetypes,
    mechanisms: compositionMechanisms,
    statuses: compositionStatuses,
    catalog_version: compositionSeed[0].catalog_version,
  };
}
export function installCompositionRoutes(
  app,
  { q, transaction, audit, admin, currentPrices },
) {
  const publicRows = async () =>
    (
      await q(
        "SELECT v.content,v.id version_id,v.revision FROM composition_entries e JOIN composition_versions v ON e.published_version_id=v.id WHERE NOT e.hidden AND v.content->>'verification_status'='verified'",
      )
    ).rows.map((r) => ({
      ...r.content,
      version_id: r.version_id,
      revision: r.revision,
    }));
  async function version(f) {
    if (!f.version) return currentPrices();
    const p = (
      await q(
        "SELECT * FROM price_versions WHERE id=$1 AND status='published'",
        [f.version],
      )
    ).rows[0];
    if (!p) throw fail("Published price version not found", 404);
    return p;
  }
  app.get("/api/compositions", async (req, res) => {
    const f = parseCompositionFilters(req.query),
      rows = await publicRows();
    const result = searchCompositions(rows, await version(f), f);
    res.json({ ...result, published_total: rows.length });
  });
  app.get("/api/compositions/:id", async (req, res) => {
    const p = (await publicRows()).find((r) => r.id === req.params.id);
    if (!p) throw fail("Composition not found", 404);
    res.json(
      enrichComposition(p, await version(parseCompositionFilters(req.query))),
    );
  });
  app.get("/api/compositions/:id/decks/:deck", async (req, res) => {
    const p = (await publicRows()).find((r) => r.id === req.params.id);
    const d = p?.decklists.find(
      (d) => d.id === req.params.deck && knownDecks.has(d.id),
    );
    if (!d) throw fail("Archived deck not found", 404);
    res
      .attachment(d.id + ".txt")
      .type("text/plain")
      .send(read("./data/compositions/decklists/" + d.id + ".txt"));
  });
  app.use("/api/admin/compositions", admin);
  app.get("/api/admin/compositions", async (req, res) =>
    res.json({
      compositions: (
        await q(
          `SELECT e.*,v.id latest_version_id,v.revision,v.content FROM composition_entries e JOIN LATERAL(SELECT * FROM composition_versions WHERE composition_id=e.id ORDER BY revision DESC LIMIT 1)v ON true ORDER BY v.content->>'display_name'`,
        )
      ).rows,
      statuses: compositionStatuses,
      mechanisms: compositionMechanisms,
      archetypes: compositionArchetypes,
      cards: compositionCards,
      rules_edition: ruleIndex.edition,
    }),
  );
  app.get("/api/admin/compositions/card", async (req, res) => {
    const c = resolveCard(String(req.query.name || ""));
    if (!c) throw fail("Unknown canonical card", 404);
    res.json(compositionCard(c.oracle_id));
  });
  app.get("/api/admin/compositions/:id/history", async (req, res) =>
    res.json(
      (
        await q(
          "SELECT * FROM composition_versions WHERE composition_id=$1 ORDER BY revision DESC",
          [req.params.id],
        )
      ).rows,
    ),
  );
  async function lock(c, id) {
    const row = (
      await c.query(
        "SELECT * FROM composition_entries WHERE id=$1 FOR UPDATE",
        [id],
      )
    ).rows[0];
    if (!row) throw fail("Composition not found", 404);
    return row;
  }
  async function draft(c, input, base, restored = null) {
    const x = validateComposition(input);
    const entry = await lock(c, x.id);
    if (entry.pair_key !== x.pair_key)
      throw fail(
        "Commander configuration is a stable identity; create a new composition instead",
      );
    const last = (
      await c.query(
        "SELECT id,revision FROM composition_versions WHERE composition_id=$1 ORDER BY revision DESC LIMIT 1",
        [x.id],
      )
    ).rows[0];
    if (!restored && (last?.id || null) !== (base || null))
      throw fail("Composition changed; reload before saving", 409);
    const id = randomUUID(),
      revision = (last?.revision || 0) + 1;
    await c.query(
      "INSERT INTO composition_versions(id,composition_id,revision,content,actor,change_note,restored_from) VALUES($1,$2,$3,$4,'admin',$5,$6)",
      [id, x.id, revision, x, x.change_note, restored],
    );
    await c.query(
      "UPDATE composition_entries SET updated_at=now() WHERE id=$1",
      [x.id],
    );
    await audit(
      c,
      "admin",
      restored ? "composition.restore" : "composition.draft",
      x.id,
      { version_id: id },
    );
    return { id, revision, content: x };
  }
  app.post("/api/admin/compositions", async (req, res) => {
    const x = validateComposition(req.body.content);
    res.status(201).json(
      await transaction(async (c) => {
        const prior = await c.query(
          "SELECT id FROM composition_entries WHERE id=$1 OR pair_key=$2",
          [x.id, x.pair_key],
        );
        if (prior.rowCount)
          throw fail(
            "This ID or unordered commander configuration already exists",
            409,
          );
        await c.query(
          "INSERT INTO composition_entries(id,pair_key) VALUES($1,$2)",
          [x.id, x.pair_key],
        );
        return draft(c, x, null);
      }),
    );
  });
  app.post("/api/admin/compositions/:id/drafts", async (req, res) => {
    if (req.params.id !== req.body.content?.id)
      throw fail("Stable ID cannot change");
    res.json(
      await transaction((c) =>
        draft(c, req.body.content, req.body.base_version_id),
      ),
    );
  });
  app.post("/api/admin/compositions/:id/publish", async (req, res) => {
    await transaction(async (c) => {
      await lock(c, req.params.id);
      const v = (
        await c.query(
          "SELECT * FROM composition_versions WHERE composition_id=$1 ORDER BY revision DESC LIMIT 1",
          [req.params.id],
        )
      ).rows[0];
      if (!v || v.id !== req.body.version_id)
        throw fail("Publish the latest reviewed version", 409);
      validateComposition(v.content, { publishing: true });
      await c.query(
        "UPDATE composition_entries SET published_version_id=$2,hidden=false,updated_at=now() WHERE id=$1",
        [req.params.id, v.id],
      );
      await audit(c, "admin", "composition.publish", req.params.id, {
        version_id: v.id,
      });
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/compositions/:id/hide", async (req, res) => {
    const reason = string(req.body.reason, 1200);
    await transaction(async (c) => {
      await lock(c, req.params.id);
      await c.query(
        "UPDATE composition_entries SET hidden=true,updated_at=now() WHERE id=$1",
        [req.params.id],
      );
      await audit(c, "admin", "composition.hide", req.params.id, { reason });
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/compositions/:id/restore", async (req, res) =>
    res.json(
      await transaction(async (c) => {
        await lock(c, req.params.id);
        const v = (
          await c.query(
            "SELECT * FROM composition_versions WHERE composition_id=$1 AND id=$2",
            [req.params.id, req.body.version_id],
          )
        ).rows[0];
        if (!v) throw fail("Historical composition not found", 404);
        return draft(
          c,
          {
            ...v.content,
            verification_status: "needs_review",
            verified_by: "",
            verified_on: "",
            change_note: string(req.body.reason, 1200),
          },
          null,
          v.id,
        );
      }),
    ),
  );
}
