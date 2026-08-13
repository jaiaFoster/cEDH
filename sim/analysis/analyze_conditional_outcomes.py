"""SIM-001 SOLO-004 section 4 — conditional outcome distributions, not just correlations.

For a curated list of structural hand classes (section 3's named examples: "1 land + T1 dork" vs
"1 land, no acceleration"; "3 lands + engine" vs "3 lands, weak business"; etc.), report the FULL
outcome vector - not a single lift number - so we learn the actual downstream consequences of
keeping each hand type: T2 engine rate, T2 engine+interaction rate, T3 strong-state rate, T3
stalled rate, mana-shortfall rate, and mean cards remaining at T3.
"""
import argparse
import json
from pathlib import Path

from analyze_land_populations import load_rows

REPO_ROOT = Path(__file__).resolve().parents[2]

OUTCOME_FIELDS = {
    "t2_engine_rate": "out_t2__t2_primary_engine_online",
    "t2_engine_plus_interaction_rate": "out_t2__t2_development_plus_interaction",
    "t3_strong_state_rate": "out_t3__t3_any_strong_state",
    "t3_strong_card_advantage_rate": "out_t3__t3_strong_card_advantage_state",
    "t3_credible_win_pressure_rate": "out_t3__t3_credible_win_pressure",
    "t3_stalled_rate": "out_t3__t3_stalled",
    "mana_shortfall_rate": "out__mana_shortfall_t3",
}
MEAN_FIELDS = {
    "mean_cards_remaining_t3": "out__cards_in_hand_t3",
    "mean_mana_capacity_t3": "out__total_mana_capacity_t3",
}


def _summarize(rows):
    n = len(rows)
    if n == 0:
        return {"n": 0}
    out = {"n": n}
    for label, field in OUTCOME_FIELDS.items():
        out[label] = sum(1 for r in rows if r.get(field)) / n
    for label, field in MEAN_FIELDS.items():
        out[label] = sum(r.get(field, 0) for r in rows) / n
    return out


# (label, land_count_filter_or_None, predicate) - predicate receives a row, applied AFTER the
# land-count filter (None = no land-count restriction).
CLASSES = [
    ("1_land_with_t1_dork", 1, lambda r: r["opener__t1_accel_executable_now"]),
    ("1_land_no_acceleration", 1, lambda r: not r["opener__has_any_accel_card"]),
    ("1_land_persistent_accel_only", 1, lambda r: (
        r["opener__has_noncreature_persistent_accel_card"] and not r["opener__has_one_shot_accel_card"]
    )),
    ("1_land_temporary_accel_only", 1, lambda r: (
        r["opener__has_one_shot_accel_card"] and not r["opener__has_noncreature_persistent_accel_card"]
    )),
    ("2_land_with_engine", 2, lambda r: r["opener__has_any_engine_card"]),
    ("2_land_no_engine", 2, lambda r: not r["opener__has_any_engine_card"]),
    ("2_land_with_tutor", 2, lambda r: r["opener__has_tutor_card"]),
    ("2_land_interaction_only", 2, lambda r: r["opener__interaction_only_hand"]),
    ("2_land_with_t1_development", 2, lambda r: (
        r["opener__t1_any_engine_cast"] or r["opener__t1_accel_executable_now"]
    )),
    ("3_land_with_engine", 3, lambda r: r["opener__has_any_engine_card"]),
    ("3_land_with_acceleration", 3, lambda r: r["opener__has_any_accel_card"]),
    ("3_land_excellent_business", 3, lambda r: (
        r["opener__has_any_engine_card"] or r["opener__has_tutor_card"]
    ) and r["opener__has_any_interaction_card"]),
    ("3_land_weak_business", 3, lambda r: (
        not r["opener__has_any_engine_card"] and not r["opener__has_tutor_card"]
        and not r["opener__has_any_accel_card"]
    )),
    ("4plus_land_premium_engine", None, lambda r: (
        r["opening_hand_land_count"] >= 4 and r["opener__has_premium_one_drop_card"]
    )),
    ("4plus_land_any_engine_no_premium", None, lambda r: (
        r["opening_hand_land_count"] >= 4 and r["opener__has_any_engine_card"]
        and not r["opener__has_premium_one_drop_card"]
    )),
    ("4plus_land_no_business", None, lambda r: (
        r["opening_hand_land_count"] >= 4 and not r["opener__has_any_engine_card"]
        and not r["opener__has_tutor_card"] and not r["opener__has_any_accel_card"]
    )),
]


def analyze(rows):
    out = {}
    for label, lc, pred in CLASSES:
        base = [r for r in rows if lc is None or r["opening_hand_land_count"] == lc]
        matched = [r for r in base if pred(r)]
        unmatched = [r for r in base if not pred(r)]
        out[label] = {"matches": _summarize(matched), "complement_within_same_land_count": _summarize(unmatched)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_play.jsonl.gz"))
    ap.add_argument("--draw", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_draw.jsonl.gz"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_conditional_hand_outcomes.json"))
    args = ap.parse_args()

    play_rows = load_rows(args.play)
    draw_rows = load_rows(args.draw)
    result = {"play": analyze(play_rows), "draw": analyze(draw_rows)}

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")

    for label, _, _ in CLASSES:
        m = result["play"][label]["matches"]
        c = result["play"][label]["complement_within_same_land_count"]
        print(f"\n{label}: matches n={m['n']}, complement n={c['n']}")
        for k in OUTCOME_FIELDS:
            mv = m.get(k)
            cv = c.get(k)
            if mv is None or cv is None:
                continue
            print(f"  {k:35s} match={mv:.1%}  complement={cv:.1%}  delta={mv - cv:+.1%}")


if __name__ == "__main__":
    main()
