import gzip
import json
from argparse import Namespace

import pytest

from sim.ingestion.topdeck_gg import (
    TopDeckAuthError,
    TopDeckClient,
    build_query,
    extract_commanders,
    normalize_tournament,
    write_tournaments,
)


def _args(**overrides):
    values = dict(tid=None, participant_min=16, start=None, end=None, last=7, include_rounds=True)
    values.update(overrides)
    return Namespace(**values)


def _tournament():
    return {
        "TID": "event-123",
        "tournamentName": "Test cEDH Open",
        "swissNum": 5,
        "startDate": 1787702400,
        "game": "Magic: The Gathering",
        "format": "EDH",
        "topCut": 4,
        "eventData": {"city": "Phoenix", "state": "AZ"},
        "standings": [
            {
                "standing": 1, "name": "Alice", "id": "a", "wins": 4,
                "draws": 1, "losses": 0, "decklist": "https://example.test/a",
                "deckObj": {"Commanders": {"Tymna the Weaver": {}, "Thrasios, Triton Hero": {}}},
            },
            {"standing": 2, "name": "Bob", "id": "b", "wins": 3, "draws": 1, "losses": 1},
        ],
        "rounds": [{
            "round": 1,
            "tables": [{
                "table": 1, "status": "Completed", "winner": "Alice", "winner_id": "a",
                "players": [{"name": "Alice", "id": "a"}, {"name": "Bob", "id": "b"}],
            }],
        }],
    }


def test_missing_key_fails_without_echoing_secret(monkeypatch):
    monkeypatch.delenv("TOPDECK_API_KEY", raising=False)
    with pytest.raises(TopDeckAuthError, match="TOPDECK_API_KEY is not set"):
        TopDeckClient()


def test_build_rolling_and_tid_queries():
    rolling = build_query(_args())
    assert rolling["game"] == "Magic: The Gathering"
    assert rolling["format"] == "EDH"
    assert rolling["last"] == 7
    assert rolling["rounds"] is True

    targeted = build_query(_args(tid=["abc_123"], include_rounds=False))
    assert targeted["TID"] == "abc_123"
    assert "game" not in targeted
    assert "rounds" not in targeted


def test_commander_extraction_structured_and_text():
    assert extract_commanders({"deckObj": {"Commanders": {"Tymna": {}, "Thrasios": {}}}}) == [
        "Thrasios", "Tymna"
    ]
    assert extract_commanders({"decklist": "~~Commanders~~\n1 Tymna\n1 Thrasios\n~~Mainboard~~\n98 Island"}) == [
        "Thrasios", "Tymna"
    ]


def test_normalization_retains_performance_and_pods():
    event = normalize_tournament(_tournament(), "2026-08-26T05:00:00Z", "a" * 64)
    assert event["field_size"] == 2
    assert event["decklist_coverage"] == {"submitted": 1, "structured": 1, "total": 2}
    assert event["entries"][0]["top_cut"] is True
    assert event["entries"][0]["winner"] is True
    assert event["entries"][0]["commanders"] == ["Thrasios, Triton Hero", "Tymna the Weaver"]
    assert event["pods"][0]["winner_id"] == "a"


def test_snapshots_are_immutable_and_idempotent(tmp_path):
    output = tmp_path / "topdeck"
    first = write_tournaments([_tournament()], output)
    assert first == {"returned": 1, "new": 1, "changed": 0, "unchanged": 0}
    manifest = json.loads((output / "manifest.json").read_text())
    raw_path = output / manifest["events"]["event-123"]["raw_snapshot"]
    with gzip.open(raw_path, "rt") as source:
        assert json.load(source)["TID"] == "event-123"

    second = write_tournaments([_tournament()], output)
    assert second == {"returned": 1, "new": 0, "changed": 0, "unchanged": 1}
    assert len(list((output / "raw" / "event-123").glob("*.json.gz"))) == 1

    changed = _tournament()
    changed["standings"][1]["wins"] = 4
    third = write_tournaments([changed], output)
    assert third["changed"] == 1
    assert len(list((output / "raw" / "event-123").glob("*.json.gz"))) == 2
