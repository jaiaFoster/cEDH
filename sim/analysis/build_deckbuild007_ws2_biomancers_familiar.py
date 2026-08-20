"""SIM-DECKBUILD-007 Workstream 2 — Biomancer's Familiar vs the practical value Training Grounds
would provide.

Both cards share IDENTICAL text for the reduction itself ("Activated abilities of creatures you
control cost {2} less to activate. This effect can't reduce the mana in that cost to less than one
mana." - web-verified for both). The reduction is a static ability, live the turn each enters (NOT
gated by summoning sickness - sickness only restricts a permanent's OWN {T}/attack abilities, never
a static ability it grants to others). Only GENERIC mana in a cost is reduced (also web-verified
for Training Grounds; assumed identical, standard rule, for Familiar's near-identical wording).

Real structural difference: Familiar is a 2-mana CREATURE (dies to removal/wraths, is a real body
for Pod/Cradle/Chord/Finale, is itself accessible via creature tutors, competes for a creature
slot/curve turn) vs Training Grounds is a LAND (survives creature removal, adds a mana source of
its own, costs a land slot instead, cannot itself be found by a creature tutor).

Relevant creature-activated abilities in the current 101 with a real mana component (a non-mana
cost like Devoted Druid's counter-based untap is NOT reduced by either card - "activated abilities
... cost {2} less" only touches the MANA portion of a cost):
  Thrasios, Triton Hero - this project's own modeled proxy cost is a flat {4} (see
    opening_hand_metrics.THRASIOS_ACTIVATION_COST - an existing, disclosed simplification of the
    real X-cost ability, unchanged here, just fed through the same reduction math).
  Kinnan, Bonder Prodigy - real {5}{G}{U} creature-tutor-into-play activation.
  Oboro Breezecaller - real {2}, return-a-land: untap-target-land activation.
  Faerie Mastermind - real {3}{U}: each player draws a card.

Method: deterministic arithmetic (not Monte Carlo) - a pure function of (cost, total mana
available, colors available), swept across realistic T3-T6 mana totals. No sampling noise to
report; the table itself IS the exact answer for any given resource level.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import deck_provenance_fields, parse_cost  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards  # noqa: E402

ABILITIES = {
    "Thrasios, Triton Hero (modeled proxy)": "{4}",
    "Kinnan, Bonder Prodigy": "{5}{G}{U}",
    "Oboro Breezecaller": "{2}",
    "Faerie Mastermind": "{3}{U}",
}


def _reduce_generic(cost_str, reduction=2):
    """Real rule: reduce GENERIC mana only, floor the TOTAL cost (generic+pips) at 1 mana overall."""
    gen, pips, x = parse_cost(cost_str)
    total_mv = gen + len(pips)
    new_total = max(len(pips) if len(pips) > 0 else 1, total_mv - reduction)
    new_gen = max(0, new_total - len(pips))
    return new_gen, pips


def _affordable(gen, pips, total_mana, colors_available):
    for pip in pips:
        need = pip if isinstance(pip, frozenset) else {pip}
        if not (need & colors_available):
            return False
    return (gen + len(pips)) <= total_mana


def main():
    payload, _ = load_deckbuild007_cards()
    out = {
        **deck_provenance_fields(payload),
        "phase": "SIM_DECKBUILD_007_WS2_BIOMANCERS_FAMILIAR", "evidence_type": "static_probability",
        "method_note": "Deterministic arithmetic sweep, not Monte Carlo - see module docstring.",
        "reduction_table_by_mana_total": {},
    }
    representative_colors = {"G", "U", "B", "W"}  # this deck's real primary colors, generously assumed available
    for total_mana in range(2, 9):
        row = {}
        for name, cost_str in ABILITIES.items():
            gen0, pips0, _ = parse_cost(cost_str)
            afford_without = _affordable(gen0, pips0, total_mana, representative_colors)
            gen1, pips1 = _reduce_generic(cost_str)
            afford_with = _affordable(gen1, pips1, total_mana, representative_colors)
            row[name] = {
                "cost_without_familiar": cost_str,
                "cost_with_familiar_or_training_grounds": f"{{{gen1}}}" + "".join(f"{{{p}}}" for p in pips1),
                "affordable_without": afford_without,
                "affordable_with": afford_with,
                "unlocked_by_reduction": (not afford_without) and afford_with,
            }
        out["reduction_table_by_mana_total"][str(total_mana)] = row

    # Summary: at what total-mana level does the reduction FIRST unlock each ability.
    first_unlock = {}
    for name in ABILITIES:
        for total_mana in range(2, 9):
            if out["reduction_table_by_mana_total"][str(total_mana)][name]["unlocked_by_reduction"]:
                first_unlock[name] = total_mana
                break
        else:
            first_unlock[name] = None
    out["required_summary"] = {
        "mana_total_where_reduction_first_matters": first_unlock,
        "structural_note": (
            "Familiar and Training Grounds are FUNCTIONALLY IDENTICAL for this reduction "
            "(same text, same floor) - the real decision is the creature-vs-land delivery "
            "vehicle tradeoff (see module docstring), not different mana math."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild007_ws2_biomancers_familiar.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_summary"], indent=2))


if __name__ == "__main__":
    main()
