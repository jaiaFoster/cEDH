"""SIM-ROGFARM-001 — card data + mechanics for cards new to the RogSi/Rog Farm/Blue Farm card
pool. Starts with Foil (the Stage 1 "RULES FIX 1" correction); more cards land here as Stage 2's
card-data build proceeds.

Follows this project's established install_new_card_tables()/uninstall_new_card_tables() pattern
for extending shared global tables (opening_hand_model.py's INTERACTION_CASTABLE,
interaction_model.py's ALT_COST_SPECS) without cross-test-file pollution.

Foil — Oracle text supplied directly by the task owner as the authoritative correction to this
project's own prior (wrong) Stage 1 draft, which had described Foil as "exile a blue card... MV<=3
restriction" (a conflation with a different, unrelated budget counterspell). Corrected text:
  {2}{U}{U} Instant — "Counter target spell. Alternative cost: You may discard an Island card and
  another card rather than pay this spell's mana cost."
Key properties (all directly required by the correction instruction, each with its own regression
test below): the alternate cost needs an Island CARD in hand (not merely blue mana available) plus
a SECOND, separate card (real two-card discard, genuine card-disadvantage cost, not a cantrip- or
replacement-style cost); there is NO mana-value restriction on the countered spell (unlike a
budget counterspell such as Spell Pierce); Foil does NOT exile a blue card (that mechanic belongs
to a different, unrelated card and was the source of the original error).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402
import interaction_model as im  # noqa: E402
import deckbuild006_cards as d6  # noqa: E402 - Lotho/Grand Abolisher/Mockingbird/An Offer/Scalding
import mana_audit002_variants as ma2  # noqa: E402 - Scalding Tarn/Arid Mesa/Bloodstained Mire/Tarnished Citadel
import deckbuild007_cards as d7  # noqa: E402 - Dark Ritual net-mana pattern, reused directly

FOIL_NAME = "Foil"

NEW_CARD_DATA = {
    FOIL_NAME: {
        "type": "Instant", "mana_cost": "{2}{U}{U}", "cmc": 4,
        "text": "Counter target spell. Alternative cost: You may discard an Island card and "
                "another card rather than pay this spell's mana cost.",
    },
}

# Registered in INTERACTION_CASTABLE with a dedicated alt-cost tag ("discard_island_plus_other")
# distinct from every existing "pitch" (exile-based) entry - Foil's alternate cost is a real
# 2-card DISCARD (to graveyard), not an exile, and is keyed off card TYPE (Island) for one card
# and no restriction at all for the other, not off color-of-card like Force of Will/Subtlety/etc.
NEW_INTERACTION_CASTABLE = {FOIL_NAME: "discard_island_plus_other"}
NEW_ALT_COST_SPECS = {FOIL_NAME: {"type": "discard_island_plus_other"}}

# Volcanic Island's mana colors, needed for available_sources()' mana-color lookup
# (opening_hand_model.LAND_COLOR_SETS is a shared global keyed by exact land name). Underground
# Sea/Tundra/Tropical Island are already registered there from the Tymna/Thrasios card pool;
# Volcanic Island is the one genuinely new dual this project's decks introduce. Registering it
# also matters for Foil's alt cost: R1 runs zero basic Islands (see test coverage), so its
# Island-subtype fuel is exactly these Island-type duals/fetchable duals.
NEW_LAND_COLOR_SETS = {
    "Volcanic Island": {"U", "R"},
}


def _is_island(card_name, cards):
    return "Island" in cards[card_name]["type"]


def foil_discard_pair(state, cards):
    """Returns (island_card_name, other_card_name) if Foil's alternate cost is currently payable
    from hand, else None. Requires an Island CARD in hand (the land itself, not merely blue mana
    availability) plus a second, distinct card - Foil itself is never counted as either half."""
    hand_others = [c for c in state.hand if c != FOIL_NAME]
    islands = [c for c in hand_others if _is_island(c, cards)]
    if not islands:
        return None
    island = islands[0]
    remaining = list(hand_others)
    remaining.remove(island)
    if not remaining:
        return None  # the Island alone isn't enough - genuine 2-card cost, need a second card
    return island, remaining[0]


def _foil_is_live(state, cards):
    from opening_hand_policy import is_currently_castable
    gen, pips, x = ohm.parse_cost(cards[FOIL_NAME]["mana_cost"])
    mana_ok = (x == 0) and is_currently_castable(state, gen, pips)
    return mana_ok or foil_discard_pair(state, cards) is not None


def _foil_resolve(state, cards):
    from opening_hand_policy import _try_pay
    gen, pips, x = ohm.parse_cost(cards[FOIL_NAME]["mana_cost"])
    if x == 0:
        plan = _try_pay(state, gen, pips)
        if plan is not None:
            return ("mana", plan)
    pair = foil_discard_pair(state, cards)
    if pair is not None:
        return ("discard_island_plus_other", pair)
    return None


def _foil_commit(name, resolution, state):
    kind, payload = resolution
    if kind == "discard_island_plus_other":
        island, other = payload
        for c in (island, other):
            state.hand.remove(c)
            state.graveyard.append(c)


# =====================================================================================
# STAGE 2 — remaining card-data build. Scope decisions (all conservative: never overcount
# a card's capability; every simplification undercounts or omits, never fabricates upside):
#
#   Rituals with a real ADDITIONAL cost this engine can't verify (sacrifice a creature/land -
#   Culling the Weak, Rain of Filth, Infernal Plunge, Diabolic Intent) are excluded from
#   auto-cast/TUTORS/ACCELERATION entirely, matching DECKBUILD-007's established Dark Ritual
#   precedent ("generic loop can't handle this correctly -> exclude, build a dedicated
#   forced-only function only if a script explicitly needs it"). None of Stage 2's required
#   outputs need these specific rituals modeled precisely, so no dedicated function is built for
#   them either - they fall to "other" (never auto-cast, never counted as acceleration).
#
#   Complex conditional mana sources this engine's board-state model can't verify (Mox Opal's
#   metalcraft, Springleaf Drum/Paradise Mantle's creature-tap requirement, Fellwar Stone's
#   opponent-land dependency, Cavern of Souls' creature-type choice, Phyrexian Tower's
#   sacrifice-a-creature mode) are modeled at their guaranteed FLOOR (0 mana, or colorless-only
#   for the two utility lands) - real precedent: Exotic Orchard/Talon Gates of Madara are already
#   treated this exact way in the base engine.
#
#   Tutors with a real additional cost (Diabolic Intent) or opponent-dependent resolution
#   (Intuition - an opponent chooses which of 3 cards you get) or a narrow/near-always-dead T1-3
#   search target (Demonic Counsel's Demon-only clause) or a mechanic this engine has no
#   representation for (Lim-Dûl's Vault's library-reordering, Wishclaw Talisman's activated-
#   ability-not-cast tutoring, Gamble's random-discard cost) are excluded from TUTORS, disclosed.
#   Mystical Tutor (top of library) and Beseech the Mirror (hand, modeled without its optional
#   Bargain upside) are the only two NEW tutors registered.
#
#   Ad Nauseam, Gitaxian Probe, Last Chance, Sevinne's Reclamation, Snap, Snapback, Borne Upon a
#   Wind, Mnemonic Betrayal, Chain of Vapor, Vexing Bauble, Defense Grid, Wishclaw Talisman are
#   real cards this deck runs but whose value depends on board states / opponent permanents this
#   solo T1-3 engine structurally cannot represent (no opponent permanents, no combat, no stack) -
#   registered with correct CARDS type/mana_cost data only (so they display correctly and are
#   never miscounted elsewhere), left un-auto-cast ("other"), disclosed rather than faked.
#
#   Engine classification (Section 7's four required categories - autonomous / opponent_dependent
#   / wheel_payoff / mana_resource - plus an informational 5th "protection" bucket for cards that
#   don't fit those four but still register as a real board presence): see ENGINE_SECTION7_CLASS
#   below, consumed directly by build_rogfarm001_stage2_harness.py's engine-timing breakdown.
# =====================================================================================

DEMONIC_CONSULTATION_NAME = "Demonic Consultation"
TAINTED_PACT_NAME = "Tainted Pact"
THASSAS_ORACLE_NAME = "Thassa's Oracle"

NEW_CARD_DATA.update({
    # ---- lands not already covered by deckbuild006_cards/mana_audit002_variants imports ----
    "Volcanic Island": {"type": "Land — Island Mountain", "mana_cost": "", "cmc": 0,
                         "text": "{T}: Add {U} or {R}."},
    "Badlands": {"type": "Land — Swamp Mountain", "mana_cost": "", "cmc": 0,
                 "text": "{T}: Add {B} or {R}."},
    "Plateau": {"type": "Land — Plains Mountain", "mana_cost": "", "cmc": 0,
                "text": "{T}: Add {W} or {R}."},
    "Blood Crypt": {"type": "Land — Swamp Mountain", "mana_cost": "", "cmc": 0,
                     "text": "Enters tapped unless you pay 2 life. {T}: Add {B} or {R}."},
    "Steam Vents": {"type": "Land — Island Mountain", "mana_cost": "", "cmc": 0,
                     "text": "Enters tapped unless you pay 2 life. {T}: Add {U} or {R}."},
    "Watery Grave": {"type": "Land — Island Swamp", "mana_cost": "", "cmc": 0,
                      "text": "Enters tapped unless you pay 2 life. {T}: Add {U} or {B}."},
    "Cavern of Souls": {"type": "Land", "mana_cost": "", "cmc": 0,
                         "text": "As Cavern of Souls enters, choose a creature type. {T}: Add "
                                 "{C}. {T}: Add one mana of any color. Spend this mana only to "
                                 "cast a creature spell of the chosen type. (Modeled at its "
                                 "guaranteed colorless floor - the creature-type choice/color "
                                 "half is not represented, undercount-only.)"},
    "Phyrexian Tower": {"type": "Land", "mana_cost": "", "cmc": 0,
                         "text": "{T}: Add {C}. {T}, Sacrifice a creature: Add two mana of any "
                                 "one color. (Modeled at its guaranteed colorless floor - the "
                                 "sacrifice mode requires a creature this engine doesn't verify, "
                                 "undercount-only.)"},
    "Spire of Industry": {"type": "Land", "mana_cost": "", "cmc": 0,
                           "text": "{T}: Add {C}. {T}: Add one mana of any color. Spire of "
                                   "Industry deals 1 damage to you unless you control an "
                                   "artifact or creature. (Life cost tracked-but-never-blocking, "
                                   "same treatment as City of Brass/Mana Confluence.)"},

    # ---- mana rocks/dorks ----
    "Grim Monolith": {"type": "Artifact", "mana_cost": "{2}", "cmc": 2,
                       "text": "{T}: Add {C}{C}{C}. {3}, {T}: Untap Grim Monolith."},
    "Arcane Signet": {"type": "Artifact", "mana_cost": "{2}", "cmc": 2,
                       "text": "{T}: Add one mana of any color in your commander(s)' color "
                               "identity."},
    "Simian Spirit Guide": {"type": "Creature — Ape", "mana_cost": "{2}{R}", "cmc": 3,
                             "text": "Exile Simian Spirit Guide from your hand: Add {R}. "
                                     "Activate only any time you could cast a sorcery."},

    # ---- rituals (net-mana instants; excluded from auto-cast, dedicated try_cast_* functions) --
    "Cabal Ritual": {"type": "Instant", "mana_cost": "{1}{B}", "cmc": 2,
                      "text": "Add {B}{B}{B}. Threshold — Add {B}{B}{B}{B}{B} instead if there "
                              "are seven or more cards in your graveyard."},
    "Rite of Flame": {"type": "Instant", "mana_cost": "{R}", "cmc": 1, "text": "Add {R}{R}."},
    "Culling the Weak": {"type": "Instant", "mana_cost": "{B}", "cmc": 1,
                          "text": "As an additional cost to cast this spell, sacrifice a "
                                  "creature. Add {B}{B}{B}{B}. (Additional sac cost not modeled "
                                  "by the generic auto-cast loop - excluded, see module docstring.)"},
    "Rain of Filth": {"type": "Instant", "mana_cost": "{B}", "cmc": 1,
                       "text": "Until end of turn, lands you control gain 'Sacrifice this land: "
                               "Add {B}.' (Not modeled - excluded, see module docstring.)"},
    "Infernal Plunge": {"type": "Instant", "mana_cost": "{R}", "cmc": 1,
                         "text": "As an additional cost to cast this spell, sacrifice a "
                                 "creature. Add {R}{R}{R}. (Additional sac cost not modeled - "
                                 "excluded.)"},

    # ---- tutors ----
    "Mystical Tutor": {"type": "Instant", "mana_cost": "{U}", "cmc": 1,
                        "text": "Search your library for an instant or sorcery card, reveal it, "
                                "then shuffle and put that card on top of your library."},
    "Beseech the Mirror": {"type": "Sorcery", "mana_cost": "{1}{B}{B}{B}", "cmc": 4,
                            "text": "Bargain. Search your library for a card, exile it face "
                                    "down, then shuffle. If this spell was bargained, you may "
                                    "cast the exiled card without paying its mana cost if that "
                                    "spell's mana value is 4 or less. Put the exiled card into "
                                    "your hand if it wasn't cast this way. (Modeled without the "
                                    "optional Bargain free-cast upside - undercount-only.)"},
    "Diabolic Intent": {"type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2,
                         "text": "As an additional cost to cast this spell, sacrifice a "
                                 "creature. Search your library for a card, put that card into "
                                 "your hand, then shuffle. (Additional sac cost not modeled - "
                                 "excluded.)"},
    "Demonic Counsel": {"type": "Sorcery", "mana_cost": "{1}{B}", "cmc": 2,
                         "text": "Search your library for a Demon card, reveal it, put it into "
                                 "your hand, then shuffle. Delirium — instead search for any "
                                 "card if 4+ card types are in your graveyard. (Near-always-dead "
                                 "T1-3 target - excluded.)"},
    "Gamble": {"type": "Sorcery", "mana_cost": "{B}", "cmc": 1,
               "text": "Search your library for a card, reveal it, put it into your hand, then "
                       "shuffle. Discard a card at random. (Random-discard cost not modeled - "
                       "excluded.)"},
    "Intuition": {"type": "Instant", "mana_cost": "{1}{U}", "cmc": 2,
                  "text": "Search your library for three cards and reveal them. An opponent "
                          "chooses one of those cards. Put that card into your hand and the "
                          "rest into your graveyard. (Opponent-choice resolution not modeled - "
                          "excluded.)"},
    "Lim-Dul's Vault": {"type": "Instant", "mana_cost": "{U}{B}", "cmc": 2,
                         "text": "Look at the top five cards of your library. As many times as "
                                 "you choose, pay 1 life, put those cards on the bottom in any "
                                 "order, then look at the top five again. Shuffle and put the "
                                 "last five looked at on top. (Library-reordering, not a hand-"
                                 "tutor - not modeled - excluded.)"},
    "Wishclaw Talisman": {"type": "Artifact", "mana_cost": "{1}{B}", "cmc": 2,
                           "text": "{2}, {T}: Target player searches their library for a card, "
                                   "puts it into their hand, then shuffles. If that player "
                                   "doesn't control Wishclaw Talisman, they lose 3 life. "
                                   "Sacrifice at the beginning of the next end step. (Activated-"
                                   "ability tutor, not a cast-and-fetch - not modeled - excluded.)"},

    # ---- interaction ----
    "Daze": {"type": "Instant", "mana_cost": "{1}{U}", "cmc": 2,
             "text": "Counter target spell unless its controller pays {1}. Alternative cost: "
                     "Return an Island you control to its owner's hand rather than pay this "
                     "spell's mana cost."},
    "Pyroblast": {"type": "Instant", "mana_cost": "{R}", "cmc": 1,
                  "text": "Choose one — Counter target spell if it's blue; or Destroy target "
                          "permanent if it's blue."},
    "Red Elemental Blast": {"type": "Instant", "mana_cost": "{R}", "cmc": 1,
                             "text": "Choose one — Counter target spell if it's blue; or "
                                     "Destroy target permanent if it's blue."},
    "Deflecting Swat": {"type": "Instant", "mana_cost": "{1}{R}", "cmc": 2,
                         "text": "If you control a commander, you may cast this spell without "
                                 "paying its mana cost. Change the target of target spell or "
                                 "ability with a single target."},
    "Chain of Vapor": {"type": "Instant", "mana_cost": "{U}", "cmc": 1,
                        "text": "Return target nonland permanent to its owner's hand. If that "
                                "permanent wasn't a token, you may return a land you control to "
                                "its owner's hand. (No opposing permanents exist in this solo "
                                "model - not auto-cast - excluded.)"},
    "Vexing Bauble": {"type": "Artifact", "mana_cost": "{1}", "cmc": 1,
                       "text": "Spells your opponents cast that have mana value 0 or 1 cost {2} "
                               "more to cast. {1}, {T}, Sacrifice: Draw a card. (Opponent-facing "
                               "tax - not auto-cast for its primary purpose - excluded.)"},
    "Defense Grid": {"type": "Artifact", "mana_cost": "{1}{U}", "cmc": 2,
                      "text": "Each spell that isn't yours costs {3} more to cast unless it's "
                              "your turn. (Opponent-facing tax - not modeled - excluded.)"},
    "Snap": {"type": "Instant", "mana_cost": "{1}{U}", "cmc": 2,
             "text": "Return target creature to its owner's hand. Untap up to two lands. (No "
                     "opposing creatures exist in this solo model - not auto-cast - excluded.)"},
    "Snapback": {"type": "Instant", "mana_cost": "{1}{U}{U}", "cmc": 3,
                 "text": "Return target permanent to its owner's hand. Its controller draws a "
                         "card. Flashback {5}{U}{U}. (Not auto-cast - excluded.)"},
    "Ad Nauseam": {"type": "Instant", "mana_cost": "{3}{B}", "cmc": 4,
                    "text": "Exile cards from the top of your library until you exile a land "
                            "card. For each nonland card exiled this way, put it into your hand "
                            "and you lose life equal to its mana value. You may stop this "
                            "process at any time. (Risky, judgment-heavy value spell - not "
                            "auto-cast - excluded.)"},
    "Gitaxian Probe": {"type": "Sorcery", "mana_cost": "{1}{U}", "cmc": 2,
                        "text": "Alternative cost: Pay 2 life rather than pay this spell's mana "
                                "cost. Look at target player's hand. Draw a card. (Not auto-cast "
                                "- excluded, marginal.)"},
    "Last Chance": {"type": "Sorcery", "mana_cost": "{R}", "cmc": 1,
                     "text": "Skip your next untap step. Extra turn after this one restriction "
                             "notwithstanding, take an additional turn after this one. Exile "
                             "this card. (Not auto-cast - excluded.)"},
    "Sevinne's Reclamation": {"type": "Sorcery", "mana_cost": "{2}{W}", "cmc": 3,
                               "text": "Return target legendary permanent card with mana value "
                                       "3 or less from your graveyard to the battlefield. Exile "
                                       "Sevinne's Reclamation. (Not auto-cast - excluded.)"},
    "Borne Upon a Wind": {"type": "Instant", "mana_cost": "{2}{U}", "cmc": 3,
                           "text": "Copy target instant or sorcery spell you control. You may "
                                   "choose new targets. Storm. (Not auto-cast - excluded.)"},
    "Mnemonic Betrayal": {"type": "Sorcery", "mana_cost": "{2}{U}{B}", "cmc": 4,
                           "text": "Exile target player's graveyard. If a nontoken creature "
                                   "card was exiled this way, create a token that's a copy of "
                                   "it. (Opponent-graveyard-dependent - not auto-cast - excluded.)"},

    # ---- engines / creatures ----
    "The One Ring": {"type": "Legendary Artifact", "mana_cost": "{4}", "cmc": 4,
                      "text": "When The One Ring enters the battlefield, if you cast it, you "
                              "gain protection from everything until your next turn. At the "
                              "beginning of your upkeep, you lose 1 life for each burden counter "
                              "on The One Ring. {T}: Put a burden counter on The One Ring, then "
                              "draw a card for each burden counter on The One Ring."},
    "Necropotence": {"type": "Enchantment", "mana_cost": "{B}", "cmc": 1,
                      "text": "Skip your draw step. Pay 1 life: Exile the top card of your "
                              "library face down under Necropotence. Put those cards into your "
                              "hand at the beginning of your next end step."},
    "Ragavan, Nimble Pilferer": {"type": "Legendary Creature — Monkey Pirate", "mana_cost": "{R}", "cmc": 1,
                                  "text": "Whenever Ragavan deals combat damage to a player, "
                                          "create a Treasure token and exile the top card of "
                                          "that player's library... Dash {1}{R}."},
    "Valley Floodcaller": {"type": "Creature — Otter Wizard", "mana_cost": "{2}{U}", "cmc": 3,
                            "text": "Flash. You may cast noncreature spells as though they had "
                                    "flash. Whenever you cast a noncreature spell, Birds, Frogs, "
                                    "Otters, and Rats you control get +1/+1 until end of turn. "
                                    "Untap them."},
    "Dragon's Rage Channeler": {"type": "Creature — Human Wizard", "mana_cost": "{R}", "cmc": 1,
                                 "text": "Whenever you cast a noncreature spell, surveil 1. "
                                         "Delirium — DRC gets +2/+1 and has flying."},
    "Knuckles the Echidna": {"type": "Legendary Creature — Echidna Warrior", "mana_cost": "{2}{R}{R}", "cmc": 4,
                              "text": "Double strike, trample, haste. Whenever one or more "
                                      "creatures you control deal combat damage to a player, "
                                      "create a Treasure token. Treasure Hunter — At the "
                                      "beginning of your upkeep, if you control thirty or more "
                                      "artifacts, you win the game."},
    "Tataru Taru": {"type": "Legendary Creature — Dwarf Advisor", "mana_cost": "{1}{W}", "cmc": 2,
                     "text": "When Tataru Taru enters, you draw a card and target opponent may "
                             "draw a card. Scions' Secretary — Whenever an opponent draws a "
                             "card off their turn, create a tapped Treasure token (once/turn)."},
    "Voice of Victory": {"type": "Creature — Griffin", "mana_cost": "{1}{W}", "cmc": 2,
                          "text": "Flying, vigilance. Whenever you cast a historic spell, put "
                                  "a +1/+1 counter on Voice of Victory."},
    "Narset, Parter of Veils": {"type": "Legendary Planeswalker — Narset", "mana_cost": "{1}{U}{U}", "cmc": 3,
                                 "text": "Each opponent can't draw more than one card each turn. "
                                         "-2: Look at the top four cards of your library..."},
    "Notion Thief": {"type": "Creature — Human Rogue", "mana_cost": "{2}{U}", "cmc": 3,
                      "text": "Flash. If an opponent would draw a card except the first one "
                              "they draw in each of their draw steps, instead that player skips "
                              "that draw and you draw a card."},
    "Orcish Bowmasters": {"type": "Creature — Orc Archer", "mana_cost": "{1}{B}", "cmc": 2,
                           "text": "Flash. When Orcish Bowmasters enters, it deals 1 damage to "
                                    "any target. Whenever an opponent draws a card except the "
                                    "first one they draw in each of their draw steps, you may "
                                    "pay {1}. If you do, create a 1/1 black Orc Army creature "
                                    "token, then that token deals 1 damage to any target."},
    THASSAS_ORACLE_NAME: {"type": "Creature — Merfolk Wizard", "mana_cost": "{1}{U}{U}", "cmc": 3,
                           "text": "When Thassa's Oracle enters the battlefield, look at the "
                                   "top X cards of your library, where X is your devotion to "
                                   "blue. Put up to one of them on top of your library and the "
                                   "rest on the bottom in a random order. Then if X is greater "
                                   "than or equal to the number of cards in your library, you "
                                   "win the game."},
    DEMONIC_CONSULTATION_NAME: {"type": "Sorcery", "mana_cost": "{B}{B}", "cmc": 2,
                                 "text": "Name a card. Search your library for that many cards "
                                         "and exile them, then shuffle. If the card named this "
                                         "way is a card, exile cards from the top of your "
                                         "library until you exile a card with that name, then "
                                         "exile the rest of your library."},
    TAINTED_PACT_NAME: {"type": "Instant", "mana_cost": "{U}{U}", "cmc": 2,
                         "text": "You may exile a blue card from your hand rather than pay this "
                                 "spell's mana cost. Exile cards from the top of your library "
                                 "until you exile a card that's not a basic land. You may play "
                                 "that card this turn. Then shuffle the rest into your library. "
                                 "(This spell requires no two cards in your library to have the "
                                 "same name.)"},

    # ---- Underworld Breach / Lion's Eye Diamond / Brain Freeze (see rogfarm001_breach_loop.py) --
    "Underworld Breach": {"type": "Enchantment", "mana_cost": "{1}{R}", "cmc": 2,
                           "text": "Each nonland card in your graveyard has escape. The escape "
                                   "cost is equal to the card's mana cost plus exile three other "
                                   "cards from your graveyard. At the beginning of the end step, "
                                   "sacrifice this enchantment."},
    "Lion's Eye Diamond": {"type": "Artifact", "mana_cost": "{0}", "cmc": 0,
                            "text": "Discard your hand, Sacrifice Lion's Eye Diamond: Add three "
                                    "mana of any one color. Activate only any time you could "
                                    "cast an instant."},
    "Brain Freeze": {"type": "Instant", "mana_cost": "{1}{U}", "cmc": 2,
                      "text": "Target player mills three cards. Storm."},

    # ---- Flashback (Secrets of Strixhaven, 2026 - real card, released after this model's own
    # training data cutoff; user-confirmed and WebSearch-verified this task after an initial
    # false negative) ----
    "Flashback": {"type": "Instant", "mana_cost": "{R}", "cmc": 1,
                  "text": "Target instant or sorcery card in your graveyard gains flashback "
                          "until end of turn. The flashback cost is equal to its mana cost."},

    # ---- remaining cards needed for full deck coverage (see missing-entry audit) ----
    "Birgi, God of Storytelling // Harnfel, Horn of Bounty": {
        "type": "Legendary Creature — God", "mana_cost": "{2}{R}", "cmc": 3,
        "text": "Whenever you cast a spell, add {R}. Until end of turn, you don't lose this mana "
                "as steps and phases end. Creatures you control can boast twice each turn. "
                "(Modeled at its front face only - the MDFC land back face, Harnfel, Horn of "
                "Bounty, is not modeled, undercount-only, matching this engine's established "
                "no-MDFC-alternate-face precedent.)",
    },
    "Hexing Squelcher": {"type": "Creature — Devil", "mana_cost": "{1}{R}", "cmc": 2,
                          "text": "This spell can't be countered. Ward—Pay 2 life. Spells you "
                                  "control can't be countered. Other creatures you control have "
                                  "Ward—Pay 2 life."},
    "Deadly Rollick": {"type": "Instant", "mana_cost": "{1}{B}", "cmc": 2,
                        "text": "You may cast Deadly Rollick for free if you control a "
                                "commander. Exile target creature."},
    "Flare of Duplication": {"type": "Instant", "mana_cost": "{2}{R}{R}", "cmc": 4,
                              "text": "You may sacrifice a nontoken red creature rather than "
                                      "pay this spell's mana cost. Copy target spell you "
                                      "control."},
    "Dramatic Reversal": {"type": "Instant", "mana_cost": "{U}", "cmc": 1,
                           "text": "Untap all nonland permanents you control."},
    "Final Fortune": {"type": "Sorcery", "mana_cost": "{1}{R}", "cmc": 2,
                       "text": "Take an extra turn after this one. At the beginning of that "
                               "turn's end step, you lose the game. This spell can't be "
                               "countered. (Judgment-heavy, game-losing-risk spell - not "
                               "auto-cast - excluded.)"},
    "Jeska's Will": {"type": "Sorcery", "mana_cost": "{2}{R}", "cmc": 3,
                      "text": "Choose one. If you control a commander as you cast this spell, "
                              "you may choose both instead. Add {R} for each card in target "
                              "opponent's hand. Exile the top three cards of your library. You "
                              "may play them this turn. (Modeled as excluded from auto-cast - "
                              "opponent-hand-size-dependent mode not representable in this solo "
                              "model.)"},
    "Strike It Rich": {"type": "Sorcery", "mana_cost": "{R}", "cmc": 1,
                        "text": "Create a Treasure token. Flashback {2}{R}."},
    "Timetwister": {"type": "Sorcery", "mana_cost": "{2}{U}", "cmc": 3,
                     "text": "Each player shuffles their hand, graveyard, and library together, "
                             "then draws seven cards."},
    "Wheel of Fortune": {"type": "Sorcery", "mana_cost": "{2}{R}", "cmc": 3,
                          "text": "Each player discards their hand, then draws seven cards."},
    "Windfall": {"type": "Sorcery", "mana_cost": "{2}{U}", "cmc": 3,
                 "text": "Each player discards their hand, then draws cards equal to the "
                         "greatest number of cards a player discarded this way."},
    "Will of the Jeskai": {"type": "Sorcery", "mana_cost": "{3}{R}", "cmc": 4,
                            "text": "Choose one. If you control a commander as you cast this "
                                    "spell, you may choose both instead. Each player may "
                                    "discard their hand and draw five cards. Each instant and "
                                    "sorcery card in your graveyard gains flashback until end "
                                    "of turn; the flashback cost is equal to its mana cost."},
    "Mox Opal": {"type": "Artifact", "mana_cost": "{0}", "cmc": 0,
                 "text": "Metalcraft — {T}: Add one mana of any color. Activate only if you "
                         "control three or more artifacts. (Metalcraft precondition not "
                         "verified by this engine's board-state model - modeled at its "
                         "guaranteed 0-mana floor, undercount-only - excluded from auto-cast.)"},
    "Paradise Mantle": {"type": "Artifact — Equipment", "mana_cost": "{1}", "cmc": 1,
                         "text": "Equipped creature has '{T}: Add one mana of any color.' "
                                 "Equip {0}. (Requires a non-summoning-sick creature this "
                                 "engine's board-state model doesn't verify - modeled at 0 mana, "
                                 "undercount-only - excluded from auto-cast.)"},
    "Springleaf Drum": {"type": "Artifact", "mana_cost": "{1}", "cmc": 1,
                         "text": "{T}, Tap an untapped creature you control: Add one mana of "
                                 "any color. (Requires an untapped creature this engine's "
                                 "board-state model doesn't verify - modeled at 0 mana, "
                                 "undercount-only - excluded from auto-cast.)"},
    "Fellwar Stone": {"type": "Artifact", "mana_cost": "{2}", "cmc": 2,
                       "text": "{T}: Add one mana of any color that a land an opponent "
                               "controls could produce. (Structurally opponent-dependent - "
                               "produces 0 mana in this solo model, same established treatment "
                               "as Exotic Orchard - excluded from auto-cast.)"},
    "Into the Flood Maw": {"type": "Instant", "mana_cost": "{1}{U}", "cmc": 2,
                            "text": "Put target nonland permanent an opponent controls on top "
                                    "of its owner's library. Its owner creates a 1/1 blue Otter "
                                    "Pirate creature token. (No opposing permanents exist in "
                                    "this solo model - not auto-cast - excluded.)"},
    "Rograkh, Son of Rohgahh": {"type": "Legendary Creature — Homunculus Mutant", "mana_cost": "{R}", "cmc": 1,
                                 "text": "Haste. Rograkh, Son of Rohgahh can't block. Whenever "
                                         "you cast a spell, put a +1/+1 counter on Rograkh, Son "
                                         "of Rohgahh. (Real mainboard card in Blue Farm's list, "
                                         "distinct from its use as a commander in Stock RogSi/R1 "
                                         "- see COMMANDER_IDENTITY_COLORS/NEW_COMMANDER_COSTS "
                                         "for the commander-mode cost {R} used there instead.)"},
})

# Section 7's four required engine-timing categories, plus an informational 5th ("protection")
# for real board-presence cards that don't fit those four. Consumed by the Stage 2 harness for
# the "autonomous / opponent-dependent / wheel-payoff / pure mana-resource" breakdown the
# assignment explicitly requires (Section 7: "Separate engines into: autonomous; opponent-
# dependent; wheel-payoff; pure mana/resource.").
ENGINE_SECTION7_CLASS = {
    "The One Ring": "autonomous",
    "Necropotence": "autonomous",
    "Valley Floodcaller": "autonomous",
    "Tataru Taru": "autonomous",
    "Narset, Parter of Veils": "wheel_payoff",
    "Notion Thief": "wheel_payoff",
    "Orcish Bowmasters": "opponent_dependent",
    "Ragavan, Nimble Pilferer": "opponent_dependent",
    "Hexing Squelcher": "protection",
    # Already-registered real-cached cards (from the base Tymna/Thrasios engine, reused here):
    "Faerie Mastermind": "wheel_payoff",  # its "opponent's 2nd card of the turn" trigger IS a wheel-specific payoff
    "Mystic Remora": "autonomous",
    "Rhystic Study": "opponent_dependent",  # its real value is opponents choosing to pay
    "Smothering Tithe": "opponent_dependent",
    "Esper Sentinel": "opponent_dependent",
    d6.LOTHO_NAME: "opponent_dependent",  # triggers off ANY player's 2nd spell each turn
    "Grand Abolisher": "protection",
}

NEW_ENGINE_CLASSES = {
    "The One Ring": "card_advantage", "Necropotence": "card_advantage",
    "Valley Floodcaller": "spell_enabler", "Tataru Taru": "card_advantage",
    "Narset, Parter of Veils": "wheel_asymmetry", "Notion Thief": "wheel_asymmetry",
    "Orcish Bowmasters": "opponent_dependent_disruption",
    "Ragavan, Nimble Pilferer": "opponent_dependent_value",
    "Hexing Squelcher": "protection",
}

NEW_INTERACTION_CLASSES = {
    "Daze": "return_island",  # real, distinct alt-cost tag - dispatched via the monkeypatch hooks
    "Pyroblast": "cheap_stack", "Red Elemental Blast": "cheap_stack",
    "Deflecting Swat": "free_if_commander",  # dispatched natively by interaction_model.py, no patch needed
}

NEW_TUTORS = {"Mystical Tutor", "Beseech the Mirror"}
NEW_TUTOR_DESTINATION_LIBRARY_TOP = {"Mystical Tutor"}

NEW_MANA_SOURCES = {
    "Grim Monolith": {"generic": 3, "creature": False},
}
NEW_ACCELERATION = {"Grim Monolith"}  # real permanents whose mana output is actually modeled

NEW_ENGINE_CLASSES["Birgi, God of Storytelling // Harnfel, Horn of Bounty"] = "storm_mana_engine"
ENGINE_SECTION7_CLASS["Birgi, God of Storytelling // Harnfel, Horn of Bounty"] = "mana_resource"
NEW_INTERACTION_CLASSES["Deadly Rollick"] = "free_if_commander"
NEW_ALT_COST_SPECS["Flare of Duplication"] = {"type": "sac_creature", "color": "R"}
NEW_INTERACTION_CASTABLE["Flare of Duplication"] = "sac_creature"

DAZE_NAME = "Daze"
SIMIAN_SPIRIT_GUIDE_NAME = "Simian Spirit Guide"


def _is_island_land_on_battlefield(state, cards):
    for land in state.lands:
        if land.tapped:
            continue
        if _is_island(land.name, cards):
            return land
    return None


def daze_alt_cost_available(state, cards):
    return _is_island_land_on_battlefield(state, cards) is not None


def _daze_is_live(state, cards):
    from opening_hand_policy import is_currently_castable
    gen, pips, x = ohm.parse_cost(cards[DAZE_NAME]["mana_cost"])
    mana_ok = (x == 0) and is_currently_castable(state, gen, pips)
    return mana_ok or daze_alt_cost_available(state, cards)


def _daze_resolve(state, cards):
    from opening_hand_policy import _try_pay
    gen, pips, x = ohm.parse_cost(cards[DAZE_NAME]["mana_cost"])
    if x == 0:
        plan = _try_pay(state, gen, pips)
        if plan is not None:
            return ("mana", plan)
    land = _is_island_land_on_battlefield(state, cards)
    if land is not None:
        return ("return_island", land)
    return None


def _daze_commit(name, resolution, state):
    kind, payload = resolution
    if kind == "return_island":
        if payload in state.lands:
            state.lands.remove(payload)


def try_cast_cabal_ritual(state, cards):
    """Real Oracle text: Add BBB, or BBBBB with threshold (7+ graveyard cards). Excluded from
    auto-cast (net-mana instant, same DECKBUILD-007 Dark Ritual precedent) - callable directly
    by analysis scripts that want to model deliberate Ritual usage."""
    from opening_hand_policy import _try_pay, _commit_payment, Perm
    name = "Cabal Ritual"
    if name not in state.hand:
        return False
    plan = _try_pay(state, 1, ["B"])
    if plan is None:
        return False
    _commit_payment(state, plan)
    state.hand.remove(name)
    state.graveyard.append(name)
    state.cast_log.append((state.turn, name, "ritual"))
    produced = 5 if len(state.graveyard) >= 7 else 3
    for _ in range(produced):
        state.nonland_perms.append(Perm("Cabal Ritual Residue", state.turn, False))
    return True


def try_cast_rite_of_flame(state, cards):
    """Real Oracle text: {R}, Add RR (net +1). Excluded from auto-cast, same precedent."""
    from opening_hand_policy import _try_pay, _commit_payment, Perm
    name = "Rite of Flame"
    if name not in state.hand:
        return False
    plan = _try_pay(state, 0, ["R"])
    if plan is None:
        return False
    _commit_payment(state, plan)
    state.hand.remove(name)
    state.graveyard.append(name)
    state.cast_log.append((state.turn, name, "ritual"))
    for _ in range(2):
        state.nonland_perms.append(Perm("Rite of Flame Residue", state.turn, False))
    return True


def sweep_stranded_ritual_residue(state, turn):
    """Same real-Magic 'mana empties at end of turn' sweep as DECKBUILD-007's Dark Ritual
    residue - covers Cabal Ritual/Rite of Flame's own residue names too."""
    names = {"Cabal Ritual Residue", "Rite of Flame Residue"}
    stranded = [
        p for p in state.nonland_perms
        if p.name in names and p.entered_turn == turn and not p.tapped
    ]
    for p in stranded:
        state.nonland_perms.remove(p)
    return len(stranded)


