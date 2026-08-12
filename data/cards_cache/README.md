# Card cache

Empty. Populated by `sim/ingestion/scryfall.py` (cross-validated against
MTGJSON) once this environment or an out-of-band process can reach those
sources — see `coverage_backlog/BACKLOG.md` `ENV-0001`. One subdirectory per
`oracle-<YYYY-MM-DD>` pull, per `docs/VERSIONING.md`; files conform to
`data/schemas/card.schema.json`.
