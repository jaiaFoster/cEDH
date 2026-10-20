# Actual frozen-cohort recalculation

| cohort | method | n | median | p10 | p90 | min | max | zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial_fixture | old | 26 | 1.0 | 0.0 | 8.0 | 0 | 28 | 11 |
| adversarial_fixture | calibrated_existing_tiers | 26 | 1.5 | 0.0 | 9.5 | 0 | 39 | 12 |
| adversarial_fixture | fine_integer | 26 | 1.5 | 0.0 | 11.0 | 0 | 39 | 12 |
| adversarial_fixture | audited | 26 | 1.5 | 0.0 | 10.0 | 0 | 39 | 12 |
| bracket3_declared | old | 150 | 42.0 | 15.0 | 83.3 | 1 | 126 | 0 |
| bracket3_declared | calibrated_existing_tiers | 150 | 65.0 | 18.0 | 139.0 | 1 | 200 | 0 |
| bracket3_declared | fine_integer | 150 | 71.5 | 20.9 | 156.0 | 2 | 222 | 0 |
| bracket3_declared | audited | 150 | 66.0 | 19.0 | 139.2 | 1 | 198 | 0 |
| cedh_holdout | old | 2520 | 169.0 | 96.9 | 254.0 | 1 | 274 | 0 |
| cedh_holdout | calibrated_existing_tiers | 2520 | 274.0 | 157.0 | 425.0 | 7 | 502 | 0 |
| cedh_holdout | fine_integer | 2520 | 305.0 | 178.0 | 462.1 | 9 | 534 | 0 |
| cedh_holdout | audited | 2520 | 278.0 | 160.0 | 425.1 | 7 | 505 | 0 |
| official_precons | old | 174 | 13.0 | 12.0 | 17.0 | 1 | 25 | 0 |
| official_precons | calibrated_existing_tiers | 174 | 16.0 | 15.0 | 22.0 | 1 | 32 | 0 |
| official_precons | fine_integer | 174 | 16.0 | 15.0 | 24.0 | 1 | 36 | 0 |
| official_precons | audited | 174 | 16.0 | 15.0 | 22.0 | 1 | 30 | 0 |

All174/150/2520 archived lists were rescored at their actual card locations;26 new legal padded fixtures are a separate cohort. Historical exceptions remain; see legality flags. TopDeck.gg attribution retained. Event labels, especially B3 and cEDH, are declarations rather than strength certification. No verified paired 2HG outcomes or upgraded-deck sample was available.

The1,000-resample intervals in cohort_distribution_summary.csv are conditional sampling intervals, not uncertainty in prices or predictions. Single-card +/-1 tests and cutoff/curve grids show construction-price sensitivity. No weight was fitted to these final cohorts, and no correlation with point totals is represented as a win-rate result.

## Point concentration and label-cost ordering

| cohort | n | median_pointed_cards | median_command_zone_share | median_top3_share | legal_lists |
| --- | --- | --- | --- | --- | --- |
| adversarial_fixture | 26 | 1.0 | 0.0 | 1.0 | 26 |
| bracket3_declared | 150 | 11.0 | 0.0 | 0.564 | 150 |
| cedh_holdout | 2520 | 44.0 | 0.022 | 0.158 | 2520 |
| official_precons | 174 | 2.0 | 0.0 | 1.0 | 171 |

| higher_label | lower_label | method | pairs | cost_ordering_ties_half |
| --- | --- | --- | --- | --- |
| bracket3_declared | official_precons | old | 26100 | 0.929 |
| bracket3_declared | official_precons | audited | 26100 | 0.932 |
| cedh_holdout | official_precons | old | 438480 | 0.999 |
| cedh_holdout | official_precons | audited | 438480 | 0.999 |
| cedh_holdout | bracket3_declared | old | 378000 | 0.983 |
| cedh_holdout | bracket3_declared | audited | 378000 | 0.984 |

Cost ordering is not a prediction metric. Low/high lists with commander/basic counts are in cohort_cost_outliers.csv. Extremely basic-heavy cEDH-labelled registrations remain included; no label cleanup was fitted to improve apparent separation.
