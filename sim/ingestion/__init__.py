"""Card/ruling/tournament data ingestion adapters.

Status:
  - scryfall.py    IMPLEMENTED. Bulk collection pull + rulings, used to
                    ingest the full SIM-001 subject deck (100/100 cards) into
                    data/cards_cache/oracle-2026-08-12/. Ability classification
                    is a heuristic text-line parser, not manually reviewed -
                    see the module docstring.
  - mtgjson.py      Not implemented yet (cross-validation against scryfall.py).
  - spellbook.py    Not implemented yet (Commander Spellbook combo/interaction
                    seed data - next planned adapter, feeds SIM-0005).
  - topdeck_gg.py   Authenticated tournament/standings/decklist/pod snapshots.
  - edhtop16.py     Not implemented yet (tournament aggregation, prevalence,
                    seats - live endpoint confirmed as a GraphQL API at
                    edhtop16.com/api/graphql, see coverage_backlog INFRA-0001).

Each adapter should be bulk-download-oriented (not per-item live calls) so
pulls are reproducible and cheap to re-run, writing timestamped,
source-version-stamped output into data/cards_cache/,
data/tournament_snapshots/, and interactions/candidate/ per
docs/VERSIONING.md.

This execution environment's outbound network egress was blocked to every
one of these hosts (coverage_backlog ENV-0001) until the user updated the
environment's network policy mid-session on 2026-08-12; now open and
confirmed with real pulls - see docs/SOURCES.md.
"""
