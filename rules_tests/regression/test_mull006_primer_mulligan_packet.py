"""SIM-001 MULL-006 section 24 — primer example packet categorization.

Proves _category_of() correctly buckets hands by contextual grade + resilience/draw-dependence,
using constructed trajectory objects rather than requiring a real search per test case.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_primer_mulligan_packet import _category_of  # noqa: E402


def _obj(**overrides):
    base = {
        "destination": "Rhystic Study", "resilience_class": "RECOVERABLE",
        "draw_dependence_class": "SELF_CONTAINED", "cards_remaining": 3, "live_agency": 0,
    }
    base.update(overrides)
    return base


def test_snap_keep_requires_top_grade_robust_and_self_contained():
    obj = _obj(resilience_class="ROBUST", draw_dependence_class="SELF_CONTAINED")
    assert _category_of(obj, "S+") == "SNAP_KEEP"
    assert _category_of(obj, "S") == "SNAP_KEEP"
    assert _category_of(obj, "A+") == "SNAP_KEEP"


def test_snap_keep_denied_if_fragile_even_at_top_grade():
    obj = _obj(resilience_class="FRAGILE")
    assert _category_of(obj, "S+") != "SNAP_KEEP"


def test_normal_keep_band():
    obj = _obj()
    for g in ("A", "B+", "B"):
        assert _category_of(obj, g) == "NORMAL_KEEP"


def test_conditional_keep_is_exactly_c():
    obj = _obj()
    assert _category_of(obj, "C") == "CONDITIONAL_KEEP"
    assert _category_of(obj, "B-") != "CONDITIONAL_KEEP"


def test_mulligan_without_deceptive_resources_is_plain_mulligan():
    obj = _obj(cards_remaining=1, live_agency=0)
    assert _category_of(obj, "D") == "MULLIGAN"
    assert _category_of(obj, "F") == "MULLIGAN"


def test_mulligan_with_many_resources_is_trap_deceptive():
    obj = _obj(cards_remaining=6, live_agency=0)
    assert _category_of(obj, "D") == "MULLIGAN_TRAP_DECEPTIVE"


def test_mulligan_with_high_live_agency_is_trap_deceptive():
    obj = _obj(cards_remaining=1, live_agency=2)
    assert _category_of(obj, "F") == "MULLIGAN_TRAP_DECEPTIVE"
