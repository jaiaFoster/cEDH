"""SIM-DECKBUILD-004 — gold-state checks for the new card mechanics this task added: Neoform's
mv_offset generalization of the battlefield-creature-tutor family, and Formidable Speaker's ETB
discard-tutor-to-hand + repeatable untap ability.
"""
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards  # noqa: E402
from deckbuild004_cards import (  # noqa: E402
    all_cards_dict, install_new_card_tables, uninstall_new_card_tables, NEOFORM_SPEC,
)
from opening_hand_policy import HandState, develop_turn, LandInPlay, Perm, DEFAULT_PRIORITY  # noqa: E402
from pod_and_battlefield_tutors import try_battlefield_creature_tutor, BATTLEFIELD_CREATURE_TUTORS  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
CARDS = all_cards_dict(BASE_CARDS)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    """Installs this module's global-table mutations only for the duration of each test in this
    file, and restores them afterward - required because these globals are shared, mutable module
    objects imported (via `from x import Y`) throughout the rest of this test suite; leaking the
    mutation past this file's own tests broke an unrelated exact-set-equality assertion in
    test_mull006_relevant_agency_model.py on first contact (see install_new_card_tables()'s own
    docstring)."""
    install_new_card_tables()
    yield
    uninstall_new_card_tables()


def test_neoform_registered_with_plus_one_offset():
    assert BATTLEFIELD_CREATURE_TUTORS["Neoform"]["mv_offset"] == 1
    assert BATTLEFIELD_CREATURE_TUTORS["Eldritch Evolution"].get("mv_offset", 2) == 2


def test_neoform_finds_exact_plus_one_target_not_plus_two():
    """Sac a real MV1 creature (Birds of Paradise); Neoform must find an MV2 target (Kinnan,
    Bonder Prodigy - GU, cmc 2), NOT an MV3 target (Eldritch Evolution's own +2 rule)."""
    rng = random.Random(0)
    state = HandState(["Neoform"], ["Kinnan, Bonder Prodigy"], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.lands += [LandInPlay("Tropical Island", 1, tapped=False)]  # G/U, funds {G}{U}
    state.nonland_perms.append(Perm("Birds of Paradise", 0, True))  # not summoning sick

    ok = try_battlefield_creature_tutor(state, CARDS, "Neoform", "Kinnan, Bonder Prodigy", "Birds of Paradise")
    assert ok
    assert "Kinnan, Bonder Prodigy" in [p.name for p in state.nonland_perms]
    assert "Birds of Paradise" not in [p.name for p in state.nonland_perms]


def test_neoform_rejects_plus_two_target():
    rng = random.Random(0)
    state = HandState(["Neoform"], ["Derevi, Empyrial Tactician"], on_play=True, rng=rng, cards=CARDS)  # cmc 3
    state.turn = 1
    state.lands += [LandInPlay("Tropical Island", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birds of Paradise", 0, True))  # cmc 1; 1+2=3 (wrong for Neoform)

    ok = try_battlefield_creature_tutor(state, CARDS, "Neoform", "Derevi, Empyrial Tactician", "Birds of Paradise")
    assert not ok


def test_formidable_speaker_etb_only_fires_when_cast_this_turn():
    """Speaker resolved on a PRIOR turn (not this call's turn) - its ETB must not fire again."""
    rng = random.Random(0)
    state = HandState(["Sol Ring"], ["Noble Hierarch"], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.nonland_perms.append(Perm("Formidable Speaker", 0, True))  # entered turn 0, not this turn
    actions = develop_turn(
        state, CARDS, priority_order=DEFAULT_PRIORITY,
        forced_formidable_speaker_choice=("Sol Ring", "Noble Hierarch"),
    )
    assert not any(a[0] == "formidable_speaker_etb" for a in actions)
    assert "Sol Ring" in state.hand  # discard never happened


def test_formidable_speaker_etb_fires_the_turn_it_is_cast():
    """Voice of Victory (unclassified 'other' - see _card_class) is used as discard fodder so it
    doesn't compete with Speaker for the generic loop's own casting priority the way an
    ACCELERATION-classified card (e.g. Sol Ring) would. Enough lands to fund both Tymna (auto-cast
    every turn she's affordable, being a real 'commander' class card) and Speaker's {2}{G}."""
    rng = random.Random(0)
    state = HandState(["Formidable Speaker", "Voice of Victory"], ["Noble Hierarch"], on_play=True, rng=rng, cards=CARDS)
    state.turn = 0
    state.command_zone.clear()  # isolate this test from commander auto-casting competing for mana
    state.lands.append(LandInPlay("City of Brass", 1, tapped=False))
    state.lands.append(LandInPlay("Command Tower", 1, tapped=False))
    state.lands.append(LandInPlay("Mana Confluence", 1, tapped=False))
    actions = develop_turn(
        state, CARDS, priority_order=DEFAULT_PRIORITY,
        forced_formidable_speaker_choice=("Voice of Victory", "Noble Hierarch"),
    )
    assert any(a[0] == "cast" and a[1] == "Formidable Speaker" for a in actions)
    assert any(a[0] == "formidable_speaker_etb" for a in actions)
    assert "Noble Hierarch" in state.hand
    assert "Voice of Victory" not in state.hand
    assert "Voice of Victory" in state.graveyard


def test_formidable_speaker_untap_ability_untaps_a_land_tapped_earlier_this_turn():
    """develop_turn's own untap_all() runs first each call, so a land must become tapped from
    THIS turn's own actions (paying for Sol Ring) for the untap-ability test to be meaningful.
    Two lands: one pays for Sol Ring (ends tapped), the other funds Speaker's own {1} untap cost -
    the SPECIFIC land the payment engine chose for Sol Ring isn't asserted (an implementation
    detail of the generic payment search), only that some land ends the turn tapped, gets
    untapped again via the forced ability, and Speaker's action is recorded."""
    # First pass: discover which land the payment engine taps for Sol Ring.
    real_state = HandState(["Sol Ring"], [], on_play=True, rng=random.Random(0), cards=CARDS)
    real_state.turn = 0
    real_state.nonland_perms.append(Perm("Formidable Speaker", 0, True))
    real_state.lands.append(LandInPlay("Command Tower", 0, tapped=False))
    real_state.lands.append(LandInPlay("City of Brass", 0, tapped=False))
    develop_turn(real_state, CARDS, priority_order=DEFAULT_PRIORITY)
    tapped_land_name = next(l.name for l in real_state.lands if l.tapped)

    real_state2 = HandState(["Sol Ring"], [], on_play=True, rng=random.Random(0), cards=CARDS)
    real_state2.turn = 0
    real_state2.nonland_perms.append(Perm("Formidable Speaker", 0, True))
    real_state2.lands.append(LandInPlay("Command Tower", 0, tapped=False))
    real_state2.lands.append(LandInPlay("City of Brass", 0, tapped=False))
    actions = develop_turn(
        real_state2, CARDS, priority_order=DEFAULT_PRIORITY,
        forced_formidable_speaker_untaps=[tapped_land_name],
    )
    assert any(a == ("formidable_speaker_untap", tapped_land_name) for a in actions)
    # The untap ability's own {1} cost necessarily taps ANOTHER source to fund it - only the
    # requested target must end up untapped, not every land (that would mean the ability was
    # free, which it isn't).
    untapped_target = next(l for l in real_state2.lands if l.name == tapped_land_name)
    assert untapped_target.tapped is False
    assert sum(l.tapped for l in real_state2.lands) == 1
