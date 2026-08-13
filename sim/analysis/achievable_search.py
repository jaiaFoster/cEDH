"""SIM-001 SOLO-002R Part B (rerun protocol) — bounded best-known-achievable search.

NOT a full game-tree search - that would require modeling held priority, opponent interaction,
and exhaustive alternate sequencing, all out of scope for this project's declared Level 1-2
model. Instead: runs a small, FIXED, documented set of alternative development lines per hand -
different turn-1 land-drop choices (the single highest-leverage early decision) crossed with a
few alternative priority orderings - and reports whether ANY explored line reaches each named
target state by the relevant turn. This is a genuine improvement over "one greedy line" (it can
find lines the default policy's fixed heuristics miss), but it is explicitly BOUNDED, not a
completeness proof: a target this search calls unreachable might still be reachable by some line
outside the small set explored here. Not included in the bounded set (disclosed scope
reduction): alternate turn-2/3 land choices, and alternate fetch-land targets - both real,
acknowledged gaps, not oversights.

"A hand should not be labeled incapable merely because the greedy policy chose another legal
line" - this module exists specifically to prevent that mislabeling for the named target list.
"""
import random

from opening_hand_model import ACCELERATION, PREMIUM_ONE_DROP_ENGINES
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY, _is_land
from opening_hand_metrics import snapshot_metrics

ENGINE_RUSH_PRIORITY = ["free_accel", "paid_accel", "engine", "premium_engine", "commander", "tutor", "interaction"]
INTERACTION_HOLD_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "commander", "engine", "interaction", "tutor"]
PRIORITY_VARIANTS = [DEFAULT_PRIORITY, ENGINE_RUSH_PRIORITY, INTERACTION_HOLD_PRIORITY]

MAX_LINES = 12  # hard cap on alternative lines explored per hand - documented bound, not exhaustive


def _t1_engine_class(state):
    accel_used_t1 = any(name in ACCELERATION for (t, name, cls) in state.cast_log if t == 1)
    for (t, name, cls) in state.cast_log:
        if t != 1 or cls not in ("engine", "premium_engine"):
            continue
        if name in PREMIUM_ONE_DROP_ENGINES:
            return "premium_one_drop"
        return "accelerated_engine" if accel_used_t1 else "two_mana_engine"
    return None


TARGETS = [
    "t1_premium_engine", "t1_two_drop_engine", "t1_any_meaningful_development",
    "t2_engine", "t2_engine_plus_interaction", "t3_tymna_supported",
    "t3_thrasios_activation", "t3_pod_functional", "t3_survival_functional",
    "t3_cradle_3plus", "t3_deterministic_win",
]


def _extract_targets(state, m1, m2, m3):
    cls_t1 = _t1_engine_class(state)
    return {
        "t1_premium_engine": cls_t1 == "premium_one_drop",
        "t1_two_drop_engine": cls_t1 == "two_mana_engine",
        "t1_any_meaningful_development": m1["mana_2plus"] or m1["any_engine_active"],
        "t2_engine": m2["any_engine_active"],
        "t2_engine_plus_interaction": m2["engine_plus_interaction"],
        "t3_tymna_supported": m3["tymna_supported"],
        "t3_thrasios_activation": m3["thrasios_activation_now"],
        "t3_pod_functional": m3["birthing_pod"]["usable_now"],
        "t3_survival_functional": m3["survival_of_the_fittest"]["usable_now"],
        "t3_cradle_3plus": m3["cradle_3plus"],
        "t3_deterministic_win": m3["deterministic_win_available"],
    }


def _run_line(hand, library, on_play, cards, combos, priority_order, forced_t1_land, max_turn):
    state = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(0), cards=cards)
    snaps = {}
    for t in range(1, max_turn + 1):
        forced = forced_t1_land if t == 1 else None
        develop_turn(state, cards, priority_order=priority_order, forced_land=forced)
        snaps[t] = snapshot_metrics(state, cards, combos)
    return state, snaps


def compute_policy_realized_and_best_known_achievable(hand, library, on_play, cards, combos, max_turn=3):
    """Returns (policy_realized: dict[target]->bool, best_known_achievable: dict[target]->bool,
    lines_explored: int)."""
    # policy_realized: the exact same single greedy line the main census runs.
    state0, snaps0 = _run_line(hand, library, on_play, cards, combos, DEFAULT_PRIORITY, None, max_turn)
    policy_realized = _extract_targets(state0, snaps0[1], snaps0[2], snaps0.get(3, snaps0[max_turn]))

    t1_land_choices = [c for c in hand if _is_land(c, cards)] or [None]
    lines = []
    for land_choice in t1_land_choices:
        for priority in PRIORITY_VARIANTS:
            lines.append((land_choice, priority))
    lines = lines[:MAX_LINES]

    best_known = dict(policy_realized)  # policy_realized always counts as one achieved line
    for land_choice, priority in lines:
        state, snaps = _run_line(hand, library, on_play, cards, combos, priority, land_choice, max_turn)
        t3 = snaps.get(3, snaps[max_turn])
        results = _extract_targets(state, snaps[1], snaps[2], t3)
        for k, v in results.items():
            if v:
                best_known[k] = True

    return policy_realized, best_known, len(lines)
