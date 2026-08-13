"""SIM-001 MULL-005 section 4 + "IMPORTANT CONSTRAINT" — bounded best-known trajectory search.

For a given opener, finds the best legal T1-T3 trajectory this hand can reach - not just what the
single greedy priority-ordered line happens to realize. Two distinct things are always reported,
per the assignment's explicit constraint:
  - greedy_realized: the SAME single greedy line every prior SOLO-002 through SOLO-004 result is
    built on (tutors never resolve a target - byte-for-byte the pre-MULL-005 behavior).
  - best_known_achievable: the greedy line PLUS, for hands with a tutor that could plausibly be
    cast, a bounded search over a small, disclosed set of high-value tutor targets (the four
    Tier-A engines, Sol Ring, and Gaea's Cradle) - each one fully re-simulated T1-T3 with that
    target forced, then graded, keeping whichever line reaches the best trajectory tier.

This is deliberately NOT exhaustive (trying every one of ~90 library cards as a tutor target per
hand would be intractable at any real sample size) - it is bounded and disclosed, consistent with
this project's established practice (achievable_search.py's own land/fetch/priority branching is
similarly bounded, not exhaustive). A hand should not be graded as trajectory-D "no engine" merely
because the greedy line didn't think to fetch Rhystic Study; it also should not be credited with
fetching an engine that was never a remotely plausible target.
"""
import random

from opening_hand_model import (
    ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE, CRADLE, TUTORS,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY
from opening_hand_metrics import snapshot_metrics
from trajectory_grading import grade_trajectory, TIER_ORDER

TUTOR_TARGET_CANDIDATES = sorted(ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE) + ["Sol Ring", CRADLE]

# A tutor sitting behind "commander" in DEFAULT_PRIORITY never gets CAST at all whenever a
# commander is also affordable that turn (commanders are checked first and consume the mana) -
# so trying different tutor TARGETS is pointless unless the search can also explore casting the
# tutor before the commander. Bounded to two extra variants (not achievable_search.py's full
# land/fetch grid) - this module's branching budget is spent on tutor targets, not sequencing.
TUTOR_FIRST_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "tutor", "commander", "engine", "interaction"]
PRIORITY_VARIANTS = [DEFAULT_PRIORITY, TUTOR_FIRST_PRIORITY]


def _simulate(hand, library, on_play, cards, combos, forced_tutor_target=None, priority_order=DEFAULT_PRIORITY, max_turn=3):
    state = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(0), cards=cards)
    snaps = {}
    for t in range(1, max_turn + 1):
        develop_turn(state, cards, priority_order=priority_order, forced_tutor_target=forced_tutor_target)
        snaps[t] = snapshot_metrics(state, cards, combos)
    return state, snaps.get(1), snaps.get(2), snaps.get(3)


def _tier_rank(tier):
    return TIER_ORDER.index(tier)


def _better(candidate, current):
    """True if `candidate` is a real improvement over `current` - a strictly better tier, or the
    same tier reached on an earlier turn (never a same-tier/same-turn 'tie' relabeled as better)."""
    if _tier_rank(candidate["tier"]) < _tier_rank(current["tier"]):
        return True
    if candidate["tier"] == current["tier"] and candidate["tier"] not in ("D", "F"):
        return (candidate["tier_turn"] or 99) < (current["tier_turn"] or 99)
    return False


def find_best_trajectory(hand, library, on_play, cards, combos):
    """Returns (greedy_result, best_result, candidates_tried) where each result is
    {"tier", "tier_engine", "tier_turn", "mechanism", "resource_cost", "forced_tutor_target",
    "priority_variant"}. greedy_result is ALWAYS DEFAULT_PRIORITY with no forced tutor target -
    the exact pre-MULL-005 line every prior result is built on. best_result searches a bounded
    grid of (priority variant) x (tutor target) - see module docstring for why both dimensions
    are needed (a tutor sitting behind "commander" in priority order never gets cast at all
    whenever a commander is also affordable, making target branching alone pointless)."""
    state, m1, m2, m3 = _simulate(hand, library, on_play, cards, combos, forced_tutor_target=None, priority_order=DEFAULT_PRIORITY)
    greedy_grade = grade_trajectory(state, cards, m1, m2, m3)
    greedy_grade["forced_tutor_target"] = None
    greedy_grade["priority_variant"] = "DEFAULT_PRIORITY"

    best = greedy_grade
    candidates_tried = 1
    has_tutor_in_hand = any(n in TUTORS for n in hand)
    targets = [None] + [t for t in TUTOR_TARGET_CANDIDATES if t in library] if has_tutor_in_hand else [None]
    priorities = PRIORITY_VARIANTS if has_tutor_in_hand else [DEFAULT_PRIORITY]

    for priority in priorities:
        for target in targets:
            if priority is DEFAULT_PRIORITY and target is None:
                continue  # already computed as greedy_grade above
            candidates_tried += 1
            state_t, m1_t, m2_t, m3_t = _simulate(
                hand, library, on_play, cards, combos, forced_tutor_target=target, priority_order=priority
            )
            grade_t = grade_trajectory(state_t, cards, m1_t, m2_t, m3_t)
            grade_t["forced_tutor_target"] = target
            grade_t["priority_variant"] = "DEFAULT_PRIORITY" if priority is DEFAULT_PRIORITY else "TUTOR_FIRST_PRIORITY"
            if _better(grade_t, best):
                best = grade_t

    return greedy_grade, best, candidates_tried
