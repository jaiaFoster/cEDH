"""SIM-001 SOLO-003 — early-game trajectory metrics.

Per the SOLO-003 conceptual correction: commander presence (Tymna castable/supported, Thrasios
on battlefield) is NOT a headline success measure. This module measures velocity, compounding
advantage, agency, and conversion potential instead, using the SOLO-002R-corrected mana engine
and the SOLO-003 engine tiers (opening_hand_model.ENGINE_TIERS) and real alternate-cost
interaction model (interaction_model.py).

Structural model limitation, disclosed rather than silently absorbed into a misleadingly high
"engine active" number: several Tier-C conditional engines trigger off OPPONENT actions this
solo/no-opponent Level 1-2 model never simulates (Heartwood Storyteller, Runic Armasaur,
Archivist of Oghma all key off "an opponent..."; Smothering Tithe off opponents making tokens;
Delney needs a combat step, not modeled). These are classified TIER_C_STRUCTURALLY_INERT below -
being on the battlefield is tracked (so a census can still report how often they're drawn/cast),
but they never count as "supported"/productive in any trajectory metric. This is a genuine,
disclosed finding about this deck's card choices in a solo-goldfish context, not a modeling gap
to silently paper over.
"""
from opening_hand_model import (
    COLORS, parse_cost, CRADLE, MANA_SOURCES, ACCELERATION, TUTORS, COMMANDERS,
    ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE, ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE,
    ENGINE_TIER_C_CONDITIONAL_VALUE, ENGINE_TIER_D_MANA_DEVELOPMENT, ENGINE_TIER_E_TUTOR_CONVERSION,
)
from opening_hand_policy import is_currently_castable
from interaction_model import interaction_is_live

TIER_C_STRUCTURALLY_INERT = {
    "Heartwood Storyteller", "Runic Armasaur", "Archivist of Oghma", "Smothering Tithe",
    "Delney, Streetwise Lookout",
}
TRAINING_GROUNDS_ACTIVATION_DISCOUNT = 2  # "costs {2} less... can't reduce below one mana"


def _tier_c_supported(name, state, cards):
    """Whether a Tier-C conditional engine's real condition is actually satisfied right now.
    See module docstring for which ones are structurally inert in a solo model."""
    if name in TIER_C_STRUCTURALLY_INERT:
        return False
    if name == "Tymna the Weaver":
        return state.creature_count() >= 1
    if name == "Faerie Mastermind":
        # its own {3}{U} "each player draws a card" ability is the only solo-usable line
        return is_currently_castable(state, *parse_cost("{3}{U}")[:2])
    if name == "Deathrite Shaman":
        return False  # graveyard-mana ability not modeled (documented SOLO-002R simplification)
    return False


def _tier_b_supported(name, state, cards):
    """Whether a Tier-B high-leverage infrastructure engine's supporting board state is actually
    present, not merely the card itself."""
    if name == "Gaea's Cradle":
        return state.creature_count() >= 2  # meaningful creature count, not just "in play"
    if name == "Birthing Pod":
        return state.creature_count() >= 1  # a legal sacrifice body
    if name == "Survival of the Fittest":
        return any("Creature" in cards[c]["type"] for c in state.hand)  # a discardable creature
    if name == "Kinnan, Bonder Prodigy":
        return any(
            MANA_SOURCES.get(p.name, {}).get("creature") for p in state.nonland_perms
        )  # a mana dork on board for Kinnan to double
    if name == "Training Grounds":
        # only meaningfully reduces something in this deck if Thrasios (the only creature with a
        # modeled activated mana cost) is also on the battlefield.
        return any(p.name == "Thrasios, Triton Hero" for p in state.nonland_perms)
    return False


def thrasios_activation_cost_generic(state):
    """{4}, reduced by Training Grounds to {2} (real Oracle text: "can't reduce... to less than
    one mana", so the floor is 1, never actually reached here since 4-2=2 > 1)."""
    base = 4
    if any(p.name == "Training Grounds" for p in state.nonland_perms):
        return max(1, base - TRAINING_GROUNDS_ACTIVATION_DISCOUNT)
    return base


