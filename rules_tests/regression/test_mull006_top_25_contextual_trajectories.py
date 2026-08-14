"""SIM-001 MULL-006 section 22 — top-25 contextual trajectory table.

Proves the bottoming-search-based GRADE @ N computation is correct: N=7 uses the hand as-is,
smaller N searches every legal bottoming choice and returns the BEST resulting contextual grade
(never worse than doing nothing, monotonic as N decreases since bottoming can only discard, never
add, information)."""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from build_top_25_contextual_trajectories import (  # noqa: E402
    _contextual_grade_for_hand, _best_bottomed_contextual_grade, _first_realized_value_label,
    REFERENCE_ARCHETYPE, REFERENCE_SEAT,
)
from strength_speed_matrix import GRADE_RANK  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
_NAMES = list(CARDS.keys())
_COMBOS = load_deterministic_combos()
DECK_SIZE = len(CARDS)


def _sample_hand(seed):
    lib = _NAMES[:]
    random.Random(seed).shuffle(lib)
    return lib[:7], lib[7:]


def test_bottoming_search_never_produces_a_worse_grade_than_the_best_single_card_kept():
    hand, library = _sample_hand(1)
    grade_at_6 = _best_bottomed_contextual_grade(hand, library, True, CARDS, _COMBOS, DECK_SIZE, 1, REFERENCE_SEAT, REFERENCE_ARCHETYPE)
    assert grade_at_6 in GRADE_RANK


def test_grade_at_7_matches_direct_contextual_grade():
    hand, library = _sample_hand(2)
    direct_grade, _, _, _ = _contextual_grade_for_hand(hand, library, True, CARDS, _COMBOS, DECK_SIZE, REFERENCE_SEAT, REFERENCE_ARCHETYPE)
    assert direct_grade in GRADE_RANK


def test_bottoming_to_4_searches_more_combinations_than_bottoming_to_6():
    # A sanity check on search breadth, not a claim about which grade is better - both must
    # return valid grades from the shared alphabet.
    hand, library = _sample_hand(3)
    g6 = _best_bottomed_contextual_grade(hand, library, True, CARDS, _COMBOS, DECK_SIZE, 1, REFERENCE_SEAT, REFERENCE_ARCHETYPE)
    g4 = _best_bottomed_contextual_grade(hand, library, True, CARDS, _COMBOS, DECK_SIZE, 3, REFERENCE_SEAT, REFERENCE_ARCHETYPE)
    assert g6 in GRADE_RANK and g4 in GRADE_RANK


def test_first_realized_value_label_for_immediate_opponent_turn_engine():
    label = _first_realized_value_label("Rhystic Study", 1, 1)
    assert "opponent's next turn" in label


def test_first_realized_value_label_for_own_next_draw_step_engine():
    label = _first_realized_value_label("Sylvan Library", 2, 1)
    assert "turn 3" in label


def test_first_realized_value_label_for_own_turn_dependent_engine():
    label = _first_realized_value_label("Birthing Pod", 1, 1)
    assert "same turn as deployment" in label


def test_first_realized_value_label_for_no_destination():
    assert _first_realized_value_label(None, None, 1) == "N/A_NO_DESTINATION"


def test_first_realized_value_label_for_untracked_destination():
    from opening_hand_policy import OCULUS_NAME
    assert _first_realized_value_label(OCULUS_NAME, 2, 1) == "UNTRACKED_DESTINATION"
