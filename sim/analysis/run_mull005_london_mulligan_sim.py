"""SIM-001 MULL-005 — full London mulligan simulation, trajectory policies vs SOLO-004 baselines.

Same real London mulligan mechanics as SOLO-004's run_london_mulligan_sim.py (draw a fresh 7 per
mulligan attempt - nothing carried over; on keep, bottom N cards from that SAME 7), reused
verbatim for the sequencing loop. Two things change for MULL-005:

  1. Bottoming is scored by TRAJECTORY TIER (grade_trajectory on the greedy line, via
     derive_hand_size_trajectory_thresholds.py's _grade_greedy/best_bottomed_tier - reused, not
     rebuilt) instead of SOLO-004's BALANCED composite-score profile, so the whole comparison
     stays inside one consistent objective. This is applied identically across every policy
     compared, so - matching SOLO-004's own methodological discipline - only the KEEP decision
     differs between policies, never the bottoming quality.
  2. Policies compared: TRAJECTORY_SIMPLE and TRAJECTORY_TREE (cheap, opener-features-only) at
     full sample size, TRAJECTORY_MACHINE (expensive - the keep decision itself runs the bounded
     search) at a smaller sample, PLUS SOLO-004's own SIMPLE_RULES and TREE_DEPTH4 baselines
     re-run through the SAME trajectory-tier-scored loop - so "trajectory-first heuristics beat
     resource-first heuristics" is a head-to-head claim under one shared evaluation metric, not two
     separate studies compared by eye.
"""
import argparse
import json
import random
import time
from pathlib import Path
from collections import Counter

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_features import extract_opener_features
from derive_hand_size_trajectory_thresholds import best_bottomed_tier, TIER_VALUE
from trajectory_policies import trajectory_simple_policy, trajectory_machine_policy
from candidate_mulligan_policies import policy_tree_depth4, policy_simple_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_MULLIGANS = 4


def policy_trajectory_tree_depth4(feats):
    """Literal translation of mull005_trajectory_tree_policy.json's learned depth-4 splits - every
    leaf beneath the two dominant splits collapsed to a single class in the fitted tree (see that
    file's rules_text), so this is a faithful, not lossy, simplification."""
    if feats["distinct_colors_potential"] <= 1.5:
        return False
    if feats["t1_mana_available_now"] <= 0.5:
        return True
    if not feats["has_mox_family_card"]:
        return False
    return feats["t1_cards_in_hand_after"] <= 4.5


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
        grade = best_bottomed_tier(hand, library, on_play, cards, combos, 0)
    else:
        grade = best_bottomed_tier(hand, library, on_play, cards, combos, mulligans)
        # best_bottomed_tier doesn't return which cards were bottomed - re-derive final_hand size
        # only (the actual card identities aren't needed downstream, only the resulting grade).
        final_hand = [None] * (7 - mulligans)
        final_library = library

    return {
        "mulligans_taken": mulligans,
        "final_hand_size": len(final_hand),
        "tier": grade["tier"],
        "mechanism": grade["mechanism"],
    }


def run_policy(keep_policy, count, seed, seat, cards, combos, max_mulligans=MAX_MULLIGANS):
    on_play = seat == "play"
    names = list(cards.keys())
    rng = random.Random(seed)
    t0 = time.time()
    results = [
        simulate_one_mulligan_sequence(names, rng, cards, combos, keep_policy, on_play, max_mulligans)
        for _ in range(count)
    ]
    elapsed = time.time() - t0
    return results, elapsed


def _bucket(mulligans):
    return {0: "0", 1: "1", 2: "2"}.get(mulligans, "3+")


MULLIGAN_CARD_COST_SENSITIVITY = [0.0, 0.5, 1.0, 1.5]  # see derive_hand_size_trajectory_thresholds.py's
# IMPORTANT LIMITATION note - raw trajectory tier has no built-in penalty for fewer cards, so a
# policy that simply mulligans more aggressively will look artificially better on mean_tier_value
# alone. Reported at several disclosed assumed per-card costs rather than one invented "true" cost.


