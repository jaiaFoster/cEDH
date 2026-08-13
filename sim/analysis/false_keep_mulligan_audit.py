"""SIM-001 SOLO-004 section 15 — false-keep / false-mulligan audit.

For a fresh sample of random sevens, compares SIMPLE_RULES' decision against the actual SIMULATED
outcome of keeping that hand as dealt (ground truth - not a model prediction of ground truth,
the real T1-T3 trajectory) and against TREE_DEPTH4's decision (the richer, less-simplified
model). Reports:
  - False keeps: SIMPLE_RULES says KEEP, but the hand's actual outcome was poor
    (not t3_any_strong_state) AND TREE_DEPTH4 would have shipped it.
  - False mulligans: SIMPLE_RULES says SHIP, but the hand's actual outcome (had it been kept
    as-is) was strong (t3_any_strong_state) AND TREE_DEPTH4 would have kept it.
Requiring TREE_DEPTH4 agreement on the "should have been the other way" call filters out cases
that are just noise in a single ground-truth draw (a hand can look weak on paper and get lucky,
or vice versa, independent of any real heuristic defect) - this way "false keep"/"false mulligan"
means two independent signals (the richer model AND the ground-truth trajectory) both disagree
with SIMPLE_RULES, not that a single unlucky/lucky playout happened to go the other way.
"""
import argparse
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from opening_hand_features import extract_opener_features
from run_solo004_dataset import simulate_hand_outcome
from candidate_mulligan_policies import policy_tree_depth4, policy_simple_rules

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=777)  # distinct from the primary dataset's seed 42 - a genuine holdout sample
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo004_false_keep_mulligan_audit.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)

    false_keeps = []
    false_mulligans = []
    n_false_keep, n_false_mulligan = 0, 0

    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]

        feats = extract_opener_features(hand, library, on_play, cards)
        simple_keep = policy_simple_rules(feats)
        tree_keep = policy_tree_depth4(feats)
        row = simulate_hand_outcome(hand, library, on_play, cards, combos)
        actual_strong = row["out_t3__t3_any_strong_state"]

        if simple_keep and not actual_strong and not tree_keep:
            n_false_keep += 1
            if len(false_keeps) < 10:
                false_keeps.append({
                    "hand": sorted(hand), "land_count": feats["land_count"],
                    "simple_rules_decision": "KEEP", "tree_depth4_decision": "MULLIGAN",
                    "actual_t3_any_strong_state": actual_strong,
                    "actual_t3_stalled": row["out_t3__t3_stalled"],
                    "actual_mana_shortfall": row["out__mana_shortfall_t3"],
                    "outcome_tags": row["outcome_tags"],
                })
        if not simple_keep and actual_strong and tree_keep:
            n_false_mulligan += 1
            if len(false_mulligans) < 10:
                false_mulligans.append({
                    "hand": sorted(hand), "land_count": feats["land_count"],
                    "simple_rules_decision": "MULLIGAN", "tree_depth4_decision": "KEEP",
                    "actual_t3_any_strong_state": actual_strong,
                    "family_tags": row["family_tags"],
                })

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_004_FALSE_KEEP_MULLIGAN_AUDIT",
        "sample_count": args.count, "seed": args.seed, "seat": args.seat,
        "note": (
            "False keep = SIMPLE_RULES keeps, actual outcome was NOT strong-state, AND "
            "TREE_DEPTH4 independently would have shipped it. False mulligan = SIMPLE_RULES "
            "ships, actual outcome WAS strong-state, AND TREE_DEPTH4 independently would have "
            "kept it. Requiring both signals filters single-draw luck/unluck from genuine "
            "heuristic defects."
        ),
        "false_keep_rate": n_false_keep / args.count,
        "false_mulligan_rate": n_false_mulligan / args.count,
        "false_keep_examples": false_keeps,
        "false_mulligan_examples": false_mulligans,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"false_keep_rate={result['false_keep_rate']:.3%}  false_mulligan_rate={result['false_mulligan_rate']:.3%}")
    print(f"\n=== {len(false_keeps)} false-keep examples ===")
    for ex in false_keeps[:5]:
        print(f"  land_count={ex['land_count']}  tags={ex['outcome_tags']}")
        print(f"    hand={ex['hand']}")
    print(f"\n=== {len(false_mulligans)} false-mulligan examples ===")
    for ex in false_mulligans[:5]:
        print(f"  land_count={ex['land_count']}  family_tags={ex['family_tags']}")
        print(f"    hand={ex['hand']}")


if __name__ == "__main__":
    main()
