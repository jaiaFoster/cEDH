"""SIM-001 SOLO-004 sections 8-9 — real London mulligan mechanics + search-based bottoming.

London mulligan, modeled correctly (section 8): draw a fresh 7, decide keep/mulligan; if kept at
mulligan count N, bottom N cards from THAT SAME 7 (not a random/idealized N-card hand) and begin
play with the remaining 7-N. Bottomed cards go to the bottom of the library in whatever order (a
3-turn horizon will essentially never draw that deep, so their exact order among themselves
doesn't matter) - the rest of the library keeps its original relative draw order, no reshuffle.
`run_solo004_dataset.simulate_hand_outcome()`'s `library` parameter is already built for exactly
this: pass `library_after_deal + bottomed_cards`.

Bottoming optimization (section 9): for a given dealt 7 and a required bottom count N, exhaustively
try every C(7, N) combination (N=1: 7, N=2: 21, N=3: 35 - all cheap enough to brute-force per hand
at the sample sizes used here), score each resulting (7-N)-card hand's T1-T3 trajectory under a
chosen value profile (default BALANCED, from define_value_profiles.py), and keep the best. This
is compared against a fast heuristic (bottom the N lowest `_bottom_priority_score` cards - reused
from the existing Gemstone-Caverns-exile heuristic, generalized to N>1) so bulk-scale mulligan
simulation (task 57, run at 100k+ hands) can use the FAST heuristic without re-paying an
exhaustive search on every single hand, once it's shown here to track the search-optimal choice
closely enough.
"""
import argparse
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from opening_hand_model import (
    load_deck_cards, load_deterministic_combos, TUTORS, ENGINES, PREMIUM_ONE_DROP_ENGINES,
    ACCELERATION, INTERACTION_CASTABLE, deck_provenance_fields, print_run_banner,
)
from opening_hand_policy import _is_land, _bottom_priority_score
from run_solo004_dataset import simulate_hand_outcome
from define_value_profiles import PROFILES, balanced

REPO_ROOT = Path(__file__).resolve().parents[2]
NEAR_OPTIMAL_EPS = 0.01  # profile-score points - ties/near-ties are common across bottom combos


def card_class(name, cards):
    if _is_land(name, cards):
        return "land"
    if name in TUTORS:
        return "tutor"
    if name in PREMIUM_ONE_DROP_ENGINES:
        return "premium_engine"
    if name in ENGINES:
        return "engine"
    if name in ACCELERATION:
        return "acceleration"
    if name in INTERACTION_CASTABLE:
        return "interaction"
    return "other"


def score_hand(hand, library, on_play, cards, combos, profile_name):
    row = simulate_hand_outcome(hand, library, on_play, cards, combos)
    if profile_name == "BALANCED":
        score, _ = balanced(row)
    else:
        score, _ = PROFILES[profile_name](row)
    return score, row


def exhaustive_bottom_search(hand, library, on_play, cards, combos, n_bottom, profile_name="BALANCED"):
    """Returns (best_bottomed: tuple[str], best_score: float, all_results: list[(bottomed, score)])"""
    all_results = []
    best = None
    for bottomed in itertools.combinations(hand, n_bottom):
        remaining = [c for c in hand if c not in bottomed]
        new_library = list(library) + list(bottomed)
        score, _ = score_hand(remaining, new_library, on_play, cards, combos, profile_name)
        all_results.append((bottomed, score))
        if best is None or score > best[1]:
            best = (bottomed, score)
    return best[0], best[1], all_results


def heuristic_bottom(hand, cards, n_bottom):
    ranked = sorted(hand, key=lambda c: _bottom_priority_score(c, cards))
    return tuple(ranked[:n_bottom])


