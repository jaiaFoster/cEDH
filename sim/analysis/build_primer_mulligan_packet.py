"""SIM-001 MULL-006 section 24 / 28 — primer_mulligan_packet_v4.md.

Generates the assignment's required primer example packet (10 snap keeps / 10 normal keeps / 10
conditional keeps / 10 mulligans / 10 deceptive hands, 16 fields each) from REAL simulated hands,
reusing every MULL-006 module built this phase. "Deceptive hands" are split into two sub-types:
TRAP (looks resource-rich - many cards/live interaction remaining - but grades D/F) and HIDDEN_GEM
(looks thin - few cards remaining - but still grades S+/S/A+/A), matching the assignment's own
framing of a primer teaching pilots to distrust surface impressions.

Also includes a short "similar hands, one variable changed" appendix, reusing task #120's real
disagreement examples (contextual_disagreement_examples.json) rather than re-deriving them.
"""
import json
import random
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, print_run_banner
from trajectory_search import _candidate_configs, _simulate, _better
from trajectory_grading import grade_trajectory
from contextual_trajectory_object import build_trajectory_object
from contextual_valuation_models import gated_model
from strength_speed_matrix import GRADE_RANK

REPO_ROOT = Path(__file__).resolve().parents[2]

CATEGORY_ARCHETYPE_CYCLE = ["RogSi", "Kinnan", "Tayam", "Blue Farm", "midrange_grind"]
CATEGORY_SEAT_CYCLE = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2]


def _find_best_trajectory_with_state(hand, library, on_play, cards, combos):
    state, m1, m2, m3 = _simulate(hand, library, on_play, cards, combos)
    best_grade = grade_trajectory(state, cards, m1, m2, m3)
    best_state = state
    for label, kwargs in _candidate_configs(hand, library, cards):
        state_t, m1_t, m2_t, m3_t = _simulate(hand, library, on_play, cards, combos, **kwargs)
        grade_t = grade_trajectory(state_t, cards, m1_t, m2_t, m3_t)
        if _better(grade_t, best_grade):
            best_grade, best_state = grade_t, state_t
    return best_state, best_grade


def _category_of(obj, cg):
    rank = GRADE_RANK[cg]
    if cg in ("S+", "S", "A+") and obj["resilience_class"] in ("ROBUST", "RECOVERABLE") and obj["draw_dependence_class"] in ("SELF_CONTAINED", "BROAD_OUTS"):
        return "SNAP_KEEP"
    if cg in ("A", "B+", "B"):
        return "NORMAL_KEEP"
    if cg == "C":
        return "CONDITIONAL_KEEP"
    if cg in ("D", "F"):
        if obj["cards_remaining"] is not None and obj["cards_remaining"] >= 5 or (obj["live_agency"] or 0) >= 2:
            return "MULLIGAN_TRAP_DECEPTIVE"
        return "MULLIGAN"
    return None


