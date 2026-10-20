# Point cutoff experiments

Recommendation: test the active tiered policy with main threshold >75 and command-zone threshold >75 as a versioned candidate schedule, not a strict validated cap. It selects 287 main-deck cards and 90 command-zone options (339 identities in their union, including hypothetical banned cards). The currently Commander-legal and 2HG-legal portion contains 304 identities (252 main and 84 command-zone). No convincing empirical natural break was demonstrated. The specialist floor and coarse source priors create artificial concentrations; they cannot justify a natural threshold.

The policy separates exceptional resource access from ordinary utility and leaves most known cards free. Top50–100 policies leave many efficient specialist engines free and collapse most precons to Sol Ring alone. Top750–1,000 policies reach unreviewed source priors and inflate apparent precision. The middle range is a policy tradeoff, not an optimum inferred from precon separation.

## Rank-quota policies (all ties included)

| policy | main_threshold | main_pointed_cards | pointed_commander_options | median | p10 | p90 | unique_totals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rank_50_include_ties | 86.250 | 50 | 14 | 5.000 | 5.000 | 5.000 | 4 |
| rank_100_include_ties | 81.750 | 108 | 35 | 8.000 | 8.000 | 9.000 | 6 |
| rank_200_include_ties | 79.500 | 202 | 52 | 8.000 | 8.000 | 10.000 | 7 |
| rank_300_include_ties | 74.250 | 300 | 102 | 13.000 | 12.000 | 18.000 | 14 |
| rank_400_include_ties | 70.500 | 416 | 137 | 23.000 | 20.000 | 31.000 | 20 |
| rank_500_include_ties | 67.000 | 505 | 185 | 27.000 | 21.000 | 38.000 | 29 |
| rank_750_include_ties | 54.812 | 760 | 329 | 57.000 | 36.000 | 89.700 | 73 |
| rank_1000_include_ties | 52.062 | 1045 | 381 | 64.000 | 42.000 | 103.000 | 80 |

Rank quotas use the main-deck threshold for both locations. They do not force the commander count to equal the quota.

## Fixed cutoffs and no-floor check

| policy | main_pointed_cards | pointed_commander_options | median | p10 | p90 | unique_totals |
| --- | --- | --- | --- | --- | --- | --- |
| threshold_65_tiered | 525 | 189 | 29.000 | 22.000 | 41.000 | 36 |
| threshold_70_tiered | 426 | 142 | 24.000 | 20.000 | 31.000 | 21 |
| threshold_75_tiered | 287 | 90 | 13.000 | 12.000 | 17.000 | 14 |
| threshold_80_tiered | 141 | 45 | 8.000 | 8.000 | 9.000 | 7 |
| threshold_85_tiered | 54 | 16 | 5.000 | 5.000 | 5.000 | 4 |
| threshold_90_tiered | 26 | 10 | 3.000 | 3.000 | 3.000 | 3 |
| threshold_75_tiered_no_specialist_floor | 259 | 90 | 13.000 | 12.000 | 17.000 | 14 |

Linear max(0,ceil(s-tau)) and quadratic ceil(20*((s-tau)/(100-tau))**2) are in cutoff_comparison.csv. Their units differ; comparing raw totals is not evidence one predicts strength better. No deck/year-specific normalization was applied.

## Recommended-policy cohort construction costs

| cohort | deck_count | legal_deck_count | median | p10 | p90 | median_pointed_cards | median_command_zone_share | median_top3_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| official_precons | 174 | 171 | 13.000 | 12.000 | 17.000 | 2.000 | 0.000 | 1.000 |
| cedh_holdout | 2520 | 2520 | 169.000 | 96.900 | 254.000 | 44.000 | 0.040 | 0.173 |
| bracket3_declared | 150 | 150 | 42.000 | 15.000 | 83.300 | 11.500 | 0.000 | 0.563 |

The B3 labels are event/user declarations, not Wizards-verified brackets. cEDH event names are a selection heuristic; no identified data demonstrate maximum 2HG competitive outcomes. Events require at least one completed pod, not proof the entire event completed. Temporal filtering excludes future events; absent structured decklists are excluded, not filled with zeros.

## Boundary review

