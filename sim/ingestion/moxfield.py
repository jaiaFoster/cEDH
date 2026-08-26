"""Fail-closed Moxfield subject-deck synchronizer.

Moxfield does not publish a supported public API. This importer uses the same
read-only JSON endpoint used by the public deck page, but deliberately keeps
the result in ``data/deck_sources``. It does not claim that a source snapshot
has passed the stricter Oracle/cache gates required for a deck-backed run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api2.moxfield.com/v3/decks/all/{deck_id}"
DECK_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
DECK_URL_RE = re.compile(
    r"^https://(?:www\.)?moxfield\.com/decks/(?P<deck_id>[A-Za-z0-9_-]+)(?:[/?#].*)?$"
)


class MoxfieldSyncError(RuntimeError):
    """Raised when the source cannot be fetched or validated safely."""


def parse_deck_id(value: str) -> str:
    match = DECK_URL_RE.match(value)
    deck_id = match.group("deck_id") if match else value
    if not DECK_ID_RE.fullmatch(deck_id):
        raise MoxfieldSyncError(f"Invalid Moxfield deck URL or public ID: {value!r}")
    return deck_id


def fetch_deck(deck_id: str, retries: int = 2) -> dict[str, Any]:
    url = API_URL.format(deck_id=deck_id)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "jaiaFoster-cEDH-metagame-updater/1.0 (+https://github.com/jaiaFoster/cEDH)",
        },
    )
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=30) as response:
                content_type = response.headers.get_content_type()
                body = response.read()
            if content_type != "application/json":
                raise MoxfieldSyncError(
                    f"Moxfield returned {content_type!r}, not JSON; access may be blocked"
                )
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise MoxfieldSyncError("Moxfield response was not a JSON object")
            return payload
        except HTTPError as error:
            if error.code in {429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(2**attempt)
                continue
            raise MoxfieldSyncError(f"Moxfield request failed with HTTP {error.code}") from error
        except URLError as error:
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            raise MoxfieldSyncError(f"Moxfield request failed: {error.reason}") from error
        except json.JSONDecodeError as error:
            raise MoxfieldSyncError("Moxfield returned invalid JSON") from error
    raise AssertionError("unreachable")


def _cards_from_board(payload: dict[str, Any], board_name: str) -> list[dict[str, Any]]:
    board = payload.get("boards", {}).get(board_name) or {}
    entries = board.get("cards") or {}
    if not isinstance(entries, dict):
        raise MoxfieldSyncError(f"Moxfield board {board_name!r} has an unexpected shape")

    cards: list[dict[str, Any]] = []
    for entry in entries.values():
        try:
            card = entry["card"]
            name = str(card["name"]).strip()
            quantity = int(entry["quantity"])
            scryfall_id = str(card["scryfall_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise MoxfieldSyncError(
                f"Moxfield board {board_name!r} contains an invalid card entry"
            ) from error
        if not name or quantity < 1:
            raise MoxfieldSyncError(
                f"Moxfield board {board_name!r} contains an invalid name or quantity"
            )
        cards.append({"name": name, "quantity": quantity, "scryfall_id": scryfall_id})
    return sorted(cards, key=lambda item: (item["name"].casefold(), item["scryfall_id"]))


def normalize_deck(
    payload: dict[str, Any],
    deck_id: str,
    expected_main: int,
    expected_commanders: int,
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    commanders = _cards_from_board(payload, "commanders")
    partners = _cards_from_board(payload, "partners")
    by_card: dict[tuple[str, str], dict[str, Any]] = {}
    for card in commanders + partners:
        key = (card["name"], card["scryfall_id"])
        by_card[key] = card
    commanders = sorted(by_card.values(), key=lambda item: item["name"].casefold())
    cards = _cards_from_board(payload, "mainboard")

    main_count = sum(card["quantity"] for card in cards)
    commander_count = sum(card["quantity"] for card in commanders)
    if main_count != expected_main:
        raise MoxfieldSyncError(
            f"Refusing snapshot: expected {expected_main} main-deck cards, found {main_count}"
        )
    if commander_count != expected_commanders:
        raise MoxfieldSyncError(
            f"Refusing snapshot: expected {expected_commanders} commanders, found {commander_count}"
        )

    canonical = {
        "commanders": [(card["name"], card["quantity"]) for card in commanders],
        "cards": [(card["name"], card["quantity"]) for card in cards],
    }
    content_hash = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    now = retrieved_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "source": {
            "type": "moxfield_public_deck",
            "deck_id": deck_id,
            "url": f"https://moxfield.com/decks/{deck_id}",
            "endpoint": API_URL.format(deck_id=deck_id),
        },
        "deck_name": payload.get("name") or "Unnamed Moxfield deck",
        "moxfield_version": payload.get("version"),
        "moxfield_updated_at": payload.get("lastUpdatedAtUtc"),
        "retrieved_at": now,
        "content_hash": content_hash,
        "counts": {"commanders": commander_count, "mainboard": main_count},
        "commanders": commanders,
        "cards": cards,
    }


def write_snapshot(snapshot: dict[str, Any], output_dir: Path) -> tuple[bool, Path]:
    current_path = output_dir / "current.json"
    if current_path.exists():
        current = json.loads(current_path.read_text())
        if current.get("content_hash") == snapshot["content_hash"]:
            return False, output_dir / current["history_file"]

    retrieved_date = snapshot["retrieved_at"][:10]
    history_path = output_dir / "history" / (
        f"{retrieved_date}_{snapshot['content_hash'][:12]}.json"
    )
    if history_path.exists():
        raise MoxfieldSyncError(f"History path already exists unexpectedly: {history_path}")

    snapshot = dict(snapshot)
    snapshot["history_file"] = history_path.relative_to(output_dir).as_posix()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    current_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    return True, history_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", required=True, help="Public Moxfield URL or deck ID")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/deck_sources/moxfield/tymna-thrasios"),
    )
    parser.add_argument("--expected-main", type=int, default=98)
    parser.add_argument("--expected-commanders", type=int, default=2)
    parser.add_argument("--input-json", type=Path, help="Offline fixture/raw response")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        deck_id = parse_deck_id(args.deck)
        payload = json.loads(args.input_json.read_text()) if args.input_json else fetch_deck(deck_id)
        snapshot = normalize_deck(
            payload, deck_id, args.expected_main, args.expected_commanders
        )
        changed, history_path = write_snapshot(snapshot, args.output_dir)
    except (MoxfieldSyncError, OSError, json.JSONDecodeError) as error:
        print(f"moxfield-sync: ERROR: {error}", file=sys.stderr)
        return 1

    status = "updated" if changed else "unchanged"
    print(f"moxfield-sync: {status}; hash={snapshot['content_hash']}; history={history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
