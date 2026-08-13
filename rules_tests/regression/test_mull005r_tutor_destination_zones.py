"""SIM-001 MULL-005R — tutor destination-zone correctness fix.

MULL-005 put every forced tutor target into HAND uniformly. Real Oracle text:
Vampiric Tutor/Imperial Seal/Enlightened Tutor put the found card on TOP OF LIBRARY - not
accessible until drawn on a LATER turn. Demonic Tutor genuinely puts it into hand.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, develop_turn  # noqa: E402

FAKE_CARDS = {
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Vampiric Tutor": {"name": "Vampiric Tutor", "type": "Instant", "mana_cost": "{B}", "cmc": 1},
    "Demonic Tutor": {"name": "Demonic Tutor", "type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2},
    "Rhystic Study": {"name": "Rhystic Study", "type": "Enchantment", "mana_cost": "{2}{U}", "cmc": 3},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Filler Card": {"name": "Filler Card", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
}


def test_vampiric_tutor_puts_target_on_top_of_library_not_hand():
    state = HandState(["Vampiric Tutor", "Underground Sea"], ["Filler Card", "Sol Ring", "Rhystic Study"],
                       on_play=True, rng=random.Random(1), cards=FAKE_CARDS)
    develop_turn(state, FAKE_CARDS, forced_tutor_target="Sol Ring")
    assert "Sol Ring" not in state.hand, "Vampiric Tutor must NOT put the target directly into hand"
    assert state.library[0] == "Sol Ring", "target must be on top of library, accessible only next draw"


def test_vampiric_tutor_target_reaches_hand_only_after_next_draw():
    state = HandState(["Vampiric Tutor", "Underground Sea", "Underground Sea"],
                       ["Filler Card", "Sol Ring", "Rhystic Study"],
                       on_play=True, rng=random.Random(1), cards=FAKE_CARDS)
    develop_turn(state, FAKE_CARDS, forced_tutor_target="Sol Ring")  # T1: tutor resolves, Sol Ring -> library top
    assert "Sol Ring" not in state.hand
    actions = develop_turn(state, FAKE_CARDS)  # T2: natural draw step should now draw Sol Ring
    assert ("draw", "Sol Ring") in actions, "Sol Ring must be drawn (not already in hand) exactly one turn later"
    # the greedy policy then immediately casts the cheap Sol Ring it just drew, same turn - that's
    # expected (it's live now), the point being tested is that it was NOT live a turn earlier.
    assert (1, "Sol Ring", "engine") not in state.cast_log
    assert (2, "Sol Ring", "paid_accel") in state.cast_log


def test_demonic_tutor_still_puts_target_directly_into_hand():
    state = HandState(["Demonic Tutor", "Underground Sea", "Underground Sea"],
                       ["Filler Card", "Sol Ring", "Rhystic Study"],
                       on_play=True, rng=random.Random(1), cards=FAKE_CARDS)
    develop_turn(state, FAKE_CARDS)
    develop_turn(state, FAKE_CARDS, forced_tutor_target="Sol Ring")
    assert "Sol Ring" in state.hand


def test_unforced_vampiric_tutor_is_still_inert_no_regression():
    state = HandState(["Vampiric Tutor", "Underground Sea"], ["Filler Card", "Sol Ring", "Rhystic Study"],
                       on_play=True, rng=random.Random(1), cards=FAKE_CARDS)
    develop_turn(state, FAKE_CARDS)
    assert "Sol Ring" not in state.hand
    assert state.library[0] != "Sol Ring", "no target forced - library order must be untouched"
