"""SIM-001 SOLO-004 sections 3-4 — what separates good hands from bad hands within a land count.

Per the explicit instruction: do not assume "2 lands = keep" or any other rule going in. This
script takes the SOLO-004 dataset (opener features joined to the greedy-realized T1-T3 outcome
vector) and, for each land-count population (0/1/2/3/4+), measures the EFFECT SIZE of every
opener-visible candidate feature against the primary success outcome
(`out_t3__t3_any_strong_state`, unchanged from SOLO-003R's definition - deliberately still not a
single invented "good hand" score, just the one already-validated broad compounding-state flag
used as the headline split variable; conditional distributions in section 4 report the FULL
outcome vector, not just this one field).

Effect size definition: P(success | feature=True) - P(success | feature=False) ("lift"), reported
alongside each side's sample size and a two-proportion z-test p-value (informational, not a
pre-registered hypothesis test - useful for triaging which candidate features have enough support
to be non-noise at this sample size, not a formal significance claim).
"""
import argparse
import gzip
import json
import math
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]

SUCCESS_FIELD = "out_t3__t3_any_strong_state"

# Candidate opener-visible features to test within each land-count population - drawn from
# section 3's explicit list (T1 accel/engine/premium engine, tutor, interaction, creature count,
# color coverage, fast/temp mana, Cradle, commander support, curve, multi-engine/tutor,
# interaction density) plus the richer opener feature set section 2 asks for. Boolean/derived
# fields only (a numeric field like tutor_count is bucketed into a boolean below).
CANDIDATE_BOOL_FEATURES = [
    "opener__t1_accel_executable_now", "opener__t1_accel_creature_only",
    "opener__has_creature_accel_card", "opener__has_noncreature_persistent_accel_card",
    "opener__has_one_shot_accel_card", "opener__has_sol_ring", "opener__has_mox_family_card",
    "opener__t1_any_engine_cast", "opener__t1_premium_engine_cast", "opener__has_any_engine_card",
    "opener__has_tier_a_engine_card", "opener__has_tier_b_engine_card",
    "opener__has_premium_one_drop_card", "opener__has_cheap_engine_card",
    "opener__has_tutor_card", "opener__t1_any_tutor_cast", "opener__tutor_cheap",
    "opener__tutor_reaches_engine", "opener__tutor_reaches_combo_piece",
    "opener__has_any_interaction_card", "opener__t1_has_live_interaction",
    "opener__interaction_density_2plus", "opener__interaction_only_hand",
    "opener__has_commander_relevant_creature_2plus", "opener__all_wubg_direct",
    "opener__all_wubg_potential", "opener__utility_land_cradle",
    "opener__utility_land_ancient_tomb", "opener__utility_land_city_of_traitors",
    "opener__utility_land_gemstone_caverns", "opener__fetch_land_count",
]
CANDIDATE_NUMERIC_THRESHOLDS = {
    # feature -> threshold for a ">=" boolean split
    "opener__engine_count": 2, "opener__tutor_count": 2, "opener__interaction_count": 2,
    "opener__creature_count_in_hand": 2, "opener__distinct_colors_direct": 3,
    "opener__cards_costing_3plus": 3, "opener__accel_card_count": 2,
}


def _z_test_p(p1, n1, p2, n2):
    if n1 == 0 or n2 == 0:
        return None
    x1, x2 = p1 * n1, p2 * n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if 0 < p_pool < 1 else 0
    if se == 0:
        return None
    z = (p1 - p2) / se
    # two-sided normal approximation p-value
    return math.erfc(abs(z) / math.sqrt(2))


def _rate(rows, field):
    n = len(rows)
    if n == 0:
        return None, 0
    return sum(1 for r in rows if r.get(field)) / n, n


