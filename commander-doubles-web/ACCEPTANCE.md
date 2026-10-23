# Executed acceptance results

Production: https://cedh-production.up.railway.app  
Admin: https://cedh-production.up.railway.app/admin  
Staging: https://commander-doubles-staging-production.up.railway.app

Executed October 22, 2026 (America/Phoenix). Test resources are explicitly disposable; production starts with no invented league events or teams.

| Evidence class | Result |
|---|---|
| Unit + PostgreSQL application integration | **47 passed, 0 failed**; fresh disposable real PostgreSQL schema |
| Deployed Chrome / mobile browser | **3 passed, 0 failed**; actual hosted UI, forms, cookies, database |
| Actual Challonge v2.1 | Complete four-team single elimination **and** round robin passed |
| Multi-event preservation | Same four team IDs; first archive unchanged after the second event completed |
| Real Moxfield direct import locally | **Succeeded**, 100 resolved cards |
| Real Moxfield direct import on Railway | **Blocked by upstream**, both tested links |
| Real Moxfield export fallback on Railway | **Saved and scored**, 100 cards, 431 points, validation issues correctly flagged |
| Backup / restore | **Passed**, isolated recovery schema; counts, champions, and frozen prices verified |

## Live tournament evidence

First event: https://commander-doubles-staging-production.up.railway.app/events/0795fd0f-b89d-4210-a72d-0c807e01a24f  
Challonge: https://challonge.com/cd_2c8e4c3378504f70b11fde7804a9ee5c  
Format: single elimination; state: complete; champion: **Disposable acceptance mvkit1j5 Team 1**. Both semifinals and final were reported through the actual Challonge API, then synchronized by the hosted application.

Second event: https://commander-doubles-staging-production.up.railway.app/events/40c113b8-99a9-434b-a419-b442b052ccc8  
Challonge: https://challonge.com/cd_7f3f540905fd43cda44b5db6e3f60e07  
Format: round robin; state: complete; champion: **Disposable acceptance mvkit1j5 Team 3**. All six round-robin matches completed. Original team identities were reused; the first event's full returned archive was compared before and after, including results and deck snapshots.

The hosted browser lifecycle independently created a mock event through the admin interface, created four teams, submitted eight decks, registered teams, locked submissions, published participants twice, played two semifinals and a final, finalized the champion, visited history, and registered an existing team in a new event. Browser tests also cover independent public browser editing, remembered team selection, admin logout, price publishing, rules preview, audit UI, mobile overflow, and search.

`evidence/summary.json`, JUnit reports, browser JSON, complete resolved lifecycle records, actual Challonge results, Moxfield results, and recovery verification provide machine-readable evidence. `scripts/live-acceptance.mjs` reproduces the bounded external test against staging only when explicitly enabled. The GitHub workflow runs deterministic database/browser tests without external-service credentials.

## Access and deployment

Retrieve the generated admin password from **Railway → Doubles EDH → cEDH → Variables → ADMIN_PASSWORD**. It is deliberately excluded from GitHub and this report. To change it, update that variable securely and redeploy. Keep SESSION_SECRET and CHALLONGE_API_KEY private. See README for all variable names and hash-only password configuration.

Production and staging are separate services and schemas in the authorized Railway environment. Creating another Railway environment was denied by the supplied environment-scoped project token; no broader token was requested. Mock tournaments are disabled in production. Persistent storage uses the existing Railway PostgreSQL service.

## Practical limits

Moxfield direct access from Railway is not reliable and is currently blocked for the tested URLs. Paste/upload fallback is implemented, tested, and required for these decks; direct access should not be represented as verified. Approved read access from Moxfield is the external improvement required for reliable direct imports.

Construction checks use the pinned October 20, 2026 catalog. New releases and later legality changes require a deliberate catalog update. Supported checks do not certify all gameplay interactions. Historical canonical pricing/rules files were not changed. Scheduled paid Railway volume backups were not claimed or enabled; the consistent application export and isolated restore were actually verified.

## Final production verification

All seven public/admin page routes loaded in actual Chrome, with no JavaScript errors or document overflow. Administrator login/logout and Secure/HttpOnly session behavior passed; anonymous admin API access was rejected. Production has the mock provider disabled and no test teams/events. Production GitHub source is `commander-doubles-league`, root `/commander-doubles-web`, with CI gating and path-based deploy filtering. Runtime configuration is stored directly in Railway, avoiding reliance on deprecated Config as Code.

## Credential remediation required

An initial browser evidence file included an absolute workspace path whose directory identifier coincided with the supplied Railway project token. That report was briefly pushed. The branch history was rewritten to remove the path, the superseded workflow run was deleted, and the current committed application/evidence was scanned against all supplied and generated credentials. No secret values remain in the current branch. Treat the old Railway project token as exposed and revoke/replace it in Railway project Settings → Tokens. The supplied environment-scoped token was denied permission to rotate itself. Browser credential changes require the account holder to complete that action. The application does not use this deployment token at runtime, so rotation does not interrupt the website.
