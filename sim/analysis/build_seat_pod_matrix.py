"""SIM-001 MULL-006 section 18 / 28 — seat_pod_matrix.json.

For representative archetypes, evaluates real simulated hands across all 4 seats and all 10
pod_archetypes.py archetypes, producing a matrix of recommendation changes. Specifically looks for
the assignment's two named cases: same seven/same trajectory/different seat -> different
recommendation, and same seven/same seat/different pod -> different recommendation.

Uses the GATED architecture (contextual_valuation_models.gated_model) as the single reference
architecture for this matrix - not because it is asserted correct (task #113 explicitly declines
to assert any of the four architectures correct), but because a matrix needs ONE fixed grading
rule to make "the same hand's recommendation changed" a well-defined statement; the full four-
architecture comparison is task #117's job. The KEEP/MULLIGAN threshold reuses MULL-005R's
existing hand-size-7 tier-C threshold (mull005r_hand_size_thresholds.json) mapped onto the shared
GRADE_ORDER scale (tier "C" is a shared label between the legacy 6-band scale and this project's
11-band scale) - a disclosed, reused provisional threshold, not re-derived for the new contextual
grades (that re-derivation is task #117's).
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory
from contextual_trajectory_object import build_trajectory_object
from contextual_valuation_models import gated_model
from strength_speed_matrix import GRADE_RANK
from pod_realization_model import ARCHETYPE_BEHAVIOR_PROFILE

REPO_ROOT = Path(__file__).resolve().parents[2]
SEATS = (1, 2, 3, 4)
ARCHETYPES = sorted(ARCHETYPE_BEHAVIOR_PROFILE)
KEEP_THRESHOLD_LABEL = "C"


def _keep_threshold_rank():
    return GRADE_RANK[KEEP_THRESHOLD_LABEL]


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


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=6007)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    deck_size = len(cards)
    rng = random.Random(args.seed)
    keep_rank = _keep_threshold_rank()

    hands_examined = 0
    seat_flip_hands = 0          # same trajectory, some archetype's decision differs across seats
    pod_flip_hands = 0           # same trajectory, some seat's decision differs across archetypes
    seat_flip_count_by_archetype = Counter()
    pod_flip_count_by_seat = Counter()
    seat_flip_examples = []
    pod_flip_examples = []
    most_seat_sensitive_engines = Counter()
    most_pod_sensitive_engines = Counter()

    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        if grade["tier_engine"] is None:
            continue  # no destination - seat/pod cannot change a decision by construction (gated_model)
        hands_examined += 1

        decisions = {}  # (seat, archetype) -> "KEEP"/"MULLIGAN"
        for seat in SEATS:
            for arch in ARCHETYPES:
                obj = build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=seat, archetype=arch)
                contextual_grade = gated_model(obj)
                decisions[(seat, arch)] = "KEEP" if GRADE_RANK[contextual_grade] <= keep_rank else "MULLIGAN"

        hand_had_seat_flip = False
        for arch in ARCHETYPES:
            arch_decisions = {decisions[(s, arch)] for s in SEATS}
            if len(arch_decisions) > 1:
                hand_had_seat_flip = True
                seat_flip_count_by_archetype[arch] += 1
        if hand_had_seat_flip:
            seat_flip_hands += 1
            most_seat_sensitive_engines[grade["tier_engine"]] += 1
            if len(seat_flip_examples) < 10:
                seat_flip_examples.append({
                    "hand": sorted(hand), "tier_engine": grade["tier_engine"], "tier_turn": grade["tier_turn"],
                    "decisions_by_seat_for_first_flipping_archetype": next(
                        (
                            {str(s): decisions[(s, a)] for s in SEATS}
                            for a in ARCHETYPES if len({decisions[(s, a)] for s in SEATS}) > 1
                        ), None
                    ),
                })

        hand_had_pod_flip = False
        for seat in SEATS:
            seat_decisions = {decisions[(seat, a)] for a in ARCHETYPES}
            if len(seat_decisions) > 1:
                hand_had_pod_flip = True
                pod_flip_count_by_seat[seat] += 1
        if hand_had_pod_flip:
            pod_flip_hands += 1
            most_pod_sensitive_engines[grade["tier_engine"]] += 1
            if len(pod_flip_examples) < 10:
                pod_flip_examples.append({
                    "hand": sorted(hand), "tier_engine": grade["tier_engine"], "tier_turn": grade["tier_turn"],
                    "decisions_by_archetype_for_first_flipping_seat": next(
                        (
                            {a: decisions[(s, a)] for a in ARCHETYPES}
                            for s in SEATS if len({decisions[(s, a)] for a in ARCHETYPES}) > 1
                        ), None
                    ),
                })

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_SEAT_POD_MATRIX",
        "evidence_type": "SIMULATION_MEASURED",
        "reference_architecture": "gated",
        "reference_architecture_note": (
            "Uses contextual_valuation_models.gated_model as the SINGLE reference architecture, "
            "not because it is asserted correct - task #113 declined to assert any of the four "
            "architectures correct - but because this matrix needs one fixed grading rule to make "
            "'the same hand's recommendation changed' well-defined. Task #117 compares all four."
        ),
        "keep_threshold": f"contextual grade at or better than {KEEP_THRESHOLD_LABEL} (reused from "
                           "mull005r_hand_size_thresholds.json's hand-size-7 tier-C threshold, "
                           "mapped onto the shared GRADE_ORDER scale - not re-derived for the new "
                           "contextual grades; that re-derivation is task #117's).",
        "sample_count": args.count, "seed": args.seed, "seat_assumption_for_sampling": args.seat,
        "hands_with_tracked_destination": hands_examined,
        "seats_evaluated": list(SEATS),
        "archetypes_evaluated": ARCHETYPES,
        "seat_flip_hands_count": seat_flip_hands,
        "seat_flip_hands_rate": round(seat_flip_hands / hands_examined, 4) if hands_examined else None,
        "seat_flip_count_by_archetype": dict(seat_flip_count_by_archetype),
        "pod_flip_hands_count": pod_flip_hands,
        "pod_flip_hands_rate": round(pod_flip_hands / hands_examined, 4) if hands_examined else None,
        "pod_flip_count_by_seat": {str(k): v for k, v in pod_flip_count_by_seat.items()},
        "most_seat_sensitive_engines": dict(most_seat_sensitive_engines.most_common(10)),
        "most_pod_sensitive_engines": dict(most_pod_sensitive_engines.most_common(10)),
        "seat_flip_examples_same_seven_same_trajectory_different_seat": seat_flip_examples,
        "pod_flip_examples_same_seven_same_seat_different_pod": pod_flip_examples,
        "limitations": [
            "Uses one reference architecture (gated) and one reused threshold - the flip RATES "
            "reported here are specific to that combination, not an architecture-independent fact "
            "about the deck. Task #117's full four-architecture comparison may show different "
            "flip rates.",
            "Only hands with a tracked destination (tier_engine not None) are examined - the "
            "gated model's no-destination ceiling makes seat/pod structurally unable to flip a "
            "destination-less hand's decision, so those hands are excluded rather than padding "
            "the denominator with guaranteed non-flips.",
        ],
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "seat_pod_matrix.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"hands_examined: {hands_examined}/{args.count}")
    print(f"seat_flip_hands: {seat_flip_hands} ({result['seat_flip_hands_rate']})")
    print(f"pod_flip_hands: {pod_flip_hands} ({result['pod_flip_hands_rate']})")


if __name__ == "__main__":
    main()
