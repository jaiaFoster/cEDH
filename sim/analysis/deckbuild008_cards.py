"""SIM-DECKBUILD-008 — card registry: Oracle-cache characteristics + hand-encoded mechanics.

Every characteristic (type line, mana cost, mana value) is read from the fresh Scryfall cache
data/cards_cache/oracle-2026-10-30/. Mechanics the solver needs (what a card taps for, what a
tutor can find and where it puts it, which combo role a card plays) are hand-encoded below from
the cached Oracle text; each encoding that materially affects a result has a regression test in
rules_tests/regression/test_deckbuild008_rules.py.

Rules decisions encoded here (verified against Oracle text, 2026-10-30):
  * Deathrite Shaman's mana ability TARGETS a land card in a graveyard, so it is not a mana
    ability (CR 605.1a) and is not "tapping for mana" (CR 106.12): Kinnan, Bonder Prodigy and
    Badgermole Cub DO NOT add mana when it is activated. It also produces nothing unless a land
    card is in a graveyard. (Supersedes DECKBUILD-007's dork treatment.)
  * Devoted Druid taps twice per turn and survives (G, -1/-1 untap, G); a third activation kills
    it before the untap resolves.
  * Swift Reconfiguration makes Druid a noncreature Vehicle, so Machine God's Effigy (copies a
    CREATURE) cannot copy a Swift-enchanted Druid.
  * Machine God's Effigy entering as a copy of a creature Devoted Druid is itself a noncreature
    Druid with an extra "{T}: Add {U}" -> infinite G and U on its own.
  * Hermit Druid reveals until a BASIC land: this deck has zero basics, so one activation puts the
    whole library into the graveyard. Divining Witch naming a card not in the library exiles it.
  * Shang-Chi, Master of Kung Fu lets creature abilities (itself included) ignore summoning
    sickness; its {T} mana is restricted to creature-source abilities.
  * Spellseeker finds instants/sorceries with MV <= 2. X spells have X = 0 in the library, so
    Finale of Devastation and Nature's Rhythm (MV 2) and Neoform are legal targets.
  * Tainted Pact in a singleton deck exiles the entire library if the caster declines every card.
  * Thrasios: {4}: scry 1, reveal top; nonland -> draw. A card a top-tutor put on top is drawn.
    Training Grounds / Biomancer's Familiar reduce it to {2}.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-10-30"
FROZEN = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-creature-factory-deckbuild008-v1.json"

COLORS = "WUBG"
ANY = frozenset(COLORS)
C = frozenset({"C"})
W, U, B, G = (frozenset({c}) for c in COLORS)
COMMANDERS = ("Thrasios, Triton Hero", "Tymna the Weaver")
BLANK = "Blank Slot (ablation placeholder)"


# ---- Oracle characteristics -------------------------------------------------------------------

@lru_cache(maxsize=1)
def oracle_rows():
    rows = {}
    for p in CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        rows[d["name"]] = {"type": d["type_line"], "cost": d["mana_cost"] or "",
                           "mv": int(d["mana_value"] or 0), "text": d["oracle_text"] or ""}
    # Synthetic inert slot used ONLY by ablation runs (never in a recommended list): replacing a
    # card with BLANK measures that card's marginal contribution with every other slot fixed.
    rows[BLANK] = {"type": "Blank", "cost": "{20}", "mv": 20, "text": ""}
    return rows


def card(name):
    return oracle_rows()[name]


def is_creature(name):
    t = card(name)["type"].split("//")[0]
    return "Creature" in t


def is_land(name):
    t = card(name)["type"]
    if name == "Sink into Stupor // Soporific Springs":
        return True  # MDFC: counted as a land for mana density (assignment instruction)
    return "Land" in t.split("//")[0]


def is_instant_or_sorcery(name):
    t = card(name)["type"].split("//")[0]
    return "Instant" in t or "Sorcery" in t


def is_instant(name):
    return "Instant" in card(name)["type"].split("//")[0]


def is_artifact_or_enchantment(name):
    t = card(name)["type"].split("//")[0]
    return "Artifact" in t or "Enchantment" in t


def is_green(name):
    return "G" in card(name)["cost"].replace("G/P", "G")


def is_blue(name):
    return "U" in card(name)["cost"]


def is_legendary(name):
    return "Legendary" in card(name)["type"]


def mv(name):
    return card(name)["mv"]


_PIP_RE = re.compile(r"\{([^}]+)\}")


@lru_cache(maxsize=None)
def parse_cost(cost):
    """-> (generic, pips tuple of frozensets, has_x). Phyrexian pips are encoded with a 'P'."""
    generic, pips, has_x = 0, [], False
    for sym in _PIP_RE.findall(cost.split("//")[0]):
        if sym.isdigit():
            generic += int(sym)
        elif sym == "X":
            has_x = True
        elif "/" in sym:
            parts = sym.split("/")
            pips.append(frozenset(p for p in parts))  # e.g. {G,P} or {B,G}
        elif sym in COLORS:
            pips.append(frozenset({sym}))
        elif sym == "C":
            pips.append(C)
    return generic, tuple(pips), has_x


def cost_of(name, x=0):
    g, pips, _ = parse_cost(card(name)["cost"])
    return g + x, pips


# ---- mana production ----------------------------------------------------------------------------
# Land units: list of colour sets, one per mana. Fetchlands resolve to a dual in the goldfish.
LAND_UNITS = {
    "Ancient Tomb": [C, C], "City of Traitors": [C, C],
    "Command Tower": [ANY], "City of Brass": [ANY], "Mana Confluence": [ANY],
    "Exotic Orchard": [ANY],  # opponent-dependent; any-colour assumption disclosed in report
    "Starting Town": [ANY], "Tarnished Citadel": [ANY],
    "Talon Gates of Madara": [C],  # its any-colour mode is a 1-for-1 filter, not net mana
    "Emergence Zone": [C], "Otawara, Soaring City": [U], "Boseiju, Who Endures": [G],
    "Sink into Stupor // Soporific Springs": [U],
    "Gemstone Caverns": [C],  # any colour only with a luck counter (on the draw, opening hand)
    "Bayou": [frozenset("BG")], "Savannah": [frozenset("GW")], "Scrubland": [frozenset("WB")],
    "Tropical Island": [frozenset("GU")], "Tundra": [frozenset("WU")],
    "Underground Sea": [frozenset("UB")],
    "Gaea's Cradle": "cradle",
}
FETCH_TARGETS = {
    "Flooded Strand": {"Plains", "Island"}, "Marsh Flats": {"Plains", "Swamp"},
    "Misty Rainforest": {"Forest", "Island"}, "Polluted Delta": {"Island", "Swamp"},
    "Verdant Catacombs": {"Swamp", "Forest"}, "Windswept Heath": {"Forest", "Plains"},
    "Wooded Foothills": {"Mountain", "Forest"},
}
DUAL_TYPES = {"Bayou": {"Swamp", "Forest"}, "Savannah": {"Forest", "Plains"},
              "Scrubland": {"Plains", "Swamp"}, "Tropical Island": {"Forest", "Island"},
              "Tundra": {"Plains", "Island"}, "Underground Sea": {"Island", "Swamp"}}
FOREST_LANDS = {n for n, t in DUAL_TYPES.items() if "Forest" in t}

# Nonland mana permanents. kind: dork (creature, summoning sick), rock (artifact), oneshot.
MANA_PERMS = {
    "Birds of Paradise": ("dork", [ANY]), "Noble Hierarch": ("dork", [frozenset("GWU")]),
    "Delighted Halfling": ("dork", [C]), "Devoted Druid": ("dork", [G, G]),
    "Avacyn's Pilgrim": ("dork", [W]), "Llanowar Elves": ("dork", [G]),
    "Elvish Mystic": ("dork", [G]), "Fyndhorn Elves": ("dork", [G]),
    "Elves of Deep Shadow": ("dork", [B]), "Boreal Druid": ("dork", [C]),
    "Arbor Elf": ("dork", "arbor"), "Deathrite Shaman": ("dork", "deathrite"),
    "Gilded Goose": ("dork", [ANY]),  # once (its starting Food); then {1}{G} per Food
    "Sol Ring": ("rock", [C, C]), "Mana Vault": ("rock", [C, C, C]),
    "Arcane Signet": ("rock", [ANY]), "Mox Diamond": ("rock", [ANY]),
    "Chrome Mox": ("rock", "imprint"), "Mox Amber": ("rock", "amber"),
    "Lotus Petal": ("oneshot", [ANY]),
    "Machine God's Effigy": ("rock", [U]),
}
# Cards whose mana is a true mana ability from tapping a permanent (Kinnan/Badgermole apply).
NOT_A_MANA_ABILITY = {"Deathrite Shaman"}
FAST_MANA_FROM_HAND = {"Elvish Spirit Guide"}
FUNCTIONAL_LANDS_EXTRA = {"Sink into Stupor // Soporific Springs"}

# ---- tutors ---------------------------------------------------------------------------------------
# dest: hand | top | bf.  speed: instant | sorcery | ability (instant-speed) | sorcery_ability
# find: predicate key.  zone: where the tutor itself must be (hand -> cast, bf -> activate).
TUTORS = {
    "Demonic Tutor": {"dest": "hand", "speed": "sorcery", "find": "any"},
    "Vampiric Tutor": {"dest": "top", "speed": "instant", "find": "any"},
    "Imperial Seal": {"dest": "top", "speed": "sorcery", "find": "any"},
    "Enlightened Tutor": {"dest": "top", "speed": "instant", "find": "artench"},
    "Mystical Tutor": {"dest": "top", "speed": "instant", "find": "instsorc"},
    "Worldly Tutor": {"dest": "top", "speed": "instant", "find": "creature"},
    "Spellseeker": {"dest": "hand", "speed": "creature", "find": "instsorc_le2"},
    "Ranger-Captain of Eos": {"dest": "hand", "speed": "creature", "find": "creature_le1"},
    "Summoner's Pact": {"dest": "hand", "speed": "instant", "find": "green_creature"},
    "Survival of the Fittest": {"dest": "hand", "speed": "ability", "find": "creature",
                                "on_bf": True, "activation": (0, (G,)), "discard_creature": True},
    "Chord of Calling": {"dest": "bf", "speed": "instant", "find": "creature_x", "x_cost": True,
                         "convoke": True},
    "Finale of Devastation": {"dest": "bf", "speed": "sorcery", "find": "creature_x",
                              "x_cost": True, "from_gy": True},
    "Nature's Rhythm": {"dest": "bf", "speed": "sorcery", "find": "creature_x", "x_cost": True},
    "Green Sun's Zenith": {"dest": "bf", "speed": "sorcery", "find": "green_creature_x",
                           "x_cost": True},
    "Eldritch Evolution": {"dest": "bf", "speed": "sorcery", "find": "creature_sac_plus2"},
    "Neoform": {"dest": "bf", "speed": "sorcery", "find": "creature_sac_plus1"},
    "Birthing Pod": {"dest": "bf", "speed": "sorcery_ability", "find": "creature_sac_plus1",
                     "on_bf": True, "activation": (1, (frozenset({"G", "P"}),))},
    "Crop Rotation": {"dest": "bf", "speed": "instant", "find": "land"},
}
TOP_TUTORS = {n for n, t in TUTORS.items() if t["dest"] == "top"}


def tutor_can_find(tutor, target, sac_mv=None):
    f = TUTORS[tutor]["find"]
    if f == "any":
        return True
    if f == "artench":
        return is_artifact_or_enchantment(target)
    if f == "instsorc":
        return is_instant_or_sorcery(target)
    if f == "instsorc_le2":
        return is_instant_or_sorcery(target) and mv(target) <= 2
    if f in ("creature", "creature_x"):
        return is_creature(target)
    if f == "creature_le1":
        return is_creature(target) and mv(target) <= 1
    if f in ("green_creature", "green_creature_x"):
        return is_creature(target) and is_green(target)
    if f == "creature_sac_plus2":
        return is_creature(target) and sac_mv is not None and mv(target) <= sac_mv + 2
    if f == "creature_sac_plus1":
        return is_creature(target) and sac_mv is not None and mv(target) == sac_mv + 1
    if f == "land":
        return is_land(target)
    return False


# ---- roles (descriptive structure, not a quality score) ------------------------------------------
PREMIUM_ENGINES = {"Birthing Pod", "Survival of the Fittest", "Rhystic Study", "Mystic Remora",
                   "Smothering Tithe", "Esper Sentinel", "Kinnan, Bonder Prodigy",
                   "Abhorrent Oculus"}
CARD_ADVANTAGE = {"Rhystic Study", "Mystic Remora", "Smothering Tithe", "Esper Sentinel",
                  "Faerie Mastermind", "The Queen of Dale", "Gleaming Splendor",
                  "Delney, Streetwise Lookout", "Lotho, Corrupt Shirriff", "The Cabbage Merchant",
                  "Abhorrent Oculus", "Orcish Bowmasters", "Sylvan Library", "Archivist of Oghma",
                  "Talion, the Kindly Lord", "Seedborn Muse", "Kinnan, Bonder Prodigy"}
PROACTIVE_PROTECTION = {"Silence", "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos",
                        "Veil of Summer", "Autumn's Veil", "Orim's Chant", "Allosaurus Shepherd"}
FREE_COUNTERS = {"Force of Will", "Force of Negation", "Fierce Guardianship", "Flare of Denial",
                 "Pact of Negation", "Mindbreak Trap", "Misdirection", "Commandeer", "Subtlety",
                 "Snapback", "Daze", "Deflecting Swat"}
CHEAP_INTERACTION = {"Swan Song", "Flusterstorm", "Mental Misstep", "Strix Serenade", "Dispel",
                     "Sink into Stupor // Soporific Springs", "Orcish Bowmasters", "Endurance",
                     "Gilded Drake", "Volatile Stormdrake", "Into the Flood Maw",
                     "Boseiju, Who Endures", "Otawara, Soaring City", "Colossal Skyturtle",
                     "Noxious Revival", "Force of Vigor"}
INTERACTION = FREE_COUNTERS | CHEAP_INTERACTION
TIMING = {"High Fae Trickster", "Teferi, Mage of Zhalfir", "Emergence Zone",
          "Borne Upon a Wind", "Valley Floodcaller"}
COMBO_PIECES = {"Devoted Druid", "Swift Reconfiguration", "Hazel's Brewmaster",
                "Machine God's Effigy", "Oboro Breezecaller", "Talon Gates of Madara",
                "Gaea's Cradle", "Thassa's Oracle", "Demonic Consultation", "Tainted Pact",
                "Hermit Druid", "Divining Witch", "Shang-Chi, Master of Kung Fu",
                "Orcish Bowmasters", "Faerie Mastermind", "Gleaming Splendor"}
COPY_EFFECTS = {"Mockingbird", "Clever Impersonator", "Flash Photography", "Machine God's Effigy"}
OUTLETS = {"Thassa's Oracle", "Orcish Bowmasters", "Faerie Mastermind", "Finale of Devastation",
           "Gleaming Splendor"}


def roles(name):
    r = set()
    if is_land(name) or name in MANA_PERMS or name in FAST_MANA_FROM_HAND:
        r.add("mana")
    if name in PREMIUM_ENGINES or name in {"Delney, Streetwise Lookout", "Gaea's Cradle"}:
        r.add("engine")
    if name in CARD_ADVANTAGE:
        r.add("card_advantage")
    if name in TUTORS or name == "Tainted Pact":
        r.add("tutor_access")
    if name in PROACTIVE_PROTECTION:
        r.add("protection")
    if name in INTERACTION:
        r.add("interaction")
    if name in COMBO_PIECES:
        r.add("combo_component")
    if name in OUTLETS:
        r.add("outlet")
    if name in TIMING:
        r.add("timing")
    if name in COPY_EFFECTS:
        r.add("copy")
    if not is_land(name) and is_creature(name):
        r.add("body")
    return sorted(r)


def frozen_baseline():
    d = json.loads(FROZEN.read_text(encoding="utf-8"))
    return [c["name"] for c in d["cards"]], d["deck_hash"]
