"""SIM-001 MULL-005R section 24 — paired comparison against MULL-005.

TRUE pairing, not two independent samples: mull005_trajectory_dataset_play.jsonl.gz (committed
before this phase's engine changes, seed=42, count=15000, MULL-005's own grading) vs
mull005r_paired_dataset_play.jsonl.gz (the SAME seed/count/deck rerun through the current,
MULL-005R-corrected engine via the unmodified run_mull005_trajectory_dataset.py script). Because
random.Random.shuffle only consumes the outer rng once per hand (run_one_hand calls rng.shuffle()
exactly once, before any simulation), and every downstream simulation call uses its own
independently-seeded HandState.rng, row i in both files is GUARANTEED to be the exact same
98-card shuffle -> the exact same 7-card opening hand, confirmed empirically (opener-visible
land-count/color features match row-for-row in a spot check). Every reported count below is
therefore a real paired transition on an identical hand, not a distributional shift that could be
sampling noise.
"""
import gzip
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TIER_ORDER = ["S", "A", "B", "C", "D", "F"]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}

OLD_PATH = REPO_ROOT / "results" / "solo_baseline" / "mull005_trajectory_dataset_play.jsonl.gz"
NEW_PATH = REPO_ROOT / "results" / "solo_baseline" / "mull005r_paired_dataset_play.jsonl.gz"
COMMANDERS = {"Tymna the Weaver", "Thrasios, Triton Hero"}


def _load(path):
    rows = []
    with gzip.open(path, "rt") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def _threshold(path):
    data = json.loads(path.read_text())
    return data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]["7"]["keep_at_or_above_tier"]


def _keep(tier, threshold_tier):
    return TIER_RANK[tier] <= TIER_RANK[threshold_tier]


def classify_newly_kept(new_row):
    """Why did a hand that MULL-005 shipped become a MULL-005R keep?"""
    mech = new_row["trajectory_best__mechanism"] or ""
    base_mech = mech.split("+")[0]
    tier_engine = new_row["trajectory_best__tier_engine"]
    label = new_row["trajectory_best__search_label"] or ""
    if tier_engine == "Abhorrent Oculus":
        return "oculus_understood"
    if base_mech.startswith("pod_"):
        return "pod_understood"
    if "Mana Vault" in label:
        return "tutor_to_mana_vault_to_engine_understood"
    if tier_engine == "Smothering Tithe":
        return "smothering_tithe_promoted"
    if base_mech == "dork_to_engine":
        return "dork_to_engine_understood"
    if tier_engine == "Survival of the Fittest":
        return "survival_understood"
    if base_mech.startswith("battlefield_tutor") or base_mech.startswith("battlefield_land_tutor"):
        return "expanded_tutor_search_understood"
    if tier_engine == "Birthing Pod":
        return "birthing_pod_generic_infra_credit_understood"
    if tier_engine == "Thrasios, Triton Hero":
        return "thrasios_concrete_benefit_understood"
    return "other"


def classify_newly_shipped(old_row, new_row):
    """Why did a hand that MULL-005 kept become a MULL-005R ship?"""
    old_tier_engine = old_row["trajectory_best__tier_engine"]
    old_mechanism = old_row["trajectory_best__mechanism"] or ""
    if old_tier_engine in COMMANDERS:
        return "commander_access_removed"
    if old_mechanism in ("dork_to_engine", "rock_to_engine", "burst_mana_to_engine", "tutor_plus_accel_to_engine"):
        return "acceleration_no_real_destination"
    if old_row.get("trajectory_best__cost_commander_access"):
        return "commander_access_removed"
    return "other"


