# Composition research and maintenance

Read [RESEARCH_REPORT.md](RESEARCH_REPORT.md) for the findings, qualifications and actual discovery counts. This directory and `data/compositions/` are the reviewed local corpus; the public website never runs the discovery algorithm.

## Reproduce

From `commander-doubles-web/`, with Node22 and Python3 (standard library only):

```sh
# Normal offline checks; no APIs or bulk downloads:
npm run test:compositions-corpus
npm run test:rulings-corpus

# Download the exact approved snapshot when recreating research artifacts.
# Use the jsonl_download_uri recorded in bulk-source.json and verify its SHA256.
# Current metadata refresh is explicit and does not approve a new source:
python3 scripts/fetch-composition-oracle.py /tmp/commander-compositions-oracle.jsonl.gz
python3 scripts/build-compositions.py /tmp/commander-compositions-oracle.jsonl.gz
python3 scripts/verify-composition-sources.py
node scripts/export-composition-benchmarks.mjs
python3 scripts/write-composition-report.py
npm run test:compositions-corpus

# Existing real PostgreSQL suite (disposable schemas):
DATABASE_URL=postgresql://USER@127.0.0.1:PORT/DB npm test
# Existing local browser fixture; credentials belong only in an ignored .env:
APP_ENV=local PORT=3000 node --env-file=.env tests/browser-server.mjs
BASE_URL=http://127.0.0.1:3000 ADMIN_PASSWORD=LOCAL_PASSWORD npm run test:e2e
```

A newer bulk timestamp is not interchangeable with the reviewed snapshot. The builder rejects a mismatched `reviewed-source.json` approval pin; review mechanics before advancing it. For exact historical reproduction download the recorded bulk URI rather than overwriting the source pin with current metadata. An expired archive is a limitation, not permission to silently substitute another catalog. The dated official TXT responses are used for hashes/research and not mirrored.

For Spellbook's optional research refresh, obtain the public URL recorded in `spellbook-selected.json` into `/tmp/commander-compositions-spellbook.json.gz`, verify its hash for exact reproduction, then run `python3 scripts/check-composition-spellbook.py`. The implementation retains selected IDs and membership only. It is not an ongoing public dependency or a blanket data-license assertion.

## Inputs and outputs

- `profiles.txt`: explicit editorial review of the38 initial and50 additional profiles; pipe-delimited fields documented in its first line. Changing a sentence requires renewed mechanics review, not a fitted synergy score.
- `review-input.json`, `review_queue.json`:14 rejected distinct pair hypotheses, seeded as unpublished admin records. `rejected-setups.json` additionally preserves two rejected configurations associated with existing pairs; these are not duplicate compositions.
- `bulk-source.json`, `reviewed-source.json`, `source-verification.json`, `spellbook-selected.json`: retrieval/provenance and publication pin.
- `commander-capability-index.json.gz`: eligible configurations, functional nominations and scope warnings. Join `metadata_reference` by Oracle ID into `data/compositions/cards.json.gz` for full text/faces, keywords, color, mana value, type, URLs and artwork.
- `generated_candidates.csv`:1,023 deduplicated functional nominations; scope matches are not verified interactions. Existing reviewed pair links are labeled.
- `candidate_table.csv`:102 reviewed pair records, including rejections; not all are public.
- `seed-audit.json`, `corrections.json`: initial coverage and exactly what required qualification.
- `data/compositions/entries.json`:88 curated profiles. `drafts.json`:14 private records. `cards.json.gz`:local card metadata, independent of prices. `decklists/`:byte-preserved18 historical100-card inventories.
- `benchmark-recomputation.json`, `research-priorities.csv`: executed bundled-v3 comparisons. These do not claim to snapshot edited hosted prices.
- `build-manifest.json`: reproducible input/output hashes checked offline by CI.
- `acceptance-results.json`: executed tests and deployment limitations.

The Node comparison exporter supports `--check`. Re-running the Python builder on the pinned input should leave all generated outputs unchanged. It does not mutate the league catalog, prices, rules, teams or events.

## Organizer workflow

Use **Admin → Compositions**. Existing commander configurations are stable identities; to change them, create another record. Enter new command zones by canonical names, including every partner or Background. A Background cannot be a standalone commander; a legendary Background creature can be. Pregame color-choice commanders require a reviewed configuration extension before publication instead of guessing colorless.

Edit text and sources, save a draft, then explicitly publish a mechanics-verified version with reviewer/date and current recorded rules references. New records default to research candidates needing review. Oracle quotations are attached from local metadata, which is evidence to review, not automatic proof of an interaction. Key-card lines accept `A: Card Name` or `B: Card Name`; an unprefixed card is an either-deck support choice, and its color identity must fit at least one complete individual command zone. Assigned cards must fit their assigned player. Additional ordinary key cards can resolve through the existing local canonical card catalog without an external API.

Hiding preserves the entry and immutable history. Restore creates a new unverified draft; it never silently republishes. The seed inserts absent identities once and never overwrites an organizer edit, hidden record or draft. Library and version rows are included in the existing protected backup export and isolated recovery tool.

All lists and prices shown are read-only information. The composition editor cannot edit prices, budgets, rules or event records. Complete archived inventories are rescored using the selected published schedule, independently for each player; a commander-only cost is never presented as a complete120-point team. Known catalog cards can be zero; an unknown league Oracle ID remains Pending.

No new100-card lists are supplied beyond the original18. Published mechanics have not been playtested and no win rates are inferred. The optional live commander-discovery UI was not added; the existing Points live Scryfall mode remains available, and local search has no ongoing external API dependency.
