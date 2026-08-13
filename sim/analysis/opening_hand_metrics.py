"""SIM-001 SOLO-002R — per-hand metric extraction after development, matching the requested
PRIMARY OUTPUT TABLE and CRITICAL SECONDARY OUTPUT (failure modes).

CORRECTNESS-REPAIR NOTE: this module previously checked "is X also affordable" via
`_affordable_in_isolation()`, which compared a cost against `turn_start_mana`/`turn_start_colors`
(the turn's FULL starting capacity) regardless of what the greedy policy had already spent -
i.e. an approximation that could claim two costs were both affordable even when they'd need the
same single source. Two different, correctly-scoped replacements are used now:

- `_individually_affordable_from_turn_capacity()` - the renamed, EXPLICITLY-LABELED survivor of
  that old check. Retained deliberately (per the correctness-repair instruction: "A metric may
  retain an explicitly named individually_affordable diagnostic, but it must not be presented as
  simultaneous availability") for single-card "was this affordable at all this turn, judged
  against the turn's full capacity" questions - e.g. "Tymna castable" in the sense of the
  original spec's "legally castable this turn," independent of whether the greedy policy
  actually chose to cast it (something else may have simply outranked it in priority).
- `is_currently_castable()` (from opening_hand_policy) - a REAL read-only payment search against
  whatever is CURRENTLY still untapped, used for every "retained/remaining/on-top-of" question
  (live interaction after an engine, an activation after casting a commander) where the honest
  answer depends on what was actually spent already.
- `can_pay_jointly()` (from opening_hand_policy) - a real multi-cost dry-run+rollback, used
  wherever MULTIPLE not-yet-committed costs must be shown simultaneously payable (combo pieces
  still sitting in hand, a protected deterministic win) - never approximated by checking each
  cost independently against the same untouched pool.
"""
from opening_hand_model import (
    COLORS, parse_cost, CRADLE, MANA_SOURCES, ACCELERATION, TUTORS,
    INTERACTION_CASTABLE, ENGINES, PREMIUM_ONE_DROP_ENGINES, COMMANDERS,
    MOX_FAMILY, TUTOR_TARGETS,
    load_deterministic_combos,
)
from opening_hand_policy import is_currently_castable, can_pay_jointly, _try_pay, _commit_payment, _rollback_payment
from interaction_model import interaction_is_live

THRASIOS_ACTIVATION_COST = "{4}"
POD_ACTIVATION_COST = "{1}{G/P}"
SURVIVAL_ACTIVATION_COST = "{G}"


def _creature_count(state, cards):
    return state.creature_count()


