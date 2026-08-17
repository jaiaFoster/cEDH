"""SIM-001 MULL-005/MULL-005R section 4 + "IMPORTANT CONSTRAINT" — bounded best-known trajectory
search.

For a given opener, finds the best legal T1-T3 trajectory this hand can reach - not just what the
single greedy priority-ordered line happens to realize. Two distinct things are always reported:
  - greedy_realized: the SAME single greedy line every prior SOLO-002 through SOLO-004 result is
    built on (tutors never resolve a target - byte-for-byte the pre-MULL-005 behavior).
  - best_known_achievable: the greedy line PLUS a bounded search over several MECHANISM FAMILIES,
    each re-simulated T1-T3 with a specific forced choice, keeping whichever line reaches the best
    trajectory tier.

MULL-005R (t1_t3_trajectory_audit.json, section 6's "remove the six-target bottleneck"): the
search now covers five distinct mechanism families, not just hand/library-top tutor targets:
  1. Hand/library-top tutor targets (Demonic/Vampiric/Imperial Seal/Enlightened/Ranger-Captain/
     Spellseeker) - EXPANDED target list (now includes Smothering Tithe, Mana Vault, Birthing Pod
     itself, and Survival of the Fittest, on top of the four original Tier-A engines/Sol Ring/
     Cradle) and the same two priority-order variants as before.
  2. Birthing Pod activation - sacrifice a creature from the ORIGINAL hand (bounded to creatures
     actually dealt, not any hypothetical board state) for a premium MV-appropriate target.
  3. Survival of the Fittest activation - discard a creature from the original hand for a premium
     target.
  4. Battlefield-destination tutors (Eldritch Evolution/Finale of Devastation/Nature's Rhythm/
     Chord of Calling) targeting a premium creature (Abhorrent Oculus or Esper Sentinel - the only
     two creature-typed Tier-S/A destinations in this deck; every other Tier-A engine is a non-
     creature enchantment, illegal for these effects).
  5. Crop Rotation's own land-target search (Gaea's Cradle, the deck's single highest-value
     alternate land target).

MULL-006 (t1_t3_trajectory_audit.json / assignment section 2 - "alternate fetch-target search
before using the machine policy as a reference evaluator"): a 6th family, alternate fetchland
targets. MULL-005R disclosed a real gap here (found via the top-25/holdout-audit work): a fetch's
crack target was ALWAYS chosen by develop_turn's own greedy need-colors-scored land-drop heuristic,
never branched by this search - so a hand whose ONLY route to a premium color (e.g. Mystic Remora's
U) ran through a specific fetch target that the greedy heuristic didn't prefer (because a different
target enabled an immediate lower-priority cast that turn) could be misjudged as unable to reach
that engine at all. Family 6 forces each fetchland actually in the OPENING HAND to search for each
of its real legal targets (by the fetch's actual printed basic types, via
FETCH_LAND_TARGET_TYPES/DUAL_LAND_BASIC_TYPES - never an assumed color pair) still present in the
library, reusing develop_turn's existing `forced_fetch_target` plumbing (already built for
achievable_search.py, previously never wired into this module).

Still deliberately NOT exhaustive - trying every one of ~90 library cards as a target per hand
would be intractable at any real sample size, and family 6 only branches ONE fetch's target at a
time (holding every other turn's choices at the greedy default), not the full joint combination
across multiple fetches in the same hand (a BOUNDED_SEARCH_LOWER_BOUND limitation, disclosed, not
claimed exhaustive). Each family is bounded to a small, disclosed candidate set, consistent with
this project's established practice (achievable_search.py's own land/fetch/priority branching is
similarly bounded, not exhaustive).
"""
import random

