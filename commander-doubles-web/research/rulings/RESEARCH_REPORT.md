# Commander Doubles rules-reference research — October 24, 2026

This is a curated interpretation corpus, not a new Wizards rules document, a power model or a live combo detector. The application seeds **57 verified public explanations**, **three private review drafts**, and preserves a separate **10-candidate review queue**. All 30 organizer subjects were reviewed; 28 entries cover those subjects (several related subjects share an entry), and **29 additional entries** extend the reference. Additional means beyond the requested initial subjects, not a claim that nobody previously researched those interactions.

## Evidence and method

Read the global v3 verification and JSONL, and all three batch Markdown/JSONL files. `input_audit.json` records the eight historical source hashes and 94 input research records. Historical files are unchanged. Existing conclusions were treated as candidate research, stripped of pricing recommendations, and checked against freshly downloaded Oracle and the current CR linked from Wizards’ rules landing page.

The official rules page linked **September 25, 2026** Comprehensive Rules. The fetched TXT SHA256 is `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`, matching the earlier batch-1 source hash. This is fresh retrieval of the same edition, not a claim of a later rules change. `verification_manifest.json` records fetch timestamps, URLs, byte counts and hashes. The current Scryfall Oracle download contained **38,991 identities**, updated October 24. Only 72 relevant card texts are retained in `oracle_evidence.json`; the scoring catalog and point prices remain unchanged. Rule-number presence and hashes are retained in `rule-index.json`; no full copy of the CR is republished. `verification_ledger.json` connects every published entry to rule hashes and Oracle-text hashes.

Official summary, verified worked interpretation, league house policy and unresolved research are different labels. There are **no new seeded house rules**. Publication is a local editorial decision backed by the recorded sources, not a representation that Wizards personally reviewed these examples. Deterministic validation checks IDs, reference existence, canonical card identities and source metadata; it does not prove the substantive rules reasoning. The source audit and worked examples supply that reasoning.

## Important findings and corrections

