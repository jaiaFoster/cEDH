# Commander League calibration — executed research snapshot

Analysis date: 2026-10-19. Scoring version: 0.2.0-provisional. This is an exploratory fixed-card resource index, **not a validated measure of Commander power**. It is ready for manual refinement and shadow scoring; it does not support a strict league cap yet.

## Executive answers

1. **174 unique paper Commander precons**, deduplicated from 198 product records. All 100 playable entries, command zones, source metadata and original records are retained in `data/clean/precons.json`.
2. Original releases cover **2011–2026**. Coverage is bounded by the retrieved archives, not a promise that every released product has been independently found.
3. Overall median: **896.5 points**; resampled-deck 95% median interval 878–916.
4. Most recent annual cohort (2026, n=21): median **939**. The latest individual release is 2026-10-02 (n=6, median 926.5); annual and release-product cohorts are different.
5. Early releases (2011–2015, n=20) median 783; modern releases (2024 onward, n=61) median 951; difference **+168** (deck bootstrap 95% interval +111 to +222). Linear slope +15.79 points/year; year-cluster bootstrap interval +12.91 to +18.78; descriptive R² 0.253.
6. Largest aggregate contributors: Sol Ring, Arcane Signet, Plains, Island, Forest. These aggregate contributions reflect inclusion and count as well as price; they were **not used to set prices**.
7. Thought Vessel (29) is implausibly above reviewed Arcane Signet (14), while The Wise Mothman and Kappa Cannoneer get only 2 each. These are concrete extraction/anchor-consistency failures, not evidence of true relative strength. Every automatic estimate is marked provisional.
8. Independent EDHREC six-deck assessment: Spearman **-0.486**, 5/15 correctly ordered pairs. This small, selected opinion sample cannot establish broad predictive accuracy. An independent Reddit author's five-deck ordering gives rho -0.600.
9. Resolve feature extraction errors, collect actual Bracket 2/3 labels and controlled league outcomes, review commander access and 2HG effects, and pre-register a broader validation set before imposing a binding cap. Card sums intentionally omit deck and teammate synergy.
10. Provisional **Core-candidate reference interval: 755–1059 points** (10th–90th percentile, n=130). This is a shadow-scoring comparison band, not an official Bracket 2 range. No quantitative Bracket 2/3 separation has been established; 1,000 and 2,000 remain design anchors.

## Data acquisition and quality control

The pinned taw commit is `38c4d2e9eb605467b7d35e5c230ef743199d3765`. The complete schema audit records every top-level and nested card key and observed Python type. The archive separates `cards` (mainboard) from `commander`; adding these is essential. `displayCommander`, sideboard, tokens, schemes and planes are preserved but excluded from the playable 100. No product was selected by a name substring or 100-card size alone: selection requires type `Commander Deck`, category `deck` and a Commander format. MTGO-only products are explicitly excluded from the paper baseline.

198 selected records all total 100. Canonical Oracle multiset deduplication collapses 24 identical records, preserving alias dates/products separately and using the earliest archived appearance for cohort statistics. This collapses Commander Anthology reprints and Collector's Editions. Different lists remain separate even if deck names match. Original 100 entries retain printing UUIDs, names, quantities and command-zone sections. Nonbasic multiplicities, missing names, size, commander color identity and current nonlegal cards are audited; legitimate any-number card exceptions are recognized.

The MTGJSON DeckList contains 198 Commander Deck records; name+set comparison finds 0 missing from taw and 0 missing from MTGJSON. **These are related sources:** taw includes MTGJSON UUIDs, so agreement does not independently verify every card. Full MTGJSON per-deck contents were not independently downloaded; this is a coverage cross-check. The all-decks HTML is client-rendered, so its published DeckList endpoint supplies the cross-check.

Oracle resolution prefers exact full names over face aliases, preventing art-series cards such as `Plains // Plains` from taking the place of Plains. The source's `(Prepared)` suffix is removed solely for exact prepared-card name matching; original strings remain saved. No fuzzy substitutions or zero-valued missing-card fallbacks are used. The snapshot contains 38,861 Oracle-ID records, including nonlegal objects for clear calculator rejection. New cards after the snapshot require reacquisition and review. `source_manifest.json` stores URLs, dates, hashes and access failures. Direct Reddit responses were challenge pages; the original-post validation labels were retrieved through the browser search text, documented separately. Moxfield returned an application shell, not a usable validated deck.

## Official guidance versus the model

Wizards' October 2025 update describes Core as unoptimized, straightforward and incrementally winning; its expected eight completed turns contrast with Upgraded's strong card quality, synergy and expected six completed turns. It removed general tutor restrictions and **decoupled precons from Core**. February 2026 reaffirmed this and added Farewell and Biorhythm to Game Changers. Searches found no later bracket update; this describes the latest official guidance retrieved, not an assertion that no later unpublished change exists. [October update](https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-october-21-2025); [February update](https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-february-9-2026).

