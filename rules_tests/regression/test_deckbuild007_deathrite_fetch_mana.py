"""SIM-DECKBUILD-007 mandatory correction — Deathrite Shaman graveyard-fetch mana.

Web-verified (2 independent search results, corroborated by real competitive-Magic deckbuilding
history - Modern/Legacy Jund runs heavy fetches specifically to fuel Deathrite): fetchlands DO
qualify for Deathrite's "{T}: Exile a land card from a graveyard: Add one mana of any color that
land could produce" ability. Prior project modeling (MANA-AUDIT-002, DECKBUILD-006) treated this
as always-dead; that was wrong and is corrected here in opening_hand_policy.py's
available_sources()/_commit_payment()/_rollback_payment().
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards  # noqa: E402
from opening_hand_policy import (  # noqa: E402
    HandState, Perm, _try_pay, _commit_payment, _rollback_payment,
)

_, CARDS = load_deck_cards()


def _state(turn=2):
    rng = random.Random(0)
    state = HandState([], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = turn
    return state


def test_deathrite_produces_no_mana_with_empty_graveyard():
    state = _state()
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))
    assert state.total_mana_value() == 0


def test_deathrite_produces_mana_from_a_graveyard_fetchland():
    state = _state()
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))
    state.graveyard.append("Polluted Delta")
    sources = state.available_sources()
    assert len(sources) == 1
    ref, colors, count = sources[0]
    assert count == 1
    assert colors == {"U", "B"}  # Polluted Delta fetches Island or Swamp


def test_deathrite_is_summoning_sick_the_turn_it_enters():
    state = _state(turn=1)
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))  # entered same turn
    state.graveyard.append("Polluted Delta")
    assert state.available_sources() == []


def test_using_deathrite_taps_it_and_exiles_the_fetch_permanently():
    state = _state()
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))
    state.graveyard.append("Polluted Delta")
    plan = _try_pay(state, 1, [])
    _commit_payment(state, plan)
    perm = state.nonland_perms[0]
    assert perm.tapped is True
    assert "Polluted Delta" not in state.graveyard
    assert state.available_sources() == []  # no double-dip same turn


def test_a_normal_non_fetch_land_in_graveyard_does_not_fuel_deathrite():
    """Only fetchlands (which have FETCH_LAND_TARGET_TYPES entries) qualify in this model - a
    plain land card in the graveyard (e.g. discarded) has no basic-type-search text to derive
    'colors it could produce' from in this project's card model."""
    state = _state()
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))
    state.graveyard.append("Savannah")
    assert state.available_sources() == []


def test_rollback_restores_the_exiled_fetch_and_untaps_deathrite():
    state = _state()
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))
    state.graveyard.append("Polluted Delta")
    plan = _try_pay(state, 1, [])
    _commit_payment(state, plan)
    _rollback_payment(state, [plan])
    assert state.nonland_perms[0].tapped is False
    assert "Polluted Delta" in state.graveyard
    assert state.available_sources() != []


def test_deathrite_taps_only_once_per_turn_even_with_two_fetches_in_graveyard():
    state = _state()
    state.nonland_perms.append(Perm("Deathrite Shaman", 1, True))
    state.graveyard.extend(["Polluted Delta", "Verdant Catacombs"])
    assert state.total_mana_value() == 1  # one ref, one unit - Deathrite can only tap once
