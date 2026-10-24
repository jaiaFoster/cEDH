const $ = (s) => document.querySelector(s),
  main = $("#main");
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
let state,
  session = { admin: false },
  adminTab = "overview",
  pointPage = 0,
  activeEvent = null;
const teamId = () => localStorage.getItem("cd-team");
const setTeam = (id) => {
  localStorage.setItem("cd-team", id);
};
let noticeTimer;
function notice(message, error = false) {
  const n = $("#notice");
  n.textContent = message;
  n.className = error ? "error" : "";
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(
    () => {
      n.textContent = "";
    },
    error ? 11000 : 5000,
  );
}
async function api(url, method = "GET", body) {
  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(session.csrf ? { "x-csrf-token": session.csrf } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "Request failed");
  return data;
}
const action = (title, fn, primary = false) =>
  `<button type="button" data-action="${esc(fn)}" class="${primary ? "primary" : ""}">${esc(title)}</button>`;
const tag = (text, warn = false) =>
  `<span class="tag ${warn ? "warn" : ""}">${esc(text)}</span>`;
const empty = (title, body = "") =>
  `<div class="empty"><strong>${esc(title)}</strong>${esc(body)}</div>`;
const dt = (d, tz = "America/Phoenix") =>
  d
    ? new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: tz,
      }).format(new Date(d)) +
      " · " +
      tz
    : "Not set";
const head = (kicker, title, description) =>
  `<div class="page-head"><div><div class="eyebrow">${esc(kicker)}</div><h1>${esc(title)}</h1><p>${esc(description)}</p></div></div>`;
const field = (name, label, value = "", type = "text", extra = "") =>
  `<div class="field"><label for="${esc(name)}">${esc(label)}</label><input id="${esc(name)}" name="${esc(name)}" type="${type}" value="${esc(value)}" ${extra}></div>`;
const area = (name, label, value = "", extra = "") =>
  `<div class="field"><label for="${esc(name)}">${esc(label)}</label><textarea id="${esc(name)}" name="${esc(name)}" ${extra}>${esc(value)}</textarea></div>`;
const teamOptions = (id = teamId(), all = false) =>
  `<option value="">Choose a team</option>${(all ? adminData?.teams : state.teams || []).map((t) => `<option value="${t.id}" ${t.id === id ? "selected" : ""}>${esc(t.name)}${t.archived ? " (archived)" : ""}</option>`).join("")}`;
function eventCard(e) {
  return `<article class="panel event-card">${tag(e.provider === "mock" ? "Test fixture · " + e.status : e.status)}<h3>${esc(e.name)}</h3><div class="meta">${esc(dt(e.starts_at, e.timezone))}</div><div class="meta">${esc(e.location)}</div><p>${esc(e.description || "Bring a teammate. Build together. Play as one.")}</p><div class="actions"><a class="button ${e.status === "registration" ? "primary" : ""}" href="/events/${e.id}">${e.status === "registration" ? "View & register →" : "View tournament →"}</a></div></article>`;
}
function matchCard(m) {
  return `<article class="match"><div class="match-head"><span class="meta">Round ${esc(m.round)} · Match ${esc(m.identifier || m.id)}</span>${tag(m.state)}</div>${(m.players || []).map((p) => `<div class="match-team ${p && String(m.winner_id) === p.id ? "winner" : ""}"><span>${esc(p?.name || "To be determined")}</span>${p && String(m.winner_id) === p.id ? "<span>Winner ↗</span>" : ""}</div>`).join("")}<span class="meta">${esc(typeof m.scores === "string" ? m.scores : "")}</span></article>`;
}
function scoreMarkup(s) {
  if (!s) return "";
  return `<div class="result ${s.legal && s.withinIndividualBudget ? "good" : "bad"}"><div class="eyebrow">${esc(s.name)}</div><span class="total">${s.points}</span> <span class="meta">points · ${s.count}/100 cards</span><p>${s.legal ? "Construction checks passed against the pinned catalog." : "Construction requires attention."} ${s.withinIndividualBudget ? "" : "Above the individual 72-point cap."}</p>${s.errors?.length ? `<ul class="error-list">${s.errors.map((e) => `<li>${esc(e)}</li>`).join("")}</ul>` : ""}<details><summary>${s.pointed.length} pointed cards · view breakdown</summary><table><thead><tr><th>Card / zone</th><th class="num">Each</th><th class="num">Points</th></tr></thead><tbody>${s.pointed.map((c) => `<tr><td>${c.count} ${esc(c.name)}<br><span class="meta">${esc(c.zone)}</span></td><td class="num">${c.each}</td><td class="num">${c.points}</td></tr>`).join("")}</tbody></table></details></div>`;
}
function teamScore(s) {
  return s?.checked
    ? `<div class="result ${s.within ? "good" : "bad"}"><h3>Team total <span class="count">${s.points} / 120</span></h3><p>${s.within ? "Within budget. Both decks pass supported construction checks." : s.budgetWithin ? "Budget passes; construction needs attention." : "Over budget or incomplete."} Transfer: ${s.transfer} / 12 points.</p></div>`
    : empty(
        "Two decks make a team",
        "Save both decks to check the combined budget.",
      );
}
async function home() {
  const running = state.events.find((e) => e.status === "running"),
    upcoming = state.events.filter((e) =>
      ["registration", "scheduled"].includes(e.status),
    ),
    featured = running || upcoming[0],
    completed = state.events.filter((e) => e.status === "complete").at(-1);
  main.innerHTML = `<section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="dot"></span> Competitive 2v2 Commander</div><h1>Two decks.<br>One <em>winning team.</em></h1><p class="lead">Build together. Share the battlefield. A Commander league where teamwork matters as much as the cards you bring.</p><div class="actions"><a class="button primary" href="${featured ? "/events/" + featured.id : "/teams"}">${featured?.status === "running" ? "Follow the tournament ↗" : featured?.status === "registration" ? "Register your team ↗" : "Find your team ↗"}</a><a class="button quiet" href="/rules">Explore the format →</a></div></div><div class="panel feature-panel"><div class="eyebrow"><span class="dot"></span> ${running ? "Live tournament" : featured ? "Up next" : completed ? "Latest champion" : "The next chapter"}</div><h2 class="feature-title">${esc(featured?.name || completed?.champion || "Your teammate is your strongest card.")}</h2><p>${featured ? esc(dt(featured.starts_at, featured.timezone)) : completed ? esc(completed.name) : "Create your team, explore the points, and be ready for the next league event."}</p>${featured ? tag(featured.status) : tag("Season 0 · v3")}<div class="actions"><a class="text-link" href="${featured ? "/events/" + featured.id : "/schedule"}">${featured ? "Tournament details" : "View the league schedule"} →</a></div></div></section><section class="stats" aria-label="Format at a glance"><div class="stat"><strong>2 × 100</strong><span>cards per team</span></div><div class="stat"><strong>120</strong><span>shared team points</span></div><div class="stat"><strong>72</strong><span>maximum individual points</span></div><div class="stat"><strong>60</strong><span>shared starting life</span></div></section><section class="wide-grid"><div><div class="section-head"><div><h2>${running ? "On the battlefield" : "League schedule"}</h2><p>${running ? "Pairings, results, and your next match." : "Make time for your next match."}</p></div><a class="text-link meta" href="/schedule">All events ↗</a></div><div id="home-event">${running ? '<div class="panel">Loading live pairings…</div>' : upcoming.length ? `<div class="grid two">${upcoming.slice(0, 2).map(eventCard).join("")}</div>` : `<div class="panel">${empty("No event announced yet", "Save your team and decks now. The next event will appear here when published.")}</div>`}</div></div><div><div class="section-head"><h2>Your team</h2></div><div class="panel selected-team"><label for="home-team">Remember a team on this browser</label><select id="home-team">${teamOptions()}</select><div id="home-team-info">${empty("Ready when you are", "Choose a registered team or create your own.")}</div><a class="button small spaced" href="/teams">Manage team & decks →</a></div></div></section><div class="section-head"><div><h2>Built for the team game</h2><p>A shared budget. More room to build your way.</p></div></div><div class="grid"><article class="panel"><span class="eyebrow">01 / Build</span><h3 class="spaced">Make every point count.</h3><p>Search the complete card catalog. Main-deck and command-zone prices are separate, with up to 12 points available to transfer.</p><a class="text-link meta" href="/points">Browse card points →</a></article><article class="panel"><span class="eyebrow">02 / Submit</span><h3 class="spaced">Two links. One lineup.</h3><p>Save public Moxfield decks, or paste an export. See your card breakdown, individual totals, and team budget.</p><a class="text-link meta" href="/teams">Prepare your decks →</a></article><article class="panel"><span class="eyebrow">03 / Compete</span><h3 class="spaced">Follow every round.</h3><p>Challonge powers the bracket. Results, winners, and frozen decklists stay in the league archive.</p><a class="text-link meta" href="/history">Tournament history →</a></article></div>`;
  $("#home-team").onchange = async (e) => {
    setTeam(e.target.value);
    await homeTeam(running);
  };
  await homeTeam(running);
  if (running) {
    const e = await api("/api/events/" + running.id);
    $("#home-event").innerHTML =
      `<div class="panel"><h3>${esc(e.name)}</h3><p class="meta">Last synced: ${esc(dt(e.synced_at))}</p>${e.sync_error ? `<p>${esc(e.sync_error)}</p>` : ""}${
        e.matches
          .filter((m) => m.state === "open")
          .map(matchCard)
          .join("") ||
        empty(
          "Waiting for pairings",
          "The latest saved tournament state is shown.",
        )
      }<a class="text-link" href="/events/${e.id}">Full bracket & standings →</a></div>`;
  }
}
async function homeTeam(event) {
  if (!teamId()) {
    return;
  }
  const team = state.teams.find((t) => t.id === teamId());
  if (!team) return;
  let extra = "";
  if (event) {
    const e = await api("/api/events/" + event.id);
    const match = e.matches.find(
      (m) =>
        m.state === "open" && m.players.some((p) => p?.team_id === team.id),
    );
    extra = match
      ? `<h3 class="spaced">Your next match</h3>${matchCard(match)}`
      : '<p class="spaced">No open match for your team in this event.</p>';
  }
  $("#home-team-info").innerHTML =
    `<h3 class="spaced">${esc(team.name)}</h3><p>${team.players.filter(Boolean).map(esc).join(" + ") || "Player names optional"}</p>${extra}`;
}
const defaultPointFilters = () => ({
  q: "",
  points: "pointed",
  zone: "either",
  identity: "",
  identityMode: "within",
  colorCount: "any",
  min: "",
  max: "",
  type: "",
  mvMin: "",
  mvMax: "",
  legality: "any",
  eligible: "any",
  sort: "main_desc",
  limit: "50",
});
let pointFilters = defaultPointFilters(),
  pointRequest,
  pointRequestId = 0,
  pointTimer;
