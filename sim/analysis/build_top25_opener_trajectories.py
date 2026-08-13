"""SIM-001 MULL-005R section 15 — top-25 actual opener trajectories report.

Samples fresh 7-card hands (a materially different pool from both MULL-005's dataset and the
mull005r_trajectory_dataset_*.jsonl.gz census dataset - a distinct seed), runs the corrected
bounded search (trajectory_search.find_best_trajectory) on each, and keeps every hand's full grade
+ actual card list (the flat census dataset only stores derived opener__ features, not hands
themselves, so a separate targeted sample is needed for a report that shows real cards). Selects
the top 25 by tier first, then de-duplicates near-identical examples (same tier + tier_engine +
mechanism) so the 25 are a representative SPREAD across destination families rather than 25
near-copies of the single most common S-tier line, before filling remaining slots with the next-
best distinct examples.
"""
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import find_best_trajectory

REPO_ROOT = Path(__file__).resolve().parents[2]
TIER_ORDER = ["S", "A", "B", "C", "D", "F"]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}


def _keep_thresholds():
    path = REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json"
    data = json.loads(path.read_text())
    table = data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]
    return {int(size): row["keep_at_or_above_tier"] for size, row in table.items()}


def _keeps(tier, thresholds):
    out = {}
    for size in (7, 6, 5):
        keep_tier = thresholds.get(size)
        out[f"keep_at_{size}"] = bool(keep_tier is not None and TIER_RANK[tier] <= TIER_RANK[keep_tier])
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=2025)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "top_25_opener_trajectories.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)
    thresholds = _keep_thresholds()

    sampled = []
    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        lib_after = lib[7:]
        _, best, tried = find_best_trajectory(hand, lib_after, on_play, cards, combos)
        sampled.append({"hand": hand, "grade": best, "candidates_tried": tried})

    # Sort by tier first (best first), then by having live interaction retained, then by more
    # resources retained (mana + cards in hand) as a tiebreak.
    def sort_key(s):
        g = s["grade"]
        rc = g["resource_cost"]
        return (
            TIER_RANK[g["tier"]],
            0 if g["tier_turn"] is None else g["tier_turn"],
            -int(rc["live_interaction_retained_t3"]),
            -rc["persistent_mana_remaining_t3"],
            -rc["cards_in_hand_t3"],
        )

    sampled.sort(key=sort_key)

    selected = []
    seen_buckets = set()
    # first pass: one representative per (tier, tier_engine, mechanism) bucket, best-tier first
    for s in sampled:
        g = s["grade"]
        bucket = (g["tier"], g["tier_engine"], g["mechanism"])
        if bucket in seen_buckets:
            continue
        seen_buckets.add(bucket)
        selected.append(s)
        if len(selected) == 25:
            break
    # second pass: fill any remaining slots with the next-best examples overall (allows repeat
    # buckets only if fewer than 25 distinct buckets exist in this sample).
    if len(selected) < 25:
        for s in sampled:
            if s in selected:
                continue
            selected.append(s)
            if len(selected) == 25:
                break

    report = []
    for rank, s in enumerate(selected, start=1):
        g = s["grade"]
        report.append({
            "rank": rank,
            "hand": s["hand"],
            "tier": g["tier"],
            "tier_engine": g["tier_engine"],
            "tier_turn": g["tier_turn"],
            "mechanism": g["mechanism"],
            "search_label": g.get("search_label"),
            "resource_cost": g["resource_cost"],
            "keep_recommendations": _keeps(g["tier"], thresholds),
            "candidates_tried": s["candidates_tried"],
        })

    out_path = Path(args.out)
    out_path.write_text(json.dumps({
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_005R_TOP_25_OPENER_TRAJECTORIES",
        "sample_count": args.count,
        "seed": args.seed,
        "seat": args.seat,
        "hand_size_thresholds_source": "mull005r_hand_size_thresholds.json (assumed_mulligan_card_cost=1.0)",
        "note": (
            "Selected to SPREAD across distinct (tier, tier_engine, mechanism) buckets found in "
            "this sample, best-tier-first, not literally the single 25 highest-scoring hands "
            "(which would mostly be near-duplicate S-tier premium-one-drop lines) - representative "
            "of the range of real opener trajectories this deck reaches, per assignment section 15."
        ),
        "trajectories": report,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(report)} trajectories, {args.count} hands sampled)")
    for r in report:
        print(f"  #{r['rank']:2d} {r['tier']} {r['tier_engine']!s:25s} T{r['tier_turn']} {r['mechanism']}")


if __name__ == "__main__":
    main()
