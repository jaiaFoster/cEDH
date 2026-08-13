"""SIM-001 SOLO-004 sections 17-18 — tutor-specific and interaction-specific analysis.

Distinguishes "tutor present" from "tutor converts this hand into a functional trajectory" per
individual tutor card (not tutors-as-a-class), and does the same rigor for interaction: does
interaction density/type actually change outcomes, and does it hold up once real liveness
conditions (a Force of Will that can't be pitched, a Fierce Guardianship with no commander out -
both already correctly modeled by interaction_model.py since SOLO-003) are respected.

Reuses the existing SOLO-004 play dataset directly - opener__tutor_names is recorded per hand, so
per-tutor breakdowns don't need new simulation.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from analyze_land_populations import load_rows
from opening_hand_model import TUTOR_TARGETS

REPO_ROOT = Path(__file__).resolve().parents[2]


def tutor_analysis(rows):
    by_tutor = defaultdict(list)
    for r in rows:
        for name in r.get("opener__tutor_names", []):
            by_tutor[name].append(r)

    n_total = len(rows)
    out = {}
    for name, subset in sorted(by_tutor.items(), key=lambda kv: -len(kv[1])):
        n = len(subset)
        t1_castable = sum(1 for r in subset if name in r.get("opener__t1_tutor_cast", [])) / n
        strong_state_rate = sum(1 for r in subset if r["out_t3__t3_any_strong_state"]) / n
        tutor_castable_t3_rate = sum(1 for r in subset if r["out__tutor_castable_t3"]) / n
        stranded_rate = sum(1 for r in subset if "stranded_tutor" in r.get("outcome_tags", [])) / n
        cards_remaining = sum(r["out__cards_in_hand_t3"] for r in subset) / n
        out[name] = {
            "opener_frequency": n / n_total,
            "n": n,
            "target_classes": sorted(TUTOR_TARGETS.get(name, [])),
            "t1_castable_rate": t1_castable,
            "t3_tutor_still_castable_rate": tutor_castable_t3_rate,
            "t3_strong_state_rate_when_present": strong_state_rate,
            "stranded_tutor_rate": stranded_rate,
            "mean_cards_remaining_t3": cards_remaining,
        }

    no_tutor = [r for r in rows if not r.get("opener__tutor_names")]
    out["_NO_TUTOR_BASELINE"] = {
        "n": len(no_tutor),
        "t3_strong_state_rate_when_present": sum(1 for r in no_tutor if r["out_t3__t3_any_strong_state"]) / len(no_tutor),
    }
    return out


def interaction_analysis(rows):
    def rate(subset, field):
        return sum(1 for r in subset if r.get(field)) / len(subset) if subset else None

    none_ = [r for r in rows if r["opener__interaction_count"] == 0]
    one_ = [r for r in rows if r["opener__interaction_count"] == 1]
    two_plus = [r for r in rows if r["opener__interaction_count"] >= 2]
    only_hand = [r for r in rows if r["opener__interaction_only_hand"]]
    dev_plus_interaction = [r for r in rows if r["opener__has_any_interaction_card"] and (
        r["opener__has_any_engine_card"] or r["opener__has_any_accel_card"] or r["opener__has_tutor_card"]
    )]
    live_paid = [r for r in rows if r["out_extra__t3_live_paid_interaction"]]
    live_free_only = [r for r in rows if r["out_t3__t3_strong_interaction_state"] and not r["out_extra__t3_live_paid_interaction"]]

    return {
        "zero_interaction_cards": {"n": len(none_), "t3_strong_state_rate": rate(none_, "out_t3__t3_any_strong_state")},
        "one_interaction_card": {"n": len(one_), "t3_strong_state_rate": rate(one_, "out_t3__t3_any_strong_state")},
        "two_plus_interaction_cards": {"n": len(two_plus), "t3_strong_state_rate": rate(two_plus, "out_t3__t3_any_strong_state")},
        "interaction_only_hand": {"n": len(only_hand), "t3_strong_state_rate": rate(only_hand, "out_t3__t3_any_strong_state")},
        "development_plus_interaction": {
            "n": len(dev_plus_interaction),
            "t3_strong_state_rate": rate(dev_plus_interaction, "out_t3__t3_any_strong_state"),
            "t3_strong_interaction_state_rate": rate(dev_plus_interaction, "out_t3__t3_strong_interaction_state"),
        },
        "live_paid_interaction_t3": {
            "n": len(live_paid),
            "t3_strong_state_rate": rate(live_paid, "out_t3__t3_any_strong_state"),
            "note": "paid interaction actually live at T3 (has_live_interaction AND NOT free_or_alt_cost_interaction_live)",
        },
        "live_free_or_alt_cost_interaction_t3": {
            "n": len(live_free_only),
            "note": "approximation via t3_strong_interaction_state minus the live-paid subset - see out_extra__t3_live_paid_interaction",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_opening_hand_dataset_play.jsonl.gz"))
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_tutor_interaction_analysis.json"))
    args = ap.parse_args()

    rows = load_rows(args.play)
    result = {"tutor_analysis": tutor_analysis(rows), "interaction_analysis": interaction_analysis(rows)}

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")

    print("\n=== Per-tutor breakdown (sorted by frequency) ===")
    for name, d in result["tutor_analysis"].items():
        if name.startswith("_"):
            continue
        print(f"  {name:28s} freq={d['opener_frequency']:.2%}  strong_state={d['t3_strong_state_rate_when_present']:.1%}  "
              f"stranded={d['stranded_tutor_rate']:.1%}  t1_castable={d['t1_castable_rate']:.1%}")
    baseline = result["tutor_analysis"]["_NO_TUTOR_BASELINE"]
    print(f"  {'(no tutor in hand)':28s} n={baseline['n']}  strong_state={baseline['t3_strong_state_rate_when_present']:.1%}")

    print("\n=== Interaction breakdown ===")
    for k, d in result["interaction_analysis"].items():
        print(f"  {k}: {d}")


if __name__ == "__main__":
    main()
