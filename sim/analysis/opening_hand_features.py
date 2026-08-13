"""SIM-001 SOLO-004 — opener-visible feature extraction.

Per the SOLO-004 spec: features must be derivable from ONLY the seven-card opening hand plus
known deck construction (which commanders exist, which duals a fetchland can legally find in the
remaining library) - never from future draws, RNG seed identity, or any post-T1 simulated state.
This module is deliberately more careful than SOLO-002's `derive_mulligan_heuristics.raw_hand_
features` (superseded, kept for provenance) about one recurring mistake that module made no
attempt to avoid: **a card being "in hand" is not the same fact as that card being usable.**

Two layers of features are produced, both still opener-visible:

1. `raw_hand_features()` - pure hand inspection, zero simulation. Land counts, card-taxonomy
   presence (tutor/engine/interaction/acceleration), colors the hand's own lands can produce,
   fetch-target legality (checked against the real remaining library, which for a keep-everything
   census is "the deck minus this hand" - known deck construction, not a future draw).
2. `t1_executable_features()` - runs ONE greedy-policy turn (`develop_turn`, turn 1 only) on a
   throwaway HandState to ask "if this hand is kept, what can turn 1 actually accomplish?" This
   is still opener-only information (nothing beyond the 7 cards has been seen or decided), and
   reuses the exact same validated SOLO-003R engine (mana tapping, summoning sickness, Kinnan,
   real alternate-cost interaction) rather than re-implementing castability logic. Turn 1 is
   pre-draw on the play and (by construction here) evaluated the same way on the draw - the
   opener is the same 7 cards either way; SOLO-004 section 19 handles play/draw separately at the
   OUTCOME level, not by changing what "opener-visible" means.

`extract_opener_features()` combines both into one flat dict, then derives the explicit
structural AND-combinations SOLO-004 section 2 calls out by name (e.g. "1 land + executable T1
acceleration"), rather than leaving interaction terms implicit for a downstream model to
rediscover by chance.
"""
import random

