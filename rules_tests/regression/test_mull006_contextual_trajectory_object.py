"""SIM-001 MULL-006 section 16 — multi-dimensional trajectory object.

Proves build_trajectory_object() assembles every section-16 field correctly from real simulated
hands, correctly falls back for destination-less (tier D/F) hands, and correctly sources
base_trajectory_grade from the strength/speed matrix for tracked engines vs the legacy tier for
untracked destinations (Oculus, Thrasios).
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from trajectory_search import _candidate_configs, _simulate, _better  # noqa: E402
from trajectory_grading import grade_trajectory  # noqa: E402
from contextual_trajectory_object import build_trajectory_object, OBJECT_PROVENANCE  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
_NAMES = list(CARDS.keys())
_COMBOS = load_deterministic_combos()
DECK_SIZE = len(CARDS)


def _best_with_state(hand, library, on_play=True):
    state, m1, m2, m3 = _simulate(hand, library, on_play, CARDS, _COMBOS)
    best = grade_trajectory(state, CARDS, m1, m2, m3)
    best_state = state
    for label, kwargs in _candidate_configs(hand, library, CARDS):
        st, a, b, c = _simulate(hand, library, on_play, CARDS, _COMBOS, **kwargs)
        g = grade_trajectory(st, CARDS, a, b, c)
        if _better(g, best):
            best, best_state = g, st
    return best_state, best


def _find_hand_with_engine(seed_start, engine_names, tries=500):
    for seed in range(seed_start, seed_start + tries):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        state, grade = _best_with_state(hand, library)
        if grade["tier_engine"] in engine_names:
            return hand, state, grade
    raise AssertionError(f"no hand found reaching {engine_names} in {tries} tries")


def test_no_destination_hand_has_none_fields_and_not_applicable_draw_dependence():
    for seed in range(1, 2000):
        lib = _NAMES[:]
        random.Random(seed).shuffle(lib)
        hand, library = lib[:7], lib[7:]
        state, grade = _best_with_state(hand, library)
        if grade["tier"] in ("D", "F"):
            obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=1, archetype="RogSi")
            assert obj["destination"] is None
            assert obj["destination_subtype"] is None
            assert obj["draw_dependence_class"] == "NOT_APPLICABLE_NO_DESTINATION"
            assert obj["resilience_class"] is None
            assert obj["probability_of_trajectory"] is None
            return
    raise AssertionError("no D/F-tier hand found in 2000 tries")


def test_resource_engine_uses_strength_speed_matrix_for_base_grade():
    hand, state, grade = _find_hand_with_engine(1, {"Rhystic Study", "Mystic Remora", "Smothering Tithe"})
    obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=1)
    assert obj["destination_subtype"] == "resource_engine"
    assert obj["base_trajectory_grade_source"] == "strength_speed_matrix"
    assert obj["intrinsic_strength"] is not None
    assert obj["relative_speed"] is not None


def test_thrasios_falls_back_to_legacy_tier_for_base_grade():
    hand, state, grade = _find_hand_with_engine(1, {"Thrasios, Triton Hero"})
    obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=1)
    assert obj["destination_subtype"] == "commander_concrete_benefit"
    assert obj["base_trajectory_grade_source"] == "legacy_tier_fallback"
    assert obj["base_trajectory_grade"] == grade["tier"]
    assert obj["intrinsic_strength"] is None  # not in engine_strength_prior at all


def test_pod_destination_subtype_is_functional_pod():
    hand, state, grade = _find_hand_with_engine(1, {"Birthing Pod"})
    obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=1)
    assert obj["destination_subtype"] == "functional_pod"


def test_seat_and_archetype_are_threaded_through():
    hand, state, grade = _find_hand_with_engine(1, {"Rhystic Study", "Mystic Remora", "Smothering Tithe"})
    obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=4, archetype="Kinnan")
    assert obj["seat"] == 4
    assert obj["archetype"] == "Kinnan"
    assert obj["pod_realization_modifier"] is not None
    assert isinstance(obj["relevant_agency"], int)  # single archetype -> scalar, not a dict


def test_no_archetype_gives_full_relevant_agency_dict():
    hand, state, grade = _find_hand_with_engine(1, {"Rhystic Study", "Mystic Remora", "Smothering Tithe"})
    obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=1, archetype=None)
    assert isinstance(obj["relevant_agency"], dict)
    assert obj["pod_realization_modifier"] is None  # requires an archetype


def test_contextual_trajectory_grade_starts_empty_dict():
    hand, state, grade = _find_hand_with_engine(1, {"Rhystic Study", "Mystic Remora", "Smothering Tithe"})
    obj = build_trajectory_object(hand, state, grade, CARDS, DECK_SIZE, True, seat=1)
    assert obj["contextual_trajectory_grade"] == {}


def test_provenance_label_is_model_derived():
    assert OBJECT_PROVENANCE == "MODEL_DERIVED"
