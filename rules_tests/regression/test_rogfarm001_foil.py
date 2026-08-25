"""SIM-ROGFARM-001 RULES FIX 1 — Foil regression tests.

Corrected Oracle text (supplied directly by the task owner as the authoritative fix to this
project's own wrong Stage 1 draft): {2}{U}{U} Instant, "Counter target spell. Alternative cost:
You may discard an Island card and another card rather than pay this spell's mana cost." No mana
value restriction on the target; no blue-card-exile mechanic (both were the original error).

Explicitly required coverage per the correction instruction: alternate-cost availability; Island
requirement; second discard requirement; full card-disadvantage cost (both cards actually leave
the hand); hardcast; unrestricted target mana value (documented, not separately modeled - this
solo/no-opponent engine has no opposing spells to target in the first place, consistent with
interaction_model.py's disclosed "'live' means payable, not 'has a legal target'" scope note).
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import rogfarm001_cards as rc  # noqa: E402
from opening_hand_policy import HandState  # noqa: E402

BASE_CARDS = {
    "Underground Sea": {"type": "Land — Island Swamp", "mana_cost": "", "cmc": 0, "text": "{T}: Add {U} or {B}."},
    "Volcanic Island": {"type": "Land — Island Mountain", "mana_cost": "", "cmc": 0, "text": "{T}: Add {U} or {R}."},
    "Badlands": {"type": "Land — Swamp Mountain", "mana_cost": "", "cmc": 0, "text": "{T}: Add {B} or {R}."},
    "Lightning Bolt": {"type": "Instant", "mana_cost": "{R}", "cmc": 1, "text": "Deal 3 damage."},
    "Dark Ritual": {"type": "Instant", "mana_cost": "{B}", "cmc": 1, "text": "Add {B}{B}{B}."},
}
CARDS = rc.all_cards_dict(BASE_CARDS)


def _state(hand):
    rng = random.Random(0)
    state = HandState(list(hand), [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 2
    return state


def setup_module(_module):
    rc.install_new_card_tables()


def teardown_module(_module):
    rc.uninstall_new_card_tables()


def test_foil_alternate_cost_available_with_island_and_second_card():
    state = _state(["Foil", "Underground Sea", "Lightning Bolt"])
    pair = rc.foil_discard_pair(state, CARDS)
    assert pair is not None
    island, other = pair
    assert island == "Underground Sea"
    assert other == "Lightning Bolt"


def test_foil_requires_an_actual_island_card_not_just_blue_mana():
    # Badlands taps for B/R, no Island subtype - has no bearing on Foil's alt cost even though
    # it's a perfectly good land in hand.
    state = _state(["Foil", "Badlands", "Lightning Bolt"])
    assert rc.foil_discard_pair(state, CARDS) is None
    assert rc._foil_is_live(state, CARDS) is False


def test_foil_requires_a_second_distinct_card_not_just_the_island():
    # Island alone (no second card) is NOT enough - genuine 2-card discard cost.
    state = _state(["Foil", "Underground Sea"])
    assert rc.foil_discard_pair(state, CARDS) is None


def test_foil_alt_cost_is_a_full_two_card_discard_not_a_cantrip():
    state = _state(["Foil", "Underground Sea", "Lightning Bolt"])
    resolution = rc._foil_resolve(state, CARDS)
    assert resolution is not None
    assert resolution[0] == "discard_island_plus_other"
    rc._foil_commit("Foil", resolution, state)
    # Both cards actually left the hand and landed in the graveyard - real card disadvantage,
    # not a replacement/cantrip effect.
    assert "Underground Sea" not in state.hand
    assert "Lightning Bolt" not in state.hand
    assert "Underground Sea" in state.graveyard
    assert "Lightning Bolt" in state.graveyard
    assert len(state.graveyard) == 2


def test_foil_hardcast_with_mana_available():
    state = _state(["Foil"])
    state.lands = []
    from opening_hand_policy import LandInPlay
    for name in ("Underground Sea", "Volcanic Island", "Badlands", "Tundra"):
        state.lands.append(LandInPlay(name, 1, tapped=False))
    resolution = rc._foil_resolve(state, CARDS)
    assert resolution is not None
    assert resolution[0] == "mana"  # paid the real {2}{U}{U} cost, not the discard alt cost


def test_foil_is_live_check_matches_resolve_availability():
    live_state = _state(["Foil", "Underground Sea", "Lightning Bolt"])
    assert rc._foil_is_live(live_state, CARDS) is True
    dead_state = _state(["Foil"])
    assert rc._foil_is_live(dead_state, CARDS) is False


def test_foil_has_no_mana_value_restriction_on_target():
    # No target-MV gate exists anywhere in this module's Foil logic (unlike a real budget
    # counterspell) - documented here as an explicit negative check: Foil's card-data text
    # contains no MV/CMC ceiling language, and neither foil_discard_pair nor _foil_is_live take
    # a target-cost argument at all.
    assert "mana value" not in CARDS["Foil"]["text"].lower()
    assert "converted mana cost" not in CARDS["Foil"]["text"].lower()
    import inspect
    assert "mv" not in inspect.signature(rc.foil_discard_pair).parameters
    assert "target_cost" not in inspect.signature(rc._foil_is_live).parameters


def test_foil_does_not_exile_a_blue_card():
    # The original (wrong) Stage 1 draft described Foil as exiling a blue card. Corrected: the
    # alt cost is a discard (to graveyard) of an Island CARD (a land, not necessarily blue-coded
    # by color identity the way a creature/spell is) plus another card - never an exile.
    state = _state(["Foil", "Underground Sea", "Lightning Bolt"])
    resolution = rc._foil_resolve(state, CARDS)
    rc._foil_commit("Foil", resolution, state)
    assert state.exile == []
    assert "Underground Sea" not in state.exile
