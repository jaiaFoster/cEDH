"""SIM-001 MULL-005 correction (A) — acceleration-without-payoff analysis.

SOLO-004's SIMPLE_RULES snap-kept any hand with "2+ acceleration" regardless of whether that mana
had anywhere to go. MULL-005 mandates removing that rule specifically when there is no
destination/payoff - "Mana is not a reason to keep a hand" on its own. This module tests that
directly: among hands with 2+ acceleration cards, does having no visible engine AND no
tutor-reachable engine actually predict a worse trajectory-best outcome, versus hands where the
acceleration has a real destination (an engine already in hand, or a tutor able to reach one)?

Three buckets, using only OPENER-VISIBLE facts (never future draws) to classify "destination
known at keep-decision time":
  - accel_with_engine_in_hand: an engine card is already among the 7
  - accel_with_tutor_reaching_engine: no engine in hand, but a held tutor's disclosed target set
    includes an engine (opener__tutor_reaches_engine)
  - accel_with_no_destination: neither - the exact case the old blanket rule wrongly rewarded
"""
import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(path):
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def _bucket(row):
    if row["opener__has_any_engine_card"]:
        return "accel_with_engine_in_hand"
    if row.get("opener__tutor_reaches_engine"):
        return "accel_with_tutor_reaching_engine"
    return "accel_with_no_destination"


def analyze(rows):
    accel_2plus = [r for r in rows if r["opener__accel_card_count"] >= 2]
    accel_lt2 = [r for r in rows if r["opener__accel_card_count"] < 2]

    buckets = {}
    for r in accel_2plus:
        buckets.setdefault(_bucket(r), []).append(r)

    def tier_summary(group):
        n = len(group)
        if n == 0:
            return {"n": 0}
        dist = Counter(r["trajectory_best__tier"] for r in group)
        good = sum(1 for r in group if r["trajectory_best__tier"] in ("S", "A"))
        bad = sum(1 for r in group if r["trajectory_best__tier"] in ("D", "F"))
        return {
            "n": n,
            "tier_distribution": {k: round(v / n, 4) for k, v in dist.items()},
            "fraction_tier_S_or_A": round(good / n, 4),
            "fraction_tier_D_or_F": round(bad / n, 4),
        }

    # The no-destination bucket still often lands on Tier A via a productive COMMANDER line - the
    # extra mana just got redirected there instead of a card engine, since Tymna/Thrasios are
    # always available from the command zone at no card cost. Split that bucket further so
    # "no destination at all" (mana that couldn't even accelerate a commander into productivity)
    # is isolated from "no ENGINE destination, but the mana fueled the commander instead."
    no_dest = buckets.get("accel_with_no_destination", [])
    no_dest_commander_rescued = [r for r in no_dest if (r["trajectory_best__mechanism"] or "").startswith("commander_engine")]
    no_dest_truly_stranded = [r for r in no_dest if not (r["trajectory_best__mechanism"] or "").startswith("commander_engine")]

    return {
        "accel_2plus_by_destination": {b: tier_summary(g) for b, g in buckets.items()},
        "accel_with_no_destination_split": {
            "commander_rescued": tier_summary(no_dest_commander_rescued),
            "truly_stranded_no_commander_either": tier_summary(no_dest_truly_stranded),
        },
        "accel_2plus_overall": tier_summary(accel_2plus),
        "accel_lt2_overall": tier_summary(accel_lt2),
        "note": (
            "If accel_with_no_destination's fraction_tier_D_or_F is close to (or worse than) "
            "accel_lt2_overall's, that confirms 2+ acceleration alone (with no engine in hand and "
            "no tutor reaching one) is NOT predictive of a good trajectory, validating MULL-005's "
            "removal of the blanket '2+ acceleration = snap keep' rule for the no-destination case."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=[
        str(REPO_ROOT / "results/solo_baseline/mull005_trajectory_dataset_play.jsonl.gz"),
        str(REPO_ROOT / "results/solo_baseline/mull005_trajectory_dataset_draw.jsonl.gz"),
    ])
    ap.add_argument("--out", default=str(REPO_ROOT / "results/solo_baseline/mull005_accel_without_payoff_analysis.json"))
    args = ap.parse_args()

    all_rows = []
    for path in args.datasets:
        all_rows.extend(_load(path))

    result = analyze(all_rows)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
