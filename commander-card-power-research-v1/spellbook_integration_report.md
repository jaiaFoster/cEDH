# Commander Spellbook integration: executed results
Official [API documentation](https://spacecowmedia.github.io/commander-spellbook-backend/api.html), [backend](https://github.com/SpaceCowMedia/commander-spellbook-backend), [website](https://commanderspellbook.com/). Data credited to Commander Spellbook.

## Live tests
Five full precons were submitted by Oracle ID to POST /find-my-combos/?limit=1000 on 2026-10-19. Each request was repeated once. All succeeded and all repeats matched exactly at this snapshot. This does not guarantee future database stability.

| deck | included | almost | almost with extra colors | identical repeat |
| --- | --- | --- | --- | --- |
| Mutant Menace | 0 | 5 | 0 | True |
| Science! | 1 | 22 | 9 | True |
| Explorers of the Deep | 0 | 13 | 7 | True |
| Necron Dynasties | 0 | 26 | 14 | True |
| From Cute to Brute | 0 | 26 | 0 | True |

Science!'s included variant is [2047-6465](https://commanderspellbook.com/combo/2047-6465/): James, Wandering Dad // Follow Him plus Mechanized Production. The API describes casting Follow Him while an upkeep trigger is pending, with up to ten mana plus possible commander tax and relevant battlefield setup. The outcome is Win the game. A component match does not prove early access, valid attachment, sufficient mana, successful timing or resistance to interaction. We flag a potential win outcome and leave early-win status unestablished.

The other four precons have no included variants in this snapshot. That means no recognized included variant was returned, not proof they contain no combo, no lock or no potent synergy. Almost matches retain missing-component/color/commander categories. No bracket label was used as strength validation, and the bracket-estimation endpoint was not benchmarked.

## Cross-team positive control
A two-card fixture splits Exquisite Blood and Sanguine Bond between hypothetical players. API variant [690-3966](https://commanderspellbook.com/combo/690-3966/) is included in the union. The prototype marks cross-deck components required, controller review required, and functionality unverified. This fixture is not a legal complete deck or evidence that all union-detected combinations work across controllers.

Check who controls each trigger, what “you” refers to, affected opponents, zones, ownership, mana, commander access and 2HG replacements/rules. Components may need one controller or transfers not present in either list. A union can generate false positives; it is a candidate generator only. No cross-controller rules solver is implemented.

## Client behavior
Local names are resolved against the complete frozen Oracle snapshot; unknown names raise an error rather than being silently dropped by the API. The CLI supports explicit Commander/Main sections, printing annotations and two deck files. It retains required component quantities, zones, templates, commander requirements, prerequisites, mana, outcomes, variant IDs and links.

Response partitions distinguish included, commander-role changes, near matches and added-color cases. Included variants with templates or concealed/null prerequisites remain unresolved. Even the component_complete label means only complete components, never executed gameplay. Template/executable state resolution and natural-language prerequisites are manual.

Potential win/lock/mass-land-denial flags use outcome wording as a conservative review aid. They are incomplete heuristics, not a comprehensive legality classifier. Mana value needed is not a win-turn prediction. Unsupported or unusual situations retain raw API fields. Every record has construction_point_adjustment=0.

Timeouts, named User-Agent, bounded 429/502/503/504 backoff, safe pagination hosts and pagination-cycle checks are implemented. Pagination preserves the POST body. API schema changes fail explicitly rather than silently making an empty success. Ten unit tests exercise client behavior; eight additional research tests verify identity, missing data, safe pickle decoding, additivity, basic-land consistency and the absence of combo point surcharges.

## Limits and reuse
The browsable root advertised API 7.2.0; a cached variants view showed 7.1.9. Frozen raw responses and UTC retrieval times are retained in data/spellbook, with payload/response hashes. No sensitivity/specificity is claimed: our fixtures do not supply complete adjudicated true-positive/false-positive labels.

The official docs recommend sparse unauthenticated requests, a named User-Agent, about 80 requests/minute as a safe level, and backoff on 429. We used sparse requests. For full local indexing, use the documented https://json.commanderspellbook.com/variants.json.gz bulk artifact with timestamp/version/aliases, not REST pagination to export the database. That bulk artifact was researched, not downloaded in this sprint.

The backend code is MIT and its full notice is retained. API documentation permits consumption and asks for credit/linking; an independent blanket data-redistribution license was not conclusively verified. Do not interpret MIT code licensing as automatically covering every third-party datum. Popularity is supplied by EDHREC and is not an independent card-strength measurement. No combo degree, salt, bracket or popularity feature is added to construction prices.
