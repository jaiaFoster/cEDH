"""SIM-001 MULL-005R section 20 — re-derived hand-size-specific trajectory thresholds (7/6/5/4).

Thin wrapper over derive_hand_size_trajectory_thresholds.run_for_size/derive_thresholds: the
underlying engine (trajectory_grading.grade_trajectory via _grade_greedy) is already the
MULL-005R-corrected one, gated on the regression gate (mull005r_regression_gate.json,
OPEN_FOR_PRODUCTION_RERUN). This is the required TEST (not hard-code) of the assignment's stated
hand-size hypotheses:
  7 - "genuinely powerful T1/T2 destination"
  6 - "slightly weaker but coherent"
  5 - "a real secondary T2 engine such as Archivist may be enough"
  4 - "stop chasing perfection, prioritize coherence"
against the corrected engine's actual tier distributions, not an assumption carried over from
MULL-005 unchanged - a materially different sample (fresh seed) from MULL-005's original run.
"""
import json
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from derive_hand_size_trajectory_thresholds import run_for_size, derive_thresholds, MULLIGAN_CARD_COST_SENSITIVITY, TIER_VALUE

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1007)  # distinct from MULL-005's seed=42
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--count7", type=int, default=4000)
    ap.add_argument("--count6", type=int, default=3000)
    ap.add_argument("--count5", type=int, default=1500)
    ap.add_argument("--count4", type=int, default=500)
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json"))
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
        "phase": "SIM_001_MULL_005R_HAND_SIZE_THRESHOLDS_CORRECTED",
        "regression_gate": "results/solo_baseline/mull005r_regression_gate.json (OPEN_FOR_PRODUCTION_RERUN, verified before this run)",
        "seat": args.seat,
        "seed": args.seed,
        "tier_value_scale": TIER_VALUE,
        "by_hand_size": by_size,
        "keep_thresholds_by_assumed_mulligan_card_cost": thresholds_by_cost,
        "note": (
            "Grading uses the greedy DEFAULT_PRIORITY line only (not the bounded tutor-target "
            "search) - see derive_hand_size_trajectory_thresholds.py's module docstring for the "
            "tractability tradeoff. Thresholds are ordinal (computed on TIER_VALUE, a disclosed "
            "monotone scale, not fit to any target). The assumed-mulligan-card-cost sensitivity "
            "sweep exists because this simulator has no full-game/4-player data to derive a "
            "single real cost-of-mulligan from - see that module's 'IMPORTANT LIMITATION'. "
            "cost=0.0 is the raw, uncorrected comparison and is expected to look mulligan-"
            "favorable; it is reported for transparency, not as guidance."
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
