"""SIM-001 MULL-005 — primer table generation sanity checks."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_mull005_primer_tables import build_quick_reference_table, build_pod_guidance_table  # noqa: E402
from pod_archetypes import ARCHETYPES  # noqa: E402


def test_quick_reference_table_covers_every_size_speed_tier_combo():
    rows = build_quick_reference_table()
    sizes = {r["hand_size"] for r in rows}
    speeds = {r["pod_speed"] for r in rows}
    tiers = {r["trajectory_tier"] for r in rows}
    assert sizes == {7, 6, 5, 4}
    assert speeds == {"FAST", "MEDIUM", "SLOW"}
    assert len(tiers) == 6
    assert len(rows) == 4 * 3 * 6


def test_quick_reference_table_tier_s_always_keeps():
    rows = build_quick_reference_table()
    for r in rows:
        if r["trajectory_tier"] == "S":
            assert r["category"] == "KEEP", r


def test_quick_reference_table_tier_f_never_keeps():
    rows = build_quick_reference_table()
    for r in rows:
        if r["trajectory_tier"] == "F":
            assert r["category"] == "SHIP", r


def test_fast_pods_only_keep_early_tiers():
    rows = build_quick_reference_table()
    for r in rows:
        if r["pod_speed"] == "FAST" and r["category"] == "KEEP":
            assert r["trajectory_tier"] in ("S", "A"), r


def test_pod_guidance_table_has_no_percentage_signs():
    rows = build_pod_guidance_table()
    assert len(rows) == len(ARCHETYPES)
    for r in rows:
        for text in r["gains_value"] + r["loses_value"] + [r["mulligan_pressure"]]:
            assert "%" not in text, (r["archetype"], text)


def test_pod_guidance_table_confidence_is_never_simulated():
    rows = build_pod_guidance_table()
    for r in rows:
        assert "STRATEGIC_PRIOR_UNVALIDATED" in r["confidence"]
