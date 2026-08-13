"""SIM-001 MULL-005R sections 16/17 — destination census + named-trajectory census.

Built from the corrected large-scale dataset (mull005r_trajectory_dataset_play.jsonl.gz, 15,000
hands, seed=1005) rather than re-simulating - every row already carries trajectory_best__* from
the bounded search over the corrected engine. "Strong state rate" reuses out_t3__t3_any_strong_
state (trajectory_metrics.t3_strong_state_metrics, unchanged this phase). "Keep@N" applies the
re-derived mull005r_hand_size_thresholds.json (assumed mulligan-card-cost=1.0) to each row's own
trajectory_best__tier, treating the SAME tier as representative of what a hand of that quality
would grade to at hand size N - the same convention already used by MULL-005's primer quick-
reference table, not a new interpretation invented for this report.
"""
import gzip
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TIER_ORDER = ["S", "A", "B", "C", "D", "F"]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}

DATASET = REPO_ROOT / "results" / "solo_baseline" / "mull005r_trajectory_dataset_play.jsonl.gz"
THRESHOLDS_PATH = REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json"

TIER_A_ENGINES = {"Rhystic Study", "Mystic Remora", "Sylvan Library", "Smothering Tithe", "Esper Sentinel"}
PREMIUM_ONE_DROP = {"Mystic Remora", "Esper Sentinel"}


def _load_rows():
    rows = []
    with gzip.open(DATASET, "rt") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def _keep_thresholds():
    data = json.loads(THRESHOLDS_PATH.read_text())
    table = data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]
    return {int(size): row["keep_at_or_above_tier"] for size, row in table.items()}


def _keeps(tier, thresholds):
    out = {}
    for size in (7, 6, 5):
        keep_tier = thresholds.get(size)
        out[f"keep_at_{size}"] = keep_tier is not None and TIER_RANK[tier] <= TIER_RANK[keep_tier]
    return out


# ---- destination family classification (assignment section 16) ---------------------------

def _destination_family(row):
    tier = row["trajectory_best__tier"]
    tier_engine = row["trajectory_best__tier_engine"]
    tier_turn = row["trajectory_best__tier_turn"]
    mechanism = row["trajectory_best__mechanism"]
    base_mech = mechanism.split("+")[0] if mechanism else mechanism

    if row["trajectory_best__cost_engine_plus_live_free_interaction"] or row["trajectory_best__cost_engine_plus_verified_combo_proximity"]:
        return "exceptional_composite_state"
    if tier_engine == "Abhorrent Oculus" and base_mech == "pod_to_oculus":
        return "pod_to_oculus"
    if tier_engine == "Abhorrent Oculus":
        return "other_early_oculus"
    if tier_engine == "Birthing Pod" or base_mech in ("pod_to_engine",):
        return "early_pod_online"
    if tier_engine == "Survival of the Fittest":
        return "survival_online"
    if tier == "S":
        return "t1_resource_engine"
    if tier_engine == "Smothering Tithe" and tier_turn == 2:
        return "t2_smothering_tithe"
    if tier_engine in TIER_A_ENGINES and tier_turn == 2:
        return "t2_other_premium_resource_engine"
    if tier in ("B", "C") and tier_engine is not None:
        return "secondary_engine"
    return "no_premium_destination"


DESTINATION_FAMILIES = [
    "t1_resource_engine", "t2_smothering_tithe", "t2_other_premium_resource_engine",
    "secondary_engine", "early_pod_online", "pod_to_oculus", "other_early_oculus",
    "survival_online", "exceptional_composite_state", "no_premium_destination",
]