def _why(obj, cg, category):
    dest = obj["destination"] or "no destination"
    if category in ("SNAP_KEEP",):
        return (
            f"{dest} at T{obj['deployment_turn']}, {obj['draw_dependence_class'].lower()}, "
            f"resilience {obj['resilience_class']} - a clean, self-supporting line with no real risk."
        )
    if category == "NORMAL_KEEP":
        return (
            f"{dest} is a solid but not exceptional line (grade {cg}); "
            f"{obj['draw_dependence_class'].lower()}, resilience {obj['resilience_class']}."
        )
    if category == "CONDITIONAL_KEEP":
        return (
            f"Right at the keep/mulligan boundary (grade {cg} == the size-7 threshold) - "
            f"{dest} is real but {obj['draw_dependence_class'].lower()} and only {obj['resilience_class']}."
        )
    if category in ("MULLIGAN", "MULLIGAN_TRAP_DECEPTIVE_reject"):
        return f"No sufficiently strong destination (grade {cg}) - not worth keeping despite surface resources."
    return f"grade {cg}"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=6013)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--tries", type=int, default=40000)
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    deck_size = len(cards)
    rng = random.Random(args.seed)

    buckets = {"SNAP_KEEP": [], "NORMAL_KEEP": [], "CONDITIONAL_KEEP": [], "MULLIGAN": [], "TRAP": [], "HIDDEN_GEM": []}
    TARGET = 10

    def _bucket_full():
        return (
            len(buckets["SNAP_KEEP"]) >= TARGET and len(buckets["NORMAL_KEEP"]) >= TARGET
            and len(buckets["CONDITIONAL_KEEP"]) >= TARGET and len(buckets["MULLIGAN"]) >= TARGET
            and (len(buckets["TRAP"]) + len(buckets["HIDDEN_GEM"])) >= TARGET
        )

    i = 0
    while i < args.tries and not _bucket_full():
        i += 1
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]
        state, grade = _find_best_trajectory_with_state(hand, library, on_play, cards, combos)
        seat = CATEGORY_SEAT_CYCLE[i % len(CATEGORY_SEAT_CYCLE)]
        archetype = CATEGORY_ARCHETYPE_CYCLE[i % len(CATEGORY_ARCHETYPE_CYCLE)]
        obj = build_trajectory_object(hand, state, grade, cards, deck_size, on_play, seat=seat, archetype=archetype)
        cg = gated_model(obj)
        cat = _category_of(obj, cg)
        row = {
            "hand": sorted(hand), "mulligan_depth": 0, "seat": seat, "pod": archetype,
            "best_line": f"T{obj['deployment_turn']} {obj['destination']} ({grade['mechanism']})" if obj["destination"] else "no destination",
            "destination": obj["destination"], "intrinsic_strength": obj["intrinsic_strength"],
            "relative_speed": obj["relative_speed"], "draw_dependence": obj["draw_dependence_class"],
            "outs": obj["outs_count"], "success_probability": obj["probability_of_trajectory"],
            "first_realized_value": obj["earliest_expected_realization"],
            "fragility": obj["resilience_class"], "recovery_plan": obj["recovery_trajectory"],
            "relevant_agency": obj["relevant_agency"], "final_decision": "KEEP" if GRADE_RANK[cg] <= GRADE_RANK["C"] else "MULLIGAN",
            "contextual_grade": cg,
        }
        row["why"] = _why(obj, cg, cat)

        if cat == "SNAP_KEEP" and len(buckets["SNAP_KEEP"]) < TARGET:
            buckets["SNAP_KEEP"].append(row)
        elif cat == "NORMAL_KEEP" and len(buckets["NORMAL_KEEP"]) < TARGET:
            buckets["NORMAL_KEEP"].append(row)
        elif cat == "CONDITIONAL_KEEP" and len(buckets["CONDITIONAL_KEEP"]) < TARGET:
            buckets["CONDITIONAL_KEEP"].append(row)
        elif cat == "MULLIGAN" and len(buckets["MULLIGAN"]) < TARGET:
            buckets["MULLIGAN"].append(row)
        elif cat == "MULLIGAN_TRAP_DECEPTIVE" and len(buckets["TRAP"]) < TARGET // 2 + 1:
            row["why"] = f"LOOKS resource-rich ({obj['cards_remaining']} cards remaining, live agency {obj['live_agency']}) but grade is {cg} - no real destination underneath the resources."
            buckets["TRAP"].append(row)
        elif cg in ("S+", "S", "A+", "A") and obj["cards_remaining"] is not None and obj["cards_remaining"] <= 2 and len(buckets["HIDDEN_GEM"]) < TARGET // 2 + 1:
            row["why"] = f"LOOKS thin (only {obj['cards_remaining']} cards remaining) but the destination itself (grade {cg}) is strong enough to be a real keep."
            buckets["HIDDEN_GEM"].append(row)

    deceptive = (buckets["TRAP"] + buckets["HIDDEN_GEM"])[:TARGET]

    disagreement_path = REPO_ROOT / "results" / "solo_baseline" / "contextual_disagreement_examples.json"
    disagreement_data = json.loads(disagreement_path.read_text()) if disagreement_path.exists() else {"examples": {}}

    def _fmt_row(n, row):
        lines = [f"### {n}. Hand: {', '.join(row['hand'])}", ""]
        lines.append(f"- **MULLIGAN DEPTH**: {row['mulligan_depth']}")
        lines.append(f"- **SEAT**: {row['seat']}")
        lines.append(f"- **POD**: {row['pod']}")
        lines.append(f"- **BEST LINE**: {row['best_line']}")
        lines.append(f"- **DESTINATION**: {row['destination']}")
        lines.append(f"- **INTRINSIC STRENGTH**: {row['intrinsic_strength']}")
        lines.append(f"- **RELATIVE SPEED**: {row['relative_speed']}")
        lines.append(f"- **DRAW DEPENDENCE**: {row['draw_dependence']}")
        lines.append(f"- **OUTS / SUCCESS PROBABILITY**: {row['outs']} / {row['success_probability']}")
        lines.append(f"- **FIRST REALIZED VALUE**: {row['first_realized_value']}")
        lines.append(f"- **FRAGILITY**: {row['fragility']}")
        lines.append(f"- **RECOVERY PLAN**: {row['recovery_plan']}")
        lines.append(f"- **RELEVANT AGENCY**: {row['relevant_agency']}")
        lines.append(f"- **FINAL DECISION**: {row['final_decision']} (contextual grade {row['contextual_grade']})")
        lines.append(f"- **WHY**: {row['why']}")
        lines.append("")
        return "\n".join(lines)

    sections = [
        "# MULL-006 Primer Mulligan Packet v4\n",
        (
            "SIM-001 MULL-006 section 24. Every hand below is a REAL simulated hand (not "
            "fabricated), evaluated via the gated contextual architecture "
            "(contextual_valuation_models.gated_model) at the seat/pod combination shown. "
            "MULLIGAN DEPTH=0 throughout (these are fresh opening-7 evaluations); FIRST REALIZED "
            "VALUE uses engine_realization_timing_model's ordinal label, never a fabricated turn "
            "estimate for opponent-dependent engines.\n"
        ),
        "## 10 Snap Keeps\n",
        "\n".join(_fmt_row(i + 1, r) for i, r in enumerate(buckets["SNAP_KEEP"][:TARGET])),
        "## 10 Normal Keeps\n",
        "\n".join(_fmt_row(i + 1, r) for i, r in enumerate(buckets["NORMAL_KEEP"][:TARGET])),
        "## 10 Conditional Keeps\n",
        "\n".join(_fmt_row(i + 1, r) for i, r in enumerate(buckets["CONDITIONAL_KEEP"][:TARGET])),
        "## 10 Mulligans\n",
        "\n".join(_fmt_row(i + 1, r) for i, r in enumerate(buckets["MULLIGAN"][:TARGET])),
        (
            "## 10 Deceptive Hands\n\n"
            "Split between TRAP hands (look resource-rich, grade poorly - no real destination "
            "underneath) and HIDDEN GEM hands (look thin, grade well - the destination alone is "
            "enough).\n"
        ),
        "\n".join(_fmt_row(i + 1, r) for i, r in enumerate(deceptive)),
        (
            "## Similar Hands, One Variable Changed\n\n"
            "Reused directly from contextual_disagreement_examples.json (task #120) - the exact "
            "same hand, decision changes from only ONE contextual variable.\n"
        ),
    ]

    for key in ("B", "E", "G"):
        ex = disagreement_data.get("examples", {}).get(key)
        if ex:
            sections.append(f"### {ex['label']}\n\n" + json.dumps(ex, indent=2) + "\n")

    text = "\n".join(sections)
    out_path = REPO_ROOT / "results" / "solo_baseline" / "primer_mulligan_packet_v4.md"
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {out_path}")
    for k, v in buckets.items():
        print(k, len(v))


if __name__ == "__main__":
    main()
