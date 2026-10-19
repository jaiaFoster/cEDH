"""Commander Spellbook candidate analyzer. No card-price adjustments.
MIT client implementation; upstream data terms remain separate.
Official API: https://spacecowmedia.github.io/commander-spellbook-backend/api.html
"""
import json, re, time, urllib.request, urllib.error
from collections import Counter

API = "https://backend.commanderspellbook.com"

def parse_decklist(text):
    """Moxfield text subset. Explicit Commander section required for commander roles."""
    main, commanders = Counter(), Counter()
    target = main
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.lstrip("# ").rstrip(":").lower() in ("commander", "commanders", "deck", "main", "mainboard"):
                line = line.lstrip("# ")
            else:
                continue
        header = line.rstrip(":").lower()
        if header in ("commander", "commanders"):
            target = commanders
            continue
        if header in ("deck", "main", "mainboard"):
            target = main
            continue
        if header in ("sideboard", "maybeboard", "considering"):
            raise ValueError("Remove non-main sections before analysis")
        match = re.match(r"^(\d+)[xX]?\s+(.+?)\s*$", line)
        if not match:
            raise ValueError(f"Unrecognized line {line_number}: {raw}")
        quantity, name = int(match[1]), match[2]
        # Printing annotations only; Oracle canonicalization is caller supplied.
        name = re.sub(r"\s+\([A-Za-z0-9]+\)\s+\S+(?:\s+\*[^*]+\*)?$", "", name)
        if quantity < 1:
            raise ValueError("Quantities must be positive")
        target[name] += quantity
    if not main and not commanders:
        raise ValueError("Empty decklist")
    return {"main": dict(main), "commanders": dict(commanders)}

def normalize_payload(deck, resolve):
    """Resolve all names locally; reject unknown cards rather than server dropping them.
    resolve(name) returns stable Oracle ID, or raises KeyError.
    """
    result = {}
    for section in ("main", "commanders"):
        merged = Counter()
        for name, quantity in deck.get(section, {}).items():
            if not isinstance(quantity, int) or quantity < 1:
                raise ValueError("Positive integer quantities required")
            oracle_id = resolve(name)
            if not oracle_id:
                raise KeyError(name)
            merged[oracle_id] += quantity
        result[section] = [{"card": key, "quantity": value}
                           for key, value in sorted(merged.items())]
    return result

class SpellbookClient:
    def __init__(self, user_agent, transport=None, sleep=time.sleep, retries=3):
        if not user_agent.strip():
            raise ValueError("Supply a named User-Agent with contact information")
        self.user_agent, self.sleep, self.retries = user_agent, sleep, retries
        self.transport = transport or self._http

    def _http(self, path, payload):
        request = urllib.request.Request(API + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "User-Agent": self.user_agent}, method="POST")
        with urllib.request.urlopen(request, timeout=40) as response:
            return json.load(response)

    def find_combos(self, payload):
        # Official maximum page size; repeat POST body for subsequent pages.
        path = "/find-my-combos/?limit=1000"
        buckets = {}
        pages = 0
        seen = set()
        while path:
            if path in seen:
                raise ValueError("Pagination cycle")
            seen.add(path)
            pages += 1
            if pages > 100:
                raise ValueError("Pagination safety limit")
            for attempt in range(self.retries + 1):
                try:
                    response = self.transport(path, payload)
                    break
                except urllib.error.HTTPError as error:
                    if error.code not in (429, 502, 503, 504) or attempt == self.retries:
                        raise
                    value = error.headers.get("Retry-After", "") if error.headers else ""
                    delay = float(value) if value.isdigit() else min(60, 2 ** attempt)
                    self.sleep(delay)
            data = response.get("results", response)
            if not isinstance(data, dict):
                raise ValueError("Unexpected API schema; expected categorized result object")
            if not isinstance(data.get("included"), list):
                raise ValueError("Unexpected API schema; missing included-variants bucket")
            for key, values in data.items():
                if isinstance(values, list):
                    buckets.setdefault(key, []).extend(values)
                else:
                    buckets.setdefault(key, values)
            next_url = response.get("next")
            if next_url:
                from urllib.parse import urlparse
                parsed = urlparse(next_url)
                if parsed.netloc and (parsed.scheme != "https" or
                                     parsed.netloc != "backend.commanderspellbook.com"):
                    raise ValueError("Unexpected pagination host")
                path = parsed.path + ("?" + parsed.query if parsed.query else "")
            else:
                path = None
        return {"categories": buckets, "pages": pages}

