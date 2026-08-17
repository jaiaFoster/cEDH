"""SIM-DECKBUILD-004 — validation gate. Mirrors build_mana_audit002_regression_gate.py's pattern."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CATEGORIES = {
    "new_card_mechanics": {
        "tests": ["rules_tests/regression/test_deckbuild004_new_cards.py"],
        "property": "Neoform's mv_offset=1 generalization, and Formidable Speaker's ETB "
                     "discard-tutor-to-hand (fires only the turn it's cast) + repeatable untap "
                     "ability, are correctly implemented and isolated (global-table pollution "
                     "found and fixed via explicit install/uninstall, not auto-install-on-import).",
    },
    "phase0_reactive_screen_structure": {
        "tests": ["rules_tests/regression/test_deckbuild004_phase0_screen.py"],
        "property": "The 4 real cut candidates and the informational-only An Offer You Can't "
                     "Refuse comparison are structurally correct (not a fabricated 5th cut).",
    },
    "e1_early_cost_helpers": {
        "tests": ["rules_tests/regression/test_deckbuild004_e1_early_cost.py"],
        "property": "T2_autonomous_engine's disclosed operational definition, and the paired-"
                     "seed flip/keep-rate-by-depth machinery, produce bounded, sane output.",
    },
    "e2_tutor_topology": {
        "tests": ["rules_tests/regression/test_deckbuild004_e2_tutor_topology.py"],
        "property": "Mechanism-presence gating is correct per variant, and - the load-bearing "
                     "check - the search reproduces a REAL already-verified project combo "
                     "(INT-0012) while correctly NOT crediting the same target reached via a "
                     "mechanism that doesn't satisfy that combo's real requirements (Neoform vs "
                     "Pod), a concrete anti-overclaim confirmation.",
    },
    "e4_pod_rungs": {
        "tests": ["rules_tests/regression/test_deckbuild004_e4_pod_rungs.py"],
        "property": "The 4->5 Pod rung's dead-end status in baseline, and Seedborn Muse "
                     "resolving it, are exact facts (zero MV5 creatures in the 98-card list "
                     "otherwise), not sampled estimates.",
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
        "phase": "SIM_DECKBUILD_004_REGRESSION_GATE",
        "full_suite_passed": passed,
        "full_suite_output_tail": tail,
        "gate_status": "OPEN" if passed else "BLOCKED",
        "required_categories": REQUIRED_CATEGORIES,
        "scope_disclosure": (
            "This gate covers everything actually built (phase_0, E1, E2, scoped E4, B4-B7 "
            "ablation census). E3 (full stratified post-fight conversion) and E5/E6 (late-draw "
            "quality, engine-behavior tagging) were not built this pass - see "
            "results/solo_baseline/deckbuild004_report.md section 9 for the full disclosure and "
            "reasoning. This is not a gap in THIS gate; those phases have no code to gate."
        ),
        "artifacts_committed": [
            "sim/analysis/deckbuild004_cards.py", "sim/analysis/deckbuild004_variants.py",
            "sim/analysis/build_deckbuild004_phase0_reactive_screen.py",
            "sim/analysis/build_deckbuild004_e1_early_cost.py",
            "sim/analysis/build_deckbuild004_e2_tutor_topology.py",
            "sim/analysis/build_deckbuild004_e4_pod_rungs.py",
            "sim/analysis/build_deckbuild004_ablation_census.py",
            "results/solo_baseline/deckbuild004_phase0_reactive_screen.json",
            "results/solo_baseline/deckbuild004_e1_early_cost.json",
            "results/solo_baseline/deckbuild004_e2_tutor_topology.json",
            "results/solo_baseline/deckbuild004_e4_pod_rungs.json",
            "results/solo_baseline/deckbuild004_ablation_census.json",
            "results/solo_baseline/deckbuild004_report.md",
        ],
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild004_regression_gate.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"full_suite_passed={passed}  gate_status={result['gate_status']}")


if __name__ == "__main__":
    main()
