"""Permanent regression test for the INT-0012 incident (2026-08-12): a record was
initially marked status=verified on the strength of an executable-engine test that
reproduced a downstream CONSEQUENCE of the interaction, not the interaction's own
exact stated transition. Nothing in the schema at the time distinguished those two
evidentiary strengths, so the gap wasn't machine-checkable. docs/VERIFICATION_LEVELS.md
and the interaction schema's verification_level/exact_reproduction fields fix that -
this test enforces the two fields stay logically consistent with each other, not just
individually well-typed (which test_schemas.py already covers).
"""
from conftest import REPO_ROOT, load_json

INTERACTIONS_VERIFIED_DIR = REPO_ROOT / "interactions" / "verified"
INTERACTIONS_CANDIDATE_DIR = REPO_ROOT / "interactions" / "candidate"

VALID_VERIFICATION_LEVELS = {
    "RULES_VERIFIED",
    "ENGINE_COMPONENT_VERIFIED",
    "ENGINE_EXACT_VERIFIED",
    "CONDITIONAL",
}


def _verified_interaction_files():
    return sorted(INTERACTIONS_VERIFIED_DIR.glob("INT-*.json"))


def test_every_verified_interaction_has_a_verification_level():
    for path in _verified_interaction_files():
        data = load_json(path)
        level = data.get("verification_level")
        assert level in VALID_VERIFICATION_LEVELS, (
            f"{path.name}: status=verified but verification_level is {level!r}, "
            f"must be one of {sorted(VALID_VERIFICATION_LEVELS)} per docs/VERIFICATION_LEVELS.md"
        )


def test_candidate_interactions_do_not_claim_a_verification_level():
    for path in sorted(INTERACTIONS_CANDIDATE_DIR.glob("INT-*.json")):
        data = load_json(path)
        level = data.get("verification_level")
        assert level in (None,), (
            f"{path.name}: status=candidate but verification_level is {level!r} - "
            f"a verification_level implies status=verified evidence exists"
        )


def test_engine_exact_verified_implies_exact_reproduction_true():
    """The INT-0012 incident, mirrored: don't let a record claim the strongest tier
    while its own engine-check evidence says it only reproduced a component."""
    for path in _verified_interaction_files():
        data = load_json(path)
        if data.get("verification_level") != "ENGINE_EXACT_VERIFIED":
            continue
        check = (data.get("verification") or {}).get("executable_engine_check")
        if check is None:
            continue
        exact = check.get("exact_reproduction")
        assert exact is True, (
            f"{path.name}: verification_level=ENGINE_EXACT_VERIFIED but "
            f"executable_engine_check.exact_reproduction is {exact!r}, not True - "
            f"either the engine check reproduced the interaction's own exact stated "
            f"transition end-to-end (set exact_reproduction: true) or the level should "
            f"be ENGINE_COMPONENT_VERIFIED instead"
        )


def test_engine_component_verified_implies_exact_reproduction_not_true():
    """The direct fix for the INT-0012 incident: a component-only engine check must
    not be paired with exact_reproduction: true, and must actually have engine
    evidence (that's what distinguishes it from RULES_VERIFIED)."""
    for path in _verified_interaction_files():
        data = load_json(path)
        if data.get("verification_level") != "ENGINE_COMPONENT_VERIFIED":
            continue
        check = (data.get("verification") or {}).get("executable_engine_check")
        assert check is not None, (
            f"{path.name}: verification_level=ENGINE_COMPONENT_VERIFIED requires "
            f"some executable_engine_check evidence to exist (that's what "
            f"distinguishes this tier from RULES_VERIFIED)"
        )
        exact = check.get("exact_reproduction")
        assert exact is not True, (
            f"{path.name}: verification_level=ENGINE_COMPONENT_VERIFIED but "
            f"executable_engine_check.exact_reproduction is True - this is exactly "
            f"the INT-0012 inconsistency this test exists to catch. If the exact "
            f"transition really was reproduced end-to-end, the level should be "
            f"ENGINE_EXACT_VERIFIED instead."
        )


def test_rules_verified_and_conditional_do_not_require_exact_reproduction_true():
    """RULES_VERIFIED and CONDITIONAL may or may not carry engine evidence, but if
    they do, it must not silently claim exact_reproduction: true - that would make
    the record indistinguishable from ENGINE_EXACT_VERIFIED without earning it."""
    for path in _verified_interaction_files():
        data = load_json(path)
        level = data.get("verification_level")
        if level not in ("RULES_VERIFIED", "CONDITIONAL"):
            continue
        check = (data.get("verification") or {}).get("executable_engine_check")
        if check is None:
            continue
        exact = check.get("exact_reproduction")
        assert exact is not True, (
            f"{path.name}: verification_level={level} but "
            f"executable_engine_check.exact_reproduction is True - if the exact "
            f"transition was really reproduced end-to-end, promote the level to "
            f"ENGINE_EXACT_VERIFIED instead of leaving it at {level}"
        )
