# Sustainable recurring data sources
As reviewed 2026-10-19. Sources with unknown automation rights are not scheduled.

| Role | Source | Refresh mechanism | Cadence / limit | Identity and changes | Rights / outage behavior |
|---|---|---|---|---|---|
| Primary identity | [Scryfall bulk](https://scryfall.com/docs/api/bulk-data) | Read bulk metadata, download changed Oracle archive | Follow current API guidance; prefer one bulk file over per-card requests | Oracle ID; bulk updated_at, SHA-256; diff relevant Oracle fields | Keep last successful snapshot; underlying card rights remain |
| Primary product metadata | [MTGJSON](https://mtgjson.com/downloads/all-decks/) | Versioned all-decks files/checksums | Set/release-driven; check metadata before download | MTGJSON UUID mapped to Oracle ID; retain source deck ID | MIT metadata; preserve third-party rights; flag gaps, do not replace with invented lists |
| Primary combo analysis | [Spellbook docs](https://spacecowmedia.github.io/commander-spellbook-backend/api.html) | Official variants.json.gz bulk, or sparse find-my-combos calls | Documentation says about 80 requests/min safe; use named User-Agent, 429 backoff | Variant ID, aliases, Oracle IDs; bulk timestamp/version and content hash | Attribution required; separate data redistribution scope unresolved; retain last version and mark stale |
| Candidate rating prior | [Published cache](https://github.com/zarzak/mtg-deck-builder) | Pin Git commit; restricted data-only pickle decoding; convert to JSON | Check on source commits or release cycle; no paid calls needed for cached records | Join current canonical name/unique first-face alias to Oracle ID; retain model, source hash, commit | MIT root license retained; no separate cache restriction found; gaps remain missing |
| Official policy | [Wizards Commander](https://magic.wizards.com/en/formats/commander) | Review official bracket, ban and Game Changer announcements | Event-driven human review; do not infer decisions from rumors | Card Oracle ID plus effective date and source URL | Factual policy reference, not open numerical ratings; freeze policy version |
| Expert reference | [Canadian Highlander points](https://canadianhighlander.ca/points-list/) | Human-reviewed versioned list | Announcement-driven | Canonical names to Oracle IDs | Sparse different-format policy; redistribution terms not established |
| Secondary validation | [TopDeck API](https://topdeck.gg/docs/tournaments-v2) | Authorized key and documented queries | Use actual API/account limits; no rate assumption made here | Tournament/player/deck IDs, Oracle mapping, revisions | Obtain access/reuse scope first; unavailable data stays unavailable |
| Secondary validation | [Playgroup](https://playgroup.gg/) | Partnership or authorized export | Not scheduled: approved raw-data access not verified | Need game, pod, pilot, deck revision, exposure and timestamp | No acquired license/API; outage cannot be replaced by marketing aggregates |
| Secondary opinion | EDHREC articles, Command Zone, EDHRECast and independent reviews | Human-reviewed factual pair/rank annotations with URL/date/criteria | New products or episodes; no automatic EDHREC queries | Frozen deck revision and reviewer/episode grouping | Do not copy whole articles or silently collapse disagreements |
| Static methods | Papers, historical code, Limited analytics | Pin publication and commit | Infrequent | DOI/arXiv/version/hash | Each code/data license checked separately |

## Scheduled architecture
1. An acquisition job downloads only authorized metadata/bulk sources, records retrieval UTC time, URL, Git SHA or upstream version, bytes and SHA-256. It validates schemas before promoting a snapshot.
2. Keep immutable source snapshots and a separate current manifest. Version the Oracle identity mapping; do not merge different cards that happen to share a face name.
3. Diff new/changed Oracle fields, missing IDs, changed ratings and revised decklists. A cache keyed by card name is not sufficient as the permanent league identity.
4. A card review queue receives new cards, changed text, outlier prices, basic/mana inconsistencies and unlicensed/missing evidence. Unrated cards stay visibly unrated; optional estimates must be labeled and globally fixed.
5. A human approves a versioned global price release and overrides with reasons. The calculator reads that immutable release. Old league rounds continue to use their original version.
6. Run coverage/additivity checks and frozen validation comparisons, then publish coverage, uncertainty and regressions. Never change coefficients automatically to chase the same review labels.
7. Service failure retains the last good snapshot and marks its age. Never overwrite evidence with empty responses, silently zero missing values, or treat unknown legality as legal.

Suggested local storage: data/raw/<source>/<version>/, an acquisition manifest, an Oracle-ID evidence table, review/override history, and separately frozen validation releases. This sprint pins downloaded source URLs to commits. The acquisition command can refresh deliberately; ordinary benchmark reproduction uses the committed snapshot and makes no network requests.

## Correlated upstreams
Scryfall edhrec_rank, EDHREC usage, Spellbook popularity and EDHREC wrappers are related evidence. TopDeck, EDHTop16 and cEDHstats may describe overlapping tournaments. AgentSamSA's repositories are one project lineage. Duplicate sources must not be treated as independent ensemble votes.

## Approval and terms boundary
An accessible endpoint, scraped library or open-source wrapper does not license the upstream database. EDHREC automation is excluded under the reviewed terms. CommanderSalt direct access was denied and was not retried through another surface. No API keys or account credentials are committed. Exact access limits not verified in this session remain unspecified.
