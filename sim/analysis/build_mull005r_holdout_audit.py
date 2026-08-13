"""SIM-001 MULL-005R section 23 — false-keep/false-mulligan holdout audit.

TRAJECTORY_SIMPLE_R (structural_hand_grade, <=10 human-memorizable rules) vs TRAJECTORY_MACHINE_R
(the bounded-search ceiling) on a FRESH holdout seed neither policy nor any prior artifact this
phase has been fit/tuned against - not a rescoring of the London mulligan sim's or the dataset's
sample. Reports precision/recall/false-keep-rate/false-mulligan-rate, then MANUALLY classifies
every disagreement into one of ten named causes (assignment section 23's list), so that
TRAJECTORY_SIMPLE_R's accuracy is diagnosed by MECHANISM, not just a headline recall number - a
simple policy must not be accepted merely because recall is high; a high recall achieved by
systematically missing one entire mechanism (e.g. every Pod/Oculus line) would be a real, actionable
gap even if the aggregate number looks good.
"""
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_features import extract_opener_features
from trajectory_policies import structural_hand_grade, TIER_RANK, _thresholds
from trajectory_search import find_best_trajectory

REPO_ROOT = Path(__file__).resolve().parents[2]

DISAGREEMENT_CAUSES_ORDER = [
    "premium_one_drop_rule", "commander_logic", "pod", "oculus", "survival",
    "tutor_conversion", "mana_without_payoff", "retained_interaction",
    "engine_realization_timing", "hand_size_threshold", "unclassified",
]


