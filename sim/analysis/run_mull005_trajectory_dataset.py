"""SIM-001 MULL-005 section 7 — trajectory-tagged opening-hand dataset generator.

For each random seven, joins:
  - the SAME opener-visible-only feature set and SOLO-004 greedy-realized multi-objective outcome
    vector as solo004_opening_hand_dataset_*.jsonl.gz (reused verbatim via
    run_solo004_dataset.simulate_hand_outcome - not rebuilt), so every downstream MULL-005 analysis
    can still ask SOLO-004's questions unchanged;
  - trajectory_greedy__* - the SAME single greedy DEFAULT_PRIORITY line, graded by
    trajectory_grading.grade_trajectory (tier/mechanism/resource_cost) - the pre-MULL-005 baseline;
  - trajectory_best__* - trajectory_search.find_best_trajectory's bounded best-known trajectory
    (tutor-target x priority-order search), the trajectory-first equivalent of SOLO-004's
    best_known_achievable. Kept strictly separate from trajectory_greedy__* per the assignment's
    explicit constraint never to conflate the two.

Bounded search only actually branches when the hand holds a tutor (see trajectory_search.py), so
cost sits in the same class as SOLO-004's --achievable pass, not 100k-hand-dataset territory -
matching that precedent's use of a smaller sample size for the search-bearing dataset.
"""
import argparse
import gzip
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from run_solo004_dataset import simulate_hand_outcome
from trajectory_search import find_best_trajectory

REPO_ROOT = Path(__file__).resolve().parents[2]


def _flatten_grade(prefix, grade):
    out = {
        f"{prefix}__tier": grade["tier"],
        f"{prefix}__tier_engine": grade["tier_engine"],
        f"{prefix}__tier_turn": grade["tier_turn"],
        f"{prefix}__mechanism": grade["mechanism"],
    }
    out.update({f"{prefix}__cost_{k}": v for k, v in grade["resource_cost"].items()})
    if "search_label" in grade:
        out[f"{prefix}__search_label"] = grade["search_label"]
    return out


def run_one_hand(names, rng, cards, combos, on_play):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    lib_after_deal = lib[7:]

    row = simulate_hand_outcome(hand, lib_after_deal, on_play, cards, combos, run_achievable=False)

    greedy_grade, best_grade, tried = find_best_trajectory(hand, lib_after_deal, on_play, cards, combos)
    row.update(_flatten_grade("trajectory_greedy", greedy_grade))
    row.update(_flatten_grade("trajectory_best", best_grade))
    row["trajectory_candidates_tried"] = tried
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=15000)
    ap.add_argument("--seed", type=int, default=42)
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
        REPO_ROOT / "results" / "solo_baseline" / f"mull005_trajectory_dataset_{args.seat}.jsonl.gz"
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
        "phase": "SIM_001_MULL_005_TRAJECTORY_DATASET",
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