| card_name | main_deck_impact | main_deck_points | category |
| --- | --- | --- | --- |
| Formidable Speaker | 77.000 | 1 | omission_audit |
| Kenrith, the Returned King | 77.000 | 1 | commander_engine |
| Misdirection | 77.000 | 1 | omission_audit |
| Najeela, the Blade-Blossom | 77.000 | 1 | commander_engine |
| Tymna the Weaver | 77.000 | 1 | commander_engine |
| Vial Smasher the Fierce | 77.000 | 1 | commander_engine |
| Yuriko, the Tiger's Shadow | 77.000 | 1 | commander_engine |
| Brain Freeze | 76.500 | 1 | specialized_win |
| Chains of Mephistopheles | 76.500 | 1 | resource_denial |
| Grapeshot | 76.500 | 1 | specialized_win |
| Smothering Tithe | 76.500 | 1 | mana_engine |
| Tendrils of Agony | 76.500 | 1 | specialized_win |
| Test of Endurance | 76.500 | 1 | two_hg_win |
| Abrupt Decay | 76.250 | 1 | interaction |
| Assassin's Trophy | 76.250 | 1 | interaction |
| Cyclonic Rift | 76.250 | 1 | interaction |
| Emergence Zone | 76.250 | 1 | omission_audit |
| Frantic Search | 76.250 | 1 | selection_engine |
| Nature's Rhythm | 76.250 | 1 | omission_audit |
| Path to Exile | 76.250 | 1 | interaction |
| Temporal Mastery | 76.250 | 1 | extra_turn |
| Toxic Deluge | 76.250 | 1 | interaction |
| Agatha of the Vile Cauldron | 76.000 | 1 | specialized_engine |
| Biomancer's Familiar | 76.000 | 1 | specialized_engine |
| Chancellor of the Tangle | 76.000 | 1 | fast_mana |
| Elvish Spirit Guide | 76.000 | 1 | fast_mana |
| Glacial Chasm | 76.000 | 1 | specialized_land |
| Gush | 76.000 | 1 | specialized_mana |
| High Tide | 76.000 | 1 | specialized_mana |
| Relic of Legends | 76.000 | 1 | specialized_mana |
| Reshape | 76.000 | 1 | artifact_tutor |
| Simian Spirit Guide | 76.000 | 1 | fast_mana |
| The Tabernacle at Pendrell Vale | 76.000 | 1 | specialized_land |
| Training Grounds | 76.000 | 1 | specialized_engine |
| Archon of Emeria | 75.750 | 1 | resource_denial |
| Back to Basics | 75.750 | 1 | resource_denial |
| Blood Moon | 75.750 | 1 | resource_denial |
| Chain of Vapor | 75.750 | 1 | interaction |
| Collector Ouphe | 75.750 | 1 | resource_denial |
| Cursed Totem | 75.750 | 1 | resource_denial |

See full cutoff_boundary_review.csv, price_tier_boundary_review.csv and manual_review_queue.csv. The price band boundaries at80/85/90/95 need as much review as75. Examples of unpointed specialized conversion pieces are Squirrel Nest, ordinary win payoffs and narrow enablement without exceptional independent conversion; Spellbook membership alone is not priced. Thassa's Oracle, Underworld Breach and efficient specialty tutors remain pointed. Lock/early-loss cards need separate legality review even if cheap under the rubric.

## Sensitivity and limitations

200 +/-2 judgment-impact scenarios yield 267–290 main-deck pointed cards, median set Jaccard 0.922. This does not capture correlated judgment error or omitted strategies. No-floor results expose the explicit safeguard's effect. Equal functional cycles, basic lands and Oracle duplication are automated checks. Color/archetype concentration is in color_and_archetype_concentration.csv; categories are analyst labels, not measured archetype balance.

A strict team cap is premature. Start by collecting real paired 2HG lists, match context and legal combo adjudications under a frozen version; inspect zero-point competitive examples and boundary disputes. Do not turn observed cohort medians into official bracket cutoffs or a 2,000-point team budget.

## Deck and individual-price sensitivity

The supplementary deck_rating_sensitivity.csv uses 200 independent +/-2 impact scenarios in both locations (seed19126). These are judgment scenarios, not statistical confidence bounds. individual_card_price_sensitivity.csv changes each of ten leading legal main-deck cards and five leading commanders by +/-1 point. cutoff_rank_stability.csv measures rank changes across policies; point histograms and boundary/free-card audits cover every cutoff.

{
  "bracket3_declared": {
    "median_score_min": 38.0,
    "median_score_max": 43.0,
    "median_rank_correlation": 0.9926572432292478
  },
  "cedh_holdout": {
    "median_score_min": 161.0,
    "median_score_max": 178.0,
    "median_rank_correlation": 0.9955197119356353
  },
  "official_precons": {
    "median_score_min": 12.0,
    "median_score_max": 13.0,
    "median_rank_correlation": 0.9503295060394996
  }
}

Command-zone discounts are explicitly listed in command_zone_price_inversions.csv and remain mandatory manual-review cases; guaranteed access does not automatically eliminate colored construction, deployment or main-deck cheating differences.
