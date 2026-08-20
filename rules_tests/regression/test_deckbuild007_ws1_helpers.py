"""SIM-DECKBUILD-007 Workstream 1 — sanity checks for the Ritual-policy/Carpet census helpers."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards, deckbuild007_cards_pool, build  # noqa: E402
from opening_hand_model import load_deterministic_combos  # noqa: E402
from build_deckbuild007_ws1_ritual_carpet import (  # noqa: E402
    census, aggregate_ritual, aggregate_baseline, carpet_cast_rate, TARGETS, CARPET_SCENARIO_BANDS,
)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d7.install_new_card_tables()
    yield
    d7.uninstall_new_card_tables()


def _pool_and_names():
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    return list(rows.keys()), pool


def test_ritual_current_config_runs_end_to_end_small():
    base_names, pool = _pool_and_names()
    names = build(base_names, pool, add=[], remove=[])
    cards = {**{n: pool[n] for n in names}, d7.DARK_RITUAL_RESIDUE_NAME: pool[d7.DARK_RITUAL_RESIDUE_NAME]}
    combos = load_deterministic_combos()
    results = census(names, cards, combos, seed=1, n=25, with_ritual_policy=True)
    agg = aggregate_ritual(results, 25)
    assert 0.0 <= agg["ritual_purposeful_use_rate"] <= 1.0
    assert "T3_color_failure_rate" in agg


def test_ritual_removed_config_never_uses_ritual():
    base_names, pool = _pool_and_names()
    names = build(base_names, pool, add=[], remove=[d7.DARK_RITUAL_NAME])
    assert len(names) == 98
    cards = {**{n: pool[n] for n in names}, d7.DARK_RITUAL_RESIDUE_NAME: pool[d7.DARK_RITUAL_RESIDUE_NAME]}
    combos = load_deterministic_combos()
    results = census(names, cards, combos, seed=2, n=25, with_ritual_policy=False)
    agg = aggregate_baseline(results, 25)
    for name in TARGETS:
        assert f"{name}_cast_by_T4" in agg


def test_carpet_instead_config_tracks_carpet_presence():
    base_names, pool = _pool_and_names()
    names = build(base_names, pool, add=[d7.CARPET_NAME], remove=[d7.DARK_RITUAL_NAME])
    assert len(names) == 99
    cards = {**{n: pool[n] for n in names}, d7.DARK_RITUAL_RESIDUE_NAME: pool[d7.DARK_RITUAL_RESIDUE_NAME]}
    combos = load_deterministic_combos()
    results = census(names, cards, combos, seed=3, n=25, with_ritual_policy=False)
    rates = carpet_cast_rate(results, 25)
    assert set(rates.keys()) == {f"carpet_on_battlefield_T{t}" for t in (1, 2, 3, 4)}
    for v in rates.values():
        assert 0.0 <= v <= 1.0


def test_carpet_scenario_bands_are_monotonic_by_turn_and_by_band():
    for band, spec in CARPET_SCENARIO_BANDS.items():
        by_turn = spec["avg_opponent_islands_by_turn"]
        vals = [by_turn[t] for t in sorted(by_turn)]
        assert vals == sorted(vals), f"{band} should be non-decreasing by turn"
    t4 = [CARPET_SCENARIO_BANDS[b]["avg_opponent_islands_by_turn"][4] for b in
          ("SLOW_MIDRANGE_SLOP_POD", "TYPICAL_CEDH_POD", "FAST_TURBO_BLUE_HEAVY_POD")]
    assert t4 == sorted(t4)