def aggregate(results):
    n = len(results)
    mull_counts = Counter(_bucket(r["mulligans_taken"]) for r in results)
    avg_final_hand_size = sum(r["final_hand_size"] for r in results) / n
    avg_cards_lost = 7 - avg_final_hand_size
    tier_dist = Counter(r["tier"] for r in results)
    mean_tier_value = sum(TIER_VALUE[r["tier"]] for r in results) / n
    mean_tier_value_after_card_cost = {
        str(cost): round(mean_tier_value - cost * avg_cards_lost, 4) for cost in MULLIGAN_CARD_COST_SENSITIVITY
    }
    by_bucket = {}
    for b in ("0", "1", "2", "3+"):
        subset = [r for r in results if _bucket(r["mulligans_taken"]) == b]
        if not subset:
            by_bucket[b] = None
            continue
        by_bucket[b] = {
            "pct_of_population": len(subset) / n,
            "tier_distribution": {t: c / len(subset) for t, c in Counter(r["tier"] for r in subset).items()},
            "mean_tier_value": sum(TIER_VALUE[r["tier"]] for r in subset) / len(subset),
        }
    return {
        "sample_size": n,
        "mulligan_distribution": {k: v / n for k, v in mull_counts.items()},
        "avg_final_hand_size": avg_final_hand_size,
        "expected_card_disadvantage": 7 - avg_final_hand_size,
        "tier_distribution": {t: c / n for t, c in tier_dist.items()},
        "fraction_tier_S_or_A": sum(1 for r in results if r["tier"] in ("S", "A")) / n,
        "fraction_tier_D_or_F": sum(1 for r in results if r["tier"] in ("D", "F")) / n,
        "mean_tier_value": mean_tier_value,
        "mean_tier_value_after_assumed_mulligan_card_cost": mean_tier_value_after_card_cost,
        "by_mulligan_count": by_bucket,
    }


POLICIES_CHEAP = {
    "TRAJECTORY_SIMPLE": feature_policy(trajectory_simple_policy),
    "TRAJECTORY_TREE": feature_policy(policy_trajectory_tree_depth4),
    "SOLO004_TREE_DEPTH4": feature_policy(policy_tree_depth4),
    "SOLO004_SIMPLE_RULES": feature_policy(policy_simple_rules),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20000)
    ap.add_argument("--machine-count", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()

    out = {
        **deck_provenance_fields(payload), "phase": "SIM_001_MULL_005_LONDON_MULLIGAN",
        "seed": args.seed, "seat": args.seat, "policies": {},
    }

    for name, policy in POLICIES_CHEAP.items():
        results, elapsed = run_policy(policy, args.count, args.seed, args.seat, cards, combos)
        agg = aggregate(results)
        agg["elapsed_seconds"] = elapsed
        out["policies"][name] = agg
        print(f"{name}: n={args.count} in {elapsed:.1f}s  dist={agg['mulligan_distribution']}  "
              f"S_or_A={agg['fraction_tier_S_or_A']:.3f}  D_or_F={agg['fraction_tier_D_or_F']:.3f}  "
              f"mean_tier_value={agg['mean_tier_value']:.3f}  "
              f"(cost1.0-adj={agg['mean_tier_value_after_assumed_mulligan_card_cost']['1.0']:.3f})  "
              f"avg_hand={agg['avg_final_hand_size']:.3f}")

    def machine_wrapped(hand, library, on_play, cards_):
        return trajectory_machine_policy(hand, library, on_play, cards_, combos)

    results, elapsed = run_policy(machine_wrapped, args.machine_count, args.seed, args.seat, cards, combos)
    agg = aggregate(results)
    agg["elapsed_seconds"] = elapsed
    out["policies"]["TRAJECTORY_MACHINE"] = agg
    print(f"TRAJECTORY_MACHINE: n={args.machine_count} in {elapsed:.1f}s  dist={agg['mulligan_distribution']}  "
          f"S_or_A={agg['fraction_tier_S_or_A']:.3f}  D_or_F={agg['fraction_tier_D_or_F']:.3f}  "
          f"mean_tier_value={agg['mean_tier_value']:.3f}  "
          f"(cost1.0-adj={agg['mean_tier_value_after_assumed_mulligan_card_cost']['1.0']:.3f})  "
          f"avg_hand={agg['avg_final_hand_size']:.3f}")

    out_path = Path(args.out) if args.out else (
        REPO_ROOT / "results" / "solo_baseline" / f"mull005_london_mulligan_results_{args.seat}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
