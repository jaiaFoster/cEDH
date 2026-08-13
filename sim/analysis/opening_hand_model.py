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

PHYREXIAN_LIFE_COST = 2  # real Oracle rule: a Phyrexian mana symbol may be paid with 2 life instead


class PhyrexianPip(frozenset):
    """A pip payable either by one of its (usually single) colors OR by paying
    PHYREXIAN_LIFE_COST life instead - real Oracle text for {G/P} etc. Subclasses frozenset
    (not merely duck-typed) so every existing `isinstance(pip, frozenset)` call site in the
    payment engine keeps working unchanged for the color-payment path; only _try_pay needs new
    logic for the life-payment fallback. MULL-005R correctness fix: the prior parser silently
    dropped the life-payment half of any {X/P} symbol, forcing color payment - this undercounted
    real castability (e.g. Birthing Pod's {3}{G/P} cast cost and {1}{G/P} activation cost)
    whenever the color was unavailable but life was not a constraint, which this project's own
    documented philosophy already says should "never block a line" (see this module's docstring)."""


def parse_cost(mana_cost_str):
    """Returns (generic:int, pips:list[str|frozenset|PhyrexianPip], x_count:int).
    pips entries are single-color strings, frozenset for true hybrid (any ONE of these colors,
    no life option - e.g. Deathrite Shaman's {B/G}), or PhyrexianPip for phyrexian mana (any ONE
    of these colors, OR PHYREXIAN_LIFE_COST life - e.g. Birthing Pod's {G/P})."""
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
            raw_parts = t.split("/")
            parts = [p for p in raw_parts if p in COLORS]
            if parts:
                if "P" in raw_parts:
                    pips.append(PhyrexianPip(parts))
                else:
                    pips.append(frozenset(parts))
        elif t == "C":
            generic += 1  # colorless pip treated as generic for our purposes
        # ignore S (snow) etc, none present
    return generic, pips, x_count


def card_colors(name, cards):
    """A card's color, derived from the mana symbols in its own printed mana cost - the correct
    rules basis for card color (barring color-indicator/devoid cases, none of which are present
    in this decklist). Used by the alternate-cost interaction model (pitch/sacrifice colors)."""
    gen, pips, x = parse_cost(cards[name]["mana_cost"])
    colors = set()
    for p in pips:
        colors |= (p if isinstance(p, frozenset) else {p})
    return colors


# ---- land / mana source model ------------------------------------------

LAND_COLOR_SETS = {
    # Plain single/multi-color-choice lands: 1 mana of ONE color from this set, per tap.
    "Bayou": {"B", "G"}, "Boseiju, Who Endures": {"G"}, "City of Brass": {"W", "U", "B", "G"},
    "Command Tower": {"W", "U", "B", "G"}, "Mana Confluence": {"W", "U", "B", "G"},
    "Minamo, School at Water's Edge": {"U"}, "Otawara, Soaring City": {"U"}, "Savannah": {"G", "W"},
    "Scrubland": {"B", "W"}, "Shifting Woodland": {"G"}, "Starting Town": {"W", "U", "B", "G"},
    "Talon Gates of Madara": {"W", "U", "B", "G"}, "Tropical Island": {"G", "U"},
    "Tundra": {"U", "W"}, "Underground Sea": {"B", "U"},
    # Gaea's Cradle: this is what colors it CAN produce - the AMOUNT ({G} for each creature you
    # control, real Oracle text) is dynamic and handled specially in opening_hand_policy.py's
    # available_sources(), never a flat 1-mana entry.
    "Gaea's Cradle": {"G"},
    # Gemstone Caverns and Exotic Orchard are NOT flat any-color sources - see
    # GEMSTONE_CAVERNS/EXOTIC_ORCHARD handling below and in opening_hand_policy.py. Fetchlands
    # (Flooded Strand etc.) are not mana sources in their own right at all - see
    # FETCH_LAND_TARGET_TYPES; they resolve immediately into a real fetched land, or (rarely, if
    # no legal target remains) fizzle, when played.
}
GENERIC_LANDS = {"Ancient Tomb": 2, "City of Traitors": 2}
ANCIENT_TOMB_LIFE_LOSS = 2  # "This land deals 2 damage to you" on tap
GEMSTONE_CAVERNS = "Gemstone Caverns"
EXOTIC_ORCHARD = "Exotic Orchard"
CITY_OF_TRAITORS = "City of Traitors"
CRADLE = "Gaea's Cradle"

