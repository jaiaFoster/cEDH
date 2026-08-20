"""SIM-DECKBUILD-007 Workstream 2 (remainder) — The Cabbage Merchant scenario model + Seedborn
Muse conversion-accelerator analysis. Lotho and Talion are NOT re-derived here (see final report):
Lotho reuses DECKBUILD-006's own E5 (self-trigger floor, T1-T6) + E6 (opponent-trigger scenario
bands) results directly - preserving prior validated findings, not repeating them. Talion uses
this task's own given default number (2) as an assumed baseline, per explicit instruction, rather
than re-derived from scratch.

The Cabbage Merchant: real Oracle text "Whenever an opponent casts a noncreature spell, create a
Food token. Whenever a creature deals combat damage to you, sacrifice a Food token. Tap two
untapped Foods you control: Add one mana of any color." Structurally similar to Lotho (an
opponent-cast-triggered resource this solo engine cannot observe at all - architecturally
invisible, same category, not merely low confidence) but with two real differences, both
UNFAVORABLE relative to Lotho: (1) the exchange rate is 2 Foods -> 1 mana, half of Lotho's 1
Treasure -> 1 mana; (2) Foods are a CONTESTED resource - any combat damage the pilot takes from
ANY creature (not just from this trigger's source) strips one, a real volatility/attrition factor
Lotho's Treasures do not share (once made, a Treasure is safe until spent). Modeled here with the
SAME scenario-band methodology as DECKBUILD-006's E6 (evidence_type: static_probability,
confidence: low, explicitly NOT a simulation), reusing that file's noncreature-spell-rate
assumption directly (Cabbage triggers on noncreature spells broadly, a strictly larger event
category than Lotho's "2nd spell of the turn" - assumed at 1.5x Lotho's per-turn trigger
probability per opponent, to reflect that any single noncreature spell qualifies, not specifically
a second one) and adding an explicit, disclosed combat-damage attrition assumption.

Seedborn Muse: real text "Each other player untaps during each upkeep, not just their own." (real
wording: untaps during EACH OTHER PLAYER'S untap step, giving the controller a full extra untap
before each of their turns.) Deterministic given a board's total mana output - not scenario-
dependent like Lotho/Cabbage, since it triggers on ALL players' untap steps unconditionally, not
on an opponent's specific action. In a 4-player pod (3 opponents), it grants 3 additional
mana-source-refresh events before the controller's own next turn - a real, exact multiplier on
whatever mana base is already assembled, deterministic given board state.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import deck_provenance_fields  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards  # noqa: E402

OPPONENT_COUNT = 3
TURNS_MODELED = 4

# Reuses DECKBUILD-006 E6's exact TYPICAL/LOW/HIGH per-opponent-per-turn probability structure,
# scaled 1.5x for the strictly broader "any noncreature spell" trigger condition vs Lotho's
# "specifically the 2nd spell" condition - an explicit, disclosed multiplier, not a fitted number.
CABBAGE_SCENARIO_BANDS = {
    "LOW_INTERACTION_POD": {"p_opponent_noncreature_spell_per_turn": 0.10 * 1.5, "rationale":
        "Scaled from DECKBUILD-006 E6's Lotho LOW band (0.10) - any noncreature spell is a "
        "broader trigger than specifically a second spell."},
    "TYPICAL_CEDH_POD": {"p_opponent_noncreature_spell_per_turn": 0.30 * 1.5, "rationale":
        "Scaled from DECKBUILD-006 E6's Lotho TYPICAL band (0.30)."},
    "HIGH_VELOCITY_POD": {"p_opponent_noncreature_spell_per_turn": min(1.0, 0.55 * 1.5), "rationale":
        "Scaled from DECKBUILD-006 E6's Lotho HIGH band (0.55), capped at 1.0 (a probability)."},
}
# Disclosed assumption: the pilot takes at least one combat-relevant hit (stripping a Food) in
# roughly 1 of every 3 turn-cycles once the board has multiple opponents' creatures active - a
# deliberately simple, labeled prior, not fit to any data source.
P_FOOD_LOST_TO_COMBAT_PER_TURN = 1.0 / 3.0


def cabbage_scenarios():
    out = {}
    for name, spec in CABBAGE_SCENARIO_BANDS.items():
        p = spec["p_opponent_noncreature_spell_per_turn"]
        expected_foods_made = OPPONENT_COUNT * TURNS_MODELED * p
        expected_foods_lost = TURNS_MODELED * P_FOOD_LOST_TO_COMBAT_PER_TURN
        net_foods = max(0.0, expected_foods_made - expected_foods_lost)
        out[name] = {
            **spec,
            "expected_foods_made_T_to_T+4": expected_foods_made,
            "expected_foods_lost_to_combat_T_to_T+4": expected_foods_lost,
            "expected_net_foods": net_foods,
            "expected_mana_from_foods": net_foods / 2,  # 2 Foods -> 1 mana, real exchange rate
        }
    return out


def seedborn_deterministic_value(mana_base_totals):
    """mana_base_totals: representative total mana outputs (e.g. [3, 5, 8] sources) - returns the
    EXACT extra mana available before the controller's own next turn, for each."""
    return {
        str(total): {
            "extra_untap_events_before_own_next_turn": OPPONENT_COUNT,
            "extra_mana_available_before_own_next_turn": total * OPPONENT_COUNT,
        }
        for total in mana_base_totals
    }


