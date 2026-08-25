"""SIM-ROGFARM-001 — regression tests for the corrected Underworld Breach + Lion's Eye Diamond +
Brain Freeze loop model (sim/analysis/rogfarm001_breach_loop.py). Validates exact deterministic
state transitions per iteration, not a prose approximation, per the assignment's explicit
correction instruction.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from rogfarm001_breach_loop import (  # noqa: E402
    BreachLoopState,
    SHELL_COST_PER_ITERATION,
    max_sustainable_opponent_target_iterations,
    mill_formula,
    min_iteration_to_mill_library,
    minimum_seed_met,
    net_delta_formula,
    run_iteration,
    simulate_loop,
)


def test_shell_cost_is_six_not_four():
    # The Stage 1 report's original "-4/loop" claim under-counted the escape-exile cost: each
    # iteration exiles 3 (LED) + 3 (Brain Freeze) = 6 cards from the "other" fuel pool, full stop,
    # before any mill is added back in.
    assert SHELL_COST_PER_ITERATION == 6


def test_minimum_seed_precondition():
    assert minimum_seed_met(BreachLoopState(other_count=6, led_in_gy=True, bf_in_gy=True, storm_count=0))
    assert not minimum_seed_met(BreachLoopState(other_count=5, led_in_gy=True, bf_in_gy=True, storm_count=0))
    assert not minimum_seed_met(BreachLoopState(other_count=100, led_in_gy=False, bf_in_gy=True, storm_count=0))
    assert not minimum_seed_met(BreachLoopState(other_count=100, led_in_gy=True, bf_in_gy=False, storm_count=0))


def test_iteration_below_seed_raises():
    state = BreachLoopState(other_count=5, led_in_gy=True, bf_in_gy=True, storm_count=0)
    with pytest.raises(ValueError):
        run_iteration(state, target_self=True)


def test_iteration_1_exact_state_self_target_k0():
    # K=0 (loop is the very first spells cast this turn), seeded with exactly 6 fuel.
    state = BreachLoopState(other_count=6, led_in_gy=True, bf_in_gy=True, storm_count=0)
    new_state, detail = run_iteration(state, target_self=True)

    # Storm: LED cast (storm 0->1), Brain Freeze cast (storm 1->2).
    assert detail["storm_before"] == 0
    assert detail["storm_after"] == 2
    # Brain Freeze cast with 1 spell (LED) already cast before it this turn -> 1 copy -> 2
    # total resolutions -> mills 3*2 = 6.
    assert detail["mill_amount"] == 6
    # Shell: 6 - 6 (both escapes) = 0; + mill 6 (self-target) = net_delta 0 -> exact breakeven.
    assert detail["other_before"] == 6
    assert detail["other_after"] == 6
    assert detail["net_delta"] == 0
    assert new_state.other_count == 6
    assert new_state.led_in_gy is True
    assert new_state.bf_in_gy is True
    assert new_state.iteration == 1


def test_iteration_2_strictly_positive_self_target_k0():
    details = simulate_loop(seed_other_count=6, k=0, iterations=2, target_self=True)
    it1, it2 = details
    assert it1["net_delta"] == 0
    # Iteration 2: spells cast before this iteration's LED = 2 (from iteration 1); before its
    # Brain Freeze = 3; resolutions = 4; mill = 12; net_delta = -6 + 12 = 6.
    assert it2["storm_before"] == 2
    assert it2["storm_after"] == 4
    assert it2["mill_amount"] == 12
    assert it2["net_delta"] == 6
    assert it2["other_after"] == 12  # 6 (after it1) + 6


def test_iteration_1_net_positive_when_k_at_least_1():
    # K=3 prior spells already cast this turn before the loop starts.
    state = BreachLoopState(other_count=6, led_in_gy=True, bf_in_gy=True, storm_count=3)
    new_state, detail = run_iteration(state, target_self=True)
    # spells before Brain Freeze = 3(K) + 1(LED) = 4; resolutions = 5; mill = 15.
    assert detail["mill_amount"] == 15
    assert detail["net_delta"] == 9  # -6 + 15 = 9 = 3*K = 3*3
    assert new_state.other_count == 15


@pytest.mark.parametrize("k,n", [(0, 1), (0, 2), (0, 5), (1, 1), (3, 4), (7, 1)])
def test_closed_form_matches_simulation_self_target(k, n):
    details = simulate_loop(seed_other_count=10_000, k=k, iterations=n, target_self=True)
    last = details[-1]
    assert last["net_delta"] == net_delta_formula(k, n, target_self=True)
    assert last["mill_amount"] == mill_formula(k, n)


def test_opponent_target_is_flat_fuel_limited_minus_six():
    details = simulate_loop(seed_other_count=100, k=0, iterations=5, target_self=False)
    for d in details:
        assert d["net_delta"] == -6
        assert d["net_delta"] == net_delta_formula(0, d["iteration"], target_self=False)
    # other_count strictly decreases by 6 each time, never refueled.
    others = [d["other_after"] for d in details]
    assert others == [94, 88, 82, 76, 70]


def test_opponent_target_eventually_exhausts_fuel():
    with pytest.raises(ValueError):
        simulate_loop(seed_other_count=6, k=0, iterations=2, target_self=False)
    # Exactly 1 iteration possible from a seed of exactly 6.
    details = simulate_loop(seed_other_count=6, k=0, iterations=1, target_self=False)
    assert details[0]["other_after"] == 0


def test_max_sustainable_opponent_target_iterations():
    assert max_sustainable_opponent_target_iterations(6) == 1
    assert max_sustainable_opponent_target_iterations(35) == 5  # floor(35/6)
    assert max_sustainable_opponent_target_iterations(5) == 0


def test_self_target_loop_is_self_sustaining_not_bounded():
    # Real infinite-combo claim: from a minimal legal seed (exactly 6, K=0), 50 iterations run
    # without ever raising (would raise on any iteration that under-flows fuel).
    details = simulate_loop(seed_other_count=6, k=0, iterations=50, target_self=True)
    assert len(details) == 50
    # Monotonically non-decreasing after the breakeven first iteration, strictly increasing
    # thereafter.
    others = [d["other_after"] for d in details]
    assert others[0] == 6
    assert all(b > a for a, b in zip(others[1:], others[2:]))
    # Final fuel pool has grown far past the seed (grows without bound, quadratically in
    # iteration count via the 6*(n-1) closed form) - not a small finite ceiling.
    cumulative = 6 + sum(net_delta_formula(0, n, target_self=True) for n in range(1, 51))
    assert others[-1] == cumulative == 7356
    assert others[-1] > 50 * SHELL_COST_PER_ITERATION


def test_min_iteration_to_mill_opponent_library():
    # library_size <= 0 -> already decked, 0 iterations needed.
    assert min_iteration_to_mill_library(k=0, library_size=0) == 0
    # mill_n = 6n at K=0; need mill_n >= 99 -> smallest n with 6n>=99 is n=17 (6*17=102).
    assert min_iteration_to_mill_library(k=0, library_size=99) == 17
    assert mill_formula(0, 17) >= 99
    assert mill_formula(0, 16) < 99


def test_r1_has_no_thassas_oracle_so_this_loop_is_its_only_deterministic_win():
    # Structural finding directly required by the assignment's Oracle-redundancy-loss metric:
    # confirm Thassa's Oracle is one of R1's explicit removed cards (see
    # build_rogfarm001_frozen_decks.py's R1 diff) - i.e. R1's only deterministic win via this
    # combo is milling the opponent's library to zero, not a self-mill-then-Oracle instant win.
    decklists = REPO_ROOT / "data" / "decklists"
    import json
    stock = json.loads((decklists / "rogsi-valley-forge-2026-v1.json").read_text())
    r1 = json.loads((decklists / "rogfarm-r1-minimal-v1.json").read_text())
    stock_names = {c["name"] for c in stock["cards"]}
    r1_names = {c["name"] for c in r1["cards"]}
    assert "Thassa's Oracle" in stock_names
    assert "Thassa's Oracle" not in r1_names
