"""SIM-DECKBUILD-006 E1 (HIGHEST priority) — early structural cost of dropping Avacyn's Pilgrim,
and Lotho's compensating value, via paired Monte Carlo across the A/B/C/D factorial configs.

Required primary number (per assignment): the pp change in T2-engine probability from
A_5D_NO_LOTHO -> B_4D_NO_LOTHO (pure Pilgrim-removal structural cost, no Lotho compensation).
Also reports every other single-factor-isolating pairwise comparison among A/B/C/D so E1's output
alone is enough to see both factors' marginal contributions, not just the one required number:
  A->B: pure cost of losing Pilgrim (no Lotho present in either config)
  A->C: pure value of adding Lotho while keeping Pilgrim (5 dorks either way)
  B->D: Lotho's compensation value in the 4-dork world (does it cover what A->B lost?)
  C->D: Pilgrim's marginal value when Lotho is already present
  A->D: the net, real proposed swap end to end (Pilgrim out AND Lotho in, simultaneously)

Directly reuses build_deckbuild004_e1_early_cost.py's machinery (census/paired-flip functions,
operational definitions, paired-seed convention/disclaimer) - same engine, same metric
definitions, so DECKBUILD-004's six-to-five 0.14pp result and this task's five-to-four result are
computed identically and can be compared without a methodology confound. The only addition: Lotho's
real trigger (apply_lotho_trigger_if_any) is applied after every develop_turn() call, so any config
containing Lotho has its Treasure/life-loss effects actually reflected in the metrics.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deterministic_combos, deck_provenance_fields  # noqa: E402
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
import deckbuild006_cards as d6  # noqa: E402
from deckbuild006_variants import load_deckbuild006_cards, deckbuild006_cards_pool, build, VARIANTS  # noqa: E402
from run_contextual_london_mulligan_sim import make_contextual_keep_policy  # noqa: E402
from build_deckbuild004_e1_early_cost import (  # noqa: E402
    MANA_ENGINE_EXCLUSIONS, aggregate_census, keep_rates_by_depth,
)

PRIMARY_COMPARISON = ("A_5D_NO_LOTHO", "B_4D_NO_LOTHO")
ALL_COMPARISONS = [
    ("A_5D_NO_LOTHO", "B_4D_NO_LOTHO"),
    ("A_5D_NO_LOTHO", "C_5D_LOTHO"),
    ("B_4D_NO_LOTHO", "D_4D_LOTHO"),
    ("C_5D_LOTHO", "D_4D_LOTHO"),
    ("A_5D_NO_LOTHO", "D_4D_LOTHO"),
]


def _one_hand(names, rng, cards, combos, on_play=True):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    library = lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    for t in range(1, 4):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        d6.apply_lotho_trigger_if_any(state, t)
        per_turn[t] = snapshot_metrics(state, cards, combos)
    per_turn["first_engine_turn"] = next(
        (t for t in (1, 2, 3) if per_turn[t]["any_engine_active"]), None
    )
    return per_turn


def _autonomous_engine(m):
    return any(n in m["engines_active"] for n in m["engines_active"]) and any(
        n not in MANA_ENGINE_EXCLUSIONS for n in m["engines_active"]
    )


def census_metrics(names, cards, combos, seed, n):
    rng = random.Random(seed)
    return [_one_hand(names, rng, cards, combos) for _ in range(n)]


def paired_flip_metrics(names_a, names_b, cards, combos, seed, n, policy):
    """SAME seed drives both variants (paired-seed convention, see module docstring)."""
    keep_flip_a_to_b_ship = 0
    ship_flip_b_to_a_keep = 0
    engine_delay = []
    engine_never_a_but_b_does = 0
    both_agree = 0
    total = 0
    for i in range(n):
        rng_a = random.Random(seed * 1_000_003 + i)
        rng_b = random.Random(seed * 1_000_003 + i)
        lib_a = names_a[:]
        rng_a.shuffle(lib_a)
        hand_a, library_a = lib_a[:7], lib_a[7:]
        lib_b = names_b[:]
        rng_b.shuffle(lib_b)
        hand_b, library_b = lib_b[:7], lib_b[7:]

        keep_a = policy(hand_a, library_a, True, cards, combos, 0)
        keep_b = policy(hand_b, library_b, True, cards, combos, 0)
        total += 1
        if keep_a and not keep_b:
            keep_flip_a_to_b_ship += 1
        elif keep_b and not keep_a:
            ship_flip_b_to_a_keep += 1
        else:
            both_agree += 1

        state_a = HandState(hand_a, library_a, on_play=True, rng=random.Random(seed * 7 + i), cards=cards)
        state_b = HandState(hand_b, library_b, on_play=True, rng=random.Random(seed * 7 + i), cards=cards)
        first_a = first_b = None
        for t in range(1, 4):
            develop_turn(state_a, cards, priority_order=DEFAULT_PRIORITY)
            d6.apply_lotho_trigger_if_any(state_a, t)
            m = snapshot_metrics(state_a, cards, combos)
            if first_a is None and m["any_engine_active"]:
                first_a = t
            develop_turn(state_b, cards, priority_order=DEFAULT_PRIORITY)
            d6.apply_lotho_trigger_if_any(state_b, t)
            m2 = snapshot_metrics(state_b, cards, combos)
            if first_b is None and m2["any_engine_active"]:
                first_b = t
        if first_a is not None and first_b is not None:
            engine_delay.append(first_b - first_a)
        elif first_a is None and first_b is not None:
            engine_never_a_but_b_does += 1

    return {
        "sample_size": total,
        "keep_A_ship_B_rate": keep_flip_a_to_b_ship / total,
        "ship_A_keep_B_rate": ship_flip_b_to_a_keep / total,
        "both_agree_rate": both_agree / total,
        "mean_engine_turn_delta_B_minus_A": (sum(engine_delay) / len(engine_delay)) if engine_delay else None,
        "pct_hands_engine_only_reachable_in_B": engine_never_a_but_b_does / total,
        "note": "A is the first-named variant, B the second. Paired-seed = same RNG seed drives "
                "both variants' draws (project convention), NOT a literal same-7-cards guarantee "
                "since the two variants' card lists differ.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=15000)
    ap.add_argument("--flip-n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=81006)
    args = ap.parse_args()

    d6.install_new_card_tables()
    try:
        payload, base_rows = load_deckbuild006_cards()
        cards_pool = deckbuild006_cards_pool(base_rows)
        base_names = list(base_rows.keys())
        combos = load_deterministic_combos()

        built = {v: build(base_names, cards_pool, v) for v in VARIANTS}
        # Treasure Token is never a decklist entry (it's a token Lotho creates in-game) but its
        # row data must be present in every variant's cards dict - apply_lotho_trigger_if_any()
        # can append one to state.nonland_perms at runtime regardless of whether the variant's
        # own 98 names list happens to include it (it never does).
        cards_by_variant = {
            v: {**{n: cards_pool[n] for n in names}, d6.TREASURE_NAME: cards_pool[d6.TREASURE_NAME]}
            for v, names in built.items()
        }

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_006_E1_EARLY_COST", "evidence_type": "goldfish",
            "operational_definitions_note": (
                "T2_autonomous_engine excludes Kinnan/Deathrite Shaman/Gaea's Cradle (mana tools, "
                "not independent value engines) - identical definition to DECKBUILD-004's E1, "
                "reused verbatim so results are comparable without a methodology confound. "
                "color_failure_rate = 1 - all_wubg at T3."
            ),
            "paired_seed_note": (
                "Same RNG seed drives both variants' draws (project convention) - NOT a literal "
                "same-7-cards guarantee, since the two variants' underlying card lists differ."
            ),
            "census_by_variant": {},
            "comparisons": {},
        }

        policy = make_contextual_keep_policy("gated")
        for v in VARIANTS:
            t0 = time.time()
            results = census_metrics(built[v], cards_by_variant[v], combos, args.seed, args.census_n)
            agg = aggregate_census(results)
            agg.update(keep_rates_by_depth(built[v], cards_by_variant[v], combos, args.seed + 500, args.flip_n, policy))
            out["census_by_variant"][v] = agg
            print(f"{v} census ({time.time()-t0:.1f}s)")

        for a, b in ALL_COMPARISONS:
            t0 = time.time()
            flip = paired_flip_metrics(built[a], built[b], cards_pool, combos, args.seed, args.flip_n, policy)
            out["comparisons"][f"{a}_vs_{b}"] = {
                "census_delta": {
                    k: out["census_by_variant"][b][k] - out["census_by_variant"][a][k]
                    for k in out["census_by_variant"][a]
                },
                "flip_metrics": flip,
            }
            print(f"{a} vs {b} ({time.time()-t0:.1f}s)")

        a, b = PRIMARY_COMPARISON
        key_delta = out["comparisons"][f"{a}_vs_{b}"]["census_delta"]["T2_any_engine"] * 100
        band = ("trivial" if abs(key_delta) < 0.5 else "modest" if abs(key_delta) < 1.5
                else "meaningful" if abs(key_delta) < 3 else "severe")
        out["required_key_number"] = {
            "exact_pp_change_T2_engine_probability_A_5D_NO_LOTHO_to_B_4D_NO_LOTHO": key_delta,
            "interpretation_band": band,
            "compare_to_deckbuild004_six_to_five_result": (
                "DECKBUILD-004's six->five dork transition (Elves of Deep Shadow->Neoform) "
                "measured +0.14pp T2-engine change (~neutral). This E1 run's five->four number "
                "above is this task's own independent measurement, computed with the identical "
                "T2_autonomous_engine/T2_any_engine definitions and paired-seed methodology - see "
                "results/solo_baseline/deckbuild004_e1_early_cost.json for the original number if "
                "a live side-by-side is needed; not re-asserted here as a fact to avoid drift if "
                "that file is ever regenerated."
            ),
        }
    finally:
        d6.uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild006_e1_early_cost.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_key_number"], indent=2))


if __name__ == "__main__":
    main()
