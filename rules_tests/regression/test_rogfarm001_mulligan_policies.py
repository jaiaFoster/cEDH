"""SIM-ROGFARM-001 Stage 2 — regression tests for the 3 pre-registered mulligan policies and the
London-bottoming/free-mulligan harness."""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import rogfarm001_cards as rc  # noqa: E402
import rogfarm001_mulligan_policies as mp  # noqa: E402

BASE_CARDS = {
    "Underground Sea": {"type": "Land — Island Swamp", "mana_cost": "", "cmc": 0, "text": ""},
    "Badlands": {"type": "Land — Swamp Mountain", "mana_cost": "", "cmc": 0, "text": ""},
    "Sol Ring": {"type": "Artifact", "mana_cost": "{1}", "cmc": 1, "text": ""},
    "Lightning Bolt": {"type": "Instant", "mana_cost": "{R}", "cmc": 1, "text": ""},
}
CARDS = rc.all_cards_dict(BASE_CARDS)


def setup_module(_module):
    rc.install_new_card_tables()


def teardown_module(_module):
    rc.uninstall_new_card_tables()


def test_p1_rejects_hand_with_no_engine_tutor_or_accel():
    features = mp.hand_features(["Underground Sea", "Badlands", "Lightning Bolt"], CARDS)
    assert mp.p1_keep(features) is False


def test_p1_accepts_hand_with_early_engine():
    hand = ["Underground Sea", "Badlands", "Narset, Parter of Veils", "Lightning Bolt"]
    features = mp.hand_features(hand, CARDS)
    assert mp.p1_keep(features) is True


def test_land_count_bounds_reject_flood_and_screw():
    screwed = mp.hand_features(["Underground Sea"], CARDS)
    assert mp.p1_keep(screwed) is False
    assert mp.p2_keep(screwed) is False
    assert mp.p3_keep(screwed) is False
    flooded = mp.hand_features(["Underground Sea"] * 6, CARDS)
    assert mp.p1_keep(flooded) is False


def test_p2_rejects_conditional_only_hand():
    # Only a wheel + wheel payoff, nothing else live - a real "conditional blank" hand.
    hand = ["Underground Sea", "Badlands", "Wheel of Fortune", "Narset, Parter of Veils"]
    features = mp.hand_features(hand, CARDS)
    assert mp.p2_keep(features) is False


def test_p2_accepts_hand_with_win_access():
    hand = ["Underground Sea", "Badlands", "Underworld Breach", "Lion's Eye Diamond", "Brain Freeze"]
    features = mp.hand_features(hand, CARDS)
    assert features["any_win_access"] is True
    assert mp.p2_keep(features) is True


def test_p3_requires_interaction_or_strong_win_access():
    hand_no_interaction_no_win = ["Underground Sea", "Badlands", "Sol Ring", "Narset, Parter of Veils"]
    features = mp.hand_features(hand_no_interaction_no_win, CARDS)
    assert mp.p3_keep(features) is False
    hand_with_interaction = ["Underground Sea", "Badlands", "Sol Ring", "Daze"]
    features2 = mp.hand_features(hand_with_interaction, CARDS)
    assert mp.p3_keep(features2) is True


def test_bottom_to_size_keeps_lands_up_to_target():
    hand = ["Underground Sea", "Badlands", "Underground Sea", "Sol Ring", "Lightning Bolt",
            "Lightning Bolt", "Lightning Bolt"]
    kept, bottomed = mp.bottom_to_size(hand, CARDS, 6)
    assert len(kept) == 6
    assert len(bottomed) == 1
    # a land-heavy hand should never bottom itself down to zero lands
    assert any(mp._is_land(c, CARDS) for c in kept)


def test_bottom_to_size_prefers_engines_over_filler():
    hand = ["Underground Sea", "Badlands", "Narset, Parter of Veils", "Lightning Bolt",
            "Lightning Bolt", "Lightning Bolt", "Lightning Bolt"]
    kept, bottomed = mp.bottom_to_size(hand, CARDS, 5)
    assert "Narset, Parter of Veils" in kept  # higher keep-value than plain filler


def test_bottom_to_size_noop_when_already_at_target():
    hand = ["Underground Sea", "Badlands", "Sol Ring"]
    kept, bottomed = mp.bottom_to_size(hand, CARDS, 7)
    assert kept == hand
    assert bottomed == []


def test_free_first_mulligan_does_not_bottom():
    # A policy that always mulligans forces mulligan_count=1 (the free mulligan) at max_mulligans=1,
    # confirming the returned hand size is still 7 (no bottoming on the first mulligan).
    lib = ["Underground Sea"] * 3 + ["Lightning Bolt"] * 4 + ["Sol Ring"] * 93
    rng = random.Random(0)
    kept, remaining_lib, mulls = mp.london_mulligan(
        lib, CARDS, rng, lambda f: False, on_play=True, max_mulligans=1,
    )
    assert mulls == 1
    assert len(kept) == 7  # free mulligan: still 7 cards, nothing bottomed


def test_second_mulligan_bottoms_one_card():
    lib = ["Underground Sea"] * 3 + ["Lightning Bolt"] * 4 + ["Sol Ring"] * 93
    rng = random.Random(1)
    kept, remaining_lib, mulls = mp.london_mulligan(
        lib, CARDS, rng, lambda f: False, on_play=True, max_mulligans=2,
    )
    assert mulls == 2
    assert len(kept) == 6  # second mulligan bottoms exactly 1


def test_london_mulligan_stops_once_policy_accepts():
    lib = ["Underground Sea"] * 4 + ["Narset, Parter of Veils"] + ["Lightning Bolt"] * 92
    rng = random.Random(2)
    kept, remaining_lib, mulls = mp.london_mulligan(
        lib, CARDS, rng, mp.p1_keep, on_play=True, max_mulligans=4,
    )
    features = mp.hand_features(kept, CARDS)
    assert mp.p1_keep(features) is True or mulls == 4
