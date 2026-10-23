import express from "express";
import helmet from "helmet";
import { rateLimit } from "express-rate-limit";
import {
  randomUUID,
  randomBytes,
  scryptSync,
  timingSafeEqual,
  createHash,
  createHmac,
} from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { pool, q, transaction, migrate, audit } from "./db.mjs";
import {
  parseExport,
  deckIdFromURL,
  getMoxfield,
  normalizeName,
} from "./scoring.mjs";
import { catalog, resolveCard, evaluate, teamEvaluation } from "./legality.mjs";
import { providerFor, matchPlayers } from "./providers.mjs";
const ROOT = path.dirname(fileURLToPath(import.meta.url));
const fail = (message, status = 400) =>
  Object.assign(new Error(message), { status });
const one = async (c, sql, values) => {
  const r = await c.query(sql, values);
  if (!r.rowCount) throw fail("Record not found", 404);
  return r.rows[0];
};
const id = () => randomUUID();
const digest = (t) => createHash("sha256").update(t).digest("hex");
const isLocked = (e) =>
  e.locked ||
  ["running", "complete", "cancelled"].includes(e.status) ||
  !!(e.lock_at && new Date(e.lock_at) <= new Date());
const label = (x, max = 80) => {
  if (typeof x !== "string" || !x.trim() || x.trim().length > max)
    throw fail("Enter text between 1 and " + max + " characters");
  return x.trim();
};
const date = (x, required = false) => {
  if (!x) {
    if (required) throw fail("Date is required");
    return null;
  }
  if (
    typeof x !== "string" ||
    !/(Z|[+-]\d\d:\d\d)$/.test(x) ||
    !Number.isFinite(Date.parse(x))
  )
    throw fail("Use an ISO date with a time-zone offset");
  return new Date(x).toISOString();
};
const bool = (x) => x === true;
export function passwordHash(password, salt = randomBytes(16).toString("hex")) {
  return salt + ":" + scryptSync(password, salt, 64).toString("hex");
}
const storedHash =
  process.env.ADMIN_PASSWORD_HASH ||
  (process.env.ADMIN_PASSWORD
    ? passwordHash(process.env.ADMIN_PASSWORD)
    : null);
function checkPassword(password) {
  if (!storedHash || typeof password !== "string" || password.length > 512)
    return false;
  const [salt, hash] = storedHash.split(":");
  if (!salt || !hash) return false;
  const a = scryptSync(password, salt, 64),
    b = Buffer.from(hash, "hex");
  return a.length === b.length && timingSafeEqual(a, b);
}
const ipHash = (req) =>
  createHmac("sha256", process.env.SESSION_SECRET || "local")
    .update(req.ip)
    .digest("hex");
