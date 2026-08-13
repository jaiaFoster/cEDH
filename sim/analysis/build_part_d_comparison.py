"""SIM-001 SOLO-002 PART D — mulligan policy comparison table.

Consolidates the Part C London-mulligan simulation output (results/solo_baseline/
solo002_mulligan_simulation.json) into the exact comparison requested: keep-7 rate, avg starting
hand size, T1/T2/T3 engine rate, development+interaction, commander castability, tutor access,
combo accessibility, cards remaining, failure modes - across policies A (engine-first), B
(agency-first), C (speed-first), D (tutor-inclusive). Policy E (seat-aware) is explicitly out of
scope here per the user's own note ("reserve for pod simulations").
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IN_PATH = REPO_ROOT / "results" / "solo_baseline" / "solo002r_mulligan_simulation.json"
OUT_PATH = REPO_ROOT / "results" / "solo_baseline" / "solo002r_part_d_policy_comparison.json"


def main():
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    rows = {}
    for pname, agg in data["policies"].items():
        pt = agg["overall_primary_table"]
        rows[pname] = {
            "keep_7_rate": agg["mulligan_distribution"].get("0", 0.0),
            "avg_starting_hand_size": agg["avg_starting_hand_size"],
            "expected_card_disadvantage": agg["expected_card_disadvantage"],
            "avg_cards_remaining_t3": agg["avg_cards_remaining_t3"],
            "any_engine_active": {t: pt["any_engine_active"][t] for t in ("1", "2", "3")},
            "development_plus_interaction": {t: pt["development_plus_interaction"][t] for t in ("1", "2", "3")},
            "tymna_castable_t3": pt["Tymna the Weaver_castable"]["3"],
            "tymna_supported_t3": pt["tymna_supported"]["3"],
            "thrasios_castable_t3": pt["Thrasios, Triton Hero_castable"]["3"],
            "thrasios_activation_now_t3": pt["thrasios_activation_now"]["3"],
            "tutor_available_t3": pt["tutor_available"]["3"],
            "tutor_castable_t3": pt["tutor_castable"]["3"],
            "one_action_from_verified_win_t3": pt["one_action_from_verified_win"]["3"],
            "deterministic_win_available_t3": pt["deterministic_win_available"]["3"],
            "deterministic_win_protected_t3": pt["deterministic_win_protected"]["3"],
            # secondary convenience metric only - per the redesigned success-metric instruction,
            # NOT used to rank/declare a single "best" policy; see the separate columns above.
            "secondary_meaningful_development_rate_t3": agg["overall_meaningful_development_rate_t3"],
            "top_3_failure_modes": list(agg["overall_failure_table"].items())[:3],
        }
    out = {
        "run_class": "DECK_BACKED_GOLDFISH",
        "evidence_type": "goldfish",
        "phase": "SIM_001_SOLO_002_PART_D",
        "source": str(IN_PATH.relative_to(REPO_ROOT)),
        "note": (
            "Policy E (seat-aware) is explicitly deferred to pod simulations per the user's own "
            "spec and is not compared here. Multi-objective by design: no single composite score "
            "is computed or used to declare one policy universally best - compare the separate "
            "columns per the tradeoff each represents."
        ),
        "comparison": rows,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")

    # compact printed table
    header = ["policy", "keep7%", "avg_hand", "eng_T1", "eng_T2", "eng_T3", "dev+int_T3", "tutor_cast_T3", "meaningful_T3"]
    print("\t".join(header))
    for pname, r in rows.items():
        print("\t".join([
            pname,
            f"{r['keep_7_rate']*100:.1f}",
            f"{r['avg_starting_hand_size']:.2f}",
            f"{r['any_engine_active']['1']*100:.1f}",
            f"{r['any_engine_active']['2']*100:.1f}",
            f"{r['any_engine_active']['3']*100:.1f}",
            f"{r['development_plus_interaction']['3']*100:.1f}",
            f"{r['tutor_castable_t3']*100:.1f}",
            f"{r['secondary_meaningful_development_rate_t3']*100:.1f}",
        ]))


if __name__ == "__main__":
    main()
