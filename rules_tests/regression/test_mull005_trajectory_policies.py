"""SIM-001 MULL-005 — TRAJECTORY_SIMPLE / structural_hand_grade regression tests.

Confirms the two explicit MULL-005 corrections are actually encoded in the human-usable policy,
not just in the underlying grading engine: (A) acceleration needs a destination, (B) a T1
creature dork feeding a T2 engine is a real keep.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from trajectory_policies import structural_hand_grade, trajectory_simple_policy  # noqa: E402


def _feats(**overrides):
    base = {
        "has_premium_one_drop_card": False,
        "land_count": 2,
        "t1_accel_executable_now": False,
        "t1_accel_creature_only": False,
        "has_any_engine_card": False,
        "has_tier_a_engine_card": False,
        "interaction_only_hand": False,
        "accel_card_count": 0,
        "distinct_colors_potential": 0,
        "tutor_names": [],
    }
    base.update(overrides)
    return base


def test_premium_one_drop_is_snap_keep():
    grade, _ = structural_hand_grade(_feats(has_premium_one_drop_card=True, land_count=0))
    assert grade == "SNAP_KEEP"
    assert trajectory_simple_policy(_feats(has_premium_one_drop_card=True, land_count=0))


def test_correction_a_two_accel_no_destination_ships():
    # 2+ acceleration, no engine, no cheap tutor, no commander-color access - the exact case
    # mull005_accel_without_payoff_analysis.json found hits Tier D/F 58.8% of the time.
    feats = _feats(accel_card_count=2, land_count=2, distinct_colors_potential=1)
    grade, reason = structural_hand_grade(feats)
    assert grade == "SHIP", (grade, reason)
    assert not trajectory_simple_policy(feats)


def test_correction_a_two_accel_with_engine_destination_keeps():
    feats = _feats(accel_card_count=2, land_count=2, has_any_engine_card=True, distinct_colors_potential=1)
    grade, _ = structural_hand_grade(feats)
    assert grade in ("SNAP_KEEP", "CONDITIONAL_KEEP")
    assert trajectory_simple_policy(feats)


def test_correction_b_creature_dork_to_commander_colors_is_conditional_keep_not_shipped():
    # A T1 creature dork (t1_accel_creature_only=True, can't tap T1) enabling plausible commander
    # colors T2 must NOT be downgraded just because the creature itself is summoning-sick.
    feats = _feats(t1_accel_creature_only=True, land_count=2, distinct_colors_potential=2)
    grade, reason = structural_hand_grade(feats)
    assert grade == "CONDITIONAL_KEEP", (grade, reason)
    assert trajectory_simple_policy(feats)


def test_zero_lands_ships():
    grade, _ = structural_hand_grade(_feats(land_count=0))
    assert grade == "SHIP"


def test_interaction_only_at_2_3_lands_ships():
    feats = _feats(land_count=2, interaction_only_hand=True, distinct_colors_potential=2)
    grade, _ = structural_hand_grade(feats)
    assert grade == "SHIP"


def test_cheap_tutor_at_2_lands_is_conditional_keep():
    feats = _feats(land_count=2, tutor_names=["Vampiric Tutor"])
    grade, _ = structural_hand_grade(feats)
    assert grade == "CONDITIONAL_KEEP"


def test_expensive_tutor_alone_is_not_a_keep_signal():
    # Demonic Tutor (CMC2) is NOT in CHEAP_TUTORS_WITH_REAL_T2_CONVERSION - a bare copy with no
    # other business must not keep the hand on its own.
    feats = _feats(land_count=2, tutor_names=["Demonic Tutor"], distinct_colors_potential=1)
    grade, _ = structural_hand_grade(feats)
    assert grade == "SHIP"