const pointSelect = (id, label, options) =>
  '<div class="field"><label for="point-' +
  id +
  '">' +
  label +
  '</label><select id="point-' +
  id +
  '" data-point-filter="' +
  id +
  '">' +
  options
    .map(
      ([v, title]) =>
        '<option value="' +
        v +
        '"' +
        (pointFilters[id] === v ? " selected" : "") +
        ">" +
        title +
        "</option>",
    )
    .join("") +
  "</select></div>";
const pointRange = (id, label, step = "1") =>
  '<div class="field"><label for="point-' +
  id +
  '">' +
  label +
  '</label><input type="number" id="point-' +
  id +
  '" data-point-filter="' +
  id +
  '" min="0" step="' +
  step +
  '" value="' +
  esc(pointFilters[id]) +
  '" placeholder="Any"></div>';
async function points() {
  clearTimeout(pointTimer);
  pointRequest?.abort();
  main.innerHTML =
    head(
      "The deckbuilding budget",
      "Every card has its place.",
      "Find cards by identity, color, type, rules text, mana value, and league points. Main-deck and command-zone prices stay separate.",
    ) +
    '<section class="panel catalog-panel"><form id="points-search" role="search" aria-label="Card catalog">' +
    '<label for="card-search">Find a card</label><div class="catalog-search-bar"><input id="card-search" type="search" placeholder=\'id:wu t:artifact mv&lt;=3 o:"draw"\' aria-describedby="point-query-help" value="' +
    esc(pointFilters.q) +
    '"><button class="primary" type="submit">Search</button></div>' +
    '<details id="catalog-advanced" class="catalog-advanced"><summary>Advanced</summary>' +
    '<p class="help" id="point-query-help">Use names or combine <code>id:</code>, <code>c:</code>, <code>t:</code>, <code>o:</code>, and <code>mv</code> comparisons. Quote phrases, such as <code>"Sol Ring"</code>. Space-separated terms use AND.</p>' +
    '<details class="catalog-help"><summary>Search examples & supported syntax</summary><p class="help"><code>id:wu t:artifact mv&lt;=3</code> finds artifacts usable in white-blue identity. <code>c:u</code> requires blue color; <code>id=wu</code> requires exactly white-blue identity. <code>o:"draw a card" -t:creature</code> excludes creatures. <code>!"Sol Ring"</code> matches an exact name. Colorless uses <code>c:c</code> or <code>id:c</code>; multicolor uses <code>c:m</code> or <code>id:m</code>. Comparisons: <code>= != &lt; &lt;= &gt; &gt;=</code> for mana value and color sets. Other Scryfall operators, OR, groups, and regex are unsupported and show an error. Oracle text uses literal text from the pinned catalog, including reminder text.</p></details>' +
    '<fieldset class="identity-filter"><legend>Color identity</legend><div class="identity-options">' +
    [
      ["w", "White"],
      ["u", "Blue"],
      ["b", "Black"],
      ["r", "Red"],
      ["g", "Green"],
    ]
      .map(
        ([c, name]) =>
          '<label><input type="checkbox" name="identity-color" value="' +
          c +
          '"' +
          (pointFilters.identity.includes(c) ? " checked" : "") +
          '><span class="color-dot color-' +
          c +
          '" aria-hidden="true"></span>' +
          name +
          "</label>",
      )
      .join("") +
    "</div>" +
    '<div class="catalog-filter-grid">' +
    pointSelect("identityMode", "Identity matching", [
      ["within", "Within colors"],
      ["exact", "Exact colors"],
    ]) +
    pointSelect("colorCount", "Identity category", [
      ["any", "Any identity"],
      ["colorless", "Colorless"],
      ["multicolor", "Multicolor"],
    ]) +
    '</div><p class="help">No colors selected means any identity. Contained identity also permits colorless cards. Query conditions and filters are combined.</p></fieldset>' +
    '<div class="catalog-filter-grid">' +
    pointSelect("points", "Point values", [
      ["all", "All cards"],
      ["pointed", "Pointed only"],
      ["zero", "Zero only"],
    ]) +
    pointSelect("zone", "Point location", [
      ["either", "Either"],
      ["main", "Main deck"],
      ["command", "Command zone"],
    ]) +
    pointRange("min", "Minimum points") +
    pointRange("max", "Maximum points") +
    '</div><p class="help">Point ranges use the selected location. Either uses the higher price.</p>' +
    '<div id="catalog-more-filters" class="catalog-filter-grid spaced">' +
    pointSelect("type", "Card type", [
      ["", "Any type"],
      ...[
        "Artifact",
        "Battle",
        "Creature",
        "Enchantment",
        "Instant",
        "Land",
        "Planeswalker",
        "Sorcery",
      ].map((x) => [x.toLowerCase(), x]),
    ]) +
    pointRange("mvMin", "Minimum mana value", "0.5") +
    pointRange("mvMax", "Maximum mana value", "0.5") +
    pointSelect("legality", "Commander legality", [
      ["any", "Any status"],
      ["legal", "Legal"],
      ["banned", "Banned"],
      ["not_legal", "Not legal"],
    ]) +
    pointSelect("eligible", "Command-zone eligibility", [
      ["any", "Any card"],
      ["1", "Eligible only"],
    ]) +
    "</div>" +
    '<div class="catalog-sort-row">' +
    pointSelect("sort", "Sort results", [
      ["main_desc", "Main-deck points: high to low"],
      ["main_asc", "Main-deck points: low to high"],
      ["command_desc", "Command-zone points: high to low"],
      ["command_asc", "Command-zone points: low to high"],
      ["name_asc", "Card name: A to Z"],
      ["name_desc", "Card name: Z to A"],
      ["mv_asc", "Mana value: low to high"],
      ["mv_desc", "Mana value: high to low"],
    ]) +
    pointSelect("limit", "Cards per page", [
      ["50", "50"],
      ["100", "100"],
    ]) +
    '<button id="point-reset" type="button">Reset filters</button></div><p class="help">Prices: ' +
    esc(state.price.name) +
    '. Card metadata and legality: October 20, 2026. — means the card is not command-zone eligible; eligibility can require a legal pair. Price compliance does not certify deck legality.</p></details></form>' +
    '<div id="point-status" class="meta" role="status" aria-live="polite"></div><div id="point-table" aria-busy="true"></div></section>';
  const form = $("#points-search");
  function changed(debounce) {
    pointFilters.q = $("#card-search").value;
    pointFilters.identity = [
      ...form.querySelectorAll('[name="identity-color"]:checked'),
    ]
      .map((c) => c.value)
      .join("");
    for (const control of form.querySelectorAll("[data-point-filter]"))
      pointFilters[control.dataset.pointFilter] = control.value;
    pointPage = 0;
    clearTimeout(pointTimer);
    pointRequest?.abort();
    pointRequestId++;
    $("#point-status").textContent = "Searching…";
    $("#point-table").innerHTML = "";
    $("#point-table").setAttribute("aria-busy", "true");
    if (debounce) pointTimer = setTimeout(loadPoints, 200);
    else loadPoints();
  }
  form.onsubmit = (e) => {
    e.preventDefault();
    changed(false);
  };
  form.oninput = (e) => {
    if (e.target.matches('input:not([type="checkbox"])')) changed(true);
  };
  form.onchange = (e) => {
    if (e.target.matches('select, input[type="checkbox"]')) changed(false);
  };
  $("#point-reset").onclick = async () => {
    pointFilters = defaultPointFilters();
    pointPage = 0;
    await points();
    $("#card-search")?.focus();
  };
  await loadPoints();
}
async function loadPoints() {
  const requestId = ++pointRequestId;
  pointRequest?.abort();
  pointRequest = new AbortController();
  const params = new URLSearchParams({
    ...pointFilters,
    offset: String(pointPage * Number(pointFilters.limit)),
    version: state.price.id,
  });
  const target = $("#point-table");
  if (!target) return;
  target.setAttribute("aria-busy", "true");
  target.innerHTML = "";
  $("#point-status").textContent = "Searching…";
  try {
    const response = await fetch("/api/points?" + params, {
      signal: pointRequest.signal,
    });
    const data = response.headers
      .get("content-type")
      ?.includes("application/json")
      ? await response.json()
      : {
          error:
            response.status === 429
              ? "Too many searches. Please wait a minute and try again."
              : "The card catalog returned HTTP " +
                response.status +
                ". Please try again.",
        };
    if (requestId !== pointRequestId || !target.isConnected) return;
    if (!response.ok) {
      $("#point-status").textContent = "Search could not be completed.";
      target.innerHTML =
        '<div class="catalog-error" role="alert"><strong>' +
        (data.code === "unsupported_query"
          ? "Unsupported search syntax"
          : data.code?.includes("query") || data.code === "invalid_filter"
            ? "Check your search or filters"
            : "Unable to load card prices") +
        "</strong><p>" +
        esc(data.error || "Please try again.") +
        "</p></div>";
      return;
    }
    if (!Number.isInteger(data.total) || !Array.isArray(data.cards))
      throw Error(
        "The card catalog returned an unreadable response. Please try again.",
      );
    const first = data.total ? data.offset + 1 : 0,
      last = Math.min(data.total, data.offset + data.cards.length);
    $("#point-status").textContent =
      "Showing " +
      first.toLocaleString() +
      "–" +
      last.toLocaleString() +
      " of " +
      data.total.toLocaleString() +
      " cards · " +
      data.version.name;
    const identity = (c) =>
      c.identity.length ? c.identity.join(" / ") : "Colorless";
    const command = (c) => (c.commanderEligible || c.command ? c.command : "—");
    target.innerHTML =
      (data.cards.length
        ? '<div class="table-wrap"><table class="catalog-table"><caption class="sr-only">Matching league card prices</caption><thead><tr><th scope="col">Card</th><th class="num" scope="col">Main deck</th><th class="num" scope="col">Command zone</th></tr></thead><tbody>' +
          data.cards
            .map(
              (c) =>
                '<tr data-oracle-id="' +
                c.oracle_id +
                '"><td class="catalog-card"><a href="' +
                esc(c.url) +
                '" target="_blank" rel="noopener noreferrer">' +
                esc(c.name) +
                ' <span aria-hidden="true">↗</span></a><div class="help">' +
                esc(c.typeLine) +
                " · MV " +
                c.mv +
                " · Identity " +
                identity(c) +
                "</div>" +
                (c.legal
                  ? ""
                  : '<span class="tag warn">Not Commander legal</span>') +
                '</td><td class="num ' +
                (c.main ? "count" : "") +
                '">' +
                c.main +
                '</td><td class="num ' +
                (c.command ? "count" : "") +
                '">' +
                command(c) +
                "</td></tr>",
            )
            .join("") +
          "</tbody></table></div>"
        : empty(
            "No matching cards",
            "Try fewer conditions, change the point view, or reset filters.",
          )) +
      '<div class="actions catalog-pagination"><button type="button" data-action="points-prev"' +
      (pointPage === 0 ? " disabled" : "") +
      '>← Previous</button><span class="meta">Page ' +
      (pointPage + 1) +
      " of " +
      Math.max(1, Math.ceil(data.total / data.limit)) +
      '</span><button type="button" data-action="points-next"' +
      (data.offset + data.limit >= data.total ? " disabled" : "") +
      ">Next →</button></div>";
  } catch (error) {
    if (
      error.name === "AbortError" ||
      requestId !== pointRequestId ||
      !target.isConnected
    )
      return;
    $("#point-status").textContent = "Unable to load card prices.";
    target.innerHTML =
      '<div class="catalog-error" role="alert">' +
      esc(error.message) +
      " Submit the search again to retry.</div>";
  } finally {
    if (requestId === pointRequestId && target.isConnected)
      target.setAttribute("aria-busy", "false");
  }
}
async function teams() {
  main.innerHTML =
    head(
      "Your side of the table",
      "Find your team.",
      "One team identity across every tournament. Anyone can edit unlocked decks. Previous versions are saved.",
    ) +
    `<div class="wide-grid"><div class="stack"><div class="panel"><label for="team-select">Select a registered team</label><select id="team-select">${teamOptions()}</select><div id="team-detail"></div></div></div><div class="panel"><h2>Make it official.</h2><p>Create your team once. Bring it back every event.</p><form id="create-team">${field("team-name", "Unique team name", "", "text", 'required maxlength="80"')}<div class="fields">${field("player-one", "Player one (optional)")}${field("player-two", "Player two (optional)")}</div><button class="primary" type="submit">Create team →</button></form></div></div>`;
  $("#team-select").onchange = async (e) => {
    setTeam(e.target.value);
    await teamDetail();
  };
  $("#create-team").onsubmit = async (e) => {
    e.preventDefault();
    await busy(e.submitter, async () => {
      const t = await api("/api/teams", "POST", {
        name: $("#team-name").value,
        players: [$("#player-one").value, $("#player-two").value],
      });
      setTeam(t.id);
      await reload();
      await teams();
      notice("Team created. Add your two decks.");
    });
  };
  await teamDetail();
}
async function teamDetail() {
  if (!teamId()) {
    if ($("#team-detail"))
      $("#team-detail").innerHTML = empty(
        "Pick your side",
        "Select a team to view its decks and edit its details.",
      );
    return;
  }
  const t = await api("/api/teams/" + teamId());
  $("#team-detail").innerHTML =
    `<div class="divider"></div><form id="edit-team"><div class="fields">${field("edit-name", "Team name", t.name, "text", 'required maxlength="80"')}${field("edit-p1", "Player one", t.players[0] || "")}</div>${field("edit-p2", "Player two", t.players[1] || "")}<button class="small" type="submit">Save team details</button></form>${teamScore(t.team_score)}<p class="help">General decks are reusable. Saving here does not change event submissions; update those on the event page before the lock.</p>${[1, 2].map((slot) => deckForm(t, slot)).join("")}`;
  $("#edit-team").onsubmit = async (e) => {
    e.preventDefault();
    await busy(e.submitter, async () => {
      await api("/api/teams/" + t.id, "PATCH", {
        name: $("#edit-name").value,
        players: [$("#edit-p1").value, $("#edit-p2").value],
      });
      await reload();
      notice("Team details saved");
    });
  };
  for (const slot of [1, 2]) {
    const form = $("#deck-" + slot);
    $("#upload-" + slot).onchange = async (e) => {
      const f = e.target.files[0];
      if (f) {
        if (f.size > 50000) return notice("Export must be under 50 KB", true);
        $("#export-" + slot).value = await f.text();
      }
    };
    form.onsubmit = async (e) => {
      e.preventDefault();
      await busy(e.submitter, async () => {
        await api(`/api/teams/${t.id}/decks/${slot}`, "POST", {
          link: $("#link-" + slot).value,
          text: $("#export-" + slot).value,
        });
        await teamDetail();
        notice("Deck scored and saved. Review the validation below.");
      });
    };
  }
}
function deckForm(t, slot) {
  const d = t.decks.find((d) => d.slot === slot);
  return `<section class="spaced"><div class="divider"></div><span class="eyebrow">Player ${slot}</span><h3 class="spaced">${esc(t.players[slot - 1] || "Deck " + slot)}</h3>${d ? `<p class="meta">Saved ${esc(dt(d.created_at))} · ${esc(d.deck.name)}</p>${scoreMarkup(d.current_score)}` : ""}<form id="deck-${slot}">${field("link-" + slot, "Public Moxfield deck URL", d?.source_url || "", "url", 'placeholder="https://moxfield.com/decks/…"')}<details ${d ? "" : "open"}><summary>Paste or upload a Moxfield text export</summary><p class="help">If Moxfield blocks automatic access, use its text export. Include COMMANDER and MAINBOARD (or DECK) section headings. Sideboard and maybeboard are ignored.</p>${area("export-" + slot, "Deck export", "", 'placeholder="COMMANDER&#10;1 Your Commander&#10;&#10;MAINBOARD&#10;99 Island"')}<div class="field"><label for="upload-${slot}">Upload .txt export</label><input id="upload-${slot}" type="file" accept=".txt,text/plain"></div></details><div class="actions"><button type="submit" class="primary">Score & save player ${slot}</button></div></form></section>`;
}
async function eventPage(eventId) {
  const e = await api("/api/events/" + eventId);
  activeEvent = e;
  main.innerHTML =
    head(
      e.provider === "mock" ? "Disposable test tournament" : "League event",
      e.name,
      e.description,
    ) +
    `<div class="actions">${tag(e.status)}${tag(e.submissions_locked ? "Decks locked" : "Decks open", e.submissions_locked)}<span class="meta">${esc(dt(e.starts_at, e.timezone))} · ${esc(e.location)}</span></div><div class="wide-grid spaced"><section class="stack"><div class="panel"><h2>Pairings & next matches</h2><p class="meta">Challonge state: ${esc(e.tournament_state || "Not started")}<br>Last synchronized: ${esc(dt(e.synced_at, e.timezone))}</p>${e.sync_error ? `<p class="danger">${esc(e.sync_error)} · Saved results remain available.</p>` : ""}${e.champion ? `<div class="result good"><div class="eyebrow">Tournament champion</div><h2 class="spaced">${esc(e.champion)}</h2></div>` : ""}${
      e.matches
        .filter((m) => m.state === "open")
        .map(matchCard)
        .join("") ||
      empty(
        "No open matches",
        e.status === "complete"
          ? "All matches are complete."
          : "Pairings appear after the organizer starts the tournament.",
      )
    }<details><summary>All rounds & results</summary>${e.matches.map(matchCard).join("") || empty("No results yet")}</details>${e.tournament_url ? `<div class="actions"><a class="button" href="${esc(e.tournament_url)}" target="_blank" rel="noopener">Open Challonge ↗</a></div><details><summary>View embedded bracket</summary><iframe title="Challonge tournament bracket" src="${esc(e.tournament_url)}/module" width="100%" height="520" loading="lazy" sandbox="allow-scripts allow-same-origin allow-popups"></iframe></details>` : ""}</div><div class="panel"><h2>${e.status === "complete" ? "Final standings" : "Registered teams"}</h2>${e.standings.length ? `<table><thead><tr><th>Rank</th><th>Team</th></tr></thead><tbody>${e.standings.map((p) => `<tr><td>${p.final_rank}</td><td>${esc(p.name)}</td></tr>`).join("")}</tbody></table>` : ""}${e.registrations.map((r) => `<details><summary>${esc(r.team_name)} · ${r.score?.points ?? "—"} points ${r.score?.within ? "✓" : "· needs decks"}</summary><p class="help">Event snapshot updated ${esc(dt(r.updated_at, e.timezone))}</p>${r.decks.map((d) => scoreMarkup(d.score) + `<details><summary>View resolved decklist</summary><pre>${esc(d.deck.cards.map((c) => `${c.zone === "command" ? "[Commander] " : ""}${c.count} ${c.name}`).join("\n"))}</pre></details>`).join("") || empty("No submitted decks yet")}</details>`).join("") || empty("The roster is open", "Be the first team to register.")}</div></section><aside class="stack"><div class="panel selected-team"><h2>Your team</h2><label for="event-team">Choose a team</label><select id="event-team">${teamOptions()}</select><div id="event-team-info"></div></div><div class="panel"><h3>Event details</h3><p class="meta">${esc(e.location)}<br>${esc(dt(e.starts_at, e.timezone))}</p><div class="divider"></div><p class="meta">Registration opens<br><strong>${esc(dt(e.registration_opens, e.timezone))}</strong></p><p class="meta">Registration closes<br><strong>${esc(dt(e.registration_closes, e.timezone))}</strong></p><p class="meta">Deck deadline<br><strong>${esc(dt(e.lock_at, e.timezone))}</strong></p><p class="help">Prices are frozen for this event. Later price publications do not change this tournament.</p></div></aside></div>`;
  $("#event-team").onchange = (e2) => {
    setTeam(e2.target.value);
    eventTeam(e);
  };
  eventTeam(e);
}
function eventTeam(e) {
  const t = state.teams.find((t) => t.id === teamId()),
    r = e.registrations.find((r) => r.team_id === teamId());
  $("#event-team-info").innerHTML = t
    ? `<h3 class="spaced">${esc(t.name)}</h3>${r ? `${tag("Registered")}${teamScore(r.score)}${!e.submissions_locked ? action("Update event from saved team decks", "event-submit", true) : '<p class="help spaced">These event decks are locked. General team decks can still be changed for future tournaments.</p>'}` : e.status === "registration" && !e.submissions_locked ? `<p class="spaced">Your saved decks will be copied into this event.</p>${action("Register this team →", "event-register", true)}` : empty("Registration is closed")}<div class="actions"><a class="text-link meta" href="/teams">Edit general team decks →</a></div>`
    : empty("Choose your team", "Or create one on the Teams page.");
}
async function schedule(history = false) {
  const events = state.events.filter((e) =>
    history
      ? e.status === "complete"
      : e.status !== "complete" && e.status !== "cancelled",
  );
  main.innerHTML =
    head(
      history ? "The league archive" : "Save the date",
      history ? "Every win has a story." : "Make the next one yours.",
      history
        ? "Completed tournaments, champions, final standings, and frozen deck submissions."
        : "Upcoming league events. Default time zone: America/Phoenix.",
    ) +
    `<div class="grid">${events.map((e) => (history ? `<article class="panel event-card">${tag("Complete")}<h3>${esc(e.name)}</h3><div class="eyebrow">Champion</div><h2>${esc(e.champion || "Final standings pending")}</h2><p class="meta">${esc(dt(e.starts_at, e.timezone))}</p><a class="button" href="/events/${e.id}">Results & deck archive →</a></article>` : eventCard(e))).join("")}</div>${events.length ? "" : `<div class="panel">${empty(history ? "The archive starts with the first final." : "No events announced yet.", history ? "Completed tournaments will stay here for future seasons." : "Check back for the next league date. Your team can prepare its decks anytime.")}</div>`}`;
}
let adminData,
  selectedDraftPrices = null;
