# Team/deck association and review — October 24, 2026

## Observed incident versus interface flaws

Read-only inspection of the production public API found **one team at the time of inspection**. Its team ID matched the organizer's previously inspected test team, and both deck-version IDs matched the original test submissions. Its team/player labels had changed. The returned deck rows each had `team_id` equal to the selected team's ID.

This establishes that the existing team record was edited/renamed; the displayed lists were its actual database records. It does not establish who edited it or prove a stale-response race caused this particular incident. No production record was changed, restored, reassigned or deleted. Personal player names, production team IDs and credentials are not committed as evidence.

Code inspection separately identified reproducible interface defects:

- The public team editor left old forms visible while another team loaded, and had no abort/generation/selection check before rendering a response. A late result could display another team's editor under the current picker value.
- An asynchronous upload used global input selectors after reading the file, allowing an old read to populate a newly rendered team's input.
- Save/error completions could refresh or focus controls belonging to a later selection.
- Organizer inspection called `setTeam()` and silently changed the remembered public team.
- Public event actions read shared browser storage rather than the visibly selected team; another tab could change their target.
- The public general-team editor displayed a pointed-card breakdown but no convenient complete saved list. Its create-versus-edit distinction and empty-slot states were unclear.

The database already stores deck versions with a team foreign key and slot. Loading is scoped with `WHERE team_id=$1`. This fix preserves that model; it does not migrate ownership or introduce accounts.

## Resulting behavior

1. A prominent **Create a new team** action targets the creation form. A different pair gets a separate team record and two empty deck slots.
2. The existing-team heading identifies the selected team. Help explains that renaming/changing players preserves its decks. Renaming asks for explicit confirmation instead of appearing to create a separate team.
3. Selection removes old forms immediately, shows loading/error/empty states, cancels superseded fetches and rejects late/mismatched results. Per-tab visible selection controls saves; storage is only an initial default.
4. Upload/save/error callbacks retain their originating elements and team ID. A delayed callback cannot populate or replace another team's form. An already submitted save still completes for the team it originally targeted.
5. Each player slot explicitly shows **No deck submitted** or identifies the saved team/slot and timestamp. **View full saved decklist** includes every known card, zero-point cards, quantities and the command zone, using sectioned importable text. A saved Moxfield source has an external link.
6. `/api/teams/:id` adds derived `current_deck` alongside `current_score`. Original stored `deck`/`score` fields are untouched. This prevents an old canonicalization mistake in a retained text export from contaminating the current list view.
7. Organizer team inspection has an independent guarded loader, both current player slots and historical versions. It leaves public browser memory unchanged; editing uses an explicit `/teams?team=...` link.
8. Unavailable explicit team links display no remembered deck. Blank/failed selections remove old details. Event registration/submission uses the visible team and preserves that choice while refreshing the event.

## Existing records still require an organizer decision

The renamed production record continues to hold the old test decks. The interface fix deliberately does not guess whether to restore that record's old name, create a separate new pair, or replace its decks. A distinct new team starts empty. Existing deck histories and any event registrations must be preserved during any separately approved data correction.

Open team editing remains deliberate: selecting an existing team permits editing it. The confirmation is a user-interface safeguard, not ownership authentication. A PIN/account model would be a separate product decision.

## Executed validation

- **82 Node/PostgreSQL checks passed**, including every previous check and a new integration scenario: one team's deck stays isolated, another team registers with no decks, its own later player-slot submission is copied only when requested, and renaming preserves the original team's deck versions. Temporary scenario records are removed from the disposable schema so the pre-existing exact-count assertions remain intact.
- **22 actual Chrome/browser tests passed**, including all 12 previous tests and 10 new team-association tests. New scenarios cover separate empty teams, full lists/current derived inventory, reloads, mobile overflow, late transport responses even when abort is ignored, failed/blank loads, in-flight saves, delayed file reads, organizer inspection/history races, rename cancel/confirm, explicit/unavailable links, and event targeting after a cross-tab storage change.
- Local browser actors use separate documentation-only proxy IPs under the app's existing one-hop proxy setting. These headers are sent only to localhost, never a hosted service. Production rate limits are unchanged.
- Mobile screenshot `reports/team-deck-association-mobile.png` was visually reviewed; browser artifacts remain ignored locally and uploaded by existing CI.
- `git diff --check` passed.

Reproduce using the Node 22/disposable PostgreSQL setup in README:

```sh
npm test
npm run test:e2e
```

No schema migration, point/rules change, historical rewrite, production mutation, merge or deployment is included. Hosted staging was not tested. The production read-only observation above is evidence of existing associations, not hosted verification of the new implementation.
