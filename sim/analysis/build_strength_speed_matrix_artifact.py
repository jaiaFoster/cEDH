"""SIM-001 MULL-006 section 5 / 28 — writes strength_speed_matrix.json, the required artifact
recording the pilot-supplied strength x speed trajectory matrix (see strength_speed_matrix.py for
the full rationale, disclosed extensions, and ambiguous-cell handling)."""
import json
from pathlib import Path

from strength_speed_matrix import (
    MATRIX, GRADE_ORDER, GRADE_RANK, STRENGTH_BAND, SPEED_COLUMN, AMBIGUOUS_CELLS,
    MATRIX_PROVENANCE, base_trajectory_quality,
)
from engine_strength_prior import ENGINE_STRENGTH_PRIOR

REPO_ROOT = Path(__file__).resolve().parents[2]


def _worked_examples():
    rows = []
    for name in ENGINE_STRENGTH_PRIOR:
        for turn in (1, 2, 3):
            grade = base_trajectory_quality(name, turn)
            if grade is not None:
                rows.append({"engine": name, "actual_turn": turn, "base_trajectory_grade": grade,
                             "grade_rank": GRADE_RANK[grade]})
    return rows


def main():
    result = {
        "phase": "SIM_001_MULL_006_STRENGTH_SPEED_MATRIX",
        "evidence_type": MATRIX_PROVENANCE,
        "grade_order_best_first": GRADE_ORDER,
        "grade_rank": GRADE_RANK,
        "strength_band_collapse_8_to_4": STRENGTH_BAND,
        "speed_column_labels": SPEED_COLUMN,
        "matrix": MATRIX,
        "ambiguous_cells": [
            {"row": row, "column": col, "primary": MATRIX[row][col][0], "alternate": MATRIX[row][col][1]}
            for row, col in AMBIGUOUS_CELLS
        ],
        "late_column_note": (
            "The assignment's given table has no LATE (relative_speed D / SUBSTANTIALLY LATE) "
            "column. Extrapolated here as exactly one grade step worse than that row's own BEHIND "
            "cell (monotonic continuation), disclosed as NOT pilot-verbatim."
        ),
        "strength_band_collapse_note": (
            "engine_strength_prior.py uses an 8-band strength scale (S, A+, A, A-, B+, B, B-, "
            "C+/B-) but this matrix's rows are only 4 bands (S/A/B/C engine) as given by the "
            "assignment. A+/A/A- collapse to the A row, B+/B/B- collapse to the B row, and the "
            "single C+/B- boundary entry (Runic Armasaur) is placed in the C row - a disclosed "
            "simplification, not a pilot-verbatim mapping."
        ),
        "ambiguous_cell_note": (
            "Two cells in the given table list two grades rather than one ('A/B+' for the A-"
            "strength/ON-TIME cell, 'B-/C+' for the C-strength/ON-TIME cell). Both are preserved "
            "here; this artifact's 'primary' resolution uses the first-listed grade. "
            "strength_speed_sensitivity.json (companion artifact) tests both resolutions against "
            "real simulated trajectory outcomes to see which one better tracks empirical results, "
            "per the assignment's explicit instruction not to blindly freeze this matrix."
        ),
        "named_relationships_verified": {
            "t1_mastermind_outranks_t2_remora": {
                "t1_mastermind_grade": base_trajectory_quality("Faerie Mastermind", 1),
                "t2_remora_grade": base_trajectory_quality("Mystic Remora", 2),
            },
            "t2_remora_does_not_get_premium_speed_credit": base_trajectory_quality("Mystic Remora", 2),
            "t2_tithe_is_exceptional": base_trajectory_quality("Smothering Tithe", 2),
            "t2_functional_pod_is_exceptional": base_trajectory_quality("Birthing Pod", 2),
            "t1_remora_normal_speed_one_drop_stays_strong": base_trajectory_quality("Mystic Remora", 1),
            "t1_sentinel_normal_speed_one_drop_stays_strong": base_trajectory_quality("Esper Sentinel", 1),
        },
        "note": (
            "This is a PILOT-SUPPLIED STRATEGIC PRIOR (the assignment's own 'initial conceptual "
            "prior'), not a conclusion - the assignment explicitly instructs 'Do NOT blindly "
            "freeze this matrix. Test it.' See strength_speed_sensitivity.json for the required "
            "test against real simulated trajectory outcomes."
        ),
        "worked_examples": _worked_examples(),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "strength_speed_matrix.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
