"""SIM-001 MULL-005 — primer quick-reference table + pod-guidance table.

Table 1 (primer quick-reference): trajectory tier x hand size x pod speed -> keep/ship category.
Built from REAL simulated data (mull005_hand_size_thresholds.json's cost=1.0 keep thresholds) for
the hand-size axis, with pod speed applied as a DISCLOSED QUALITATIVE adjustment (not simulated -
see pod_archetypes.py) on top:
  - FAST pods (RogSi-speed): only trajectories that land ON TIME (Tier S/A, online by T1/T2)
    clear the bar regardless of the neutral hand-size threshold - a Tier C engine arriving T3 is
    close to irrelevant if the game can end before then. This directly reflects the RogSi/Sisay
    archetype notes (raw_speed_low_curve increased, card_advantage_engine decreased in value).
  - SLOW pods (Blue Farm-speed): the neutral bar relaxes by one tier step - a hand one tier below
    the neutral threshold is still worth keeping, since a slower resilient pod doesn't punish
    being a turn behind as hard. Reflects Blue Farm's notes (card_advantage_engine/mana_resilience
    increased, raw_speed_low_curve decreased).
  - MEDIUM pods use the neutral, hand-size-only threshold unchanged.
This qualitative adjustment is itself unvalidated pod-conditioning (same STRATEGIC_PRIOR_
UNVALIDATED status as pod_archetypes.py) layered on top of the REAL hand-size thresholds - the
table cells are therefore mixed-confidence and labeled as such per-axis, not given one blanket
confidence label.

Table 2 (pod-guidance table): opponent archetype -> mulligan pressure + what gains/loses value,
read directly off pod_archetypes.py's ARCHETYPES dict. Per the assignment's explicit constraint,
this table contains NO simulated percentages anywhere - only qualitative descriptions.
"""
import json
from pathlib import Path

from trajectory_grading import TIER_ORDER
from pod_archetypes import ARCHETYPES

REPO_ROOT = Path(__file__).resolve().parents[2]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}

POD_SPEED_BUCKETS = {
    "FAST": {"RogSi", "Sisay"},
    "MEDIUM": {"Kinnan", "Rog/Thras Tree Farm", "Tayam", "Tivit", "midrange_grind"},
    "SLOW": {"Blue Farm", "Etali", "stax_heavy"},
}


def _neutral_threshold_by_size():
    path = REPO_ROOT / "results" / "solo_baseline" / "mull005_hand_size_thresholds.json"
    data = json.loads(path.read_text())
    table = data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]
    out = {}
    for size, row in table.items():
        out[int(size)] = row["keep_at_or_above_tier"]
    return out


def build_quick_reference_table():
    neutral = _neutral_threshold_by_size()
    rows = []
    for size in sorted(neutral, reverse=True):
        neutral_tier = neutral[size]
        for speed in ("FAST", "MEDIUM", "SLOW"):
            for tier in TIER_ORDER:
                if speed == "MEDIUM":
                    # No threshold data for this size (out of the derived 7/6/5/4 scope) falls
                    # back to "keep unless F" - same floor used elsewhere, never "ship everything".
                    keep = tier != "F" if neutral_tier is None else TIER_RANK[tier] <= TIER_RANK[neutral_tier]
                elif speed == "FAST":
                    keep = tier in ("S", "A")
                else:  # SLOW - relax neutral bar by one tier step, but NEVER as far as Tier F -
                       # pod context cannot rescue a hand with no functional trajectory at all,
                       # regardless of how slow/patient the opposing pod is (governing constraint).
                    if neutral_tier is None:
                        keep = tier != "F"
                    else:
                        relaxed_idx = min(TIER_RANK["D"], TIER_RANK[neutral_tier] + 1)
                        keep = TIER_RANK[tier] <= relaxed_idx
                rows.append({
                    "hand_size": size, "pod_speed": speed, "trajectory_tier": tier,
                    "category": "KEEP" if keep else "SHIP",
                    "hand_size_axis_confidence": "SIMULATED",
                    "pod_speed_axis_confidence": "STRATEGIC_PRIOR_UNVALIDATED" if speed != "MEDIUM" else "SIMULATED (no adjustment applied)",
                })
    return rows


def build_pod_guidance_table():
    rows = []
    for name, data in ARCHETYPES.items():
        pressure = {
            "very_fast": "HIGH - mulligan aggressively toward speed/interaction, tolerate a slightly worse engine hand to be on time",
            "fast_to_medium": "MEDIUM-HIGH - favor hands that are live early, don't durdle on a slow grindy plan",
            "medium": "BASELINE - the neutral structural thresholds apply about as-is",
            "medium_slow": "LOW-MEDIUM - a slightly slower, more resilient hand is fine; punish their early game if you can",
            "slow": "LOW - patience is rewarded; a card-advantage-heavy hand is fine even if a turn slow",
            "slow_by_design": "LOW BUT SHARP - patience is fine, but a hand needs to survive to actually execute; mana resilience matters a lot",
        }.get(data["speed"], "BASELINE")
        rows.append({
            "archetype": name,
            "speed": data["speed"],
            "mulligan_pressure": pressure,
            "gains_value": data["increases_value_of"],
            "loses_value": data["decreases_value_of"],
            "confidence": "STRATEGIC_PRIOR_UNVALIDATED - no simulated matchup percentages exist for this archetype",
        })
    return rows


def main():
    quick_ref = build_quick_reference_table()
    pod_guidance = build_pod_guidance_table()

    result = {
        "phase": "SIM_001_MULL_005_PRIMER_TABLES",
        "primer_quick_reference_table": quick_ref,
        "pod_guidance_table": pod_guidance,
        "notes": (
            "primer_quick_reference_table's hand_size axis is SIMULATED (mull005_hand_size_"
            "thresholds.json). Its pod_speed axis is a disclosed qualitative adjustment, NOT "
            "simulated, except the MEDIUM row which applies no adjustment. pod_guidance_table is "
            "entirely STRATEGIC_PRIOR_UNVALIDATED and contains no simulated percentages anywhere, "
            "per the assignment's explicit constraint."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mull005_primer_tables.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"quick_reference rows: {len(quick_ref)}")
    print(f"pod_guidance rows: {len(pod_guidance)}")


if __name__ == "__main__":
    main()
