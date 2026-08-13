"""SIM-001 MULL-006 section 2 — fetch-target branching impact validation.

Measures, on a fresh sample, how often family 6 (alternate fetchland targets) actually changes
the best-known trajectory and the final mulligan decision, and its computational cost - required
before this project trusts TRAJECTORY_MACHINE_R (now implicitly TRAJECTORY_MACHINE_006, same code,
corrected search) as MULL-006's reference evaluator for every subsequent contextual dimension.
"""
import json
import random
import time
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better, find_best_trajectory
from trajectory_grading import grade_trajectory, TIER_ORDER

REPO_ROOT = Path(__file__).resolve().parents[2]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}


def _keep_threshold_7():
    path = REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json"
    data = json.loads(path.read_text())
    return data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]["7"]["keep_at_or_above_tier"]


def _best_without_fetch_family(hand, library, on_play, cards, combos):
    """Same search as find_best_trajectory, but skipping every fetch:* candidate - the PRE-
    MULL-006 search behavior, reimplemented here (not by mutating production code) purely to
    measure the delta this validation exists to report."""
    state, m1, m2, m3 = _simulate(hand, library, on_play, cards, combos)
    best = grade_trajectory(state, cards, m1, m2, m3)
    best["search_label"] = "greedy"
    tried = 1
    for label, kwargs in _candidate_configs(hand, library, cards):
        if label.startswith("fetch:"):
            continue
        tried += 1
        state_t, m1_t, m2_t, m3_t = _simulate(hand, library, on_play, cards, combos, **kwargs)
        grade_t = grade_trajectory(state_t, cards, m1_t, m2_t, m3_t)
        grade_t["search_label"] = label
        if _better(grade_t, best):
            best = grade_t
    return best, tried


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=6001)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)
    keep_tier = _keep_threshold_7()

    changed_tier = 0
    changed_decision = 0
    hands_with_fetch_candidates = 0
    total_tried_with = 0
    total_tried_without = 0
    examples = []

    t0 = time.time()
    for i in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]

        has_fetch_candidate = any(
            label.startswith("fetch:") for label, kwargs in _candidate_configs(hand, library, cards)
        )
        without, tried_without = _best_without_fetch_family(hand, library, on_play, cards, combos)
        _, with_fetch, tried_with = find_best_trajectory(hand, library, on_play, cards, combos)
        total_tried_with += tried_with
        total_tried_without += tried_without

        if has_fetch_candidate:
            hands_with_fetch_candidates += 1

        tier_changed = with_fetch["tier"] != without["tier"] or with_fetch["tier_engine"] != without["tier_engine"]
        if tier_changed:
            changed_tier += 1
            decision_before = TIER_RANK[without["tier"]] <= TIER_RANK[keep_tier]
            decision_after = TIER_RANK[with_fetch["tier"]] <= TIER_RANK[keep_tier]
            if decision_before != decision_after:
                changed_decision += 1
                if len(examples) < 20:
                    examples.append({
                        "hand": sorted(hand),
                        "tier_before": without["tier"], "tier_engine_before": without["tier_engine"],
                        "tier_after": with_fetch["tier"], "tier_engine_after": with_fetch["tier_engine"],
                        "search_label_after": with_fetch["search_label"],
                        "decision_before": "KEEP" if decision_before else "MULLIGAN",
                        "decision_after": "KEEP" if decision_after else "MULLIGAN",
                    })
    elapsed = time.time() - t0

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_FETCH_BRANCHING_VALIDATION",
        "evidence_type": "SIMULATION_MEASURED",
        "sample_count": args.count, "seed": args.seed, "seat": args.seat,
        "keep_tier_threshold_size7": keep_tier,
        "hands_with_at_least_one_fetch_candidate": hands_with_fetch_candidates,
        "hands_with_fetch_candidate_rate": round(hands_with_fetch_candidates / args.count, 4),
        "best_trajectory_changed_count": changed_tier,
        "best_trajectory_changed_rate": round(changed_tier / args.count, 4),
        "best_trajectory_changed_rate_among_hands_with_fetch_candidates": (
            round(changed_tier / hands_with_fetch_candidates, 4) if hands_with_fetch_candidates else None
        ),
        "mulligan_decision_changed_count": changed_decision,
        "mulligan_decision_changed_rate": round(changed_decision / args.count, 4),
        "computational_cost": {
            "elapsed_seconds_total": elapsed,
            "avg_candidates_tried_with_fetch_family": round(total_tried_with / args.count, 3),
            "avg_candidates_tried_without_fetch_family": round(total_tried_without / args.count, 3),
            "avg_extra_candidates_from_fetch_family": round((total_tried_with - total_tried_without) / args.count, 3),
        },
        "remaining_bounded_search_limitations": [
            "Family 6 only branches ONE fetch's target at a time per candidate, holding every "
            "other turn's land/fetch/tutor choice at the greedy default - NOT the full joint "
            "combination across multiple fetches in the same hand (BOUNDED_SEARCH_LOWER_BOUND).",
            "Family 6 only considers fetches actually present in the OPENING HAND, not a fetch "
            "drawn on a later turn within the T1-T3 window.",
            "The search still does not explore Kinnan/Cradle/other mana-doubling interactions "
            "jointly with fetch-target choice.",
            "No other bounded family (tutor targets, Pod/Survival activations, battlefield "
            "tutors) has yet been cross-branched WITH fetch-target alternatives in the same "
            "candidate (each family is still independent, not a joint product search).",
        ],
        "example_decision_flips": examples,
        "note": (
            "'best_trajectory_changed' compares (tier, tier_engine) with vs without family 6; a "
            "changed mulligan DECISION additionally requires crossing the keep/ship threshold at "
            "hand size 7 (mull005r_hand_size_thresholds.json, cost=1.0) - most tier changes do not "
            "cross that specific boundary, so the decision-changed rate is expected to be smaller "
            "than the trajectory-changed rate."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "fetch_branching_validation.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"hands_with_fetch_candidates: {hands_with_fetch_candidates}/{args.count}")
    print(f"best_trajectory_changed: {changed_tier}/{args.count} ({result['best_trajectory_changed_rate']:.4f})")
    print(f"mulligan_decision_changed: {changed_decision}/{args.count} ({result['mulligan_decision_changed_rate']:.4f})")
    print(f"elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
