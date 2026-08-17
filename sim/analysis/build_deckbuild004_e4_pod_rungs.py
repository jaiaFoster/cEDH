"""SIM-DECKBUILD-004 E4 (scoped) — Birthing Pod target quality census by rung.

Reuses E2's constructed-state + try_activate_pod machinery (no new engine code). For each rung
(1->2, 2->3, 3->4, 4->5), enumerates EVERY legal Pod target in the variant's real library from a
representative MV-appropriate sacrifice, classifies each target's resulting state, and reports
the distribution - directly answering the assignment's Talion_rung_value/Seedborn_rung_value/
Pod_dead_end_rate questions for the two specific rungs (3->4, 4->5) those cards actually occupy.

Target quality classes (a simplified, disclosed version of the assignment's 6-class taxonomy):
  - immediate_win: deterministic_win_available on the resulting state.
  - protected_conversion: deterministic_win_protected (implies immediate_win too, reported
    separately since not every immediate win is protected).
  - one_action_from_win: one_action_from_verified_win (a real, mana- or tutor-backed step from a
    verified combo - NOT a topdeck-dependent one_draw_step, matching this project's own
    established distinction) - used as this pass's proxy for "credible near-term win," not a
    literal "next untap" turn-clock claim.
  - engine_upgrade: two_plus_engines_active becomes true, or the target itself is in ENGINES.
  - value_only: none of the above, but a legal target exists.
  - dead_end: no legal target exists in the library at this rung at all.

Not the assignment's full frequency-weighted, exhaustive per-target census (deferred - see this
task's final report) - a single representative sacrifice per rung, all its legal targets, per
variant. Scoped given this project's remaining effort budget for SIM-DECKBUILD-004.
"""
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, ENGINES  # noqa: E402
from opening_hand_policy import HandState, LandInPlay, Perm  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from pod_and_battlefield_tutors import try_activate_pod, POD_NAME  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build  # noqa: E402

RUNGS = {
    "1_to_2": "Avacyn's Pilgrim",   # real MV1 creature in this deck
    "2_to_3": "Devoted Druid",       # real MV2 creature
    "3_to_4": "Derevi, Empyrial Tactician",  # real MV3 creature
    "4_to_5": "Hazel's Brewmaster",  # real MV4 creature (Talion is also MV4, Seedborn MV5)
}
VARIANTS = ["B0_BASELINE", "B3_FULL_PACKAGE", "B6_NO_TALION", "B7_NO_SEEDBORN"]


def _classify(m):
    if m["deterministic_win_protected"]:
        return "protected_conversion"
    if m["deterministic_win_available"]:
        return "immediate_win"
    if m["one_action_from_verified_win"]:
        return "one_action_from_win"
    if m["two_plus_engines_active"] or m["any_engine_active"]:
        return "engine_upgrade"
    return "value_only"


def rung_census(variant_names, cards, combos, sac_name):
    sac_mv = cards[sac_name]["cmc"]
    library = [n for n in variant_names if n != sac_name and n != POD_NAME]
    targets_tried = 0
    class_counts = {}
    best_targets = {}
    for target in library:
        if "Creature" not in cards.get(target, {}).get("type", ""):
            continue
        if cards[target]["cmc"] != sac_mv + 1:
            continue
        targets_tried += 1
        state = HandState([], list(library), on_play=True, rng=__import__("random").Random(0), cards=cards)
        state.turn = 3
        state.command_zone.clear()
        for _ in range(8):
            state.lands.append(LandInPlay("City of Brass", 1, tapped=False))
        state.nonland_perms.append(Perm(POD_NAME, 1, False))
        state.nonland_perms.append(Perm(sac_name, 1, True))
        if not try_activate_pod(state, cards, sac_name, target):
            continue
        m = snapshot_metrics(state, cards, combos)
        cls = _classify(m)
        class_counts[cls] = class_counts.get(cls, 0) + 1
        best_targets.setdefault(cls, []).append(target)
    if targets_tried == 0:
        return {"dead_end": True, "targets_tried": 0, "class_distribution": {}, "example_targets_by_class": {}}
    return {
        "dead_end": False, "targets_tried": targets_tried,
        "class_distribution": {k: v / targets_tried for k, v in class_counts.items()},
        "example_targets_by_class": {k: sorted(set(v))[:5] for k, v in best_targets.items()},
    }


def main():
    payload, base_cards = load_deck_cards()
    cards_pool = all_cards_dict(base_cards)
    install_new_card_tables()
    base_names = list(base_cards.keys())
    combos = load_deterministic_combos()

    try:
        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_004_E4_POD_RUNGS_SCOPED", "evidence_type": "static_probability",
            "scope_note": (
                "One representative sacrifice per rung (see RUNGS), every legal target in the "
                "variant's real library, NOT the assignment's full frequency-weighted exhaustive "
                "census across every possible sacrifice - deferred, see final report."
            ),
            "results": {},
        }
        for rung_name, sac_name in RUNGS.items():
            out["results"][rung_name] = {"sacrifice": sac_name}
            for variant in VARIANTS:
                t0 = time.time()
                names = build(base_names, cards_pool, variant)
                cards = {n: cards_pool[n] for n in names}
                out["results"][rung_name][variant] = rung_census(names, cards, combos, sac_name)
                print(f"{rung_name} :: {variant} ({time.time()-t0:.2f}s)")

        talion_rung = out["results"]["3_to_4"]
        seedborn_rung = out["results"]["4_to_5"]
        out["talion_seedborn_rung_summary"] = {
            "talion_appears_as_legal_target_B3": "Talion, the Kindly Lord" in
                [t for v in talion_rung.get("B3_FULL_PACKAGE", {}).get("example_targets_by_class", {}).values() for t in v],
            "talion_rung_B3_class_distribution": talion_rung.get("B3_FULL_PACKAGE", {}).get("class_distribution"),
            "talion_rung_B0_class_distribution": talion_rung.get("B0_BASELINE", {}).get("class_distribution"),
            "seedborn_appears_as_legal_target_B3": "Seedborn Muse" in
                [t for v in seedborn_rung.get("B3_FULL_PACKAGE", {}).get("example_targets_by_class", {}).values() for t in v],
            "seedborn_rung_B3_class_distribution": seedborn_rung.get("B3_FULL_PACKAGE", {}).get("class_distribution"),
            "seedborn_rung_B0_class_distribution": seedborn_rung.get("B0_BASELINE", {}).get("class_distribution"),
            "note": (
                "'Appears as a legal target' only confirms Pod CAN find it at this rung - it says "
                "nothing about whether landing on Talion/Seedborn specifically was the BEST "
                "available target that turn (a real creature-selection question the greedy Pod "
                "target choice - not modeled here, this census enumerates ALL legal targets, not "
                "which one a pilot would actually pick) - and, per this task's standing "
                "disclosure, says NOTHING about Seedborn's real value even once resolved (that "
                "value requires opponent turns this solo engine cannot simulate)."
            ),
        }
    finally:
        uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild004_e4_pod_rungs.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["talion_seedborn_rung_summary"], indent=2))


if __name__ == "__main__":
    main()
