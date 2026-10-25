// Plain-text curated reference. No live combo service and no scoring dependency.
import fs from "node:fs";
import { randomUUID, createHash } from "node:crypto";
import { resolveCard } from "./legality.mjs";
export const rulingSeed = JSON.parse(
  fs.readFileSync(new URL("./data/rulings/entries.json", import.meta.url)),
);
export const rulingDraftSeed = JSON.parse(
  fs.readFileSync(new URL("./data/rulings/drafts.json", import.meta.url)),
);
export const ruleIndex = JSON.parse(
  fs.readFileSync(
    new URL("./research/rulings/rule-index.json", import.meta.url),
  ),
);
export const categories = [
  "Fundamentals",
  "Shared turns",
  "Protection",
  "Friendly fire",
  "Shared life",
  "Opponent scaling",
  "Cross-controller",
  "False-positive combos",
];
export const classifications = [
  "Works",
  "Doesn’t Work",
  "Friendly Fire",
  "General Rule",
];
export const evidenceTypes = [
  "official_rules",
  "verified_interpretation",
  "house_rule",
];
const fail = (m, status = 400) => Object.assign(Error(m), { status });
const txt = (s, max = 6000) => {
  if (typeof s !== "string" || s.trim().length > max)
    throw fail("Invalid text field");
  return s.trim();
};
const required = (s, max) => {
  const v = txt(s, max);
  if (!v) throw fail("Required text is missing");
  return v;
};
function strings(a, max = 40) {
  if (!Array.isArray(a) || a.length > max) throw fail("Invalid list");
  return a.map((s) => required(s, 2000));
}
export function sourceURL(s) {
  let u;
  try {
    u = new URL(required(s, 2000));
  } catch {
    throw fail("Enter a valid HTTPS source URL");
  }
  if (u.protocol !== "https:" || u.username || u.password)
    throw fail("Sources must use HTTPS without credentials");
  return u.href;
}
export function validateRuling(input, { publishing = false } = {}) {
  if (!input || typeof input !== "object") throw fail("Ruling is required");
  const x = {};
  x.id = required(input.id, 80);
  if (!/^[a-z][a-z0-9-]{2,79}$/.test(x.id))
    throw fail("Use a stable lowercase hyphenated ID");
  for (const k of ["title", "answer", "explanation", "example"])
    x[k] = required(input[k], k === "title" ? 180 : 6000);
  for (const [k, allowed] of Object.entries({
    category: categories,
    classification: classifications,
    evidence_type: evidenceTypes,
    verification_status: ["verified", "needs_review", "rejected"],
  })) {
    if (!allowed.includes(input[k])) throw fail("Invalid " + k);
    x[k] = input[k];
  }
  x.prerequisites = strings(input.prerequisites);
  x.exceptions = strings(input.exceptions);
  x.rule_references = strings(input.rule_references);
  if (
    !x.rule_references.length ||
    x.rule_references.some(
      (r) =>
        !/^\d{3}\.\d+[a-z]?$/.test(r) || (publishing && !ruleIndex.rules[r]),
    )
  )
    throw fail(
      "Use existing Comprehensive Rules references from the recorded edition",
    );
  x.sources = strings(input.sources).map(sourceURL);
  if (!x.sources.length) throw fail("At least one source is required");
  x.sources = [
    ruleIndex.source_url,
    ...new Set(x.sources.filter((s) => s !== ruleIndex.source_url)),
  ];
  x.rules_edition = required(input.rules_edition, 100);
  if (publishing && x.rules_edition !== ruleIndex.edition)
    throw fail(
      "Rules edition does not match the verified source index; refresh evidence before changing edition",
    );
  x.verified_on = txt(input.verified_on || "", 10);
  if (
    x.verified_on &&
    (!/^\d{4}-\d{2}-\d{2}$/.test(x.verified_on) ||
      !Number.isFinite(Date.parse(x.verified_on)) ||
      new Date(x.verified_on).toISOString().slice(0, 10) !== x.verified_on ||
      x.verified_on > new Date().toISOString().slice(0, 10))
  )
    throw fail("Invalid verification date");
  x.verified_by = txt(input.verified_by || "", 160);
  if (!Array.isArray(input.cards) || input.cards.length > 30)
    throw fail("Invalid card list");
  x.cards = input.cards.map((card) => {
    const r = resolveCard(typeof card === "string" ? card : card.name);
    // Never accept fuzzy guesses or user-supplied card URLs as authoritative IDs.
    if (!r) throw fail("Unknown card in ruling: " + (card.name || card));
    const c = r;
    if (card.oracle_id && card.oracle_id !== c.oracle_id)
      throw fail("Card Oracle ID does not match name");
    return {
      oracle_id: c.oracle_id,
      name: c.name,
      url: "https://scryfall.com/search?q=oracleid%3A" + c.oracle_id,
    };
  });
  x.initial_subjects = Array.isArray(input.initial_subjects)
    ? input.initial_subjects.filter(
        (n) => Number.isInteger(n) && n >= 1 && n <= 30,
      )
    : [];
  x.change_note = required(input.change_note, 1200);
  if (
    publishing &&
    (x.verification_status !== "verified" || !x.verified_on || !x.verified_by)
  )
    throw fail(
      "Publication requires verified evidence, reviewer and verification date",
    );
  return x;
}
export async function seedRulings(c) {
  for (const input of [...rulingSeed, ...rulingDraftSeed]) {
    const content = validateRuling(input, {
      publishing: input.verification_status === "verified",
    });
    const hash = createHash("sha256")
      .update(JSON.stringify(input))
      .digest("hex");
    const inserted = await c.query(
      "INSERT INTO ruling_entries(id,seed_hash) VALUES($1,$2) ON CONFLICT DO NOTHING RETURNING id",
      [content.id, hash],
    );
    if (!inserted.rowCount) continue; // Organizer versions and hidden entries are never overwritten.
    const id = randomUUID();
    await c.query(
      "INSERT INTO ruling_versions(id,ruling_id,revision,content,actor,change_note) VALUES($1,$2,1,$3,'research seed',$4)",
      [id, content.id, content, content.change_note],
    );
    if (content.verification_status === "verified")
      await c.query(
        "UPDATE ruling_entries SET published_version_id=$2 WHERE id=$1",
        [content.id, id],
      );
  }
}
export async function publicRulings(c, filters = {}) {
  const query = String(filters.q || "")
    .trim()
    .toLocaleLowerCase();
  if (query.length > 250) throw fail("Search is limited to 250 characters");
  for (const [k, values] of [
    ["category", categories],
    ["classification", classifications],
  ])
    if (filters[k] && !values.includes(filters[k]))
      throw fail("Unsupported " + k);
  const { rows } = await c.query(
    `SELECT e.id,v.id AS version_id,v.revision,v.content,v.created_at FROM ruling_entries e JOIN ruling_versions v ON v.id=e.published_version_id WHERE NOT e.hidden AND v.content->>'verification_status'='verified' ORDER BY v.content->>'title',e.id`,
  );
  const matches = rows.filter(
    (r) =>
      (!filters.category || r.content.category === filters.category) &&
      (!filters.classification ||
        r.content.classification === filters.classification) &&
      (!query ||
        [
          r.content.title,
          r.content.answer,
          r.content.explanation,
          r.content.example,
          ...r.content.cards.map((c) => c.name),
          ...r.content.exceptions,
          ...r.content.prerequisites,
        ]
          .join(" ")
          .toLocaleLowerCase()
          .includes(query)),
  );
  return {
    total: matches.length,
    rulings: matches.map((r) => ({
      ...r.content,
      version_id: r.version_id,
      revision: r.revision,
    })),
    categories,
    classifications,
    rules_edition: ruleIndex.edition,
  };
}
export function installRulingRoutes(app, { q, transaction, audit, admin }) {
  app.get("/api/rulings", async (req, res) =>
    res.json(await publicRulings({ query: q }, req.query)),
  );
  app.get("/api/rulings/:id", async (req, res) => {
    const x = (await publicRulings({ query: q })).rulings.find(
      (r) => r.id === req.params.id,
    );
    if (!x) throw fail("Ruling not found", 404);
    res.json(x);
  });
  // Explicit per-route auth: these routes are mounted before the existing admin prefix.
  app.use("/api/admin/rulings", admin);
  app.get("/api/admin/rulings", async (req, res) => {
    const { rows } = await q(
      `SELECT e.*,v.id AS latest_version_id,v.revision,v.content FROM ruling_entries e JOIN LATERAL(SELECT * FROM ruling_versions WHERE ruling_id=e.id ORDER BY revision DESC LIMIT 1)v ON true ORDER BY v.content->>'title'`,
    );
    res.json({
      rulings: rows,
      categories,
      classifications,
      evidence_types: evidenceTypes,
      rules_edition: ruleIndex.edition,
    });
  });
  app.get("/api/admin/rulings/export", async (req, res) => {
    const data = await transaction(async (c) => {
      await c.query("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ");
      return {
        format: "commander-doubles-rulings-v1",
        exported_at: new Date().toISOString(),
        entries: (await c.query("SELECT * FROM ruling_entries ORDER BY id"))
          .rows,
        versions: (
          await c.query(
            "SELECT * FROM ruling_versions ORDER BY ruling_id,revision",
          )
        ).rows,
      };
    });
    res.attachment("commander-doubles-rulings.json").json(data);
  });
  app.get("/api/admin/rulings/:id/history", async (req, res) => {
    res.json(
      (
        await q(
          "SELECT * FROM ruling_versions WHERE ruling_id=$1 ORDER BY revision DESC",
          [req.params.id],
        )
      ).rows,
    );
  });
  const locked = async (c, id) => {
    const { rows } = await c.query(
      "SELECT * FROM ruling_entries WHERE id=$1 FOR UPDATE",
      [id],
    );
    if (!rows[0]) throw fail("Ruling not found", 404);
    return rows[0];
  };
  async function draft(c, input, base, restored = null) {
    const x = validateRuling(input);
    if (!restored) {
      const last = (
        await c.query(
          "SELECT id FROM ruling_versions WHERE ruling_id=$1 ORDER BY revision DESC LIMIT 1",
          [x.id],
        )
      ).rows[0];
      if ((last?.id || null) !== (base || null))
        throw fail("This ruling changed. Reload before saving.", 409);
    }
    const revision = Number(
      (
        await c.query(
          "SELECT COALESCE(max(revision),0)+1 AS n FROM ruling_versions WHERE ruling_id=$1",
          [x.id],
        )
      ).rows[0].n,
    );
    const id = randomUUID();
    await c.query(
      "INSERT INTO ruling_versions(id,ruling_id,revision,content,actor,change_note,restored_from) VALUES($1,$2,$3,$4,'admin',$5,$6)",
      [id, x.id, revision, x, x.change_note, restored],
    );
    await c.query("UPDATE ruling_entries SET updated_at=now() WHERE id=$1", [
      x.id,
    ]);
    await audit(
      c,
      "admin",
      restored ? "ruling.restore" : "ruling.draft",
      x.id,
      { version_id: id, restored_from: restored },
    );
    return { id, revision, content: x };
  }
  app.post("/api/admin/rulings", async (req, res) => {
    const x = validateRuling(req.body.content);
    const result = await transaction(async (c) => {
      if (
        !(
          await c.query(
            "INSERT INTO ruling_entries(id) VALUES($1) ON CONFLICT DO NOTHING RETURNING id",
            [x.id],
          )
        ).rowCount
      )
        throw fail("ID already exists", 409);
      return draft(c, x, null);
    });
    res.status(201).json(result);
  });
  app.post("/api/admin/rulings/:id/drafts", async (req, res) => {
    res.json(
      await transaction(async (c) => {
        await locked(c, req.params.id);
        if (req.body.content?.id !== req.params.id)
          throw fail("Stable ID cannot change");
        return draft(c, req.body.content, req.body.base_version_id);
      }),
    );
  });
  app.post("/api/admin/rulings/:id/publish", async (req, res) => {
    await transaction(async (c) => {
      await locked(c, req.params.id);
      const v = (
        await c.query(
          "SELECT * FROM ruling_versions WHERE ruling_id=$1 ORDER BY revision DESC LIMIT 1",
          [req.params.id],
        )
      ).rows[0];
      if (!v || v.id !== req.body.version_id)
        throw fail("Publish the latest reviewed version", 409);
      validateRuling(v.content, { publishing: true });
      await c.query(
        "UPDATE ruling_entries SET published_version_id=$2,hidden=false,updated_at=now() WHERE id=$1",
        [req.params.id, v.id],
      );
      await audit(c, "admin", "ruling.publish", req.params.id, {
        version_id: v.id,
      });
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/rulings/:id/hide", async (req, res) => {
    const reason = required(req.body.reason, 1200);
    await transaction(async (c) => {
      await locked(c, req.params.id);
      await c.query(
        "UPDATE ruling_entries SET hidden=true,updated_at=now() WHERE id=$1",
        [req.params.id],
      );
      await audit(c, "admin", "ruling.hide", req.params.id, { reason });
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/rulings/:id/restore", async (req, res) => {
    res.json(
      await transaction(async (c) => {
        await locked(c, req.params.id);
        const v = (
          await c.query(
            "SELECT * FROM ruling_versions WHERE ruling_id=$1 AND id=$2",
            [req.params.id, req.body.version_id],
          )
        ).rows[0];
        if (!v) throw fail("Historical version not found", 404);
        return draft(
          c,
          {
            ...v.content,
            verification_status: "needs_review",
            verified_by: "",
            verified_on: "",
            change_note: required(req.body.reason, 1200),
          },
          null,
          v.id,
        );
      }),
    );
  });
}
