"""SIM-001 MULL-006 section 5 — strength x speed trajectory matrix.

Proves the matrix reproduces every cell given verbatim in the assignment's "initial conceptual
prior" table, the two disclosed extensions (LATE column extrapolation, 8-band -> 4-band strength
collapse), and the named relationship claims the assignment explicitly wants preserved (T1
Mastermind outranks T2 Remora; T2 Tithe/Pod are exceptional; T1 two-drop engines get substantial
acceleration credit; normal-speed one-drops remain strong without being mislabeled accelerated).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from strength_speed_matrix import (  # noqa: E402
    MATRIX, GRADE_ORDER, GRADE_RANK, STRENGTH_BAND, AMBIGUOUS_CELLS, MATRIX_PROVENANCE,
    matrix_cell, base_trajectory_quality, grade_to_legacy_band,
)


def test_given_table_cells_reproduced_exactly():
    assert MATRIX["S"]["EXTREME"] == "S+"
    assert MATRIX["S"]["AHEAD"] == "S"
    assert MATRIX["S"]["ON-TIME"] == "A"
    assert MATRIX["S"]["BEHIND"] == "B"

    assert MATRIX["A"]["EXTREME"] == "S"
    assert MATRIX["A"]["AHEAD"] == "A+"
    assert MATRIX["A"]["ON-TIME"] == ("A", "B+")
    assert MATRIX["A"]["BEHIND"] == "C+"

    assert MATRIX["B"]["EXTREME"] == "A+"
    assert MATRIX["B"]["AHEAD"] == "A"
    assert MATRIX["B"]["ON-TIME"] == "B"
    assert MATRIX["B"]["BEHIND"] == "C"

    assert MATRIX["C"]["EXTREME"] == "A"
    assert MATRIX["C"]["AHEAD"] == "B+"
    assert MATRIX["C"]["ON-TIME"] == ("B-", "C+")
    assert MATRIX["C"]["BEHIND"] == "D"


def test_late_column_is_one_step_worse_than_behind_per_row():
    assert MATRIX["S"]["LATE"] == "B-"    # one step worse than "B"
    assert MATRIX["A"]["LATE"] == "C"     # one step worse than "C+"
    assert MATRIX["B"]["LATE"] == "D"     # one step worse than "C"
    assert MATRIX["C"]["LATE"] == "F"     # one step worse than "D" (saturates at F, not off-scale)


def test_ambiguous_cells_disclosed_and_resolvable_both_ways():
    assert set(AMBIGUOUS_CELLS) == {("A", "ON-TIME"), ("C", "ON-TIME")}
    assert matrix_cell("A", "B", resolution="primary") == "A"
    assert matrix_cell("A", "B", resolution="alternate") == "B+"
    assert matrix_cell("C+/B-", "B", resolution="primary") == "B-"
    assert matrix_cell("C+/B-", "B", resolution="alternate") == "C+"


def test_strength_band_collapse_8_to_4():
    assert STRENGTH_BAND["S"] == "S"
    assert STRENGTH_BAND["A+"] == STRENGTH_BAND["A"] == STRENGTH_BAND["A-"] == "A"
    assert STRENGTH_BAND["B+"] == STRENGTH_BAND["B"] == STRENGTH_BAND["B-"] == "B"
    assert STRENGTH_BAND["C+/B-"] == "C"


def test_t1_mastermind_outranks_t2_remora():
    t1_mastermind = base_trajectory_quality("Faerie Mastermind", 1)
    t2_remora = base_trajectory_quality("Mystic Remora", 2)
    assert t1_mastermind == "A+"
    assert t2_remora == "C+"
    assert GRADE_RANK[t1_mastermind] < GRADE_RANK[t2_remora]


def test_t2_remora_does_not_get_premium_speed_credit():
    # Remora is strength A- (a strong engine) but deployed BEHIND its own curve at T2 - the matrix
    # must not let its raw strength buy it a premium grade merely because Remora is powerful.
    assert base_trajectory_quality("Mystic Remora", 2) == "C+"
    assert GRADE_RANK[base_trajectory_quality("Mystic Remora", 2)] > GRADE_RANK["A"]


def test_t2_tithe_and_t2_pod_are_exceptional():
    t2_tithe = base_trajectory_quality("Smothering Tithe", 2)
    t2_pod = base_trajectory_quality("Birthing Pod", 2)
    assert t2_tithe == "S"
    assert t2_pod == "S"
    assert GRADE_RANK[t2_tithe] <= GRADE_RANK["S"]
    assert GRADE_RANK[t2_pod] <= GRADE_RANK["S"]


def test_t1_two_drop_engines_get_substantial_acceleration_credit():
    # "Substantial acceleration credit" means each mid engine's T1 (AHEAD) grade must be strictly
    # better than its own T2 (ON-TIME) grade - not that every mid engine reaches an identical
    # absolute grade regardless of its own intrinsic strength band.
    for name in ("Rhystic Study", "Faerie Mastermind", "Archivist of Oghma", "Sylvan Library",
                 "Heartwood Storyteller", "Runic Armasaur"):
        t1_grade = base_trajectory_quality(name, 1)
        t2_grade = base_trajectory_quality(name, 2)
        assert GRADE_RANK[t1_grade] < GRADE_RANK[t2_grade], (name, t1_grade, t2_grade)


def test_normal_speed_one_drops_remain_strong_without_accelerated_mislabel():
    # T1 Remora/Sentinel is their EXPECTED (ON-TIME) turn, not accelerated - the resolved grade
    # must sit at the row's ON-TIME cell, not its (better) EXTREME or AHEAD cells.
    t1_remora = base_trajectory_quality("Mystic Remora", 1)
    assert t1_remora == "A"  # ON-TIME primary resolution for the A row, not "S"/"A+"
    assert GRADE_RANK[t1_remora] > GRADE_RANK["A+"]  # strictly worse than the AHEAD cell


def test_unrecognized_or_oculus_returns_none():
    assert base_trajectory_quality("Abhorrent Oculus", 1) is None
    assert base_trajectory_quality("Some Random Card", 1) is None


def test_grade_to_legacy_band_collapses_to_first_letter():
    assert grade_to_legacy_band("S+") == "S"
    assert grade_to_legacy_band("A+") == "A"
    assert grade_to_legacy_band("B-") == "B"
    assert grade_to_legacy_band("C+") == "C"


def test_grade_order_is_monotonic():
    assert GRADE_ORDER == ["S+", "S", "A+", "A", "B+", "B", "B-", "C+", "C", "D", "F"]
    for i in range(len(GRADE_ORDER) - 1):
        assert GRADE_RANK[GRADE_ORDER[i]] < GRADE_RANK[GRADE_ORDER[i + 1]]


def test_provenance_label_is_pilot_supplied_strategic_prior():
    assert MATRIX_PROVENANCE == "PILOT_SUPPLIED_STRATEGIC_PRIOR"
