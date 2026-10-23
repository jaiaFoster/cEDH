# Commander Doubles — MVP Dashboard

Minimal public website: **score one or two public Moxfield Commander decks** against the pinned Season 0 v3 points snapshot, and show the next league matchups. This is a point calculator and display, not a tournament management platform.

## Features
- Paste one or two Moxfield links; score all **100 cards per player**, including one or two command-zone cards at their separate CZ prices.
- Show combined team budget **120**, one-head maximum **72**, and available point transfer (**up to 12 from the teammate's unused share of 60**).
- Expand a list of cards that cost points. Cards absent from the 549-card list cost **0** by policy, not by a card-legality determination.
- Read-only bracket via a JSON environment variable. No user accounts, deck storage, admin login, or database.
- Backup entry via pasted Moxfield text export. The Moxfield API is **unofficial** and may return 401/403/429 from Railway's server IP. This fallback prevents a blocked API from preventing use of the points system.

## Local
Requires Node 20 or later; zero runtime packages.

    cd commander-doubles-web
    npm test
    npm start

Visit http://localhost:3000. Health endpoint: /health.

## Deploy to Railway
1. Connect Railway to GitHub and choose repository **jaiaFoster/cEDH**; deploy the merged branch containing this folder (or select the MVP feature branch for testing).
2. In Railway **Service Settings → Source**, set **Root Directory** to **/commander-doubles-web**. The package.json and railway.json are in that folder.
3. Railway runs **npm start** with its assigned **PORT**; health check is **/health**. Generate a public domain for the service.
4. Optional: set the service environment variable **BRACKET_JSON** to an event fixture like:

    {"event":"Friday Commander Doubles — Round 1","rounds":[{"name":"Round 1","matches":[{"table":1,"teamA":"Team Alpha","teamB":"Team Beta","status":"next"},{"table":2,"teamA":"Team Gamma","teamB":"Team Delta","status":"upcoming"}]}]}

   The JSON env setting replaces bracket.json. If unset, the page accurately says no matchups are posted. This is a **manual organizer-edit** read-only bracket, not automatic pairings or score reporting. No made-up teams or matchups are seeded by default.

## Frozen price data
**points.csv** is a file-for-file copy of the 549 pointed card identities from:
commander-doubles-deck-benchmarks/recalibration/community_review/POINTS_v3.csv

Every entry includes the deck price and (if applicable) command-zone price. Exact same v3 snapshot; no live edits or separate shadow pricing logic. **To update after a future pricing decision**, replace this CSV and redeploy. Existing season0-proposed and activated=false designations are retained; showing a score does not activate league rules.

### Deck import contract
- Accepts only https://moxfield.com/decks/{publicId} (and www); server calls the fixed Moxfield read endpoint; never fetches user-provided arbitrary URLs.
- Expects Moxfield JSON mainboard and commanders; ignores sideboards/maybeboards.
- Export fallback expects a sectioned text list with **COMMANDER** and **MAINBOARD/DECK** headings. Set markers/collector numbers are optional. A deck with != 100 cards is scored but flagged incomplete, and cannot receive a green team-budget result.
- Server caches Moxfield decks for 60 seconds; no card lists saved or written to disk.
- **Important limitation:** Moxfield has no supported public API; some services require Moxfield-approved User-Agent/auth and automated fetches can fail. Test actual imports on the deployed Railway domain with a public deck. If denied, request official read access or keep paste-export fallback; do not request users' Moxfield passwords or copy session credentials into the site.

### Scope and next steps
No recommendations, leaderboards, authentication, persistent brackets, deck editing, signup or payment. A future version could use a database or organizer-protected bracket editor after the baseline is tested. Point validation is not a legality check; existing Commander / Commander Doubles bans and color-identity requirements still apply independently.
