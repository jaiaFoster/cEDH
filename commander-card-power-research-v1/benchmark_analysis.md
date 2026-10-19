# Executed benchmark analysis
Research and snapshot date: 2026-10-19. No values were fitted to reviewer labels. Baseline files remain unchanged.

## Coverage and score meaning
The frozen baseline has 174 decks and 6,429 distinct Oracle IDs. Nine methods/controls were executed, producing 1,566 deck-method rows. A complete score is emitted only when all 100 entries have a defined value. Incomplete methods retain a diagnostic known-card subtotal and a blank score.

The published cache contains 32,075 names. It matches 32,171 cards in the frozen Oracle snapshot, including 6,394 precon IDs. Unique first-face aliases resolve the two meld cards; all other missing ratings remain missing. It fully scores 164 decks and leaves 10 incomplete. The 35 missing precon IDs are listed in data/missing_precon_ratings.csv. Coverage gaps include older AFR cards, banned cards and newer products: they are not merely recency gaps.

Among its 164 complete decks, the raw cache has median **5350.0**, mean 5343.90, sample SD 380.02, IQR 499.75, and range 4219–6247. These are sums of source 0–100 judgments, not calibrated league points. No 1,000-point anchor, per-deck normalization or per-year normalization was used. The median subtotal including incomplete decks is 5344.0; it must not be confused with the complete-deck median.

The Canlander and Game Changer controls define unlisted cards as zero by policy. That definition is different from assuming that an unknown external rating is zero. Creature and adoption subtotals do not yield a complete deck-price model.

## External opinion comparisons
| method | complete decks | EDHREC n | EDHREC rho | EDHREC tau | EDHREC pair accuracy | Reddit n | Reddit rho | Reddit tau | Reddit pair accuracy | new pair accuracy | new complete pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_v02 | 174 | 6 | -0.486 | -0.333 | 0.333 | 5 | -0.600 | -0.400 | 0.300 | 0.200 | 5 |
| canlander | 174 | 6 | -0.393 | -0.346 | 0.400 | 5 | — | — | 0.500 | 0.600 | 5 |
| official_gc | 174 | 6 | -0.131 | -0.115 | 0.467 | 5 | 0.707 | 0.632 | 0.700 | 0.400 | 5 |
| xmage_card_adapter | 174 | 6 | 0.257 | 0.200 | 0.600 | 5 | 0.400 | 0.400 | 0.700 | 0.400 | 5 |
| adoption_log_proxy | 0 | 0 | — | — | — | 0 | — | — | — | — | 0 |
| expert_flag_votes | 174 | 6 | -0.414 | -0.365 | 0.367 | 5 | 0.707 | 0.632 | 0.700 | 0.500 | 5 |
| creature_published_partial | 0 | 0 | — | — | — | 0 | — | — | — | — | 0 |
| zarzak_cached_llm | 164 | 6 | 0.200 | 0.067 | 0.533 | 4 | 0.400 | 0.333 | 0.667 | 0.800 | 5 |
| zarzak_basic_equalized | 164 | 6 | -0.029 | 0.067 | 0.533 | 4 | 0.400 | 0.333 | 0.667 | 0.600 | 5 |

Higher scores are compared to lower reviewer rank numbers. Pair accuracy gives ties half credit. The EDHREC sample contains six decks, the original Reddit sample five. For the cached source only four Reddit decks are complete: Exit from Exile is missing Danse Macabre. Its reported +0.400 is therefore a four-deck result and is not directly comparable to another method's five-deck +0.400. The preliminary +0.300 using five partial subtotals is explicitly superseded and is not a valid full-coverage result.

Added evaluation: five within-year pairs (2021–2025), ten decks, from Josh Nelson's [best](https://edhrec.com/articles/the-five-best-commander-precons-of-the-last-five-years) and [worst](https://cloudflare.edhrec.com/articles/the-five-worst-commander-precons-of-the-last-five-years) articles. They are not one ten-deck ordering. Theme/value and power are mixed in editorial assessments, and different reviewers disagree. These pairs were frozen before acquiring the new cache; no weights or individual prices were optimized on them. Public reviews could nevertheless be represented in an LLM's training, so strict training-set independence cannot be established.

| stronger | weaker | difference | credit | complete |
| --- | --- | --- | --- | --- |
| Elven Empire | Spirit Squadron | 87.000 | 1.000 | True |
| Necron Dynasties | Painbow | -565.000 | 0.000 | True |
| Eldrazi Unbound | Virtue and Valor | 59.000 | 1.000 | True |
| Endless Punishment | Deadly Disguise | 539.000 | 1.000 | True |
| Limit Break (FINAL FANTASY VII) | Living Energy | 174.000 | 1.000 | True |