FETCH_LANDS = {"Flooded Strand", "Marsh Flats", "Misty Rainforest", "Polluted Delta", "Verdant Catacombs", "Windswept Heath", "Wooded Foothills"}

# Real basic land types printed on each fetchland's two search targets (Oracle text, not the
# fetch's "apparent" color pair) and on the deck's own lands that actually carry a basic type -
# only these are legal fetch targets. This deck has zero true basic lands; the only fetchable
# cards are the six ABUR duals below, each of which really does carry two basic land subtypes
# (e.g. Bayou is "Land — Swamp Forest"). Computed once from data/cards_cache type_lines, not
# assumed - see the correctness-repair commit for the verification query.
FETCH_LAND_TARGET_TYPES = {
    "Flooded Strand": frozenset({"Plains", "Island"}),
    "Marsh Flats": frozenset({"Plains", "Swamp"}),
    "Misty Rainforest": frozenset({"Forest", "Island"}),
    "Polluted Delta": frozenset({"Island", "Swamp"}),
    "Verdant Catacombs": frozenset({"Swamp", "Forest"}),
    "Windswept Heath": frozenset({"Forest", "Plains"}),
    "Wooded Foothills": frozenset({"Mountain", "Forest"}),
}
DUAL_LAND_BASIC_TYPES = {
    "Bayou": frozenset({"Swamp", "Forest"}),
    "Savannah": frozenset({"Forest", "Plains"}),
    "Scrubland": frozenset({"Plains", "Swamp"}),
    "Tropical Island": frozenset({"Forest", "Island"}),
    "Tundra": frozenset({"Plains", "Island"}),
    "Underground Sea": frozenset({"Island", "Swamp"}),
}
# maps color letter -> basic type name, for need_colors-aware fetch-target scoring
BASIC_TYPE_COLOR = {"Plains": "W", "Island": "U", "Swamp": "B", "Forest": "G", "Mountain": "R"}

