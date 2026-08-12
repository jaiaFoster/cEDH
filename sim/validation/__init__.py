"""Layer 6 - Validation: does this instrument behave enough like real cEDH
to justify using its output?

Not implemented yet. Planned responsibility: gate runners for
docs/VALIDATION_GATES.md - a gold-board-state checker (Gate 2), a gold-game
checker (Gate 3), tooling to support the ~100-game manual inspection pass
(Gate 4), and the sensitivity/regression harness for Gates 5-7. Every
discovered rules or policy bug found here becomes a permanent test under
rules_tests/regression/ (charter, "Regression testing").

The schema-conformance checks that already exist today
(rules_tests/regression/test_schemas.py) are a precursor to this module, not
this module itself - they validate the *shape* of data/schemas artifacts,
not gameplay behavior, since there's no gameplay yet to check.
"""
