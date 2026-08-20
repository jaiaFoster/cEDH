"""SIM-DECKBUILD-007 — gold-state checks for the 4 new cards' mechanics (Dark Ritual's net-mana
residue pattern is the load-bearing one) and the frozen-deck/loader provenance."""
import copy
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402
from opening_hand_model import load_deck_cards, ACCELERATION  # noqa: E402
import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import (  # noqa: E402
    DECKBUILD007_DECKLIST_PATH, load_deckbuild007_cards, deckbuild007_cards_pool, build,
)
from opening_hand_policy import HandState, Perm  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
CARDS = dict(d7.NEW_CARD_DATA)
CARDS.update(BASE_CARDS)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d7.install_new_card_tables()
    yield
    d7.uninstall_new_card_tables()


def test_frozen_deck_hash_matches_and_has_99_plus_2():
    payload = json.loads(DECKBUILD007_DECKLIST_PATH.read_text(encoding="utf-8"))
    assert len(payload["cards"]) == 99
    assert payload["deck_hash"] == compute_deck_hash(payload["commanders"], payload["cards"])


def test_load_deckbuild007_cards_rejects_tampered_hash(tmp_path, monkeypatch):
    payload = json.loads(DECKBUILD007_DECKLIST_PATH.read_text(encoding="utf-8"))
    tampered = copy.deepcopy(payload)
    tampered["cards"][0]["name"] = "Not A Real Card"
    p = tmp_path / "tampered.json"
    p.write_text(json.dumps(tampered), encoding="utf-8")
    import deckbuild007_variants as dv
    monkeypatch.setattr(dv, "DECKBUILD007_DECKLIST_PATH", p)
    with pytest.raises(ValueError):
        dv.load_deckbuild007_cards()


def test_diff_vs_deckbuild006_matches_assignment_framing():
    _, rows = load_deckbuild007_cards()
    names = set(rows.keys())
    added = {"Biomancer's Familiar", "Birthing Ritual", "Dark Ritual", "The Cabbage Merchant"}
    for n in added:
        assert n in names
    for n in ("An Offer You Can't Refuse", "Shang-Chi, Master of Kung Fu", "Training Grounds"):
        assert n not in names


def test_dark_ritual_nets_plus_two_black_mana():
    rng = random.Random(0)
    state = HandState(["Dark Ritual"], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.lands.append(__import__("opening_hand_policy").LandInPlay("Bayou", 1, tapped=False))
    before = state.total_mana_value()
    assert before == 1
    fired = d7.try_cast_dark_ritual(state, CARDS)
    assert fired is True
    assert "Dark Ritual" not in state.hand
    assert state.total_mana_value() == 3  # spent 1 B, gained 3 B = net +2, all B


def test_dark_ritual_fails_without_black_mana():
    rng = random.Random(0)
    state = HandState(["Dark Ritual"], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    fired = d7.try_cast_dark_ritual(state, CARDS)
    assert fired is False
    assert "Dark Ritual" in state.hand


def test_dark_ritual_residue_is_stranded_if_unused():
    rng = random.Random(0)
    state = HandState(["Dark Ritual"], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.lands.append(__import__("opening_hand_policy").LandInPlay("Bayou", 1, tapped=False))
    d7.try_cast_dark_ritual(state, CARDS)
    stranded = d7.sweep_stranded_dark_ritual_residue(state, 1)
    assert stranded == 3  # nothing spent it
    assert state.total_mana_value() == 0


def test_dark_ritual_residue_partially_used_is_not_double_counted():
    rng = random.Random(0)
    state = HandState(["Dark Ritual"], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.lands.append(__import__("opening_hand_policy").LandInPlay("Bayou", 1, tapped=False))
    d7.try_cast_dark_ritual(state, CARDS)
    from opening_hand_policy import _try_pay, _commit_payment
    plan = _try_pay(state, 0, ["B", "B"])
    _commit_payment(state, plan)
    stranded = d7.sweep_stranded_dark_ritual_residue(state, 1)
    assert stranded == 1  # used 2 of 3


def test_dark_ritual_residue_does_not_carry_over_to_next_turn():
    rng = random.Random(0)
    state = HandState(["Dark Ritual"], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.lands.append(__import__("opening_hand_policy").LandInPlay("Bayou", 1, tapped=False))
    d7.try_cast_dark_ritual(state, CARDS)
    d7.sweep_stranded_dark_ritual_residue(state, 1)
    state.turn = 2
    assert state.total_mana_value() == 0


def test_birthing_ritual_and_carpet_are_registered_acceleration_dark_ritual_is_not():
    assert "Birthing Ritual" in ACCELERATION
    assert d7.CARPET_NAME in ACCELERATION
    # Dark Ritual is deliberately excluded - see deckbuild007_cards.py's module docstring for why
    # auto-casting an Instant through the generic permanent-creation path would silently waste it.
    assert "Dark Ritual" not in ACCELERATION


def test_dark_ritual_is_never_auto_cast_by_the_generic_greedy_loop():
    from opening_hand_policy import _card_class, DEFAULT_PRIORITY
    assert _card_class("Dark Ritual", CARDS) not in DEFAULT_PRIORITY


def test_variant_builder_carpet_instead_of_ritual():
    _, rows = load_deckbuild007_cards()
    pool = deckbuild007_cards_pool(rows)
    base_names = list(rows.keys())
    swapped = build(base_names, pool, add=[d7.CARPET_NAME], remove=["Dark Ritual"])
    assert len(swapped) == 99
    assert d7.CARPET_NAME in swapped
    assert "Dark Ritual" not in swapped
