# Egress allowlist request — SIM-001 and beyond

Compiled 2026-08-12 in response to `coverage_backlog` `ENV-0001`. This is
every domain this research instrument is realistically expected to need
across the charter's full source hierarchy (`docs/SOURCES.md`) and SIM-001's
35 phases — not just the handful that were tested and found blocked. Grouped
by what it unblocks so it's clear what's load-bearing vs. nice-to-have.

Once added, re-run the reachability check (`curl -sS "$HTTPS_PROXY/__agentproxy/status"`
plus direct `curl`/`WebFetch` probes, same as used to detect ENV-0001) to
confirm, and this repo's `docs/SOURCES.md` reachability table gets updated.

## Tier 1 — Rules authority (load-bearing)

```
magic.wizards.com
media.wizards.com
gatherer.wizards.com
mtgcommander.net
```

## Tier 2 — Executable rules engines (load-bearing for INFRA-0002)

```
github.com
raw.githubusercontent.com
objects.githubusercontent.com
codeload.githubusercontent.com
api.github.com
card-forge.github.io
jaydi85.github.io
sourceforge.net
downloads.sourceforge.net
```

## Tier 3 — Structured card & interaction data (load-bearing, highest priority)

```
api.scryfall.com
scryfall.com
svgs.scryfall.io
cards.scryfall.io
mtgjson.com
backend.commanderspellbook.com
commanderspellbook.com
```

## Tier 4 — Tournament data (load-bearing for the metagame census, Phases 6-11)

```
topdeck.gg
api.topdeck.gg
edhtop16.com
cedhtop16.com
mtgtop8.com
cedhstats.org
```

## Tier 5 — Archetype/decklist references (load-bearing for representative-list selection, Phase 9)

```
moxfield.com
api.moxfield.com
cedh-decklist-database.com
edhrec.com
archidekt.com
```

## Tier 6 — Human-behavior calibration / prior art (used for policy modeling and background research, lower urgency but genuinely useful)

```
mtgnexus.com
cedh-analytics.com
reddit.com
old.reddit.com
youtube.com
mtgsalvation.com
draftsim.com
mtggoldfish.com
starcitygames.com
```

## Explicitly not requested

Retail/marketplace domains (TCGplayer, CardKingdom, eBay, Card Kingdom,
etc.) — these showed up constantly in WebSearch results as price-tracking
noise, but nothing in the charter needs pricing data. Left off deliberately
rather than padded in for the sake of "excessive."

## After this is granted

Update `docs/SOURCES.md`'s reachability table and `coverage_backlog/BACKLOG.md`
`ENV-0001` to resolved, then proceed with the "Immediate next steps" list in
`docs/assignments/SIM-001.md` (bulk Scryfall pull, MTGJSON cross-validation,
Commander Spellbook combo pull, Forge/XMage clone + card-coverage check,
TopDeck.gg/EDHTop16 census pull).
