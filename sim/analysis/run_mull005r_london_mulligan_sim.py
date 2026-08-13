"""SIM-001 MULL-005R section 19 — full London mulligan simulation, corrected trajectory policies
vs SOLO-004 baselines.

Thin wrapper over run_mull005_london_mulligan_sim.py's simulation loop (simulate_one_mulligan_
sequence/run_policy/aggregate) - that loop already calls the CORRECTED trajectory_policies.
trajectory_simple_policy/trajectory_machine_policy (both now read mull005r_hand_size_thresholds.
json - see trajectory_policies.py's _load_thresholds()) and the CORRECTED
derive_hand_size_trajectory_thresholds.best_bottomed_tier (grade_trajectory, including this
phase's battlefield_t1/t2 ONLINE_CLASSES fix). Only TRAJECTORY_TREE needs a fresh hardcoded
translation here: mull005_trajectory_tree_policy.json's tree was fit on the UNCORRECTED dataset,
so the literal split logic below is transcribed from the newly-fit
mull005r_trajectory_tree_policy.json (see fit_trajectory_tree_policy.py's rerun against
mull005r_trajectory_dataset_play.jsonl.gz) instead - a fresh fit, not a rescoring of the old one,
per the assignment's explicit instruction that this must be a real rerun.
"""
import argparse
import json
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_policies import trajectory_simple_policy, trajectory_machine_policy
from candidate_mulligan_policies import policy_tree_depth4, policy_simple_rules
from run_mull005_london_mulligan_sim import feature_policy, run_policy, aggregate

REPO_ROOT = Path(__file__).resolve().parents[2]


def policy_trajectory_tree_r_depth4(feats):
    """Literal translation of mull005r_trajectory_tree_policy.json's fresh depth-4 fit (rules_text)
    - every leaf beneath the dominant splits collapsed to a single class, a faithful (not lossy)
    simplification of that file's tree structure."""
    if feats["distinct_colors_potential"] <= 0.5:
        if not feats["t1_accel_executable_now"]:
            return False
        if feats["t1_cards_in_hand_after"] <= 4.5:
            return bool(feats["has_tier_a_engine_card"])
        return False
    # distinct_colors_potential > 0.5
    if feats["nonland_count"] <= 5.5:
        return True
    if feats["t1_ceiling_mana_next_turn"] <= 1.5:
        return True
    return bool(feats["has_mox_family_card"])


POLICIES_CHEAP_R = {
    "TRAJECTORY_SIMPLE_R": feature_policy(trajectory_simple_policy),
    "TRAJECTORY_TREE_R": feature_policy(policy_trajectory_tree_r_depth4),
    "SOLO004_TREE_DEPTH4": feature_policy(policy_tree_depth4),
    "SOLO004_SIMPLE_RULES": feature_policy(policy_simple_rules),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20000)
    ap.add_argument("--machine-count", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=1008)  # distinct from MULL-005's seed=42
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()

    out = {
        **deck_provenance_fields(payload), "phase": "SIM_001_MULL_005R_LONDON_MULLIGAN_CORRECTED",
        "regression_gate": "results/solo_baseline/mull005r_regression_gate.json (OPEN_FOR_PRODUCTION_RERUN, verified before this run)",
        "seed": args.seed, "seat": args.seat, "policies": {},
    }

    for name, policy in POLICIES_CHEAP_R.items():
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
    out["policies"]["TRAJECTORY_MACHINE_R"] = agg
    print(f"TRAJECTORY_MACHINE_R: n={args.machine_count} in {elapsed:.1f}s  dist={agg['mulligan_distribution']}  "
          f"S_or_A={agg['fraction_tier_S_or_A']:.3f}  D_or_F={agg['fraction_tier_D_or_F']:.3f}  "
          f"mean_tier_value={agg['mean_tier_value']:.3f}  "
          f"(cost1.0-adj={agg['mean_tier_value_after_assumed_mulligan_card_cost']['1.0']:.3f})  "
          f"avg_hand={agg['avg_final_hand_size']:.3f}")

    out_path = Path(args.out) if args.out else (
        REPO_ROOT / "results" / "solo_baseline" / f"mull005r_london_mulligan_results_{args.seat}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
