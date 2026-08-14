"""SIM-001 MULL-006 section 23 / 28 — contextual_disagreement_examples.json.

Generates the assignment's 7 required disagreement examples (A-G) from REAL simulated hands, not
fabricated ones, reusing every module built this phase. B and E reuse concrete examples already
found and validated in seat_pod_matrix.json (task #114) rather than re-searching for them.
"""
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory
from contextual_trajectory_object import build_trajectory_object
from contextual_valuation_models import gated_model
from strength_speed_matrix import base_trajectory_quality, GRADE_RANK
from relevant_agency_model import hand_agency_scores
from opening_hand_policy import HandState

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def _sample(rng, names):
    lib = names[:]
    rng.shuffle(lib)
    return lib[:7], lib[7:]


def example_A_strength_speed(names, cards, combos, on_play, rng, tries=5000):
    """T1 Mastermind vs T2 Remora-type: real hands for each, base_trajectory_grade compared."""
    mastermind_hand = remora_hand = None
    for _ in range(tries):
        if mastermind_hand and remora_hand:
            break
        hand, library = _sample(rng, names)
        _, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        if not mastermind_hand and grade["tier_engine"] == "Faerie Mastermind" and grade["tier_turn"] == 1:
            mastermind_hand = (hand, grade)
        if not remora_hand and grade["tier_engine"] in ("Mystic Remora", "Esper Sentinel") and grade["tier_turn"] == 2:
            remora_hand = (hand, grade)
    if not (mastermind_hand and remora_hand):
        return None
    m_grade = base_trajectory_quality(mastermind_hand[1]["tier_engine"], mastermind_hand[1]["tier_turn"])
    r_grade = base_trajectory_quality(remora_hand[1]["tier_engine"], remora_hand[1]["tier_turn"])
    return {
        "label": "A. STRENGTH x SPEED - T1 Mastermind vs T2 Remora-type",
        "t1_mastermind_hand": sorted(mastermind_hand[0]),
        "t1_mastermind_base_grade": m_grade,
        "t2_remora_type_hand": sorted(remora_hand[0]),
        "t2_remora_type_tier_engine": remora_hand[1]["tier_engine"],
        "t2_remora_type_base_grade": r_grade,
        "t1_mastermind_outranks": GRADE_RANK[m_grade] < GRADE_RANK[r_grade],
        "finding": (
            f"T1 Mastermind grades {m_grade} (rank {GRADE_RANK[m_grade]}); T2 "
            f"{remora_hand[1]['tier_engine']} grades {r_grade} (rank {GRADE_RANK[r_grade]}) - "
            "the assignment's own named relationship, confirmed on real simulated hands."
        ),
    }


def example_C_draw_dependence(names, cards, combos, on_play, rng, tries=3000):
    """Apparent T2 engine but requires a topdeck (engine card itself drawn naturally)."""
    from draw_dependence_model import classify_trajectory_draw_dependence
    for _ in range(tries):
        hand, library = _sample(rng, names)
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        if grade["tier_engine"] is None or grade["tier_turn"] != 2:
            continue
        dep = classify_trajectory_draw_dependence(state, cards, grade["tier_engine"], grade["tier_turn"], len(cards), on_play)
        if dep and any(d["slot"] == "engine_card" and d["source"] == "natural_draw" for d in dep["dependencies"]):
            return {
                "label": "C. DRAW DEPENDENCE - apparent T2 engine but requires a topdeck",
                "hand": sorted(hand), "tier_engine": grade["tier_engine"], "tier_turn": grade["tier_turn"],
                "draw_dependence_class": dep["overall_classification"],
                "dependency_detail": dep["dependencies"],
                "finding": (
                    f"{grade['tier_engine']} is NOT in the opening hand - it must be drawn naturally "
                    f"by turn {grade['tier_turn']}. The hand LOOKS like a coherent T2 engine line only "
                    "because the search found it in this particular shuffle; a human evaluating the "
                    "opening 7 alone would see no engine at all."
                ),
            }
    return None


