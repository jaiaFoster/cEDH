# Schemas

JSON Schema (2020-12) definitions for every artifact type this project
produces, per the charter's "raw-result schemas" initialization requirement.

| Schema | Backs |
|---|---|
| `card.schema.json` | `data/cards_cache/` |
| `decklist.schema.json` | `data/decklists/` |
| `interaction.schema.json` | `interactions/verified/`, `interactions/candidate/` |
| `archetype.schema.json` | `data/archetypes/` |
| `policy.schema.json` | `data/policies/` |
| `gold_board_state.schema.json` | `rules_tests/gold_board_states/` |
| `gold_game.schema.json` | `rules_tests/gold_games/` |
| `simulation_result.schema.json` | `results/raw/<run_id>/config.json` |
| `matchup_matrix.schema.json` | `results/raw/` matchup outputs |
| `coverage_backlog_entry.schema.json` | `coverage_backlog/backlog.jsonl` |

These schemas are deliberately written before any data exists, so that the
first real ingestion pass (Gate 1) has a contract to conform to rather than
inventing shapes ad hoc. Expect them to evolve once real data is ingested and
edge cases show up — when a schema changes in a breaking way, bump the
`$id` version suffix and note the change in `docs/VERSIONING.md`'s history
rather than silently mutating a schema older data already conforms to.

No schema for `results/findings_packets/*.md` — those follow the charter's
Findings Packet format directly as prose/markdown (Finding, Evidence,
Interpretation, Pilot/Deckbuilding Implication, Provenance, Confidence/
Limitation), not structured JSON, since they're meant for direct human/primer
consumption.
