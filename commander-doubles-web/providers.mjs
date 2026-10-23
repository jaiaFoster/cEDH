import { randomUUID } from "node:crypto";
export class Challonge {
  constructor({
    key = process.env.CHALLONGE_API_KEY,
    fetcher = fetch,
    timeout = 12000,
  } = {}) {
    this.key = key;
    this.fetcher = fetcher;
    this.timeout = timeout;
  }
  async request(method, path, attributes, type) {
    if (!this.key) throw Error("Challonge API key is not configured");
    let res;
    try {
      res = await this.fetcher("https://api.challonge.com/v2.1" + path, {
        method,
        signal: AbortSignal.timeout(this.timeout),
        headers: {
          Authorization: this.key,
          "Authorization-Type": "v1",
          Accept: "application/json",
          "Content-Type": "application/vnd.api+json",
          "User-Agent": "CommanderDoublesLeague/1.0",
        },
        ...(attributes
          ? { body: JSON.stringify({ data: { type, attributes } }) }
          : {}),
      });
    } catch {
      throw Error(
        "Challonge timed out or could not be reached; saved results are unchanged",
      );
    }
    if (!res.ok) {
      let detail = "";
      try {
        const body = await res.json();
        detail = (body.errors || [])
          .map((e) => JSON.stringify({ detail: e.detail, source: e.source }))
          .join("; ")
          .slice(0, 800);
      } catch {}
      const e = new Error(
        "Challonge HTTP " +
          res.status +
          (res.status === 429 ? " — rate limit; retry later" : "") +
          (detail ? " — " + detail : ""),
      );
      e.status = res.status;
      throw e;
    }
    if (res.status === 204) return null;
    return (await res.json()).data;
  }
  async all(path) {
    let out = [];
    for (let page = 1; page <= 100; page++) {
      const data = await this.request(
        "GET",
        path +
          (path.includes("?") ? "&" : "?") +
          "page=" +
          page +
          "&per_page=100",
      );
      if (!Array.isArray(data)) throw Error("Unexpected Challonge collection");
      out.push(...data);
      if (data.length < 100) return out;
    }
    throw Error("Challonge pagination limit reached");
  }
  async create(name, type = "single elimination", slug) {
    const data = await this.request(
      "POST",
      "/tournaments",
      {
        name,
        tournament_type: type,
        ...(type === "round robin"
          ? { round_robin_options: { iterations: 1, ranking: "match wins" } }
          : {}),
        ...(type === "swiss"
          ? {
              swiss_options: {
                rounds: 3,
                pts_for_match_win: 1,
                pts_for_match_tie: 0.5,
                pts_for_game_win: 0,
                pts_for_game_tie: 0,
              },
            }
          : {}),
        ...(type === "double elimination"
          ? {
              double_elimination_options: {
                split_participants: false,
                grand_finals_modifier: "",
              },
            }
          : {}),
        url: slug || "cd_" + randomUUID().replaceAll("-", ""),
        private: true,
      },
      "Tournaments",
    );
    return { id: data.id, ...data.attributes };
  }
  async participant(id, name, misc) {
    const d = await this.request(
      "POST",
      `/tournaments/${encodeURIComponent(id)}/participants`,
      { name, misc },
      "Participants",
    );
    return { id: String(d.id), ...d.attributes };
  }
  async participants(id) {
    return (
      await this.all(`/tournaments/${encodeURIComponent(id)}/participants`)
    ).map((d) => ({ id: String(d.id), ...d.attributes }));
  }
  async state(id, state) {
    return this.request(
      "PUT",
      `/tournaments/${encodeURIComponent(id)}/change_state`,
      { state },
      "TournamentState",
    );
  }
  async report(id, match, entries) {
    return this.request(
      "PUT",
      `/tournaments/${encodeURIComponent(id)}/matches/${encodeURIComponent(match)}`,
      { match: entries },
      "Match",
    );
  }
  async snapshot(id) {
    const t = await this.request(
      "GET",
      `/tournaments/${encodeURIComponent(id)}`,
    );
    const participants = await this.participants(id);
    const matches = (
      await this.all(`/tournaments/${encodeURIComponent(id)}/matches`)
    ).map((d) => ({
      id: String(d.id),
      ...d.attributes,
      relationships: d.relationships,
    }));
    return {
      tournament: { id: String(t.id), ...t.attributes },
      participants,
      matches,
    };
  }
}
// Test provider only: production never uses local advancement or local match reporting.
export class MockProvider {
  constructor(client) {
    this.c = client;
  }
  async load(id) {
    const r = await this.c.query(
      "SELECT state FROM mock_tournaments WHERE id=$1 FOR UPDATE",
      [id],
    );
    if (!r.rowCount) throw Error("Mock tournament missing");
    return r.rows[0].state;
  }
  async save(s) {
    await this.c.query("UPDATE mock_tournaments SET state=$2 WHERE id=$1", [
      s.tournament.id,
      JSON.stringify(s),
    ]);
    return s;
  }
  async create(name, type = "single elimination") {
    if (type !== "single elimination")
      throw Error("Mock supports single elimination only");
    const id = "mock-" + randomUUID();
    await this.c.query("INSERT INTO mock_tournaments(id,state) VALUES($1,$2)", [
      id,
      JSON.stringify({
        tournament: { id, name, state: "pending", tournament_type: type },
        participants: [],
        matches: [],
      }),
    ]);
    return { id };
  }
  async participants(id) {
    return (await this.load(id)).participants;
  }
  async participant(id, name, misc) {
    const s = await this.load(id);
    const p = { id: String(s.participants.length + 1), name, misc };
    s.participants.push(p);
    await this.save(s);
    return p;
  }
  async state(id, state) {
    const s = await this.load(id);
    if (state === "start") {
      if (s.participants.length !== 4)
        throw Error("Mock fixture requires four participants");
      s.tournament.state = "underway";
      s.matches = [
        { id: "1", round: 1, state: "open", player1_id: "1", player2_id: "2" },
        { id: "2", round: 1, state: "open", player1_id: "3", player2_id: "4" },
        {
          id: "3",
          round: 2,
          state: "pending",
          player1_id: null,
          player2_id: null,
        },
      ];
    } else if (state === "finalize") {
      if (s.matches.some((m) => m.state !== "complete"))
        throw Error("Matches are incomplete");
      s.tournament.state = "complete";
      const champion = s.matches[2].winner_id;
      for (const p of s.participants)
        p.final_rank =
          p.id === champion
            ? 1
            : [s.matches[2].player1_id, s.matches[2].player2_id].includes(p.id)
              ? 2
              : 3;
    } else throw Error("Unsupported state");
    await this.save(s);
  }
  async report(id, match, entries) {
    const s = await this.load(id),
      m = s.matches.find((m) => m.id === match),
      winner = entries.find((e) => e.advancing);
    if (
      !m ||
      m.state !== "open" ||
      !winner ||
      ![m.player1_id, m.player2_id].includes(String(winner.participant_id))
    )
      throw Error("Invalid result");
    m.winner_id = String(winner.participant_id);
    m.state = "complete";
    m.scores = entries.map((e) => e.score_set).join(" - ");
    if (
      s.matches[0].state === "complete" &&
      s.matches[1].state === "complete" &&
      s.matches[2].state === "pending"
    )
      Object.assign(s.matches[2], {
        player1_id: s.matches[0].winner_id,
        player2_id: s.matches[1].winner_id,
        state: "open",
      });
    await this.save(s);
  }
  async snapshot(id) {
    return this.load(id);
  }
}
export const providerFor = (event, c) =>
  event.provider === "mock" ? new MockProvider(c) : new Challonge();
export function matchPlayers(match) {
  const rel = match.relationships?.participants?.data;
  return [
    match.player1_id ??
      match.points_by_participant?.[0]?.participant_id ??
      (Array.isArray(rel) ? rel[0]?.id : null),
    match.player2_id ??
      match.points_by_participant?.[1]?.participant_id ??
      (Array.isArray(rel) ? rel[1]?.id : null),
  ].map((x) => (x == null ? null : String(x)));
}