NEW_LAND_COLOR_SETS.update({
    "Badlands": {"B", "R"}, "Plateau": {"W", "R"}, "Blood Crypt": {"B", "R"},
    "Steam Vents": {"U", "R"}, "Watery Grave": {"U", "B"},
    "Spire of Industry": set(ohm.COLORS),
})
NEW_GENERIC_LANDS = {"Cavern of Souls": 1, "Phyrexian Tower": 1}

NEW_DUAL_LAND_BASIC_TYPES = {
    "Volcanic Island": frozenset({"Island", "Mountain"}),
    "Badlands": frozenset({"Swamp", "Mountain"}),
    "Plateau": frozenset({"Plains", "Mountain"}),
}

# Real, Grixis/4c commander identities for Arcane Signet's "any color in commander(s)' identity"
# - keyed by (frozenset of commander names) so install_new_card_tables() can select the right one
# for whichever deck is currently being simulated. Registered as MANA_SOURCES, not GENERIC_LANDS
# (it's an artifact, not a land).
COMMANDER_IDENTITY_COLORS = {
    frozenset({"Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"}): {"U", "B", "R"},
    frozenset({"Tymna the Weaver", "Kraum, Ludevic's Opus"}): {"W", "U", "B", "R"},
}

# Real costs for the 3 commanders new to this project (Tymna the Weaver is already registered).
NEW_COMMANDER_COSTS = {
    "Rograkh, Son of Rohgahh": "{R}",
    "Silas Renn, Seeker Adept": "{1}{U}{B}",
    "Kraum, Ludevic's Opus": "{1}{U}{R}",
}
_ORIG_COMMANDERS_DICT = None


