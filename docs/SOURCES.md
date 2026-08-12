# Sources — hierarchy, access methods, and current reachability

Per `docs/CHARTER.md`'s source hierarchy. For every source: what it's for,
how we plan to access it, and what was actually confirmed reachable **from
this execution environment**, as of 2026-08-12.

## Environment network reality (read this first)

This session's outbound egress is proxied and policy-gated. Direct testing
(`curl` from Bash, and `WebFetch`) against every external data source below
returned `EGRESS_BLOCKED` / `403 policy denial` at the proxy:

| Host | Bash curl | WebFetch |
|---|---|---|
| api.scryfall.com | 403 (connect_rejected) | EGRESS_BLOCKED |
| mtgjson.com | 403 (connect_rejected) | not retried (same proxy) |
| backend.commanderspellbook.com | 403 (connect_rejected) | not retried |
| topdeck.gg | 403 (connect_rejected) | EGRESS_BLOCKED |
| cedhtop16.com | 403 (connect_rejected) | not retried |
| edhtop16.com | 403 (connect_rejected) | not retried |

`WebSearch` **does** work (it returns third-party search snippets, not raw
API responses) and is how the infrastructure survey below was actually
researched. So: this environment can currently *learn about* these sources
through search-engine summaries, but cannot *pull structured data* from any
of them via Bash or WebFetch.

**Implication:** card ingestion, ruling ingestion, interaction-database
pulls, and tournament-data pulls cannot happen inside a session configured
like this one. Before Gate 1 (card & rule coverage) can run for real, one of
the following is needed:
1. This environment's network policy is changed to allow the specific hosts
   below (ideal — enables direct, repeatable, versioned pulls), or
2. Data is pulled out-of-band (a different environment/session with broader
   egress, or the user supplies exports) and dropped into `data/cards_cache/`,
   `data/tournament_snapshots/`, etc. as static, timestamped files that
   `sim/ingestion/` then reads.

This blocker is logged in `coverage_backlog/BACKLOG.md` as
`ENV-0001`. Re-test reachability at the start of any future session before
assuming either path — network policy is a property of the environment, not
of this repository, and may differ next session.

## Tier 1 — Rules authority

- **MTG Comprehensive Rules** (Wizards of the Coast) — primary rules truth.
- **Oracle text and official rulings** — via Scryfall's card objects (Tier 3)
  or Gatherer; Oracle wording wins over printed text.
- **Official Commander rules** — rules committee (mtgcommander.net) for
  Commander-specific rules (color identity, commander damage, commander tax,
  etc.) where they matter.

Access method: no API; text is ingested and cached locally once reachable, so
rules citations for validated interactions don't depend on live access at
simulation time.

## Tier 2 — Executable rules engines

- **Forge** (`Card-Forge/forge` on GitHub, Java, LGPL-family unofficial
  engine). Cross-platform, extensive card coverage, has Commander/multiplayer
  support. Candidate for exact-line validation (Level 4) and gold-state
  regression via its scripting/test hooks.
- **XMage** (`magefree/mage` on GitHub, Java). Long-running project (10+
  years, tens of thousands of commits), unit-test-driven card implementation,
  and — notably for us — a **local-server test mode for predefined
  conditions/combos**, which is close to a direct fit for Gate 2 (gold board
  states) and Gate 3 (gold games).

Neither has been cloned, built, or driven from this session yet (see network
reality above, plus no decklist to test against). Evaluation criteria to
apply once reachable: card coverage of the actual decklist, ease of scripting
a predefined board state, ease of extracting legal-action sets
programmatically, multiplayer/Commander fidelity, and license compatibility
with this project. Do not assume either engine's built-in AI represents
competent cEDH play — used for legality/exact-line only, per the charter.

Decision: **defer** until the decklist exists (need a real card list to
evaluate "does this engine implement our cards") and until either engine's
repo is reachable to clone.

## Tier 3 — Structured card & interaction data

