"""SIM-001 MULL-005 — trajectory-first engine extension regression tests.

Proves the new engine capabilities added for MULL-005 (tutor library-search resolution, and
whatever else this phase adds) before any trajectory-tier analysis is trusted to run on top of
them.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import random  # noqa: E402

from opening_hand_policy import HandState, LandInPlay, develop_turn  # noqa: E402

FAKE_CARDS = {
    "Command Tower": {"name": "Command Tower", "type": "Land", "mana_cost": "", "cmc": 0},
    "Bayou": {"name": "Bayou", "type": "Land — Swamp Forest", "mana_cost": "", "cmc": 0},
    "Demonic Tutor": {"name": "Demonic Tutor", "type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2},
    "Rhystic Study": {"name": "Rhystic Study", "type": "Enchantment", "mana_cost": "{2}{U}", "cmc": 3},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Filler Card": {"name": "Filler Card", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
}


def _minimal_state(hand, library):
    return HandState(list(hand), list(library), on_play=True, rng=random.Random(1), cards=FAKE_CARDS)


# ---- 1. default (unforced) tutor resolution is a no-op - byte-for-byte unchanged pre-MULL-005 ----
def test_default_tutor_cast_does_not_fetch_anything():
    # Filler Card sits at library index 0 so T2's own natural draw doesn't confound the test by
    # drawing the would-be tutor target on its own, independent of tutor resolution.
    state = _minimal_state(
        hand=["Demonic Tutor", "Bayou", "Command Tower"],
        library=["Filler Card", "Sol Ring", "Rhystic Study"],
    )
    develop_turn(state, FAKE_CARDS)  # T1: land drop only, Demonic Tutor uncastable (needs 2 mana)
    develop_turn(state, FAKE_CARDS)  # T2: second land + natural draw, now Demonic Tutor castable
    assert "Demonic Tutor" not in state.hand, "the tutor should have been cast"
    assert "Sol Ring" not in state.hand and "Rhystic Study" not in state.hand, \
        "without a forced_tutor_target, no card should ever be fetched into hand"
    assert "Sol Ring" in state.library and "Rhystic Study" in state.library


# ---- 2. forced_tutor_target performs a real search: removes from library, adds to hand ----
def test_forced_tutor_target_fetches_real_card():
    state = _minimal_state(
        hand=["Demonic Tutor", "Bayou", "Command Tower"],
        library=["Filler Card", "Sol Ring", "Rhystic Study"],
    )
    develop_turn(state, FAKE_CARDS)
    develop_turn(state, FAKE_CARDS, forced_tutor_target="Sol Ring")
    assert "Sol Ring" in state.hand
    assert "Sol Ring" not in state.library
    assert "Rhystic Study" in state.library, "only the forced target should be fetched"


# ---- 3. forced_tutor_target for a card NOT in the library is a safe no-op ----
def test_forced_tutor_target_not_in_library_is_noop():
    state = _minimal_state(
        hand=["Demonic Tutor", "Bayou", "Command Tower"],
        library=["Filler Card"],
    )
    develop_turn(state, FAKE_CARDS)
    develop_turn(state, FAKE_CARDS, forced_tutor_target="Sol Ring")  # not in library
    assert "Sol Ring" not in state.hand
    assert "Demonic Tutor" not in state.hand, "the tutor still resolves/casts normally"
