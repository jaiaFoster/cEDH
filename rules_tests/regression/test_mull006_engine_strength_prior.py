"""SIM-001 MULL-006 section 3 — pilot-supplied engine-strength prior.

Proves the strength labels/ranking are exactly as specified, the Faerie Mastermind correction
(passive alone counts as engine status, no activation requirement), and the concrete FUNCTIONAL
gates for Birthing Pod / Survival of the Fittest (deployed + fodder/fuel + a currently-payable
useful activation - not merely "on the battlefield").
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, Perm, LandInPlay  # noqa: E402
from engine_strength_prior import (  # noqa: E402
    engine_strength, functional_pod, functional_survival, ENGINE_STRENGTH_PRIOR,
    ENGINE_STRENGTH_RANK, STRENGTH_PROVENANCE,
)

FAKE_CARDS = {
    "Birthing Pod": {"name": "Birthing Pod", "type": "Artifact", "mana_cost": "{3}{G/P}", "cmc": 4},
    "Survival of the Fittest": {"name": "Survival of the Fittest", "type": "Enchantment", "mana_cost": "{1}{G}", "cmc": 2},
    "Devoted Druid": {"name": "Devoted Druid", "type": "Creature — Elf Druid", "mana_cost": "{1}{G}", "cmc": 2},
    "Vanilla Creature": {"name": "Vanilla Creature", "type": "Creature — Bear", "mana_cost": "{2}{G}", "cmc": 3},
    "Tropical Island": {"name": "Tropical Island", "type": "Land — Island Forest", "mana_cost": "", "cmc": 0},
    "Faerie Mastermind": {"name": "Faerie Mastermind", "type": "Creature — Faerie Rogue", "mana_cost": "{1}{U}", "cmc": 2},
    "Smothering Tithe": {"name": "Smothering Tithe", "type": "Enchantment", "mana_cost": "{3}{W}", "cmc": 4},
}


def _state(hand=None, library=None):
    return HandState(hand or [], library or [], on_play=True, rng=random.Random(0), cards=FAKE_CARDS)


def test_prior_labels_match_the_pilot_supplied_table():
    assert ENGINE_STRENGTH_PRIOR["Smothering Tithe"] == "S"
    assert ENGINE_STRENGTH_PRIOR["Birthing Pod"] == "S"
    assert ENGINE_STRENGTH_PRIOR["Rhystic Study"] == "A+"
    assert ENGINE_STRENGTH_PRIOR["Mystic Remora"] == "A"
    assert ENGINE_STRENGTH_PRIOR["Faerie Mastermind"] == "A"
    assert ENGINE_STRENGTH_PRIOR["Esper Sentinel"] == "A-"
    assert ENGINE_STRENGTH_PRIOR["Archivist of Oghma"] == "A-"
    assert ENGINE_STRENGTH_PRIOR["Sylvan Library"] == "B+"
    assert ENGINE_STRENGTH_PRIOR["Survival of the Fittest"] == "B"
    assert ENGINE_STRENGTH_PRIOR["Heartwood Storyteller"] == "B-"
    assert ENGINE_STRENGTH_PRIOR["Runic Armasaur"] == "C+/B-"


def test_strength_rank_is_monotonically_ordered_s_strongest():
    assert ENGINE_STRENGTH_RANK["S"] < ENGINE_STRENGTH_RANK["A+"] < ENGINE_STRENGTH_RANK["A"]
    assert ENGINE_STRENGTH_RANK["A"] < ENGINE_STRENGTH_RANK["A-"] < ENGINE_STRENGTH_RANK["B+"]
    assert ENGINE_STRENGTH_RANK["B+"] < ENGINE_STRENGTH_RANK["B"] < ENGINE_STRENGTH_RANK["B-"]
    assert ENGINE_STRENGTH_RANK["B-"] < ENGINE_STRENGTH_RANK["C+/B-"]


def test_oculus_is_not_in_the_engine_strength_table():
    assert "Abhorrent Oculus" not in ENGINE_STRENGTH_PRIOR


def test_provenance_label_is_pilot_supplied_strategic_prior():
    assert STRENGTH_PROVENANCE == "PILOT_SUPPLIED_STRATEGIC_PRIOR"


def test_mastermind_counts_as_engine_a_with_zero_mana_no_activation_support():
    # The FAERIE MASTERMIND CORRECTION: passive alone is the engine - must NOT require the {3}{U}
    # activated ability to be payable (unlike MULL-005R's Tier-C _tier_c_supported check).
    state = _state()
    state.nonland_perms.append(Perm("Faerie Mastermind", 1, is_creature=True))
    # zero lands/mana at all
    assert engine_strength("Faerie Mastermind", state, FAKE_CARDS) == "A"


def test_mastermind_not_on_battlefield_returns_none():
    state = _state(hand=["Faerie Mastermind"])
    assert engine_strength("Faerie Mastermind", state, FAKE_CARDS) is None


def test_pod_on_battlefield_with_no_fodder_is_not_functional():
    state = _state()
    state.nonland_perms.append(Perm("Birthing Pod", 1, False))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    assert functional_pod(state, FAKE_CARDS) is False
    assert engine_strength("Birthing Pod", state, FAKE_CARDS) is None


def test_pod_with_fodder_but_no_mana_is_not_functional():
    state = _state()
    state.nonland_perms.append(Perm("Birthing Pod", 1, False))
    state.nonland_perms.append(Perm("Vanilla Creature", 1, is_creature=True))
    # no untapped lands at all -> can't pay {1}{G/P}
    assert functional_pod(state, FAKE_CARDS) is False


def test_pod_with_fodder_and_payable_activation_is_functional_s_tier():
    state = _state()
    state.nonland_perms.append(Perm("Birthing Pod", 1, False))
    state.nonland_perms.append(Perm("Vanilla Creature", 1, is_creature=True))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    assert functional_pod(state, FAKE_CARDS) is True
    assert engine_strength("Birthing Pod", state, FAKE_CARDS) == "S"


def test_survival_without_hand_fuel_is_not_functional():
    state = _state(hand=[])
    state.nonland_perms.append(Perm("Survival of the Fittest", 1, False))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    assert functional_survival(state, FAKE_CARDS) is False
    assert engine_strength("Survival of the Fittest", state, FAKE_CARDS) is None


def test_survival_with_fuel_and_mana_is_functional_b_tier():
    state = _state(hand=["Vanilla Creature"])
    state.nonland_perms.append(Perm("Survival of the Fittest", 1, False))
    state.lands.append(LandInPlay("Tropical Island", 1, tapped=False))
    assert functional_survival(state, FAKE_CARDS) is True
    assert engine_strength("Survival of the Fittest", state, FAKE_CARDS) == "B"


def test_unrecognized_card_returns_none():
    state = _state()
    assert engine_strength("Some Random Card Not In The Prior", state, FAKE_CARDS) is None


def test_rhystic_study_in_hand_only_returns_none():
    # Deployment is still necessary for every entry, including Tier-A proxy-credited engines -
    # the FAERIE MASTERMIND CORRECTION removes the ACTIVATION requirement, not the deployment one.
    state = _state(hand=["Smothering Tithe"])
    assert engine_strength("Smothering Tithe", state, FAKE_CARDS) is None


def test_smothering_tithe_strength_deployment_alone_no_gating():
    # Tithe is NOT functional-gated like Pod/Survival - deployment alone is enough per the
    # existing disclosed-proxy pattern (TITHE-001), just as Rhystic/Remora already are.
    state = _state()
    state.nonland_perms.append(Perm("Smothering Tithe", 1, False))
    assert engine_strength("Smothering Tithe", state, FAKE_CARDS) == "S"
