"""SIM-001 MULL-006 section 22 / 28 — top_25_contextual_trajectories.json.

Regenerates MULL-005R's top-25 opener report (top_25_opener_trajectories.json) with the full
section-22 column set, using every MULL-006 module built in this phase. Ranks real individual
sampled hands (matching the established MULL-005R precedent - 25 concrete hands, not 25 abstract
trajectory TYPES) by their contextual grade under the GATED architecture (the same single reference
used throughout this phase's seat/pod/one-land work, for consistency - not asserted correct over
the other three).

REPORTING CONVENTIONS (disclosed, since the assignment's schema doesn't fully specify these):
  - SEAT is fixed at 1 for this table's ranking/columns - full seat variation is already reported
    exhaustively in seat_pod_matrix.json (task #114); this table would be needlessly redundant if
    it duplicated that sweep per hand.
  - POD MODIFIER (and RELEVANT INTERACTION, which is archetype-dependent) is reported against ONE
    representative archetype, "midrange_grind" (pod_archetypes.py's own generic/no-skew baseline),
    not all 10 - again to avoid redundancy with seat_pod_matrix.json's full archetype sweep.
  - GRADE @ 7/6/5/4: the hand's OWN contextual grade at 7 (no bottoming), then for 6/5/4 the BEST
    achievable contextual grade over every C(7, 7-N) bottoming choice from this SAME 7-card hand -
    the contextual-grading analogue of derive_hand_size_trajectory_thresholds.best_bottomed_tier,
    rescored under the gated architecture instead of the legacy tier.
"""
import itertools
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory
from contextual_trajectory_object import build_trajectory_object
from contextual_valuation_models import gated_model
from strength_speed_matrix import GRADE_RANK
from engine_realization_timing_model import realization_timing_profile

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ARCHETYPE = "midrange_grind"
REFERENCE_SEAT = 1
TOP_N = 25


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


def _contextual_grade_for_hand(hand, library, on_play, cards, combos, deck_size, seat, archetype):
    state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
    obj = build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=seat, archetype=archetype)
    return gated_model(obj), obj, grade, state


def _best_bottomed_contextual_grade(hand, library, on_play, cards, combos, deck_size, n_bottom, seat, archetype):
    best_grade = None
    for bottomed in itertools.combinations(hand, n_bottom):
        remaining = [c for c in hand if c not in bottomed]
        new_library = list(library) + list(bottomed)
        cg, _, _, _ = _contextual_grade_for_hand(remaining, new_library, on_play, cards, combos, deck_size, seat, archetype)
        if best_grade is None or GRADE_RANK[cg] < GRADE_RANK[best_grade]:
            best_grade = cg
    return best_grade


def _first_realized_value_label(destination, deployment_turn, seat):
    if destination is None or deployment_turn is None:
        return "N/A_NO_DESTINATION"
    timing = realization_timing_profile(destination, deployment_turn, seat)
    if timing is None:
        return "UNTRACKED_DESTINATION"
    cls = timing["realization_timing_class"]
    if cls == "IMMEDIATE_OPPONENT_TURN":
        return f"opponent's next turn (turn {deployment_turn}+, before our own next turn)"
    if cls == "OWN_NEXT_DRAW_STEP":
        return f"our own draw step, turn {deployment_turn + 1}"
    return f"turn {deployment_turn} (same turn as deployment)"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=6011)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    deck_size = len(cards)
    rng = random.Random(args.seed)

    candidates = []
    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]
        cg, obj, grade, state = _contextual_grade_for_hand(hand, library, on_play, cards, combos, deck_size, REFERENCE_SEAT, REFERENCE_ARCHETYPE)
        candidates.append((GRADE_RANK[cg], grade["tier_turn"] or 99, hand, library, cg, obj, grade, state))

    candidates.sort(key=lambda c: (c[0], c[1]))
    top = candidates[:TOP_N]

    rows = []
    for rank, (rank_key, _turn_key, hand, library, cg7, obj, grade, state) in enumerate(top, start=1):
        grade_at = {"7": cg7}
        for n_size, n_bottom in ((6, 1), (5, 2), (4, 3)):
            grade_at[str(n_size)] = _best_bottomed_contextual_grade(
                hand, library, on_play, cards, combos, deck_size, n_bottom, REFERENCE_SEAT, REFERENCE_ARCHETYPE
            )

        rows.append({
            "rank": rank,
            "hand": sorted(hand),
            "trajectory": f"T{obj['deployment_turn']} {obj['destination']}" if obj["destination"] else "no destination",
            "intrinsic_strength": obj["intrinsic_strength"],
            "relative_speed": obj["relative_speed"],
            "seat": REFERENCE_SEAT,
            "self_contained": obj["draw_dependence_class"] == "SELF_CONTAINED",
            "draw_dependence_class": obj["draw_dependence_class"],
            "outs": obj["outs_count"],
            "success_probability": obj["probability_of_trajectory"],
            "first_realized_value": _first_realized_value_label(obj["destination"], obj["deployment_turn"], REFERENCE_SEAT),
            "resources_consumed": obj["resources_consumed"],
            "cards_remaining": obj["cards_remaining"],
            "resilience": obj["resilience_class"],
            "secondary_plan": obj["recovery_trajectory"],
            "live_interaction": obj["live_agency"],
            "relevant_interaction": obj["relevant_agency"],
            "pod_modifier": obj["pod_realization_modifier"],
            "grade_at_7": grade_at["7"],
            "grade_at_6": grade_at["6"],
            "grade_at_5": grade_at["5"],
            "grade_at_4": grade_at["4"],
            "legacy_tier": grade["tier"],
        })

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_TOP_25_CONTEXTUAL_TRAJECTORIES",
        "evidence_type": "SIMULATION_MEASURED",
        "sample_count": args.count, "seed": args.seed, "seat_assumption_for_sampling": args.seat,
        "reference_architecture": "gated",
        "reference_seat_for_columns": REFERENCE_SEAT,
        "reference_archetype_for_columns": REFERENCE_ARCHETYPE,
        "reporting_convention_note": (
            "SEAT is fixed at 1 and archetype fixed at 'midrange_grind' (pod_archetypes.py's "
            "generic baseline) for this table's columns - full seat/archetype sweeps are already "
            "reported exhaustively in seat_pod_matrix.json (task #114) and would be redundant "
            "here. GRADE @ N for N<7 is the BEST achievable contextual grade over every legal "
            "bottoming choice from this SAME 7-card hand (the contextual-grading analogue of "
            "derive_hand_size_trajectory_thresholds.best_bottomed_tier)."
        ),
        "trajectories": rows,
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "top_25_contextual_trajectories.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    for r in rows[:5]:
        print(r["rank"], r["trajectory"], r["grade_at_7"], r["grade_at_6"], r["grade_at_5"], r["grade_at_4"])


if __name__ == "__main__":
    main()
