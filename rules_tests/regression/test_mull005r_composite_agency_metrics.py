"""SIM-001 MULL-005R — ENGINE_PLUS_LIVE_FREE_INTERACTION / ENGINE_PLUS_LIVE_PAID_INTERACTION
composite metrics (assignment section 9 / t1_t3_trajectory_audit.json AGENCY-001).

Tests _finish() directly against controlled snapshot dicts, rather than fighting the greedy
policy's tendency to opportunistically cast any freely-pitchable interaction the moment it's
reachable (a real, pre-existing, documented characteristic of this project's DEFAULT_PRIORITY
model, not something this test is trying to change) - isolates the metric's own logic.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from trajectory_grading import _finish  # noqa: E402


class _FakeState:
    def __init__(self):
        self.cast_log = [(1, "Sol Ring", "paid_accel"), (2, "Rhystic Study", "engine")]
        self.temp_mana_used_log = []


BASE_M3 = {
    "total_mana": 5, "cards_in_hand": 1, "tutor_castable": False,
    "two_plus_engines_active": False,
    "deterministic_win_available": False, "one_action_from_verified_win": False,
}


def _m3(has_live_interaction, free_or_alt_cost_interaction_live, **combo_overrides):
    m = dict(BASE_M3)
    m["has_live_interaction"] = has_live_interaction
    m["free_or_alt_cost_interaction_live"] = free_or_alt_cost_interaction_live
    m.update(combo_overrides)
    return m


def test_engine_plus_free_interaction_flag_true_when_both_present():
    state = _FakeState()
    m3 = _m3(has_live_interaction=True, free_or_alt_cost_interaction_live=True)
    result = _finish("A", "Rhystic Study", 2, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_live_free_interaction"] is True
    assert result["resource_cost"]["engine_plus_live_paid_interaction"] is False
    assert "free_interaction" in result["mechanism"]


def test_engine_plus_paid_interaction_flag_true_when_interaction_not_free():
    state = _FakeState()
    m3 = _m3(has_live_interaction=True, free_or_alt_cost_interaction_live=False)
    result = _finish("A", "Rhystic Study", 2, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_live_paid_interaction"] is True
    assert result["resource_cost"]["engine_plus_live_free_interaction"] is False
    assert "paid_interaction" in result["mechanism"]


def test_no_destination_never_sets_either_composite_flag_even_with_interaction():
    # A hand with only interaction and no engine (D/F tier, or mechanism "none") must not be
    # credited with "engine + interaction" - there is no engine.
    state = _FakeState()
    state.cast_log = []
    m3 = _m3(has_live_interaction=True, free_or_alt_cost_interaction_live=True)
    result = _finish("D", None, None, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_live_free_interaction"] is False
    assert result["resource_cost"]["engine_plus_live_paid_interaction"] is False
    assert result["mechanism"] == "interaction_only"


def test_no_interaction_at_all_sets_neither_flag():
    state = _FakeState()
    m3 = _m3(has_live_interaction=False, free_or_alt_cost_interaction_live=False)
    result = _finish("A", "Rhystic Study", 2, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_live_free_interaction"] is False
    assert result["resource_cost"]["engine_plus_live_paid_interaction"] is False
    assert "interaction" not in result["mechanism"]


def test_engine_plus_verified_combo_proximity_true_when_both_present():
    # COMBO-001 / assignment section 11: verified combo proximity is an upside modifier ON TOP OF
    # a real destination, sourced only from the existing deterministic_win_available /
    # one_action_from_verified_win flags (themselves backed by the verified-combo registry).
    state = _FakeState()
    m3 = _m3(has_live_interaction=False, free_or_alt_cost_interaction_live=False,
              one_action_from_verified_win=True)
    result = _finish("A", "Rhystic Study", 2, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_verified_combo_proximity"] is True


def test_verified_combo_proximity_without_a_real_destination_does_not_set_the_flag():
    # A D/F-tier hand (no mechanism) must not be credited "engine + combo proximity" - there is no
    # engine. Combo proximity alone is never the primary keep destination.
    state = _FakeState()
    state.cast_log = []
    m3 = _m3(has_live_interaction=False, free_or_alt_cost_interaction_live=False,
              deterministic_win_available=True)
    result = _finish("D", None, None, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_verified_combo_proximity"] is False


def test_no_combo_proximity_sets_the_flag_false():
    state = _FakeState()
    m3 = _m3(has_live_interaction=False, free_or_alt_cost_interaction_live=False)
    result = _finish("A", "Rhystic Study", 2, state, {}, m3, m3, m3)
    assert result["resource_cost"]["engine_plus_verified_combo_proximity"] is False
