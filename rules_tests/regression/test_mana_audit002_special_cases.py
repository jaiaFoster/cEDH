"""MANA-AUDIT-002 section B — gold-state checks for the two findings this task made to the
shared mana model: Talon Gates of Madara's colorless-only guaranteed output (was incorrectly a
flat free WUBG source), and the confirmation that Deathrite Shaman's mana ability is structurally
dead in this exact 98-card list (zero real basic land cards anywhere for it to exile).
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, GENERIC_LANDS, LAND_COLOR_SETS  # noqa: E402
from opening_hand_policy import HandState  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()


def test_talon_gates_no_longer_a_flat_rainbow_source():
    assert "Talon Gates of Madara" not in LAND_COLOR_SETS


def test_talon_gates_is_a_guaranteed_generic_one_source():
    assert GENERIC_LANDS["Talon Gates of Madara"] == 1


def test_talon_gates_available_sources_reports_generic_only():
    rng = random.Random(0)
    state = HandState(["Talon Gates of Madara"], [], on_play=True, rng=rng, cards=CARDS)
    state.turn = 1
    from opening_hand_policy import LandInPlay
    state.lands.append(LandInPlay("Talon Gates of Madara", 1, tapped=False))
    sources = state.available_sources()
    assert len(sources) == 1
    ref, colors, count = sources[0]
    assert colors is None  # generic-only, not a color set
    assert count == 1


def test_deathrite_shaman_absent_from_mana_sources():
    from opening_hand_model import MANA_SOURCES
    assert "Deathrite Shaman" not in MANA_SOURCES


def test_cmc_field_now_populates_from_real_card_data():
    """MANA-AUDIT-002 found load_deck_cards() reading a nonexistent 'cmc' cache key (the real
    field is 'mana_value'), so every card's parsed cmc was silently 0. Confirms the fix."""
    assert CARDS["Force of Will"]["cmc"] == 5
    assert CARDS["Smothering Tithe"]["cmc"] == 4
    assert CARDS["Sol Ring"]["cmc"] == 1
    assert CARDS["Birthing Pod"]["cmc"] == 4


def test_deck_has_zero_basic_land_cards():
    """Confirms the premise behind treating Deathrite as a non-mana-source in this exact list:
    its mana ability requires exiling a BASIC LAND CARD from a graveyard, and this list has none."""
    import json
    import glob
    cache = {}
    for p in glob.glob(str(REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12" / "*.json")):
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        cache[d["scryfall_id"]] = d
    basics = [
        cache[c["scryfall_id"]]["name"] for c in _PAYLOAD["cards"]
        if "Basic" in cache[c["scryfall_id"]].get("type_line", "")
    ]
    assert basics == []