- **Commander damage:** CR903.10a says a *player* dealt 21 combat damage from one commander loses; CR810.8a makes that a team loss. Wizards’ format overview instead uses team-level language. The public reference states the unambiguous single-recipient threshold and explicitly flags the aggregation conflict. It does **not** establish that 11+10 across heads is a loss. `commander-aggregation` remains a private draft and organizer question. The existing league rules are unchanged.
- **Orim’s Chant:** its kicked clause says creatures cannot attack, not just the target player’s creatures. Friendly attacks are also stopped. Silence restricts both opposing heads; the normal Chant casting restriction targets one player.
- **Tymna:** counts opposing players dealt **combat damage**, including combat damage from an ally. It does not count ordinary life loss. Maximum distinct opponents here is two.
- **Pox versus Havoc Festival:** Pox losses are computed for each head from the same pre-loss total; at 60 an unmodified team reaches20. Friendly Bloodletter on the active team’s turn makes the enemy lose40 per head and reach−20. Havoc’s separate “that player” triggers resolve sequentially:60→30→15, not60→0.
- **Heartless Hidetsugu:** one resolution damages each head for half its shared total, rounded down:60→0,61→1. An unprotected symmetric activation can lose both teams the game.
- **Shared life is not shared gain:** split Bond/Blood does not loop. Split Heliod/Ballista does not recreate the same-controller engine. Children of Korlis does not refund an ally’s payments.
- **Cross-controller combinations that can work:** global Aluren permission enables an ally’s Acererak; Rest in Peace globally replaces cards from an ally’s Helm; Derevi can untap an ally’s sources to fund that ally’s Najeela; charged Bloodchief Ascension and allied Mindcrank can chain if cards actually enter graveyards. Each has explicit conditions. Library exile or depletion alone is not immediate defeat.
- **Aluren/Acererak arithmetic:** starting outside a dungeon, Lost Mine’s Dark Pool is reached on the third entry, then every fourth entry. Thirty Dark Pools take119 entries, including29 preceding Temple draws. This is a conditional finite kill at opposing60 life, requiring sufficient library and no relevant disruption. It is not unconditional infinity.
- **Batch2 correction:** the Chainer/K’rrik/Gray Merchant/**Viscera Seer** configuration has devotion9, not8:3+3+2+1. It gains18 before payments. A different configuration with colorless Ashnod’s Altar has devotion8; do not conflate them. The historical document is retained as-is and the correction is in the review queue.
- **Protection differs:** Teferi’s Protection freezes the shared total, while The One Ring/Glacial Chasm protect only their recipient. Teammate permanents do not phase out with another head’s Teferi’s Protection. Poison, commander combat damage and failed draws require separate treatment.
- **Shared steps:** Necropotence/Necrodominance skip the team draw step; normal draws still belong to individual heads. Sphinx sees two opposing draws; their execution is ordered under121.2d. Seedborn Muse does not grant two untaps from one opposing shared step.
- **Proliferate:** choosing both heads adds only **one** shared poison counter under701.34b.

## Expanded coverage

Additional entries cover life payments and Children refunds; split Heliod/Ballista; Gray Merchant devotion; Havoc, Hidetsugu and Repay in Kind; Serra Ascendant and Beacon; Platinum Angel; individual protection; proliferate; Earthcraft and Arcum cooperation; Equipment/Aura controller differences; Heritage versus Bruse targeting; Mindcrank; Rule of Law allowances; Seedborn and Orbs; own-library Oracle checks; Drannith versus commander ninjutsu; paired Yuriko topdecks; designated tax payers; first draws/mulligans; shared priority; turn control; Ghostly Prison; and the individual monarch designation.

Search/filter facets are Fundamentals, Shared turns, Protection, Friendly fire, Shared life, Opponent scaling, Cross-controller, and False-positive combos. Every entry carries source links, edition/date, examples, conditions, card identities and history. Companion JSONL is the reproducible research export; PostgreSQL versions preserve subsequent organizer decisions separately.

## Commander Spellbook investigation

Read the backend’s official API documentation and MIT code license. The documentation recommends bulk downloads instead of crawling all API pages, asks for attribution/linking, documents public read access and conservative 80 requests/minute with429 backoff. The backend software license does **not** establish a blanket license for redistributing all combo narratives. This feature therefore stores only minimal supporting identifiers/links and independently authored explanations. No live Spellbook request is made when players browse the site.

Five sparse API queries returned HTTP200 but no usable variants in the attempted query envelope. They are saved as **unsuccessful lookup attempts**, not evidence that combinations do not exist. The initial Node whole-string bulk parse also failed due to its string-size limit. A streaming Python/ijson pass then successfully examined **115,954** variants in the documented bulk snapshot, version 7.3.1. `spellbook_bulk_provenance.json` records the snapshot timestamp/hash and minimal matches:

| Pair | Variant | Cross-controller conclusion from our independent rules analysis |
|---|---|---|
| Najeela / Derevi | [2011-2608](https://commanderspellbook.com/combo/2011-2608/) | Conditional cooperation works; Derevi’s controller must connect; Najeela’s controller funds its own activation |
| Rest in Peace / Helm | [3002-5065](https://commanderspellbook.com/combo/3002-5065/) | Global replacement supports allied Helm; arrange a failed draw for defeat |
| Bond / Blood | [690-3966](https://commanderspellbook.com/combo/690-3966/) | Familiar ordinary combo does **not** loop when split |
| Mindcrank / Ascension | [936-1290](https://commanderspellbook.com/combo/936-1290/) | Conditional cross-controller chain; graveyard entry, counters and finite library matter |

No exact Aluren/Acererak pair matched this scan. Its public entry relies on current Oracle, the dungeon’s text and CR, rather than inventing a Spellbook match. These lookups establish database membership only, never cross-team proof or a new gameplay ban.

## Review queue and limits

`review_queue.json` has ten explicitly classified candidates: four unresolved rules/state questions, one corrected old arithmetic claim, three rejected claims, one duplicate, and one unresolved lookup gap (five unresolved in total). The three immediately editable research drafts are commander-damage aggregation, Angel’s Grace allied-damage details, and multiple Notion Thief replacements. The other items are retained for provenance rather than padded into public questions.

The public corpus is a finite, manually reviewed snapshot. New Oracle/CR editions can invalidate it. Refresh downloads in a review branch, compare hashes, revisit affected reasoning, then create reviewed revisions. The app’s publish gate enforces metadata and review status, not judge certification. Organizers must not mark unresolved interpretations verified merely to make them visible. Hosted staging was not tested in this continuation; prior access was denied. No Railway credentials or production mutations are used.
