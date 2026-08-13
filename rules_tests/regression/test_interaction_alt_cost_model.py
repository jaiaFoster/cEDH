"""SIM-001 SOLO-003 checkpoint — real alternate-cost interaction model regression tests.

Validates interaction_model.py's interaction_is_live()/resolve_interaction_cast() against each
card's real Oracle text (verified against data/cards_cache/oracle-2026-08-12). Required because
"development + interaction" is a primary SOLO-003 metric, and SOLO-002R/the original SOLO-002
checked interaction castability using ONLY the printed mana cost - understating exactly the
cards this deck plays interaction for in the first place.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from opening_hand_policy import HandState, develop_turn, Perm, LandInPlay  # noqa: E402
from interaction_model import interaction_is_live  # noqa: E402

payload, CARDS = load_deck_cards()


def _bare_state(hand):
    return HandState(list(hand), [], on_play=True, rng=random.Random(1), cards=CARDS)


# ---- Force of Will: pitch (blue card + 1 life) or its real {3}{U}{U} mana cost ----
def test_force_of_will_needs_blue_pitch_or_real_mana():
    state = _bare_state(["Force of Will", "Ancient Tomb"])  # no other blue card, no real mana
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Force of Will", state, CARDS) is False

    state2 = _bare_state(["Force of Will", "Mystic Remora"])  # Remora is blue - pitchable
    state2.turn = 1
    state2.turn_start_mana, state2.turn_start_colors = 0, set()
    assert interaction_is_live("Force of Will", state2, CARDS) is True

    # real mana path: 5 mana with a U source should also work without any pitch card
    state3 = _bare_state(["Force of Will"])
    for _ in range(4):
        state3.lands.append(LandInPlay("Command Tower", 0))
    state3.lands.append(LandInPlay("Tundra", 0))
    state3.turn = 1
    assert interaction_is_live("Force of Will", state3, CARDS) is True


# ---- Commandeer: needs exactly TWO other blue cards to pitch (not one) ----
def test_commandeer_needs_two_blue_cards_when_pitched():
    state = _bare_state(["Commandeer", "Mystic Remora"])  # only one other blue card
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Commandeer", state, CARDS) is False, (
        "Commandeer's pitch alt-cost needs TWO other blue cards, not one"
    )

    state2 = _bare_state(["Commandeer", "Mystic Remora", "Faerie Mastermind"])  # two other blue cards
    state2.turn = 1
    state2.turn_start_mana, state2.turn_start_colors = 0, set()
    assert interaction_is_live("Commandeer", state2, CARDS) is True


# ---- Fierce Guardianship: free ONLY when a commander is actually on the battlefield ----
def test_fierce_guardianship_free_only_with_commander_present():
    state = _bare_state(["Fierce Guardianship"])
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Fierce Guardianship", state, CARDS) is False

    state2 = _bare_state(["Fierce Guardianship"])
    state2.nonland_perms.append(Perm("Tymna the Weaver", 0, is_creature=True))
    state2.turn = 1
    state2.turn_start_mana, state2.turn_start_colors = 0, set()
    assert interaction_is_live("Fierce Guardianship", state2, CARDS) is True


# ---- Flare of Denial: needs a nontoken blue creature to sacrifice as its alt cost ----
def test_flare_of_denial_needs_blue_creature_to_sacrifice():
    state = _bare_state(["Flare of Denial"])
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Flare of Denial", state, CARDS) is False

    state2 = _bare_state(["Flare of Denial"])
    state2.nonland_perms.append(Perm("Subtlety", 0, is_creature=True))  # a real blue creature
    state2.turn = 1
    state2.turn_start_mana, state2.turn_start_colors = 0, set()
    assert interaction_is_live("Flare of Denial", state2, CARDS) is True
    # the sac target must actually be a CREATURE, not e.g. a noncreature blue permanent
    state3 = _bare_state(["Flare of Denial"])
    state3.nonland_perms.append(Perm("Mystic Remora", 0, is_creature=False))  # blue, not a creature
    state3.turn = 1
    state3.turn_start_mana, state3.turn_start_colors = 0, set()
    assert interaction_is_live("Flare of Denial", state3, CARDS) is False


# ---- Mindbreak Trap: free ONLY under its real condition, which is structurally never true in a
# solo/no-opponent model (no opponent ever casts 3+ spells here) ----
def test_mindbreak_trap_never_free_in_solo_model():
    state = _bare_state(["Mindbreak Trap"])
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Mindbreak Trap", state, CARDS) is False, (
        "Mindbreak Trap's free alt-cost condition ('an opponent cast 3+ spells this turn') can "
        "never be true in a solo/no-opponent model - only its real {2}{U}{U} should ever apply"
    )
    state2 = _bare_state(["Mindbreak Trap"])
    for _ in range(4):
        state2.lands.append(LandInPlay("Command Tower", 0))
    state2.turn = 1
    assert interaction_is_live("Mindbreak Trap", state2, CARDS) is True, (
        "with real mana ({2}{U}{U} = 4, all colors available), it should still be castable normally"
    )


# ---- Pact of Negation: current castability (always, {0}) vs. the deferred obligation, tracked
# SEPARATELY, not as a gate ----
def test_pact_of_negation_castability_and_deferred_obligation_are_separate():
    state = _bare_state(["Pact of Negation"])
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Pact of Negation", state, CARDS) is True, "Pact's printed cost is {0} - always castable"
    assert state.pact_of_negation_obligations == [], "merely being castable must not itself create an obligation"

    actions = develop_turn(state, CARDS)
    assert ("cast", "Pact of Negation", "interaction") in actions
    assert len(state.pact_of_negation_obligations) == 1
    obligation = state.pact_of_negation_obligations[0]
    assert obligation["cost"] == "{3}{U}{U}"
    assert obligation["due_turn"] == obligation["cast_turn"] + 1


# ---- Misdirection / Subtlety / Force of Negation: exact alternate-cost and timing restrictions ----
def test_misdirection_pitch_alt_cost():
    state = _bare_state(["Misdirection"])
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Misdirection", state, CARDS) is False
    state2 = _bare_state(["Misdirection", "Mystic Remora"])
    state2.turn = 1
    state2.turn_start_mana, state2.turn_start_colors = 0, set()
    assert interaction_is_live("Misdirection", state2, CARDS) is True


def test_subtlety_evoke_vs_hardcast_battlefield_fate():
    # Evoked (pitch alt-cost, no real mana): enters, then is immediately sacrificed per its own
    # Evoke rule - must resolve to the graveyard, not stay as a permanent.
    state = _bare_state(["Subtlety", "Mystic Remora"])
    develop_turn(state, CARDS)
    assert "Subtlety" in state.graveyard
    assert not any(p.name == "Subtlety" for p in state.nonland_perms)

    # Hardcast (real mana, {2}{U}{U}): stays as a real permanent creature. Commanders are cleared
    # from the command zone so the greedy policy's higher-priority commander casts don't consume
    # the mana this test actually wants to exercise on Subtlety.
    state2 = _bare_state(["Subtlety"])
    state2.command_zone = set()
    for _ in range(4):
        state2.lands.append(LandInPlay("Command Tower", 0))
    develop_turn(state2, CARDS)
    assert any(p.name == "Subtlety" for p in state2.nonland_perms)
    assert "Subtlety" not in state2.graveyard


def test_force_of_negation_never_free_in_solo_model():
    # Force of Negation's alt cost is "if it's not your turn" - every snapshot in this model is
    # taken during the pilot's own turn, so the alt cost is structurally never available, even
    # with a pitchable blue card in hand.
    state = _bare_state(["Force of Negation", "Mystic Remora"])
    state.turn = 1
    state.turn_start_mana, state.turn_start_colors = 0, set()
    assert interaction_is_live("Force of Negation", state, CARDS) is False
    state2 = _bare_state(["Force of Negation"])
    for _ in range(3):
        state2.lands.append(LandInPlay("Command Tower", 0))
    state2.turn = 1
    assert interaction_is_live("Force of Negation", state2, CARDS) is True, (
        "real mana cost {1}{U}{U} = 3 should still work normally"
    )
