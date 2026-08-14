"""SIM-001 MULL-006 section 10 — relevant agency, new dimension #5.

Upgrades the project's existing "live interaction" model (interaction_model.interaction_is_live,
already the authoritative alt-cost-aware castability check) into the assignment's required four-
tier classification. A Force of Will being live is not enough to conclude it is highly valuable
against every pod - relevance depends on whether the specific pod's threat axes are the kind this
card actually answers.

    INTERACTION_PRESENT   the card is physically in the hand at all (regardless of castability).
    INTERACTION_CASTABLE  its PRINTED mana cost is payable right now (ignores alternate costs -
                           the pre-SOLO-003 approximation, kept here only as an intermediate tier).
    INTERACTION_LIVE      interaction_model.interaction_is_live() is True - payable via printed
                           mana cost OR a real, currently-available alternate cost (pitch, free-if-
                           commander, sacrifice, etc.) - the project's existing authoritative
                           castability check, reused unchanged.
    INTERACTION_RELEVANT  INTERACTION_LIVE AND the card's real functional threat-axis tag(s)
                           intersect the target pod archetype's expected threat axes.

THREAT AXES (assignment's own given examples, reused verbatim where given; archetypes the
assignment did not explicitly cover are extrapolated from pod_archetypes.py's existing
speed/primary_resource_axis/interaction_demand fields, disclosed as extrapolated rather than
pilot-verbatim):

    RogSi (TURBO/ROGSI-LIKE, given)      -> stack_interaction, silence_effect, free_interaction,
                                             early_win_prevention, anti_combo
    Kinnan (KINNAN/CREATURE ENGINE, given)-> creature_removal, commander_interaction, theft,
                                             activation_disruption, stack_interaction
    Sisay (given)                        -> commander_interaction, activation_disruption,
                                             creature_removal
    Tayam (given)                        -> graveyard_interaction, board_interaction,
                                             engine_disruption
    Tivit (GRIND/TIVIT-LIKE, given)      -> resilient_card_advantage, commander_interaction,
                                             long_game_agency
    Rog/Thras Tree Farm (extrapolated)   -> creature_removal, engine_disruption, stack_interaction
    Blue Farm (extrapolated)             -> resilient_card_advantage, long_game_agency,
                                             stack_interaction
    Etali (extrapolated)                 -> stack_interaction, creature_removal
    stax_heavy (extrapolated)            -> stack_interaction, anti_combo
    midrange_grind (extrapolated)        -> stack_interaction, resilient_card_advantage

CARD THREAT-AXIS TAGS: hand-derived from each card's REAL Oracle function (not its printed mana
cost/alt-cost TYPE, which interaction_model.py already tags separately for a different purpose).
This deck's INTERACTION_CASTABLE suite is majority stack/counter-based - it has NO dedicated
creature-removal or activation-disruption spell. This is a genuine, disclosed structural gap:
against creature/activation-centric pods (Kinnan, Sisay), relevant_agency is capped even when
live_agency is high, because the live cards simply don't answer that axis.

GOVERNING RULE (assignment's own explicit boundary): pod relevance may UPGRADE a coherent marginal
hand. It may NOT rescue "mana + interaction + no destination" into a premium keep - this module
only REPORTS live_agency_score and relevant_agency_score; it does not itself grant any keep
recommendation, and callers must respect this boundary when combining it with a destination-first
policy (task #117's contextual policy comparison is where that combination happens, not here).
"""
from opening_hand_model import INTERACTION_CASTABLE, parse_cost
from opening_hand_policy import is_currently_castable
from interaction_model import interaction_is_live

AGENCY_PROVENANCE = "MODEL_DERIVED"

