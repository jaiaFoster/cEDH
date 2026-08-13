"""SIM-001 MULL-005R — Devoted Druid's real 2-mana/turn ceiling (t1_t3_trajectory_audit.json
DORK-001). Real Oracle text: '{T}: Add {G}.' + 'Put a -1/-1 counter on this creature: Untap this
creature.' The second ability has no tap symbol, so once no longer summoning sick, Druid can tap
for G, self-untap, and tap again for a second G in the same turn.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, Perm  # noqa: E402

FAKE_CARDS = {
    "Devoted Druid": {"name": "Devoted Druid", "type": "Creature — Elf Druid", "mana_cost": "{1}{G}", "cmc": 2},
}


def test_devoted_druid_produces_zero_mana_while_summoning_sick():
    state = HandState([], [], on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 1
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))
    assert state.total_mana_value() == 0


def test_devoted_druid_produces_two_mana_once_not_summoning_sick():
    state = HandState([], [], on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 2
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))  # entered T1, now T2
    assert state.total_mana_value() == 2
    sources = state.available_sources()
    assert sources[0][1] == {"G"}
    assert sources[0][2] == 2


def test_devoted_druid_two_mana_is_actually_payable_not_just_counted():
    from opening_hand_policy import _try_pay
    from opening_hand_model import parse_cost

    state = HandState([], [], on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 2
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))
    gen, pips, x = parse_cost("{G}{G}")
    plan = _try_pay(state, gen, pips)
    assert plan is not None
