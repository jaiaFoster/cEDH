# Winning & Losing FAQ and official rules access

The Rules page starts with **Official Rules & Sources**, above unchanged league content. Its shortcut opens **Winning & Losing in Two-Headed Giant**, with the organizer’s exact requested subtitle and six groups. All 32 supplied research topics have published coverage; related questions reuse **27 maintained answers**, rather than creating a duplicate entry for each question. The complete local reference has **84 verified seed identities and the same 3 private drafts**.

The initial PR draft was prepared before the original checklist was supplied. This revision follows the actual handoff. [QUESTIONS.md](QUESTIONS.md) maps every required topic to its stable database identity. The feature adds 27 distinct new entries overall, reuses 12 original entries in its source audit, and supplies reviewed version updates for five existing entries. Twelve of the new entries provide additional timing/protection/loop questions in the general reference; they are not added as duplicate cards in the focused 32-topic collection.

## Source verification

On November 2, 2026, Wizards’ [permanent Rules page](https://magic.wizards.com/en/rules) still linked to the **September 25, 2026** Comprehensive Rules. The permanent page is the primary link. PDF/TXT downloads carry their effective date; the official 2HG overview is linked with a reminder to use its Commander subsection.

`source-verification.json` records successful HTTP responses, retrieval times, document hashes and **63 referenced rule hashes**. `oracle-evidence.json` contains **28 selected current Oracle records**, retrieved in one Scryfall collection request and checked against local Oracle identities. Downloaded CR text is used only in memory for research. **No full rulebook mirror or extended rulebook excerpts are republished.** All answers and calculations are original editorial explanations, labeled as official-rules summaries or verified worked examples rather than newly issued Wizards rulings.

Each answer displays its CR identifiers, rules edition, verification date, examples, exceptions and external source actions. Links open separately with `noopener noreferrer`, preserving the current FAQ. TXT does not support section anchors; the interface instructs players to use Find. A compact index highlights CR 104, 119, 121, 704, 805, 810 and 903.

## Coverage and interpretation checks

- Shared wins/losses, concession and simultaneous team losses: CR 810.8a–b, 104.4a and 104.4d. Restrictions on winning/losing must be applied before deciding the outcome.
- Milling does not itself cause an empty-library loss. A later unreplaced failed draw causes the state-based loss: CR 104.3c, 121.4, 704.5b and 810.8a. The requested 30-card/70-card example is included. Brain Freeze followed by Blue Sun’s Zenith must target the same opponent to produce this line.
- Helm plus Rest in Peace can operate across controllers; its replacement exiles the library, and a subsequent failed draw or another loss condition is still needed. X cannot be zero under current Oracle text.
- Commander combat damage is separate for each commander. The settled same-commander/same-recipient 21-damage case is public. **The split-head aggregation discrepancy remains unresolved and private:** CR 903.10a describes a recipient player, while the Wizards overview uses team wording. No claim is made that 11 to one head plus 10 to the other definitively combines or does not combine. The existing private `commander-aggregation` draft and original caveat are preserved.
- Fifteen poison is shared. Prologue to Phyresis gives each opposing player one counter: 13 + 1 + 1 = 15. Infect changes a damage result; toxic adds its value following combat damage to a player. Proliferate adds only one poison counter to an already-poisoned team, even if both heads are selected.
- Oracle uses its ability controller’s library/devotion. Laboratory Maniac and Jace’s static ability replace only their own controller’s empty-library draw. Successful individual wins win for both teammates.
- Test of Endurance needs 50 shared life and Felidar Sovereign needs 40, at upkeep triggering and resolution. Removing a source after its ability triggers does not itself counter that ability.
- Approach must resolve after being cast from hand, with a previous cast of another spell of that name by that player; the previous spell need not have resolved or come from hand. A teammate’s cast does not count. Maze’s End checks the ability controller’s Gates, not pooled teammate lands.
- Door to Nothingness can eliminate a team by making one opponent lose. Sorin from 60 gives 60 − 50 = 10. Pox at 60 makes each head lose 20, leaving an unmodified team at 20. Each-opponent loss of 3 reduces the opposing shared pool by 6. Reservoir’s unmodified 50 damage leaves a team starting at 60 alive at 10.
- Platinum Angel’s two clauses keep its whole team from losing and the opposing team from winning, but do not restore resources or prevent concession. The One Ring and Glacial Chasm protect only their relevant controller; Teferi’s Protection has distinct shared-life and individual-permanent/protection effects.

Angel’s Grace is discussed without publishing the previous unresolved teammate-damage calculation as established arithmetic. No prices, budgets, bans, early-turn restrictions or combo legality policies are introduced.

## Data and preservation

- `data/rulings/winning-losing-topics.json`: 32-topic coverage, six groups, stable ruling references and curated natural-language search aliases. It is an index into existing ruling records, not a second content database.
- `research/winning-losing/faq-input.json`: new original summaries and canonical card names.
- `research/winning-losing/update-input.json`: five reviewed improvements to existing entries: `cant-lose-team`, `oracle-own-library`, `rip-helm`, `life-threshold-wins` and `reservoir-fifty`.
- `data/rulings/winning-losing.json` / `winning-losing-updates.json`: generated, identity-enriched seeds/updates.
- `data/rulings/official-sources.json`: official URLs, edition, checked date and priority sections.
- `public-export.jsonl` / `verification-ledger.json`: 39 audited new/reused entries and source hashes. Original verification dates remain distinct from the current source recheck date.
- `preserved-source-checksums.json`: unchanged originals, historical exports, v3 prices and league rules versus development commit `5e6a78f`.

The original 57-entry seed, its research export/ledger and the three private drafts are unchanged. Existing PostgreSQL tables, protected editor, immutable revisions, review/publish/hide/restore controls and backups are reused. An absent new ID is inserted once. A reviewed update appends revision 2 **only if** the original seed is still public/unhidden, the sole version, authored by the research seeder and has its original seed hash. Any organizer edit, draft, hide or restore blocks that automatic update. Existing revision 1 is retained. Repeated migrations do not generate further revisions.

Tests simulate the pre-upgrade state, an organizer draft, hidden entries and untouched seeds. They check that only eligible seeds receive a new version, originals remain intact, reruns are idempotent and published prices/rules do not change. Existing full admin/history/backup, team, deck and event suites remain included.

For corrections use **Admin → Rulings → Save draft → Publish reviewed latest version**. A future new seed correction does not silently replace an organizer version. New custom rulings remain searchable through All rulings and their category; the 32-topic curated collection is a versioned checklist in code.

## Search and browsing

Search uses local plain-text fields, card names, rule numbers and curated question aliases. Normalization handles punctuation/curly apostrophes and accent marks, with a conservative all-meaningful-word fallback. All six exact conversational queries in the handoff are exercised in Node and Chrome tests. This is deterministic lexical search, not an unrestricted semantic question-answering system.

The collection filter, six-group selector, existing category selector and classification selector intersect. Related topics map to one accordion identity, rendered once even when an answer belongs to multiple groups. All rulings/reset restores the general reference. Loading, error, retry and stale-request handling are preserved. There is no third-party API dependency during normal FAQ browsing.

## Reproduction

Node 22 and the existing dependencies suffice:

```sh
node scripts/build-winning-losing.mjs
# Research-only network refresh; fails if Wizards changes its current URLs/edition:
node scripts/verify-win-loss-sources.mjs
node scripts/verify-winning-losing.mjs
npm run test:rulings-corpus
# Real disposable PostgreSQL required:
DATABASE_URL=postgresql://USER@127.0.0.1:PORT/DB npm test
# Local fixture uses real persistence/auth/scoring, deterministic upstream import refusal:
APP_ENV=local PORT=3000 node --env-file=.env tests/browser-server.mjs
BASE_URL=http://127.0.0.1:3000 ADMIN_PASSWORD=LOCAL_TEST_PASSWORD npm run test:e2e
```

The source refresh stores hashes, not CR body text. A changed rules edition or Oracle text needs human review; hashes prove which evidence was used, not that an interpretation is correct. `QUESTIONS.md`, the export and the ledger are regenerated and checked offline.

## Verification and deployment

Executed results are recorded in `acceptance-results.json`. Local tests use Node 22, PostgreSQL 17 and actual Chrome, including mobile widths of 320 and 375 pixels. Official-link navigation has a browser popup fixture, while separate real HTTP verification checks the official URLs and current documents.

Railway authentication was checked again and fails because its OAuth refresh expired (`invalid_grant`). No historical exposed token was reused. **This feature has not been deployed or verified on hosted staging.** Production data and deployment remain unchanged; PR #16 is the review/deployment package.
