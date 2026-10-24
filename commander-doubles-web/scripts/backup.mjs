import fs from "node:fs";
import { pool, transaction } from "../db.mjs";
const file = process.argv[2];
if (!file) throw Error("Usage: npm run backup -- /secure/path/league.json");
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
  };
  for (const table of tables)
    out[table] = (await c.query("SELECT * FROM " + table)).rows;
  return out;
});
fs.writeFileSync(file, JSON.stringify(out, null, 2), { mode: 0o600 });
console.log("League data exported");
await pool.end();
