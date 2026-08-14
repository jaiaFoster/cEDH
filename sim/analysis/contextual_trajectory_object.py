"""SIM-001 MULL-006 section 16 — multi-dimensional trajectory object.

Assembles the full contextual trajectory object the assignment's section 16 sketches, reusing
every MULL-006 module built so far (sections 3-11) rather than recomputing anything. Per the
assignment's own permission ("Use exact project schema conventions rather than this literal
schema if necessary"), a few fields are adapted:
    - opponent_windows_before_deployment / earliest_realization / opponent_windows_before_
      realization are sourced from engine_realization_timing_model.py (the superset of
      seat_timing_model.py that also folds in the pod realization modifier).
    - contextual_trajectory_grade is a DICT keyed by valuation architecture name (see
      contextual_valuation_models.py) rather than a single value, since section 17 explicitly
      requires comparing multiple architectures rather than committing to one.
    - base_trajectory_grade falls back to the pre-existing legacy tier (grade_trajectory()'s own
      S/A/B/C/D/F) for destinations outside the strength/speed matrix's scope (Oculus, Thrasios) -
      disclosed via base_trajectory_grade_source.
"""
from opening_hand_policy import OCULUS_NAME
from engine_strength_prior import ENGINE_STRENGTH_PRIOR
from relative_speed_model import relative_speed
from strength_speed_matrix import base_trajectory_quality, grade_to_legacy_band
from draw_dependence_model import classify_trajectory_draw_dependence
from trajectory_fragility_model import assess_fragility
from pod_realization_model import pod_trigger_realization, TRACKED_POD_ENGINES
from relevant_agency_model import hand_agency_scores
from engine_realization_timing_model import realization_timing_profile

OBJECT_PROVENANCE = "MODEL_DERIVED"

DESTINATION_SUBTYPE_OVERRIDE = {
    OCULUS_NAME: "oculus",
    "Birthing Pod": "functional_pod",
    "Survival of the Fittest": "functional_survival",
    "Thrasios, Triton Hero": "commander_concrete_benefit",
}


def _destination_subtype(tier_engine):
    if tier_engine is None:
        return None
    if tier_engine in DESTINATION_SUBTYPE_OVERRIDE:
        return DESTINATION_SUBTYPE_OVERRIDE[tier_engine]
    if tier_engine in ENGINE_STRENGTH_PRIOR:
        return "resource_engine"
    return "other"


def build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=1, archetype=None):
    """Returns the full contextual trajectory object for one real simulated best trajectory
    (`grade` from trajectory_search.find_best_trajectory / grade_trajectory), or a minimal object
    with every contextual field set to None if the hand has no destination (tier D/F) - the
    assignment's own destination-first governing principle (section 12/17's gating example)."""
    tier_engine, tier_turn = grade["tier_engine"], grade["tier_turn"]

    intrinsic_strength = ENGINE_STRENGTH_PRIOR.get(tier_engine)
    speed = relative_speed(tier_engine, tier_turn) if tier_turn is not None else None
    base_grade = base_trajectory_quality(tier_engine, tier_turn) if (intrinsic_strength and speed) else None
    base_grade_source = "strength_speed_matrix" if base_grade is not None else "legacy_tier_fallback"
    if base_grade is None:
        base_grade = grade["tier"]  # already S/A/B/C/D/F - same alphabet, coarser

    timing = realization_timing_profile(tier_engine, tier_turn, seat, archetype=archetype) if tier_turn is not None else None
    draw_dep = classify_trajectory_draw_dependence(state, cards, tier_engine, tier_turn, deck_size, on_play)
    fragility = assess_fragility(state, cards, tier_engine, tier_turn, on_play)
    agency = hand_agency_scores(state, cards, archetypes=[archetype] if archetype else None)
    pod_modifier = (
        pod_trigger_realization(tier_engine, archetype)
        if (tier_engine in TRACKED_POD_ENGINES and archetype is not None) else None
    )

    worst_dependency = None
    if draw_dep and draw_dep["dependencies"]:
        worst_dependency = max(
            draw_dep["dependencies"],
            key=lambda d: {"BROAD_OUTS": 0, "NARROW_OUTS": 1, "EXACT_OR_NEAR_EXACT": 2}.get(d["classification"], 0),
        )

    return {
        "destination": tier_engine,
        "destination_subtype": _destination_subtype(tier_engine),
        "intrinsic_strength": intrinsic_strength,
        "deployment_turn": tier_turn,
        "relative_speed": speed,
        "seat": seat,
        "archetype": archetype,
        "opponent_windows_before_deployment": timing["opponent_action_windows_before_deployment"] if timing else None,
        "earliest_realization_class": timing["realization_timing_class"] if timing else None,
        "earliest_expected_realization": timing["earliest_expected_realization"] if timing else None,
        "opponent_windows_before_realization": timing["opponent_action_windows_before_first_possible_realization"] if timing else None,
        "draw_dependence_class": draw_dep["overall_classification"] if draw_dep else "NOT_APPLICABLE_NO_DESTINATION",
        "outs_count": worst_dependency["outs_count"] if worst_dependency else None,
        "probability_of_trajectory": (
            worst_dependency["probability_of_success_by_turn"] if worst_dependency
            else (1.0 if tier_engine is not None else None)
        ),
        "resources_consumed": fragility["cards_committed"] if fragility else None,
        "cards_remaining": fragility["cards_remaining"] if fragility else None,
        "persistent_mana_remaining": fragility["permanent_mana_remaining"] if fragility else None,
        "resilience_class": fragility["resilience_class"] if fragility else None,
        "recovery_trajectory": (
            fragility["second_best_destination_realized"] or fragility["weak_in_hand_fallback"] or "NONE"
        ) if fragility else None,
        "live_agency": agency["live_agency_score"],
        "relevant_agency": agency["relevant_agency_score"].get(archetype) if archetype else agency["relevant_agency_score"],
        "pod_realization_modifier": pod_modifier,
        "verified_combo_proximity": grade["resource_cost"]["engine_plus_verified_combo_proximity"],
        "base_trajectory_grade": base_grade,
        "base_trajectory_grade_source": base_grade_source,
        "legacy_tier": grade["tier"],
        "contextual_trajectory_grade": {},  # filled in by contextual_valuation_models.py
    }
