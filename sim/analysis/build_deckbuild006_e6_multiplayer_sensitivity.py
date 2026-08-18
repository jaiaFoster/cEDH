"""SIM-DECKBUILD-006 E6 (secondary priority) — multiplayer sensitivity for Lotho's real value.

Lotho, Corrupt Shirriff's REAL Oracle text triggers on ANY player's second spell each turn, not
just the pilot's own (real text: "Whenever a player casts their second spell each turn..."). This
solo, opponent-free T1-3/T6 engine (E1/E2/E5) can only ever see the pilot's OWN second-spell
trigger - opponent second-spell triggers are architecturally invisible here, exactly like Talion's
and Seedborn Muse's opponent-dependent triggers (DECKBUILD-004's own established disclosure
category), NOT merely a low-confidence estimate of something the engine could in principle capture.

Per this task's own explicit methodology_principles: "multiplayer-only effects must use explicit
scenarios/sensitivity bands (never collapse into one claimed real-game expected value unless
empirically calibrated)" and "never create fake precision from assumed opponent behavior." This
module is therefore NOT a Monte Carlo simulation - it is a small, explicitly-labeled arithmetic
scenario model over ASSUMED opponent second-spell rates (no tournament or replay data source
backs these numbers - there is no calibration source available in this project for per-turn
opponent spell velocity by pod archetype). Every number below is evidence_type "static_probability"
under an explicitly disclosed assumption, confidence = low, and must never be read as a measured or
calibrated real-game rate.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import deck_provenance_fields  # noqa: E402
from deckbuild006_variants import load_deckbuild006_cards  # noqa: E402

# ASSUMED, NOT MEASURED - labeled sensitivity bands for "P(a given opponent casts a real 2nd
# spell in a given one of their own turns), once the game has left the opening turns." No
# tournament-replay or topdeck.gg per-turn-spell-count data source exists in this project to
# calibrate these; picked as a spread wide enough to bracket plausible cEDH pod behavior
# (low-interaction stax/durdle pods through fast, spell-dense combo/control pods).
SCENARIO_BANDS = {
    "LOW_INTERACTION_POD": {
        "p_opponent_casts_2nd_spell_per_turn": 0.10,
        "rationale": "Slow, land-light, or single-action-per-turn opponents (e.g. a grindy stax "
                     "or ramp pod) - a real second spell in one turn is uncommon.",
    },
    "TYPICAL_CEDH_POD": {
        "p_opponent_casts_2nd_spell_per_turn": 0.30,
        "rationale": "A representative competitive pod mixing rocks/dorks with spells - a second "
                     "spell (e.g. a rock plus a tutor, or two cheap interaction pieces) is a "
                     "regular but not universal occurrence.",
    },
    "HIGH_VELOCITY_POD": {
        "p_opponent_casts_2nd_spell_per_turn": 0.55,
        "rationale": "Fast combo-dense or storm-adjacent pods where multi-spell turns are the "
                     "norm rather than the exception.",
    },
}

OPPONENT_COUNT = 3  # 4-player pod, this task's stated commander context (Tymna/Thrasios cEDH)
TURNS_MODELED = 4   # turns 3-6 inclusive, matching E5's post-T3 extension horizon


def scenario_expected_treasures(p_per_opponent_per_turn, opponents, turns):
    """Simple expectation, not a simulation: E[triggers] = opponents * turns * p. Each trigger is
    1 Treasure + 1 life lost (real Oracle text, verified in deckbuild006_cards.py). Independence
    across opponents/turns is an explicit simplifying assumption (real pods have correlated
    behavior - e.g. a topdeck-starved opponent stays quiet across many turns) - the arithmetic
    mean is still the correct EXPECTATION under any distribution with this per-event marginal
    probability, so the number itself is not invalidated by correlation, only its variance is
    understated; not treated as a variance-calibrated result."""
    return opponents * turns * p_per_opponent_per_turn


def main():
    payload, _ = load_deckbuild006_cards()
    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_DECKBUILD_006_E6_MULTIPLAYER_SENSITIVITY",
        "evidence_type": "static_probability",
        "confidence": {
            "level": "low",
            "reason": "No tournament-replay or per-turn-spell-count calibration source exists in "
                      "this project for opponent behavior by pod archetype; SCENARIO_BANDS' "
                      "probabilities are explicitly labeled ASSUMPTIONS chosen to bracket "
                      "plausible cEDH pod behavior, not measured or fit to any dataset.",
        },
        "architectural_invisibility_note": (
            "This solo engine structurally cannot observe an opponent casting a spell at any "
            "turn count - not a low-confidence estimate of something it could in principle see, "
            "the same category as Talion's and Seedborn Muse's opponent-dependent triggers "
            "(DECKBUILD-004's established disclosure). E5's cumulative_lotho_triggers numbers are "
            "therefore a real FLOOR on Lotho's total value (self-triggers only) - everything in "
            "this module is additive upside on top of that floor, in an explicitly labeled "
            "scenario, not a replacement for it."
        ),
        "opponent_count_assumed": OPPONENT_COUNT,
        "turns_modeled": TURNS_MODELED,
        "scenario_bands": {},
    }

    for name, spec in SCENARIO_BANDS.items():
        p = spec["p_opponent_casts_2nd_spell_per_turn"]
        expected = scenario_expected_treasures(p, OPPONENT_COUNT, TURNS_MODELED)
        out["scenario_bands"][name] = {
            **spec,
            "expected_additional_treasures_from_opponents_over_turns_modeled": expected,
            "expected_additional_life_lost_from_opponents_over_turns_modeled": expected,
        }

    typical = out["scenario_bands"]["TYPICAL_CEDH_POD"]["expected_additional_treasures_from_opponents_over_turns_modeled"]
    low = out["scenario_bands"]["LOW_INTERACTION_POD"]["expected_additional_treasures_from_opponents_over_turns_modeled"]
    high = out["scenario_bands"]["HIGH_VELOCITY_POD"]["expected_additional_treasures_from_opponents_over_turns_modeled"]
    out["required_key_number"] = {
        "typical_pod_expected_additional_treasures_T3_to_T6": typical,
        "band_range_low_to_high": [low, high],
        "interpretation": (
            f"Under the TYPICAL_CEDH_POD assumption, Lotho generates an expected {typical:.1f} "
            f"extra Treasures (and {typical:.1f} life lost) from opponents alone across the "
            f"{TURNS_MODELED} turns modeled (T3-T6), ranging {low:.1f}-{high:.1f} across the "
            "LOW-to-HIGH bands, ON TOP OF E5's measured self-trigger floor - a real, structurally "
            "significant value driver this solo engine cannot itself simulate. This is presented "
            "as a labeled, uncalibrated sensitivity band, not a claimed real-game expected value - "
            "see report_policy's explicit instruction against overstating scenario-derived numbers."
        ),
    }

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild006_e6_multiplayer_sensitivity.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_key_number"], indent=2))


if __name__ == "__main__":
    main()
