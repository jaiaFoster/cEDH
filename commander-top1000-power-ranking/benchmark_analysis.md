# Candidate schedule benchmark

All174 archived precons were scored at fixed Oracle-ID prices, including their separate command zones. They are official product lists, not automatically all Bracket2. Precon guidance was decoupled from Bracket2, and current Game Changer/ban status is preserved separately.

| cohort | deck_count | median | p10 | p90 | mean | std | unique_totals | median_pointed_cards |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| official_precons | 174 | 13.000 | 12.000 | 17.000 | 14.029 | 2.639 | 14 | 2.000 |
| cedh_holdout | 2520 | 169.000 | 96.900 | 254.000 | 171.222 | 53.820 | 228 | 44.000 |
| bracket3_declared | 150 | 42.000 | 15.000 | 83.300 | 46.013 | 26.448 | 76 | 11.500 |

Of174 precons,171 pass this backend's current basic legality checks. Flags are reported rather than dropping historical products:

| deck_name | legality_flags |
| --- | --- |
| Political Puppets | official_commander_illegal:Trade Secrets |
| Mystic Intellect | official_commander_illegal:Dockside Extortionist |
| Upgrades Unleashed | singleton_limit:Mossfire Valley |

The precon median is concentrated in ubiquitous Sol Ring; the median top-three contribution share is100%. There are only 14 distinct precon totals. This is consistent with sparse resource pricing but a poor tool for ranking synergy-driven precon effectiveness.

## Existing reviewer diagnostics

| source | n | spearman | kendall | pairwise_ties_half_credit | bootstrap_rho_p025 | bootstrap_rho_p975 | independence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| validation.csv | 6 | -0.802 | -0.701 | 0.200 | -1.000 | 0.000 | reused diagnostic, not untouched validation; only four-player reviewer opinions |
| reddit_validation.csv | 5 | 0.154 | 0.105 | 0.550 | -1.000 | 1.000 | reused diagnostic, not untouched validation; only four-player reviewer opinions |

Six-deck assessment source: https://cloudflare.edhrec.com/articles/the-best-commander-precons-of-2024 . Five-deck assessment source: https://www.reddit.com/r/EDH/comments/1eetahl/redhs_best_precon_commanders_of_all_time/ . These are existing cached opinions, not win records. Tie credit is one half in pairwise accuracy. No improvement is claimed when a tiny diagnostic fails. Five previously inspected comparative pairs give accuracy 0.500; full cases are in analysis_summary.json.

## Difficult representative cases

| deck_name | total_points | command_zone_points | pointed_card_count | top3_point_share |
| --- | --- | --- | --- | --- |
| From Cute to Brute | 19 | 1 | 4 | 0.947 |
| Necron Dynasties | 12 | 0 | 1 | 1.000 |
| Explorers of the Deep | 12 | 0 | 1 | 1.000 |
| Mutant Menace | 12 | 0 | 1 | 1.000 |
| Science! | 13 | 0 | 2 | 1.000 |

Mutant Menace, Explorers and Necrons can be strong through synergy that the budget intentionally leaves uncharged. Science! being tied with or above them is a known resource-score/holistic-strength discrepancy, not concealed evidence of a successful power predictor.

## Historical fixed-price trend

| release_year | count | mean | median | std | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| 2011 | 5 | 14.200 | 15.000 | 1.095 | 13 | 15 |
| 2013 | 5 | 13.200 | 12.000 | 2.168 | 12 | 17 |
| 2014 | 5 | 14.000 | 13.000 | 2.550 | 12 | 18 |
| 2015 | 5 | 12.800 | 12.000 | 1.304 | 12 | 15 |
| 2016 | 5 | 17.400 | 16.000 | 3.578 | 13 | 22 |
| 2017 | 4 | 17.750 | 17.500 | 5.315 | 12 | 24 |
| 2018 | 4 | 12.250 | 12.000 | 0.500 | 12 | 13 |
| 2019 | 4 | 14.250 | 14.000 | 2.630 | 12 | 17 |
| 2020 | 9 | 14.556 | 13.000 | 3.127 | 12 | 21 |
| 2021 | 15 | 12.400 | 12.000 | 0.632 | 12 | 14 |
| 2022 | 25 | 13.080 | 13.000 | 3.040 | 1 | 17 |
| 2023 | 27 | 14.185 | 14.000 | 1.902 | 12 | 19 |
| 2024 | 26 | 14.385 | 13.000 | 2.886 | 12 | 25 |
| 2025 | 14 | 14.714 | 14.000 | 2.494 | 12 | 20 |
| 2026 | 21 | 14.238 | 14.000 | 2.119 | 12 | 20 |

Year is not an input to card prices. Small annual cohorts and uneven product selection prevent a simple causal power-creep claim. Detailed distributions, quota sensitivities, no-floor checks, external labelled cohorts and versioned prices are in the CSV outputs. Original v0.2 and v1 research remain untouched for comparison.

## Data access, exclusions and generalization

TopDeck.gg attribution: https://topdeck.gg . Existing manifest entries=1472; eligible name/date/size/pod event candidates=701. Training registrations=7906; holdout registrations=2628, deduplicated lists=2520; declared-B3 registrations=151, lists=150. Missing structured decks and unresolved/not100 records are excluded with exact counts in analysis_summary.json. No synthetic placeholder-ID repository deck was treated as an empirical sample.

Holdout means October lists were excluded from frequency nomination data. No weights were trained on tournament outcomes. Deck identities can recur across time; deduplication is within cohort, so this is not a commander/archetype-isolated predictive holdout. Missing decks, submitted-list quality and event selection create selection bias. No reliable intermediate 'upgraded precon/high-power/optimized' labelled cohorts were verified; the available B3 declarations cannot fill that gap. No 2HG match outcomes were obtained.

## Initial league test

Use the candidate schedule only after reviewing current legality, the high-priority queue and actual team lists. Preserve zero teammate/in-deck synergy premiums, but adjudicate controller-specific combos and team-turn locks independently. A construction budget cannot make intrinsically unacceptable play patterns acceptable.

## Event-label outlier and review feedback

The lowest-cost cEDH-labelled registration is an intentionally weak-looking Dosan list with68 basic Forests and many inefficient cards, rather than an optimized competitive benchmark. It was retained rather than removed using the model score. This directly limits interpretation of event labels. Interchangeable-name repair recovered a few legitimate source lists; the exact final counts above supersede exploratory in-memory counts. Card assessments were revised following this audit, so these distributions are descriptive, not a blinded final outcome test.