def classify_response(response):
    """Component matching does not establish executable conditions or a win turn."""
    records = []
    for category, variants in response["categories"].items():
        if not isinstance(variants, list):
            continue
        for variant in variants:
            uses = variant.get("uses", [])
            outcomes = [x.get("feature", {}).get("name", "") for x in variant.get("produces", [])]
            outcome_text = " ".join(outcomes).lower()
            requires_commander = any(x.get("mustBeCommander", False) for x in
                                      uses + variant.get("requires", []))
            components = [{
                "oracle_id": item.get("card", {}).get("oracleId"),
                "name": item.get("card", {}).get("name"),
                "quantity": item.get("quantity", 1),
                "commander_required": item.get("mustBeCommander", False),
                "zone_locations": item.get("zoneLocations"),
                "battlefield_state": item.get("battlefieldCardState"),
                "graveyard_state": item.get("graveyardCardState"),
                "exile_state": item.get("exileCardState"),
                "library_state": item.get("libraryCardState"),
            } for item in uses]
            unresolved = (bool(variant.get("requires")) or
                          variant.get("easyPrerequisites") is None or
                          variant.get("notablePrerequisites") is None or
                          variant.get("description") is None)
            if category == "included":
                status = "component_complete_unresolved" if unresolved else "component_complete"
            elif category.startswith("almostIncluded") or category.startswith("almost_included"):
                status = "missing_components_or_conditions"
            else:
                status = "commander_role_change_or_unsupported"
            records.append({
                "id": variant.get("id"), "category": category, "status": status,
                "url": "https://commanderspellbook.com/combo/" + str(variant.get("id")) + "/",
                "components": components, "templates": variant.get("requires", []),
                "easy_prerequisites": variant.get("easyPrerequisites"),
                "notable_prerequisites": variant.get("notablePrerequisites"),
                "mana_needed": variant.get("manaNeeded"),
                "mana_value_needed": variant.get("manaValueNeeded"),
                "description": variant.get("description"), "outcomes": outcomes,
                "requires_commander": requires_commander,
                "potential_win_outcome": any(x in outcome_text for x in
                    ("win the game", "lose the game", "infinite damage", "infinite life loss")),
                "early_win": "not_established_by_component_match",
                "lock_candidate": any(x in outcome_text for x in
                    ("lock", "skip", "extra turn", "prevent")),
                "mass_land_denial_candidate": any(x in outcome_text for x in
                    ("land destruction", "destroy all lands", "mass land")),
                "manual_review": True,
                "construction_point_adjustment": 0,
            })
    return records

def team_candidates(deck_a, deck_b):
    """Oracle-ID normalized counters. Union is a candidate search, not legal proof.
    Union commanders are hypothetical; actual Commander legality remains individual.
    """
    union = {}
    for section in ("main", "commanders"):
        union[section] = dict(Counter(deck_a.get(section, {})) +
                              Counter(deck_b.get(section, {})))
    return union

def mark_controller_review(records, deck_a, deck_b):
    a = Counter(deck_a.get("main", {})) + Counter(deck_a.get("commanders", {}))
    b = Counter(deck_b.get("main", {})) + Counter(deck_b.get("commanders", {}))
    result = []
    for record in records:
        needed = Counter()
        for card in record["components"]:
            if card["oracle_id"]:
                needed[card["oracle_id"]] += card["quantity"]
        fits_a = bool(needed) and all(a[k] >= v for k, v in needed.items())
        fits_b = bool(needed) and all(b[k] >= v for k, v in needed.items())
        result.append({**record,
            "cross_deck_components_required": bool(needed) and not fits_a and not fits_b,
            "controller_review_required": True,
            "team_functionality": "unverified",
            "review_notes": [
                "Check ownership and controller restrictions, zones and mana sharing.",
                "Check commander access separately for each player.",
                "Templates and prerequisites can invalidate apparent union matches."
            ]})
    return result


def cli():
    import argparse
    import gzip
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("--team-b", type=Path)
    parser.add_argument("--oracle-data", type=Path, default=Path(__file__).resolve().parent.parent /
                        "commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with gzip.open(args.oracle_data, "rt") as stream:
        cards = [json.loads(line) for line in stream]
    aliases = {card["name"].casefold(): card["oracle_id"] for card in cards if card.get("oracle_id")}
    def resolve(name):
        return aliases[name.casefold()]
    deck_a = parse_decklist(args.deck.read_text())
    normalized_a = normalize_payload(deck_a, resolve)
    a = {k: {item["card"]: item["quantity"] for item in v} for k, v in normalized_a.items()}
    b = None
    payload = normalized_a
    if args.team_b:
        normalized_b = normalize_payload(parse_decklist(args.team_b.read_text()), resolve)
        b = {k: {item["card"]: item["quantity"] for item in v} for k, v in normalized_b.items()}
        payload = normalize_payload(team_candidates(a, b), lambda value: value)
    client = SpellbookClient("CommanderLeagueResearch/1.0 (github.com/jaiaFoster/cEDH)")
    raw = client.find_combos(payload)
    records = classify_response(raw)
    if b is not None:
        records = mark_controller_review(records, a, b)
    output = {"credit": "Commander Spellbook — https://commanderspellbook.com/",
              "records": records, "raw": raw, "construction_point_adjustment": 0}
    text = json.dumps(output, indent=2)
    if args.output:
        args.output.write_text(text)
    else:
        print(text)


if __name__ == "__main__":
    cli()