from opening_hand_model import (
    ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE, CRADLE, TUTORS, PREMIUM_ONE_DROP_ENGINES,
    FETCH_LANDS, FETCH_LAND_TARGET_TYPES, DUAL_LAND_BASIC_TYPES,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY, OCULUS_NAME
from opening_hand_metrics import snapshot_metrics
from trajectory_grading import grade_trajectory, TIER_ORDER
from pod_and_battlefield_tutors import BATTLEFIELD_CREATURE_TUTORS, BATTLEFIELD_LAND_TUTORS

# ---- family 1: hand/library-top tutor targets ------------------------------------------------
TUTOR_TARGET_CANDIDATES = sorted(ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE) + [
    "Sol Ring", CRADLE, "Mana Vault", "Birthing Pod", "Survival of the Fittest",
]
HAND_LIBRARY_TOP_TUTORS = {"Demonic Tutor", "Vampiric Tutor", "Imperial Seal", "Enlightened Tutor",
                            "Ranger-Captain of Eos", "Spellseeker"}

# A tutor sitting behind "commander" in DEFAULT_PRIORITY never gets CAST at all whenever a
# commander is also affordable that turn (commanders are checked first and consume the mana) -
# so trying different tutor TARGETS is pointless unless the search can also explore casting the
# tutor before the commander. Bounded to two extra variants (not achievable_search.py's full
# land/fetch grid) - this module's branching budget is spent on tutor targets, not sequencing.
TUTOR_FIRST_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "tutor", "commander", "engine", "interaction"]
PRIORITY_VARIANTS = [DEFAULT_PRIORITY, TUTOR_FIRST_PRIORITY]

# ---- families 2-4: bounded premium targets for Pod / Survival / battlefield-creature-tutors ---
# The only two creature-typed Tier-S/A destinations in this deck - every other Tier-A engine
# (Rhystic Study, Sylvan Library, Mystic Remora, Smothering Tithe) is a non-creature enchantment,
# an illegal target for any of these creature-search effects.
PREMIUM_CREATURE_TARGETS = [OCULUS_NAME, "Esper Sentinel"]

# ---- family 5: Crop Rotation's own land-target search -----------------------------------------
LAND_TUTOR_TARGET_CANDIDATES = [CRADLE]


def _simulate(hand, library, on_play, cards, combos, priority_order=DEFAULT_PRIORITY,
              forced_tutor_target=None, forced_pod_activation=None, forced_survival_activations=None,
              forced_battlefield_tutor=None, forced_land_tutor=None, forced_fetch_target=None, max_turn=3):
    state = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(0), cards=cards)
    snaps = {}
    for t in range(1, max_turn + 1):
        develop_turn(
            state, cards, priority_order=priority_order, forced_tutor_target=forced_tutor_target,
            forced_pod_activation=forced_pod_activation, forced_survival_activations=forced_survival_activations,
            forced_battlefield_tutor=forced_battlefield_tutor, forced_land_tutor=forced_land_tutor,
            forced_fetch_target=forced_fetch_target,
        )
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


