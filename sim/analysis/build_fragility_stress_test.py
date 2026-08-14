"""SIM-001 MULL-006 section 20 / 28 — fragility stress test on named trajectory families.

Applies trajectory_fragility_model.assess_fragility() (task #109's counterfactual-removal model,
reused unchanged) to the assignment's own named list of trajectory families, over real simulated
hands whose winning trajectory matches each family. This is NOT a full opponent simulation and
does NOT estimate how often opponents actually have/use removal - per the assignment, it measures
CONSEQUENCE IF ANSWERED, using the exact same disclosed counterfactual as task #109.

Family membership is determined from the winning trajectory's (tier_engine, tier_turn, mechanism)
- all already computed by trajectory_grading.grade_trajectory(), not re-derived here.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory
from trajectory_fragility_model import assess_fragility, RESILIENCE_ORDER
from opening_hand_policy import OCULUS_NAME

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


def _family_matchers():
    def mana_vault_to_tithe(grade, state):
        return (
            grade["tier_engine"] == "Smothering Tithe"
            and grade["mechanism"].startswith("rock_to_engine")
            and any(n == "Mana Vault" for (t, n, c) in state.cast_log if t < (grade["tier_turn"] or 99))
        )

    return {
        "T1 Remora": lambda g, s: g["tier_engine"] == "Mystic Remora" and g["tier_turn"] == 1,
        "T1 Sentinel": lambda g, s: g["tier_engine"] == "Esper Sentinel" and g["tier_turn"] == 1,
        "T1 Mastermind": lambda g, s: g["tier_engine"] == "Faerie Mastermind" and g["tier_turn"] == 1,
        "T1 Archivist": lambda g, s: g["tier_engine"] == "Archivist of Oghma" and g["tier_turn"] == 1,
        "T1 Rhystic": lambda g, s: g["tier_engine"] == "Rhystic Study" and g["tier_turn"] == 1,
        "T2 Rhystic": lambda g, s: g["tier_engine"] == "Rhystic Study" and g["tier_turn"] == 2,
        "T2 Tithe": lambda g, s: g["tier_engine"] == "Smothering Tithe" and g["tier_turn"] == 2,
        "T2 functional Pod": lambda g, s: g["tier_engine"] == "Birthing Pod" and g["tier_turn"] == 2,
        "early Oculus": lambda g, s: g["tier_engine"] == OCULUS_NAME and (g["tier_turn"] or 99) <= 2,
        "functional Survival": lambda g, s: g["tier_engine"] == "Survival of the Fittest",
        "tutor -> engine": lambda g, s: g["mechanism"].startswith("tutor_to_engine") or g["mechanism"].startswith("tutor_plus_accel_to_engine"),
        "Mana Vault -> Tithe": mana_vault_to_tithe,
        "dork -> engine": lambda g, s: g["mechanism"].startswith("dork_to_engine"),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=6009)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)
    matchers = _family_matchers()

    family_samples = defaultdict(list)  # family -> [assess_fragility result, ...]
    family_examples = defaultdict(list)

    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        if grade["tier_engine"] is None:
            continue
        matched = [fam for fam, fn in matchers.items() if fn(grade, state)]
        if not matched:
            continue
        result = assess_fragility(state, cards, grade["tier_engine"], grade["tier_turn"], on_play)
        for fam in matched:
            family_samples[fam].append(result)
            if len(family_examples[fam]) < 5:
                family_examples[fam].append({"hand": sorted(hand), **result})

    def _avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else None

    family_reports = {}
    for fam, results in family_samples.items():
        n = len(results)
        cards_remaining = [r["cards_remaining"] for r in results]
        strong_secondary = sum(1 for r in results if r["second_best_destination_realized"] is not None)
        stranded = sum(1 for r in results if r["hand_effectively_collapses"])
        resilience_dist = Counter(r["resilience_class"] for r in results)
        time_to_dev = [r["time_until_next_development"] for r in results if r["time_until_next_development"] is not None]
        no_known_next_dev = sum(1 for r in results if r["time_until_next_development"] is None)

        family_reports[fam] = {
            "sample_count": n,
            "avg_cards_remaining": _avg(cards_remaining),
            "min_cards_remaining": min(cards_remaining) if cards_remaining else None,
            "max_cards_remaining": max(cards_remaining) if cards_remaining else None,
            "resilience_class_distribution": dict(resilience_dist),
            "percentage_with_strong_secondary_trajectory": round(strong_secondary / n, 4) if n else None,
            "percentage_effectively_stranded": round(stranded / n, 4) if n else None,
            "avg_time_until_next_development_when_known": _avg(time_to_dev),
            "hands_with_no_known_next_development": no_known_next_dev,
            "example_hands": family_examples[fam],
        }

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_FRAGILITY_STRESS_TEST",
        "evidence_type": "SIMULATION_MEASURED",
        "sample_count": args.count, "seed": args.seed, "seat": args.seat,
        "method_note": (
            "This is a controlled COUNTERFACTUAL REMOVAL test, not a full opponent simulation, "
            "and does not estimate how often opponents actually have or use removal. It measures "
            "CONSEQUENCE IF ANSWERED - what the hand's remaining resources look like at the moment "
            "the named trajectory's primary destination comes online, as if it were answered "
            "immediately afterward. Reuses trajectory_fragility_model.assess_fragility() (task "
            "#109) unchanged, applied to real hands filtered by named family membership."
        ),
        "families_evaluated": sorted(family_reports),
        "families_with_zero_samples": sorted(set(matchers) - set(family_reports)),
        "family_reports": family_reports,
        "resilience_order_best_first": RESILIENCE_ORDER,
    }
    stress_path = REPO_ROOT / "results" / "solo_baseline" / "fragility_stress_test.json"
    stress_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {stress_path}")
    for fam, rep in family_reports.items():
        print(f"{fam}: n={rep['sample_count']} strong_secondary={rep['percentage_with_strong_secondary_trajectory']} stranded={rep['percentage_effectively_stranded']}")
    if set(matchers) - set(family_reports):
        print(f"zero-sample families: {sorted(set(matchers) - set(family_reports))}")


if __name__ == "__main__":
    main()