# Monkeypatch hooks: interaction_model.py's interaction_is_live/resolve_interaction_cast/
# commit_interaction_cast dispatch purely on ALT_COST_SPECS[name]["type"], so Foil's new type
# needs a branch in each. Rather than editing the shared module's if/elif chains directly (which
# would hardcode a rogfarm-only mechanic into a file every other task also imports), these
# wrapper functions are what analysis scripts call instead - installed/uninstalled alongside the
# data tables, exactly like every other per-task engine extension in this project.
#
# CORRECTNESS NOTE (found while smoke-testing the Stage 2 harness): reassigning
# im.interaction_is_live etc. only updates interaction_model.py's OWN module attribute. Every
# caller this project's actual simulation path goes through - opening_hand_metrics.py's
# snapshot_metrics() and opening_hand_policy.py's develop_turn() - imported these three names
# directly ("from interaction_model import interaction_is_live", etc.) at THEIR OWN import time,
# binding their own module-level names to the ORIGINAL function objects; rebinding
# interaction_model's attribute never touches those already-bound references. Every module that
# holds one of these stale direct-import bindings must be patched individually.
import opening_hand_metrics as ohmetrics  # noqa: E402
import opening_hand_policy as ohp  # noqa: E402

_ORIG_IS_LIVE = im.interaction_is_live
_ORIG_RESOLVE = im.resolve_interaction_cast
_ORIG_COMMIT = im.commit_interaction_cast
_ORIG_METRICS_IS_LIVE = ohmetrics.interaction_is_live
_ORIG_POLICY_RESOLVE = ohp.resolve_interaction_cast
_ORIG_POLICY_COMMIT = ohp.commit_interaction_cast


