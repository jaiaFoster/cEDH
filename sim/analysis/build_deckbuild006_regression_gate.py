"""SIM-DECKBUILD-006 — validation gate. Mirrors build_mana_audit002_regression_gate.py's pattern."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CATEGORIES = {
    "frozen_deck_provenance": {
        "tests": ["rules_tests/regression/test_deckbuild006_frozen_deck_and_variants.py"],
        "property": "The operative 98's deck_hash matches its own recomputed hash, a tampered "
                     "copy is rejected, and the A/B/C/D factorial configs each build to exactly "
                     "98 cards with the correct dork/Lotho composition and no unintended card "
                     "drift between configs (C vs D differs by exactly +Pilgrim/-Mindbreak Trap).",
    },
    "lotho_treasure_and_new_card_mechanics": {
        "tests": ["rules_tests/regression/test_deckbuild006_new_cards.py"],
        "property": "Lotho's second-spell-of-the-turn trigger fires and does not fire in exactly "
                     "the cases dictated by its real Oracle text and this project's cast_log "
                     "tagging conventions (7 dedicated cases); Treasure Token reuses Lotus "
                     "Petal's one-shot mana-source shape exactly; Grand Abolisher/Mockingbird are "
                     "classified correctly (engine vs unclassified 'other').",
    },
    "badgermole_not_modeled_disclosure": {
        "tests": ["rules_tests/regression/test_deckbuild006_badgermole_not_modeled.py"],
        "property": "Badgermole Cub's creature-mana amplifier is mechanically confirmed NOT to "
                     "grant bonus mana in this engine (a pre-existing, deliberately-deferred gap, "
                     "explicitly tested rather than silently assumed) - a real, directionally-"
                     "conservative bias against the 5-dork configs' measured advantage.",
    },
    "e2_network_and_deathrite_reverification": {
        "tests": ["rules_tests/regression/test_deckbuild006_e2_helpers.py"],
        "property": "The creature-mana-network census/aggregate helpers run correctly end to end, "
                     "functional dork count never exceeds nominal dork count in any config "
                     "(Deathrite is nominal-only, its ability unmodeled), and the Deathrite "
                     "graveyard-fuel re-verification correctly finds only Mox Diamond as a "
                     "land-discard outlet in the new operative 98.",
    },
    "e5_e6_late_draw_and_multiplayer_sensitivity": {
        "tests": ["rules_tests/regression/test_deckbuild006_e5_e6_helpers.py"],
        "property": "The T1-T6 extension runs correctly (cumulative Lotho triggers are monotonic "
                     "non-decreasing, no-Lotho configs never record a trigger), and E6's scenario "
                     "arithmetic is simple, correctly-ordered linear expectation over disclosed "
                     "assumptions, never a simulation dressed up as one.",
    },
}


def _run_full_suite():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "rules_tests/", "-q"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return result.returncode == 0, result.stdout[-3000:]


def main():
    passed, tail = _run_full_suite()
    result = {
        "phase": "SIM_DECKBUILD_006_REGRESSION_GATE",
        "full_suite_passed": passed,
        "full_suite_output_tail": tail,
        "gate_status": "OPEN" if passed else "BLOCKED",
        "required_categories": REQUIRED_CATEGORIES,
        "scope_disclosure": (
            "This gate covers everything actually built this task: frozen-deck minting, Lotho/"
            "Grand Abolisher/Mockingbird/Treasure mechanics, A/B/C/D factorial configs, E1 (early "
            "cost), E2 (creature-mana network), E5 (late-draw value, T1-T6 extension), E6 "
            "(multiplayer sensitivity scenario model). E3 (Cradle draw probability) and E4 (Pod "
            "rung census) were skipped with disclosure after the phase-1 checkpoint showed the "
            "effect size was already too small to change the decision; E7 (post-first-fight state "
            "modeling) was skipped because SIM-DECKBUILD-005's framework does not exist to reuse "
            "and phases 1/E5/E6 already resolved the decision - see "
            "results/solo_baseline/deckbuild006_report.md's 'Scope disclosure' section for the "
            "full reasoning. This is not a gap in THIS gate; those phases have no code to gate."
        ),
        "artifacts_committed": [
            "data/decklists/tymna-thrasios-treefarm-deckbuild006-v1.json",
            "sim/analysis/build_deckbuild006_frozen_deck.py",
            "sim/analysis/deckbuild006_cards.py", "sim/analysis/deckbuild006_variants.py",
            "sim/analysis/build_deckbuild006_e1_early_cost.py",
            "sim/analysis/build_deckbuild006_e2_creature_mana_network.py",
            "sim/analysis/build_deckbuild006_e5_late_draw_value.py",
            "sim/analysis/build_deckbuild006_e6_multiplayer_sensitivity.py",
            "results/solo_baseline/deckbuild006_e1_early_cost.json",
            "results/solo_baseline/deckbuild006_e2_creature_mana_network.json",
            "results/solo_baseline/deckbuild006_e5_late_draw_value.json",
            "results/solo_baseline/deckbuild006_e6_multiplayer_sensitivity.json",
            "results/solo_baseline/deckbuild006_report.md",
        ],
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild006_regression_gate.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"full_suite_passed={passed}  gate_status={result['gate_status']}")


if __name__ == "__main__":
    main()
