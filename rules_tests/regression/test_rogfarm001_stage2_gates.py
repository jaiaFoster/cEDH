"""SIM-ROGFARM-001 Stage 2 — regression tests for the 5 Section 9 gate-evaluation formulas
(build_rogfarm001_stage2_gates.py), using synthetic aggregate dicts so the exact threshold math
is verified independent of any real Monte Carlo run."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_rogfarm001_stage2_gates import evaluate_gates  # noqa: E402


def _agg(**overrides):
    base = {
        "protected_engine_online_by_t2": 0.10, "engine_online_by_t2": 0.30,
        "has_live_interaction_t3": 0.10, "identity_card_stranded_rate": None,
        "meaningful_mana_failure_rate": 0.03, "protected_asymmetric_wheel_by_t3": 0.15,
    }
    base.update(overrides)
    return base


def _decks(r1, stock, blue):
    return {
        "R1_ROG_FARM": {"policies": {"P1": r1}},
        "STOCK_ROGSI": {"policies": {"P1": stock}},
        "BLUE_FARM": {"policies": {"P1": blue}},
    }


def test_engine_advantage_path_a_protected_engine_7pp():
    decks = _decks(
        r1=_agg(protected_engine_online_by_t2=0.20),
        stock=_agg(),
        blue=_agg(protected_engine_online_by_t2=0.10),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["engine_advantage"]["pass"] is True
    assert result["gates"]["engine_advantage"]["path_a_protected_engine_ge_7pp"] is True


def test_engine_advantage_fails_below_both_thresholds():
    decks = _decks(
        r1=_agg(protected_engine_online_by_t2=0.11, engine_online_by_t2=0.31),
        stock=_agg(),
        blue=_agg(protected_engine_online_by_t2=0.10, engine_online_by_t2=0.30),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["engine_advantage"]["pass"] is False


def test_engine_advantage_path_b_requires_interaction_not_worse():
    # engine delta clears +10pp but interaction is far worse than Blue Farm - path B must fail.
    decks = _decks(
        r1=_agg(engine_online_by_t2=0.45, has_live_interaction_t3=0.02),
        stock=_agg(),
        blue=_agg(engine_online_by_t2=0.30, has_live_interaction_t3=0.15),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["engine_advantage"]["path_b_engine_ge_10pp_and_interaction_not_worse"] is False
    assert result["gates"]["engine_advantage"]["pass"] is False


def test_defensive_retention_fails_when_worse_than_5pp():
    decks = _decks(
        r1=_agg(has_live_interaction_t3=0.03),
        stock=_agg(has_live_interaction_t3=0.10),
        blue=_agg(),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["rogsi_defensive_retention"]["pass"] is False


def test_defensive_retention_passes_within_5pp():
    decks = _decks(
        r1=_agg(has_live_interaction_t3=0.06),
        stock=_agg(has_live_interaction_t3=0.10),
        blue=_agg(),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["rogsi_defensive_retention"]["pass"] is True


def test_conditional_burden_uses_zero_stock_baseline_when_none():
    decks = _decks(
        r1=_agg(identity_card_stranded_rate=0.06),  # 6pp > 4pp threshold vs 0 baseline
        stock=_agg(identity_card_stranded_rate=None),
        blue=_agg(),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["conditional_burden"]["pass"] is False
    assert result["gates"]["conditional_burden"]["identity_stranded_rate_delta_pp"] == 6.0


def test_mana_gate_requires_both_absolute_and_relative_threshold():
    decks = _decks(
        r1=_agg(meaningful_mana_failure_rate=0.06),  # >= 5% absolute -> fails regardless of delta
        stock=_agg(meaningful_mana_failure_rate=0.05),
        blue=_agg(),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["mana"]["pass"] is False


def test_mana_gate_passes_under_both_thresholds():
    decks = _decks(
        r1=_agg(meaningful_mana_failure_rate=0.04),
        stock=_agg(meaningful_mana_failure_rate=0.02),
        blue=_agg(),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["mana"]["pass"] is True


def test_wheel_emergence_threshold_12_percent():
    decks = _decks(
        r1=_agg(protected_asymmetric_wheel_by_t3=0.11),
        stock=_agg(), blue=_agg(),
    )
    assert evaluate_gates(decks, "P1")["gates"]["wheel_emergence"]["pass"] is False
    decks2 = _decks(
        r1=_agg(protected_asymmetric_wheel_by_t3=0.12),
        stock=_agg(), blue=_agg(),
    )
    assert evaluate_gates(decks2, "P1")["gates"]["wheel_emergence"]["pass"] is True


def test_stop_rule_triggers_at_two_failing_gates():
    decks = _decks(
        r1=_agg(has_live_interaction_t3=0.01, meaningful_mana_failure_rate=0.06),
        stock=_agg(has_live_interaction_t3=0.10, meaningful_mana_failure_rate=0.02),
        blue=_agg(),
    )
    result = evaluate_gates(decks, "P1")
    assert result["fail_count"] >= 2
    assert result["stop_rule_triggered"] is True


def test_stop_rule_not_triggered_with_one_failing_gate():
    # Isolate ONLY defensive retention as a failure: R1's protected-engine lead over Blue Farm
    # clears gate 1 via path A regardless of the interaction delta, so only gate 2 fails here.
    decks = _decks(
        r1=_agg(has_live_interaction_t3=0.01, protected_engine_online_by_t2=0.25),
        stock=_agg(has_live_interaction_t3=0.10),
        blue=_agg(protected_engine_online_by_t2=0.10),
    )
    result = evaluate_gates(decks, "P1")
    assert result["gates"]["engine_advantage"]["pass"] is True
    assert result["fail_count"] == 1
    assert result["stop_rule_triggered"] is False