from opening_hand_model import (
    COLORS, parse_cost, card_colors, CRADLE, MANA_SOURCES, ACCELERATION, TUTORS,
    INTERACTION_CASTABLE, ENGINES, PREMIUM_ONE_DROP_ENGINES, COMMANDERS, MOX_FAMILY,
    TUTOR_TARGETS, LAND_COLOR_SETS, GENERIC_LANDS, GEMSTONE_CAVERNS, EXOTIC_ORCHARD,
    FETCH_LANDS, FETCH_LAND_TARGET_TYPES, DUAL_LAND_BASIC_TYPES, BASIC_TYPE_COLOR,
    ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE, ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY, is_currently_castable
from interaction_model import interaction_is_live

ONE_SHOT_ACCEL = {n for n, spec in MANA_SOURCES.items() if spec.get("one_shot") or spec.get("from_hand")}
CREATURE_ACCEL = {n for n, spec in MANA_SOURCES.items() if spec.get("creature")}
NONCREATURE_PERSISTENT_ACCEL = set(ACCELERATION) - CREATURE_ACCEL - ONE_SHOT_ACCEL


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def _cheap(name, cards, max_mana=2):
    gen, pips, x = parse_cost(cards[name]["mana_cost"])
    return x == 0 and (gen + len(pips)) <= max_mana


# ---------------------------------------------------------------- raw hand (no simulation) ----

def raw_hand_features(hand, library, cards):
    lands = [c for c in hand if _is_land(c, cards)]
    nonlands = [c for c in hand if c not in lands]

    fetch_lands_in_hand = [l for l in lands if l in FETCH_LANDS]
    # Colors the hand's OWN lands can produce right now, plus what each fetch in hand could add -
    # "known deck construction" (which duals remain in the library), not a future draw.
    direct_colors = set()
    for l in lands:
        if l == CRADLE:
            continue  # Cradle's color output depends on creatures controlled, not a flat set
        if l in GENERIC_LANDS or l in (GEMSTONE_CAVERNS, EXOTIC_ORCHARD):
            continue
        direct_colors |= LAND_COLOR_SETS.get(l, set())
    fetchable_colors = set()
    for f in fetch_lands_in_hand:
        wanted = FETCH_LAND_TARGET_TYPES.get(f, frozenset())
        for dual, types in DUAL_LAND_BASIC_TYPES.items():
            if (types & wanted) and dual in library:
                fetchable_colors |= {BASIC_TYPE_COLOR[t] for t in types}
    potential_colors = direct_colors | fetchable_colors

    tutors_in_hand = [c for c in nonlands if c in TUTORS]
    engines_in_hand = [c for c in nonlands if c in ENGINES]
    interaction_in_hand = [c for c in nonlands if c in INTERACTION_CASTABLE]
    accel_in_hand = [c for c in nonlands if c in ACCELERATION]
    creature_count_in_hand = sum(1 for c in nonlands if "Creature" in cards[c]["type"])

    tutor_target_reach = set()
    for t in tutors_in_hand:
        tutor_target_reach |= TUTOR_TARGETS.get(t, frozenset())

    return {
        "land_count": len(lands),
        "land_count_bucket": len(lands) if len(lands) <= 4 else "5+",
        "fetch_land_count": len(fetch_lands_in_hand),
        "utility_land_ancient_tomb": "Ancient Tomb" in lands,
        "utility_land_city_of_traitors": "City of Traitors" in lands,
        "utility_land_gemstone_caverns": GEMSTONE_CAVERNS in lands,
        "utility_land_cradle": CRADLE in lands,
        "colors_direct_from_lands": sorted(direct_colors),
        "colors_potential_with_fetches": sorted(potential_colors),
        "distinct_colors_direct": len(direct_colors),
        "distinct_colors_potential": len(potential_colors),
        "all_wubg_direct": set(COLORS) <= direct_colors,
        "all_wubg_potential": set(COLORS) <= potential_colors,
        "color_bottleneck_direct": sorted(set(COLORS) - direct_colors),

        "accel_card_count": len(accel_in_hand),
        "has_any_accel_card": len(accel_in_hand) > 0,
        "has_creature_accel_card": any(c in CREATURE_ACCEL for c in accel_in_hand),
        "has_noncreature_persistent_accel_card": any(c in NONCREATURE_PERSISTENT_ACCEL for c in accel_in_hand),
        "has_one_shot_accel_card": any(c in ONE_SHOT_ACCEL for c in accel_in_hand),
        "has_mox_family_card": any(c in MOX_FAMILY for c in accel_in_hand),
        "has_sol_ring": "Sol Ring" in accel_in_hand,

        "tutor_count": len(tutors_in_hand),
        "has_tutor_card": len(tutors_in_hand) > 0,
        "tutor_names": sorted(tutors_in_hand),
        "tutor_reaches_engine": "engine" in tutor_target_reach,
        "tutor_reaches_combo_piece": "combo_piece" in tutor_target_reach,
        "tutor_reaches_interaction": "interaction" in tutor_target_reach,
        "tutor_reaches_land_or_cradle": bool({"land", "cradle"} & tutor_target_reach),
        "tutor_cheap": any(_cheap(t, cards, 2) for t in tutors_in_hand),

        "engine_count": len(engines_in_hand),
        "has_any_engine_card": len(engines_in_hand) > 0,
        "has_tier_a_engine_card": any(c in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE for c in engines_in_hand),
        "has_tier_b_engine_card": any(c in ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE for c in engines_in_hand),
        "has_premium_one_drop_card": any(c in PREMIUM_ONE_DROP_ENGINES for c in engines_in_hand),
        "has_cheap_engine_card": any(c in ENGINES and _cheap(c, cards, 2) for c in engines_in_hand),

        "interaction_count": len(interaction_in_hand),
        "has_any_interaction_card": len(interaction_in_hand) > 0,
        "interaction_only_hand": len(interaction_in_hand) >= 1 and not engines_in_hand and not accel_in_hand,
        "interaction_density_2plus": len(interaction_in_hand) >= 2,

        "creature_count_in_hand": creature_count_in_hand,
        "has_commander_relevant_creature_2plus": creature_count_in_hand >= 2,

        "nonland_count": len(nonlands),
        "cards_costing_3plus": sum(
            1 for c in nonlands if parse_cost(cards[c]["mana_cost"])[0] + len(parse_cost(cards[c]["mana_cost"])[1]) >= 3
        ),
    }


# ---------------------------------------------------------- T1-executable (one-turn sim) ------

def t1_executable_features_from_state(state, cards):
    """Same extraction as t1_executable_features(), but from a HandState that ALREADY had turn 1
    developed by the caller (e.g. a dataset generator that's about to continue on to T2/T3 on the
    same state anyway) - avoids simulating turn 1 twice. Still opener-only information: nothing
    beyond what turn 1 could see/decide from the original 7 cards is used here."""
    cast_t1 = {n for (t, n, c) in state.cast_log if t == 1}
    accel_cast_t1 = cast_t1 & set(ACCELERATION)
    engine_cast_t1 = cast_t1 & set(ENGINES)
    tutor_cast_t1 = cast_t1 & set(TUTORS)

    turn_hand = set(state.hand) | cast_t1
    interaction_candidates_t1 = [n for n in turn_hand if n in INTERACTION_CASTABLE]
    live_interaction_t1 = [n for n in interaction_candidates_t1 if interaction_is_live(n, state, cards)]

    return {
        "t1_land_played": len(state.lands) >= 1,
        "t1_mana_available_now": state.total_mana_value(),
        "t1_accel_cast": sorted(accel_cast_t1),
        "t1_accel_executable_now": any(n in NONCREATURE_PERSISTENT_ACCEL | ONE_SHOT_ACCEL for n in accel_cast_t1),
        "t1_accel_creature_only": bool(accel_cast_t1) and not any(
            n in NONCREATURE_PERSISTENT_ACCEL | ONE_SHOT_ACCEL for n in accel_cast_t1
        ),
        "t1_engine_cast": sorted(engine_cast_t1),
        "t1_any_engine_cast": bool(engine_cast_t1),
        "t1_premium_engine_cast": bool(engine_cast_t1 & PREMIUM_ONE_DROP_ENGINES),
        "t1_tutor_cast": sorted(tutor_cast_t1),
        "t1_any_tutor_cast": bool(tutor_cast_t1),
        "t1_live_interaction": sorted(live_interaction_t1),
        "t1_has_live_interaction": len(live_interaction_t1) > 0,
        "t1_cards_in_hand_after": len(state.hand),
        "t1_ceiling_mana_next_turn": state.total_mana_value() + 1,  # +1 for T2's own land drop, ignoring T2 draws
    }


def t1_executable_features(hand, library, on_play, cards, rng_seed=0):
    """Standalone convenience wrapper: builds a throwaway state, develops turn 1, and extracts
    the same fields as t1_executable_features_from_state(). Use the _from_state() variant
    directly when the caller already has (or is about to build) a HandState it will keep
    developing past turn 1, to avoid simulating turn 1 twice."""
    state = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(rng_seed), cards=cards)
    develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
    return t1_executable_features_from_state(state, cards)


