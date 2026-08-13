"""SIM-001 SOLO-003 — expanded bounded best-known-achievable search, with state deduplication.

Supersedes the SOLO-002R version, which only branched on turn-1 land choice. Per SOLO-003's
explicit checkpoint requirement: this now branches on land choice AND fetch target at EVERY turn
(T1-T3), crossed with a small set of alternative priority orderings, using a frontier/BFS-style
search with state deduplication (two branches reaching an identical (lands, battlefield, hand,
life, command-zone) signature are merged rather than re-explored independently) so the expanded
branching factor stays tractable.

Still NOT a full game-tree search - no held priority, no opponent interaction, and the frontier
is explicitly capped each turn (MAX_FRONTIER_STATES survivors, MAX_BRANCHES_PER_STATE branches
tried per survivor) rather than exhaustively explored. A target this search calls unreachable
might still be reachable by some line outside the bounded set explored here - that is an accepted,
documented limitation of a bounded search, not a completeness claim.

Deduplication caveat (disclosed): the state signature does not include exact remaining library
order/composition beyond "same hand" - two branches with identical (lands, battlefield, hand,
life, command zone) are treated as equivalent even though a fetch earlier in one branch but not
the other could, in principle, leave slightly different remaining libraries. Given the search
horizon is only 1-3 more turns and hands rarely see more than one or two fetches, this is judged
an acceptable approximation for a bounded search, not a claim of exact equivalence.

"A hand should not be labeled incapable merely because the greedy policy chose another legal
line" - this module exists specifically to prevent that mislabeling for the named target list.
"""
import random

from opening_hand_model import ACCELERATION, PREMIUM_ONE_DROP_ENGINES, FETCH_LANDS
from opening_hand_policy import (
    HandState, Perm, LandInPlay, develop_turn, DEFAULT_PRIORITY, _is_land, _legal_fetch_targets,
)
from opening_hand_metrics import snapshot_metrics

ENGINE_RUSH_PRIORITY = ["free_accel", "paid_accel", "engine", "premium_engine", "commander", "tutor", "interaction"]
INTERACTION_HOLD_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "commander", "engine", "interaction", "tutor"]
PRIORITY_VARIANTS = [DEFAULT_PRIORITY, ENGINE_RUSH_PRIORITY, INTERACTION_HOLD_PRIORITY]

MAX_FRONTIER_STATES = 8   # surviving distinct states carried into the next turn's expansion
MAX_BRANCHES_PER_STATE = 6  # (land choice x fetch target x priority) combinations tried per state per turn


def clone_state(state):
    """Deep-enough copy for branching search: cards (read-only, shared, potentially huge) and rng
    (never advanced inside develop_turn - all sequencing here is deterministic) are shared by
    reference; everything develop_turn can mutate is copied."""
    new = HandState.__new__(HandState)
    new.hand = list(state.hand)
    new.opening_hand = list(state.opening_hand)
    new.library = list(state.library)
    new.on_play = state.on_play
    new.rng = state.rng
    new.cards = state.cards
    new.lands = [LandInPlay(l.name, l.entered_turn, l.tapped, l.has_luck_counter) for l in state.lands]
    new.nonland_perms = []
    for p in state.nonland_perms:
        clone_p = Perm(p.name, p.entered_turn, p.is_creature, p.never_untaps)
        clone_p.tapped = p.tapped
        new.nonland_perms.append(clone_p)
    new.graveyard = list(state.graveyard)
    new.exile = list(state.exile)
    new.life = state.life
    new.turn = state.turn
    new.cast_log = list(state.cast_log)
    new.temp_mana_used_log = list(state.temp_mana_used_log)
    new.mox_diamond_pending_discard = state.mox_diamond_pending_discard
    new.landdrop_used = state.landdrop_used
    new.turn_start_mana = state.turn_start_mana
    new.turn_start_colors = set(state.turn_start_colors)
    new.command_zone = set(state.command_zone)
    new.pact_of_negation_obligations = [dict(o) for o in state.pact_of_negation_obligations]
    return new


