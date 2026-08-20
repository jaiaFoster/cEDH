"""SIM-DECKBUILD-007 Workstream 2 remainder — Cabbage Merchant scenario + Seedborn Muse checks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sim" / "analysis"))

from build_deckbuild007_ws2_multiplayer_scenarios import (  # noqa: E402
    cabbage_scenarios, seedborn_deterministic_value, OPPONENT_COUNT,
)


def test_cabbage_bands_are_monotonic_and_weaker_than_lotho_typical():
    bands = cabbage_scenarios()
    vals = [bands[b]["expected_mana_from_foods"] for b in
             ("LOW_INTERACTION_POD", "TYPICAL_CEDH_POD", "HIGH_VELOCITY_POD")]
    assert vals == sorted(vals)
    # DECKBUILD-006 E6's Lotho TYPICAL result was 3.6 expected mana over the same T3-T6 span.
    assert bands["TYPICAL_CEDH_POD"]["expected_mana_from_foods"] < 3.6


def test_cabbage_net_foods_never_negative():
    bands = cabbage_scenarios()
    for b in bands.values():
        assert b["expected_net_foods"] >= 0.0


def test_seedborn_value_scales_linearly_with_mana_base_and_opponent_count():
    result = seedborn_deterministic_value([4, 8])
    assert result["8"]["extra_mana_available_before_own_next_turn"] == 2 * result["4"]["extra_mana_available_before_own_next_turn"]
    assert result["4"]["extra_untap_events_before_own_next_turn"] == OPPONENT_COUNT
