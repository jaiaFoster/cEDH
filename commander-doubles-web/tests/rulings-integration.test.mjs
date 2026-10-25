import test from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
if (!process.env.DATABASE_URL)
  throw Error("Real disposable PostgreSQL required");
process.env.DATABASE_SCHEMA = "test_ruling_" + randomUUID().replaceAll("-", "");
process.env.ADMIN_PASSWORD = "rulings-integration-password";
process.env.SESSION_SECRET = "rulings-integration-session";
process.env.ALLOW_MOCK = "true";
const { pool, q, migrate } = await import("../db.mjs");
const { createApp } = await import("../app.mjs");
await test("real PostgreSQL rulings workflow and recovery", async (t) => {
  await migrate();
  await migrate();
  const server = createApp().listen(0, "127.0.0.1");
  await new Promise((r) => server.on("listening", r));
  const base = "http://127.0.0.1:" + server.address().port;
  let cookie, csrf, latest, content;
  async function call(
    p,
    m = "GET",
    body,
    auth = false,
    status = 200,
    headers = {},
  ) {
    const r = await fetch(base + p, {
      method: m,
      headers: {
        "content-type": "application/json",
        ...(auth ? { cookie, "x-csrf-token": csrf } : {}),
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const data = await r.json();
    assert.equal(r.status, status, JSON.stringify(data));
    return { data, r };
  }
  try {
    await t.test(
      "insert-only seed initializes verified entries and private drafts idempotently",
      async () => {
        assert.equal(
          (await q("SELECT count(*) FROM ruling_entries")).rows[0].count,
          "60",
        );
        assert.equal(
          (await q("SELECT count(*) FROM ruling_versions")).rows[0].count,
          "60",
        );
        const { data } = await call("/api/rulings");
        assert.equal(data.total, 57);
        await call(
          "/api/rulings/commander-aggregation",
          "GET",
          undefined,
          false,
          404,
        );
        await call("/api/admin/rulings", "GET", undefined, false, 401);
      },
    );
    await t.test(
      "v1 schema upgrade preserves published prices and rules",
      async () => {
        const beforePrices = (
          await q("SELECT * FROM price_versions ORDER BY id")
        ).rows;
        const beforeRules = (
          await q("SELECT * FROM rules_versions ORDER BY id")
        ).rows;
        await q("DROP TABLE ruling_entries,ruling_versions CASCADE");
        await q("DELETE FROM migrations WHERE version=2");
        await migrate();
        assert.deepEqual(
          (await q("SELECT * FROM price_versions ORDER BY id")).rows,
          beforePrices,
        );
        assert.deepEqual(
          (await q("SELECT * FROM rules_versions ORDER BY id")).rows,
          beforeRules,
        );
        assert.equal((await call("/api/rulings")).data.total, 57);
      },
    );
    await t.test(
      "public search, category/classification intersection, retrieval and references",
      async () => {
        const y = (await call("/api/rulings?q=Yuriko")).data;
        assert.ok(y.total >= 3);
        const filtered = (
          await call(
            "/api/rulings?q=Kinnan&category=False-positive%20combos&classification=Doesn%E2%80%99t%20Work",
          )
        ).data;
        assert.equal(filtered.total, 1);
        const r = (await call("/api/rulings/pox-bloodletter")).data;
        assert.ok(r.sources[0].includes("MagicCompRules"));
        assert.ok(r.rule_references.includes("810.9a"));
        assert.ok(r.cards[0].oracle_id);
        assert.equal(
          (await call("/api/rulings?q=nonexistentfoo")).data.total,
          0,
        );
        await call(
          "/api/rulings?category=invented",
          "GET",
          undefined,
          false,
          400,
        );
      },
    );
    await t.test(
      "auth, CSRF, immutable drafts, explicit publish and stale-write protection",
      async () => {
        const login = await call("/api/login", "POST", {
          password: process.env.ADMIN_PASSWORD,
        });
        cookie = login.r.headers.get("set-cookie").split(";")[0];
        csrf = login.data.csrf;
        await call("/api/admin/rulings", "POST", {}, true, 403, {
          "x-csrf-token": "wrong",
        });
        content = {
          ...(await call("/api/rulings/shared-resources")).data,
          id: "test-ruling-entry",
          title: "Test source-backed ruling",
          change_note: "Create a test draft",
          verification_status: "needs_review",
          verified_on: "",
          verified_by: "",
        };
        latest = (
          await call("/api/admin/rulings", "POST", { content }, true, 201)
        ).data.id;
        await call(
          "/api/rulings/test-ruling-entry",
          "GET",
          undefined,
          false,
          404,
        );
        await call(
          "/api/admin/rulings/test-ruling-entry/publish",
          "POST",
          { version_id: latest },
          true,
          400,
        );
        content = {
          ...content,
          title: "<img src=x onerror=alert(1)> Safe literal title",
          verification_status: "verified",
          verified_on: "2026-10-24",
          verified_by: "Test reviewer",
          change_note: "Reviewed version",
        };
        const first = latest;
        latest = (
          await call(
            "/api/admin/rulings/test-ruling-entry/drafts",
            "POST",
            { content, base_version_id: latest },
            true,
          )
        ).data.id;
        await call(
          "/api/admin/rulings/test-ruling-entry/drafts",
          "POST",
          { content, base_version_id: first },
          true,
          409,
        );
        await call(
          "/api/admin/rulings/test-ruling-entry/publish",
          "POST",
          { version_id: first },
          true,
          409,
        );
        await call(
          "/api/admin/rulings/test-ruling-entry/publish",
          "POST",
          { version_id: latest },
          true,
        );
        assert.equal(
          (await call("/api/rulings/test-ruling-entry")).data.title,
          content.title,
        );
        const hist = (
          await call(
            "/api/admin/rulings/test-ruling-entry/history",
            "GET",
            undefined,
            true,
          )
        ).data;
        assert.equal(hist.length, 2);
        assert.equal(hist[1].content.title, "Test source-backed ruling");
      },
    );
    await t.test(
      "draft edit preserves public version; hide, migration and restore preserve organizer history",
      async () => {
        latest = (
          await call(
            "/api/admin/rulings/test-ruling-entry/drafts",
            "POST",
            {
              content: { ...content, title: "Unpublished correction" },
              base_version_id: latest,
            },
            true,
          )
        ).data.id;
        assert.notEqual(
          (await call("/api/rulings/test-ruling-entry")).data.title,
          "Unpublished correction",
        );
        await call(
          "/api/admin/rulings/test-ruling-entry/hide",
          "POST",
          { reason: "Needs correction" },
          true,
        );
        await call(
          "/api/rulings/test-ruling-entry",
          "GET",
          undefined,
          false,
          404,
        );
        await migrate();
        await call(
          "/api/rulings/test-ruling-entry",
          "GET",
          undefined,
          false,
          404,
        );
        // Hide seeded entry as well: migrations must not republish it.
        await call(
          "/api/admin/rulings/shared-resources/hide",
          "POST",
          { reason: "Test seed safety" },
          true,
        );
        await migrate();
        await call(
          "/api/rulings/shared-resources",
          "GET",
          undefined,
          false,
          404,
        );
        const restored = (
          await call(
            "/api/admin/rulings/test-ruling-entry/restore",
            "POST",
            { version_id: latest, reason: "Historical recovery test" },
            true,
          )
        ).data;
        assert.equal(restored.content.verification_status, "needs_review");
        assert.equal(restored.content.verified_by, "");
        await call(
          "/api/admin/rulings/test-ruling-entry/publish",
          "POST",
          { version_id: restored.id },
          true,
          400,
        );
        const exported = (
          await call("/api/admin/rulings/export", "GET", undefined, true)
        ).data;
        assert.equal(exported.entries.length, 61);
        assert.equal(exported.versions.length, 64);
      },
    );
    await t.test(
      "unsafe links and mismatched IDs rejected; complete backup restores history to isolated schema",
      async () => {
        await call(
          "/api/admin/rulings/test-ruling-entry/drafts",
          "POST",
          {
            content: { ...content, sources: ["javascript:alert(1)"] },
            base_version_id: latest,
          },
          true,
          400,
        );
        const backup = (await call("/api/admin/export", "GET", undefined, true))
          .data;
        assert.equal(backup.ruling_entries.length, 61);
        const file = "/tmp/rulings-backup-" + randomUUID() + ".json";
        fs.writeFileSync(file, JSON.stringify(backup), { mode: 0o600 });
        const recovery = "restore_rulings_" + randomUUID().replaceAll("-", "");
        try {
          // Child executes synchronous; parent has released every DB client.
          execFileSync(process.execPath, ["scripts/restore.mjs", file], {
            cwd: new URL("../", import.meta.url),
            env: { ...process.env, DATABASE_SCHEMA: recovery },
            timeout: 60000,
          });
          assert.equal(
            (await q(`SELECT count(*) FROM ${recovery}.ruling_versions`))
              .rows[0].count,
            "64",
          );
          assert.equal(
            (
              await q(
                `SELECT hidden FROM ${recovery}.ruling_entries WHERE id='shared-resources'`,
              )
            ).rows[0].hidden,
            true,
          );
        } finally {
          fs.unlinkSync(file);
          await q("DROP SCHEMA IF EXISTS " + recovery + " CASCADE");
        }
      },
    );
  } finally {
    await new Promise((r) => server.close(r));
    await q("DROP SCHEMA " + process.env.DATABASE_SCHEMA + " CASCADE");
    await pool.end();
  }
});