def t1_metrics(state, cards, m1):
    """Turn-1 trajectory metrics (SOLO-003 section 3)."""
    battlefield_t1 = {p.name for p in state.nonland_perms if p.entered_turn == 1}
    cast_t1 = {n for (t, n, c) in state.cast_log if t == 1}
    out = {}
    for name in sorted(ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE):
        out[f"t1_engine_{name}"] = name in battlefield_t1
    out["t1_any_tier_a_engine"] = any(out[f"t1_engine_{n}"] for n in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE)
    accel_used_t1 = any(n in ACCELERATION for n in cast_t1)
    out["t1_accelerated_two_drop"] = accel_used_t1 and any(
        parse_cost(cards[n]["mana_cost"])[0] + len(parse_cost(cards[n]["mana_cost"])[1]) == 2
        for n in cast_t1 if n not in ACCELERATION and n not in COMMANDERS
    )
    out["t1_mana_creature"] = any(
        n in cast_t1 and MANA_SOURCES.get(n, {}).get("creature") for n in cast_t1
    )
    out["t1_persistent_rock"] = any(
        n in cast_t1 and n in ACCELERATION and not MANA_SOURCES.get(n, {}).get("creature")
        and not MANA_SOURCES.get(n, {}).get("one_shot") and n != "Elvish Spirit Guide"
        for n in cast_t1
    )
    persistent_mana_perms_t1 = [
        p for p in state.nonland_perms
        if p.entered_turn == 1 and p.name in MANA_SOURCES and not MANA_SOURCES[p.name].get("one_shot")
    ]
    out["t1_multiple_persistent_mana_sources"] = len(persistent_mana_perms_t1) >= 2
    out["t1_burst_mana_used"] = any(t == 1 for (t, n) in state.temp_mana_used_log)
    out["t1_acceleration_retaining_resources"] = accel_used_t1 and m1["cards_in_hand"] >= 4
    out["t1_engine_deployed"] = m1["any_engine_active"]
    out["t1_live_interaction"] = m1["has_live_interaction"]
    compound_flags = [out["t1_engine_deployed"], accel_used_t1 or bool(persistent_mana_perms_t1), out["t1_live_interaction"]]
    out["t1_compound_development"] = sum(1 for f in compound_flags if f) >= 2
    return out


def t2_quality_metrics(state, cards, m2):
    battlefield_names = {p.name for p in state.nonland_perms}
    tier_a_online = any(n in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE for n in battlefield_names)
    tier_b_online_supported = any(
        n in ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE and n in battlefield_names
        and _tier_b_supported(n, state, cards)
        for n in ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE
    )
    return {
        "t2_primary_engine_online": tier_a_online,
        "t2_infrastructure_online_supported": tier_b_online_supported,
        "t2_development_plus_interaction": (
            (m2["mana_2plus"] or tier_a_online or tier_b_online_supported) and m2["has_live_interaction"]
        ),
    }


def t3_strong_state_metrics(state, cards, m3):
    """Per the SOLO-003 conceptual correction: Tymna castable/supported/on-battlefield must NOT
    inflate any generic "strong state" flag - it has its own dedicated conditional-productivity
    tiers (tymna_conditional_productivity below) precisely so a deployed-but-unsupported Tymna
    can never masquerade as a genuine card-advantage/compounding state here."""
    battlefield_names = {p.name for p in state.nonland_perms}
    tier_a_online = any(n in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE for n in battlefield_names)
    tier_c_supported_online = any(
        n in battlefield_names and _tier_c_supported(n, state, cards)
        for n in ENGINE_TIER_C_CONDITIONAL_VALUE if n != "Tymna the Weaver"
    )
    strong_card_advantage = tier_a_online or tier_c_supported_online
    land_count = len(state.lands)
    strong_mana_state = (m3["total_mana"] >= land_count + 2) or (m3["cradle_output_if_deployed"] >= 3)
    strong_conversion_state = m3["tutor_castable"] and bool(
        {"engine", "combo_piece"} & set(m3["tutor_targets_accessible"])
    )
    strong_interaction_state = m3["has_live_interaction"] and (m3["any_engine_active"] or m3["mana_2plus"])
    strong_flags = [strong_card_advantage, strong_mana_state, strong_conversion_state, strong_interaction_state]
    strong_optionality = sum(1 for f in strong_flags if f) >= 2
    credible_win_pressure = m3["deterministic_win_available"] or m3["one_action_from_verified_win"]
    return {
        "t3_strong_card_advantage_state": strong_card_advantage,
        "t3_strong_mana_state": strong_mana_state,
        "t3_strong_conversion_state": strong_conversion_state,
        "t3_strong_interaction_state": strong_interaction_state,
        "t3_strong_optionality_state": strong_optionality,
        "t3_credible_win_pressure": credible_win_pressure,
        "t3_any_strong_state": any(strong_flags) or credible_win_pressure,
        "t3_stalled": not (any(strong_flags) or credible_win_pressure) and m3["total_mana"] < 3,
    }


