"""SIM-001 SOLO-002 PART A — keep-everything opening-hand census.

Native Python Monte Carlo (no XMage - see opening_hand_model.py's
docstring for why). Random seven-card hands, keep every seven, develop
through end of turn 3 (turn 4 secondary) under a deck-aware greedy policy,
snapshot metrics each turn, aggregate into the PRIMARY OUTPUT TABLE and
CRITICAL SECONDARY OUTPUT (failure modes) exactly as specified.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import (
    load_deck_cards, load_deterministic_combos, COMMANDERS,
    PREMIUM_ONE_DROP_ENGINES, ACCELERATION, deck_provenance_fields, print_run_banner,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY
from opening_hand_metrics import (
    snapshot_metrics, classify_failure_mode, classify_failure_reasons_detailed, tag_archetype,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

PRIMARY_METRICS = [
    "mana_2plus", "mana_3plus", "mana_4plus", "all_wubg",
    "any_engine_active", "premium_engine_active", "two_plus_engines_active",
    "engine_plus_interaction", "development_plus_interaction",
    "Tymna the Weaver_castable", "tymna_supported",
    "Thrasios, Triton Hero_castable", "thrasios_activation_now",
    "tutor_available", "tutor_castable",
    "cradle_on_battlefield", "cradle_3plus",
    "deterministic_win_available", "deterministic_win_protected",
    "one_action_from_verified_win", "two_actions_from_verified_win",
]

# Redesigned success metrics (correctness-repair instruction: "Do not use one broad meaningful
# T3 score as the principal target. Keep it only as a secondary convenience metric.") - these are
# reported as SEPARATE headline outcomes, never collapsed into one composite label. Each maps to
# an existing per-turn snapshot field; the turn it's read at is fixed by the outcome's own name.
PRIMARY_OUTCOMES = [
    ("t1_premium_engine", 1, "premium_engine_active"),
    ("t1_2drop_engine", 1, "any_engine_active"),  # refined by t1_engine_class_breakdown below
    ("t2_engine", 2, "any_engine_active"),
    ("t2_engine_plus_interaction", 2, "engine_plus_interaction"),
    ("t3_2plus_engines", 3, "two_plus_engines_active"),
    ("t3_supported_tymna", 3, "tymna_supported"),
    ("t3_thrasios_engine_active", 3, "Thrasios, Triton Hero_on_battlefield"),
    ("t3_cradle_3plus", 3, "cradle_3plus"),
    ("t3_tutor_convertible", 3, "tutor_castable"),
    ("t3_deterministic_win_accessible", 3, "deterministic_win_available"),
]


def run_one_hand(names, rng, cards, combos, on_play, max_turn=4, priority_order=DEFAULT_PRIORITY, hold_interaction=False):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    lib = lib[7:]
    state = HandState(hand, lib, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    for t in range(1, max_turn + 1):
        develop_turn(state, cards, priority_order=priority_order, hold_interaction=hold_interaction)
        per_turn[t] = snapshot_metrics(state, cards, combos)
    per_turn["failure_mode_t3"] = classify_failure_mode(per_turn[3], state, cards)
    per_turn["failure_reasons_detailed_t3"] = classify_failure_reasons_detailed(per_turn[3], state, cards)
    per_turn["final_hand_size_t3"] = per_turn[3]["cards_in_hand"]
    per_turn["archetype_tags"] = tag_archetype(per_turn[1], per_turn[2], per_turn[3], per_turn["failure_mode_t3"])
    # raw cast_log (turn, name, class) kept only long enough to build the exact-engine-identity
    # breakdowns in aggregate() below - not written to the final output payload itself.
    per_turn["_cast_log"] = list(state.cast_log)
    return per_turn


def _t1_engine_class(cast_log):
    """Category 2: exact T1 engine class - premium one-drop / two-mana / accelerated-into -
    rather than one broad engine=true label."""
    t1_accel_used = any(name in ACCELERATION for (t, name, cls) in cast_log if t == 1)
    for (t, name, cls) in cast_log:
        if t != 1 or cls not in ("engine", "premium_engine"):
            continue
        if name in PREMIUM_ONE_DROP_ENGINES:
            return name, "premium_one_drop"
        if t1_accel_used:
            return name, "accelerated_engine"
        return name, "two_mana_engine"
    return None, None


def aggregate(results, turns=(1, 2, 3)):
    n = len(results)
    table = {}
    for metric in PRIMARY_METRICS:
        table[metric] = {}
        for t in turns:
            key = metric
            hits = sum(1 for r in results if r[t].get(key))
            table[metric][str(t)] = hits / n
    failure_counts = Counter(r["failure_mode_t3"] for r in results if r["failure_mode_t3"])
    total_failures = sum(failure_counts.values())
    failure_table = {
        k: {"count": v, "pct_of_all_hands": v / n, "pct_of_failures": (v / total_failures if total_failures else 0)}
        for k, v in failure_counts.most_common()
    }

    # ---- category 2/3: exact engine identity by turn -------------------------------------
    engine_identity_by_turn = {}
    for t in turns:
        c = Counter()
        for r in results:
            for name in r[t]["engines_active"]:
                c[name] += 1
        engine_identity_by_turn[str(t)] = {k: v / n for k, v in c.most_common()}

    t1_engine_class_counts = Counter()
    for r in results:
        _, cls = _t1_engine_class(r["_cast_log"])
        if cls:
            t1_engine_class_counts[cls] += 1
    t1_engine_class_breakdown = {k: v / n for k, v in t1_engine_class_counts.most_common()}

    # category 3: engine(s) newly deployed on turn 2 specifically, by exact card (includes a
    # commander if cast T2, since Tymna/Thrasios are modeled engines too).
    t2_new_engine_counts = Counter()
    for r in results:
        for (t, name, cls) in r["_cast_log"]:
            if t == 2 and cls in ("engine", "premium_engine", "commander"):
                t2_new_engine_counts[name] += 1
    t2_new_engine_by_card = {k: v / n for k, v in t2_new_engine_counts.most_common()}

    # category 4: T3 engine-count histogram + most frequent live-engine combinations
    t3_engine_count_hist = Counter()
    t3_engine_combo_counts = Counter()
    for r in results:
        cnt = r[3]["engine_count"]
        t3_engine_count_hist[str(min(cnt, 3)) + ("+" if cnt >= 3 else "")] += 1
        combo = tuple(sorted(r[3]["engines_active"]))
        if combo:
            t3_engine_combo_counts[combo] += 1
    t3_engine_count_histogram = {k: v / n for k, v in t3_engine_count_hist.most_common()}
    t3_top_engine_combinations = [
        {"engines": list(combo), "count": cnt, "pct_of_all_hands": cnt / n}
        for combo, cnt in t3_engine_combo_counts.most_common(15)
    ]

    # category 13: resource efficiency (persistent vs temporary) at T3
    persistent_vals = [r[3]["persistent_nonland_permanents"] for r in results]
    temp_vals = [r[3]["temporary_resources_consumed"] for r in results]
    hand_vals = [r[3]["cards_in_hand"] for r in results]
    def _mean(xs):
        return sum(xs) / len(xs) if xs else 0
    resource_efficiency_t3 = {
        "mean_persistent_nonland_permanents": _mean(persistent_vals),
        "mean_temporary_resources_consumed": _mean(temp_vals),
        "mean_cards_remaining": _mean(hand_vals),
        "pct_hands_with_any_temp_resource_used": sum(1 for v in temp_vals if v > 0) / n,
    }

    # category 14 (full taxonomy, multi-label): granular failure reasons. Restricted to hands
    # classify_failure_mode already counted as failures (its "meaningful" gate) - a tag like
    # "tutor stuck" can also fire on a hand that's fine overall (engine already covers it), and
    # counting those against pct_of_failed_hands would push it over 100%.
    total_failed_hands = sum(1 for r in results if r["failure_mode_t3"])
    detailed_failure_counts = Counter()
    for r in results:
        if not r["failure_mode_t3"]:
            continue
        for tag in r["failure_reasons_detailed_t3"]:
            detailed_failure_counts[tag] += 1
    failure_reasons_detailed_table = {
        k: {
            "count": v, "pct_of_all_hands": v / n,
            "pct_of_failed_hands": (v / total_failed_hands if total_failed_hands else 0),
        }
        for k, v in detailed_failure_counts.most_common()
    }

    # category 8: tutor target-class accessibility, per turn (rate a castable tutor could reach
    # at least one card of that class)
    tutor_target_rates = {}
    for t in turns:
        c = Counter()
        for r in results:
            for tag in r[t]["tutor_targets_accessible"]:
                c[tag] += 1
        tutor_target_rates[str(t)] = {k: v / n for k, v in c.most_common()}

    # category 15: rule-based archetype tags (starting taxonomy, not a data-derived clustering -
    # see write-up disclosure)
    archetype_counts = Counter()
    archetype_combo_counts = Counter()
    for r in results:
        for tag in r["archetype_tags"]:
            archetype_counts[tag] += 1
        archetype_combo_counts[tuple(sorted(r["archetype_tags"]))] += 1
    archetype_distribution = {k: v / n for k, v in archetype_counts.most_common()}
    archetype_top_combinations = [
        {"tags": list(combo), "count": cnt, "pct_of_all_hands": cnt / n}
        for combo, cnt in archetype_combo_counts.most_common(15)
    ]

    # ---- redesigned primary outcomes: separate named metrics, no single composite headline ----
    primary_outcomes = {}
    for outcome_name, t, field in PRIMARY_OUTCOMES:
        primary_outcomes[outcome_name] = sum(1 for r in results if r[t].get(field)) / n
    # t1_2drop_engine needs the finer t1_engine_class breakdown, not just "any engine at T1"
    primary_outcomes["t1_2drop_engine"] = t1_engine_class_breakdown.get("two_mana_engine", 0.0)
    primary_outcomes["t3_pod_functional"] = sum(1 for r in results if r[3]["birthing_pod"]["usable_now"]) / n
    primary_outcomes["t3_survival_functional"] = sum(1 for r in results if r[3]["survival_of_the_fittest"]["usable_now"]) / n
    primary_outcomes["mean_hand_resources_remaining_t3"] = resource_efficiency_t3["mean_cards_remaining"]

    return {
        "sample_size": n,
        "primary_outcomes": primary_outcomes,
        "primary_table": table,
        "failure_table": failure_table,
        "secondary_convenience_metrics": {
            "meaningful_development_rate_t3": 1 - (total_failures / n),
        },
        "engine_identity_by_turn": engine_identity_by_turn,
        "t1_engine_class_breakdown": t1_engine_class_breakdown,
        "t2_new_engine_by_card": t2_new_engine_by_card,
        "t3_engine_count_histogram": t3_engine_count_histogram,
        "t3_top_engine_combinations": t3_top_engine_combinations,
        "resource_efficiency_t3": resource_efficiency_t3,
        "failure_reasons_detailed_table": failure_reasons_detailed_table,
        "tutor_target_rates_by_turn": tutor_target_rates,
        "archetype_distribution": archetype_distribution,
        "archetype_top_combinations": archetype_top_combinations,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seat", choices=["play", "draw"], default="play",
                     help="on-the-play (skips T1 draw) or on-the-draw (Gemstone Caverns-relevant baseline)")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo002_opening_hand_census.json"))
    args = ap.parse_args()
    on_play = args.seat == "play"

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    rng = random.Random(args.seed)

    t0 = time.time()
    results = [run_one_hand(names, rng, cards, combos, on_play=on_play) for _ in range(args.count)]
    elapsed = time.time() - t0

    agg = aggregate(results)
    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_002_PART_A",
        "sample_count": args.count,
        "seed": args.seed,
        "seat": args.seat,
        "on_play": on_play,
        "elapsed_seconds": elapsed,
        "hands_per_second": args.count / elapsed if elapsed > 0 else None,
        "policy": "default_greedy",
        **agg,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({args.count} hands in {elapsed:.1f}s, {args.count/elapsed:.0f} hands/sec)")
    print(json.dumps(agg["primary_outcomes"], indent=2))
    print(json.dumps(agg["failure_table"], indent=2))


if __name__ == "__main__":
    main()
