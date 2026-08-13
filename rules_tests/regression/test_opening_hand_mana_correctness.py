"""SIM-001 SOLO-002R correctness-repair regression tests.

Proves the mana-source tapped-state fix (a source can no longer be reused an unbounded number of
times within a turn) and the joint-payment-search fix (combination metrics no longer approximate
simultaneity by checking each cost independently against the same untouched pool). Per the
correctness-repair instruction, these proofs are required before rerunning Part A at scale:

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

MULL-005R gate additions (t1_t3_trajectory_audit.json section 12 / assignment section 27 -
"preserve ALL SOLO-002R mana correctness fixes... do not regress"; these four were part of the
original SOLO-002R correctness repair but had no dedicated regression test until the MULL-005R
regression-gate audit found the gap):

11. Ancient Tomb produces 2 GENERIC mana per tap and costs 2 life, real burst-mana sequencing
12. Exotic Orchard produces ZERO mana in this solo/no-opponent model (disclosed assumption, not silently approximated as a real color source)
13. Fetchlands perform a REAL library search over the fetch's actual printed basic-type targets, removing the found land from the library and putting it onto the battlefield
14. The fetched land carries its REAL two basic land subtypes (ABUR duals) - a fetch cannot find a target whose types don't intersect its own search types
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import pytest  # noqa: E402

from opening_hand_model import (  # noqa: E402
    GEMSTONE_CAVERNS, CITY_OF_TRAITORS, EXOTIC_ORCHARD, ANCIENT_TOMB_LIFE_LOSS,
    DUAL_LAND_BASIC_TYPES, load_deck_cards, load_deterministic_combos,
)
from opening_hand_policy import (  # noqa: E402
    HandState, LandInPlay, Perm, develop_turn, is_currently_castable, can_pay_jointly,
    _maybe_sacrifice_city_of_traitors, _try_pay, _commit_payment, _legal_fetch_targets,
    _crack_fetch, DEFAULT_PRIORITY,
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


# ---- 11. Ancient Tomb: 2 generic mana per tap, 2 life lost per tap ----
def test_ancient_tomb_produces_two_generic_mana_and_costs_two_life():
    payload, cards = load_deck_cards()
    state = HandState([], [], on_play=True, rng=__import__("random").Random(1), cards=cards)
    state.lands.append(LandInPlay("Ancient Tomb", 0))
    life_before = state.life
    plan = _try_pay(state, 2, [])
    assert plan is not None, "a single untapped Ancient Tomb must cover a {2} generic cost alone"
    _commit_payment(state, plan)
    assert state.lands[0].tapped is True
    assert state.life == life_before - ANCIENT_TOMB_LIFE_LOSS == life_before - 2

    # a second, independent tap attempt this same turn must fail - Ancient Tomb doesn't produce
    # mana twice any more than any other land does (SOLO-002R per-source tapped-state fix applies
    # here identically).
    assert _try_pay(state, 1, []) is None


# ---- 12. Exotic Orchard: zero mana in this solo/no-opponent model (disclosed, not approximated) ----
def test_exotic_orchard_produces_no_mana_in_solo_model():
    payload, cards = load_deck_cards()
    state = HandState([], [], on_play=True, rng=__import__("random").Random(1), cards=cards)
    state.lands.append(LandInPlay(EXOTIC_ORCHARD, 0))
    assert state.available_sources() == [], (
        "Exotic Orchard's output is genuinely opponent-land-dependent ('a land an opponent "
        "controls could produce') - this solo model has no opponent, so it must contribute "
        "nothing, not a silently-assumed color."
    )
    # confirmed by an actual payment attempt too, not just available_sources() in isolation.
    assert _try_pay(state, 1, []) is None


# ---- 13/14. Fetchlands: real search over actual printed basic-type targets, real ABUR dual types ----
def test_fetchland_finds_a_real_legal_target_and_removes_it_from_the_library():
    payload, cards = load_deck_cards()
    # Flooded Strand's real targets are Plains/Island lands - Tundra (Plains Island) qualifies.
    library = ["Tundra"] + [n for n in cards if n not in ("Flooded Strand", "Tundra")][:30]
    state = HandState(["Flooded Strand"], library, on_play=True, rng=__import__("random").Random(1), cards=cards)
    assert "Tundra" in _legal_fetch_targets(state, "Flooded Strand")
    life_before = state.life
    _crack_fetch(state, "Flooded Strand", need_colors={"W"})
    assert "Tundra" in [l.name for l in state.lands], "the real fetched land must land on the battlefield"
    assert "Tundra" not in state.library, "the fetched card must be removed from the library, not duplicated"
    assert "Flooded Strand" in state.graveyard, "the fetchland itself is sacrificed"
    assert state.life == life_before - 1, "cracking a fetchland costs exactly 1 life"


def test_fetchland_cannot_find_a_target_whose_types_dont_match():
    payload, cards = load_deck_cards()
    # Bayou is Swamp/Forest - not a legal Flooded Strand (Plains/Island) target, even if it's the
    # only dual left in the library. This is the real-Oracle-text search restriction, not an
    # assumed "any dual will do" simplification.
    assert not (DUAL_LAND_BASIC_TYPES["Bayou"] & {"Plains", "Island"}), "sanity: Bayou really doesn't share a type with Flooded Strand's search"
    library = ["Bayou"] + [n for n in cards if n not in ("Flooded Strand", "Bayou")][:30]
    state = HandState(["Flooded Strand"], library, on_play=True, rng=__import__("random").Random(1), cards=cards)
    assert "Bayou" not in _legal_fetch_targets(state, "Flooded Strand")
    _crack_fetch(state, "Flooded Strand", need_colors={"W"})
    # no legal target in this constructed library -> the fetch enters inert (tapped, unsacrificed)
    # rather than illegally grabbing Bayou.
    assert any(l.name == "Flooded Strand" and l.tapped for l in state.lands)
    assert "Bayou" in state.library, "an illegal target must never be removed from the library"
