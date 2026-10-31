"""SIM-DECKBUILD-008b — Oracle + Tainted Pact + Spellseeker follow-up: shared analysis helpers.

Reuses the DECKBUILD-008 goldfish (deckbuild008_goldfish.Game), solver (deckbuild008_solver) and card
registry (deckbuild008_cards). Adds, without changing any 008 default behaviour:

* rule extensions switched on per game (solver.enable_008b_rules): Tainted Pact as a fair instant tutor
  (with the exile-above exposure rule) and Colossal Skyturtle's channel regrowth;
* a Standalone Card Quality / Brick Burden classifier for every card in hand at each of the pilot's
  main phases (T1-T4);
* category interaction-access checks (theft, creature-spell counters, bounce, ...);
* fair Tainted Pact search arithmetic (exact, from the real library order, and closed form).

Every classification rule is stated in code and pinned by rules_tests/regression/test_deckbuild008b_rules.py.
"""
from __future__ import annotations

from collections import Counter

import deckbuild008_cards as dc
import deckbuild008_solver as sv
from deckbuild008_cards import ANY, B, G, U, W  # noqa: F401

ORACLE, CONSULT, PACT, SEEKER = sv.ORACLE, sv.CONSULT, sv.PACT, sv.SPELLSEEKER
DRUID, SWIFT, HAZEL, EFFIGY = sv.DRUID, sv.SWIFT, sv.HAZEL, sv.EFFIGY
OBORO = "Oboro Breezecaller"
CRADLE = sv.CRADLE
TALON = "Talon Gates of Madara"
SKYTURTLE = sv.SKYTURTLE
POD, SURVIVAL = sv.POD, sv.SURVIVAL
BOWMASTERS, MASTERMIND = sv.BOWMASTERS, sv.MASTERMIND
COMMANDERS_ON_BF = {sv.THRASIOS, sv.TYMNA}

# ---- standalone-quality classes -------------------------------------------------------------------
# Material roles: the card does something real now. Secondary roles: pitch fuel / Pod-type body /
# a future land drop / a risky fair mode. Stranded: nothing at all.
MATERIAL = ("combo_live", "combo_pair", "fair_tutor", "development", "interaction_held", "land_drop")
SECONDARY = ("fair_risky", "body", "pitch", "extra_land")

BLUE_PITCH_SPELLS = {"Force of Will", "Force of Negation", "Misdirection", "Commandeer", "Subtlety"}
GREEN_PITCH_SPELLS = {"Endurance"}
HOLD_UP = dc.INTERACTION | dc.PROACTIVE_PROTECTION | {"Flash Photography", "Mockingbird",
                                                     "Clever Impersonator"}
# Dedicated combo cards whose castability alone is NOT counted as development (assignment prior:
# Oracle is a brick outside a winning state; Hazel / Swift are tolerated low-floor combo cards).
LOW_FLOOR_CASTABLE = {ORACLE, CONSULT, SWIFT, HAZEL}

PARTNERS = {
    ORACLE: lambda h, bf, gy: bool({CONSULT, PACT} & h),
    CONSULT: lambda h, bf, gy: ORACLE in h,
    PACT: lambda h, bf, gy: ORACLE in h,
    SWIFT: lambda h, bf, gy: DRUID in h or DRUID in bf,
    DRUID: lambda h, bf, gy: bool({SWIFT, EFFIGY, HAZEL} & (h | bf)),
    EFFIGY: lambda h, bf, gy: DRUID in h or DRUID in bf,
    HAZEL: lambda h, bf, gy: DRUID in gy or DRUID in h or DRUID in bf,
    OBORO: lambda h, bf, gy: CRADLE in h or CRADLE in bf,
    BOWMASTERS: lambda h, bf, gy: MASTERMIND in h or MASTERMIND in bf,
    MASTERMIND: lambda h, bf, gy: BOWMASTERS in h or BOWMASTERS in bf,
}


def units_of(snap):
    ctx = sv.Ctx(snap, 0)
    return sv._units_for(ctx, snap)


def castable(units, name, x=0):
    if "{X}" not in dc.card(name)["cost"]:
        x = 0  # X only applies to X spells (Chord / Finale / Nature's Rhythm / Mockingbird)
    g, pips = dc.cost_of(name, x)
    return sv.pay(units, pips, g)