def state_signature(state):
    """Deduplication key - see module docstring for the library-order caveat."""
    return (
        tuple(sorted(l.name for l in state.lands)),
        tuple(sorted(p.name for p in state.nonland_perms)),
        tuple(sorted(state.hand)),
        state.life,
        tuple(sorted(state.command_zone)),
    )


def _expand_branches(state, cards):
    """All (land_choice, fetch_target, priority_order) combinations to try from this state's
    upcoming turn, capped at MAX_BRANCHES_PER_STATE."""
    land_choices = [c for c in state.hand if _is_land(c, cards)] or [None]
    branches = []
    for land_choice in land_choices:
        if land_choice is not None and land_choice in FETCH_LANDS:
            targets = _legal_fetch_targets(state, land_choice)[:2] or [None]  # top-2 legal targets, bounded
            for target in targets:
                for priority in PRIORITY_VARIANTS:
                    branches.append((land_choice, target, priority))
        else:
            for priority in PRIORITY_VARIANTS:
                branches.append((land_choice, None, priority))
    return branches[:MAX_BRANCHES_PER_STATE]


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


def _extract_targets_partial(state, m1, m2, m3):
    """Only reports targets whose turn has actually been simulated so far (m2/m3 may be None
    mid-search)."""
    out = {}
    if m1 is not None:
        cls_t1 = _t1_engine_class(state)
        out["t1_premium_engine"] = cls_t1 == "premium_one_drop"
        out["t1_two_drop_engine"] = cls_t1 == "two_mana_engine"
        out["t1_any_meaningful_development"] = m1["mana_2plus"] or m1["any_engine_active"]
    if m2 is not None:
        out["t2_engine"] = m2["any_engine_active"]
        out["t2_engine_plus_interaction"] = m2["engine_plus_interaction"]
    if m3 is not None:
        out["t3_tymna_supported"] = m3["tymna_supported"]
        out["t3_thrasios_activation"] = m3["thrasios_activation_now"]
        out["t3_pod_functional"] = m3["birthing_pod"]["usable_now"]
        out["t3_survival_functional"] = m3["survival_of_the_fittest"]["usable_now"]
        out["t3_cradle_3plus"] = m3["cradle_3plus"]
        out["t3_deterministic_win"] = m3["deterministic_win_available"]
    return out


def _run_default_line(hand, library, on_play, cards, combos, max_turn):
    """The exact single greedy line the main census runs - policy_realized."""
    state = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(0), cards=cards)
    snaps = {}
    for t in range(1, max_turn + 1):
        develop_turn(state, cards)
        snaps[t] = snapshot_metrics(state, cards, combos)
    return _extract_targets_partial(state, snaps[1], snaps.get(2), snaps.get(3))


def compute_policy_realized_and_best_known_achievable(hand, library, on_play, cards, combos, max_turn=3):
    """Returns (policy_realized: dict[target]->bool, best_known_achievable: dict[target]->bool,
    lines_explored: int) using the expanded T1-T3 land/fetch/priority frontier search with
    state deduplication."""
    policy_realized = _run_default_line(hand, library, on_play, cards, combos, max_turn)

    root = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(0), cards=cards)
    frontier = {state_signature(root): (root, {})}
    best_known = {k: v for k, v in policy_realized.items()}  # policy_realized always counts as one achieved line
    total_lines = 0

    for t in range(1, max_turn + 1):
        next_frontier = {}
        for sig, (state, snaps) in frontier.items():
            for land_choice, fetch_target, priority in _expand_branches(state, cards):
                new_state = clone_state(state)
                develop_turn(
                    new_state, cards, priority_order=priority,
                    forced_land=land_choice, forced_fetch_target=fetch_target,
                )
                total_lines += 1
                new_snaps = dict(snaps)
                new_snaps[t] = snapshot_metrics(new_state, cards, combos)
                partial = _extract_targets_partial(
                    new_state, new_snaps.get(1), new_snaps.get(2), new_snaps.get(3)
                )
                for k, v in partial.items():
                    if v:
                        best_known[k] = True
                new_sig = state_signature(new_state)
                if new_sig not in next_frontier and len(next_frontier) < MAX_FRONTIER_STATES:
                    next_frontier[new_sig] = (new_state, new_snaps)
        frontier = next_frontier

    return policy_realized, best_known, total_lines
