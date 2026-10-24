# Commander Doubles league

A persistent, mobile-friendly 2v2 Commander league application. Public browsing, persistent teams, and team editing require no accounts. PostgreSQL stores teams, versioned decks, event registrations, frozen price schedules and submissions, rules, tournament history, and the administrator audit trail. Challonge v2.1 remains the tournament engine.

## Run locally

Requires Node 22 and PostgreSQL 16 or later.

```sh
cd commander-doubles-web
npm ci
cp .env.example .env
# Set DATABASE_URL, ADMIN_PASSWORD and SESSION_SECRET in .env.
node --env-file=.env app.mjs
```

Migrations and initial v3/rules initialization run transactionally on startup, protected by a database advisory lock. `npm run migrate` also runs migrations. The app fails closed if the database or administrator credentials are missing. `/health` checks the actual database connection.

Routes: `/`, `/rules`, `/points`, `/schedule`, `/teams`, `/history`, `/events/:id`, `/admin`. Server-side admin routes are under `/api/admin`. `/api/session` returns a CSRF token only for an authenticated admin session.

## Configuration

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string; use Railway's private network in deployed services. |
| `DATABASE_SCHEMA` | Dedicated schema: `league_production`, `league_staging`, or `league_local`. Validated identifier. |
| `APP_ENV` | Visible environment label: production/staging/local. |
| `NODE_ENV` | Set `production` on Railway for secure cookies. |
| `ADMIN_PASSWORD_HASH` | Preferred administrator password: scrypt `salt:hexhash`. |
| `ADMIN_PASSWORD` | Alternative bootstrap password, hashed in memory with scrypt. Never stored in PostgreSQL. |
| `SESSION_SECRET` | Random secret for hashing login-throttle IP identifiers. |
| `CHALLONGE_API_KEY` | Challonge account API key, server-side only. |
| `ALLOW_MOCK` | `true` only on staging/local/CI. Production uses `false`. |
| `PORT` | HTTP port assigned by Railway; default 3000. |
| `PUBLIC_URL` | Optional canonical HTTPS origin for strict write-origin checking. |

Generate secrets with `openssl rand -hex 32`. Generate a password hash with the exported `passwordHash()` from `app.mjs`, passing the password through stdin rather than a shell argument. Store credentials exclusively in Railway service Variables or an ignored local environment file. Rotate the administrator password by updating its Railway variable and redeploying; invalidate existing sessions with `DELETE FROM <schema>.sessions` when rotating after suspected compromise.

Sessions use random 256-bit tokens; PostgreSQL stores only their SHA-256 hashes. Cookies are HttpOnly, SameSite=Strict, Secure in production, and expire after eight hours. Administrative writes require the session CSRF token; JSON-only mutation endpoints also reject foreign browser origins. Login limits are persistent in PostgreSQL, and a separate per-process API rate limit bounds ordinary requests. Deployed container runs as a non-root user.

## Operating the league

1. In `/admin`, create an event, set its date, IANA time zone, location, registration window, and deck deadline. Phoenix is the default. The event receives the currently published point schedule as an immutable copy.
2. Open registration. Players create a separate team for their pair and register it on the event page; registration can happen before either deck is ready. They then save both decks before the deck deadline and explicitly update the event submission. Public editing is deliberate: anyone selecting a team can edit its general decks and update unlocked event submissions.
3. General team decks and event submissions are separate. Players explicitly copy their saved decks into an event with **Update event from saved team decks**. Changing general decks never changes a historical event.
4. Close registration, review both decks and the team budget, and lock submissions. A configured deadline is enforced at request time, including if the app was asleep when the deadline passed.
5. Create a Challonge tournament or link its integer ID / URL slug. Publish participants. Repeating publication reconciles markers and participant IDs instead of creating duplicates. Both decks must pass supported construction checks and budget checks before the website starts an event.
6. Start the tournament. Challonge supplies every real pairing and result. Use **Manage in Challonge** to report results; the app deliberately has no competing real-match reporting system.
7. Saved pairings refresh on a 30-second server timer when older than 45 seconds. Open public event pages refresh every minute. Rate-limit and timeout errors preserve the last successful snapshot and expose the error and last successful synchronization.
8. Finalize a completed tournament from the admin dashboard. Challonge's final ranks determine the champion. The archive retains final matches, standings, participant mappings, price version, and deck snapshots. Create a new event and reuse the same team identities.

