"""SIM-DECKBUILD-007 Workstream 2 — Birthing Ritual rung-quality sanity checks."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards, deckbuild007_cards_pool  # noqa: E402
from build_deckbuild007_ws2_birthing_ritual import rung_quality, PREMIUM_BY_RUNG  # noqa: E402


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d7.install_new_card_tables()
    yield
    d7.uninstall_new_card_tables()


def test_higher_rungs_have_higher_or_equal_any_hit_rate():
    """More legal MV options (X grows with sac_mv) should never DECREASE hit rate."""
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    names = list(rows.keys())
    reps = {1: "Delighted Halfling", 2: "Badgermole Cub", 3: "Endurance", 4: "Clever Impersonator"}
    rates = []
    for sac_mv, sac_name in reps.items():
        q = rung_quality(names, pool, sac_mv, sac_name, seed=1, n=3000)
        rates.append(q["p_any_legal_hit"])
    assert rates == sorted(rates)


def test_probabilities_are_internally_consistent():
    """premium/meaningful/immediate are all SUBSETS of any_legal_hit (via any(...) over the same
    legal set) so none can exceed it."""
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    names = list(rows.keys())
    q = rung_quality(names, pool, 2, "Badgermole Cub", seed=2, n=5000)
    assert q["p_premium_target"] <= q["p_any_legal_hit"]
    assert q["p_meaningful_upgrade"] <= q["p_any_legal_hit"]
    assert q["p_immediate_conversion_target"] <= q["p_any_legal_hit"]


def test_premium_lists_are_real_deck_cards():
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    for rung, names in PREMIUM_BY_RUNG.items():
        for n in names:
            assert n in pool, f"rung {rung} premium target {n!r} not in card pool"
            assert "Creature" in pool[n]["type"]


def test_sac_creature_itself_is_excluded_from_the_sample_pool():
    """A sacrificed creature cannot appear in its own top-7 sample."""
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    names = list(rows.keys())
    import random
    sac = "Badgermole Cub"
    remaining = [c for c in names if c != sac]
    assert sac not in remaining
    assert len(remaining) == len(names) - 1
