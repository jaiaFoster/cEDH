# Moxfield canonical deck sources

The Tymna/Thrasios source of truth is:

`https://moxfield.com/decks/gvyGvOx0g0uJ7ultPy-pbw`

`.github/workflows/sync-moxfield.yml` checks it every six hours and can also
be run manually. A changed gameplay list creates an immutable file under
`tymna-thrasios/history/` and updates `tymna-thrasios/current.json`. An
unchanged list creates no commit.

The importer fails closed unless it sees exactly two commanders and 98
main-deck cards. Its normalized content hash intentionally ignores printing
changes while retaining Scryfall printing IDs in the snapshot.

These files are canonical **source snapshots**, not automatically approved
simulation decklists. Promotion into `data/decklists/` must still satisfy the
Oracle/card-cache and frozen-deck requirements in `docs/VERSIONING.md` and
`sim/validation/run_classification.py`.

Moxfield does not provide a supported public API. This integration uses its
read-only public-deck JSON endpoint and will fail visibly if that endpoint or
its access policy changes.
