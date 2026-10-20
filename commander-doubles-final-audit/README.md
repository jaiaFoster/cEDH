# Commander Doubles final audit — season0-proposed

Read final_audit_executive_summary.md first. This is a review package, not activated official rules. Previous project directories/branches are preserved.

From repository root:

```sh
python -m pip install -r commander-top1000-power-ranking/requirements.txt
python commander-doubles-final-audit/audit_pipeline.py
python commander-doubles-final-audit/audit_tests.py
python commander-doubles-final-audit/audit_backend.py commander-doubles-final-audit/adversarial_decklists/T01_A.txt --deck-b commander-doubles-final-audit/adversarial_decklists/T01_B.txt --export team-report.json
```

Uses existing Python environment/requirements from commander-top1000-power-ranking, complete Oracle snapshot, prior resolver/legality checks/Moxfield parser, frozen precons and authorized TopDeck.gg snapshots. No paid API or ordinary network calls. All50 human tiers live separately in human_calibration_anchors.json/audit_inputs.json; proposed numeric prices are editable Oracle-ID overrides in scoring_config.json. To regenerate overrides from judgments edit audit_inputs.json. Rerunning pipeline resets scoring_config from audit_inputs: direct config edits are for calculator experiments unless copied into inputs. Human tier bounds are enforced. Main/CZ prices are alternatives, partners charged individually.

Known verified unpointed cards default0; unknown identities error. Banned cards keep legality failures at any hypothetical price. Team caps/individual reference/20% transfer envelope configurable. JSON decks import/export via main/commanders maps; Moxfield Commander/Deck sections supported. Scored exports include submitted deck maps and can be imported for recalculation; --overrides imports an Oracle-ID map and --export-overrides exports it. Companion, rulebreaker and pregame-color-choice permissions require explicit manual review.

42 interactions include verified conditional splits, support and explicit false unions; automated matching reports candidates only.26 padded legal fixtures cover13 archetypes and are not optimized decklists or measured consistency. No simulator, true2HG performance dataset or verified paired cohort was available.

The delivery session generated and tested files in memory because local writes were disabled, then committed through the authorized GitHub connector. Two inherited tests requiring temporary files could not run locally;35 inherited read-only tests passed. The new audit tests and full new artifacts were exercised in memory; see test_results.json. Reproduction requires writable output directory. Artifact hashes/checks and deterministic regeneration are tested without altering earlier versions.