Content supports editor previews, drafts, publishing, and loading an earlier version into the editor. Pricing supports complete-catalog search (including unpointed cards), independent main/CZ prices, editable multi-card drafts, publication, and restoration as a new draft. Published versions are immutable. Deck history supports restoration by player slot. Event history supports audited correction reasons and restoration of previous submission snapshots. Team removal archives identity rather than destroying event history.

## Team decks and organizer review

Deck versions are stored in PostgreSQL under a team ID and player slot. Browser storage remembers a default team selection; it does not own or store deck submissions. A direct link such as `/teams?team=TEAM_UUID` selects that team explicitly. Invalid/unavailable links do not fall back to another remembered team's decks.

Use **Create a new team** for a different pair. Editing player names or renaming an existing team preserves its ID, saved decks and registrations. The existing-team editor labels this clearly and asks for confirmation when renaming. This is a safeguard against accidental editing, not a new authorization system; the original open-edit model remains.

Each player slot shows **No deck submitted** until that team has a saved deck in that slot. Saved decks identify their team/slot, timestamp and full resolved list, including free cards and commanders. The text is formatted for Moxfield import. Current views use corrected canonical resolution; historical stored inventories/scores remain available unchanged.

In **Admin → Teams**, choose a team to view both current decks and submission history. Inspection does not change the organizer's remembered public team. **Edit team & decks** links explicitly to the inspected team. General saved decks and frozen event submissions remain separate; saving a general deck does not silently replace an event snapshot.

Team loading clears old forms immediately and discards aborted/stale responses. Saves, uploads and errors stay attached to their originating team/form. Event actions use the visible per-tab team choice, even if browser memory changes in another tab. See [TEAM_DECK_ASSOCIATION_FIX.md](TEAM_DECK_ASSOCIATION_FIX.md) for the investigation and regression evidence.

## Points catalog search

The search bar and results remain visible. Search help, filters, sorting, page-size selection, reset, and metadata notes are grouped in the **Advanced** disclosure, collapsed by default. Closing it preserves active filters and results; resetting filters restores the collapsed view.

`/points` supports a **bounded Scryfall-style subset**, backed by the local pinned catalog. It is not a proxy to Scryfall. Ordinary searches need no external API access. Search metadata never supplies or estimates league prices: `/api/points` reads the selected **published PostgreSQL price version** on every request. The browser pins that version while paginating to avoid mixed schedules; reload the page to pick up a later publication. Administrator card picking still uses the same endpoint, with its original numeric `main` and `command` fields.

| Search | Meaning |
|---|---|
| `Sol Ring` | Both name fragments, combined with AND; quote `"Sol Ring"` for one contiguous phrase |
| `!"Sol Ring"` | Exact canonical name or exact face name; returns one Oracle identity |
| `id:wu` | Identity contained in white-blue, including colorless and mono-colored cards |
| `id=wu` | Exactly white-blue identity |
| `c:u` | A blue card face; actual card color, not identity |
| `id:c`, `c:c` | Colorless identity / colorless card color respectively |
| `id:m`, `c:m` | Multicolor identity / multicolor card color respectively |
| `t:artifact` | Literal, case-insensitive type-line substring |
| `o:"draw a card"` | Literal Oracle text substring in the pinned catalog, including reminder text |
| `mv<=3`, `mv:3`, `mv:>=3` | Mana-value comparison (also accepts `cmc`) |
| `id:wu t:artifact o:"draw a card" mv<=3` | All conditions must match |
| `-t:creature` | Negation of one condition |

Aliases: `identity`, `color`, `type`, `oracle`. Numeric and color-set comparisons accept `=`, `!=`, `<`, `<=`, `>`, `>=`. For color sets these are subset/superset comparisons, not just color-count comparisons. Color names and WUBRG letters are supported. Face-dependent colors are evaluated per face: Archangel Avacyn is searchable as white or red but does not have a white-red face; Glasspool Shore is a colorless face of its blue MDFC. Multiple conditions can match different faces, and results still contain one Oracle identity. The exact-color metadata includes Dryad Arbor's color indicator and devoid cards; color identity and mana costs are never used to guess color.