def _patched_is_live(name, state, cards):
    if name == FOIL_NAME:
        return _foil_is_live(state, cards)
    return _ORIG_IS_LIVE(name, state, cards)


def _patched_resolve(name, state, cards):
    if name == FOIL_NAME:
        return _foil_resolve(state, cards)
    return _ORIG_RESOLVE(name, state, cards)


def _patched_commit(name, resolution, state):
    if name == FOIL_NAME and resolution[0] == "discard_island_plus_other":
        _foil_commit(name, resolution, state)
        return
    if name == DAZE_NAME and resolution[0] == "return_island":
        _daze_commit(name, resolution, state)
        return
    _ORIG_COMMIT(name, resolution, state)


_ORIG_AVAILABLE_SOURCES = None


def _patched_available_sources(self):
    out = _ORIG_AVAILABLE_SOURCES(self)
    # Simian Spirit Guide: real Oracle text is an activated ability FROM HAND ("Exile Simian
    # Spirit Guide from your hand: Add {R}"), not a spell - modeled as a virtual untapped source
    # while still in hand, exactly like the base engine's own existing Elvish Spirit Guide
    # precedent (opening_hand_model.py's available_sources() docstring/module notes).
    if SIMIAN_SPIRIT_GUIDE_NAME in self.hand:
        out.append(("__ssg_virtual__", {"R"}, 1))
    return out


