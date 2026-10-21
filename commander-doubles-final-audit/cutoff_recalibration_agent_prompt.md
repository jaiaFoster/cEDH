# Assignment: recalibrate Commander Doubles entire sparse points list

Work in repository jaiaFoster/cEDH at branch commander-doubles-final-audit. Baseline commit aa34ca7 (plus subsequent organizer-calibration commits). First read:
- commander-doubles-final-audit/organizer_calibration_2026-10-20.md
- commander-doubles-final-audit/human_calibration_anchors.json
- commander-doubles-final-audit/final_audit_executive_summary.md
- commander-doubles-final-audit/audited_point_schedule.csv
- commander-doubles-final-audit/cutoff_finalization_report.md
- commander-doubles-final-audit/scoring_config.json
- commander-doubles-final-audit/official_2hg_rules_verification.md
- commander-doubles-final-audit/team_combo_rules_analysis.md
- commander-top1000-power-ranking/top_1000_main_deck_cards.csv
- commander-top1000-power-ranking/top_commanders.csv

Goal: produce a **recalibrated, evidence-based sparse points list and impact cutoff** reflecting all original 50 qualitative anchors AND the subsequent organizer numeric decisions. Clearly separate confirmed organizer values, tolerated ranges, provisional assistant working numbers, and unapproved proposals. Do not claim all suggested figures are locked.

1. Verify all anchor card IDs, names, zone eligibility, and current price. The original 50 anchors are 0–5 QUALITATIVE TIERS, not numeric construction points. Later discussions contain NUMERICAL POINT prices. Preserve both with provenance, date and precedence; newer direct user decisions supersede earlier suggestions. No hidden overrides.
2. Evaluate whole candidate population, including top 1,000 main deck, command-zone ranking, ~321 currently pointed legal identities, near cutoff and omitted high-ceiling card families. Analyze functional equivalents, tutors, protection, mana, extra turns, 60-life thresholds, each-opponent damage/drain, draw denial, symmetrical stax, combo payoff versus enabler, controller splits.
3. **Reestimate cutoff**. Current impact cutoff =75, but it is a policy choice, not an empirically discovered break. Compare cutoffs 70/72.5/75/77.5/80 and additional justified candidates. Show the last 20 admitted and first 20 unpointed at each candidate cutoff BEFORE and AFTER explicit exceptions. Quantify pointed totals, marginal utility, false-positive ordinary utility taxation and missing exceptional cards. Recommend a cutoff on sound policy grounds; do not manipulate score solely to place a desired card across the line. Provide a clear exceptions ledger.
4. Price within tiers, preserve monotonicity wherever possible, and give transparent reasons for deviations. Test existing nonlinear curve vs simpler alternatives. Keep moderate defense inexpensive and extraordinary tutors/accelerants/proactive team-turn protection/extra turns expensive. Assess strong narrow tools individually. Never add partner/team synergy surcharges.
5. **Cache and cite 2HG rulings** in a versioned machine-readable `two_hg_rules_cache.jsonl` plus narrative `two_hg_rules_cache.md`: exact card Oracle text source/Oracle ID/retrieval date; precise CR provisions; specific interpretation; individual vs team controller/state; impact on price; tested interaction/false positive; verified vs unresolved; invalidation trigger on Oracle or CR revision. Validate rules against current official Wizards sources and legal Commander 2HG modifier. Give fresh and archived provenance. Do not declare rulings judge-certified.
6. Stress-test with archived 174 precons, 150 self-declared B3, 2520 event-labeled cEDH, 13 adversarial archetypes/26 decks and 42 split-controller interactions. These cohorts are deck-construction distributions, not win rates. Add representative life/extra-turn/draw-denial teams. Do not assume a low-point combo requires ban: organizer favors repricing individual outstanding cards, reserving explicit prohibitions for truly egregious cases. Clearly explain vulnerabilities still not addressable by an additive card-price system.
7. Recompute cap proposals around 60/player reference,120/team,72 individual maximum/12 transferable; assess sensitivity to revised price scale and cutoff. Preserve legal, CZ and banned handling, and official experimental bans unless explicitly approved.
8. Commit reproducible artifacts on a NEW working branch named `commander-doubles-cutoff-recalibration` based on the latest audit branch; never overwrite archived analyses. Include `recalibrated_point_schedule.csv`, `cutoff_sensitivity.csv`, `cutoff_before_after_boundaries.csv`, `calibration_precedence.json`, `organizer_approval_queue.md`, `two_hg_rules_cache.jsonl`, `two_hg_rules_cache.md`, `price_changes.csv`, `card_family_reviews.md`, `cohort_score_changes.csv`, `adversarial_retest.md`, `tests`, and `recalibration_executive_summary.md`.
9. In final summary explain recommended cutoff, point list size, ten most important repricings, outstanding uncertain price ranges, 2HG quirks that changed rankings, revealed loopholes, and exactly what organizer must approve. Mark season0-proposed, NOT ACTIVE. Quote commit ID and branch.

Do the analysis and implement reproducible outputs; don't stop at suggestions.
