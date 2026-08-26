import json

import pytest

from sim.ingestion.moxfield import (
    MoxfieldSyncError,
    normalize_deck,
    parse_deck_id,
    write_snapshot,
)


def _entry(name, scryfall_id, quantity=1):
    return {"quantity": quantity, "card": {"name": name, "scryfall_id": scryfall_id}}


def _payload(main_count=98):
    return {
        "name": "Tree Farm",
        "version": 7,
        "lastUpdatedAtUtc": "2026-08-25T12:00:00Z",
        "boards": {
            "commanders": {
                "cards": {
                    "t": _entry("Tymna the Weaver", "00000000-0000-4000-8000-000000000001"),
                    "h": _entry("Thrasios, Triton Hero", "00000000-0000-4000-8000-000000000002"),
                }
            },
            "mainboard": {
                "cards": {
                    "x": _entry("Island", "00000000-0000-4000-8000-000000000003", main_count)
                }
            },
        },
    }


def test_parse_public_url():
    assert parse_deck_id("https://moxfield.com/decks/gvyGvOx0g0uJ7ultPy-pbw") == "gvyGvOx0g0uJ7ultPy-pbw"


def test_normalize_and_write_is_idempotent(tmp_path):
    snapshot = normalize_deck(
        _payload(), "gvyGvOx0g0uJ7ultPy-pbw", 98, 2, "2026-08-25T20:00:00Z"
    )
    output = tmp_path / "data" / "deck_sources" / "moxfield" / "tymna-thrasios"
    changed, history = write_snapshot(snapshot, output)
    assert changed
    assert history.exists()
    current = json.loads((output / "current.json").read_text())
    assert current["counts"] == {"commanders": 2, "mainboard": 98}

    changed_again, same_history = write_snapshot(snapshot, output)
    assert not changed_again
    assert same_history == history
    assert len(list((output / "history").glob("*.json"))) == 1


def test_wrong_main_count_fails_closed():
    with pytest.raises(MoxfieldSyncError, match="expected 98"):
        normalize_deck(_payload(97), "gvyGvOx0g0uJ7ultPy-pbw", 98, 2)
