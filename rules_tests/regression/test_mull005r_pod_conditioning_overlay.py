"""SIM-001 MULL-005R — pod-conditioning overlay (assignment section 21 / task #97).

pod_archetypes.py's own algorithm (ARCHETYPES/POD_MODIFIERS/the hard SHIP floor in
pod_conditioned_grade()) is unchanged this phase - the assignment explicitly says "preserve MULL-
005's overlay architecture... do NOT run full pod simulations this phase." What DID need auditing
is whether the overlay's REAL, simulated inputs are still correct now that the underlying
trajectory architecture has been corrected - concretely, CMDR-003 (removing Tymna/Thrasios from
the legacy ENGINES dict) affects opening_hand_metrics.snapshot_metrics's any_engine_active/
engine_count fields and opening_hand_features.py's t1-simulated engine_cast_t1, both computed from
REAL SIMULATED STATE (commanders live in a separate command_zone, never in the drawn hand/library
pool itself - see opening_hand_policy.HandState.command_zone - so the contamination vector was
specifically "a commander gets cast during simulation," not "a commander card sits in the opening
hand list").
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, Perm, LandInPlay, develop_turn  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from opening_hand_features import extract_opener_features  # noqa: E402
from trajectory_policies import structural_hand_grade  # noqa: E402
from pod_archetypes import pod_conditioned_grade, hand_feature_categories_present, ARCHETYPES, POD_MODIFIERS  # noqa: E402

FAKE_CARDS = {
    "Tropical Island": {"name": "Tropical Island", "type": "Land — Island Forest", "mana_cost": "", "cmc": 0},
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Force of Will": {"name": "Force of Will", "type": "Instant", "mana_cost": "{3}{U}{U}", "cmc": 5},
    "Mystic Remora": {"name": "Mystic Remora", "type": "Enchantment", "mana_cost": "{U}", "cmc": 1},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
    "Vanilla Creature": {"name": "Vanilla Creature", "type": "Creature — Bear", "mana_cost": "{2}{G}", "cmc": 3},
    "Lotus Petal": {"name": "Lotus Petal", "type": "Artifact", "mana_cost": "{0}", "cmc": 0},
}


def test_thrasios_cast_t1_does_not_contaminate_t1_engine_cast_feature():
    # Thrasios (GU, castable T1 with 2 blue/green sources) must not, once cast, show up in the
    # t1-simulated engine_cast_t1 set - the real vector CMDR-003 fixed (a commander getting cast
    # during the T1 simulation itself, not the opener hand list, which can never contain a
    # commander - see HandState.command_zone).
    hand = ["Tropical Island", "Lotus Petal", "Filler Land", "Filler Land", "Filler Land", "Filler Land", "Filler Land"]
    library = ["Filler Land"] * 20
    # confirm, via a real one-turn simulation, that Thrasios genuinely gets cast T1 here -
    # otherwise this test would trivially pass for the wrong reason.
    state = HandState(list(hand), list(library), on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    develop_turn(state, FAKE_CARDS)
    assert any(n == "Thrasios, Triton Hero" for (t, n, c) in state.cast_log if t == 1), state.cast_log

    feats = extract_opener_features(hand, library, True, FAKE_CARDS)
    assert feats["t1_engine_cast"] == []
    assert feats["t1_any_engine_cast"] is False
    assert feats["has_any_engine_card"] is False  # no real engine card was ever in this hand


def test_battlefield_commander_alone_does_not_set_any_engine_active():
    state = HandState(["Tropical Island"], ["Filler Land"] * 20, on_play=True,
                       rng=random.Random(0), cards=FAKE_CARDS)
    state.nonland_perms.append(Perm("Thrasios, Triton Hero", 1, is_creature=True))
    m = snapshot_metrics(state, FAKE_CARDS, [])
    assert m["any_engine_active"] is False
    assert m["engine_count"] == 0
    assert m["two_plus_engines_active"] is False


def _real_ship_hand_feats():
    # A genuinely bad hand under the real corrected engine: 1 land, no engine, no accel, no
    # tutor, no interaction - must structurally grade SHIP on its own merits, no commander
    # involvement needed to prove the floor holds.
    hand = ["Tropical Island"] + ["Vanilla Creature"] * 6
    library = ["Filler Land"] * 20
    return extract_opener_features(hand, library, True, FAKE_CARDS)


def test_ship_floor_holds_for_every_named_archetype_post_correction():
    feats = _real_ship_hand_feats()
    grade, reason = structural_hand_grade(feats)
    assert grade == "SHIP", (grade, reason)  # sanity: this really is a SHIP-graded hand
    for arch_name in ARCHETYPES:
        result = pod_conditioned_grade(grade, reason, [arch_name], feats)
        assert result["pod_adjusted_grade"] == "SHIP", (arch_name, result)
        assert result["pod_confidence"] == "STRATEGIC_PRIOR_UNVALIDATED"
        assert result["structural_confidence"] == "SIMULATED"


def test_ship_floor_holds_even_for_the_most_favorable_multi_archetype_combination():
    feats = _real_ship_hand_feats()
    grade, reason = structural_hand_grade(feats)
    assert grade == "SHIP"
    result = pod_conditioned_grade(grade, reason, list(ARCHETYPES.keys()), feats)
    assert result["pod_adjusted_grade"] == "SHIP"


def test_real_premium_engine_hand_gets_a_nonnegative_rogsi_modifier_when_free_interaction_present():
    # RogSi rewards free/cheap interaction + raw speed most heavily (worked example named in the
    # assignment) - a real T1 premium-engine + free-interaction hand should show a non-negative
    # RogSi shift and remain at its ceiling band.
    hand = ["Mystic Remora", "Force of Will", "Underground Sea", "Underground Sea", "Tropical Island"]
    library = ["Filler Land"] * 30
    feats = extract_opener_features(hand, library, True, FAKE_CARDS)
    grade, reason = structural_hand_grade(feats)
    assert grade == "SNAP_KEEP"
    result = pod_conditioned_grade(grade, reason, ["RogSi"], feats)
    assert result["pod_modifier_breakdown"]["RogSi"]["shift"] >= 0
    assert result["pod_adjusted_grade"] == "SNAP_KEEP"


def test_tayam_archetype_only_rewards_graveyard_interaction_and_redundancy_categories():
    # Tayam (graveyard recursion/aristocrats) - worked example named in the assignment - keys
    # specifically off graveyard_interaction/redundancy_resilience, not raw_speed_low_curve
    # (which RogSi rewards but Tayam deliberately does not).
    tayam_mods = POD_MODIFIERS["Tayam"]
    assert "raw_speed_low_curve" not in tayam_mods
    assert tayam_mods.get("graveyard_interaction", 0) > 0
