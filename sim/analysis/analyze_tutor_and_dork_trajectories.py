"""SIM-001 MULL-005 section 9-ish — tutor virtual-engine analysis + dork-to-engine analysis.

Governing question for tutors, per the assignment (rejecting SOLO-004's blanket "tutors are
negative" conclusion as insufficient): "Can this tutor legally and economically become a
meaningful engine on T1/T2?" This module answers that PER TUTOR CARD, not for "tutors" as one
undifferentiated class - Vampiric Tutor (CMC1, instant-speed in real Magic, cheap here) and
Survival of the Fittest (CMC2 enchantment, itself a Tier-B engine AND a tutor) are structurally
different animals from Demonic Tutor or Chord of Calling, and get measured individually.

For each tutor card actually held in a hand, using trajectory_best (the bounded search's result -
the search explicitly tries forcing that hand's tutor toward each disclosed high-value target, so
"can this tutor become an engine" is answered by whether the search's best line ever cast it into
one), a hand is bucketed into exactly one outcome:
  - tutor_to_t1_engine:  best tier S, mechanism contains "tutor" (rare / near-impossible given real
    CMCs, included for completeness rather than expectation)
  - tutor_to_t2_engine:  best tier A, mechanism contains "tutor" - the case MULL-005 cares about
  - tutor_live_but_delayed: best tier B or C, mechanism contains "tutor" - a real engine, just late
  - tutor_stranded: best tier D or F, OR best tier >= B with a mechanism that does NOT involve the
    tutor at all - the tutor never became a meaningful engine in the best line this search found
  - superseded_by_commander: best mechanism is commander_engine (a productive commander was reached
    without ever needing the tutor) - the tutor was irrelevant to the best line, not "stranded" in
    the failure sense, but also not the reason the hand is good

Dork-to-engine analysis asks the same kind of question for T1 creature mana dorks specifically -
the assignment's correction (B): a summoning-sick T1 dork enabling a T2 engine must not be
undervalued. Reports, for hands containing >=1 creature dork, how often trajectory_best's
mechanism is "dork_to_engine" (or the dork contributed to a later best-tier line at all), versus
the dork simply being stranded mana with no destination.
"""
import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TUTORS = {
    "Birthing Pod", "Chord of Calling", "Crop Rotation", "Demonic Tutor",
    "Eldritch Evolution", "Enlightened Tutor", "Finale of Devastation",
    "Imperial Seal", "Nature's Rhythm", "Ranger-Captain of Eos",
    "Sowing Mycospawn", "Spellseeker", "Survival of the Fittest", "Vampiric Tutor",
}
CREATURE_DORKS = {
    "Avacyn's Pilgrim", "Birds of Paradise", "Delighted Halfling",
    "Devoted Druid", "Elves of Deep Shadow", "Noble Hierarch",
}
TIER_RANK = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}


def _load(path):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def _bucket_tutor_outcome(row):
    tier = row["trajectory_best__tier"]
    mech = row["trajectory_best__mechanism"] or ""
    tutor_mech = "tutor" in mech  # catches tutor_to_engine, tutor_plus_accel_to_engine
    if mech.startswith("commander_engine"):
        return "superseded_by_commander"
    if tutor_mech and tier == "S":
        return "tutor_to_t1_engine"
    if tutor_mech and tier == "A":
        return "tutor_to_t2_engine"
    if tutor_mech and tier in ("B", "C"):
        return "tutor_live_but_delayed"
    return "tutor_stranded"


def analyze_tutors(rows):
    per_card = defaultdict(lambda: Counter())
    per_card_n = Counter()
    for row in rows:
        names = row.get("opener__tutor_names") or []
        if not names:
            continue
        bucket = _bucket_tutor_outcome(row)
        for name in names:
            per_card[name][bucket] += 1
            per_card_n[name] += 1
    out = {}
    for name in sorted(per_card_n):
        n = per_card_n[name]
        dist = per_card[name]
        out[name] = {
            "hands_with_this_tutor": n,
            **{k: round(dist.get(k, 0) / n, 4) for k in (
                "tutor_to_t1_engine", "tutor_to_t2_engine", "tutor_live_but_delayed",
                "tutor_stranded", "superseded_by_commander",
            )},
            "raw_counts": dict(dist),
        }
    return out


