"""SIM-001 MULL-005 sections 4-6 — trajectory tier grading + mechanism tagging + resource cost.

Governing principle (the whole point of MULL-005): KEEP TRAJECTORIES, NOT RESOURCES. Mana,
tutors, interaction, and acceleration are not reasons to keep a hand on their own - they matter
only insofar as they create or protect a real engine trajectory. This module answers, for an
ALREADY-SIMULATED T1-T3 line (from trajectory_search.py, which tries several - not just the
single greedy line), three questions:
  1. What TIER of trajectory did this hand actually reach (S/A/B/C/D/F)?
  2. What MECHANISM produced it (dork_to_engine, tutor_to_engine, natural_engine, ...)?
  3. What did it COST (cards spent, mana consumed, resources retained)?

Tiers (section 4), individually measured per engine - "measure them individually," never assume
tier membership implies equal strength:
  S - Premium T1 trajectory: a premium one-drop engine (Mystic Remora/Esper Sentinel) cast T1, or
      an accelerated T1 cast of a Tier-A engine that wouldn't otherwise fit.
  A - Premium T2 trajectory: a Tier-A engine (Rhystic Study/Sylvan Library, or a premium one-drop
      not caught by S) online by T2, OR a genuinely productive commander online by T2 (Tymna with
      real attack-eligible support, Thrasios actually able to activate, Kinnan with a real mana
      dork to double).
  B - Good T2 secondary-engine trajectory: a Tier-B/C engine (Archivist of Oghma, Runic Armasaur,
      Heartwood Storyteller, Kinnan, Training Grounds, ...) online AND SUPPORTED by T2/T3, or a
      supported Survival/Pod, or a productive commander online by T3 specifically (not T2).
  C - T3-only or weakly supported: an engine exists but is unsupported, or only arrives T3, or a
      commander is on the battlefield without real productivity.
  D - No meaningful engine trajectory at all, but the hand isn't outright broken (mana/tutor/
      interaction present with no payoff, or a passive land-heavy hand).
  F - Mana/color/nonfunctional failure - real mana shortfall or color lockout prevented any
      meaningful development, independent of what was drawn.
"""
from opening_hand_model import (
    CRADLE, PREMIUM_ONE_DROP_ENGINES, ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE,
    ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE, ENGINE_TIER_C_CONDITIONAL_VALUE,
    ACCELERATION, TUTORS, INTERACTION_CASTABLE, MOX_FAMILY,
)
import trajectory_metrics as tm

CREATURE_ACCEL = {n for n, spec in __import__("opening_hand_model").MANA_SOURCES.items() if spec.get("creature")}
ONE_SHOT_ACCEL = {n for n, spec in __import__("opening_hand_model").MANA_SOURCES.items() if spec.get("one_shot") or spec.get("from_hand")}
PERSISTENT_NONCREATURE_ACCEL = set(ACCELERATION) - CREATURE_ACCEL - ONE_SHOT_ACCEL

TIER_ORDER = ["S", "A", "B", "C", "D", "F"]


def _engine_online_turn(state, name):
    """First turn `name` appears on the battlefield (commander or nonland perm), or None."""
    for (t, n, c) in state.cast_log:
        if n == name and c in ("commander", "engine", "premium_engine", "paid_accel", "free_accel"):
            return t
    return None


def _first_cast_turn(state, name):
    for (t, n, c) in state.cast_log:
        if n == name:
            return t
    return None


def _t2_or_t3_supported_tier_b_or_c(state, cards, cast_by_turn):
    """Returns (name, turn) for the best Tier-B/C engine actually SUPPORTED by the given turn -
    reuses trajectory_metrics's own supported-checks so this stays consistent with every other
    SOLO-003R/SOLO-004 metric that already answers 'is this engine's condition actually met'."""
    battlefield_names = {p.name for p in state.nonland_perms if p.entered_turn <= cast_by_turn}
    for name in ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE:
        if name in battlefield_names and tm._tier_b_supported(name, state, cards):
            return name, _engine_online_turn(state, name)
    for name in ENGINE_TIER_C_CONDITIONAL_VALUE:
        if name == "Tymna the Weaver":
            continue  # commanders handled separately (productivity, not generic tier-C support)
        if name in battlefield_names and tm._tier_c_supported(name, state, cards):
            return name, _engine_online_turn(state, name)
    return None, None


