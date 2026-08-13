"""SIM-001 MULL-005 — annotated example generator (structural + pod-conditioned).

Deals real hands from the real 98-card deck (fixed seed, fully reproducible) and collects the
example sets the assignment requires: 10 snap keeps, 10 conditional keeps, 10 mulligans, 5
"misleading hands" (a REAL correction MULL-005 makes over SOLO-004's SIMPLE_RULES, not an
invented illustration - each one is a hand where the old resource-first rule and the new
trajectory-first rule disagree, and the bounded trajectory search confirms which one was right),
plus 15+ pod-conditioned examples spanning several named pod combinations (e.g. "Kinnan/RogSi/
Tayam"). Every example is fully annotated: hand, land count, structural grade + reason, best-known
trajectory tier + mechanism, and (for pod examples) the two required confidence labels.
"""
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, print_run_banner, deck_provenance_fields
from opening_hand_features import extract_opener_features
from opening_hand_policy import _is_land
from trajectory_search import find_best_trajectory
from trajectory_policies import structural_hand_grade
from candidate_mulligan_policies import policy_simple_rules
from pod_archetypes import pod_conditioned_grade

REPO_ROOT = Path(__file__).resolve().parents[2]


def _annotate(hand, library, on_play, cards, combos):
    feats = extract_opener_features(hand, library, on_play, cards)
    grade, reason = structural_hand_grade(feats)
    old_keep = policy_simple_rules(feats)
    new_keep = grade in ("SNAP_KEEP", "CONDITIONAL_KEEP")
    _, best, _ = find_best_trajectory(hand, library, on_play, cards, combos)
    land_ct = sum(1 for c in hand if _is_land(c, cards))
    return {
        "hand": sorted(hand), "land_count": land_ct,
        "structural_grade": grade, "structural_reason": reason,
        "trajectory_best_tier": best["tier"], "trajectory_best_mechanism": best["mechanism"],
        "trajectory_best_tier_engine": best["tier_engine"], "trajectory_best_tier_turn": best["tier_turn"],
        "solo004_simple_rules_keep": old_keep,
        "trajectory_simple_keep": new_keep,
        "_feats": feats,
    }


def collect_examples(cards, combos, on_play, seed, target_counts, max_draws=40000):
    names = list(cards.keys())
    rng = random.Random(seed)
    buckets = {"SNAP_KEEP": [], "CONDITIONAL_KEEP": [], "SHIP": []}
    misleading = []
    for _ in range(max_draws):
        if all(len(buckets[k]) >= target_counts[k] for k in buckets) and len(misleading) >= target_counts["MISLEADING"]:
            break
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        ex = _annotate(hand, library, on_play, cards, combos)
        grade = ex["structural_grade"]
        if len(buckets.get(grade, [])) < target_counts.get(grade, 0):
            buckets.setdefault(grade, []).append(ex)

        if len(misleading) < target_counts["MISLEADING"] and ex["solo004_simple_rules_keep"] != ex["trajectory_simple_keep"]:
            # A genuine correction: the trajectory-first decision must be the one the bounded
            # search's best-known tier actually agrees with (best tier S/A/B -> keep was right;
            # best tier D/F -> ship was right) - otherwise it's just noise, not a real example.
            best_tier = ex["trajectory_best_tier"]
            trajectory_was_right = (
                (ex["trajectory_simple_keep"] and best_tier in ("S", "A", "B"))
                or (not ex["trajectory_simple_keep"] and best_tier in ("D", "F"))
            )
            if trajectory_was_right:
                misleading.append(ex)

    return buckets, misleading


POD_QUERY_EXAMPLES = [
    ["RogSi"], ["Kinnan"], ["Blue Farm"], ["Sisay"], ["Tayam"], ["Tivit"], ["Etali"],
    ["stax_heavy"], ["Rog/Thras Tree Farm"], ["midrange_grind"],
    ["Kinnan", "RogSi", "Tayam"], ["RogSi", "Sisay"], ["Blue Farm", "stax_heavy"],
    ["Rog/Thras Tree Farm", "Etali"], ["Tivit", "midrange_grind"],
    ["RogSi", "Kinnan", "Sisay"], ["Tayam", "Tivit", "Blue Farm"],
]


def build_pod_examples(structural_examples, cards):
    """15+ pod-conditioned examples: take representative structural examples (a mix of SNAP_KEEP/
    CONDITIONAL_KEEP/SHIP so the SHIP-floor constraint is visibly exercised) and run them against
    several distinct named pod combinations."""
    pool = (
        structural_examples["SNAP_KEEP"][:3]
        + structural_examples["CONDITIONAL_KEEP"][:4]
        + structural_examples["SHIP"][:2]
    )
    out = []
    for i, pod in enumerate(POD_QUERY_EXAMPLES):
        ex = pool[i % len(pool)]
        result = pod_conditioned_grade(ex["structural_grade"], ex["structural_reason"], pod, ex["_feats"])
        out.append({
            "hand": ex["hand"], "land_count": ex["land_count"],
            "pod": pod,
            **{k: v for k, v in result.items()},
        })
    return out


def _strip_internal(ex):
    return {k: v for k, v in ex.items() if k != "_feats"}


def main():
    print_run_banner()
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()

    target_counts = {"SNAP_KEEP": 10, "CONDITIONAL_KEEP": 10, "SHIP": 10, "MISLEADING": 5}
    buckets, misleading = collect_examples(cards, combos, on_play=True, seed=7, target_counts=target_counts)

    pod_examples = build_pod_examples(buckets, cards)

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_005_EXAMPLES",
        "snap_keeps": [_strip_internal(e) for e in buckets["SNAP_KEEP"]],
        "conditional_keeps": [_strip_internal(e) for e in buckets["CONDITIONAL_KEEP"]],
        "mulligans": [_strip_internal(e) for e in buckets["SHIP"]],
        "misleading_hands": [_strip_internal(e) for e in misleading],
        "pod_conditioned_examples": pod_examples,
        "counts": {
            "snap_keeps": len(buckets["SNAP_KEEP"]), "conditional_keeps": len(buckets["CONDITIONAL_KEEP"]),
            "mulligans": len(buckets["SHIP"]), "misleading_hands": len(misleading),
            "pod_conditioned_examples": len(pod_examples),
        },
    }

    out_path = REPO_ROOT / "results" / "solo_baseline" / "mull005_annotated_examples.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result["counts"], indent=2))
    if misleading:
        print(f"\n=== sample misleading hand ===")
        print(json.dumps(_strip_internal(misleading[0]), indent=2))
    if len(misleading) < target_counts["MISLEADING"]:
        print(f"\nWARNING: only found {len(misleading)}/{target_counts['MISLEADING']} misleading-hand examples "
              f"within max_draws - consider raising --max-draws or the seed.")


if __name__ == "__main__":
    main()
