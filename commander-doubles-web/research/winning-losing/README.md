# Winning & Losing FAQ and official rules access

The Rules page now starts with **Official Rules & Sources**, followed by unchanged published league content and the existing searchable FAQ. A top shortcut opens the **Winning & Losing** category. The new category has 32 entries; the combined seed contains **89 verified public entries and the same 3 private drafts**.

The original 32-question handoff was not available in the repository/conversation. The organizer explicitly instructed the agent to proceed after that gap was raised. [QUESTIONS.md](QUESTIONS.md) records the implemented coverage, without claiming to reproduce an unavailable document word for word.

## Source verification

On November 2, 2026, Wizards’ [permanent Rules page](https://magic.wizards.com/en/rules) still linked to the **September 25, 2026** Comprehensive Rules. Both supplied dated download URLs remain current. The permanent page is the primary website link; PDF/TXT downloads carry their effective date. The official 2HG overview is linked with a reminder to use its Commander subsection.

`source-verification.json` records actual successful HTTP requests, retrieval times, source hashes and **52 referenced rule hashes**. `oracle-evidence.json` contains 17 selected current Oracle records retrieved with one Scryfall collection request, including IDs, source URLs and text hashes. Downloaded CR text was used for research only. **No full CR text/PDF or extended rulebook excerpts were added to the public database or this research directory.** Rule references are identifiers/hashes; explanatory summaries and examples are original editorial wording.

Each published answer displays its recorded rules edition, verification date, exact CR references and an action opening the official TXT in a new tab. Since TXT section anchors are unavailable, the UI explains how to Find a rule number. Priority sections 104, 119, 121, 704, 805, 810 and 903 have a compact index. Rule numbers can also be searched directly, including `CR 104.3c`.

The FAQ remains a local reference. Normal browsing does not call Wizards, Scryfall or a combo service. External links use a new tab and `noopener noreferrer`, preserving the current search and expanded question. Official rules summaries, researched card examples and league house rules retain their distinct labels.

## Important interpretation checks

- Milling is not itself an empty-library loss. A subsequent unreplaced empty draw creates the state-based loss, which eliminates the team: CR 104.3c, 121.4, 704.5b and 810.8a.
- Drawing the last available card succeeds. An insufficient multi-card draw finishes the resolving instruction before the state-based check, unless a replacement win or another immediate ending intervenes.
- An already-failed draw is not repaired simply by refilling the library before the check. A replacement must apply at the draw, or a relevant loss-prevention effect must be operating.
- Laboratory Maniac and Oracle refer to their own ability controller’s resources, not a merged team library. A successful win nevertheless wins for the team.
- “Can’t lose the game,” “can’t lose life,” and “opponents can’t win” are different restrictions. One-shot prevented losses do not queue automatically; continuing zero-life/fifteen-poison conditions are checked again.
- Removing Test of Endurance/Felidar after an upkeep ability has triggered does not by itself counter the ability. Their intervening conditions still matter at resolution.
- Mandatory loops and optional repeatable combos differ. An unrelated removal spell need not be spent merely to stop a mandatory loop. No new combo bans, turn limits, point penalties or tournament policy were introduced.

The existing **split-recipient commander-damage discrepancy remains flagged**: CR 903.10a describes a recipient player, while the official format overview uses team wording. The new answer uses the definite same-commander/same-recipient 21-damage case and does not resolve 11-to-one-head plus 10-to-the-other. The earlier private draft and published caveat are preserved. Angel’s Grace’s teamwide can’t-lose clauses are explained without publishing the previously unresolved teammate-damage arithmetic as a settled numerical ruling.

## Data, editing and preservation

- `research/winning-losing/faq-input.json`: editable original summaries, examples, references and canonical card names.
- `data/rulings/winning-losing.json`: generated, identity-enriched new seed.
- `data/rulings/official-sources.json`: four official links, effective edition, verification date and priority sections.
- `public-export.jsonl`, `verification-ledger.json`: machine-readable curated export and per-entry provenance.
- `preserved-source-checksums.json`: byte comparisons to development commit `5e6a78f` for earlier reviewed entries/drafts/exports, v3 prices and league rules.

The existing PostgreSQL ruling tables, protected editor, publication controls, immutable versions, hiding and recovery are reused. Seeding remains insert-only. An upgrade adds the 32 absent IDs but never overwrites organizer text, a hidden entry or an existing ID. Tests recreate a pre-upgrade database with a hidden original ruling and confirm its exact rows/history remain unchanged across repeated migrations. The original 57-entry research export/ledger is intentionally not rewritten; new research has a separate directory.

For a deployed correction, use **Admin → Rulings → Save draft → Publish reviewed latest version**. Editing an existing seed file does not overwrite its already-published database entry. A later source edition requires reference review and an explicit evidence-index update, rather than silently relabeling older rulings.

## Reproduction

Node 22 and the app’s existing npm dependencies suffice.

```sh
# Rebuild only the new curated seed from editorial inputs:
node scripts/build-winning-losing.mjs
# Research-only network refresh. No DB writes and no CR mirror:
node scripts/verify-win-loss-sources.mjs
# Validate and regenerate the new ledger/export:
node scripts/verify-winning-losing.mjs
# Offline checks, including the untouched original corpus:
npm run test:rulings-corpus
# Requires real disposable PostgreSQL:
DATABASE_URL=postgresql://USER@127.0.0.1:PORT/DB npm test
# Local fixture app uses real persistence/auth/scoring, deterministic Moxfield refusal:
APP_ENV=local PORT=3000 node --env-file=.env tests/browser-server.mjs
BASE_URL=http://127.0.0.1:3000 ADMIN_PASSWORD=LOCAL_TEST_PASSWORD npm run test:e2e
```

The source-refresh command checks the current Wizards landing page. If its PDF/TXT URLs or effective edition differ, it fails for review instead of publishing claims under a silently changed edition. Review new Oracle text as well; hashes prove the records used, not the correctness of an interpretation. The source fetcher holds rulebook text only in memory and persists provenance hashes, not the document.

## Verification and deployment

Local validation uses Node 22, PostgreSQL 17 and real installed Chrome. Coverage includes all 32 entries, reference hashes, card identities, source metadata, HTTP link checks, idempotent upgrades, original-version preservation, admin authorization/draft/publication/hiding, source links opening separately, category/search combinations, failure recovery/reset, and 320/375-pixel layout. Full existing deck-import, points, administrator, rulings and tournament suites remain included. Executed counts are in `acceptance-results.json`.

Railway CLI authentication was checked and failed with an expired OAuth refresh (`invalid_grant`). No exposed historical token was reused. **This feature has not been deployed or verified on hosted staging.** Local screenshots and stubbed popup-navigation tests are not hosted evidence. The actual four official URL responses are separately retained in the source report. Production, tournament results, historical snapshots, prices, budgets, bans and league-format decisions remain unchanged. Delivery is a PR for review.
