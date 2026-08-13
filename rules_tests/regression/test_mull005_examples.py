"""SIM-001 MULL-005 — annotated example generator sanity checks."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from generate_mull005_examples import collect_examples, build_pod_examples  # noqa: E402
from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402


def test_collect_examples_finds_all_target_counts_within_reasonable_draws():
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()
    target = {"SNAP_KEEP": 3, "CONDITIONAL_KEEP": 3, "SHIP": 3, "MISLEADING": 2}
    buckets, misleading = collect_examples(cards, combos, on_play=True, seed=1, target_counts=target, max_draws=20000)
    assert len(buckets["SNAP_KEEP"]) == 3
    assert len(buckets["CONDITIONAL_KEEP"]) == 3
    assert len(buckets["SHIP"]) == 3
    assert len(misleading) == 2


def test_misleading_hands_are_genuine_disagreements_confirmed_by_trajectory_search():
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()
    target = {"SNAP_KEEP": 1, "CONDITIONAL_KEEP": 1, "SHIP": 1, "MISLEADING": 3}
    _, misleading = collect_examples(cards, combos, on_play=True, seed=1, target_counts=target, max_draws=20000)
    for ex in misleading:
        assert ex["solo004_simple_rules_keep"] != ex["trajectory_simple_keep"]
        best_tier = ex["trajectory_best_tier"]
        if ex["trajectory_simple_keep"]:
            assert best_tier in ("S", "A", "B"), ex
        else:
            assert best_tier in ("D", "F"), ex


def test_pod_examples_respect_ship_floor():
    payload, cards = load_deck_cards()
    combos = load_deterministic_combos()
    target = {"SNAP_KEEP": 2, "CONDITIONAL_KEEP": 2, "SHIP": 2, "MISLEADING": 0}
    buckets, _ = collect_examples(cards, combos, on_play=True, seed=1, target_counts=target, max_draws=20000)
    pod_examples = build_pod_examples(buckets, cards)
    assert len(pod_examples) >= 6
    for ex in pod_examples:
        if ex["structural_grade"] == "SHIP":
            assert ex["pod_adjusted_grade"] == "SHIP"
        assert ex["structural_confidence"] == "SIMULATED"
        assert ex["pod_confidence"] == "STRATEGIC_PRIOR_UNVALIDATED"
