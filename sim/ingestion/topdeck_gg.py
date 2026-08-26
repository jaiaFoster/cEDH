"""Authenticated TopDeck.gg V2 tournament ingestion.

The API key is read only from ``TOPDECK_API_KEY``. Raw API responses are
stored as deterministic gzip snapshots; readable normalized event records
retain standings, commander hints, and round/pod structure for later analysis.

Examples:
    python -m sim.ingestion.topdeck_gg --smoke
    python -m sim.ingestion.topdeck_gg --last 7 --participant-min 16 --include-rounds
    python -m sim.ingestion.topdeck_gg --tid EVENT_ID --include-rounds
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://topdeck.gg/api"
ATTRIBUTION = {"name": "TopDeck.gg", "url": "https://topdeck.gg"}
DEFAULT_COLUMNS = [
    "name", "id", "decklist", "wins", "winsSwiss", "winsBracket",
    "draws", "losses", "lossesSwiss", "lossesBracket", "byes",
]
SAFE_TID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class TopDeckError(RuntimeError):
    """Base error for authenticated TopDeck access or validation failures."""


class TopDeckAuthError(TopDeckError):
    """Raised for missing or rejected credentials."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class TopDeckClient:
    def __init__(self, api_key: str | None = None, retries: int = 3):
        self.api_key = api_key or os.environ.get("TOPDECK_API_KEY")
        if not self.api_key:
            raise TopDeckAuthError(
                "TOPDECK_API_KEY is not set; store it as a GitHub Actions secret"
            )
        self.retries = retries

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        body = None
        headers = {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "User-Agent": "jaiaFoster-cEDH-metagame-updater/1.0 (+https://github.com/jaiaFoster/cEDH)",
        }
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode()
            headers["Content-Type"] = "application/json"
        request = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)

        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=60) as response:
                    response_body = response.read()
                return json.loads(response_body)
            except HTTPError as error:
                if error.code == 401:
                    raise TopDeckAuthError("TopDeck rejected TOPDECK_API_KEY") from error
                retry_after = error.headers.get("Retry-After")
                if error.code in {429, 500, 502, 503, 504} and attempt < self.retries:
                    try:
                        delay = min(max(float(retry_after or 2**attempt), 0), 60)
                    except ValueError:
                        delay = float(2**attempt)
                    time.sleep(delay)
                    continue
                detail = ""
                try:
                    parsed = json.loads(error.read())
                    detail = f": {parsed.get('error', 'request failed')}"
                except (json.JSONDecodeError, AttributeError):
                    pass
                raise TopDeckError(f"TopDeck returned HTTP {error.code}{detail}") from error
            except URLError as error:
                if attempt < self.retries:
                    time.sleep(2**attempt)
                    continue
                raise TopDeckError(f"TopDeck connection failed: {error.reason}") from error
            except json.JSONDecodeError as error:
                raise TopDeckError("TopDeck returned invalid JSON") from error
        raise AssertionError("unreachable")

    def smoke_test(self) -> int:
        result = self.request("GET", "/v2/me/tournaments?" + urlencode({"filter": "all"}))
        if not isinstance(result, list):
            raise TopDeckError("TopDeck smoke response was not a list")
        return len(result)

    def tournaments(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        result = self.request("POST", "/v2/tournaments", query)
        if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
            raise TopDeckError("TopDeck tournament response was not a list of objects")
        return result


def build_query(args: argparse.Namespace) -> dict[str, Any]:
    if args.tid:
        tids = args.tid
        for tid in tids:
            if not SAFE_TID_RE.fullmatch(tid):
                raise TopDeckError(f"Invalid tournament ID: {tid!r}")
        query: dict[str, Any] = {"TID": tids[0] if len(tids) == 1 else tids}
    else:
        query = {
            "game": "Magic: The Gathering",
            "format": "EDH",
            "participantMin": args.participant_min,
        }
        if args.start is not None or args.end is not None:
            if args.start is not None:
                query["start"] = args.start
            if args.end is not None:
                query["end"] = args.end
        else:
            query["last"] = args.last

    query["columns"] = DEFAULT_COLUMNS
    if args.include_rounds:
        query.update({
            "rounds": True,
            "tables": ["table", "players", "winner", "status"],
            "players": ["name", "id"],
        })
    return query


def _board(deck_obj: Any, name: str) -> Any:
    if not isinstance(deck_obj, dict):
        return None
    for key, value in deck_obj.items():
        if str(key).casefold() == name.casefold():
            return value
    return None


def _names_from_board(board: Any) -> list[str]:
    names: list[str] = []
    if isinstance(board, dict):
        for key, value in board.items():
            candidate = None
            if isinstance(value, dict):
                card = value.get("card") if isinstance(value.get("card"), dict) else value
                candidate = card.get("name")
            names.append(str(candidate or key).strip())
    elif isinstance(board, list):
        for value in board:
            if isinstance(value, str):
                names.append(value.strip())
            elif isinstance(value, dict):
                card = value.get("card") if isinstance(value.get("card"), dict) else value
                if card.get("name"):
                    names.append(str(card["name"]).strip())
    return sorted({name for name in names if name}, key=str.casefold)


def _commanders_from_text(decklist: Any) -> list[str]:
    if not isinstance(decklist, str) or "~~Commanders~~" not in decklist:
        return []
    section = decklist.split("~~Commanders~~", 1)[1].split("~~", 1)[0]
    names = []
    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^\d+\s*[xX]?\s+", "", line)
        line = re.sub(r"\s+\([A-Z0-9]+\)\s+\d+.*$", "", line)
        if line:
            names.append(line)
    return sorted(set(names), key=str.casefold)


def extract_commanders(row: dict[str, Any]) -> list[str]:
    structured = _names_from_board(_board(row.get("deckObj"), "Commanders"))
    return structured or _commanders_from_text(row.get("decklist"))


def normalize_tournament(raw: dict[str, Any], pulled_at: str, content_hash: str) -> dict[str, Any]:
    tid = raw.get("TID") or raw.get("tid")
    if not tid:
        raise TopDeckError("Tournament response is missing TID")
    standings = raw.get("standings") or []
    if not isinstance(standings, list):
        raise TopDeckError(f"Tournament {tid} standings are not a list")
    top_cut = int(raw.get("topCut") or 0)

    entries = []
    decklists = structured = 0
    for index, row in enumerate(standings, start=1):
        if not isinstance(row, dict):
            raise TopDeckError(f"Tournament {tid} contains an invalid standing")
        standing = int(row.get("standing") or index)
        has_decklist = bool(row.get("decklist"))
        has_structured = bool(row.get("deckObj"))
        decklists += int(has_decklist)
        structured += int(has_structured)
        entries.append({
            "standing": standing,
            "player_id": row.get("id"),
            "player_name": row.get("name"),
            "commanders": extract_commanders(row),
            "wins": row.get("wins"),
            "wins_swiss": row.get("winsSwiss"),
            "wins_bracket": row.get("winsBracket"),
            "draws": row.get("draws"),
            "losses": row.get("losses"),
            "losses_swiss": row.get("lossesSwiss"),
            "losses_bracket": row.get("lossesBracket"),
            "byes": row.get("byes"),
            "top_cut": bool(top_cut and standing <= top_cut),
            "winner": standing == 1,
            "decklist_present": has_decklist,
            "structured_deck_present": has_structured,
        })

    pods = []
    rounds = raw.get("rounds") or []
    for round_obj in rounds:
        if not isinstance(round_obj, dict):
            continue
        for table in round_obj.get("tables") or []:
            if not isinstance(table, dict):
                continue
            pods.append({
                "round": round_obj.get("round"),
                "table": table.get("table"),
                "status": table.get("status"),
                "winner": table.get("winner"),
                "winner_id": table.get("winner_id"),
                "players": [
                    {"id": player.get("id"), "name": player.get("name")}
                    for player in (table.get("players") or [])
                    if isinstance(player, dict)
                ],
            })

    start_date = raw.get("startDate")
    start_utc = None
    if isinstance(start_date, (int, float)):
        start_utc = datetime.fromtimestamp(start_date, timezone.utc).isoformat().replace("+00:00", "Z")
    field_size = len(entries)
    return {
        "schema_version": 1,
        "source": "topdeck.gg",
        "attribution": ATTRIBUTION,
        "pulled_at": pulled_at,
        "content_hash": content_hash,
        "tid": str(tid),
        "name": raw.get("tournamentName") or raw.get("name") or str(tid),
        "game": raw.get("game"),
        "format": raw.get("format"),
        "start_date_unix": start_date,
        "start_date_utc": start_utc,
        "swiss_rounds": raw.get("swissNum"),
        "top_cut_size": top_cut,
        "event_data": raw.get("eventData") or {},
        "field_size": field_size,
        "decklist_coverage": {
            "submitted": decklists,
            "structured": structured,
            "total": field_size,
        },
        "entries": entries,
        "pods": pods,
    }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _write_gzip(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
            compressed.write(payload)


def write_tournaments(tournaments: list[dict[str, Any]], output_root: Path) -> dict[str, int]:
    manifest_path = output_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "schema_version": 1,
        "source": "topdeck.gg",
        "attribution": ATTRIBUTION,
        "events": {},
    }
    pulled_at = utc_now()
    counts = {"returned": len(tournaments), "new": 0, "changed": 0, "unchanged": 0}

    for raw in tournaments:
        tid = str(raw.get("TID") or raw.get("tid") or "")
        if not tid or not SAFE_TID_RE.fullmatch(tid):
            raise TopDeckError(f"Unsafe or missing tournament ID: {tid!r}")
        payload = _canonical_bytes(raw)
        content_hash = hashlib.sha256(payload).hexdigest()
        previous = manifest["events"].get(tid)
        if previous and previous.get("content_hash") == content_hash:
            counts["unchanged"] += 1
            continue

        raw_relative = Path("raw") / tid / f"{content_hash}.json.gz"
        normalized_relative = Path("normalized") / f"{tid}.json"
        _write_gzip(output_root / raw_relative, payload)
        normalized = normalize_tournament(raw, pulled_at, content_hash)
        (output_root / normalized_relative).parent.mkdir(parents=True, exist_ok=True)
        (output_root / normalized_relative).write_text(
            json.dumps(normalized, indent=2, ensure_ascii=False) + "\n"
        )
        manifest["events"][tid] = {
            "content_hash": content_hash,
            "raw_snapshot": raw_relative.as_posix(),
            "normalized_event": normalized_relative.as_posix(),
            "start_date_unix": normalized["start_date_unix"],
            "field_size": normalized["field_size"],
            "captured_at": pulled_at,
        }
        counts["changed" if previous else "new"] += 1

    if counts["new"] or counts["changed"] or not manifest_path.exists():
        output_root.mkdir(parents=True, exist_ok=True)
        manifest["events"] = dict(sorted(manifest["events"].items()))
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return counts


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--smoke", action="store_true", help="Authenticate without ingesting")
    result.add_argument("--tid", action="append", help="Specific tournament ID; repeatable")
    result.add_argument("--last", type=int, default=7, help="Rolling days when no TID/range is supplied")
    result.add_argument("--start", type=int, help="Start date as Unix seconds")
    result.add_argument("--end", type=int, help="End date as Unix seconds")
    result.add_argument("--participant-min", type=int, default=16)
    result.add_argument("--include-rounds", action="store_true")
    result.add_argument(
        "--output-root", type=Path,
        default=Path("data/tournament_snapshots/topdeck"),
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        client = TopDeckClient()
        if args.smoke:
            owned = client.smoke_test()
            print(f"topdeck-smoke: authenticated; owned_tournaments={owned}")
            return 0
        query = build_query(args)
        tournaments = client.tournaments(query)
        counts = write_tournaments(tournaments, args.output_root)
        print("topdeck-ingest: " + "; ".join(f"{key}={value}" for key, value in counts.items()))
        return 0
    except (TopDeckError, OSError, json.JSONDecodeError) as error:
        print(f"topdeck-ingest: ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
