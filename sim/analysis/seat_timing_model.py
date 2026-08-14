"""SIM-001 MULL-006 section 6 — seat-adjusted timing, new dimension #1.

MODEL_DERIVED: turn-order geometry is exact (4-player round-robin turn order is a fixed rule of
the game), but the "action window" counting convention and the per-engine REALIZATION_TIMING_CLASS
below are disclosed simplifications, not measured or pilot-verbatim facts.

------------------------------------------------------------------------------------------------
TURN-ORDER GEOMETRY (exact, not a prior)

4 players take turns in a fixed round-robin: seat 1, 2, 3, 4, repeat. A player's Nth personal turn
(N = 1, 2, 3, ... - matching this project's existing T1/T2/T3 trajectory-turn numbering) occurs at
overall turn index (N-1)*4 + seat. The number of OPPONENT turns that occur strictly before a
player's Nth personal turn is therefore:

    opponent_turns_before(N, seat) = 3*(N-1) + (seat-1)

This is exact game structure, independent of engine identity - Seat 1's T1 always has 0 opponent
turns before it (the very first turn of the game); Seat 4's T1 always has 3 (every other seat has
already gone once). This project's opening-hand engine is a SOLO goldfish simulator (no live
opponents), so the underlying T1-T3 line itself does not change with seat - only these CONTEXTUAL
exposure/timing fields do.

------------------------------------------------------------------------------------------------
ACTION WINDOW CONVENTION (disclosed simplification, not a literal MTG priority-pass count)

"Opponent action windows" approximates the number of instant-speed opportunities an opponent has
to interact, not a literal count of every priority pass. Convention used here: 2 action windows
per opponent turn (their precombat main phase, and their end step - the two highest-leverage
windows in a typical cEDH turn for either side to act). This is a coarse proxy, disclosed as such;
it is NOT claimed to be simulation-measured.

------------------------------------------------------------------------------------------------
REALIZATION TIMING CLASS (per engine, MODEL_DERIVED - narrower than the full section-11/task-112
engine realization timing expansion, which this module does not attempt to replace)

IMMEDIATE_OPPONENT_TURN
    Value can occur as early as the very next opponent turn after deployment, because the trigger
    condition is opponent-driven (an opponent casting a spell, playing a land, drawing their
    second card, or searching their library). Applies to: Rhystic Study, Mystic Remora, Esper
    Sentinel, Smothering Tithe, Faerie Mastermind, Archivist of Oghma, Heartwood Storyteller,
    Runic Armasaur - every engine in engine_strength_prior.py whose trigger is opponent-driven.

OWN_NEXT_DRAW_STEP
    Value is delayed to our own next personal turn's draw step, regardless of seat or opponent
    action. Applies to: Sylvan Library.

OWN_TURN_DEPENDENT
    Realization timing depends on our own mana availability, not opponent turns at all. Applies
    to: Birthing Pod, Survival of the Fittest - both are gated by engine_strength_prior.py's
    FUNCTIONAL checks, which already require the activation to be currently payable, so a
    functional Pod/Survival realizes on the SAME turn it is deployed (0 opponent turns before
    realization).
"""
from engine_strength_prior import ENGINE_STRENGTH_PRIOR

TIMING_PROVENANCE = "MODEL_DERIVED"

ACTION_WINDOWS_PER_OPPONENT_TURN = 2

REALIZATION_TIMING_CLASS = {
    "Rhystic Study": "IMMEDIATE_OPPONENT_TURN",
    "Mystic Remora": "IMMEDIATE_OPPONENT_TURN",
    "Esper Sentinel": "IMMEDIATE_OPPONENT_TURN",
    "Smothering Tithe": "IMMEDIATE_OPPONENT_TURN",
    "Faerie Mastermind": "IMMEDIATE_OPPONENT_TURN",
    "Archivist of Oghma": "IMMEDIATE_OPPONENT_TURN",
    "Heartwood Storyteller": "IMMEDIATE_OPPONENT_TURN",
    "Runic Armasaur": "IMMEDIATE_OPPONENT_TURN",
    "Sylvan Library": "OWN_NEXT_DRAW_STEP",
    "Birthing Pod": "OWN_TURN_DEPENDENT",
    "Survival of the Fittest": "OWN_TURN_DEPENDENT",
}
assert set(REALIZATION_TIMING_CLASS) == set(ENGINE_STRENGTH_PRIOR)

