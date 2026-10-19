# Recommendation: reuse evidence, retain human control
Do not promote any tested model directly to strict league prices. Use the published intrinsic-rating cache as a reviewable starting prior, with Scryfall identity, curated expert references and separate legality analysis. It is the most useful new reusable input discovered; its raw basic-land errors prevent adoption without review.

## Direct answers
1. **Reusable comprehensive database?** A substantial MIT-repository cache exists: 32,075 names. It is not comprehensive for our cohort and is not independently validated measured power. No verified, comprehensive, outcome-validated Commander price database was found.
2. **Closest existing project?** zarzak/mtg-deck-builder's commander-independent scorer is closest structurally. Canadian Highlander is closest as an established additive budget policy but is sparse and for another format. EDHPowerLevel's presentation is close; approved export was not verified.
3. **Direct reuse?** The cache/code can serve as a pinned research prior under the retained MIT notice; no separate cache restriction was found. Underlying card rights remain. Use current Oracle IDs and keep missing/freshness flags. Do not import its contextual synergy or EDHREC collection machinery.
4. **Reliable external evaluator?** No service with verified permitted bulk access and demonstrated predictive reliability was acquired. Available source claims and attractive outputs are insufficient.
5. **Actual precon scores?** See benchmark_analysis.md and benchmark_results.csv. The raw cache fully covers 164 of 174 decks; incomplete decks have blank scores and separate subtotals. Units are uncalibrated; no 1,000-point target was imposed.
6. **Best agreement?** The raw cache wins four of five added reviewer pairs, but has weak older-sample correlations, missing coverage and basic-land inconsistencies. XMage has a better six-deck correlation but worse new-pair results. No overall winner is statistically established.
7. **Recover prices from deck scores?** Technically possible only with informative priors/constraints; not uniquely from these 174 decks. The executed ridge emulation generalizes poorly. Do not represent inferred coefficients as measured card effects.
8. **Recurring sources?** Scryfall, MTGJSON, official Spellbook bulk, Wizards policy and versioned published rating snapshots. Add permissioned outcome data only after access and provenance checks. Do not bulk scrape restricted EDHREC endpoints.
9. **Spellbook?** Separate component/prerequisite/commander/controller analyzer with attribution. Live tests succeeded. Cross-team union matches remain candidates for manual rules review; no point surcharge.
10. **Remaining limitations?** Tiny opinion samples, conflicting reviewer criteria, unverified LLM training overlap, sparse outcome data, stale/missing source ratings, source-specific biases, lack of 2HG validation and structural additive limits.
11. **Replace regex with what?** An evidence table and review process built around a pinned external card prior, verified functional tags, sparse expert anchors and explicit global overrides. Require land consistency and out-of-sample tests before releasing any replacement. There is no justified automatic replacement today.
12. **Preserve what?** Existing Oracle joins, cleaned precons, provenance, deck audits, integer calculator, override import/export, team addition and original validation fixtures. Keep v0.2 unchanged as the baseline. Retire its unvalidated automatic regex estimates as the presumed authoritative source once a reviewed replacement is ready.

## Feasible approaches ranked by evidence and practical use
| Approach | Empirical support here | Transparency | Maintenance | Reuse | Decision |
|---|---|---|---|---|---|
| Published intrinsic cache | Mixed, four/five new pairs; weak small-set correlations | Rubric/code/cache visible; model opaque | Git snapshots and text changes; gaps need review | MIT repository notices retained | Best reviewable candidate; do not deploy raw |
| XMage adapter | Mixed older sets, two/five new pairs | High source transparency | Code refresh needed; old lists/bugs | MIT | Comparison control, no preferred production role |
| Canlander/GC expert lists | Sparse, many ties | High policy transparency | Announcement review | Public facts; blanket data license unverified | High-impact review anchors |
| Sparse vote ensemble | No consistent improvement | High | Easy but correlated evidence | Source-dependent | Diagnostic only |
| Existing regex v0.2 | Negative original correlations, one/five new pairs | High | Locally editable | Existing baseline | Preserve for comparison |
| Zero-prior inverse regression | Poor held-out emulation, negative coefficients | High | Requires diverse licensed labels | Permitted labels used in diagnostic | Reject as card-price recovery method here |
| Partial creature/adoption features | No full deck coverage | Mixed | Source-dependent | Respect source terms | Coverage/error analysis only |
| Hosted evaluators | Not acquired or not approved for batch use | Unverified | External dependency | Unverified | No empirical rank assigned |

This is not a ranking of true competitive predictive validity. No model has outcome evidence sufficient for that claim.

## Proposed data contract
A release record should contain Oracle ID, globally fixed integer price, source/model version, evidence grade, source-text freshness, missing/provisional status, review reason and override history. The effective price is override if present, otherwise an explicitly accepted source estimate; missing values must not silently become zero. Keep the old database separate until a human approves a new release.

First review basic lands as a common mana baseline, utility/nonbasic land increments, fast mana, flexible tutors, repeatable card advantage and narrow combo-only pieces. Use the source cache to save annotation effort; audit anchors before trusting its scale. An unresolved card should trigger review or a labeled provisional global price. No deck-specific or commander-specific imputation.

Avoid tuning several thousand prices against 20 reviewer-selected decks. Obtain independent pods and league games with pilots, deck revisions, opponents, turn count and coarse game-ending mechanism. Keep a future release holdout. Statistical adjustment should shrink a small number of predeclared calibration dimensions unless much richer data is obtained.

## Go-live gate
Before enforcing a strict cap: complete legal-card coverage, document a consistent land policy, resolve glaring price inversions, test unseen non-precon Bracket 3 lists, and gather actual 2HG experience. These are task-specific unresolved requirements, not evidence that synergy should be penalized. Scale all accepted prices globally only after relative values are reviewed. Team score remains P(A)+P(B), with no team-synergy term.
