"""SIM-ROGFARM-001 Stage 2 — regression tests for rogfarm001_cards.py's remaining mechanics:
Daze's alt cost, the ritual helpers, deck-scoped COMMANDERS/Arcane Signet installation, and
Simian Spirit Guide's hand-virtual mana source.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import rogfarm001_cards as rc  # noqa: E402
import opening_hand_model as ohm  # noqa: E402
from opening_hand_policy import HandState, LandInPlay  # noqa: E402

BASE_CARDS = {
    "Underground Sea": {"type": "Land — Island Swamp", "mana_cost": "", "cmc": 0, "text": ""},
    "Badlands": {"type": "Land — Swamp Mountain", "mana_cost": "", "cmc": 0, "text": ""},
    "Lightning Bolt": {"type": "Instant", "mana_cost": "{R}", "cmc": 1, "text": ""},
}
CARDS = rc.all_cards_dict(BASE_CARDS)


def _state(hand):
    rng = random.Random(0)
    state = HandState(list(hand), [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 2
    return state


def setup_module(_module):
    rc.install_new_card_tables(commander_names=["Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"])


def teardown_module(_module):
    rc.uninstall_new_card_tables()


def test_commander_scoping_excludes_other_decks_commanders():
    assert set(ohm.COMMANDERS.keys()) == {"Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"}
    assert "Tymna the Weaver" not in ohm.COMMANDERS
    assert "Kraum, Ludevic's Opus" not in ohm.COMMANDERS


def test_uninstall_restores_original_commanders():
    rc.uninstall_new_card_tables()
    assert "Tymna the Weaver" in ohm.COMMANDERS
    assert "Rograkh, Son of Rohgahh" not in ohm.COMMANDERS
    rc.install_new_card_tables(commander_names=["Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"])


def test_arcane_signet_grixis_colors_for_rogsi():
    assert ohm.MANA_SOURCES["Arcane Signet"]["colors"] == {"U", "B", "R"}


def test_command_zone_uses_scoped_commanders_not_stale_module_binding():
    # Regression for a real bug caught by the Stage 2 harness's own smoke test: HandState's
    # command_zone comes from opening_hand_policy.py's own "from opening_hand_model import
    # COMMANDERS" binding, not a fresh module-attribute lookup - reassigning ohm.COMMANDERS to a
    # brand new dict object (rather than mutating the existing one in place) left that binding
    # pointing at the OLD dict, so a RogSi simulation's command_zone silently still contained
    # Tymna the Weaver/Thrasios, Triton Hero after "install" claimed to scope it to Rograkh/Silas.
    state = _state([])
    assert state.command_zone == {"Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"}
    assert "Tymna the Weaver" not in state.command_zone


def test_interaction_dispatch_patch_visible_through_snapshot_metrics():
    # Regression for the same class of stale-binding bug: opening_hand_metrics.py imported
    # interaction_is_live directly at ITS OWN import time, so patching only
    # interaction_model.interaction_is_live never reached snapshot_metrics()'s actual call site -
    # Foil/Daze's alt costs were silently invisible to every real simulation despite passing in
    # isolation. Verifies Foil's alt cost is correctly detected THROUGH the real call path.
    from opening_hand_metrics import snapshot_metrics
    state = _state(["Foil", "Underground Sea", "Lightning Bolt"])
    state.turn = 2
    snap = snapshot_metrics(state, CARDS, [])
    assert "Foil" in snap["live_interaction"]


def test_daze_hardcast_with_mana():
    state = _state(["Daze"])
    state.lands.append(LandInPlay("Underground Sea", 1, tapped=False))
    state.lands.append(LandInPlay("Badlands", 1, tapped=False))
    resolution = rc._daze_resolve(state, CARDS)
    assert resolution is not None
    assert resolution[0] == "mana"


def test_daze_alt_cost_requires_island_land_on_battlefield_not_hand():
    state = _state(["Daze", "Underground Sea"])  # Island-type land in HAND, not battlefield
    assert rc.daze_alt_cost_available(state, CARDS) is False
    state.lands.append(LandInPlay("Underground Sea", 1, tapped=False))
    assert rc.daze_alt_cost_available(state, CARDS) is True


def test_daze_alt_cost_bounces_the_island_not_discards_it():
    state = _state(["Daze"])
    land = LandInPlay("Underground Sea", 1, tapped=False)
    state.lands.append(land)
    resolution = rc._daze_resolve(state, CARDS)
    assert resolution == ("return_island", land)
    rc._daze_commit("Daze", resolution, state)
    assert land not in state.lands
    assert "Underground Sea" not in state.graveyard  # bounced to hand, not discarded


def test_daze_tapped_island_does_not_satisfy_alt_cost():
    state = _state(["Daze"])
    state.lands.append(LandInPlay("Underground Sea", 1, tapped=True))
    assert rc.daze_alt_cost_available(state, CARDS) is False


def test_cabal_ritual_flat_rate_below_threshold():
    state = _state(["Cabal Ritual"])
    state.lands.append(LandInPlay("Badlands", 1, tapped=False))
    state.lands.append(LandInPlay("Underground Sea", 1, tapped=False))
    assert len(state.graveyard) < 7
    ok = rc.try_cast_cabal_ritual(state, CARDS)
    assert ok is True
    residue = [p for p in state.nonland_perms if p.name == "Cabal Ritual Residue"]
    assert len(residue) == 3


def test_cabal_ritual_threshold_at_seven_graveyard_cards():
    state = _state(["Cabal Ritual"])
    state.lands.append(LandInPlay("Badlands", 1, tapped=False))
    state.lands.append(LandInPlay("Underground Sea", 1, tapped=False))
    state.graveyard.extend(["a", "b", "c", "d", "e", "f", "g"])
    ok = rc.try_cast_cabal_ritual(state, CARDS)
    assert ok is True
    residue = [p for p in state.nonland_perms if p.name == "Cabal Ritual Residue"]
    assert len(residue) == 5


def test_rite_of_flame_net_plus_one():
    state = _state(["Rite of Flame"])
    state.lands.append(LandInPlay("Badlands", 1, tapped=False))
    ok = rc.try_cast_rite_of_flame(state, CARDS)
    assert ok is True
    residue = [p for p in state.nonland_perms if p.name == "Rite of Flame Residue"]
    assert len(residue) == 2


def test_ritual_residue_swept_at_end_of_turn_if_unused():
    state = _state(["Rite of Flame"])
    state.lands.append(LandInPlay("Badlands", 1, tapped=False))
    rc.try_cast_rite_of_flame(state, CARDS)
    stranded = rc.sweep_stranded_ritual_residue(state, state.turn)
    assert stranded == 2
    assert not any(p.name == "Rite of Flame Residue" for p in state.nonland_perms)


def test_simian_spirit_guide_hand_virtual_mana_source():
    state = _state([rc.SIMIAN_SPIRIT_GUIDE_NAME])
    sources = state.available_sources()
    virtual = [s for s in sources if s[0] == "__ssg_virtual__"]
    assert len(virtual) == 1
    assert virtual[0][1] == {"R"}
    assert virtual[0][2] == 1


def test_simian_spirit_guide_absent_when_not_in_hand():
    state = _state(["Daze"])
    sources = state.available_sources()
    assert not any(s[0] == "__ssg_virtual__" for s in sources)
