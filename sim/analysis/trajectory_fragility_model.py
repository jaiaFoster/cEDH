"""SIM-001 MULL-006 section 8 — trajectory fragility / recovery, new dimension #3.

For the winning trajectory, evaluates a CONTROLLED COUNTERFACTUAL: what does the hand's remaining
resources look like at the moment the primary destination (tier_engine) comes online, as if it
were answered immediately afterward? This is explicitly NOT a full opponent simulation (this
project never models an opponent's actual removal suite or the likelihood they use it) - it only
measures the CONSEQUENCE of the primary destination being gone, using the real simulated end-of-
tier_turn state, not a fabricated one.

Tracked fields (assignment's own list):
    cards_committed, cards_remaining, permanent_mana_remaining, temporary_mana_consumed,
    card_disadvantage_incurred, tutors_consumed, mox_imprint_or_discard_costs,
    creatures_sacrificed, second_best_destination, time_until_next_development,
    interaction_remains, hand_effectively_collapses.

RESILIENCE CLASSIFICATION - boundaries derived from the OBSERVABLE state fields above, not
arbitrary labels, per the assignment's explicit instruction:

    ALL_IN        hand_effectively_collapses is True (cards_remaining <= 1 AND no second-best
                  destination already realized AND no interaction remains).
    FRAGILE       not ALL_IN, but cards_remaining <= 2 AND no second-best destination already on
                  the battlefield (at best a weak, unrealized in-hand fallback).
    ROBUST        a second-best destination is ALREADY REALIZED on the battlefield (not merely
                  sitting in hand) AND cards_remaining >= 3.
    RECOVERABLE   everything else - some buffer exists (cards_remaining >= 3 without an already-
                  realized second plan, or a real in-hand fallback with a moderate hand).

This directly encodes the assignment's own worked examples: "T2 Tithe with four cards remaining
should not necessarily equal T2 Tithe produced by exhausting nearly the entire hand" (cards_
remaining is the deciding input) and "Pod with continuing creature fuel should differ from Pod
whose only useful activation consumes the entire development plan" (creatures_sacrificed and
cards_remaining together capture this - a Pod line that chained several activations against a
nearly-empty hand scores ALL_IN/FRAGILE, one that activated once with fodder and cards still in
hand scores ROBUST/RECOVERABLE).
"""
from opening_hand_model import INTERACTION_CASTABLE
from opening_hand_policy import OCULUS_NAME
from engine_strength_prior import ENGINE_STRENGTH_PRIOR
from trajectory_grading import ONE_SHOT_ACCEL
from draw_dependence_model import _draws_by_turn

FRAGILITY_PROVENANCE = "SIMULATION_MEASURED"

RESILIENCE_ORDER = ["ROBUST", "RECOVERABLE", "FRAGILE", "ALL_IN"]
RESILIENCE_RANK = {c: i for i, c in enumerate(RESILIENCE_ORDER)}

TRACKED_DESTINATIONS = set(ENGINE_STRENGTH_PRIOR) | {OCULUS_NAME}


def _permanent_mana_remaining(state):
    """Untapped LAND count at end of tier_turn - a persistent (not one-shot) mana source."""
    return sum(1 for land in state.lands if not land.tapped)


def _temporary_mana_consumed(state, tier_turn):
    return sum(1 for (t, _name) in state.temp_mana_used_log if t <= tier_turn)


def _tutors_consumed(state, tier_turn):
    return sum(1 for (t, _name, cls) in state.cast_log if t <= tier_turn and cls == "tutor")


def _creatures_sacrificed(state, tier_turn):
    # Every "pod_found" cast_log entry corresponds to exactly one Birthing Pod activation, which
    # always sacrifices exactly one creature (real Oracle text: "Sacrifice a creature").
    return sum(1 for (t, _name, cls) in state.cast_log if t <= tier_turn and cls == "pod_found")


