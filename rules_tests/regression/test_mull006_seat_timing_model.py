"""SIM-001 MULL-006 section 6 — seat-adjusted timing (new dimension #1).

Proves the turn-order geometry is exact for all 4 seats, the three realization-timing classes
compute correct opponent-turn/window counts, and the assignment's own named examples (T1
Mastermind Seat 1 vs Seat 4 are not equivalent; T2 engine Seat 1 vs Seat 4 should not receive
identical contextual value) hold.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from seat_timing_model import (  # noqa: E402
    opponent_turns_before, opponent_action_windows_before, seat_adjusted_timing,
    REALIZATION_TIMING_CLASS, TIMING_PROVENANCE, ACTION_WINDOWS_PER_OPPONENT_TURN,
)
from engine_strength_prior import ENGINE_STRENGTH_PRIOR  # noqa: E402


def test_seat1_turn1_has_zero_opponent_turns_before():
    assert opponent_turns_before(1, 1) == 0


def test_seat4_turn1_has_three_opponent_turns_before():
    assert opponent_turns_before(1, 4) == 3


def test_seat1_turn2_has_three_opponent_turns_before():
    assert opponent_turns_before(2, 1) == 3


def test_seat4_turn2_has_six_opponent_turns_before():
    assert opponent_turns_before(2, 4) == 6


def test_opponent_turns_before_is_monotonic_in_seat():
    for turn in (1, 2, 3):
        counts = [opponent_turns_before(turn, s) for s in (1, 2, 3, 4)]
        assert counts == sorted(counts)
        assert len(set(counts)) == 4


def test_invalid_seat_raises():
    import pytest
    with pytest.raises(ValueError):
        opponent_turns_before(1, 5)
    with pytest.raises(ValueError):
        opponent_turns_before(1, 0)


def test_action_windows_are_turns_times_convention_constant():
    assert opponent_action_windows_before(2, 3) == opponent_turns_before(2, 3) * ACTION_WINDOWS_PER_OPPONENT_TURN


def test_every_tracked_engine_has_a_realization_timing_class():
    assert set(REALIZATION_TIMING_CLASS) == set(ENGINE_STRENGTH_PRIOR)


def test_immediate_opponent_turn_engines_realize_before_our_next_turn():
    for name in ("Rhystic Study", "Mystic Remora", "Esper Sentinel", "Smothering Tithe",
                 "Faerie Mastermind", "Archivist of Oghma", "Heartwood Storyteller", "Runic Armasaur"):
        result = seat_adjusted_timing(name, 1, 1)
        assert result["realization_timing_class"] == "IMMEDIATE_OPPONENT_TURN"
        assert result["value_generated_before_our_next_turn"] is True
        # earliest possible realization is exactly one opponent turn after deployment
        assert result["opponent_turns_before_first_possible_realization"] == result["opponent_turns_before_deployment"] + 1


def test_sylvan_library_never_realizes_before_our_next_turn():
    for seat in (1, 2, 3, 4):
        result = seat_adjusted_timing("Sylvan Library", 2, seat)
        assert result["realization_timing_class"] == "OWN_NEXT_DRAW_STEP"
        assert result["value_generated_before_our_next_turn"] is False
        assert result["opponent_turns_before_first_possible_realization"] == result["opponent_turns_before_deployment"] + 3


def test_functional_pod_and_survival_realize_same_turn_as_deployment():
    for name in ("Birthing Pod", "Survival of the Fittest"):
        result = seat_adjusted_timing(name, 1, 4)
        assert result["realization_timing_class"] == "OWN_TURN_DEPENDENT"
        assert result["opponent_turns_before_first_possible_realization"] == result["opponent_turns_before_deployment"]
        assert result["value_generated_before_our_next_turn"] is True


def test_t1_mastermind_seat1_vs_seat4_are_not_equivalent():
    # The assignment's own named example: same engine, same personal turn, different seat, must
    # produce materially different exposure/realization windows.
    seat1 = seat_adjusted_timing("Faerie Mastermind", 1, 1)
    seat4 = seat_adjusted_timing("Faerie Mastermind", 1, 4)
    assert seat1["opponent_turns_before_deployment"] != seat4["opponent_turns_before_deployment"]
    assert seat1["opponent_turns_before_first_possible_realization"] != seat4["opponent_turns_before_first_possible_realization"]
    assert seat4["opponent_turns_before_deployment"] - seat1["opponent_turns_before_deployment"] == 3


def test_t2_engine_seat1_vs_seat4_not_automatically_identical():
    seat1 = seat_adjusted_timing("Rhystic Study", 2, 1)
    seat4 = seat_adjusted_timing("Rhystic Study", 2, 4)
    assert seat1 != seat4
    assert seat4["opponent_turns_before_deployment"] - seat1["opponent_turns_before_deployment"] == 3


def test_card_draw_engines_flag_possible_live_interaction_others_do_not():
    remora = seat_adjusted_timing("Mystic Remora", 1, 1)
    assert remora["newly_generated_card_could_become_live_interaction_before_our_next_turn"] == "POSSIBLE_CONTENTS_UNKNOWN"
    tithe = seat_adjusted_timing("Smothering Tithe", 1, 1)  # generates mana, not a card
    assert tithe["newly_generated_card_could_become_live_interaction_before_our_next_turn"] == "NOT_APPLICABLE_NOT_A_CARD_DRAW_TRIGGER"
    library = seat_adjusted_timing("Sylvan Library", 2, 1)
    assert library["newly_generated_card_could_become_live_interaction_before_our_next_turn"] == "NOT_POSSIBLE_BEFORE_OWN_NEXT_TURN"


def test_unrecognized_engine_returns_none():
    assert seat_adjusted_timing("Abhorrent Oculus", 1, 1) is None
    assert seat_adjusted_timing("Some Random Card", 1, 1) is None


def test_provenance_label_is_model_derived():
    assert TIMING_PROVENANCE == "MODEL_DERIVED"