def build_destination_census(rows, thresholds):
    n = len(rows)
    buckets = {fam: [] for fam in DESTINATION_FAMILIES}
    for row in rows:
        buckets[_destination_family(row)].append(row)

    out = []
    for fam in DESTINATION_FAMILIES:
        members = buckets[fam]
        c = len(members)
        strong_rate = sum(1 for r in members if r["out_t3__t3_any_strong_state"]) / c if c else None
        keep7_rate = sum(1 for r in members if _keeps(r["trajectory_best__tier"], thresholds)["keep_at_7"]) / c if c else None
        keep6_rate = sum(1 for r in members if _keeps(r["trajectory_best__tier"], thresholds)["keep_at_6"]) / c if c else None
        tier_dist = {}
        for r in members:
            tier_dist[r["trajectory_best__tier"]] = tier_dist.get(r["trajectory_best__tier"], 0) + 1
        out.append({
            "destination_family": fam,
            "count": c,
            "frequency": round(c / n, 4),
            "strong_state_rate": round(strong_rate, 4) if strong_rate is not None else None,
            "keep_at_7_rate": round(keep7_rate, 4) if keep7_rate is not None else None,
            "keep_at_6_rate": round(keep6_rate, 4) if keep6_rate is not None else None,
            "tier_distribution": tier_dist,
        })
    return out


# ---- named trajectory classification (assignment section 17) ------------------------------

def _named_trajectories(row):
    """Multi-label: a row can match more than one named trajectory tag."""
    tags = []
    tier_engine = row["trajectory_best__tier_engine"]
    tier_turn = row["trajectory_best__tier_turn"]
    tier = row["trajectory_best__tier"]
    mechanism = row["trajectory_best__mechanism"]
    base_mech = mechanism.split("+")[0] if mechanism else mechanism
    search_label = row["trajectory_best__search_label"] or ""

    if row["out_t1__t1_engine_Mystic Remora"]:
        tags.append("t1_remora")
    if row["out_t1__t1_engine_Esper Sentinel"]:
        tags.append("t1_sentinel")
    if tier_engine == "Smothering Tithe" and tier_turn == 2:
        tags.append("t2_tithe")
    if tier_engine == "Rhystic Study" and tier_turn == 2:
        tags.append("t2_rhystic")
    if tier_engine == "Faerie Mastermind" and tier_turn == 2:
        tags.append("t2_mastermind")
    if tier_engine == "Archivist of Oghma" and tier_turn == 2:
        tags.append("t2_archivist")
    if tier_engine == "Sylvan Library" and tier_turn == 2:
        tags.append("t2_library")
    if tier_engine == "Heartwood Storyteller" and tier_turn == 2:
        tags.append("t2_heartwood")
    if tier_engine == "Runic Armasaur" and tier_turn == 2:
        tags.append("t2_armasaur")
    if base_mech == "dork_to_engine" and tier in ("S", "A"):
        tags.append("t1_dork_to_t2_premium_engine")
    if base_mech == "tutor_to_engine" and tier in ("S", "A"):
        tags.append("tutor_to_t2_premium_engine")
    if search_label.startswith("tutor:Mana Vault"):
        tags.append("tutor_to_mana_vault_to_early_tithe" if tier_engine == "Smothering Tithe" else "tutor_to_mana_vault")
    if base_mech == "rock_to_engine" and tier_engine == "Smothering Tithe":
        tags.append("mana_vault_or_rock_to_t2_tithe")
    if tier_engine == "Birthing Pod":
        tags.append("pod_online_t2" if tier_turn == 2 else "pod_online_t3")
    if base_mech == "pod_to_oculus":
        tags.append("pod_to_oculus")
    if base_mech == "battlefield_tutor_to_oculus":
        if "Finale of Devastation" in search_label:
            tags.append("finale_to_oculus")
        elif "Nature's Rhythm" in search_label:
            tags.append("natures_rhythm_to_oculus")
        elif "Eldritch Evolution" in search_label:
            tags.append("eldritch_evolution_to_oculus")
        elif "Chord of Calling" in search_label:
            tags.append("chord_to_oculus")
        else:
            tags.append("other_battlefield_tutor_to_oculus")
    if tier_engine == "Survival of the Fittest":
        tags.append("survival_online")
    if row["trajectory_best__cost_engine_plus_live_free_interaction"]:
        tags.append("engine_plus_live_free_interaction")
    if row["opener__accel_card_count"] >= 2 and tier in ("D", "F"):
        tags.append("acceleration_rich_destination_poor")
    if not tags:
        tags.append("unclassified" if tier not in ("D", "F") else "no_destination_reached")
    return tags


