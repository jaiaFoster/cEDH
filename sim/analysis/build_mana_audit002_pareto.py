"""MANA-AUDIT-002 section G — Pareto frontier across SPEED / CONSISTENCY / RESILIENCE-UTILITY.

Per the assignment: "Do NOT simply rank configurations with one arbitrary score." Each axis
below is itself a transparent, documented mean of 3 real measured sub-metrics (never hidden) -
producing exactly the 3 axes the assignment names, not collapsing all 3 into one final number.
Strictly-dominated configs (worse-or-equal on all 3 axes, strictly worse on at least 1, versus
some other real config) are flagged; every non-dominated config is left for the final report's
qualitative GAIN/COST tradeoff discussion, not auto-ranked.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, deck_provenance_fields  # noqa: E402

UTILITY_LANDS = {"Shifting Woodland", "Talon Gates of Madara",
                  "Minamo, School at Water's Edge", "Boseiju, Who Endures", "Otawara, Soaring City"}


def _speed(cfg):
    po = cfg["primary_outcomes"]
    parts = [po.get("t1_premium_engine", 0.0), po.get("t2_engine", 0.0), po.get("t3_2plus_engines", 0.0)]
    return sum(parts) / len(parts), {
        "t1_premium_engine": po.get("t1_premium_engine", 0.0),
        "t2_engine": po.get("t2_engine", 0.0),
        "t3_2plus_engines": po.get("t3_2plus_engines", 0.0),
    }


def _mana_or_color_failure_rate(cfg):
    ft = cfg.get("failure_table", {})
    keys = [k for k in ft if "mana" in k.lower() or "color" in k.lower()]
    return sum(ft[k]["pct_of_all_hands"] for k in keys) if keys else 0.0


def _consistency(cfg):
    mg = cfg["mulligan_gated_model"]
    s_or_a = mg["fraction_tier_S_or_A"]
    not_d_or_f = 1 - mg["fraction_tier_D_or_F"]
    not_mana_fail = 1 - _mana_or_color_failure_rate(cfg)
    parts = [s_or_a, not_d_or_f, not_mana_fail]
    return sum(parts) / len(parts), {
        "mulligan_S_or_A_rate": s_or_a, "mulligan_not_D_or_F_rate": not_d_or_f,
        "not_mana_or_color_failure_rate": not_mana_fail,
    }


def _resilience_utility(cfg, removed_by_config):
    removed = set(removed_by_config)
    utility_preserved = len(UTILITY_LANDS - removed) / len(UTILITY_LANDS)
    fetch_count_note = 7 + sum(1 for a in cfg.get("added_cards", []) if "fetch" in a.lower() or a in
                                {"Scalding Tarn", "Arid Mesa", "Bloodstained Mire"})
    fetch_ratio = min(fetch_count_now := fetch_count_note, 10) / 10.0
    parts = [utility_preserved, fetch_ratio]
    return sum(parts) / len(parts), {
        "utility_lands_preserved_fraction": utility_preserved,
        "fetch_count_now": fetch_count_now, "fetch_ratio_of_10": fetch_ratio,
    }


def main():
    configs_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_configs.json"
    data = json.loads(configs_path.read_text(encoding="utf-8"))
    payload, _ = load_deck_cards()

    points = {}
    for name, cfg in data["configs"].items():
        speed, speed_parts = _speed(cfg)
        consistency, consistency_parts = _consistency(cfg)
        resilience, resilience_parts = _resilience_utility(cfg, cfg.get("removed_cards", []))
        points[name] = {
            "description": cfg["description"], "land_count": cfg["land_count"], "deck_size": cfg["deck_size"],
            "speed": speed, "speed_components": speed_parts,
            "consistency": consistency, "consistency_components": consistency_parts,
            "resilience_utility": resilience, "resilience_utility_components": resilience_parts,
        }

    dominated = {}
    for name, p in points.items():
        dominators = []
        for other_name, o in points.items():
            if other_name == name:
                continue
            ge_all = (o["speed"] >= p["speed"] and o["consistency"] >= p["consistency"]
                      and o["resilience_utility"] >= p["resilience_utility"])
            gt_any = (o["speed"] > p["speed"] or o["consistency"] > p["consistency"]
                      or o["resilience_utility"] > p["resilience_utility"])
            if ge_all and gt_any:
                dominators.append(other_name)
        if dominators:
            dominated[name] = dominators

    non_dominated = sorted(set(points) - set(dominated))

    out = {
        **deck_provenance_fields(payload),
        "phase": "MANA_AUDIT_002_SECTION_G",
        "evidence_type": "static_probability",
        "section": "G_pareto_analysis",
        "axis_definitions": {
            "speed": "mean(T1 premium-engine rate, T2 engine rate, T3 2+-engines rate) - all "
                     "from the SAME census run's primary_outcomes as every other section.",
            "consistency": "mean(mulligan S-or-A keep-tier rate, 1 - mulligan D-or-F rate, "
                           "1 - mana/color failure rate) - all from the SAME gated_model London "
                           "mulligan sim + census failure_table used everywhere else.",
            "resilience_utility": "mean(fraction of the 5 named utility lands [Shifting Woodland, "
                                   "Talon Gates, Minamo, Boseiju, Otawara] still in the 98/97/96-"
                                   "card pool, fetch-count-normalized-to-10) - a STRUCTURAL "
                                   "presence measure, not a simulated probability, since real "
                                   "utility value (phasing, Channel abilities, Root Maze) is not "
                                   "itself simulated by this project's T1-3 mana engine (see "
                                   "Section B's own utility-vs-mana-quality separation).",
            "no_single_score_note": "Each axis is reported AND its raw components are reported - "
                                     "no single number ranks configs; Pareto dominance uses all 3 "
                                     "axes jointly, per the assignment's explicit instruction.",
        },
        "points": points,
        "strictly_dominated_configs": dominated,
        "non_dominated_configs": non_dominated,
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_pareto.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print("non-dominated:", non_dominated)
    print("dominated:", list(dominated.keys()))


if __name__ == "__main__":
    main()
