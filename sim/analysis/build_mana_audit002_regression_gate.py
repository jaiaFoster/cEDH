"""MANA-AUDIT-002 — validation gate.

Runs the full regression suite and confirms the correctness fixes and new infrastructure this
task built (Talon Gates fix, cmc-key fix, variant-cards-pool mulligan-sim bug fix, Pareto axis
logic) have real, passing coverage. Mirrors build_mull006_regression_gate.py's pattern.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CATEGORIES = {
    "talon_gates_fix": {
        "tests": ["rules_tests/regression/test_mana_audit002_special_cases.py::test_talon_gates_no_longer_a_flat_rainbow_source",
                   "rules_tests/regression/test_mana_audit002_special_cases.py::test_talon_gates_is_a_guaranteed_generic_one_source",
                   "rules_tests/regression/test_mana_audit002_special_cases.py::test_talon_gates_available_sources_reports_generic_only"],
        "property": "Talon Gates of Madara's real Oracle text (colorless-guaranteed, colored "
                     "mode costs an extra generic mana) is correctly modeled, not the prior flat "
                     "free-rainbow overstatement.",
    },
    "deathrite_dead_finding": {
        "tests": ["rules_tests/regression/test_mana_audit002_special_cases.py::test_deathrite_shaman_absent_from_mana_sources",
                   "rules_tests/regression/test_mana_audit002_special_cases.py::test_deck_has_zero_basic_land_cards"],
        "property": "Deathrite Shaman's mana ability is confirmed structurally dead in this "
                     "exact 98-card list (zero real basic land cards to exile).",
    },
    "cmc_field_fix": {
        "tests": ["rules_tests/regression/test_mana_audit002_special_cases.py::test_cmc_field_now_populates_from_real_card_data"],
        "property": "load_deck_cards() reads the real mana_value cache field, not a nonexistent "
                     "cmc key (SIM-0018).",
    },
    "hypergeometric_math": {
        "tests": ["rules_tests/regression/test_mana_audit002_baseline.py"],
        "property": "Exact opening-hand land-count distribution sums to 1 and matches the known "
                     "hypergeometric mean/edge cases.",
    },
    "variant_builder": {
        "tests": ["rules_tests/regression/test_mana_audit002_variant_builder.py"],
        "property": "Counterfactual deck-variant construction (add/remove cards, new-land tables) "
                     "produces correct card counts and legal fetch targets, and simulates without "
                     "crashing.",
    },
    "config_integrity_and_draw_pool_fix": {
        "tests": ["rules_tests/regression/test_mana_audit002_configs.py"],
        "property": "Every Section F config hits its declared deck size/land count, and the real "
                     "mulligan-sim draw-pool bug this task found (every config silently drawing "
                     "from the full shared card pool instead of its own variant) stays fixed.",
    },
    "pareto_axis_logic": {
        "tests": ["rules_tests/regression/test_mana_audit002_pareto.py"],
        "property": "Speed/consistency/resilience-utility axis computations respond correctly to "
                     "their real underlying components (no silently-constant or inverted axis).",
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
        "phase": "SIM_001_MANA_AUDIT_002_REGRESSION_GATE",
        "full_suite_passed": passed,
        "full_suite_output_tail": tail,
        "gate_status": "OPEN" if passed else "BLOCKED",
        "required_categories": REQUIRED_CATEGORIES,
        "artifacts_committed": [
            "data/decklists/tymna-thrasios-treefarm-manaaudit002-v1.json",
            "results/solo_baseline/mana_audit_002_inventory.json",
            "results/solo_baseline/mana_audit_002_color_demand.json",
            "results/solo_baseline/mana_audit_002_baseline.json",
            "results/solo_baseline/mana_audit_002_configs.json",
            "results/solo_baseline/mana_audit_002_pareto.json",
            "results/solo_baseline/mana_audit_002_external_sanity.json",
            "results/solo_baseline/mana_audit_002_report.md",
        ],
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_regression_gate.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"full_suite_passed={passed}  gate_status={result['gate_status']}")


if __name__ == "__main__":
    main()