def compounding_state_metrics(state, cards, m3):
    """Same Tymna exclusion as t3_strong_state_metrics - see that function's docstring."""
    battlefield_names = {p.name for p in state.nonland_perms}
    card_engine = any(n in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE for n in battlefield_names) or any(
        n in ENGINE_TIER_C_CONDITIONAL_VALUE and n in battlefield_names and _tier_c_supported(n, state, cards)
        for n in ENGINE_TIER_C_CONDITIONAL_VALUE if n != "Tymna the Weaver"
    )
    mana_engine = any(
        n in ENGINE_TIER_D_MANA_DEVELOPMENT and n in battlefield_names for n in ENGINE_TIER_D_MANA_DEVELOPMENT
    ) or (CRADLE in [l.name for l in state.lands] and state.creature_count() >= 2)
    tutor_live = m3["tutor_castable"]
    interaction_live = m3["has_live_interaction"]
    cradle_creature_infra = CRADLE in [l.name for l in state.lands] and state.creature_count() >= 2
    survival_supported = "Survival of the Fittest" in battlefield_names and _tier_b_supported("Survival of the Fittest", state, cards)
    pod_supported = "Birthing Pod" in battlefield_names and m3["birthing_pod"]["usable_now"]
    win_conversion = m3["deterministic_win_available"] or m3["one_action_from_verified_win"]
    multi_engine = m3["two_plus_engines_active"]
    return {
        "card_engine_plus_mana_engine": card_engine and mana_engine,
        "card_engine_plus_interaction": card_engine and interaction_live,
        "card_engine_plus_tutor": card_engine and tutor_live,
        "mana_engine_plus_tutor": mana_engine and tutor_live,
        "cradle_plus_creature_infrastructure": cradle_creature_infra,
        "survival_supported": survival_supported,
        "pod_supported": pod_supported,
        "tutor_plus_resources_to_deploy": tutor_live and m3["total_mana"] >= 2,
        "engine_plus_win_conversion": card_engine and win_conversion,
        "multi_engine_plus_interaction": multi_engine and interaction_live,
    }


def tymna_conditional_productivity(state, cards, cast_turn):
    """Section 9: Tymna is a conditional CONVERSION metric, not a success headline."""
    on_bf = any(p.name == "Tymna the Weaver" for p in state.nonland_perms)
    if not on_bf:
        return {"tymna_deployed": False, "tymna_tier": None}
    attackers = state.creature_count()
    if attackers >= 3:
        tier = "tymna_high"
    elif attackers >= 2:
        tier = "tymna_medium"
    elif attackers >= 1:
        tier = "tymna_low"
    else:
        tier = "tymna_low"  # deployed with no attackers at all - essentially inert this turn
    return {
        "tymna_deployed": True, "tymna_cast_turn": cast_turn, "tymna_creatures_present": attackers,
        "tymna_tier": tier,
    }


def thrasios_productivity(state, cards, m3):
    """Section 10: measure PRODUCTIVITY, not presence."""
    on_bf = any(p.name == "Thrasios, Triton Hero" for p in state.nonland_perms)
    act_cost = thrasios_activation_cost_generic(state)
    activation_now = on_bf and is_currently_castable(state, act_cost, [])
    training_grounds_active = any(p.name == "Training Grounds" for p in state.nonland_perms)
    kinnan_active = any(p.name == "Kinnan, Bonder Prodigy" for p in state.nonland_perms)
    cradle_active = CRADLE in [l.name for l in state.lands]
    return {
        "thrasios_castable": m3["Thrasios, Triton Hero_castable"],
        "thrasios_on_battlefield": on_bf,
        "thrasios_activation_cost_generic": act_cost if on_bf else None,
        "thrasios_activation_now": activation_now,
        "thrasios_training_grounds_discount_active": on_bf and training_grounds_active,
        "thrasios_kinnan_present": on_bf and kinnan_active,
        "thrasios_cradle_present": on_bf and cradle_active,
        "thrasios_productive": activation_now,  # productivity is defined by real activation capacity, not presence
    }


def classify_trajectory_failure(m1, m2, m3, state, cards):
    """Section 20: outcome failure (what) vs. causal diagnosis (why), both multi-label."""
    outcome_tags = []
    t3strong = t3_strong_state_metrics(state, cards, m3)
    if not m1["any_engine_active"] and not m1["mana_2plus"] and m1["total_mana"] < 2 and m2["total_mana"] < 2:
        outcome_tags.append("no_proactive_development")
    elif not t3strong["t3_any_strong_state"]:
        outcome_tags.append("development_but_no_compounding_value")
    if m3["any_engine_active"] and not t3strong["t3_strong_card_advantage_state"]:
        outcome_tags.append("stranded_or_unsupported_engine")
    if m3["tutor_available"] and not m3["tutor_castable"]:
        outcome_tags.append("stranded_tutor")
    interaction_cast_by_t3 = any(c == "interaction" for (t, n, c) in state.cast_log if t <= 3)
    if (m1["has_live_interaction"] or m2["has_live_interaction"]) and not m3["has_live_interaction"] \
            and not interaction_cast_by_t3:
        outcome_tags.append("stranded_interaction")
    if not m3["all_wubg"] and m3["total_mana"] >= 3:
        outcome_tags.append("color_failure")
    if m3["temporary_resources_consumed"] > 0 and not t3strong["t3_any_strong_state"]:
        outcome_tags.append("resource_destructive_acceleration_no_payoff")
    if len(state.lands) >= 4 and m3["cards_in_hand"] <= 2:
        outcome_tags.append("flooded_action_light")
    if m3["total_mana"] < 2:
        outcome_tags.append("insufficient_mana")
    if not outcome_tags:
        outcome_tags.append("functional")

    causal_tags = []
    if len(state.lands) < 2:
        causal_tags.append("no_second_land")
    if m3["total_mana"] < 2:
        causal_tags.append("insufficient_persistent_mana")
    return outcome_tags, causal_tags
