"""SIM-001 MULL-005 — non-simulated pod-conditioning overlay.

Governing constraint (verbatim from the assignment): "Pod context modifies a structurally coherent
hand. It does not rescue a hand with no credible engine trajectory." This module is explicitly NOT
simulation output - no 4-player matchup has been run in this project (that is out of scope for this
phase; see the assignment's stop condition). Everything here is a disclosed STRATEGIC PRIOR, built
from general cEDH archetype knowledge, meant to be edited/corrected by a human pilot, never treated
as measured fact. Every pod-conditioned recommendation this module produces carries two SEPARATE
confidence labels:
  - structural_confidence: "SIMULATED" - comes from real T1-T3 simulation (structural_hand_grade /
    TRAJECTORY_MACHINE), exactly as validated elsewhere in this phase.
  - pod_confidence: "STRATEGIC_PRIOR_UNVALIDATED" - always this value, on every archetype, always -
    because none of it has been checked against actual pod simulation yet.

Per the assignment, this module must NEVER phrase a pod modifier as a simulated statistic ("wins
63% against RogSi"). Only structural language is used ("receives a positive keep modifier because
X plays fast and punishes slow starts").

ARCHETYPES: multi-dimensional tags (speed, primary_resource_axis, interaction_demand,
resilience_profile) plus qualitative "increases value of / decreases value of" priors, for the
named pod archetypes/commanders: RogSi, Kinnan, Rog/Thras Tree Farm, Blue Farm, Sisay, Tayam,
Tivit, Etali, stax-heavy pods, and generic midrange/grind pods.

POD_MODIFIERS: bounded +2/+1/0/-1/-2 adjustments per archetype, over a small fixed set of hand
FEATURE CATEGORIES (never raw win-rate numbers). Modifiers can shift a hand up or down within its
structural band but can NEVER promote a structural SHIP into a keep - see pod_conditioned_grade().
"""

FEATURE_CATEGORIES = (
    "free_or_cheap_interaction",   # Force of Will/Fierce Guardianship/Flusterstorm/Swan Song/etc.
    "any_live_interaction",        # any castable interaction at all, paid or free
    "raw_speed_low_curve",         # premium T1 engine, T1 executable accel with a real destination
    "card_advantage_engine",       # any engine card present (Tier A/B/C alike)
    "mana_resilience",             # 3+ lands / redundant colored sources, not just raw accel count
    "graveyard_interaction",       # graveyard hate specifically (not modeled elsewhere in this deck's
                                    # interaction suite in detail - flagged qualitatively only)
    "proactive_early_development", # anything that develops the board/engine before turn 3
    "tutor_flexibility",           # any live tutor, regardless of CMC-based T2 conversion odds
    "redundancy_resilience",       # 2+ independent lines/engines in the same hand
)

