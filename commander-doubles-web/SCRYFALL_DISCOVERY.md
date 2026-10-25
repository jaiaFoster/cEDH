# Optional live card discovery — October 24, 2026

**Points → Advanced → Search all Magic cards with Scryfall** expands card discovery beyond the pinned league catalog. The normal page remains offline and unchanged by default. The checkbox is opt-in, survives closing Advanced, and Reset restores the local defaults. It does not alter point prices, catalog contents, deck imports, scoring, bans, budgets or historical snapshots. No migration or dependency is added.

## Behavior and tradeoff

Live mode accepts native Scryfall syntax, plus the compatible color/type/mana/legality controls. Name and mana-value sorts are delegated to the entire provider result set before 175-card pagination. Point filters and point sorting are disabled, with an explanation: Scryfall has no league prices, and sorting a single returned page by points would give a misleading global order. The previous local point settings are restored on return. Native syntax and metadata help are labeled separately from the local subset and pinned metadata date.

The normal Scryfall omission of extras prevents an art-card Sol Ring from appearing beside the playable card by default. `include:extras` explicitly includes such objects. Card links give Scryfall credit and let players inspect full details; no images or external scripts load in the public page.

The adapter matches **Oracle IDs** against the local catalog, then joins canonical names to the selected **published** PostgreSQL pricing version. Recognized unlisted cards are zero; unknown league identities are `priceKnown:false`, with `main:null`/`command:null`, shown as **Pending**. This remains true if the current Scryfall card is legal, or its name resembles a priced card. Card legality shown in live mode is Scryfall’s current metadata, not an automatic league approval. Commander eligibility is the league catalog’s value for known identities and `null` for unknown ones. No Scryfall monetary-price field is retained or used.

The fixed-origin server adapter has identified headers, no redirects, an 8-second request timeout, a bounded serial queue with 5-second maximum wait, max 12 pending calls, max 5 upstream starts/second per process, in-flight deduplication, and a 64-page/60-second metadata cache. Each caller joins its own selected published prices after cache retrieval. 429 cooldown accepts numeric/date Retry-After. No caller-supplied endpoint or `next_page` URL is fetched. 400/422 query errors,404 no matches,429/backpressure and network/upstream failures have distinct behavior; live failure never silently becomes an empty/free result or replaces the offline source.

## Executed validation

- **90 Node/PostgreSQL checks passed, zero failures**, including all 82 earlier checks plus 8 new tests. New checks cover native query composition, canonical identity joins, known zero/CZ prices, unverified legal fixtures, price-version changes with cached metadata, fixed host/headers/redirect behavior, pagination/sort forwarding, errors, deduplication/expiry, global spacing and queue bounds. A real disposable PostgreSQL/HTTP test checks current versus pinned published versions and preservation of stored prices/catalog size.
- **24 Chrome/Playwright tests passed, zero failures**, including all 22 previous browser checks plus two new live-mode browser tests. Existing administrator pricing, team/deck association and tournament lifecycle tests remain included. New tests cover opt-in visibility, pending prices, combined native syntax,175/25-card pages, global sort requests, restored controls, source-specific help, mobile layout, explicit service failure and delayed responses after switching offline. These automated cases use deterministic provider/browser fixtures and do not require Scryfall availability.
- A separate **actual Chrome + local application + real Scryfall API** smoke test passed: exact Sol Ring returned one identity and the current15-point published price; **Data, New Life** was outside the pinned catalog and returned Pending (`main:null`). Its live Commander legality was **not_legal**, not claimed legal or experimentally unbanned. A nonexistent-name sentinel returned 200 with zero results. `set:lea OR set:leb`, second page, returned 117 cards from 292 matches at offset 175. Mobile 375px had no document overflow. The smoke test is read-only and local; it is not Railway evidence.
- Screenshot review caught local-only syntax help remaining visible because the existing `.help` rule overrides the native `hidden` style. The catalog now explicitly honors hidden elements and labels live metadata without the pinned October20 date.

Reproduce normal tests with Node22 and a disposable PostgreSQL database using `npm test` and `npm run test:e2e`. Optional real-service smoke (requires Chrome, a running local app and internet):

```sh
BASE_URL=http://127.0.0.1:3340 node scripts/verify-scryfall-live.mjs
```

Its report/screenshots are under ignored `reports/`; it refuses nonlocal hosts. Future catalog updates may recognize the example new card, in which case the smoke test expects its verified numeric price instead of Pending. The API and fixture tests continue to exercise the unknown-identity condition independently.

Sources consulted: https://scryfall.com/docs/api/cards/search and https://scryfall.com/docs/syntax (the research web reader received403); the SDK author’s source at https://github.com/ChiriVulpes/scryfall-sdk/blob/main/src/api/Cards.ts documents the fixed175-card search page and sort options. The authorized public API returned 200 and its response shape, page size and query behavior were exercised directly. No credentials, paid API, new Railway authentication, hosted staging check, production write or deployment was used. Previous rulings work remains preserved in its own PR/branch.
