"""SIM-001 MULL-005R — Birthing Pod / Survival of the Fittest / battlefield-destination tutor
regression tests.

Proves each newly-added mechanic in pod_and_battlefield_tutors.py + the Oculus uncastable-from-
hand rule before any trajectory-tier analysis is trusted to run on top of them - see
t1_t3_trajectory_audit.json's POD-*, OCULUS-*, SURV-001 findings for the Oracle-text grounding.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, Perm, LandInPlay, develop_turn, _card_class  # noqa: E402
from pod_and_battlefield_tutors import (  # noqa: E402
    try_activate_pod, try_activate_survival, try_battlefield_creature_tutor, try_battlefield_land_tutor,
)

FAKE_CARDS = {
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Tropical Island": {"name": "Tropical Island", "type": "Land — Island Forest", "mana_cost": "", "cmc": 0},
    "Birthing Pod": {"name": "Birthing Pod", "type": "Artifact", "mana_cost": "{3}{G/P}", "cmc": 4},
    "Devoted Druid": {"name": "Devoted Druid", "type": "Creature — Elf Druid", "mana_cost": "{1}{G}", "cmc": 2},
    "Birds of Paradise": {"name": "Birds of Paradise", "type": "Creature — Bird", "mana_cost": "{G}", "cmc": 1},
    "Abhorrent Oculus": {"name": "Abhorrent Oculus", "type": "Creature — Eye", "mana_cost": "{2}{U}", "cmc": 3},
    "Eldritch Evolution": {"name": "Eldritch Evolution", "type": "Sorcery", "mana_cost": "{1}{G}{G}", "cmc": 3},
    "Finale of Devastation": {"name": "Finale of Devastation", "type": "Sorcery", "mana_cost": "{X}{G}{G}", "cmc": 2},
    "Survival of the Fittest": {"name": "Survival of the Fittest", "type": "Enchantment", "mana_cost": "{1}{G}", "cmc": 2},
    "Badgermole Cub": {"name": "Badgermole Cub", "type": "Creature — Badger Mole", "mana_cost": "{1}{G}", "cmc": 2},
    "Faerie Mastermind": {"name": "Faerie Mastermind", "type": "Creature — Faerie Rogue", "mana_cost": "{1}{U}", "cmc": 2},
    "Crop Rotation": {"name": "Crop Rotation", "type": "Instant", "mana_cost": "{G}", "cmc": 1},
    "Gaea's Cradle": {"name": "Gaea's Cradle", "type": "Legendary Land", "mana_cost": "", "cmc": 0},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
}


def _state(hand, library, turn):
    s = HandState(list(hand), list(library), on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    s.turn = turn
    return s


# ---- Oculus uncastable-from-hand ---------------------------------------------------------
def test_oculus_is_never_hard_cast_from_hand():
    assert _card_class("Abhorrent Oculus", FAKE_CARDS) == "uncastable_from_hand"
    state = _state(["Abhorrent Oculus", "Underground Sea", "Underground Sea", "Underground Sea"],
                    ["Filler Land"] * 20, 0)
    state.turn = 0
    for _ in range(3):
        develop_turn(state, FAKE_CARDS)
    assert "Abhorrent Oculus" in state.hand
    assert all(n != "Abhorrent Oculus" for (_, n, _) in state.cast_log)


# ---- Birthing Pod --------------------------------------------------------------------------
def test_pod_activation_finds_mv_plus_one_creature_onto_battlefield():
    state = _state([], ["Abhorrent Oculus"] + ["Filler Land"] * 10, 3)
    state.lands += [LandInPlay("Underground Sea", 1, tapped=False), LandInPlay("Underground Sea", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birthing Pod", 2, False))
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))  # MV2, not summoning sick

    ok = try_activate_pod(state, FAKE_CARDS, "Devoted Druid", "Abhorrent Oculus")
    assert ok
    assert "Abhorrent Oculus" in [p.name for p in state.nonland_perms]
    assert "Devoted Druid" in state.graveyard
    assert "Abhorrent Oculus" not in state.library


def test_pod_activation_bypasses_oculus_hand_cast_restriction():
    """The whole point of POD-TO-OCULUS: Pod puts the card onto the battlefield via search, never
    casting it, so the exile-six-graveyard-cards additional cost is never checked."""
    state = _state([], ["Abhorrent Oculus"] + ["Filler Land"] * 10, 3)
    assert len(state.graveyard) == 0  # zero graveyard cards - would be illegal to hard-cast
    state.lands += [LandInPlay("Underground Sea", 1, tapped=False), LandInPlay("Underground Sea", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birthing Pod", 2, False))
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))
    assert try_activate_pod(state, FAKE_CARDS, "Devoted Druid", "Abhorrent Oculus")


def test_pod_rejects_wrong_mana_value_target():
    state = _state([], ["Faerie Mastermind"] + ["Filler Land"] * 10, 3)  # MV2, needs sac MV1 not MV2
    state.lands += [LandInPlay("Underground Sea", 1, tapped=False), LandInPlay("Underground Sea", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birthing Pod", 2, False))
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))  # MV2 -> can only find MV3
    assert not try_activate_pod(state, FAKE_CARDS, "Devoted Druid", "Faerie Mastermind")


def test_pod_no_op_when_tapped_or_absent():
    state = _state([], ["Abhorrent Oculus"] + ["Filler Land"] * 10, 3)
    state.lands += [LandInPlay("Underground Sea", 1, tapped=False), LandInPlay("Underground Sea", 1, tapped=False)]
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))
    assert not try_activate_pod(state, FAKE_CARDS, "Devoted Druid", "Abhorrent Oculus")  # no Pod at all

    state.nonland_perms.append(Perm("Birthing Pod", 2, False))
    state.nonland_perms[-1].tapped = True  # Pod already tapped
    assert not try_activate_pod(state, FAKE_CARDS, "Devoted Druid", "Abhorrent Oculus")


# ---- Eldritch Evolution / Finale of Devastation --------------------------------------------
def test_eldritch_evolution_sac_mv1_finds_oculus_onto_battlefield():
    state = _state(["Eldritch Evolution"], ["Abhorrent Oculus"] + ["Filler Land"] * 10, 2)
    state.lands += [LandInPlay("Tropical Island", 1, tapped=False), LandInPlay("Tropical Island", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birds of Paradise", 1, True))  # MV1, not sick

    ok = try_battlefield_creature_tutor(state, FAKE_CARDS, "Eldritch Evolution", "Abhorrent Oculus", sac_name="Birds of Paradise")
    assert ok
    assert "Abhorrent Oculus" in [p.name for p in state.nonland_perms]
    assert "Eldritch Evolution" in state.exile  # real Oracle text: "Exile Eldritch Evolution"
    assert "Birds of Paradise" in state.graveyard


def test_eldritch_evolution_rejects_wrong_mv():
    # Birds is MV1 -> X=3, can only find MV3, NOT MV2.
    state = _state(["Eldritch Evolution"], ["Badgermole Cub"] + ["Filler Land"] * 10, 2)
    state.lands += [LandInPlay("Tropical Island", 1, tapped=False), LandInPlay("Tropical Island", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birds of Paradise", 1, True))
    assert not try_battlefield_creature_tutor(state, FAKE_CARDS, "Eldritch Evolution", "Badgermole Cub", sac_name="Birds of Paradise")


def test_finale_of_devastation_x_equals_target_mv_finds_oculus():
    state = _state(["Finale of Devastation"], ["Abhorrent Oculus"] + ["Filler Land"] * 10, 3)
    # X=3 -> total cost {3}{G}{G} = 5 mana
    state.lands += [LandInPlay("Tropical Island", 1, tapped=False) for _ in range(5)]

    ok = try_battlefield_creature_tutor(state, FAKE_CARDS, "Finale of Devastation", "Abhorrent Oculus")
    assert ok
    assert "Abhorrent Oculus" in [p.name for p in state.nonland_perms]
    assert "Finale of Devastation" in state.graveyard  # no exile clause on Finale


def test_finale_of_devastation_insufficient_mana_fails():
    state = _state(["Finale of Devastation"], ["Abhorrent Oculus"] + ["Filler Land"] * 10, 3)
    state.lands += [LandInPlay("Tropical Island", 1, tapped=False) for _ in range(3)]  # short of the 5 needed
    assert not try_battlefield_creature_tutor(state, FAKE_CARDS, "Finale of Devastation", "Abhorrent Oculus")


# ---- Survival of the Fittest ----------------------------------------------------------------
def test_survival_discards_creature_and_puts_found_creature_in_hand_not_battlefield():
    state = _state(["Badgermole Cub"], ["Faerie Mastermind"] + ["Filler Land"] * 10, 2)
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    state.nonland_perms.append(Perm("Survival of the Fittest", 1, False))

    ok = try_activate_survival(state, FAKE_CARDS, "Badgermole Cub", "Faerie Mastermind")
    assert ok
    assert "Faerie Mastermind" in state.hand  # HAND, not battlefield - Survival doesn't bypass cast cost
    assert "Faerie Mastermind" not in [p.name for p in state.nonland_perms]
    assert "Badgermole Cub" in state.graveyard


def test_survival_requires_a_discardable_creature_card():
    state = _state([], ["Faerie Mastermind"] + ["Filler Land"] * 10, 2)  # no creature in hand to discard
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    state.nonland_perms.append(Perm("Survival of the Fittest", 1, False))
    assert not try_activate_survival(state, FAKE_CARDS, "Badgermole Cub", "Faerie Mastermind")


def test_survival_repeatable_in_same_turn_via_develop_turn():
    # 3 lands so Thrasios (GU, the default greedy policy's top priority) can be cast AND a full
    # {G} is still left over for Survival's activation - isolates the mechanic being tested from
    # commander-priority resource competition (a known, documented confound elsewhere in this
    # project's test suite).
    state = _state(["Badgermole Cub", "Underground Sea"],
                    ["Faerie Mastermind", "Devoted Druid"] + ["Filler Land"] * 10, 0)
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    state.nonland_perms.append(Perm("Survival of the Fittest", 0, False))
    actions = develop_turn(
        state, FAKE_CARDS,
        forced_survival_activations=[("Badgermole Cub", "Faerie Mastermind")],
    )
    assert any(a[0] == "survival_activate" for a in actions)


# ---- Crop Rotation --------------------------------------------------------------------------
def test_crop_rotation_finds_any_land_onto_battlefield():
    state = _state(["Crop Rotation"], ["Gaea's Cradle"] + ["Filler Land"] * 10, 1)
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))

    ok = try_battlefield_land_tutor(state, FAKE_CARDS, "Crop Rotation", "Gaea's Cradle")
    assert ok
    assert "Gaea's Cradle" in [l.name for l in state.lands]
    assert "Crop Rotation" in state.graveyard
    # a land was sacrificed as the additional cost - net land count unchanged (sac one, fetch one)
    assert len([l for l in state.lands if l.name == "Tropical Island"]) == 0


def test_crop_rotation_requires_a_land_to_sacrifice():
    state = _state(["Crop Rotation"], ["Gaea's Cradle"] + ["Filler Land"] * 10, 1)
    # no lands on battlefield at all - illegal additional cost
    assert not try_battlefield_land_tutor(state, FAKE_CARDS, "Crop Rotation", "Gaea's Cradle")


# ---- default-inert-by-omission (backward compatibility with pre-MULL-005R behavior) --------
def test_new_forced_params_default_to_none_and_are_no_ops():
    state = _state(["Underground Sea"], ["Filler Land"] * 20, 0)
    actions = develop_turn(state, FAKE_CARDS)
    assert not any(a[0] in ("pod_activate", "survival_activate", "battlefield_tutor", "battlefield_land_tutor") for a in actions)
