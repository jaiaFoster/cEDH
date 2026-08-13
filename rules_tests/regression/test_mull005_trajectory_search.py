"""SIM-001 MULL-005 — bounded best-known trajectory search regression tests.

Confirms find_best_trajectory() actually reports two DIFFERENT things when they diverge (per the
assignment's explicit constraint not to conflate greedy-realized outcome with best-known achievable
outcome), and that greedy_result always stays byte-for-byte the same as the pre-MULL-005 line
(DEFAULT_PRIORITY, no forced tutor target).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from trajectory_search import find_best_trajectory  # noqa: E402

FAKE_CARDS = {
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Demonic Tutor": {"name": "Demonic Tutor", "type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Rhystic Study": {"name": "Rhystic Study", "type": "Enchantment", "mana_cost": "{2}{U}", "cmc": 3},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
    "Filler1": {"name": "Filler1", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
}


def test_greedy_fizzles_but_bounded_search_finds_tutor_to_engine_line():
    # Demonic Tutor with no forced target (the pre-MULL-005 greedy line) is cast and fizzles -
    # Tier D. The bounded search, trying disclosed candidate targets, should find that forcing
    # "Rhystic Study" reaches a real (if delayed to T3) engine trajectory - Tier C.
    hand = ["Demonic Tutor", "Underground Sea", "Underground Sea"]
    library = ["Filler Land"] * 5 + ["Rhystic Study"] + ["Sol Ring"] + ["Filler Land"] * 13

    greedy, best, tried = find_best_trajectory(hand, library, True, FAKE_CARDS, [])

    assert greedy["tier"] == "D", greedy
    assert greedy["mechanism"] == "none"

    assert best["tier"] == "C", best
    assert best["tier_engine"] == "Rhystic Study"
    assert best["mechanism"] == "tutor_to_engine"
    assert best["search_label"] == "tutor:Rhystic Study:DEFAULT_PRIORITY"
    assert tried > 1, "search should have tried more than just the greedy line"


def test_greedy_result_is_always_default_priority_no_forced_target():
    hand = ["Demonic Tutor", "Underground Sea", "Underground Sea"]
    library = ["Filler Land"] * 5 + ["Rhystic Study"] + ["Filler Land"] * 14
    greedy, best, tried = find_best_trajectory(hand, library, True, FAKE_CARDS, [])
    assert greedy["search_label"] == "greedy"


def test_no_tutor_in_hand_only_tries_the_greedy_line():
    # Without a tutor in hand, branching over tutor targets/priority variants is pointless - the
    # search should be a cheap no-op (1 candidate, greedy == best) rather than wastefully
    # re-simulating the same line under every priority variant.
    hand = ["Sol Ring", "Rhystic Study", "Underground Sea", "Underground Sea"]
    library = ["Filler Land"] * 20
    greedy, best, tried = find_best_trajectory(hand, library, True, FAKE_CARDS, [])
    assert tried == 1
    assert best is greedy
    assert greedy["tier"] == "A"
    assert greedy["mechanism"] == "rock_to_engine"
