"""SIM-001 MULL-005 — trajectory tier grading (S/A/B/C/D/F) + mechanism tagging regression tests.

Each test uses a small synthetic FAKE_CARDS deck with tightly controlled color access (real-deck
lands like Command Tower or fetchlands were found to confound these tests by accidentally enabling
Tymna/Thrasios, which outranks "engine"/"tutor" in DEFAULT_PRIORITY and hijacks the greedy line
before the mechanism under test can be observed - see trajectory_search.py's own docstring for the
same rationale). Where a test needs to isolate an engine/dork mechanism from that commander
priority confound, it passes an explicit priority_order with "engine" ahead of "commander" - this
is legitimate for unit-testing grade_trajectory's classification of an already-simulated line, even
though trajectory_search.py itself only ever searches DEFAULT_PRIORITY/TUTOR_FIRST_PRIORITY.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import random  # noqa: E402

from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from trajectory_grading import grade_trajectory  # noqa: E402

FAKE_CARDS = {
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Tropical Island": {"name": "Tropical Island", "type": "Land — Island Forest", "mana_cost": "", "cmc": 0},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Birds of Paradise": {"name": "Birds of Paradise", "type": "Creature — Bird", "mana_cost": "{G}", "cmc": 1},
    "Vampiric Tutor": {"name": "Vampiric Tutor", "type": "Instant", "mana_cost": "{B}", "cmc": 1},
    "Demonic Tutor": {"name": "Demonic Tutor", "type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2},
    "Mystic Remora": {"name": "Mystic Remora", "type": "Enchantment", "mana_cost": "{U}", "cmc": 1},
    "Rhystic Study": {"name": "Rhystic Study", "type": "Enchantment", "mana_cost": "{2}{U}", "cmc": 3},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
    "Filler1": {"name": "Filler1", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
    "Filler2": {"name": "Filler2", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
    "Filler3": {"name": "Filler3", "type": "Instant", "mana_cost": "{1}", "cmc": 1},
}

ENGINE_FIRST_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "engine", "commander", "tutor", "interaction"]


def _sim_with_snapshots(hand, library, priority_order=DEFAULT_PRIORITY, forced_tutor_target=None, turns=3):
    state = HandState(list(hand), list(library), on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    snaps = {}
    for t in range(1, turns + 1):
        develop_turn(state, FAKE_CARDS, priority_order=priority_order, forced_tutor_target=forced_tutor_target)
        snaps[t] = snapshot_metrics(state, FAKE_CARDS, [])
    return state, snaps[1], snaps[2], snaps[3]


def test_tier_s_premium_one_drop_cast_t1():
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Mystic Remora", "Underground Sea", "Filler1"],
        library=["Filler Land"] * 20,
    )
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "S", g
    assert g["tier_engine"] == "Mystic Remora"
    assert g["tier_turn"] == 1


def test_tier_a_rock_to_engine():
    # Sol Ring T1 -> Rhystic Study T2, on U/B-only mana so no commander can compete for priority.
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Sol Ring", "Rhystic Study", "Underground Sea", "Underground Sea"],
        library=["Filler Land"] * 20,
    )
    assert state.cast_log == [(1, "Sol Ring", "paid_accel"), (2, "Rhystic Study", "engine")]
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "A", g
    assert g["tier_engine"] == "Rhystic Study"
    assert g["tier_turn"] == 2
    assert g["mechanism"] == "rock_to_engine"


def test_tier_a_dork_to_engine_summoning_sick_t1_creature_still_counts():
    # MULL-005 correction (B): a summoning-sick T1 dork enabling a T2 engine IS a premium (Tier A)
    # trajectory - must not be undervalued merely because the creature couldn't tap T1.
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Birds of Paradise", "Rhystic Study", "Tropical Island", "Underground Sea"],
        library=["Filler Land"] * 20,
        priority_order=ENGINE_FIRST_PRIORITY,
    )
    assert state.cast_log[:2] == [(1, "Birds of Paradise", "paid_accel"), (2, "Rhystic Study", "engine")]
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "A", g
    assert g["tier_engine"] == "Rhystic Study"
    assert g["tier_turn"] == 2
    assert g["mechanism"] == "dork_to_engine"


def test_tier_a_pure_tutor_to_engine_no_accel_contamination():
    # Vampiric Tutor (CMC1) T1 fetches Mystic Remora (CMC1), cast T2 - reaches Tier A with NO
    # acceleration involved, so mechanism must read as plain "tutor_to_engine", not
    # "tutor_plus_accel_to_engine".
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Vampiric Tutor", "Underground Sea", "Underground Sea"],
        library=["Mystic Remora"] + ["Filler Land"] * 19,
        forced_tutor_target="Mystic Remora",
    )
    assert state.cast_log == [(1, "Vampiric Tutor", "tutor"), (2, "Mystic Remora", "premium_engine")]
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "A", g
    assert g["tier_engine"] == "Mystic Remora"
    assert g["tier_turn"] == 2
    assert g["mechanism"] == "tutor_to_engine"


def test_tier_c_tutor_engine_arriving_t3_is_not_tier_a():
    # Demonic Tutor (CMC2) needs T2's mana just to resolve; the fetched Rhystic Study (CMC3) can't
    # also be hard-cast that same turn without further ramp, so it lands T3 - correctly Tier C
    # ("only arrives T3"), not Tier A. Confirms the tier boundary is honest about WHEN the engine
    # actually came online, not merely that a tutor+engine chain eventually happened.
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Demonic Tutor", "Sol Ring", "Underground Sea", "Underground Sea"],
        library=["Rhystic Study"] + ["Filler Land"] * 19,
        priority_order=["free_accel", "paid_accel", "premium_engine", "tutor", "commander", "engine", "interaction"],
        forced_tutor_target="Rhystic Study",
    )
    assert state.cast_log == [
        (1, "Sol Ring", "paid_accel"), (2, "Demonic Tutor", "tutor"), (3, "Rhystic Study", "engine"),
    ]
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "C", g
    assert g["tier_engine"] == "Rhystic Study"
    assert g["tier_turn"] == 3
    assert g["mechanism"] == "tutor_plus_accel_to_engine"


def test_tier_d_functional_mana_no_engine():
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Underground Sea", "Underground Sea", "Filler1", "Filler2", "Filler3"],
        library=["Filler Land"] * 20,
    )
    assert state.cast_log == []
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "D", g
    assert g["tier_engine"] is None
    assert g["mechanism"] == "none"


def test_tier_f_mana_failure():
    state, m1, m2, m3 = _sim_with_snapshots(
        hand=["Filler1", "Filler2", "Filler3"],
        library=["Filler Land"] * 20,
    )
    assert state.hand == ["Filler1", "Filler2", "Filler3"], "no lands to draw into within 3 turns from this library"
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "F", g
    assert g["tier_engine"] is None
