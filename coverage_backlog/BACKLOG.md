# Coverage backlog

See `README.md` in this directory for the lifecycle and ranking method. This
file must stay in sync with `backlog.jsonl`.

## Open

| ID | Area | Summary | Impact | Opened |
|---|---|---|---|---|
| ENV-0001 | ENV | This execution environment's outbound network egress is blocked (403 at the proxy) to api.scryfall.com, mtgjson.com, backend.commanderspellbook.com, topdeck.gg, cedhtop16.com, edhtop16.com, and (retested for SIM-001) moxfield.com — confirmed via both Bash `curl` and `WebFetch`. Only `WebSearch` (search-snippet access, not raw API) works. Retested 2026-08-12 at SIM-001 kickoff; still blocked. | Blocks all of Gate 1 (card/rule coverage) and any tournament-data pull. Nothing in Tiers 2-5 can be ingested until this is resolved or data is supplied out-of-band. Currently blocking nearly all of SIM-001 phases 1-2, 6-11. | 2026-08-12 |
| INFRA-0001 | INFRA | EDHTop16's live API base URL is unconfirmed — search results reference both `edhtop16.com` and an API surface documented in an `edhtop16-legacy` GitHub repo pointing at `cedhtop16.com/api`. Not verified against a live, current source. | Blocks writing the EDHTop16 ingestion adapter with confidence; risks building against a dead/legacy endpoint. | 2026-08-12 |
| INFRA-0002 | INFRA | Forge vs. XMage vs. a native Level 1-2 tracker has not been decided. Both engines' actual coverage of the subject deck's specific cards is unknown, and neither has been cloned/built/run from this environment. | Blocks Layer 1 (rules engine interface) implementation start. | 2026-08-12 |
| SIM-0001 | RULES | SIM-001's subject decklist (98 cards + 2 commanders) is transcribed from the assignment text, not independently re-pulled from the supplied Moxfield URL (`moxfield.com` is blocked, see ENV-0001). | If the assignment's transcription has any error, or the live Moxfield list has since changed, the entire deck version `tymna-thrasios-treefarm-v1` is wrong. | 2026-08-12 |
| SIM-0002 | RULES | 75 of the 98 subject-deck cards are marked `well_known` in `data/decklists/_provisional/tymna-thrasios-treefarm-v1.json` — asserted from prior knowledge, not verified this session. Among the 23 cards that were spot-checked, roughly a quarter had a wrong detail (color, set, or cost) on first recall before verification. | The well_known set should be assumed to contain undiscovered errors, including possibly legality-relevant ones, until actually checked. | 2026-08-12 |
| SIM-0003 | RULES | Commandeer's exact printed mana cost is not yet confirmed (only the two-blue-card pitch alt-cost is confirmed via search). | Blocks precise mana-cost modeling for this card; does not block color-identity legality (already confirmed blue). | 2026-08-12 |
| SIM-0004 | SIM | Volatile Stormdrake uses the Energy ({E}) counter mechanic; no other card in the subject 98 appears to produce or spend Energy. | The rules-engine state tracker (`sim/rules_engine/`) needs explicit support for Energy as a resource type for this one card, or its ETB ability can't be modeled correctly. | 2026-08-12 |
| SIM-0005 | INTERACT | Several interaction lines named in the SIM-001 assignment's discovery seed list (Oboro Breezecaller lines, Shifting Woodland, Devoted Druid lines, Faerie Mastermind + Smothering Tithe loops) have not been checked against Commander Spellbook or an executable engine (blocked by ENV-0001). | None of these should be assumed to be real, functioning interactions until Phase 2/3 validation runs; several read as plausible but unconfirmed. | 2026-08-12 |

## Resolved

| ID | Area | Summary | Resolution | Resolved |
|---|---|---|---|---|
| DECK-0001 | RULES | No subject decklist had been supplied to this repository. | SIM-001 supplied the exact subject decklist (Tymna the Weaver / Thrasios, Triton Hero, 98 main-deck cards). Transcribed into `data/decklists/_provisional/tymna-thrasios-treefarm-v1.json`. Superseded by, and its residual risk tracked in, SIM-0001 (transcription not independently re-pulled from Moxfield). | 2026-08-12 |