ARCHETYPES = {
    "RogSi": {
        "speed": "very_fast",
        "primary_resource_axis": "low curve + fast mana + cheap tutors, minimal grind",
        "interaction_demand": "high - needs cheap/free interaction to survive to your own turns",
        "resilience_profile": "low redundancy, high explosiveness - a single answer often stops the whole line",
        "increases_value_of": [
            "free or alternate-cost interaction (it must be live before their combo turn, not eventually)",
            "any T1-T2 proactive development - the game can be over before a slow hand matters",
            "redundant fast starts (RogSi punishes slow/greedy hands harder than any other pod archetype here)",
        ],
        "decreases_value_of": [
            "pure card-advantage engines with no early defensive value (Rhystic Study alone does nothing turn 2 vs a turn-3 kill)",
            "tutors that pay off on turn 3+ (tutor_live_but_delayed outcomes are close to irrelevant in this matchup)",
            "durdly mana development with no immediate interactive or combo-relevant payoff",
        ],
    },
    "Kinnan": {
        "speed": "fast_to_medium",
        "primary_resource_axis": "mana-doubling into a big X payoff (Walking Ballista/Kinnan combo lines)",
        "interaction_demand": "medium-high - needs an answer to the mana engine itself, not just the payoff",
        "resilience_profile": "moderate - vulnerable if the doubler or the mana base is disrupted, resilient once online",
        "increases_value_of": [
            "interaction that can answer a noncreature mana-doubling permanent, not only creatures",
            "your own fast starts - Kinnan pods are often mana-rich but not always fast to actually close",
            "mana resilience (redundant colored sources) so you aren't the one who stumbles while they ramp",
        ],
        "decreases_value_of": [
            "hands with zero interaction of any kind - Kinnan can go over the top on raw mana if left unchecked",
            "slow, single-line combo attempts with no fallback if disrupted",
        ],
    },
    "Rog/Thras Tree Farm": {
        "speed": "medium",
        "primary_resource_axis": "creature/mana-engine value (Gaea's Cradle style), grindy and resilient - a mirror of this deck's own archetype",
        "interaction_demand": "medium - the matchup is decided by engine tempo more than raw interaction density",
        "resilience_profile": "high - built around redundant engines, hard to fully lock out",
        "increases_value_of": [
            "proactive engines that come online FASTER than theirs (a mirror match rewards tempo)",
            "interaction that can strip a specific synergy piece (Cradle, a key creature) rather than generic removal",
            "redundancy - a mirror match goes long, so a hand with only one plan is fragile",
        ],
        "decreases_value_of": [
            "hands that plan to race on raw damage alone with no engine backing - this matchup rewards engines, not aggression",
        ],
    },
    "Blue Farm": {
        "speed": "slow",
        "primary_resource_axis": "card-advantage/tax value (Rhystic Study, Smothering Tithe, wraths) - classic control grind",
        "interaction_demand": "low-to-medium early, high late - the game is decided by who out-values whom, not who acts first",
        "resilience_profile": "very high - built to survive individual disruption and grind through it",
        "increases_value_of": [
            "your own card-advantage engines - this matchup is decided by compounding advantage, not speed",
            "mana resilience/patience - there is little cost to a slightly slower, more resilient start here",
        ],
        "decreases_value_of": [
            "one-shot interaction with no follow-up - a single Force of Will does not beat a value-grind deck by itself",
            "raw speed with no staying power - Blue Farm out-grinds hands that can't sustain pressure",
        ],
    },
    "Sisay": {
        "speed": "fast_to_medium",
        "primary_resource_axis": "legendary tutor-toolbox chain (Sisay, Weatherlight Captain assembling a combo via successive tutors)",
        "interaction_demand": "high - the combo resolves in one big turn once Sisay is live, so interaction must be timed to that turn",
        "resilience_profile": "low once disrupted mid-chain, but the deck often has redundant entry points",
        "increases_value_of": [
            "stack interaction that can stop a combo chain, ideally free/cheap so it's live on their turn",
            "proactive speed - racing before Sisay assembles is a real plan against a tutor-toolbox deck",
        ],
        "decreases_value_of": [
            "slow grindy plans that let Sisay simply out-tutor you turn after turn",
        ],
    },
    "Tayam": {
        "speed": "medium",
        "primary_resource_axis": "graveyard recursion / aristocrats value-combo (Tayam, Luminous Enigma)",
        "interaction_demand": "medium - centered on disrupting a recursive loop rather than a single spell",
        "resilience_profile": "high once a recursion loop is set up - individual removal is often insufficient",
        "increases_value_of": [
            "graveyard interaction specifically (not modeled in this deck's structural simulation - qualitative only)",
            "resilience/redundancy - this matchup tends to go long",
        ],
        "decreases_value_of": [
            "purely proactive hands with no way to interact with a recursive engine once it's assembled",
        ],
    },
    "Tivit": {
        "speed": "medium",
        "primary_resource_axis": "blink/extra-turn value-combo (Tivit, Seller of Secrets), grindy card-advantage engine into a combo finish",
        "interaction_demand": "medium-high, particularly around extra-turn or blink trigger windows",
        "resilience_profile": "moderate-high - built on compounding value, resilient to single answers",
        "increases_value_of": [
            "interaction, especially anything that can interrupt an extra-turn or blink-trigger sequence",
            "your own card-advantage engines - the matchup can become a value race if their combo is delayed",
        ],
        "decreases_value_of": [
            "hyper-aggressive plans with no staying power - Tivit pods often win by simply outlasting a fast start",
        ],
    },
    "Etali": {
        "speed": "medium_slow",
        "primary_resource_axis": "big-mana ramp/cascade value (Etali, Primal Conqueror) - Temur midrange grind with a large top end",
        "interaction_demand": "medium - mostly about answering their top-end threats before they compound",
        "resilience_profile": "high late, but has a real early-game window before ramp pays off",
        "increases_value_of": [
            "proactive fast starts - Etali pods are usually slower to develop than combo pods, punish that",
            "interaction for their eventual big threats, held rather than spent early",
        ],
        "decreases_value_of": [
            "purely reactive/passive hands - Etali will out-grind a hand with no proactive plan of its own",
        ],
    },
    "stax_heavy": {
        "speed": "slow_by_design",
        "primary_resource_axis": "resource denial - taxes, mana/land destruction, effects that punish multi-piece plans",
        "interaction_demand": "low toward opponents, high toward the stax pieces themselves",
        "resilience_profile": "board-state resilient, resource-fragile - stax decks strip resources from everyone including you",
        "increases_value_of": [
            "mana resilience (redundant colored sources) - stax punishes anyone who stumbles on mana first",
            "proactive early plays BEFORE a lock resolves - a slow hand may never get to execute at all",
            "tutors that can find your own answer to a specific stax piece",
        ],
        "decreases_value_of": [
            "greedy multi-piece combo lines requiring many resources/turns - stax is built to strip exactly this",
            "fragile one-shot mana with no follow-up, since a stax pod often punishes over-extension",
        ],
    },
    "midrange_grind": {
        "speed": "medium",
        "primary_resource_axis": "generic average cEDH pod - some interaction, some engines, no extreme skew",
        "interaction_demand": "medium",
        "resilience_profile": "medium",
        "increases_value_of": [
            "card-advantage engines - the default baseline value driver against an unremarkable pod",
            "redundancy/resilience - a generic grindy pod rewards a hand that isn't reliant on one card",
        ],
        "decreases_value_of": [
            "nothing especially - this is the closest archetype to the solo baseline this whole project has already measured",
        ],
    },
}

