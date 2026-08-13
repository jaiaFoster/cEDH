"""SIM-001 MULL-005R — Phyrexian mana correctness fix.

Pre-existing bug (inherited unchanged through SOLO-002 - MULL-005): parse_cost() dropped the
life-payment half of any {X/P} Phyrexian mana symbol, forcing color payment even though real
Oracle text allows paying PHYREXIAN_LIFE_COST life instead. This silently undercounted Birthing
Pod's real castability ({3}{G/P} cast cost, {1}{G/P} activation cost) whenever green was
unavailable. True hybrid mana ({B/G}, Deathrite Shaman) has no life-payment option and must NOT
be affected by this fix.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import parse_cost, PhyrexianPip, PHYREXIAN_LIFE_COST  # noqa: E402
from opening_hand_policy import HandState, LandInPlay, _try_pay  # noqa: E402

FAKE_CARDS = {
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
}


def test_phyrexian_pip_parsed_distinctly_from_hybrid():
    gen, pips, x = parse_cost("{3}{G/P}")
    assert isinstance(pips[0], PhyrexianPip)
    assert set(pips[0]) == {"G"}

    gen2, pips2, x2 = parse_cost("{B/G}")
    assert not isinstance(pips2[0], PhyrexianPip)
    assert isinstance(pips2[0], frozenset)
    assert set(pips2[0]) == {"B", "G"}


def test_phyrexian_pip_payable_via_life_when_color_unavailable():
    state = HandState(["Underground Sea"], ["Filler Land"] * 10, on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 1
    state.lands.append(LandInPlay("Underground Sea", 1))  # produces only U or B, never G

    gen, pips, x = parse_cost("{1}{G/P}")  # Birthing Pod's activation cost
    plan = _try_pay(state, gen, pips)
    assert plan is not None, "should be payable via life for the phyrexian half even with zero G sources"
    life_entries = [units for ref, units in plan if ref == "__phyrexian_life__"]
    assert life_entries == [1]


def test_phyrexian_life_payment_actually_deducts_and_rolls_back_life():
    from opening_hand_policy import _commit_payment, _rollback_payment

    state = HandState(["Underground Sea"], ["Filler Land"] * 10, on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 1
    state.lands.append(LandInPlay("Underground Sea", 1))
    start_life = state.life

    gen, pips, x = parse_cost("{1}{G/P}")
    plan = _try_pay(state, gen, pips)
    _commit_payment(state, plan)
    assert state.life == start_life - PHYREXIAN_LIFE_COST

    _rollback_payment(state, [plan])
    assert state.life == start_life


def test_true_hybrid_pip_still_requires_a_real_color_source_no_life_fallback():
    # Deathrite Shaman's {B/G} must still fail outright with zero B/G sources - no life option.
    state = HandState([], ["Filler Land"] * 10, on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 1
    gen, pips, x = parse_cost("{B/G}")
    plan = _try_pay(state, gen, pips)
    assert plan is None
