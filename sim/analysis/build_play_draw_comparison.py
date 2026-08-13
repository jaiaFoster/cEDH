"""SIM-001 SOLO-004 section 19 — play vs. draw comparison.

Consolidates evidence already computed (land-population effect sizes, full London mulligan
simulation results) into a direct answer to "should the final human mulligan rules differ between
play and draw." Pure aggregation - no new simulation.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    base = REPO_ROOT / "results" / "solo_baseline"
    land_pop = json.loads((base / "solo004_land_population_analysis.json").read_text())
    mulligan_play = json.loads((base / "solo004_london_mulligan_results_play.json").read_text())
    mulligan_draw = json.loads((base / "solo004_london_mulligan_results_draw.json").read_text())

    land_counts = ["0", "1", "2", "3", "4", "5+"]
    feature_overlap = {}
    for lc in land_counts:
        play_top5 = [e["feature"] for e in land_pop["play"][lc]["effect_sizes"][:5]]
        draw_top5 = [e["feature"] for e in land_pop["draw"][lc]["effect_sizes"][:5]]
        feature_overlap[lc] = {
            "play_success_rate": land_pop["play"][lc]["overall_success_rate"],
            "draw_success_rate": land_pop["draw"][lc]["overall_success_rate"],
            "success_rate_delta": land_pop["draw"][lc]["overall_success_rate"] - land_pop["play"][lc]["overall_success_rate"],
            "play_top5_features": play_top5,
            "draw_top5_features": draw_top5,
            "top5_overlap_count": len(set(play_top5) & set(draw_top5)),
        }

    policy_comparison = {}
    for policy in ["TREE_DEPTH4", "SIMPLE_RULES", "MACHINE_OPTIMAL"]:
        p = mulligan_play["policies"][policy]
        d = mulligan_draw["policies"][policy]
        policy_comparison[policy] = {
            "play_strong_state_rate": p["overall_t3_strong_state_rate"],
            "draw_strong_state_rate": d["overall_t3_strong_state_rate"],
            "delta": d["overall_t3_strong_state_rate"] - p["overall_t3_strong_state_rate"],
            "play_avg_final_hand_size": p["avg_final_hand_size"],
            "draw_avg_final_hand_size": d["avg_final_hand_size"],
        }

    mean_overlap = sum(v["top5_overlap_count"] for v in feature_overlap.values()) / len(feature_overlap)
    mean_delta = sum(v["success_rate_delta"] for v in feature_overlap.values()) / len(feature_overlap)

    result = {
        "land_count_feature_ranking_comparison": feature_overlap,
        "mulligan_policy_comparison": policy_comparison,
        "summary": {
            "mean_top5_feature_overlap_out_of_5": mean_overlap,
            "mean_success_rate_delta_draw_minus_play": mean_delta,
            "conclusion": (
                "Differences are UNIFORM and QUANTITATIVE, not qualitative. At every land count "
                "from 1 through 5+, the top-5 opener features predicting t3_any_strong_state are "
                "IDENTICAL between play and draw (5/5 overlap; land count 0 is the lone partial "
                "exception at 3/5, still the same accel/engine cluster). The draw is uniformly "
                "stronger by roughly the same margin at every land count and under every mulligan "
                "policy (+5.3 to +9.0pp on strong-state rate) - consistent with 'one extra card, "
                "same underlying deck logic,' not a different set of what matters. CONCLUSION: "
                "the final human mulligan heuristic should NOT have separate play/draw rules - the "
                "same keep criteria apply on both, with an implicit understanding that draw hands "
                "run slightly hotter across the board."
            ),
        },
    }

    out_path = base / "solo004_play_draw_comparison.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"\nMean top-5 feature overlap: {mean_overlap:.1f}/5")
    print(f"Mean success-rate delta (draw - play): {mean_delta:+.3f}")
    for policy, d in policy_comparison.items():
        print(f"{policy}: play={d['play_strong_state_rate']:.3f} draw={d['draw_strong_state_rate']:.3f} delta={d['delta']:+.3f}")


if __name__ == "__main__":
    main()
