"""SIM-DECKBUILD-006 — frozen operative deck provenance + A/B/C/D factorial config checks."""
import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402
from deckbuild006_variants import (  # noqa: E402
    DECKBUILD006_DECKLIST_PATH, load_deckbuild006_cards, deckbuild006_cards_pool, build, VARIANTS,
    PILGRIM_NAME, PLACEHOLDER_NAME, FUNDING_CUT_FOR_C,
)
import deckbuild006_cards as d6  # noqa: E402


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d6.install_new_card_tables()
    yield
    d6.uninstall_new_card_tables()


def test_frozen_deck_has_98_cards_plus_two_commanders():
    payload = json.loads(DECKBUILD006_DECKLIST_PATH.read_text(encoding="utf-8"))
    assert len(payload["cards"]) == 98
    assert len(payload["cards"]) == len({c["name"] for c in payload["cards"]})
    assert set(payload["commanders"]) == {"Thrasios, Triton Hero", "Tymna the Weaver"}


def test_frozen_deck_hash_matches_recomputed():
    payload = json.loads(DECKBUILD006_DECKLIST_PATH.read_text(encoding="utf-8"))
    assert payload["deck_hash"] == compute_deck_hash(payload["commanders"], payload["cards"])


def test_frozen_deck_contains_lotho_not_pilgrim():
    payload = json.loads(DECKBUILD006_DECKLIST_PATH.read_text(encoding="utf-8"))
    names = {c["name"] for c in payload["cards"]}
    assert d6.LOTHO_NAME in names
    assert PILGRIM_NAME not in names


def test_load_deckbuild006_cards_rejects_tampered_hash(tmp_path, monkeypatch):
    payload = json.loads(DECKBUILD006_DECKLIST_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(payload)
    tampered["cards"][0]["name"] = "Not A Real Card"
    tampered_path = tmp_path / "tampered.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")

    import deckbuild006_variants as dv
    monkeypatch.setattr(dv, "DECKBUILD006_DECKLIST_PATH", tampered_path)
    with pytest.raises(ValueError):
        dv.load_deckbuild006_cards()


def test_load_deckbuild006_cards_returns_98_rows():
    _, rows = load_deckbuild006_cards()
    assert len(rows) == 98


def _pool_and_names():
    _, rows = load_deckbuild006_cards()
    base_names = list(rows.keys())
    pool = deckbuild006_cards_pool(rows)
    return base_names, pool


@pytest.mark.parametrize("variant_name,expect_pilgrim,expect_lotho", [
    ("A_5D_NO_LOTHO", True, False),
    ("B_4D_NO_LOTHO", False, False),
    ("C_5D_LOTHO", True, True),
    ("D_4D_LOTHO", False, True),
])
def test_factorial_configs_have_correct_dork_lotho_composition(variant_name, expect_pilgrim, expect_lotho):
    base_names, pool = _pool_and_names()
    names = build(base_names, pool, variant_name)
    assert len(names) == 98
    assert len(names) == len(set(names))
    assert (PILGRIM_NAME in names) is expect_pilgrim
    assert (d6.LOTHO_NAME in names) is expect_lotho


def test_b_config_uses_placeholder_and_never_a_and_d_or_c():
    base_names, pool = _pool_and_names()
    b_names = build(base_names, pool, "B_4D_NO_LOTHO")
    assert PLACEHOLDER_NAME in b_names
    for other in ("A_5D_NO_LOTHO", "C_5D_LOTHO", "D_4D_LOTHO"):
        assert PLACEHOLDER_NAME not in build(base_names, pool, other)


def test_c_config_cuts_only_the_disclosed_funding_card_relative_to_shared_97():
    """C should differ from D (the real operative) by exactly: +Avacyn's Pilgrim, -Mindbreak Trap.
    No other card should silently change - this is the "do not infer which real card should be
    cut" isolation guarantee, checked mechanically rather than just asserted in prose."""
    base_names, pool = _pool_and_names()
    d_names = set(build(base_names, pool, "D_4D_LOTHO"))
    c_names = set(build(base_names, pool, "C_5D_LOTHO"))
    assert c_names - d_names == {PILGRIM_NAME}
    assert d_names - c_names == {FUNDING_CUT_FOR_C}


def test_a_config_differs_from_operative_by_exactly_pilgrim_for_lotho():
    base_names, pool = _pool_and_names()
    d_names = set(build(base_names, pool, "D_4D_LOTHO"))
    a_names = set(build(base_names, pool, "A_5D_NO_LOTHO"))
    assert a_names - d_names == {PILGRIM_NAME}
    assert d_names - a_names == {d6.LOTHO_NAME}


def test_placeholder_is_not_a_creature_and_not_classified_anywhere():
    from opening_hand_model import ENGINES, ACCELERATION, TUTORS, INTERACTION_CASTABLE
    _, rows = load_deckbuild006_cards()
    pool = deckbuild006_cards_pool(rows)
    assert "Creature" not in pool[PLACEHOLDER_NAME]["type"]
    assert PLACEHOLDER_NAME not in ENGINES
    assert PLACEHOLDER_NAME not in ACCELERATION
    assert PLACEHOLDER_NAME not in TUTORS
    assert PLACEHOLDER_NAME not in INTERACTION_CASTABLE


def test_every_variant_pool_has_data_for_every_name_it_uses():
    base_names, pool = _pool_and_names()
    for variant_name in VARIANTS:
        names = build(base_names, pool, variant_name)
        for n in names:
            assert n in pool, f"{variant_name} uses {n!r} with no card data in the pool"
