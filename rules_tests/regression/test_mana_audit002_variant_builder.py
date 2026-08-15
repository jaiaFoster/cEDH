"""MANA-AUDIT-002 section F infrastructure — counterfactual deck-variant builder correctness."""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, DUAL_LAND_BASIC_TYPES, FETCH_LAND_TARGET_TYPES  # noqa: E402
from mana_audit002_variants import all_cards_dict, build_variant  # noqa: E402
from opening_hand_policy import HandState, LandInPlay  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
CARDS_POOL = all_cards_dict(CARDS)
BASE_NAMES = list(CARDS.keys())


def test_variant_add_remove_preserves_98_count():
    variant = build_variant(BASE_NAMES, CARDS_POOL, add=["Scalding Tarn"], remove=["City of Traitors"])
    assert len(variant) == 98
    assert "Scalding Tarn" in variant
    assert "City of Traitors" not in variant


def test_variant_remove_only_reduces_count():
    variant = build_variant(BASE_NAMES, CARDS_POOL, remove=["Ancient Tomb"])
    assert len(variant) == 97


def test_scalding_tarn_effective_targets_are_island_typed_duals_only():
    """This deck has zero Mountain-typed cards, so Scalding Tarn (Island-or-Mountain) can only
    ever reach the three Island-typed ABUR duals."""
    wanted = FETCH_LAND_TARGET_TYPES["Scalding Tarn"]
    targets = sorted(n for n, t in DUAL_LAND_BASIC_TYPES.items() if t & wanted)
    assert targets == ["Tropical Island", "Tundra", "Underground Sea"]


def test_rainbow_candidates_produce_any_color():
    rng = random.Random(0)
    state = HandState(["Gemstone Mine", "Tarnished Citadel", "Forbidden Orchard"], [], on_play=True, rng=rng, cards=CARDS_POOL)
    state.turn = 1
    for n in ["Gemstone Mine", "Tarnished Citadel", "Forbidden Orchard"]:
        state.lands.append(LandInPlay(n, 1, tapped=False))
    sources = {ref.name: (colors, count) for ref, colors, count in state.available_sources()}
    for n in ["Gemstone Mine", "Tarnished Citadel", "Forbidden Orchard"]:
        colors, count = sources[n]
        assert colors == {"W", "U", "B", "G"}
        assert count == 1


def test_variant_simulates_without_crashing():
    variant = build_variant(BASE_NAMES, CARDS_POOL, add=["Gemstone Mine"], remove=["Talon Gates of Madara"])
    from opening_hand_policy import develop_turn, DEFAULT_PRIORITY
    rng = random.Random(7)
    for _ in range(50):
        lib = variant[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        state = HandState(hand, library, on_play=True, rng=rng, cards=CARDS_POOL)
        for t in range(1, 4):
            develop_turn(state, CARDS_POOL, priority_order=DEFAULT_PRIORITY)
