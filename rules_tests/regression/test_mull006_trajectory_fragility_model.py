"""SIM-001 MULL-006 section 8 — trajectory fragility / recovery, new dimension #3.

Proves the counterfactual-removal tracked fields and the ROBUST/RECOVERABLE/FRAGILE/ALL_IN
classification boundaries, including the assignment's own named examples: T2 Tithe with four
cards remaining differs from T2 Tithe from an exhausted hand; Pod with continuing creature fuel
differs from Pod whose only activation consumes the entire development plan.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, Perm, LandInPlay  # noqa: E402
from trajectory_fragility_model import assess_fragility, FRAGILITY_PROVENANCE  # noqa: E402

FAKE_CARDS = {
    "Smothering Tithe": {"name": "Smothering Tithe", "type": "Enchantment", "mana_cost": "{3}{W}", "cmc": 4},
    "Birthing Pod": {"name": "Birthing Pod", "type": "Artifact", "mana_cost": "{3}{G/P}", "cmc": 4},
    "Sylvan Library": {"name": "Sylvan Library", "type": "Enchantment", "mana_cost": "{G}", "cmc": 1},
    "Vanilla Creature": {"name": "Vanilla Creature", "type": "Creature — Bear", "mana_cost": "{2}{G}", "cmc": 3},
    "Chrome Mox": {"name": "Chrome Mox", "type": "Artifact", "mana_cost": "{0}", "cmc": 0},
    "Enlightened Tutor": {"name": "Enlightened Tutor", "type": "Instant", "mana_cost": "{W}", "cmc": 1},
    "Flusterstorm": {"name": "Flusterstorm", "type": "Instant", "mana_cost": "{U}", "cmc": 1},
    "Island": {"name": "Island", "type": "Basic Land — Island", "mana_cost": "", "cmc": 0},
}
for i in range(10):
    FAKE_CARDS[f"Filler {i}"] = {"name": f"Filler {i}", "type": "Instant", "mana_cost": "{1}", "cmc": 1}


def _state(hand, on_play=True):
    return HandState(hand, [], on_play=on_play, rng=random.Random(0), cards=FAKE_CARDS)


def test_t2_tithe_with_four_cards_remaining_is_not_fragile():
    hand = ["Smothering Tithe", "Island", "Filler 0", "Filler 1", "Filler 2", "Filler 3", "Filler 4"]
    state = _state(hand)
    state.hand = ["Filler 1", "Filler 2", "Filler 3", "Filler 4"]  # 4 cards remaining, unspent
    state.nonland_perms.append(Perm("Smothering Tithe", 2, False))
    result = assess_fragility(state, FAKE_CARDS, "Smothering Tithe", 2, True)
    assert result["cards_remaining"] == 4
    assert result["resilience_class"] in ("RECOVERABLE", "ROBUST")
    assert result["resilience_class"] != "FRAGILE"
    assert result["resilience_class"] != "ALL_IN"


def test_t2_tithe_from_exhausted_hand_is_fragile_or_all_in():
    hand = ["Smothering Tithe", "Island", "Filler 0", "Filler 1", "Filler 2", "Filler 3", "Filler 4"]
    state = _state(hand)
    state.hand = []  # entire hand committed
    state.nonland_perms.append(Perm("Smothering Tithe", 2, False))
    result = assess_fragility(state, FAKE_CARDS, "Smothering Tithe", 2, True)
    assert result["cards_remaining"] == 0
    assert result["resilience_class"] == "ALL_IN"
    assert result["hand_effectively_collapses"] is True


def test_pod_with_continuing_fuel_and_hand_left_is_more_resilient_than_exhausted_pod():
    hand = ["Birthing Pod", "Vanilla Creature", "Island", "Island", "Filler 0", "Filler 1", "Filler 2"]
    robust_state = _state(hand)
    robust_state.hand = ["Filler 0", "Filler 1", "Filler 2"]
    robust_state.nonland_perms.append(Perm("Birthing Pod", 1, False))
    robust_state.nonland_perms.append(Perm("Vanilla Creature", 1, True))  # fodder still on board
    robust_result = assess_fragility(robust_state, FAKE_CARDS, "Birthing Pod", 1, True)

    fragile_state = _state(hand)
    fragile_state.hand = []
    fragile_state.nonland_perms.append(Perm("Birthing Pod", 1, False))
    fragile_state.cast_log.append((1, "Vanilla Creature", "pod_found"))  # activation consumed everything
    fragile_result = assess_fragility(fragile_state, FAKE_CARDS, "Birthing Pod", 1, True)

    from trajectory_fragility_model import RESILIENCE_RANK
    assert RESILIENCE_RANK[robust_result["resilience_class"]] < RESILIENCE_RANK[fragile_result["resilience_class"]]
    assert fragile_result["creatures_sacrificed"] == 1
    assert robust_result["creatures_sacrificed"] == 0


def test_second_best_destination_already_on_board_yields_robust():
    hand = ["Smothering Tithe", "Sylvan Library", "Island", "Island", "Filler 0", "Filler 1", "Filler 2"]
    state = _state(hand)
    state.hand = ["Filler 0", "Filler 1", "Filler 2"]
    state.nonland_perms.append(Perm("Smothering Tithe", 2, False))
    state.nonland_perms.append(Perm("Sylvan Library", 1, False))
    result = assess_fragility(state, FAKE_CARDS, "Smothering Tithe", 2, True)
    assert result["second_best_destination_realized"] == "Sylvan Library"
    assert result["resilience_class"] == "ROBUST"
    assert result["time_until_next_development"] == 0


def test_weak_in_hand_fallback_is_recoverable_not_robust():
    hand = ["Smothering Tithe", "Enlightened Tutor", "Island", "Filler 0", "Filler 1", "Filler 2", "Filler 3"]
    state = _state(hand)
    state.hand = ["Enlightened Tutor", "Filler 1", "Filler 2"]
    state.nonland_perms.append(Perm("Smothering Tithe", 2, False))
    result = assess_fragility(state, FAKE_CARDS, "Smothering Tithe", 2, True)
    assert result["second_best_destination_realized"] is None
    assert result["weak_in_hand_fallback"] == "Enlightened Tutor"
    assert result["resilience_class"] == "RECOVERABLE"
    assert result["time_until_next_development"] == 3


def test_interaction_remaining_prevents_hand_collapse_flag():
    hand = ["Smothering Tithe", "Flusterstorm", "Island"] + [f"Filler {i}" for i in range(4)]
    state = _state(hand)
    state.hand = ["Flusterstorm"]  # 1 card left, but it's live interaction
    state.nonland_perms.append(Perm("Smothering Tithe", 2, False))
    result = assess_fragility(state, FAKE_CARDS, "Smothering Tithe", 2, True)
    assert result["interaction_remains"] is True
    assert result["hand_effectively_collapses"] is False
    assert result["cards_remaining"] == 1


def test_chrome_mox_imprint_and_permanent_mana_tracked():
    hand = ["Smothering Tithe", "Chrome Mox", "Island"] + [f"Filler {i}" for i in range(4)]
    state = _state(hand)
    state.hand = ["Filler 0", "Filler 1", "Filler 2", "Filler 3"]
    state.nonland_perms.append(Perm("Smothering Tithe", 2, False))
    state.nonland_perms.append(Perm("Chrome Mox", 1, False))
    state.exile.append("Filler 4")  # imprinted card
    state.lands.append(LandInPlay("Island", 1, tapped=False))
    result = assess_fragility(state, FAKE_CARDS, "Smothering Tithe", 2, True)
    assert result["mox_imprint_or_discard_costs"] == 1
    assert result["permanent_mana_remaining"] == 1


def test_none_tier_engine_returns_none():
    state = _state([f"Filler {i}" for i in range(7)])
    assert assess_fragility(state, FAKE_CARDS, None, None, True) is None


def test_resilience_rank_is_monotonic_robust_best():
    from trajectory_fragility_model import RESILIENCE_ORDER, RESILIENCE_RANK
    assert RESILIENCE_ORDER == ["ROBUST", "RECOVERABLE", "FRAGILE", "ALL_IN"]
    for i in range(len(RESILIENCE_ORDER) - 1):
        assert RESILIENCE_RANK[RESILIENCE_ORDER[i]] < RESILIENCE_RANK[RESILIENCE_ORDER[i + 1]]


def test_provenance_label_is_simulation_measured():
    assert FRAGILITY_PROVENANCE == "SIMULATION_MEASURED"
