"""SIM-ROGFARM-001 — loads the three frozen decks (rogsi-valley-forge-2026-v1,
rogfarm-r1-minimal-v1, bluefarm-control-2026-v1) into (commanders, mainboard_names, cards_dict)
tuples ready for HandState-based simulation. Verifies deck_hash on every load (fail loudly on
tamper/edit, matching the assignment's own hash_policy)."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402
import rogfarm001_cards as rc  # noqa: E402

DECKLISTS = REPO_ROOT / "data" / "decklists"
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"

DECK_VERSIONS = {
    "STOCK_ROGSI": "rogsi-valley-forge-2026-v1",
    "R1_ROG_FARM": "rogfarm-r1-minimal-v1",
    "BLUE_FARM": "bluefarm-control-2026-v1",
}


def _cache_by_scryfall_id():
    by_id = {}
    for p in CARDS_CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        by_id[d["scryfall_id"]] = d
    return by_id


def _row_from_cache_card(name, cache_entry):
    return {
        "name": name, "type": cache_entry.get("type_line", ""),
        "text": cache_entry.get("oracle_text", "") or "",
        "mana_cost": cache_entry.get("mana_cost") or "", "cmc": cache_entry.get("mana_value") or 0,
    }


def load_rogfarm001_deck(label):
    """label: one of DECK_VERSIONS' keys. Returns (payload, commanders, mainboard_names, cards)."""
    version = DECK_VERSIONS[label]
    payload = json.loads((DECKLISTS / f"{version}.json").read_text(encoding="utf-8"))
    recomputed = compute_deck_hash(payload["commanders"], payload["cards"])
    if recomputed != payload["deck_hash"]:
        raise ValueError(
            f"{version}: stored deck_hash={payload['deck_hash']} does not match recomputed "
            f"hash={recomputed} - file was edited after freezing or tampered with."
        )
    cache = _cache_by_scryfall_id()
    synthetic_names = set(payload["ingested"]["synthetic_card_names"])
    all_new = rc.all_cards_dict({})
    rows = {}
    for c in payload["cards"]:
        name = c["name"]
        if name in synthetic_names:
            card = all_new[name]
            rows[name] = {
                "name": name, "type": card["type"], "text": card.get("text", ""),
                "mana_cost": card.get("mana_cost", ""), "cmc": card.get("cmc", 0),
            }
        else:
            rows[name] = _row_from_cache_card(name, cache[c["scryfall_id"]])
    mainboard_names = [c["name"] for c in payload["cards"]]
    return payload, payload["commanders"], mainboard_names, rows
