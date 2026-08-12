"""Scryfall ingestion adapter (Tier 3, docs/SOURCES.md).

Bulk-pulls a card list via the /cards/collection endpoint (up to 75 names
per request), fetches rulings per card, and writes card.schema.json-
conformant records to data/cards_cache/oracle-<date>/.

Ability classification (activated/triggered/static/replacement/mana) is a
rule-based heuristic text-line parser, NOT a manually reviewed rules
implementation. It's a reasonable Level 1 first pass (charter Level 1:
"cards must retain relevant actual characteristics") but every card carries
a note in characteristics.notes saying so, and nothing here should be
treated as Level 4 exact-line-validated without independent review — see
docs/CHARTER.md Phase/Level definitions and rules_tests/gold_board_states/
once those exist.

Usage:
    python3 sim/ingestion/scryfall.py <names.json> <output_dir> [--rulings]

names.json: a JSON array of exact card names.
output_dir: directory to write one <scryfall_id>.json file per card into.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCRYFALL_COLLECTION_URL = "https://api.scryfall.com/cards/collection"
BATCH_SIZE = 75
REQUEST_DELAY_S = 0.1  # Scryfall asks for ~50-100ms between requests


def _curl_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    # Shelling out to curl rather than urllib: this environment's egress proxy
    # (see docs/SOURCES.md) returned HTTP 400 from urllib.request's POST
    # handling for reasons not fully diagnosed, while curl (proven reachable
    # in the reachability checks that unblocked ENV-0001) works reliably.
    cmd = ["curl", "-sS", "--max-time", "30", "-H", "Accept: application/json"]
    if method == "POST":
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "--data", json.dumps(payload)]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}) for {url}: {result.stderr}")
    return json.loads(result.stdout)


def _post_json(url: str, payload: dict) -> dict:
    return _curl_json(url, method="POST", payload=payload)


def _get_json(url: str) -> dict:
    return _curl_json(url, method="GET")


def fetch_collection(names: list[str]) -> tuple[list[dict], list[dict]]:
    found, not_found = [], []
    for i in range(0, len(names), BATCH_SIZE):
        batch = names[i:i + BATCH_SIZE]
        payload = {"identifiers": [{"name": n} for n in batch]}
        result = _post_json(SCRYFALL_COLLECTION_URL, payload)
        found.extend(result.get("data", []))
        not_found.extend(result.get("not_found", []))
        time.sleep(REQUEST_DELAY_S)
    return found, not_found


def fetch_rulings(rulings_uri: str) -> list[dict]:
    result = _get_json(rulings_uri)
    time.sleep(REQUEST_DELAY_S)
    return [
        {"date": r["published_at"], "text": r["comment"], "source": "scryfall_rulings"}
        for r in result.get("data", [])
    ]


_TIMING_PATTERNS = [
    "activate only as a sorcery",
    "activate only during your turn",
    "activate only once each turn",
    "activate only any time you could cast a sorcery",
]

_ALT_COST_RE = re.compile(
    r"(you may [^.]*?rather than pay[^.]*\.|as an additional cost to cast this spell[^.]*\.)",
    re.IGNORECASE,
)


def _classify_line(line: str) -> dict:
    stripped = line.strip()
    lower = stripped.lower()
    has_cost_colon = ":" in stripped and not lower.startswith(("when ", "whenever ", "at the beginning"))

    kind = "static"
    cost = None
    if has_cost_colon:
        cost_part, _, effect_part = stripped.partition(":")
        cost = cost_part.strip()
        effect_lower = effect_part.lower()
        if "add " in effect_lower and ("{" in effect_part or "mana" in effect_lower):
            kind = "mana"
        else:
            kind = "activated"
    elif lower.startswith(("when ", "whenever ", "at the beginning of", "at the beginning")):
        kind = "triggered"
    elif "instead" in lower or "would" in lower and "if" in lower:
        kind = "replacement"

    timing_restriction = next((t for t in _TIMING_PATTERNS if t in lower), None)
    alt_cost_match = _ALT_COST_RE.search(stripped)
    alt_cost = alt_cost_match.group(0) if alt_cost_match else None

    return {
        "kind": kind,
        "text": stripped,
        "cost": cost,
        "timing_restriction": timing_restriction,
        "zone_restriction": None,
        "alternative_cost": alt_cost,
    }


def parse_abilities(oracle_text: str) -> list[dict]:
    if not oracle_text:
        return []
    lines = [l for l in oracle_text.split("\n") if l.strip()]
    return [_classify_line(l) for l in lines]


def _face_text(card: dict, key: str) -> str:
    if key in card:
        return card[key] or ""
    faces = card.get("card_faces") or []
    return " // ".join(f.get(key, "") or "" for f in faces if f.get(key))


def to_card_record(card: dict, pull_date: str, source_version: str) -> dict:
    oracle_text = _face_text(card, "oracle_text")
    mana_cost = _face_text(card, "mana_cost")
    type_line = card.get("type_line", "")
    power = card.get("power")
    toughness = card.get("toughness")
    if power is None and card.get("card_faces"):
        power = card["card_faces"][0].get("power")
        toughness = card["card_faces"][0].get("toughness")

    is_creature = "Creature" in type_line
    is_land = "Land" in type_line
    supertypes, cardtypes_subtypes = [], type_line
    front = type_line.split("//")[0].strip()
    em_dash_split = front.split("—")
    left = em_dash_split[0].strip()
    subtypes_str = em_dash_split[1].strip() if len(em_dash_split) > 1 else ""
    known_supertypes = {"Legendary", "Basic", "Snow", "World", "Ongoing"}
    words = left.split()
    supertypes = [w for w in words if w in known_supertypes]
    cardtypes = [w for w in words if w not in known_supertypes]
    subtypes = subtypes_str.split() if subtypes_str else []

    is_mana_source = bool(re.search(r"\{T\}[^.]*:\s*Add ", oracle_text, re.IGNORECASE)) or (
        is_land and "add" in oracle_text.lower()
    ) or is_land

    notes = [
        "Ability `kind` classification is a rule-based heuristic text-line parser "
        "(sim/ingestion/scryfall.py), not manually reviewed. Verify before Level 4 "
        "exact-line validation use."
    ]

    return {
        "scryfall_id": card["id"],
        "mtgjson_uuid": None,
        "name": card["name"],
        "oracle_text": oracle_text,
        "type_line": type_line,
        "color_identity": card.get("color_identity", []),
        "mana_cost": mana_cost,
        "mana_value": card.get("cmc", 0),
        "characteristics": {
            "card_types": cardtypes,
            "subtypes": subtypes,
            "supertypes": supertypes,
            "is_mana_source": is_mana_source,
            "is_creature": is_creature,
            "is_permanent": any(t in type_line for t in ["Creature", "Artifact", "Enchantment", "Land", "Planeswalker", "Battle"]),
            "power": power,
            "toughness": toughness,
            "produces_convoke_eligible": is_creature,
            "notes": notes,
        },
        "abilities": parse_abilities(oracle_text),
        "tutor_restrictions": None,
        "commander_interactions": [],
        "rulings": card.get("_rulings", []),
        "legalities": card.get("legalities", {}),
        "source_pull_date": pull_date,
        "source_version": source_version,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    names_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    fetch_rulings_flag = "--rulings" in sys.argv

    names = json.loads(names_path.read_text())
    print(f"Fetching {len(names)} cards from Scryfall...", file=sys.stderr)
    found, not_found = fetch_collection(names)
    print(f"  found={len(found)} not_found={len(not_found)}", file=sys.stderr)
    if not_found:
        print(f"  NOT FOUND: {not_found}", file=sys.stderr)

    if fetch_rulings_flag:
        for card in found:
            card["_rulings"] = fetch_rulings(card["rulings_uri"])
            print(f"  rulings: {card['name']} ({len(card['_rulings'])})", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    pull_date = time.strftime("%Y-%m-%d")
    source_version = f"scryfall-live-{pull_date}"
    for card in found:
        record = to_card_record(card, pull_date, source_version)
        out_path = out_dir / f"{record['scryfall_id']}.json"
        out_path.write_text(json.dumps(record, indent=2) + "\n")

    print(f"Wrote {len(found)} card records to {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
