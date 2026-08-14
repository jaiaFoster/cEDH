"""SIM-001 MULL-006 section 11 — engine realization timing, expanding MULL-005R's realization work.

Preserves and expands seat_timing_model.py (task #107, section 6) rather than duplicating it -
this module combines that module's exact turn-order geometry ("earliest POSSIBLE" realization)
with pod_realization_model.py's qualitative pod-trigger modifier (task #110, section 9) to produce
an "earliest EXPECTED" realization estimate, and adds one new field the seat-timing work did not
cover: whether a newly-drawn card could IMMEDIATELY enable pitch/free interaction on the very turn
it arrives.

EARLIEST POSSIBLE vs EARLIEST EXPECTED (the assignment's own distinct terms):
    earliest POSSIBLE realization = seat_timing_model's structural, opponent-behavior-independent
        floor (assumes the trigger condition is met the very first chance it could be) - already
        exact game-structure arithmetic, not a prior.
    earliest EXPECTED realization = a QUALITATIVE label folding in pod_realization_model's VERY_
        HIGH/HIGH/MODERATE/LOW/UNKNOWN modifier for opponent-triggered engines. Per the assignment's
        explicit "MULL-006 is NOT yet authorized to fabricate exact multiplayer trigger rates,"
        this is an ordinal label (e.g. "WITHIN_A_FEW_ROUNDS"), never a fabricated turn number,
        clearly separate from the exact "possible" floor.

Named examples (assignment's own, reusing seat_timing_model.REALIZATION_TIMING_CLASS exactly as
already built in task #107 - not re-derived here):
    FAERIE MASTERMIND - passive trigger is the engine (see engine_strength_prior.py's FAERIE
        MASTERMIND CORRECTION); can generate cards on opponents' turns - IMMEDIATE_OPPONENT_TURN.
    ARCHIVIST OF OGHMA - can generate cards during opponent turns when searches occur -
        IMMEDIATE_OPPONENT_TURN.
    SYLVAN LIBRARY - does not realize immediately; delayed until our own next draw step -
        OWN_NEXT_DRAW_STEP, and (new here) the pod realization modifier does NOT apply to it at
        all, since its trigger is not opponent-behavior-dependent.
    HEARTWOOD STORYTELLER / RUNIC ARMASAUR - can generate opponent-turn value but depend strongly
        on pod behavior - IMMEDIATE_OPPONENT_TURN structurally, but their earliest EXPECTED
        realization varies widely by archetype (see pod_realization_prior.json).

Realization timing is used here as a MODIFIER distinct from intrinsic strength - this module does
not read or alter engine_strength_prior.py's strength labels at all.
"""
from seat_timing_model import seat_adjusted_timing, REALIZATION_TIMING_CLASS, CARD_DRAW_ENGINES
from pod_realization_model import pod_trigger_realization, TRACKED_POD_ENGINES
from relevant_agency_model import CARD_THREAT_AXES

REALIZATION_TIMING_PROVENANCE = "MODEL_DERIVED"

# Ordinal expected-realization labels for opponent-triggered engines, keyed by the pod realization
# modifier - never a fabricated turn count, per the assignment's explicit prohibition.
EXPECTED_REALIZATION_BY_MODIFIER = {
    "VERY_HIGH": "LIKELY_AT_EARLIEST_POSSIBLE_OPPONENT_TURN",
    "HIGH": "TYPICALLY_WITHIN_THE_FIRST_ROUND",
    "MODERATE": "WITHIN_A_FEW_ROUNDS",
    "LOW": "UNCERTAIN_MAY_NOT_REALIZE_WITHIN_T1_T3_WINDOW",
    "UNKNOWN": "UNKNOWN",
}

FREE_INTERACTION_CARDS = sorted(
    name for name, axes in CARD_THREAT_AXES.items() if "free_interaction" in axes
)


def realization_timing_profile(engine_name, deployment_turn, seat, archetype=None):
    """Returns the full expanded section-11 field set for `engine_name` deployed on
    `deployment_turn` from `seat`, optionally folding in a pod archetype's realization modifier.
    Returns None if `engine_name` is untracked by seat_timing_model.REALIZATION_TIMING_CLASS."""
    base = seat_adjusted_timing(engine_name, deployment_turn, seat)
    if base is None:
        return None

    timing_class = base["realization_timing_class"]
    is_opponent_dependent = engine_name in TRACKED_POD_ENGINES

    if is_opponent_dependent and archetype is not None:
        modifier = pod_trigger_realization(engine_name, archetype)
        earliest_expected = EXPECTED_REALIZATION_BY_MODIFIER[modifier]
    elif is_opponent_dependent:
        modifier = None
        earliest_expected = "REQUIRES_ARCHETYPE_TO_ESTIMATE"
    else:
        # OWN_NEXT_DRAW_STEP / OWN_TURN_DEPENDENT engines aren't opponent-behavior-dependent - the
        # pod realization modifier does not apply, "expected" collapses to the exact "possible".
        modifier = "NOT_APPLICABLE_NOT_OPPONENT_DEPENDENT"
        earliest_expected = "SAME_AS_EARLIEST_POSSIBLE_NOT_OPPONENT_DEPENDENT"

    value_enters_hand_immediately = (
        timing_class == "IMMEDIATE_OPPONENT_TURN" and engine_name in CARD_DRAW_ENGINES
    )
    if value_enters_hand_immediately:
        pitch_enablement = "POSSIBLE_CONTENTS_UNKNOWN"
    elif timing_class == "IMMEDIATE_OPPONENT_TURN":
        pitch_enablement = "NOT_APPLICABLE_NOT_A_CARD_DRAW_TRIGGER"
    else:
        pitch_enablement = "NOT_APPLICABLE_VALUE_NOT_REALIZED_ON_OPPONENT_TURN"

    return {
        **base,
        "archetype": archetype,
        "pod_realization_modifier": modifier,
        "earliest_expected_realization": earliest_expected,
        "value_enters_hand_immediately_on_realization": value_enters_hand_immediately,
        "newly_drawn_card_could_enable_immediate_pitch_interaction": pitch_enablement,
        "free_interaction_cards_this_deck_could_draw_into": (
            FREE_INTERACTION_CARDS if value_enters_hand_immediately else []
        ),
    }
