"""SIM-DECKBUILD-007 Workstream 3 — post-fight conversion architecture + Pod line verification.

Higher priority than generic goldfish win rate per the assignment. Constructs REPRESENTATIVE
T3-T5 post-first-fight states across a structured grid (not fully random - more interpretable,
and this project's combat/opponent-interaction layer isn't modeled, so "post-fight" states are
hand-built resource snapshots, not derived from a simulated fight):
  mana_total in {4, 6, 8, 10} (covers the assignment's "4-8+")
  creature_count in {2, 3, 5} (covers "2-5+")
  pod_present in {True, False}
  protection_count in {0, 1, 2}
= 4*3*2*3 = 72 grid cells, each averaged over N random creature/engine draws (the specific
creatures/engine on board vary - this is what the Monte Carlo layer captures within each cell).

Simplifications, disclosed: mana is modeled via generic any-color sources (like
build_deckbuild004_e4_pod_rungs.py's own rung_census pattern) - optimistic on color fixing, a
real limitation of not modeling a full opponent-aware color-availability state; "opponents
partially depleted but still capable of interaction" is represented only implicitly, via the
protection_count axis (0-2 held-up interaction pieces) checked against real joint-payability
(deterministic_win_protected), not simulated opponent actions.

Failure classification (per assignment): mana / access-tutor / protection / wrong_pod_mv /
missing_outlet / interaction / sequencing. This project's engine does not model an opponent or a
stack, so "interaction" and "sequencing" failures are inferred structurally (no live protection
payable / a legal Pod target existed but wasn't the RIGHT one for a deterministic win), not
observed from actual opposing plays - disclosed, not overclaimed.
"""
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards, deckbuild007_cards_pool  # noqa: E402
from opening_hand_model import load_deterministic_combos, deck_provenance_fields, ENGINES, INTERACTION_CASTABLE  # noqa: E402
from opening_hand_policy import HandState, LandInPlay, Perm  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from pod_and_battlefield_tutors import try_activate_pod, POD_NAME  # noqa: E402

MANA_LEVELS = [4, 6, 8, 10]
CREATURE_COUNTS = [2, 3, 5]
PROTECTION_COUNTS = [0, 1, 2]
SAMPLES_PER_CELL = 150

POD_RUNGS = {
    "1_to_2": {"sac_mv": 1, "sac_example": "Delighted Halfling",
               "key_targets": {"Devoted Druid", "Grand Abolisher"}},
    "2_to_3": {"sac_mv": 2, "sac_example": "Badgermole Cub",
               "key_targets": {"Derevi, Empyrial Tactician", "Ranger-Captain of Eos", "Abhorrent Oculus", "Formidable Speaker"}},
    "3_to_4": {"sac_mv": 3, "sac_example": "Endurance",
               "key_targets": {"Hazel's Brewmaster", "Clever Impersonator", "Talion, the Kindly Lord"}},
    "4_to_5": {"sac_mv": 4, "sac_example": "Clever Impersonator",
               "key_targets": {"Seedborn Muse"}},
}


def _classify_state(m):
    if m["deterministic_win_protected"]:
        return "protected_conversion"
    if m["deterministic_win_available"]:
        return "unprotected_conversion"
    if m["one_action_from_verified_win"]:
        return "one_action_away"
    return "not_converting"


def _classify_failure(m, mana_total, protection_count, pod_present, pod_used):
    """Best-effort single dominant reason, per the assignment's taxonomy."""
    if m["deterministic_win_protected"]:
        return None
    if m["deterministic_win_available"] and protection_count == 0:
        return "protection"
    if m["one_action_from_verified_win"]:
        return "sequencing"
    if pod_present and not pod_used:
        return "wrong_pod_mv"
    if not pod_present:
        return "missing_outlet"
    if mana_total < 6:
        return "mana"
    return "access"


def rung_census(all_names, cards, combos, sac_mv, sac_name, key_targets):
    library = [n for n in all_names if n != sac_name and n != POD_NAME]
    targets_tried = 0
    key_hits = 0
    class_counts = {}
    for target in library:
        if "Creature" not in cards.get(target, {}).get("type", ""):
            continue
        if cards[target]["cmc"] != sac_mv + 1:
            continue
        targets_tried += 1
        state = HandState([], list(library), on_play=True, rng=random.Random(0), cards=cards)
        state.turn = 3
        state.command_zone.clear()
        for _ in range(8):
            state.lands.append(LandInPlay("City of Brass", 1, tapped=False))
        state.nonland_perms.append(Perm(POD_NAME, 1, False))
        state.nonland_perms.append(Perm(sac_name, 1, True))
        if not try_activate_pod(state, cards, sac_name, target):
            continue
        m = snapshot_metrics(state, cards, combos)
        cls = _classify_state(m)
        class_counts[cls] = class_counts.get(cls, 0) + 1
        if target in key_targets:
            key_hits += 1
    return {
        "dead_end": targets_tried == 0,
        "targets_tried": targets_tried,
        "class_distribution": {k: v / targets_tried for k, v in class_counts.items()} if targets_tried else {},
        "key_target_hit_rate": key_hits / targets_tried if targets_tried else None,
    }


