# Full-list cutoff recalibration — season0-proposed

Read recalibration_executive_summary.md, then organizer_approval_queue.md. Earlier directories and branches are preserved. No schedule or new legality policy is activated.

From repository root, Python3.11+ with pandas,numpy,scipy,requests (existing requirements):

```sh
python -m pip install -r commander-doubles-cutoff-recalibration/requirements.txt
python commander-doubles-cutoff-recalibration/recalibrate.py
python commander-doubles-cutoff-recalibration/audit_tests.py
python commander-doubles-cutoff-recalibration/recalibrate.py --check
python commander-doubles-cutoff-recalibration/recalibrated_backend.py commander-doubles-cutoff-recalibration/adversarial_decklists/T09_A.txt --deck-b commander-doubles-cutoff-recalibration/adversarial_decklists/T09_B.txt --export team-report.json
```

Offline regeneration uses pinned current Oracle/rules, frozen prior9610 impacts, original50 anchors, organizer numerical ledger, reviewed exceptions and archived authorized TopDeck snapshots. No paid API or network calls for scoring. Entire original pool receives a price/evidence/functional-route reassessment; this is not a new expert score for every card. Known unpointed identities cost0; unknown names error, and known unrated identities get review flags. Main/CZ prices replace one another by location; partner prices sum. Banned legality is independent of hypothetical points. Commander pair/color/singleton/size checks remain; unsupported rulebreaker, companion and pregame-color permissions require manual review.

Edit review_inputs.py to change authoritative/working/proposed decisions or cutoff, then regenerate. Keep category/status and ranges accurate. Original impact scores must not be silently edited to force admission. Generated scoring_config.json contains effective fixed Oracle/location overrides and budget settings; temporary --config/--overrides experiments do not modify canonical review inputs. Explicit organizer prices/approved ranges/free anchors are validated. --export-overrides exports accepted config; --export exports complete submitted decks plus scores, and such exports can be imported again. Single-deck --individual-cap and team --team-cap/--individual-cap/--individual-reference/--transfer-fraction supported. No synergy adjustment or automatic combo certification.

To intentionally refresh online inputs:

```sh
python commander-doubles-cutoff-recalibration/refresh_sources.py
python commander-doubles-cutoff-recalibration/recalibrate.py
```

Refresh changes versioned inputs. Review all Oracle/legality changes, update dates/version/rules interpretation, and rerun tests before accepting refreshed artifacts. Original network source URLs, hashes and snapshot dates live in source_provenance.json and data/source_snapshot_manifest.json. Current CR text is compressed only as a small source snapshot for reproducible citation verification, with Wizards attribution; no invented data-license permission. Scryfall official bulk endpoint authorized download; card/Oracle text © Wizards, Scryfall API terms apply. Inherited external-cache licenses/notices and prior42-source inventory retained, no restricted new bulk scraping. Published cache ratings are not directly priced. No third-party evaluator output acquired in this sprint.

cutoff_sensitivity.csv:6cutoffs×3curves×4exceptionstages×4cohorts (includes79.5 to test near-floor fragility). cutoff_per_deck_scores.csv includes all nonlinear/stage/cutoff list totals. Boundaries list20 above/below with unchanged impact at each threshold and zone, before/after exceptions. Parameter coefficients are documented policy, not fitted outcome effects. Cohort labels and existing reviewer diagnostics are not true win-strength labels. Exact pair budget enumeration, fixed-seed bootstrap and subjective±2 sensitivity are distinct analyses. Specialist floor/no-floor and one-point premium sensitivity are exported separately. No verified paired2HG cohort or gameplay simulator was available.

The copied human_calibration_anchors.json preserves the earlier file verbatim; its historical proposed_points fields are not updated numerical decisions. Use calibration_precedence.json and recalibrated_point_schedule.csv for current effective prices.

All 21 pair fixtures are legal100-card basic-padded illustrations, not optimized decklists; two are explicitly resource/turn counterexamples rather than wins. Rules cache covers conditional controller splits and false positives. Risk matches never establish game state or functionality. See unresolved commander-damage and October rulebreaker freshness in rules cache. No broad combo ban, turn limit, teammate surcharge or experimental unban is activated.
