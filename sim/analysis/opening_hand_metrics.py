"""SIM-001 SOLO-002 — per-hand metric extraction after development, matching
the requested PRIMARY OUTPUT TABLE and CRITICAL SECONDARY OUTPUT (failure
modes) exactly. Operates on a HandState snapshot at the end of a turn.
"""
from opening_hand_model import (
    COLORS, parse_cost, CRADLE, MANA_SOURCES, ACCELERATION, TUTORS,
    INTERACTION_CASTABLE, ENGINES, PREMIUM_ONE_DROP_ENGINES, COMMANDERS,
    MOX_FAMILY, TUTOR_TARGETS,
    load_deterministic_combos,
)


def _creature_count(state, cards):
    return sum(
        1 for p in state.nonland_perms
        if p.name in COMMANDERS or "Creature" in cards[p.name]["type"]
    )


def _castable_now(state, cards, name):
    if name not in state.hand:
        return False
    gen, pips, x = parse_cost(cards[name]["mana_cost"])
    if x > 0:
        return False
    from opening_hand_policy import _try_pay
    return _try_pay(state, gen, pips, set()) is not None


def _affordable_in_isolation(cost_str, turn_start_mana, turn_start_colors):
    """Would this cost have been payable using the turn's FULL mana pool, independent of what
    the greedy policy actually spent it on this turn? See HandState.turn_start_mana docstring."""
    gen, pips, x = parse_cost(cost_str)
    if x > 0:
        return False
    for pip in pips:
        need = pip if isinstance(pip, frozenset) else {pip}
        if not (need & turn_start_colors):
            return False
    return (gen + len(pips)) <= turn_start_mana


