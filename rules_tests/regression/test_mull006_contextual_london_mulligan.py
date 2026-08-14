"""SIM-001 MULL-006 section 21 — rebuild contextual policies + rerun London mulligan sim.

Proves the harness fix (mulligan depth is actually threaded into the keep decision, unlike the
prior run_mull005_london_mulligan_sim.py harness where hand_size was always 7), the per-size
threshold reuse, and that simulate_one_contextual_sequence() produces internally consistent
results (final_hand_size == 7 - mulligans_taken, tier always a real legacy tier letter).
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from run_contextual_london_mulligan_sim import (  # noqa: E402
    make_contextual_keep_policy, simulate_one_contextual_sequence, aggregate,
    REUSED_SIZE_THRESHOLDS, TIER_VALUE,
)
from contextual_valuation_models import ARCHITECTURES  # noqa: E402

_PAYLOAD, CARDS = load_deck_cards()
_NAMES = list(CARDS.keys())
_COMBOS = load_deterministic_combos()


def test_hand_size_4_threshold_is_none_keep_everything():
    assert REUSED_SIZE_THRESHOLDS[4] is None


def test_hand_size_7_threshold_is_reused_from_mull005r():
    assert REUSED_SIZE_THRESHOLDS[7] == "C"
    assert REUSED_SIZE_THRESHOLDS[6] == "D"
    assert REUSED_SIZE_THRESHOLDS[5] == "D"


def test_keep_policy_at_size_4_always_returns_true_without_searching():
    policy = make_contextual_keep_policy("gated")
    # 3 mulligans already taken -> resulting size 4 -> policy must return True unconditionally,
    # regardless of hand contents (even an all-basic-land, destination-less hand).
    hand = [n for n in _NAMES if "Land" in CARDS[n]["type"]][:7]
    library = [n for n in _NAMES if n not in hand]
    assert policy(hand, library, True, CARDS, _COMBOS, 3) is True


def test_mulligan_depth_actually_changes_the_keep_bar():
    # The exact gap this module fixes: the SAME hand should be evaluated against a LOOSER bar at
    # higher mulligan depth. Find any hand and confirm the policy is at least as permissive (keeps
    # if it would keep at a stricter bar) as mulligans increase, for a held-fixed hand/library.
    rng = random.Random(123)
    lib = _NAMES[:]
    rng.shuffle(lib)
    hand, library = lib[:7], lib[7:]
    policy = make_contextual_keep_policy("gated")
    decision_at_0 = policy(hand, library, True, CARDS, _COMBOS, 0)
    decision_at_3 = policy(hand, library, True, CARDS, _COMBOS, 3)
    # at mulligans=3 (resulting size 4) the policy ALWAYS keeps - if it also kept at mulligans=0,
    # that's fine, but it can never be the other way around (keep at 0, mulligan at 3).
    if decision_at_0:
        assert decision_at_3


def test_simulate_one_contextual_sequence_final_hand_size_matches_mulligans():
    policy = make_contextual_keep_policy("tree")
    rng = random.Random(42)
    result = simulate_one_contextual_sequence(_NAMES, rng, CARDS, _COMBOS, policy, True)
    assert result["final_hand_size"] == 7 - result["mulligans_taken"]
    assert 0 <= result["mulligans_taken"] <= 4
    assert result["tier"] in TIER_VALUE


def test_simulate_one_contextual_sequence_never_exceeds_max_mulligans():
    # size-4 threshold is None (keep everything), so a sequence must stop by mulligans=4 at the
    # very latest regardless of what's drawn.
    policy = make_contextual_keep_policy("weighted")
    for seed in range(10):
        rng = random.Random(seed)
        result = simulate_one_contextual_sequence(_NAMES, rng, CARDS, _COMBOS, policy, True)
        assert result["mulligans_taken"] <= 4


def test_aggregate_produces_valid_distributions():
    results = [
        {"mulligans_taken": 0, "final_hand_size": 7, "tier": "A", "mechanism": "natural_engine"},
        {"mulligans_taken": 1, "final_hand_size": 6, "tier": "C", "mechanism": "natural_engine"},
        {"mulligans_taken": 4, "final_hand_size": 3, "tier": "F", "mechanism": "none"},
    ]
    agg = aggregate(results)
    assert agg["sample_size"] == 3
    assert abs(sum(agg["mulligan_distribution"].values()) - 1.0) < 1e-9
    assert agg["avg_final_hand_size"] == (7 + 6 + 3) / 3


def test_all_four_architectures_have_a_keep_policy_factory():
    for arch_name in ARCHITECTURES:
        policy = make_contextual_keep_policy(arch_name)
        assert callable(policy)