# Engines whose opponent-driven trigger specifically puts a NEW CARD in our hand (as opposed to
# mana, damage, or a tax effect) - only these can possibly turn into live interaction before our
# next turn, and even then only if what's drawn happens to BE interaction (unknown at deployment
# time - this project never fabricates a probability for that, see relevant_agency work, task 111).
CARD_DRAW_ENGINES = {"Rhystic Study", "Mystic Remora", "Faerie Mastermind", "Archivist of Oghma"}


def opponent_turns_before(personal_turn, seat):
    """Exact count of opponent turns strictly before a player's Nth personal turn, given seat
    (1-4). Pure game-structure arithmetic, not a prior."""
    if seat not in (1, 2, 3, 4):
        raise ValueError(f"seat must be 1-4, got {seat}")
    return 3 * (personal_turn - 1) + (seat - 1)


def opponent_action_windows_before(personal_turn, seat):
    return opponent_turns_before(personal_turn, seat) * ACTION_WINDOWS_PER_OPPONENT_TURN


def seat_adjusted_timing(engine_name, deployment_turn, seat):
    """Returns the full section-6 field set for `engine_name` deployed on personal turn
    `deployment_turn` from `seat` (1-4), or None if `engine_name` has no REALIZATION_TIMING_CLASS
    entry (e.g. Abhorrent Oculus, or any card outside the tracked engine set)."""
    timing_class = REALIZATION_TIMING_CLASS.get(engine_name)
    if timing_class is None:
        return None

    opp_turns_before_deploy = opponent_turns_before(deployment_turn, seat)
    opp_windows_before_deploy = opponent_action_windows_before(deployment_turn, seat)

    if timing_class == "IMMEDIATE_OPPONENT_TURN":
        # Earliest possible realization: the very first opponent turn following deployment - this
        # is always exactly 1 opponent turn later, independent of seat (after OUR turn, the next
        # turn is always the next seat in rotation, regardless of which seat we are).
        opp_turns_before_realization = opp_turns_before_deploy + 1
        opp_windows_before_realization = opp_windows_before_deploy + ACTION_WINDOWS_PER_OPPONENT_TURN
        realized_before_our_next_turn = True  # 1 opponent turn is always < the 3 before our next turn
    elif timing_class == "OWN_NEXT_DRAW_STEP":
        # Realization occurs exactly AT our own next personal turn - all 3 opponents in the round
        # go first, so it is never realized strictly BEFORE our next turn.
        opp_turns_before_realization = opp_turns_before_deploy + 3
        opp_windows_before_realization = opp_windows_before_deploy + 3 * ACTION_WINDOWS_PER_OPPONENT_TURN
        realized_before_our_next_turn = False
    else:  # OWN_TURN_DEPENDENT
        # engine_strength_prior's FUNCTIONAL gate already requires the activation to be payable
        # now, so a functional Pod/Survival realizes the same turn it deploys.
        opp_turns_before_realization = opp_turns_before_deploy
        opp_windows_before_realization = opp_windows_before_deploy
        realized_before_our_next_turn = True

    if timing_class == "IMMEDIATE_OPPONENT_TURN" and engine_name in CARD_DRAW_ENGINES:
        card_could_become_live_interaction_before_next_turn = "POSSIBLE_CONTENTS_UNKNOWN"
    elif timing_class == "IMMEDIATE_OPPONENT_TURN":
        card_could_become_live_interaction_before_next_turn = "NOT_APPLICABLE_NOT_A_CARD_DRAW_TRIGGER"
    else:
        card_could_become_live_interaction_before_next_turn = "NOT_POSSIBLE_BEFORE_OWN_NEXT_TURN"

    return {
        "engine": engine_name,
        "deployment_turn": deployment_turn,
        "seat": seat,
        "realization_timing_class": timing_class,
        "opponent_turns_before_deployment": opp_turns_before_deploy,
        "opponent_action_windows_before_deployment": opp_windows_before_deploy,
        "opponent_turns_before_first_possible_realization": opp_turns_before_realization,
        "opponent_action_windows_before_first_possible_realization": opp_windows_before_realization,
        "value_generated_before_our_next_turn": realized_before_our_next_turn,
        "newly_generated_card_could_become_live_interaction_before_our_next_turn":
            card_could_become_live_interaction_before_next_turn,
    }
