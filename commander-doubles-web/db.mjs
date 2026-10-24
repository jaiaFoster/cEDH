import pg from "pg";
import fs from "node:fs";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import { PRICES } from "./scoring.mjs";
import { seedRulings } from "./rulings.mjs";
const schema = process.env.DATABASE_SCHEMA || "league";
if (!/^[a-z][a-z0-9_]{0,50}$/.test(schema))
  throw Error("Invalid DATABASE_SCHEMA");
export const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  connectionTimeoutMillis: 10000,
  options: `-c search_path=${schema},public`,
});
export const q = (text, params = []) => pool.query(text, params);
export async function transaction(fn) {
  const c = await pool.connect();
  try {
    await c.query("BEGIN");
    const out = await fn(c);
    await c.query("COMMIT");
    return out;
  } catch (e) {
    await c.query("ROLLBACK");
    throw e;
  } finally {
    c.release();
  }
}
export async function migrate() {
  await transaction(async (c) => {
    await c.query("SELECT pg_advisory_xact_lock(81023276)");
    await c.query(`CREATE SCHEMA IF NOT EXISTS ${schema}`);
    const exists = await c.query("SELECT to_regclass($1) AS t", [
      schema + ".migrations",
    ]);
    if (!exists.rows[0].t)
      await c.query(
        fs.readFileSync(
          new URL("./migrations/001.sql", import.meta.url),
          "utf8",
        ),
      );
    if (!(await c.query("SELECT 1 FROM migrations WHERE version=2")).rowCount)
      await c.query(
        fs.readFileSync(new URL("./migrations/002_rulings.sql", import.meta.url), "utf8"),
      );
    await seedRulings(c);
    if (!(await c.query("SELECT id FROM price_versions LIMIT 1")).rowCount) {
      const prices = Object.fromEntries(
        [...new Set(PRICES.values())].map((x) => [
          x.name,
          { main: x.main, command: x.command },
        ]),
      );
      await c.query(
        "INSERT INTO price_versions(id,name,status,prices,published_at) VALUES($1,'Season 0 · v3','published',$2,now())",
        [randomUUID(), JSON.stringify(prices)],
      );
    }
    if (!(await c.query("SELECT id FROM rules_versions LIMIT 1")).rowCount)
      await c.query(
        "INSERT INTO rules_versions(id,title,body,status,published_at) VALUES($1,'Commander Doubles', $2,'published',now())",
        [
          randomUUID(),
          fs.readFileSync(new URL("./data/rules.txt", import.meta.url), "utf8"),
        ],
      );
  });
}
export async function audit(c, actor, action, id, detail = {}) {
  await c.query(
    "INSERT INTO audit_log(actor,action,entity_id,detail) VALUES($1,$2,$3,$4)",
    [actor, action, id, JSON.stringify(detail)],
  );
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await migrate();
  console.log("Migrations complete");
  await pool.end();
}
