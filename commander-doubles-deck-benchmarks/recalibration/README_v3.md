# Global recalibration v3 — Issue #5

Status: season0-proposed, activated=false. Feature branch targets commander-doubles-deck-benchmarks. Read organizer_audio_summary.md, global_recalibration_analysis.md, decision_taxonomy.md and exception_and_conflict_queue.md first.

The effective organizer v2 overlay is authoritative for this experiment, with explicit nonchanges and prior unsuperseded decisions preserved. Candidate v3 adds individually documented proposals_v3.tsv rows. That file is editable research input, not organizer approval. Original320-row schedule, all50 qualitative observations, all18 decklists and historical scores stay immutable.

## Reproduce from repository root

```sh
python -m pip install -r commander-doubles-deck-benchmarks/requirements.txt
python commander-doubles-deck-benchmarks/recalibration/recalibration_v3.py
python commander-doubles-deck-benchmarks/recalibration/recalibration_v3.py --check
python commander-doubles-deck-benchmarks/recalibration/validate_recalibration_v3.py
python commander-doubles-deck-benchmarks/recalibration/score_recalibration_v3.py commander-doubles-deck-benchmarks/batch3/decks/H1.txt --deck-b commander-doubles-deck-benchmarks/batch3/decks/H2.json --model candidate-v3 --summary
```

The validation command runs all56 preserved Batch suites, the new global suite, and byte reproduction, then records actual results in validation_results_v3.json. The example H team exits1 because it exceeds budget. Use the existing Python dependencies. The offline scorer score_recalibration_v3.py accepts a deck path, optional --deck-b, --model organizer-v2 or candidate-v3, --summary and --export. Exit0 means legal and within cap; exit1 means construction/budget noncompliance, and exit2 means invalid input. It never certifies gameplay legality. Ordinary regeneration/scoring is offline. Source commit and file checksums are in source_provenance.json. All complete JSON deck inventories are read from original Batch1/2/3 folders and never rewritten. Full_card_rescoring_ledger has1800 rows, with quantities expanded to one row per physical card and three comparable prices per row. The primary schedule has one row per Oracle identity and construction zone. Ineligible command zones are not priced. Unknown identities and negative/noninteger prices fail; Known free cards stay free. Edit proposals_v3.tsv, then regenerate; exported CSVs are derived outputs, not editable active inputs. Naming uses the existing Oracle resolver plus a local face-alias extension; back-face names still resolve to one Oracle identity.

Columns separate raw organizer labels from provenance-corrected exact/working status. decision_lineage preserves prior events and literal source mentions; it does not turn every incidental preview-row zero into a human approval. family_coverage_audit identifies individually proposed, organizer-reviewed and inherited/screened rows. targeted_oracle_discovery includes nominations that are not fully rated; unpriced_high_risk_queue explicitly marks that limitation.

No coefficients were learned from the eighteen decks, no per-deck normalization was used, and no sample outcome data was fabricated. Prices are auditable comparative judgments. No known combo or teammate pairing increases a construction price automatically. The old impact cutoff is preserved, while named price exceptions form the new versioned overlay. A card's legal status is independent of points and all existing bans remain.

The official rule landing/ban list and two primary combo examples were read2026-10-22. Oracle text is the pinned October20 dataset; a failed Scryfall web retrieval is recorded and no new full bulk update is claimed. Current CR805.8 and810.9 support the team-turn/life analyses, while original Batches1–3 controller cases remain accessible. See v3_inputs/research_evidence.json and rules_verification_v3.md for source-specific conclusions and unresolved strength judgments.