- **Scryfall** (`api.scryfall.com`) — Oracle text, characteristics,
  legalities, rulings, identifiers, bulk data export. Primary card-data
  source; free, no key required, documented rate limits (~10 req/s
  recommended, bulk-data files for full-database pulls).
- **MTGJSON** (`mtgjson.com/api/v5/`) — precompiled JSON/CSV/SQLite exports,
  built daily, used as a cross-validation source against Scryfall rather than
  a primary source (per charter).
- **Commander Spellbook** (`backend.commanderspellbook.com`, Django REST API,
  MIT-licensed, endpoints include `variants`, `features`, `cards`,
  `templates`, `find-my-combos`, `estimate-bracket`) — combo/interaction seed
  and validation source. Not treated as the complete interaction graph, per
  charter — our own discovery pass (pairs/triples/higher-order groups) is
  still required.

Access method once reachable: `sim/ingestion/scryfall.py`,
`sim/ingestion/mtgjson.py`, `sim/ingestion/spellbook.py` — one adapter per
source, bulk-download-oriented (not per-card live calls) so pulls are
reproducible and cheap to re-run, each writing to `data/cards_cache/` /
`interactions/candidate/` with a pull-date and source-version stamp.

## Tier 4 — Tournament data

- **TopDeck.gg** (`topdeck.gg/docs/tournaments-v2`) — Tournaments V2 REST
  API. Free, ~100 req/min general endpoints (lower for bulk queries),
  **requires visible attribution/link-back** per their terms — any published
  artifact using this data must credit TopDeck.gg. Provides events, players,
  standings, pairings, results.
- **EDHTop16** (search results point to both `edhtop16.com` and an API
  surface referenced as `cedhtop16.com/api` — **domain needs verification
  once reachable**, do not hardcode a base URL from search-snippet inference
  alone) — tournament aggregation, commander prevalence, decklists,
  conversion stats, seat statistics, metagame summaries. JSON, MongoDB-style
  filters, 120 req/min.

Both are the primary source for the empirical archetype registry (Layer 3)
and empirical pod distributions (charter section "Empirical pod
distributions"). Access blocked in this environment currently (see above).

## Tier 5 — Archetype definition (secondary sources)

- **cEDH Decklist Database** (`cedh-decklist-database.com`) — curated
  decklists with primers (strategy, win conditions, mulligan notes),
  archetype-tagged (Turbo Combo, Midrange Combo, Stax, Control Combo, etc. —
  exact taxonomy to confirm once reachable). Strategic/archetype reference,
  **not** an exhaustive metagame representation — used to explain *why*
  tournament-observed archetypes behave as they do, not to define archetype
  prevalence.
- Recent tournament lists and multiple current lists (Tier 4) take priority
  over this for defining what's actually being played.

## Tier 6 — Human behavior calibration

Tournament gameplay footage, tournament reports, pilot writeups, detailed
primers, documented decision discussions, gameplay analysis. Not a rules
authority. Used only to calibrate the policy layer (Layer 4). No specific
sources locked in yet — to be identified per-archetype as policies are built,
prioritized by the archetypes with highest tournament prevalence per the
charter's confidence-stratification rule.

## Prior art already surveyed

See `docs/INFRASTRUCTURE_SURVEY.md` for the full write-up. Notable finds
beyond the charter's explicit list:
- **Project cEDH** (`richard-lam/project-cedh-research-papers`) — an academic
  initiative proposing cEDH as an AI benchmark, with a "deterministic
  simulation framework supporting reproducible experimentation" — worth
  reading closely before building Layer 5, since it may have already solved
  some of the reproducibility/determinism problems this charter cares about.
- **cEDH Metagame Project** (MTGNexus community threads, Google-Form-based
  game-result collection, multiple versions/iterations) — a human-data
  precedent for the "real-game data" category in the charter, distinct from
  simulation.
- **cEDH Analytics** (`cedh-analytics.com`) — cross-references EDHTop16 +
  Moxfield + Scryfall for metagame overviews; a working example of the exact
  kind of multi-source pipeline this project needs for Layer 3.
