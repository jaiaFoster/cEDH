# Tournament data snapshots

`commanders_SIX_MONTHS.json` and `commanders_ONE_YEAR.json` — raw EDHTop16
GraphQL responses (150 commander pairings each, tournaments 32+ players)
pulled 2026-08-12 via `sim/ingestion/edhtop16.py`. These back the archetype
registry in `data/archetypes/` — see that directory's README and
`docs/assignments/SIM-001.md` "Phase 6" for the full write-up.

TopDeck.gg pulls not yet done (EDHTop16 already aggregates TopDeck.gg data
for most cEDH tournaments, so the marginal near-term value of a separate
direct TopDeck.gg pull is lower — revisit if EDHTop16's coverage of a
specific event turns out to be incomplete).
