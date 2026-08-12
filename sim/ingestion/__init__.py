"""Card/ruling/tournament data ingestion adapters.

Not implemented yet. Planned one module per source:
  - scryfall.py      (Tier 3 - Oracle text, characteristics, legalities, rulings)
  - mtgjson.py        (Tier 3 - cross-validation against scryfall.py)
  - spellbook.py       (Tier 3 - Commander Spellbook combo/interaction seed data)
  - topdeck_gg.py       (Tier 4 - tournament events/standings/decklists)
  - edhtop16.py          (Tier 4 - tournament aggregation, prevalence, seats)

Each adapter should be bulk-download-oriented (not per-item live calls) so
pulls are reproducible and cheap to re-run, writing timestamped,
source-version-stamped output into data/cards_cache/,
data/tournament_snapshots/, and interactions/candidate/ per
docs/VERSIONING.md.

Blocked on: this execution environment's outbound network egress, which is
currently blocked to every one of these hosts (coverage_backlog ENV-0001,
docs/SOURCES.md). Do not stub in fake/sample data to work around this -
per charter, "current simulation fidelity is insufficient" is the correct
statement until real access exists.
"""
