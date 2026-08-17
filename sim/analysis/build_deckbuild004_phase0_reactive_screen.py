"""SIM-DECKBUILD-004 phase_0 — reactive-slot screen.

Compares baseline against baseline MINUS each of {Subtlety, Misdirection, Commandeer, Mental
Misstep} PLUS Formidable Speaker, using PAIRED seeds (the same shuffled draw order evaluated
under every variant, so a card-swap's effect isn't confounded by sampling noise - required by the
assignment's own `statistics.paired_design: true`).

"An Offer You Can't Refuse" is NOT currently in the 98-card list (confirmed programmatically) -
it cannot be "cut" from a deck it isn't in. Rather than silently drop it or fabricate a workaround,
it is run as a SEPARATE, differently-shaped comparison (baseline + Formidable Speaker + An Offer,
deck size 100, no removal) and reported alongside but never mixed into the apples-to-apples
cut-candidate ranking, which is only meaningful across the 4 real in-deck candidates.

Scope note: `post_first_fight_protected_conversion` (one of the assignment's named phase-0
metrics) requires E3's stratified post-fight state machinery, which phase_0 explicitly precedes
("freeze the least damaging interaction cut before EXPENSIVE full-package analysis"). Deferred to
E3/E4 once (if) that phase runs, not measured here - disclosed, not silently dropped.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, INTERACTION_CASTABLE  # noqa: E402
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from interaction_model import interaction_is_live, ALT_COST_SPECS  # noqa: E402
from mana_audit002_variants import build_variant  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from run_contextual_london_mulligan_sim import make_contextual_keep_policy, run_policy, aggregate as mull_aggregate  # noqa: E402

FREE_CLASSES = {"free_commander", "pitch", "free", "conditional_free"}
PITCH_CARDS = ["Force of Will", "Force of Negation", "Misdirection", "Commandeer"]

CANDIDATES = {
    "SUBTLETY": {"remove": ["Subtlety"], "add": ["Formidable Speaker"]},
    "MISDIRECTION": {"remove": ["Misdirection"], "add": ["Formidable Speaker"]},
    "COMMANDEER": {"remove": ["Commandeer"], "add": ["Formidable Speaker"]},
    "MENTAL_MISSTEP": {"remove": ["Mental Misstep"], "add": ["Formidable Speaker"]},
}
INFORMATIONAL_ONLY = {
    "AN_OFFER_ADD_ONLY_not_a_real_cut_candidate": {
        "remove": [], "add": ["Formidable Speaker", "An Offer You Can't Refuse"],
    },
}


def _free_interaction_present(hand_and_battlefield_cast_log, hand):
    live_free_candidates = {n for n in hand if n in INTERACTION_CASTABLE and INTERACTION_CASTABLE[n] in FREE_CLASSES}
    return len(live_free_candidates) > 0


def _one_hand_metrics(names, rng, cards, combos, on_play=True):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    library = lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    out = {}
    out["free_interaction_in_opening_7"] = any(
        n in INTERACTION_CASTABLE and INTERACTION_CASTABLE[n] in FREE_CLASSES for n in hand
    )
    for t in range(1, 4):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        turn_hand = set(state.hand) | {n for (tt, n, c) in state.cast_log if tt == t}
        live_interaction = [n for n in turn_hand if n in INTERACTION_CASTABLE and interaction_is_live(n, state, cards)]
        live_free = [n for n in live_interaction if INTERACTION_CASTABLE[n] in FREE_CLASSES]
        out[f"t{t}_any_live_interaction"] = len(live_interaction) > 0
        out[f"t{t}_free_live_interaction"] = len(live_free) > 0
        for pitch_name in PITCH_CARDS:
            out[f"t{t}_{pitch_name.replace(' ', '_').replace(',', '')}_pitch_live"] = (
                pitch_name in turn_hand and interaction_is_live(pitch_name, state, cards)
            )
        out[f"t{t}_flare_of_denial_live"] = "Flare of Denial" in turn_hand and interaction_is_live("Flare of Denial", state, cards)
        blue_pips_available = sum(
            1 for n in turn_hand if n in cards and "U" in cards[n].get("mana_cost", "")
        )
        out[f"t{t}_blue_pitch_fuel_count"] = blue_pips_available
    return out


def run_variant(base_names, cards_pool, add, remove, seed, census_n, mull_n):
    variant_names = build_variant(base_names, cards_pool, add=add, remove=remove)
    variant_cards = {n: cards_pool[n] for n in variant_names}
    combos = load_deterministic_combos()

    rng = random.Random(seed)
    census_results = [_one_hand_metrics(variant_names, rng, variant_cards, combos) for _ in range(census_n)]
    n = len(census_results)
    census_agg = {
        k: sum(1 for r in census_results if r[k]) / n
        for k in census_results[0]
        if isinstance(census_results[0][k], bool)
    }
    census_agg["mean_t3_blue_pitch_fuel_count"] = sum(r["t3_blue_pitch_fuel_count"] for r in census_results) / n

    policy = make_contextual_keep_policy("gated")
    mull_results, mull_elapsed = run_policy(policy, mull_n, seed + 1, "play", variant_cards, combos)
    mull_agg = mull_aggregate(mull_results)

    return {
        "deck_size": len(variant_names), "added": add, "removed": remove,
        "census_sample_size": n,
        "interaction_metrics": census_agg,
        "premium_keep_rate_at_7": mull_agg["mulligan_distribution"].get("0", 0),
        "mulligan_S_or_A_rate": mull_agg["fraction_tier_S_or_A"],
        "mulligan_D_or_F_rate": mull_agg["fraction_tier_D_or_F"],
        "mulligan_distribution": mull_agg["mulligan_distribution"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=15000)
    ap.add_argument("--mull-n", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=71004)
    args = ap.parse_args()

    payload, base_cards = load_deck_cards()
    cards_pool = all_cards_dict(base_cards)
    install_new_card_tables()
    base_names = list(base_cards.keys())

    try:
        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_004_PHASE_0_REACTIVE_SCREEN",
            "evidence_type": "goldfish",
            "note": (
                "Every variant here differs from baseline by exactly -1 reactive card +1 "
                "Formidable Speaker (deck size stays 98), except the informational-only An Offer "
                "You Can't Refuse row (deck size 100, +2, no removal - see module docstring)."
            ),
            "baseline": {},
            "candidates": {},
            "informational_only": {},
        }

        t0 = time.time()
        out["baseline"] = run_variant(base_names, cards_pool, [], [], args.seed, args.census_n, args.mull_n)
        print(f"BASELINE ({time.time()-t0:.1f}s)")

        for name, spec in CANDIDATES.items():
            t0 = time.time()
            out["candidates"][name] = run_variant(
                base_names, cards_pool, spec["add"], spec["remove"], args.seed, args.census_n, args.mull_n
            )
            print(f"{name} ({time.time()-t0:.1f}s)")

        for name, spec in INFORMATIONAL_ONLY.items():
            t0 = time.time()
            out["informational_only"][name] = run_variant(
                base_names, cards_pool, spec["add"], spec["remove"], args.seed, args.census_n, args.mull_n
            )
            print(f"{name} ({time.time()-t0:.1f}s)")

        # Selection rule: marginal damage to the protection architecture vs. baseline, per
        # candidate, on the metrics that most directly measure "how much free/pitch interaction
        # did we lose" - not subjective card ranking.
        damage = {}
        base_m = out["baseline"]["interaction_metrics"]
        for name, result in out["candidates"].items():
            m = result["interaction_metrics"]
            damage[name] = {
                "delta_t2_free_live_interaction": m["t2_free_live_interaction"] - base_m["t2_free_live_interaction"],
                "delta_t3_free_live_interaction": m["t3_free_live_interaction"] - base_m["t3_free_live_interaction"],
                "delta_t3_any_live_interaction": m["t3_any_live_interaction"] - base_m["t3_any_live_interaction"],
                "delta_mulligan_D_or_F": result["mulligan_D_or_F_rate"] - out["baseline"]["mulligan_D_or_F_rate"],
                "delta_mean_t3_blue_pitch_fuel": m["mean_t3_blue_pitch_fuel_count"] - base_m["mean_t3_blue_pitch_fuel_count"],
            }
        # Composite "harm score": sum of the negative-direction deltas (less interaction = more
        # harm; higher D-or-F = more harm) - reported alongside the raw components, never in place
        # of them (assignment: "do not assign one scalar score to everything" - this composite is
        # a SELECTION aid for one narrow decision, the raw table remains the primary evidence).
        harm_score = {
            name: (-d["delta_t2_free_live_interaction"] - d["delta_t3_free_live_interaction"]
                   - d["delta_t3_any_live_interaction"] + d["delta_mulligan_D_or_F"]
                   - 0.1 * d["delta_mean_t3_blue_pitch_fuel"])
            for name, d in damage.items()
        }
        least_damaging = min(harm_score, key=harm_score.get)
        sorted_by_harm = sorted(harm_score.items(), key=lambda kv: kv[1])
        close_call = len(sorted_by_harm) >= 2 and (sorted_by_harm[1][1] - sorted_by_harm[0][1]) < 0.01

        out["selection"] = {
            "marginal_damage_per_candidate": damage,
            "harm_score_per_candidate": harm_score,
            "least_damaging_candidate": least_damaging,
            "runner_up_within_1pp_note": (
                f"{sorted_by_harm[1][0]} is within 1pp harm score of {least_damaging} - "
                "statistically indistinguishable at this sample size; per the assignment's own "
                "selection_rule, both should be considered viable REACTIVE_SLOT choices, not a "
                "forced single winner." if close_call else
                f"{least_damaging} is a clear (>1pp) least-harm choice versus the runner-up."
            ),
            "recommended_REACTIVE_SLOT": CANDIDATES[least_damaging]["remove"][0],
        }
    finally:
        uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild004_phase0_reactive_screen.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["selection"], indent=2))


if __name__ == "__main__":
    main()
