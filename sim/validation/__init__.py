"""Layer 6 - Validation: does this instrument behave enough like real cEDH
to justify using its output?

Status:
  - run_classification.py  IMPLEMENTED. RunClass taxonomy and fail-closed
                            deck-loading guards (docs/RUN_CLASSIFICATION.md).
                            The only sanctioned way to load a decklist for
                            a DECK_BACKED_* run - sim/simulation/ must call
                            load_frozen_deck() before touching a deck.
  - Everything else: not implemented yet. Planned: gate runners for
    docs/VALIDATION_GATES.md - a gold-board-state checker (Gate 2), a
    gold-game checker (Gate 3), tooling to support the ~100-game manual
    inspection pass (Gate 4), and the sensitivity/regression harness for
    Gates 5-7. Every discovered rules or policy bug found here becomes a
    permanent test under rules_tests/regression/ (charter, "Regression
    testing").

The schema-conformance checks
(rules_tests/regression/test_schemas.py, test_run_classification_guards.py)
are a precursor to the gate-runner tooling, not a substitute for it - they
validate the *shape* of data/schemas artifacts and the deck-loading guards,
not gameplay behavior, since there's no gameplay yet to check.
"""
