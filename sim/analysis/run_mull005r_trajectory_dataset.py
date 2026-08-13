"""SIM-001 MULL-005R section 19 — corrected trajectory-tagged opening-hand dataset generator.

Thin wrapper over run_mull005_trajectory_dataset.run_one_hand: the underlying engine
(trajectory_search.find_best_trajectory, trajectory_grading.grade_trajectory,
opening_hand_policy.develop_turn) IS the MULL-005R-corrected engine as of this phase - every
finding in t1_t3_trajectory_audit.json (Oculus/Pod/Survival/Tithe/Mana-Vault/dork/Kinnan/tutor-
search/commander-credit/agency/premium-one-drop/combo-proximity/engine-realization corrections)
is already live in those modules and covered by the MULL-005R regression gate
(mull005r_regression_gate.json, GATE STATUS: OPEN_FOR_PRODUCTION_RERUN) BEFORE this script runs.
This is not a re-implementation - it is the required large-scale rerun the assignment's own
ordering constraint gated on that regression gate being green.

Per assignment section 19: rerun the London mulligan simulation and dataset generation with the
corrected engine, NOT merely rescore MULL-005's old hands - a materially different, freshly-dealt
sample is used here (a different seed from MULL-005's mull005_trajectory_dataset_*.jsonl.gz), so
every downstream MULL-005R analysis (census, policy fits, hand-size derivation) is built on hands
the corrected engine actually played out, not old hands re-labeled.
"""
import gzip
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from run_mull005_trajectory_dataset import run_one_hand

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=15000)
    ap.add_argument("--seed", type=int, default=1005)  # distinct from MULL-005's seed=42
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)

    out_path = Path(args.out) if args.out else (
        REPO_ROOT / "results" / "solo_baseline" / f"mull005r_trajectory_dataset_{args.seat}.jsonl.gz"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        for i in range(args.count):
            row = run_one_hand(names, rng, cards, combos, on_play)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if (i + 1) % 2000 == 0:
                elapsed = time.time() - t0
                print(f"  {i + 1}/{args.count} ({(i + 1) / elapsed:.1f} hands/sec)", file=sys.stderr)
    elapsed = time.time() - t0

    summary = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_005R_TRAJECTORY_DATASET_CORRECTED",
        "regression_gate": "results/solo_baseline/mull005r_regression_gate.json (OPEN_FOR_PRODUCTION_RERUN, verified before this run)",
        "sample_count": args.count,
        "seed": args.seed,
        "seat": args.seat,
        "on_play": on_play,
        "elapsed_seconds": elapsed,
        "hands_per_second": args.count / elapsed,
        "dataset_file": str(out_path),
    }
    summary_path = Path(str(out_path).replace(".jsonl.gz", ".summary.json"))
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({args.count} hands in {elapsed:.1f}s, {args.count / elapsed:.1f} hands/sec)")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
