"""SIM-001 MULL-006 section 7 — draw dependence / outs, new dimension #2.

Proves the SELF_CONTAINED / BROAD_OUTS / NARROW_OUTS / EXACT_OR_NEAR_EXACT classification, the
hypergeometric outs math, the fetch/tutor "self-contained via a hand card" carve-outs, and the
assignment's own named example (T1 Birds -> T2 Rhystic with land already present is materially
different from the same line needing a land draw).
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, LandInPlay  # noqa: E402
from draw_dependence_model import (  # noqa: E402
    classify_trajectory_draw_dependence, hypergeometric_at_least_one, _draws_by_turn,
    _classify_outs, DEPENDENCE_PROVENANCE,
)

FAKE_CARDS = {
    "Llanowar Elves": {"name": "Llanowar Elves", "type": "Creature — Elf Druid", "mana_cost": "{G}", "cmc": 1},
    "Rhystic Study": {"name": "Rhystic Study", "type": "Enchantment", "mana_cost": "{2}{U}", "cmc": 3},
    "Forest": {"name": "Forest", "type": "Basic Land — Forest", "mana_cost": "", "cmc": 0},
    "Island": {"name": "Island", "type": "Basic Land — Island", "mana_cost": "", "cmc": 0},
    "Tropical Island": {"name": "Tropical Island", "type": "Land — Island Forest", "mana_cost": "", "cmc": 0},
    "Wooded Foothills": {"name": "Wooded Foothills", "type": "Land", "mana_cost": "", "cmc": 0},
    "Enlightened Tutor": {"name": "Enlightened Tutor", "type": "Instant", "mana_cost": "{W}", "cmc": 1},
    "Sylvan Library": {"name": "Sylvan Library", "type": "Enchantment", "mana_cost": "{G}", "cmc": 1},
}
# A big enough filler pool so remaining_library_size is realistic (99-card singleton deck).
for i in range(91):
    FAKE_CARDS[f"Filler {i}"] = {"name": f"Filler {i}", "type": "Instant", "mana_cost": "{1}", "cmc": 1}
DECK_SIZE = len(FAKE_CARDS)  # 99


def _state(opening_hand):
    return HandState(opening_hand, [], on_play=True, rng=random.Random(0), cards=FAKE_CARDS)


def test_self_contained_when_everything_used_was_in_opening_hand():
    hand = ["Llanowar Elves", "Rhystic Study", "Forest", "Island"] + [f"Filler {i}" for i in range(3)]
    state = _state(hand)
    state.lands.append(LandInPlay("Forest", 1))
    state.lands.append(LandInPlay("Island", 2))
    state.cast_log.append((2, "Rhystic Study", "engine"))
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["overall_classification"] == "SELF_CONTAINED"
    assert result["dependency_count"] == 0


def test_t1_birds_t2_rhystic_with_second_land_present_is_self_contained():
    # The assignment's own named example, first half.
    hand = ["Llanowar Elves", "Rhystic Study", "Island", "Island"] + [f"Filler {i}" for i in range(3)]
    state = _state(hand)
    state.lands.append(LandInPlay("Island", 1))
    state.lands.append(LandInPlay("Island", 2))
    state.cast_log.append((2, "Rhystic Study", "engine"))
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["overall_classification"] == "SELF_CONTAINED"


def test_t1_birds_t2_rhystic_needing_a_land_draw_is_not_self_contained():
    # The assignment's own named example, second half: same line, but the second land was NOT in
    # the opening hand - a genuine draw dependency.
    hand = ["Llanowar Elves", "Rhystic Study", "Island"] + [f"Filler {i}" for i in range(4)]
    state = _state(hand)
    state.lands.append(LandInPlay("Island", 1))
    state.lands.append(LandInPlay("Tropical Island", 2))  # drawn, not in hand, no fetch cracked
    state.cast_log.append((2, "Rhystic Study", "engine"))
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["overall_classification"] != "SELF_CONTAINED"
    dep = result["dependencies"][0]
    assert dep["slot"] == "supporting_land"
    assert dep["source"] == "natural_draw"
    assert dep["outs_type"] == "any_land"


def test_land_from_hand_held_cracked_fetch_is_self_contained():
    hand = ["Llanowar Elves", "Rhystic Study", "Wooded Foothills"] + [f"Filler {i}" for i in range(4)]
    state = _state(hand)
    state.lands.append(LandInPlay("Tropical Island", 1))  # fetched target, not itself in hand
    state.graveyard.append("Wooded Foothills")  # the hand fetch was cracked to find it
    state.cast_log.append((1, "Rhystic Study", "engine"))
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 1, DECK_SIZE, True)
    assert result["overall_classification"] == "SELF_CONTAINED"


def test_engine_card_drawn_naturally_is_exact_or_near_exact():
    hand = ["Llanowar Elves", "Forest", "Island"] + [f"Filler {i}" for i in range(4)]
    state = _state(hand)
    state.lands.append(LandInPlay("Forest", 1))
    state.lands.append(LandInPlay("Island", 2))
    state.cast_log.append((2, "Rhystic Study", "engine"))  # not in hand, no tutor cast
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["overall_classification"] == "EXACT_OR_NEAR_EXACT"
    dep = next(d for d in result["dependencies"] if d["slot"] == "engine_card")
    assert dep["outs_count"] == 1
    assert dep["source"] == "natural_draw"


def test_hand_held_tutor_cast_before_makes_engine_self_contained():
    hand = ["Enlightened Tutor", "Forest", "Island"] + [f"Filler {i}" for i in range(4)]
    state = _state(hand)
    state.lands.append(LandInPlay("Forest", 1))
    state.lands.append(LandInPlay("Island", 2))
    state.cast_log.append((1, "Enlightened Tutor", "tutor"))
    state.cast_log.append((2, "Rhystic Study", "engine"))  # found by the tutor, cast normally later
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["overall_classification"] == "SELF_CONTAINED"


def test_pod_found_class_is_self_contained_not_a_natural_draw():
    hand = ["Forest", "Island"] + [f"Filler {i}" for i in range(5)]
    state = _state(hand)
    state.lands.append(LandInPlay("Forest", 1))
    state.lands.append(LandInPlay("Island", 2))
    state.cast_log.append((2, "Rhystic Study", "pod_found"))
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["overall_classification"] == "SELF_CONTAINED"


def test_none_tier_engine_returns_none():
    hand = [f"Filler {i}" for i in range(7)]
    state = _state(hand)
    assert classify_trajectory_draw_dependence(state, FAKE_CARDS, None, None, DECK_SIZE, True) is None


def test_multiple_dependency_slots_report_overlap_flag():
    hand = ["Forest"] + [f"Filler {i}" for i in range(6)]
    state = _state(hand)
    state.lands.append(LandInPlay("Forest", 1))
    state.lands.append(LandInPlay("Island", 2))  # natural draw land
    state.cast_log.append((2, "Rhystic Study", "engine"))  # natural draw engine card too
    result = classify_trajectory_draw_dependence(state, FAKE_CARDS, "Rhystic Study", 2, DECK_SIZE, True)
    assert result["dependency_count"] == 2
    assert result["multiple_dependency_classes_overlap"] is True
    assert result["overall_classification"] == "EXACT_OR_NEAR_EXACT"  # worst of the two governs


def test_hypergeometric_zero_outs_is_zero_probability():
    assert hypergeometric_at_least_one(90, 0, 3) == 0.0


def test_hypergeometric_known_small_case():
    # N=10 cards, K=2 outs, k=1 draw -> P = K/N = 0.2 (single-draw case is exactly K/N).
    assert abs(hypergeometric_at_least_one(10, 2, 1) - 0.2) < 1e-9


def test_hypergeometric_all_outs_is_certain():
    assert hypergeometric_at_least_one(10, 10, 3) == 1.0


def test_draws_by_turn_matches_develop_turn_draw_skip_rule():
    assert _draws_by_turn(1, on_play=True) == 0   # turn 1 on the play: no draw
    assert _draws_by_turn(2, on_play=True) == 1
    assert _draws_by_turn(3, on_play=True) == 2
    assert _draws_by_turn(1, on_play=False) == 1  # turn 1 on the draw: does draw
    assert _draws_by_turn(3, on_play=False) == 3


def test_outs_classification_boundaries():
    assert _classify_outs(1, 90) == "EXACT_OR_NEAR_EXACT"
    assert _classify_outs(2, 90) == "EXACT_OR_NEAR_EXACT"
    assert _classify_outs(5, 90) == "NARROW_OUTS"     # 5/90 ~ 5.6% < 15%, and > 2
    assert _classify_outs(20, 90) == "BROAD_OUTS"      # 20/90 ~ 22% >= 15%


def test_provenance_label_is_simulation_measured():
    assert DEPENDENCE_PROVENANCE == "SIMULATION_MEASURED"