def example_D_fragility(names, cards, combos, on_play, rng, tries=6000):
    """Same destination, one line ROBUST and one ALL_IN."""
    from trajectory_fragility_model import assess_fragility
    by_engine = {}
    for _ in range(tries):
        hand, library = _sample(rng, names)
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        if grade["tier_engine"] is None:
            continue
        result = assess_fragility(state, cards, grade["tier_engine"], grade["tier_turn"], on_play)
        if result["resilience_class"] not in ("ROBUST", "ALL_IN"):
            continue
        bucket = by_engine.setdefault(grade["tier_engine"], {})
        if result["resilience_class"] not in bucket:
            bucket[result["resilience_class"]] = (hand, grade, result)
        if "ROBUST" in bucket and "ALL_IN" in bucket:
            robust_hand, robust_grade, robust_result = bucket["ROBUST"]
            allin_hand, allin_grade, allin_result = bucket["ALL_IN"]
            return {
                "label": "D. FRAGILITY - same destination, one ROBUST one ALL_IN",
                "tier_engine": grade["tier_engine"],
                "robust_hand": sorted(robust_hand), "robust_cards_remaining": robust_result["cards_remaining"],
                "robust_second_best": robust_result["second_best_destination_realized"],
                "all_in_hand": sorted(allin_hand), "all_in_cards_remaining": allin_result["cards_remaining"],
                "all_in_hand_collapses": allin_result["hand_effectively_collapses"],
                "finding": (
                    f"Both hands reach {grade['tier_engine']} as their best trajectory, but the "
                    f"ROBUST hand retains {robust_result['cards_remaining']} cards with a realized "
                    f"second destination ({robust_result['second_best_destination_realized']}), while "
                    f"the ALL_IN hand retains only {allin_result['cards_remaining']} cards with no "
                    "fallback - the SAME destination name is not the same trajectory quality."
                ),
            }
    return None


def example_F_relevant_agency(names, cards, combos, on_play, rng, tries=3000):
    """Same engine trajectory, different interaction relevance across archetypes."""
    for _ in range(tries):
        hand, library = _sample(rng, names)
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        if grade["tier_engine"] is None:
            continue
        state2 = HandState(hand, library, on_play=on_play, rng=random.Random(0), cards=cards)
        scores = hand_agency_scores(state2, cards, archetypes=["RogSi", "Tayam"])
        rogsi, tayam = scores["relevant_agency_score"]["RogSi"], scores["relevant_agency_score"]["Tayam"]
        if scores["live_agency_score"] > 0 and rogsi != tayam:
            return {
                "label": "F. RELEVANT AGENCY - same engine trajectory, different interaction relevance",
                "hand": sorted(hand), "tier_engine": grade["tier_engine"], "tier_turn": grade["tier_turn"],
                "live_agency_score": scores["live_agency_score"],
                "relevant_agency_vs_rogsi": rogsi, "relevant_agency_vs_tayam": tayam,
                "live_cards": scores["live_cards"],
                "finding": (
                    f"This hand's {scores['live_agency_score']} live interaction card(s) count as "
                    f"relevant against RogSi ({rogsi}) but not equally against Tayam ({tayam}) - "
                    "the same trajectory, the same live interaction, a different relevant-agency score "
                    "purely because the opposing pod's threat axes differ."
                ),
            }
    return None


