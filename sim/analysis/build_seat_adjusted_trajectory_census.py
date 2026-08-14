"""SIM-001 MULL-006 section 6 / 28 — seat_adjusted_trajectory_census.json.

Applies seat_timing_model.py to REAL simulated best trajectories (this project's solo goldfish
engine does not itself vary by seat - only these CONTEXTUAL exposure/realization fields do) across
all 4 seats, and measures the assignment's required "KEEP -> MULL / MULL -> KEEP changes caused
solely by seat."

The pre-existing legacy trajectory_grading.grade_trajectory() tier is entirely seat-blind (it has
no seat concept at all), so a real seat-sensitivity measurement requires a probe rule that actually
consults seat. This script defines ONE narrow, fully disclosed SEAT_EXPOSURE_PROBE_RULE for
measurement purposes only - it is explicitly NOT a production contextual policy (those are compared
properly in task #117's contextual_policy_weighted/lexicographic/gated/tree.json, per assignment
section 17's instruction not to naively freeze a single valuation architecture). The probe:

    baseline recommendation (at the REFERENCE seat, seat 1) = KEEP if the trajectory's legacy tier
    is at or above MULL-005R's hand-size-7 keep threshold (mull005r_hand_size_thresholds.json).

    excess_exposure_turns(seat) = opponent_turns_before_deployment(seat) -
                                   opponent_turns_before_deployment(seat=1)
                                 = (seat - 1)   [exact, constant for any deployment turn N - see
                                   seat_timing_model.py's docstring]

    PROBE: for a trajectory sitting EXACTLY at the keep/mulligan boundary tier (a marginal keep,
    not a clear one), downgrade the recommendation to MULLIGAN if excess_exposure_turns(seat) >= 2
    (i.e. Seat 3 or Seat 4 relative to the Seat-1 reference).

This isolates a genuine seat effect (excess_exposure_turns depends only on seat, never on
deployment turn or engine identity) without requiring the full contextual valuation architecture to
already exist.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import find_best_trajectory
from trajectory_grading import TIER_ORDER
from seat_timing_model import seat_adjusted_timing, opponent_turns_before, TIMING_PROVENANCE
from engine_strength_prior import ENGINE_STRENGTH_PRIOR

REPO_ROOT = Path(__file__).resolve().parents[2]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}
SEATS = (1, 2, 3, 4)


def _keep_threshold_7():
    path = REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json"
    data = json.loads(path.read_text())
    return data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]["7"]["keep_at_or_above_tier"]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=6000)
    ap.add_argument("--seed", type=int, default=6003)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)
    keep_tier = _keep_threshold_7()
    keep_rank = TIER_RANK[keep_tier]

    per_engine_turn_samples = []  # (engine, turn, legacy_tier)
    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]
        _, grade, _ = find_best_trajectory(hand, library, on_play, cards, combos)
        engine, turn = grade["tier_engine"], grade["tier_turn"]
        if engine in ENGINE_STRENGTH_PRIOR and turn is not None:
            per_engine_turn_samples.append((engine, turn, grade["tier"]))

    # ---- per-seat exposure/realization tables, aggregated over real deployment turns ----------
    per_seat_stats = {}
    for seat in SEATS:
        turns_before_deploy = []
        turns_before_realize = []
        realized_before_next_turn_count = 0
        for engine, turn, _ in per_engine_turn_samples:
            timing = seat_adjusted_timing(engine, turn, seat)
            turns_before_deploy.append(timing["opponent_turns_before_deployment"])
            turns_before_realize.append(timing["opponent_turns_before_first_possible_realization"])
            if timing["value_generated_before_our_next_turn"]:
                realized_before_next_turn_count += 1
        n = len(per_engine_turn_samples)
        per_seat_stats[str(seat)] = {
            "sample_count": n,
            "avg_opponent_turns_before_deployment": round(sum(turns_before_deploy) / n, 3) if n else None,
            "avg_opponent_turns_before_first_possible_realization": round(sum(turns_before_realize) / n, 3) if n else None,
            "realized_before_our_next_turn_count": realized_before_next_turn_count,
            "realized_before_our_next_turn_rate": round(realized_before_next_turn_count / n, 4) if n else None,
        }

    # ---- structural finding: excess exposure delta is a pure function of seat ----------------
    excess_exposure_by_seat = {str(s): opponent_turns_before(1, s) - opponent_turns_before(1, 1) for s in SEATS}
    relative_severity_by_deployment_turn = {}
    for n_turn in (1, 2, 3):
        seat1_exposure = opponent_turns_before(n_turn, 1)
        seat4_exposure = opponent_turns_before(n_turn, 4)
        relative_severity_by_deployment_turn[f"T{n_turn}"] = {
            "seat1_opponent_turns_before_deployment": seat1_exposure,
            "seat4_opponent_turns_before_deployment": seat4_exposure,
            "absolute_delta": seat4_exposure - seat1_exposure,
            "relative_increase": (
                "INFINITE (seat1 baseline is zero)" if seat1_exposure == 0
                else round((seat4_exposure - seat1_exposure) / seat1_exposure, 3)
            ),
        }

    # ---- seat-exposure probe rule: KEEP->MULL / MULL->KEEP flips caused solely by seat --------
    flips_keep_to_mull = 0
    flips_mull_to_keep = 0  # the probe rule is monotonic (only ever downgrades), so this stays 0 -
                             # recorded explicitly rather than omitted, so the artifact shows the
                             # check was actually performed, not skipped.
    marginal_hands_examined = 0
    example_flips = []
    for engine, turn, tier in per_engine_turn_samples:
        if TIER_RANK[tier] != keep_rank:
            continue  # only exactly-at-the-boundary trajectories are eligible for the probe
        marginal_hands_examined += 1
        baseline_keep = True  # tier == keep_rank means KEEP at the seat-1 reference
        for seat in SEATS:
            excess = seat - 1
            probe_recommends_mull = excess >= 2
            decision = "MULLIGAN" if probe_recommends_mull else "KEEP"
            if seat == 1:
                continue  # seat 1 IS the reference baseline, not a flip candidate against itself
            if baseline_keep and decision == "MULLIGAN":
                flips_keep_to_mull += 1
                if len(example_flips) < 10:
                    example_flips.append({
                        "engine": engine, "deployment_turn": turn, "legacy_tier": tier,
                        "seat": seat, "excess_exposure_turns": excess,
                        "decision_before_probe": "KEEP", "decision_after_probe": "MULLIGAN",
                    })

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_SEAT_ADJUSTED_TRAJECTORY_CENSUS",
        "evidence_type": "SIMULATION_MEASURED",
        "timing_model_evidence_type": TIMING_PROVENANCE,
        "sample_count": args.count, "seed": args.seed, "seat_assumption_for_sampling": args.seat,
        "keep_tier_threshold_size7": keep_tier,
        "hands_with_tracked_engine_as_best_trajectory": len(per_engine_turn_samples),
        "per_seat_exposure_and_realization_stats": per_seat_stats,
        "excess_exposure_turns_by_seat_relative_to_seat1": excess_exposure_by_seat,
        "relative_seat_severity_by_deployment_turn": relative_severity_by_deployment_turn,
        "relative_severity_finding": (
            "The ABSOLUTE opponent-turn exposure delta between Seat 1 and Seat 4 is exactly 3 for "
            "ANY deployment turn (structural, not trajectory-specific - see seat_timing_model.py). "
            "But the RELATIVE severity of that delta shrinks as deployment turn increases: a T1 "
            "trajectory goes from 0 (seat1) to 3 (seat4) opponent turns of exposure before "
            "deployment - an infinite relative increase from a zero baseline - while a T3 "
            "trajectory only goes from 6 to 9, a 50% relative increase. T1 trajectories are "
            "therefore the MOST seat-sensitive in relative terms, even though every trajectory "
            "shares the same absolute 3-turn swing."
        ),
        "value_generated_before_our_next_turn_is_seat_invariant": (
            "realized_before_our_next_turn_rate is identical across all 4 seats (see per-seat "
            "stats above) - this yes/no property depends only on REALIZATION_TIMING_CLASS "
            "(engine identity), never on seat. Seat changes the MAGNITUDE of exposure (how many "
            "opponent turns/windows), not whether realization structurally precedes our own next "
            "turn."
        ),
        "seat_exposure_probe_rule": {
            "description": (
                "PROBE RULE FOR MEASUREMENT ONLY - explicitly NOT a production contextual policy. "
                "Downgrades a KEEP to MULLIGAN only for trajectories sitting EXACTLY at the "
                "hand-size-7 keep/mulligan boundary tier, only when excess_exposure_turns(seat) = "
                "(seat - 1) >= 2 (Seat 3 or Seat 4 relative to the Seat-1 reference). The full "
                "contextual policy comparison (weighted/lexicographic/gated/tree) is reserved for "
                "task #117, per assignment section 17."
            ),
            "marginal_hands_examined": marginal_hands_examined,
            "keep_to_mull_flips_caused_solely_by_seat": flips_keep_to_mull,
            "mull_to_keep_flips_caused_solely_by_seat": flips_mull_to_keep,
            "keep_to_mull_flip_rate_among_marginal_hands": (
                round(flips_keep_to_mull / (marginal_hands_examined * 3), 4) if marginal_hands_examined else None
            ),
            "example_flips": example_flips,
            "note": (
                "mull_to_keep_flips is structurally always 0 under this probe - it is a one-"
                "directional downgrade-only rule (higher seat number can only ever look WORSE, "
                "never better, in raw opponent-turn-exposure terms), so no MULL->KEEP direction "
                "exists for this particular probe. Reported explicitly rather than omitted."
            ),
        },
        "most_seat_sensitive_trajectory_classes": (
            "By realization_timing_class: OWN_NEXT_DRAW_STEP (Sylvan Library) is the most seat-"
            "compounding class - its realization exposure (opponent_turns_before_first_possible_"
            "realization) is opponent_turns_before_deployment + 3, so the seat-1-vs-seat-4 delta "
            "at REALIZATION time is still exactly 3, same as at deployment, meaning Library never "
            "gets to 'catch up' the way an IMMEDIATE_OPPONENT_TURN engine's very next opponent "
            "turn can. OWN_TURN_DEPENDENT (functional Pod/Survival) is the least seat-sensitive "
            "for realization specifically, since realization is pinned to deployment turn itself "
            "regardless of what opponents do (though DEPLOYMENT exposure is identical to every "
            "other class)."
        ),
        "limitations": [
            "The probe rule only tests ONE narrow, disclosed measurement heuristic - it is not the "
            "final contextual policy and should not be cited as a production recommendation.",
            "opponent_action_windows_before_* uses a disclosed, non-measured convention (2 windows "
            "per opponent turn) - treat those specific counts as illustrative, not calibrated.",
            "This solo goldfish engine cannot model an opponent's actual timing of removal/"
            "disruption during those extra opponent turns - it only counts the STRUCTURAL number "
            "of turns/windows that exist, not whether anything happens in them (that is the "
            "fragility/recovery work, task #109).",
        ],
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "seat_adjusted_trajectory_census.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"hands_with_tracked_engine: {len(per_engine_turn_samples)}/{args.count}")
    print(f"marginal_hands_examined: {marginal_hands_examined}")
    print(f"keep_to_mull_flips_caused_solely_by_seat: {flips_keep_to_mull}")


if __name__ == "__main__":
    main()
