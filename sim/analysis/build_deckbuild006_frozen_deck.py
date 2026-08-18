"""SIM-DECKBUILD-006 — mint the new frozen operative 98-card subject.

Per the assignment's own operative_deck_requirements ("freeze and hash that list before
analysis... do not silently reuse an older subject deck") and the user's explicit confirmation:
the user pasted the complete, literal, ground-truth 98-card decklist (+ the two commanders) as
the real CURRENT operative deck. This already contains the candidate swap being studied (Lotho,
Corrupt Shirriff IN / Avacyn's Pilgrim OUT) plus 8 other card changes accumulated since the
MANA-AUDIT-002 frozen subject (tymna-thrasios-treefarm-manaaudit002-v1.json) — a real diff of 9
removed / 9 added, net zero, independently verified (see this script's own diff output below).

Provenance for the 9 new cards' scryfall_id: this environment's network egress to every
card-database domain (scryfall, gatherer, edhrec, etc.) is blocked (a long-standing, disclosed
project limitation — see prior tasks' WebFetch EGRESS_BLOCKED notes), so real Scryfall UUIDs for
Lotho/Grand Abolisher/Mockingbird/Neoform/Formidable Speaker/Talion/Seedborn Muse/An Offer You
Can't Refuse/Scalding Tarn cannot be fetched. This script mints clearly-labeled SYNTHETIC
placeholder UUIDs (namespaced with the fixed prefix "deadbeef-", never a real Scryfall ID format
collision) for those 9 entries only. The other 89 entries reuse the REAL scryfall_id already
verified in the MANA-AUDIT-002 frozen file (same printings, same names). This deliberately means
this new frozen file does NOT pass sim/validation/run_classification.py's strict
load_frozen_deck() (which requires every scryfall_id to resolve in the real oracle cards_cache) —
by design, since 9 of its cards have no real cache entry. DECKBUILD-006's own loader
(build_deckbuild006_variants.py) does its own hash-verification instead and sources the 9 new
cards' row data from deckbuild006_cards.NEW_CARD_DATA, exactly mirroring the DECKBUILD-004
precedent of NEW_CARD_DATA supplying non-cached card facts, applied here to the frozen file's
metadata too since this is now the deck's OWN real current list rather than a hypothetical
counterfactual.

"La abundancia de Yucahú" (a line in the user's pasted list) is a Spanish-language alt-name
printing of Sylvan Library — normalized to the English name at ingestion (see deckbuild006_cards.py
module docstring), not treated as a 10th new/unknown card.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402

PASTED_LIST_PATH = Path("/tmp/pasted_list.txt")
PREV_FROZEN_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-manaaudit002-v1.json"
OUT_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-deckbuild006-v1.json"

NAME_NORMALIZATION = {
    "La abundancia de Yucahú": "Sylvan Library",
}

# The 9 cards with no real scryfall_id available in this environment. Fixed, disclosed,
# deterministic synthetic UUIDs (not randomly generated per-run, so this script is idempotent).
SYNTHETIC_SCRYFALL_IDS = {
    "An Offer You Can't Refuse": "deadbeef-0001-4000-8000-000000000001",
    "Formidable Speaker": "deadbeef-0001-4000-8000-000000000002",
    "Grand Abolisher": "deadbeef-0001-4000-8000-000000000003",
    "Lotho, Corrupt Shirriff": "deadbeef-0001-4000-8000-000000000004",
    "Mockingbird": "deadbeef-0001-4000-8000-000000000005",
    "Neoform": "deadbeef-0001-4000-8000-000000000006",
    "Scalding Tarn": "deadbeef-0001-4000-8000-000000000007",
    "Seedborn Muse": "deadbeef-0001-4000-8000-000000000008",
    "Talion, the Kindly Lord": "deadbeef-0001-4000-8000-000000000009",
}
COMMANDERS = ["Thrasios, Triton Hero", "Tymna the Weaver"]


def _read_pasted_names():
    names = []
    for line in PASTED_LIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        # lines are "1 <name>"
        parts = line.split(" ", 1)
        assert parts[0] == "1", f"unexpected quantity token in line: {line!r}"
        name = parts[1].strip()
        name = NAME_NORMALIZATION.get(name, name)
        names.append(name)
    return names


def main():
    new_names = _read_pasted_names()
    assert len(new_names) == 98, f"expected 98 cards, got {len(new_names)}"
    assert len(set(new_names)) == 98, "duplicate card name in pasted list"

    prev = json.loads(PREV_FROZEN_PATH.read_text(encoding="utf-8"))
    prev_by_name = {c["name"]: c for c in prev["cards"]}
    prev_names = set(prev_by_name)
    new_names_set = set(new_names)

    removed = sorted(prev_names - new_names_set)
    added = sorted(new_names_set - prev_names)
    print(f"removed ({len(removed)}): {removed}")
    print(f"added ({len(added)}): {added}")
    assert set(added) == set(SYNTHETIC_SCRYFALL_IDS), (
        "the set of newly-added card names does not match this script's known synthetic-id "
        "table - a card list drifted without updating this script; refusing to silently mint "
        f"a frozen file. added={sorted(added)} known_new={sorted(SYNTHETIC_SCRYFALL_IDS)}"
    )

    cards = []
    for name in new_names:
        if name in prev_by_name:
            scryfall_id = prev_by_name[name]["scryfall_id"]
        else:
            scryfall_id = SYNTHETIC_SCRYFALL_IDS[name]
        cards.append({"scryfall_id": scryfall_id, "name": name, "quantity": 1})

    deck_hash = compute_deck_hash(COMMANDERS, cards)

    payload = {
        "deck_version": "tymna-thrasios-treefarm-deckbuild006-v1",
        "deck_name": "Tymna the Weaver / Thrasios, Triton Hero — Tree Farm x CounterSlop "
                     "(SIM-DECKBUILD-006 operative)",
        "commanders": COMMANDERS,
        "archetype_id": None,
        "role": "subject",
        "cards": cards,
        "source": {
            "type": "user_supplied",
            "reference": "User pasted the complete, literal 98-card operative decklist directly "
                         "in the SIM-DECKBUILD-006 task thread (2026-08-18), explicitly confirming "
                         "it as accurate and noting it already contains Lotho, Corrupt Shirriff in "
                         "place of Avacyn's Pilgrim — the swap under study.",
            "date": "2026-08-18",
        },
        "changelog": [
            {
                "version": "tymna-thrasios-treefarm-deckbuild006-v1",
                "note": (
                    "SIM-DECKBUILD-006 requires the exact current operative 98 and explicitly "
                    "forbids silently reusing the previous frozen subject. The assignment's own "
                    "'known_current_changes' changelog (referencing an 'Emergence Zone' swap) did "
                    "not match reality: applying it literally to the MANA-AUDIT-002 frozen list "
                    "produced 100 cards with only 3 of 5 real removals accounted for and one "
                    "fabricated/never-present card ('Emergence Zone'). This ambiguity was raised "
                    "to the user via AskUserQuestion; the user resolved it by pasting the complete "
                    "real 98-card list instead of picking from the offered options. A programmatic "
                    "diff against tymna-thrasios-treefarm-manaaudit002-v1.json found exactly 9 "
                    "cards removed (Avacyn's Pilgrim, Elves of Deep Shadow, Heartwood Storyteller, "
                    "King T'Challa // Black Panther Hope Enduring, Misdirection, Shifting "
                    "Woodland, Swan Song, Voice of Victory, Volatile Stormdrake) and 9 added (An "
                    "Offer You Can't Refuse, Formidable Speaker, Grand Abolisher, Lotho Corrupt "
                    "Shirriff, Mockingbird, Neoform, Scalding Tarn, Seedborn Muse, Talion the "
                    "Kindly Lord) — net zero, 98 cards confirmed. 'La abundancia de Yucahú' in "
                    "the pasted list is a Spanish alt-name printing of the already-known Sylvan "
                    "Library, normalized at ingestion, not counted as a 10th new card. This deck "
                    "already reflects Talon Gates of Madara retained alongside the newly-added "
                    "Scalding Tarn (both present) — i.e. the deckbuilder added Scalding Tarn "
                    "without following MANA-AUDIT-002's specific recommendation to cut Talon "
                    "Gates of Madara for it; that is the deckbuilder's prerogative, not an error "
                    "in either task. The 89 cards shared with the prior frozen file reuse their "
                    "REAL, already-verified scryfall_id. The 9 newly-added cards use disclosed "
                    "SYNTHETIC placeholder scryfall_ids (fixed 'deadbeef-0001-...' prefix, listed "
                    "in build_deckbuild006_frozen_deck.py's SYNTHETIC_SCRYFALL_IDS table) because "
                    "this environment's network egress to every card-database domain is blocked "
                    "(a recurring, previously-disclosed limitation) — real Oracle text for these "
                    "9 cards was instead verified via WebSearch and hand-encoded in "
                    "deckbuild006_cards.py / deckbuild004_cards.py. Per docs/VERSIONING.md this "
                    "IS a content-changing version bump (9 cards genuinely differ from the prior "
                    "frozen file) — a new file, never an edit to the prior one, with its own "
                    "independently-computed canonical hash. Because it contains cards with no "
                    "real cards_cache entry, this file intentionally does NOT pass "
                    "sim.validation.run_classification.load_frozen_deck()'s strict scryfall-cache "
                    "resolution check — DECKBUILD-006's own loader "
                    "(build_deckbuild006_variants.py) verifies this file's hash directly instead "
                    "and sources the 9 new cards' gameplay data from deckbuild006_cards.NEW_CARD_DATA."
                ),
            }
        ],
        "ingested": {
            "oracle_data_version": "scryfall-live-2026-08-12",
            "ingested_date": "2026-08-12",
            "cards_cache_path": "data/cards_cache/oracle-2026-08-12/",
            "synthetic_card_data_note": (
                "9 of 98 cards (see changelog) have SYNTHETIC placeholder scryfall_ids not "
                "present in the real oracle cache above; their gameplay data comes from "
                "sim/analysis/deckbuild006_cards.py and deckbuild004_cards.py instead."
            ),
        },
        "deck_hash": deck_hash,
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"deck_hash={deck_hash}")


if __name__ == "__main__":
    main()