def free_castable(name, hand, bfnames, bf, units, timing="instant"):
    """Alternative costs that need no mana (pitch / evoke / conditional free)."""
    others = [c for c in hand if c != name]
    blue = [c for c in others if dc.is_blue(c)]
    green = [c for c in others if dc.is_green(c)]
    if name == "Pact of Negation":
        return True
    if name == "Mindbreak Trap":
        return True  # conditional free (3+ spells cast by an opponent this turn); labelled
    if name in ("Force of Will", "Misdirection", "Subtlety", "Force of Negation"):
        return len(blue) >= 1
    if name == "Commandeer":
        return len(blue) >= 2
    if name == "Fierce Guardianship":
        return bool(COMMANDERS_ON_BF & bfnames)
    if name == "Flare of Denial":
        return any(dc.is_blue(p.name) and dc.is_creature(p.name) and not dc.is_land(p.name) for p in bf)
    if name == "Endurance":
        return len(green) >= 1
    if name == "Mental Misstep":
        return True  # Phyrexian {U}: payable with 2 life
    if name == "Otawara, Soaring City":
        return sv.pay(units, (U,), max(0, 3 - sum(1 for p in bf if p.name in sv.LEGENDARY_COLORS)))
    if name == "Boseiju, Who Endures":
        return sv.pay(units, (G,), max(0, 1 - sum(1 for p in bf if p.name in sv.LEGENDARY_COLORS)))
    if name == SKYTURTLE:
        return sv.pay(units, (U,), 1) or sv.pay(units, (G,), 2)  # channel bounce {1}{U} / regrowth {2}{G}
    return False


def tutor_usable(name, hand, bf, library, units):
    """A tutor in hand (or Pod/Survival on the battlefield) that can be used now with a target left."""
    bfn = {p.name for p in bf}
    creatures_bf = [p.name for p in bf if dc.is_creature(p.name) and not dc.is_land(p.name)]
    lib = set(library)
    if name == PACT:
        return bool(lib) and castable(units, PACT)
    if name == CONSULT:
        return False
    if name not in dc.TUTORS:
        return False
    t = dc.TUTORS[name]
    if not any(dc.tutor_can_find(name, c, sac_mv=9) or
               (t["find"] in ("creature_sac_plus1", "creature_sac_plus2") and dc.is_creature(c)) or
               (t["find"] == "land" and dc.is_land(c)) for c in lib):
        return False
    if name in ("Neoform", "Eldritch Evolution"):
        return bool(creatures_bf) and castable(units, name)
    if name == "Crop Rotation":
        return any(dc.is_land(p.name) for p in bf) and castable(units, name)
    if t["find"] in ("creature_x", "green_creature_x"):
        return castable(units, name, x=1)
    return castable(units, name)


def classify_card(name, snap, units, live_cards):
    """Return (best_class, set_of_roles) for one card in hand at a main-phase snapshot."""
    hand = list(snap.hand)
    hset = set(hand)
    bf = snap.bf
    bfn = {p.name for p in bf}
    gy = set(snap.gy)
    roles = set()
    if name in live_cards:
        roles.add("combo_live")
    if name in PARTNERS and PARTNERS[name](hset - {name}, bfn, gy):
        roles.add("combo_pair")
    if dc.is_land(name):
        lands_in_hand = [c for c in hand if dc.is_land(c)]
        roles.add("land_drop" if lands_in_hand and lands_in_hand[0] == name and snap.land_drop else "extra_land")
    else:
        if name == CONSULT and castable(units, CONSULT):
            roles.add("fair_risky")
        if tutor_usable(name, hand, bf, snap.library, units):
            roles.add("fair_tutor")
        if name in HOLD_UP and (castable(units, name, x=1) or free_castable(name, hand, bfn, bf, units)):
            roles.add("interaction_held")
        permanent = not dc.is_instant_or_sorcery(name)
        if permanent and name not in LOW_FLOOR_CASTABLE and name not in HOLD_UP and \
                castable(units, name, x=1):
            roles.add("development")
        if name == OBORO and "combo_pair" not in roles and castable(units, name):
            roles.discard("development")
            roles.add("body")
        if dc.is_creature(name):
            if POD in bfn or SURVIVAL in bfn or ({"Neoform", "Eldritch Evolution"} & hset):
                roles.add("body")
            if name in (ORACLE, HAZEL) and castable(units, name):
                roles.add("body")  # a castable low-floor creature is a body, not development
        if dc.is_blue(name) and (BLUE_PITCH_SPELLS & (hset - {name})):
            roles.add("pitch")
        if dc.is_green(name) and (GREEN_PITCH_SPELLS & (hset - {name})):
            roles.add("pitch")
    if roles & set(MATERIAL):
        best = "material"
    elif roles & set(SECONDARY):
        best = "secondary"
    else:
        best = "stranded"
    return best, roles


def classify_hand(snap, live_cards):
    units = units_of(snap)
    return {c: classify_card(c, snap, units, live_cards) for c in snap.hand}


