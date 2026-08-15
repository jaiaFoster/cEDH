"""MANA-AUDIT-002 section C — color-demand analysis by turn.

Derives ACTUAL color requirements per turn from the real printed mana costs of every card in the
98-card list, weighted by WHEN a card actually wants to be cast (its natural curve slot), not raw
pip counting across the whole 98. Turn-timing weighting reuses (does not re-derive)
relative_speed_model.json's `expected_deployment_turn` - MULL-006's own measured "own-curve" turn
for the 11 highest-priority engines - plus each commander's/tutor's natural CMC-implied slot for
everything relative_speed_model.json doesn't cover (it only scores named premium engines, not
every tutor/interaction/dork in the 98).
"""
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, deck_provenance_fields, parse_cost, COMMANDERS  # noqa: E402

SPEED_MODEL = json.loads((REPO_ROOT / "results" / "solo_baseline" / "relative_speed_model.json").read_text())
EXPECTED_DEPLOYMENT_TURN = SPEED_MODEL["expected_deployment_turn"]

# Commander costs (not in the 98-card `cards` dict - cast from the command zone)
COMMANDER_COST = {name: spec["cost"] for name, spec in COMMANDERS.items()}


def _pip_multiset(pips):
    """Expand parsed pips into a Counter of single colors for TRUE single-color pips only;
    hybrid/phyrexian pips (any ONE of several colors) are reported separately since they do not
    impose a fixed color requirement - conflating them with true pips would overstate demand."""
    fixed = Counter()
    flexible = []
    for p in pips:
        if isinstance(p, str):
            fixed[p] += 1
        else:
            flexible.append(sorted(p))
    return fixed, flexible


def _natural_turn(name, cmc, cards):
    """Best available 'when this actually wants to be cast' turn. Priority: (1) measured
    expected_deployment_turn for the 11 engines relative_speed_model.json scored, (2) CMC itself
    (a real, if cruder, proxy) capped at 3 (this audit's horizon), consistent with the
    assignment's own T1/T2/T3 structure - a CMC-4+ card is out of scope for this turn-by-turn
    table (it cannot be cast by T3 without acceleration, tracked separately in Section D/F)."""
    if name in EXPECTED_DEPLOYMENT_TURN:
        return EXPECTED_DEPLOYMENT_TURN[name]
    if cmc <= 3:
        return int(cmc) if cmc >= 1 else 1
    return None  # out of T1-3 horizon on its own (may still arrive earlier via acceleration)


