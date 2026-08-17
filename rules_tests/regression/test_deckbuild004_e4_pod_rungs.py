"""SIM-DECKBUILD-004 E4 (scoped) — Pod rung census sanity checks."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build  # noqa: E402
from build_deckbuild004_e4_pod_rungs import rung_census  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
COMBOS = load_deterministic_combos()


@pytest.fixture(autouse=True)
def _installed_card_tables():
    install_new_card_tables()
    yield
    uninstall_new_card_tables()


def test_4_to_5_rung_is_a_dead_end_in_baseline():
    """The current 98-card list has zero MV5 creatures - a real, checkable fact, not an
    assumption - so Pod's 4->5 rung must be reported as a genuine dead end in B0."""
    cards_pool = all_cards_dict(BASE_CARDS)
    names = build(list(BASE_CARDS.keys()), cards_pool, "B0_BASELINE")
    result = rung_census(names, cards_pool, COMBOS, "Hazel's Brewmaster")
    assert result["dead_end"] is True
    assert result["targets_tried"] == 0


def test_seedborn_muse_is_the_only_4_to_5_target_created_by_full_package():
    cards_pool = all_cards_dict(BASE_CARDS)
    names = build(list(BASE_CARDS.keys()), cards_pool, "B3_FULL_PACKAGE")
    result = rung_census(names, cards_pool, COMBOS, "Hazel's Brewmaster")
    assert result["dead_end"] is False
    assert result["targets_tried"] == 1
    assert result["example_targets_by_class"]["engine_upgrade"] == ["Seedborn Muse"]


def test_talion_widens_but_does_not_dominate_the_3_to_4_rung():
    cards_pool = all_cards_dict(BASE_CARDS)
    names_b0 = build(list(BASE_CARDS.keys()), cards_pool, "B0_BASELINE")
    names_b3 = build(list(BASE_CARDS.keys()), cards_pool, "B3_FULL_PACKAGE")
    r0 = rung_census(names_b0, cards_pool, COMBOS, "Derevi, Empyrial Tactician")
    r3 = rung_census(names_b3, cards_pool, COMBOS, "Derevi, Empyrial Tactician")
    assert r3["targets_tried"] == r0["targets_tried"] + 1
    assert "Talion, the Kindly Lord" in r3["example_targets_by_class"].get("engine_upgrade", [])