The construction guidance uses zero Game Changers for Core and up to three for Upgraded, alongside restrictions on land denial, extra turns and game-ending combos. Presence or absence alone does not measure intent or speed. The October 2025 embedded official deck-list plus the two February additions reconciles exactly with Oracle; `game_changer_reconciliation.json` records the check. The downloaded Oracle snapshot flags 53 Game Changers; the full list is in `data/clean/game_changers.json`. MH3, Secret Lair and Commander Masters are separated as premium review cohorts; Starter decks are separate. Other zero-GC lists are only **Core candidates**, without a completed combo, turn-speed or gameplay audit. GC-bearing precons are exceptions, never silently treated as Core. Current banned cards in historical decks are flagged rather than removed from their original list. Upgrades Unleashed is a separate quality exception: its two Mossfire Valleys violate singleton. Wizards confirms the printing error and recommends replacing one with a basic or another land. The archived list is preserved without a silent correction. Foundations Commander (2026) is grouped with introductory products, following its official description.

For Commander 2HG, Wizards' format page specifies 60 shared starting life, no unified construction, 100 cards per player, and team loss at 21 damage from a single commander or 15 poison. Shared turns do not share hands or mana. Effects on each opponent apply to each player separately; there are two opponents, versus three in ordinary four-player FFA. These changes are card-specific and not a universal multiplier. The Commander 2HG format page and the general Comprehensive Rules need to be read together. [2HG format](https://magic.wizards.com/en/formats/two-headed-giant); [Comprehensive Rules snapshot](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt).

