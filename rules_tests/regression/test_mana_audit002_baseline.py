"""MANA-AUDIT-002 section D — sanity checks for the baseline-metrics build script."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_mana_audit002_baseline import exact_hypergeometric_land_distribution  # noqa: E402


def test_hypergeometric_distribution_sums_to_one():
    dist = exact_hypergeometric_land_distribution(deck_size=98, land_count=27, hand_size=7)
    assert abs(sum(dist.values()) - 1.0) < 1e-9


def test_hypergeometric_distribution_matches_known_mean():
    """Expected lands in a 7-card hand from a 98-card deck with 27 lands: 7 * 27/98."""
    dist = exact_hypergeometric_land_distribution(deck_size=98, land_count=27, hand_size=7)
    mean = sum(k * p for k, p in dist.items())
    assert abs(mean - 7 * 27 / 98) < 1e-9


def test_hypergeometric_zero_lands_case():
    dist = exact_hypergeometric_land_distribution(deck_size=98, land_count=0, hand_size=7)
    assert dist[0] == 1.0
    assert all(dist[k] == 0.0 for k in range(1, 8))
