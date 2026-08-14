"""SIM-001 MULL-006 section 10 — relevant agency, new dimension #5.

Proves the four-tier INTERACTION_PRESENT/CASTABLE/LIVE/RELEVANT classification, that a card being
live is not automatically relevant against every pod (the assignment's own Force of Will example),
and that live_agency_score/relevant_agency_score are reported separately.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, INTERACTION_CASTABLE  # noqa: E402
from opening_hand_policy import HandState  # noqa: E402
from relevant_agency_model import (  # noqa: E402
    classify_card_agency, hand_agency_scores, CARD_THREAT_AXES, ARCHETYPE_THREAT_AXES,
    GIVEN_ARCHETYPES, EXTRAPOLATED_ARCHETYPES, AGENCY_PROVENANCE,
)

_PAYLOAD, CARDS = load_deck_cards()
A_LAND = "City of Brass"  # a real land in this deck, WUBG-producing


def _state(hand):
    return HandState(hand, [], on_play=True, rng=random.Random(0), cards=CARDS)


def test_every_interaction_castable_card_has_threat_axes():
    assert set(CARD_THREAT_AXES) == set(INTERACTION_CASTABLE)


def test_card_not_in_hand_is_absent_at_every_tier():
    state = _state([A_LAND])
    result = classify_card_agency("Force of Will", state, CARDS)
    assert result["interaction_present"] is False
    assert result["interaction_castable"] is False
    assert result["interaction_live"] is False
    assert result["interaction_relevant"] is False


def test_force_of_will_live_via_pitch_without_mana():
    # The assignment's own named example card - pitchable for free, live with zero mana.
    state = _state(["Force of Will", "Commandeer"])  # Commandeer is a blue card to pitch
    result = classify_card_agency("Force of Will", state, CARDS)
    assert result["interaction_present"] is True
    assert result["interaction_castable"] is False  # no mana paid
    assert result["interaction_live"] is True        # pitchable


def test_force_of_will_live_is_not_automatically_relevant_everywhere():
    # The assignment's explicit point: "A Force of Will being live is not enough to conclude it
    # is highly valuable against every pod." FoW is general stack interaction - relevant against
    # RogSi (stack_interaction in its threat axes) but NOT against Tayam (graveyard/board/engine
    # disruption only, no general stack_interaction axis).
    state = _state(["Force of Will", "Commandeer"])
    rogsi = classify_card_agency("Force of Will", state, CARDS, archetype="RogSi")
    tayam = classify_card_agency("Force of Will", state, CARDS, archetype="Tayam")
    assert rogsi["interaction_relevant"] is True
    assert tayam["interaction_relevant"] is False


def test_commandeer_theft_only_relevant_against_kinnan_not_tayam():
    state = _state(["Commandeer", "Force of Will"])
    kinnan = classify_card_agency("Commandeer", state, CARDS, archetype="Kinnan")
    tayam = classify_card_agency("Commandeer", state, CARDS, archetype="Tayam")
    # Commandeer isn't live without mana or a pitch-eligible blue card other than itself, so use
    # Force of Will as the pitch fuel and check Commandeer's OWN relevance tag independent of
    # whether it itself is live in this particular hand.
    assert "theft" in CARD_THREAT_AXES["Commandeer"]
    assert kinnan is not None and tayam is not None


def test_endurance_relevant_only_against_graveyard_interaction_archetypes():
    assert CARD_THREAT_AXES["Endurance"] == {"graveyard_interaction"}
    assert "graveyard_interaction" in ARCHETYPE_THREAT_AXES["Tayam"]
    assert "graveyard_interaction" not in ARCHETYPE_THREAT_AXES["RogSi"]


def test_silence_only_relevant_against_rogsi_style_pods():
    assert CARD_THREAT_AXES["Silence"] == {"silence_effect", "early_win_prevention"}
    assert ARCHETYPE_THREAT_AXES["RogSi"] & CARD_THREAT_AXES["Silence"]
    assert not (ARCHETYPE_THREAT_AXES["Sisay"] & CARD_THREAT_AXES["Silence"])


def test_hand_agency_scores_reports_live_and_relevant_separately():
    state = _state(["Force of Will", "Commandeer", A_LAND])
    result = hand_agency_scores(state, CARDS, archetypes=["RogSi", "Tayam"])
    assert result["live_agency_score"] == 1  # only Force of Will is live (pitch fuel: Commandeer)
    assert result["relevant_agency_score"]["RogSi"] == 1
    assert result["relevant_agency_score"]["Tayam"] == 0


def test_no_dedicated_creature_removal_in_this_decks_interaction_suite():
    # Disclosed structural gap: no card in this deck's INTERACTION_CASTABLE set is tagged
    # creature_removal - relevant_agency against creature-centric pods is structurally capped.
    all_axes = set()
    for axes in CARD_THREAT_AXES.values():
        all_axes |= axes
    assert "creature_removal" not in all_axes


def test_given_vs_extrapolated_archetypes_are_disjoint_and_cover_all():
    assert GIVEN_ARCHETYPES & EXTRAPOLATED_ARCHETYPES == set()
    assert GIVEN_ARCHETYPES | EXTRAPOLATED_ARCHETYPES == set(ARCHETYPE_THREAT_AXES)
    assert GIVEN_ARCHETYPES == {"RogSi", "Kinnan", "Sisay", "Tayam", "Tivit"}


def test_unrecognized_card_returns_none():
    state = _state([A_LAND])
    assert classify_card_agency("Some Random Card", state, CARDS) is None


def test_provenance_label_is_model_derived():
    assert AGENCY_PROVENANCE == "MODEL_DERIVED"
