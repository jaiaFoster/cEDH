"""SIM-001 MULL-006 section 19 / 28 — one_land_hand_audit.json.

A dedicated analysis of one-land opening hands, reusing draw_dependence_model.py (outs/
probability), trajectory_fragility_model.py (fallback), and the bounded trajectory search - no new
mechanics, only a filtered, tagged census over hands with exactly one land in the opening draw.

HAND-SIZE SAMPLING (disclosed simplification): "by hand size" is approximated here by drawing N
cards directly from a freshly shuffled deck for N in (7, 6, 5, 4), NOT by modeling the full London
mulligan BOTTOMING decision (which card the pilot would choose to bottom before drawing back to N).
This measures "hands of size N that happen to have exactly one land," not "hands reached by
mulliganing to N and bottoming down from a real 7-card draw" - the latter, more accurate model is
task #117's full mulligan-sim rebuild. Disclosed as a limitation, not silently conflated.

CATEGORY TAGS (assignment's "separate at minimum" list) are NOT mutually exclusive - a hand can
carry more than one tag (e.g. "1 land + dork + self-contained T2 engine" and "1 land + broad
outs" cannot both apply to the exact same trajectory, but "1 land + tutor" can co-occur with any
destination category). Reported as tag counts/keep-rates, not a forced single bucket.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from opening_hand_model import (
    load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner,
    MANA_SOURCES, TUTORS,
)
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory
from draw_dependence_model import classify_trajectory_draw_dependence, _is_land
from trajectory_fragility_model import assess_fragility
from engine_strength_prior import ENGINE_STRENGTH_PRIOR
from contextual_trajectory_object import build_trajectory_object
from contextual_valuation_models import gated_model
from strength_speed_matrix import GRADE_RANK

REPO_ROOT = Path(__file__).resolve().parents[2]
DORKS = {n for n, spec in MANA_SOURCES.items() if spec.get("creature")}
FAST_MANA = set(MANA_SOURCES) - DORKS
HAND_SIZES = (7, 6, 5, 4)
SEATS = (1, 2, 3, 4)
KEEP_RANK = GRADE_RANK["C"]


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


def _classify_one_land_hand(hand, state, grade, cards, deck_size, on_play):
    t1_accel_available = any(n in DORKS | FAST_MANA for n in hand)
    has_dork = any(n in DORKS for n in hand)
    has_fast_mana = any(n in FAST_MANA for n in hand)
    engine_already_present = any(n in ENGINE_STRENGTH_PRIOR for n in hand)
    tutor_already_present = any(n in TUTORS for n in hand)

    draw_dep = classify_trajectory_draw_dependence(state, cards, grade["tier_engine"], grade["tier_turn"], deck_size, on_play)
    fragility = assess_fragility(state, cards, grade["tier_engine"], grade["tier_turn"], on_play)

    needs_land = False
    land_outs = sum(1 for n in cards if _is_land(n, cards) and n not in hand)
    nonland_mana_outs = sum(1 for n in cards if n in (DORKS | FAST_MANA) and n not in hand)
    if draw_dep:
        for dep in draw_dep["dependencies"]:
            if dep["slot"] == "supporting_land":
                needs_land = True

    deterministic = draw_dep["overall_classification"] == "SELF_CONTAINED" if draw_dep else None
    probability = None
    if draw_dep and draw_dep["dependencies"]:
        worst = max(
            draw_dep["dependencies"],
            key=lambda d: {"BROAD_OUTS": 0, "NARROW_OUTS": 1, "EXACT_OR_NEAR_EXACT": 2}.get(d["classification"], 0),
        )
        probability = worst["probability_of_success_by_turn"]
    elif grade["tier_engine"] is not None:
        probability = 1.0

    fallback = None
    if fragility:
        fallback = fragility["second_best_destination_realized"] or fragility["weak_in_hand_fallback"] or "NONE"

    tags = []
    if grade["tier_engine"] is None:
        tags.append("1 land + no destination")
    else:
        overall = draw_dep["overall_classification"] if draw_dep else "SELF_CONTAINED"
        if has_dork and overall == "SELF_CONTAINED" and grade["tier_turn"] is not None and grade["tier_turn"] <= 2:
            tags.append("1 land + dork + self-contained T2 engine")
        if has_dork and needs_land:
            tags.append("1 land + dork + needs land")
        if has_fast_mana and not has_dork:
            tags.append("1 land + fast mana + engine")
        if overall == "BROAD_OUTS":
            tags.append("1 land + broad outs")
        if overall in ("NARROW_OUTS", "EXACT_OR_NEAR_EXACT"):
            tags.append("1 land + narrow outs")
    if tutor_already_present:
        tags.append("1 land + tutor")

    return {
        "t1_acceleration_available": t1_accel_available,
        "second_mana_source_already_available": has_dork or has_fast_mana,
        "second_land_required": needs_land,
        "live_land_outs": land_outs,
        "nonland_mana_outs": nonland_mana_outs,
        "engine_already_present": engine_already_present,
        "tutor_already_present": tutor_already_present,
        "advertised_trajectory_deterministic": deterministic,
        "probability_trajectory_succeeds": probability,
        "fallback_if_draw_misses": fallback,
        "legacy_tier": grade["tier"],
        "tier_engine": grade["tier_engine"],
        "tags": tags,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count-per-size", type=int, default=6000)
    ap.add_argument("--seed", type=int, default=6008)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    deck_size = len(cards)

    by_hand_size = {}
    for n_size in HAND_SIZES:
        rng = random.Random(args.seed + n_size)
        one_land_count = 0
        total_sampled = 0
        tag_counts = Counter()
        tag_keeps = Counter()
        field_examples = []
        keep_count_by_seat = defaultdict(int)
        one_land_count_by_seat_denom = 0

        for _ in range(args.count_per_size):
            lib = names[:]
            rng.shuffle(lib)
            hand, library = lib[:n_size], lib[n_size:]
            total_sampled += 1
            n_lands = sum(1 for c in hand if _is_land(c, cards))
            if n_lands != 1:
                continue
            one_land_count += 1

            state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
            audit = _classify_one_land_hand(hand, state, grade, cards, deck_size, on_play)

            for tag in audit["tags"]:
                tag_counts[tag] += 1
                obj = build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=1)
                keep = GRADE_RANK[gated_model(obj)] <= KEEP_RANK
                if keep:
                    tag_keeps[tag] += 1

            one_land_count_by_seat_denom += 1
            for seat in SEATS:
                obj = build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=seat)
                keep = GRADE_RANK[gated_model(obj)] <= KEEP_RANK
                if keep:
                    keep_count_by_seat[seat] += 1

            if len(field_examples) < 15:
                field_examples.append({"hand": sorted(hand), **audit})

        by_hand_size[str(n_size)] = {
            "total_sampled": total_sampled,
            "one_land_hand_count": one_land_count,
            "one_land_hand_rate": round(one_land_count / total_sampled, 4) if total_sampled else None,
            "tag_counts": dict(tag_counts),
            "tag_keep_rates": {
                tag: round(tag_keeps[tag] / cnt, 4) for tag, cnt in tag_counts.items()
            },
            "keep_rate_by_seat": {
                str(s): round(keep_count_by_seat[s] / one_land_count_by_seat_denom, 4)
                for s in SEATS
            } if one_land_count_by_seat_denom else {},
            "example_hands": field_examples,
        }

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_ONE_LAND_HAND_AUDIT",
        "evidence_type": "SIMULATION_MEASURED",
        "seed_base": args.seed, "seat_assumption_for_sampling": args.seat,
        "count_per_hand_size": args.count_per_size,
        "keep_threshold": "contextual grade (gated architecture, seat 1 unless noted) at or better than C",
        "hand_size_sampling_note": (
            "Each hand size is sampled by drawing N cards DIRECTLY from a freshly shuffled deck, "
            "not by modeling the full London mulligan bottoming decision from a real 7-card draw - "
            "see module docstring. This measures 'hands of size N with exactly one land,' not "
            "'hands reached by mulliganing to N.' The accurate bottoming-aware model is task "
            "#117's full mulligan-sim rebuild."
        ),
        "category_tags_not_mutually_exclusive_note": (
            "A hand may carry multiple tags (e.g. '1 land + tutor' can co-occur with any "
            "destination category) - tag_counts/tag_keep_rates are reported per-tag, not as a "
            "forced single bucket per hand."
        ),
        "results_by_hand_size": by_hand_size,
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "one_land_hand_audit.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    for n_size in HAND_SIZES:
        d = by_hand_size[str(n_size)]
        print(f"size {n_size}: one_land={d['one_land_hand_count']}/{d['total_sampled']} tags={d['tag_counts']}")


if __name__ == "__main__":
    main()
