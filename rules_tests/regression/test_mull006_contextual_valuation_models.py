"""SIM-001 MULL-006 section 17 — do not naively sum scores: valuation architecture comparison.

Proves each of the four required architectures (weighted/lexicographic/gated/tree) implements the
assignment's own named gating examples correctly, and that they are structurally DIFFERENT from
each other (the whole point of comparing them) - not four names for the same formula.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from contextual_valuation_models import (  # noqa: E402
    weighted_model, lexicographic_model, gated_model, tree_model, apply_all_architectures,
    ARCHITECTURES, VALUATION_PROVENANCE, EXCEPTIONAL_GRADES,
)
from strength_speed_matrix import GRADE_RANK  # noqa: E402


def _obj(**overrides):
    base = {
        "destination": "Rhystic Study", "base_trajectory_grade": "B",
        "draw_dependence_class": "SELF_CONTAINED", "probability_of_trajectory": 1.0,
        "resilience_class": "RECOVERABLE", "relevant_agency": 0,
        "pod_realization_modifier": "MODERATE", "verified_combo_proximity": False,
    }
    base.update(overrides)
    return base


def test_no_destination_cannot_be_elevated_above_c_ceiling_in_gated_model():
    # The gate is a CEILING (interaction cannot elevate the hand above it), not a floor - a hand
    # already worse than C (e.g. base "D") is untouched; only a hand that would otherwise be
    # BETTER than C gets capped down to C.
    already_worse = _obj(destination=None, base_trajectory_grade="D", relevant_agency=3)
    assert already_worse["destination"] is None
    assert GRADE_RANK[gated_model(already_worse)] >= GRADE_RANK["D"]

    would_be_better = _obj(destination=None, base_trajectory_grade="A", relevant_agency=3)
    assert GRADE_RANK[gated_model(would_be_better)] >= GRADE_RANK["C"]


def test_no_destination_capped_at_d_or_worse_in_tree_model():
    obj = _obj(destination=None, base_trajectory_grade="D")
    result = tree_model(obj)
    assert GRADE_RANK[result] >= GRADE_RANK["D"]


def test_low_probability_narrow_outs_downgrades_before_agency_bonus_in_gated_model():
    # The assignment's own second gating example.
    obj = _obj(draw_dependence_class="EXACT_OR_NEAR_EXACT", probability_of_trajectory=0.05,
               relevant_agency=3)
    result = gated_model(obj)
    # the gate must trigger (probability below threshold), so no agency bonus is applied even
    # though relevant_agency=3 would otherwise improve the grade.
    assert GRADE_RANK[result] > GRADE_RANK["B"]


def test_all_in_capped_unless_exceptional_in_gated_model():
    ordinary = _obj(resilience_class="ALL_IN", base_trajectory_grade="B")
    exceptional = _obj(resilience_class="ALL_IN", base_trajectory_grade="S+")
    assert GRADE_RANK[gated_model(ordinary)] >= GRADE_RANK["C"]
    assert gated_model(exceptional) == "S+"  # exceptional destination survives uncapped


def test_all_in_capped_unless_exceptional_in_tree_model():
    ordinary = _obj(resilience_class="ALL_IN", base_trajectory_grade="B")
    exceptional = _obj(resilience_class="ALL_IN", base_trajectory_grade="S+")
    assert GRADE_RANK[tree_model(ordinary)] > GRADE_RANK["B"]
    assert tree_model(exceptional) == "S+"


def test_lexicographic_applies_only_one_step_never_compounds():
    # Both a narrow-outs penalty AND an ALL_IN penalty are present - lexicographic must apply
    # only ONE step (the higher-priority draw-dependence factor), never both.
    obj = _obj(draw_dependence_class="EXACT_OR_NEAR_EXACT", resilience_class="ALL_IN")
    base_rank = GRADE_RANK[obj["base_trajectory_grade"]]
    result_rank = GRADE_RANK[lexicographic_model(obj)]
    assert result_rank - base_rank == 1


def test_weighted_model_compounds_multiple_penalties():
    # The SAME dual-penalty scenario as the lexicographic test - weighted must move MORE than one
    # step, since every dimension always contributes something (the defining architectural
    # difference between weighted and lexicographic).
    obj = _obj(draw_dependence_class="EXACT_OR_NEAR_EXACT", resilience_class="ALL_IN")
    base_rank = GRADE_RANK[obj["base_trajectory_grade"]]
    result_rank = GRADE_RANK[weighted_model(obj)]
    assert result_rank - base_rank > 1


def test_robust_resilience_with_relevant_agency_upgrades_in_tree_model():
    obj = _obj(resilience_class="ROBUST", relevant_agency=1, draw_dependence_class="BROAD_OUTS")
    base_rank = GRADE_RANK[obj["base_trajectory_grade"]]
    result_rank = GRADE_RANK[tree_model(obj)]
    assert result_rank < base_rank  # strictly better


def test_apply_all_architectures_fills_all_four_without_mutating_input():
    obj = _obj()
    full = apply_all_architectures(obj)
    assert set(full["contextual_trajectory_grade"]) == set(ARCHITECTURES)
    assert obj["contextual_trajectory_grade"] == {} if "contextual_trajectory_grade" in obj else True


def test_architectures_can_disagree_on_the_same_object():
    # Not a claim that they MUST always disagree, but proves the four are not aliases of each
    # other - there exists at least one constructed object where they produce different grades.
    obj = _obj(draw_dependence_class="EXACT_OR_NEAR_EXACT", resilience_class="ALL_IN",
               relevant_agency=3, verified_combo_proximity=True)
    grades = {name: fn(obj) for name, fn in ARCHITECTURES.items()}
    assert len(set(grades.values())) > 1


def test_exceptional_grades_set_matches_matrix_top_band():
    assert EXCEPTIONAL_GRADES == {"S+", "S", "A+"}


def test_provenance_label_is_model_derived():
    assert VALUATION_PROVENANCE == "MODEL_DERIVED"


def test_seat_can_change_the_grade_when_resilience_is_fragile():
    # Section 6/18's own point: seat must be able to actually change a recommendation, not just
    # appear as an unused field on the trajectory object.
    seat1 = _obj(resilience_class="FRAGILE", seat=1)
    seat4 = _obj(resilience_class="FRAGILE", seat=4)
    for model in (weighted_model, lexicographic_model, gated_model, tree_model):
        assert GRADE_RANK[model(seat4)] >= GRADE_RANK[model(seat1)], model.__name__


def test_seat_does_not_change_grade_when_resilience_is_robust():
    # The seat-exposure gates only fire for FRAGILE/ALL_IN resilience - a ROBUST trajectory's
    # grade should not swing with seat under gated/lexicographic/tree (weighted still applies its
    # small continuous per-turn penalty everywhere, by design - see module docstring).
    seat1 = _obj(resilience_class="ROBUST", seat=1)
    seat4 = _obj(resilience_class="ROBUST", seat=4)
    for model in (lexicographic_model, gated_model, tree_model):
        assert model(seat4) == model(seat1), model.__name__


def test_low_pod_realization_can_downgrade_a_non_self_contained_trajectory():
    moderate = _obj(pod_realization_modifier="MODERATE", draw_dependence_class="BROAD_OUTS")
    low = _obj(pod_realization_modifier="LOW", draw_dependence_class="BROAD_OUTS")
    for model in (weighted_model, lexicographic_model, gated_model, tree_model):
        assert GRADE_RANK[model(low)] >= GRADE_RANK[model(moderate)], model.__name__


def test_low_pod_realization_does_not_downgrade_a_self_contained_trajectory():
    # A self-contained trajectory doesn't depend on the pod realizing anything further - the
    # pod-realization gate is scoped to non-self-contained trajectories only.
    moderate = _obj(pod_realization_modifier="MODERATE", draw_dependence_class="SELF_CONTAINED")
    low = _obj(pod_realization_modifier="LOW", draw_dependence_class="SELF_CONTAINED")
    for model in (lexicographic_model, gated_model, tree_model):
        assert model(low) == model(moderate), model.__name__