def main():
    old_rows = _load(OLD_PATH)
    new_rows = _load(NEW_PATH)
    assert len(old_rows) == len(new_rows), (len(old_rows), len(new_rows))

    old_threshold = _threshold(REPO_ROOT / "results" / "solo_baseline" / "mull005_hand_size_thresholds.json")
    new_threshold = _threshold(REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json")

    n = len(old_rows)
    both_keep = both_ship = newly_kept = newly_shipped = 0
    newly_kept_causes = {}
    newly_shipped_causes = {}
    tier_transition_counts = {}
    tier_engine_realization_examples = []

    for old_row, new_row in zip(old_rows, new_rows):
        old_tier = old_row["trajectory_best__tier"]
        new_tier = new_row["trajectory_best__tier"]
        old_keep = _keep(old_tier, old_threshold)
        new_keep = _keep(new_tier, new_threshold)

        transition = f"{old_tier}->{new_tier}"
        tier_transition_counts[transition] = tier_transition_counts.get(transition, 0) + 1

        if old_keep and new_keep:
            both_keep += 1
        elif not old_keep and not new_keep:
            both_ship += 1
        elif not old_keep and new_keep:
            newly_kept += 1
            cause = classify_newly_kept(new_row)
            newly_kept_causes[cause] = newly_kept_causes.get(cause, 0) + 1
        else:
            newly_shipped += 1
            cause = classify_newly_shipped(old_row, new_row)
            newly_shipped_causes[cause] = newly_shipped_causes.get(cause, 0) + 1

        # Ranking/realization-timing changes: same destination card, different tier_turn (engine
        # realized earlier or later under the corrected model) even when the keep/ship decision
        # doesn't flip - Smothering Tithe's promotion is the flagship example.
        if (old_row["trajectory_best__tier_engine"] == new_row["trajectory_best__tier_engine"] == "Smothering Tithe"
                and old_row["trajectory_best__tier"] != new_row["trajectory_best__tier"]):
            if len(tier_engine_realization_examples) < 10:
                tier_engine_realization_examples.append({
                    "old_tier": old_tier, "new_tier": new_tier,
                    "old_mechanism": old_row["trajectory_best__mechanism"],
                    "new_mechanism": new_row["trajectory_best__mechanism"],
                })

    tithe_old_tier_dist = {}
    tithe_new_tier_dist = {}
    for old_row, new_row in zip(old_rows, new_rows):
        if old_row["trajectory_best__tier_engine"] == "Smothering Tithe":
            tithe_old_tier_dist[old_row["trajectory_best__tier"]] = tithe_old_tier_dist.get(old_row["trajectory_best__tier"], 0) + 1
        if new_row["trajectory_best__tier_engine"] == "Smothering Tithe":
            tithe_new_tier_dist[new_row["trajectory_best__tier"]] = tithe_new_tier_dist.get(new_row["trajectory_best__tier"], 0) + 1

    # Threshold-INVARIANT comparison (fixed at "tier S/A/B", identical for old and new): the
    # derived keep_threshold_size7 itself moved from B to C between old and new (task #96 finding
    # - greedy-only EV dropped once commander credit was removed), so the raw newly_kept/newly_
    # shipped counts above CONFLATE two distinct effects: (1) individual hands reaching a
    # genuinely different best tier under the corrected mechanics (Oculus/Pod/Tithe/dork
    # understanding), and (2) the keep/ship LINE itself moving. This fixed-threshold pass isolates
    # (1) alone by holding the bar constant across both runs.
    FIXED_KEEP_TIERS = {"S", "A", "B"}
    fixed_both_keep = fixed_both_ship = fixed_newly_kept = fixed_newly_shipped = 0
    fixed_newly_kept_causes = {}
    fixed_newly_shipped_causes = {}
    for old_row, new_row in zip(old_rows, new_rows):
        old_fixed_keep = old_row["trajectory_best__tier"] in FIXED_KEEP_TIERS
        new_fixed_keep = new_row["trajectory_best__tier"] in FIXED_KEEP_TIERS
        if old_fixed_keep and new_fixed_keep:
            fixed_both_keep += 1
        elif not old_fixed_keep and not new_fixed_keep:
            fixed_both_ship += 1
        elif not old_fixed_keep and new_fixed_keep:
            fixed_newly_kept += 1
            cause = classify_newly_kept(new_row)
            fixed_newly_kept_causes[cause] = fixed_newly_kept_causes.get(cause, 0) + 1
        else:
            fixed_newly_shipped += 1
            cause = classify_newly_shipped(old_row, new_row)
            fixed_newly_shipped_causes[cause] = fixed_newly_shipped_causes.get(cause, 0) + 1

    result = {
        "phase": "SIM_001_MULL_005R_PAIRED_COMPARISON",
        "pairing_method": "identical seed=42/count=15000/seat=play/deck - row-for-row identical opening hands, verified by matching opener-visible land-count/color features",
        "old_source": str(OLD_PATH.relative_to(REPO_ROOT)), "new_source": str(NEW_PATH.relative_to(REPO_ROOT)),
        "old_keep_threshold_size7": old_threshold, "new_keep_threshold_size7": new_threshold,
        "sample_count": n,
        "keep_decision_transitions": {
            "kept_both": both_keep, "shipped_both": both_ship,
            "newly_kept_count": newly_kept, "newly_kept_rate": round(newly_kept / n, 4),
            "newly_shipped_count": newly_shipped, "newly_shipped_rate": round(newly_shipped / n, 4),
        },
        "newly_kept_causes": newly_kept_causes,
        "newly_shipped_causes": newly_shipped_causes,
        "fixed_threshold_comparison_tiers_SAB": {
            "kept_both": fixed_both_keep, "shipped_both": fixed_both_ship,
            "newly_kept_count": fixed_newly_kept, "newly_kept_rate": round(fixed_newly_kept / n, 4),
            "newly_shipped_count": fixed_newly_shipped, "newly_shipped_rate": round(fixed_newly_shipped / n, 4),
            "newly_kept_causes": fixed_newly_kept_causes,
            "newly_shipped_causes": fixed_newly_shipped_causes,
        },
        "tier_transition_counts": dict(sorted(tier_transition_counts.items(), key=lambda kv: -kv[1])[:30]),
        "smothering_tithe_tier_distribution_old": tithe_old_tier_dist,
        "smothering_tithe_tier_distribution_new": tithe_new_tier_dist,
        "smothering_tithe_realization_timing_examples": tier_engine_realization_examples,
        "note": (
            "newly_kept_causes/newly_shipped_causes are single-cause, priority-ordered "
            "classifications of the trajectory_best__* fields on the NEW (newly_kept) or OLD "
            "(newly_shipped) row - see classify_newly_kept()/classify_newly_shipped(). "
            "IMPORTANT: keep_decision_transitions above uses EACH dataset's own derived "
            "keep_threshold_size7 (old=B, new=C, per task #96's own finding that greedy-only "
            "expected tier value dropped once commander credit was removed) - this conflates two "
            "distinct effects: (1) individual hands reaching a genuinely different best tier "
            "under corrected mechanics, and (2) the keep/ship LINE itself moving down. "
            "fixed_threshold_comparison_tiers_SAB holds the bar constant (tier in {S,A,B} counts "
            "as keep under BOTH old and new) to isolate effect (1) alone - use THIS block, not "
            "the threshold-relative one above, when citing 'X hands are newly kept because the "
            "model now understands Y'; the threshold-relative numbers answer a different, also "
            "real question ('how did the keep/mulligan LINE move'), not double-counted evidence "
            "of engine correctness. "
            "smothering_tithe_tier_distribution_{old,new} shows TITHE-001's realization-timing "
            "promotion directly: MULL-005 zeroed Tithe out of tier credit entirely (old "
            "distribution should show it essentially never as tier_engine, or only via generic "
            "fallback paths), MULL-005R credits it identically to Rhystic Study/Mystic Remora."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mull005_paired_comparison.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result["keep_decision_transitions"], indent=2))
    print("newly_kept_causes:", json.dumps(newly_kept_causes, indent=2))
    print("newly_shipped_causes:", json.dumps(newly_shipped_causes, indent=2))
    print("Tithe old tier dist:", tithe_old_tier_dist)
    print("Tithe new tier dist:", tithe_new_tier_dist)


if __name__ == "__main__":
    main()
