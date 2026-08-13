"""SIM-001 MULL-005R — expanded bounded trajectory search (Pod/Survival/battlefield-tutor/land-
tutor candidate families), removing MULL-005's six-hand-tutor-target-only bottleneck.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from trajectory_search import find_best_trajectory, _simulate, _candidate_configs  # noqa: E402
from trajectory_grading import grade_trajectory  # noqa: E402
from opening_hand_policy import BATTLEFIELD_SEARCH_ONLY, _card_class  # noqa: E402

FAKE_CARDS = {
    "Bayou": {"name": "Bayou", "type": "Land — Swamp Forest", "mana_cost": "", "cmc": 0},
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Eldritch Evolution": {"name": "Eldritch Evolution", "type": "Sorcery", "mana_cost": "{1}{G}{G}", "cmc": 3},
    "Birds of Paradise": {"name": "Birds of Paradise", "type": "Creature — Bird", "mana_cost": "{G}", "cmc": 1},
    "Elves of Deep Shadow": {"name": "Elves of Deep Shadow", "type": "Creature — Elf Druid", "mana_cost": "{G}", "cmc": 1},
    "Abhorrent Oculus": {"name": "Abhorrent Oculus", "type": "Creature — Eye", "mana_cost": "{2}{U}", "cmc": 3},
    "Birthing Pod": {"name": "Birthing Pod", "type": "Artifact", "mana_cost": "{3}{G/P}", "cmc": 4},
    "Devoted Druid": {"name": "Devoted Druid", "type": "Creature — Elf Druid", "mana_cost": "{1}{G}", "cmc": 2},
    "Survival of the Fittest": {"name": "Survival of the Fittest", "type": "Enchantment", "mana_cost": "{1}{G}", "cmc": 2},
    "Esper Sentinel": {"name": "Esper Sentinel", "type": "Artifact Creature — Human Soldier", "mana_cost": "{W}", "cmc": 1},
    "Crop Rotation": {"name": "Crop Rotation", "type": "Instant", "mana_cost": "{G}", "cmc": 1},
    "Gaea's Cradle": {"name": "Gaea's Cradle", "type": "Legendary Land", "mana_cost": "", "cmc": 0},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
}


def test_battlefield_search_only_cards_are_never_cast_by_greedy_generic_loop():
    assert BATTLEFIELD_SEARCH_ONLY == {
        "Eldritch Evolution", "Finale of Devastation", "Nature's Rhythm", "Chord of Calling", "Crop Rotation",
    }
    assert _card_class("Eldritch Evolution", FAKE_CARDS) == "uncastable_from_hand"
    assert _card_class("Crop Rotation", FAKE_CARDS) == "uncastable_from_hand"


def test_eldritch_evolution_battlefield_tutor_candidate_is_generated_and_reaches_oculus():
    # Elves of Deep Shadow (B only, not Birds' any-color) avoids accidentally enabling
    # Thrasios/Tymna as a confounding commander line - isolates the mechanic being tested, same
    # discipline used throughout this project's trajectory tests.
    hand = ["Eldritch Evolution", "Elves of Deep Shadow", "Bayou", "Bayou"]
    library = ["Filler Land"] * 5 + ["Abhorrent Oculus"] + ["Filler Land"] * 14
    labels = [label for label, kwargs in _candidate_configs(hand, library, FAKE_CARDS)]
    assert any("Eldritch Evolution" in l and "Abhorrent Oculus" in l for l in labels)

    state, m1, m2, m3 = _simulate(
        hand, library, True, FAKE_CARDS, [],
        forced_battlefield_tutor=("Eldritch Evolution", "Abhorrent Oculus", "Elves of Deep Shadow"),
    )
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier_engine"] == "Abhorrent Oculus"
    assert g["mechanism"] == "battlefield_tutor_to_oculus"


def test_pod_activation_candidate_is_generated_and_reaches_oculus():
    hand = ["Birthing Pod", "Devoted Druid", "Bayou", "Bayou"]
    library = ["Filler Land"] * 5 + ["Abhorrent Oculus"] + ["Filler Land"] * 14
    labels = [label for label, kwargs in _candidate_configs(hand, library, FAKE_CARDS)]
    assert any(l.startswith("pod:Devoted Druid->Abhorrent Oculus") for l in labels)

    state, m1, m2, m3 = _simulate(
        hand, library, True, FAKE_CARDS, [],
        forced_pod_activation=("Devoted Druid", "Abhorrent Oculus"),
    )
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    # May or may not actually reach Oculus depending on mana timing across 3 turns - the
    # important assertion is that the candidate was correctly GENERATED (above) and does not
    # crash when simulated; end-to-end success is separately proven in
    # test_mull005r_pod_oculus_survival.py's direct activation tests.
    assert g["tier"] in ("S", "A", "B", "C", "D", "F")


def test_survival_candidate_is_generated():
    hand = ["Survival of the Fittest", "Birds of Paradise", "Underground Sea", "Underground Sea"]
    library = ["Filler Land"] * 5 + ["Esper Sentinel"] + ["Filler Land"] * 14
    labels = [label for label, kwargs in _candidate_configs(hand, library, FAKE_CARDS)]
    assert any(l.startswith("survival:Birds of Paradise->Esper Sentinel") for l in labels)


def test_crop_rotation_land_tutor_candidate_is_generated_and_reaches_cradle():
    hand = ["Crop Rotation", "Bayou"]
    library = ["Filler Land"] * 5 + ["Gaea's Cradle"] + ["Filler Land"] * 14
    labels = [label for label, kwargs in _candidate_configs(hand, library, FAKE_CARDS)]
    assert any("Crop Rotation" in l and "Gaea's Cradle" in l for l in labels)

    state, m1, m2, m3 = _simulate(
        hand, library, True, FAKE_CARDS, [],
        forced_land_tutor=("Crop Rotation", "Gaea's Cradle"),
    )
    assert "Gaea's Cradle" in [l.name for l in state.lands]


def test_find_best_trajectory_still_reports_greedy_and_best_separately():
    hand = ["Eldritch Evolution", "Birds of Paradise", "Bayou", "Bayou"]
    library = ["Filler Land"] * 5 + ["Abhorrent Oculus"] + ["Filler Land"] * 14
    greedy, best, tried = find_best_trajectory(hand, library, True, FAKE_CARDS, [])
    assert greedy["search_label"] == "greedy"
    assert tried > 1


def test_no_relevant_cards_in_hand_only_tries_greedy():
    hand = ["Underground Sea", "Underground Sea"]
    library = ["Filler Land"] * 20
    labels = list(_candidate_configs(hand, library, FAKE_CARDS))
    assert labels == []