Four/five is promising but weak evidence: one changed opinion changes accuracy by 20 percentage points. It is not a win-rate estimate or statistically established superiority. The raw cache still puts Painbow 565 points above Necron Dynasties.

## Bootstrap and sample sensitivity
Paired deck bootstrap, 1,500 resamples, seed 20261019, percentile intervals. Degenerate resamples are omitted. Small samples, ties and repeated observations make these intervals unstable; they describe conditional opinion-sample variation, not actual competitive strength uncertainty. In sparse controls, even an apparently one-sided interval is driven by very few score levels.

| method | sample | n | bootstrap95 rho |
| --- | --- | --- | --- |
| baseline_v02 | edhrec6 | 6 | [-1.0, 1.0] |
| baseline_v02 | reddit5 | 5 | [-1.0, 1.0] |
| canlander | edhrec6 | 6 | [-0.9486832980505139, 0.1391216687280505] |
| canlander | reddit5 | 5 | None |
| official_gc | edhrec6 | 6 | [-0.9332565252573828, 0.44721359549995804] |
| official_gc | reddit5 | 5 | [0.7071067811865475, 1.0] |
| xmage_card_adapter | edhrec6 | 6 | [-1.0, 1.0] |
| xmage_card_adapter | reddit5 | 5 | [-0.8749999999999999, 1.0] |
| adoption_log_proxy | edhrec6 | 0 | not estimated |
| adoption_log_proxy | reddit5 | 0 | not estimated |
| expert_flag_votes | edhrec6 | 6 | [-0.9486832980505139, 0.4647580015448901] |
| expert_flag_votes | reddit5 | 5 | [0.7071067811865475, 1.0] |
| creature_published_partial | edhrec6 | 0 | not estimated |
| creature_published_partial | reddit5 | 0 | not estimated |
| zarzak_cached_llm | edhrec6 | 6 | [-1.0, 0.92] |
| zarzak_cached_llm | reddit5 | 4 | [-1.0, 1.0] |
| zarzak_basic_equalized | edhrec6 | 6 | [-1.0, 1.0] |
| zarzak_basic_equalized | reddit5 | 4 | [-1.0, 1.0] |

Leave-one-out rank ranges are in data/sample_sensitivity.csv. The validation samples share some products; do not sum pair counts as independent games. No standardized Commander outcome dataset or 2HG outcome dataset was obtained. Archetype conclusions are individual error cases, not powered subgroup estimates.

## Required difficult cases
| deck | baseline_v02 | xmage_card_adapter | zarzak_cached_llm | zarzak_basic_equalized | zarzak_cached_llm_covered_cards |
| --- | --- | --- | --- | --- | --- |
| Mutant Menace | 728 | 252 | 5355 | 5205 | 100 |
| Science! | 1056 | 222 | 5354 | 5434 | 100 |
| Explorers of the Deep | 859 | 231 | 5482 | 5412 | 100 |
| Necron Dynasties | 762 | 211 | 5228 | 4628 | 100 |
| From Cute to Brute | 1412 | 271 | 6247 | 6217 | 100 |

Mutant Menace and Science! differ by only one raw-cache point despite their large gap in one reviewer ordering. Tribal/synergy-driven Necron Dynasties remains underrated by the added review comparison. Explorers of the Deep also demonstrates why synergistic tribal performance need not be captured by individual standalone prices. From Cute to Brute is the highest complete raw-cache deck, which may partly reflect individual staples and nonbasic mana rather than coherent deck performance. The league intentionally permits synergy to exceed its construction price; these errors are relevant without implying a synergy surcharge is desirable.

## A disqualifying card-level consistency problem
| name | zarzak_cached_llm | zarzak_basic_equalized |
| --- | --- | --- |
| Wastes | 30.000 | 30.000 |
| Swamp | 50.000 | 30.000 |
| Mountain | 10.000 | 30.000 |
| Island | 30.000 | 30.000 |
| Forest | 40.000 | 30.000 |
| Plains | 30.000 | 30.000 |

Thirty Swamps versus thirty Mountains differ by **1,200 raw points**, far more than one Sol Ring at 98. These prices cannot be deployed without review. The equalized-basic control fixes rated basics at 30 globally as an explicit color-neutral assumption. It is a sensitivity diagnostic, not an empirically fitted or accepted replacement. Snow/other basic lands also use the same rule when rated; missing cards remain missing.

Basic equalization changes the six-deck Spearman from +0.200 to -0.029 and added-pair accuracy from 4/5 to 3/5. The seemingly better raw result is therefore sensitive to an implausible land convention. This does not establish a causal explanation for every ranking error, but it weakens any claim that 4/5 validates the source. Summing an anchored 0–100 judgment scale also assumes cardinal differences and additivity; those assumptions have not been outcome-calibrated.

