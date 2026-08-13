"""SIM-001 SOLO-002 PART B — derive candidate mulligan heuristics from the Part A census.

Only run after Part A (see run_opening_hand_census.py) - per the user's spec, "Do not define
the final keep policy before seeing the opening-hand census." This script re-simulates the same
population (same seed, same policy) but additionally records, for each hand, features observable
from the RAW SEVEN CARDS BEFORE ANY TURN IS PLAYED (the only information actually available at a
real mulligan decision point) alongside the T3 outcome the greedy policy achieved with that hand.
It then reports simple conditional-probability lifts (P(outcome | feature) - P(outcome | not
feature)) for each candidate feature against several T3 success outcomes, and encodes the
resulting four candidate policies (A-D) used by Part C/D.
"""
import json
import random
import sys
import time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import (
    load_deck_cards, load_deterministic_combos, parse_cost,
    TUTORS, INTERACTION_CASTABLE, ENGINES, PREMIUM_ONE_DROP_ENGINES, ACCELERATION,
    LAND_COLOR_SETS, GENERIC_LANDS, CRADLE, COLORS, deck_provenance_fields, print_run_banner,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY
from opening_hand_metrics import snapshot_metrics, classify_failure_mode

REPO_ROOT = Path(__file__).resolve().parents[2]


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def raw_hand_features(hand, cards):
    """Features computable from the 7 cards alone, before any land is played or spell cast -
    i.e. what a real mulligan decision actually has access to."""
    lands = [c for c in hand if _is_land(c, cards)]
    nonlands = [c for c in hand if c not in lands]
    colors = set()
    for l in lands:
        colors |= LAND_COLOR_SETS.get(l, set())
    cheap_engines = []
    for c in nonlands:
        if c in ENGINES:
            gen, pips, x = parse_cost(cards[c]["mana_cost"])
            if (gen + len(pips)) <= 2:
                cheap_engines.append(c)
    creature_count = sum(1 for c in nonlands if "Creature" in cards[c]["type"])
    return {
        "land_count": len(lands),
        "land_count_2plus": len(lands) >= 2,
        "land_count_3plus": len(lands) >= 3,
        "colors_in_lands": len(colors),
        "all_wubg_in_lands": set(COLORS) <= colors,
        "has_cheap_engine": len(cheap_engines) > 0,
        "has_premium_one_drop": any(c in PREMIUM_ONE_DROP_ENGINES for c in nonlands),
        "has_any_engine_card": any(c in ENGINES for c in nonlands),
        "has_tutor": any(c in TUTORS for c in nonlands),
        "has_interaction": any(c in INTERACTION_CASTABLE for c in nonlands),
        "has_acceleration": any(c in ACCELERATION for c in nonlands),
        "creature_count_2plus": creature_count >= 2,
        "has_cradle_or_creature": (CRADLE in hand) or creature_count >= 1,
        "nonland_count_5plus": len(nonlands) >= 5,  # proxy for "flooded/light on lands"
    }


def run_one(names, rng, cards, combos, on_play, max_turn=3):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    lib = lib[7:]
    feats = raw_hand_features(hand, cards)
    state = HandState(hand, lib, on_play=on_play, rng=rng, cards=cards)
    m3 = None
    for t in range(1, max_turn + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        m3 = snapshot_metrics(state, cards, combos)
    failure_mode = classify_failure_mode(m3, state, cards)
    outcomes = {
        "meaningful_t3": failure_mode is None,
        "any_engine_active_t3": m3["any_engine_active"],
        "tutor_castable_t3": m3["tutor_castable"],
        "has_live_interaction_t3": m3["has_live_interaction"],
        "combo_progress_t3": m3["deterministic_win_available"] or m3["one_action_from_verified_win"],
        "cards_remaining_2plus_t3": m3["cards_in_hand"] >= 2,
    }
    return feats, outcomes


def correlation_table(records):
    """records: list of (feats, outcomes). Returns, per feature, per outcome: lift = P(outcome|feat)-P(outcome|not feat).
    Restricted to genuinely boolean features - an int feature (land_count, colors_in_lands)
    branching on Python truthiness would silently collapse to a ">=1" indicator and duplicate/
    confuse the explicit *_2plus/_3plus boolean buckets already provided."""
    feature_names = [k for k, v in records[0][0].items() if isinstance(v, bool)]
    outcome_names = list(records[0][1].keys())
    table = {}
    for fname in feature_names:
        table[fname] = {}
        for oname in outcome_names:
            with_f = [o[oname] for f, o in records if f[fname]]
            without_f = [o[oname] for f, o in records if not f[fname]]
            p_with = sum(with_f) / len(with_f) if with_f else None
            p_without = sum(without_f) / len(without_f) if without_f else None
            table[fname][oname] = {
                "p_given_feature": p_with,
                "p_given_not_feature": p_without,
                "lift": (p_with - p_without) if (p_with is not None and p_without is not None) else None,
                "feature_prevalence": sum(1 for f, _ in records if f[fname]) / len(records),
            }
    return table


# ---- Part D candidate keep policies, encoded on raw hand features (used by run_mulligan_sim.py) ----
def policy_engine_first(feats):
    """Policy A: prioritize any engine access + reasonable mana."""
    return feats["land_count_2plus"] and (feats["has_any_engine_card"] or feats["has_acceleration"])


def policy_agency_first(feats):
    """Policy B: development AND interaction both represented."""
    return feats["land_count_2plus"] and (feats["has_any_engine_card"] or feats["has_acceleration"]) and (
        feats["has_interaction"] or feats["has_tutor"]
    )


def policy_speed_first(feats):
    """Policy C: maximize raw T1/T2 mana development, engines secondary."""
    return feats["land_count_2plus"] or feats["has_acceleration"]


def policy_tutor_inclusive(feats):
    """Policy D: tutor access counted as a partial engine-access equivalent."""
    return feats["land_count_2plus"] and (
        feats["has_any_engine_card"] or feats["has_acceleration"] or feats["has_tutor"]
    )


CANDIDATE_POLICIES = {
    "A_engine_first": policy_engine_first,
    "B_agency_first": policy_agency_first,
    "C_speed_first": policy_speed_first,
    "D_tutor_inclusive": policy_tutor_inclusive,
}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--on-play", action="store_true", default=True)
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo002_mulligan_heuristics.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    rng = random.Random(args.seed)

    t0 = time.time()
    records = [run_one(names, rng, cards, combos, on_play=args.on_play) for _ in range(args.count)]
    elapsed = time.time() - t0

    corr = correlation_table(records)

    policy_stats = {}
    for pname, pfn in CANDIDATE_POLICIES.items():
        kept = [r for r in records if pfn(r[0])]
        policy_stats[pname] = {
            "keep_rate": len(kept) / len(records),
            "meaningful_t3_rate_if_kept": sum(1 for f, o in kept if o["meaningful_t3"]) / len(kept) if kept else None,
            "meaningful_t3_rate_unfiltered": sum(1 for f, o in records if o["meaningful_t3"]) / len(records),
        }

    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_002_PART_B",
        "sample_count": args.count,
        "seed": args.seed,
        "on_play": args.on_play,
        "elapsed_seconds": elapsed,
        "note": (
            "Features are computed on the raw 7-card hand only, before any land drop or cast - "
            "matching what a real mulligan decision can actually see. Lift = P(T3 outcome | "
            "feature present) - P(T3 outcome | feature absent), over the SAME keep-everything "
            "population as Part A (no mulliganing here - see run_mulligan_sim.py for Part C)."
        ),
        "correlation_table": corr,
        "candidate_policy_quicklook": policy_stats,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({args.count} hands in {elapsed:.1f}s)")

    # print a compact ranked-lift summary for the "meaningful_t3" outcome specifically
    ranked = sorted(corr.items(), key=lambda kv: abs(kv[1]["meaningful_t3"]["lift"] or 0), reverse=True)
    print("\nFeature lift on meaningful_t3 (ranked by |lift|):")
    for fname, ov in ranked:
        lift = ov["meaningful_t3"]["lift"]
        prev = ov["meaningful_t3"]["feature_prevalence"]
        print(f"  {fname:28s} lift={lift:+.3f}  prevalence={prev:.3f}")
    print("\nCandidate policy quicklook:")
    print(json.dumps(policy_stats, indent=2))


if __name__ == "__main__":
    main()