def effect_sizes_for_population(rows, success_field=SUCCESS_FIELD):
    results = []
    for feat in CANDIDATE_BOOL_FEATURES:
        if feat == "opener__fetch_land_count":
            continue  # handled via numeric thresholds below
        pos = [r for r in rows if r.get(feat)]
        neg = [r for r in rows if not r.get(feat)]
        p_pos, n_pos = _rate(pos, success_field)
        p_neg, n_neg = _rate(neg, success_field)
        if p_pos is None or p_neg is None:
            continue
        results.append({
            "feature": feat, "lift": p_pos - p_neg,
            "success_rate_with": p_pos, "n_with": n_pos,
            "success_rate_without": p_neg, "n_without": n_neg,
            "p_value": _z_test_p(p_pos, n_pos, p_neg, n_neg),
        })
    for feat, thresh in CANDIDATE_NUMERIC_THRESHOLDS.items():
        pos = [r for r in rows if r.get(feat, 0) >= thresh]
        neg = [r for r in rows if r.get(feat, 0) < thresh]
        p_pos, n_pos = _rate(pos, success_field)
        p_neg, n_neg = _rate(neg, success_field)
        if p_pos is None or p_neg is None:
            continue
        results.append({
            "feature": f"{feat}>={thresh}", "lift": p_pos - p_neg,
            "success_rate_with": p_pos, "n_with": n_pos,
            "success_rate_without": p_neg, "n_without": n_neg,
            "p_value": _z_test_p(p_pos, n_pos, p_neg, n_neg),
        })
    results.sort(key=lambda r: -abs(r["lift"]))
    return results


def load_rows(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def analyze(rows, land_counts):
    out = {}
    for lc in land_counts:
        subset = [r for r in rows if r["opening_hand_land_count"] == lc]
        overall_rate, n = _rate(subset, SUCCESS_FIELD)
        out[str(lc)] = {
            "n": n,
            "pct_of_population": n / len(rows) if rows else None,
            "overall_success_rate": overall_rate,
            "effect_sizes": effect_sizes_for_population(subset),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_play.jsonl.gz"))
    ap.add_argument("--draw", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_draw.jsonl.gz"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_land_population_analysis.json"))
    args = ap.parse_args()

    play_rows = load_rows(args.play)
    draw_rows = load_rows(args.draw)

    result = {
        "success_field_used": SUCCESS_FIELD,
        "note": (
            "Effect size = P(success|feature) - P(success|not feature) within each land-count "
            "population. p_value is an informational two-proportion z-test, not a pre-registered "
            "hypothesis test. All features are opener-visible (see opening_hand_features.py)."
        ),
        "play": analyze(play_rows, [0, 1, 2, 3, 4, 5]),
        "draw": analyze(draw_rows, [0, 1, 2, 3, 4, 5]),
    }
    # merge 5+ manually (5 and any higher land counts, but dataset land_count isn't capped so
    # check for 6/7 too)
    for seat_rows, seat_key in ((play_rows, "play"), (draw_rows, "draw")):
        extra = [r for r in seat_rows if r["opening_hand_land_count"] >= 5]
        overall_rate, n = _rate(extra, SUCCESS_FIELD)
        result[seat_key]["5+"] = {
            "n": n, "pct_of_population": n / len(seat_rows) if seat_rows else None,
            "overall_success_rate": overall_rate,
            "effect_sizes": effect_sizes_for_population(extra),
        }
        del result[seat_key]["5"]

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")

    for lc in ["0", "1", "2", "3", "4", "5+"]:
        d = result["play"][lc]
        print(f"\n=== PLAY land_count={lc} (n={d['n']}, {d['pct_of_population']:.1%} of pop, "
              f"success_rate={d['overall_success_rate']:.1%}) ===")
        for e in d["effect_sizes"][:8]:
            sig = "*" if (e["p_value"] is not None and e["p_value"] < 0.01) else " "
            print(f"  {sig} {e['feature']:45s} lift={e['lift']:+.3f} "
                  f"(with={e['success_rate_with']:.1%} n={e['n_with']}, "
                  f"without={e['success_rate_without']:.1%} n={e['n_without']})")


if __name__ == "__main__":
    main()
