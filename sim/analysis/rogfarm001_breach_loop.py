"""SIM-ROGFARM-001 — exact deterministic state model for the Underworld Breach + Lion's Eye
Diamond + Brain Freeze loop.

Corrects the Stage 1 report's original "net -4 graveyard cards per loop, hard fuel-limited" claim,
which omitted Brain Freeze's own self-mill entirely. Oracle text verified via WebSearch this task
(all three cards, each an independent query, 2026-08-25):

  Underworld Breach {1}{R} Enchantment — "Each nonland card in your graveyard has escape. The
  escape cost is equal to the card's mana cost plus exile three other cards from your graveyard.
  ... At the beginning of the end step, sacrifice this enchantment." Escaping a card pays its full
  mana cost AND exiles 3 other graveyard cards (the exile is additive, not a replacement for the
  mana cost).

  Lion's Eye Diamond {0} Artifact — "Discard your hand, Sacrifice Lion's Eye Diamond: Add three
  mana of any one color. Activate only any time you could cast an instant." Not a spell cast (an
  activated ability) — does not add to storm count. LED goes to the graveyard when sacrificed (no
  replacement effect redirects it to exile).

  Brain Freeze {1}{U} Instant — "Target player mills three cards. Storm." Storm copies resolve in
  addition to the original (total resolutions = spells cast before Brain Freeze this turn, + 1).
  Each resolution (original and every copy) mills 3 cards from its own target — copies may choose
  new targets. The original Brain Freeze card then goes to the caster's graveyard normally (it is
  not exiled — Breach's exile-instead-of-graveyard clause applies only to Breach's OWN sacrifice
  trigger, not to spells cast via escape).

One iteration of the loop (assuming LED and Brain Freeze are both already in the graveyard and
Breach is already resolved on the battlefield):
  1. Escape-cast LED: pay {0}, exile 3 OTHER graveyard cards. LED leaves the graveyard (cast as a
     spell -> storm count += 1) and resolves to the battlefield.
  2. Activate LED: discard hand (empty, mid-storm-turn) + sacrifice LED -> add 3 mana of one
     color. LED returns to the graveyard (sacrificed permanents go to the graveyard; not a spell
     cast, storm count unaffected).
  3. Escape-cast Brain Freeze: pay {1}{U} (using LED's 3 mana), exile 3 OTHER graveyard cards
     (drawn from the general "other" pool, never LED itself, so LED stays available next
     iteration). Storm count += 1.
  4. Brain Freeze resolves (original + copies = storm-count-before-this-cast + 1 total
     resolutions), each resolution mills 3 cards from its target. Original Brain Freeze card then
     returns to the graveyard.

Per-iteration graveyard "shell" cost (before counting the mill): -3 (LED escape) - 3 (Brain Freeze
escape) + 1 (LED returns) + 1 (Brain Freeze returns) = -4 net LED/BF-only movement, but the fuel
pool ("other" cards) specifically loses 6 (both escapes draw from it) and gains 0 back from LED/BF
themselves (they aren't "other" cards, they're tracked separately) — so other_count drops by
exactly 6 per iteration before any mill is added back in.

If Brain Freeze targets the CASTER (self), its mill refuels the caster's own "other" pool. If it
targets an OPPONENT, no refuel occurs and the pool is strictly fuel-limited.

Closed form (K = spells already cast this turn before the loop starts, n = iteration number
counting from 1, storm counted as "spells cast so far this turn"):
  spells cast before this iteration's Brain Freeze = K + 2*(n-1) + 1  (the K prior spells, the
    2*(n-1) LED+BrainFreeze pairs from earlier iterations, plus this iteration's own LED cast)
  mill_n = 3 * (K + 2*(n-1) + 1 + 1) = 3K + 6n              [self-target mode]
  net_delta_n (self-target)   = -6 + mill_n = 3K + 6*(n-1)
  net_delta_n (opponent-target) = -6                         [flat, no refuel, fuel-limited]

At K=0, self-target: iteration 1 is an EXACT breakeven (net_delta_1 = 0), iteration 2 onward is
strictly positive and grows without bound -> the loop is self-sustaining/effectively infinite once
minimally seeded, matching community consensus (commanderspellbook.com / edh-combos.com list this
as an infinite mill / infinite storm combo, not a bounded value engine).
"""
from dataclasses import dataclass, replace


LED_ESCAPE_EXILE = 3
BRAIN_FREEZE_ESCAPE_EXILE = 3
SHELL_COST_PER_ITERATION = LED_ESCAPE_EXILE + BRAIN_FREEZE_ESCAPE_EXILE  # 6, before any mill


@dataclass(frozen=True)
class BreachLoopState:
    """other_count: graveyard cards available as escape-exile fuel (excludes LED and Brain Freeze
    themselves, which are tracked by their own booleans). storm_count: spells cast so far this
    turn (running total, includes everything cast before the loop started)."""
    other_count: int
    led_in_gy: bool
    bf_in_gy: bool
    storm_count: int
    iteration: int = 0


