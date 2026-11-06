// Local curated profiles. Price fields are supplied by the published-schedule API.
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const opts = (values, selected = "", all = "Any") =>
  `<option value="">${esc(all)}</option>` +
  values
    .map(
      (v) =>
        `<option value="${esc(v)}" ${v === selected ? "selected" : ""}>${esc(v)}</option>`,
    )
    .join("");
const list = (values) =>
  values?.length
    ? `<ul>${values.map((v) => `<li>${esc(v)}</li>`).join("")}</ul>`
    : "";
const link = (url, text) => {
  try {
    const u = new URL(url);
    return u.protocol === "https:" && !u.username && !u.password
      ? `<a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">${esc(text)} ↗</a>`
      : esc(text);
  } catch {
    return esc(text);
  }
};
const price = (n) => (n === null ? "Pending" : String(n));
function portrait(c) {
  const valid =
    c.image_url &&
    /^https:\/\/(?:cards|images)\.scryfall\.io\//.test(c.image_url);
  return `<span class="composition-portrait">${valid ? `<img src="${esc(c.image_url)}" alt="${esc(c.name)}" width="44" height="44" loading="lazy" decoding="async" referrerpolicy="no-referrer">` : ""}<span class="composition-image-fallback" ${valid ? "hidden" : ""} aria-hidden="true">◇</span></span>`;
}
function heads(cs, side) {
  return `<div class="composition-player"><span class="meta">Player ${side}</span><div class="composition-heads">${cs.map(portrait).join("")}<span class="composition-names">${cs.map((c) => `<span>${esc(c.name)}</span>`).join("")}</span></div></div>`;
}
function profile(p, open) {
  const team = p.command_zone_points.team;
  const histories = [
    ...new Set(
      p.decklists
        .map((d) => d.historical_team_points)
        .filter((n) => Number.isInteger(n)),
    ),
  ];
  return `<details class="composition-card" id="composition-${esc(p.id)}" data-composition="${esc(p.id)}" ${open ? "open" : ""}><summary aria-expanded="${open ? "true" : "false"}"><span class="composition-chevron" aria-hidden="true">⌄</span><span class="composition-commanders">${heads(p.commanders_a, "A")}${heads(p.commanders_b, "B")}</span><strong class="composition-title">${esc(p.display_name)}</strong><span class="meta">${esc(p.archetype)} · ${esc(p.research_status)}</span><span class="composition-hook">${esc(p.hook)}</span><span class="composition-tags">${p.tags
    .slice(0, 3)
    .map((t) => `<span class="tag">${esc(t)}</span>`)
    .join(
      "",
    )}</span><span class="composition-expand">Expand strategy</span></summary><div class="composition-body"><p class="meta">Mechanics verified ${esc(p.verified_on)} · Strategic strength untested · Revision ${p.revision || 1}</p><h3>Overview</h3><p>${esc(p.overview)}</p><h3>Why this works in 2HG</h3><p>${esc(p.interaction)}</p><h3>How to execute</h3><ol>${p.execution.map((s) => `<li>${esc(s)}</li>`).join("")}</ol><h3>Strengths</h3>${list(p.strengths)}<h3>Weaknesses</h3>${list(p.weaknesses)}${p.key_card_details.length ? `<h3>Key cards</h3><p>${p.key_card_details.map((c) => link(c.scryfall_url, c.name) + ` <span class="meta">(${esc(p.key_card_owners?.[c.oracle_id] || "Either")} deck)</span>`).join(" · ")}</p>` : ""}<h3>Strategy and deck construction</h3><p><strong>Player A:</strong> ${esc(p.role_a)}</p><p><strong>Player B:</strong> ${esc(p.role_b)}</p>${p.win_conditions.length ? `<h3>Win conditions and advantages</h3>${list(p.win_conditions)}` : ""}${p.counterplay.length ? `<h3>Counterplay</h3>${list(p.counterplay)}` : ""}<h3>League points</h3><p class="composition-points">Command zone: A <strong>${price(p.command_zone_points.a)}</strong> · B <strong>${price(p.command_zone_points.b)}</strong> · Combined <strong>${price(team)}</strong></p><p class="help">Published schedule: ${esc(p.price_version.name)}. Commander-only prices are not complete deck costs or proof of 120-point team compliance.${team !== null ? ` Theoretical team budget left before main decks: ${120 - team}.` : ""}</p>${
    p.decklists.length
      ? `<h3>Decklists</h3>${p.decklists.map((d) => `<p>${d.id ? `<a href="/api/compositions/${encodeURIComponent(p.id)}/decks/${encodeURIComponent(d.id)}">Download original ${esc(d.id)} text</a> · ` : ""}${link(d.source_url, "Source decklist")}<br><span class="help">${esc(d.provenance)}</span></p>`).join("")}${histories.length ? `<p>Historical candidate-v3 team total: <strong>${histories.join(", ")}</strong>. This is separate from the following recomputation.</p>` : ""}${
          p.deck_scores.length
            ? `<p>Recomputed with the selected published schedule: ${p.deck_scores.map((d) => `${esc(d.id)}: ${d.points} points · ${d.count} cards`).join("; ")}.</p><p class="${p.budget_validated ? "" : "danger"}">Team: ${p.full_team_score.points} / 120 · ${p.budget_validated ? "Supported construction and budget checks passed for these inventories." : "Historical benchmark requires reconstruction; not certified budget-compliant."}</p>${p.deck_scores
                .filter((d) => !d.legal)
                .map(
                  (d) =>
                    `<p class="help">${esc(d.id)} construction warnings: ${esc(d.errors.join("; "))}</p>`,
                )
                .join("")}`
            : ""
        }`
      : '<p class="help">Concept only. No complete 100-card inventories have been validated for this pairing.</p>'
  }<h3>Rules and evidence</h3><p>${p.rule_references.map((r) => link("https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt", "CR " + r)).join(" · ")}</p><p class="help">Rules edition: ${esc(p.rules_edition)}. Open the official TXT and use Find for a rule number; these are researched interpretations, not new Wizards rulings.</p><details><summary>Oracle evidence and sources</summary>${p.oracle_evidence.map((e) => `<p>${link(e.source_url, [...p.commanders_a, ...p.commanders_b, ...p.key_card_details].find((c) => c.oracle_id === e.oracle_id)?.name || "Card source")}</p><blockquote>${esc(e.quote)}</blockquote>`).join("")}<ul>${p.sources.map((s) => `<li>${link(s, new URL(s).hostname)}</li>`).join("")}</ul></details><h3>Research status</h3><p>${esc(p.research_status)}. ${esc(p.verification_notes)}</p><p class="help">Card data and imagery: ${link("https://scryfall.com", "Scryfall")}. Oracle snapshot ${esc(p.catalog_version)}.</p><a class="composition-permalink" href="#composition-${esc(p.id)}">Link to this composition</a></div></details>`;
}
export async function renderCompositions(el, api) {
  const filterNames = [
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
  ];
  const select = (name, label, values, def = "") =>
    `<div class="field"><label for="composition-filter-${name}">${esc(label)}</label><select id="composition-filter-${name}" name="${name}">${opts(values, def)}</select></div>`;
  el.innerHTML = `<div class="page-head"><div><div class="eyebrow">Build together</div><h1>Team Compositions</h1><p>Discover two-deck strategies built around the unique mechanics of Two-Headed Giant Commander.</p></div></div><form id="composition-search" role="search"><div class="composition-search-line"><label class="sr-only" for="composition-query">Search compositions</label><input id="composition-query" name="q" type="search" maxlength="250" placeholder="Search commanders, teams, strategies, synergies..."><button type="button" id="composition-advanced-toggle" aria-expanded="false" aria-controls="composition-advanced">Advanced</button></div><div id="composition-advanced" class="panel" hidden><div class="composition-filters"><label>Commander name<input name="commander" placeholder="Either player, including partners"></label>${select("exact", "Commander matching", ["0", "1"])}<label>Player A colors (WUBRG or C)<input name="aColors" placeholder="Any colors"></label><label>Player B colors (WUBRG or C)<input name="bColors" placeholder="Any colors"></label><label>Combined team colors (WUBRG or C)<input name="teamColors" placeholder="Any colors"></label>${select("colorMode", "Color matching", ["within", "exact"])}${select("archetype", "Archetype", [])}${select("mechanism", "2HG mechanism", [])}${select("status", "Research status", [])}${select("decks", "Decklist status", ["any", "full", "concept", "compliant", "historical"])}<label>Minimum command-zone team points<input type="number" name="min" min="0" step="1"></label><label>Maximum command-zone team points<input type="number" name="max" min="0" step="1"></label>${select("sort", "Sort", ["featured", "name", "recent", "archetype", "points_asc", "points_desc"])}</div><p class="help">Color filters apply to the Player A/B orientation shown; within means an identity contained in those colors, including colorless. Exact means the same color set. Points filter command zones only, never complete team costs.</p><div class="actions"><button type="reset">Clear all filters</button><button type="button" id="composition-refresh-prices">Load latest published prices</button></div></div></form><p id="composition-count" role="status" aria-live="polite">Loading compositions…</p><p id="composition-price-note" class="help"></p><div id="composition-results" class="composition-gallery" aria-busy="true"></div><button id="composition-more" type="button" hidden>Load more compositions</button>`;
  const form = el.querySelector("form"),
    $ = (s) => el.querySelector(s);
  const field = (n) => form.elements.namedItem(n);
  let loaded = false,
    serial = 0,
    controller,
    timer,
    rows = [],
    offset = 0,
    version = "",
    metadata,
    linked = null;
  const openIds = new Set();
  function readLocation() {
    const p = new URL(location.href).searchParams;
    for (const n of ["q", ...filterNames])
      field(n).value =
        p.get(n) ||
        { exact: "0", colorMode: "within", sort: "featured", decks: "any" }[
          n
        ] ||
        "";
    version = p.get("version") || "";
  }
  function writeLocation(push = false, hash = location.hash) {
    const u = new URL(location.href);
    u.search = "";
    for (const n of ["q", ...filterNames])
      if (field(n).value) u.searchParams.set(n, field(n).value);
    if (version) u.searchParams.set("version", version);
    u.hash = hash;
    history[push ? "pushState" : "replaceState"](
      null,
      "",
      u.pathname + u.search + u.hash,
    );
  }
  const selectedLabels = {
    exact: { 0: "Name fragment", 1: "Exact commander / recognized alias" },
    colorMode: {
      within: "Identity within selected colors",
      exact: "Exact identity",
    },
    decks: {
      any: "Any decklist status",
      full: "Full archived lists available",
      concept: "Concept only",
      compliant: "Current-budget compliant and validated",
      historical: "Historical benchmark requiring reconstruction",
    },
    sort: {
      featured: "Featured",
      name: "Alphabetical",
      recent: "Recently researched",
      archetype: "Archetype",
      points_asc: "Command-zone points: low first",
      points_desc: "Command-zone points: high first",
    },
  };
  function options(data) {
    const old = Object.fromEntries(filterNames.map((n) => [n, field(n).value]));
    for (const [n, values] of [
      ["archetype", data.archetypes],
      ["mechanism", data.mechanisms],
      ["status", data.statuses],
    ])
      field(n).innerHTML = opts(values, old[n]);
    for (const [n, labels] of Object.entries(selectedLabels))
      field(n).innerHTML = Object.entries(labels)
        .map(([v, l]) => `<option value="${v}">${l}</option>`)
        .join("");
    readLocation();
    loaded = true;
  }
  function bind() {
    for (const d of el.querySelectorAll("[data-composition]")) {
      let previous = d.open;
      d.ontoggle = () => {
        d.querySelector("summary").setAttribute(
          "aria-expanded",
          String(d.open),
        );
        if (previous === d.open) return;
        previous = d.open;
        if (d.open) {
          openIds.add(d.dataset.composition);
          if (location.hash !== "#composition-" + d.dataset.composition)
            writeLocation(true, "#composition-" + d.dataset.composition);
        } else {
          openIds.delete(d.dataset.composition);
          if (location.hash === "#composition-" + d.dataset.composition)
            writeLocation(true, "");
        }
      };
      for (const img of d.querySelectorAll("img"))
        img.onerror = () => {
          img.hidden = true;
          img.nextElementSibling.hidden = false;
        };
    }
  }
  async function load(append = false, fromHistory = false) {
    const request = ++serial;
    controller?.abort();
    controller = new AbortController();
    $("#composition-results").setAttribute("aria-busy", "true");
    $("#composition-count").textContent = "Loading compositions…";
    if (!append) offset = 0;
    const p = new URLSearchParams({
      q: field("q").value,
      offset: String(offset),
      limit: "24",
    });
    for (const n of filterNames) {
      const v = !loaded
        ? new URL(location.href).searchParams.get(n) || field(n).value
        : field(n).value;
      if (v) p.set(n, v);
    }
    if (version) p.set("version", version);
    try {
      const data = await api("/api/compositions?" + p, "GET", undefined, {
        signal: controller.signal,
      });
      if (request !== serial) return;
      metadata = data;
      if (!loaded) options(data);
      version = data.price_version.id;
      rows = append ? [...rows, ...data.compositions] : data.compositions;
      offset = rows.length;
      const deep = location.hash.match(/^#composition-([a-z0-9-]+)$/)?.[1];
      linked = null;
      if (deep) {
        openIds.add(deep);
        if (!rows.some((r) => r.id === deep)) {
          try {
            linked = await api(
              "/api/compositions/" +
                deep +
                "?version=" +
                encodeURIComponent(version),
              "GET",
              undefined,
              { signal: controller.signal },
            );
          } catch (e) {
            if (e.name === "AbortError") throw e;
          }
        }
      }
      if (request !== serial) return;
      $("#composition-results").innerHTML =
        (linked
          ? `<section class="composition-linked"><p class="help">Linked composition; shown separately from the filtered results.</p>${profile(linked, true)}</section>`
          : "") + rows.map((r) => profile(r, openIds.has(r.id))).join("") ||
        '<div class="empty"><strong>No matching compositions</strong>Try a commander name or clear the Advanced filters.</div>';
      bind();
      $("#composition-count").textContent =
        `${data.total} matching composition${data.total === 1 ? "" : "s"} · ${data.published_total} published in the library · ${rows.length} shown`;
      $("#composition-price-note").textContent =
        "Command-zone prices: " +
        data.price_version.name +
        ". Competitive strength is untested; historical lists may exceed the league budget.";
      $("#composition-more").hidden = rows.length >= data.total;
      if (!fromHistory) writeLocation();
      if (deep && !append) {
        const d = document.getElementById("composition-" + deep);
        if (d) {
          d.open = true;
          d.scrollIntoView({ block: "start" });
        }
      }
    } catch (e) {
      if (e.name !== "AbortError" && request === serial) {
        $("#composition-count").textContent = "Could not load compositions";
        $("#composition-results").innerHTML =
          `<p class="danger">${esc(e.message)}</p><button type="button" id="composition-retry">Retry</button>`;
        $("#composition-more").hidden = true;
        $("#composition-retry").onclick = () => load();
      }
    } finally {
      if (request === serial)
        $("#composition-results").setAttribute("aria-busy", "false");
    }
  }
  $("#composition-advanced-toggle").onclick = () => {
    const panel = $("#composition-advanced");
    panel.hidden = !panel.hidden;
    $("#composition-advanced-toggle").setAttribute(
      "aria-expanded",
      String(!panel.hidden),
    );
  };
  form.onsubmit = (e) => {
    e.preventDefault();
    clearTimeout(timer);
    writeLocation(false, "");
    load();
  };
  form.oninput = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      writeLocation(false, "");
      load();
    }, 180);
  };
  form.onchange = () => {
    clearTimeout(timer);
    writeLocation(false, "");
    load();
  };
  form.onreset = (e) => {
    e.preventDefault();
    clearTimeout(timer);
    for (const n of ["q", ...filterNames])
      field(n).value =
        { exact: "0", colorMode: "within", sort: "featured", decks: "any" }[
          n
        ] || "";
    version = "";
    writeLocation(false, "");
    load();
  };
  $("#composition-more").onclick = () => load(true);
  $("#composition-refresh-prices").onclick = () => {
    version = "";
    writeLocation();
    load();
  };
  window.addEventListener("popstate", () => {
    readLocation();
    load(false, true);
  });
  readLocation();
  await load();
}
export async function renderCompositionAdmin(el, api, notice) {
  const data = await api("/api/admin/compositions");
  const cards = data.cards,
    names = new Map(
      Object.values(cards).flatMap((c) =>
        [c.name, ...c.aliases].map((n) => [n.toLowerCase(), c.oracle_id]),
      ),
    );
  el.innerHTML = `<div class="panel"><h2>Composition review & publication</h2><p>Strategies are researched interpretations. Save drafts, verify mechanics, then publish explicitly. Hiding and restoring preserve history.</p><label>Choose a composition<select id="composition-admin-select"><option value="">Add a new composition</option>${data.compositions.map((c) => `<option value="${esc(c.id)}">${esc(c.content.display_name)} · ${c.hidden ? "hidden" : c.published_version_id === c.latest_version_id ? "published" : "draft"}</option>`).join("")}</select></label><div id="composition-admin-editor"></div></div>`;
  const $ = (s) => el.querySelector(s);
  async function edit(entry) {
    const x = entry?.content || {
      id: "",
      display_name: "",
      archetype: "Resource engine",
      hook: "",
      description: "",
      overview: "",
      interaction: "",
      role_a: "",
      role_b: "",
      execution: [],
      strengths: [],
      weaknesses: [],
      key_cards: [],
      tags: ["Controller-independent triggers"],
      win_conditions: [],
      counterplay: [],
      rule_references: [],
      sources: ["https://magic.wizards.com/en/rules"],
      rules_edition: data.rules_edition,
      catalog_version: Object.values(cards)[0].source_updated_at,
      verification_notes:
        "Strategy untested; verify the exact control configuration before publication.",
      verification_status: "needs_review",
      research_status: "Research candidate",
      verified_on: "",
      verified_by: "",
      featured_order: 100,
      player_a: [],
      player_b: [],
      decklists: [],
    };
    const field = (n, label, value, type = "text") =>
      `<label>${label}<input id="composition-edit-${n}" value="${esc(value)}" type="${type}"></label>`;
    const area = (n, label, value) =>
      `<label>${label}<textarea id="composition-edit-${n}" rows="3">${esc(value)}</textarea></label>`;
    const select = (n, label, values) =>
      `<label>${label}<select id="composition-edit-${n}">${values.map((v) => `<option ${x[n] === v ? "selected" : ""}>${esc(v)}</option>`).join("")}</select></label>`;
    $("#composition-admin-editor").innerHTML =
      `<form id="composition-editor">${field("id", "Stable composition ID", x.id)}${field("display_name", "Composition name", x.display_name)}${area("player_a", "Player A commanders (one canonical name per line)", x.player_a.map((id) => cards[id].name).join("\n"))}${area("player_b", "Player B commanders (one canonical name per line)", x.player_b.map((id) => cards[id].name).join("\n"))}${select("archetype", "Archetype", data.archetypes)}${field("hook", "One-line hook", x.hook)}${area("description", "Short description", x.description)}${area("overview", "Overview", x.overview)}${area("interaction", "Verified 2HG interaction", x.interaction)}${area("execution", "Execution (one step per line)", x.execution.join("\n"))}${area("strengths", "Strengths (one per line)", x.strengths.join("\n"))}${area("weaknesses", "Weaknesses (one per line)", x.weaknesses.join("\n"))}${area("role_a", "Player A role", x.role_a)}${area("role_b", "Player B role", x.role_b)}${area("key_cards", "Key cards (one name per line; optional A: or B: prefix)", x.key_cards.map((id) => (x.key_card_owners?.[id] && x.key_card_owners[id] !== "Either" ? x.key_card_owners[id] + ": " : "") + cards[id].name).join("\n"))}${area("tags", "Mechanisms (one per line)", x.tags.join("\n"))}<p class="help">Available mechanisms: ${esc(data.mechanisms.join("; "))}</p>${area("win_conditions", "Win conditions / advantages (one per line)", x.win_conditions.join("\n"))}${area("counterplay", "Counterplay (one per line)", x.counterplay.join("\n"))}${area("rule_references", "CR references (one number per line)", x.rule_references.join("\n"))}${area("sources", "HTTPS sources (one per line)", x.sources.join("\n"))}${area("verification_notes", "Verification notes", x.verification_notes)}${select("research_status", "Development status", data.statuses)}${select("verification_status", "Mechanics review status", ["needs_review", "verified", "rejected"])}${field("verified_on", "Verified date", x.verified_on, "date")}${field("verified_by", "Reviewer", x.verified_by)}${field("featured_order", "Featured order", x.featured_order, "number")}${area("change_note", "Revision reason (required)", "")}<p class="help">Commander identities stay fixed after creation. Source Oracle quotations are attached automatically from the recorded catalog; a reviewer must still check the actual interaction. Price fields are never editable here.</p><div class="actions"><button type="submit">Save composition draft</button>${entry ? '<button id="composition-publish" type="button">Publish reviewed composition</button><button id="composition-hide" type="button">Hide composition</button>' : ""}</div></form><div id="composition-history"></div>`;
    $("#composition-edit-id").readOnly = !!entry;
    for (const s of ["a", "b"])
      $("#composition-edit-player_" + s).readOnly = !!entry;
    const val = (n) => $("#composition-edit-" + n).value;
    const lines = (n) =>
      val(n)
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
    const ids = async (n) =>
      Promise.all(
        lines(n).map(async (name) => {
          if (n === "key_cards") name = name.replace(/^[AB]:\s*/i, "");
          let id = names.get(name.toLowerCase());
          if (!id) {
            const c = await api(
              "/api/admin/compositions/card?name=" + encodeURIComponent(name),
            );
            cards[c.oracle_id] = c;
            names.set(c.name.toLowerCase(), c.oracle_id);
            id = c.oracle_id;
          }
          return id;
        }),
      );
    let busy = false;
    async function run(fn) {
      if (busy) return;
      busy = true;
      const controls = [...el.querySelectorAll("input,textarea,select,button")];
      for (const c of controls) c.disabled = true;
      try {
        await fn();
        await renderCompositionAdmin(el, api, notice);
        const sel = el.querySelector("#composition-admin-select");
        sel.value = x.id;
        sel.dispatchEvent(new Event("change"));
      } catch (e) {
        notice(e.message, true);
      } finally {
        busy = false;
        for (const c of controls) if (c.isConnected) c.disabled = false;
      }
    }
    $("#composition-editor").onsubmit = (e) => {
      e.preventDefault();
      run(async () => {
        const c = { ...x };
        for (const n of [
          "id",
          "display_name",
          "archetype",
          "hook",
          "description",
          "overview",
          "interaction",
          "role_a",
          "role_b",
          "verification_notes",
          "research_status",
          "verification_status",
          "verified_on",
          "verified_by",
          "change_note",
        ])
          c[n] = val(n);
        for (const n of [
          "execution",
          "strengths",
          "weaknesses",
          "tags",
          "win_conditions",
          "counterplay",
          "rule_references",
          "sources",
        ])
          c[n] = lines(n);
        for (const n of ["player_a", "player_b", "key_cards"])
          c[n] = await ids(n);
        c.key_card_owners = Object.fromEntries(
          c.key_cards.map((id, i) => [
            id,
            lines("key_cards")
              [i].match(/^([AB]):/i)?.[1]
              ?.toUpperCase() || "Either",
          ]),
        );
        c.featured_order = Number(val("featured_order"));
        c.oracle_evidence = [...c.player_a, ...c.player_b].map((id) => ({
          oracle_id: id,
          quote: cards[id].oracle_text,
          source_url: cards[id].scryfall_url,
        }));
        x.id = c.id;
        await api(
          "/api/admin/compositions" + (entry ? "/" + entry.id + "/drafts" : ""),
          "POST",
          { content: c, base_version_id: entry?.latest_version_id },
        );
        notice("Composition draft saved. Published version unchanged.");
      });
    };
    if (entry) {
      $("#composition-publish").onclick = () =>
        run(async () => {
          await api(
            "/api/admin/compositions/" + entry.id + "/publish",
            "POST",
            { version_id: entry.latest_version_id },
          );
          notice("Reviewed composition published.");
        });
      $("#composition-hide").onclick = () =>
        run(async () => {
          await api("/api/admin/compositions/" + entry.id + "/hide", "POST", {
            reason: val("change_note"),
          });
          notice("Composition hidden; history preserved.");
        });
      const history = await api(
        "/api/admin/compositions/" + entry.id + "/history",
      );
      if (!el.isConnected || $("#composition-admin-select").value !== entry.id)
        return;
      $("#composition-history").innerHTML =
        "<h3>Version history</h3>" +
        history
          .map(
            (v) =>
              `<details><summary>Revision ${v.revision} · ${esc(v.change_note)}</summary><p>${esc(v.content.hook)}</p><button type="button" data-composition-restore="${v.id}">Restore revision ${v.revision} as review draft</button></details>`,
          )
          .join("");
      for (const button of el.querySelectorAll("[data-composition-restore]"))
        button.onclick = () =>
          run(async () => {
            await api(
              "/api/admin/compositions/" + entry.id + "/restore",
              "POST",
              {
                version_id: button.dataset.compositionRestore,
                reason: val("change_note"),
              },
            );
            notice("Composition restored as a review draft.");
          });
    }
  }
  $("#composition-admin-select").onchange = () =>
    edit(
      data.compositions.find(
        (c) => c.id === $("#composition-admin-select").value,
      ),
    ).catch((e) => notice(e.message, true));
  await edit();
}