def analyze_greedy_vs_best_for_tutor_hands(rows):
    """How much does the bounded search actually recover, specifically for hands holding a
    tutor? (Isolates the value of trajectory-aware tutor targeting from general search noise.)"""
    with_tutor = [r for r in rows if r.get("opener__tutor_names")]
    if not with_tutor:
        return {}
    improved = sum(1 for r in with_tutor if TIER_RANK[r["trajectory_best__tier"]] < TIER_RANK[r["trajectory_greedy__tier"]])
    greedy_dist = Counter(r["trajectory_greedy__tier"] for r in with_tutor)
    best_dist = Counter(r["trajectory_best__tier"] for r in with_tutor)
    n = len(with_tutor)
    return {
        "hands_with_any_tutor": n,
        "fraction_where_search_strictly_improves_tier": round(improved / n, 4),
        "greedy_tier_distribution": {k: round(v / n, 4) for k, v in greedy_dist.items()},
        "best_tier_distribution": {k: round(v / n, 4) for k, v in best_dist.items()},
    }


def analyze_dork_to_engine(rows):
    # trajectory_best__mechanism is derived from the actually-simulated cast_log, so it is already
    # correctly creature-specific (dork_to_engine only fires when a CREATURE mana source - not a
    # rock/burst source - was cast before the tier-defining engine); no need for a hand-composition
    # proxy here.
    n_dork_mech = sum(1 for r in rows if (r["trajectory_best__mechanism"] or "").startswith("dork_to_engine"))
    n_dork_mech_greedy = sum(1 for r in rows if (r["trajectory_greedy__mechanism"] or "").startswith("dork_to_engine"))
    dork_hands = [r for r in rows if (r["trajectory_best__mechanism"] or "").startswith("dork_to_engine")]
    dork_tier_dist = Counter(r["trajectory_best__tier"] for r in dork_hands)
    return {
        "total_hands": len(rows),
        "hands_reaching_dork_to_engine_best": n_dork_mech,
        "hands_reaching_dork_to_engine_greedy": n_dork_mech_greedy,
        "dork_to_engine_tier_distribution": dict(dork_tier_dist),
        "note": (
            "dork_to_engine is read directly from trajectory_best__mechanism, which is derived "
            "from the actually-simulated cast_log (a creature-type mana source cast before the "
            "tier-defining engine) - not from a raw hand-composition proxy. This is the direct "
            "empirical check of MULL-005 correction (B): T1 dork -> T2 engine reaching Tier A."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=[
        str(REPO_ROOT / "results/solo_baseline/mull005_trajectory_dataset_play.jsonl.gz"),
        str(REPO_ROOT / "results/solo_baseline/mull005_trajectory_dataset_draw.jsonl.gz"),
    ])
    ap.add_argument("--out", default=str(REPO_ROOT / "results/solo_baseline/mull005_tutor_dork_analysis.json"))
    args = ap.parse_args()

    all_rows = []
    per_seat = {}
    for path in args.datasets:
        rows = _load(path)
        seat = "play" if "_play" in path else ("draw" if "_draw" in path else Path(path).stem)
        per_seat[seat] = rows
        all_rows.extend(rows)

    result = {
        "combined": {
            "n_hands": len(all_rows),
            "per_tutor_card": analyze_tutors(all_rows),
            "search_value_for_tutor_hands": analyze_greedy_vs_best_for_tutor_hands(all_rows),
            "dork_to_engine": analyze_dork_to_engine(all_rows),
        },
    }
    for seat, rows in per_seat.items():
        result[seat] = {
            "n_hands": len(rows),
            "per_tutor_card": analyze_tutors(rows),
            "search_value_for_tutor_hands": analyze_greedy_vs_best_for_tutor_hands(rows),
            "dork_to_engine": analyze_dork_to_engine(rows),
        }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result["combined"]["per_tutor_card"], indent=2))
    print(json.dumps(result["combined"]["search_value_for_tutor_hands"], indent=2))
    print(json.dumps(result["combined"]["dork_to_engine"], indent=2))


if __name__ == "__main__":
    main()
