"""Commander Spellbook ingestion adapter (Tier 3, docs/SOURCES.md).

Per charter Layer 2 / "Interaction discovery pass": Commander Spellbook is a
seed and validation source, not the complete interaction graph. This module
queries the /variants endpoint once per card in the subject deck (the
find-my-combos endpoint requires auth we don't have; the public variants
search with a `card=` filter does not), dedupes the results, and classifies
each variant as:

  - "fully_in_deck": every card the variant uses is in the subject decklist
    (by name) -> a strong CANDIDATE interaction, written to
    interactions/candidate/. Still requires Phase 3 exact-line validation
    before it can move to interactions/verified/ - this module only proves
    "Commander Spellbook believes this line exists and every piece is in
    our list," not "we've independently confirmed the rules text supports
    it here."
  - "one_card_away": the variant uses exactly one card not in the deck ->
    logged separately as a deckbuilding note, NOT written as a candidate
    interaction (it isn't a real line in this exact 98).

Every emitted interactions/candidate/ record cites the Spellbook variant ID
and description verbatim, per charter's requirement to record supporting
sources for interaction claims.

Usage:
    python3 sim/ingestion/spellbook.py <card_names.json> <output_dir>
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

VARIANTS_URL = "https://backend.commanderspellbook.com/variants"
REQUEST_DELAY_S = 0.15


def _curl_json(url: str) -> dict:
    result = subprocess.run(
        ["curl", "-sS", "--max-time", "20", "-H", "Accept: application/json", url],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed ({result.returncode}) for {url}: {result.stderr}")
    return json.loads(result.stdout)


def fetch_variants_for_card(name: str) -> list[dict]:
    variants = []
    url = f"{VARIANTS_URL}?q={quote('card=' + json.dumps(name))}&limit=100"
    while url:
        page = _curl_json(url)
        variants.extend(page.get("results", []))
        url = page.get("next")
        time.sleep(REQUEST_DELAY_S)
    return variants


def classify_variant(variant: dict, deck_names: set[str]) -> tuple[str, set[str]]:
    uses_names = {u["card"]["name"].split(" // ")[0] for u in variant.get("uses", [])}
    missing = uses_names - deck_names
    if not missing:
        return "fully_in_deck", missing
    if len(missing) == 1:
        return "one_card_away", missing
    return "not_close", missing


def to_interaction_record(variant: dict, next_id: int, scryfall_id_by_name: dict[str, str]) -> dict:
    cards = [
        {
            "scryfall_id": scryfall_id_by_name.get(u["card"]["name"].split(" // ")[0], u["card"]["oracleId"]),
            "name": u["card"]["name"].split(" // ")[0],
            "role": "commander" if u.get("mustBeCommander") else "piece",
        }
        for u in variant.get("uses", [])
    ]
    produces = variant.get("produces", [])
    result_summary = ", ".join(p["feature"]["name"] for p in produces) or "(no produces field from Spellbook)"
    is_win = any("win" in p["feature"]["name"].lower() or "damage" in p["feature"]["name"].lower() for p in produces)

    other_notes = []
    if variant.get("notablePrerequisites"):
        other_notes.append(f"Notable prerequisites: {variant['notablePrerequisites']}")
    if variant.get("description"):
        other_notes.append(f"Spellbook description: {variant['description']}")
    if variant.get("identity"):
        other_notes.append(f"Spellbook color identity: {variant['identity']}")
    if variant.get("popularity") is not None:
        other_notes.append(f"Spellbook popularity score: {variant['popularity']}")
    commander_legal = (variant.get("legalities") or {}).get("commander")
    if commander_legal is not None:
        other_notes.append(f"Spellbook-reported Commander legal: {commander_legal}")

    return {
        "id": f"INT-{next_id:04d}",
        "status": "candidate",
        "name": f"[Spellbook {variant['id']}] {result_summary}",
        "cards": cards,
        "prerequisites": {
            "zones": sorted({loc for u in variant.get("uses", []) for loc in u.get("zoneLocations", [])}),
            "mana_available": variant.get("manaNeeded") or None,
            "timing": variant.get("easyPrerequisites") or "not specified by Spellbook",
            "targets_required": [],
            "other": other_notes,
        },
        "result": {
            "summary": result_summary,
            "is_win_condition": is_win,
            "is_loop": "repeat" in (variant.get("description") or "").lower() or "loop" in result_summary.lower(),
            "loop_termination": None,
        },
        "deterministic": False,  # never true for a candidate - only Phase 3/Level 4 validation can set this
        "verification": None,
        "sources": [
            {"type": "commander_spellbook", "reference": f"https://commanderspellbook.com/combo/{variant['id']}"},
        ],
        "discovered_via": "commander_spellbook_pull",
        "coverage_backlog_ref": "SIM-0005",
    }


def load_scryfall_id_map(cards_cache_dir: Path) -> dict[str, str]:
    mapping = {}
    for p in cards_cache_dir.glob("*.json"):
        d = json.loads(p.read_text())
        for face_name in d["name"].split(" // "):
            mapping[face_name] = d["scryfall_id"]
    return mapping


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("Also requires a third arg: path to the card cache dir for scryfall_id lookups.", file=sys.stderr)
        sys.exit(1)
    names_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    cards_cache_dir = Path(sys.argv[3])
    deck_names = set(json.loads(names_path.read_text()))
    scryfall_id_by_name = load_scryfall_id_map(cards_cache_dir)

    all_variants = {}
    for i, name in enumerate(sorted(deck_names)):
        print(f"[{i + 1}/{len(deck_names)}] querying: {name}", file=sys.stderr)
        for v in fetch_variants_for_card(name):
            all_variants[v["id"]] = v

    print(f"Total unique variants touching this deck: {len(all_variants)}", file=sys.stderr)

    fully_in_deck, one_away, not_close = [], [], []
    for v in all_variants.values():
        classification, missing = classify_variant(v, deck_names)
        if classification == "fully_in_deck":
            fully_in_deck.append(v)
        elif classification == "one_card_away":
            one_away.append((v, missing))
        else:
            not_close.append(v)

    print(f"fully_in_deck={len(fully_in_deck)} one_card_away={len(one_away)} not_close={len(not_close)}", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    for i, v in enumerate(fully_in_deck, start=1):
        record = to_interaction_record(v, i, scryfall_id_by_name)
        (out_dir / f"{record['id']}.json").write_text(json.dumps(record, indent=2) + "\n")

    one_away_path = out_dir.parent / "one_card_away_from_deck.json"
    one_away_path.write_text(json.dumps(
        [{"variant_id": v["id"], "description": v.get("description"),
          "missing_card": sorted(missing)[0], "produces": [p["feature"]["name"] for p in v.get("produces", [])],
          "popularity": v.get("popularity")}
         for v, missing in one_away],
        indent=2,
    ) + "\n")

    print(f"Wrote {len(fully_in_deck)} candidate interactions to {out_dir}", file=sys.stderr)
    print(f"Wrote {len(one_away)} one-card-away notes to {one_away_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
