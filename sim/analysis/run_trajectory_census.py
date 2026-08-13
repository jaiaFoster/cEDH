"""SIM-001 SOLO-003 PART A — early-game trajectory census (keep-everything, no mulligan).

Uses the SOLO-002R-corrected mana/rules engine plus SOLO-003's real alternate-cost interaction
model and trajectory metrics (trajectory_metrics.py). Random seven-card hands, keep every seven,
develop through end of turn 3 under the greedy policy, snapshot trajectory metrics each turn,
aggregate into: the primary trajectory table, land-count stratification (0/1/2/3/4/5+), dedicated
1-land/2-land audits, the revised (outcome + causal) failure taxonomy, trajectory-family
distribution, and Tymna/Thrasios conditional metrics. Per the SOLO-003 conceptual correction,
no single composite score drives any of this - see trajectory_metrics.py's docstrings.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_policy import HandState, develop_turn, _is_land
from opening_hand_metrics import snapshot_metrics
import trajectory_metrics as tm

REPO_ROOT = Path(__file__).resolve().parents[2]

PRIMARY_TRAJECTORY_FIELDS_T1 = [
    "t1_any_tier_a_engine", "t1_accelerated_two_drop", "t1_mana_creature", "t1_persistent_rock",
    "t1_multiple_persistent_mana_sources", "t1_burst_mana_used", "t1_acceleration_retaining_resources",
    "t1_engine_deployed", "t1_live_interaction", "t1_compound_development",
]
PRIMARY_TRAJECTORY_FIELDS_T2 = [
    "t2_primary_engine_online", "t2_infrastructure_online_supported", "t2_development_plus_interaction",
]
PRIMARY_TRAJECTORY_FIELDS_T3 = [
    "t3_strong_card_advantage_state", "t3_strong_mana_state", "t3_strong_conversion_state",
    "t3_strong_interaction_state", "t3_strong_optionality_state", "t3_credible_win_pressure",
    "t3_any_strong_state", "t3_stalled",
]
COMPOUNDING_FIELDS = [
    "card_engine_plus_mana_engine", "card_engine_plus_interaction", "card_engine_plus_tutor",
    "mana_engine_plus_tutor", "cradle_plus_creature_infrastructure", "survival_supported",
    "pod_supported", "tutor_plus_resources_to_deploy", "engine_plus_win_conversion",
    "multi_engine_plus_interaction",
]


def run_one_hand(names, rng, cards, combos, on_play, max_turn=3):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    lib = lib[7:]
    # SOLO-003 section 11 stratifies by OPENING-HAND land count (0-7, as actually dealt) - this
    # is deliberately captured BEFORE any development, and is NOT the same thing as
    # len(state.lands) after T3 (which is structurally capped at 3, since only 3 land drops are
    # even possible in a 3-turn horizon - a 5-land opener still only gets 3 of them down by T3,
    # with 2 sitting dead in hand, which is exactly the opportunity-cost question section 14 asks
    # about, not something the T3 battlefield count could ever reveal on its own).
    opening_hand_land_count = sum(1 for c in hand if _is_land(c, cards))
    state = HandState(hand, lib, on_play=on_play, rng=rng, cards=cards)
    snaps = {}
    for t in range(1, max_turn + 1):
        develop_turn(state, cards)
        snaps[t] = snapshot_metrics(state, cards, combos)
    m1, m2, m3 = snaps[1], snaps[2], snaps[3]
    t1 = tm.t1_metrics(state, cards, m1)
    t2 = tm.t2_quality_metrics(state, cards, m2)
    t3s = tm.t3_strong_state_metrics(state, cards, m3)
    comp = tm.compounding_state_metrics(state, cards, m3)
    tymna = tm.tymna_attack_capacity(state, cards, None)
    thras = tm.thrasios_productivity(state, cards, m3)
    outcome_tags, causal_tags = tm.classify_trajectory_failure(m1, m2, m3, state, cards)
    family_tags = tm.trajectory_family_tags(state, cards, m1, m2, m3)
    return {
        "opening_hand_land_count": opening_hand_land_count,
        "lands_played_by_t3": len(state.lands),  # diagnostic only - structurally capped at 3, see above
        "t1": t1, "t2": t2, "t3s": t3s, "comp": comp,
        "tymna": tymna, "thras": thras,
        "outcome_tags": outcome_tags, "causal_tags": causal_tags, "family_tags": family_tags,
        "m1": m1, "m2": m2, "m3": m3,
    }


def _rate(results, getter):
    n = len(results)
    return sum(1 for r in results if getter(r)) / n if n else None


def _land_bucket(n):
    return str(n) if n <= 4 else "5+"


def aggregate(results):
    n = len(results)
    primary_table = {
        "t1": {k: _rate(results, lambda r, k=k: r["t1"].get(k)) for k in PRIMARY_TRAJECTORY_FIELDS_T1},
        "t2": {k: _rate(results, lambda r, k=k: r["t2"].get(k)) for k in PRIMARY_TRAJECTORY_FIELDS_T2},
        "t3": {k: _rate(results, lambda r, k=k: r["t3s"].get(k)) for k in PRIMARY_TRAJECTORY_FIELDS_T3},
    }
    compounding_table = {k: _rate(results, lambda r, k=k: r["comp"].get(k)) for k in COMPOUNDING_FIELDS}

    land_buckets = ["0", "1", "2", "3", "4", "5+"]
    land_strat = {}
    for b in land_buckets:
        subset = [r for r in results if _land_bucket(r["opening_hand_land_count"]) == b]
        if not subset:
            land_strat[b] = {"n": 0}
            continue
        land_strat[b] = {
            "n": len(subset),
            "pct_of_population": len(subset) / n,
            "t1_premium_engine": _rate(subset, lambda r: r["t1"].get("t1_any_tier_a_engine")),
            "t1_meaningful_development": _rate(subset, lambda r: r["m1"]["mana_2plus"] or r["t1"].get("t1_engine_deployed")),
            "t2_primary_engine": _rate(subset, lambda r: r["t2"].get("t2_primary_engine_online")),
            "t2_infrastructure_online": _rate(subset, lambda r: r["t2"].get("t2_infrastructure_online_supported")),
            "t2_dev_plus_interaction": _rate(subset, lambda r: r["t2"].get("t2_development_plus_interaction")),
            "t3_strong_compounding_state": _rate(subset, lambda r: r["t3s"].get("t3_any_strong_state")),
            "t3_tutor_convertible": _rate(subset, lambda r: r["m3"]["tutor_castable"]),
            "t3_credible_win_pressure": _rate(subset, lambda r: r["t3s"].get("t3_credible_win_pressure")),
            "t3_stalled": _rate(subset, lambda r: r["t3s"].get("t3_stalled")),
            "mean_cards_remaining_t3": sum(r["m3"]["cards_in_hand"] for r in subset) / len(subset),
        }

    # ---- dedicated 1-land audit: break down by acceleration/tutor/engine/interaction/utility present ----
    one_land = [r for r in results if r["opening_hand_land_count"] == 1]
    one_land_audit = {}
    if one_land:
        one_land_audit = {
            "n": len(one_land),
            "with_mana_creature_t1_rate": _rate(one_land, lambda r: r["t1"].get("t1_mana_creature")),
            "with_persistent_rock_t1_rate": _rate(one_land, lambda r: r["t1"].get("t1_persistent_rock")),
            "with_burst_mana_t1_rate": _rate(one_land, lambda r: r["t1"].get("t1_burst_mana_used")),
            "strong_state_rate_overall": _rate(one_land, lambda r: r["t3s"].get("t3_any_strong_state")),
            "strong_state_rate_with_t1_accel": _rate(
                [r for r in one_land if r["t1"].get("t1_mana_creature") or r["t1"].get("t1_persistent_rock") or r["t1"].get("t1_burst_mana_used")],
                lambda r: r["t3s"].get("t3_any_strong_state"),
            ),
            "strong_state_rate_without_t1_accel": _rate(
                [r for r in one_land if not (r["t1"].get("t1_mana_creature") or r["t1"].get("t1_persistent_rock") or r["t1"].get("t1_burst_mana_used"))],
                lambda r: r["t3s"].get("t3_any_strong_state"),
            ),
            "stalled_rate": _rate(one_land, lambda r: r["t3s"].get("t3_stalled")),
        }

    # ---- dedicated 2-land audit: break down by color coverage / accel / engine / interaction / tutor ----
    two_land = [r for r in results if r["opening_hand_land_count"] == 2]
    two_land_audit = {}
    if two_land:
        def _full_color_by_t3(r):
            return r["m1"]["all_wubg"] or r["m2"]["all_wubg"] or r["m3"]["all_wubg"]
        all_wubg_2l = [r for r in two_land if _full_color_by_t3(r)]
        not_all_wubg_2l = [r for r in two_land if not _full_color_by_t3(r)]
        two_land_audit = {
            "n": len(two_land),
            "strong_state_rate_overall": _rate(two_land, lambda r: r["t3s"].get("t3_any_strong_state")),
            "strong_state_rate_full_color_by_t3": _rate(all_wubg_2l, lambda r: r["t3s"].get("t3_any_strong_state")),
            "strong_state_rate_color_screwed": _rate(not_all_wubg_2l, lambda r: r["t3s"].get("t3_any_strong_state")),
            "deceptive_two_land_rate": _rate(two_land, lambda r: "deceptive_two_land_hand" in r["family_tags"]),
            "engine_by_t2_rate": _rate(two_land, lambda r: r["t2"].get("t2_primary_engine_online") or r["m2"]["any_engine_active"]),
            "tutor_convertible_t3_rate": _rate(two_land, lambda r: r["m3"]["tutor_castable"]),
            "live_interaction_t3_rate": _rate(two_land, lambda r: r["m3"]["has_live_interaction"]),
        }

    # ---- 3+/4/5+ opportunity-cost comparison ----
    opportunity_cost = {}
    for b in ("3", "4", "5+"):
        subset = [r for r in results if _land_bucket(r["opening_hand_land_count"]) == b]
        if not subset:
            continue
        opportunity_cost[b] = {
            "n": len(subset),
            "t1_engine_rate": _rate(subset, lambda r: r["t1"].get("t1_engine_deployed")),
            "tutor_convertible_t3_rate": _rate(subset, lambda r: r["m3"]["tutor_castable"]),
            "live_interaction_t3_rate": _rate(subset, lambda r: r["m3"]["has_live_interaction"]),
            "mean_cards_remaining_t3": sum(r["m3"]["cards_in_hand"] for r in subset) / len(subset),
            "strong_state_rate": _rate(subset, lambda r: r["t3s"].get("t3_any_strong_state")),
            "stalled_rate": _rate(subset, lambda r: r["t3s"].get("t3_stalled")),
            "flooded_hand_rate": _rate(subset, lambda r: "flooded_hand" in r["family_tags"]),
        }

    outcome_counts = Counter()
    causal_counts = Counter()
    family_counts = Counter()
    tymna_tier_counts = Counter()
    for r in results:
        for tag in r["outcome_tags"]:
            outcome_counts[tag] += 1
        for tag in r["causal_tags"]:
            causal_counts[tag] += 1
        for tag in r["family_tags"]:
            family_counts[tag] += 1
        tymna_tier_counts[r["tymna"]["tymna_attack_capacity_tier"] or "not_deployed"] += 1

    thrasios_productive_rate = _rate(results, lambda r: r["thras"]["thrasios_productive"])

    return {
        "sample_size": n,
        "primary_trajectory_table": primary_table,
        "compounding_state_table": compounding_table,
        "land_count_stratification": land_strat,
        "one_land_audit": one_land_audit,
        "two_land_audit": two_land_audit,
        "opportunity_cost_3plus": opportunity_cost,
        "outcome_failure_distribution": {k: v / n for k, v in outcome_counts.most_common()},
        "causal_diagnosis_distribution": {k: v / n for k, v in causal_counts.most_common()},
        "trajectory_family_distribution": {k: v / n for k, v in family_counts.most_common()},
        "tymna_attack_capacity_distribution": {k: v / n for k, v in tymna_tier_counts.most_common()},
        "thrasios_productive_rate_t3": thrasios_productive_rate,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo003_trajectory_census.json"))
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
        "phase": "SIM_001_SOLO_003_PART_A_TRAJECTORY_CENSUS",
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
    print(json.dumps(agg["primary_trajectory_table"], indent=2))


if __name__ == "__main__":
    main()