# Bounded modifiers (never above +2 / below -2), applied to FEATURE_CATEGORIES present in a hand.
# Missing (archetype, category) pairs default to 0 - "no stated opinion", not a hidden negative.
POD_MODIFIERS = {
    "RogSi": {
        "free_or_cheap_interaction": 2, "any_live_interaction": 1, "raw_speed_low_curve": 2,
        "card_advantage_engine": -1, "tutor_flexibility": -1, "proactive_early_development": 1,
        "redundancy_resilience": 1,
    },
    "Kinnan": {
        "any_live_interaction": 1, "mana_resilience": 1, "proactive_early_development": 1,
        "raw_speed_low_curve": 1,
    },
    "Rog/Thras Tree Farm": {
        "proactive_early_development": 2, "card_advantage_engine": 1, "redundancy_resilience": 1,
        "raw_speed_low_curve": -1,
    },
    "Blue Farm": {
        "card_advantage_engine": 2, "mana_resilience": 1, "raw_speed_low_curve": -1,
        "free_or_cheap_interaction": -1,
    },
    "Sisay": {
        "free_or_cheap_interaction": 2, "any_live_interaction": 1, "raw_speed_low_curve": 1,
    },
    "Tayam": {
        "graveyard_interaction": 2, "redundancy_resilience": 1,
    },
    "Tivit": {
        "any_live_interaction": 1, "card_advantage_engine": 1, "raw_speed_low_curve": -1,
    },
    "Etali": {
        "proactive_early_development": 2, "raw_speed_low_curve": 1,
    },
    "stax_heavy": {
        "mana_resilience": 2, "proactive_early_development": 2, "tutor_flexibility": 1,
        "redundancy_resilience": -1,
    },
    "midrange_grind": {
        "card_advantage_engine": 1, "redundancy_resilience": 1,
    },
}