# nonland mana sources: name -> dict(kind, colors|generic, is_creature, one_shot, requires,
# never_untaps)
MANA_SOURCES = {
    "Avacyn's Pilgrim": {"colors": {"W"}, "creature": True},
    "Birds of Paradise": {"colors": set(COLORS), "creature": True},
    "Delighted Halfling": {"generic": 1, "creature": True},
    "Devoted Druid": {"colors": {"G"}, "creature": True},
    "Elves of Deep Shadow": {"colors": {"B"}, "creature": True},
    "Noble Hierarch": {"colors": {"W", "U", "G"}, "creature": True},
    "Chrome Mox": {"colors": set(COLORS), "creature": False, "requires_imprint": True},
    "Lotus Petal": {"colors": set(COLORS), "creature": False, "one_shot": True},
    "Mana Vault": {"generic": 3, "creature": False, "never_untaps": True},
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

# ---- SIM-001 SOLO-003 engine taxonomy: NOT all ENGINES entries contribute equally to
# "any_engine_active" or similar broad metrics. A card can belong to more than one tier (Birthing
# Pod/Survival of the Fittest are both infrastructure AND conversion; Gaea's Cradle is both
# infrastructure AND mana development) - tier membership drives which SOLO-003 trajectory metrics
# a card counts toward, it does not replace the existing ENGINES/TUTORS/ACCELERATION
# classifications SOLO-002R already relies on.
#
# A. Primary early card-advantage engines - tracked INDIVIDUALLY by exact card, never collapsed
#    into one interchangeable "engine" label (Remora/Sentinel/Rhystic/Sylvan are materially
#    different: different mana cost, different color, different downside/upside shape).
ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE = {
    "Mystic Remora", "Esper Sentinel", "Rhystic Study", "Sylvan Library",
}
# B. High-leverage infrastructure engines - functionality is CONDITIONAL on supporting board
#    state, not merely presence (Cradle needs creatures; Training Grounds needs a creature with
#    a relevant activated ability - notably Thrasios's own {4} activation, reduced to {2} while
#    Training Grounds is in play; Pod/Survival need a legal sacrifice/discard target).
ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE = {
    "Survival of the Fittest", "Birthing Pod", "Kinnan, Bonder Prodigy",
    "Gaea's Cradle", "Training Grounds",
}
# C. Conditional/contextual value engines - only actually productive when their specific
#    condition is supported (Tymna needs an attacker; Faerie Mastermind/Heartwood
#    Storyteller/Runic Armasaur/Archivist of Oghma/Delney trigger off specific board actions;
#    Smothering Tithe/Deathrite Shaman are structurally near-dead in a solo/no-opponent,
#    graveyard-ability-unmodeled context respectively - flagged, not silently dropped).
ENGINE_TIER_C_CONDITIONAL_VALUE = {
    "Tymna the Weaver", "Faerie Mastermind", "Heartwood Storyteller", "Runic Armasaur",
    "Archivist of Oghma", "Delney, Streetwise Lookout", "Smothering Tithe", "Deathrite Shaman",
}
# D. Mana/development infrastructure - does NOT count as card-advantage merely by being present;
#    contributes to trajectories by accelerating stronger subsequent actions instead.
ENGINE_TIER_D_MANA_DEVELOPMENT = set(ACCELERATION) | {"Gaea's Cradle"}
# E. Tutor/conversion infrastructure - measured by CURRENT conversion ability (see
#    interaction_model.py / trajectory_metrics.py), not mere presence. TUTORS is already defined
#    above this point in the file.
ENGINE_TIER_E_TUTOR_CONVERSION = set(TUTORS)

ENGINE_TIERS = {}
for _name in (ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE | ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE
              | ENGINE_TIER_C_CONDITIONAL_VALUE | ENGINE_TIER_D_MANA_DEVELOPMENT
              | ENGINE_TIER_E_TUTOR_CONVERSION):
    tiers = set()
    if _name in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE:
        tiers.add("A")
    if _name in ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE:
        tiers.add("B")
    if _name in ENGINE_TIER_C_CONDITIONAL_VALUE:
        tiers.add("C")
    if _name in ENGINE_TIER_D_MANA_DEVELOPMENT:
        tiers.add("D")
    if _name in ENGINE_TIER_E_TUTOR_CONVERSION:
        tiers.add("E")
    ENGINE_TIERS[_name] = tiers
del _name

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
# MULL-005R correctness fix (t1_t3_trajectory_audit.json, section 18's "top-of-library tutors
# actually delay access until draw"): MULL-005 put every forced tutor target into HAND uniformly.
# Real Oracle text: Vampiric Tutor/Imperial Seal/Enlightened Tutor put the found card on TOP OF
# LIBRARY, not into hand - it is not actually accessible until drawn on a LATER turn, a real
# delay this simulator must represent. Demonic Tutor, and the ETB-triggered searches on
# Ranger-Captain of Eos / Spellseeker, genuinely do put the card into hand. Cards not listed here
# either aren't hand/library-zone tutors (Birthing Pod/Survival of the Fittest are activated
# abilities, handled separately - see pod_and_battlefield_tutors.py) or are battlefield-zone
# search effects (see BATTLEFIELD_TUTOR_SPECS below).
TUTOR_DESTINATION_HAND = {"Demonic Tutor", "Ranger-Captain of Eos", "Spellseeker"}
TUTOR_DESTINATION_LIBRARY_TOP = {"Vampiric Tutor", "Imperial Seal", "Enlightened Tutor"}

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