# ------------------------------------------------------------------ combined + structural -----

def derive_structural_features(raw, t1):
    """SOLO-004 section 2's explicit AND-combinations, factored out so callers that already have
    `raw`/`t1` dicts (e.g. a dataset generator threading its own HandState through T1-T3) don't
    need to go through extract_opener_features()'s convenience (and re-simulating) API."""
    f = {}
    lc = raw["land_count"]
    f["struct_1land_plus_executable_accel"] = lc == 1 and t1["t1_accel_executable_now"]
    f["struct_1land_plus_accel_plus_engine"] = (
        lc == 1 and raw["has_any_accel_card"] and raw["has_any_engine_card"]
    )
    f["struct_1land_plus_accel_plus_tutor"] = (
        lc == 1 and raw["has_any_accel_card"] and raw["has_tutor_card"]
    )
    f["struct_2land_plus_engine"] = lc == 2 and raw["has_any_engine_card"]
    f["struct_2land_plus_t1_development"] = lc == 2 and (t1["t1_any_engine_cast"] or t1["t1_accel_executable_now"])
    f["struct_2land_plus_engine_plus_interaction"] = (
        lc == 2 and raw["has_any_engine_card"] and raw["has_any_interaction_card"]
    )
    f["struct_2land_plus_tutor"] = lc == 2 and raw["has_tutor_card"]
    f["struct_2land_interaction_only"] = lc == 2 and raw["interaction_only_hand"]
    f["struct_3land_plus_engine"] = lc == 3 and raw["has_any_engine_card"]
    f["struct_3land_plus_accel"] = lc == 3 and raw["has_any_accel_card"]
    f["struct_3land_sufficient_business"] = lc == 3 and raw["nonland_count"] >= 3 and (
        raw["has_any_engine_card"] or raw["has_tutor_card"] or raw["has_any_interaction_card"]
    )
    f["struct_4plusland_plus_premium_engine"] = lc >= 4 and raw["has_premium_one_drop_card"]
    f["struct_fast_mana_no_payoff"] = (
        raw["has_one_shot_accel_card"] and not raw["has_any_engine_card"] and not raw["has_tutor_card"]
    )
    f["struct_engine_insufficient_colors"] = raw["has_any_engine_card"] and not raw["all_wubg_potential"]
    f["struct_tutor_insufficient_mana"] = raw["has_tutor_card"] and lc <= 1
    f["struct_cradle_plus_creature_density"] = raw["utility_land_cradle"] and raw["creature_count_in_hand"] >= 2
    f["struct_tymna_plus_attack_support"] = raw["creature_count_in_hand"] >= 1  # commander always in command zone
    f["struct_thrasios_plus_mana_infra"] = raw["has_any_accel_card"] or lc >= 2

    return f


def extract_opener_features(hand, library, on_play, cards, rng_seed=0):
    raw = raw_hand_features(hand, library, cards)
    t1 = t1_executable_features(hand, library, on_play, cards, rng_seed=rng_seed)
    return {**raw, **t1, **derive_structural_features(raw, t1)}


FEATURE_KEYS_STABLE_ORDER = None  # populated lazily by callers that need a fixed column order


def feature_key_order(sample_feature_dict):
    return sorted(sample_feature_dict.keys())