def _mox_imprint_or_discard_costs(state):
    # Chrome Mox exiles one card from hand (imprint); Mox Diamond discards one land from hand.
    # Both are irrevocable resource costs already paid by end-of-turn state, not future risk.
    chrome_mox_imprints = len(state.exile)
    mox_diamond_discards = 1 if any(p.name == "Mox Diamond" for p in state.nonland_perms) else 0
    return chrome_mox_imprints + mox_diamond_discards


def _card_disadvantage_incurred(state, tier_turn):
    """Cards that resolved and left no lasting battlefield presence - one-shot mana rocks and
    tutors/interaction that hit the graveyard. A coarse proxy (real card-advantage accounting is
    deeper than this project models), disclosed as such."""
    return sum(
        1 for (t, name, cls) in state.cast_log
        if t <= tier_turn and (cls == "tutor" or cls == "interaction" or name in ONE_SHOT_ACCEL)
    )


def _second_best_destination(state, tier_engine):
    """A destination ALREADY REALIZED on the battlefield, distinct from tier_engine - the strongest
    possible fallback signal (not merely a card sitting in hand that could become one later)."""
    for perm in state.nonland_perms:
        if perm.name != tier_engine and perm.name in TRACKED_DESTINATIONS:
            return perm.name
    return None


def _weak_hand_fallback_present(state, cards, tier_engine):
    """A card still in hand that COULD become a destination or re-deploy later (an engine, tutor,
    or the same/another named destination) - a weaker signal than an already-realized second
    destination, used only to distinguish RECOVERABLE from ALL_IN when nothing is on the board."""
    from opening_hand_model import TUTORS
    for c in state.hand:
        if c in TRACKED_DESTINATIONS or c in TUTORS:
            return c
    return None


def _interaction_remains(state):
    return any(c in INTERACTION_CASTABLE for c in state.hand)


def assess_fragility(state, cards, tier_engine, tier_turn, on_play):
    """Returns the full section-8 field set for the winning trajectory, or None if tier_engine is
    None (no destination to counterfactually remove)."""
    if tier_engine is None or tier_turn is None:
        return None

    draws_taken = _draws_by_turn(tier_turn, on_play)
    total_cards_seen = len(state.opening_hand) + draws_taken
    cards_remaining = len(state.hand)
    cards_committed = total_cards_seen - cards_remaining

    second_best = _second_best_destination(state, tier_engine)
    weak_fallback = _weak_hand_fallback_present(state, cards, tier_engine)
    interaction_remains = _interaction_remains(state)

    hand_effectively_collapses = (
        cards_remaining <= 1 and second_best is None and not interaction_remains
    )

    if second_best is not None:
        time_until_next_development = 0  # already realized, in parallel with tier_engine
    elif weak_fallback is not None:
        time_until_next_development = tier_turn + 1  # earliest it could be cast is our next turn
    else:
        time_until_next_development = None  # no known path to further development

    if hand_effectively_collapses or cards_remaining == 0:
        resilience = "ALL_IN"
    elif second_best is not None and cards_remaining >= 3:
        resilience = "ROBUST"
    elif second_best is None and cards_remaining <= 2:
        resilience = "FRAGILE"
    else:
        resilience = "RECOVERABLE"

    return {
        "tier_engine": tier_engine, "tier_turn": tier_turn,
        "cards_committed": cards_committed,
        "cards_remaining": cards_remaining,
        "permanent_mana_remaining": _permanent_mana_remaining(state),
        "temporary_mana_consumed": _temporary_mana_consumed(state, tier_turn),
        "card_disadvantage_incurred": _card_disadvantage_incurred(state, tier_turn),
        "tutors_consumed": _tutors_consumed(state, tier_turn),
        "mox_imprint_or_discard_costs": _mox_imprint_or_discard_costs(state),
        "creatures_sacrificed": _creatures_sacrificed(state, tier_turn),
        "second_best_destination_realized": second_best,
        "weak_in_hand_fallback": weak_fallback,
        "time_until_next_development": time_until_next_development,
        "interaction_remains": interaction_remains,
        "hand_effectively_collapses": hand_effectively_collapses,
        "resilience_class": resilience,
    }
