# Infrastructure survey (prior art)

Conducted 2026-08-12 via `WebSearch` (this environment cannot reach the
underlying sites directly — see `docs/SOURCES.md`). This is a first pass to
decide what to build on top of vs. reimplement; it is **not** a final
engineering decision, since none of these have been cloned, built, or run
against the actual subject decklist yet. Re-verify claims here once the
environment can reach the repos/APIs directly.

## Rules engines

### Forge (`Card-Forge/forge`)
- Java, open-source ("An unofficial rules engine for the world's greatest
  card game"), cross-platform (Windows/Mac/Linux/Android).
- Supports Sealed, Draft, **Commander**, Cube; single-player and online
  multiplayer.
- Many forks exist (`jacogrande/forge-multiplayer` explicitly adds
  multiplayer improvements) — worth checking whether a fork is more
  Commander/multiplayer-complete than upstream before picking a base.
- Documentation site: `card-forge.github.io/forge/`; wiki on GitHub.
- **Candidate role:** exact-line validation, gold board states, regression
  testing (Tier 2 executable engine per charter). Extensibility for adding
  missing cards is explicitly a design goal, which matters since our subject
  deck's exact card pool isn't guaranteed to be 100% implemented upstream.

### XMage (`magefree/mage`)
- Java, 10+ years active development, ~47,000 commits, ~1.8M LOC per search
  summaries (verify directly once reachable — large numbers like this are
  exactly the kind of claim that needs a real `git log` check, not a search
  snippet).
- Has a **local-server test mode for predefined conditions/combos** — this
  is a strong, close-to-direct fit for Gate 2 (gold board states) and Gate 3
  (gold games), more so than what was found for Forge.
- Card implementations are unit-tested individually; framework-level changes
  require tests. This is a good sign for trusting XMage's per-card rules
  correctness once we're pulling specific interactions from it.
- Community write-up: "Forge and XMage: The best free and open source rules
  engines for MTG" (cgomesu.com) — independent comparison worth reading in
  full once reachable, rather than relying on the search snippet.

**Working hypothesis (to be confirmed, not acted on yet):** XMage's
predefined-test-state mode may be the better fit for Gates 2–3 specifically;
Forge's broader platform/multiplayer framing may be more relevant if we ever
need full autonomous four-player games driven by an external engine rather
than our own Level 1–3 native tracker. Both should be evaluated against the
actual decklist's card pool before committing — an engine that's missing key
subject-deck cards is a non-starter regardless of its other merits.

## Structured data / combo sources

### Commander Spellbook
- Architecture: PostgreSQL + Django REST backend + React frontend, **MIT
  licensed**, backend repo `SpaceCowMedia/commander-spellbook-backend`, API
  root `backend.commanderspellbook.com`, ReDoc schema published.
- Endpoints of interest: `variants`, `features`, `cards`, `templates`,
  `variant-suggestions`, `find-my-combos`, `estimate-bracket`.
- Confirms charter's framing: this is a **seed and validation** source, not
  exhaustive — `variant-suggestions` existing as an endpoint implies even
  Spellbook treats its own graph as incomplete/crowdsourced.

### Scryfall / MTGJSON
- Scryfall: REST + bulk-data JSON dumps, the de facto standard, well
  documented at `scryfall.com/docs/api`.
- MTGJSON: not a REST API in the traditional sense — precompiled JSON/CSV/
  SQL/SQLite files at `mtgjson.com/api/v5/`, rebuilt daily. Good for
  cross-validation and for machine-readable keyword/ability classification
  work (charter's card-ingestion step 3–8), less good as a live lookup
  service.

## Tournament data

### TopDeck.gg
- Tournaments V2 API, free, documented at `topdeck.gg/docs/tournaments-v2`.
- Rate limits: ~100 req/min general, lower for bulk endpoints, 429 on excess.
- **Attribution required** — any output derived from this data must credit
  TopDeck.gg with a visible link. This needs to be carried into any
  primer/Findings Packet that cites TopDeck-derived numbers.
- Also discovered: `cedhstats.org`, which appears to be a TopDeck.gg-adjacent
  or -derived cEDH stats project — worth a closer look as either a
  cross-validation source or additional prior art, not yet classified.

### EDHTop16
- Two related-looking domains surfaced: `edhtop16.com` (site) and an API
  reference at `cedhtop16.com/api` from an older `edhtop16-legacy` GitHub
  repo's `api_docs.md`. **Do not treat these as confirmed equivalent** —
  the legacy repo name suggests the API may have moved or been rebuilt;
  confirm the live base URL before writing an ingestion adapter.
- JSON responses, MongoDB-style filters, 120 req/min, org is `EDH-Top-16` on
  GitHub (multiple repos, including the legacy one with API docs — check for
  a non-legacy successor).

## Prior art beyond the charter's explicit list

- **Project cEDH** (`richard-lam/project-cedh-research-papers`) — frames
  competitive Magic as an AI benchmark ("imperfect information, stochastic
  dynamics, symbolic rule interactions, multi-agent competition, evolving
  strategy space") and claims a **deterministic simulation framework for
  reproducible experimentation**. This is close enough to this project's own
  reproducibility goals (see `docs/VERSIONING.md`) that it should be read in
  full before this project's Layer 5 (Simulation) is designed in detail —
  either to adopt ideas from it or to explicitly document why we diverge.
- **cEDH Metagame Project** — community-run, Google-Form-based human game
  reporting, multiple iterations (v1–v3+ per MTGNexus threads). Precedent for
  a "real games, not simulated" dataset distinct from tournament results
  (tournament results are *outcomes*; this kind of project captures
  *in-game* events pilots self-report). Relevant to the charter's
  "real-game data" and Tier 6 human-behavior sections.
- **cEDH Analytics** (`cedh-analytics.com`) — reportedly cross-references
  EDHTop16 + Moxfield + Scryfall already. If still active and reachable, this
  is worth evaluating as a partial substitute or cross-check for parts of our
  own Layer 3 pipeline rather than rebuilding everything from raw EDHTop16/
  TopDeck.gg pulls.
- **Academic computational-Magic work**: "Magic: The Gathering is Turing
  Complete" (arXiv:1904.09828) is a complexity-theory result, not directly
  actionable for this project, but useful context for why Level 4 exact-line
  validation (rather than general search) is the right approach for
  deterministic combos — the charter's instinct to bound search rather than
  solve Magic generally is consistent with the literature. "AI solutions for
  drafting in Magic: The Gathering" (arXiv:2009.00655) is draft-specific and
  likely low-relevance to cEDH constructed policy work.

## Decisions NOT made yet (deliberately)

- Which rules engine (Forge, XMage, both, or a native Level 1–2 tracker only)
  is the execution substrate — deferred until the decklist can be checked
  against each engine's card coverage.
- Whether to build a from-scratch Level 1–2 structural tracker in this
  repo's own language/stack, vs. driving XMage's test mode even for
  lower-fidelity runs — deferred for the same reason, plus performance
  characteristics (Level 3 four-player Monte Carlo at Gate 6/7 scale likely
  needs something faster than launching a full JVM engine per game; TBD once
  we know real timing numbers).
- Primary implementation language/stack for `sim/` — deliberately left
  unstarted; see `sim/README.md`.

## Coverage backlog items opened from this survey

- `ENV-0001` — network egress blocked to all Tier 2–5 sources from this
  environment.
- `INFRA-0001` — EDHTop16 live API base URL unconfirmed (legacy vs. current).
- `INFRA-0002` — Forge vs. XMage vs. native tracker decision blocked on
  decklist + engine card-coverage check.
See `coverage_backlog/BACKLOG.md`.