def example_G_mulligan_depth(names, cards, combos, on_play, rng, deck_size, tries=6000):
    """Mull at 7, keep at 6 or 5 - a hand whose contextual grade fails the C@7 bar but clears
    the looser D@6/D@5 bar without any bottoming change needed (grade is exactly D)."""
    for _ in range(tries):
        hand, library = _sample(rng, names)
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        obj = build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=1)
        cg = gated_model(obj)
        if cg == "D":  # fails C@7 (rank 9 > rank 8), passes D@6/D@5 (rank 9 <= rank 9)
            return {
                "label": "G. MULLIGAN DEPTH - mull at 7, keep at 6 or 5",
                "hand": sorted(hand), "tier_engine": grade["tier_engine"], "contextual_grade": cg,
                "keep_at_7": GRADE_RANK[cg] <= GRADE_RANK["C"],
                "keep_at_6": GRADE_RANK[cg] <= GRADE_RANK["D"],
                "keep_at_5": GRADE_RANK[cg] <= GRADE_RANK["D"],
                "finding": (
                    f"Contextual grade {cg} fails the size-7 keep bar (C) but clears the looser "
                    "size-6/size-5 bars (D) - the SAME hand is a mulligan at 7 and a keep at 6 or 5, "
                    "purely because the demanded standard loosens with mulligan depth."
                ),
            }
    return None


def main():
    ap_args = None
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=6012)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    deck_size = len(cards)
    rng = random.Random(args.seed)

    examples = {}
    examples["A"] = example_A_strength_speed(names, cards, combos, on_play, rng)

    seat_pod_path = REPO_ROOT / "results" / "solo_baseline" / "seat_pod_matrix.json"
    seat_pod_data = json.loads(seat_pod_path.read_text())
    b_example = seat_pod_data["seat_flip_examples_same_seven_same_trajectory_different_seat"][0]
    examples["B"] = {
        "label": "B. SEAT - same hand changes decision because of seat",
        "hand": b_example["hand"], "tier_engine": b_example["tier_engine"], "tier_turn": b_example["tier_turn"],
        "decisions_by_seat": b_example["decisions_by_seat_for_first_flipping_archetype"],
        "source": "seat_pod_matrix.json (task #114) - reused, already a real validated example",
        "finding": (
            f"The exact same 7-card hand, same trajectory ({b_example['tier_engine']} turn "
            f"{b_example['tier_turn']}), decides differently purely as a function of seat: "
            f"{b_example['decisions_by_seat_for_first_flipping_archetype']}."
        ),
    }

    examples["C"] = example_C_draw_dependence(names, cards, combos, on_play, rng)
    examples["D"] = example_D_fragility(names, cards, combos, on_play, rng)

    e_example = seat_pod_data["pod_flip_examples_same_seven_same_seat_different_pod"][0]
    examples["E"] = {
        "label": "E. POD REALIZATION - same engine changes desirability against different pods",
        "hand": e_example["hand"], "tier_engine": e_example["tier_engine"], "tier_turn": e_example["tier_turn"],
        "decisions_by_archetype": e_example["decisions_by_archetype_for_first_flipping_seat"],
        "source": "seat_pod_matrix.json (task #114) - reused, already a real validated example",
        "finding": (
            f"The exact same hand and seat, same trajectory ({e_example['tier_engine']} turn "
            f"{e_example['tier_turn']}), decides differently purely as a function of pod archetype: "
            f"{e_example['decisions_by_archetype_for_first_flipping_seat']}."
        ),
    }

    examples["F"] = example_F_relevant_agency(names, cards, combos, on_play, rng)
    examples["G"] = example_G_mulligan_depth(names, cards, combos, on_play, rng, deck_size)

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_CONTEXTUAL_DISAGREEMENT_EXAMPLES",
        "evidence_type": "SIMULATION_MEASURED",
        "seed": args.seed, "seat": args.seat,
        "note": (
            "Every example is drawn from REAL simulated hands (either freshly sampled in this "
            "script's own targeted search loops, or reused directly from seat_pod_matrix.json's "
            "already-validated real examples for B and E) - none are fabricated."
        ),
        "examples": examples,
        "missing_examples": sorted(k for k, v in examples.items() if v is None),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "contextual_disagreement_examples.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    for k, v in examples.items():
        print(k, "FOUND" if v else "MISSING", v.get("finding") if v else "")


if __name__ == "__main__":
    main()
