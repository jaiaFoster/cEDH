"""SIM-001 SOLO-002 — shared card model + mana/policy primitives.

Native (non-XMage) simulator, deliberately: XMage's JVM/AI overhead
(~2-16s/game observed in results/diagnostic/) makes 100,000-hand sampling
infeasible. This module is a scoped Level 1-2 structural/sequencing model
(exactly what sim/rules_engine/__init__.py's docstring always flagged as
eventually needed) covering ONLY what turn-1-3 opening-hand development
requires: land drops, mana-source taps (with summoning sickness for
creature sources), casting affordable spells, in dependency order. It does
NOT model combat, opponents, the stack, or triggered abilities beyond ETB
mana/type effects - those are out of scope for this question.

Card-level modeling is heuristic and documented per-card below, not a
formally verified rules engine - consistent with this project's established
"heuristic classification, acceptable for diagnostic purposes" standard.
Known simplifications (each is a deliberate, bounded approximation, not an
oversight):
  - City of Traitors' "sacrifice on 2nd land" downside is not modeled.
  - Gemstone Caverns is treated as an always-untapped any-color source
    (its real luck-counter/exile condition is close to this in an opening
    hand context, but not exact).
  - Exotic Orchard is treated as an any-color source (its real text depends
    on opponents' lands, irrelevant in a solo/goldfish model).
  - Deathrite Shaman's graveyard-land mana ability is not modeled (treated
    as a 0-mana card for sequencing purposes - it has no early graveyard
    fuel in an opening-hand context anyway).
  - Mana Vault's life-loss drawback and City of Brass/Mana Confluence's
    pain are tracked as life totals but never block a line.
  - Mox Amber requires a legendary creature/planeswalker already in play.
  - Fetchlands are treated as instantly cracking for a same-turn dual
    (both colors of their target), 1 life, no library-size modeling.
"""
import random
import re
from pathlib import Path
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

DECKLIST_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-v1.json"
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"
INTERACTIONS_DIR = REPO_ROOT / "interactions" / "verified"

COLORS = "WUBG"

# ---- mana cost parsing -----------------------------------------------

def parse_cost(mana_cost_str):
    """Returns (generic:int, pips:list[str|frozenset], x_count:int).
    pips entries are single-color strings, or frozenset for hybrid/phyrexian
    (treated as "any one of these, no extra cost distinction")."""
    if not mana_cost_str:
        return 0, [], 0
    tokens = re.findall(r"\{([^}]+)\}", mana_cost_str)
    generic = 0
    pips = []
    x_count = 0
    for t in tokens:
        if t == "X":
            x_count += 1
        elif t.isdigit():
            generic += int(t)
        elif t in COLORS:
            pips.append(t)
        elif "/" in t:
            parts = [p for p in t.split("/") if p in COLORS]
            if parts:
                pips.append(frozenset(parts))
            # {U/P} phyrexian-with-generic-color handled as that color pip
        elif t == "C":
            generic += 1  # colorless pip treated as generic for our purposes
        # ignore S (snow) etc, none present
    return generic, pips, x_count


# ---- land / mana source model ------------------------------------------

LAND_COLOR_SETS = {
    "Bayou": {"B", "G"}, "Boseiju, Who Endures": {"G"}, "City of Brass": {"W", "U", "B", "G"},
    "Command Tower": {"W", "U", "B", "G"}, "Exotic Orchard": {"W", "U", "B", "G"},
    "Flooded Strand": {"U", "W"}, "Gaea's Cradle": {"G"}, "Mana Confluence": {"W", "U", "B", "G"},
    "Marsh Flats": {"B", "W"}, "Minamo, School at Water's Edge": {"U"}, "Misty Rainforest": {"G", "U"},
    "Otawara, Soaring City": {"U"}, "Polluted Delta": {"B", "U"}, "Savannah": {"G", "W"},
    "Scrubland": {"B", "W"}, "Shifting Woodland": {"G"}, "Starting Town": {"W", "U", "B", "G"},
    "Talon Gates of Madara": {"W", "U", "B", "G"}, "Tropical Island": {"G", "U"},
    "Tundra": {"U", "W"}, "Underground Sea": {"B", "U"}, "Verdant Catacombs": {"B", "G"},
    "Windswept Heath": {"G", "W"}, "Wooded Foothills": {"G"}, "Gemstone Caverns": {"W", "U", "B", "G"},
}
GENERIC_LANDS = {"Ancient Tomb": 2, "City of Traitors": 2}
FETCH_LANDS = {"Flooded Strand", "Marsh Flats", "Misty Rainforest", "Polluted Delta", "Verdant Catacombs", "Windswept Heath", "Wooded Foothills"}
CRADLE = "Gaea's Cradle"

