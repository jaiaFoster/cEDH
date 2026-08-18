"""SIM-DECKBUILD-006 — operative deck loader + A/B/C/D factorial config builder.

Loads the frozen operative subject (tymna-thrasios-treefarm-deckbuild006-v1.json, minted by
build_deckbuild006_frozen_deck.py) directly rather than through
sim.validation.run_classification.load_frozen_deck() — that strict loader requires every card's
scryfall_id to resolve in the real oracle cards_cache, which by design fails for the 9 newly-added
cards (see that script's docstring: this environment cannot fetch real Scryfall data for them).
This module does its own hash-verification instead (recomputes compute_deck_hash() and asserts it
matches the stored value — same tamper/drift protection, just without the cache-resolution
requirement) and sources the 9 new cards' row data from deckbuild006_cards.NEW_CARD_DATA.

Factorial construction (assignment's factorial_core, A/B/C/D):
The operative 98 already contains Lotho, Corrupt Shirriff and does NOT contain Avacyn's Pilgrim
(the swap under study is already "live" in this operative list). Define SHARED_97 = the operative
98 minus Lotho — 97 cards common to every config, containing neither Pilgrim nor Lotho.

  A_5D_NO_LOTHO = SHARED_97 + Avacyn's Pilgrim                      (98, 5 dorks, no Lotho)
  B_4D_NO_LOTHO = SHARED_97 + PLACEHOLDER                            (98, 4 dorks, no Lotho)
  D_4D_LOTHO    = SHARED_97 + Lotho                                  (98, 4 dorks, +Lotho) [= operative]
  C_5D_LOTHO    = SHARED_97 - Mindbreak Trap + Avacyn's Pilgrim + Lotho   (98, 5 dorks, +Lotho)

C needs both Pilgrim AND Lotho present at once, which doesn't fit in 97 shared slots (97 + 2 = 99)
- one real card must be cut to fund it. Per the assignment's explicit instruction ("Do not infer
which real card should be cut"), this funding cut is NOT chosen as a deckbuilding suggestion. It is
"Mindbreak Trap": a free-alternative-cost counterspell whose alt-cost condition (opponent has cast
3+ spells this turn) can never be satisfied in this solo, opponent-free T1-3 engine, and which (like
every INTERACTION_CASTABLE-class card) the generic greedy dev loop essentially never casts anyway in
this horizon even when hard-cast is available. Removing it is, within THIS specific analysis, a real
no-op for every metric measured here — the closest thing to a free funding slot that still uses a
real, already-in-the-decklist card rather than fabricating a second synthetic placeholder. This is
disclosed, not silently chosen, and must not be read as "cut Mindbreak Trap" advice.

PLACEHOLDER is a synthetic, clearly-labeled, never-real card: not a mana source, not a creature (so
it cannot pollute Gaea's Cradle's creature count or any creature-triggered mechanic), not classified
into ENGINES/TUTORS/INTERACTION_CASTABLE/ACCELERATION (so the generic greedy loop never casts it) -
its only modeled function is occupying a library slot, diluting draw probabilities exactly like a
real dead card would, so B's 98-card deck is only different from a "hypothetical 97-card deck" in
the one way we want to measure (Pilgrim's mana + network functions gone) and not also confounded by
a smaller deck size / cleaner draws. Per the assignment: "Do not treat placeholder performance as a
deckbuilding recommendation" - it is never proposed as something to actually play.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402
from mana_audit002_variants import build_variant  # noqa: E402
import deckbuild006_cards  # noqa: E402

DECKBUILD006_DECKLIST_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-deckbuild006-v1.json"
MANAAUDIT002_DECKLIST_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-manaaudit002-v1.json"
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"

PILGRIM_NAME = "Avacyn's Pilgrim"
FUNDING_CUT_FOR_C = "Mindbreak Trap"

PLACEHOLDER_NAME = "Structural Placeholder (DECKBUILD-006 non-network filler — not a real card)"
PLACEHOLDER_CARD_DATA = {
    "type": "Sorcery", "mana_cost": "", "cmc": 0,
    "text": "Synthetic filler card for SIM-DECKBUILD-006 config B_4D_NO_LOTHO. Not a real Magic "
            "card, never a deckbuilding suggestion. No mana ability, not a creature, not "
            "classified into any cast-priority table - the generic development loop never casts "
            "it. Exists only to hold the library at 98 cards so draw-probability denominators "
            "match every other config exactly, isolating Avacyn's Pilgrim's mana+network removal "
            "as the one real difference between B and A.",
}


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


def load_deckbuild006_cards():
    """Returns (payload, rows) for the frozen operative 98. `rows` covers exactly the 98 cards
    in the frozen file - counterfactual-only cards (Avacyn's Pilgrim, the funding cut's own data
    is not needed since it's only ever removed, the placeholder) are added separately by
    deckbuild006_cards_pool(), mirroring deckbuild004_cards.all_cards_dict()'s pattern of layering
    non-baseline card data on top rather than folding it into the frozen file's own row set."""
    payload = json.loads(DECKBUILD006_DECKLIST_PATH.read_text(encoding="utf-8"))
    recomputed = compute_deck_hash(payload["commanders"], payload["cards"])
    if recomputed != payload["deck_hash"]:
        raise ValueError(
            f"{DECKBUILD006_DECKLIST_PATH}: stored deck_hash={payload['deck_hash']} does not "
            f"match recomputed hash={recomputed} - file was edited after freezing or tampered with."
        )

    cache = _cache_by_scryfall_id()
    new_card_data = deckbuild006_cards.NEW_CARD_DATA
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


def deckbuild006_cards_pool(base_rows):
    """base_rows (the operative 98's own rows) plus every card needed ONLY by the A/B/C/D
    counterfactual configs: Avacyn's Pilgrim (real card, pulled from MANA-AUDIT-002's frozen
    file + real cards_cache - same real printing already verified there, not re-fabricated) and
    the synthetic PLACEHOLDER. Mindbreak Trap needs no entry here since every config either
    keeps it (already in base_rows) or removes it (build_variant needs no data for a removal)."""
    merged = dict(base_rows)
    if PILGRIM_NAME not in merged:
        prev_payload = json.loads(MANAAUDIT002_DECKLIST_PATH.read_text(encoding="utf-8"))
        prev_by_name = {c["name"]: c for c in prev_payload["cards"]}
        cache = _cache_by_scryfall_id()
        merged[PILGRIM_NAME] = _row_from_cache_card(
            PILGRIM_NAME, cache[prev_by_name[PILGRIM_NAME]["scryfall_id"]]
        )
    merged[PLACEHOLDER_NAME] = dict(PLACEHOLDER_CARD_DATA, name=PLACEHOLDER_NAME)
    # Treasure Token is never a real decklist entry (it's a token Lotho creates in-game) but every
    # config needs its row data available for state.cards lookups the moment
    # deckbuild006_cards.apply_lotho_trigger_if_any() appends one to nonland_perms - present in
    # ALL configs (not just the Lotho ones) so a stray lookup never KeyErrors even where it can
    # never actually be created.
    treasure = deckbuild006_cards.NEW_CARD_DATA[deckbuild006_cards.TREASURE_NAME]
    merged[deckbuild006_cards.TREASURE_NAME] = dict(treasure, name=deckbuild006_cards.TREASURE_NAME)
    return merged


LOTHO_NAME = deckbuild006_cards.LOTHO_NAME

VARIANTS = {
    "A_5D_NO_LOTHO": {
        "add": [PILGRIM_NAME], "remove": [LOTHO_NAME], "deck_size": 98,
        "desc": "SHARED_97 + Avacyn's Pilgrim. Primary reference: 5 true one-mana dorks, no Lotho.",
    },
    "B_4D_NO_LOTHO": {
        "add": [PLACEHOLDER_NAME], "remove": [LOTHO_NAME], "deck_size": 98,
        "desc": "SHARED_97 + synthetic placeholder. Isolates pure Pilgrim-removal structural "
                "cost: 4 dorks, no Lotho, no compensating card of any kind.",
    },
    "C_5D_LOTHO": {
        "add": [PILGRIM_NAME], "remove": [FUNDING_CUT_FOR_C], "deck_size": 98,
        "desc": "SHARED_97 - Mindbreak Trap (disclosed no-op funding cut, not a recommendation) "
                "+ Avacyn's Pilgrim + Lotho. 5 dorks AND Lotho both present.",
    },
    "D_4D_LOTHO": {
        "add": [], "remove": [], "deck_size": 98,
        "desc": "The real operative 98 as-is: 4 dorks, +Lotho. The actual proposed swap.",
    },
}


def build(base_names, cards_pool, variant_name):
    """base_names must be the operative 98's own name list (already contains Lotho, not Pilgrim)."""
    spec = VARIANTS[variant_name]
    names = build_variant(base_names, cards_pool, add=spec["add"], remove=spec["remove"])
    assert len(names) == spec["deck_size"], (variant_name, len(names), spec["deck_size"])
    return names
