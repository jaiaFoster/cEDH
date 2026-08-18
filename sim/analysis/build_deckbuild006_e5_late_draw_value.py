"""SIM-DECKBUILD-006 E5 (secondary priority) — late-draw value, T4-T6 extension.

Phase-1 checkpoint (E1+E2) found the 5->4 dork structural cost trivial-to-modest at every metric
(all deltas <1pp / <0.1 mean creatures at T1-T3) - per the assignment's own execution_order this
means proceeding directly to E5/E6 rather than building out E3 (Cradle network, already
substantially answered by E2's structural-ceiling numbers) or E4 (Pod fodder, whose population is
barely touched by a ~0.07-creature average difference). See deckbuild006_report.md section 5 for
the full checkpoint writeup.

This block extends the SAME validated T1-3 engine to T4-T6 - develop_turn() has no turn-3 cap
anywhere in its own logic (verified by inspection: the T1-3 convention lives entirely in CALLING
code's `for t in range(1,4)` loops, never in develop_turn itself), so running it further is not a
new or different model, just a longer run of the identical one. This is the first time this
project has looked past T3, so results here are not directly comparable to any prior T1-3-only
census without noting the turn count explicitly.

Question: does Lotho's OWN self-trigger value (the pilot's own second-spell-of-the-turn, the only
trigger source this solo engine can see - opponent triggers are architecturally invisible, see E6)
compound over a longer game enough to matter, and does the tiny early structural gap between the
4-dork and 5-dork configs grow, shrink, or stay flat by T6?
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

MAX_TURN = 6


def _one_hand(names, rng, cards, combos, on_play=True):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    library = lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    cumulative_lotho_triggers = 0
    cumulative_life_lost_to_lotho = 0
    for t in range(1, MAX_TURN + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        fired = d6.apply_lotho_trigger_if_any(state, t)
        if fired:
            cumulative_lotho_triggers += 1
            cumulative_life_lost_to_lotho += 1
        m = snapshot_metrics(state, cards, combos)
        m["cumulative_lotho_triggers"] = cumulative_lotho_triggers
        m["cumulative_life_lost_to_lotho"] = cumulative_life_lost_to_lotho
        per_turn[t] = m
    return per_turn


def census(names, cards, combos, seed, n):
    rng = random.Random(seed)
    return [_one_hand(names, rng, cards, combos) for _ in range(n)]


def aggregate(results):
    n = len(results)
    out = {}
    for t in range(1, MAX_TURN + 1):
        def mean(key):
            return sum(r[t][key] for r in results) / n
        def rate(fn):
            return sum(1 for r in results if fn(r[t])) / n
        out[f"T{t}"] = {
            "any_engine_active_rate": rate(lambda m: m["any_engine_active"]),
            "two_plus_engines_active_rate": rate(lambda m: m["two_plus_engines_active"]),
            "functional_mana_rate": rate(lambda m: m["mana_2plus"]),
            "mean_cumulative_lotho_triggers": mean("cumulative_lotho_triggers"),
            "mean_cumulative_life_lost_to_lotho": mean("cumulative_life_lost_to_lotho"),
            "pct_at_least_one_lotho_trigger_by_this_turn": rate(lambda m: m["cumulative_lotho_triggers"] > 0),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=85006)
    args = ap.parse_args()

    d6.install_new_card_tables()
    try:
        payload, base_rows = load_deckbuild006_cards()
        cards_pool = deckbuild006_cards_pool(base_rows)
        base_names = list(base_rows.keys())
        combos = load_deterministic_combos()

        built = {v: build(base_names, cards_pool, v) for v in VARIANTS}
        cards_by_variant = {
            v: {**{n: cards_pool[n] for n in names}, d6.TREASURE_NAME: cards_pool[d6.TREASURE_NAME]}
            for v, names in built.items()
        }

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_006_E5_LATE_DRAW_VALUE", "evidence_type": "goldfish",
            "max_turn_note": (
                f"Extends the same validated T1-3 engine to T1-T{MAX_TURN} - not a new model, a "
                "longer run of the identical develop_turn() loop (no turn-3 cap exists in that "
                "function itself). First time this project has looked past T3; not directly "
                "comparable to prior T1-3-only census tables without matching the turn number."
            ),
            "lotho_self_trigger_only_note": (
                "cumulative_lotho_triggers/life_lost counts ONLY the pilot's own second-spell "
                "triggers (the sole source this solo engine can see) - opponent second-spell "
                "triggers, Lotho's other real value driver in an actual pod, are architecturally "
                "invisible here and covered qualitatively, with explicit scenario bands, by E6."
            ),
            "by_turn": {},
        }

        for v in VARIANTS:
            t0 = time.time()
            results = census(built[v], cards_by_variant[v], combos, args.seed, args.census_n)
            out["by_turn"][v] = aggregate(results)
            print(f"{v} ({time.time()-t0:.1f}s)")

        deltas = {}
        for a, b in [("A_5D_NO_LOTHO", "B_4D_NO_LOTHO"), ("A_5D_NO_LOTHO", "D_4D_LOTHO")]:
            deltas[f"{a}_vs_{b}"] = {
                t: {k: out["by_turn"][b][t][k] - out["by_turn"][a][t][k] for k in out["by_turn"][a][t]}
                for t in [f"T{i}" for i in range(1, MAX_TURN + 1)]
            }
        out["deltas"] = deltas
        out["required_key_number"] = {
            "T6_any_engine_active_delta_A_to_D": deltas["A_5D_NO_LOTHO_vs_D_4D_LOTHO"]["T6"]["any_engine_active_rate"] * 100,
            "T6_mean_cumulative_lotho_triggers_in_D": out["by_turn"]["D_4D_LOTHO"]["T6"]["mean_cumulative_lotho_triggers"],
            "interpretation": (
                "If the T2/T3 structural gap (E1/E2) does not widen by T6, the 5->4 transition's "
                "cost is confirmed flat, not compounding, over this engine's full modeled horizon. "
                "The Lotho self-trigger count shows the FLOOR of Lotho's real value (opponent "
                "triggers, uncounted here, can only add to it - see E6)."
            ),
        }
    finally:
        d6.uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild006_e5_late_draw_value.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_key_number"], indent=2))


if __name__ == "__main__":
    main()
