"""SIM-001 MULL-006 section 11 — engine realization timing, expanding MULL-005R's realization work.

Proves the earliest-POSSIBLE-vs-earliest-EXPECTED distinction, the named examples (Mastermind,
Archivist, Sylvan Library, Heartwood/Armasaur), that the pod realization modifier never applies to
non-opponent-dependent engines (Sylvan Library, Pod/Survival), and the new pitch/free-interaction
enablement field.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from engine_realization_timing_model import (  # noqa: E402
    realization_timing_profile, EXPECTED_REALIZATION_BY_MODIFIER, FREE_INTERACTION_CARDS,
    REALIZATION_TIMING_PROVENANCE,
)


def test_unrecognized_engine_returns_none():
    assert realization_timing_profile("Abhorrent Oculus", 1, 1) is None
    assert realization_timing_profile("Some Random Card", 1, 1) is None


def test_faerie_mastermind_generates_on_opponent_turns():
    result = realization_timing_profile("Faerie Mastermind", 1, 1, archetype="RogSi")
    assert result["realization_timing_class"] == "IMMEDIATE_OPPONENT_TURN"
    assert result["value_generated_before_our_next_turn"] is True
    assert result["value_enters_hand_immediately_on_realization"] is True


def test_archivist_generates_during_opponent_searches():
    result = realization_timing_profile("Archivist of Oghma", 1, 1, archetype="Sisay")
    assert result["realization_timing_class"] == "IMMEDIATE_OPPONENT_TURN"
    assert result["value_enters_hand_immediately_on_realization"] is True
    assert result["pod_realization_modifier"] == "HIGH"  # Sisay is tutor-search-dense


def test_sylvan_library_delayed_to_own_draw_step_and_pod_modifier_not_applicable():
    result = realization_timing_profile("Sylvan Library", 2, 1, archetype="RogSi")
    assert result["realization_timing_class"] == "OWN_NEXT_DRAW_STEP"
    assert result["value_generated_before_our_next_turn"] is False
    assert result["pod_realization_modifier"] == "NOT_APPLICABLE_NOT_OPPONENT_DEPENDENT"
    assert result["earliest_expected_realization"] == "SAME_AS_EARLIEST_POSSIBLE_NOT_OPPONENT_DEPENDENT"


def test_heartwood_and_armasaur_depend_strongly_on_pod_behavior():
    heartwood_high = realization_timing_profile("Heartwood Storyteller", 2, 1, archetype="RogSi")
    heartwood_low = realization_timing_profile("Heartwood Storyteller", 2, 1, archetype="Kinnan")
    assert heartwood_high["pod_realization_modifier"] != heartwood_low["pod_realization_modifier"]
    armasaur_high = realization_timing_profile("Runic Armasaur", 2, 1, archetype="Kinnan")
    armasaur_low = realization_timing_profile("Runic Armasaur", 2, 1, archetype="RogSi")
    assert armasaur_high["pod_realization_modifier"] != armasaur_low["pod_realization_modifier"]


def test_pod_dependent_engine_without_archetype_requires_archetype_to_estimate():
    result = realization_timing_profile("Rhystic Study", 1, 1)  # no archetype given
    assert result["pod_realization_modifier"] is None
    assert result["earliest_expected_realization"] == "REQUIRES_ARCHETYPE_TO_ESTIMATE"


def test_own_turn_dependent_engines_pod_modifier_never_applies():
    for name in ("Birthing Pod", "Survival of the Fittest"):
        result = realization_timing_profile(name, 1, 1, archetype="RogSi")
        assert result["pod_realization_modifier"] == "NOT_APPLICABLE_NOT_OPPONENT_DEPENDENT"


def test_every_pod_realization_modifier_label_maps_to_an_expected_label():
    for modifier in ("VERY_HIGH", "HIGH", "MODERATE", "LOW", "UNKNOWN"):
        assert modifier in EXPECTED_REALIZATION_BY_MODIFIER


def test_pitch_interaction_enablement_only_flagged_for_card_draw_engines():
    remora = realization_timing_profile("Mystic Remora", 1, 1, archetype="RogSi")
    assert remora["value_enters_hand_immediately_on_realization"] is True
    assert remora["newly_drawn_card_could_enable_immediate_pitch_interaction"] == "POSSIBLE_CONTENTS_UNKNOWN"
    assert set(remora["free_interaction_cards_this_deck_could_draw_into"]) == set(FREE_INTERACTION_CARDS)

    tithe = realization_timing_profile("Smothering Tithe", 1, 1, archetype="RogSi")
    assert tithe["value_enters_hand_immediately_on_realization"] is False
    assert tithe["newly_drawn_card_could_enable_immediate_pitch_interaction"] == "NOT_APPLICABLE_NOT_A_CARD_DRAW_TRIGGER"
    assert tithe["free_interaction_cards_this_deck_could_draw_into"] == []


def test_free_interaction_cards_are_a_nonempty_real_subset():
    assert len(FREE_INTERACTION_CARDS) > 0
    assert "Force of Will" in FREE_INTERACTION_CARDS


def test_provenance_label_is_model_derived():
    assert REALIZATION_TIMING_PROVENANCE == "MODEL_DERIVED"
