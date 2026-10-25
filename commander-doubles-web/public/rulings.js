// Text-only rendering: never render researched or organizer-supplied HTML.
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const label = {
  official_rules: "Official rules summary",
  verified_interpretation: "Verified worked example",
  house_rule: "League house rule",
};
const opts = (values, selected = "", all = "") =>
  (all ? `<option value="">${esc(all)}</option>` : "") +
  values
    .map(
      (v) =>
        `<option value="${esc(v)}" ${v === selected ? "selected" : ""}>${esc(v)}</option>`,
    )
    .join("");
const list = (x) =>
  x.length ? `<ul>${x.map((s) => `<li>${esc(s)}</li>`).join("")}</ul>` : "";
const safeLink = (url, text) => {
  try {
    const u = new URL(url);
    if (u.protocol !== "https:" || u.username || u.password) return esc(text);
    return `<a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">${esc(text)} ↗</a>`;
  } catch {
    return esc(text);
  }
};
function rulingCard(r) {
  return `<details class="ruling-card" id="ruling-${esc(r.id)}"><summary><span>${esc(r.title)}</span><span class="ruling-labels"><span class="tag">${esc(r.classification)}</span><span class="meta">${esc(r.category)}</span></span></summary><div class="ruling-body"><p class="meta">${esc(label[r.evidence_type])} · Verified ${esc(r.verified_on)} · Revision ${r.revision}</p><p class="ruling-answer">${esc(r.answer)}</p>${r.explanation !== r.answer ? `<p>${esc(r.explanation)}</p>` : ""}<h4>Worked example</h4><p>${esc(r.example)}</p>${r.prerequisites.length ? `<h4>Prerequisites</h4>${list(r.prerequisites)}` : ""}${r.exceptions.length ? `<h4>Exceptions & conditions</h4>${list(r.exceptions)}` : ""}${r.cards.length ? `<p class="ruling-cards">${r.cards.map((c) => safeLink(c.url, c.name)).join(" · ")}</p>` : ""}<h4>Supporting rules</h4><p class="meta">Comprehensive Rules · ${esc(r.rules_edition)} · ${r.rule_references.map(esc).join(", ")}</p><ul class="ruling-sources">${r.sources.map((s, i) => `<li>${safeLink(s, i === 0 ? "Comprehensive Rules" : new URL(s).hostname + " · source " + (i + 1))}</li>`).join("")}</ul><p class="help">This reference summarizes existing rules. Worked examples are researched interpretations, not newly issued Wizards rulings. League house rules are labeled separately.</p></div></details>`;
}
export async function renderRulings(el, api) {
  el.innerHTML = `<div class="section-head"><div><h2>2HG Rulings & Interactions</h2><p>Unique interactions, unexpected combos, and common rules questions.</p></div></div><p class="help">A source-linked reference, separate from league prices and deck legality. Expand a question for examples and important conditions.</p><form id="rulings-search" role="search"><div class="field"><label for="ruling-query">Search rulings or cards</label><input id="ruling-query" type="search" maxlength="250" placeholder="Try Yuriko, shared life, or Time Sieve"></div><div class="fields"><div class="field"><label for="ruling-category">Category</label><select id="ruling-category"><option value="">All categories</option></select></div><div class="field"><label for="ruling-classification">Interaction</label><select id="ruling-classification"><option value="">All classifications</option></select></div></div><button type="reset">Reset rulings filters</button></form><p id="ruling-count" role="status" aria-live="polite">Loading rulings…</p><div id="ruling-results" aria-busy="true"></div>`;
  const $ = (s) => el.querySelector(s);
  let timer,
    controller,
    request = 0,
    loaded = false;
  async function load() {
    const current = ++request;
    controller?.abort();
    controller = new AbortController();
    $("#ruling-results").setAttribute("aria-busy", "true");
    $("#ruling-count").textContent = "Loading rulings…";
    const p = new URLSearchParams({
      q: $("#ruling-query").value,
      category: $("#ruling-category").value,
      classification: $("#ruling-classification").value,
    });
    try {
      const data = await api("/api/rulings?" + p, "GET", undefined, {
        signal: controller.signal,
      });
      if (current !== request) return;
      if (!loaded) {
        $("#ruling-category").innerHTML = opts(
          data.categories,
          "",
          "All categories",
        );
        $("#ruling-classification").innerHTML = opts(
          data.classifications,
          "",
          "All classifications",
        );
        loaded = true;
      }
      $("#ruling-count").textContent =
        `${data.total} ruling${data.total === 1 ? "" : "s"} · Rules edition: ${data.rules_edition}`;
      $("#ruling-results").innerHTML =
        data.rulings.map(rulingCard).join("") ||
        '<div class="empty"><strong>No matching rulings</strong>Try a card name or reset the filters.</div>';
      const deep = location.hash.match(/^#ruling-([a-z0-9-]+)$/)?.[1];
      if (deep) {
        const d = document.getElementById("ruling-" + deep);
        if (d) {
          d.open = true;
          d.scrollIntoView();
        }
      }
    } catch (e) {
      if (e.name !== "AbortError" && current === request) {
        $("#ruling-count").textContent = "Could not load rulings";
        $("#ruling-results").innerHTML =
          `<p class="danger">${esc(e.message)}</p><button type="button" id="ruling-retry">Retry</button>`;
        $("#ruling-retry").onclick = load;
      }
    } finally {
      if (current === request)
        $("#ruling-results").setAttribute("aria-busy", "false");
    }
  }
  $("#rulings-search").onsubmit = (e) => {
    e.preventDefault();
    clearTimeout(timer);
    load();
  };
  $("#ruling-query").oninput = () => {
    clearTimeout(timer);
    timer = setTimeout(load, 180);
  };
  for (const s of ["#ruling-category", "#ruling-classification"])
    $(s).onchange = () => {
      clearTimeout(timer);
      load();
    };
  $("#rulings-search").onreset = () => {
    clearTimeout(timer);
    setTimeout(load, 0);
  };
  await load();
}
const field = (key, title, value = "", type = "text") =>
  `<div class="field"><label for="r-edit-${key}">${esc(title)}</label><input id="r-edit-${key}" type="${type}" value="${esc(value)}"></div>`;
const area = (key, title, value = "") =>
  `<div class="field"><label for="r-edit-${key}">${esc(title)}</label><textarea rows="3" id="r-edit-${key}">${esc(value)}</textarea></div>`;
export async function renderRulingAdmin(el, api, notice) {
  const data = await api("/api/admin/rulings");
  el.innerHTML = `<div class="panel"><h2>Rulings review & publication</h2><p>Save edits as drafts. Only explicitly published, verified versions appear publicly. Hiding preserves history; restoring creates a draft requiring review.</p><div class="field"><label for="r-admin-select">Choose a ruling</label><select id="r-admin-select"><option value="">Add a new ruling</option>${data.rulings.map((r) => `<option value="${esc(r.id)}">${esc(r.content.title)} · ${r.hidden ? "hidden" : r.published_version_id === r.latest_version_id ? "published" : "draft"} · ${esc(r.content.verification_status)}</option>`).join("")}</select></div><p><a href="/api/admin/rulings/export">Download rulings & full history (JSON) ↗</a></p><div id="r-admin-editor"></div></div>`;
  const $ = (s) => el.querySelector(s);
  async function edit(entry) {
    const x = entry?.content || {
      id: "",
      title: "",
      category: data.categories[0],
      classification: data.classifications[0],
      evidence_type: "verified_interpretation",
      verification_status: "needs_review",
      rules_edition: data.rules_edition,
      answer: "",
      explanation: "",
      example: "",
      cards: [],
      prerequisites: [],
      exceptions: [],
      sources: [],
      rule_references: [],
      verified_by: "",
      verified_on: "",
      initial_subjects: [],
    };
    const select = (key, title, values) =>
      `<div class="field"><label for="r-edit-${key}">${esc(title)}</label><select id="r-edit-${key}">${opts(values, x[key])}</select></div>`;
    $("#r-admin-editor").innerHTML =
      `<form id="ruling-editor">${field("id", "Stable ruling ID", x.id)}${field("title", "Question / title", x.title)}<div class="fields">${select("category", "Category", data.categories)}${select("classification", "Interaction classification", data.classifications)}</div><div class="fields">${select("evidence_type", "Evidence type", data.evidence_types)}${select("verification_status", "Review status", ["needs_review", "verified", "rejected"])}</div>${area("answer", "Short answer", x.answer)}${area("explanation", "Expanded explanation", x.explanation)}${area("example", "Worked example / calculation", x.example)}${area("prerequisites", "Prerequisites (one per line)", x.prerequisites.join("\n"))}${area("exceptions", "Exceptions / limitations (one per line)", x.exceptions.join("\n"))}${area("cards", "Canonical card names (one per line)", x.cards.map((c) => c.name).join("\n"))}${field("rule_references", "Comprehensive Rules references (comma separated)", x.rule_references.join(", "))}${area("sources", "Source URLs (HTTPS, one per line)", x.sources.join("\n"))}${field("rules_edition", "Source rules edition", x.rules_edition)}<p class="help">Current verified index: ${esc(data.rules_edition)}. Historical editions can be recovered as drafts; publication requires the current verified edition. Refresh the evidence index in code before adopting a new edition. Text is displayed as plain text; HTML is never executed.</p><div class="fields">${field("verified_on", "Verification date", x.verified_on, "date")}${field("verified_by", "Verified by", x.verified_by)}</div>${area("change_note", "Reason for this revision (required)", "")}<div class="actions"><button class="primary" type="submit">Save ruling draft</button>${entry ? '<button type="button" id="r-publish">Publish reviewed latest version</button><button type="button" id="r-hide">Hide published ruling</button>' : ""}</div><p class="help">Publish uses the saved latest version. Save your edits before publishing. No pricing or format rules are changed.</p></form><div id="r-history" class="spaced"></div>`;
    $("#r-edit-id").readOnly = !!entry;
    const lines = (key) =>
      $("#r-edit-" + key)
        .value.split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
    async function run(fn) {
      try {
        await fn();
        await renderRulingAdmin(el, api, notice);
        const sel = el.querySelector("#r-admin-select");
        sel.value = x.id;
        sel.dispatchEvent(new Event("change"));
      } catch (e) {
        notice(e.message, true);
      }
    }
    $("#ruling-editor").onsubmit = (e) => {
      e.preventDefault();
      run(async () => {
        const content = { ...x };
        for (const k of [
          "id",
          "title",
          "category",
          "classification",
          "evidence_type",
          "verification_status",
          "answer",
          "explanation",
          "example",
          "rules_edition",
          "verified_on",
          "verified_by",
          "change_note",
        ])
          content[k] = $("#r-edit-" + k).value;
        for (const k of ["prerequisites", "exceptions", "sources", "cards"])
          content[k] = lines(k);
        content.rule_references = $("#r-edit-rule_references")
          .value.split(",")
          .map((s) => s.trim())
          .filter(Boolean);
        x.id = content.id;
        await api(
          "/api/admin/rulings" + (entry ? "/" + entry.id + "/drafts" : ""),
          "POST",
          { content, base_version_id: entry?.latest_version_id },
        );
        notice("Ruling draft saved. Public version unchanged.");
      });
    };
    if (entry) {
      $("#r-publish").onclick = () =>
        run(async () => {
          await api("/api/admin/rulings/" + entry.id + "/publish", "POST", {
            version_id: entry.latest_version_id,
          });
          notice("Verified ruling published.");
        });
      $("#r-hide").onclick = () =>
        run(async () => {
          await api("/api/admin/rulings/" + entry.id + "/hide", "POST", {
            reason: $("#r-edit-change_note").value,
          });
          notice("Ruling hidden; history preserved.");
        });
      const history = await api("/api/admin/rulings/" + entry.id + "/history");
      if (!el.isConnected || $("#r-admin-select").value !== entry.id) return;
      $("#r-history").innerHTML =
        "<h3>Version history</h3>" +
        history
          .map(
            (v) =>
              `<details class="history-item"><summary>Revision ${v.revision} · ${esc(v.content.title)} · ${entry.published_version_id === v.id ? "public version" : "saved version"}</summary><p>${esc(v.change_note)}</p><p>${esc(v.content.answer)}</p><p class="meta">${esc(v.created_at)} · ${esc(v.actor)}</p><button type="button" data-ruling-restore="${esc(v.id)}">Restore revision ${v.revision} as review draft</button></details>`,
          )
          .join("");
      for (const b of el.querySelectorAll("[data-ruling-restore]"))
        b.onclick = () =>
          run(async () => {
            await api("/api/admin/rulings/" + entry.id + "/restore", "POST", {
              version_id: b.dataset.rulingRestore,
              reason: $("#r-edit-change_note").value,
            });
            notice(
              "Historical content restored as a draft requiring fresh verification.",
            );
          });
    }
  }
  $("#r-admin-select").onchange = () =>
    edit(data.rulings.find((r) => r.id === $("#r-admin-select").value)).catch(
      (e) => notice(e.message, true),
    );
  await edit();
}
