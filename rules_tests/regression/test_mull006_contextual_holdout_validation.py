"""SIM-001 MULL-006 — contextual holdout validation.

Proves classify_disagreement_cause()'s priority-ordered attribution matches
contextual_valuation_models.gated_model's own gate-evaluation order exactly, so every
disagreement this audit reports is attributable to the SAME gate that actually fired.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_contextual_holdout_validation import classify_disagreement_cause, DISAGREEMENT_CAUSES_ORDER  # noqa: E402


def _obj(**overrides):
    base = {
        "destination": "Rhystic Study", "draw_dependence_class": "SELF_CONTAINED",
        "probability_of_trajectory": 1.0, "resilience_class": "RECOVERABLE",
        "relevant_agency": 0, "pod_realization_modifier": "MODERATE", "seat": 1,
    }
    base.update(overrides)
    return base


def test_draw_dependence_gate_takes_priority_over_all_in():
    obj = _obj(draw_dependence_class="EXACT_OR_NEAR_EXACT", probability_of_trajectory=0.05,
               resilience_class="ALL_IN")
    assert classify_disagreement_cause(obj) == "draw_dependence_gate"


def test_all_in_resilience_gate_fires_when_draw_dependence_gate_does_not():
    obj = _obj(resilience_class="ALL_IN", draw_dependence_class="SELF_CONTAINED")
    assert classify_disagreement_cause(obj) == "all_in_resilience_gate"


def test_seat_exposure_gate_requires_excess_exposure_and_fragile_resilience():
    obj = _obj(seat=4, resilience_class="FRAGILE")
    assert classify_disagreement_cause(obj) == "seat_exposure_gate"
    obj_ok_seat = _obj(seat=1, resilience_class="FRAGILE")
    assert classify_disagreement_cause(obj_ok_seat) != "seat_exposure_gate"


def test_pod_realization_gate_requires_low_and_non_self_contained():
    obj = _obj(pod_realization_modifier="LOW", draw_dependence_class="BROAD_OUTS")
    assert classify_disagreement_cause(obj) == "pod_realization_gate"
    obj_self_contained = _obj(pod_realization_modifier="LOW", draw_dependence_class="SELF_CONTAINED")
    assert classify_disagreement_cause(obj_self_contained) != "pod_realization_gate"


def test_agency_upgrade_only_when_no_other_gate_fires():
    obj = _obj(relevant_agency=3)
    assert classify_disagreement_cause(obj) == "agency_upgrade"


def test_unclassified_when_nothing_matches():
    obj = _obj()
    assert classify_disagreement_cause(obj) == "unclassified"


def test_all_causes_list_matches_gate_evaluation_order():
    assert DISAGREEMENT_CAUSES_ORDER == [
        "draw_dependence_gate", "all_in_resilience_gate", "seat_exposure_gate",
        "pod_realization_gate", "agency_upgrade", "unclassified",
    ]