Land points are not neglected by the cache: median collective land fraction is 0.319 among complete decks. Detailed contributions are in data/land_contributions.csv. A large land share alone is not evidence of correct land pricing. Source values also omit Dockside Extortionist, Jeweled Lotus, Primeval Titan and Prophet of Kruphix; those remain missing, never silently legal or zero.

## Historical behavior
Statistics below use complete raw-cache decks only. Counts show both total cohort size and complete coverage. Missingness can bias recent and older comparisons. Release year is explanatory, never a card-price modifier. Same Oracle ID always keeps the same source value.

| year | n | mean | median | sd | p10 | p25 | p75 | p90 | iqr | complete_decks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2011 | 5 | 4892.000 | 4844.000 | 288.726 | 4647.400 | 4673.500 | 5062.500 | 5175.000 | 389.000 | 4 |
| 2013 | 5 | 4628.000 | 4653.000 | 155.995 | 4472.000 | 4475.000 | 4710.000 | 4783.200 | 235.000 | 5 |
| 2014 | 5 | 4900.400 | 4774.000 | 530.722 | 4412.200 | 4702.000 | 5179.000 | 5448.400 | 477.000 | 5 |
| 2015 | 5 | 5004.800 | 5039.000 | 377.350 | 4639.000 | 4930.000 | 5119.000 | 5342.200 | 189.000 | 5 |
| 2016 | 5 | 5419.000 | 5402.000 | 251.636 | 5163.400 | 5308.000 | 5631.000 | 5664.600 | 323.000 | 5 |
| 2017 | 4 | 5312.500 | 5312.500 | 81.226 | 5237.600 | 5252.000 | 5373.000 | 5387.400 | 121.000 | 4 |
| 2018 | 4 | 4961.500 | 5004.500 | 197.509 | 4766.200 | 4853.500 | 5112.500 | 5122.400 | 259.000 | 4 |
| 2019 | 4 | 5112.333 | 5120.000 | 296.574 | 4873.600 | 4966.000 | 5262.500 | 5348.000 | 296.500 | 3 |
| 2020 | 9 | 5193.778 | 5240.000 | 216.524 | 4936.600 | 5036.000 | 5340.000 | 5426.400 | 304.000 | 9 |
| 2021 | 15 | 5174.000 | 5144.000 | 104.305 | 5048.000 | 5131.000 | 5254.000 | 5317.000 | 123.000 | 11 |
| 2022 | 25 | 5364.917 | 5425.500 | 361.575 | 4915.400 | 5049.750 | 5647.750 | 5820.300 | 598.000 | 24 |
| 2023 | 27 | 5424.926 | 5420.000 | 280.118 | 5161.000 | 5226.000 | 5587.000 | 5708.400 | 361.000 | 27 |
| 2024 | 26 | 5586.885 | 5694.000 | 268.498 | 5213.000 | 5354.250 | 5758.500 | 5909.000 | 404.250 | 26 |
| 2025 | 14 | 5749.167 | 5715.500 | 245.355 | 5459.500 | 5608.750 | 5991.250 | 6000.100 | 382.500 | 12 |
| 2026 | 21 | 5374.950 | 5439.500 | 396.362 | 4881.000 | 5245.000 | 5572.000 | 5730.500 | 327.000 | 20 |

All method/cohort statistics are in data/annual_distributions.csv. The baseline's annual medians run from 772 in 2011 to 939 in 2026, but a flawed price model cannot establish actual power creep. Neither this trajectory nor the external cache proves a change in observed win probability. Product composition, land pricing, identity coverage and source bias require resolution before interpreting cohort trends causally.

## Exact price sensitivity
Among complete raw-cache decks, adjust one globally fixed price by ±20, recompute totals, and compare ranks. No deck-specific normalization or refitting is performed.

| card | price_delta | affected_decks | maximum_deck_delta | complete_decks | spearman_to_original | strict_pair_reversals |
| --- | --- | --- | --- | --- | --- | --- |
| Sol Ring | -20 | 163 | 20.000 | 164 | 1.000 | 0 |
| Sol Ring | 20 | 163 | 20.000 | 164 | 1.000 | 2 |
| Command Tower | -20 | 150 | 20.000 | 164 | 1.000 | 34 |
| Command Tower | 20 | 150 | 20.000 | 164 | 1.000 | 21 |
| Temple of the False God | -20 | 63 | 20.000 | 164 | 0.999 | 100 |
| Temple of the False God | 20 | 63 | 20.000 | 164 | 0.999 | 91 |
| Arcane Signet | -20 | 122 | 20.000 | 164 | 1.000 | 65 |
| Arcane Signet | 20 | 122 | 20.000 | 164 | 1.000 | 51 |