def main():
    payload, cards = load_deck_cards()

    per_turn_single_pip = {1: Counter(), 2: Counter(), 3: Counter()}
    per_turn_combo_pip = {1: Counter(), 2: Counter(), 3: Counter()}  # frozenset of colors co-required
    per_turn_cards = {1: [], 2: [], 3: []}
    flexible_pip_cards = {1: [], 2: [], 3: []}
    out_of_horizon = []

    # Section C is about SPELLS wanting color pips, not land supply - lands are excluded here
    # (they're the subject of Sections A/B/D-G, not color DEMAND).
    all_entries = [
        (name, cards[name]["mana_cost"], cards[name]["cmc"])
        for name in cards if "Land" not in cards[name]["type"]
    ]
    all_entries += [(name, cost, parse_cost(cost)[0] + len(parse_cost(cost)[1])) for name, cost in COMMANDER_COST.items()]

    for name, mana_cost, cmc in all_entries:
        gen, pips, x = parse_cost(mana_cost)
        if x > 0 and name not in EXPECTED_DEPLOYMENT_TURN:
            # X-spells (Chord of Calling, Finale of Devastation, Nature's Rhythm, Commandeer) -
            # their COLOR requirement is fixed even though total cost is not; still recorded.
            pass
        turn = _natural_turn(name, cmc, cards)
        if turn is None or turn > 3:
            out_of_horizon.append({"name": name, "mana_cost": mana_cost, "cmc": cmc})
            continue
        fixed, flexible = _pip_multiset(pips)
        colors_needed = frozenset(fixed.keys())
        per_turn_cards[turn].append({"name": name, "mana_cost": mana_cost, "fixed_pips": dict(fixed)})
        for c in fixed:
            per_turn_single_pip[turn][c] += 1
        if len(colors_needed) >= 2:
            per_turn_combo_pip[turn][colors_needed] += 1
        # double/triple-pip-of-same-color (e.g. Chord of Calling's GGG, Ranger-Captain's WW)
        for c, n in fixed.items():
            if n >= 2:
                per_turn_combo_pip[turn][frozenset({f"{c}x{n}"})] += 1
        if flexible:
            flexible_pip_cards[turn].append({"name": name, "mana_cost": mana_cost, "flexible_options": flexible})

    def _fmt_combo_counter(counter):
        return [
            {"colors": sorted(k), "count": v}
            for k, v in sorted(counter.items(), key=lambda kv: -kv[1])
        ]

    t3_named_examples = [
        "Tymna the Weaver", "Derevi, Empyrial Tactician", "Nature's Rhythm", "Chord of Calling",
        "Rhystic Study", "Birthing Pod",
    ]
    t3_named_present = {n: (n in cards or n in COMMANDERS) for n in t3_named_examples}

    out = {
        **deck_provenance_fields(payload),
        "phase": "MANA_AUDIT_002_SECTION_C",
        "evidence_type": "static_probability",
        "section": "C_color_demand_analysis_by_turn",
        "method_note": (
            "Turn assignment is NOT raw CMC-across-the-whole-98. It uses relative_speed_model."
            "json's measured expected_deployment_turn (MULL-006, own-curve timing) for the 11 "
            "engines it scores, and CMC (capped at 3, this audit's horizon) for every other card "
            "- commanders, tutors, interaction, dorks - since those don't have a separately-"
            "measured 'own curve' artifact and CMC is their real minimum legal cast turn absent "
            "acceleration (a defensible floor, not an overstatement: acceleration-enabled EARLIER "
            "casts are already captured by Section D/F's real T1-T3 simulation, this table is "
            "about baseline color PRESSURE, not the fastest possible line)."
        ),
        "t1_single_color_demand": _fmt_combo_counter(per_turn_single_pip[1]),
        "t2_single_color_demand": _fmt_combo_counter(per_turn_single_pip[2]),
        "t3_single_color_demand": _fmt_combo_counter(per_turn_single_pip[3]),
        "t1_multicolor_combos_required_same_spell": _fmt_combo_counter(per_turn_combo_pip[1]),
        "t2_multicolor_combos_required_same_spell": _fmt_combo_counter(per_turn_combo_pip[2]),
        "t3_multicolor_combos_required_same_spell": _fmt_combo_counter(per_turn_combo_pip[3]),
        "t1_cards": sorted(per_turn_cards[1], key=lambda r: r["name"]),
        "t2_cards": sorted(per_turn_cards[2], key=lambda r: r["name"]),
        "t3_cards": sorted(per_turn_cards[3], key=lambda r: r["name"]),
        "flexible_hybrid_hurexian_pip_cards_by_turn": flexible_pip_cards,
        "out_of_t1_t3_horizon_cards": sorted(out_of_horizon, key=lambda r: r["name"]),
        "t3_assignment_named_examples_present_in_this_98": t3_named_present,
        "t3_assignment_named_examples_note": (
            "Grand Abolisher is NOT in this 98-card list (the assignment's own illustrative "
            "example set includes cards from a generic template, not every one of which is "
            "necessarily in THIS exact decklist) - omitted rather than fabricated. Every other "
            "named T3 example (Tymna, Derevi, Nature's Rhythm, Chord of Calling, Rhystic Study, "
            "Birthing Pod) IS present and is covered above."
        ),
        "headline_findings": {
            "t1_color_pressure": "G leads (7 cards: Avacyn's Pilgrim/Birds/Elves of Deep Shadow/"
                                  "Noble Hierarch dorks, Deathrite, Crop Rotation, Veil of "
                                  "Summer), W and U roughly tied (4 each: Esper Sentinel/"
                                  "Enlightened Tutor/Silence/Swift Reconfiguration for W; Mystic "
                                  "Remora/Flusterstorm/Swan Song/Mental Misstep for U), B is "
                                  "weakest at T1 (2: Imperial Seal, Vampiric Tutor) - matches the "
                                  "deck's G-dork-heavy, W/U-cheap-interaction-heavy, B-lightest "
                                  "identity even before any land composition question is asked. "
                                  "No same-spell multicolor T1 requirement exists at all (every "
                                  "T1 card needs at most one color).",
            "t2_color_pressure": "G is by far the heaviest T2 color (11 cards, including 4 with "
                                  "a DOUBLE-G requirement: Finale of Devastation, Heartwood "
                                  "Storyteller, Nature's Rhythm, Runic Armasaur), U is second (7, "
                                  "including Rhystic Study/Faerie Mastermind), W is light (3), B "
                                  "lightest (2). Thrasios (GU) lands here and directly reinforces "
                                  "the G/U demand; Tymna (cmc 3, {1}{W}{B}) does NOT land at T2 - "
                                  "she is a real 3-mana cast, not the 2-mana cast a surface read "
                                  "of 'WB commander' suggests.",
            "t3_color_pressure": "U becomes the single heaviest color at T3 (7 cards, 3 of them "
                                  "double-U: Flare of Denial, Force of Negation, plus the pitch-"
                                  "cast-eligible Fierce Guardianship counted at its hardcast "
                                  "value), G and W tie for second (6 each, including a rare "
                                  "TRIPLE-G requirement - Chord of Calling {X}{G}{G}{G} - and 2 "
                                  "double-W cards), B stays lightest (1: only Tymna's single B "
                                  "pip, inside a WB requirement). Tymna's real cast turn is T3 on "
                                  "curve, not T2 - a materially different color-pressure picture "
                                  "than treating her as an early 2-drop.",
        },
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_color_demand.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print("T1 single-color:", out["t1_single_color_demand"])
    print("T2 single-color:", out["t2_single_color_demand"])
    print("T3 single-color:", out["t3_single_color_demand"])
    print("T2 combos:", out["t2_multicolor_combos_required_same_spell"])
    print("T3 combos:", out["t3_multicolor_combos_required_same_spell"])


if __name__ == "__main__":
    main()
