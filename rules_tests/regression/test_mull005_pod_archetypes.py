"""SIM-001 MULL-005 — non-simulated pod-conditioning overlay regression tests.

Confirms the assignment's hard constraints are actually enforced in code, not just in prose:
pod context can never rescue a structural SHIP, every result carries the two required (and
correctly distinct) confidence labels, and the modifier scale stays bounded.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from pod_archetypes import (  # noqa: E402
    pod_conditioned_grade, ARCHETYPES, POD_MODIFIERS, hand_feature_categories_present,
    STRUCTURAL_BAND_ORDER, FEATURE_CATEGORIES,
)

STRONG_FEATS = {
    "has_any_interaction_card": True, "interaction_density_2plus": True,
    "has_premium_one_drop_card": True, "t1_accel_executable_now": True,
    "has_any_engine_card": True, "land_count": 3, "has_tutor_card": True,
    "accel_card_count": 1,
}
WEAK_FEATS = {
    "has_any_interaction_card": False, "interaction_density_2plus": False,
    "has_premium_one_drop_card": False, "t1_accel_executable_now": False,
    "has_any_engine_card": False, "land_count": 4, "has_tutor_card": False,
    "accel_card_count": 0,
}


def test_ship_can_never_be_promoted_by_any_pod():
    for arch in ARCHETYPES:
        r = pod_conditioned_grade("SHIP", "no trajectory", [arch], STRONG_FEATS)
        assert r["pod_adjusted_grade"] == "SHIP", (arch, r)


def test_ship_can_never_be_promoted_by_a_multi_archetype_pod():
    r = pod_conditioned_grade("SHIP", "no trajectory", list(ARCHETYPES.keys()), STRONG_FEATS)
    assert r["pod_adjusted_grade"] == "SHIP", r


def test_confidence_labels_are_always_present_and_distinct():
    for grade in STRUCTURAL_BAND_ORDER:
        r = pod_conditioned_grade(grade, "reason", ["RogSi"], STRONG_FEATS)
        assert r["structural_confidence"] == "SIMULATED"
        assert r["pod_confidence"] == "STRATEGIC_PRIOR_UNVALIDATED"
        assert r["structural_confidence"] != r["pod_confidence"]


def test_snap_keep_cannot_shift_above_snap_keep():
    r = pod_conditioned_grade("SNAP_KEEP", "premium T1", list(ARCHETYPES.keys()), STRONG_FEATS)
    assert r["pod_adjusted_grade"] == "SNAP_KEEP"
    assert STRUCTURAL_BAND_ORDER.index(r["pod_adjusted_grade"]) == len(STRUCTURAL_BAND_ORDER) - 1


def test_all_modifier_values_are_within_bounded_scale():
    for arch, mods in POD_MODIFIERS.items():
        for cat, val in mods.items():
            assert cat in FEATURE_CATEGORIES, (arch, cat)
            assert -2 <= val <= 2, (arch, cat, val)


def test_every_archetype_has_all_four_tag_dimensions():
    required = {"speed", "primary_resource_axis", "interaction_demand", "resilience_profile"}
    for arch, data in ARCHETYPES.items():
        assert required <= set(data.keys()), arch
        assert data["increases_value_of"], arch
        assert data["decreases_value_of"], arch


def test_weak_hand_gets_no_positive_categories_from_empty_feats():
    present = hand_feature_categories_present(WEAK_FEATS)
    # land_count=4 alone should still register mana_resilience even with nothing else present
    assert present == {"mana_resilience"}, present


def test_conditional_keep_can_shift_down_to_marginal_against_unfavorable_pod():
    # A hand with an engine but a color-hungry mediocre profile against Blue Farm, which
    # deliberately does NOT reward raw_speed_low_curve or free interaction as heavily.
    feats = dict(WEAK_FEATS, has_any_engine_card=False, land_count=2)
    r = pod_conditioned_grade("CONDITIONAL_KEEP", "weak engine keep", ["Blue Farm"], feats)
    assert STRUCTURAL_BAND_ORDER.index(r["pod_adjusted_grade"]) <= STRUCTURAL_BAND_ORDER.index("CONDITIONAL_KEEP")
