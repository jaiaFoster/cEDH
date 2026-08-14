"""SIM-001 MULL-006 section 7 — draw dependence / outs, new dimension #2.

Distinguishes trajectories ALREADY PRESENT in the opening hand from trajectories that require a
favorable future draw, per the assignment's own example:

    T1 Birds -> T2 Rhystic with second land already present
        is materially different from
    T1 Birds -> T2 Rhystic only if the next draw is a land.

CLASSIFICATION (per trajectory, worst dependency governs):

SELF_CONTAINED
    Every card the winning line uses through tier_turn (the engine card itself, and every land
    played to support it) was either already in the opening hand, or reached the battlefield via a
    card that was already in the opening hand (a hand-held fetchland cracked for a needed dual, or
    a hand-held tutor/Pod/battlefield-search effect finding its target - see TUTOR-SOURCED note
    below). No future draw is required for this specific line.

BROAD_OUTS / NARROW_OUTS / EXACT_OR_NEAR_EXACT
    At least one dependency slot requires a card that was NOT in the opening hand and was NOT
    reached via a hand-held tutor/fetch - i.e., it came from a genuine natural top-of-library draw.
    Classified by outs_count relative to the remaining-library size (SIMULATION_MEASURED exact
    outs count; RULES_VERIFIED hypergeometric probability, not a fabricated estimate):
        outs_count / remaining_library_size >= 0.15  -> BROAD_OUTS
        2 < outs_count / remaining_library_size < 0.15 (and outs_count > 2) -> NARROW_OUTS
        outs_count <= 2                               -> EXACT_OR_NEAR_EXACT
    Thresholds are a disclosed, round convention (not pilot-supplied, not empirically fit) -
    consistent with the "many / relatively small subset / one or few highly specific" language the
    assignment itself uses for these three bands.

TUTOR-SOURCED vs NATURAL-DRAW (assignment's explicit "whether a tutor draw counts differently"):
    A card found by a hand-held tutor spell (cast_log class == "tutor", detected via a tutor
    spell's own cast_log entry at or before the dependency turn) or by a battlefield/Pod search
    effect (cast_log class in pod_found/battlefield_tutor_found/battlefield_land_tutor_found) is
    treated as SELF_CONTAINED, not as draw dependence - it is contingent only on a legal target
    existing in the library (which trajectory_search.py's own candidate generation already
    verifies), not on a favorable random draw. This is a disclosed heuristic proxy (it cannot always
    perfectly attribute which specific tutor found which specific card in a multi-tutor hand), not
    a perfect trace.

OUTS COUNTING (disclosed simplification, not a full color/functional-requirement solver):
    LAND dependency -> outs = every LAND remaining in the deck outside the opening hand (broad
        proxy: in this deck almost any additional land advances the curve, not just the specific
        color actually drawn in this one simulated instance).
    NONLAND (engine-card) dependency -> outs = 1, the literal singleton copy of that exact card
        remaining in the deck (Commander decks are singleton) - always EXACT_OR_NEAR_EXACT. This
        module does NOT attempt to find broader functional substitutes for a missing engine card
        (that would require re-running the bounded search once per candidate substitute across the
        full remaining library - deferred, disclosed BOUNDED_SEARCH_LOWER_BOUND limitation).

PROBABILITY (RULES_VERIFIED exact combinatorics, not fabricated): hypergeometric P(at least one out
among the k draws taken by the dependency's turn) = 1 - C(N-K, k) / C(N, k), where N = remaining
library size right after the opening hand is drawn (pre-mulligan-decision denominator - this
project never conditions on cards already known to have been drawn in other, independent slots),
K = outs_count, k = draws taken by that turn (k = turn-1 on the play, k = turn on the draw, per
develop_turn()'s own draw-skip-on-T1-play rule).
"""
import math
from opening_hand_model import FETCH_LANDS, FETCH_LAND_TARGET_TYPES, DUAL_LAND_BASIC_TYPES

DEPENDENCE_PROVENANCE = "SIMULATION_MEASURED"

TUTOR_FOUND_CLASSES = {"pod_found", "battlefield_tutor_found", "battlefield_land_tutor_found"}

CLASS_ORDER = ["SELF_CONTAINED", "BROAD_OUTS", "NARROW_OUTS", "EXACT_OR_NEAR_EXACT"]
CLASS_RANK = {c: i for i, c in enumerate(CLASS_ORDER)}

BROAD_OUTS_RATIO_THRESHOLD = 0.15
EXACT_OUTS_COUNT_THRESHOLD = 2


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def hypergeometric_at_least_one(N, K, k):
    """P(at least one success in k draws without replacement from N cards containing K
    successes). Exact combinatorics, not an approximation."""
    if N <= 0 or k <= 0 or K <= 0:
        return 0.0
    if K >= N or k >= N:
        return 1.0 if K > 0 else 0.0
    return 1.0 - (math.comb(N - K, k) / math.comb(N, k))


def _draws_by_turn(turn, on_play):
    return (turn - 1) if on_play else turn


