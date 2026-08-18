"""SIM-DECKBUILD-006 — gold-state checks for the new card mechanics this task added: Lotho,
Corrupt Shirriff's second-spell-of-the-turn trigger (the load-bearing mechanic - see
deckbuild006_cards.lotho_triggers_this_turn's own docstring for the exact rules derivation),
Treasure token's one-shot any-color mana source, and Grand Abolisher / Mockingbird classification.
"""
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, MANA_SOURCES  # noqa: E402
from deckbuild006_cards import (  # noqa: E402
    LOTHO_NAME, TREASURE_NAME, NEW_CARD_DATA, install_new_card_tables, uninstall_new_card_tables,
    lotho_triggers_this_turn, apply_lotho_trigger_if_any,
)
from opening_hand_policy import HandState, Perm, _card_class  # noqa: E402
from opening_hand_model import ENGINES, ACCELERATION, TUTORS, INTERACTION_CASTABLE  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
CARDS = dict(NEW_CARD_DATA)
CARDS.update(BASE_CARDS)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    install_new_card_tables()
    yield
    uninstall_new_card_tables()


def _state_with_lotho(entered_turn):
    rng = random.Random(0)
    state = HandState([], [], on_play=True, rng=rng, cards=CARDS)
    state.nonland_perms.append(Perm(LOTHO_NAME, entered_turn, True))
    return state


def test_lotho_present_all_turn_triggers_on_second_real_cast():
    state = _state_with_lotho(entered_turn=1)
    state.cast_log = [(2, "Sol Ring", "engine"), (2, "Demonic Tutor", "tutor")]
    assert lotho_triggers_this_turn(state, 2) is True


def test_lotho_cast_before_the_second_spell_this_turn_triggers():
    """Lotho itself is the FIRST real cast this turn; a different card is the second - Lotho was
    on the battlefield strictly before that second cast resolved, so it must trigger."""
    state = _state_with_lotho(entered_turn=3)
    state.cast_log = [(3, LOTHO_NAME, "engine"), (3, "Sol Ring", "engine")]
    assert lotho_triggers_this_turn(state, 3) is True


def test_lotho_as_the_second_spell_itself_does_not_trigger():
    """Lotho's own casting IS the qualifying second-spell event - it cannot retroactively see the
    event that put it into play."""
    state = _state_with_lotho(entered_turn=3)
    state.cast_log = [(3, "Sol Ring", "engine"), (3, LOTHO_NAME, "engine")]
    assert lotho_triggers_this_turn(state, 3) is False


def test_lotho_cast_after_the_second_spell_does_not_trigger():
    state = _state_with_lotho(entered_turn=3)
    state.cast_log = [(3, "Sol Ring", "engine"), (3, "Demonic Tutor", "tutor"), (3, LOTHO_NAME, "engine")]
    assert lotho_triggers_this_turn(state, 3) is False


def test_only_one_real_cast_this_turn_does_not_trigger():
    state = _state_with_lotho(entered_turn=1)
    state.cast_log = [(2, "Sol Ring", "engine")]
    assert lotho_triggers_this_turn(state, 2) is False


def test_non_cast_tags_do_not_count_toward_second_spell():
    """pod_found/battlefield_tutor_found/survival_discard are search results or discards, not
    real spell casts - Lotho's trigger counts real casts only."""
    state = _state_with_lotho(entered_turn=1)
    state.cast_log = [
        (2, "Some Creature", "pod_found"), (2, "Sol Ring", "engine"), (2, "Demonic Tutor", "tutor"),
    ]
    # Only 2 real casts this turn (Sol Ring, Demonic Tutor); Demonic Tutor is the real 2nd spell.
    assert lotho_triggers_this_turn(state, 2) is True


def test_lotho_not_in_play_never_triggers():
    rng = random.Random(0)
    state = HandState([], [], on_play=True, rng=rng, cards=CARDS)
    state.cast_log = [(2, "Sol Ring", "engine"), (2, "Demonic Tutor", "tutor")]
    assert lotho_triggers_this_turn(state, 2) is False


def test_apply_lotho_trigger_adds_treasure_and_life_loss_when_it_fires():
    state = _state_with_lotho(entered_turn=1)
    state.cast_log = [(2, "Sol Ring", "engine"), (2, "Demonic Tutor", "tutor")]
    life_before = state.life
    fired = apply_lotho_trigger_if_any(state, 2)
    assert fired is True
    assert state.life == life_before - 1
    assert any(p.name == TREASURE_NAME for p in state.nonland_perms)


def test_apply_lotho_trigger_no_op_when_it_does_not_fire():
    state = _state_with_lotho(entered_turn=1)
    state.cast_log = [(2, "Sol Ring", "engine")]
    life_before = state.life
    fired = apply_lotho_trigger_if_any(state, 2)
    assert fired is False
    assert state.life == life_before
    assert not any(p.name == TREASURE_NAME for p in state.nonland_perms)


def test_treasure_token_is_a_one_shot_any_color_source_like_lotus_petal():
    assert MANA_SOURCES[TREASURE_NAME] == MANA_SOURCES["Lotus Petal"]


def test_grand_abolisher_is_an_engine_mockingbird_is_not():
    assert "Grand Abolisher" in ENGINES
    assert LOTHO_NAME in ENGINES
    assert "Mockingbird" not in ENGINES
    assert "Mockingbird" not in ACCELERATION
    assert "Mockingbird" not in TUTORS
    assert "Mockingbird" not in INTERACTION_CASTABLE
    assert _card_class("Mockingbird", CARDS) == "other"
