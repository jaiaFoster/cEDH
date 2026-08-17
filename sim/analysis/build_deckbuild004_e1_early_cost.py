"""SIM-DECKBUILD-004 E1 — mulligan and early-engine opportunity cost.

Paired Monte Carlo: B0 vs B1/B2/B3 (primary_comparisons) + the SIX_DORKS_VS_FIVE special
comparison (Elves of Deep Shadow -> Neoform only, isolated). "Paired" here means the SAME RNG
seed drives both variants' draws (this project's established convention, e.g.
MANA-AUDIT-002's config runs) - not a literal same-7-cards guarantee, since the two variants'
card lists differ; disclosed, not overclaimed.

Operational definitions for two assignment-named metrics that aren't already-existing fields
(disclosed rather than silently guessed):
  - T2_autonomous_engine: any_engine_active at T2 EXCLUDING Kinnan/Deathrite Shaman/Gaea's Cradle
    (mana-multiplier/mana-source "engines" in this project's ENGINES taxonomy, not independent
    card-advantage/tax value engines) - i.e. a genuine value engine, not a mana tool.
  - color_failure_rate: 1 - all_wubg, at T3 (this project's existing all_wubg field, inverted).
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, ENGINES  # noqa: E402
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build, VARIANTS  # noqa: E402
from run_contextual_london_mulligan_sim import make_contextual_keep_policy, simulate_one_contextual_sequence  # noqa: E402

MANA_ENGINE_EXCLUSIONS = {"Kinnan, Bonder Prodigy", "Deathrite Shaman", "Gaea's Cradle"}

PRIMARY_COMPARISONS = [("B0_BASELINE", "B1_ENGINE_SWAP"), ("B0_BASELINE", "B2_CONVERSION_SWAP"),
                        ("B0_BASELINE", "B3_FULL_PACKAGE")]
SPECIAL_COMPARISON = ("B0_BASELINE", "SIX_DORKS_VS_FIVE")


def _one_hand(names, rng, cards, combos, on_play=True):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    library = lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    for t in range(1, 4):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
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
    results = [_one_hand(names, rng, cards, combos) for _ in range(n)]
    return results


def aggregate_census(results):
    n = len(results)
    def rate(fn):
        return sum(1 for r in results if fn(r)) / n
    return {
        "T1_premium_engine": rate(lambda r: r[1]["premium_engine_active"]),
        "T2_any_engine": rate(lambda r: r[2]["any_engine_active"]),
        "T2_autonomous_engine": rate(lambda r: _autonomous_engine(r[2])),
        "T2_engine_plus_interaction_retained": rate(lambda r: r[2]["engine_plus_interaction"]),
        "T2_engine_plus_persistent_mana_remaining": rate(
            lambda r: r[2]["any_engine_active"] and r[2]["mana_remaining_unused"] > 0
        ),
        "T3_two_plus_engines": rate(lambda r: r[3]["two_plus_engines_active"]),
        "T1_functional_mana": rate(lambda r: r[1]["mana_2plus"]),
        "T2_functional_mana": rate(lambda r: r[2]["mana_2plus"]),
        "T3_functional_mana": rate(lambda r: r[3]["mana_2plus"]),
        "color_failure_rate_T3": rate(lambda r: not r[3]["all_wubg"]),
        "mean_final_hand_size_T3": sum(r[3]["cards_in_hand"] for r in results) / n,
    }


def paired_flip_metrics(names_a, names_b, cards, combos, seed, n, policy):
    """SAME seed drives both variants (this project's established paired-seed convention).
    Flip metrics compare the SAME-INDEX draw across variant A and B."""
    keep_flip_a_to_b_ship = 0  # A keeps, B ships (interpreted as "keep_to_mull_flip_due_to_X_loss")
    ship_flip_b_to_a_keep = 0  # B keeps, A ships ("mull_to_keep_flip_due_to_X_gain")
    engine_delay = []  # B's first-engine-turn minus A's, when both reach an engine
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
            m = snapshot_metrics(state_a, cards, combos)
            if first_a is None and m["any_engine_active"]:
                first_a = t
            develop_turn(state_b, cards, priority_order=DEFAULT_PRIORITY)
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
        "note": "A is the first-named variant, B the second - e.g. for (B0, SIX_DORKS_VS_FIVE): "
                "keep_A_ship_B_rate = 'keep_to_mull_flip_due_to_Elves_loss' rate; "
                "ship_A_keep_B_rate = 'mull_to_keep_flip_due_to_Neoform_gain' rate; a positive "
                "mean_engine_turn_delta_B_minus_A = B's engine arrives LATER on average.",
    }


def keep_rates_by_depth(names, cards, combos, seed, n, policy, max_mulligans=2):
    """P(keep) at each London mulligan depth (7/6/5), conditional on having reached that
    decision point (i.e. mulled every prior attempt) - not simulate_one_contextual_sequence's
    single final-outcome record, which hides the per-depth pass/fail this metric needs."""
    depth_attempts = {7: 0, 6: 0, 5: 0}
    depth_keeps = {7: 0, 6: 0, 5: 0}
    final_hand_sizes = []
    rng = random.Random(seed)
    names_list = list(names)
    for _ in range(n):
        mulligans = 0
        while True:
            size = 7 - mulligans
            lib = names_list[:]
            rng.shuffle(lib)
            hand = lib[:7]
            library = lib[7:]
            if size in depth_attempts:
                depth_attempts[size] += 1
            keep = policy(hand, library, True, cards, combos, mulligans)
            if size in depth_attempts and keep:
                depth_keeps[size] += 1
            if keep or mulligans >= max_mulligans:
                final_hand_sizes.append(size)
                break
            mulligans += 1
    return {
        "keep_rate_7": (depth_keeps[7] / depth_attempts[7]) if depth_attempts[7] else None,
        "keep_rate_6": (depth_keeps[6] / depth_attempts[6]) if depth_attempts[6] else None,
        "keep_rate_5": (depth_keeps[5] / depth_attempts[5]) if depth_attempts[5] else None,
        "average_final_hand_size": sum(final_hand_sizes) / len(final_hand_sizes),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=15000)
    ap.add_argument("--flip-n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=81004)
    args = ap.parse_args()

    payload, base_cards = load_deck_cards()
    cards_pool = all_cards_dict(base_cards)
    install_new_card_tables()
    base_names = list(base_cards.keys())
    combos = load_deterministic_combos()

    try:
        built = {v: build(base_names, cards_pool, v) for v in VARIANTS}
        cards_by_variant = {v: {n: cards_pool[n] for n in names} for v, names in built.items()}

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_004_E1_EARLY_COST", "evidence_type": "goldfish",
            "operational_definitions_note": (
                "T2_autonomous_engine excludes Kinnan/Deathrite Shaman/Gaea's Cradle (mana tools "
                "in this project's ENGINES taxonomy, not independent card-advantage/tax value "
                "engines). color_failure_rate = 1 - all_wubg at T3. Both disclosed, not asserted "
                "as the assignment's own unstated intent."
            ),
            "paired_seed_note": (
                "'Paired' = same RNG seed drives both variants' draws (this project's established "
                "convention, e.g. MANA-AUDIT-002's config comparisons) - NOT a literal same-7-"
                "cards-except-swapped guarantee, since the two variants' underlying card lists "
                "differ (a shuffle of a different list, even with the same seed, does not "
                "necessarily deal the same 7 cards)."
            ),
            "census_by_variant": {},
            "primary_comparisons": {},
            "special_comparison_six_dorks_vs_five": {},
        }

        policy = make_contextual_keep_policy("gated")
        for v in ("B0_BASELINE", "B1_ENGINE_SWAP", "B2_CONVERSION_SWAP", "B3_FULL_PACKAGE", "SIX_DORKS_VS_FIVE"):
            t0 = time.time()
            results = census_metrics(built[v], cards_by_variant[v], combos, args.seed, args.census_n)
            agg = aggregate_census(results)
            agg.update(keep_rates_by_depth(built[v], cards_by_variant[v], combos, args.seed + 500, args.flip_n, policy))
            out["census_by_variant"][v] = agg
            print(f"{v} census ({time.time()-t0:.1f}s)")

        for a, b in PRIMARY_COMPARISONS:
            t0 = time.time()
            flip = paired_flip_metrics(
                built[a], built[b], cards_pool, combos, args.seed, args.flip_n, policy
            )
            out["primary_comparisons"][f"{a}_vs_{b}"] = {
                "census_delta": {
                    k: out["census_by_variant"][b][k] - out["census_by_variant"][a][k]
                    for k in out["census_by_variant"][a]
                },
                "flip_metrics": flip,
            }
            print(f"{a} vs {b} flip metrics ({time.time()-t0:.1f}s)")

        a, b = SPECIAL_COMPARISON
        t0 = time.time()
        out["special_comparison_six_dorks_vs_five"] = {
            "census_delta": {
                k: out["census_by_variant"][b][k] - out["census_by_variant"][a][k]
                for k in out["census_by_variant"][a]
            },
            "flip_metrics": paired_flip_metrics(built[a], built[b], cards_pool, combos, args.seed, args.flip_n, policy),
        }
        print(f"SIX_DORKS_VS_FIVE flip metrics ({time.time()-t0:.1f}s)")

        key_delta = out["special_comparison_six_dorks_vs_five"]["census_delta"]["T2_any_engine"] * 100
        band = ("trivial" if abs(key_delta) < 0.5 else "modest" if abs(key_delta) < 1.5
                else "meaningful" if abs(key_delta) < 3 else "severe")
        out["required_key_number"] = {
            "exact_pp_change_T2_engine_probability_Elves_to_Neoform": key_delta,
            "interpretation_band": band,
        }
    finally:
        uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild004_e1_early_cost.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_key_number"], indent=2))


if __name__ == "__main__":
    main()
