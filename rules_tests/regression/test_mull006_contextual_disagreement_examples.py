"""SIM-001 MULL-006 section 23 — required disagreement examples A-G.

Proves each example-generating function returns structurally correct real-hand evidence for its
named comparison (not fabricated, not merely plausible-looking).
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from build_contextual_disagreement_examples import (  # noqa: E402
    example_A_strength_speed, example_C_draw_dependence, example_D_fragility,
    example_F_relevant_agency, example_G_mulligan_depth,
)
from strength_speed_matrix import GRADE_RANK  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
_NAMES = list(CARDS.keys())
_COMBOS = load_deterministic_combos()
DECK_SIZE = len(CARDS)


def test_example_a_t1_mastermind_outranks_t2_remora_type():
    result = example_A_strength_speed(_NAMES, CARDS, _COMBOS, True, random.Random(1), tries=8000)
    assert result is not None
    assert result["t1_mastermind_outranks"] is True
    assert GRADE_RANK[result["t1_mastermind_base_grade"]] < GRADE_RANK[result["t2_remora_type_base_grade"]]


def test_example_c_engine_card_is_a_natural_draw_dependency():
    result = example_C_draw_dependence(_NAMES, CARDS, _COMBOS, True, random.Random(2), tries=6000)
    assert result is not None
    assert result["tier_turn"] == 2
    assert any(d["slot"] == "engine_card" and d["source"] == "natural_draw" for d in result["dependency_detail"])
    assert result["tier_engine"] not in result["hand"]


def test_example_d_same_destination_different_resilience():
    result = example_D_fragility(_NAMES, CARDS, _COMBOS, True, random.Random(3), tries=8000)
    assert result is not None
    assert result["robust_hand"] != result["all_in_hand"]
    assert result["all_in_hand_collapses"] is True
    assert result["robust_second_best"] is not None


def test_example_f_relevant_agency_differs_across_archetypes():
    result = example_F_relevant_agency(_NAMES, CARDS, _COMBOS, True, random.Random(4), tries=6000)
    assert result is not None
    assert result["live_agency_score"] > 0
    assert result["relevant_agency_vs_rogsi"] != result["relevant_agency_vs_tayam"]


def test_example_g_grade_d_fails_size7_passes_size6_and_5():
    result = example_G_mulligan_depth(_NAMES, CARDS, _COMBOS, True, random.Random(5), DECK_SIZE, tries=8000)
    assert result is not None
    assert result["contextual_grade"] == "D"
    assert result["keep_at_7"] is False
    assert result["keep_at_6"] is True
    assert result["keep_at_5"] is True