def snapshot_metrics(state, cards, combos):
    m = {}
    total_mana = state.total_mana_value()
    colors = state.colors_available()
    m["total_mana"] = total_mana
    m["colors_available"] = sorted(colors)
    m["mana_2plus"] = total_mana >= 2
    m["mana_3plus"] = total_mana >= 3
    m["mana_4plus"] = total_mana >= 4
    m["all_wubg"] = set(COLORS) <= colors

    battlefield_names = {p.name for p in state.nonland_perms}
    # engines ON BATTLEFIELD and (for creatures) not summoning sick this turn - "active" for our
    # purposes means: an artifact/enchantment engine is active immediately; a creature engine
    # (e.g. Deathrite Shaman as a value piece) is "deployed" even if summoning sick, since most
    # deck engines here are noncreature (documented simplification: creature-engine "activity" is
    # approximated as deployed=active, since none of this deck's ENGINES list are creatures with a
    # sickness-gated activated ability except Deathrite Shaman, which this model doesn't give mana
    # from anyway).
    active_engines = [n for n in battlefield_names if n in ENGINES]
    m["engines_active"] = sorted(active_engines)
    m["engine_count"] = len(active_engines)
    m["any_engine_active"] = len(active_engines) > 0
    m["premium_engine_active"] = any(n in PREMIUM_ONE_DROP_ENGINES for n in active_engines)
    m["two_plus_engines_active"] = len(active_engines) >= 2

    # Cards relevant "this turn" = still in hand OR already cast this turn by the greedy policy -
    # affordability is checked against the turn's FULL mana pool (turn_start_mana/colors), not
    # post-hoc remaining hand, because the greedy policy may have already spent the mana that
    # would have paid for a tutor/interaction card, removing it from hand (see
    # HandState.turn_start_mana's docstring for the full explanation of why this matters).
    turn_hand = set(state.hand) | {n for (t, n, c) in state.cast_log if t == state.turn}
    interaction_candidates = [n for n in turn_hand if n in INTERACTION_CASTABLE]
    affordable_interaction = [
        n for n in interaction_candidates
        if _affordable_in_isolation(cards[n]["mana_cost"], state.turn_start_mana, state.turn_start_colors)
    ]
    m["live_interaction"] = sorted(affordable_interaction)
    m["has_live_interaction"] = len(affordable_interaction) > 0
    # Approximation (documented): "engine deployed this game" AND "an interaction card was
    # affordable from this turn's full mana pool in isolation" - not a proof both are
    # simultaneously payable from one shared pool (that needs full joint-payment search, out of
    # scope for this pass). Directionally correct, not exact.
    m["engine_plus_interaction"] = m["any_engine_active"] and m["has_live_interaction"]
    m["development_plus_interaction"] = (total_mana >= 2 or m["any_engine_active"]) and m["has_live_interaction"]

    tutor_candidates = [n for n in turn_hand if n in TUTORS]
    tutor_affordable = [
        n for n in tutor_candidates
        if _affordable_in_isolation(cards[n]["mana_cost"], state.turn_start_mana, state.turn_start_colors)
    ]
    m["tutor_in_hand"] = sorted([n for n in state.hand if n in TUTORS])
    m["tutor_available"] = len(m["tutor_in_hand"]) > 0
    m["tutor_castable"] = len(tutor_affordable) > 0
    # What a currently-castable tutor can presently access, not "every possible card" (category 8:
    # "Do not count a tutor as equivalent to every possible card if mana, timing, card type, or
    # board requirements prevent that target" - target-class breadth is per-card, see
    # TUTOR_TARGETS; board/mana gating on the FETCHED card itself, e.g. "can it be cast once
    # found," is out of scope for this pass).
    tutor_target_tags = set()
    for n in tutor_affordable:
        tutor_target_tags |= TUTOR_TARGETS.get(n, frozenset())
    m["tutor_targets_accessible"] = sorted(tutor_target_tags)

    for cname, spec in COMMANDERS.items():
        gen, pips, x = parse_cost(spec["cost"])
        on_bf = cname in battlefield_names
        # Commanders live in the command zone, not the library/hand - castable whenever still in
        # the command zone (not yet cast) and affordable from this turn's full mana pool. Once
        # cast, "castable" is reported False (it's on the battlefield, not awaiting a cast).
        castable = (cname in state.command_zone) and _affordable_in_isolation(spec["cost"], state.turn_start_mana, state.turn_start_colors)
        m[f"{cname}_castable"] = castable
        m[f"{cname}_on_battlefield"] = on_bf
        if cname == "Tymna the Weaver":
            m["tymna_creatures_for_attack"] = _creature_count(state, cards)
            m["tymna_supported"] = on_bf and _creature_count(state, cards) >= 1
        if cname == "Thrasios, Triton Hero":
            remaining_after = max(0, total_mana - (gen + len(pips))) if castable else total_mana
            m["thrasios_mana_after_cast"] = remaining_after
            m["thrasios_activatable_soon"] = remaining_after >= 4 or on_bf

    cradle_on_bf = CRADLE in state.lands
    m["cradle_on_battlefield"] = cradle_on_bf
    m["cradle_in_hand"] = CRADLE in state.hand
    creature_ct = _creature_count(state, cards)
    m["cradle_output_if_deployed"] = creature_ct if cradle_on_bf else 0
    m["cradle_3plus"] = cradle_on_bf and creature_ct >= 3

    def _functional(name, sac_or_discard_available, activation_mana):
        in_hand = name in state.hand
        castable = in_hand and _castable_now(state, cards, name)
        on_bf = name in battlefield_names
        return {
            "in_hand": in_hand, "castable": castable, "on_battlefield": on_bf,
            "usable_now": on_bf and sac_or_discard_available and activation_mana,
        }
    pod_body_available = creature_ct >= 1
    m["birthing_pod"] = _functional("Birthing Pod", pod_body_available, total_mana >= 2)
    survival_discard_available = any(
        "Creature" in cards[c]["type"] for c in state.hand if c != "Survival of the Fittest"
    )
    m["survival_of_the_fittest"] = _functional("Survival of the Fittest", survival_discard_available, total_mana >= 1)

    # Deliberately NOT "natural co-location" (the user's spec explicitly warns against measuring
    # only whether the named cards were drawn together) - a card sitting in the graveyard or exile
    # isn't castable, and a card sitting in hand that's unaffordable this turn isn't a live win
    # either. "zero_step" requires every combo piece to be either already deployed on the
    # battlefield, or in hand and individually affordable from this turn's full mana pool
    # (approximation, documented: doesn't prove joint payability of multiple hand pieces from one
    # shared pool - same tradeoff as engine_plus_interaction above). Pieces not seen at all need a
    # tutor/draw; pieces seen in hand but presently uncastable need another turn's mana, not a
    # tutor - both count as "missing" for the one/two-actions-away tiers, but are tracked
    # separately so tutor-gated cases aren't conflated with mana-gated ones.
    has_tutor = bool(tutor_affordable or tutor_candidates)
    combo_status = {}
    for combo in combos:
        deployed = [c for c in combo["cards"] if c in battlefield_names]
        in_hand = [c for c in combo["cards"] if c in state.hand and c not in battlefield_names]
        unseen = [c for c in combo["cards"] if c not in battlefield_names and c not in state.hand]
        hand_stuck = [
            c for c in in_hand
            if not _affordable_in_isolation(cards[c]["mana_cost"], state.turn_start_mana, state.turn_start_colors)
        ]
        missing = len(unseen) + len(hand_stuck)
        if missing == 0:
            status = "zero_step"
        elif missing == 1 and unseen and has_tutor:
            status = "one_action_away"
        elif missing == 1:
            status = "one_action_away_no_tutor"
        elif missing == 2 and len(unseen) >= 1 and has_tutor:
            status = "two_actions_away"
        else:
            status = "not_close"
        combo_status[combo["id"]] = status
    m["combo_status"] = combo_status
    m["deterministic_win_available"] = any(v == "zero_step" for v in combo_status.values())
    m["one_action_from_verified_win"] = any(v.startswith("one_action_away") for v in combo_status.values())
    m["two_actions_from_verified_win"] = any(v == "two_actions_away" for v in combo_status.values())

    m["cards_in_hand"] = len(state.hand)
    persistent = [p.name for p in state.nonland_perms if not MANA_SOURCES.get(p.name, {}).get("one_shot")]
    m["persistent_nonland_permanents"] = len(persistent)
    temp_used_this_snapshot = len(state.temp_mana_used_log)
    m["temporary_resources_consumed"] = temp_used_this_snapshot

    return m


