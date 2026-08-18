"""SIM-DECKBUILD-006 E2 regression_requirements — "Badgermole trigger math" verification.

Confirms the CURRENT, disclosed status of Badgermole Cub's "whenever you tap a creature for mana,
add an additional G" amplifier: NOT modeled (DORK-003 in build_t1_t3_trajectory_audit.py, deferred
before this task even existed). This test exists so that status is explicitly, mechanically
checked rather than merely asserted in prose - if a future change silently starts granting the
bonus without a deliberate, reviewed engine change (see DORK-003's own correctness-risk writeup
for why a naive implementation would be wrong), this test fails and calls it out.
"""
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards  # noqa: E402
import deckbuild006_cards as d6  # noqa: E402
from opening_hand_policy import HandState, Perm, LandInPlay  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
CARDS = dict(d6.NEW_CARD_DATA)
CARDS.update(BASE_CARDS)


@pytest.fixture(autouse=True)
def _installed_card_tables():
    d6.install_new_card_tables()
    yield
    d6.uninstall_new_card_tables()


def test_badgermole_cub_grants_no_extra_mana_when_a_creature_dork_is_tapped():
    """Birds of Paradise alone should advertise exactly 1 unit of mana; adding Badgermole Cub to
    the battlefield must not increase that - if it ever does, Badgermole's amplifier has been
    implemented and this task's E2 disclosure (which assumes it has NOT) needs updating too."""
    rng = random.Random(0)
    state = HandState([], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    state.nonland_perms.append(Perm("Birds of Paradise", 0, True))  # entered T0, not sick at T1
    without_badgermole = state.total_mana_value()

    state.nonland_perms.append(Perm("Badgermole Cub", 0, True))
    with_badgermole = state.total_mana_value()

    assert without_badgermole == 1
    assert with_badgermole == without_badgermole, (
        "Badgermole Cub has no mana ability of its own (only amplifies OTHER creatures' taps) - "
        "if this assertion now fails because with_badgermole grew, the amplifier has become "
        "implemented; update this test and this task's E2 disclosure together."
    )


def test_badgermole_cub_is_not_registered_as_a_mana_source():
    from opening_hand_model import MANA_SOURCES
    assert "Badgermole Cub" not in MANA_SOURCES
