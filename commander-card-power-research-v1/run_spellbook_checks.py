"""Sparse live official-API checks; retain original responses and hashes."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import time

from spellbook_integration import SpellbookClient, classify_response, mark_controller_review

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "commander-league-card-point-calibration"


def main():
    client = SpellbookClient("CommanderLeagueResearch/1.0 (github.com/jaiaFoster/cEDH)")
    decks = json.loads((BASE / "data/clean/precons.json").read_text())
    destination = ROOT / "data/spellbook"
    destination.mkdir(exist_ok=True)
    summaries = []
    for name in ("Mutant Menace", "Science!", "Explorers of the Deep", "Necron Dynasties", "From Cute to Brute"):
        deck = next(d for d in decks if d["name"] == name)
        commanders = set(deck["commander_ids"])
        payload = {"main": [{"card": oid, "quantity": qty} for oid, qty in deck["counts"].items() if oid not in commanders],
                   "commanders": [{"card": oid, "quantity": deck["counts"][oid]} for oid in commanders]}
        slug = name.lower().replace(" ", "_").replace("!", "")
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            raw = client.find_combos(payload)
            second = client.find_combos(payload)  # One repeat to measure snapshot determinism.
            output = {"input": payload, "response": raw, "classified": classify_response(raw)}
            encoded = json.dumps(output, sort_keys=True).encode()
            (destination / (slug + ".json")).write_bytes(encoded)
            summaries.append({"deck": name, "retrieved_at": started,
                "url": "https://backend.commanderspellbook.com/find-my-combos/",
                "payload_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
                "response_sha256": hashlib.sha256(encoded).hexdigest(),
                "deterministic_repeat": raw == second,
                "categories": {k: len(v) for k, v in raw["categories"].items() if isinstance(v, list)},
                "status": "success"})
        except Exception as error:
            summaries.append({"deck": name, "retrieved_at": started, "status": "failed", "error": str(error)})
        time.sleep(1)
    # Positive component-match control, split across hypothetical teammates.
    # This is a two-card test fixture, not a legal 100-card deck or controller proof.
    with gzip.open(BASE / "data/raw/oracle_cards.jsonl.gz", "rt") as stream:
        cards = [json.loads(line) for line in stream]
    lookup = {c["name"]: c["oracle_id"] for c in cards if c.get("oracle_id")}
    blood, bond = lookup["Exquisite Blood"], lookup["Sanguine Bond"]
    payload = {"main": [{"card": blood, "quantity": 1}, {"card": bond, "quantity": 1}], "commanders": []}
    try:
        raw = client.find_combos(payload)
        records = mark_controller_review(classify_response(raw), {"main": {blood: 1}}, {"main": {bond: 1}})
        (destination / "cross_team_positive_control.json").write_text(json.dumps({"input": payload, "raw": raw, "records": records}, indent=2))
        summaries.append({"deck": "cross-team positive component fixture", "status": "success",
            "included": sum(r["category"] == "included" for r in records),
            "controller_functionality": "unverified"})
    except Exception as error:
        summaries.append({"deck": "cross-team positive component fixture", "status": "failed", "error": str(error)})
    (destination / "summary.json").write_text(json.dumps(summaries, indent=2))
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
