"""SIM-DECKBUILD-006 E5/E6 — sanity checks for the T4-T6 extension and the multiplayer
sensitivity scenario arithmetic."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild006_cards as d6  # noqa: E402
from deckbuild006_variants import load_deckbuild006_cards, deckbuild006_cards_pool, build, VARIANTS  # noqa: E402
from opening_hand_model import load_deterministic_combos  # noqa: E402
from build_deckbuild006_e5_late_draw_value import census, aggregate, MAX_TURN  # noqa: E402
from build_deckbuild006_e6_multiplayer_sensitivity import (  # noqa: E402
    scenario_expected_treasures, SCENARIO_BANDS, OPPONENT_COUNT, TURNS_MODELED,
)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d6.install_new_card_tables()
    yield
    d6.uninstall_new_card_tables()


def test_e5_runs_to_t6_and_lotho_triggers_are_monotonic_nondecreasing():
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    base_names = list(rows.keys())
    combos = load_deterministic_combos()
    names = build(base_names, pool, "D_4D_LOTHO")
    cards = {**{n: pool[n] for n in names}, d6.TREASURE_NAME: pool[d6.TREASURE_NAME]}
    results = census(names, cards, combos, seed=3, n=30)
    assert MAX_TURN == 6
    for r in results:
        assert set(r.keys()) == set(range(1, 7))
        counts = [r[t]["cumulative_lotho_triggers"] for t in range(1, 7)]
        assert counts == sorted(counts), "cumulative trigger count must never decrease turn over turn"


def test_e5_no_lotho_configs_never_record_a_trigger():
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    base_names = list(rows.keys())
    combos = load_deterministic_combos()
    for v in ("A_5D_NO_LOTHO", "B_4D_NO_LOTHO"):
        names = build(base_names, pool, v)
        cards = {**{n: pool[n] for n in names}, d6.TREASURE_NAME: pool[d6.TREASURE_NAME]}
        results = census(names, cards, combos, seed=4, n=30)
        for r in results:
            assert r[6]["cumulative_lotho_triggers"] == 0


def test_e5_aggregate_produces_all_six_turns():
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    base_names = list(rows.keys())
    combos = load_deterministic_combos()
    names = build(base_names, pool, "D_4D_LOTHO")
    cards = {**{n: pool[n] for n in names}, d6.TREASURE_NAME: pool[d6.TREASURE_NAME]}
    agg = aggregate(census(names, cards, combos, seed=5, n=20))
    assert set(agg.keys()) == {f"T{i}" for i in range(1, 7)}


def test_e6_scenario_expectation_is_simple_linear_arithmetic():
    assert scenario_expected_treasures(0.3, 3, 4) == pytest.approx(3.6)
    assert scenario_expected_treasures(0.0, 3, 4) == 0.0


def test_e6_bands_are_monotonic_low_to_high():
    ps = [SCENARIO_BANDS[k]["p_opponent_casts_2nd_spell_per_turn"]
          for k in ("LOW_INTERACTION_POD", "TYPICAL_CEDH_POD", "HIGH_VELOCITY_POD")]
    assert ps == sorted(ps)
    for p in ps:
        assert 0.0 <= p <= 1.0


def test_e6_default_scale_matches_module_constants():
    assert OPPONENT_COUNT == 3
    assert TURNS_MODELED == 4