def _candidate_configs(hand, library, cards):
    """Yields (label, kwargs) for every bounded candidate this search tries, beyond the greedy
    baseline. `kwargs` are the forced_* parameters passed straight to _simulate()."""
    has_hand_tutor = any(n in HAND_LIBRARY_TOP_TUTORS for n in hand)
    if has_hand_tutor:
        for priority in PRIORITY_VARIANTS:
            priority_label = "DEFAULT_PRIORITY" if priority is DEFAULT_PRIORITY else "TUTOR_FIRST_PRIORITY"
            for target in TUTOR_TARGET_CANDIDATES:
                if target not in library:
                    continue
                if priority is DEFAULT_PRIORITY and target is None:
                    continue
                yield (f"tutor:{target}:{priority_label}", {
                    "priority_order": priority, "forced_tutor_target": target,
                })

    creatures_in_hand = [c for c in hand if "Creature" in cards.get(c, {}).get("type", "")]

    if "Birthing Pod" in hand or "Birthing Pod" in library:
        for sac in creatures_in_hand:
            sac_mv = cards[sac]["cmc"]
            for target in PREMIUM_CREATURE_TARGETS:
                if target not in library or target not in cards:
                    continue
                if cards[target]["cmc"] == sac_mv + 1:
                    yield (f"pod:{sac}->{target}", {"forced_pod_activation": (sac, target)})

    if "Survival of the Fittest" in hand or "Survival of the Fittest" in library:
        for discard in creatures_in_hand:
            for target in PREMIUM_CREATURE_TARGETS:
                if target not in library or target == discard:
                    continue
                yield (f"survival:{discard}->{target}", {
                    "forced_survival_activations": [(discard, target)],
                })

    for tutor_name, spec in BATTLEFIELD_CREATURE_TUTORS.items():
        if tutor_name not in hand:
            continue
        for target in PREMIUM_CREATURE_TARGETS:
            if target not in library or target not in cards:
                continue
            if spec["sac_required"]:
                # SIM-DECKBUILD-004: mv_offset generalizes this beyond Eldritch Evolution's own
                # hardcoded +2 (see pod_and_battlefield_tutors.py's matching generalization) -
                # Neoform's real text is +1, not +2.
                mv_offset = spec.get("mv_offset", 2)
                for sac in creatures_in_hand:
                    if cards[target]["cmc"] == cards[sac]["cmc"] + mv_offset:
                        yield (f"battlefield_tutor:{tutor_name}->{target}(sac {sac})", {
                            "forced_battlefield_tutor": (tutor_name, target, sac),
                        })
            else:
                yield (f"battlefield_tutor:{tutor_name}->{target}", {
                    "forced_battlefield_tutor": (tutor_name, target, None),
                })

    for tutor_name in BATTLEFIELD_LAND_TUTORS:
        if tutor_name not in hand:
            continue
        for target in LAND_TUTOR_TARGET_CANDIDATES:
            if target not in library:
                continue
            yield (f"land_tutor:{tutor_name}->{target}", {"forced_land_tutor": (tutor_name, target)})

    # ---- family 6: alternate fetchland targets (MULL-006 section 2) ---------------------------
    # Only fetches actually IN THE OPENING HAND - a fetch that might be drawn later is already
    # covered by the greedy line's own in-the-moment choice when it's drawn, same as every other
    # card this search doesn't specifically branch on. Each candidate forces ONE fetch's target;
    # every other turn's land/fetch choice still uses develop_turn's own greedy heuristic (a
    # disclosed, bounded, non-joint search - see module docstring).
    seen_fetch_targets = set()
    for fetch_name in sorted(set(hand) & FETCH_LANDS):
        types_wanted = FETCH_LAND_TARGET_TYPES.get(fetch_name, frozenset())
        legal_targets = sorted(
            name for name, types in DUAL_LAND_BASIC_TYPES.items()
            if (types & types_wanted) and name in library
        )
        for target in legal_targets:
            key = (fetch_name, target)
            if key in seen_fetch_targets:
                continue
            seen_fetch_targets.add(key)
            yield (f"fetch:{fetch_name}->{target}", {"forced_fetch_target": target})


def find_best_trajectory(hand, library, on_play, cards, combos):
    """Returns (greedy_result, best_result, candidates_tried) where each result is
    {"tier", "tier_engine", "tier_turn", "mechanism", "resource_cost", "search_label"}.
    greedy_result is ALWAYS DEFAULT_PRIORITY with no forced choices - the exact pre-MULL-005 line
    every prior result is built on. best_result searches the bounded candidate families described
    in this module's docstring."""
    state, m1, m2, m3 = _simulate(hand, library, on_play, cards, combos)
    greedy_grade = grade_trajectory(state, cards, m1, m2, m3)
    greedy_grade["search_label"] = "greedy"

    best = greedy_grade
    candidates_tried = 1

    for label, kwargs in _candidate_configs(hand, library, cards):
        candidates_tried += 1
        state_t, m1_t, m2_t, m3_t = _simulate(hand, library, on_play, cards, combos, **kwargs)
        grade_t = grade_trajectory(state_t, cards, m1_t, m2_t, m3_t)
        grade_t["search_label"] = label
        if _better(grade_t, best):
            best = grade_t

    return greedy_grade, best, candidates_tried
