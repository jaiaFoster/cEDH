# Card identity and deck-import correction — October 24, 2026

This is a website validation/import fix. It changes no league prices, point caps, Commander bans, rules, or historical records. Resolution version: `oracle-identity-v2`; the Oracle snapshot remains October 20, 2026.

## Confirmed causes

1. `evaluate()` required `games` to contain `paper` and `digital` to be false on the single representative Oracle bulk record. **1,047 identities** in this exact snapshot are marked Commander-legal despite having nonpaper/digital representatives. All 14 unique cards shown in the organizer's screenshots are in that group: Lotus Petal, Strip Mine, Bayou, Cabal Ritual, Putrid Imp, Glacial Chasm, City of Traitors, Mox Diamond, Savannah, Scrubland, Survival of the Fittest, Tropical Island, Tundra, and Underground Sea. These cards were recognized, not unknown. Legality now uses the identity's explicit Commander status. Actually banned and nonlegal identities remain rejected.
2. The old alias builder let another legal card's face replace a standalone canonical name. **Demonic Tutor** was resolved as **Emeritus of Woe // Demonic Tutor**, losing the actual tutor's price. Canonical names now take priority, including when a token shares a name. Explicit pre-existing interchangeable-name mappings remain supported. Face names still resolve where unambiguous; canonical price keys also take priority over face-price aliases.

## Measured incident regressions

| Retained input | Before | After under bundled v3 |
|---|---|---|
| Original 100-card text export, Thrasios/Tymna | 492 points, ten false printing-legality errors | **507 points, 100 cards, construction-legal**; Demonic Tutor receives its existing 15 points. Still over the 72-point league limit. |
| Saved Gitrog resolved inventory | 279 points, 98 cards, six false printing-legality errors | **279 points, 98 cards**; only the genuine incomplete-inventory check remains: 97 main-deck + one command-zone card. |

The Gitrog fixture is an existing resolved inventory, **not a fresh Moxfield API response**. Its old canonical names cannot be inferred backwards safely. No two replacement cards are fabricated. A direct public Moxfield request for that list returned **HTTP403** during this investigation, so the original response and cause of the 98-card source count could not be recovered. The decoder's fixtures demonstrate that all returned mainboard/commander quantities are preserved; sideboards/maybeboards are deliberately excluded. The count issue remains a source-verification question, not a claimed decoder repair.

Original public deck links, retrieved from the saved submission metadata on October 24:
- [100-card text-export source](https://moxfield.com/decks/gvyGvOx0g0uJ7ultPy-pbw)
- [98-card saved-inventory source](https://moxfield.com/decks/AOcIsMkjW0Kg4V6tkON-eQ)

`tests/fixtures/import-incident-100.txt` contains the original retained public deck export. `import-incident-98.json` contains only the saved deck inventory; player names, team identifiers and account metadata are excluded. These are reproducible incident fixtures, not claims about a later edit of either live list.

## Tolerant names without invented legality

`card-resolution.mjs` resolves exact canonical names, unambiguous faces/known alternate names, then punctuation/diacritic normalization. Small spelling differences use bounded optimal-string-alignment distance, including adjacent transpositions. One edit is allowed for 5–11-character folded names; two for longer names; fewer than five characters are not guessed. A runner-up identity within one edit of the best match blocks automatic selection. Candidates include banned cards: typos cannot make a recognized banned card free or legal. Unknown Arena `A-` names are not guessed as paper cards.

Corrections include submitted name, canonical name, Oracle ID, and match method in the returned score and saved rows. The public result visibly asks players to review matches. Corrected identities drive point costs, singleton, color-identity and commander checks. Organizer price editing still uses exact resolution. Unknown/ambiguous inputs fail without saving a new deck.

Previously retained text is re-parsed for current scores, new event submissions, and explicit deck restores. Historical deck/score versions and frozen event registrations are untouched. A previously misresolved URL-only deck should be reimported, because the old importer did not retain its original names. No production records were edited during this work.

## Moxfield and TopDeck

Moxfield's intermittent HTTP401/403/429 restrictions are independent of card legality. We retain the existing bounded fixed-host adapter, timeout, cache and text fallback. There is no proxy rotation, browser-cookie harvesting, challenge bypass or claim of guaranteed URL access. Unreadable success bodies now give an actionable fallback message. Blocked/unavailable URL imports automatically open/focus the export fallback and preserve existing saved data.

[TopDeck's own explanation, June 11, 2025](https://topdeck.gg/blog/scrollrack-deck-submission-20250611), checked October 24, describes its in-house **Scrollrack** validation engine and support for Moxfield URL or plain-text imports. It does not publish the access arrangement or request strategy that makes Moxfield imports reliable for them. We reuse the documented separation of importing from identity/format validation, rather than asserting their proprietary implementation is available.

## Reproduction and verification

Use Node 22 and a disposable PostgreSQL database as documented in README:

```sh
node --test tests/imports.test.mjs
npm test
npm run test:e2e
```

The regression suite checks all 1,047 affected identities, all legal/banned canonical names across the entire catalog, the 14 reported cards, both retained incident fixtures, canonical/face/token conflicts, both price locations, fuzzy ambiguity and banned-card handling, export variants, exact 100/98 counts, database history preservation and malformed/blocked upstream responses.

Browser checks exercise the actual public form with the 100-card fixture, visible correction notices, mobile layout, unknown-name errors, saving via export after a simulated upstream block, and preservation of old saved data. The original tournament lifecycle, admin price editing and catalog tests remain included. Only the new **local** import-test actor supplies a documentation-only proxy IP to model a separate client under the local app's one-hop proxy configuration; this is never sent to a hosted service and production limits are unchanged.

No deployment or hosted staging verification is included. Do not confuse local fixtures or simulated blocking with successful live Moxfield access.