def _individually_affordable_from_turn_capacity(cost_str, turn_start_mana, turn_start_colors):
    """EXPLICIT diagnostic (not a simultaneity claim): would this cost have been payable using
    the turn's FULL mana capacity in isolation, independent of what the greedy policy actually
    spent it on. See module docstring."""
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
    # SOLO-003R root-cause fix: `total_mana`/`colors_available` here now report this turn's
    # starting CAPACITY (state.turn_start_mana/turn_start_colors, captured inside develop_turn()
    # right after the land drop, before anything is cast) - not whatever happens to be left over
    # after the greedy policy already spent mana this turn. Every existing consumer of these two
    # fields (in this module and in trajectory_metrics.py) wants "how much mana did this hand
    # have to work with this turn," not "how much is unspent right now" - conflating the two was
    # the root cause of the reviewer-flagged bug where a hand that spent its whole turn casting
    # real spells could still be mislabeled "insufficient_mana" for finishing at 0-1 untapped.
    # The old leftover/residual quantity is preserved separately below, under explicit names, for
    # any diagnostic that specifically wants post-cast leftover rather than starting capacity.
    total_mana = state.turn_start_mana
    colors = state.turn_start_colors
    m["total_mana"] = total_mana
    m["colors_available"] = sorted(colors)
    m["mana_remaining_unused"] = state.total_mana_value()
    m["colors_remaining_unused"] = sorted(state.colors_available())
    m["mana_2plus"] = total_mana >= 2
    m["mana_3plus"] = total_mana >= 3
    m["mana_4plus"] = total_mana >= 4
    m["all_wubg"] = set(COLORS) <= colors

    battlefield_names = {p.name for p in state.nonland_perms}
    active_engines = [n for n in battlefield_names if n in ENGINES]
    m["engines_active"] = sorted(active_engines)
    m["engine_count"] = len(active_engines)
    m["any_engine_active"] = len(active_engines) > 0
    m["premium_engine_active"] = any(n in PREMIUM_ONE_DROP_ENGINES for n in active_engines)
    m["two_plus_engines_active"] = len(active_engines) >= 2

    # "Retained interaction" is inherently a residual question - given whatever the policy
    # ACTUALLY did this turn, is there still enough real mana AND/OR a real alternate cost
    # (pitch/sacrifice/commander-gated-free) left to also cast an interaction card? SOLO-003:
    # uses interaction_is_live() (interaction_model.py), the real alternate-cost model, not just
    # a plain mana-cost check - Force of Will/Fierce Guardianship/etc. are only premium BECAUSE
    # of their alternate costs, so checking printed mana cost alone understated this metric.
    turn_hand = set(state.hand) | {n for (t, n, c) in state.cast_log if t == state.turn}
    interaction_candidates = sorted(n for n in turn_hand if n in INTERACTION_CASTABLE)
    live_interaction = [n for n in interaction_candidates if interaction_is_live(n, state, cards)]
    m["live_interaction"] = live_interaction
    m["has_live_interaction"] = len(live_interaction) > 0
    m["free_or_alt_cost_interaction_live"] = any(
        n for n in live_interaction
        if not is_currently_castable(state, *parse_cost(cards[n]["mana_cost"])[:2])
    )
    # Now a TRUE joint statement, not an approximation: any_engine_active reflects a real sunk
    # deployment (mana already spent for real), and has_live_interaction is checked against what
    # is genuinely still untapped after that - their conjunction is a correct joint fact.
    m["engine_plus_interaction"] = m["any_engine_active"] and m["has_live_interaction"]
    m["development_plus_interaction"] = (total_mana >= 2 or m["any_engine_active"]) and m["has_live_interaction"]

    tutor_candidates_in_hand = sorted(n for n in state.hand if n in TUTORS)
    m["tutor_in_hand"] = tutor_candidates_in_hand
    m["tutor_available"] = len(tutor_candidates_in_hand) > 0
    tutor_live = []
    for n in (set(tutor_candidates_in_hand) | {n for (t, n, c) in state.cast_log if t == state.turn and n in TUTORS}):
        gen, pips, x = parse_cost(cards[n]["mana_cost"])
        if x == 0 and is_currently_castable(state, gen, pips):
            tutor_live.append(n)
    m["tutor_castable"] = len(tutor_live) > 0  # live/retained: "ALSO affordable on top of everything else"
    tutor_target_tags = set()
    for n in tutor_live:
        tutor_target_tags |= TUTOR_TARGETS.get(n, frozenset())
    # NOTE: reachable target CLASS only - not a claim that the fetched card could ALSO be
    # deployed this same turn (that would need a tutor-then-cast joint search, out of scope here;
    # see the correctness-repair write-up's scope disclosure).
    m["tutor_targets_accessible"] = sorted(tutor_target_tags)

    for cname, spec in COMMANDERS.items():
        gen, pips, x = parse_cost(spec["cost"])
        on_bf = cname in battlefield_names
        still_pending = cname in state.command_zone
        # "Castable" = the original spec's "legally castable this turn" - a CAPACITY question
        # (was the turn's mana, in total, enough), independent of whether the greedy policy's
        # priority order chose to actually cast it. Deliberately the explicit
        # individually_affordable diagnostic, not a simultaneity claim (see module docstring).
        castable_capacity = still_pending and _individually_affordable_from_turn_capacity(
            spec["cost"], state.turn_start_mana, state.turn_start_colors
        )
        m[f"{cname}_castable"] = castable_capacity
        m[f"{cname}_on_battlefield"] = on_bf
        if cname == "Tymna the Weaver":
            # SOLO-003R: "for attack" must mean attack-ELIGIBLE (excludes summoning-sick
            # creatures, including Tymna herself if just cast this same turn) - creature_count()
            # deliberately includes sick creatures for its OTHER uses (Cradle output, Pod/
            # Survival fodder) where sickness doesn't apply; attack eligibility is exact
            # rules-state and must not reuse that broader count.
            m["tymna_creatures_for_attack"] = state.attack_eligible_creature_count()
            m["tymna_supported"] = on_bf and state.attack_eligible_creature_count() >= 1
        if cname == "Thrasios, Triton Hero":
            # "commander + activation uses shared mana correctly" (regression test #10): a REAL
            # live check, since this asks about capacity actually remaining after a real cast.
            act_gen, act_pips, _ = parse_cost(THRASIOS_ACTIVATION_COST)
            m["thrasios_activation_now"] = on_bf and is_currently_castable(state, act_gen, act_pips)
            # secondary, explicitly-approximate forward-looking projection (not primary) - kept
            # only as a coarse "does next turn look plausible" diagnostic.
            m["thrasios_activatable_soon_approx"] = m["thrasios_activation_now"] or (on_bf and total_mana >= 2)

    cradle_on_bf = CRADLE in [l.name for l in state.lands]
    m["cradle_on_battlefield"] = cradle_on_bf
    m["cradle_in_hand"] = CRADLE in state.hand
    creature_ct = state.creature_count()
    m["cradle_output_if_deployed"] = creature_ct if cradle_on_bf else 0
    m["cradle_2plus"] = cradle_on_bf and creature_ct >= 2
    m["cradle_3plus"] = cradle_on_bf and creature_ct >= 3
    m["cradle_5plus"] = cradle_on_bf and creature_ct >= 5

    def _functional(name, activation_cost_str, sac_body_available):
        in_hand = name in state.hand
        castable_capacity = in_hand and _individually_affordable_from_turn_capacity(
            cards[name]["mana_cost"], state.turn_start_mana, state.turn_start_colors
        )
        on_bf = name in battlefield_names
        act_gen, act_pips, _ = parse_cost(activation_cost_str)
        activation_mana_now = on_bf and is_currently_castable(state, act_gen, act_pips)
        return {
            "in_hand": in_hand, "castable": castable_capacity, "on_battlefield": on_bf,
            "activation_mana_available": activation_mana_now,
            "usable_now": on_bf and sac_body_available and activation_mana_now,
        }
    pod_body_available = creature_ct >= 1
    m["birthing_pod"] = _functional("Birthing Pod", POD_ACTIVATION_COST, pod_body_available)
    survival_discard_available = any(
        "Creature" in cards[c]["type"] for c in state.hand if c != "Survival of the Fittest"
    )
    m["survival_of_the_fittest"] = _functional("Survival of the Fittest", SURVIVAL_ACTIVATION_COST, survival_discard_available)

    # Combo accessibility - a REAL joint check for hand-still-uncast pieces (not "natural
    # co-location," and not independent per-piece isolation, which can silently double-count a
    # single shared source). Pieces already on the battlefield are sunk (need no further mana);
    # pieces still in hand are tentatively committed together via can_pay_jointly's underlying
    # search-then-rollback, so a "zero_step" claim reflects a real simultaneous allocation.
    battlefield_and_lands = battlefield_names | {l.name for l in state.lands}
    # SOLO-003R fix: has_tutor_live previously ORed in mere hand-PRESENCE (tutor_candidates_in_hand)
    # alongside real castability (tutor_live) - defeating the exact live-vs-present distinction
    # this project has enforced everywhere else. A tutor only counts here if it is actually
    # castable right now. Separately, a tutor only counts as a real path to a MISSING combo piece
    # if its own target-class reach actually includes "combo_piece" (TUTOR_TARGETS) - a live
    # land-only tutor (e.g. Sowing Mycospawn) cannot fetch a creature combo piece, and must not be
    # treated as if it could.
    has_tutor_live = len(tutor_live) > 0
    tutor_reaches_combo_piece = any("combo_piece" in TUTOR_TARGETS.get(n, frozenset()) for n in tutor_live)
    combo_status = {}
    combo_protected = {}
    for combo in combos:
        in_hand = [c for c in combo["cards"] if c in state.hand and c not in battlefield_and_lands]
        unseen = [c for c in combo["cards"] if c not in battlefield_and_lands and c not in state.hand]
        has_x_piece = False
        payable_costs = []
        for c in in_hand:
            gen, pips, x = parse_cost(cards[c]["mana_cost"])
            if x > 0:
                has_x_piece = True  # X-cost pieces not modeled by this greedy dev policy at all
            else:
                payable_costs.append((gen, pips))
        if has_x_piece:
            jointly_payable = False
        elif payable_costs:
            jointly_payable = can_pay_jointly(state, payable_costs)
        else:
            jointly_payable = True  # no in-hand pieces need casting (everything else is sunk/deployed)
        # If the joint check fails we don't know exactly which piece(s) are the bottleneck (a
        # real diagnosis would need its own backtracking search) - conservatively treat ALL
        # in-hand pieces as "stuck" for the missing-count tiering below.
        hand_stuck = [] if jointly_payable else list(in_hand)
        missing_unseen = len(unseen)
        missing_stuck = len(hand_stuck)
        missing = missing_unseen + missing_stuck
        # SOLO-003R fix: "one action away" previously conflated three very different situations
        # under one label (and one_action_from_verified_win counted ALL of them as "credible win
        # pressure"): a piece sitting in hand that just needs more mana next turn (a real,
        # execution-only-dependent-on-mana signal); a missing piece a LIVE, combo-reaching tutor
        # could fetch this turn (a real, concrete action); and a missing piece with no such tutor,
        # which requires topdecking the exact card naturally (a much weaker signal that must NOT
        # be reported as "credible win pressure").
        if missing == 0:
            status = "zero_step"
        elif missing == 1 and missing_stuck == 1:
            status = "one_mana_step_from_win"
        elif missing == 1 and missing_unseen == 1 and tutor_reaches_combo_piece:
            status = "one_tutor_step_from_win"
        elif missing == 1 and missing_unseen == 1:
            status = "one_draw_step_from_win"
        elif missing == 2 and missing_unseen >= 1 and tutor_reaches_combo_piece:
            status = "two_actions_away"
        else:
            status = "not_close"
        combo_status[combo["id"]] = status

        protected = False
        if status == "zero_step" and payable_costs:
            # "protected deterministic win states": while the combo pieces' mana is still
            # tentatively committed, check whether an interaction card is ALSO jointly payable -
            # a real joint check across combo assembly AND protection, not two separate isolated
            # checks.
            plan_list = []
            all_ok = True
            for gen, pips in payable_costs:
                plan = _try_pay(state, gen, pips)
                if plan is None:
                    all_ok = False
                    break
                _commit_payment(state, plan)
                plan_list.append(plan)
            if all_ok:
                for n in interaction_candidates:
                    gen, pips, x = parse_cost(cards[n]["mana_cost"])
                    if x == 0 and is_currently_castable(state, gen, pips):
                        protected = True
                        break
            _rollback_payment(state, plan_list)
        elif status == "zero_step" and not payable_costs:
            # every piece already deployed - protection just needs a normal live interaction check
            protected = m["has_live_interaction"]
        combo_protected[combo["id"]] = protected

    m["combo_status"] = combo_status
    m["combo_protected"] = combo_protected
    m["deterministic_win_available"] = any(v == "zero_step" for v in combo_status.values())
    m["deterministic_win_protected"] = any(combo_protected.get(k) for k, v in combo_status.items() if v == "zero_step")
    # SOLO-003R fix: these three are now reported SEPARATELY (never collapsed into one
    # "one action away" umbrella) precisely because they are different-strength signals - a
    # topdeck-dependent piece (one_draw_step) must never be presented as equivalent to a
    # tutor-backed or mana-backed one.
    m["one_mana_step_from_win"] = any(v == "one_mana_step_from_win" for v in combo_status.values())
    m["one_tutor_step_from_win"] = any(v == "one_tutor_step_from_win" for v in combo_status.values())
    m["one_draw_step_from_win"] = any(v == "one_draw_step_from_win" for v in combo_status.values())
    # "Credible win pressure" / one_action_from_verified_win must only include steps that don't
    # depend on topdecking the exact missing card - a mana-backed step (all pieces already seen,
    # just needs more mana) or a tutor-backed step (a live tutor that actually reaches combo
    # pieces) are real, executable-soon facts; a draw-dependent step is not.
    m["one_action_from_verified_win"] = m["one_mana_step_from_win"] or m["one_tutor_step_from_win"]
    m["two_actions_from_verified_win"] = any(v == "two_actions_away" for v in combo_status.values())

    m["cards_in_hand"] = len(state.hand)
    persistent = [p.name for p in state.nonland_perms if not MANA_SOURCES.get(p.name, {}).get("one_shot")]
    m["persistent_nonland_permanents"] = len(persistent)
    m["temporary_resources_consumed"] = len(state.temp_mana_used_log)

    # SOLO-003R reviewer concept #3, the only one of (capacity, utilization, shortfall) that is
    # actual evidence of a mana bottleneck: was a DESIRABLE action (a tutor, an engine of any
    # tier, or an interaction spell) unavailable specifically because legal mana generation was
    # insufficient - i.e. uncastable even against the turn's FULL starting capacity in isolation,
    # not merely because the greedy policy chose to spend that capacity on something else first.
    # X-cost cards are excluded (this policy doesn't model X-cost affordability at all, so their
    # exclusion from "desirable" here isn't a mana signal). Deliberately scoped to cards actually
    # IN HAND, not the command zone: both commanders sit in state.command_zone for essentially the
    # entire game until cast, each needing a different 2-3 color combination - treating either as
    # "desirable" unconditionally would make this fire on nearly every hand that hasn't assembled
    # all four commander colors yet, which is normal and not a mana bottleneck finding. A
    # commander's own capacity-affordability is already tracked precisely by its dedicated
    # `{name}_castable` field above; this diagnostic isn't meant to duplicate that.
    desirable_costs = []
    for n in set(state.hand):
        if n in TUTORS or n in ENGINES or n in INTERACTION_CASTABLE:
            desirable_costs.append(cards[n]["mana_cost"])
    mana_shortfall = False
    for cost in desirable_costs:
        _, _, x = parse_cost(cost)
        if x > 0:
            continue
        if not _individually_affordable_from_turn_capacity(cost, state.turn_start_mana, state.turn_start_colors):
            mana_shortfall = True
            break
    m["mana_shortfall"] = mana_shortfall

    return m


def classify_failure_mode(m_t3, state, cards):
    """Best-effort single dominant reason a hand failed to reach meaningful T3 development
    ('meaningful' = mana_2plus AND (any_engine_active OR tutor_castable OR has_live_interaction)).
    This composite is now explicitly a SECONDARY convenience metric, not the principal target -
    see the redesigned separate primary-outcome table in run_opening_hand_census.py."""
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


def classify_failure_reasons_detailed(m_t3, state, cards):
    """Multi-label granular failure diagnostics (category 14's full requested taxonomy)."""
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
    cradle_present = CRADLE in state.hand or CRADLE in [l.name for l in state.lands]
    if cradle_present and state.creature_count() == 0:
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
    """Rule-based opening-hand archetype tags (category 15) - a starting taxonomy, not a
    data-derived clustering (disclosed scope reduction, see write-up)."""
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
    if m2.get("tymna_supported") or m2.get("thrasios_activation_now"):
        tags.append("commander_hand")
    if m3["deterministic_win_available"] or m3["one_action_from_verified_win"]:
        tags.append("combo_hand")
    if failure_mode_t3 is not None:
        tags.append("nonfunctional_hand")
    if not tags:
        tags.append("unclassified_hand")
    return tags
