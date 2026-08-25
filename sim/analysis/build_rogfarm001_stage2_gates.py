"""SIM-ROGFARM-001 Stage 2 — evaluates the 5 Section 9 falsification gates from
results/solo_baseline/rogfarm001_stage2_results.json, per policy, plus an aggregate PASS/FAIL
decision. Exact thresholds from the assignment's own Section 9 text (recovered verbatim from the
pre-compaction transcript, not reconstructed from memory):

  Engine advantage: PASS if (protected engine by T2 >= Blue Farm +7pp) OR (engine by T2 >=
    Blue Farm +10pp while interaction readiness is not meaningfully worse).
  RogSi defensive retention: interaction readiness against canonical T2 pressure - no worse than
    Stock RogSi by >5pp.
  Conditional burden: identity stranded-card rate - no worse than Stock RogSi by >4pp.
  Mana: kept-hand meaningful mana/color failure <5%, and no worse than Stock by >3pp.
  Wheel emergence: protected asymmetric-wheel opportunity by T3 >= 12% of kept hands.

Stop rule: if R1 clearly fails two or more of these five gates, STOP with
ROG_FARM_FALSIFIED_OR_REDESIGN.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

RESULTS_PATH = REPO_ROOT / "results" / "solo_baseline" / "rogfarm001_stage2_results.json"

# "Not meaningfully worse" (gate 1's interaction-readiness qualifier) operationalized as: R1's
# has_live_interaction_t3 rate is not more than 5pp below Blue Farm's - the SAME threshold gate 2
# uses for "no worse than Stock by >5pp," applied symmetrically since the assignment gives no
# separate numeric threshold for this specific qualifier.
NOT_MEANINGFULLY_WORSE_PP = 5.0


def pp(x):
    return x * 100.0


def evaluate_gates(deck_results, policy_name):
    r1 = deck_results["R1_ROG_FARM"]["policies"][policy_name]
    stock = deck_results["STOCK_ROGSI"]["policies"][policy_name]
    blue = deck_results["BLUE_FARM"]["policies"][policy_name]

    gates = {}

    # Gate 1: engine advantage
    protected_delta = pp(r1["protected_engine_online_by_t2"] - blue["protected_engine_online_by_t2"])
    engine_delta = pp(r1["engine_online_by_t2"] - blue["engine_online_by_t2"])
    interaction_delta_vs_blue = pp(r1["has_live_interaction_t3"] - blue["has_live_interaction_t3"])
    not_meaningfully_worse = interaction_delta_vs_blue >= -NOT_MEANINGFULLY_WORSE_PP
    path_a = protected_delta >= 7.0
    path_b = (engine_delta >= 10.0) and not_meaningfully_worse
    gates["engine_advantage"] = {
        "pass": path_a or path_b,
        "protected_engine_by_t2_delta_pp": round(protected_delta, 2),
        "engine_by_t2_delta_pp": round(engine_delta, 2),
        "interaction_delta_vs_blue_pp": round(interaction_delta_vs_blue, 2),
        "path_a_protected_engine_ge_7pp": path_a,
        "path_b_engine_ge_10pp_and_interaction_not_worse": path_b,
    }

    # Gate 2: RogSi defensive retention
    retention_delta = pp(r1["has_live_interaction_t3"] - stock["has_live_interaction_t3"])
    gates["rogsi_defensive_retention"] = {
        "pass": retention_delta >= -5.0,
        "interaction_delta_vs_stock_pp": round(retention_delta, 2),
        "threshold_pp": -5.0,
    }

    # Gate 3: conditional burden. Stock has (by construction) ~0 R1-identity-card hands, so its
    # own stranded rate is undefined/None - the comparison baseline is 0 (Stock structurally
    # cannot strand cards it doesn't run), disclosed rather than silently defaulted.
    stock_stranded = stock["identity_card_stranded_rate"] or 0.0
    r1_stranded = r1["identity_card_stranded_rate"] or 0.0
    burden_delta = pp(r1_stranded - stock_stranded)
    gates["conditional_burden"] = {
        "pass": burden_delta <= 4.0,
        "identity_stranded_rate_delta_pp": round(burden_delta, 2),
        "stock_baseline_note": "Stock runs none of R1's 6 identity cards - baseline is structurally 0, not measured.",
        "threshold_pp": 4.0,
    }

    # Gate 4: mana
    mana_fail_r1 = pp(r1["meaningful_mana_failure_rate"])
    mana_fail_stock = pp(stock["meaningful_mana_failure_rate"])
    mana_delta = mana_fail_r1 - mana_fail_stock
    gates["mana"] = {
        "pass": (mana_fail_r1 < 5.0) and (mana_delta <= 3.0),
        "r1_meaningful_mana_failure_pct": round(mana_fail_r1, 2),
        "stock_meaningful_mana_failure_pct": round(mana_fail_stock, 2),
        "delta_pp": round(mana_delta, 2),
    }

    # Gate 5: wheel emergence
    wheel_pct = pp(r1["protected_asymmetric_wheel_by_t3"])
    gates["wheel_emergence"] = {
        "pass": wheel_pct >= 12.0,
        "protected_asymmetric_wheel_by_t3_pct": round(wheel_pct, 2),
        "threshold_pct": 12.0,
    }

    fail_count = sum(1 for g in gates.values() if not g["pass"])
    return {
        "policy": policy_name, "gates": gates, "fail_count": fail_count,
        "stop_rule_triggered": fail_count >= 2,
    }


def main():
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    decks = results["decks"]
    out = {"phase": "SIM_ROGFARM_001_STAGE2_GATES", "n_trials": results["n_trials"], "by_policy": {}}
    for policy_name in ("P1_ENGINE_FORWARD", "P2_BALANCED", "P3_TURBO_RESPECTFUL"):
        out["by_policy"][policy_name] = evaluate_gates(decks, policy_name)

    fail_counts = [out["by_policy"][p]["fail_count"] for p in out["by_policy"]]
    stop_in_all = all(out["by_policy"][p]["stop_rule_triggered"] for p in out["by_policy"])
    stop_in_any = any(out["by_policy"][p]["stop_rule_triggered"] for p in out["by_policy"])
    primary = out["by_policy"]["P2_BALANCED"]
    out["primary_policy"] = "P2_BALANCED"
    out["primary_decision"] = "ROG_FARM_FALSIFIED_OR_REDESIGN" if primary["stop_rule_triggered"] else "ADVANCE"
    out["stop_rule_triggered_all_policies"] = stop_in_all
    out["stop_rule_triggered_any_policy"] = stop_in_any
    out["fail_counts_by_policy"] = dict(zip(out["by_policy"].keys(), fail_counts))

    out_path = REPO_ROOT / "results" / "solo_baseline" / "rogfarm001_stage2_gates.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps({"primary_decision": out["primary_decision"], "fail_counts": out["fail_counts_by_policy"]}, indent=2))


if __name__ == "__main__":
    main()
