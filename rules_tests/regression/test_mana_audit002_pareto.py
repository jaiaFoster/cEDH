"""MANA-AUDIT-002 section G — Pareto axis computation + dominance logic checks."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_mana_audit002_pareto import _speed, _consistency, _resilience_utility, UTILITY_LANDS  # noqa: E402


def _cfg(t1=0.1, t2=0.1, t3=0.1, s_or_a=0.3, d_or_f=0.1, mana_fail=0.05):
    return {
        "primary_outcomes": {"t1_premium_engine": t1, "t2_engine": t2, "t3_2plus_engines": t3},
        "mulligan_gated_model": {"fraction_tier_S_or_A": s_or_a, "fraction_tier_D_or_F": d_or_f},
        "failure_table": {"insufficient_mana": {"pct_of_all_hands": mana_fail}},
    }


def test_speed_is_mean_of_three_components():
    speed, parts = _speed(_cfg(t1=0.2, t2=0.4, t3=0.6))
    assert abs(speed - 0.4) < 1e-9
    assert parts["t1_premium_engine"] == 0.2


def test_consistency_penalizes_failure_and_ships():
    c1, _ = _consistency(_cfg(s_or_a=0.5, d_or_f=0.0, mana_fail=0.0))
    c2, _ = _consistency(_cfg(s_or_a=0.5, d_or_f=0.3, mana_fail=0.2))
    assert c1 > c2


def test_resilience_drops_when_utility_land_removed():
    r_full, _ = _resilience_utility({"added_cards": []}, removed_by_config=[])
    r_ablated, _ = _resilience_utility({"added_cards": []}, removed_by_config=["Boseiju, Who Endures"])
    assert r_ablated < r_full


def test_resilience_rewards_extra_fetch():
    r_base, parts_base = _resilience_utility({"added_cards": []}, removed_by_config=[])
    r_more, parts_more = _resilience_utility({"added_cards": ["Scalding Tarn"]}, removed_by_config=[])
    assert parts_more["fetch_count_now"] == parts_base["fetch_count_now"] + 1
    assert r_more >= r_base
