"""SIM-001 MULL-006 section 2 — alternate fetch-target branching.

MULL-005R disclosed (holdout_disagreement_audit.json) that the bounded trajectory search never
explored alternate fetchland targets - a fetch's crack target was always chosen by develop_turn's
own greedy need-colors-scored land-drop heuristic alone, which can legitimately trade a
higher-priority premium-engine color for an immediate lower-priority cast. This is the exact real
case found during that audit: a hand with Wooded Foothills as its only land, Mystic Remora
requiring U - the greedy line fetches Bayou (G/B, enabling an immediate Imperial Seal cast) and
never finds Remora's U, but Wooded Foothills can ALSO legally fetch Tropical Island (G/U), which
would let Remora resolve. Family 6 (trajectory_search.py's fetch:* candidates) must find this.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from trajectory_search import find_best_trajectory, _candidate_configs, _simulate  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
COMBOS = load_deterministic_combos()

WOODED_FOOTHILLS_HAND = [
    "Enlightened Tutor", "Flusterstorm", "Hazel's Brewmaster", "Imperial Seal",
    "Mystic Remora", "Rhystic Study", "Wooded Foothills",
]


def _library(hand, seed):
    names = list(CARDS.keys())
    lib = [n for n in names if n not in hand]
    random.Random(seed).shuffle(lib)
    return lib


def test_greedy_line_fails_to_find_remoras_blue_via_this_fetch():
    # sanity: confirms the documented failure mode is real BEFORE checking the fix - the greedy
    # line fetches a land that cannot pay Remora's U, so Remora is never cast.
    library = _library(WOODED_FOOTHILLS_HAND, 9001)
    state, m1, m2, m3 = _simulate(WOODED_FOOTHILLS_HAND, library, True, CARDS, COMBOS)
    assert not any(n == "Mystic Remora" for (t, n, c) in state.cast_log)


def test_fetch_candidate_family_is_generated_for_wooded_foothills():
    library = _library(WOODED_FOOTHILLS_HAND, 9001)
    labels = [label for label, kwargs in _candidate_configs(WOODED_FOOTHILLS_HAND, library, CARDS)]
    fetch_labels = [l for l in labels if l.startswith("fetch:Wooded Foothills->")]
    # Wooded Foothills' real legal targets (Mountain/Forest basic types) among this deck's 6 ABUR
    # duals are Bayou (Forest) and Tropical Island (Forest) - Savannah is also Forest/Plains.
    assert any("Tropical Island" in l for l in fetch_labels)


def test_alternate_fetch_target_reaches_tier_s_remora_where_greedy_reaches_tier_f():
    # The required regression per assignment section 2: greedy/default fetch target -> failed
    # trajectory, but alternate legal fetch target -> successful premium trajectory.
    library = _library(WOODED_FOOTHILLS_HAND, 9001)
    greedy, best, tried = find_best_trajectory(WOODED_FOOTHILLS_HAND, library, True, CARDS, COMBOS)
    assert greedy["tier"] == "F"
    assert greedy["tier_engine"] is None
    assert best["tier"] == "S"
    assert best["tier_engine"] == "Mystic Remora"
    assert best["search_label"] == "fetch:Wooded Foothills->Tropical Island"
    assert tried > 1


def test_fetch_branching_never_removes_a_legal_target_from_the_library_permanently():
    # Each candidate re-simulates from the ORIGINAL library, not a mutated shared one - a forced
    # fetch target in one candidate must not affect any other candidate's library state.
    library = _library(WOODED_FOOTHILLS_HAND, 9001)
    library_before = list(library)
    find_best_trajectory(WOODED_FOOTHILLS_HAND, library, True, CARDS, COMBOS)
    assert library == library_before


def test_no_fetchland_in_hand_generates_no_fetch_candidates():
    hand = ["Sol Ring", "Underground Sea", "Underground Sea"]
    library = _library(hand, 1)
    labels = [label for label, kwargs in _candidate_configs(hand, library, CARDS)]
    assert not any(l.startswith("fetch:") for l in labels)


def test_fetch_candidate_cannot_target_an_illegal_basic_type_combination():
    # Wooded Foothills searches for Mountain OR Forest - Underground Sea (Island/Swamp) shares
    # neither type and must never appear as a fetch:* candidate target for it.
    hand = ["Wooded Foothills", "Sol Ring"]
    library = ["Underground Sea"] + ["Filler Land"] * 20
    # Filler Land isn't a real card; use only real deck cards for this specific check.
    library = [n for n in list(CARDS.keys()) if n not in hand][:40]
    labels = [label for label, kwargs in _candidate_configs(hand, library, CARDS)]
    fetch_labels = [l for l in labels if l.startswith("fetch:Wooded Foothills->")]
    assert not any("Underground Sea" in l for l in fetch_labels)