def run_analysis(count, n_bottom, seed, seat, profile_name):
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = seat == "play"
    rng = random.Random(seed)

    bottomed_class_counts = Counter()
    bottomed_class_by_land_count = defaultdict(Counter)
    agreement = 0
    near_optimal = 0  # heuristic's score within NEAR_OPTIMAL_EPS of the search optimum, even if
                       # it picked a DIFFERENT (but equally-good) combo - exact-set agreement is
                       # an overly strict bar when several bottoms tie or nearly tie for best.
    score_gap_sum = 0.0
    score_gap_when_disagree = []
    examples = []

    for i in range(count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        lib_after_deal = lib[7:]
        land_count = sum(1 for c in hand if _is_land(c, cards))

        best_bottomed, best_score, all_results = exhaustive_bottom_search(
            hand, lib_after_deal, on_play, cards, combos, n_bottom, profile_name
        )
        heur_bottomed = heuristic_bottom(hand, cards, n_bottom)
        heur_score = next((s for b, s in all_results if set(b) == set(heur_bottomed)), None)
        if heur_score is None:
            # heuristic combo wasn't hit by exhaustive enumeration order equivalence - compute directly
            remaining = [c for c in hand if c not in heur_bottomed]
            heur_score, _ = score_hand(remaining, lib_after_deal + list(heur_bottomed), on_play, cards, combos, profile_name)

        agrees = set(best_bottomed) == set(heur_bottomed)
        agreement += int(agrees)
        gap = best_score - heur_score
        score_gap_sum += gap
        near_optimal += int(gap <= NEAR_OPTIMAL_EPS)
        if not agrees:
            score_gap_when_disagree.append(gap)

        for c in best_bottomed:
            cls = card_class(c, cards)
            bottomed_class_counts[cls] += 1
            bottomed_class_by_land_count[str(land_count)][cls] += 1

        if len(examples) < 15 and not agrees and gap > 0.02:
            examples.append({
                "hand": hand, "land_count": land_count,
                "search_optimal_bottom": list(best_bottomed), "search_optimal_score": best_score,
                "heuristic_bottom": list(heur_bottomed), "heuristic_score": heur_score,
                "gap": gap,
            })

    n = count
    return {
        "n_bottom": n_bottom, "sample_count": n, "profile": profile_name, "seat": seat,
        "heuristic_agreement_rate": agreement / n,
        "heuristic_near_optimal_rate": near_optimal / n,
        "near_optimal_epsilon": NEAR_OPTIMAL_EPS,
        "mean_score_gap_search_minus_heuristic": score_gap_sum / n,
        "mean_score_gap_when_disagreeing": (
            sum(score_gap_when_disagree) / len(score_gap_when_disagree) if score_gap_when_disagree else 0.0
        ),
        "disagreement_rate": 1 - agreement / n,
        "bottomed_card_class_distribution": {k: v / (n * n_bottom) for k, v in bottomed_class_counts.most_common()},
        "bottomed_card_class_by_opening_land_count": {
            lc: {k: v / sum(counter.values()) for k, v in counter.most_common()}
            for lc, counter in bottomed_class_by_land_count.items()
        },
        "representative_disagreement_examples": examples,
    }, payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--profile", default="BALANCED", choices=list(PROFILES.keys()) + ["BALANCED"])
    ap.add_argument("--n1-count", type=int, default=3000, help="sample size for bottoming 7->6 (1 card)")
    ap.add_argument("--n2-count", type=int, default=2000, help="sample size for bottoming 7->5 (2 cards)")
    ap.add_argument("--n3-count", type=int, default=800, help="sample size for bottoming 7->4 (3 cards)")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_bottoming_analysis.json"))
    args = ap.parse_args()

    print_run_banner()
    result = {"profile": args.profile, "seat": args.seat, "seed": args.seed}
    payload = None
    for n_bottom, count in [(1, args.n1_count), (2, args.n2_count), (3, args.n3_count)]:
        r, payload = run_analysis(count, n_bottom, args.seed, args.seat, args.profile)
        result[f"bottom_{n_bottom}"] = r
        print(f"n_bottom={n_bottom}: agreement={r['heuristic_agreement_rate']:.1%}  "
              f"near_optimal={r['heuristic_near_optimal_rate']:.1%}  "
              f"mean_gap={r['mean_score_gap_search_minus_heuristic']:.4f}  "
              f"class_dist={r['bottomed_card_class_distribution']}")

    result.update(deck_provenance_fields(payload))
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