def _sample_state(all_names, cards, combos, rng, mana_total, creature_count, pod_present, protection_count):
    engine_pool = sorted(n for n in ENGINES if n in cards and "Land" not in cards[n]["type"] and n != POD_NAME)
    creature_pool = sorted(n for n in cards if "Creature" in cards[n]["type"] and n not in (d7.CARPET_NAME,))
    interaction_pool = sorted(n for n in INTERACTION_CASTABLE if n in cards)

    engine_choice = rng.choice(engine_pool)
    creature_choices = rng.sample([c for c in creature_pool if c != engine_choice], creature_count)
    protection_choices = rng.sample(interaction_pool, min(protection_count, len(interaction_pool)))

    library = [n for n in all_names if n not in creature_choices and n != engine_choice
               and n not in protection_choices and n != POD_NAME]
    state = HandState(list(protection_choices), library, on_play=True, rng=rng, cards=cards)
    state.turn = 4
    state.command_zone.clear()
    for _ in range(mana_total):
        state.lands.append(LandInPlay("City of Brass", 1, tapped=False))
    for c in creature_choices:
        state.nonland_perms.append(Perm(c, 1, True))
    is_creature_engine = "Creature" in cards[engine_choice]["type"]
    state.nonland_perms.append(Perm(engine_choice, 1, is_creature_engine))
    if pod_present:
        state.nonland_perms.append(Perm(POD_NAME, 1, False))

    pod_used = False
    if pod_present and creature_choices:
        sac = max(creature_choices, key=lambda c: cards[c]["cmc"])
        sac_mv = cards[sac]["cmc"]
        target = next(
            (t for t in library if "Creature" in cards.get(t, {}).get("type", "") and cards[t]["cmc"] == sac_mv + 1),
            None,
        )
        if target is not None:
            pod_used = try_activate_pod(state, cards, sac, target)

    m = snapshot_metrics(state, cards, combos)
    return m, pod_used


def main():
    d7.install_new_card_tables()
    try:
        payload, base_rows = load_deckbuild007_cards()
        cards_pool = deckbuild007_cards_pool(base_rows)
        all_names = list(base_rows.keys())
        combos = load_deterministic_combos()

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_007_WS3_CONVERSION_ARCHITECTURE", "evidence_type": "goldfish",
            "grid_note": (
                "Structured grid (mana x creatures x pod-present x protection), "
                f"{SAMPLES_PER_CELL} random creature/engine draws per cell - see module docstring "
                "for disclosed simplifications (generic any-color mana, no live opponent model)."
            ),
            "pod_rungs": {}, "grid_results": {}, "aggregate_by_axis": {},
        }

        t0 = time.time()
        for rung_name, spec in POD_RUNGS.items():
            out["pod_rungs"][rung_name] = rung_census(
                all_names, cards_pool, combos, spec["sac_mv"], spec["sac_example"], spec["key_targets"]
            )
        print(f"pod rungs ({time.time()-t0:.1f}s)")

        rng = random.Random(87300)
        pod_present_results = {"protected": 0, "unprotected": 0, "one_action": 0, "not_converting": 0, "n": 0}
        pod_absent_results = {"protected": 0, "unprotected": 0, "one_action": 0, "not_converting": 0, "n": 0}
        failure_counts = {}
        t0 = time.time()
        for mana_total in MANA_LEVELS:
            for creature_count in CREATURE_COUNTS:
                for pod_present in (True, False):
                    for protection_count in PROTECTION_COUNTS:
                        key = f"mana{mana_total}_creatures{creature_count}_pod{pod_present}_prot{protection_count}"
                        cls_counts = {}
                        pod_used_count = 0
                        for _ in range(SAMPLES_PER_CELL):
                            m, pod_used = _sample_state(
                                all_names, cards_pool, combos, rng, mana_total, creature_count,
                                pod_present, protection_count,
                            )
                            cls = _classify_state(m)
                            cls_counts[cls] = cls_counts.get(cls, 0) + 1
                            if pod_used:
                                pod_used_count += 1
                            fail = _classify_failure(m, mana_total, protection_count, pod_present, pod_used)
                            if fail:
                                failure_counts[fail] = failure_counts.get(fail, 0) + 1
                            bucket = pod_present_results if pod_present else pod_absent_results
                            bucket["n"] += 1
                            if cls == "protected_conversion":
                                bucket["protected"] += 1
                            elif cls == "unprotected_conversion":
                                bucket["unprotected"] += 1
                            elif cls == "one_action_away":
                                bucket["one_action"] += 1
                            else:
                                bucket["not_converting"] += 1
                        out["grid_results"][key] = {
                            k: v / SAMPLES_PER_CELL for k, v in cls_counts.items()
                        } | {"pod_used_rate": pod_used_count / SAMPLES_PER_CELL if pod_present else None}
        print(f"grid ({time.time()-t0:.1f}s)")

        def convert_rate(bucket):
            return (bucket["protected"] + bucket["unprotected"]) / bucket["n"]

        out["aggregate_by_axis"] = {
            "P_convert_given_pod_present": convert_rate(pod_present_results),
            "P_convert_given_pod_absent": convert_rate(pod_absent_results),
            "P_protected_convert_given_pod_present": pod_present_results["protected"] / pod_present_results["n"],
            "P_protected_convert_given_pod_absent": pod_absent_results["protected"] / pod_absent_results["n"],
            "failure_mode_distribution": {
                k: v / sum(failure_counts.values()) for k, v in failure_counts.items()
            } if failure_counts else {},
        }
    finally:
        d7.uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild007_ws3_conversion_architecture.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["pod_rungs"], indent=2))
    print(json.dumps(out["aggregate_by_axis"], indent=2))


if __name__ == "__main__":
    main()
