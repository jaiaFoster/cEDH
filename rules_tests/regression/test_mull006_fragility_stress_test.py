"""SIM-001 MULL-006 section 20 — fragility stress test on named trajectory families.

Proves the family matchers correctly identify each of the assignment's 13 named trajectory
families from grade_trajectory()'s own (tier_engine, tier_turn, mechanism) fields, using
constructed grade dicts rather than requiring a real search to happen to land each rare family.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_fragility_stress_test import _family_matchers  # noqa: E402
from opening_hand_policy import OCULUS_NAME  # noqa: E402


class _FakeState:
    def __init__(self, cast_log=None):
        self.cast_log = cast_log or []


def _grade(tier_engine, tier_turn, mechanism="natural_engine"):
    return {"tier_engine": tier_engine, "tier_turn": tier_turn, "mechanism": mechanism, "tier": "A"}


def test_t1_families_match_exact_turn_only():
    m = _family_matchers()
    assert m["T1 Remora"](_grade("Mystic Remora", 1), _FakeState())
    assert not m["T1 Remora"](_grade("Mystic Remora", 2), _FakeState())
    assert m["T1 Sentinel"](_grade("Esper Sentinel", 1), _FakeState())
    assert m["T1 Mastermind"](_grade("Faerie Mastermind", 1), _FakeState())
    assert m["T1 Archivist"](_grade("Archivist of Oghma", 1), _FakeState())
    assert m["T1 Rhystic"](_grade("Rhystic Study", 1), _FakeState())
    assert not m["T1 Rhystic"](_grade("Rhystic Study", 2), _FakeState())


def test_t2_families_match_exact_turn_only():
    m = _family_matchers()
    assert m["T2 Rhystic"](_grade("Rhystic Study", 2), _FakeState())
    assert not m["T2 Rhystic"](_grade("Rhystic Study", 1), _FakeState())
    assert m["T2 Tithe"](_grade("Smothering Tithe", 2), _FakeState())
    assert m["T2 functional Pod"](_grade("Birthing Pod", 2), _FakeState())
    assert not m["T2 functional Pod"](_grade("Birthing Pod", 1), _FakeState())


def test_early_oculus_matches_turn_1_or_2_only():
    m = _family_matchers()
    assert m["early Oculus"](_grade(OCULUS_NAME, 1), _FakeState())
    assert m["early Oculus"](_grade(OCULUS_NAME, 2), _FakeState())
    assert not m["early Oculus"](_grade(OCULUS_NAME, 3), _FakeState())


def test_functional_survival_matches_any_turn():
    m = _family_matchers()
    assert m["functional Survival"](_grade("Survival of the Fittest", 1), _FakeState())
    assert m["functional Survival"](_grade("Survival of the Fittest", 3), _FakeState())


def test_tutor_to_engine_matches_mechanism_prefix():
    m = _family_matchers()
    assert m["tutor -> engine"](_grade("Rhystic Study", 2, mechanism="tutor_to_engine"), _FakeState())
    assert m["tutor -> engine"](_grade("Rhystic Study", 2, mechanism="tutor_plus_accel_to_engine"), _FakeState())
    assert not m["tutor -> engine"](_grade("Rhystic Study", 2, mechanism="natural_engine"), _FakeState())


def test_dork_to_engine_matches_mechanism_prefix():
    m = _family_matchers()
    assert m["dork -> engine"](_grade("Rhystic Study", 2, mechanism="dork_to_engine"), _FakeState())
    assert not m["dork -> engine"](_grade("Rhystic Study", 2, mechanism="rock_to_engine"), _FakeState())


def test_mana_vault_to_tithe_requires_mana_vault_actually_cast_before_tier_turn():
    m = _family_matchers()
    grade = _grade("Smothering Tithe", 3, mechanism="rock_to_engine")
    with_vault = _FakeState(cast_log=[(1, "Mana Vault", "paid_accel")])
    without_vault = _FakeState(cast_log=[(1, "Sol Ring", "paid_accel")])
    too_late_vault = _FakeState(cast_log=[(3, "Mana Vault", "paid_accel")])  # cast ON tier_turn, not before
    assert m["Mana Vault -> Tithe"](grade, with_vault)
    assert not m["Mana Vault -> Tithe"](grade, without_vault)
    assert not m["Mana Vault -> Tithe"](grade, too_late_vault)


def test_mana_vault_to_tithe_requires_rock_to_engine_mechanism():
    m = _family_matchers()
    grade = _grade("Smothering Tithe", 3, mechanism="natural_engine")
    state = _FakeState(cast_log=[(1, "Mana Vault", "paid_accel")])
    assert not m["Mana Vault -> Tithe"](grade, state)


def test_all_thirteen_named_families_are_present():
    m = _family_matchers()
    expected = {
        "T1 Remora", "T1 Sentinel", "T1 Mastermind", "T1 Archivist", "T1 Rhystic",
        "T2 Rhystic", "T2 Tithe", "T2 functional Pod", "early Oculus", "functional Survival",
        "tutor -> engine", "Mana Vault -> Tithe", "dork -> engine",
    }
    assert set(m) == expected
