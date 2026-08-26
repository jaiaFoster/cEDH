# TopDeck.gg tournament snapshots

Tournament data in this directory is provided by [TopDeck.gg](https://topdeck.gg).

`raw/<TID>/<sha256>.json.gz` contains immutable, deterministically compressed
API responses. `normalized/<TID>.json` contains the current readable event
record, including standings, commander hints, decklist coverage, and pod data.
`manifest.json` maps each tournament ID to its current raw and normalized
artifacts.

The API key is read only from the `TOPDECK_API_KEY` environment variable. It
must be stored as a GitHub Actions secret and must never be committed.

The scheduled workflow checks the previous seven days every six hours. Because
snapshots are content-addressed, identical completed-event responses create no
new files or commits.