def install_new_card_tables(commander_names=None):
    """commander_names: optional 2-tuple/list of this deck's exact commander names. When given,
    the GLOBAL COMMANDERS dict (opening_hand_model.COMMANDERS - shared across every task, keyed
    by name, with each HandState computing self.command_zone = set(COMMANDERS.keys()) fresh at
    construction time) is temporarily REPLACED (not merged) with a dict containing ONLY those two
    commanders, so a RogSi/R1 simulation never sees Tymna/Kraum sitting in its command zone and
    vice versa. Restored exactly by uninstall_new_card_tables(). Also selects Arcane Signet's
    real color-identity-dependent mana output for that same commander pair."""
    global _ORIG_COMMANDERS_DICT, _ORIG_AVAILABLE_SOURCES

    for name, tag in NEW_INTERACTION_CASTABLE.items():
        ohm.INTERACTION_CASTABLE[name] = tag
    for name, tag in NEW_INTERACTION_CLASSES.items():
        ohm.INTERACTION_CASTABLE[name] = tag
    im.ALT_COST_SPECS.update(NEW_ALT_COST_SPECS)
    im.ALT_COST_SPECS[DAZE_NAME] = {"type": "return_island"}
    im.ALT_COST_SPECS["Deflecting Swat"] = {"type": "free_if_commander"}
    im.interaction_is_live = _patched_is_live
    im.resolve_interaction_cast = _patched_resolve
    im.commit_interaction_cast = _patched_commit
    ohmetrics.interaction_is_live = _patched_is_live
    ohp.resolve_interaction_cast = _patched_resolve
    ohp.commit_interaction_cast = _patched_commit

    for name, colors in NEW_LAND_COLOR_SETS.items():
        ohm.LAND_COLOR_SETS[name] = colors
    for name, n in NEW_GENERIC_LANDS.items():
        ohm.GENERIC_LANDS[name] = n
    for name, types in NEW_DUAL_LAND_BASIC_TYPES.items():
        ohm.DUAL_LAND_BASIC_TYPES[name] = types

    for name, spec in NEW_MANA_SOURCES.items():
        ohm.MANA_SOURCES[name] = spec
    for name in NEW_ACCELERATION:
        ohm.ACCELERATION.add(name)

    for name, tag in NEW_ENGINE_CLASSES.items():
        ohm.ENGINES[name] = tag
    for name in NEW_TUTORS:
        ohm.TUTORS.add(name)
    for name in NEW_TUTOR_DESTINATION_LIBRARY_TOP:
        ohm.TUTOR_DESTINATION_LIBRARY_TOP.add(name)

    ma2.install_new_land_tables()
    d6.install_new_card_tables()  # cascades deckbuild004/mana_audit002's own installs

    if commander_names is not None:
        key = frozenset(commander_names)
        colors = COMMANDER_IDENTITY_COLORS.get(key, set())
        ohm.MANA_SOURCES["Arcane Signet"] = {"colors": colors, "creature": False}
        ohm.ACCELERATION.add("Arcane Signet")
        # In-place mutation, NOT reassignment: opening_hand_policy.py (and other modules) did
        # "from opening_hand_model import COMMANDERS" at THEIR OWN import time, binding their own
        # name to this exact dict OBJECT - reassigning ohm.COMMANDERS to a new object (as an
        # earlier version of this function did) only rebinds THIS module's attribute and leaves
        # every other module still looking at the old dict, which is how a RogSi simulation
        # ended up with Tymna/Thrasios sitting in its command_zone (found via the Stage 2
        # harness's smoke test - see rogfarm001_cards regression tests for the isolation check
        # this bug produced). Mutating the same object in place is visible everywhere.
        _ORIG_COMMANDERS_DICT = dict(ohm.COMMANDERS)  # snapshot of the CONTENT, for restore
        new_commanders = {}
        for name in commander_names:
            if name in _ORIG_COMMANDERS_DICT:
                new_commanders[name] = _ORIG_COMMANDERS_DICT[name]
            elif name in NEW_COMMANDER_COSTS:
                new_commanders[name] = {"cost": NEW_COMMANDER_COSTS[name]}
            else:
                raise ValueError(f"no cost registered for commander {name!r}")
        ohm.COMMANDERS.clear()
        ohm.COMMANDERS.update(new_commanders)

    if SIMIAN_SPIRIT_GUIDE_NAME in NEW_CARD_DATA:
        from opening_hand_policy import HandState
        if _ORIG_AVAILABLE_SOURCES is None:
            _ORIG_AVAILABLE_SOURCES = HandState.available_sources
        HandState.available_sources = _patched_available_sources


