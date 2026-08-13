"""SIM-001 SOLO-002 PART E — paired-seed deckbuilding harness (infrastructure check).

Confirms the simulator supports rerunning the EXACT SAME shuffle order across two card-pool
variants (e.g. a proposed card swap), so a swap's effect is isolated from sampling noise (a
paired comparison, not two independent samples that could disagree by chance alone). This module
is an infrastructure demonstration, not a deckbuilding recommendation: the swap used here
(Birthing Pod -> a synthetic basic Forest) exists only to prove the harness works, chosen because
Part A's census already shows Birthing Pod's real board impact is small (in ENGINES with a low
"usable_now" rate) and a basic land needs no card-cache lookup. Any REAL proposed swap would use
two real cards from data/cards_cache instead of a synthetic row.

Pairing mechanism: random.Random.shuffle is a pure index-permutation (Fisher-Yates) - it doesn't
look at list values, only positions. So if both variant card-pools have the same length and the
same base ordering except at the one swapped index, seeding two independent rng.Random(seed)
objects identically and shuffling each variant's name list produces the SAME sequence of index
swaps: whatever original position ends up at output slot k in variant A is the same original
position that ends up at slot k in variant B. The single swapped index is therefore drawn into
the SAME hand, on the SAME turn, in both variants - only that one card's identity differs.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from run_opening_hand_census import run_one_hand, PRIMARY_METRICS

REPO_ROOT = Path(__file__).resolve().parents[2]

SYNTHETIC_FOREST = {
    "name": "Forest", "type": "Basic Land — Forest", "text": "({T}: Add {G}.)",
    "mana_cost": "", "cmc": 0,
}


def build_variant(base_cards, remove_name, add_name, add_row):
    """Returns (names_in_base_order_with_swap, cards_dict) - same length/order as base_cards
    except add_name replaces remove_name at its original position, so the paired shuffle lines
    up index-for-index with the unmodified variant."""
    order = list(base_cards.keys())
    idx = order.index(remove_name)
    order[idx] = add_name
    cards = dict(base_cards)
    del cards[remove_name]
    cards[add_name] = add_row
    return order, cards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--on-play", action="store_true", default=True)
    ap.add_argument("--remove", default="Birthing Pod")
    ap.add_argument("--out", default=str(REPO_ROOT / "results" / "solo_baseline" / "solo002_part_e_paired_demo.json"))
    args = ap.parse_args()

    print_run_banner()
    payload, base_cards = load_deck_cards()
    combos = load_deterministic_combos()

    names_a = list(base_cards.keys())
    names_b, cards_b = build_variant(base_cards, args.remove, "Forest", SYNTHETIC_FOREST)

    rng_a = random.Random(args.seed)
    rng_b = random.Random(args.seed)

    t0 = time.time()
    paired_deltas = {m: 0 for m in ("mana_2plus_t1", "any_engine_active_t3", "meaningful_t3")}
    wins_a = {m: 0 for m in paired_deltas}
    wins_b = {m: 0 for m in paired_deltas}
    results_a, results_b = [], []
    for _ in range(args.count):
        ra = run_one_hand(names_a, rng_a, base_cards, combos, on_play=args.on_play)
        rb = run_one_hand(names_b, rng_b, cards_b, combos, on_play=args.on_play)
        results_a.append(ra)
        results_b.append(rb)
        va = {
            "mana_2plus_t1": ra[1]["mana_2plus"],
            "any_engine_active_t3": ra[3]["any_engine_active"],
            "meaningful_t3": not ra["failure_mode_t3"],
        }
        vb = {
            "mana_2plus_t1": rb[1]["mana_2plus"],
            "any_engine_active_t3": rb[3]["any_engine_active"],
            "meaningful_t3": not rb["failure_mode_t3"],
        }
        for m in paired_deltas:
            if va[m] and not vb[m]:
                wins_a[m] += 1
            elif vb[m] and not va[m]:
                wins_b[m] += 1
    elapsed = time.time() - t0

    def rate(results, key_fn):
        return sum(1 for r in results if key_fn(r)) / len(results)

    out = {
        # Variant A is the real, unmodified frozen deck (basics_substituted: false). Variant B is
        # a declared ablation of that same deck (docs/RUN_CLASSIFICATION.md requirement 2:
        # "never silently simplify" - basics_substituted may only be true with a non-empty
        # ablation_justification), recorded separately below rather than overriding the top-level
        # provenance block, since only variant B is altered.
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_002_PART_E",
        "sample_count": args.count,
        "seed": args.seed,
        "on_play": args.on_play,
        "swap": {"removed": args.remove, "added": "Forest (synthetic basic land, demo only)"},
        "variant_b_provenance": {
            **{k: v for k, v in deck_provenance_fields(payload).items() if k not in ("basics_substituted",)},
            "basics_substituted": True,
            "ablation_justification": (
                f"Infrastructure demonstration of the paired-seed harness (Part E): {args.remove} "
                "replaced with a synthetic basic Forest to test whether the harness correctly "
                "isolates a single card's effect via seed-matched paired reruns (sign test on "
                "per-hand outcome pairs), independent of sampling noise. Not a deckbuilding "
                "recommendation - see this file's module docstring."
            ),
        },
        "variant_a_rates": {
            "mana_2plus_t1": rate(results_a, lambda r: r[1]["mana_2plus"]),
            "any_engine_active_t3": rate(results_a, lambda r: r[3]["any_engine_active"]),
            "meaningful_t3": rate(results_a, lambda r: not r["failure_mode_t3"]),
        },
        "variant_b_rates": {
            "mana_2plus_t1": rate(results_b, lambda r: r[1]["mana_2plus"]),
            "any_engine_active_t3": rate(results_b, lambda r: r[3]["any_engine_active"]),
            "meaningful_t3": rate(results_b, lambda r: not r["failure_mode_t3"]),
        },
        "paired_sign_test": {
            m: {"variant_a_only": wins_a[m], "variant_b_only": wins_b[m], "net": wins_b[m] - wins_a[m]}
            for m in paired_deltas
        },
        "elapsed_seconds": elapsed,
        "note": (
            "Infrastructure demonstration only - proves seed-matched paired reruns work and "
            "isolate a swap's effect via a sign test on per-hand outcome pairs, rather than "
            "reporting only two independent aggregate rates that could disagree by sampling luck "
            "alone. The specific swap (a functional, situational tutor-engine for a basic land) "
            "is not a deckbuilding recommendation."
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({args.count} paired hands in {elapsed:.1f}s)")
    print(json.dumps(out["variant_a_rates"], indent=2))
    print(json.dumps(out["variant_b_rates"], indent=2))
    print(json.dumps(out["paired_sign_test"], indent=2))


if __name__ == "__main__":
    main()
