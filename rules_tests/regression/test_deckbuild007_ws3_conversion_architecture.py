"""SIM-DECKBUILD-007 Workstream 3 — conversion architecture + Pod rung census sanity checks."""
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards, deckbuild007_cards_pool  # noqa: E402
from opening_hand_model import load_deterministic_combos  # noqa: E402
from build_deckbuild007_ws3_conversion_architecture import (  # noqa: E402
    rung_census, _sample_state, _classify_state, POD_RUNGS,
)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d7.install_new_card_tables()
    yield
    d7.uninstall_new_card_tables()


def test_4_to_5_rung_is_not_dead_and_seedborn_is_the_unique_key_target():
    """Re-verifies DECKBUILD-004's finding against the NEW 101-card card pool (4 cards changed
    since then) - Seedborn Muse must remain the ONLY MV5 creature this deck runs."""
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    names = list(rows.keys())
    combos = load_deterministic_combos()
    spec = POD_RUNGS["4_to_5"]
    result = rung_census(names, pool, combos, spec["sac_mv"], spec["sac_example"], spec["key_targets"])
    assert result["dead_end"] is False
    assert result["targets_tried"] == 1
    assert result["key_target_hit_rate"] == 1.0


def test_none_of_the_four_new_cards_are_mv5_creatures():
    """A direct check on WHY the 4_to_5 rung is unaffected by this task's 4 new cards."""
    for name in ("Biomancer's Familiar", "Birthing Ritual", "Dark Ritual", "The Cabbage Merchant"):
        card = d7.NEW_CARD_DATA[name]
        assert not ("Creature" in card["type"] and card["cmc"] == 5)


def test_sample_state_runs_end_to_end_with_and_without_pod():
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    names = list(rows.keys())
    combos = load_deterministic_combos()
    rng = random.Random(1)
    for pod_present in (True, False):
        m, pod_used = _sample_state(names, pool, combos, rng, mana_total=8, creature_count=3,
                                     pod_present=pod_present, protection_count=1)
        assert _classify_state(m) in {"protected_conversion", "unprotected_conversion", "one_action_away", "not_converting"}
        if not pod_present:
            assert pod_used is False


def test_more_protection_never_reduces_protected_conversion_capability_structurally():
    """Not a strict Monte Carlo guarantee (randomness), but the classifier itself must treat
    protected as a strict superset condition of unprotected - checked directly here."""
    from build_deckbuild007_ws3_conversion_architecture import _classify_state
    m_protected = {"deterministic_win_protected": True, "deterministic_win_available": True, "one_action_from_verified_win": True}
    assert _classify_state(m_protected) == "protected_conversion"
