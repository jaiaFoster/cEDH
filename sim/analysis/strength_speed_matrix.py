"""SIM-001 MULL-006 section 5 — strength x speed trajectory matrix.

Combines the two independent axes built in sections 3-4 (engine_strength_prior.py,
relative_speed_model.py) into a single BASE TRAJECTORY QUALITY grade, exactly reproducing the
assignment's own "initial conceptual prior" table:

                      EXTREME     AHEAD       ON-TIME      BEHIND
    S engine            S+          S            A            B
    A engine             S         A+          A/B+          C+
    B engine            A+          A            B            C
    C engine             A          B+         B-/C+          D

PILOT_SUPPLIED_STRATEGIC_PRIOR - the assignment is explicit: "Do NOT blindly freeze this matrix.
Test it." strength_speed_sensitivity.json (task #106, companion artifact) tests this table against
real simulated trajectory outcomes; this module only encodes the table as given plus two disclosed
extensions the given table does not cover:

1. STRENGTH BAND COLLAPSE - engine_strength_prior.py uses an 8-band scale (S, A+, A, A-, B+, B, B-,
   C+/B-) but this matrix's rows are only 4 bands (S/A/B/C engine). The collapse used here:
       S              -> S row
       A+, A, A-      -> A row
       B+, B, B-      -> B row
       C+/B-          -> C row   (Runic Armasaur is the only entry; it sits on the C+/B- boundary
                                   and the matrix has no B/C-boundary row, so it is placed in the
                                   weaker of its two adjacent rows - a disclosed simplification)

2. LATE COLUMN EXTRAPOLATION - the given table has no column for relative_speed_model's "D"
   (SUBSTANTIALLY LATE) band; the assignment only says D is "generally too late to justify the
   opener by itself." Extrapolated here as exactly one grade step worse than that row's own
   BEHIND-column cell (monotonic continuation of each row), NOT pilot-verbatim.

3. AMBIGUOUS CELLS - two cells in the given table list two grades ("A/B+" and "B-/C+") rather than
   one. Both are preserved verbatim (primary = first-listed, alternate = second-listed); the
   sensitivity analysis exists specifically to test which resolution better tracks real simulated
   outcomes for these two cells, per the assignment's "T2 Remora should not receive premium-speed
   credit merely because Remora itself is powerful" / "normal-speed one-drop engines should remain
   strong without being mislabeled 'accelerated'" guidance.
"""
from engine_strength_prior import ENGINE_STRENGTH_PRIOR
from relative_speed_model import relative_speed, SPEED_ORDER

MATRIX_PROVENANCE = "PILOT_SUPPLIED_STRATEGIC_PRIOR"

# Finest grade scale the matrix cells are drawn from, strongest first. Legacy grade_trajectory()
# tiers (S/A/B/C/D/F) are a DIFFERENT, coarser namespace - see grade_to_legacy_band() below.
GRADE_ORDER = ["S+", "S", "A+", "A", "B+", "B", "B-", "C+", "C", "D", "F"]
GRADE_RANK = {g: i for i, g in enumerate(GRADE_ORDER)}

STRENGTH_BAND = {
    "S": "S",
    "A+": "A", "A": "A", "A-": "A",
    "B+": "B", "B": "B", "B-": "B",
    "C+/B-": "C",
}

SPEED_COLUMN = {"S": "EXTREME", "A": "AHEAD", "B": "ON-TIME", "C": "BEHIND", "D": "LATE"}

# The four given columns, exactly as printed in the assignment. Ambiguous cells are tuples
# (primary, alternate); every other cell is a single pilot-verbatim grade.
_GIVEN_MATRIX = {
    "S": {"EXTREME": "S+", "AHEAD": "S", "ON-TIME": "A", "BEHIND": "B"},
    "A": {"EXTREME": "S", "AHEAD": "A+", "ON-TIME": ("A", "B+"), "BEHIND": "C+"},
    "B": {"EXTREME": "A+", "AHEAD": "A", "ON-TIME": "B", "BEHIND": "C"},
    "C": {"EXTREME": "A", "AHEAD": "B+", "ON-TIME": ("B-", "C+"), "BEHIND": "D"},
}
AMBIGUOUS_CELLS = [("A", "ON-TIME"), ("C", "ON-TIME")]


def _cell_primary_grade(cell):
    return cell[0] if isinstance(cell, tuple) else cell


def _one_step_worse(grade):
    rank = GRADE_RANK[grade]
    return GRADE_ORDER[min(rank + 1, len(GRADE_ORDER) - 1)]


def _build_full_matrix():
    matrix = {}
    for row, cols in _GIVEN_MATRIX.items():
        matrix[row] = dict(cols)
        matrix[row]["LATE"] = _one_step_worse(_cell_primary_grade(cols["BEHIND"]))
    return matrix

MATRIX = _build_full_matrix()


def matrix_cell(strength_label, speed_label, resolution="primary"):
    """Returns the base trajectory grade for a matrix row/column, given strength_speed_matrix's
    own S/A/B/C row and relative_speed_model's S/A/B/C/D column labels. `resolution` picks
    "primary" or "alternate" for the two disclosed-ambiguous cells; ignored elsewhere."""
    row = STRENGTH_BAND.get(strength_label, strength_label)
    col = SPEED_COLUMN[speed_label]
    cell = MATRIX[row][col]
    if isinstance(cell, tuple):
        return cell[0] if resolution == "primary" else cell[1]
    return cell


def base_trajectory_quality(engine_name, actual_turn, resolution="primary"):
    """Returns the base trajectory grade for `engine_name` deployed on `actual_turn`, combining
    engine_strength_prior's intrinsic strength with relative_speed_model's deployment speed, or
    None if either axis has no entry for `engine_name` (e.g. Abhorrent Oculus, Birthing Pod's own
    prior applies only once functional - callers checking a live board should resolve strength via
    engine_strength_prior.engine_strength() first and pass its label through matrix_cell() instead
    when the FUNCTIONAL gate matters)."""
    strength = ENGINE_STRENGTH_PRIOR.get(engine_name)
    speed = relative_speed(engine_name, actual_turn)
    if strength is None or speed is None:
        return None
    return matrix_cell(strength, speed, resolution=resolution)


def grade_to_legacy_band(grade):
    """Collapses a fine-grained matrix grade to the coarser legacy S/A/B/C/D/F band used by
    trajectory_grading.grade_trajectory(), for comparison against real simulated outcomes."""
    return grade[0]
