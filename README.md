# cEDH Simulation & Quantitative Research Instrument

This repository is a rules-aware quantitative research instrument for competitive
Commander (cEDH) deck development, built for a Tymna the Weaver / Thrasios,
Triton Hero creature-heavy Tree Farm × CounterSlop deck (exact list supplied
separately — see `data/decklists/`).

It is **not** a Monte Carlo script. It is a research system with six layers
(rules, interactions, archetypes, policies, simulation, validation), a source
hierarchy, validation gates, and provenance requirements. The governing charter
lives at [`docs/CHARTER.md`](docs/CHARTER.md); every other document in `docs/`
operationalizes some part of it.

## Status: Initialization

No subject decklist has been ingested yet and **no gameplay simulation has been
run**. This repository currently contains the research instrument's scaffold:
conventions, schemas, directory structure, and an infrastructure survey. See
[`docs/INFRASTRUCTURE_SURVEY.md`](docs/INFRASTRUCTURE_SURVEY.md) for what was
investigated and why, and [`docs/VALIDATION_GATES.md`](docs/VALIDATION_GATES.md)
for the gates that must pass before any result is treated as evidence.

## Layout

| Path | Purpose |
|---|---|
| `docs/` | Charter, architecture, sources, versioning, validation gates, policy framework |
| `data/decklists/` | Subject and opponent decklists (versioned) |
| `data/deck_sources/` | Automatically captured canonical source lists before Oracle/cache promotion |
| `data/cards_cache/` | Ingested Oracle/rulings data, keyed by Scryfall ID + printing |
| `data/archetypes/` | Empirical archetype registry derived from tournament data |
| `data/policies/` | Archetype policy definitions and their evidence sources |
| `data/tournament_snapshots/` | Pulled TopDeck.gg / EDHTop16 data snapshots, with pull date |
| `data/schemas/` | JSON Schemas for every artifact type this project produces |
| `interactions/verified/` | Interactions validated against rules + (where possible) an executable engine |
| `interactions/candidate/` | Unverified/candidate interactions awaiting validation |
| `rules_tests/gold_board_states/` | Hand-authored board states with known-correct legal actions (Gate 2) |
| `rules_tests/gold_games/` | Hand-reviewed full game sequences (Gate 3) |
| `rules_tests/regression/` | Permanent regression tests for every discovered rules/policy bug |
| `coverage_backlog/` | Unknown-state and missing-capability tracker |
| `sim/` | The instrument itself (rules engine interface, interactions, archetypes, policies, simulation loop, validation harness, ingestion) |
| `results/raw/` | Raw simulation output, always tagged with full provenance (see `docs/VERSIONING.md`) |
| `results/findings_packets/` | Primer-facing Findings Packets distilled from raw results |

## Before you run anything

Read, in order:
1. `docs/CHARTER.md` — the non-negotiable rules this project operates under.
2. `docs/ARCHITECTURE.md` — the six layers and how they fit together.
3. `docs/SOURCES.md` — the source hierarchy and current access status for each source.
4. `docs/VALIDATION_GATES.md` — why we are not running production simulations yet.
5. `docs/RUN_CLASSIFICATION.md` — how every executable run is classified
   synthetic vs. deck-backed, and why a gold-state test can never be
   confused with (or silently feed) empirical deck-performance statistics.

Tournament data sourced from [TopDeck.gg](https://topdeck.gg) is ingested by
`sim/ingestion/topdeck_gg.py` and retains the attribution required by TopDeck's
API terms.

## Current data status

- The subject Moxfield list is imported and refreshed automatically.
- The authenticated TopDeck.gg feed is live. GitHub Actions refreshes completed
  EDH tournament candidates every six hours and stores immutable raw snapshots
  alongside normalized event records.
- TopDeck.gg labels the format as EDH rather than cEDH. Downstream metagame reports
  must apply an explicit event-eligibility/classification layer before treating the
  candidate feed as a cEDH population.