Current official bans are captured in `experimental_unban_review.csv`, including category bans and Lutri's companion-only restriction. The snapshot reconciles official named bans against Oracle legality in `legality_reconciliation.json`. Biorhythm and Lutri are no longer blanket banned; do not copy obsolete ban lists. The October 12, 2026 announcement's Yuriko commander ban concerns Competitive Brawl, not multiplayer Commander. [Official banned list](https://magic.wizards.com/en/banned-restricted-list).

## Mathematical model and coefficients

Each Oracle card gets one fixed nonnegative integer. Printing, year, monetary price, EDHREC rank and precon frequency are excluded. There is **no fitted card-power response variable**. Coefficients are explicit analyst priors motivated by functional resource access and Wizards' emphasis on efficient engines, interaction and tutors. Descriptive regression and bootstrap results test properties of this index; they do not transform its inputs into objective power ratings.

For nonlands, define binary role matches from reminder-stripped Oracle text. Each role is counted at most once; a repeatable acceleration, draw or board role is multiplied by 1.35; sufficiently broad removal by 1.25. The role weights are:

| role | weight |
|---|---|
| acceleration | 20 |
| advantage | 18 |
| tutor | 24 |
| interaction | 20 |
| board | 10 |

Let r₁ and r₂ be the two largest role values. Automatic nonland points before rounding are `2 + (r₁ + 0.35*r₂)/(1 + 0.22*max(0,mana_value−2))`. The primary role captures useful function; the second, discounted role credits flexibility. Remaining roles do not add points, limiting double counting. Raw body stats only supply a capped board role when power+toughness exceeds twice mana value. It is not a mana-value reward: expensive spells face a larger discount. No separate efficiency bonus duplicates the role value.

Land points are separate: basics 2; nonbasics 3 plus 3 for broad fixing, minus 2 for a matched tapped-entry clause, plus 3 for matched utility, floored at zero. Land text is not also given acceleration or tutor role points. This is an absolute land allowance; relative land quality, not a tax on using land, is what matters when comparing normal 100-card decks. Median collective land share is 13.0% of deck totals. Modal land faces and conditional tapped clauses need human review.

Game Changer status imposes a floor of 45, **not an additive bonus**, avoiding a duplicate charge for the same engine. Reviewed cards replace the whole estimate with a documented absolute override; they are not additive bonuses. There are 73 overrides. The global multiplier is 1.0; no observed deck/year is normalized. Final rounding is floor(value+0.5), consistent with integer overrides. Component columns explain estimated roles; because only the largest two enter the formula and floors/overrides replace it, **component columns must not simply be summed**.

The previous candidate v0.1 omitted the mana-value discount; v0.2 discounts expensive effects to address the conceptual risk of overpricing splashy cards. The change was specified before inspecting held-out scores and was not tuned to their rank. `initial_points` and `total_points` preserve both versions. Median deck change: -160; largest absolute change: 295. This is a transparent structural revision, not empirically optimized calibration. Magnitudes remain uncertain. Optional commander adjustment defaults to zero; adding one requires new commander-specific evidence. Teammate synergy is never a scoring input.

## Observed distributions

| year | count | mean | median | std | iqr | p5 | p10 | p25 | p75 | p90 | p95 | min | max | high_impact_mean | high_impact_median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011 | 5 | 760.20 | 772.00 | 124.44 | 130.00 | 647.00 | 648.00 | 651.00 | 781.00 | 883.00 | 917.00 | 646.00 | 951.00 | 2.00 | 2.00 |
| 2012 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 2013 | 5 | 736.40 | 751.00 | 63.54 | 87.00 | 657.80 | 667.60 | 697.00 | 784.00 | 794.80 | 798.40 | 648.00 | 802.00 | 1.60 | 1.00 |
| 2014 | 5 | 826.60 | 830.00 | 56.42 | 58.00 | 754.20 | 768.40 | 811.00 | 869.00 | 877.40 | 880.20 | 740.00 | 883.00 | 2.60 | 2.00 |
| 2015 | 5 | 839.40 | 845.00 | 74.71 | 115.00 | 754.80 | 761.60 | 782.00 | 897.00 | 913.80 | 919.40 | 748.00 | 925.00 | 1.80 | 2.00 |
| 2016 | 5 | 832.80 | 844.00 | 110.89 | 86.00 | 690.00 | 720.00 | 810.00 | 896.00 | 930.80 | 942.40 | 660.00 | 954.00 | 2.40 | 2.00 |
| 2017 | 4 | 865.75 | 875.00 | 42.98 | 35.75 | 815.30 | 824.60 | 852.50 | 888.25 | 899.50 | 903.25 | 806.00 | 907.00 | 2.50 | 2.50 |
| 2018 | 4 | 828.25 | 829.50 | 51.55 | 82.75 | 779.10 | 781.20 | 787.50 | 870.25 | 874.30 | 875.65 | 777.00 | 877.00 | 2.00 | 1.50 |
| 2019 | 4 | 842.25 | 827.50 | 41.57 | 39.75 | 812.60 | 813.20 | 815.00 | 854.75 | 883.10 | 892.55 | 812.00 | 902.00 | 2.50 | 2.50 |
| 2020 | 9 | 867.89 | 853.00 | 121.31 | 153.00 | 728.80 | 755.60 | 772.00 | 925.00 | 1028.60 | 1053.80 | 702.00 | 1079.00 | 3.00 | 3.00 |
| 2021 | 15 | 863.47 | 879.00 | 77.51 | 129.00 | 759.30 | 768.00 | 793.00 | 922.00 | 932.20 | 960.00 | 753.00 | 1023.00 | 1.80 | 2.00 |
| 2022 | 25 | 901.08 | 885.00 | 102.96 | 157.00 | 743.60 | 768.40 | 837.00 | 994.00 | 1027.80 | 1045.80 | 732.00 | 1063.00 | 2.36 | 2.00 |
| 2023 | 27 | 930.96 | 916.00 | 143.23 | 139.50 | 730.00 | 792.20 | 860.00 | 999.50 | 1070.20 | 1107.70 | 682.00 | 1412.00 | 2.26 | 2.00 |
| 2024 | 26 | 958.92 | 943.00 | 112.36 | 172.50 | 821.50 | 834.50 | 879.75 | 1052.25 | 1102.00 | 1119.25 | 728.00 | 1190.00 | 2.46 | 2.50 |
| 2025 | 14 | 986.93 | 979.00 | 110.44 | 151.00 | 812.85 | 861.10 | 928.50 | 1079.50 | 1100.90 | 1121.75 | 755.00 | 1151.00 | 2.50 | 2.00 |
| 2026 | 21 | 977.86 | 939.00 | 91.92 | 105.00 | 879.00 | 893.00 | 914.00 | 1019.00 | 1107.00 | 1142.00 | 844.00 | 1203.00 | 3.10 | 3.00 |

Overall score percentiles:

| percentile | points |
|---|---|
| 5 | 730.60 |
| 10 | 764.10 |
| 25 | 830.75 |
| 50 | 896.50 |
| 75 | 990.00 |
| 90 | 1062.40 |
| 95 | 1106.35 |

High-impact cards (≥30 points) per deck:

| cards | decks |
|---|---|
| 1 | 45 |
| 2 | 58 |
| 3 | 45 |
| 4 | 17 |
| 5 | 5 |
| 6 | 3 |
| 11 | 1 |

Product-cohort contrasts:

| classification | count | mean | median | std | min | max |
|---|---|---|---|---|---|---|
| core_candidate_unverified | 130 | 898.38 | 886.00 | 119.55 | 646 | 1203 |
| game_changer_exception | 14 | 900.50 | 885.50 | 82.09 | 772 | 1079 |
| historical_nonlegal | 2 | 796.50 | 796.50 | 21.92 | 781 | 812 |
| premium_exception | 17 | 984.76 | 971.00 | 154.33 | 682 | 1412 |
| quality_exception | 1 | 739.00 | 739.00 | — | 739 | 739 |
| starter | 10 | 936.20 | 919.00 | 62.02 | 871 | 1063 |

Each precon is part of a finite observed archive, so its score is exact conditional on this configuration. Bootstrap intervals describe sensitivity to resampling cohorts, **not uncertainty in true card power**. Deck bootstraps assume sampled decks are exchangeable; yearly cluster bootstraps retain within-year dependence but have only 15 clusters. No causal or significance claim follows from a positive or negative time trend. Shared reprints, changing color mix, different product tiers and current Oracle text confound release-year comparisons. This analysis uses current text/legality for historical lists; it does not reconstruct historical play environments.

The largest adjacent annual median movements, including product mix changes, are:

| year | count | median | median_change |
|---|---|---|---|
| 2014 | 5 | 830.00 | 79.00 |
| 2018 | 4 | 829.50 | -45.50 |
| 2026 | 21 | 939.00 | -40.00 |
| 2025 | 14 | 979.00 | 36.00 |
| 2017 | 4 | 875.00 | 31.00 |

A composition regression of score on year, nonland mean mana value, GC count and land points is saved separately. It describes the scoring formula and deck mix, not independent causal predictors of wins. Annual role counts and mana values are in the deck CSV, allowing construction-based inspection without assuming creep beforehand.

## Independent validation and error analysis

The frozen holdout comes from Andy Zupke's published 2024 list: his five ordered favorites plus Science!, explicitly described as worst. Labels are **one author's assessments**, mixing quality and play experience; neither community consensus nor measured results. No coefficients or overrides were fitted to these outcomes. [Assessment source](https://cloudflare.edhrec.com/articles/the-best-commander-precons-of-2024).

| name | community_rank | model_points | model_rank |
|---|---|---|---|
| Mutant Menace | 1 | 728 | 6.00 |
| Animated Army | 2 | 1041 | 2.00 |
| Miracle Worker | 3 | 907 | 4.00 |
| Creative Energy | 4 | 1003 | 3.00 |
| Death Toll | 5 | 871 | 5.00 |
| Science! | 6 | 1056 | 1.00 |

Spearman rho -0.486; approximate two-sided p=0.329 is provided for completeness, with n=6 and selection bias making conventional significance inference unsuitable. Pair agreement 5/15. Validation failure must lead to review, not retrospectively fitting these decks and reporting them as holdouts. The Reddit original post supplies a second five-deck personal ordering; rho -0.600. It is a noisy restricted-range check, not a larger independent trial. Reddit commenters disagree; vote counts cannot substitute for outcomes.

Relevant qualitative context: r/CompetitiveEDH discussions emphasize efficient mana, tutors and interaction, supporting categories without supplying coefficients. EDHREC popularity is not a strength measurement. Commander Spellbook is a combo registry, useful for a separate gameplay audit rather than a synergy surcharge. TopDeck documents tournament data access but this run did not acquire a comparable Bracket 2/3 2HG outcome sample. Moxfield labels are user declarations and its retrieved shell did not furnish reliable validation data. [cEDH discussion](https://www.reddit.com/r/CompetitiveEDH/comments/1fj7zkd/); [Spellbook](https://commanderspellbook.com/about/); [TopDeck](https://topdeck.gg/docs/tournaments-v2).

Known failure modes:

* **Tribal and synergy decks:** standalone tribal enablers may get only a board role or base points while the deck performs very well. Explorers of the Deep, Mutant Menace and Cavalry Charge are diagnostic examples. This is partly intentional under the access-to-card-power philosophy; deck win ranking is therefore not the sole objective. Do not remedy this by taxing teammate synergy.
* **Efficient tutors/fast mana:** anchors correct Sol Ring, efficient tutors, mana rocks and dorks. Automatic regexes miss named mana symbols, indirect cost cheating or restricted tutors, and can mistake conditional text for reliable effects. Unknown/obscure cards do not get an automatic novelty premium; low provisional prices could nevertheless create a loophole. Require pre-league review of novel cards, rather than assume they are accurately priced.
* **Splashy spells:** discounting mana cost is directionally sensible, but alternative costs, discounts and free casting can make this excessive. Blasphemous Act is manually corrected. Cyclonic Rift is corrected for its split utility. Commander access and prepare costs are not modeled accurately.
* **Land quality:** basics contribute collectively; tapped fixing and premium lands have different points. Generic conditional-tap regexes may penalize lands that usually enter untapped. Fetch, shock, original dual, fast, battle and filter cycles need a full reviewed land taxonomy.
* **Engines and compact combos:** conditional draw phrases are not expected-card calculations; Thassa's Oracle's floor reflects combo risk rather than standalone body value. Game Changers are a policy signal, not a cardinal power scale. Infinite loops and locks require a separate gameplay policy regardless of points.
* **Archetype testing:** tribal, graveyard, spellslinger, artifact and energy strategies lack adequate independent labels. A small ranked sample cannot quantify systematic archetype bias. Published rank disagreement below is evidence to investigate, not proof of any deck's win rate.

Reviewed-versus-automatic discrepancies (largest absolute adjustments among cards appearing in precons):

| card_name | automatic_estimate | base_points | override_delta | notes |
|---|---|---|---|---|
| Deflecting Swat | 2 | 40 | 38 | Conditional free redirection. |
| Sol Ring | 29 | 65 | 36 | One mana for repeatable two-mana acceleration; large opening-hand advantage. |
| Mystic Remora | 26 | 60 | 34 | One-mana multiplayer draw engine, cumulative upkeep. |
| Toxic Deluge | 2 | 35 | 33 | Three-mana scalable toughness sweeper with life cost. |
| Flawless Maneuver | 2 | 30 | 28 | Conditional free creature protection. |
| Reanimate | 2 | 30 | 28 | One-mana graveyard-to-battlefield effect with life cost. |
| Mind Stone | 38 | 12 | -26 | Two-mana colorless rock with paid sacrifice draw. |
| Blasphemous Act | 2 | 25 | 23 | Often one-mana damage sweeper. |
| Commander's Sphere | 31 | 8 | -23 | Three-mana rock with sacrifice draw. |
| Deadly Rollick | 16 | 38 | 22 | Conditional free creature exile. |
| Wayfarer's Bauble | 29 | 9 | -20 | Three total mana split over turns for basic land ramp. |
| Farseek | 33 | 16 | -17 | Efficient typed land acceleration, tapped. |

These discrepancies identify extraction and functional-context problems. Overrides improve known cards but create uneven evidence coverage; most of the complete catalog remains low confidence.

## Sensitivity

Every feature weight, the GC floor, basic land allowance, mana decay and secondary-role credit was changed independently ±25%; absolute manual overrides stayed fixed. Integer rounding is applied again to every card. This isolates each parameter but understates uncertainty if manual anchors are wrong together. No year/deck normalization occurs.

| parameter | factor | median_score | median_absolute_change | max_absolute_change | spearman | max_rank_shift |
|---|---|---|---|---|---|---|
| acceleration | 0.75 | 863.50 | 33.00 | 91.00 | 0.99 | 29.00 |
| acceleration | 1.25 | 928.50 | 36.00 | 102.00 | 0.99 | 22.00 |
| advantage | 0.75 | 851.00 | 43.00 | 103.00 | 0.99 | 24.00 |
| advantage | 1.25 | 940.00 | 43.00 | 103.00 | 0.99 | 21.50 |
| tutor | 0.75 | 895.50 | 0.00 | 31.00 | 1.00 | 12.00 |
| tutor | 1.25 | 899.00 | 0.00 | 32.00 | 1.00 | 10.00 |
| interaction | 0.75 | 861.00 | 33.00 | 79.00 | 0.99 | 35.50 |
| interaction | 1.25 | 934.00 | 34.00 | 79.00 | 0.99 | 24.50 |
| board | 0.75 | 881.50 | 15.00 | 58.00 | 1.00 | 19.00 |
| board | 1.25 | 915.50 | 16.00 | 68.00 | 1.00 | 15.00 |
| game_changer_floor | 0.75 | 896.50 | 0.00 | 11.00 | 1.00 | 6.50 |
| game_changer_floor | 1.25 | 896.50 | 0.00 | 11.00 | 1.00 | 9.00 |
| basic_land | 0.75 | 896.50 | 0.00 | 0.00 | 1.00 | 0.00 |
| basic_land | 1.25 | 913.50 | 18.00 | 34.00 | 1.00 | 10.50 |
| efficiency_decay | 0.75 | 926.50 | 28.00 | 45.00 | 1.00 | 11.00 |
| efficiency_decay | 1.25 | 875.00 | 21.00 | 38.00 | 1.00 | 12.50 |
| second_role_fraction | 0.75 | 891.00 | 4.00 | 30.00 | 1.00 | 4.50 |
| second_role_fraction | 1.25 | 899.50 | 4.00 | 27.00 | 1.00 | 4.00 |

Card perturbations are also saved: increasing any single card by 10 adds exactly 10×its count to each deck containing it and zero to decks without it. A team adds both individual changes. No cross-deck term exists. Since Sol Ring is widespread, its absolute price often shifts totals more than ranks. Published sensitivity is conditional on the fixed manual set; before cap adoption also perturb manually reviewed engines and land cycles jointly.

## Twenty highest-scoring precons

| name | release_year | total_points | percentile | classification |
|---|---|---|---|---|
| From Cute to Brute | 2023 | 1412 | 100.00 | premium_exception |
| Multiverse Reforged | 2026 | 1203 | 99.43 | core_candidate_unverified |
| Peace Offering | 2024 | 1190 | 98.85 | core_candidate_unverified |
| Scions & Spellcraft (FINAL FANTASY XIV) | 2025 | 1151 | 98.28 | core_candidate_unverified |
| Witherbloom Pestilence | 2026 | 1142 | 97.70 | core_candidate_unverified |
| Most Wanted | 2024 | 1122 | 97.13 | core_candidate_unverified |
| Food and Fellowship | 2023 | 1114 | 96.55 | core_candidate_unverified |
| Squirreled Away | 2024 | 1111 | 95.98 | core_candidate_unverified |
| Goblin Storm | 2026 | 1107 | 95.40 | premium_exception |
| World Shaper | 2025 | 1106 | 94.83 | core_candidate_unverified |
| Eldrazi Incursion | 2024 | 1093 | 93.97 | premium_exception |
| Enduring Enchantments | 2023 | 1093 | 93.97 | premium_exception |
| Living Energy | 2025 | 1089 | 93.10 | core_candidate_unverified |
| Jeskai Striker | 2025 | 1085 | 92.53 | core_candidate_unverified |
| Family Matters | 2024 | 1084 | 91.95 | core_candidate_unverified |
| Timeless Wisdom | 2020 | 1079 | 91.38 | game_changer_exception |
| Revival Trance (FINAL FANTASY VI) | 2025 | 1063 | 90.52 | core_candidate_unverified |
| Token Triumph | 2022 | 1063 | 90.52 | starter |
| Doom Prevails | 2026 | 1061 | 89.66 | core_candidate_unverified |
| Hail, Caesar | 2024 | 1059 | 89.08 | core_candidate_unverified |

## Twenty lowest-scoring precons

| name | release_year | total_points | percentile | classification |
|---|---|---|---|---|
| Heavenly Inferno | 2011 | 646 | 0.57 | core_candidate_unverified |
| Nature of the Beast | 2013 | 648 | 1.15 | core_candidate_unverified |
| Devour for Power | 2011 | 651 | 1.72 | core_candidate_unverified |
| Breed Lethality | 2016 | 660 | 2.30 | core_candidate_unverified |
| Sliver Swarm | 2023 | 682 | 2.87 | premium_exception |
| Eternal Bargain | 2013 | 697 | 3.45 | core_candidate_unverified |
| Symbiotic Swarm | 2020 | 702 | 4.02 | core_candidate_unverified |
| Call for Backup | 2023 | 709 | 4.60 | core_candidate_unverified |
| Mutant Menace | 2024 | 728 | 5.17 | core_candidate_unverified |
| Draconic Dissent | 2022 | 732 | 5.75 | core_candidate_unverified |
| Upgrades Unleashed | 2022 | 739 | 6.32 | quality_exception |
| Forged In Stone | 2014 | 740 | 6.90 | core_candidate_unverified |
| Wade into Battle | 2015 | 748 | 7.47 | core_candidate_unverified |
| Mind Seize | 2013 | 751 | 8.05 | core_candidate_unverified |
| Silverquill Statement | 2021 | 753 | 8.62 | core_candidate_unverified |
| Counter Intelligence | 2025 | 755 | 9.20 | core_candidate_unverified |
| Necron Dynasties | 2022 | 762 | 10.06 | core_candidate_unverified |
| Draconic Rage | 2021 | 762 | 10.06 | core_candidate_unverified |
| Arm for Battle | 2020 | 769 | 10.92 | core_candidate_unverified |
| Mirror Mastery | 2011 | 772 | 11.78 | core_candidate_unverified |

## Representative deck breakdowns

### Counterpunch (2011)

Commander: Ghave, Guru of Spores. Product: Commander 2011. Total **951**, percentile 68.4; land contribution 96; high-impact cards 3; Game Changers 1; classification `game_changer_exception`. Nonland mean mana value 3.79. Reviewed cards contribute 146 points.

| card_name | count | points_each | points_total | section |
|---|---|---|---|---|
| Sol Ring | 1 | 65 | 65 | mainboard |
| Aura Shards | 1 | 45 | 45 | mainboard |
| Skullclamp | 1 | 40 | 40 | mainboard |
| Orzhov Signet | 1 | 29 | 29 | mainboard |
| Golgari Signet | 1 | 29 | 29 | mainboard |
| Selesnya Signet | 1 | 29 | 29 | mainboard |
| Awakening Zone | 1 | 28 | 28 | mainboard |
| Necrogenesis | 1 | 27 | 27 | mainboard |
| Golgari Guildmage | 1 | 26 | 26 | mainboard |
| Darksteel Ingot | 1 | 24 | 24 | mainboard |
| Acorn Catapult | 1 | 23 | 23 | mainboard |
| Doom Blade | 1 | 22 | 22 | mainboard |

Remaining 88 cards contribute 564 points. Full 100-card detail is in `deck_card_points.csv`. Role matches: acceleration 8, advantage 6, tutor 0, interaction 16, board 17. Role counts can overlap and are not independent contributions.

### Explorers of the Deep (2023)

Commander: Hakbal of the Surging Soul. Product: The Lost Caverns of Ixalan Commander. Total **859**, percentile 34.2; land contribution 101; high-impact cards 1; Game Changers 0; classification `core_candidate_unverified`. Nonland mean mana value 3.12. Reviewed cards contribute 146 points.

| card_name | count | points_each | points_total | section |
|---|---|---|---|---|
| Sol Ring | 1 | 65 | 65 | mainboard |
| Simic Signet | 1 | 29 | 29 | mainboard |
| Island | 13 | 2 | 26 | mainboard |
| Rapid Hybridization | 1 | 26 | 26 | mainboard |
| Benthic Biomancer | 1 | 26 | 26 | mainboard |
| Svyelun of Sea and Sky | 1 | 22 | 22 | mainboard |
| Stonybrook Banneret | 1 | 22 | 22 | mainboard |
| Sage of Fables | 1 | 22 | 22 | mainboard |
| Cold-Eyed Selkie | 1 | 22 | 22 | mainboard |
| Ravenform | 1 | 21 | 21 | mainboard |
| Explore | 1 | 20 | 20 | mainboard |
| Growth Spiral | 1 | 20 | 20 | mainboard |

Remaining 76 cards contribute 538 points. Full 100-card detail is in `deck_card_points.csv`. Role matches: acceleration 6, advantage 18, tutor 0, interaction 7, board 13. Role counts can overlap and are not independent contributions.

### Science! (2024)

Commander: Dr. Madison Li. Product: Fallout. Total **1056**, percentile 88.5; land contribution 131; high-impact cards 3; Game Changers 0; classification `core_candidate_unverified`. Nonland mean mana value 3.24. Reviewed cards contribute 196 points.

| card_name | count | points_each | points_total | section |
|---|---|---|---|---|
| Sol Ring | 1 | 65 | 65 | mainboard |
| Red Death, Shipwrecker | 1 | 38 | 38 | mainboard |
| Intelligence Bobblehead | 1 | 31 | 31 | mainboard |
| Thought Vessel | 1 | 29 | 29 | mainboard |
| Talisman of Progress | 1 | 29 | 29 | mainboard |
| Talisman of Creativity | 1 | 29 | 29 | mainboard |
| Talisman of Conviction | 1 | 29 | 29 | mainboard |
| Everflowing Chalice | 1 | 29 | 29 | mainboard |
| Dr. Madison Li | 1 | 28 | 28 | commander |
| Endurance Bobblehead | 1 | 28 | 28 | mainboard |
| Curie, Emergent Intelligence | 1 | 26 | 26 | mainboard |
| Swords to Plowshares | 1 | 25 | 25 | mainboard |

Remaining 88 cards contribute 670 points. Full 100-card detail is in `deck_card_points.csv`. Role matches: acceleration 17, advantage 15, tutor 0, interaction 11, board 8. Role counts can overlap and are not independent contributions.

### Mutant Menace (2024)

Commander: The Wise Mothman. Product: Fallout. Total **728**, percentile 5.2; land contribution 135; high-impact cards 1; Game Changers 0; classification `core_candidate_unverified`. Nonland mean mana value 3.56. Reviewed cards contribute 142 points.

| card_name | count | points_each | points_total | section |
|---|---|---|---|---|
| Sol Ring | 1 | 65 | 65 | mainboard |
| Talisman of Resilience | 1 | 29 | 29 | mainboard |
| Talisman of Dominance | 1 | 29 | 29 | mainboard |
| Talisman of Curiosity | 1 | 29 | 29 | mainboard |
| Strength Bobblehead | 1 | 24 | 24 | mainboard |
| Harold and Bob, First Numens | 1 | 24 | 24 | mainboard |
| Jason Bright, Glowing Prophet | 1 | 22 | 22 | mainboard |
| Contaminated Drink | 1 | 20 | 20 | mainboard |
| Struggle for Project Purity | 1 | 19 | 19 | mainboard |
| Guardian Project | 1 | 19 | 19 | mainboard |
| Atomize | 1 | 19 | 19 | mainboard |
| Putrefy | 1 | 18 | 18 | mainboard |

Remaining 88 cards contribute 411 points. Full 100-card detail is in `deck_card_points.csv`. Role matches: acceleration 10, advantage 10, tutor 1, interaction 4, board 6. Role counts can overlap and are not independent contributions.

### Token Triumph (2022)

Commander: Emmara, Soul of the Accord. Product: Starter Commander Decks. Total **1063**, percentile 90.5; land contribution 105; high-impact cards 4; Game Changers 0; classification `starter`. Nonland mean mana value 3.56. Reviewed cards contribute 116 points.

| card_name | count | points_each | points_total | section |
|---|---|---|---|---|
| Sol Ring | 1 | 65 | 65 | mainboard |
| Karametra's Favor | 1 | 38 | 38 | mainboard |
| Dawn of Hope | 1 | 31 | 31 | mainboard |
| Idol of Oblivion | 1 | 31 | 31 | mainboard |
| Forest | 15 | 2 | 30 | mainboard |
| Talisman of Unity | 1 | 29 | 29 | mainboard |
| Avacyn's Pilgrim | 1 | 29 | 29 | mainboard |
| Jaspera Sentinel | 1 | 29 | 29 | mainboard |
| Leafkin Druid | 1 | 29 | 29 | mainboard |
| Plains | 14 | 2 | 28 | mainboard |
| Aura Mutation | 1 | 26 | 26 | mainboard |
| Rishkar, Peema Renegade | 1 | 24 | 24 | mainboard |

Remaining 61 cards contribute 674 points. Full 100-card detail is in `deck_card_points.csv`. Role matches: acceleration 13, advantage 12, tutor 0, interaction 9, board 27. Role counts can overlap and are not independent contributions.

### Multiverse Reforged (2026)

Commander: Jace, Multiverse Architect. Product: Reality Fracture Commander. Total **1203**, percentile 99.4; land contribution 171; high-impact cards 6; Game Changers 0; classification `core_candidate_unverified`. Nonland mean mana value 4.05. Reviewed cards contribute 182 points.

| card_name | count | points_each | points_total | section |
|---|---|---|---|---|
| Sol Ring | 1 | 65 | 65 | mainboard |
| Currency Converter | 1 | 38 | 38 | mainboard |
| Martial Coup | 1 | 31 | 31 | mainboard |
| Staff of the Storyteller | 1 | 31 | 31 | mainboard |
| White Sun's Twilight | 1 | 31 | 31 | mainboard |
| Flawless Maneuver | 1 | 30 | 30 | mainboard |
| Izzet Signet | 1 | 29 | 29 | mainboard |
| Dimir Signet | 1 | 29 | 29 | mainboard |
| Azorius Signet | 1 | 29 | 29 | mainboard |
| Rakdos Signet | 1 | 29 | 29 | mainboard |
| Talisman of Creativity | 1 | 29 | 29 | mainboard |
| Talisman of Dominance | 1 | 29 | 29 | mainboard |

Remaining 88 cards contribute 803 points. Full 100-card detail is in `deck_card_points.csv`. Role matches: acceleration 16, advantage 12, tutor 0, interaction 12, board 20. Role counts can overlap and are not independent contributions.

## Experimental banned-card evaluation

The separate worksheet contains every named ban matched to Oracle plus Oracle category-banned cards and Lutri's companion restriction. All 42 individually named bans, including the seven requested cards, have individual functional and 2HG assessments grounded in current Oracle text. Price magnitudes remain analyst policy priors. Generic unreviewed category-ban rows are explicitly low-confidence reserves, not researched final prices; they default to retaining the ban. Proposed points are separate hypothetical testing values and **never change legality or the main model**. A 100-point allowance cannot make collusive draw, early locks, non-game mechanics or explosive opening mana appropriate. Prophet's untap count differs in shared turns; Dockside counts only opposing permanents; Trade Secrets can target a teammate. These require distinct testing protocols.

## Recommendations before a strict cap

1. Use this build to shadow-score league decks and inspect cheap automatic cards, keeping overrides versioned. Review lands and prepare/modal cards first, then fast mana, tutors, free spells and engines.
2. Gather a preregistered, independently labeled deck sample spanning Core and Upgraded. Include low/high standalone strength and low/high synergy separately. Do not train and evaluate on the same decks.
3. Record turn of first credible win attempt, mulligans, seats, pilots, archetypes, teammate pairings and game length. Use mixed-effects or matched analyses to distinguish card access, pilots and synergy; do not turn the teammate synergy estimate into a budget surcharge.
4. Fit only coefficients supported by the data, with shrinkage and out-of-sample validation. Obtain uncertainty for card values, not only archive medians. Many cards will remain weakly identified.
5. Keep ban legality and combo/lock policy separate from card totals. Establish commander-access adjustments only after dedicated tests. Validate a global unit conversion against actual Bracket 3 decks before treating 1,000 points as an empirical average.

The result is a reproducible precon index and an editable calculator. It is not yet an accurate cardinal calibration of Core or Upgraded power, and a strict 2,000-point team cap would be premature.

## Source ledger

| key | url | retrieved | status |
|---|---|---|---|
| kamigawa_erratum | https://magic.wizards.com/en/news/feature/kamigawa-neon-dynasty-commander-decklists-2022-02-07 | 2026-10-19T21:44:16.909434+00:00 | downloaded |
| foundations | https://magic.wizards.com/en/news/announcements/foundations-commander-decklists | 2026-10-19T21:44:17.403438+00:00 | downloaded |
| october_bans | https://www.magic.wizards.com/en/news/announcements/banned-and-restricted-october-12-2026 | 2026-10-19T21:44:18.162063+00:00 | downloaded |
| bulk_index | https://api.scryfall.com/bulk-data | 2026-10-19T21:34:27.479238+00:00 | downloaded |
| mtg_decklist | https://mtgjson.com/api/v5/DeckList.json | 2026-10-19T21:34:27.689315+00:00 | downloaded |
| mtg_all_decks | https://mtgjson.com/downloads/all-decks/ | 2026-10-19T21:35:41.731564+00:00 | downloaded |
| brackets_2025 | https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-october-21-2025 | 2026-10-19T21:35:42.394984+00:00 | downloaded |
| brackets_2026 | https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-february-9-2026 | 2026-10-19T21:35:42.954613+00:00 | downloaded |
| banned | https://magic.wizards.com/en/banned-restricted-list | 2026-10-19T21:35:43.115183+00:00 | downloaded |
| two_headed | https://magic.wizards.com/en/formats/two-headed-giant | 2026-10-19T21:35:43.789719+00:00 | downloaded |
| rules | https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt | 2026-10-19T21:35:44.078383+00:00 | downloaded |
| edhrec_validation | https://cloudflare.edhrec.com/articles/the-best-commander-precons-of-2024 | 2026-10-19T21:35:44.228321+00:00 | downloaded |
| reddit_validation | https://www.reddit.com/r/EDH/comments/1eetahl/redhs_best_precon_commanders_of_all_time/ | 2026-10-19T21:35:44.377845+00:00 | access_challenge_or_empty |
| cedh_context | https://www.reddit.com/r/CompetitiveEDH/comments/1fj7zkd/ | 2026-10-19T21:35:44.450206+00:00 | access_challenge_or_empty |
| spellbook | https://commanderspellbook.com/about/ | 2026-10-19T21:35:44.786861+00:00 | downloaded |
| topdeck | https://topdeck.gg/docs/tournaments-v2 | 2026-10-19T21:35:45.115358+00:00 | downloaded |
| moxfield_example | https://moxfield.com/decks/0GMkJIsGM0qNsSesov9A1g | 2026-10-19T21:35:45.317928+00:00 | application_shell_no_deck |
| oracle_cards | https://data.scryfall.io/oracle-cards/oracle-cards-20261019210228.jsonl.gz | 2026-10-19T21:34:50.669867+00:00 | downloaded |
| taw | https://github.com/taw/magic-preconstructed-decks-data | 2026-10-19T21:44:18.342056+00:00 | pinned git |
