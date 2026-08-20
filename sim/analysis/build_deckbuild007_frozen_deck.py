"""SIM-DECKBUILD-007 — mint the new frozen 101-card candidate build.

Per the assignment: "Use this exact list. Do not inherit older deck hashes." Diff against
tymna-thrasios-treefarm-deckbuild006-v1.json (the prior frozen subject) found exactly 3 removed
(An Offer You Can't Refuse, Shang-Chi Master of Kung Fu, Training Grounds - all three are on this
task's own "currently absent, assess whether reasonable" list, confirming the diff matches the
assignment's own framing) and 4 added (Biomancer's Familiar, Birthing Ritual, Dark Ritual, The
Cabbage Merchant) - net 98 - 3 + 4 = 99 main-deck cards, + Thrasios/Tymna = 101 total.

Same synthetic-scryfall-id provenance pattern as deckbuild006's minting script: real scryfall_ids
reused for the 95 already-known cards, disclosed synthetic placeholder UUIDs for the 4 genuinely
new cards (network egress to card-database domains remains blocked in this environment - real
Oracle text for all 4 was instead verified via WebSearch, see deckbuild007_cards.py).
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402

LIST_PATH = Path("/tmp/claude-0/-home-user-cEDH/eae84c92-f7a7-5b91-a2b5-bb444a7ee454/scratchpad/deckbuild007_list.txt")
PREV_FROZEN_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-deckbuild006-v1.json"
OUT_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-deckbuild007-v1.json"

SYNTHETIC_SCRYFALL_IDS = {
    "Biomancer's Familiar": "deadbeef-0002-4000-8000-000000000001",
    "Birthing Ritual": "deadbeef-0002-4000-8000-000000000002",
    "Dark Ritual": "deadbeef-0002-4000-8000-000000000003",
    "The Cabbage Merchant": "deadbeef-0002-4000-8000-000000000004",
}
COMMANDERS = ["Thrasios, Triton Hero", "Tymna the Weaver"]


def _read_names():
    names = []
    for line in LIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        assert parts[0] == "1", f"unexpected quantity token: {line!r}"
        names.append(parts[1].strip())
    return names


def main():
    new_names = _read_names()
    assert len(new_names) == 99, f"expected 99 main-deck cards, got {len(new_names)}"
    assert len(set(new_names)) == 99, "duplicate card name in list"

    prev = json.loads(PREV_FROZEN_PATH.read_text(encoding="utf-8"))
    prev_by_name = {c["name"]: c for c in prev["cards"]}
    prev_names = set(prev_by_name)
    new_set = set(new_names)

    removed = sorted(prev_names - new_set)
    added = sorted(new_set - prev_names)
    print(f"removed ({len(removed)}): {removed}")
    print(f"added ({len(added)}): {added}")
    assert set(added) == set(SYNTHETIC_SCRYFALL_IDS), (
        "newly-added card names don't match this script's known synthetic-id table - refusing to "
        f"silently mint. added={sorted(added)} known_new={sorted(SYNTHETIC_SCRYFALL_IDS)}"
    )

    cards = []
    for name in new_names:
        scryfall_id = prev_by_name[name]["scryfall_id"] if name in prev_by_name else SYNTHETIC_SCRYFALL_IDS[name]
        cards.append({"scryfall_id": scryfall_id, "name": name, "quantity": 1})

    deck_hash = compute_deck_hash(COMMANDERS, cards)
    payload = {
        "deck_version": "tymna-thrasios-treefarm-deckbuild007-v1",
        "deck_name": "Tymna the Weaver / Thrasios, Triton Hero — Tree Farm x CounterSlop "
                     "(SIM-DECKBUILD-007 candidate)",
        "commanders": COMMANDERS,
        "archetype_id": None,
        "role": "subject",
        "cards": cards,
        "source": {
            "type": "user_supplied",
            "reference": "User supplied the complete, literal 99-main-deck-card candidate list "
                         "directly in the SIM-DECKBUILD-007 task text (2026-08-20).",
            "date": "2026-08-20",
        },
        "changelog": [
            {
                "version": "tymna-thrasios-treefarm-deckbuild007-v1",
                "note": (
                    "SIM-DECKBUILD-007 explicitly instructed: 'Use this exact list. Do not "
                    "inherit older deck hashes.' Diff against "
                    "tymna-thrasios-treefarm-deckbuild006-v1.json found exactly 3 removed (An "
                    "Offer You Can't Refuse, Shang-Chi Master of Kung Fu, Training Grounds - all "
                    "three appear on this task's own 'currently absent' assessment list, "
                    "confirming the diff matches the assignment's framing) and 4 added "
                    "(Biomancer's Familiar, Birthing Ritual, Dark Ritual, The Cabbage Merchant). "
                    "The 95 shared cards reuse their REAL, already-verified scryfall_id from the "
                    "prior frozen file. The 4 newly-added cards use disclosed SYNTHETIC "
                    "placeholder scryfall_ids (fixed 'deadbeef-0002-...' prefix) because this "
                    "environment's network egress to card-database domains is blocked - real "
                    "Oracle text for these 4 was verified via WebSearch instead and hand-encoded "
                    "in deckbuild007_cards.py. Per docs/VERSIONING.md this is a content-changing "
                    "version bump - a new file, never an edit to the prior one, with its own "
                    "independently-computed canonical hash. This file intentionally does NOT "
                    "pass sim.validation.run_classification.load_frozen_deck()'s strict "
                    "scryfall-cache resolution check (same pattern as deckbuild006's own frozen "
                    "file) - DECKBUILD-007's own loader verifies this file's hash directly and "
                    "sources the 4 new cards' gameplay data from deckbuild007_cards.NEW_CARD_DATA."
                ),
            }
        ],
        "ingested": {
            "oracle_data_version": "scryfall-live-2026-08-12",
            "ingested_date": "2026-08-12",
            "cards_cache_path": "data/cards_cache/oracle-2026-08-12/",
            "synthetic_card_data_note": (
                "4 of 99 main-deck cards (see changelog) have SYNTHETIC placeholder scryfall_ids "
                "not present in the real oracle cache; their gameplay data comes from "
                "sim/analysis/deckbuild007_cards.py instead."
            ),
        },
        "deck_hash": deck_hash,
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"deck_hash={deck_hash}")


if __name__ == "__main__":
    main()
