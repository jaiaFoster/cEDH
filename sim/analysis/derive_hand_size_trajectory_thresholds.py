"""SIM-001 MULL-005 section — hand-size-specific trajectory thresholds (7/6/5/4).

Re-derives SOLO-004's mulligan cost curve under trajectory-first logic instead of the multi-
objective composite score: for each hand size N in {7,6,5,4}, what trajectory tier distribution is
achievable via OPTIMAL bottoming of a fresh 7 down to N cards (real London mulligan mechanics -
draw 7, bottom 7-N), and therefore what is the minimum trajectory tier worth KEEPING at that size
rather than mulliganing again?

Grading uses grade_trajectory on the single greedy DEFAULT_PRIORITY line (not the full bounded
tutor-target search) for tractability - bottoming already requires C(7, 7-N) re-simulations per
dealt hand (35 at N=4), and stacking the ~13x tutor-target search on top of that would be
prohibitively slow at any usable sample size. This is a deliberate, disclosed cost/precision
tradeoff, consistent with SOLO-004's own bottoming_search.py using the cheaper simulate_hand_outcome
(not --achievable) for its exhaustive inner loop.

Decision rule: assign each tier an ordinal value (TIER_VALUE, disclosed below - not fit to any
target, a simple monotone scale matching the tier definitions' qualitative ordering with S/A given
real separation over B/C since those are the trajectories MULL-005 identifies as premium). A hand
at size N with tier T is worth KEEPING over mulliganing to N-1 iff TIER_VALUE(T) >= EV(N-1), where
EV(N-1) is the empirical expected tier value of a FRESH optimally-bottomed hand at size N-1 (a
mulligan draws an entirely new 7, not a better bottoming of the same one). This yields one
threshold tier per hand size - the trajectory-first equivalent of a keep-7 decision table.
"""
import argparse
import itertools
import json
import random
from collections import Counter
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY
from opening_hand_metrics import snapshot_metrics
from trajectory_grading import grade_trajectory, TIER_ORDER

REPO_ROOT = Path(__file__).resolve().parents[2]

TIER_VALUE = {"S": 6.0, "A": 4.5, "B": 2.5, "C": 1.0, "D": 0.0, "F": -1.5}
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}


def _grade_greedy(hand, library, on_play, cards, combos):
    state = HandState(list(hand), list(library), on_play=on_play, rng=random.Random(0), cards=cards)
    snaps = {}
    for t in range(1, 4):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        snaps[t] = snapshot_metrics(state, cards, combos)
    return grade_trajectory(state, cards, snaps[1], snaps[2], snaps[3])


def best_bottomed_tier(hand, library, on_play, cards, combos, n_bottom):
    """Returns the grade dict for the best-tier (7-n_bottom)-card sub-hand, search-optimal over
    all C(7, n_bottom) bottoming choices."""
    if n_bottom == 0:
        return _grade_greedy(hand, library, on_play, cards, combos)
    best = None
    for bottomed in itertools.combinations(hand, n_bottom):
        remaining = [c for c in hand if c not in bottomed]
        new_library = list(library) + list(bottomed)
        grade = _grade_greedy(remaining, new_library, on_play, cards, combos)
        if best is None or (TIER_RANK[grade["tier"]], grade["tier_turn"] or 99) < (TIER_RANK[best["tier"]], best["tier_turn"] or 99):
            best = grade
    return best