async function currentPrices(c = pool) {
  return one(
    c,
    "SELECT * FROM price_versions WHERE status='published' ORDER BY published_at DESC LIMIT 1",
    [],
  );
}
async function deckPair(c, team, prices) {
  const r = await c.query(
    "SELECT DISTINCT ON(slot) * FROM deck_versions WHERE team_id=$1 ORDER BY slot,created_at DESC,id DESC",
    [team],
  );
  return r.rows.map((d) => {
    const v = evaluate(d.deck, prices);
    return {
      version_id: d.id,
      slot: d.slot,
      source_url: d.source_url,
      deck: v.deck,
      score: v.score,
      submitted_at: d.created_at,
    };
  });
}
async function registrationSnapshot(c, reg, decks, actor) {
  const score = teamEvaluation(decks.map((d) => d.score));
  await c.query(
    "UPDATE registrations SET decks=$2,score=$3,updated_at=now() WHERE id=$1",
    [reg.id, JSON.stringify(decks), JSON.stringify(score)],
  );
  await c.query(
    "INSERT INTO registration_versions(id,registration_id,decks,score,actor) VALUES($1,$2,$3,$4,$5)",
    [id(), reg.id, JSON.stringify(decks), JSON.stringify(score), actor],
  );
  return score;
}
function annotateEvent(e) {
  return { ...e, submissions_locked: isLocked(e), price_snapshot: undefined };
}
async function getEvent(c, event, lock = false) {
  return one(
    c,
    "SELECT * FROM events WHERE id=$1" + (lock ? " FOR UPDATE" : ""),
    [event],
  );
}
async function sync(c, event) {
  const e = await getEvent(c, event, true);
  if (!e.tournament_id)
    throw fail("Link or create a Challonge tournament first");
  const data = await providerFor(e, c).snapshot(e.tournament_id);
  const champion =
    data.participants.find((p) => Number(p.final_rank) === 1)?.name || null;
  const state = data.tournament.state;
  const status =
    state === "complete"
      ? "complete"
      : [
            "underway",
            "awaiting_review",
            "group_stages_underway",
            "group_stages_finalized",
          ].includes(state)
        ? "running"
        : e.status;
  if (["running", "complete"].includes(status) && !isLocked(e))
    await audit(c, "system", "event.lock.external-start", e.id);
  await c.query(
    "UPDATE events SET sync_data=$2,synced_at=now(),sync_error=NULL,tournament_state=$3,champion=$4,status=$5,locked=CASE WHEN $5 IN ('running','complete') THEN true ELSE locked END WHERE id=$1",
    [e.id, JSON.stringify(data), state, champion, status],
  );
  await audit(c, "system", "challonge.sync", e.id, {
    state,
    participants: data.participants.length,
    matches: data.matches.length,
  });
  return data;
}
export function createApp() {
  const app = express();
  app.set("trust proxy", 1);
  app.disable("x-powered-by");
  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'"],
          styleSrc: ["'self'"],
          imgSrc: ["'self'", "data:"],
          frameSrc: ["https://challonge.com", "https://*.challonge.com"],
          connectSrc: ["'self'"],
          upgradeInsecureRequests:
            process.env.NODE_ENV === "production" ? [] : null,
        },
      },
    }),
  );
  app.use(
    "/api",
    rateLimit({
      windowMs: 60000,
      limit: 240,
      standardHeaders: "draft-8",
      legacyHeaders: false,
    }),
  );
  app.use(express.json({ limit: "220kb", strict: true }));
  app.use(async (req, res, next) => {
    try {
      res.set("Cache-Control", "no-store");
      if (["POST", "PUT", "PATCH", "DELETE"].includes(req.method)) {
        if (
          req.headers.origin &&
          req.headers.origin !==
            (process.env.PUBLIC_URL || `${req.protocol}://${req.get("host")}`)
        )
          throw fail("Cross-origin writes are not allowed", 403);
        if (!req.is("application/json"))
          throw fail("Use application/json", 415);
      }
      const token = (req.headers.cookie || "")
        .split(";")
        .map((c) => c.trim())
        .find((c) => c.startsWith("cd_admin="))
        ?.slice(9);
      if (token) {
        const r = await q(
          "SELECT * FROM sessions WHERE token_hash=$1 AND expires_at>now()",
          [digest(token)],
        );
        req.admin = r.rows[0] || null;
        req.sessionHash = digest(token);
      }
      if (
        req.admin &&
        ["POST", "PUT", "PATCH", "DELETE"].includes(req.method) &&
        req.path !== "/api/login" &&
        req.headers["x-csrf-token"] !== req.admin.csrf
      )
        throw fail("CSRF token required", 403);
      next();
    } catch (e) {
      next(e);
    }
  });
  const admin = (req, res, next) => {
    if (!req.admin) return next(fail("Administrator login required", 401));
    if (req.method !== "GET" && req.headers["x-csrf-token"] !== req.admin.csrf)
      return next(fail("CSRF token required", 403));
    next();
  };
  app.get("/health", async (req, res) => {
    await q("SELECT 1");
    res.json({
      ok: true,
      version: "1.0.0",
      environment: process.env.APP_ENV || "production",
    });
  });
  app.get("/api/session", (req, res) =>
    res.json({ admin: !!req.admin, csrf: req.admin?.csrf || null }),
  );
  app.post("/api/login", async (req, res) => {
    const key = ipHash(req);
    const allowed = await transaction(async (c) => {
      await c.query(
        "INSERT INTO login_attempts(ip_hash,attempts,resets_at) VALUES($1,1,now()+interval '15 minutes') ON CONFLICT(ip_hash) DO UPDATE SET attempts=CASE WHEN login_attempts.resets_at<now() THEN 1 ELSE login_attempts.attempts+1 END,resets_at=CASE WHEN login_attempts.resets_at<now() THEN now()+interval '15 minutes' ELSE login_attempts.resets_at END",
        [key],
      );
      const r = await c.query(
        "SELECT attempts FROM login_attempts WHERE ip_hash=$1",
        [key],
      );
      return r.rows[0].attempts <= 8;
    });
    if (!allowed)
      throw fail("Too many login attempts. Retry in 15 minutes.", 429);
    if (!checkPassword(req.body.password))
      throw fail("Incorrect administrator password", 401);
    const token = randomBytes(32).toString("hex"),
      csrf = randomBytes(24).toString("hex");
    await q(
      "INSERT INTO sessions(token_hash,csrf,expires_at) VALUES($1,$2,now()+interval '8 hours')",
      [digest(token), csrf],
    );
    await q("DELETE FROM login_attempts WHERE ip_hash=$1", [key]);
    res.cookie("cd_admin", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      maxAge: 8 * 3600000,
      path: "/",
    });
    res.json({ admin: true, csrf });
  });
  app.post("/api/logout", admin, async (req, res) => {
    await q("DELETE FROM sessions WHERE token_hash=$1", [req.sessionHash]);
    res.clearCookie("cd_admin", { path: "/" });
    res.json({ ok: true });
  });
  app.get("/api/home", async (req, res) => {
    const [events, teams, rules, price] = await Promise.all([
      q("SELECT * FROM events ORDER BY starts_at"),
      q(
        "SELECT id,name,players,created_at FROM teams WHERE NOT archived ORDER BY lower(name)",
      ),
      q(
        "SELECT * FROM rules_versions WHERE status='published' ORDER BY published_at DESC LIMIT 1",
      ),
      currentPrices(),
    ]);
    res.json({
      events: events.rows.map(annotateEvent),
      teams: teams.rows,
      rules: rules.rows[0],
      price: { id: price.id, name: price.name },
      catalogVersion: "2026-10-20",
      mockEnabled: process.env.ALLOW_MOCK === "true",
    });
  });
  app.get("/api/points", async (req, res) => {
    const version = req.query.version
      ? await one(
          pool,
          "SELECT * FROM price_versions WHERE id=$1 AND status='published'",
          [req.query.version],
        )
      : await currentPrices();
    const needle = normalizeName(req.query.q || "");
    const offset = Math.max(0, Math.min(50000, Number(req.query.offset) || 0));
    const filtered = catalog
      .filter(
        (c) =>
          c.oracle_id &&
          (!needle || normalizeName(c.name).includes(needle)) &&
          (!req.query.pointed ||
            (version.prices[c.name]?.main || 0) +
              (version.prices[c.name]?.command || 0) >
              0),
      )
      .sort((a, b) => a.name.localeCompare(b.name));
    res.json({
      version: { id: version.id, name: version.name },
      total: filtered.length,
      cards: filtered
        .slice(offset, offset + 100)
        .map((c) => ({
          name: c.name,
          oracle_id: c.oracle_id,
          legal: c.legalities?.commander === "legal",
          main: version.prices[c.name]?.main || 0,
          command: version.prices[c.name]?.command ?? 0,
        })),
      offset,
    });
  });
  app.post("/api/score", async (req, res) => {
    if (
      !Array.isArray(req.body.decks) ||
      req.body.decks.length < 1 ||
      req.body.decks.length > 2
    )
      throw fail("Submit one or two decks");
    const version = req.body.event_id
      ? await getEvent(pool, req.body.event_id)
      : await currentPrices();
    const prices = version.price_snapshot || version.prices;
    const decks = await Promise.all(
      req.body.decks.map(async (d) => {
        const raw = d.text?.trim()
          ? parseExport(d.text)
          : await getMoxfield(deckIdFromURL(d.link));
        return evaluate(raw, prices);
      }),
    );
    res.json({
      decks: decks.map((d) => d.score),
      resolved: decks.map((d) => d.deck),
      team: teamEvaluation(decks.map((d) => d.score)),
      price_version: version.price_version_id || version.id,
    });
  });
  app.post("/api/teams", async (req, res) => {
    const name = label(req.body.name);
    const players = [
      req.body.players?.[0] || "",
      req.body.players?.[1] || "",
    ].map((x) => String(x).trim().slice(0, 80));
    const team = await transaction(async (c) => {
      const r = await c.query(
        "INSERT INTO teams(id,name,name_key,players) VALUES($1,$2,$3,$4) RETURNING *",
        [id(), name, normalizeName(name), JSON.stringify(players)],
      );
      await audit(c, "public", "team.create", r.rows[0].id);
      return r.rows[0];
    });
    res.status(201).json(team);
  });
  app.get("/api/teams/:id", async (req, res) => {
    const team = await one(pool, "SELECT * FROM teams WHERE id=$1", [
      req.params.id,
    ]);
    const rows = await q(
      "SELECT DISTINCT ON(slot) * FROM deck_versions WHERE team_id=$1 ORDER BY slot,created_at DESC,id DESC",
      [team.id],
    );
    const version = await currentPrices();
    const decks = rows.rows.map((d) => ({
      ...d,
      current_score: evaluate(d.deck, version.prices).score,
    }));
    res.json({
      ...team,
      decks,
      team_score: teamEvaluation(decks.map((d) => d.current_score)),
    });
  });
  app.patch("/api/teams/:id", async (req, res) => {
    const name = label(req.body.name);
    const players = [
      req.body.players?.[0] || "",
      req.body.players?.[1] || "",
    ].map((x) => String(x).slice(0, 80));
    const team = await transaction(async (c) => {
      const old = await one(c, "SELECT * FROM teams WHERE id=$1 FOR UPDATE", [
        req.params.id,
      ]);
      await audit(c, req.admin ? "admin" : "public", "team.edit", old.id, {
        previousName: old.name,
        previousPlayers: old.players,
      });
      return one(
        c,
        "UPDATE teams SET name=$2,name_key=$3,players=$4,updated_at=now() WHERE id=$1 RETURNING *",
        [old.id, name, normalizeName(name), JSON.stringify(players)],
      );
    });
    res.json(team);
  });
  app.post("/api/teams/:id/decks/:slot", async (req, res) => {
    const slot = Number(req.params.slot);
    if (![1, 2].includes(slot)) throw fail("Slot must be 1 or 2");
    let source_url = req.body.link ? String(req.body.link) : null;
    if (source_url) deckIdFromURL(source_url);
    const raw = req.body.text?.trim()
      ? parseExport(req.body.text)
      : await getMoxfield(deckIdFromURL(source_url));
    const d = await transaction(async (c) => {
      await one(c, "SELECT id FROM teams WHERE id=$1 FOR UPDATE", [
        req.params.id,
      ]);
      const version = await currentPrices(c),
        v = evaluate(raw, version.prices),
        deckId = id();
      await c.query(
        "INSERT INTO deck_versions(id,team_id,slot,source_url,source_text,deck,score,price_version_id,actor) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)",
        [
          deckId,
          req.params.id,
          slot,
          source_url,
          req.body.text || null,
          JSON.stringify(v.deck),
          JSON.stringify(v.score),
          version.id,
          req.admin ? "admin" : "public",
        ],
      );
      await audit(c, req.admin ? "admin" : "public", "deck.save", deckId, {
        team: req.params.id,
        slot,
        points: v.score.points,
      });
      return { id: deckId, ...v };
    });
    res.status(201).json(d);
  });
  app.get("/api/events/:id", async (req, res) => {
    const e = await getEvent(pool, req.params.id);
    const regs = await q(
      "SELECT * FROM registrations WHERE event_id=$1 ORDER BY created_at",
      [e.id],
    );
    const participants = e.sync_data.participants || [],
      matches = (e.sync_data.matches || []).map((m) => ({
        ...m,
        players: matchPlayers(m).map((pid) => {
          const p = participants.find((p) => String(p.id) === pid);
          return p
            ? {
                id: pid,
                name: p.name,
                team_id: regs.rows.find((r) => r.participant_id === pid)
                  ?.team_id,
              }
            : null;
        }),
      }));
    res.json({
      ...annotateEvent(e),
      registrations: regs.rows,
      matches,
      standings: participants
        .filter((p) => p.final_rank)
        .sort((a, b) => a.final_rank - b.final_rank),
    });
  });
  app.post("/api/events/:id/register", async (req, res) => {
    const reg = await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (["running", "complete", "cancelled"].includes(e.status))
        throw fail("This event no longer accepts registrations", 409);
      const now = new Date();
      if (
        !req.admin &&
        (e.status !== "registration" ||
          isLocked(e) ||
          (e.registration_opens && now < new Date(e.registration_opens)) ||
          (e.registration_closes && now >= new Date(e.registration_closes)))
      )
        throw fail("Registration is closed", 409);
      const t = await one(
        c,
        "SELECT * FROM teams WHERE id=$1 AND NOT archived FOR UPDATE",
        [req.body.team_id],
      );
      const r = await one(
        c,
        "INSERT INTO registrations(id,event_id,team_id,team_name) VALUES($1,$2,$3,$4) RETURNING *",
        [id(), e.id, t.id, t.name],
      );
      const decks = await deckPair(c, t.id, e.price_snapshot);
      await registrationSnapshot(c, r, decks, req.admin ? "admin" : "public");
      await audit(c, req.admin ? "admin" : "public", "event.register", r.id);
      return r;
    });
    res.status(201).json(reg);
  });
  app.post("/api/events/:id/submission", async (req, res) => {
    const out = await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      const override =
        req.admin &&
        req.headers["x-csrf-token"] === req.admin.csrf &&
        req.body.reason;
      if (isLocked(e) && !override)
        throw fail(
          "Event deck submissions are locked. General team decks remain editable.",
          423,
        );
      if (["complete", "cancelled"].includes(e.status) && !override)
        throw fail("Event is archived", 423);
      const r = await one(
        c,
        "SELECT * FROM registrations WHERE event_id=$1 AND team_id=$2 FOR UPDATE",
        [e.id, req.body.team_id],
      );
      const decks = await deckPair(c, r.team_id, e.price_snapshot);
      const score = await registrationSnapshot(
        c,
        r,
        decks,
        override ? "admin override" : "public",
      );
      await audit(
        c,
        override ? "admin" : "public",
        override ? "submission.override" : "submission.update",
        r.id,
        { reason: req.body.reason || null },
      );
      return { decks, score };
    });
    res.json(out);
  });
  app.use("/api/admin", admin);
  app.get("/api/admin/dashboard", async (req, res) => {
    const [prices, rules, audits, teams] = await Promise.all([
      q(
        "SELECT id,name,status,created_at,published_at FROM price_versions ORDER BY created_at DESC",
      ),
      q("SELECT * FROM rules_versions ORDER BY created_at DESC"),
      q("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100"),
      q("SELECT * FROM teams ORDER BY lower(name)"),
    ]);
    res.json({
      prices: prices.rows,
      rules: rules.rows,
      audits: audits.rows,
      teams: teams.rows,
      challongeConfigured: !!process.env.CHALLONGE_API_KEY,
      environment: process.env.APP_ENV || "production",
    });
  });
  app.get("/api/admin/prices/:id", async (req, res) =>
    res.json(
      await one(pool, "SELECT * FROM price_versions WHERE id=$1", [
        req.params.id,
      ]),
    ),
  );
  app.post("/api/admin/prices", async (req, res) => {
    const p = await transaction(async (c) => {
      const base = req.body.restore_id
        ? await one(c, "SELECT * FROM price_versions WHERE id=$1", [
            req.body.restore_id,
          ])
        : await currentPrices(c);
      const prices = structuredClone(base.prices);
      for (const change of req.body.changes || []) {
        const card = resolveCard(change.name);
        if (!card) throw fail("Unknown card " + change.name);
        if (
          ![change.main, change.command].every(
            (x) => Number.isInteger(x) && x >= 0 && x <= 10000,
          )
        )
          throw fail("Prices must be nonnegative whole numbers");
        prices[card.name] = { main: change.main, command: change.command };
      }
      const r = await one(
        c,
        "INSERT INTO price_versions(id,name,status,prices) VALUES($1,$2,'draft',$3) RETURNING id,name,status",
        [id(), label(req.body.name), JSON.stringify(prices)],
      );
      await audit(c, "admin", "prices.draft", r.id, {
        base: base.id,
        changes: req.body.changes || [],
      });
      return r;
    });
    res.status(201).json(p);
  });
  app.patch("/api/admin/prices/:id", async (req, res) => {
    const p = await transaction(async (c) => {
      const base = await one(
        c,
        "SELECT * FROM price_versions WHERE id=$1 AND status='draft' FOR UPDATE",
        [req.params.id],
      );
      const prices = structuredClone(base.prices);
      for (const change of req.body.changes || []) {
        const card = resolveCard(change.name);
        if (!card) throw fail("Unknown card " + change.name);
        if (
          ![change.main, change.command].every(
            (x) => Number.isInteger(x) && x >= 0 && x <= 10000,
          )
        )
          throw fail("Prices must be nonnegative whole numbers");
        prices[card.name] = { main: change.main, command: change.command };
      }
      await c.query("UPDATE price_versions SET name=$2,prices=$3 WHERE id=$1", [
        base.id,
        req.body.name ? label(req.body.name) : base.name,
        JSON.stringify(prices),
      ]);
      await audit(c, "admin", "prices.edit-draft", base.id, {
        changes: req.body.changes || [],
      });
      return { id: base.id };
    });
    res.json(p);
  });
  app.post("/api/admin/prices/:id/publish", async (req, res) => {
    const p = await transaction(async (c) => {
      await c.query("SELECT pg_advisory_xact_lock(81023277)");
      const p = await one(
        c,
        "UPDATE price_versions SET status='published',published_at=now() WHERE id=$1 AND status='draft' RETURNING id,name,status",
        [req.params.id],
      );
      await audit(c, "admin", "prices.publish", p.id);
      return p;
    });
    res.json(p);
  });
  app.post("/api/admin/rules", async (req, res) => {
    const r = await transaction(async (c) => {
      const r = await one(
        c,
        "INSERT INTO rules_versions(id,title,body,status) VALUES($1,$2,$3,'draft') RETURNING *",
        [id(), label(req.body.title, 120), label(req.body.body, 40000)],
      );
      await audit(c, "admin", "rules.draft", r.id);
      return r;
    });
    res.status(201).json(r);
  });
  app.post("/api/admin/rules/:id/publish", async (req, res) => {
    const r = await transaction(async (c) => {
      const r = await one(
        c,
        "UPDATE rules_versions SET status='published',published_at=now() WHERE id=$1 AND status='draft' RETURNING *",
        [req.params.id],
      );
      await audit(c, "admin", "rules.publish", r.id);
      return r;
    });
    res.json(r);
  });
  app.get("/api/admin/teams/:id/history", async (req, res) => {
    const r = await q(
      "SELECT * FROM deck_versions WHERE team_id=$1 ORDER BY created_at DESC,id DESC",
      [req.params.id],
    );
    res.json(r.rows);
  });
  app.post("/api/admin/decks/:id/restore", async (req, res) => {
    const out = await transaction(async (c) => {
      const d = await one(c, "SELECT * FROM deck_versions WHERE id=$1", [
        req.params.id,
      ]);
      await one(c, "SELECT id FROM teams WHERE id=$1 FOR UPDATE", [d.team_id]);
      const p = await currentPrices(c),
        v = evaluate(d.deck, p.prices),
        n = id();
      await c.query(
        "INSERT INTO deck_versions(id,team_id,slot,source_url,source_text,deck,score,price_version_id,actor,restored_from) VALUES($1,$2,$3,$4,$5,$6,$7,$8,'admin',$9)",
        [
          n,
          d.team_id,
          d.slot,
          d.source_url,
          d.source_text,
          JSON.stringify(v.deck),
          JSON.stringify(v.score),
          p.id,
          d.id,
        ],
      );
      await audit(c, "admin", "deck.restore", n, { restored_from: d.id });
      return { id: n };
    });
    res.json(out);
  });
  app.delete("/api/admin/teams/:id", async (req, res) => {
    await transaction(async (c) => {
      await one(
        c,
        "UPDATE teams SET archived=true,updated_at=now() WHERE id=$1 RETURNING id",
        [req.params.id],
      );
      await audit(c, "admin", "team.archive", req.params.id);
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/teams/:id/restore", async (req, res) => {
    await transaction(async (c) => {
      await one(
        c,
        "UPDATE teams SET archived=false,updated_at=now() WHERE id=$1 RETURNING id",
        [req.params.id],
      );
      await audit(c, "admin", "team.unarchive", req.params.id);
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/events", async (req, res) => {
    const b = req.body;
    const timezone = b.timezone || "America/Phoenix";
    try {
      new Intl.DateTimeFormat("en", { timeZone: timezone });
    } catch {
      throw fail("Invalid time zone");
    }
    const starts = date(b.starts_at, true),
      opens = date(b.registration_opens),
      closes = date(b.registration_closes),
      lock = date(b.lock_at);
    if (opens && closes && opens >= closes)
      throw fail("Registration must open before it closes");
    if (b.provider === "mock" && process.env.ALLOW_MOCK !== "true")
      throw fail("Mock provider is disabled", 403);
    if (
      ![
        "single elimination",
        "double elimination",
        "round robin",
        "swiss",
      ].includes(b.tournament_type || "single elimination")
    )
      throw fail("Unsupported tournament format");
    const e = await transaction(async (c) => {
      const p = await currentPrices(c);
      const e = await one(
        c,
        "INSERT INTO events(id,name,description,starts_at,timezone,location,registration_opens,registration_closes,lock_at,status,price_version_id,price_snapshot,provider,tournament_type) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,'scheduled',$10,$11,$12,$13) RETURNING *",
        [
          id(),
          label(b.name),
          String(b.description || "").slice(0, 4000),
          starts,
          timezone,
          String(b.location || "Online").slice(0, 200),
          opens,
          closes,
          lock,
          p.id,
          JSON.stringify(p.prices),
          b.provider || "challonge",
          b.tournament_type || "single elimination",
        ],
      );
      await audit(c, "admin", "event.create", e.id);
      return e;
    });
    res.status(201).json(annotateEvent(e));
  });
  app.patch("/api/admin/events/:id", async (req, res) => {
    const out = await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (e.status === "complete")
        throw fail(
          "Completed events are archived; use an audited submission override for corrections",
          409,
        );
      const b = req.body;
      const timezone = b.timezone || e.timezone;
      try {
        new Intl.DateTimeFormat("en", { timeZone: timezone });
      } catch {
        throw fail("Invalid time zone");
      }
      if (
        b.status &&
        !["scheduled", "registration", "cancelled"].includes(b.status)
      )
        throw fail("Start and finalize tournaments through Challonge");
      if (b.status === "registration" && (e.locked || e.status === "running"))
        throw fail("Unlock before reopening registration");
      const opens =
          b.registration_opens === undefined
            ? e.registration_opens
            : date(b.registration_opens),
        closes =
          b.registration_closes === undefined
            ? e.registration_closes
            : date(b.registration_closes);
      if (opens && closes && new Date(opens) >= new Date(closes))
        throw fail("Registration must open before it closes");
      if (b.tournament_id !== undefined) {
        if (e.tournament_id && e.tournament_id !== b.tournament_id)
          throw fail("Tournament association already set", 409);
        if ((e.sync_data.participants || []).length)
          throw fail("Cannot relink a populated tournament", 409);
      }
      const r = await one(
        c,
        "UPDATE events SET name=$2,description=$3,starts_at=$4,timezone=$5,location=$6,registration_opens=$7,registration_closes=$8,lock_at=$9,status=$10,tournament_id=$11,tournament_url=$12 WHERE id=$1 RETURNING *",
        [
          e.id,
          b.name === undefined ? e.name : label(b.name),
          String(b.description ?? e.description).slice(0, 4000),
          b.starts_at ? date(b.starts_at, true) : e.starts_at,
          timezone,
          String(b.location ?? e.location).slice(0, 200),
          opens,
          closes,
          b.lock_at === undefined ? e.lock_at : date(b.lock_at),
          b.status || e.status,
          b.tournament_id === undefined
            ? e.tournament_id
            : label(b.tournament_id, 150),
          b.tournament_id
            ? "https://challonge.com/" + encodeURIComponent(b.tournament_id)
            : e.tournament_url,
        ],
      );
      await audit(c, "admin", "event.edit", e.id, { fields: Object.keys(b) });
      return r;
    });
    res.json(annotateEvent(out));
  });
  app.post("/api/admin/events/:id/lock", async (req, res) => {
    await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (["running", "complete"].includes(e.status) && !req.body.locked)
        throw fail(
          "Use an audited submission override for a running or completed event",
          409,
        );
      await c.query("UPDATE events SET locked=$2 WHERE id=$1", [
        e.id,
        bool(req.body.locked),
      ]);
      await audit(
        c,
        "admin",
        req.body.locked ? "event.lock" : "event.unlock",
        e.id,
      );
    });
    res.json({ ok: true });
  });
  app.get("/api/admin/registrations/:id/history", async (req, res) => {
    const rows = await q(
      "SELECT * FROM registration_versions WHERE registration_id=$1 ORDER BY created_at DESC",
      [req.params.id],
    );
    res.json(rows.rows);
  });
  app.post("/api/admin/registrations/:id/restore", async (req, res) => {
    const out = await transaction(async (c) => {
      const r = await one(c, "SELECT * FROM registrations WHERE id=$1", [
        req.params.id,
      ]);
      await getEvent(c, r.event_id, true);
      const v = await one(
        c,
        "SELECT * FROM registration_versions WHERE id=$1 AND registration_id=$2",
        [req.body.version_id, r.id],
      );
      if (!req.body.reason) throw fail("A correction reason is required");
      await registrationSnapshot(c, r, v.decks, "admin restore");
      await audit(c, "admin", "submission.restore", r.id, {
        version: v.id,
        reason: label(req.body.reason, 500),
      });
      return { ok: true };
    });
    res.json(out);
  });
  app.delete("/api/admin/registrations/:id", async (req, res) => {
    await transaction(async (c) => {
      const r = await one(
        c,
        "SELECT * FROM registrations WHERE id=$1 FOR UPDATE",
        [req.params.id],
      );
      const e = await getEvent(c, r.event_id, true);
      if (r.participant_id || isLocked(e))
        throw fail("Cannot remove a published or locked registration", 409);
      await audit(c, "admin", "registration.remove", r.id, { registration: r });
      await c.query(
        "DELETE FROM registration_versions WHERE registration_id=$1",
        [r.id],
      );
      await c.query("DELETE FROM registrations WHERE id=$1", [r.id]);
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/events/:id/tournament", async (req, res) => {
    const out = await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (e.tournament_id) throw fail("Tournament already linked", 409);
      const t = await providerFor(e, c).create(e.name, e.tournament_type);
      const url =
        e.provider === "challonge"
          ? "https://challonge.com/" + encodeURIComponent(t.url || t.id)
          : null;
      await c.query(
        "UPDATE events SET tournament_id=$2,tournament_url=$3 WHERE id=$1",
        [e.id, String(t.id), url],
      );
      await audit(c, "admin", "tournament.create", e.id, { id: t.id });
      return t;
    });
    res.json(out);
  });
  app.post("/api/admin/events/:id/participants", async (req, res) => {
    await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (!e.tournament_id) throw fail("Create or link a tournament first");
      if (["running", "complete"].includes(e.status))
        throw fail("Tournament has started", 409);
      const provider = providerFor(e, c),
        participants = await provider.participants(e.tournament_id);
      const regs = await c.query(
        "SELECT * FROM registrations WHERE event_id=$1 ORDER BY created_at",
        [e.id],
      );
      for (const r of regs.rows) {
        if (r.participant_id) continue;
        const marker = "cd-registration:" + r.id;
        let p = participants.find((p) => p.misc === marker);
        if (!p) {
          const same = participants.filter(
            (p) => p.name === r.team_name && !p.misc,
          );
          if (same.length === 1) p = same[0];
        }
        if (!p)
          p = await provider.participant(e.tournament_id, r.team_name, marker);
        participants.push(p);
        await c.query(
          "UPDATE registrations SET participant_id=$2 WHERE id=$1",
          [r.id, String(p.id)],
        );
      }
      await audit(c, "admin", "participants.publish", e.id, {
        count: regs.rowCount,
      });
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/events/:id/start", async (req, res) => {
    await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (!e.tournament_id) throw fail("Create or link a tournament first");
      if (["running", "complete", "cancelled"].includes(e.status))
        throw fail("Event cannot be started", 409);
      const regs = await c.query(
        "SELECT * FROM registrations WHERE event_id=$1",
        [e.id],
      );
      if (
        regs.rowCount < 2 ||
        regs.rows.some((r) => !r.participant_id || !r.score?.within)
      )
        throw fail(
          "Every registration needs two legal, within-budget decks and a published participant ID",
        );
      await providerFor(e, c).state(e.tournament_id, "start");
      await c.query(
        "UPDATE events SET locked=true,status='running' WHERE id=$1",
        [e.id],
      );
      await audit(c, "admin", "event.start", e.id);
      await sync(c, e.id);
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/events/:id/finalize", async (req, res) => {
    await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (!e.tournament_id || e.status !== "running")
        throw fail("Tournament is not running");
      await providerFor(e, c).state(e.tournament_id, "finalize");
      await sync(c, e.id);
      await audit(c, "admin", "event.finalize", e.id);
    });
    res.json({ ok: true });
  });
  app.post("/api/admin/events/:id/sync", async (req, res) => {
    try {
      const data = await transaction((c) => sync(c, req.params.id));
      res.json(data);
    } catch (e) {
      await q("UPDATE events SET sync_error=$2 WHERE id=$1", [
        req.params.id,
        e.message,
      ]);
      throw e;
    }
  });
  app.post("/api/admin/events/:id/mock-result", async (req, res) => {
    await transaction(async (c) => {
      const e = await getEvent(c, req.params.id, true);
      if (e.provider !== "mock" || process.env.ALLOW_MOCK !== "true")
        throw fail("Report real results in Challonge", 403);
      await providerFor(e, c).report(
        e.tournament_id,
        String(req.body.match_id),
        req.body.entries,
      );
      await sync(c, e.id);
    });
    res.json({ ok: true });
  });
  app.get("/api/admin/export", async (req, res) => {
    const tables = [
      "price_versions",
      "rules_versions",
      "teams",
      "deck_versions",
      "events",
      "registrations",
      "registration_versions",
      "audit_log",
    ];
    const out = await transaction(async (c) => {
      await c.query("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ");
      const out = {
        format: "commander-doubles-backup-v1",
        exported_at: new Date().toISOString(),
        catalogVersion: "2026-10-20",
      };
      for (const t of tables)
        out[t] = (await c.query("SELECT * FROM " + t)).rows;
      await audit(c, "admin", "backup.export", null);
      return out;
    });
    res.attachment("commander-doubles-backup.json").json(out);
  });
  app.use("/api", (req, res) =>
    res.status(404).json({ error: "API endpoint not found" }),
  );
  app.use(express.static(path.join(ROOT, "public"), { maxAge: 0 }));
  for (const route of [
    "/",
    "/rules",
    "/points",
    "/schedule",
    "/teams",
    "/history",
    "/admin",
    "/events/:id",
  ])
    app.get(route, (req, res) =>
      res.sendFile(path.join(ROOT, "public/index.html")),
    );
  app.use(async (err, req, res, next) => {
    const operation = req.path.match(
      /^\/api\/admin\/events\/([0-9a-f-]{36})\/(tournament|participants|start|finalize|sync)$/,
    );
    if (operation) {
      try {
        await transaction(async (c) => {
          await c.query("UPDATE events SET sync_error=$2 WHERE id=$1", [
            operation[1],
            String(err.message).slice(0, 1200),
          ]);
          await audit(c, "admin", "integration.failed", operation[1], {
            operation: operation[2],
            error: String(err.message).slice(0, 1200),
          });
        });
      } catch {}
    }
    let status = err.status || 400,
      message = err.message;
    if (err.code === "23505") {
      status = 409;
      message = "This team name or event registration already exists";
    } else if (err.code === "22P02") {
      status = 400;
      message = "Invalid record identifier";
    } else if (err.code && err.code.startsWith("23")) {
      status = 409;
      message = "This operation conflicts with a related record";
    } else if (!err.status && err.code) {
      status = 500;
      message = "Database operation failed";
    }
    if (status >= 500)
      console.error(
        JSON.stringify({
          level: "error",
          path: req.path,
          code: err.code || "internal",
        }),
      );
    res.status(status).json({ error: message });
  });
  return app;
}
export async function scheduledSync() {
  const rows = await q(
    "SELECT id FROM events WHERE tournament_id IS NOT NULL AND status IN ('running','registration','scheduled') AND (synced_at IS NULL OR synced_at<now()-interval '45 seconds')",
  );
  for (const e of rows.rows) {
    try {
      await transaction((c) => sync(c, e.id));
    } catch (err) {
      await q("UPDATE events SET sync_error=$2 WHERE id=$1", [
        e.id,
        err.message,
      ]);
    }
  }
  await q("DELETE FROM sessions WHERE expires_at<now()");
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (!storedHash || !process.env.SESSION_SECRET || !process.env.DATABASE_URL)
    throw Error(
      "DATABASE_URL, ADMIN_PASSWORD_HASH (or ADMIN_PASSWORD), and SESSION_SECRET are required",
    );
  await migrate();
  const server = createApp().listen(
    Number(process.env.PORT || 3000),
    "0.0.0.0",
    () => console.log("Commander Doubles listening"),
  );
  let syncing = false;
  const timer = setInterval(async () => {
    if (syncing) return;
    syncing = true;
    try {
      await scheduledSync();
    } catch (e) {
      console.error("Scheduled synchronization failed");
    } finally {
      syncing = false;
    }
  }, 30000);
  timer.unref();
  process.on("SIGTERM", () => {
    clearInterval(timer);
    server.close(async () => {
      await pool.end();
      process.exit(0);
    });
  });
}
