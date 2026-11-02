# Printing-aware deck imports — November 1, 2026

This repair is based on `f6b3bdc` (development after PRs #11–#14). It does not change the accepted points CSV, league rules, budgets, existing deck versions, or frozen event submissions. It adds migration 003 and a versioned card-data bundle.

## Player workflow

Paste a public Moxfield link, including a shared link with a query/fragment, a primer URL, or a bare `moxfield.com/decks/...` address. The server saves its canonical HTTPS URL. Fetches always go to one fixed public API host; user input cannot select an arbitrary fetch host or endpoint. HTTP links are upgraded to HTTPS.

- **Inventory imported & resolved:** actual rows are resolved and evaluated. Counts, main/command prices, construction errors and budget status remain separate. An incomplete or over-budget import is not certified legal.
- **Saved, awaiting decklist:** the link is retained in PostgreSQL but has **no score**. The previous inventory remains visible and unchanged. Open More → Export in Moxfield, then paste or upload its `.txt` list directly in the same player slot.
- **Awaiting card review:** all unresolved rows appear together. Choose suggested identities, or explicitly supply an exact known name where there is no suggestion. The original text and submitted names are retained. No new deck version is created until every identity resolves.
- Invalid input is an error. It cannot overwrite a prior inventory. Cancel a pending reference to keep using the previous saved deck.

Pending imports are excluded when copying general decks into a new event submission. Registration without complete decks still works, with an unchecked budget. Existing event snapshots are never changed merely by saving a general reference. Complete the import and explicitly update the event before its lock.

## Local identity data

The active bundle has **39,287 Oracle identities, 547,500 indexed printings, and 288,467 original name strings**. Case/whitespace normalization yields 287,002 exact-name keys; punctuation/diacritic folding yields 285,383 keys. 19 Scryfall language codes are represented, including es, ja, fr, de, it, pt, ru, ko, zhs and zht. Counts include nonlegal and nontraditional objects; recognition does not make them Commander-legal.

Actual Oracle and All Cards archives dated November 1 were downloaded from Scryfall. SHA-256 hashes, download URLs, source update timestamps, derived-file hashes and counts are retained in `data/catalogs/*/manifest.json`; original API metadata is retained under `research/import-verification/`.

Resolution order:

1. Exact canonical name, including the existing explicit interchangeable-name mappings.
2. Exact Scryfall printing UUID, or set/collector metadata when supplied.
3. Exact indexed names, including localized, printed, flavor and face names.
4. Normalized names and punctuation.
5. Existing conservative bounded fuzzy matching of canonical/face names.
6. Consolidated user confirmation when there is no unique safe result.

Canonical names take precedence over another card's face alias: **Demonic Tutor remains the 15-point sorcery**, rather than the reverse face of Emeritus of Woe. A known printing is stronger evidence than a typo; if printing metadata identifies multiple identities it requires review. Unknown printing UUIDs do not silently become guessed paper cards. No mana/Oracle-text similarity is used to merge cards.

Current Scryfall records already group the tested UB/Within counterparts under one Oracle ID. `equivalent-names.json` records English printed-name relationships from those actual records, and the original explicit mappings remain intact. Singleton counts use the resolved Oracle ID. Printed/flavor aliases are distinct from an assertion that every renamed treatment introduces a new cross-ID rules equivalence. A future genuinely separate-ID equivalence requires explicit source review; do not infer it from similar text.

The index contains real ambiguity: Portuguese **Abafar** refers to both **Douse** and **Swelter**. The picker presents both; the server rejects an unrelated selection. There are 3,000 multi-identity exact-name keys, many involving tokens/faces. They are not 3,000 confirmed playable ambiguities; canonical precedence and playable-face handling apply before review.

Names and UUIDs use compact sorted binary indexes rather than hundreds of thousands of JavaScript object maps. Resolution is local. No per-card Scryfall request is needed for ordinary imports. Translated/alternate names are preserved without adding a warning for every legitimate printing variation; uncertain fuzzy matches retain warnings.

## Prices, legality and historical stability

`points.csv` and every existing published price version are unchanged. A card receives the selected published schedule's main/command value after canonical resolution. A known unlisted identity follows the existing zero-point policy. Unknown identities produce HTTP 422 review errors, never a zero-point certification. Banned/not-legal identities remain recognized but produce construction errors.

The updated bundle adds 347 identities relative to the old 38,940-card snapshot. In this particular source snapshot none of those new identities is marked Commander-legal; tests verify recognition and nonlegal handling rather than claiming to have tested newly released legal cards that do not exist in this comparison. Live Scryfall discovery remains available in Points → Advanced for controlled investigation of a missing/new printing; discovered cards absent from the local catalog remain pending, not verified free cards. Incorporation uses the reviewed bulk-refresh procedure below.

Original submitted text, old resolved inventories and stored scores remain in `deck_versions`. Current views are derived. User-confirmed rows retain their identities when re-evaluating retained source text. Event decks and scores remain frozen JSON snapshots. The append-only `deck_import_attempts` table stores references/review attempts separately from actual inventories and is included in backups/restores. Its successful/cancelled markers do not delete earlier attempts.

## Refresh and reproduce

Runtime requires only Node 22 and the bundled indexes. Refresh tooling uses Python 3.9+ standard library; no paid API or Python dependencies are required.

```sh
# New snapshot; use a new cache directory for each attempt. All Cards is large.
python3 scripts/refresh-card-catalog.py --cache /secure/cache/scryfall-YYYY-MM-DD --download
# Inspect the new manifest, legality/name changes, equivalence relationships and source hashes.
# Activate only after that review; the pointer switch is atomic.
python3 scripts/refresh-card-catalog.py --cache /secure/cache/scryfall-YYYY-MM-DD --activate
node scripts/audit-card-index.mjs /tmp/index-audit.json
npm test
```

Without `--activate`, the old pointer remains active. An existing version cannot be overwritten with different bytes. Failed downloads/builds do not replace the pointer. Workers load one immutable snapshot per process; restart/redeploy workers after activating. Retain the previous bundle/pointer for rollback. Do not refresh a serving directory in place. Build and test on a feature branch; do not run this against tournament tables.

To replay the committed snapshot, copy `research/import-verification/bulk-metadata-2026-11-01.json` to the cache as `bulk-metadata.json`, download the two exact `archives.*.url` values in the active manifest as `oracle_cards.jsonl.gz` and `all_cards.jsonl.gz`, verify their SHA-256 values, then run the script without `--download`. Current bulk inputs use JSONL gzip; the builder fails on an unsupported archive format instead of creating a partial index. A second offline build was executed and reproduced the same manifest and artifact checksums.

```sh
node scripts/build-printing-fixture.mjs --check
node scripts/verify-rulings.mjs --check
# Real disposable PostgreSQL, not an in-memory replacement:
DATABASE_URL=postgresql://USER@127.0.0.1:PORT/DB node --test tests/*.test.mjs
# Deterministic browser refusal fixture; ordinary app/database/auth/scoring are real:
APP_ENV=local node --env-file=.env tests/browser-server.mjs
BASE_URL=http://127.0.0.1:3000 ADMIN_PASSWORD=LOCAL_TEST_PASSWORD npm run test:e2e
# Actual upstream/deployed read-only probes, separate from mocked failure tests:
node scripts/verify-import-live.mjs local /tmp/local-imports.json
node scripts/verify-import-live.mjs https://commander-doubles-staging-production.up.railway.app /tmp/staging-imports.json
```

The read-only probe invokes `/api/score`; it does not create or modify production teams, tournaments or deck versions. Do not run the general lifecycle test against production.

## Before/after evidence

| Case | Before this repair | After |
|---|---|---|
| Biblioteca silvana / La abundancia de Yucahú | No indexed legitimate printing relationship | Both resolve to Sylvan Library, Oracle `92eed395-62ca-4293-882b-8565c40daab5`, **7 main-deck points** |
| 太陽の指輪 | No comprehensive Japanese index | Resolves to Sol Ring, **15 main-deck points** |
| Original 100-card incident, seven names replaced by actual Spanish/French/German/Portuguese/Japanese printings | Localized names absent from the old index | Same 100 cards, two commanders, **507 points**, construction legal, over budget |
| Original saved frog inventory | 98 cards | Still **98**, **279 points**, incomplete; no cards fabricated |
| Abafar | Unknown or unsafe to infer | Explicit Douse/Swelter confirmation |
| Moxfield refusal | Error; link not persisted | URL saved awaiting decklist; no score, fallback open, previous deck preserved |

The multilingual fixture is a deliberate printing substitution into the actual reported list, not a claim that its owner submitted that exact language mix. Its seven printing UUIDs, names and source links are saved in `tests/fixtures/printing-incident-sources.json`; `build-printing-fixture.mjs` reproduces it.

## Live Moxfield findings and deployment limit

Saved JSON evidence distinguishes direct local access from deployed Railway behavior:

- Locally, `AOcIsMkjW0Kg4V6tkON-eQ` (**frog**) returned **98 cards** on both three-deck probes. An intervening separate attempt was blocked. The other incident URL `gvyGvOx0g0uJ7ultPy-pbw` and the additional public archetype URL were blocked. The probe records actual counts; the 279-point figure above is the retained full offline incident fixture, not a fabricated live score.
- On the existing **Railway staging and production** `/api/score`, all three URLs were refused with the upstream-blocked message. **No successful direct Railway import was observed.** These are baseline deployed-code probes, not tests of a newly deployed feature.
- Current Railway CLI authentication fails with an expired OAuth refresh (`invalid_grant`). No exposed historical project token was reused. **This branch was not deployed or browser-verified on staging.** Staging rollout needs renewed account authentication and a repeat of the documented verification. Production remains unchanged.

Moxfield's existing public read endpoint is best-effort, not a published guarantee of public automation access. No supported account-independent API contract was found that removes these refusals. The implementation uses no login cookies, clearance tokens, authenticated-user impersonation, proxies, challenge solving or alternate-host evasion. A named User-Agent, fixed host, timeout, concurrent-request deduplication, bounded cache and short refusal cooldown are used. Direct-import reliability requires Moxfield-approved access; manual export remains the reliable authorized fallback. Internal arrangements used by other deck platforms were not verified and are not assumed reusable.

## Sources

- [Scryfall bulk data](https://scryfall.com/docs/api/bulk-data) and [actual bulk metadata API](https://api.scryfall.com/bulk-data). The documentation page returned 403 during this run; the public metadata and bulk archive downloads succeeded. Source/card URLs are retained; Scryfall data remains subject to its API usage conditions and Wizards' underlying Magic rights. No card image assets or market-price estimates were imported into scoring.
- [Wizards current rules landing page](https://magic.wizards.com/en/rules), retrieved November 1, links to [September 25, 2026 Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt). CR 201.3a–c governs interchangeable names; CR 201.6 covers alternate-name treatments. Name matching is a sourced interpretation of these identities, not a new league rule.
- [Spanish Sylvan Library](https://scryfall.com/card/dmr/441/es/biblioteca-silvana-(sylvan-library)), [Spanish Secret Lair](https://scryfall.com/card/sld/2058/es/biblioteca-silvana-(sylvan-library)), and [Japanese Sol Ring](https://scryfall.com/card/voc/168/ja/太陽の指輪-(sol-ring)), verified from the archived All Cards records rather than invented translations.

## Executed checks

- **122/122 Node and real PostgreSQL checks passed**, including migration idempotency, all reported legal cards, canonical collisions, localized/flavor/face names, singleton enforcement, banned cards, all-row error consolidation, whitelist validation, URL references across restarts, team/slot isolation, actual event copying, unchanged event snapshots, raw-history preservation, restoration, published-price versions, budgets, and the existing Challonge lifecycle.
- **33/33 installed-Chrome browser checks passed**, including 375-pixel mobile upload, saved pending URLs after reload, no zero score for a reference, multi-row confirmation, the real Abafar dropdown, cancellation retaining the previous deck, team-switch races, admin inspection/pricing, search, rulings and multi-event lifecycle. Browser Moxfield refusal is a labelled deterministic fixture; live evidence is separate.
- Rulings-corpus verification still passes (57 published entries, 3 drafts); it was not changed.
- Index audit validates all record ordering/reference bounds and checks 5,904 sampled name lookups plus 2,183 printing UUID lookups. It is reproducible with `scripts/audit-card-index.mjs`.
- SHA-256 comparison to `f6b3bdc` confirms unchanged accepted v3 `points.csv`, old `data/oracle.jsonl.gz` and `data/rules.txt`. Offline regeneration reproduced the active catalog byte-for-byte.

Machine-readable results are in `research/import-verification/test-results.json`. Screenshots and full local runner logs are build artifacts, not source data or live-deployment claims.