def classify_disagreement_cause(feats, simple_grade, simple_reason, best_grade):
    """Priority-ordered, single-cause classification per disagreement - reason-string evidence
    (direct evidence of WHY TRAJECTORY_SIMPLE_R decided what it decided) is checked before
    destination-based inference from the machine's best-known trajectory."""
    reason = simple_reason or ""
    mechanism = best_grade["mechanism"] or ""
    tier_engine = best_grade["tier_engine"]

    if "premium" in reason:
        return "premium_one_drop_rule"
    if "commander" in reason:
        return "commander_logic"
    if mechanism.startswith("pod_") or (best_grade.get("search_label") or "").startswith("pod:"):
        return "pod"
    if tier_engine == "Abhorrent Oculus":
        return "oculus"
    if tier_engine == "Survival of the Fittest":
        return "survival"
    if "tutor" in reason or mechanism.startswith("tutor_") or mechanism.startswith("battlefield_tutor"):
        return "tutor_conversion"
    if feats["accel_card_count"] >= 2 and not feats["has_any_engine_card"]:
        return "mana_without_payoff"
    if "interaction" in mechanism:
        return "retained_interaction"
    if tier_engine in ("Rhystic Study", "Mystic Remora", "Smothering Tithe", "Esper Sentinel", "Sylvan Library"):
        return "engine_realization_timing"
    if best_grade["tier"] in ("C", "D"):
        # a one-tier-off miss right at the keep/mulligan boundary, not attributable to a specific
        # named mechanic above.
        return "hand_size_threshold"
    return "unclassified"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=9001)  # fresh holdout seed - unused by any prior MULL-005R artifact
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "holdout_disagreement_audit.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)
    keep_tier_7 = _thresholds()[7]

    tp = fp = fn = tn = 0
    disagreements = []
    cause_counts = {c: {"false_keep": 0, "false_mulligan": 0} for c in DISAGREEMENT_CAUSES_ORDER}

    for i in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]

        feats = extract_opener_features(hand, library, on_play, cards)
        simple_grade, simple_reason = structural_hand_grade(feats)
        simple_keep = simple_grade in ("SNAP_KEEP", "CONDITIONAL_KEEP")

        _, best, _ = find_best_trajectory(hand, library, on_play, cards, combos)
        machine_keep = TIER_RANK[best["tier"]] <= TIER_RANK[keep_tier_7]

        if simple_keep and machine_keep:
            tp += 1
        elif simple_keep and not machine_keep:
            fp += 1
            cause = classify_disagreement_cause(feats, simple_grade, simple_reason, best)
            cause_counts[cause]["false_keep"] += 1
            if len(disagreements) < 200:
                disagreements.append({
                    "type": "false_keep", "cause": cause, "hand": sorted(hand),
                    "simple_grade": simple_grade, "simple_reason": simple_reason,
                    "machine_tier": best["tier"], "machine_tier_engine": best["tier_engine"],
                    "machine_mechanism": best["mechanism"],
                })
        elif not simple_keep and machine_keep:
            fn += 1
            cause = classify_disagreement_cause(feats, simple_grade, simple_reason, best)
            cause_counts[cause]["false_mulligan"] += 1
            if len(disagreements) < 200:
                disagreements.append({
                    "type": "false_mulligan", "cause": cause, "hand": sorted(hand),
                    "simple_grade": simple_grade, "simple_reason": simple_reason,
                    "machine_tier": best["tier"], "machine_tier_engine": best["tier_engine"],
                    "machine_mechanism": best["mechanism"],
                })
        else:
            tn += 1

    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    false_keep_rate = fp / (fp + tn) if (fp + tn) else None   # of machine-mulligans, how many did simple wrongly keep
    false_mulligan_rate = fn / (tp + fn) if (tp + fn) else None  # of machine-keeps, how many did simple wrongly ship

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_005R_HOLDOUT_DISAGREEMENT_AUDIT",
        "sample_count": n, "seed": args.seed, "seat": args.seat,
        "keep_tier_threshold_size7": keep_tier_7,
        "confusion_matrix": {"true_positive_both_keep": tp, "false_positive_simple_keeps_machine_ships": fp,
                              "false_negative_simple_ships_machine_keeps": fn, "true_negative_both_ship": tn},
        "precision": precision, "recall": recall,
        "false_keep_rate": false_keep_rate, "false_mulligan_rate": false_mulligan_rate,
        "disagreement_cause_counts": cause_counts,
        "disagreement_total": fp + fn,
        "sample_disagreements_capped_200": disagreements,
        "note": (
            "precision/recall/false_keep_rate/false_mulligan_rate all use TRAJECTORY_MACHINE_R "
            "(the bounded-search ceiling) as ground truth and TRAJECTORY_SIMPLE_R as the "
            "predictor - false_keep = SIMPLE keeps a hand MACHINE would ship (precision loss), "
            "false_mulligan = SIMPLE ships a hand MACHINE would keep (recall loss). "
            "disagreement_cause_counts classifies EVERY disagreement (not just the capped 200-hand "
            "sample) by the ten named mechanisms in assignment section 23, single-cause, priority-"
            "ordered (reason-string evidence checked before destination inference) - see "
            "classify_disagreement_cause() for the exact ordering. A high recall/precision headline "
            "does not excuse a concentrated cause cluster; both are reported. "
            "IMPORTANT DISCLOSED CAVEAT found via manual inspection of premium_one_drop_rule "
            "false_keep examples: TRAJECTORY_MACHINE_R itself is not a perfect ceiling for hands "
            "whose ONLY land is a fetchland - trajectory_search.py's bounded search (_candidate_"
            "configs) explores hand/library-top tutor targets, Pod/Survival activations, and "
            "battlefield-tutor targets, but NEVER alternate fetchland targets; a fetch's crack "
            "target is always chosen by develop_turn's own greedy land-drop heuristic (which can "
            "legitimately prefer a target that enables an immediate lower-priority cast this turn "
            "over one that would enable a higher-priority premium engine, e.g. fetching Bayou for "
            "Imperial Seal's B instead of Tropical Island for Mystic Remora's U). A hand can "
            "therefore be graded a real 'false_keep' against MACHINE_R here even when a legal, "
            "reachable line the search never explored would have made SIMPLE_R's SNAP_KEEP "
            "correct. Some (not necessarily all) of the premium_one_drop_rule false_keep count is "
            "this MACHINE-side gap, not a SIMPLE-side error - manual spot-check before treating "
            "this cause's count as proof the premium-one-drop rule needs further tightening. "
            "Exploring alternate fetch targets as a 6th bounded-search family is disclosed future "
            "work, not implemented this phase (scope/effort tradeoff, consistent with the "
            "project's other disclosed bounded-search limitations)."
        ),
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"n={n}  precision={precision:.4f}  recall={recall:.4f}  "
          f"false_keep_rate={false_keep_rate:.4f}  false_mulligan_rate={false_mulligan_rate:.4f}")
    print(json.dumps(cause_counts, indent=2))


if __name__ == "__main__":
    main()
