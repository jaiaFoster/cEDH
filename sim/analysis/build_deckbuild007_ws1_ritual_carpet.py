"""SIM-DECKBUILD-007 Workstream 1 — Dark Ritual vs Carpet of Flowers premium-engine acceleration.

Four configs (assignment's #1-4; #5 fifth-dork comparator skipped with disclosure - DECKBUILD-006
already built a dedicated, validated dork-density analysis and re-litigating it here would violate
this task's own "do not repeat prior validated findings" instruction):
  RITUAL_CURRENT: the real 99-card build (Dark Ritual in, no Carpet).
  RITUAL_REMOVED: 98 cards (Dark Ritual cut, nothing added).
  CARPET_INSTEAD: 99 cards (Dark Ritual OUT, Carpet of Flowers IN).
  BOTH_FLEX_CUT: 99 cards, Ritual KEPT + Carpet ADDED, funded by cutting Mindbreak Trap - a
    disclosed, controlled, no-op flex removal (same justification as DECKBUILD-006's C_5D_LOTHO
    funding cut: Mindbreak Trap's free-alt-cost condition, "opponent cast 3+ spells this turn,"
    can never be satisfied in this solo engine, so cutting it changes nothing else measured here).

Dark Ritual: real Monte Carlo. Uses a disclosed, EXPLICIT purposeful-cast policy (the generic
greedy loop cannot auto-cast an Instant with a net-mana effect - see deckbuild007_cards.py's own
docstring on why) - "cast Ritual on turn T iff doing so newly enables at least one of the four
named premium engines (Birthing Pod/Talion/Smothering Tithe/Seedborn Muse) that isn't cast yet,
using the turn's starting mana capacity." This is a real, defined, disclosed heuristic - not a
claim about optimal play, but a reasonable proxy for "does the pilot who holds up Ritual for this
purpose get the payoff."

Carpet of Flowers: its OWN cast decision is real Monte Carlo (a normal {G} enchantment through the
generic engine). Its MANA OUTPUT depends on target opponent's Island count - genuinely opponent-
dependent and NOT simulated here (per this task's explicit prohibition on fake precision from
assumed opponent behavior). Uses labeled, uncalibrated scenario bands instead (same
evidence_type: static_probability, confidence: low pattern as DECKBUILD-006's E6), with one real
rules correction folded in: Carpet counts ANY land with the Island TYPE, not just basic Islands -
original dual lands (Tropical Island, Underground Sea, Tundra) are printed "Land - X Island" and
have the Island type for every rules purpose, including this one. Since blue is well-established as
cEDH's single most staple-dense, most-played color (WebSearch-corroborated, a stable structural
format fact, not a fast-moving statistic - "do not over-research the metagame" per this task's own
instruction), this raises the realistic floor of Carpet's trigger condition above a naive
basic-Islands-only read.
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
from opening_hand_metrics import snapshot_metrics, _individually_affordable_from_turn_capacity  # noqa: E402
import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards, deckbuild007_cards_pool, build  # noqa: E402

TARGETS = {
    "Birthing Pod": {"cost": "{3}{G/P}", "relevant_turns": (1, 2)},
    "Talion, the Kindly Lord": {"cost": "{2}{U}{B}", "relevant_turns": (2,)},
    "Smothering Tithe": {"cost": "{3}{W}", "relevant_turns": (2,)},
    "Seedborn Muse": {"cost": "{3}{G}{G}", "relevant_turns": (3,)},
}
FUNDING_CUT_FOR_BOTH = "Mindbreak Trap"
MAX_TURN = 4

CARPET_SCENARIO_BANDS = {
    "SLOW_MIDRANGE_SLOP_POD": {
        "avg_opponent_islands_by_turn": {1: 0.3, 2: 0.6, 3: 1.0, 4: 1.4},
        "rationale": "Midrange/'slop' pods lean less blue-dense on average; still nonzero because "
                     "blue remains the format's single most-played color even outside dedicated "
                     "control shells (Rhystic Study/Mystic Remora-style splashes are common).",
    },
    "TYPICAL_CEDH_POD": {
        "avg_opponent_islands_by_turn": {1: 0.5, 2: 1.0, 3: 1.6, 4: 2.1},
        "rationale": "Blue is the most staple-dense color in the format by a wide margin - most "
                     "competitive decks run it as a primary or secondary color. Counts original "
                     "dual lands with the Island type (Tropical Island/Underground Sea/Tundra), "
                     "not just basics - a real rules fact, not an assumption.",
    },
    "FAST_TURBO_BLUE_HEAVY_POD": {
        "avg_opponent_islands_by_turn": {1: 0.8, 2: 1.5, 3: 2.3, 4: 3.0},
        "rationale": "Fast combo/control pods skew even more blue-dense (Thoracle, Rog Si, "
                     "Kinnan-mirror, stax-control shells) - the scenario where Carpet's design "
                     "intent (accelerating against blue-heavy tables) should matter most.",
    },
}


def _one_hand_baseline(names, rng, cards, combos, on_play=True):
    """No Ritual usage - clean baseline for the 'natural' timing of the 4 targets."""
    lib = names[:]
    rng.shuffle(lib)
    hand, library = lib[:7], lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    for t in range(1, MAX_TURN + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        m = snapshot_metrics(state, cards, combos)
        m["carpet_on_battlefield"] = any(p.name == d7.CARPET_NAME for p in state.nonland_perms)
        per_turn[t] = m
    per_turn["first_cast_turn"] = {
        name: next((t for (t, n, c) in state.cast_log if n == name), None) for name in TARGETS
    }
    return per_turn


def _one_hand_with_ritual_policy(names, rng, cards, combos, on_play=True):
    """Purposeful-Ritual policy (see module docstring). Also returns Ritual-usage bookkeeping for
    stranded-rate/dead-rate metrics."""
    lib = names[:]
    rng.shuffle(lib)
    hand, library = lib[:7], lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    ritual_cast_turn = None
    ritual_enabled_target = None
    stranded_units = None
    for t in range(1, MAX_TURN + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        already_cast = {n for (tt, n, c) in state.cast_log if n in TARGETS}
        if d7.DARK_RITUAL_NAME in state.hand and ritual_cast_turn is None:
            for name, spec in TARGETS.items():
                if name in already_cast or t not in spec["relevant_turns"] or name not in state.hand:
                    continue
                afford_now = _individually_affordable_from_turn_capacity(
                    spec["cost"], state.turn_start_mana, state.turn_start_colors
                )
                afford_with_ritual = _individually_affordable_from_turn_capacity(
                    spec["cost"], state.turn_start_mana + 2, state.turn_start_colors | {"B"}
                )
                if not afford_now and afford_with_ritual:
                    fired = d7.try_cast_dark_ritual(state, cards)
                    if fired:
                        ritual_cast_turn = t
                        ritual_enabled_target = name
                        # Attempt the target immediately with the fresh residue mana.
                        from opening_hand_policy import _try_pay, _commit_payment, parse_cost, Perm
                        gen, pips, _ = parse_cost(spec["cost"])
                        plan = _try_pay(state, gen, pips)
                        if plan is not None:
                            _commit_payment(state, plan)
                            state.hand.remove(name)
                            state.nonland_perms.append(Perm(name, state.turn, "Creature" in cards[name]["type"]))
                            state.cast_log.append((state.turn, name, "engine"))
                    break
        if ritual_cast_turn == t:
            stranded_units = d7.sweep_stranded_dark_ritual_residue(state, t)
        m = snapshot_metrics(state, cards, combos)
        m["carpet_on_battlefield"] = any(p.name == d7.CARPET_NAME for p in state.nonland_perms)
        per_turn[t] = m
    per_turn["first_cast_turn"] = {
        name: next((t for (t, n, c) in state.cast_log if n == name), None) for name in TARGETS
    }
    per_turn["ritual_cast_turn"] = ritual_cast_turn
    per_turn["ritual_enabled_target"] = ritual_enabled_target
    per_turn["ritual_stranded_units"] = stranded_units
    return per_turn


def census(names, cards, combos, seed, n, with_ritual_policy):
    rng = random.Random(seed)
    fn = _one_hand_with_ritual_policy if with_ritual_policy else _one_hand_baseline
    return [fn(names, rng, cards, combos) for _ in range(n)]


def aggregate_baseline(results, n):
    def rate(fn):
        return sum(1 for r in results if fn(r)) / n
    out = {"T3_color_failure_rate": rate(lambda r: not r[3]["all_wubg"])}
    for name in TARGETS:
        for t in (1, 2, 3, 4):
            out[f"{name}_cast_by_T{t}"] = rate(
                lambda r, name=name, t=t: r["first_cast_turn"][name] is not None and r["first_cast_turn"][name] <= t
            )
    return out


def aggregate_ritual(results, n):
    out = aggregate_baseline(results, n)
    ritual_used = [r for r in results if r["ritual_cast_turn"] is not None]
    out["ritual_purposeful_use_rate"] = len(ritual_used) / n
    if ritual_used:
        out["ritual_mean_stranded_units_when_used"] = sum(r["ritual_stranded_units"] for r in ritual_used) / len(ritual_used)
        out["ritual_pct_fully_stranded_when_used"] = sum(1 for r in ritual_used if r["ritual_stranded_units"] == 3) / len(ritual_used)
        from collections import Counter
        out["ritual_enabled_target_breakdown"] = dict(Counter(r["ritual_enabled_target"] for r in ritual_used))
    else:
        out["ritual_mean_stranded_units_when_used"] = None
        out["ritual_pct_fully_stranded_when_used"] = None
        out["ritual_enabled_target_breakdown"] = {}
    return out


def carpet_cast_rate(results, n):
    def rate(fn):
        return sum(1 for r in results if fn(r)) / n
    return {f"carpet_on_battlefield_T{t}": rate(lambda r, t=t: r[t]["carpet_on_battlefield"]) for t in (1, 2, 3, 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=12000)
    ap.add_argument("--seed", type=int, default=87001)
    args = ap.parse_args()

    d7.install_new_card_tables()
    try:
        payload, base_rows = load_deckbuild007_cards()
        cards_pool = deckbuild007_cards_pool(base_rows)
        base_names = list(base_rows.keys())
        combos = load_deterministic_combos()

        configs = {
            "RITUAL_CURRENT": {"add": [], "remove": []},
            "RITUAL_REMOVED": {"add": [], "remove": [d7.DARK_RITUAL_NAME]},
            "CARPET_INSTEAD": {"add": [d7.CARPET_NAME], "remove": [d7.DARK_RITUAL_NAME]},
            "BOTH_FLEX_CUT": {"add": [d7.CARPET_NAME], "remove": [FUNDING_CUT_FOR_BOTH]},
        }
        built = {k: build(base_names, cards_pool, add=v["add"], remove=v["remove"]) for k, v in configs.items()}
        # Dark Ritual Residue is a runtime-only bookkeeping object (never a decklist entry) - its
        # row data must be present in every config's cards dict regardless of whether that config
        # actually has Dark Ritual (RITUAL_REMOVED never creates one, but needs no KeyError if it did).
        cards_by_cfg = {
            k: {**{n: cards_pool[n] for n in names}, d7.DARK_RITUAL_RESIDUE_NAME: cards_pool[d7.DARK_RITUAL_RESIDUE_NAME]}
            for k, names in built.items()
        }

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_007_WS1_RITUAL_CARPET", "evidence_type": "goldfish",
            "config_sizes": {k: len(v) for k, v in built.items()},
            "ritual_policy_note": (
                "Purposeful-cast heuristic (see module docstring): cast Ritual on turn T iff it "
                "newly enables one of the 4 named targets that isn't cast yet, using turn-start "
                "capacity. Not a claim of optimal play - a defined, disclosed proxy."
            ),
            "carpet_scenario_note": (
                "Carpet's mana output is NOT simulated (opponent-dependent) - see "
                "carpet_scenario_bands, evidence_type static_probability, confidence low. Its own "
                "cast timing (on_battlefield rate) IS simulated normally below."
            ),
            "results": {}, "carpet_scenario_bands": CARPET_SCENARIO_BANDS,
        }

        for cfg_name, names in built.items():
            t0 = time.time()
            has_ritual = d7.DARK_RITUAL_NAME in names
            results = census(names, cards_by_cfg[cfg_name], combos, args.seed, args.census_n, with_ritual_policy=has_ritual)
            agg = aggregate_ritual(results, args.census_n) if has_ritual else aggregate_baseline(results, args.census_n)
            if d7.CARPET_NAME in names:
                agg.update(carpet_cast_rate(results, args.census_n))
            out["results"][cfg_name] = agg
            print(f"{cfg_name} ({time.time()-t0:.1f}s)")

        r_current = out["results"]["RITUAL_CURRENT"]
        r_removed = out["results"]["RITUAL_REMOVED"]
        out["required_key_numbers"] = {
            "ritual_purposeful_use_rate_in_current_build": r_current["ritual_purposeful_use_rate"],
            "ritual_enabled_target_breakdown": r_current["ritual_enabled_target_breakdown"],
            "ritual_mean_stranded_units_when_used": r_current["ritual_mean_stranded_units_when_used"],
            "smothering_tithe_T2_delta_ritual_vs_removed_pp": (
                r_current["Smothering Tithe_cast_by_T2"] - r_removed["Smothering Tithe_cast_by_T2"]
            ) * 100,
            "birthing_pod_T2_delta_ritual_vs_removed_pp": (
                r_current["Birthing Pod_cast_by_T2"] - r_removed["Birthing Pod_cast_by_T2"]
            ) * 100,
            "talion_T2_delta_ritual_vs_removed_pp": (
                r_current["Talion, the Kindly Lord_cast_by_T2"] - r_removed["Talion, the Kindly Lord_cast_by_T2"]
            ) * 100,
            "seedborn_T3_delta_ritual_vs_removed_pp": (
                r_current["Seedborn Muse_cast_by_T3"] - r_removed["Seedborn Muse_cast_by_T3"]
            ) * 100,
        }
    finally:
        d7.uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild007_ws1_ritual_carpet.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_key_numbers"], indent=2))


if __name__ == "__main__":
    main()
