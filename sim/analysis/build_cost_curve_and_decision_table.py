"""SIM-001 SOLO-004 sections 13-14 — mulligan cost curve + keep-7 decision table.

Consolidates results already computed by run_london_mulligan_sim.py (the "how expensive is one
more mulligan" curve, by mulligan count reached) and land_population/conditional_outcomes
analyses (the keep-7 decision table by common structural hand type) into the exact requested
report shapes, for all seats/policies at once - no new simulation, pure aggregation/formatting.
"""
import argparse
import json
from pathlib import Path

from analyze_land_populations import load_rows

REPO_ROOT = Path(__file__).resolve().parents[2]

STRUCTURES = [
    ("1 land + T1 persistent acceleration", 1, lambda r: r["opener__t1_accel_executable_now"]),
    ("1 land + temporary acceleration only", 1, lambda r: (
        r["opener__has_one_shot_accel_card"] and not r["opener__has_noncreature_persistent_accel_card"]
    )),
    ("1 land, no acceleration", 1, lambda r: not r["opener__has_any_accel_card"]),
    ("2 lands + premium engine", 2, lambda r: r["opener__has_premium_one_drop_card"]),
    ("2 lands + dork/rock (2+ accel)", 2, lambda r: r["opener__accel_card_count"] >= 2),
    ("2 lands + tutor (no engine)", 2, lambda r: r["opener__has_tutor_card"] and not r["opener__has_any_engine_card"]),
    ("2 lands + interaction-heavy (2+)", 2, lambda r: r["opener__interaction_density_2plus"]),
    ("2 lands, no T1/T2 development", 2, lambda r: not r["opener__has_any_engine_card"] and not r["opener__has_any_accel_card"]),
    ("3 lands + engine", 3, lambda r: r["opener__has_any_engine_card"]),
    ("3 lands + acceleration", 3, lambda r: r["opener__has_any_accel_card"]),
    ("3 lands, weak business", 3, lambda r: (
        not r["opener__has_any_engine_card"] and not r["opener__has_tutor_card"] and not r["opener__has_any_accel_card"]
    )),
    ("4+ lands + premium engine", None, lambda r: r["opening_hand_land_count"] >= 4 and r["opener__has_premium_one_drop_card"]),
    ("4+ lands, no premium development", None, lambda r: (
        r["opening_hand_land_count"] >= 4 and not r["opener__has_premium_one_drop_card"]
    )),
]


def keep_7_decision_table(rows):
    n_total = len(rows)
    table = []
    for label, lc, pred in STRUCTURES:
        base = [r for r in rows if lc is None or r["opening_hand_land_count"] == lc]
        matched = [r for r in base if pred(r)]
        if not matched:
            continue
        n = len(matched)
        strong_state_rate = sum(1 for r in matched if r["out_t3__t3_any_strong_state"]) / n
        table.append({
            "structure": label,
            "frequency_pct_of_population": n / n_total,
            "n": n,
            "t3_strong_state_rate": strong_state_rate,
            "recommendation": (
                "snap keep" if strong_state_rate >= 0.65 else
                "keep" if strong_state_rate >= 0.50 else
                "conditional / lean ship" if strong_state_rate >= 0.35 else
                "usually ship"
            ),
            "confidence": "high" if n >= 500 else "moderate" if n >= 100 else "low (small sample)",
        })
    return table


def mulligan_cost_curve(mulligan_results):
    out = {}
    for policy, data in mulligan_results["policies"].items():
        if not isinstance(data, dict) or "by_mulligan_count" not in data:
            continue
        rows = []
        for bucket, label in [("0", "Kept 7"), ("1", "Kept 6"), ("2", "Kept 5"), ("3+", "Kept 4-or-fewer")]:
            b = data["by_mulligan_count"].get(bucket)
            if b is None:
                continue
            rows.append({
                "starting_hand": label,
                "probability_reached": b["pct_of_population"],
                "t2_engine_rate": b["t2_engine_rate"],
                "t3_strong_state_rate": b["t3_strong_state_rate"],
                "t3_stalled_rate": b["t3_stalled_rate"],
                "mean_cards_remaining_t3": b["mean_cards_remaining_t3"],
            })
        out[policy] = rows
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-dataset", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_play.jsonl.gz"))
    ap.add_argument("--play-mulligan", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_london_mulligan_results_play.json"))
    ap.add_argument("--draw-mulligan", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_london_mulligan_results_draw.json"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_mulligan_cost_curve.json"))
    args = ap.parse_args()

    rows = load_rows(args.play_dataset)
    decision_table = keep_7_decision_table(rows)

    result = {"keep_7_decision_table": decision_table, "mulligan_cost_curve": {}}
    for seat, path in [("play", args.play_mulligan), ("draw", args.draw_mulligan)]:
        p = Path(path)
        if p.exists():
            result["mulligan_cost_curve"][seat] = mulligan_cost_curve(json.loads(p.read_text()))

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")

    print("\n=== Keep-7 decision table (play) ===")
    for row in sorted(decision_table, key=lambda r: -r["t3_strong_state_rate"]):
        print(f"  {row['structure']:38s} freq={row['frequency_pct_of_population']:.1%}  "
              f"strong_state={row['t3_strong_state_rate']:.1%}  -> {row['recommendation']:22s} "
              f"({row['confidence']})")

    for seat in result["mulligan_cost_curve"]:
        print(f"\n=== Mulligan cost curve ({seat}) ===")
        for policy, rows_ in result["mulligan_cost_curve"][seat].items():
            print(f"\n{policy}:")
            for r in rows_:
                print(f"  {r['starting_hand']:18s} P={r['probability_reached']:.1%}  "
                      f"T2eng={r['t2_engine_rate']:.1%}  T3strong={r['t3_strong_state_rate']:.1%}  "
                      f"T3stalled={r['t3_stalled_rate']:.1%}  cards_left={r['mean_cards_remaining_t3']:.2f}")


if __name__ == "__main__":
    main()
