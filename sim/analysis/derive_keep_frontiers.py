"""SIM-001 SOLO-004 section 7 — machine-optimal keep frontiers per hand size.

Per the spec's own framing: "A mediocre 7 is not being compared with an ideal 6. It is being
compared with the DISTRIBUTION of outcomes obtained by mulliganing to 6." Operationalized here as:

  keep THIS 7 iff value(this 7) >= baseline(6)
  keep-and-bottom-to-6 (i.e. accept the mulligan-to-6 hand) iff value(bottomed-to-6) >= baseline(5)
  keep-and-bottom-to-5 iff value(bottomed-to-5) >= baseline(4)

where baseline(N) is the expected value of a FRESH random 7, optimally bottomed down to N cards
(reusing bottoming_search.py's exhaustive search) - i.e. "what mulliganing actually gets you," not
an idealized hand. Recursion note (disclosed simplification): baseline(N) here is the UNCONDITIONAL
population-average optimally-bottomed value at that size, not the value conditional on the
policy's own keep threshold at that level (a fully self-consistent fixed point, which section 7
allows skipping - "derive these recursively WHERE PRACTICAL" - would need each baseline computed
only over hands the policy would actually accept at that level, a further refinement left to the
full London mulligan simulation in task 57, which validates/corrects this first-order estimate
empirically rather than analytically).

Profile-aware: baselines and thresholds are computed for each of the five SOLO-004 objective
profiles separately, so the reader can see whether/how much the "right" aggression level shifts
depending on what's being optimized for.
"""
import argparse
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_policy import _is_land
from define_value_profiles import PROFILES, balanced

REPO_ROOT = Path(__file__).resolve().parents[2]
ALL_PROFILES = {**PROFILES, "BALANCED": balanced}


def sample_baselines(count, seed, seat, cards, combos):
    """For a sample of fresh 7s, computes: value if kept as-is (n_bottom=0), and best value if
    optimally bottomed to 6/5/4 (n_bottom=1/2/3) - under EVERY profile at once (each hand only
    needs to be simulated once per bottom combo; profile scores are all derived from the same
    outcome row)."""
    names = list(cards.keys())
    on_play = seat == "play"
    rng = random.Random(seed)

    sums = {p: {"kept7": 0.0, "best6": 0.0, "best5": 0.0, "best4": 0.0} for p in ALL_PROFILES}
    n = 0
    for _ in range(count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        n += 1

        from run_solo004_dataset import simulate_hand_outcome
        kept7_row = simulate_hand_outcome(hand, library, on_play, cards, combos)
        for profile_name, fn in ALL_PROFILES.items():
            score, _ = fn(kept7_row)
            sums[profile_name]["kept7"] += score

        _, all_results_1 = _run_and_cache(hand, library, on_play, cards, combos, 1)
        _, all_results_2 = _run_and_cache(hand, library, on_play, cards, combos, 2)
        _, all_results_3 = _run_and_cache(hand, library, on_play, cards, combos, 3)
        for profile_name in ALL_PROFILES:
            sums[profile_name]["best6"] += max(s[profile_name] for _, s in all_results_1)
            sums[profile_name]["best5"] += max(s[profile_name] for _, s in all_results_2)
            sums[profile_name]["best4"] += max(s[profile_name] for _, s in all_results_3)

    return {p: {k: v / n for k, v in d.items()} for p, d in sums.items()}, n


def _run_and_cache(hand, library, on_play, cards, combos, n_bottom):
    """Runs the exhaustive bottom search ONCE per (hand, n_bottom), scoring EVERY profile for
    each candidate combo in the same pass (avoids re-simulating T1-T3 per profile)."""
    import itertools
    from run_solo004_dataset import simulate_hand_outcome
    results = []
    for bottomed in itertools.combinations(hand, n_bottom):
        remaining = [c for c in hand if c not in bottomed]
        new_library = list(library) + list(bottomed)
        row = simulate_hand_outcome(remaining, new_library, on_play, cards, combos)
        scores = {}
        for profile_name, fn in ALL_PROFILES.items():
            scores[profile_name], _ = fn(row)
        results.append((bottomed, scores))
    best = max(results, key=lambda r: r[1]["BALANCED"])
    return best, results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1500, help="sample size (each hand costs 1+7+21+35=64 sims)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_keep_thresholds_by_hand_size.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()

    baselines, n = sample_baselines(args.count, args.seed, args.seat, cards, combos)

    result = {**deck_provenance_fields(payload), "sample_count": n, "seed": args.seed, "seat": args.seat, "profiles": {}}
    for profile_name, b in baselines.items():
        result["profiles"][profile_name] = {
            "baseline_kept_as_dealt_7": b["kept7"],
            "baseline_optimally_bottomed_6": b["best6"],
            "baseline_optimally_bottomed_5": b["best5"],
            "baseline_optimally_bottomed_4": b["best4"],
            "keep_threshold_at_7": b["best6"],
            "keep_threshold_at_6_after_bottoming": b["best5"],
            "keep_threshold_at_5_after_bottoming": b["best4"],
        }
        print(f"\n{profile_name}:")
        print(f"  E[value | kept as dealt 7]        = {b['kept7']:.4f}")
        print(f"  E[value | optimally bottomed to 6] = {b['best6']:.4f}  <- keep-at-7 threshold")
        print(f"  E[value | optimally bottomed to 5] = {b['best5']:.4f}  <- keep-at-6 threshold")
        print(f"  E[value | optimally bottomed to 4] = {b['best4']:.4f}  <- keep-at-5 threshold")
        gap76 = b["kept7"] - b["best6"]
        print(f"  Average 7 vs average mulligan-to-6: {gap76:+.4f} "
              f"({'keeping an average 7 beats mulliganing' if gap76 > 0 else 'mulliganing beats an average 7'})")

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
