"""SIM-001 MULL-006 section 9 — pod-trigger realization, new dimension #4.

Several tracked engines require OPPONENT behavior to generate value:
    Rhystic Study, Mystic Remora, Esper Sentinel, Faerie Mastermind,
    Archivist of Oghma, Heartwood Storyteller, Runic Armasaur, Smothering Tithe

Per the assignment, MULL-006 is NOT authorized to fabricate exact multiplayer trigger rates - no
real 4-player simulation exists in this project. This module instead builds a QUALITATIVE/ORDINAL
realization model (VERY_HIGH/HIGH/MODERATE/LOW/UNKNOWN per engine x archetype), reusing the
existing metagame archetype work (pod_archetypes.py's ARCHETYPES, built for MULL-005's pod-
conditioning overlay) rather than inventing a new taxonomy. This module does NOT modify
pod_archetypes.py or engine_strength_prior.py - it is a separate, additive POD REALIZATION
MODIFIER layer, exactly as the assignment instructs: "Keep engine intrinsic strength separate from
expected realization in this pod. Do not rewrite the engine ranking itself every time the pod
changes."

EVERY value produced by this module is STRATEGIC_PRIOR_UNVALIDATED and stays that way until real
multiplayer simulation/tournament calibration exists - never cite this as measured.

METHOD (disclosed, rule-based, not "just vibes" - derived FROM pod_archetypes.py's existing
per-archetype qualitative descriptions, so it is reproducible and testable even though its INPUTS
are still strategic priors, not measurements):

1. Each archetype gets a hand-authored behavior-density PROFILE across the assignment's own listed
   opponent-behavior axes (noncreature spell density, tutor/library-search density, creature
   density, second-card-draw density, ability to pay taxes), each LOW(0)/MODERATE(1)/HIGH(2),
   derived from that archetype's existing primary_resource_axis/interaction_demand/speed fields in
   pod_archetypes.ARCHETYPES. Smothering Tithe gets its own land_drop_reliability axis (land drops
   are near-universal every turn, so this starts near-HIGH for every archetype, with only stax_
   heavy pods deviating - some stax pods deliberately slow down their own land drops).

2. Each of the 8 opponent-triggered engines is mapped to the ONE driver dimension its real Oracle
   trigger condition actually depends on:
       Rhystic Study, Mystic Remora, Esper Sentinel -> noncreature_spell_density
           (all three trigger on an opponent casting a spell - Sentinel specifically noncreature)
       Faerie Mastermind -> second_draw_density (triggers on an opponent's SECOND card draw a
           turn - a narrower, specific trigger than "casts a spell")
       Archivist of Oghma -> tutor_search_density (triggers on library searches)
       Heartwood Storyteller -> noncreature_spell_density (single-target spell triggers, treated
           as a subset of general noncreature spell behavior - this project's established, less
           mechanically-precise characterization of Heartwood, per prior MULL-005R/006 work)
       Runic Armasaur -> creature_density (triggers on an opponent's creature entering)
       Smothering Tithe -> land_drop_reliability (triggers on an opponent playing a land)

3. Rhystic Study, Mystic Remora, Esper Sentinel, and Smothering Tithe all have a real "unless that
   player pays {N}" clause - a HIGH tax_payment_ability archetype denies realization even when the
   driver dimension itself is high (they simply pay through it), so these four get an additional
   tax_payment_ability PENALTY subtracted from the driver score. Faerie Mastermind, Archivist of
   Oghma, Heartwood Storyteller, and Runic Armasaur have no such clause and are not penalized.

4. final_score = driver_dimension_value - (tax_payment_ability_value - 1 if tax-gated else 0),
   clipped and mapped: <=0 LOW, 1 MODERATE, 2 HIGH, >=3 VERY_HIGH. UNKNOWN is returned only when
   the engine or archetype is outside this module's known set (never fabricated for a known pair).
"""
from pod_archetypes import ARCHETYPES

POD_REALIZATION_PROVENANCE = "STRATEGIC_PRIOR_UNVALIDATED"

TRACKED_POD_ENGINES = {
    "Rhystic Study", "Mystic Remora", "Esper Sentinel", "Faerie Mastermind",
    "Archivist of Oghma", "Heartwood Storyteller", "Runic Armasaur", "Smothering Tithe",
}
TAX_GATED_ENGINES = {"Rhystic Study", "Mystic Remora", "Esper Sentinel", "Smothering Tithe"}

