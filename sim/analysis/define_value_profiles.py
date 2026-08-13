"""SIM-001 SOLO-004 section 6 — explicit multi-objective hand-value profiles.

Per the spec: "Do not silently invent weights. Construct several explicit objective profiles."
Read literally: the requirement is not that weights must be derived rather than chosen (a
composite scoring function is inherently a value judgment about what matters), it is that the
choice must be OPEN and there must be MORE THAN ONE, so a reader can see how the recommendation
changes depending on what kind of pilot/matchup is being optimized for - never a single hidden
"the" score presented as objectively correct. Each profile's exact formula is defined here in
plain sight, built entirely from OUTCOME fields already in the SOLO-004 dataset (never opener
features - profiles score what a hand's trajectory ACHIEVED, they are not themselves predictors).

Five profiles, each a weighted sum of [0,1]-normalized outcome indicators:
  DEVELOPMENT_FIRST - early engine, compounding card advantage, commander conversion, cards kept.
  AGENCY_FIRST       - live interaction (free and paid), protection, optionality, avoiding
                       mana-shortfall-forced inaction.
  SPEED_FIRST        - earliest possible development, acceleration actually used, win pressure.
  RESILIENCE_FIRST    - card retention, multiple simultaneous strong states, avoiding resource-
                       destructive lines that don't pay off.
  BALANCED           - equal-weight blend of the four specialist profiles' own scores.

Nothing here declares one profile "correct" - section 7 (keep frontiers) and the eventual London
mulligan simulation (task 57) will show how the resulting keep/mulligan recommendation actually
shifts, or doesn't, across profiles.
"""
import argparse
import json
from pathlib import Path

from analyze_land_populations import load_rows

REPO_ROOT = Path(__file__).resolve().parents[2]


def _b(row, field):
    return 1.0 if row.get(field) else 0.0


def _tymna_tier_score(row):
    tier = row.get("out_tymna__tymna_attack_capacity_tier")
    return {"attack_capacity_high": 1.0, "attack_capacity_medium": 0.6, "attack_capacity_low": 0.2}.get(tier, 0.0)


def development_first(row):
    components = {
        "t1_engine_deployed": _b(row, "out_t1__t1_engine_deployed"),
        "t2_primary_engine_online": _b(row, "out_t2__t2_primary_engine_online"),
        "t3_strong_card_advantage": _b(row, "out_t3__t3_strong_card_advantage_state"),
        "card_engine_plus_mana_engine": _b(row, "out_comp__card_engine_plus_mana_engine"),
        "commander_conversion": max(_tymna_tier_score(row), _b(row, "out_thras__thrasios_productive")),
        "cards_retained": min(row.get("out__cards_in_hand_t3", 0) / 5.0, 1.0),
    }
    weights = {
        "t1_engine_deployed": 0.15, "t2_primary_engine_online": 0.25, "t3_strong_card_advantage": 0.25,
        "card_engine_plus_mana_engine": 0.15, "commander_conversion": 0.10, "cards_retained": 0.10,
    }
    return sum(components[k] * weights[k] for k in weights), components


def agency_first(row):
    components = {
        "t1_live_interaction": _b(row, "out_t1__t1_live_interaction"),
        "t2_dev_plus_interaction": _b(row, "out_t2__t2_development_plus_interaction"),
        "t3_strong_interaction": _b(row, "out_t3__t3_strong_interaction_state"),
        "protection_agency": _b(row, "out_extra__t3_protection_agency"),
        "t3_strong_optionality": _b(row, "out_t3__t3_strong_optionality_state"),
        "no_mana_shortfall": 1.0 - _b(row, "out__mana_shortfall_t3"),
    }
    weights = {
        "t1_live_interaction": 0.10, "t2_dev_plus_interaction": 0.20, "t3_strong_interaction": 0.25,
        "protection_agency": 0.15, "t3_strong_optionality": 0.20, "no_mana_shortfall": 0.10,
    }
    return sum(components[k] * weights[k] for k in weights), components


def speed_first(row):
    components = {
        "t1_any_tier_a_engine": _b(row, "out_t1__t1_any_tier_a_engine"),
        "t1_compound_development": _b(row, "out_t1__t1_compound_development"),
        "t2_primary_engine_online": _b(row, "out_t2__t2_primary_engine_online"),
        "deterministic_win": _b(row, "out__deterministic_win_available"),
        "one_action_from_win": _b(row, "out__one_action_from_verified_win"),
        "t3_credible_win_pressure": _b(row, "out_t3__t3_credible_win_pressure"),
    }
    weights = {
        "t1_any_tier_a_engine": 0.25, "t1_compound_development": 0.20, "t2_primary_engine_online": 0.20,
        "deterministic_win": 0.15, "one_action_from_win": 0.10, "t3_credible_win_pressure": 0.10,
    }
    return sum(components[k] * weights[k] for k in weights), components


