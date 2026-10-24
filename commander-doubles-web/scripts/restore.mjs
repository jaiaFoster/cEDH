import fs from "node:fs";
import { pool, migrate, transaction } from "../db.mjs";
if (!process.env.DATABASE_SCHEMA?.startsWith("restore_"))
  throw Error("Restore requires a new DATABASE_SCHEMA starting with restore_");
const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
if (data.format !== "commander-doubles-backup-v1")
  throw Error("Unsupported backup");
await migrate();
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
await transaction(async (c) => {
  if (Number((await c.query("SELECT count(*) AS n FROM teams")).rows[0].n) > 0)
    throw Error("Refusing to overwrite nonempty schema");
  await c.query("DELETE FROM rules_versions");
  await c.query("DELETE FROM price_versions");
  for (const table of tables) {
    const columns = (
      await c.query(
        "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=$1 ORDER BY ordinal_position",
        [table],
      )
    ).rows.map((c) => c.column_name);
    for (const row of data[table] || []) {
      const keys = columns.filter((k) => Object.hasOwn(row, k));
      await c.query(
        "INSERT INTO " +
          table +
          "(" +
          keys.join(",") +
          ") VALUES(" +
          keys.map((_, i) => "$" + (i + 1)).join(",") +
          ")",
        keys.map((k) =>
          row[k] !== null && typeof row[k] === "object"
            ? JSON.stringify(row[k])
            : row[k],
        ),
      );
    }
  }
  await c.query(
    "SELECT setval(pg_get_serial_sequence('audit_log','id'),greatest(coalesce((SELECT max(id) FROM audit_log),1),1))",
  );
});
console.log("Backup restored to isolated recovery schema");
await pool.end();