def minimum_seed_met(state: BreachLoopState) -> bool:
    """Hard precondition for even attempting iteration 1: LED and Brain Freeze both already in
    the graveyard, and enough 'other' fuel for both escapes sequentially (3 + 3 = 6, drawn from
    the same pool one exile-event at a time)."""
    return state.led_in_gy and state.bf_in_gy and state.other_count >= SHELL_COST_PER_ITERATION


def run_iteration(state: BreachLoopState, target_self: bool):
    """Executes exactly one iteration (escape LED -> sac for mana -> escape Brain Freeze -> mill).
    Raises ValueError if the minimum-seed precondition isn't met (mirrors the real game: you can't
    exile 3 cards you don't have, or escape a card that isn't in the graveyard). Returns
    (new_state, detail_dict)."""
    if not minimum_seed_met(state):
        raise ValueError(
            f"cannot run iteration {state.iteration + 1}: minimum seed not met "
            f"(led_in_gy={state.led_in_gy}, bf_in_gy={state.bf_in_gy}, "
            f"other_count={state.other_count}, need >= {SHELL_COST_PER_ITERATION})"
        )

    # Step 1: escape-cast LED (spell cast, storm += 1; exile 3 other; LED leaves graveyard).
    storm = state.storm_count + 1
    other = state.other_count - LED_ESCAPE_EXILE
    led_in_gy = False

    # Step 2: activate LED (not a spell cast, storm unaffected); LED returns to graveyard.
    led_in_gy = True

    # Step 3: escape-cast Brain Freeze (spell cast, storm += 1; exile 3 other; BF leaves gy).
    spells_cast_before_brain_freeze = storm  # storm count immediately before this cast
    storm += 1
    other -= BRAIN_FREEZE_ESCAPE_EXILE
    bf_in_gy = False

    # Step 4: Brain Freeze resolves (original + copies = spells_cast_before + 1 resolutions),
    # each mills 3 cards from its target. Original card returns to the graveyard afterward.
    resolutions = spells_cast_before_brain_freeze + 1
    mill_amount = 3 * resolutions
    bf_in_gy = True
    if target_self:
        other += mill_amount

    new_state = BreachLoopState(
        other_count=other, led_in_gy=led_in_gy, bf_in_gy=bf_in_gy,
        storm_count=storm, iteration=state.iteration + 1,
    )
    net_delta = new_state.other_count - state.other_count
    detail = {
        "iteration": new_state.iteration,
        "target_self": target_self,
        "mill_amount": mill_amount,
        "other_before": state.other_count,
        "other_after": new_state.other_count,
        "net_delta": net_delta,
        "storm_before": state.storm_count,
        "storm_after": new_state.storm_count,
    }
    return new_state, detail


def net_delta_formula(k: int, n: int, target_self: bool) -> int:
    """Closed-form net_delta for iteration n (1-indexed), given K prior spells cast this turn
    before the loop began. Matches run_iteration()'s actual per-iteration net_delta exactly."""
    if not target_self:
        return -SHELL_COST_PER_ITERATION
    return 3 * k + 6 * (n - 1)


def mill_formula(k: int, n: int) -> int:
    """Closed-form Brain Freeze mill amount on iteration n (whichever player is targeted)."""
    return 3 * k + 6 * n


def simulate_loop(seed_other_count: int, k: int, iterations: int, target_self: bool):
    """Runs `iterations` iterations from a fresh seed (LED and Brain Freeze already in the
    graveyard, storm_count starting at k). Returns the list of per-iteration detail dicts. Raises
    ValueError (propagated from run_iteration) the moment fuel runs out — this is itself a
    meaningful result for the opponent-target/fuel-limited case."""
    state = BreachLoopState(
        other_count=seed_other_count, led_in_gy=True, bf_in_gy=True, storm_count=k,
    )
    details = []
    for _ in range(iterations):
        state, detail = run_iteration(state, target_self=target_self)
        details.append(detail)
    return details


def max_sustainable_opponent_target_iterations(seed_other_count: int) -> int:
    """Opponent-target mode is flat -6/iteration with no refuel: the number of iterations
    achievable before fuel is exhausted is purely seed_other_count // 6 (integer floor, since each
    iteration needs a full 6 fuel up front)."""
    return seed_other_count // SHELL_COST_PER_ITERATION


def min_iteration_to_mill_library(k: int, library_size: int) -> int:
    """Smallest n such that a SINGLE Brain Freeze cast on iteration n (redirected at an opponent
    that iteration only) mills their entire library. This is the realistic kill line: self-target
    to build storm for n-1 iterations (free, self-sustaining once minimum_seed_met), then redirect
    the nth Brain Freeze at the opponent."""
    if library_size <= 0:
        return 0
    n = 1
    while mill_formula(k, n) < library_size:
        n += 1
    return n