CARD_THREAT_AXES = {
    "Fierce Guardianship": {"stack_interaction", "free_interaction"},
    "Flare of Denial": {"stack_interaction"},
    "Flusterstorm": {"stack_interaction", "anti_combo"},
    "Force of Negation": {"stack_interaction", "free_interaction"},
    "Force of Will": {"stack_interaction", "free_interaction"},
    "Mental Misstep": {"stack_interaction"},
    "Pact of Negation": {"stack_interaction", "free_interaction"},
    "Swan Song": {"stack_interaction"},
    "Mindbreak Trap": {"stack_interaction", "anti_combo"},
    "Silence": {"silence_effect", "early_win_prevention"},
    "Misdirection": {"stack_interaction"},
    "Commandeer": {"stack_interaction", "theft"},
    "Subtlety": {"stack_interaction"},
    "Veil of Summer": {"stack_interaction"},
    "Endurance": {"graveyard_interaction"},
}
assert set(CARD_THREAT_AXES) == set(INTERACTION_CASTABLE)

ARCHETYPE_THREAT_AXES = {
    "RogSi": {"stack_interaction", "silence_effect", "free_interaction", "early_win_prevention", "anti_combo"},
    "Kinnan": {"creature_removal", "commander_interaction", "theft", "activation_disruption", "stack_interaction"},
    "Sisay": {"commander_interaction", "activation_disruption", "creature_removal"},
    "Tayam": {"graveyard_interaction", "board_interaction", "engine_disruption"},
    "Tivit": {"resilient_card_advantage", "commander_interaction", "long_game_agency"},
    "Rog/Thras Tree Farm": {"creature_removal", "engine_disruption", "stack_interaction"},
    "Blue Farm": {"resilient_card_advantage", "long_game_agency", "stack_interaction"},
    "Etali": {"stack_interaction", "creature_removal"},
    "stax_heavy": {"stack_interaction", "anti_combo"},
    "midrange_grind": {"stack_interaction", "resilient_card_advantage"},
}
EXTRAPOLATED_ARCHETYPES = {"Rog/Thras Tree Farm", "Blue Farm", "Etali", "stax_heavy", "midrange_grind"}
GIVEN_ARCHETYPES = set(ARCHETYPE_THREAT_AXES) - EXTRAPOLATED_ARCHETYPES


def _castable_by_printed_cost(name, state, cards):
    gen, pips, x = parse_cost(cards[name]["mana_cost"])
    return x == 0 and is_currently_castable(state, gen, pips)


def classify_card_agency(name, state, cards, archetype=None):
    """Returns the four-tier classification for one interaction card, plus (if `archetype` is
    given) whether it is INTERACTION_RELEVANT against that specific archetype. Returns None if
    `name` is not in the tracked INTERACTION_CASTABLE set."""
    if name not in CARD_THREAT_AXES:
        return None
    present = name in state.hand
    castable = present and _castable_by_printed_cost(name, state, cards)
    live = present and interaction_is_live(name, state, cards)
    relevant = False
    if live and archetype is not None:
        archetype_axes = ARCHETYPE_THREAT_AXES.get(archetype, set())
        relevant = bool(CARD_THREAT_AXES[name] & archetype_axes)
    return {
        "card": name,
        "interaction_present": present,
        "interaction_castable": castable,
        "interaction_live": live,
        "interaction_relevant": relevant,
        "threat_axes": sorted(CARD_THREAT_AXES[name]),
    }


def hand_agency_scores(state, cards, archetypes=None):
    """Returns live_agency_score (count of hand's LIVE interaction cards, archetype-independent)
    and relevant_agency_score per archetype (count of LIVE cards whose threat axes intersect that
    archetype's expected threat axes). `archetypes` defaults to every known archetype."""
    archetypes = archetypes if archetypes is not None else sorted(ARCHETYPE_THREAT_AXES)
    live_cards = [n for n in state.hand if n in CARD_THREAT_AXES and interaction_is_live(n, state, cards)]
    live_agency_score = len(live_cards)
    relevant_agency_score = {}
    relevant_cards_by_archetype = {}
    for arch in archetypes:
        axes = ARCHETYPE_THREAT_AXES.get(arch, set())
        relevant = [n for n in live_cards if CARD_THREAT_AXES[n] & axes]
        relevant_agency_score[arch] = len(relevant)
        relevant_cards_by_archetype[arch] = relevant
    return {
        "live_agency_score": live_agency_score,
        "live_cards": live_cards,
        "relevant_agency_score": relevant_agency_score,
        "relevant_cards_by_archetype": relevant_cards_by_archetype,
    }