Near-universal Sol Ring provides almost no information about its relative coefficient from precon totals alone. A team or deck interaction premium is absent throughout. Stability under a staple edit does not validate the underlying prices. The basic-land control is a stronger structural perturbation than a small staple edit.

## Additive inverse problem: executed chronological holdout
Matrix rank 174; nullity at least 6,255; 4,382 one-deck cards; 317 multi-card identical-column groups containing 4,766 cards. We cannot recover unique individual prices from these totals.

Ridge labels below are permitted raw-cache additive sums, not a hosted evaluator or independent power measurement. Train through 2023, test complete 2024–2026 decks. Alpha values are declared diagnostic settings; none is chosen using reviewer labels.

| method | alpha | training_decks | held_out_decks | held_out_mae | held_out_spearman | negative_coefficients | purpose |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_zero_prior | 0.100 | 106 | 58 | 1162.081 | -0.089 | 1615 | emulation identifiability diagnostic; labels are known card-score sums |
| ridge_zero_prior | 10.000 | 106 | 58 | 1207.856 | -0.126 | 1589 | emulation identifiability diagnostic; labels are known card-score sums |
| ridge_zero_prior | 1000.000 | 106 | 58 | 2204.050 | -0.391 | 1029 | emulation identifiability diagnostic; labels are known card-score sums |

Poor future-deck emulation and many negative coefficients illustrate the problem even when the labels were generated by a truly additive function. Ridge is not promoted to card prices. NNLS/nonnegative priors could constrain signs but cannot eliminate the null space. Nonlinear external evaluators would add another approximation error.

## Highest and lowest complete source totals
These are rankings under the raw source, not claims of actual strongest/weakest decks.

### Highest 20
| deck | release_year | score |
| --- | --- | --- |
| From Cute to Brute | 2023 | 6247.000 |
| Jeskai Striker | 2025 | 6163.000 |
| Odds and Ends | 2026 | 6049.000 |
| Urza's Iron Alliance | 2022 | 6019.000 |
| Most Wanted | 2024 | 6008.000 |
| Sultai Arisen | 2025 | 6001.000 |
| Scions & Spellcraft (FINAL FANTASY XIV) | 2025 | 5992.000 |
| Mardu Surge | 2025 | 5991.000 |
| Graveyard Overdrive | 2024 | 5974.000 |
| Witherbloom Pestilence | 2026 | 5969.000 |
| Grand Larceny | 2024 | 5920.000 |
| Squirreled Away | 2024 | 5898.000 |
| Obscura Operation | 2022 | 5856.000 |
| Miracle Worker | 2024 | 5836.000 |
| Mishra's Burnished Banner | 2022 | 5832.000 |
| Death Toll | 2024 | 5821.000 |
| Painbow | 2022 | 5793.000 |
| Blood Rites | 2023 | 5791.000 |
| Enduring Enchantments | 2023 | 5781.000 |
| Revenant Recon | 2024 | 5763.000 |

### Lowest 20
| deck | release_year | score |
| --- | --- | --- |
| Built From Scratch | 2014 | 4219.000 |
| Reign of Dragons | 2026 | 4420.000 |
| Wade into Battle | 2015 | 4445.000 |
| Nature of the Beast | 2013 | 4470.000 |
| Power Hungry | 2013 | 4475.000 |
| Heavenly Inferno | 2011 | 4630.000 |
| Eternal Bargain | 2013 | 4653.000 |
| Mirror Mastery | 2011 | 4688.000 |
| Draconic Destruction | 2022 | 4690.000 |
| Peer Through Time | 2014 | 4702.000 |
| Exquisite Invention | 2018 | 4708.000 |
| Mind Seize | 2013 | 4710.000 |
| Goblin Storm | 2026 | 4773.000 |
| Forged In Stone | 2014 | 4774.000 |
| Divine Convocation | 2023 | 4782.000 |
| Merciless Rage | 2019 | 4812.000 |
| Evasive Maneuvers | 2013 | 4832.000 |
| Arm for Battle | 2020 | 4835.000 |
| Keen Engineering | 2026 | 4893.000 |
| Calling All Angels | 2026 | 4896.000 |

## Decision
Keep the baseline and original calculator intact. The published cache saves substantial initial annotation work, but basic-land inconsistencies, missing cards and weak/conflicting validation prevent direct adoption. Use it as a reviewable prior, not a mathematical proof of relative power. Expand independent unseen deck/pod evidence before a strict cap. The additive-only design has a structural gap from holistic deck strength that is consistent with the league's chosen philosophy; no numerical ceiling on agreement can be estimated from these samples.