def build_named_trajectory_census(rows, thresholds):
    n = len(rows)
    counts = {}
    for row in rows:
        for tag in _named_trajectories(row):
            counts.setdefault(tag, []).append(row)
    out = []
    for tag, members in sorted(counts.items(), key=lambda kv: -len(kv[1])):
        c = len(members)
        keep7 = sum(1 for r in members if _keeps(r["trajectory_best__tier"], thresholds)["keep_at_7"]) / c
        avg_turn = [r["trajectory_best__tier_turn"] for r in members if r["trajectory_best__tier_turn"] is not None]
        out.append({
            "named_trajectory": tag,
            "count": c,
            "frequency": round(c / n, 4),
            "keep_at_7_rate": round(keep7, 4),
            "avg_tier_turn": round(sum(avg_turn) / len(avg_turn), 3) if avg_turn else None,
            "tier_distribution": {t: sum(1 for r in members if r["trajectory_best__tier"] == t) for t in TIER_ORDER},
        })
    return out


def main():
    rows = _load_rows()
    thresholds = _keep_thresholds()

    dest_census = build_destination_census(rows, thresholds)
    named_census = build_named_trajectory_census(rows, thresholds)

    # Disclosed finding: search_label prefix distribution, so the census makes visible how often
    # each search family (greedy/tutor/pod/survival/battlefield_tutor/land_tutor) actually WON as
    # the best-known trajectory in this random sample - not merely that the mechanism exists.
    label_prefix_counts = {}
    for r in rows:
        label = r["trajectory_best__search_label"] or ""
        prefix = label.split(":")[0] if label else "none"
        label_prefix_counts[prefix] = label_prefix_counts.get(prefix, 0) + 1

    dest_out = REPO_ROOT / "results" / "solo_baseline" / "destination_census.json"
    named_out = REPO_ROOT / "results" / "solo_baseline" / "named_trajectory_census.json"
    common_header = {
        "phase": "SIM_001_MULL_005R_CENSUS",
        "source_dataset": str(DATASET.relative_to(REPO_ROOT)),
        "sample_count": len(rows),
        "seat": "play",
    }
    dest_out.write_text(json.dumps({
        **common_header,
        "note": (
            "destination_family is a single best-match classification per hand (mutually "
            "exclusive, assignment section 16) using trajectory_best__* fields; "
            "search_label_prefix_distribution shows how often each of the 5 bounded-search "
            "families (greedy/tutor/pod/survival/battlefield_tutor/land_tutor) actually won as "
            "best-known trajectory in this sample - the Pod-activation family never won outright "
            "in this 15,000-hand sample (0 occurrences), a real, disclosed rarity finding, not a "
            "bug: Pod's OWN board presence + a sac creature already earns Tier B/C credit via the "
            "generic support check before an explicit activation is even attempted, and Pod's "
            "{1}{G/P} activation on top of its own {3}{G/P} cast is genuinely mana-heavy for a "
            "T1-T3 window."
        ),
        "search_label_prefix_distribution": label_prefix_counts,
        "destination_families": dest_census,
    }, indent=2) + "\n", encoding="utf-8")
    named_out.write_text(json.dumps({
        **common_header,
        "note": "named_trajectory tags are MULTI-LABEL (a hand can match more than one); frequencies sum to more than 1.0.",
        "named_trajectories": named_census,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dest_out}")
    print(f"wrote {named_out}")
    for d in dest_census:
        print(f"  {d['destination_family']:35s} freq={d['frequency']:.4f} strong={d['strong_state_rate']} keep7={d['keep_at_7_rate']}")
    print()
    for d in named_census[:15]:
        print(f"  {d['named_trajectory']:35s} freq={d['frequency']:.4f} keep7={d['keep_at_7_rate']}")


if __name__ == "__main__":
    main()
