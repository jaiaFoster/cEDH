"""SIM-001 SOLO-002 PART C — London mulligan simulation for each Part B candidate policy.

Real London mulligan: at each look, draw a fresh 7. If the keep policy accepts it (or the
mulligan cap forces a keep), bottom N cards (N = mulligans already taken) and play on with the
resulting hand. If rejected, the whole 7 (including any cards already seen) returns to the
library and a fresh 7 is drawn from a full reshuffle - matching real London mulligan rules
(nothing is "remembered" about a rejected hand's specific cards).
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import (
    load_deck_cards, load_deterministic_combos,
    TUTORS, ENGINES, PREMIUM_ONE_DROP_ENGINES, INTERACTION_CASTABLE, ACCELERATION,
    deck_provenance_fields, print_run_banner,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY
from opening_hand_metrics import snapshot_metrics, classify_failure_mode
from derive_mulligan_heuristics import raw_hand_features, CANDIDATE_POLICIES
from run_opening_hand_census import PRIMARY_METRICS

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_MULLIGANS = 4  # forced keep beyond this (hand size down to 3) - practically never reached at these keep rates


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def _bottom_score(name, cards):
    if name in TUTORS or name in ENGINES or name in PREMIUM_ONE_DROP_ENGINES:
        return 4
    if _is_land(name, cards) or name in ACCELERATION:
        return 3
    if name in INTERACTION_CASTABLE:
        return 2
    return 1


def choose_bottom_cards(hand, cards, n):
    """Heuristic bottoming (not claimed optimal - same standard as the greedy dev policy, see
    opening_hand_policy.py's module docstring): bottom excess lands beyond 4 first, then the
    lowest keep-priority-scored remaining cards."""
    if n <= 0:
        return []
    lands = [c for c in hand if _is_land(c, cards)]
    bottomed = list(lands[4:]) if len(lands) > 4 else []
    bottomed = bottomed[:n]
    remaining_pool = [c for c in hand if c not in bottomed]
    remaining_pool.sort(key=lambda c: _bottom_score(c, cards))
    for c in remaining_pool:
        if len(bottomed) >= n:
            break
        bottomed.append(c)
    return bottomed[:n]


def simulate_london_mulligan(names, rng, cards, keep_policy, max_mulligans=MAX_MULLIGANS):
    mulligans = 0
    while True:
        lib = names[:]
        rng.shuffle(lib)
        hand7 = lib[:7]
        lib_after_hand = lib[7:]  # already in draw order: index 0 = next card drawn
        feats = raw_hand_features(hand7, cards)
        keep = keep_policy(feats) or mulligans >= max_mulligans
        if keep:
            bottomed = choose_bottom_cards(hand7, cards, mulligans)
            final_hand = [c for c in hand7 if c not in bottomed]
            lib_final = lib_after_hand + bottomed  # bottomed cards go to the bottom, not reshuffled in
            return final_hand, lib_final, mulligans
        mulligans += 1


def run_one_hand_mull(names, rng, cards, combos, keep_policy, on_play, max_turn=3):
    hand, lib, mulligans = simulate_london_mulligan(names, rng, cards, keep_policy)
    state = HandState(hand, lib, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    for t in range(1, max_turn + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        per_turn[t] = snapshot_metrics(state, cards, combos)
    per_turn["failure_mode_t3"] = classify_failure_mode(per_turn[3], state, cards)
    per_turn["mulligans_taken"] = mulligans
    per_turn["starting_hand_size"] = len(hand)
    return per_turn


def _bucket(mulligans):
    return {0: "0", 1: "1", 2: "2"}.get(mulligans, "3+")


def _primary_table(results, turns=(1, 2, 3)):
    n = len(results)
    if n == 0:
        return None
    table = {}
    for metric in PRIMARY_METRICS:
        table[metric] = {str(t): sum(1 for r in results if r[t].get(metric)) / n for t in turns}
    return table


def aggregate_mulligan(results):
    n = len(results)
    mull_counts = {}
    for r in results:
        b = _bucket(r["mulligans_taken"])
        mull_counts[b] = mull_counts.get(b, 0) + 1
    mulligan_distribution = {k: v / n for k, v in mull_counts.items()}
    avg_starting_hand_size = sum(r["starting_hand_size"] for r in results) / n
    by_bucket = {}
    for b in ("0", "1", "2", "3+"):
        subset = [r for r in results if _bucket(r["mulligans_taken"]) == b]
        by_bucket[b] = {
            "pct_of_population": len(subset) / n,
            "primary_table": _primary_table(subset),
            "meaningful_development_rate_t3": (
                sum(1 for r in subset if not r["failure_mode_t3"]) / len(subset) if subset else None
            ),
        }
    total_failures = sum(1 for r in results if r["failure_mode_t3"])
    from collections import Counter
    failure_counts = Counter(r["failure_mode_t3"] for r in results if r["failure_mode_t3"])
    failure_table = {
        k: {"count": v, "pct_of_all_hands": v / n, "pct_of_failures": (v / total_failures if total_failures else 0)}
        for k, v in failure_counts.most_common()
    }
    avg_cards_remaining_t3 = sum(r[3]["cards_in_hand"] for r in results) / n
    return {
        "sample_size": n,
        "mulligan_distribution": mulligan_distribution,
        "avg_starting_hand_size": avg_starting_hand_size,
        "expected_card_disadvantage": 7 - avg_starting_hand_size,
        "avg_cards_remaining_t3": avg_cards_remaining_t3,
        "by_mulligan_count": by_bucket,
        "overall_primary_table": _primary_table(results),
        "overall_meaningful_development_rate_t3": 1 - (total_failures / n),
        "overall_failure_table": failure_table,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=25000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--on-play", action="store_true", default=True)
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo002_mulligan_simulation.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()

    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_002_PART_C",
        "sample_count_per_policy": args.count,
        "seed": args.seed,
        "on_play": args.on_play,
        "policies": {},
    }
    for pname, pfn in CANDIDATE_POLICIES.items():
        rng = random.Random(args.seed)
        t0 = time.time()
        results = [run_one_hand_mull(names, rng, cards, combos, pfn, on_play=args.on_play) for _ in range(args.count)]
        elapsed = time.time() - t0
        agg = aggregate_mulligan(results)
        agg["elapsed_seconds"] = elapsed
        out["policies"][pname] = agg
        print(f"{pname}: {args.count} hands in {elapsed:.1f}s - avg_start_size={agg['avg_starting_hand_size']:.3f} "
              f"meaningful_t3={agg['overall_meaningful_development_rate_t3']:.3f} "
              f"dist={agg['mulligan_distribution']}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
