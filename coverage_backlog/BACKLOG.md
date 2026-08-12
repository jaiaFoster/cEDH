# Coverage backlog

See `README.md` in this directory for the lifecycle and ranking method. This
file must stay in sync with `backlog.jsonl`.

## Open

| ID | Area | Summary | Impact | Opened |
|---|---|---|---|---|
| ENV-0001 | ENV | This execution environment's outbound network egress is blocked (403 at the proxy) to api.scryfall.com, mtgjson.com, backend.commanderspellbook.com, topdeck.gg, cedhtop16.com, edhtop16.com — confirmed via both Bash `curl` and `WebFetch`. Only `WebSearch` (search-snippet access, not raw API) works. | Blocks all of Gate 1 (card/rule coverage) and any tournament-data pull. Nothing in Tiers 2-5 can be ingested until this is resolved or data is supplied out-of-band. | 2026-08-12 |
| INFRA-0001 | INFRA | EDHTop16's live API base URL is unconfirmed — search results reference both `edhtop16.com` and an API surface documented in an `edhtop16-legacy` GitHub repo pointing at `cedhtop16.com/api`. Not verified against a live, current source. | Blocks writing the EDHTop16 ingestion adapter with confidence; risks building against a dead/legacy endpoint. | 2026-08-12 |
| INFRA-0002 | INFRA | Forge vs. XMage vs. a native Level 1-2 tracker has not been decided. Both engines' actual coverage of the subject deck's specific cards is unknown, and neither has been cloned/built/run from this environment. | Blocks Layer 1 (rules engine interface) implementation start. | 2026-08-12 |
| DECK-0001 | RULES | No subject decklist has been supplied to this repository. Charter explicitly states the exact list is separate and may change over time; nothing in the charter text itself should be treated as a current list. | Blocks all card ingestion, interaction discovery, archetype/policy work specific to the subject deck, and every gate past nothing. | 2026-08-12 |

## Resolved

_None yet._