def uninstall_new_card_tables():
    global _ORIG_COMMANDERS_DICT

    for name in NEW_INTERACTION_CASTABLE:
        ohm.INTERACTION_CASTABLE.pop(name, None)
    for name in NEW_INTERACTION_CLASSES:
        ohm.INTERACTION_CASTABLE.pop(name, None)
    for name in NEW_ALT_COST_SPECS:
        im.ALT_COST_SPECS.pop(name, None)
    im.ALT_COST_SPECS.pop(DAZE_NAME, None)
    im.ALT_COST_SPECS.pop("Deflecting Swat", None)
    im.interaction_is_live = _ORIG_IS_LIVE
    im.resolve_interaction_cast = _ORIG_RESOLVE
    im.commit_interaction_cast = _ORIG_COMMIT
    ohmetrics.interaction_is_live = _ORIG_METRICS_IS_LIVE
    ohp.resolve_interaction_cast = _ORIG_POLICY_RESOLVE
    ohp.commit_interaction_cast = _ORIG_POLICY_COMMIT

    for name in NEW_LAND_COLOR_SETS:
        ohm.LAND_COLOR_SETS.pop(name, None)
    for name in NEW_GENERIC_LANDS:
        ohm.GENERIC_LANDS.pop(name, None)
    for name in NEW_DUAL_LAND_BASIC_TYPES:
        ohm.DUAL_LAND_BASIC_TYPES.pop(name, None)

    for name in NEW_MANA_SOURCES:
        ohm.MANA_SOURCES.pop(name, None)
    for name in NEW_ACCELERATION:
        ohm.ACCELERATION.discard(name)
    ohm.MANA_SOURCES.pop("Arcane Signet", None)
    ohm.ACCELERATION.discard("Arcane Signet")

    for name in NEW_ENGINE_CLASSES:
        ohm.ENGINES.pop(name, None)
    for name in NEW_TUTORS:
        ohm.TUTORS.discard(name)
    for name in NEW_TUTOR_DESTINATION_LIBRARY_TOP:
        ohm.TUTOR_DESTINATION_LIBRARY_TOP.discard(name)

    d6.uninstall_new_card_tables()

    if _ORIG_COMMANDERS_DICT is not None:
        ohm.COMMANDERS.clear()
        ohm.COMMANDERS.update(_ORIG_COMMANDERS_DICT)
        _ORIG_COMMANDERS_DICT = None

    if _ORIG_AVAILABLE_SOURCES is not None:
        from opening_hand_policy import HandState
        HandState.available_sources = _ORIG_AVAILABLE_SOURCES


def all_cards_dict(base_cards):
    merged = dict(NEW_CARD_DATA)
    merged.update(d6.NEW_CARD_DATA)
    merged.update(ma2.NEW_LAND_CARDS)
    merged.update(d7.NEW_CARD_DATA)
    merged.update(base_cards)
    return merged