# nonland mana sources: name -> dict(kind, colors|generic, is_creature, one_shot, requires)
MANA_SOURCES = {
    "Avacyn's Pilgrim": {"colors": {"W"}, "creature": True},
    "Birds of Paradise": {"colors": set(COLORS), "creature": True},
    "Delighted Halfling": {"generic": 1, "creature": True},
    "Devoted Druid": {"colors": {"G"}, "creature": True},
    "Elves of Deep Shadow": {"colors": {"B"}, "creature": True},
    "Noble Hierarch": {"colors": {"W", "U", "G"}, "creature": True},
    "Chrome Mox": {"colors": set(COLORS), "creature": False, "requires_imprint": True},
    "Lotus Petal": {"colors": set(COLORS), "creature": False, "one_shot": True},
    "Mana Vault": {"generic": 3, "creature": False},
    "Mox Amber": {"colors": set(COLORS), "creature": False, "requires_legendary": True},
    "Mox Diamond": {"colors": set(COLORS), "creature": False, "requires_land_discard": True},
    "Sol Ring": {"generic": 2, "creature": False},
    "Elvish Spirit Guide": {"colors": {"G"}, "creature": False, "from_hand": True, "one_shot": True},
}

ACCELERATION = set(MANA_SOURCES.keys())

# ---- classification (reused/extended from solo_baseline_static.py) ----

TUTORS = {
    "Birthing Pod", "Chord of Calling", "Crop Rotation", "Demonic Tutor",
    "Eldritch Evolution", "Enlightened Tutor", "Finale of Devastation",
    "Imperial Seal", "Nature's Rhythm", "Ranger-Captain of Eos",
    "Sowing Mycospawn", "Spellseeker", "Survival of the Fittest", "Vampiric Tutor",
}

INTERACTION_CASTABLE = {
    # name: (class, mana_cost_str override if needed)
    "Fierce Guardianship": "free_commander", "Flare of Denial": "pitch", "Flusterstorm": "cheap_stack",
    "Force of Negation": "pitch", "Force of Will": "pitch", "Mental Misstep": "cheap_stack",
    "Pact of Negation": "free", "Swan Song": "cheap_stack", "Mindbreak Trap": "conditional_free",
    "Silence": "cheap_stack", "Misdirection": "pitch", "Commandeer": "pitch", "Subtlety": "pitch",
    "Veil of Summer": "cheap_stack", "Endurance": "pitch",
}

ENGINES = {
    # name: (class, is_premium_one_drop)
    "Mystic Remora": "card_advantage", "Esper Sentinel": "card_advantage",
    "Sylvan Library": "card_selection", "Faerie Mastermind": "card_advantage",
    "Kinnan, Bonder Prodigy": "mana_doubler", "Rhystic Study": "card_advantage",
    "Smothering Tithe": "tax_value", "Runic Armasaur": "card_advantage",
    "Heartwood Storyteller": "card_advantage", "Archivist of Oghma": "card_advantage",
    "Survival of the Fittest": "tutor_engine", "Birthing Pod": "tutor_engine",
    "Delney, Streetwise Lookout": "doubler", "Deathrite Shaman": "mana_gy",
    "Gaea's Cradle": "mana_engine", "Tymna the Weaver": "commander_engine",
    "Thrasios, Triton Hero": "commander_engine",
}
PREMIUM_ONE_DROP_ENGINES = {"Mystic Remora", "Esper Sentinel"}

COMMANDERS = {
    "Tymna the Weaver": {"cost": "{1}{W}{B}"},
    "Thrasios, Triton Hero": {"cost": "{G}{U}"},
}

# Mox-family / non-land acceleration a hand can become dependent on instead of a second land -
# used for the "mox_dependency" failure-mode tag (category 14). Deliberately excludes the mana
# dork creatures (Birds/Pilgrim/Halfling/Druid/Hierarch/Elves), which are lands-equivalent
# permanents, not one-shot/fragile resources.
MOX_FAMILY = {"Chrome Mox", "Lotus Petal", "Mox Amber", "Mox Diamond", "Sol Ring", "Mana Vault", "Elvish Spirit Guide"}

