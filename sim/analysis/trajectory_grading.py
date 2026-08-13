"""SIM-001 MULL-005/MULL-005R sections 4-6 — trajectory tier grading + mechanism tagging + resource
cost.

Governing principle: KEEP TRAJECTORIES, NOT RESOURCES. Mana, tutors, interaction, and
acceleration are not reasons to keep a hand on their own - they matter only insofar as they
create or protect a real engine trajectory. This module answers, for an ALREADY-SIMULATED T1-T3
line (from trajectory_search.py, which tries several - not just the single greedy line), three
questions:
  1. What TIER of trajectory did this hand actually reach (S/A/B/C/D/F)?
  2. What MECHANISM produced it (dork_to_engine, tutor_to_engine, pod_to_engine, ...)?
  3. What did it COST (cards spent, mana consumed, resources retained)?

MULL-005R revisions (t1_t3_trajectory_audit.json - see CMDR-001/002, KINNAN-001, TITHE-001):
  - Tymna the Weaver receives ZERO positive tier credit anywhere in this module, per the pilot's
    explicit strategic directive - it is not a scored destination in this phase.
  - Thrasios, Triton Hero is credited ONLY for a concrete, specific benefit (enabling Mox Amber,
    turning Fierce Guardianship free, or genuine immediate {4}-activation productivity) - never
    for generic "commander castable" or "commander on battlefield" alone.
  - Kinnan, Bonder Prodigy is never a standalone tier destination - it is purely a mana-doubling
    mechanism (already correctly modeled in opening_hand_policy.py's available_sources()) that
    feeds whatever OTHER destination it accelerates.
  - Smothering Tithe is now in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE (promoted from being
    zeroed out entirely - see opening_hand_model.py's own comment for the consistency rationale),
    so it flows through the existing Tier-A path with no special-casing needed here.
  - Abhorrent Oculus is a first-class premium destination once actually on the battlefield
    (never merely in hand, which this project's engine already treats as permanently uncastable -
    see opening_hand_policy.py's OCULUS_NAME handling), graded alongside the Tier-A engine set.

Tiers, individually measured per engine - "measure them individually," never assume tier
membership implies equal strength:
  S - Premium T1 trajectory: a premium one-drop engine (Mystic Remora/Esper Sentinel) cast T1.
  A - Premium T2 trajectory: a Tier-A engine (Rhystic Study/Sylvan Library/Smothering Tithe, or a
      premium one-drop not caught by S) or Abhorrent Oculus online by T2, OR Thrasios providing a
      concrete, specific benefit (Mox Amber enabled, Fierce Guardianship turned free, or genuine
      immediate activation productivity) by T2.
  B - Good T2-T3 secondary-engine trajectory: a Tier-B/C engine (Archivist of Oghma, Runic
      Armasaur, Heartwood Storyteller, Training Grounds, ...) online AND SUPPORTED, a supported
      Survival/Pod, Oculus online by T3, or Thrasios's concrete benefit arriving specifically by
      T3 (not T2).
  C - T3-only or weakly supported: an engine exists but is unsupported, or only arrives T3.
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
from opening_hand_policy import OCULUS_NAME
import trajectory_metrics as tm

CREATURE_ACCEL = {n for n, spec in __import__("opening_hand_model").MANA_SOURCES.items() if spec.get("creature")}
ONE_SHOT_ACCEL = {n for n, spec in __import__("opening_hand_model").MANA_SOURCES.items() if spec.get("one_shot") or spec.get("from_hand")}
PERSISTENT_NONCREATURE_ACCEL = set(ACCELERATION) - CREATURE_ACCEL - ONE_SHOT_ACCEL

TIER_ORDER = ["S", "A", "B", "C", "D", "F"]

# Cast-log classes that put a card onto the battlefield "for real" (used by _engine_online_turn) -
# includes the MULL-005R battlefield-search mechanisms alongside the original cast classes.
ONLINE_CLASSES = (
    "commander", "engine", "premium_engine", "paid_accel", "free_accel",
    "pod_found", "battlefield_tutor_found", "battlefield_land_tutor_found",
)
PREMIUM_DESTINATIONS = ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE | PREMIUM_ONE_DROP_ENGINES | {OCULUS_NAME}


def _engine_online_turn(state, name):
    """First turn `name` appears on the battlefield (commander or nonland perm), or None."""
    for (t, n, c) in state.cast_log:
        if n == name and c in ONLINE_CLASSES:
            return t
    return None


def _first_cast_turn(state, name):
    for (t, n, c) in state.cast_log:
        if n == name:
            return t
    return None


def _thrasios_concrete_benefit_turn(state, cards, snapshots):
    """MULL-005R (CMDR-002): Thrasios is credited ONLY for a specific, concrete benefit - never
    for generic commander presence. Returns the earliest turn (2 or 3) any of the three named
    concrete benefits is real, or None. All three checks require Thrasios ON THE BATTLEFIELD by
    that turn (already correctly required by the base engine for Mox Amber's `controls_legendary`
    gate and Fierce Guardianship's `free_if_commander` gate - see t1_t3_trajectory_audit.json
    CMDR-002 - this function only adds the SCORING distinction, not new legality)."""
    thras_turn = _engine_online_turn(state, "Thrasios, Triton Hero")
    if thras_turn is None:
        return None
    for turn in (2, 3):
        if turn < thras_turn:
            continue
        snap = snapshots.get(turn)
        if snap is None:
            continue
        battlefield_by_turn = {p.name for p in state.nonland_perms if p.entered_turn <= turn}
        if "Thrasios, Triton Hero" not in battlefield_by_turn:
            continue
        # (1) enables Mox Amber - Amber is on the battlefield (only possible with a legendary
        #     creature/PW already in play, per opening_hand_model.py's controls_legendary gate).
        if "Mox Amber" in battlefield_by_turn:
            return turn
        # (2) turns Fierce Guardianship free/live - it's genuinely still in hand AND live via the
        #     free-commander path (interaction_is_live checks nonland_perms for a commander, so
        #     this is only true because Thrasios is actually on the battlefield, not merely
        #     castable - see interaction_model.py's ALT_COST_SPECS "free_if_commander").
        if "Fierce Guardianship" in state.hand:
            from interaction_model import interaction_is_live
            if interaction_is_live("Fierce Guardianship", state, cards):
                return turn
        # (3) genuine immediate {4}-activation productivity (Training Grounds discount included
        #     automatically by thrasios_productivity's own cost check).
        thras_prod = tm.thrasios_productivity(state, cards, snap)
        if thras_prod["thrasios_activation_now"]:
            return turn
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
        if name in battlefield_names and tm._tier_c_supported(name, state, cards):
            return name, _engine_online_turn(state, name)
    return None, None


def grade_trajectory(state, cards, m1, m2, m3):
    """Returns a dict: tier, tier_engine (the specific card/commander that earned the tier),
    tier_turn (when it came online), mechanism, resource_cost."""
    # Filtered to ONLINE_CLASSES, matching _engine_online_turn below - cast_log also records
    # non-battlefield events under the SAME card name (a tutor spell being cast: class "tutor"; a
    # creature discarded to Survival: class "survival_discard"), and a card can be both an engine
    # AND legal fodder (e.g. Abhorrent Oculus, a creature, discarded to Survival to find something
    # else) - without this filter, a discarded/consumed card would be misread as "on the
    # battlefield" and could wrongly earn Tier S/A credit for a card that was never actually cast.
    battlefield_t1 = {n for (t, n, c) in state.cast_log if t == 1 and c in ONLINE_CLASSES}
    battlefield_t2 = {n for (t, n, c) in state.cast_log if t <= 2 and c in ONLINE_CLASSES}
    snapshots = {1: m1, 2: m2, 3: m3}

    thras_benefit_turn = _thrasios_concrete_benefit_turn(state, cards, snapshots)

    # ---- Tier S: premium one-drop cast T1 ----
    premium_t1 = battlefield_t1 & PREMIUM_ONE_DROP_ENGINES
    if premium_t1:
        name = sorted(premium_t1)[0]
        return _finish("S", name, 1, state, cards, m1, m2, m3)

    # ---- Tier A: a Tier-A engine/Oculus online by T2, or Thrasios's concrete benefit by T2 ----
    tier_a_t2 = battlefield_t2 & PREMIUM_DESTINATIONS
    if tier_a_t2:
        name = sorted(tier_a_t2)[0]
        return _finish("A", name, _engine_online_turn(state, name), state, cards, m1, m2, m3)
    if thras_benefit_turn == 2:
        return _finish("A", "Thrasios, Triton Hero", 2, state, cards, m1, m2, m3)

    # ---- Tier B: Oculus by T3, a supported Tier-B/C engine (secondary), or Thrasios's concrete
    #      benefit specifically by T3 ----
    # Oculus is checked FIRST: a generic "Pod is supported" check (ENGINE_TIER_B_HIGH_LEVERAGE_
    # INFRASTRUCTURE's own creature_count()>=1 fodder check) would otherwise trivially pass
    # merely because Oculus ITSELF is a creature now on the battlefield, incorrectly crediting
    # idle Pod infrastructure over the premium destination Pod just found.
    if OCULUS_NAME in {p.name for p in state.nonland_perms}:
        return _finish("B", OCULUS_NAME, _engine_online_turn(state, OCULUS_NAME), state, cards, m1, m2, m3)
    name, turn = _t2_or_t3_supported_tier_b_or_c(state, cards, 3)
    if name:
        return _finish("B", name, turn, state, cards, m1, m2, m3)
    if thras_benefit_turn == 3:
        return _finish("B", "Thrasios, Triton Hero", 3, state, cards, m1, m2, m3)

    # ---- Tier C: an engine exists but is unsupported / arrives late ----
    any_engine_on_bf = {p.name for p in state.nonland_perms} & (
        ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE | ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE
        | ENGINE_TIER_C_CONDITIONAL_VALUE | PREMIUM_ONE_DROP_ENGINES
    )
    thras_on_bf = "Thrasios, Triton Hero" in {p.name for p in state.nonland_perms}
    if any_engine_on_bf or thras_on_bf:
        name = sorted(any_engine_on_bf)[0] if any_engine_on_bf else "Thrasios, Triton Hero"
        return _finish("C", name, _first_cast_turn(state, name), state, cards, m1, m2, m3)

    # ---- Tier F vs D: genuine mana/color failure vs merely no engine found ----
    if m3["total_mana"] < 2 or (not m3["all_wubg"] and m3["total_mana"] < 3):
        return _finish("F", None, None, state, cards, m1, m2, m3)
    return _finish("D", None, None, state, cards, m1, m2, m3)


def _mechanism(state, cards, tier_engine, tier_turn):
    if tier_engine is None:
        return "none"
    if tier_engine == "Thrasios, Triton Hero":
        return "commander_engine"
    if tier_engine == CRADLE:
        return "cradle_development"

    found_class = next((c for (t, n, c) in state.cast_log if n == tier_engine and t == tier_turn), None)
    if found_class == "pod_found":
        return "pod_to_engine" if tier_engine != OCULUS_NAME else "pod_to_oculus"
    if found_class == "battlefield_tutor_found":
        return "battlefield_tutor_to_engine" if tier_engine != OCULUS_NAME else "battlefield_tutor_to_oculus"
    if found_class == "battlefield_land_tutor_found":
        return "battlefield_land_tutor_to_engine"

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
    return "natural_engine"


def _finish(tier, tier_engine, tier_turn, state, cards, m1, m2, m3):
    mechanism = _mechanism(state, cards, tier_engine, tier_turn)
    # MULL-005R (t1_t3_trajectory_audit.json AGENCY-001, assignment section 9): distinguish FREE
    # from PAID retained interaction rather than one generic "+interaction" suffix - a hand that
    # kept a real destination AND still has Force of Will pitchable for free is a materially
    # different, stronger state than one that kept the destination but only has interaction it
    # would need to tap out for.
    interaction_is_free = m3["has_live_interaction"] and m3["free_or_alt_cost_interaction_live"]
    interaction_is_paid_only = m3["has_live_interaction"] and not m3["free_or_alt_cost_interaction_live"]
    has_real_destination = tier not in ("D", "F") and mechanism != "none"
    # MULL-005R (t1_t3_trajectory_audit.json COMBO-001, assignment section 11): verified combo
    # proximity is an UPSIDE MODIFIER on top of a real destination, never a destination or tier
    # driver on its own - grade_trajectory() above never reads either flag, so a hand cannot reach
    # a higher tier from combo proximity alone. Sourced entirely from the existing verified-combo
    # registry (interactions/verified/, deterministic_win_available / one_action_from_verified_win
    # in opening_hand_metrics.snapshot_metrics) - no new speculative combo line was added this
    # phase (COMBO-001 checked the assignment's five named example cards and found none).
    verified_combo_proximity = m3["deterministic_win_available"] or m3["one_action_from_verified_win"]
    if m3["has_live_interaction"]:
        if mechanism == "none":
            mechanism = "interaction_only"
        elif interaction_is_free:
            mechanism = mechanism + "+free_interaction"
        else:
            mechanism = mechanism + "+paid_interaction"
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
        "commander_access": tier_engine == "Thrasios, Triton Hero",
        "engine_plus_live_free_interaction": has_real_destination and interaction_is_free,
        "engine_plus_live_paid_interaction": has_real_destination and interaction_is_paid_only,
        "engine_plus_verified_combo_proximity": has_real_destination and verified_combo_proximity,
    }
    return {
        "tier": tier, "tier_engine": tier_engine, "tier_turn": tier_turn,
        "mechanism": mechanism, "resource_cost": resource_cost,
    }