def resilience_first(row):
    components = {
        "cards_retained": min(row.get("out__cards_in_hand_t3", 0) / 5.0, 1.0),
        "t3_strong_optionality": _b(row, "out_t3__t3_strong_optionality_state"),
        "multi_engine_plus_interaction": _b(row, "out_comp__multi_engine_plus_interaction"),
        "not_stalled": 1.0 - _b(row, "out_t3__t3_stalled"),
        "low_temp_resource_burn": 1.0 - min(row.get("out__temporary_resources_consumed_t3", 0) / 2.0, 1.0),
        "no_mana_shortfall": 1.0 - _b(row, "out__mana_shortfall_t3"),
    }
    weights = {
        "cards_retained": 0.20, "t3_strong_optionality": 0.20, "multi_engine_plus_interaction": 0.15,
        "not_stalled": 0.25, "low_temp_resource_burn": 0.10, "no_mana_shortfall": 0.10,
    }
    return sum(components[k] * weights[k] for k in weights), components


PROFILES = {
    "DEVELOPMENT_FIRST": development_first,
    "AGENCY_FIRST": agency_first,
    "SPEED_FIRST": speed_first,
    "RESILIENCE_FIRST": resilience_first,
}


def balanced(row):
    scores = {name: fn(row)[0] for name, fn in PROFILES.items()}
    return sum(scores.values()) / len(scores), scores


def score_row(row):
    out = {}
    for name, fn in PROFILES.items():
        score, _ = fn(row)
        out[name] = score
    out["BALANCED"] = sum(out.values()) / len(PROFILES)
    return out


def _corr(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx ** 0.5 * vy ** 0.5)


OPENER_FEATURES_FOR_CORR = [
    "opener__accel_card_count", "opener__has_any_accel_card", "opener__has_premium_one_drop_card",
    "opener__has_sol_ring", "opener__has_tier_a_engine_card", "opener__has_tutor_card",
    "opener__has_any_interaction_card", "opener__interaction_density_2plus",
    "opener__interaction_only_hand", "opener__t1_accel_executable_now",
    "opener__distinct_colors_potential", "opener__land_count",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_play.jsonl.gz"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_objective_profile_comparison.json"))
    args = ap.parse_args()

    rows = load_rows(args.play)
    for r in rows:
        r["_profile_scores"] = score_row(r)

    profile_names = list(PROFILES.keys()) + ["BALANCED"]
    correlations = {p: {} for p in profile_names}
    for feat in OPENER_FEATURES_FOR_CORR:
        xs = [float(r.get(feat, 0)) for r in rows]
        for p in profile_names:
            ys = [r["_profile_scores"][p] for r in rows]
            correlations[p][feat] = _corr(xs, ys)

    profile_stats = {
        p: {
            "mean": sum(r["_profile_scores"][p] for r in rows) / len(rows),
            "top_correlated_opener_features": sorted(
                ((f, c) for f, c in correlations[p].items() if c is not None),
                key=lambda t: -abs(t[1])
            )[:8],
        }
        for p in profile_names
    }

    # Where do profiles DISAGREE most? For each opener feature, the spread (max-min correlation
    # across profiles) shows which features are valued very differently depending on objective.
    disagreement = []
    for feat in OPENER_FEATURES_FOR_CORR:
        vals = {p: correlations[p][feat] for p in profile_names if correlations[p][feat] is not None}
        if len(vals) < 2:
            continue
        spread = max(vals.values()) - min(vals.values())
        disagreement.append({"feature": feat, "spread": spread, "by_profile": vals})
    disagreement.sort(key=lambda d: -d["spread"])

    result = {
        "note": (
            "Each profile is an explicit, disclosed weighted sum over OUTCOME fields (never "
            "opener features - see docstring for exact formulas/weights). Correlations here are "
            "opener-feature-vs-profile-score Pearson r, reported to show how emphasis shifts "
            "across profiles - not a claim that any one profile is correct."
        ),
        "profile_stats": profile_stats,
        "feature_disagreement_across_profiles": disagreement,
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")

    print("\n=== Profile means ===")
    for p in profile_names:
        print(f"  {p:20s} mean={profile_stats[p]['mean']:.3f}")

    print("\n=== Top opener-feature correlations by profile ===")
    for p in profile_names:
        print(f"\n{p}:")
        for f, c in profile_stats[p]["top_correlated_opener_features"]:
            print(f"  {f:40s} r={c:+.3f}")

    print("\n=== Features where profiles disagree most (correlation spread) ===")
    for d in disagreement[:8]:
        print(f"  {d['feature']:40s} spread={d['spread']:.3f}  " +
              "  ".join(f"{p}={v:+.2f}" for p, v in d["by_profile"].items()))


if __name__ == "__main__":
    main()
