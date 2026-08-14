"""SIM-001 MULL-006 section 21 / 28 — rebuild contextual policies + rerun London mulligan sim.

Reuses the exact London mulligan mechanics already established (run_mull005_london_mulligan_sim.py:
draw a fresh 7 per attempt, decide keep/mulligan, bottom N cards on keep via
derive_hand_size_trajectory_thresholds.best_bottomed_tier - unchanged, so bottoming QUALITY stays
identical across every policy compared, only the KEEP decision differs).

FIXES A REAL GAP in the prior harness, found while building this task: run_mull005_london_mulligan_
sim.py's simulate_one_mulligan_sequence() calls keep_policy(hand, library, on_play, cards) on a
hand that is ALWAYS freshly drawn at size 7 (every mulligan attempt redraws 7 cards - the mulligan
count is never passed to the policy at all). trajectory_machine_policy() then computes
`hand_size = len(hand)`, which is therefore ALWAYS 7, so its keep bar never actually loosens with
mulligan depth despite mull005r_hand_size_thresholds.json separately deriving looser thresholds for
6/5/4 - those looser thresholds were computed but never WIRED into the keep decision the prior
harness's mulligan-sequence simulation actually runs. This module's simulate_one_contextual_
sequence() explicitly threads `mulligans` (the count already taken) into the keep policy, so the
RESULTING hand size (7 - mulligans) determines which size-specific threshold applies to that
attempt's decision - the assignment's own section 21 instruction ("evaluate 7/6/5/4 independently")
requires exactly this.

PER-SIZE THRESHOLDS are REUSED, not re-derived, from mull005r_hand_size_thresholds.json (C@7, D@6,
D@5, None@4 i.e. keep-everything at 4 under assumed-cost=1.0) - mapped onto the shared GRADE_ORDER
letters. A full re-derivation of contextual-scale thresholds via the same EV-sweep methodology
MULL-005R used is disclosed as future work (see the final report's Next Research section), not
attempted here given the added cost of a full bounded search per candidate threshold sweep point.
"""
import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory, TIER_ORDER
from derive_hand_size_trajectory_thresholds import best_bottomed_tier
from contextual_trajectory_object import build_trajectory_object
from contextual_valuation_models import ARCHITECTURES
from strength_speed_matrix import GRADE_RANK

REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_MULLIGANS = 4
TIER_VALUE = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1, "F": 0}

REUSED_SIZE_THRESHOLDS = {7: "C", 6: "D", 5: "D", 4: None}


def _find_best_trajectory_with_state(hand, library, on_play, cards, combos):
    state, m1, m2, m3 = _simulate(hand, library, on_play, cards, combos)
    best_grade = grade_trajectory(state, cards, m1, m2, m3)
    best_state = state
    for label, kwargs in _candidate_configs(hand, library, cards):
        state_t, m1_t, m2_t, m3_t = _simulate(hand, library, on_play, cards, combos, **kwargs)
        grade_t = grade_trajectory(state_t, cards, m1_t, m2_t, m3_t)
        if _better(grade_t, best_grade):
            best_grade, best_state = grade_t, state_t
    return best_state, best_grade


def make_contextual_keep_policy(architecture_name, thresholds_by_size=None, seat=1, archetype=None):
    architecture_fn = ARCHITECTURES[architecture_name]
    thresholds_by_size = thresholds_by_size or REUSED_SIZE_THRESHOLDS

    def policy(hand, library, on_play, cards, combos, mulligans):
        resulting_size = 7 - mulligans
        keep_tier = thresholds_by_size.get(resulting_size)
        if keep_tier is None:
            return True  # size 4 (or unlisted) -> keep everything, per the reused threshold table
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        obj = build_trajectory_object(hand, state, grade, cards, len(cards), on_play, seat=seat, archetype=archetype)
        contextual_grade = architecture_fn(obj)
        return GRADE_RANK[contextual_grade] <= GRADE_RANK[keep_tier]

    return policy


def simulate_one_contextual_sequence(names, rng, cards, combos, keep_policy, on_play, max_mulligans=MAX_MULLIGANS):
    mulligans = 0
    while True:
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        if keep_policy(hand, library, on_play, cards, combos, mulligans) or mulligans >= max_mulligans:
            break
        mulligans += 1
    grade = best_bottomed_tier(hand, library, on_play, cards, combos, mulligans)
    return {"mulligans_taken": mulligans, "final_hand_size": 7 - mulligans, "tier": grade["tier"], "mechanism": grade["mechanism"]}


def run_policy(keep_policy, count, seed, seat, cards, combos):
    on_play = seat == "play"
    names = list(cards.keys())
    rng = random.Random(seed)
    t0 = time.time()
    results = [
        simulate_one_contextual_sequence(names, rng, cards, combos, keep_policy, on_play)
        for _ in range(count)
    ]
    elapsed = time.time() - t0
    return results, elapsed


def _bucket(mulligans):
    return {0: "0", 1: "1", 2: "2"}.get(mulligans, "3+")


