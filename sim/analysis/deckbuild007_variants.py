"""SIM-DECKBUILD-007 — operative-101 loader + variant builder. Same non-strict-loader pattern as
deckbuild006_variants.py (this frozen file has 4 synthetic-scryfall-id cards, so it deliberately
does not pass load_frozen_deck()'s strict cache-resolution check - hash-verifies itself instead).
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402
from mana_audit002_variants import build_variant  # noqa: E402
import deckbuild007_cards  # noqa: E402

DECKBUILD007_DECKLIST_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-deckbuild007-v1.json"
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"


def _cache_by_scryfall_id():
    cache = {}
    for p in CARDS_CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        cache[d["scryfall_id"]] = d
    return cache


def _row_from_cache_card(name, cache_card):
    return {
        "name": name, "type": cache_card.get("type_line", ""),
        "text": cache_card.get("oracle_text", "") or "",
        "mana_cost": cache_card.get("mana_cost") or "", "cmc": cache_card.get("mana_value") or 0,
    }


def load_deckbuild007_cards():
    payload = json.loads(DECKBUILD007_DECKLIST_PATH.read_text(encoding="utf-8"))
    recomputed = compute_deck_hash(payload["commanders"], payload["cards"])
    if recomputed != payload["deck_hash"]:
        raise ValueError(
            f"{DECKBUILD007_DECKLIST_PATH}: stored deck_hash={payload['deck_hash']} does not "
            f"match recomputed hash={recomputed} - file was edited after freezing or tampered with."
        )
    cache = _cache_by_scryfall_id()
    new_card_data = deckbuild007_cards.NEW_CARD_DATA
    rows = {}
    for c in payload["cards"]:
        name = c["name"]
        if name in new_card_data:
            card = new_card_data[name]
            rows[name] = {
                "name": name, "type": card["type"], "text": card.get("text", ""),
                "mana_cost": card.get("mana_cost", ""), "cmc": card.get("cmc", 0),
            }
        else:
            rows[name] = _row_from_cache_card(name, cache[c["scryfall_id"]])
    return payload, rows


def deckbuild007_cards_pool(base_rows):
    """base_rows (the operative 99's own rows) plus comparison-only/bookkeeping cards that are
    never IN the 99 but are needed by this task's analysis scripts: Carpet of Flowers (Workstream
    1 comparator), Dark Ritual Residue (bookkeeping, see deckbuild007_cards.py), and Avacyn's
    Pilgrim / Training Grounds / An Offer You Can't Refuse / Shang-Chi (needed only for the
    'is their absence reasonable' final-judgment checks, pulled from the prior frozen file's real
    cache-verified data, same reuse pattern as deckbuild006_variants.py's Pilgrim handling)."""
    merged = dict(base_rows)
    merged[deckbuild007_cards.CARPET_NAME] = dict(
        deckbuild007_cards.NEW_CARD_DATA[deckbuild007_cards.CARPET_NAME], name=deckbuild007_cards.CARPET_NAME
    )
    merged[deckbuild007_cards.DARK_RITUAL_RESIDUE_NAME] = dict(
        deckbuild007_cards.NEW_CARD_DATA[deckbuild007_cards.DARK_RITUAL_RESIDUE_NAME],
        name=deckbuild007_cards.DARK_RITUAL_RESIDUE_NAME,
    )
    absent_names = ["Avacyn's Pilgrim", "Training Grounds", "An Offer You Can't Refuse", "Shang-Chi, Master of Kung Fu"]
    prev_006 = json.loads((REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-deckbuild006-v1.json").read_text(encoding="utf-8"))
    prev_manaaudit = json.loads((REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-manaaudit002-v1.json").read_text(encoding="utf-8"))
    prev_by_name = {c["name"]: c for c in prev_006["cards"]}
    for c in prev_manaaudit["cards"]:
        prev_by_name.setdefault(c["name"], c)  # Avacyn's Pilgrim: real, was cut before deckbuild006
    cache = _cache_by_scryfall_id()
    new_card_data = deckbuild007_cards.NEW_CARD_DATA  # includes deckbuild006's own new-card data
    for name in absent_names:
        if name in merged:
            continue
        if name in new_card_data:
            card = new_card_data[name]
            merged[name] = {
                "name": name, "type": card["type"], "text": card.get("text", ""),
                "mana_cost": card.get("mana_cost", ""), "cmc": card.get("cmc", 0),
            }
        elif name in prev_by_name:
            merged[name] = _row_from_cache_card(name, cache[prev_by_name[name]["scryfall_id"]])
    return merged


def build(base_names, cards_pool, add=(), remove=()):
    return build_variant(base_names, cards_pool, add=add, remove=remove)