def main():
    payload, _ = load_deckbuild007_cards()
    cabbage = cabbage_scenarios()
    seedborn = seedborn_deterministic_value([3, 5, 8])

    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_DECKBUILD_007_WS2_MULTIPLAYER_SCENARIOS",
        "evidence_type": "static_probability",
        "confidence": {"level": "low", "reason": "Scenario bands, not calibrated - see module docstring."},
        "lotho_reused_from": "results/solo_baseline/deckbuild006_e5_late_draw_value.json + deckbuild006_e6_multiplayer_sensitivity.json (not re-simulated here)",
        "talion_default_number_used": 2,
        "cabbage_merchant": {
            "scenario_bands": cabbage,
            "vs_lotho_note": (
                "Structurally weaker than Lotho on both axes measured: half the exchange rate "
                "(2 Foods/mana vs 1 Treasure/mana) and a real attrition risk Lotho's Treasures "
                "don't share (combat damage strips Foods)."
            ),
        },
        "seedborn_muse": {
            "deterministic_value_by_mana_base": seedborn,
            "conversion_accelerator_note": (
                "Deterministic (not scenario-based) - triggers on EVERY other player's untap "
                "step unconditionally, not on a specific opponent action. In a 4-player pod, "
                "grants 3 additional full mana-refresh events BEFORE the controller's own next "
                "turn - i.e. real value starting immediately at the first opponent's very next "
                "untap step, not deferred to a future turn. Functions as BOTH a near-term "
                "conversion accelerator (extra protection/response mana available during "
                "opponents' turns, directly relevant to the assignment's 'survive/profit from "
                "the first fight' phase) AND a long-game value multiplier (compounds every cycle "
                "it survives) - not an either/or."
            ),
            "pod_4_to_5_unique_target_note": (
                "Re-verified in Workstream 3 (deckbuild007_ws3_conversion_architecture.json: "
                "pod_rungs.4_to_5) against the new 101-card pool: Seedborn Muse remains the ONLY "
                "MV5 creature this deck runs, so it is still Pod's unique resolver for that rung."
            ),
        },
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild007_ws2_multiplayer_scenarios.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["cabbage_merchant"]["scenario_bands"], indent=2))
    print(json.dumps(out["seedborn_muse"]["deterministic_value_by_mana_base"], indent=2))


if __name__ == "__main__":
    main()