def _land_came_from_hand_fetch(land_name, opening_hand, state):
    """True if `land_name` (a land now on the battlefield) was not itself in the opening hand, but
    a fetchland that WAS in the opening hand was cracked (appears in state.graveyard) to find it -
    a hand-sourced trajectory, not a draw dependency. Does not verify target-type matching in
    hands with multiple simultaneous fetches (disclosed simplification - see module docstring)."""
    cracked_hand_fetches = [f for f in FETCH_LANDS if f in opening_hand and f in state.graveyard]
    return bool(cracked_hand_fetches)


def _engine_card_source(tier_engine, tier_turn, opening_hand, state):
    """Returns one of 'hand_direct', 'tutor_sourced', or 'natural_draw' for the card that earned
    the trajectory's tier."""
    if tier_engine in opening_hand:
        return "hand_direct"
    entry = next((e for e in state.cast_log if e[1] == tier_engine and e[0] <= tier_turn), None)
    if entry is not None and entry[2] in TUTOR_FOUND_CLASSES:
        return "tutor_sourced"
    hand_tutor_cast_before = any(
        e[2] == "tutor" and e[0] <= tier_turn for e in state.cast_log
    )
    if hand_tutor_cast_before:
        return "tutor_sourced"
    return "natural_draw"


def _supporting_lands(tier_turn, opening_hand, state):
    """Every land on the battlefield by tier_turn, with its source classification."""
    results = []
    for land in state.lands:
        if land.entered_turn > tier_turn:
            continue
        if land.name in opening_hand:
            source = "hand_direct"
        elif _land_came_from_hand_fetch(land.name, opening_hand, state):
            source = "hand_via_fetch"
        else:
            source = "natural_draw"
        results.append({"land": land.name, "turn": land.entered_turn, "source": source})
    return results


def _classify_outs(outs_count, remaining_library_size):
    if remaining_library_size <= 0:
        return "EXACT_OR_NEAR_EXACT"
    ratio = outs_count / remaining_library_size
    if outs_count <= EXACT_OUTS_COUNT_THRESHOLD:
        return "EXACT_OR_NEAR_EXACT"
    if ratio >= BROAD_OUTS_RATIO_THRESHOLD:
        return "BROAD_OUTS"
    return "NARROW_OUTS"


def classify_trajectory_draw_dependence(state, cards, tier_engine, tier_turn, deck_size, on_play):
    """Returns the full section-7 field set for the winning trajectory (tier_engine earned by
    tier_turn), or None if tier_engine is None (no trajectory / F-tier hand - draw dependence is
    not meaningful for a hand with no destination at all). Uses state.opening_hand (the original
    7-card deal, preserved by HandState regardless of subsequent draws/discards) as the hand-vs-
    draw boundary, not the live, mutated state.hand."""
    if tier_engine is None or tier_turn is None:
        return None

    opening_hand = state.opening_hand
    remaining_library_size = deck_size - len(opening_hand)
    dependencies = []

    engine_source = _engine_card_source(tier_engine, tier_turn, opening_hand, state)
    if engine_source == "natural_draw":
        k = _draws_by_turn(tier_turn, on_play)
        prob = hypergeometric_at_least_one(remaining_library_size, 1, k)
        dependencies.append({
            "slot": "engine_card", "card": tier_engine, "turn": tier_turn, "source": engine_source,
            "outs_count": 1, "outs_type": "singleton_exact_card",
            "draws_available_by_turn": k, "probability_of_success_by_turn": round(prob, 4),
            "classification": "EXACT_OR_NEAR_EXACT",
        })

    full_remaining_pool = set(cards) - set(opening_hand)  # pre-hoc: deck minus hand, not
    # conditioned on what THIS simulated shuffle happened to draw in other slots - see module
    # docstring's "PROBABILITY" section.
    for land_info in _supporting_lands(tier_turn, opening_hand, state):
        if land_info["source"] != "natural_draw":
            continue
        outs_count = sum(1 for n in full_remaining_pool if _is_land(n, cards))
        k = _draws_by_turn(land_info["turn"], on_play)
        prob = hypergeometric_at_least_one(remaining_library_size, outs_count, k)
        dependencies.append({
            "slot": "supporting_land", "card": land_info["land"], "turn": land_info["turn"],
            "source": land_info["source"], "outs_count": outs_count, "outs_type": "any_land",
            "draws_available_by_turn": k, "probability_of_success_by_turn": round(prob, 4),
            "classification": _classify_outs(outs_count, remaining_library_size),
        })

    if not dependencies:
        overall = "SELF_CONTAINED"
    else:
        overall = max(dependencies, key=lambda d: CLASS_RANK[d["classification"]])["classification"]

    return {
        "tier_engine": tier_engine, "tier_turn": tier_turn,
        "remaining_library_size": remaining_library_size,
        "overall_classification": overall,
        "dependency_count": len(dependencies),
        "dependencies": dependencies,
        "multiple_dependency_classes_overlap": len({d["outs_type"] for d in dependencies}) > 1,
    }