ENGINE_DRIVER_DIMENSION = {
    "Rhystic Study": "noncreature_spell_density",
    "Mystic Remora": "noncreature_spell_density",
    "Esper Sentinel": "noncreature_spell_density",
    "Faerie Mastermind": "second_draw_density",
    "Archivist of Oghma": "tutor_search_density",
    "Heartwood Storyteller": "noncreature_spell_density",
    "Runic Armasaur": "creature_density",
    "Smothering Tithe": "land_drop_reliability",
}
assert set(ENGINE_DRIVER_DIMENSION) == TRACKED_POD_ENGINES

DENSITY_LABEL = {0: "LOW", 1: "MODERATE", 2: "HIGH"}

# Hand-authored, derived from each archetype's EXISTING pod_archetypes.ARCHETYPES description
# (primary_resource_axis / interaction_demand / speed) - see module docstring for the reasoning
# behind each column. Every archetype name here must already exist in pod_archetypes.ARCHETYPES.
ARCHETYPE_BEHAVIOR_PROFILE = {
    "RogSi":                {"noncreature_spell_density": 2, "tutor_search_density": 2, "creature_density": 0, "second_draw_density": 0, "tax_payment_ability": 0, "land_drop_reliability": 2},
    "Kinnan":                {"noncreature_spell_density": 1, "tutor_search_density": 1, "creature_density": 2, "second_draw_density": 0, "tax_payment_ability": 2, "land_drop_reliability": 2},
    "Rog/Thras Tree Farm":   {"noncreature_spell_density": 1, "tutor_search_density": 1, "creature_density": 2, "second_draw_density": 1, "tax_payment_ability": 1, "land_drop_reliability": 2},
    "Blue Farm":             {"noncreature_spell_density": 2, "tutor_search_density": 1, "creature_density": 0, "second_draw_density": 2, "tax_payment_ability": 2, "land_drop_reliability": 2},
    "Sisay":                 {"noncreature_spell_density": 1, "tutor_search_density": 2, "creature_density": 1, "second_draw_density": 0, "tax_payment_ability": 1, "land_drop_reliability": 2},
    "Tayam":                 {"noncreature_spell_density": 1, "tutor_search_density": 0, "creature_density": 2, "second_draw_density": 1, "tax_payment_ability": 1, "land_drop_reliability": 2},
    "Tivit":                 {"noncreature_spell_density": 2, "tutor_search_density": 1, "creature_density": 1, "second_draw_density": 1, "tax_payment_ability": 2, "land_drop_reliability": 2},
    "Etali":                 {"noncreature_spell_density": 1, "tutor_search_density": 0, "creature_density": 1, "second_draw_density": 0, "tax_payment_ability": 2, "land_drop_reliability": 2},
    "stax_heavy":            {"noncreature_spell_density": 2, "tutor_search_density": 1, "creature_density": 0, "second_draw_density": 0, "tax_payment_ability": 0, "land_drop_reliability": 1},
    "midrange_grind":        {"noncreature_spell_density": 1, "tutor_search_density": 1, "creature_density": 1, "second_draw_density": 1, "tax_payment_ability": 1, "land_drop_reliability": 2},
}
assert set(ARCHETYPE_BEHAVIOR_PROFILE) == set(ARCHETYPES)

REALIZATION_ORDER = ["VERY_HIGH", "HIGH", "MODERATE", "LOW", "UNKNOWN"]
REALIZATION_RANK = {label: i for i, label in enumerate(REALIZATION_ORDER)}


def pod_trigger_realization(engine_name, archetype):
    """Returns the VERY_HIGH/HIGH/MODERATE/LOW/UNKNOWN realization label for `engine_name` against
    `archetype`, or UNKNOWN if either is outside this module's known set. STRATEGIC_PRIOR_
    UNVALIDATED - never cite as a measured trigger frequency."""
    driver = ENGINE_DRIVER_DIMENSION.get(engine_name)
    profile = ARCHETYPE_BEHAVIOR_PROFILE.get(archetype)
    if driver is None or profile is None:
        return "UNKNOWN"
    score = profile[driver]
    if engine_name in TAX_GATED_ENGINES:
        score -= (profile["tax_payment_ability"] - 1)
    if score <= 0:
        return "LOW"
    if score == 1:
        return "MODERATE"
    if score == 2:
        return "HIGH"
    return "VERY_HIGH"


def full_realization_table():
    """Every (engine, archetype) pair's realization label - the required engine x archetype
    matrix (assignment section 9's 'for each engine x archetype/pod classify...')."""
    return {
        engine: {arch: pod_trigger_realization(engine, arch) for arch in ARCHETYPE_BEHAVIOR_PROFILE}
        for engine in ENGINE_DRIVER_DIMENSION
    }