def run_for_size(count, n_bottom, seed, seat, names, cards, combos):
    on_play = seat == "play"
    rng = random.Random(seed)
    dist = Counter()
    mech_dist = Counter()
    for _ in range(count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        lib_after_deal = lib[7:]
        grade = best_bottomed_tier(hand, lib_after_deal, on_play, cards, combos, n_bottom)
        dist[grade["tier"]] += 1
        mech_dist[grade["mechanism"]] += 1
    n = count
    ev = sum(TIER_VALUE[t] * (c / n) for t, c in dist.items())
    return {
        "hand_size": 7 - n_bottom,
        "sample_count": n,
        "tier_distribution": {t: round(c / n, 4) for t, c in dist.items()},
        "mechanism_distribution_top10": {k: round(v / n, 4) for k, v in mech_dist.most_common(10)},
        "expected_tier_value": round(ev, 4),
    }


# IMPORTANT LIMITATION (disclosed, not smoothed over): trajectory tier is graded purely from the
# T1-T3 line, which has NO built-in penalty for holding fewer cards - bottoming a card that was
# never going to be cast anyway is a free, tier-neutral action in this model. That means raw
# expected_tier_value is structurally biased to look FLAT-TO-BETTER at smaller hand sizes (you
# always get to discard your single worst card for "free" when bottoming down by 1), which is NOT
# a claim that mulliganing is actually free - real Magic pays for a mulligan with a permanently
# smaller hand for the rest of the game, a cost entirely outside this project's 3-turn window and
# NOT measured by this simulator (no full-game/4-player matchup data exists yet - stop condition of
# this phase). Rather than inventing a single "true" cost figure this project has no simulated
# basis for, MULLIGAN_CARD_COST_SENSITIVITY reports thresholds under several disclosed assumed
# per-card costs (in TIER_VALUE units), including 0.0 (the raw, uncorrected comparison) so the
# structural bias itself stays visible rather than hidden inside one authoritative-looking number.
MULLIGAN_CARD_COST_SENSITIVITY = [0.0, 0.5, 1.0, 1.5, 2.0]


def derive_thresholds(by_size, card_cost):
    """For each size N (largest first), the minimum tier worth keeping over mulliganing to N-1,
    using N-1's expected_tier_value (penalized by `card_cost` per card below 7) as the mulligan
    alternative's EV. Size 4 has no EV(3) computed here (out of MULL-005's stated 7/6/5/4 scope)."""
    sizes = sorted(by_size, reverse=True)  # [7, 6, 5, 4]
    thresholds = {}
    for size in sizes:
        lower = size - 1
        if lower not in by_size:
            thresholds[size] = {
                "keep_at_or_above_tier": None,
                "note": "no EV computed for mulliganing below this size within 7/6/5/4 scope",
            }
            continue
        ev_lower = by_size[lower]["expected_tier_value"] - card_cost * (7 - lower)
        keep_tier = None
        for t in TIER_ORDER:  # S,A,B,C,D,F - find the WORST tier still worth keeping
            if TIER_VALUE[t] >= ev_lower:
                keep_tier = t
            else:
                break
        thresholds[size] = {
            "keep_at_or_above_tier": keep_tier,
            "ev_of_mulliganing_to_size": lower,
            "ev_of_mulliganing_value_raw": round(by_size[lower]["expected_tier_value"], 4),
            "ev_of_mulliganing_value_after_card_cost": round(ev_lower, 4),
        }
    return thresholds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--count7", type=int, default=4000)
    ap.add_argument("--count6", type=int, default=3000)
    ap.add_argument("--count5", type=int, default=1500)
    ap.add_argument("--count4", type=int, default=500)
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "mull005_hand_size_thresholds.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()

    by_size = {}
    for n_bottom, count in [(0, args.count7), (1, args.count6), (2, args.count5), (3, args.count4)]:
        r = run_for_size(count, n_bottom, args.seed, args.seat, names, cards, combos)
        by_size[r["hand_size"]] = r
        print(f"size={r['hand_size']}: EV={r['expected_tier_value']:.3f}  dist={r['tier_distribution']}")

    thresholds_by_cost = {
        str(cost): derive_thresholds(by_size, cost) for cost in MULLIGAN_CARD_COST_SENSITIVITY
    }
    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_005_HAND_SIZE_THRESHOLDS",
        "seat": args.seat,
        "seed": args.seed,
        "tier_value_scale": TIER_VALUE,
        "by_hand_size": by_size,
        "keep_thresholds_by_assumed_mulligan_card_cost": thresholds_by_cost,
        "note": (
            "Grading uses the greedy DEFAULT_PRIORITY line only (not the bounded tutor-target "
            "search) - see module docstring for the tractability tradeoff. Thresholds are ordinal "
            "(computed on TIER_VALUE, a disclosed monotone scale, not fit to any target). The "
            "assumed-mulligan-card-cost sensitivity sweep exists because this simulator has no "
            "full-game/4-player data to derive a single real cost-of-mulligan from - see module "
            "docstring 'IMPORTANT LIMITATION'. cost=0.0 is the raw, uncorrected comparison and is "
            "expected to look mulligan-favorable; it is reported for transparency, not as guidance."
        ),
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out_path}")
    for cost, table in thresholds_by_cost.items():
        print(f"\n-- assumed mulligan card cost = {cost} --")
        print(json.dumps(table, indent=2))


if __name__ == "__main__":
    main()
