"""SIM-001 SOLO-003R correctness-repair regression tests.

Proves the four fixes requested by the SOLO-003 (commit 5d62a60) review before any rerun of the
trajectory census is trusted:

1. Kinnan, Bonder Prodigy doubles a nonland mana permanent's output, but not a land (Gaea's
   Cradle) and not Elvish Spirit Guide (never a permanent).
2. A tutor sitting in hand but NOT currently castable does not count as "live" for combo-proximity
   tiering, and a live tutor only counts as a path to a missing combo piece if its own target-class
   reach actually includes "combo_piece".
3. "One action from a win" (credible win pressure) excludes the pure-topdeck case
   (one_draw_step_from_win) and includes the mana-backed and tutor-backed cases.
4. Tymna's (and any creature's) attack capacity respects summoning sickness - a creature cast this
   same turn cannot attack.
5. `total_mana`/`colors_available` in snapshot_metrics() report this turn's STARTING CAPACITY, not
   post-cast leftover, and `mana_shortfall` is only true when a desirable card was uncastable even
   against the turn's full capacity.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, LandInPlay, Perm  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402

FAKE_CARDS = {
    "Command Tower": {"name": "Command Tower", "type": "Land", "mana_cost": "", "cmc": 0},
    "Bayou": {"name": "Bayou", "type": "Land — Swamp Forest", "mana_cost": "", "cmc": 0},
    "Birds of Paradise": {"name": "Birds of Paradise", "type": "Creature — Bird", "mana_cost": "{G}", "cmc": 1},
    "Kinnan, Bonder Prodigy": {
        "name": "Kinnan, Bonder Prodigy", "type": "Legendary Creature — Human Druid",
        "mana_cost": "{1}{G}{U}", "cmc": 3,
    },
    "Tymna the Weaver": {
        "name": "Tymna the Weaver", "type": "Legendary Creature — Human Cleric",
        "mana_cost": "{1}{W}{B}", "cmc": 3,
    },
    "Grizzly Bears": {"name": "Grizzly Bears", "type": "Creature — Bear", "mana_cost": "{1}{G}", "cmc": 2},
    "Demonic Tutor": {"name": "Demonic Tutor", "type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2},
    "Sowing Mycospawn": {"name": "Sowing Mycospawn", "type": "Creature", "mana_cost": "{4}{R}", "cmc": 5},
    "Combo Piece A": {"name": "Combo Piece A", "type": "Creature", "mana_cost": "{1}{G}", "cmc": 2},
    "Combo Piece B": {"name": "Combo Piece B", "type": "Creature", "mana_cost": "{1}{U}", "cmc": 2},
    "Rhystic Study": {"name": "Rhystic Study", "type": "Enchantment", "mana_cost": "{2}{U}", "cmc": 3},
}
FAKE_COMBO = {"id": "TEST-0001", "cards": ["Combo Piece A", "Combo Piece B"]}


def _minimal_state(hand=None, library=None, on_play=True, turn=3):
    state = HandState(hand or [], library or [], on_play=on_play, rng=random.Random(1), cards=FAKE_CARDS)
    state.turn = turn
    return state


# ---- 1. Kinnan doubles nonland mana permanents, not lands or Elvish Spirit Guide ----
def test_kinnan_doubles_mana_dork_output():
    state = _minimal_state()
    state.nonland_perms.append(Perm("Birds of Paradise", 1, is_creature=True))  # not cast this turn
    assert state.total_mana_value() == 1
    state.nonland_perms.append(Perm("Kinnan, Bonder Prodigy", 1, is_creature=True))
    assert state.total_mana_value() == 2, "Kinnan must double a nonland mana dork's output"


def test_kinnan_does_not_double_gaeas_cradle():
    from opening_hand_model import CRADLE
    state = _minimal_state()
    state.lands.append(LandInPlay(CRADLE, 0))
    state.nonland_perms.append(Perm("Birds of Paradise", 1, is_creature=True))
    before = state.total_mana_value()  # Cradle (1, one creature) + Birds (1) = 2
    assert before == 2
    state.nonland_perms.append(Perm("Kinnan, Bonder Prodigy", 1, is_creature=True))
    # Kinnan doubles Birds (1 -> 2) but NOT Cradle directly - Cradle's own output only rises
    # because Kinnan herself is now an additional creature Cradle counts (1 -> 2 creatures).
    after = state.total_mana_value()
    assert after == 4, "Cradle (now 2 creatures = 2) + Birds doubled (2) = 4, not Cradle doubled directly"


def test_kinnan_does_not_double_elvish_spirit_guide():
    state = _minimal_state(hand=["Combo Piece A"])
    state.hand.append("Elvish Spirit Guide")
    FAKE_CARDS.setdefault(
        "Elvish Spirit Guide",
        {"name": "Elvish Spirit Guide", "type": "Creature — Elf", "mana_cost": "{1}{G}", "cmc": 2},
    )
    without_kinnan = state.total_mana_value()
    state.nonland_perms.append(Perm("Kinnan, Bonder Prodigy", 1, is_creature=True))
    with_kinnan = state.total_mana_value()
    assert with_kinnan == without_kinnan, "Elvish Spirit Guide is never a permanent - Kinnan cannot double it"


# ---- 2. tutor liveness (castable, not merely present) + combo-piece target reach ----
# All three tests below deploy Combo Piece A already (sunk, no further mana needed) so the only
# missing combo piece is Combo Piece B (unseen) - isolating exactly what the tutor-liveness/reach
# check is supposed to gate, per the "missing == 1" tiering in snapshot_metrics().
def test_uncastable_tutor_in_hand_does_not_grant_tutor_step():
    # Demonic Tutor in hand but NO mana at all - not castable.
    state = _minimal_state(hand=["Demonic Tutor"])
    state.nonland_perms.append(Perm("Combo Piece A", 1, is_creature=True))
    state.turn_start_mana = 0
    state.turn_start_colors = set()
    m = snapshot_metrics(state, FAKE_CARDS, [FAKE_COMBO])
    assert m["combo_status"]["TEST-0001"] == "one_draw_step_from_win"
    assert m["one_tutor_step_from_win"] is False
    assert m["one_action_from_verified_win"] is False, \
        "an uncastable (merely present) tutor must not count as credible win pressure"


def test_tutor_that_cannot_reach_combo_pieces_does_not_grant_tutor_step():
    # Sowing Mycospawn is castable (plenty of mana) but its target reach is land-only, not
    # combo_piece - must not be treated as a path to the missing combo piece.
    state = _minimal_state(hand=["Sowing Mycospawn"])
    state.nonland_perms.append(Perm("Combo Piece A", 1, is_creature=True))
    state.lands = [LandInPlay("Bayou", 0) for _ in range(6)]
    state.turn_start_mana = 6
    state.turn_start_colors = {"G", "B"}
    m = snapshot_metrics(state, FAKE_CARDS, [FAKE_COMBO])
    assert m["combo_status"]["TEST-0001"] == "one_draw_step_from_win"
    assert m["one_action_from_verified_win"] is False


def test_live_combo_reaching_tutor_grants_tutor_step():
    state = _minimal_state(hand=["Demonic Tutor"])
    state.nonland_perms.append(Perm("Combo Piece A", 1, is_creature=True))
    state.lands = [LandInPlay("Bayou", 0), LandInPlay("Command Tower", 0)]
    state.turn_start_mana = 2
    state.turn_start_colors = {"B", "G"}
    m = snapshot_metrics(state, FAKE_CARDS, [FAKE_COMBO])
    assert m["combo_status"]["TEST-0001"] == "one_tutor_step_from_win"
    assert m["one_tutor_step_from_win"] is True
    assert m["one_action_from_verified_win"] is True


# ---- 3. draw-dependent step excluded, mana-backed step included ----
def test_mana_backed_step_counts_as_credible_win_pressure():
    # Combo Piece A already deployed (sunk); Combo Piece B is in hand but not affordable with
    # zero mana available - that's a mana-progression-only signal (both pieces already SEEN), not
    # a topdeck-dependent one, and must count as credible win pressure.
    state = _minimal_state(hand=["Combo Piece B"])
    state.nonland_perms.append(Perm("Combo Piece A", 1, is_creature=True))
    state.lands = []
    m = snapshot_metrics(state, FAKE_CARDS, [FAKE_COMBO])
    assert m["combo_status"]["TEST-0001"] == "one_mana_step_from_win"
    assert m["one_mana_step_from_win"] is True
    assert m["one_action_from_verified_win"] is True


# ---- 4. attack eligibility respects summoning sickness ----
def test_tymna_attack_capacity_excludes_same_turn_creatures():
    import trajectory_metrics as tm
    state = _minimal_state(turn=3)
    state.nonland_perms.append(Perm("Tymna the Weaver", 3, is_creature=True))  # cast THIS turn
    result = tm.tymna_attack_capacity(state, FAKE_CARDS, cast_turn=3)
    assert result["tymna_deployed"] is True
    assert result["tymna_creatures_able_to_attack"] == 0, "a same-turn Tymna has summoning sickness"
    assert result["tymna_attack_capacity_tier"] == "attack_capacity_low"

    state.nonland_perms.append(Perm("Grizzly Bears", 2, is_creature=True))  # cast last turn
    result2 = tm.tymna_attack_capacity(state, FAKE_CARDS, cast_turn=3)
    assert result2["tymna_creatures_able_to_attack"] == 1, "an older creature is not summoning sick"


def test_attack_eligible_creature_count_matches_creature_count_only_for_non_sick():
    state = _minimal_state(turn=3)
    state.nonland_perms.append(Perm("Tymna the Weaver", 3, is_creature=True))
    state.nonland_perms.append(Perm("Grizzly Bears", 3, is_creature=True))  # also cast this turn
    assert state.creature_count() == 2
    assert state.attack_eligible_creature_count() == 0
    state.nonland_perms.append(Perm("Birds of Paradise", 1, is_creature=True))  # older
    assert state.creature_count() == 3
    assert state.attack_eligible_creature_count() == 1


# ---- 5. mana capacity vs. leftover vs. shortfall ----
def test_total_mana_reports_capacity_not_leftover_after_spending():
    # Turn's starting capacity was 4, but by the time snapshot_metrics runs, 3 of it has already
    # been spent (only 1 untapped land remains) - total_mana must still read 4 (capacity), and
    # the old leftover value must be preserved separately, not silently dropped.
    state = _minimal_state(hand=[])
    state.lands = [LandInPlay("Bayou", 0, tapped=True), LandInPlay("Bayou", 0, tapped=True),
                   LandInPlay("Bayou", 0, tapped=True), LandInPlay("Bayou", 0)]
    state.turn_start_mana = 4
    state.turn_start_colors = {"G"}
    m = snapshot_metrics(state, FAKE_CARDS, [])
    assert m["total_mana"] == 4, "total_mana must reflect starting CAPACITY, not what's left untapped"
    assert m["mana_remaining_unused"] == 1, "the old leftover semantic must survive under its own name"


def test_mana_shortfall_true_when_desirable_card_uncastable_at_full_capacity():
    # Rhystic Study ({2}{U}) in hand, but this turn's FULL capacity is only 1 generic mana - even
    # spending the whole turn on nothing else, Rhystic Study could not have been cast.
    state = _minimal_state(hand=["Rhystic Study"])
    state.lands = [LandInPlay("Command Tower", 0)]
    state.turn_start_mana = 1
    state.turn_start_colors = set()
    m = snapshot_metrics(state, FAKE_CARDS, [])
    assert m["mana_shortfall"] is True


def test_mana_shortfall_false_when_hand_merely_spent_its_mana_elsewhere():
    # Turn capacity was 3 (enough for Rhystic Study's {2}{U}), even though nothing is untapped by
    # the time this snapshot runs - utilization, not shortfall.
    state = _minimal_state(hand=["Rhystic Study"])
    state.lands = [LandInPlay("Bayou", 0, tapped=True), LandInPlay("Command Tower", 0, tapped=True)]
    state.turn_start_mana = 3
    state.turn_start_colors = {"G", "U"}
    m = snapshot_metrics(state, FAKE_CARDS, [])
    assert m["mana_shortfall"] is False, "spending mana on something else this turn is not a shortfall"


def test_mana_shortfall_ignores_uncastable_command_zone_commanders():
    # An empty hand with only the two structurally-always-present partner commanders sitting in
    # the command zone (neither castable with 0 mana of any color) must NOT register as a mana
    # shortfall - that would fire on nearly every early hand simply because it hasn't assembled
    # all four commander colors yet, which is normal and not a bottleneck finding. Commander
    # affordability is tracked separately via the dedicated `{name}_castable` fields.
    state = _minimal_state(hand=[])
    state.turn_start_mana = 0
    state.turn_start_colors = set()
    m = snapshot_metrics(state, FAKE_CARDS, [])
    assert m["mana_shortfall"] is False
    assert m["Tymna the Weaver_castable"] is False
    assert m["Thrasios, Triton Hero_castable"] is False