OR, grouped expressions, regex, unsupported operators (including `set:`, `is:`, `legal:`), malformed quotes, and invalid filters produce **HTTP 400**, with a descriptive `error` and `code`. Valid searches with no matches return **HTTP 200** with `total: 0, cards: []`. This is intentionally not every feature of [Scryfall's syntax](https://scryfall.com/docs/syntax).

The UI provides five color checkboxes, contained/exact identity, colorless/multicolor categories, point location and integer ranges, zero/pointed/all views, type, mana ranges, pinned Commander legality, commander eligibility, and all eight requested sort orders. Search and GUI conditions are ANDed. “Either location” filters the higher of the two prices. Ineligible cards display **—** in the command-zone column, rather than presenting an ineligible card as a free commander; known eligible zero-point commanders display **0**. Commander-zero/range filters exclude ineligible zero entries. A nonzero published command price remains visible even if an organizer assigned it to an ineligible card; it does not confer eligibility.

Filtering and sorting happen across the entire matching set **before** slicing pages. Equal prices/mana values tie-break by canonical name and Oracle ID. Ineligible command-zone values sort last in either direction. Search requests are debounced and aborted when superseded; old responses cannot replace newer results. Loading, empty, syntax-error and network-error states are distinct. The page retains the existing pointed-only default, offers 50/100-card pages, and includes Scryfall links without loading external card images.

### API parameters

`GET /api/points`: `q`, `version` (published UUID), `offset` (0–1,000,000), `limit` (1–100, default 100); `sort` (`main_desc`, `main_asc`, `command_desc`, `command_asc`, `name_asc`, `name_desc`, `mv_asc`, `mv_desc`; default `name_asc`); `points` (`all`, `pointed`, `zero`); `zone` (`either`, `main`, `command`); integer `min`/`max`; `identity` (WUBRG letters or `c`), `identityMode` (`within`, `exact`), `colorCount` (`any`, `colorless`, `multicolor`); literal `type`, numeric `mvMin`/`mvMax`, `legality` (`any`, `legal`, `banned`, `not_legal`), `eligible` (`any`, `1`). Empty optional ranges/identity/type mean no filter. Legacy `pointed=1` remains supported; explicit `points` takes precedence. Repeated/unknown parameters, invalid enums, negative/noninteger pagination or points, and inverted ranges are rejected.

Responses retain `version`, `total`, `offset`, `cards[].name/oracle_id/legal/main/command`, and add `limit`, card color/identity, individual color faces, type line, mana value, pinned legality status, commander eligibility and Scryfall URL. Only verified catalog identities receive known-unlisted zero prices; a nonexistent card search returns no row. Legality and eligibility here describe catalog metadata, not certification of a complete deck, partner pair or gameplay interaction. No scoring or construction rules were changed.

### Rebuild search metadata

The October 20 scoring snapshot intentionally omitted top-level colors. `data/search-metadata.json.gz` adds colors/face colors and card URLs from the **exact original full Oracle archive**, not a new catalog. All 38,940 identities must match; the builder verifies the raw bulk SHA-256 and the loader verifies catalog and uncompressed metadata checksums. Provenance and the download URL are in `data/search-metadata-source.json` and `data/search-metadata.provenance.json`. No prices, bans, card identities or scoring fields are imported.

Download that recorded URL to a local file, then, with Node 22:

```sh
node scripts/build-search-metadata.mjs /path/to/oracle-cards-20261020210200.jsonl.gz
node scripts/build-search-metadata.mjs /path/to/oracle-cards-20261020210200.jsonl.gz --check
```

Normal startup and tests use the committed metadata offline. If the archived download expires, use a retained copy with the same recorded hash; do not silently replace it with current data. A future catalog refresh needs an explicit new catalog/source pin and regenerated metadata together. Historical event inventories and prices are independent of these search fields.

## Scoring and construction checks

`points.csv` is byte-identical to the canonical 549-identity `commander-doubles-deck-benchmarks/recalibration/community_review/POINTS_v3.csv` from merged PR #6. Historical research files are unchanged, including their `season0-proposed` / `activated=false` designations. The deployed initial schedule is the accepted v3 playtesting baseline; website operation does not rewrite historical activation claims.

The prototype's tested CSV, parser, URL validation, Moxfield decoding, and budget logic are preserved in `scoring.mjs`. Budget policy matches the existing backend: 120 combined, nominal 60 each, maximum 72 individual, up to 12 points of the teammate's unused share. Starting life is 60 shared.

The bundled full Oracle snapshot (`data/oracle.jsonl.gz`) is copied from the repository's pinned October 20, 2026 catalog, with interchangeable-name aliases from its existing ranking code. Known unlisted cards cost zero; unresolved or ambiguous cards are errors. Legality uses the identity's `legalities.commander` status. The Oracle bulk record's `digital`/`games` flags describe its representative printing and must not disqualify a card that has legal paper printings.

Deck imports prefer exact canonical names over face aliases (for example, Demonic Tutor over the spell face of Emeritus of Woe). Nonambiguous punctuation/diacritic differences and small spelling errors can resolve locally; corrections are displayed, persisted, and charged the canonical card's published price. Fuzzy matching allows one edit for folded names of 5–11 characters and two for longer names, including adjacent transpositions; competing identities within one edit of the best match require an exact name. Short names are never guessed. Arena `A-` names cannot be guessed into their paper counterparts. Organizer price editing remains exact. A new card absent from the pinned catalog still requires a catalog update, not an invented free price.

Current views and new event submissions re-evaluate retained text exports to recover past name-resolution mistakes. Stored deck versions, stored scores, frozen event registrations, and historical prices are not rewritten. Old URL-only imports have no retained original names; reimport them to verify identities if a previous alias was wrong. See [IMPORT_FIX.md](IMPORT_FIX.md) for incident evidence and remaining limitations. Construction checks cover 100-card inventories, command-zone eligibility and legal pairs (Partner, named partners, Backgrounds, Friends forever, and Doctor companions), color identity, singleton/copy-limit exceptions, and paper Commander legality/bans in that pinned catalog. Both faces resolve to one identity and one zone price. Judge rulings, future card releases/ban changes, gameplay policies, and full execution of combo interactions are not certified by these checks. The date and this distinction are shown publicly.

## Moxfield: verified limitations and fallback

Moxfield has no supported public application contract for this importer. The adapter calls only the fixed public `api2.moxfield.com/v3/decks/all/{id}` host, with a ten-second timeout, no redirects, and a bounded one-minute in-memory cache. It uses no player passwords, browser sessions, or private cookies. Mainboard and commanders are decoded independently; sideboards and maybeboards are excluded.

Actual tests performed in this implementation:

- Local direct import of `https://moxfield.com/decks/Ar6aYd7qVkK6GoFD4f9P4Q` succeeded, resolving **100 cards** (`Thrasios & Bruse, Dawnwaker cEDH`).
- Another public deck was denied from Node locally. Python and Node responses differed; access is not reliable across clients or hosting IPs.
- **Both tested direct imports on the deployed Railway service were denied.** No deployed direct-import success is claimed.
- That real imported list was converted to sectioned text, submitted through the deployed fallback, scored at **431 v3 points**, flagged for construction/budget issues, and persisted with its resolved inventory and original Moxfield link.
- Synthetic, construction-valid two-deck fixtures were scored at 19 each / 38 combined through the real hosted UI and PostgreSQL. They are explicitly test records, not real league results.

Players may paste or upload a Moxfield `.txt` export. Include `COMMANDER` and `MAINBOARD` (or `DECK`) headings, or mark commander lines with `*CMDR*`, so commander prices are unambiguous; set/collector and foil/etched annotations are accepted. Bracketed/colon headings and `1x` quantities are also supported. Blocked/unavailable imports automatically reveal and focus the text fallback without erasing the saved deck or URL. The validator reports main-deck and command-zone counts separately when the total is not 100. The form explains this and preserves the URL alongside the export. A failed import is an error, never a zero-point score. Approved Moxfield API access would improve direct imports; fallback scoring and saving already work on Railway.

## Railway deployment

One application service and PostgreSQL suffice for production. `Dockerfile` uses Node 22, `npm ci --omit=dev`, and a non-root runtime. `scripts/configure-railway.mjs` stores the start command, `/health` check, and bounded restart policy directly in Railway. `railway.json` is retained only for older deployment compatibility; it is deprecated by Railway and is not required by the configured production service. Set the GitHub service root to `/commander-doubles-web` and choose `commander-doubles-league`; production has this branch/root configuration and Wait for CI enabled. To reproduce runtime settings, run `node scripts/configure-railway.mjs` with `RAILWAY_TOKEN`, `RAILWAY_SERVICE_ID`, and `RAILWAY_ENVIRONMENT_ID` supplied securely in the environment. With a subdirectory-only CLI upload, use the uploaded folder as root (`/`) instead.

Production and staging use distinct app services and database schemas on the existing Railway project. The supplied project token is restricted to the existing Railway environment; creating another Railway environment was denied. Schema/service separation provides independent application and data configuration without requiring broader credentials or another database. Avoid pointing staging lifecycle tests at the production schema. Staging alone enables the deterministic test provider.

## Testing and evidence

```sh
# Real PostgreSQL required. Integration tests create and drop only a fresh test_<uuid> schema.
npm test
# JUnit machine-readable report plus readable output:
mkdir -p reports
node --test --test-reporter=spec --test-reporter=junit \
  --test-reporter-destination=stdout --test-reporter-destination=reports/unit-integration.xml tests/*.test.mjs
# Start local app first. On macOS, tests use installed Google Chrome.
# CI uses Playwright Chromium (npx playwright install --with-deps chromium).
BASE_URL=http://localhost:3000 npm run test:e2e
```

CI runs unit/integration tests with PostgreSQL 17 and full browser lifecycle tests. Browser output is JSON, JUnit, and screenshots under `reports/`; retained failure traces are under `test-results/`. External-service tests are separate, opt-in, and never run automatically against real tournaments from a PR.

The deterministic mock provider is confined to test/staging events, implements only the four-team single-elimination acceptance fixture, and is disabled in production. It is not a league tournament engine. The actual Challonge adapter was separately exercised through complete disposable single-elimination and round-robin tournaments, including hosted event creation/linking, repeat participant synchronization, start, real API result reporting, manual synchronization, finalization, champion/standings, and second-event history preservation.

See `ACCEPTANCE.md` for the final executed results and deployment links. Do not equate mock, actual external API, and deployed-browser evidence.

## Backups and recovery

`/admin` → **Export league backup** downloads a consistent PostgreSQL snapshot containing all important league records, price versions, decks, registration history, and audit entries. Sessions, credentials, and login IP hashes are deliberately excluded.

```sh
npm run backup -- /secure/path/commander-doubles.json
# Restore only to a NEW recovery schema; never overwrite production in place:
DATABASE_SCHEMA=restore_recovery node scripts/restore.mjs /secure/path/commander-doubles.json
```

Keep exports private: player names and deck history are included. `scripts/restore.mjs` refuses a schema not starting with `restore_` and refuses nonempty team data. Verify counts/snapshots in the recovered schema, then change the service's `DATABASE_SCHEMA` and redeploy to cut over. Railway's PostgreSQL volume backups should also be enabled according to the account's backup policy; this code does not claim a paid backup schedule was configured. Keep the previous schema and deployment until recovery is verified. An earlier application image can be redeployed through Railway; additive schema migrations preserve the recovery path.

## Integration references

- [Challonge v2.1 getting started](https://challonge.apidog.io/getting-started-1726706m0)
- [Challonge authorization](https://challonge.apidog.io/authorization-1726705m0)
- [Challonge tournament create and format options](https://challonge.apidog.io/create-tournament-23619740e0)
- [Challonge tournament lifecycle example](https://challonge.apidog.io/running-a-two-stage-tournament-1726921m0)
- [Railway API authentication](https://docs.railway.com/integrations/api)
- [Railway service configuration](https://docs.railway.com/integrations/api/manage-services)
- [Scryfall bulk data](https://scryfall.com/docs/api/bulk-data)

Card data and game names belong to their respective owners. No ownership of Oracle text is claimed.
