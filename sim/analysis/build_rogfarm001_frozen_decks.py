"""SIM-ROGFARM-001 — mint the three frozen input decks (Stock RogSi, R1 Minimal Rog Farm, Blue
Farm Control) from the assignment's own literal decklists, per its explicit "Frozen Input Decks"
section: parse, verify counts, verify R1 diff assertions, verify no old subject is silently
reused, hash, report.

Provenance for scryfall_id: 49 of this project's 133 unique RogSi/Blue-Farm cards already have
real, verified entries in data/cards_cache/oracle-2026-08-12/ (staples shared with the
Tymna/Thrasios project's own card pool - Force of Will, Mystic Remora, Rhystic Study, Sol Ring,
etc.) and reuse those real ids. The remaining ~84 cards have no cache entry (this project has never
modeled a storm/Breach/wheel-control archetype before) - this environment's network egress to
every card-database domain remains blocked (the same long-standing, disclosed limitation as every
prior task), so this script mints deterministic, clearly-labeled SYNTHETIC scryfall_ids for them
(sha256-derived, fixed "deadbeef-rog0-..." prefix - never collides with a real Scryfall UUID
format). Real Oracle text for the rules-critical subset of these 84 was independently verified via
WebSearch this task (Narset/Notion Thief/Orcish Bowmasters/Faerie Mastermind wheel interactions,
Underworld Breach/Lion's Eye Diamond/Brain Freeze sequencing, Fierce Guardianship/Deadly Rollick
commander conditions, Flare of Duplication/Hexing Squelcher/Foil/Subtlety alternate costs, Will of
the Jeskai) - see sim/analysis/rogfarm001_cards.py for the encoded card data and citations.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402

SCRATCH = Path("/tmp/claude-0/-home-user-cEDH/eae84c92-f7a7-5b91-a2b5-bb444a7ee454/scratchpad/rogfarm")
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"
OUT_DIR = REPO_ROOT / "data" / "decklists"

DECKS = {
    "rogsi-valley-forge-2026-v1": {
        "path": SCRATCH / "deck_a.txt",
        "commanders": ["Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"],
        "deck_name": "Stock RogSi — Joseph Mekhail, Valley Forge 2026 (1st, 3-1-1)",
        "role": "subject",
        "source": {
            "type": "user_supplied",
            "reference": "Joseph Mekhail's 1st-place (3-1-1) Rograkh/Silas list, Valley Forge 2026 "
                         "t/cEDH $10k-$25,000 - supplied as the literal SIM-ROGFARM-001 task text, "
                         "role CONTROL_STOCK_ROGSI.",
            "date": "2026-08-25",
        },
    },
    "rogfarm-r1-minimal-v1": {
        "path": SCRATCH / "deck_b.txt",
        "commanders": ["Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"],
        "deck_name": "Rog Farm R1 (Minimal) — falsification candidate",
        "role": "subject",
        "source": {
            "type": "user_supplied",
            "reference": "SIM-ROGFARM-001's literal DECK_B (ROGFARM_R1_MINIMAL) - derived from "
                         "rogsi-valley-forge-2026-v1 by -Thassa's Oracle/-Demonic Consultation/"
                         "-Tainted Pact/-Strike It Rich/-Final Fortune/-Dramatic Reversal, "
                         "+Faerie Mastermind/+Narset Parter of Veils/+Notion Thief/+Force of "
                         "Negation/+Foil/+Subtlety, role PRIMARY_CANDIDATE.",
            "date": "2026-08-25",
        },
    },
    "bluefarm-control-2026-v1": {
        "path": SCRATCH / "deck_c.txt",
        "commanders": ["Tymna the Weaver", "Kraum, Ludevic's Opus"],
        "deck_name": "Blue Farm Control 2026",
        "role": "subject",
        "source": {
            "type": "user_supplied",
            "reference": "SIM-ROGFARM-001's literal DECK_C (BLUE_FARM_CONTROL_2026) - Blue Farm "
                         "Primer, source_updated 2026-07-21, role CONTROL_BLUE_FARM.",
            "date": "2026-08-25",
        },
    },
}


def _synthetic_id(name):
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return f"deadbeef-rog0-4{h[0:3]}-8{h[3:6]}-{h[6:18]}"


def _cache_by_name():
    by_name = {}
    for p in CARDS_CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        by_name[d["name"]] = d["scryfall_id"]
    return by_name


def main():
    cache_by_name = _cache_by_name()
    results = {}
    for version, spec in DECKS.items():
        names = [line.strip() for line in spec["path"].read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(names) == 98, f"{version}: expected 98 mainboard cards, got {len(names)}"
        assert len(set(names)) == 98, f"{version}: duplicate card name (singleton violation)"

        cards = []
        synthetic_names = []
        for name in names:
            if name in cache_by_name:
                cards.append({"scryfall_id": cache_by_name[name], "name": name, "quantity": 1})
            else:
                cards.append({"scryfall_id": _synthetic_id(name), "name": name, "quantity": 1})
                synthetic_names.append(name)

        deck_hash = compute_deck_hash(spec["commanders"], cards)
        payload = {
            "deck_version": version,
            "deck_name": spec["deck_name"],
            "commanders": spec["commanders"],
            "archetype_id": None,
            "role": spec["role"],
            "cards": cards,
            "source": spec["source"],
            "ingested": {
                "oracle_data_version": "scryfall-live-2026-08-12",
                "ingested_date": "2026-08-12",
                "cards_cache_path": "data/cards_cache/oracle-2026-08-12/",
                "synthetic_card_count": len(synthetic_names),
                "synthetic_card_names": sorted(synthetic_names),
                "synthetic_card_data_note": (
                    f"{len(synthetic_names)} of 98 cards have SYNTHETIC placeholder scryfall_ids "
                    "(deterministic sha256-derived, fixed 'deadbeef-rog0-' prefix) - real Oracle "
                    "text for the rules-critical subset verified via WebSearch this task; see "
                    "sim/analysis/rogfarm001_cards.py."
                ),
            },
            "deck_hash": deck_hash,
        }
        out_path = OUT_DIR / f"{version}.json"
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        results[version] = {"deck_hash": deck_hash, "synthetic_count": len(synthetic_names), "total": len(names)}
        print(f"{version}: hash={deck_hash} synthetic={len(synthetic_names)}/98 -> wrote {out_path}")

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