def grade_trajectory(state, cards, m1, m2, m3):
    """Returns a dict: tier, tier_engine (the specific card/commander that earned the tier),
    tier_turn (when it came online), mechanism, resource_cost."""
    battlefield_t1 = {n for (t, n, c) in state.cast_log if t == 1}
    battlefield_t2 = {n for (t, n, c) in state.cast_log if t <= 2}

    thras = tm.thrasios_productivity(state, cards, m3)
    tymna_tier = tm.tymna_attack_capacity(state, cards, _first_cast_turn(state, "Tymna the Weaver"))

    # ---- Tier S: premium one-drop cast T1 ----
    premium_t1 = battlefield_t1 & PREMIUM_ONE_DROP_ENGINES
    if premium_t1:
        name = sorted(premium_t1)[0]
        return _finish("S", name, 1, state, cards, m1, m2, m3)

    # ---- Tier A: a Tier-A engine (or premium not caught above) online by T2, or a genuinely
    #      productive commander online by T2 ----
    tier_a_t2 = (battlefield_t2 & ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE) | (battlefield_t2 & PREMIUM_ONE_DROP_ENGINES)
    if tier_a_t2:
        name = sorted(tier_a_t2)[0]
        return _finish("A", name, _engine_online_turn(state, name), state, cards, m1, m2, m3)
    if "Thrasios, Triton Hero" in battlefield_t2 and thras["thrasios_activation_now"] and m2 is not None:
        # productive specifically by the T2 snapshot, not just eventually by T3
        thras_t2 = tm.thrasios_productivity(state, cards, m2)
        if thras_t2["thrasios_activation_now"]:
            return _finish("A", "Thrasios, Triton Hero", 2, state, cards, m1, m2, m3)
    if "Tymna the Weaver" in battlefield_t2 and m2 is not None and state.attack_eligible_creature_count() >= 1:
        return _finish("A", "Tymna the Weaver", 2, state, cards, m1, m2, m3)
    if "Kinnan, Bonder Prodigy" in battlefield_t2 and tm._tier_b_supported("Kinnan, Bonder Prodigy", state, cards):
        return _finish("A", "Kinnan, Bonder Prodigy", 2, state, cards, m1, m2, m3)

    # ---- Tier B: a supported Tier-B/C engine (secondary), or a productive commander, by T3 ----
    name, turn = _t2_or_t3_supported_tier_b_or_c(state, cards, 3)
    if name:
        return _finish("B", name, turn, state, cards, m1, m2, m3)
    if thras["thrasios_activation_now"]:
        return _finish("B", "Thrasios, Triton Hero", _first_cast_turn(state, "Thrasios, Triton Hero"), state, cards, m1, m2, m3)
    if tymna_tier["tymna_deployed"] and tymna_tier["tymna_attack_capacity_tier"] in ("attack_capacity_medium", "attack_capacity_high"):
        return _finish("B", "Tymna the Weaver", _first_cast_turn(state, "Tymna the Weaver"), state, cards, m1, m2, m3)

    # ---- Tier C: an engine exists but is unsupported / arrives late, or an unproductive commander ----
    any_engine_on_bf = {p.name for p in state.nonland_perms} & (
        ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE | ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE
        | ENGINE_TIER_C_CONDITIONAL_VALUE | PREMIUM_ONE_DROP_ENGINES
    )
    if any_engine_on_bf or tymna_tier["tymna_deployed"] or thras["thrasios_on_battlefield"]:
        name = sorted(any_engine_on_bf)[0] if any_engine_on_bf else (
            "Tymna the Weaver" if tymna_tier["tymna_deployed"] else "Thrasios, Triton Hero"
        )
        return _finish("C", name, _first_cast_turn(state, name), state, cards, m1, m2, m3)

    # ---- Tier F vs D: genuine mana/color failure vs merely no engine found ----
    if m3["total_mana"] < 2 or (not m3["all_wubg"] and m3["total_mana"] < 3):
        return _finish("F", None, None, state, cards, m1, m2, m3)
    return _finish("D", None, None, state, cards, m1, m2, m3)


def _mechanism(state, cards, tier_engine, tier_turn):
    if tier_engine is None:
        return "none"
    if tier_engine in ("Tymna the Weaver", "Thrasios, Triton Hero"):
        return "commander_engine"
    if tier_engine == CRADLE:
        return "cradle_development"
    cast_before = [n for (t, n, c) in state.cast_log if t < (tier_turn or 99)]
    tutor_used = any(n in TUTORS for n in cast_before)
    accel_used = [n for n in cast_before if n in ACCELERATION]
    creature_accel = any(n in CREATURE_ACCEL for n in accel_used)
    persistent_accel = any(n in PERSISTENT_NONCREATURE_ACCEL for n in accel_used)
    burst_accel = any(n in ONE_SHOT_ACCEL for n in accel_used)
    other_engines_before = [
        n for (t, n, c) in state.cast_log
        if t < (tier_turn or 99) and c in ("engine", "premium_engine")
    ]
    if tutor_used and accel_used:
        return "tutor_plus_accel_to_engine"
    if tutor_used:
        return "tutor_to_engine"
    if other_engines_before:
        return "engine_to_second_engine"
    if creature_accel:
        return "dork_to_engine"
    if persistent_accel:
        return "rock_to_engine"
    if burst_accel:
        return "burst_mana_to_engine"
    if tier_turn is not None and tier_turn == 1:
        return "natural_engine"
    return "natural_engine"


def _finish(tier, tier_engine, tier_turn, state, cards, m1, m2, m3):
    mechanism = _mechanism(state, cards, tier_engine, tier_turn)
    if m3["has_live_interaction"]:
        mechanism = mechanism + "+interaction" if mechanism != "none" else "interaction_only"
    tutor_still_live = m3["tutor_castable"]
    if tutor_still_live and "tutor" not in mechanism and mechanism not in ("none", "interaction_only"):
        mechanism = mechanism + "+tutor_retained"

    resource_cost = {
        "cards_spent_by_tier_turn": len([1 for (t, n, c) in state.cast_log if t <= (tier_turn or 3)]),
        "one_shot_mana_consumed": len(state.temp_mana_used_log),
        "persistent_mana_remaining_t3": m3["total_mana"],
        "cards_in_hand_t3": m3["cards_in_hand"],
        "live_interaction_retained_t3": m3["has_live_interaction"],
        "tutor_consumed": any(n in TUTORS for (t, n, c) in state.cast_log),
        "tutor_still_live_t3": tutor_still_live,
        "second_engine_potential": m3["two_plus_engines_active"],
        "commander_access": tier_engine in ("Tymna the Weaver", "Thrasios, Triton Hero"),
    }
    return {
        "tier": tier, "tier_engine": tier_engine, "tier_turn": tier_turn,
        "mechanism": mechanism, "resource_cost": resource_cost,
    }
