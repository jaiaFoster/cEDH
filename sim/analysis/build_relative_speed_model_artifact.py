"""SIM-001 MULL-006 section 4 / 28 — writes relative_speed_model.json, the required artifact
recording the pilot-supplied relative-deployment-speed prior (see relative_speed_model.py for the
full back-derivation rationale)."""
import json
from pathlib import Path

from relative_speed_model import (
    EXPECTED_DEPLOYMENT_TURN, EXTRAPOLATED_ENTRIES, SPEED_ORDER, SPEED_RANK, SPEED_PROVENANCE,
    relative_speed,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _worked_examples_table():
    rows = []
    for name, expected in EXPECTED_DEPLOYMENT_TURN.items():
        for actual in range(1, expected + 3):
            rows.append({
                "engine": name,
                "expected_deployment_turn": expected,
                "actual_turn": actual,
                "diff": actual - expected,
                "relative_speed": relative_speed(name, actual),
                "extrapolated": name in EXTRAPOLATED_ENTRIES,
            })
    return rows


def main():
    result = {
        "phase": "SIM_001_MULL_006_RELATIVE_SPEED_MODEL",
        "evidence_type": SPEED_PROVENANCE,
        "speed_order_fastest_first": SPEED_ORDER,
        "speed_rank": SPEED_RANK,
        "expected_deployment_turn": EXPECTED_DEPLOYMENT_TURN,
        "extrapolated_entries": sorted(EXTRAPOLATED_ENTRIES),
        "classification_formula": {
            "description": "diff = actual_turn - expected_deployment_turn(engine)",
            "diff_le_-2": "S (EXTREMELY ACCELERATED)",
            "diff_eq_-1": "A (AHEAD OF CURVE)",
            "diff_eq_0": "B (ON TIME / EXPECTED)",
            "diff_eq_+1": "C (BEHIND CURVE)",
            "diff_ge_+2": "D (SUBSTANTIALLY LATE)",
        },
        "back_derivation_note": (
            "expected_deployment_turn is explicitly NOT printed mana value (assignment section 4: "
            "'Smothering Tithe and Pod should NOT be evaluated purely from printed mana value... "
            "expected deployment is deck-specific'). Every entry except Survival of the Fittest is "
            "algebraically back-derived to exactly reproduce a worked example given verbatim in the "
            "assignment text (T1/T2 Pod -> S/A, T1/T2 Tithe -> S/A, T1/T2 of the six mid engines -> "
            "A/B, T1/T2 Remora+Sentinel -> B/C, a T3 two-drop engine -> C). Survival of the Fittest "
            "is not one of the given worked examples; its expected_deployment_turn=2 is an "
            "EXTRAPOLATED prior matched to the CMC-2 mid-engine class it shares with Sylvan Library "
            "and Faerie Mastermind, disclosed as extrapolated rather than pilot-verbatim."
        ),
        "abhorrent_oculus_excluded": (
            "Abhorrent Oculus deliberately has no expected_deployment_turn entry - per assignment "
            "section 3 it is a separate premier destination, never scored on this engine-speed "
            "scale (same exclusion as engine_strength_prior.json)."
        ),
        "note": (
            "This is a PILOT-SUPPLIED STRATEGIC PRIOR (an initialization point), not a conclusion. "
            "Section 5/6 (strength_speed_sensitivity.json, task #106) tests this prior against real "
            "simulated trajectory outcomes and may recommend boundary adjustments - do not cite this "
            "artifact alone as validating the S/A/B/C/D thresholds."
        ),
        "worked_examples_reproduced": _worked_examples_table(),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "relative_speed_model.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
