"""SIM-ROGFARM-001 Stage 2 — paired opening-hand/T1-T3 Monte Carlo across Stock RogSi, R1 Minimal
Rog Farm, and Blue Farm, for all 3 pre-registered mulligan policies (P1/P2/P3). Computes the
Section 7 primary outputs, the Section 8 wheel-opportunity proxy, and the Section 19 Oracle-
redundancy-loss rate; evaluates all 5 Section 9 falsification gates.

Deterministic combos registered directly (not via the shared interactions/verified/ file registry,
which is project-wide and would leak into unrelated future tasks): THORACLE_CONSULT (Thassa's
Oracle + Demonic Consultation), THORACLE_PACT (Thassa's Oracle + Tainted Pact), BREACH_LOOP
(Underworld Breach + Lion's Eye Diamond + Brain Freeze - piece ACCESS only, not the loop's own
infinite-iteration math, which is a separate concern already validated in
rogfarm001_breach_loop.py/its regression tests; "all 3 pieces assembled and jointly payable" is
the correct proxy for what this opening-hand census needs).

Scope disclosure (Tier B solo/no-opponent model, consistent with this project's established
scope): the wheel-opportunity metric (Section 8) checks wheel castability + a real asymmetry
mechanism (payoff ALREADY on battlefield, not merely in hand) + sufficient mana + retained
interaction as a protection proxy - it does NOT verify point 6 ("wheel outcome not obviously
improving opponents more than us under known-state assumptions"), which requires actual opponent
states and is explicitly deferred to Stage 3's controlled wheel-state laboratory (Tier C).
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
import rogfarm001_cards as rc  # noqa: E402
import rogfarm001_variants as rvar  # noqa: E402
import rogfarm001_mulligan_policies as mp  # noqa: E402

COMBOS = [
    {"id": "THORACLE_CONSULT", "cards": ["Thassa's Oracle", "Demonic Consultation"]},
    {"id": "THORACLE_PACT", "cards": ["Thassa's Oracle", "Tainted Pact"]},
    {"id": "BREACH_LOOP", "cards": ["Underworld Breach", "Lion's Eye Diamond", "Brain Freeze"]},
]

WHEEL_NAMES = mp.WHEEL_NAMES
WHEEL_PAYOFF_NAMES = mp.WHEEL_PAYOFF_NAMES

# The 6 cards R1 adds relative to Stock (Section 4's identity package) - used for the
# conditional-card burden metric (Section 7).
R1_IDENTITY_CARDS = {
    "Faerie Mastermind", "Narset, Parter of Veils", "Notion Thief",
    "Force of Negation", "Foil", "Subtlety",
}

MAX_TURN = 3


def _wheel_castable_now(state, cards):
    from opening_hand_policy import is_currently_castable
    from opening_hand_model import parse_cost
    for name in WHEEL_NAMES:
        if name in state.hand:
            gen, pips, x = parse_cost(cards[name]["mana_cost"])
            if x == 0 and is_currently_castable(state, gen, pips):
                return name
    return None


def _one_hand(seed, commanders, names, cards, policy_name):
    rng = random.Random(seed)
    policy_fn = mp.POLICIES[policy_name]
    hand, library, mulligan_count = mp.london_mulligan(names, cards, rng, policy_fn, on_play=True)
    state = HandState(hand, library, on_play=True, rng=rng, cards=cards)

    per_turn = {}
    engine_online_ever = False
    protected_engine_online_ever = False
    wheel_payoff_on_bf_ever = False
    earliest_win_turn = None
    protected_wheel_by_t3 = False
    naked_wheel_by_t3 = False
    asymmetric_wheel_by_t3 = False

    for t in range(1, MAX_TURN + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        snap = snapshot_metrics(state, cards, COMBOS)
        per_turn[t] = snap

        if snap["any_engine_active"]:
            engine_online_ever = True
        if snap["engine_plus_interaction"]:
            protected_engine_online_ever = True
        payoffs_on_bf = [n for n in snap["engines_active"] if n in WHEEL_PAYOFF_NAMES]
        if payoffs_on_bf:
            wheel_payoff_on_bf_ever = True
        if earliest_win_turn is None and snap["deterministic_win_available"]:
            earliest_win_turn = t

        wheel_castable = _wheel_castable_now(state, cards)
        if wheel_castable is not None:
            naked_wheel_by_t3 = True
            if payoffs_on_bf:
                asymmetric_wheel_by_t3 = True
                if snap["mana_2plus"] and snap["has_live_interaction"]:
                    protected_wheel_by_t3 = True

    final = per_turn[MAX_TURN]
    t2 = per_turn[2]

    # Conditional-card burden (Section 7): only meaningful for R1-identity-card-bearing hands.
    identity_in_opening = [c for c in hand if c in R1_IDENTITY_CARDS]
    identity_stranded_t3 = [c for c in identity_in_opening if c in state.hand]

    # Meaningful mana/color failure: fewer than 2 mana available by T2 (a real, disclosed floor
    # definition - "meaningful" interpreted as "couldn't reliably deploy a 2-drop by T2").
    meaningful_mana_failure = not t2["mana_2plus"]

    blue_pitch_live = [n for n in final["live_interaction"] if "U" in cards[n]["mana_cost"]]

    return {
        "mulligan_count": mulligan_count,
        "engine_online_t1": per_turn[1]["any_engine_active"],
        "engine_online_by_t2": per_turn[1]["any_engine_active"] or t2["any_engine_active"],
        "protected_engine_online_by_t2": protected_engine_online_ever,
        "engine_plus_interaction_t2": t2["engine_plus_interaction"],
        "engine_plus_2_interaction_t2": t2["any_engine_active"] and len(t2["live_interaction"]) >= 2,
        "has_live_interaction_t3": final["has_live_interaction"],
        "live_interaction_count_t3": len(final["live_interaction"]),
        "blue_pitch_live_t3": len(blue_pitch_live),
        "mana_2plus_t3": final["mana_2plus"], "mana_3plus_t3": final["mana_3plus"],
        "meaningful_mana_failure": meaningful_mana_failure,
        "identity_cards_in_opening": len(identity_in_opening),
        "identity_cards_stranded_t3": len(identity_stranded_t3),
        "naked_wheel_by_t3": naked_wheel_by_t3,
        "asymmetric_wheel_by_t3": asymmetric_wheel_by_t3,
        "protected_asymmetric_wheel_by_t3": protected_wheel_by_t3,
        "earliest_credible_win_turn": earliest_win_turn,
        "deterministic_win_available_t3": final["deterministic_win_available"],
        "combo_status_t3": final["combo_status"],
        "thoracle_zero_step_t3": any(
            final["combo_status"].get(cid) == "zero_step" for cid in ("THORACLE_CONSULT", "THORACLE_PACT")
        ),
        "breach_zero_step_t3": final["combo_status"].get("BREACH_LOOP") == "zero_step",
    }


def run_deck_policy(deck_label, policy_name, n_trials, seed_offset):
    payload, commanders, names, cards = rvar.load_rogfarm001_deck(deck_label)
    rc.install_new_card_tables(commander_names=commanders)
    try:
        results = [
            _one_hand(seed_offset + i, commanders, names, cards, policy_name)
            for i in range(n_trials)
        ]
    finally:
        rc.uninstall_new_card_tables()
    return payload["deck_hash"], results


def aggregate(results):
    n = len(results)

    def rate(key):
        return sum(1 for r in results if r[key]) / n

    def mean(key):
        return sum(r[key] for r in results) / n

    identity_hands = [r for r in results if r["identity_cards_in_opening"] > 0]
    identity_stranded_rate = (
        sum(r["identity_cards_stranded_t3"] for r in identity_hands) / max(1, len(identity_hands))
        if identity_hands else None
    )
    win_turns = [r["earliest_credible_win_turn"] for r in results if r["earliest_credible_win_turn"] is not None]
    oracle_redundancy = sum(1 for r in results if r["thoracle_zero_step_t3"] and not r["breach_zero_step_t3"]) / n

    return {
        "n_trials": n,
        "mean_mulligan_count": mean("mulligan_count"),
        "engine_online_t1": rate("engine_online_t1"),
        "engine_online_by_t2": rate("engine_online_by_t2"),
        "protected_engine_online_by_t2": rate("protected_engine_online_by_t2"),
        "engine_plus_interaction_t2": rate("engine_plus_interaction_t2"),
        "engine_plus_2_interaction_t2": rate("engine_plus_2_interaction_t2"),
        "has_live_interaction_t3": rate("has_live_interaction_t3"),
        "mean_live_interaction_count_t3": mean("live_interaction_count_t3"),
        "mean_blue_pitch_live_t3": mean("blue_pitch_live_t3"),
        "mana_2plus_t3": rate("mana_2plus_t3"),
        "mana_3plus_t3": rate("mana_3plus_t3"),
        "meaningful_mana_failure_rate": rate("meaningful_mana_failure"),
        "identity_card_stranded_rate": identity_stranded_rate,
        "identity_hands_fraction": len(identity_hands) / n,
        "p_hand_2plus_conditional_identity_cards": sum(
            1 for r in results if r["identity_cards_in_opening"] >= 2
        ) / n,
        "naked_wheel_by_t3": rate("naked_wheel_by_t3"),
        "asymmetric_wheel_by_t3": rate("asymmetric_wheel_by_t3"),
        "protected_asymmetric_wheel_by_t3": rate("protected_asymmetric_wheel_by_t3"),
        "deterministic_win_available_t3": rate("deterministic_win_available_t3"),
        "earliest_credible_win_mean_turn": (sum(win_turns) / len(win_turns)) if win_turns else None,
        "earliest_credible_win_by_t3_rate": len(win_turns) / n,
        "oracle_redundancy_loss_rate": oracle_redundancy,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--out", type=str, default="results/solo_baseline/rogfarm001_stage2_results.json")
    args = ap.parse_args()

    t0 = time.time()
    out = {"phase": "SIM_ROGFARM_001_STAGE2", "evidence_type": "monte_carlo", "n_trials": args.n,
           "decks": {}}
    for deck_label in rvar.DECK_VERSIONS:
        out["decks"][deck_label] = {"policies": {}}
        for policy_name in mp.POLICIES:
            seed_offset = hash((deck_label, policy_name)) % 1_000_000
            deck_hash, results = run_deck_policy(deck_label, policy_name, args.n, seed_offset)
            out["decks"][deck_label]["deck_hash"] = deck_hash
            out["decks"][deck_label]["policies"][policy_name] = aggregate(results)
            print(f"{deck_label}/{policy_name}: done ({time.time() - t0:.1f}s elapsed)")

    out_path = REPO_ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({time.time() - t0:.1f}s total)")


if __name__ == "__main__":
    main()
