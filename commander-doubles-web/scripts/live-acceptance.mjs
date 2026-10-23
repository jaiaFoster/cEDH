// Opt-in, destructive only to disposable test resources created by this script.
// BASE_URL must be staging with ALLOW_MOCK=true; never runs automatically in CI.
import fs from "node:fs";
import assert from "node:assert/strict";
import { Challonge, matchPlayers } from "../providers.mjs";
const base = process.env.BASE_URL;
if (
  !base ||
  !process.env.ADMIN_PASSWORD ||
  !process.env.CHALLONGE_API_KEY ||
  process.env.RUN_LIVE_ACCEPTANCE !== "true"
)
  throw Error(
    "Set staging BASE_URL, ADMIN_PASSWORD, CHALLONGE_API_KEY, RUN_LIVE_ACCEPTANCE=true",
  );
const provider = new Challonge();
let cookie = "",
  csrf = "";
async function api(path, method = "GET", body) {
  const r = await fetch(base + path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(cookie ? { cookie, "x-csrf-token": csrf } : {}),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await r.json();
  if (!r.ok) throw Error(path + ": " + r.status + " " + data.error);
  return { data, response: r };
}
const info = (await api("/api/home")).data;
if (!info.mockEnabled)
  throw Error(
    "Refusing live acceptance against a service without staging/test configuration",
  );
const auth = await api("/api/login", "POST", {
  password: process.env.ADMIN_PASSWORD,
});
cookie = auth.response.headers.get("set-cookie").split(";")[0];
csrf = auth.data.csrf;
const prefix = "Disposable acceptance " + Date.now().toString(36),
  teams = [];
const text =
  "COMMANDER\n1 Shorikai, Genesis Engine\nMAINBOARD\n98 Island\n1 Sol Ring";
for (let i = 1; i <= 4; i++) {
  const t = (await api("/api/teams", "POST", { name: prefix + " Team " + i }))
    .data;
  for (const slot of [1, 2])
    await api(`/api/teams/${t.id}/decks/${slot}`, "POST", { text });
  teams.push(t);
}
const completed = [];
let frozen;
for (const format of ["single elimination", "round robin"]) {
  const e = (
    await api("/api/admin/events", "POST", {
      name: prefix + " " + format,
      description: "Disposable automated acceptance; not a real league event.",
      starts_at: new Date(Date.now() + 86400000).toISOString(),
      provider: "challonge",
      tournament_type: format,
    })
  ).data;
  await api("/api/admin/events/" + e.id, "PATCH", { status: "registration" });
  for (const t of teams)
    await api("/api/events/" + e.id + "/register", "POST", { team_id: t.id });
  await api("/api/admin/events/" + e.id, "PATCH", { status: "scheduled" });
  await api("/api/admin/events/" + e.id + "/lock", "POST", { locked: true });
  await api("/api/admin/events/" + e.id + "/tournament", "POST", {});
  for (let n = 0; n < 2; n++)
    await api("/api/admin/events/" + e.id + "/participants", "POST", {});
  await api("/api/admin/events/" + e.id + "/start", "POST", {});
  let current = (await api("/api/events/" + e.id)).data;
  assert.equal(current.registrations.length, 4);
  assert.equal(
    new Set(current.registrations.map((r) => r.participant_id)).size,
    4,
  );
  let rounds = 0;
  while (current.matches.some((m) => m.state === "open")) {
    if (++rounds > 20) throw Error("Bounded acceptance loop exceeded");
    for (const match of current.matches.filter((m) => m.state === "open")) {
      assert.ok(match.players.every(Boolean));
      await provider.report(
        current.tournament_id,
        match.id,
        matchPlayers(match).map((participant_id, i) => ({
          participant_id,
          score_set: i === 0 ? "1" : "0",
          advancing: i === 0,
        })),
      );
    }
    await api("/api/admin/events/" + e.id + "/sync", "POST", {});
    current = (await api("/api/events/" + e.id)).data;
  }
  await api("/api/admin/events/" + e.id + "/finalize", "POST", {});
  current = (await api("/api/events/" + e.id)).data;
  assert.equal(current.status, "complete");
  assert.equal(current.standings.length, 4);
  assert.ok(current.champion);
  if (frozen)
    assert.deepEqual(
      (await api("/api/events/" + completed[0].id)).data,
      frozen,
    );
  else frozen = structuredClone(current);
  completed.push(current);
}
fs.mkdirSync("reports", { recursive: true });
fs.writeFileSync(
  "reports/live-challonge.json",
  JSON.stringify(
    { base, provider: "actual Challonge v2.1", events: completed },
    null,
    2,
  ),
);
console.log("Live acceptance passed:", completed.map((e) => e.id).join(", "));
