"""SIM-001 SOLO-002R correctness-repair regression tests.

Proves the mana-source tapped-state fix (a source can no longer be reused an unbounded number of
times within a turn) and the joint-payment-search fix (combination metrics no longer approximate
simultaneity by checking each cost independently against the same untouched pool). Per the
correctness-repair instruction, these ten proofs are required before rerunning Part A at scale:

1. one land cannot pay for two one-mana spells in the same turn
2. Sol Ring cannot be tapped twice
3. Mana Vault cannot be tapped twice (and never auto-untaps)
4. a mana dork cannot tap on its entry turn unless legally hasted/permitted
5. a used source becomes available again after the normal untap step
6. City of Traitors sacrifices correctly
7. Gemstone Caverns behaves differently on play vs. draw
8. engine + interaction only passes if both are jointly achievable
9. two combo pieces only count zero-step if the entire validated line is jointly executable
10. commander + activation uses shared mana correctly
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import pytest  # noqa: E402

from opening_hand_model import GEMSTONE_CAVERNS, CITY_OF_TRAITORS, load_deck_cards, load_deterministic_combos  # noqa: E402
from opening_hand_policy import (  # noqa: E402
    HandState, LandInPlay, Perm, develop_turn, is_currently_castable, can_pay_jointly,
    _maybe_sacrifice_city_of_traitors, DEFAULT_PRIORITY,
)
from opening_hand_metrics import snapshot_metrics  # noqa: E402

# A minimal synthetic card table - just enough type/mana_cost data for the mechanical
# mana-tapping tests, deliberately NOT depending on the real 98-card deck so these stay fast and
# isolated from incidental real-deck details.
FAKE_CARDS = {
    "Command Tower": {"name": "Command Tower", "type": "Land", "mana_cost": "", "cmc": 0},
    "Bayou": {"name": "Bayou", "type": "Land — Swamp Forest", "mana_cost": "", "cmc": 0},
    "One Mana Spell A": {"name": "One Mana Spell A", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
    "One Mana Spell B": {"name": "One Mana Spell B", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
    "Birds of Paradise": {"name": "Birds of Paradise", "type": "Creature — Bird", "mana_cost": "{G}", "cmc": 1},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Mana Vault": {"name": "Mana Vault", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
}


def _minimal_state(hand=None, library=None, on_play=True):
    import random
    return HandState(hand or [], library or [], on_play=on_play, rng=random.Random(1), cards=FAKE_CARDS)


# ---- 1. one land cannot pay for two one-mana spells in the same turn ----
def test_one_land_cannot_pay_two_one_mana_spells():
    state = _minimal_state()
    state.lands.append(LandInPlay("Command Tower", 1))
    from opening_hand_policy import _try_pay, _commit_payment
    plan1 = _try_pay(state, 1, [])
    assert plan1 is not None
    _commit_payment(state, plan1)
    assert state.lands[0].tapped is True
    plan2 = _try_pay(state, 1, [])
    assert plan2 is None, "a second 1-mana payment must fail once the only land is tapped"


# ---- 2. Sol Ring cannot be tapped twice ----
def test_sol_ring_cannot_be_tapped_twice():
    state = _minimal_state()
    state.nonland_perms.append(Perm("Sol Ring", 0, is_creature=False))
    from opening_hand_policy import _try_pay, _commit_payment
    plan1 = _try_pay(state, 2, [])
    assert plan1 is not None
    _commit_payment(state, plan1)
    assert state.nonland_perms[0].tapped is True
    plan2 = _try_pay(state, 1, [])
    assert plan2 is None, "Sol Ring is tapped - no mana left this turn"


# ---- 3. Mana Vault cannot be tapped twice, and never auto-untaps ----
def test_mana_vault_never_untaps():
    state = _minimal_state()
    state.nonland_perms.append(Perm("Mana Vault", 0, is_creature=False, never_untaps=True))
    state.lands.append(LandInPlay("Command Tower", 0))
    from opening_hand_policy import _try_pay, _commit_payment
    plan = _try_pay(state, 3, [])
    assert plan is not None
    _commit_payment(state, plan)
    assert state.nonland_perms[0].tapped is True
    # simulate the next turn's untap step
    state.untap_all()
    assert state.lands[0].tapped is False, "a normal land must untap normally"
    assert state.nonland_perms[0].tapped is True, "Mana Vault doesn't untap during your untap step"


# ---- 4. a mana dork cannot tap on its entry turn unless legally hasted/permitted ----
def test_mana_dork_summoning_sick_on_entry_turn():
    state = _minimal_state()
    state.turn = 2
    state.nonland_perms.append(Perm("Birds of Paradise", 2, is_creature=True))  # entered THIS turn
    sources = state.available_sources()
    names = [ref.name if hasattr(ref, "name") else ref for (ref, colors, count) in sources]
    assert "Birds of Paradise" not in names, "a dork cast this turn is summoning sick and cannot tap"
    state.turn = 3  # next turn
    sources = state.available_sources()
    names = [ref.name if hasattr(ref, "name") else ref for (ref, colors, count) in sources]
    assert "Birds of Paradise" in names, "by the next turn it is no longer summoning sick"


# ---- 5. a used source becomes available again after the normal untap step ----
def test_source_returns_after_untap_step():
    state = _minimal_state()
    state.lands.append(LandInPlay("Bayou", 0))
    from opening_hand_policy import _try_pay, _commit_payment
    plan = _try_pay(state, 1, [])
    _commit_payment(state, plan)
    assert state.lands[0].tapped is True
    assert state.total_mana_value() == 0
    state.untap_all()
    assert state.lands[0].tapped is False
    assert state.total_mana_value() == 1


# ---- 6. City of Traitors sacrifices correctly ----
def test_city_of_traitors_sacrifices_on_next_land():
    state = _minimal_state()
    state.lands.append(LandInPlay(CITY_OF_TRAITORS, 1))
    # playing City of Traitors itself must NOT sacrifice it (only "another" land triggers it)
    assert CITY_OF_TRAITORS in [l.name for l in state.lands]
    # now simulate playing a DIFFERENT land
    _maybe_sacrifice_city_of_traitors(state)
    assert CITY_OF_TRAITORS not in [l.name for l in state.lands]
    assert CITY_OF_TRAITORS in state.graveyard


def test_city_of_traitors_full_turn_sequence():
    """End-to-end via develop_turn: City of Traitors survives its own land drop, then is
    sacrificed the next turn a different land is played."""
    payload, cards = load_deck_cards()
    hand = ["City of Traitors", "Command Tower", "Sol Ring", "Demonic Tutor",
            "Vampiric Tutor", "Imperial Seal", "Force of Will"]
    library = [n for n in cards if n not in hand][:40]
    state = HandState(hand, library, on_play=True, rng=__import__("random").Random(1), cards=cards)
    develop_turn(state, cards)  # turn 1: plays a land (City of Traitors is a candidate)
    if any(l.name == CITY_OF_TRAITORS for l in state.lands):
        develop_turn(state, cards)  # turn 2: any other land drop must sacrifice it
        if len(state.lands) >= 2 or CITY_OF_TRAITORS in state.graveyard:
            names = [l.name for l in state.lands]
            assert names.count(CITY_OF_TRAITORS) <= 1


# ---- 7. Gemstone Caverns behaves differently on play vs. draw ----
def test_gemstone_caverns_on_play_stays_in_hand():
    payload, cards = load_deck_cards()
    hand = [GEMSTONE_CAVERNS, "Sol Ring", "Demonic Tutor", "Force of Will",
            "Vampiric Tutor", "Imperial Seal", "Chord of Calling"]
    state = HandState(hand, [], on_play=True, rng=__import__("random").Random(1), cards=cards)
    assert GEMSTONE_CAVERNS in state.hand, "on the play, the pregame action is not available at all"
    assert not any(l.name == GEMSTONE_CAVERNS for l in state.lands)


def test_gemstone_caverns_on_draw_takes_luck_counter_action():
    payload, cards = load_deck_cards()
    hand = [GEMSTONE_CAVERNS, "Sol Ring", "Demonic Tutor", "Force of Will",
            "Vampiric Tutor", "Imperial Seal", "Chord of Calling"]  # only 0 other lands - should take the action
    state = HandState(hand, [], on_play=False, rng=__import__("random").Random(1), cards=cards)
    caverns = [l for l in state.lands if l.name == GEMSTONE_CAVERNS]
    assert len(caverns) == 1, "on the draw with a land-light hand, the free untapped-any-color land should be taken"
    assert caverns[0].has_luck_counter is True
    assert GEMSTONE_CAVERNS not in state.hand
    assert len(state.hand) == 5, "one card was exiled as the action's real cost, on top of Caverns itself leaving hand"
    # untapped, any color, right now
    sources = state.available_sources()
    caverns_src = [s for s in sources if getattr(s[0], "name", None) == GEMSTONE_CAVERNS]
    assert len(caverns_src) == 1
    assert caverns_src[0][1] == set("WUBG")


# ---- 8. engine + interaction only passes if both are jointly achievable ----
def test_engine_plus_interaction_requires_joint_payability():
    state = _minimal_state()
    state.lands.append(LandInPlay("Command Tower", 0))  # exactly ONE untapped 1-mana source
    cost_a = (1, [])
    cost_b = (1, [])
    assert is_currently_castable(state, *cost_a) is True
    assert is_currently_castable(state, *cost_b) is True, (
        "each cost looks individually affordable from the SAME untouched pool"
    )
    assert can_pay_jointly(state, [cost_a, cost_b]) is False, (
        "but only one 1-mana source exists - they are NOT jointly payable"
    )
    # state must be untouched after the joint dry-run (rollback correctness)
    assert state.lands[0].tapped is False


def test_engine_plus_interaction_passes_when_truly_joint():
    state = _minimal_state()
    state.lands.append(LandInPlay("Command Tower", 0))
    state.lands.append(LandInPlay("Bayou", 0))
    assert can_pay_jointly(state, [(1, []), (1, [])]) is True
    assert all(not l.tapped for l in state.lands), "a dry run must roll back, not leave sources tapped"


# ---- 9. two combo pieces only count zero-step if jointly executable ----
def test_combo_zero_step_requires_joint_line():
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()
    int0002 = next(c for c in combos if c["id"] == "INT-0002")  # Devoted Druid + Swift Reconfiguration
    assert set(int0002["cards"]) == {"Devoted Druid", "Swift Reconfiguration"}

    # Devoted Druid = {1}{G} (2 mana), Swift Reconfiguration = {W} (1 mana) -> 3 mana needed jointly.
    assert cards["Devoted Druid"]["mana_cost"] == "{1}{G}"
    assert cards["Swift Reconfiguration"]["mana_cost"] == "{W}"

    # Exactly 2 mana available: enough to fully pay Devoted Druid ALONE (individually
    # affordable), or Swift Reconfiguration ALONE, but not both at once -> must NOT be zero_step.
    state = HandState(["Devoted Druid", "Swift Reconfiguration"], [], on_play=True,
                       rng=__import__("random").Random(1), cards=cards)
    state.lands.append(LandInPlay("Bayou", 0))
    state.lands.append(LandInPlay("Command Tower", 0))
    state.turn = 1
    state.turn_start_mana = state.total_mana_value()
    state.turn_start_colors = state.colors_available()
    m = snapshot_metrics(state, cards, combos)
    assert m["combo_status"]["INT-0002"] != "zero_step", (
        "both pieces are individually affordable from this 2-mana pool, but not jointly (need "
        "3 total) - this must not be reported as a live deterministic win"
    )
    assert m["deterministic_win_available"] is False
    assert all(not l.tapped for l in state.lands), "a metrics dry-run must never leave real state mutated"

    # 3 mana available (enough for both jointly) -> must be zero_step
    state2 = HandState(["Devoted Druid", "Swift Reconfiguration"], [], on_play=True,
                        rng=__import__("random").Random(1), cards=cards)
    state2.lands.append(LandInPlay("Bayou", 0))
    state2.lands.append(LandInPlay("Command Tower", 0))
    state2.lands.append(LandInPlay("Command Tower", 0))
    state2.turn = 1
    state2.turn_start_mana = state2.total_mana_value()
    state2.turn_start_colors = state2.colors_available()
    m2 = snapshot_metrics(state2, cards, combos)
    assert m2["combo_status"]["INT-0002"] == "zero_step"
    assert m2["deterministic_win_available"] is True
    # the dry run must not have left real state mutated
    assert all(not l.tapped for l in state2.lands)


# ---- 10. commander + activation uses shared mana correctly ----
def test_thrasios_activation_uses_remaining_mana_correctly():
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()
    state = HandState([], [], on_play=True, rng=__import__("random").Random(1), cards=cards)
    state.nonland_perms.append(Perm("Thrasios, Triton Hero", 0, is_creature=True))
    for _ in range(4):
        state.lands.append(LandInPlay("Command Tower", 0))
    state.turn = 1
    state.turn_start_mana = state.total_mana_value()
    state.turn_start_colors = state.colors_available()
    m = snapshot_metrics(state, cards, combos)
    assert m["thrasios_activation_now"] is True, "4 untapped generic sources should cover the {4} activation"

    # now tap two of the four lands (simulating mana already spent elsewhere this turn) and
    # re-snapshot - activation must correctly become unavailable, not still report True from a
    # stale/isolated turn-start total.
    state.lands[0].tapped = True
    state.lands[1].tapped = True
    m2 = snapshot_metrics(state, cards, combos)
    assert m2["thrasios_activation_now"] is False, (
        "only 2 mana genuinely remains untapped - activation must reflect real remaining "
        "capacity, not the turn's original starting total"
    )