def aggregate(results):
    n = len(results)
    mull_counts = Counter(_bucket(r["mulligans_taken"]) for r in results)
    avg_final_hand_size = sum(r["final_hand_size"] for r in results) / n
    tier_dist = Counter(r["tier"] for r in results)
    mean_tier_value = sum(TIER_VALUE[r["tier"]] for r in results) / n
    by_bucket = {}
    for b in ("0", "1", "2", "3+"):
        subset = [r for r in results if _bucket(r["mulligans_taken"]) == b]
        if not subset:
            by_bucket[b] = None
            continue
        by_bucket[b] = {
            "pct_of_population": len(subset) / n,
            "tier_distribution": {t: c / len(subset) for t, c in Counter(r["tier"] for r in subset).items()},
            "mean_tier_value": sum(TIER_VALUE[r["tier"]] for r in subset) / len(subset),
        }
    return {
        "sample_size": n,
        "mulligan_distribution": {k: v / n for k, v in mull_counts.items()},
        "avg_final_hand_size": avg_final_hand_size,
        "expected_card_disadvantage": 7 - avg_final_hand_size,
        "tier_distribution": {t: c / n for t, c in tier_dist.items()},
        "fraction_tier_S_or_A": sum(1 for r in results if r["tier"] in ("S", "A")) / n,
        "fraction_tier_D_or_F": sum(1 for r in results if r["tier"] in ("D", "F")) / n,
        "mean_tier_value": mean_tier_value,
        "by_mulligan_count": by_bucket,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=6010)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()

    london_out = {
        **deck_provenance_fields(payload), "phase": "SIM_001_MULL_006_CONTEXTUAL_LONDON_MULLIGAN",
        "evidence_type": "SIMULATION_MEASURED",
        "seed": args.seed, "seat": args.seat, "sample_size_per_architecture": args.count,
        "reused_size_thresholds_note": (
            "Per-size keep thresholds (C@7, D@6, D@5, keep-everything@4) are REUSED from "
            "mull005r_hand_size_thresholds.json (assumed-mulligan-card-cost=1.0), not re-derived "
            "for the new contextual grade scale - a full re-derivation via the same EV-sweep "
            "methodology is disclosed as future work in the final report's Next Research section."
        ),
        "harness_fix_note": (
            "Fixes a real gap in the prior harness (run_mull005_london_mulligan_sim.py): its "
            "keep_policy was never told how many mulligans had already been taken, so its "
            "size-specific threshold table was computed but never actually wired into the "
            "mulligan-sequence keep decision (hand_size was always 7, every attempt). This "
            "module's simulate_one_contextual_sequence() explicitly threads mulligan depth "
            "through to the policy, so the RESULTING hand size determines which threshold "
            "applies - the assignment's own section 21 instruction to evaluate 7/6/5/4 "
            "independently requires this."
        ),
        "policies": {},
    }
    policy_artifacts = {}

    for arch_name in sorted(ARCHITECTURES):
        policy = make_contextual_keep_policy(arch_name)
        results, elapsed = run_policy(policy, args.count, args.seed, args.seat, cards, combos)
        agg = aggregate(results)
        agg["elapsed_seconds"] = elapsed
        london_out["policies"][arch_name] = agg
        print(f"{arch_name}: n={args.count} in {elapsed:.1f}s  dist={agg['mulligan_distribution']}  "
              f"S_or_A={agg['fraction_tier_S_or_A']:.3f}  D_or_F={agg['fraction_tier_D_or_F']:.3f}  "
              f"mean_tier_value={agg['mean_tier_value']:.3f}  avg_hand={agg['avg_final_hand_size']:.3f}")

        policy_artifacts[arch_name] = {
            **deck_provenance_fields(payload),
            "phase": f"SIM_001_MULL_006_CONTEXTUAL_POLICY_{arch_name.upper()}",
            "evidence_type": "MODEL_DERIVED",
            "architecture": arch_name,
            "per_size_keep_threshold": {str(k): v for k, v in REUSED_SIZE_THRESHOLDS.items()},
            "seat_assumed": 1, "archetype_assumed": None,
            "london_mulligan_results": agg,
            "note": (
                f"Policy: keep iff the {arch_name} architecture's contextual grade for the "
                "resulting hand (7 - mulligans already taken) is at or better than that hand "
                "size's reused threshold. See run_contextual_london_mulligan_sim.py for the full "
                "keep-decision logic and contextual_valuation_models.py for the architecture "
                "itself. Not asserted correct relative to the other three architectures - see "
                "contextual_london_results.json for the head-to-head comparison."
            ),
        }

    for arch_name, artifact in policy_artifacts.items():
        out_path = REPO_ROOT / "results" / "solo_baseline" / f"contextual_policy_{arch_name}.json"
        out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_path}")

    london_path = REPO_ROOT / "results" / "solo_baseline" / "contextual_london_results.json"
    london_path.write_text(json.dumps(london_out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {london_path}")


if __name__ == "__main__":
    main()