# Heuristic, per-card target classification for tutors (category 8: "what can it presently
# access" rather than treating a tutor as equivalent to every possible card). Tags drawn from:
# mana, land, cradle, engine, interaction, protection, combo_piece, creature. Approximate -
# manual classification consistent with this project's established "heuristic classification,
# acceptable for diagnostic purposes" standard (docs/VALIDATION_GATES.md Gate 1).
TUTOR_TARGETS = {
    "Demonic Tutor": frozenset({"mana", "land", "cradle", "engine", "interaction", "protection", "combo_piece", "creature"}),
    "Vampiric Tutor": frozenset({"mana", "land", "cradle", "engine", "interaction", "protection", "combo_piece", "creature"}),
    "Imperial Seal": frozenset({"mana", "land", "cradle", "engine", "interaction", "protection", "combo_piece", "creature"}),
    "Enlightened Tutor": frozenset({"mana", "engine"}),
    "Chord of Calling": frozenset({"engine", "combo_piece", "creature"}),
    "Eldritch Evolution": frozenset({"engine", "combo_piece", "creature"}),
    "Finale of Devastation": frozenset({"engine", "combo_piece", "creature"}),
    "Nature's Rhythm": frozenset({"engine", "combo_piece", "creature"}),
    "Survival of the Fittest": frozenset({"engine", "combo_piece", "creature"}),
    "Birthing Pod": frozenset({"engine", "combo_piece", "creature"}),
    "Ranger-Captain of Eos": frozenset({"creature", "protection"}),
    "Spellseeker": frozenset({"interaction", "protection"}),
    "Crop Rotation": frozenset({"land", "cradle"}),
    "Sowing Mycospawn": frozenset({"land", "cradle"}),
}


def load_deck_cards():
    # sim/validation/run_classification.py's load_frozen_deck() is "the ONLY sanctioned way to
    # load a decklist for a DECK_BACKED_* run" (its own module docstring) - it does everything a
    # bare hash-equality assert would (docs/RUN_CLASSIFICATION.md requirement 3: hash match,
    # hash presence, non-provisional path, no synthetic-fixture markers, every card's
    # scryfall_id resolves in the declared oracle_data_version cache, no placeholder names).
    from sim.validation.run_classification import load_frozen_deck
    payload = load_frozen_deck(DECKLIST_PATH, CARDS_CACHE)
    cards_by_id = {}
    for p in CARDS_CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        cards_by_id[d["scryfall_id"]] = d
    rows = {}
    for c in payload["cards"]:
        card = cards_by_id[c["scryfall_id"]]
        rows[c["name"]] = {
            "name": c["name"], "type": card.get("type_line", ""), "text": card.get("oracle_text", "") or "",
            "mana_cost": card.get("mana_cost") or "", "cmc": card.get("cmc") or 0,
        }
    return payload, rows


def deck_provenance_fields(payload):
    """Common provenance block for every SOLO-002 output file - all of these runs are real
    turn-by-turn gameplay (land drops, casts, sequencing) against no opponent with the actual
    subject deck, which is docs/RUN_CLASSIFICATION.md's definition of DECK_BACKED_GOLDFISH, not
    STATIC_ANALYSIS ("Level 0 hypergeometric/probability calculation, no gameplay" - that label
    belongs to sim/analysis/solo_baseline_static.py's pure combinatorial math, not this module).
    Matches the existing DECK_BACKED_GOLDFISH precedent already used by
    results/solo_baseline/solo-goldfish-batch002-realhands-raw_snapshots.json.
    """
    return {
        "run_class": "DECK_BACKED_GOLDFISH",
        "evidence_type": "goldfish",
        "subject_deck_version": payload["deck_version"],
        "subject_deck_hash": payload["deck_hash"],
        "subject_deck_card_count": len(payload["cards"]),
        "commander_identities": list(payload["commanders"]),
        "basics_substituted": False,
    }


def print_run_banner():
    from sim.validation.run_classification import format_run_banner, RunClass
    print(format_run_banner(RunClass.DECK_BACKED_GOLDFISH, deck_representative=True, synthetic_mana=False))


def load_deterministic_combos():
    combos = []
    for f in sorted(INTERACTIONS_DIR.glob("INT-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("conditional") is False:
            combos.append({"id": d["id"], "cards": [c["name"] for c in d["cards"]]})
    return combos
