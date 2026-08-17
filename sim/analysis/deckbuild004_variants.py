"""SIM-DECKBUILD-004 — B0-B7 deck variant definitions.

REACTIVE_SLOT resolves to Commandeer per phase_0's completed screen
(results/solo_baseline/deckbuild004_phase0_reactive_screen.json: Commandeer is the clear,
>1pp-margin least-damaging cut). Every B4-B7 ablation "reverts" exactly ONE of B3's four
ADDITIONS while keeping all four REMOVALS - a deliberate, disclosed 97-card asymmetry (isolates
one card's marginal contribution to the full package, holding everything else fixed), not an
error - matching this project's established MANA-AUDIT-002 precedent for controlled isolation
via an intentional deck-size float.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from mana_audit002_variants import build_variant  # noqa: E402
from deckbuild004_cards import all_cards_dict  # noqa: E402

REACTIVE_SLOT = "Commandeer"

ENGINE_PACKAGE_REMOVE = ["Heartwood Storyteller", "King T'Challa // Black Panther, Hope Enduring"]
ENGINE_PACKAGE_ADD = ["Talion, the Kindly Lord", "Seedborn Muse"]
CONVERSION_PACKAGE_REMOVE = ["Elves of Deep Shadow", REACTIVE_SLOT]
CONVERSION_PACKAGE_ADD = ["Neoform", "Formidable Speaker"]

VARIANTS = {
    "B0_BASELINE": {"add": [], "remove": [], "deck_size": 98, "desc": "Exact current 98."},
    "B1_ENGINE_SWAP": {
        "add": ENGINE_PACKAGE_ADD, "remove": ENGINE_PACKAGE_REMOVE, "deck_size": 98,
        "desc": "-Heartwood Storyteller/King T'Challa, +Talion/Seedborn Muse.",
    },
    "B2_CONVERSION_SWAP": {
        "add": CONVERSION_PACKAGE_ADD, "remove": CONVERSION_PACKAGE_REMOVE, "deck_size": 98,
        "desc": f"-Elves of Deep Shadow/{REACTIVE_SLOT}, +Neoform/Formidable Speaker.",
    },
    "B3_FULL_PACKAGE": {
        "add": ENGINE_PACKAGE_ADD + CONVERSION_PACKAGE_ADD,
        "remove": ENGINE_PACKAGE_REMOVE + CONVERSION_PACKAGE_REMOVE,
        "deck_size": 98, "desc": "All four removals + all four additions.",
    },
    "B4_NO_NEOFORM": {
        "add": [c for c in ENGINE_PACKAGE_ADD + CONVERSION_PACKAGE_ADD if c != "Neoform"],
        "remove": ENGINE_PACKAGE_REMOVE + CONVERSION_PACKAGE_REMOVE,
        "deck_size": 97, "desc": "B3 minus Neoform's addition only (all 4 removals kept).",
    },
    "B5_NO_SPEAKER": {
        "add": [c for c in ENGINE_PACKAGE_ADD + CONVERSION_PACKAGE_ADD if c != "Formidable Speaker"],
        "remove": ENGINE_PACKAGE_REMOVE + CONVERSION_PACKAGE_REMOVE,
        "deck_size": 97, "desc": "B3 minus Formidable Speaker's addition only.",
    },
    "B6_NO_TALION": {
        "add": [c for c in ENGINE_PACKAGE_ADD + CONVERSION_PACKAGE_ADD if c != "Talion, the Kindly Lord"],
        "remove": ENGINE_PACKAGE_REMOVE + CONVERSION_PACKAGE_REMOVE,
        "deck_size": 97, "desc": "B3 minus Talion's addition only.",
    },
    "B7_NO_SEEDBORN": {
        "add": [c for c in ENGINE_PACKAGE_ADD + CONVERSION_PACKAGE_ADD if c != "Seedborn Muse"],
        "remove": ENGINE_PACKAGE_REMOVE + CONVERSION_PACKAGE_REMOVE,
        "deck_size": 97, "desc": "B3 minus Seedborn Muse's addition only.",
    },
    # E1's special_comparison: SIX_DORKS_VS_FIVE, changes_only (remove Elves, add Neoform) - NOT
    # part of the B0-B7 factorial/ablation set, a standalone isolated comparison.
    "SIX_DORKS_VS_FIVE": {
        "add": ["Neoform"], "remove": ["Elves of Deep Shadow"], "deck_size": 98,
        "desc": "Isolated: -Elves of Deep Shadow, +Neoform only (E1 special_comparison).",
    },
}


def build(base_names, cards_pool, variant_name):
    spec = VARIANTS[variant_name]
    names = build_variant(base_names, cards_pool, add=spec["add"], remove=spec["remove"])
    assert len(names) == spec["deck_size"], (variant_name, len(names), spec["deck_size"])
    return names
