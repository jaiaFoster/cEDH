"""SIM-001 SOLO-004 section 12 — full London mulligan simulations per candidate policy.

Real London mulligan (section 8, matching bottoming_search.py's mechanics): draw a fresh 7,
evaluate the keep policy; if rejected, the ENTIRE 7 goes back and a completely fresh 7 is drawn
(nothing carried over - real London mulligan rules, not a biased "redraw only the bad cards");
if kept at mulligan count N, bottom N cards from THAT SAME 7 using the SEARCH-based bottoming
(bottoming_search.py's exhaustive_bottom_search, scored under the BALANCED profile uniformly
across all policy comparisons - so only the KEEP decision differs between policies being
compared, not bottoming quality) - not the fast heuristic, which was shown to leave real value on
the table (solo004_bottoming_analysis.json: only 35.1%/21.4%/15.1% near-optimal at bottom 1/2/3).

Three policies compared: TREE_DEPTH4 and SIMPLE_RULES (cheap - keep decision needs only opener
features, no full T1-T3 sim), and MACHINE_OPTIMAL (expensive - the keep decision itself requires
simulating the candidate hand, so it's run at a smaller sample size, matching this project's
established practice for expensive searches).
"""
import argparse
import json
import random
import time
from pathlib import Path
from collections import Counter

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_features import extract_opener_features
from run_solo004_dataset import simulate_hand_outcome
from bottoming_search import exhaustive_bottom_search
from candidate_mulligan_policies import policy_tree_depth4, policy_simple_rules, policy_machine_optimal_factory

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_MULLIGANS = 4


def feature_policy(fn):
    def wrapped(hand, library, on_play, cards):
        feats = extract_opener_features(hand, library, on_play, cards)
        return fn(feats)
    return wrapped


def simulate_one_mulligan_sequence(names, rng, cards, combos, keep_policy, on_play, max_mulligans=MAX_MULLIGANS):
    mulligans = 0
    while True:
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        if keep_policy(hand, library, on_play, cards) or mulligans >= max_mulligans:
            break
        mulligans += 1

    if mulligans == 0:
        final_hand, final_library = hand, library
    else:
        best_bottomed, _, _ = exhaustive_bottom_search(hand, library, on_play, cards, combos, mulligans, "BALANCED")
        final_hand = [c for c in hand if c not in best_bottomed]
        final_library = library + list(best_bottomed)

    row = simulate_hand_outcome(final_hand, final_library, on_play, cards, combos)
    row["mulligans_taken"] = mulligans
    row["final_hand_size"] = len(final_hand)
    return row


def run_policy(policy_name, keep_policy, count, seed, seat, cards, combos):
    on_play = seat == "play"
    names = list(cards.keys())
    rng = random.Random(seed)
    t0 = time.time()
    results = []
    for i in range(count):
        row = simulate_one_mulligan_sequence(names, rng, cards, combos, keep_policy, on_play)
        results.append(row)
    elapsed = time.time() - t0
    return results, elapsed


def _bucket(mulligans):
    return {0: "0", 1: "1", 2: "2"}.get(mulligans, "3+")


def aggregate(results):
    n = len(results)
    mull_counts = Counter(_bucket(r["mulligans_taken"]) for r in results)
    avg_final_hand_size = sum(r["final_hand_size"] for r in results) / n
    by_bucket = {}
    for b in ("0", "1", "2", "3+"):
        subset = [r for r in results if _bucket(r["mulligans_taken"]) == b]
        if not subset:
            by_bucket[b] = None
            continue
        by_bucket[b] = {
            "pct_of_population": len(subset) / n,
            "t3_strong_state_rate": sum(1 for r in subset if r["out_t3__t3_any_strong_state"]) / len(subset),
            "t3_stalled_rate": sum(1 for r in subset if r["out_t3__t3_stalled"]) / len(subset),
            "t2_engine_rate": sum(1 for r in subset if r["out_t2__t2_primary_engine_online"]) / len(subset),
            "mana_shortfall_rate": sum(1 for r in subset if r["out__mana_shortfall_t3"]) / len(subset),
            "mean_cards_remaining_t3": sum(r["out__cards_in_hand_t3"] for r in subset) / len(subset),
        }
    return {
        "sample_size": n,
        "mulligan_distribution": {k: v / n for k, v in mull_counts.items()},
        "avg_final_hand_size": avg_final_hand_size,
        "expected_card_disadvantage": 7 - avg_final_hand_size,
        "overall_t3_strong_state_rate": sum(1 for r in results if r["out_t3__t3_any_strong_state"]) / n,
        "overall_t3_stalled_rate": sum(1 for r in results if r["out_t3__t3_stalled"]) / n,
        "overall_mana_shortfall_rate": sum(1 for r in results if r["out__mana_shortfall_t3"]) / n,
        "by_mulligan_count": by_bucket,
    }


POLICIES_CHEAP = {
    "TREE_DEPTH4": feature_policy(policy_tree_depth4),
    "SIMPLE_RULES": feature_policy(policy_simple_rules),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=100000)
    ap.add_argument("--machine-optimal-count", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()

    out = {**deck_provenance_fields(payload), "phase": "SIM_001_SOLO_004_LONDON_MULLIGAN", "seed": args.seed, "seat": args.seat, "policies": {}}

    for name, policy in POLICIES_CHEAP.items():
        results, elapsed = run_policy(name, policy, args.count, args.seed, args.seat, cards, combos)
        agg = aggregate(results)
        agg["elapsed_seconds"] = elapsed
        out["policies"][name] = agg
        print(f"{name}: n={args.count} in {elapsed:.1f}s - dist={agg['mulligan_distribution']} "
              f"strong_state={agg['overall_t3_strong_state_rate']:.3f} avg_hand={agg['avg_final_hand_size']:.3f}")

    mo_keep = policy_machine_optimal_factory(cards, combos, args.seat == "play", "BALANCED")

    def mo_wrapped(hand, library, on_play, cards_):
        return mo_keep(hand, library)

    results, elapsed = run_policy("MACHINE_OPTIMAL", mo_wrapped, args.machine_optimal_count, args.seed, args.seat, cards, combos)
    agg = aggregate(results)
    agg["elapsed_seconds"] = elapsed
    out["policies"]["MACHINE_OPTIMAL"] = agg
    print(f"MACHINE_OPTIMAL: n={args.machine_optimal_count} in {elapsed:.1f}s - dist={agg['mulligan_distribution']} "
          f"strong_state={agg['overall_t3_strong_state_rate']:.3f} avg_hand={agg['avg_final_hand_size']:.3f}")

    # KEEP_EVERYTHING baseline for reference (SOLO-003R's own population, no mulligan at all)
    out["policies"]["KEEP_EVERYTHING_BASELINE_NOTE"] = (
        "See solo003r_trajectory_census_{play,draw}.json: t3_any_strong_state = 0.438 (play) / "
        "0.511 (draw), avg_hand_size = 7.0 always, expected_card_disadvantage = 0."
    )

    out_path = Path(args.out) if args.out else (
        REPO_ROOT / "results" / "solo_baseline" / f"solo004_london_mulligan_results_{args.seat}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
