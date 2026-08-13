"""SIM-001 SOLO-002R rerun protocol Part B — policy_realized vs. best_known_achievable.

Run at a deliberately smaller sample than the main 100k Part A census: this search explores up
to MAX_LINES (12) alternative development lines per hand instead of one, so its cost per hand is
roughly an order of magnitude higher. Disclosed scope reduction, not a silent shortcut - see
achievable_search.py's module docstring for exactly what is and isn't covered by the bounded
search.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from achievable_search import compute_policy_realized_and_best_known_achievable, TARGETS

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--on-play", action="store_true", default=True)
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo002r_achievable_search.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    rng = random.Random(args.seed)

    realized_counts = {k: 0 for k in TARGETS}
    achievable_counts = {k: 0 for k in TARGETS}
    lines_total = 0

    t0 = time.time()
    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        lib = lib[7:]
        pr, bka, n_lines = compute_policy_realized_and_best_known_achievable(hand, lib, args.on_play, cards, combos)
        lines_total += n_lines
        for k in TARGETS:
            if pr[k]:
                realized_counts[k] += 1
            if bka[k]:
                achievable_counts[k] += 1
    elapsed = time.time() - t0

    n = args.count
    comparison = {
        k: {
            "policy_realized_rate": realized_counts[k] / n,
            "best_known_achievable_rate": achievable_counts[k] / n,
            "gap": (achievable_counts[k] - realized_counts[k]) / n,
        }
        for k in TARGETS
    }

    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_002R_ACHIEVABLE_SEARCH",
        "sample_count": n,
        "seed": args.seed,
        "on_play": args.on_play,
        "avg_lines_explored_per_hand": lines_total / n,
        "search_bound_max_lines": 12,
        "elapsed_seconds": elapsed,
        "comparison": comparison,
        "note": (
            "A hand should not be labeled incapable merely because the greedy policy chose "
            "another legal line. 'gap' = how often the bounded search found the target state "
            "reachable via SOME alternative line even though the single default greedy policy "
            "line (policy_realized, same line used by the main Part A census) did not reach it. "
            "This is a lower bound on true achievability - the search is bounded (see "
            "achievable_search.py), not exhaustive."
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({n} hands, avg {lines_total/n:.1f} lines/hand, {elapsed:.1f}s)")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
