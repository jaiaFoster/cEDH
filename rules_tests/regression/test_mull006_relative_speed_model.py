"""SIM-001 MULL-006 section 4 — relative deployment speed, independent of engine strength.

Proves relative_speed() reproduces every worked example given verbatim in the assignment text,
plus the boundary/edge cases (D for substantially late, None for unrecognized cards/Oculus).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from relative_speed_model import (  # noqa: E402
    relative_speed, EXPECTED_DEPLOYMENT_TURN, EXTRAPOLATED_ENTRIES, SPEED_ORDER, SPEED_RANK,
    SPEED_PROVENANCE,
)

MID_ENGINES = [
    "Rhystic Study", "Faerie Mastermind", "Archivist of Oghma", "Sylvan Library",
    "Heartwood Storyteller", "Runic Armasaur",
]


def test_t1_functional_pod_is_s():
    assert relative_speed("Birthing Pod", 1) == "S"


def test_t2_functional_pod_is_a():
    assert relative_speed("Birthing Pod", 2) == "A"


def test_t1_smothering_tithe_is_s():
    assert relative_speed("Smothering Tithe", 1) == "S"


def test_t2_smothering_tithe_is_a():
    assert relative_speed("Smothering Tithe", 2) == "A"


def test_t1_mid_engines_are_a():
    for name in MID_ENGINES:
        assert relative_speed(name, 1) == "A", name


def test_t2_mid_engines_are_b():
    for name in MID_ENGINES:
        assert relative_speed(name, 2) == "B", name


def test_t1_remora_and_sentinel_are_b():
    assert relative_speed("Mystic Remora", 1) == "B"
    assert relative_speed("Esper Sentinel", 1) == "B"


def test_t2_remora_and_sentinel_are_c():
    assert relative_speed("Mystic Remora", 2) == "C"
    assert relative_speed("Esper Sentinel", 2) == "C"


def test_t3_two_drop_engine_is_c():
    # "T3 two-drop engine -> C (expected=2, actual=3, diff=+1)" - any of the mid engines qualifies.
    assert relative_speed("Rhystic Study", 3) == "C"


def test_substantially_late_is_d():
    assert relative_speed("Mystic Remora", 4) == "D"  # diff = +3
    assert relative_speed("Birthing Pod", 5) == "D"   # diff = +2


def test_extremely_accelerated_beyond_t1_is_still_s():
    # No engine can be deployed on turn 0 in this format, but the boundary itself (diff <= -2)
    # should still saturate at S rather than erroring for any theoretical earlier turn.
    assert relative_speed("Smothering Tithe", 1) == "S"  # diff = -2, already covered above
    assert relative_speed("Rhystic Study", 0) == "S"  # diff = -2


def test_unrecognized_card_returns_none():
    assert relative_speed("Some Random Card", 1) is None


def test_abhorrent_oculus_has_no_expected_deployment_turn():
    assert "Abhorrent Oculus" not in EXPECTED_DEPLOYMENT_TURN
    assert relative_speed("Abhorrent Oculus", 1) is None


def test_survival_of_the_fittest_is_flagged_extrapolated():
    assert "Survival of the Fittest" in EXTRAPOLATED_ENTRIES
    assert EXPECTED_DEPLOYMENT_TURN["Survival of the Fittest"] == 2
    # every other entry is back-derived from a worked example, not extrapolated
    assert EXTRAPOLATED_ENTRIES == {"Survival of the Fittest"}


def test_speed_rank_is_monotonically_ordered_s_fastest():
    assert SPEED_RANK["S"] < SPEED_RANK["A"] < SPEED_RANK["B"] < SPEED_RANK["C"] < SPEED_RANK["D"]
    assert SPEED_ORDER == ["S", "A", "B", "C", "D"]


def test_provenance_label_is_pilot_supplied_strategic_prior():
    assert SPEED_PROVENANCE == "PILOT_SUPPLIED_STRATEGIC_PRIOR"
