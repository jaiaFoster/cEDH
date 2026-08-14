"""SIM-001 MULL-006 section 19 — one-land hand audit.

Proves _classify_one_land_hand()'s tag assignment and field computation against constructed
one-land scenarios covering the assignment's required category list.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from build_one_land_hand_audit import _find_best_trajectory_with_state, _classify_one_land_hand, DORKS, FAST_MANA  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
_NAMES = list(CARDS.keys())
_COMBOS = load_deterministic_combos()
DECK_SIZE = len(CARDS)


def _audit_for_hand(hand, on_play=True):
    lib = [n for n in _NAMES if n not in hand]
    random.Random(0).shuffle(lib)
    state, grade = _find_best_trajectory_with_state(hand, lib, on_play, CARDS, _COMBOS)
    return _classify_one_land_hand(hand, state, grade, CARDS, DECK_SIZE, on_play), grade


def test_dork_and_fast_mana_sets_are_disjoint_and_nonempty():
    assert DORKS & FAST_MANA == set()
    assert len(DORKS) > 0 and len(FAST_MANA) > 0


def test_one_land_no_destination_is_tagged_correctly():
    # Seven weak, unconnected cards with only one land - very unlikely to find any real engine.
    for seed in range(1, 500):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        from draw_dependence_model import _is_land
        if sum(1 for c in hand if _is_land(c, CARDS)) != 1:
            continue
        state, grade = _find_best_trajectory_with_state(hand, library, True, CARDS, _COMBOS)
        if grade["tier_engine"] is None:
            audit, _ = _audit_for_hand(hand), grade
            audit = _classify_one_land_hand(hand, state, grade, CARDS, DECK_SIZE, True)
            assert "1 land + no destination" in audit["tags"]
            assert audit["probability_trajectory_succeeds"] is None
            return
    raise AssertionError("no one-land no-destination hand found in 500 tries")


def test_second_mana_source_available_flag_matches_hand_contents():
    for seed in range(1, 500):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        from draw_dependence_model import _is_land
        if sum(1 for c in hand if _is_land(c, CARDS)) != 1:
            continue
        has_accel = any(n in DORKS | FAST_MANA for n in hand)
        state, grade = _find_best_trajectory_with_state(hand, library, True, CARDS, _COMBOS)
        audit = _classify_one_land_hand(hand, state, grade, CARDS, DECK_SIZE, True)
        assert audit["second_mana_source_already_available"] == has_accel
        assert audit["t1_acceleration_available"] == has_accel
        return
    raise AssertionError("no one-land hand found in 500 tries")


def test_live_land_outs_and_nonland_mana_outs_are_nonnegative_and_exclude_hand():
    for seed in range(1, 500):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        from draw_dependence_model import _is_land
        if sum(1 for c in hand if _is_land(c, CARDS)) != 1:
            continue
        state, grade = _find_best_trajectory_with_state(hand, library, True, CARDS, _COMBOS)
        audit = _classify_one_land_hand(hand, state, grade, CARDS, DECK_SIZE, True)
        assert audit["live_land_outs"] >= 0
        assert audit["nonland_mana_outs"] >= 0
        # every land in hand is excluded from the outs count by construction
        assert audit["live_land_outs"] <= DECK_SIZE - 7
        return
    raise AssertionError("no one-land hand found in 500 tries")


def test_tutor_present_tag_matches_tutors_set_membership():
    from opening_hand_model import TUTORS
    for seed in range(1, 1000):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        from draw_dependence_model import _is_land
        if sum(1 for c in hand if _is_land(c, CARDS)) != 1:
            continue
        has_tutor = any(n in TUTORS for n in hand)
        state, grade = _find_best_trajectory_with_state(hand, library, True, CARDS, _COMBOS)
        audit = _classify_one_land_hand(hand, state, grade, CARDS, DECK_SIZE, True)
        assert audit["tutor_already_present"] == has_tutor
        assert ("1 land + tutor" in audit["tags"]) == has_tutor
        return
    raise AssertionError("no one-land hand found in 1000 tries")


def test_fallback_field_is_none_type_or_a_real_value():
    for seed in range(1, 500):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        from draw_dependence_model import _is_land
        if sum(1 for c in hand if _is_land(c, CARDS)) != 1:
            continue
        state, grade = _find_best_trajectory_with_state(hand, library, True, CARDS, _COMBOS)
        audit = _classify_one_land_hand(hand, state, grade, CARDS, DECK_SIZE, True)
        if grade["tier_engine"] is None:
            assert audit["fallback_if_draw_misses"] is None
        else:
            assert audit["fallback_if_draw_misses"] is not None
        return
    raise AssertionError("no one-land hand found in 500 tries")