# ---- interaction categories (coverage, not count) -----------------------------------------------
# Hand-assigned from Oracle text (deckbuild008b_interaction_coverage.json carries the per-card notes).
CATEGORIES = {
    "free_counter": {"Force of Will", "Force of Negation", "Fierce Guardianship", "Flare of Denial",
                     "Pact of Negation", "Mindbreak Trap", "Commandeer", "Subtlety"},
    "paid_counter": {"Swan Song", "Flusterstorm", "Mental Misstep", "Strix Serenade"},
    # can stop a CREATURE spell (counter / put back / return to hand)
    "creature_spell_answer": {"Force of Will", "Pact of Negation", "Mindbreak Trap", "Flare of Denial", "Subtlety",
                              "Strix Serenade", "Sink into Stupor // Soporific Springs"},
    # can stop an ARTIFACT spell
    "artifact_spell_answer": {"Force of Will", "Force of Negation", "Fierce Guardianship", "Pact of Negation",
                              "Mindbreak Trap", "Flare of Denial", "Commandeer", "Strix Serenade",
                              "Sink into Stupor // Soporific Springs"},
    "creature_theft": {"Gilded Drake", "Volatile Stormdrake"},
    # removes / neutralises a resolved opposing creature
    "resolved_creature_answer": {"Gilded Drake", "Volatile Stormdrake", "Colossal Skyturtle",
                                 "Otawara, Soaring City", "Sink into Stupor // Soporific Springs"},
    "resolved_artifact_enchantment_answer": {"Boseiju, Who Endures", "Otawara, Soaring City",
                                             "Sink into Stupor // Soporific Springs"},
    "spell_redirect": {"Misdirection"},
    "graveyard_interaction": {"Endurance"},
    "proactive_protection": {"Silence", "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos"},
    "regrowth_of_spent_resources": {"Colossal Skyturtle"},
    # answers almost any single threat at any point (spell or permanent)
    "flexible_catch_all": {"Force of Will", "Pact of Negation", "Flare of Denial", "Mindbreak Trap",
                           "Sink into Stupor // Soporific Springs"},
}


def category_access(snap, units, category, deck_cards):
    """(in_hand_castable, tutor_reachable_now) for one interaction category."""
    cards = CATEGORIES[category] & set(deck_cards)
    hand = set(snap.hand)
    bfn = {p.name for p in snap.bf}
    in_hand = any(c in hand and (castable(units, c, x=1) or free_castable(c, snap.hand, bfn, snap.bf, units)
                                 or (c == "Colossal Skyturtle" and sv.pay(units, (U,), 1)))
                  for c in cards)
    lib_targets = [c for c in cards if c in snap.library]
    reach = False
    for t in dc.TUTORS:
        if t not in hand and not (dc.TUTORS[t].get("on_bf") and t in bfn):
            continue
        if not tutor_usable(t, snap.hand, snap.bf, snap.library, units):
            continue
        if any(dc.tutor_can_find(t, c, sac_mv=9) for c in lib_targets):
            reach = True
            break
    return in_hand, reach


# ---- fair Tainted Pact search arithmetic -------------------------------------------------------

def pact_walk(library, accept):
    """Walk the real library order: exiled cards before the first acceptable hit, and the hit.

    Tainted Pact: exile the top card; you may put it into your hand unless it shares a name with another
    card exiled this way; repeat until you take one or exile two cards with the same name. With no
    duplicate names the pilot stops on the first acceptable card. If none exists, the whole library is
    exiled (hit None)."""
    exiled = []
    for c in library:
        if c in accept:
            return exiled, c
        exiled.append(c)
    return exiled, None


def pact_closed_form(n_library, k_acceptable):
    """Uniformly random order: E[cards exiled before the first of k hits] = (N-k)/(k+1);
    P(a specific non-hit card is exiled) = 1/(k+1); P(no hit at all) = [k == 0]."""
    if k_acceptable <= 0:
        return {"expected_exiled": float(n_library), "p_specific_card_exiled": 1.0}
    return {"expected_exiled": (n_library - k_acceptable) / (k_acceptable + 1),
            "p_specific_card_exiled": 1.0 / (k_acceptable + 1)}


CRITICAL = {
    "druid_axis": {DRUID, SWIFT, HAZEL, EFFIGY},
    "oboro_axis": {OBORO, CRADLE, TALON},
    "bowmasters_axis": {BOWMASTERS, MASTERMIND},
    "engines": {POD, SURVIVAL, "Rhystic Study", "Mystic Remora", "Smothering Tithe", "Abhorrent Oculus"},
    "protection": {"Silence", "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos"},
    "free_counters": CATEGORIES["free_counter"],
}