STRUCTURAL_BAND_ORDER = ["SHIP", "MARGINAL", "CONDITIONAL_KEEP", "SNAP_KEEP"]


def hand_feature_categories_present(feats):
    """Maps an opener-features dict to the small fixed FEATURE_CATEGORIES set the pod modifiers
    are defined over. Deliberately coarse - the pod layer is qualitative, not a second simulator."""
    present = set()
    if feats.get("has_any_interaction_card"):
        present.add("any_live_interaction")
    if feats.get("interaction_density_2plus") or feats.get("has_any_interaction_card"):
        present.add("free_or_cheap_interaction")  # this deck's interaction suite is majority free/cheap
    if feats.get("has_premium_one_drop_card") or feats.get("t1_accel_executable_now"):
        present.add("raw_speed_low_curve")
    if feats.get("has_any_engine_card"):
        present.add("card_advantage_engine")
    if feats.get("land_count", 0) >= 3:
        present.add("mana_resilience")
    if feats.get("has_any_engine_card") or feats.get("t1_accel_executable_now"):
        present.add("proactive_early_development")
    if feats.get("has_tutor_card"):
        present.add("tutor_flexibility")
    if feats.get("has_any_engine_card") and feats.get("accel_card_count", 0) >= 1:
        present.add("redundancy_resilience")
    return present


def pod_conditioned_grade(structural_grade, structural_reason, archetypes, feats):
    """Combines a REAL structural_hand_grade() result with the non-simulated pod overlay for one
    or more named archetypes (a "pod" is usually a mix - e.g. ["Kinnan", "RogSi", "Tayam"]).
    Returns the adjusted band, the raw numeric shift, per-archetype breakdown, and the two
    mandatory confidence labels. A SHIP can NEVER be promoted into any keep band, regardless of
    total modifier - this is enforced structurally below, not by convention."""
    present = hand_feature_categories_present(feats)
    total_shift = 0
    breakdown = {}
    for arch in archetypes:
        mods = POD_MODIFIERS.get(arch, {})
        arch_shift = sum(mods.get(cat, 0) for cat in present)
        breakdown[arch] = {
            "shift": arch_shift,
            "categories_present": sorted(present & set(mods.keys())),
        }
        total_shift += arch_shift

    band_idx = STRUCTURAL_BAND_ORDER.index(structural_grade)
    if structural_grade == "SHIP":
        adjusted_band = "SHIP"  # hard floor - pod context cannot rescue a hand with no trajectory
    else:
        # each +1/-1 of *net* modifier shifts at most one band, never crosses the SHIP floor from
        # a keep band, and never exceeds SNAP_KEEP.
        step = 1 if total_shift >= 2 else (-1 if total_shift <= -2 else 0)
        new_idx = max(1, min(len(STRUCTURAL_BAND_ORDER) - 1, band_idx + step))
        adjusted_band = STRUCTURAL_BAND_ORDER[new_idx]

    return {
        "structural_grade": structural_grade,
        "structural_reason": structural_reason,
        "structural_confidence": "SIMULATED",
        "pod_archetypes": archetypes,
        "pod_modifier_total": total_shift,
        "pod_modifier_breakdown": breakdown,
        "pod_adjusted_grade": adjusted_band,
        "pod_confidence": "STRATEGIC_PRIOR_UNVALIDATED",
    }