def classify_failure_reasons_detailed(m_t3, state, cards):
    """Multi-label granular failure diagnostics (category 14's full requested taxonomy), unlike
    classify_failure_mode's single dominant reason (kept separately for the primary failure_table
    so that table's schema/history stays stable). A hand can carry more than one tag; percentages
    in the aggregate report sum to more than 100% by design."""
    tags = []
    total_mana = m_t3["total_mana"]
    if total_mana < 2:
        tags.append("insufficient_persistent_mana")
    if not m_t3["all_wubg"] and total_mana >= 3:
        missing = set(COLORS) - set(m_t3["colors_available"])
        tags.append(f"color_failure_missing_{''.join(sorted(missing))}")
    battlefield_names = {p.name for p in state.nonland_perms}
    if len(state.lands) < 2:
        tags.append("no_second_land")
        if any(n in MOX_FAMILY for n in battlefield_names):
            tags.append("mox_dependency")
    cradle_present = CRADLE in state.hand or CRADLE in state.lands
    if cradle_present and _creature_count(state, cards) == 0:
        tags.append("no_creature_for_cradle")
    if "Chrome Mox" in state.hand and not any(
        h != "Chrome Mox" and "Land" not in cards[h]["type"] for h in state.hand
    ):
        tags.append("no_disposable_for_chrome_mox")
    if "Mox Diamond" in state.hand and not any(
        h != "Mox Diamond" and "Land" in cards[h]["type"] for h in state.hand
    ):
        tags.append("no_land_for_mox_diamond")
    if m_t3["has_live_interaction"] and not m_t3["any_engine_active"]:
        tags.append("interaction_only_no_engine")
    if m_t3["tutor_available"] and not m_t3["tutor_castable"]:
        tags.append("tutor_but_no_viable_sequencing")
    if not m_t3["any_engine_active"] and not m_t3["tutor_available"] and not m_t3["has_live_interaction"]:
        tags.append("no_meaningful_t1_t2_development")
    return tags


def tag_archetype(m1, m2, m3, failure_mode_t3):
    """Rule-based opening-hand archetype tags (category 15), evaluated on structural T1-T3
    behavior. Multi-label - a hand can match more than one archetype. Deliberately NOT a
    hard-coded exhaustive taxonomy claim: this is a starting rule set, not a data-derived
    clustering (that would need a real clustering pass over the raw per-hand feature vectors,
    scoped down for this run - see write-up for disclosure)."""
    tags = []
    if m3["any_engine_active"]:
        tags.append("engine_hand")
    if m1["tutor_castable"] or m2["tutor_castable"]:
        tags.append("tutor_hand")
    if len(m3["live_interaction"]) >= 2 or (m1["has_live_interaction"] and m2["has_live_interaction"]):
        tags.append("interaction_heavy_hand")
    if m3.get("tymna_creatures_for_attack", 0) >= 3 and not m1["any_engine_active"]:
        tags.append("creature_development_hand")
    if m3["temporary_resources_consumed"] >= 2:
        tags.append("burst_mana_hand")
    if m2.get("tymna_supported") or m2.get("thrasios_activatable_soon"):
        tags.append("commander_hand")
    if m3["deterministic_win_available"] or m3["one_action_from_verified_win"]:
        tags.append("combo_hand")
    if failure_mode_t3 is not None:
        tags.append("nonfunctional_hand")
    if not tags:
        tags.append("unclassified_hand")
    return tags


def classify_failure_mode(m_t3, state, cards):
    """Best-effort single dominant reason a hand failed to reach meaningful T3 development
    ('meaningful' = mana_2plus AND (any_engine_active OR tutor_castable OR has_live_interaction))."""
    meaningful = m_t3["mana_2plus"] and (m_t3["any_engine_active"] or m_t3["tutor_castable"] or m_t3["has_live_interaction"])
    if meaningful:
        return None
    if m_t3["total_mana"] < 2:
        return "insufficient_persistent_mana"
    if not m_t3["all_wubg"] and m_t3["total_mana"] >= 3:
        missing = set(COLORS) - set(m_t3["colors_available"])
        return f"color_failure_missing_{''.join(sorted(missing))}"
    if m_t3["has_live_interaction"] and not m_t3["any_engine_active"]:
        return "interaction_only_no_engine"
    if not m_t3["any_engine_active"] and not m_t3["tutor_available"]:
        return "no_meaningful_t1_t2_development"
    if m_t3["tutor_available"] and not m_t3["tutor_castable"]:
        return "tutor_but_no_viable_sequencing"
    return "no_meaningful_t1_t2_development"
