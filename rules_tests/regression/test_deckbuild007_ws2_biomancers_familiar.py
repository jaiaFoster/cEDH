"""SIM-DECKBUILD-007 Workstream 2 — Biomancer's Familiar cost-reduction arithmetic checks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sim" / "analysis"))

from build_deckbuild007_ws2_biomancers_familiar import _reduce_generic, _affordable  # noqa: E402


def test_reduction_only_touches_generic_never_colored_pips():
    gen, pips = _reduce_generic("{5}{G}{U}")
    assert pips == ["G", "U"]
    assert gen == 3  # 7 total - 2 = 5 total, minus 2 pips = 3 generic


def test_reduction_floors_at_one_total_mana_not_zero():
    gen, pips = _reduce_generic("{2}")
    assert gen + len(pips) == 1  # {2} - {2} would be 0, floored to 1


def test_reduction_never_reduces_a_cost_that_is_already_all_pips():
    """A hypothetical all-colored cost like {U}{U} has no generic to reduce and the floor rule
    should never push it below its own pip count."""
    gen, pips = _reduce_generic("{U}{U}")
    assert gen == 0
    assert pips == ["U", "U"]


def test_thrasios_proxy_cost_unlocked_by_reduction_at_two_mana():
    gen0, pips0 = 4, []
    gen1, pips1 = _reduce_generic("{4}")
    assert not _affordable(gen0, pips0, 2, {"G", "U"})
    assert _affordable(gen1, pips1, 2, {"G", "U"})
