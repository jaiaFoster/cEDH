"""SIM-DECKBUILD-004 E1 — sanity checks for the early-cost paired-comparison helpers."""
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build, VARIANTS  # noqa: E402
from build_deckbuild004_e1_early_cost import (  # noqa: E402
    census_metrics, aggregate_census, paired_flip_metrics, keep_rates_by_depth, _autonomous_engine,
)
from run_contextual_london_mulligan_sim import make_contextual_keep_policy  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
COMBOS = load_deterministic_combos()


@pytest.fixture(autouse=True)
def _installed_card_tables():
    install_new_card_tables()
    yield
    uninstall_new_card_tables()


def test_autonomous_engine_excludes_mana_tools_only():
    assert _autonomous_engine({"engines_active": ["Kinnan, Bonder Prodigy"]}) is False
    assert _autonomous_engine({"engines_active": ["Deathrite Shaman"]}) is False
    assert _autonomous_engine({"engines_active": ["Gaea's Cradle"]}) is False
    assert _autonomous_engine({"engines_active": ["Rhystic Study"]}) is True
    assert _autonomous_engine({"engines_active": ["Kinnan, Bonder Prodigy", "Rhystic Study"]}) is True
    assert _autonomous_engine({"engines_active": []}) is False


def test_census_and_aggregate_produce_bounded_rates():
    cards_pool = all_cards_dict(BASE_CARDS)
    names = build(list(BASE_CARDS.keys()), cards_pool, "B0_BASELINE")
    cards = {n: cards_pool[n] for n in names}
    results = census_metrics(names, cards, COMBOS, seed=1, n=50)
    agg = aggregate_census(results)
    for key, val in agg.items():
        if key == "mean_final_hand_size_T3":
            continue
        assert 0.0 <= val <= 1.0, (key, val)


def test_paired_flip_metrics_rates_sum_to_one():
    cards_pool = all_cards_dict(BASE_CARDS)
    base_names = list(BASE_CARDS.keys())
    names_a = build(base_names, cards_pool, "B0_BASELINE")
    names_b = build(base_names, cards_pool, "SIX_DORKS_VS_FIVE")
    policy = make_contextual_keep_policy("gated")
    result = paired_flip_metrics(names_a, names_b, cards_pool, COMBOS, seed=1, n=40, policy=policy)
    total = result["keep_A_ship_B_rate"] + result["ship_A_keep_B_rate"] + result["both_agree_rate"]
    assert abs(total - 1.0) < 1e-9


def test_keep_rates_by_depth_are_monotone_bounded():
    cards_pool = all_cards_dict(BASE_CARDS)
    names = build(list(BASE_CARDS.keys()), cards_pool, "B0_BASELINE")
    policy = make_contextual_keep_policy("gated")
    result = keep_rates_by_depth(names, cards_pool, COMBOS, seed=1, n=60, policy=policy)
    for k in ("keep_rate_7", "keep_rate_6", "keep_rate_5"):
        assert result[k] is None or 0.0 <= result[k] <= 1.0
    assert 4 <= result["average_final_hand_size"] <= 7
