# Commander Doubles Batch3 — season0-proposed

Read organizer_audio_review.md first, then teams.csv, decks/, score_ledger.csv, rules_interactions.md and organizer_review_and_limits.md. G/H/I are six complete independent100-card decks; H1 has two legal Partners and98 main cards. No rules or price activation and no experimental unbans.

## Reproduce from repository root

~~~sh
python commander-doubles-deck-benchmarks/build_batch3.py
python commander-doubles-deck-benchmarks/build_batch3.py --check
python -m unittest discover -s commander-doubles-deck-benchmarks/tests -p test_batch3.py -v
python commander-doubles-deck-benchmarks/score_batch3.py commander-doubles-deck-benchmarks/batch3/decks/G1.txt --deck-b commander-doubles-deck-benchmarks/batch3/decks/G2.json --summary
~~~

Uses the existing Python dependencies, pinned Oracle and source snapshots; ordinary scoring is offline. Frozen inputs are deck_inputs.json, review_content.json, research/foundations.json and source_checks.json. Latest price authority is the accepted_working_price_overrides_2026-10-21.csv file committed at0b1d2dd. Copy is frozen under research for deterministic historical regeneration.

price_snapshot.csv includes all31069 known legal paper Oracle identities, including explicit zeros; unknown names remain errors. Separate zone prices replace rather than add. Full known-card population is verified in provenance. README and price manifest identify the exact override composition.

Sources are attributed factual registrations already in the authorized archive. No mass scrape, paid API, inaccessible primer reproduction or invented standings. New deck changes are original analysis. The current linkedCR and official banned list were rereadOct21; pinned Oracle snapshot remainsOct20, not a claimed new bulk download. Text lists have Commander/Deck sections; JSON uses submitted_deck with Oracle IDs and version/checksum metadata.

Earlier Batch1/2 lists and retotal files are preserved. Source results do not belong to these adaptations. All budget checks use120 team/72 head/60 reference/12 max transfer and zero synergy surcharge.
