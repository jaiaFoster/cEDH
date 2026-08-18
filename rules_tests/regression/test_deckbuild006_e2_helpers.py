"""SIM-DECKBUILD-006 E2 — sanity checks for the creature-mana-network census helpers and the
Deathrite graveyard-fuel re-verification (regression_requirements: "Deathrite fetchland/graveyard
mana" must be re-checked against the NEW operative list, not merely assumed unchanged)."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild006_cards as d6  # noqa: E402
from deckbuild006_variants import load_deckbuild006_cards  # noqa: E402
from build_deckbuild006_e2_creature_mana_network import (  # noqa: E402
    NOMINAL_TRUE_ONE_MANA_DORKS, deathrite_graveyard_fuel_reverification, census, aggregate,
)
from deckbuild006_variants import deckbuild006_cards_pool, build, VARIANTS  # noqa: E402
from opening_hand_model import load_deterministic_combos  # noqa: E402


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d6.install_new_card_tables()
    yield
    d6.uninstall_new_card_tables()


def test_nominal_true_one_mana_dorks_are_all_real_deck_cards():
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    for name in NOMINAL_TRUE_ONE_MANA_DORKS:
        assert name in pool, f"{name!r} missing from card pool"


def test_deathrite_reverification_finds_only_mox_diamond():
    _, rows = load_deckbuild006_cards()
    result = deathrite_graveyard_fuel_reverification(list(rows.keys()))
    assert set(result["land_discard_outlets_present_in_new_operative_98"]) == {"Mox Diamond"}


def test_e2_census_and_aggregate_run_end_to_end_small():
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    base_names = list(rows.keys())
    combos = load_deterministic_combos()
    names = build(base_names, pool, "D_4D_LOTHO")
    cards = {**{n: pool[n] for n in names}, d6.TREASURE_NAME: pool[d6.TREASURE_NAME]}
    results = census(names, cards, combos, seed=1, n=25)
    agg = aggregate(results)
    assert set(agg.keys()) == {"T1", "T2", "T3"}
    for t in agg:
        assert 0 <= agg[t]["mean_creature_count"]
        assert 0 <= agg[t]["kinnan_active_rate"] <= 1


def test_functional_dork_count_never_exceeds_nominal_count_per_config():
    """Deathrite is nominal-only (unmodeled ability), so functional <= nominal always."""
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    base_names = list(rows.keys())
    combos = load_deterministic_combos()
    for v in VARIANTS:
        names = build(base_names, pool, v)
        cards = {**{n: pool[n] for n in names}, d6.TREASURE_NAME: pool[d6.TREASURE_NAME]}
        results = census(names, cards, combos, seed=2, n=25)
        for r in results:
            for t in (1, 2, 3):
                assert r[t]["functional_dorks_in_play_count"] <= r[t]["nominal_dorks_in_play_count"]