function localInZone(d, tz) {
  if (!d) return "";
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: tz,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(new Date(d))
      .map((p) => [p.type, p.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}
function fromZone(value, tz) {
  if (!value) return null;
  const target = new Date(value + "Z").getTime();
  let guess = target;
  for (let i = 0; i < 4; i++) {
    const local = localInZone(guess, tz);
    const diff = target - new Date(local + "Z").getTime();
    if (!diff) break;
    guess += diff;
  }
  if (localInZone(guess, tz) !== value)
    throw Error("This local time does not exist in the selected time zone");
  return new Date(guess).toISOString();
}

async function admin() {
  if (!session.admin) {
    main.innerHTML = `<section class="panel login"><div class="eyebrow">Organizer access</div><h1>Run the league.</h1><p>Sign in to manage events, rules, prices, and team submissions.</p><form id="login">${field("password", "Administrator password", "", "password", 'required autocomplete="current-password"')}<button type="submit" class="primary">Sign in →</button></form></section>`;
    $("#login").onsubmit = async (e) => {
      e.preventDefault();
      await busy(e.submitter, async () => {
        session = await api("/api/login", "POST", {
          password: $("#password").value,
        });
        await admin();
      });
    };
    return;
  }
  adminData = await api("/api/admin/dashboard");
  main.innerHTML =
    head(
      "League control room",
      "Keep things moving.",
      `Environment: ${adminData.environment}. All administrative changes are recorded.`,
    ) +
    `<div class="admin-layout"><aside class="admin-menu">${["overview", "events", "teams", "prices", "content", "audit"].map((x) => `<button data-admin-tab="${x}" class="${adminTab === x ? "active" : ""}">${x[0].toUpperCase() + x.slice(1)}</button>`).join("")}<button data-action="export">Export league backup ↗</button><button data-action="logout">Sign out</button></aside><section class="admin-section" id="admin-content"></section></div>`;
  await renderAdmin();
}
function eventForm(e) {
  const prefix = e ? "edit-event" : "new-event";
  const isoLocal = (d) => localInZone(d, e?.timezone || "America/Phoenix");
  return `<form id="${prefix}">${field("event-name", "Event name", e?.name || "", "text", 'required maxlength="80"')}${area("event-description", "Description", e?.description || "")}<div class="fields">${field("event-start", "Start time", isoLocal(e?.starts_at), "datetime-local", "required")}${field("event-location", "Location / Online", e?.location || "Online")}</div><div class="fields">${field("event-open", "Registration opens", isoLocal(e?.registration_opens), "datetime-local")}${field("event-close", "Registration closes", isoLocal(e?.registration_closes), "datetime-local")}</div>${field("event-lock", "Deck lock deadline", isoLocal(e?.lock_at), "datetime-local")}${field("event-timezone", "Event time zone (IANA)", e?.timezone || "America/Phoenix", "text", "required")}${e ? `<div class="field"><label for="event-status">Status</label><select id="event-status">${["scheduled", "registration", "cancelled"].map((s) => `<option value="${s}" ${s === e.status ? "selected" : ""}>${s}</option>`).join("")}</select><span class="help">Start and complete tournaments with the Challonge controls.</span></div>` : `<div class="fields"><div class="field"><label for="event-provider">Tournament provider</label><select id="event-provider"><option value="challonge">Challonge</option>${state.mockEnabled ? '<option value="mock">Deterministic test fixture</option>' : ""}</select></div><div class="field"><label for="event-format">Tournament format</label><select id="event-format">${["single elimination", "double elimination", "round robin", "swiss"].map((x) => `<option>${x}</option>`).join("")}</select></div></div>`}<button type="submit" class="primary">${e ? "Save event changes" : "Create event →"}</button></form>`;
}
function eventBody() {
  const timezone = $("#event-timezone").value;
  const when = (n) => fromZone($("#" + n).value, timezone);
  return {
    name: $("#event-name").value,
    description: $("#event-description").value,
    starts_at: when("event-start"),
    timezone,
    location: $("#event-location").value,
    registration_opens: when("event-open"),
    registration_closes: when("event-close"),
    lock_at: when("event-lock"),
  };
}
async function renderAdmin() {
  const el = $("#admin-content");
  if (adminTab === "overview") {
    el.innerHTML = `<div class="grid two"><div class="panel"><div class="eyebrow">League records</div><h2 class="spaced">${state.teams.length} teams · ${state.events.length} events</h2><p>Registration, submissions, and history are stored in PostgreSQL.</p>${action("Manage events", "admin-events", true)}</div><div class="panel"><div class="eyebrow">Challonge integration</div><h2 class="spaced">${adminData.challongeConfigured ? "Connected credentials" : "Key required"}</h2><p>Create or link a tournament from an event. Publish participants before starting. Report actual results in Challonge.</p></div></div><div class="panel spaced"><h2>Current point schedule</h2><p>${esc(state.price.name)}. Event schedules remain frozen when a new version is published.</p><h3>Operational checklist</h3><p>Create an event → open registration → review team decks → close registration → lock submissions → create/link Challonge → publish participants → start tournament.</p><p>After the final, finalize the tournament to archive its champion and standings. Create the next event and reuse existing teams.</p></div>`;
  }
  if (adminTab === "events") {
    el.innerHTML = `<div class="panel"><h2>Events</h2><label for="admin-event">Choose an event to manage</label><select id="admin-event"><option value="">Create a new event</option>${state.events.map((e) => `<option value="${e.id}">${esc(e.name)} · ${e.status}</option>`).join("")}</select><div id="event-editor" class="spaced">${eventForm()}</div></div>`;
    $("#admin-event").onchange = async (e) => {
      if (e.target.value) await adminEvent(e.target.value);
      else {
        $("#event-editor").innerHTML = eventForm();
        bindEventForm();
      }
    };
    bindEventForm();
  }
  if (adminTab === "teams") {
    el.innerHTML = `<div class="panel"><h2>Team records & recovery</h2><p>Public team details and decks can be edited on the Teams page. Archived teams retain event history.</p><label for="admin-team">Team</label><select id="admin-team">${teamOptions("", true)}</select><div id="admin-team-detail"></div><a href="/teams" class="text-link">Create or edit a team →</a></div>`;
    $("#admin-team").onchange = async (e) => {
      if (e.target.value) await adminTeam(e.target.value);
    };
  }
  if (adminTab === "prices") {
    el.innerHTML = `<div class="panel"><h2>Publish a price version</h2><p>Search the complete catalog, including zero-point cards. A draft is created from the current schedule. Publishing affects new events only.</p><form id="price-draft"><div class="field"><label for="price-edit-draft">Edit a draft or create a new version</label><select id="price-edit-draft"><option value="">New draft from current published prices</option>${adminData.prices
      .filter((p) => p.status === "draft")
      .map((p) => `<option value="${p.id}">${esc(p.name)}</option>`)
      .join(
        "",
      )}</select></div>${field("price-search", "Search complete catalog", "", "search", 'placeholder="Enter a card name"')}<div id="price-results"></div>${field("price-card", "Selected card", "", "text", "required readonly")}<div class="fields">${field("main-price", "Main-deck points", "0", "number", 'required min="0" max="10000" step="1"')}${field("command-price", "Command-zone points", "0", "number", 'required min="0" max="10000" step="1"')}</div>${field("price-name", "Version name", "", "text", "required")}<button class="primary" type="submit">Save draft →</button></form></div><div class="panel spaced"><h2>Version history</h2>${adminData.prices.map((p) => `<div class="history-item"><h3>${esc(p.name)} ${tag(p.status)}</h3><p class="meta">${esc(dt(p.created_at))}</p><div class="actions">${p.status === "draft" ? action("Publish this version", "publish-price:" + p.id, true) : ""}${action("Restore as new draft", "restore-price:" + p.id)}</div></div>`).join("")}</div>`;
    selectedDraftPrices = null;
    $("#price-edit-draft").onchange = async (e) => {
      try {
        const p = adminData.prices.find((p) => p.id === e.target.value);
        $("#price-name").value = p?.name || "";
        selectedDraftPrices = p
          ? (await api("/api/admin/prices/" + p.id)).prices
          : null;
      } catch (err) {
        notice(err.message, true);
      }
    };
    let timer;
    $("#price-search").oninput = (e) => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        try {
          const d = await api(
            "/api/points?q=" + encodeURIComponent(e.target.value),
          );
          $("#price-results").innerHTML = d.cards
            .slice(0, 8)
            .map(
              (c) =>
                `<button type="button" class="small spaced" data-pick-card="${esc(c.name)}" data-main="${c.main}" data-command="${c.command}">${esc(c.name)} · ${c.main}/${c.command}</button>`,
            )
            .join("");
        } catch (err) {
          notice(err.message, true);
        }
      }, 200);
    };
    $("#price-draft").onsubmit = async (e) => {
      e.preventDefault();
      await busy(e.submitter, async () => {
        await api(
          "/api/admin/prices" +
            ($("#price-edit-draft").value
              ? "/" + $("#price-edit-draft").value
              : ""),
          $("#price-edit-draft").value ? "PATCH" : "POST",
          {
            name: $("#price-name").value,
            changes: [
              {
                name: $("#price-card").value,
                main: Number($("#main-price").value),
                command: Number($("#command-price").value),
              },
            ],
          },
        );
        await reload();
        await admin();
        notice("Draft saved. Review and publish when ready.");
      });
    };
  }
  if (adminTab === "content") {
    const current = adminData.rules.find((r) => r.status === "published");
    el.innerHTML = `<div class="panel"><h2>Rules & format content</h2><form id="rules-draft">${field("rules-title", "Page title", current?.title || "Commander Doubles", "text", "required")}${area("rules-body", "Published format description and rules", current?.body || "", 'required rows="18"')}<div class="actions">${action("Preview changes", "rules-preview")}<button type="submit" class="primary">Save draft →</button></div><div id="rules-preview" class="spaced"></div></form></div><div class="panel spaced"><h2>Content history</h2>${adminData.rules.map((r) => `<details class="history-item"><summary>${esc(r.title)} · ${esc(r.status)} · ${esc(dt(r.created_at))}</summary><div class="rule-text spaced">${esc(r.body)}</div><div class="actions">${r.status === "draft" ? action("Publish draft", "publish-rule:" + r.id, true) : ""}${action("Restore to editor", "restore-rule:" + r.id)}</div></details>`).join("")}</div>`;
    $("#rules-draft").onsubmit = async (e) => {
      e.preventDefault();
      await busy(e.submitter, async () => {
        await api("/api/admin/rules", "POST", {
          title: $("#rules-title").value,
          body: $("#rules-body").value,
        });
        await reload();
        await admin();
        notice("Rules draft saved");
      });
    };
  }
  if (adminTab === "audit") {
    el.innerHTML = `<div class="panel"><h2>Recent audit trail</h2><p>Submission history, restoration, overrides, pricing, and tournament operations.</p>${adminData.audits.map((a) => `<div class="audit"><span class="muted">${esc(dt(a.created_at))}</span><div><strong>${esc(a.action)}</strong> · ${esc(a.actor)}<details><summary>Details</summary><pre>${esc(JSON.stringify(a.detail, null, 2))}</pre><span class="meta">${esc(a.entity_id)}</span></details></div></div>`).join("")}</div>`;
  }
}
function bindEventForm(e) {
  const f = $("#" + (e ? "edit-event" : "new-event"));
  if (!f) return;
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    await busy(ev.submitter, async () => {
      const b = eventBody();
      if (e) {
        b.status = ["running", "complete"].includes(e.status)
          ? undefined
          : $("#event-status").value;
        await api("/api/admin/events/" + e.id, "PATCH", b);
        await reload();
        await adminEvent(e.id);
      } else {
        b.provider = $("#event-provider").value;
        b.tournament_type = $("#event-format").value;
        const created = await api("/api/admin/events", "POST", b);
        await reload();
        await admin();
        $("#admin-event").value = created.id;
        await adminEvent(created.id);
      }
      notice("Event saved");
    });
  };
}
async function adminEvent(eventId) {
  const e = await api("/api/events/" + eventId);
  activeEvent = e;
  $("#event-editor").innerHTML =
    `<div class="actions">${tag(e.status)}${tag(e.submissions_locked ? "Locked" : "Unlocked", e.submissions_locked)}<a class="text-link" href="/events/${e.id}">Public event ↗</a></div><div class="divider"></div>${e.status === "complete" ? `<h2>Archived · ${esc(e.champion || e.name)}</h2><p>Results and snapshots are preserved. Corrections require an audit reason.</p>` : `<details><summary>Edit event details & registration windows</summary><div class="spaced">${eventForm(e)}</div></details>`}<div class="actions">${!["running", "complete"].includes(e.status) ? `${action("Open registration", "event-open:" + e.id)}${action("Close registration", "event-close:" + e.id)}${action(e.locked ? "Unlock submissions" : "Lock submissions", (e.locked ? "unlock:" : "lock:") + e.id)}` : ""}</div><div class="divider"></div><h3>Challonge tournament</h3><p class="meta">${esc(e.tournament_id || "No tournament linked")} · ${esc(e.tournament_state || "Not started")}<br>Last success: ${esc(dt(e.synced_at))}</p>${e.sync_error ? `<p class="danger">${esc(e.sync_error)}</p>` : ""}<div class="actions">${!e.tournament_id ? action("Create tournament", "create-tournament:" + e.id, true) : `${action("Publish registered teams", "participants:" + e.id)}${action("Force refresh", "sync:" + e.id)}${!["running", "complete"].includes(e.status) ? action("Start & lock tournament", "start:" + e.id, true) : e.status === "running" ? action("Finalize completed tournament", "finalize:" + e.id, true) : ""}`}${e.tournament_url ? `<a class="button" href="${esc(e.tournament_url)}/settings" target="_blank" rel="noopener">Manage in Challonge ↗</a>` : ""}</div>${!e.tournament_id ? `<form id="link-tournament" class="spaced">${field("tournament-id", "Or link an existing Challonge tournament ID / URL slug", "", "text", "required")}<button type="submit">Link tournament</button></form>` : ""}<div class="divider"></div><h3>Event roster</h3><div class="fields"><div class="field"><label for="add-team">Add a registered league team</label><select id="add-team">${teamOptions("")}</select></div><div class="actions">${action("Add team", "admin-register:" + e.id)}</div></div>${e.registrations.map((r) => `<div class="history-item"><h3>${esc(r.team_name)} · ${r.score?.points ?? "—"} points</h3><p class="meta">Challonge participant: ${esc(r.participant_id || "Not published")} · ${r.score?.within ? "Ready" : "Needs deck review"}</p><div class="actions">${action("Review history & restore", "reg-history:" + r.id)}${action("Override from general decks", "override:" + r.team_id)}${!r.participant_id && !e.submissions_locked ? action("Remove registration", "remove-reg:" + r.id) : ""}</div><div id="reg-${r.id}"></div></div>`).join("") || empty("No registered teams")}${
      e.provider === "mock" && e.status === "running"
        ? `<div class="divider"></div><h3>Test fixture results</h3>${e.matches
            .filter((m) => m.state === "open")
            .map(
              (m) =>
                `<div class="match">${matchCard(m)}${m.players
                  .filter(Boolean)
                  .map((p) =>
                    action(p.name + " wins", "mock-win:" + m.id + ":" + p.id),
                  )
                  .join("")}</div>`,
            )
            .join("")}`
        : ""
    }`;
  bindEventForm(e);
  if ($("#link-tournament"))
    $("#link-tournament").onsubmit = async (ev) => {
      ev.preventDefault();
      await busy(ev.submitter, async () => {
        let v = $("#tournament-id").value.trim();
        if (v.startsWith("https://challonge.com/"))
          v = new URL(v).pathname.split("/").filter(Boolean).at(-1);
        await api("/api/admin/events/" + e.id, "PATCH", { tournament_id: v });
        await reload();
        await adminEvent(e.id);
        notice("Tournament linked. Refresh to retrieve its state.");
      });
    };
}
async function adminTeam(team) {
  const t = adminData.teams.find((t) => t.id === team);
  const history = await api("/api/admin/teams/" + team + "/history");
  setTeam(team);
  $("#admin-team-detail").innerHTML =
    `<h3 class="spaced">${esc(t.name)}</h3><div class="actions"><a class="button small" href="/teams">Edit team & decks</a>${action(t.archived ? "Restore team" : "Archive team", (t.archived ? "unarchive:" : "archive:") + team)}</div><h3 class="spaced">Deck submission history</h3>${history.map((d) => `<details class="history-item"><summary>Player ${d.slot} · ${esc(dt(d.created_at))} · ${d.score.points} points · ${esc(d.actor)}</summary>${scoreMarkup(d.score)}<pre>${esc(d.deck.cards.map((c) => `${c.zone} · ${c.count} ${c.name}`).join("\n"))}</pre>${action("Restore this deck version", "restore-deck:" + d.id)}</details>`).join("") || empty("No saved decks")}`;
}
async function regHistory(regId) {
  const versions = await api("/api/admin/registrations/" + regId + "/history");
  $("#reg-" + regId).innerHTML = versions
    .map(
      (v) =>
        `<details class="history-item"><summary>${esc(dt(v.created_at))} · ${esc(v.actor)} · ${v.score?.points ?? "—"} points</summary>${v.decks.map((d) => scoreMarkup(d.score)).join("")}${field("restore-reason-" + v.id, "Correction reason", "", "text")}${action("Restore this event snapshot", "restore-reg:" + regId + ":" + v.id)}</details>`,
    )
    .join("");
}
async function busy(button, fn) {
  const text = button?.textContent;
  if (button) {
    button.disabled = true;
    button.textContent = "Working…";
  }
  try {
    await fn();
  } catch (e) {
    notice(e.message, true);
  } finally {
    if (button && button.isConnected) {
      button.disabled = false;
      button.textContent = text;
    }
  }
}
async function reload() {
  state = await api("/api/home");
}
async function refreshEventAdmin() {
  await reload();
  await adminEvent(activeEvent.id);
}
document.addEventListener("click", async (ev) => {
  const tab = ev.target.closest("[data-admin-tab]");
  if (tab) {
    adminTab = tab.dataset.adminTab;
    await admin();
    return;
  }
  const pick = ev.target.closest("[data-pick-card]");
  if (pick) {
    $("#price-card").value = pick.dataset.pickCard;
    $("#main-price").value =
      selectedDraftPrices?.[pick.dataset.pickCard]?.main ?? pick.dataset.main;
    $("#command-price").value =
      selectedDraftPrices?.[pick.dataset.pickCard]?.command ??
      pick.dataset.command;
    $("#price-results").innerHTML = "";
    return;
  }
  const button = ev.target.closest("[data-action]");
  if (!button) return;
  await busy(button, async () => {
    const [a, b, c] = button.dataset.action.split(":");
    if (a === "points-prev") {
      pointPage--;
      return loadPoints();
    }
    if (a === "points-next") {
      pointPage++;
      return loadPoints();
    }
    if (a === "event-register") {
      await api("/api/events/" + activeEvent.id + "/register", "POST", {
        team_id: teamId(),
      });
      await eventPage(activeEvent.id);
      notice("Team registered");
      return;
    }
    if (a === "event-submit") {
      await api("/api/events/" + activeEvent.id + "/submission", "POST", {
        team_id: teamId(),
      });
      await eventPage(activeEvent.id);
      notice("Event submission updated from your saved decks");
      return;
    }
    if (a === "logout") {
      await api("/api/logout", "POST", {});
      session = { admin: false };
      await admin();
      return;
    }
    if (a === "admin-events") {
      adminTab = "events";
      return admin();
    }
    if (a === "export") {
      const r = await fetch("/api/admin/export");
      if (!r.ok) throw Error("Export failed");
      const blob = await r.blob(),
        link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download =
        "commander-doubles-backup-" +
        new Date().toISOString().slice(0, 10) +
        ".json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 2000);
      notice("League backup downloaded");
      return;
    }
    if (a === "rules-preview") {
      $("#rules-preview").className = "preview spaced";
      $("#rules-preview").textContent =
        $("#rules-title").value + "\n\n" + $("#rules-body").value;
      return;
    }
    if (a === "restore-rule") {
      const r = adminData.rules.find((r) => r.id === b);
      $("#rules-title").value = r.title;
      $("#rules-body").value = r.body;
      notice("Previous rules loaded into editor. Save a new draft.");
      return;
    }
    if (a === "publish-rule") {
      await api("/api/admin/rules/" + b + "/publish", "POST", {});
      await reload();
      await admin();
      notice("Rules published");
      return;
    }
    if (a === "publish-price") {
      await api("/api/admin/prices/" + b + "/publish", "POST", {});
      await reload();
      await admin();
      notice("Price version published. Existing events retain their prices.");
      return;
    }
    if (a === "restore-price") {
      const p = adminData.prices.find((p) => p.id === b);
      await api("/api/admin/prices", "POST", {
        name: "Restore · " + p.name,
        restore_id: b,
      });
      await admin();
      notice("Previous prices copied to a new draft");
      return;
    }
    if (a === "restore-deck") {
      await api("/api/admin/decks/" + b + "/restore", "POST", {});
      await adminTeam($("#admin-team").value);
      notice("Deck version restored");
      return;
    }
    if (a === "archive" || a === "unarchive") {
      await api(
        "/api/admin/teams/" + b + (a === "unarchive" ? "/restore" : ""),
        a === "archive" ? "DELETE" : "POST",
        {},
      );
      await reload();
      await admin();
      notice(
        a === "archive" ? "Team archived; history preserved" : "Team restored",
      );
      return;
    }
    if (a === "reg-history") return regHistory(b);
    if (a === "restore-reg") {
      await api("/api/admin/registrations/" + b + "/restore", "POST", {
        version_id: c,
        reason: $("#restore-reason-" + c).value,
      });
      await refreshEventAdmin();
      notice("Event snapshot restored with an audit entry");
      return;
    }
    if (a === "override") {
      const reason = document.createElement("dialog");
      reason.innerHTML = `<h2>Correct event submission</h2><p>This replaces the event snapshot with this team's current general decks. The previous snapshot is preserved.</p><form method="dialog" id="override-form">${field("override-reason", "Required correction reason", "", "text", "required")}<div class="actions"><button type="submit" class="primary">Apply correction</button><button type="button" id="cancel-override">Cancel</button></div></form>`;
      document.body.append(reason);
      reason.showModal();
      $("#cancel-override").onclick = () => {
        reason.close();
        reason.remove();
      };
      $("#override-form").onsubmit = async (e) => {
        e.preventDefault();
        await busy(e.submitter, async () => {
          await api("/api/events/" + activeEvent.id + "/submission", "POST", {
            team_id: b,
            reason: $("#override-reason").value,
          });
          reason.close();
          reason.remove();
          await refreshEventAdmin();
          notice("Correction saved with audit trail");
        });
      };
      return;
    }
    if (a === "remove-reg") {
      await api("/api/admin/registrations/" + b, "DELETE", {});
      return refreshEventAdmin();
    }
    if (a === "admin-register") {
      await api("/api/events/" + b + "/register", "POST", {
        team_id: $("#add-team").value,
      });
      return refreshEventAdmin();
    }
    if (a === "mock-win") {
      const m = activeEvent.matches.find((m) => m.id === b);
      await api(
        "/api/admin/events/" + activeEvent.id + "/mock-result",
        "POST",
        {
          match_id: b,
          entries: m.players.map((p) => ({
            participant_id: p.id,
            score_set: p.id === c ? "1" : "0",
            advancing: p.id === c,
          })),
        },
      );
      return refreshEventAdmin();
    }
    if (a === "event-open" || a === "event-close") {
      await api("/api/admin/events/" + b, "PATCH", {
        status: a === "event-open" ? "registration" : "scheduled",
      });
      await refreshEventAdmin();
      notice(
        a === "event-open" ? "Registration opened" : "Registration closed",
      );
      return;
    }
    if (a === "lock" || a === "unlock") {
      await api("/api/admin/events/" + b + "/lock", "POST", {
        locked: a === "lock",
      });
      return refreshEventAdmin();
    }
    const ops = {
      "create-tournament": "tournament",
      participants: "participants",
      sync: "sync",
      start: "start",
      finalize: "finalize",
    };
    if (ops[a]) {
      await api("/api/admin/events/" + b + "/" + ops[a], "POST", {});
      await refreshEventAdmin();
      notice("Tournament operation completed");
    }
  });
});
async function route() {
  await reload();
  session = await api("/api/session");
  const p = location.pathname;
  document.querySelectorAll("nav a").forEach((a) => {
    if (a.getAttribute("href") === p) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (p === "/") return home();
  if (p === "/rules") {
    main.innerHTML =
      head(
        "Know the format",
        state.rules.title,
        "The published format, budget, and submission rules.",
      ) +
      `<article class="panel"><div class="rule-text">${esc(state.rules.body)}</div></article>`;
    return;
  }
  if (p === "/points") return points();
  if (p === "/teams") return teams();
  if (p === "/schedule") return schedule();
  if (p === "/history") return schedule(true);
  if (p === "/admin") return admin();
  if (p.startsWith("/events/")) return eventPage(p.split("/")[2]);
}
route().catch((e) => {
  main.innerHTML =
    head("Unable to load", "The league is taking a moment.", e.message) +
    `<a href="/" class="button">Try again</a>`;
  notice(e.message, true);
});
setInterval(async () => {
  try {
    if (document.hidden) return;
    if (location.pathname.startsWith("/events/"))
      await eventPage(location.pathname.split("/")[2]);
    else if (location.pathname === "/") {
      await reload();
      await home();
    }
  } catch {}
}, 60000);
