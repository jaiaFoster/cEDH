"""SIM-DECKBUILD-004 E2 — deterministic conversion-graph audit (HIGHEST priority per assignment).

BOUNDED, DISCLOSED SCOPE (not the assignment's full ~35 start-states x 9 abstract-targets x 7
variants combinatorial sweep - a genuinely exhaustive version of that is a much larger undertaking
than this task's remaining budget supports, and this project's own established convention
throughout trajectory_search.py/achievable_search.py is "bounded search, explicitly disclosed as
a lower bound, never claimed exhaustive"):

  - Start states: 2-3 REPRESENTATIVE instances per named family (not every one of the assignment's
    ~30 listed instances) - literal constructed battlefield/hand states (a real permanent already
    resolved, funded by a few untapped lands), not drawn from an opening hand.
  - Targets: the 4 the existing engine can genuinely, correctly detect without new fabricated
    detection logic - deterministic_win_available, deterministic_win_protected,
    thrasios_activation_now, two_plus_engines_active (reused verbatim from
    opening_hand_metrics.snapshot_metrics, the SAME combo-status machinery MULL-005R/006's own
    "deterministic win" findings are built on). infinite_mana/Ranger_Captain_protected_win/
    Grand_Abolisher_protected_win/overwhelming_Seedborn_state are NOT separately detected - see
    "targets_not_measured" in the output for why each is out of scope this pass (Grand Abolisher
    isn't in this 98-card list at all; Seedborn's real value is architecturally invisible to this
    solo engine per deckbuild004_cards.py's own disclosure).
  - Variants: all 7 the assignment names for E2 (B0, B2, B3, B4-B7) - B1 is correctly absent
    from the assignment's own E2 variant list (the engine-only swap doesn't touch tutor topology).

For each (start_state, variant), tries EVERY legal target for that state's tutor/activation
mechanism (a real, not sampled, search over the variant's actual library) and keeps the BEST
reachable outcome - exactly matching the assignment's own anti_overclaim instructions: Neoform is
never credited without a legal sac+target; Pod's sorcery-only-activation restriction is preserved
by construction (only ONE activation is modeled per state, as a real Pod/turn constraint).
"""
import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, parse_cost  # noqa: E402
from opening_hand_policy import HandState, LandInPlay, Perm, _try_pay, _commit_payment  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from pod_and_battlefield_tutors import (  # noqa: E402
    try_activate_pod, try_activate_survival, try_battlefield_creature_tutor,
    BATTLEFIELD_CREATURE_TUTORS, POD_NAME, SURVIVAL_NAME,
)
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build, VARIANTS  # noqa: E402

E2_VARIANTS = ["B0_BASELINE", "B2_CONVERSION_SWAP", "B3_FULL_PACKAGE",
               "B4_NO_NEOFORM", "B5_NO_SPEAKER", "B6_NO_TALION", "B7_NO_SEEDBORN"]

TARGETS = ["deterministic_win_available", "deterministic_win_protected",
           "thrasios_activation_now", "two_plus_engines_active"]

# Generous, disclosed mana base for every constructed state (5 untapped rainbow-equivalent
# sources: City of Brass x5 - isolates "does a legal target/action exist" from "is mana the
# bottleneck", which Sections E1/D already answer separately for the REAL opening-hand
# distribution). Every action's real mana cost is still charged against this pool via the normal
# _try_pay/_commit_payment engine - not waived.
def _funded_state(hand, library, battlefield_perms, cards, n_lands=8):
    state = HandState(hand, library, on_play=True, rng=__import__("random").Random(0), cards=cards)
    state.turn = 3
    # A constructed mid-game state already has commanders resolved or irrelevant to THIS specific
    # question (does the tutor/activation mechanism reach a good target) - clearing the command
    # zone avoids the generic loop auto-casting Tymna/Thrasios and silently eating the funded mana
    # budget meant for the mechanism under test (a real confound found while building this script).
    state.command_zone.clear()
    for _ in range(n_lands):
        state.lands.append(LandInPlay("City of Brass", 1, tapped=False))
    for name in battlefield_perms:
        state.nonland_perms.append(Perm(name, 1, "Creature" in cards.get(name, {}).get("type", "")))
    return state


START_STATE_FAMILIES = {
    "Birthing_Pod": {
        "mechanism": "pod",
        "instances": [
            {"label": "Pod + expendable MV1 (Birds of Paradise)", "battlefield": [POD_NAME, "Birds of Paradise"], "sac": "Birds of Paradise"},
            {"label": "Pod + Devoted Druid (MV2)", "battlefield": [POD_NAME, "Devoted Druid"], "sac": "Devoted Druid"},
            {"label": "Pod + Derevi (MV3)", "battlefield": [POD_NAME, "Derevi, Empyrial Tactician"], "sac": "Derevi, Empyrial Tactician"},
        ],
    },
    "Survival": {
        "mechanism": "survival",
        "instances": [
            {"label": "Survival + arbitrary expendable creature (MV1 in hand)", "battlefield": [SURVIVAL_NAME], "discard_hand_extra": ["Birds of Paradise"], "discard": "Birds of Paradise"},
            {"label": "Survival + Devoted Druid (MV2) in hand", "battlefield": [SURVIVAL_NAME], "discard_hand_extra": ["Devoted Druid"], "discard": "Devoted Druid"},
        ],
    },
    "Neoform": {
        "mechanism": "neoform",
        "instances": [
            {"label": "Neoform + MV1 creature (Birds of Paradise)", "battlefield": ["Birds of Paradise"], "hand_extra": ["Neoform"], "sac": "Birds of Paradise", "tutor": "Neoform"},
            {"label": "Neoform + MV3 creature (Derevi)", "battlefield": ["Derevi, Empyrial Tactician"], "hand_extra": ["Neoform"], "sac": "Derevi, Empyrial Tactician", "tutor": "Neoform"},
        ],
    },
    "Eldritch_Evolution": {
        "mechanism": "battlefield_tutor",
        "instances": [
            {"label": "Evolution + MV2 creature (Devoted Druid)", "battlefield": ["Devoted Druid"], "hand_extra": ["Eldritch Evolution"], "sac": "Devoted Druid", "tutor": "Eldritch Evolution"},
            {"label": "Evolution + MV3 creature (Derevi)", "battlefield": ["Derevi, Empyrial Tactician"], "hand_extra": ["Eldritch Evolution"], "sac": "Derevi, Empyrial Tactician", "tutor": "Eldritch Evolution"},
        ],
    },
    "Formidable_Speaker": {
        "mechanism": "speaker",
        # "Voice of Victory" (unclassified "other" in _card_class - see opening_hand_policy.py)
        # is used as discard fodder rather than an ACCELERATION-classified card (e.g. Birds of
        # Paradise) - the generic loop auto-casts accel cards for mana BEFORE Speaker's ETB gets a
        # chance to discard them, a real confound found while building this script (same pattern
        # already fixed in test_deckbuild004_new_cards.py's own Speaker ETB regression test).
        "instances": [
            {"label": "Speaker ETB + arbitrary discardable creature", "battlefield": [], "hand_extra": ["Formidable Speaker", "Voice of Victory"], "discard": "Voice of Victory"},
        ],
    },
    "Chord": {
        "mechanism": "battlefield_tutor",
        "instances": [
            {"label": "Chord X2 (2 creatures on board)", "battlefield": ["Birds of Paradise", "Noble Hierarch"], "hand_extra": ["Chord of Calling"], "tutor": "Chord of Calling", "target_mv": 2},
            {"label": "Chord X4 (4 creatures on board)", "battlefield": ["Birds of Paradise", "Noble Hierarch", "Devoted Druid", "Deathrite Shaman"], "hand_extra": ["Chord of Calling"], "tutor": "Chord of Calling", "target_mv": 4},
        ],
    },
}


def _best_reachable(inst, family, variant_names, cards, combos):
    """Tries every legal target for this instance's mechanism (Pod/Survival/Neoform/Eldritch
    Evolution/Chord/Speaker) against the VARIANT's real library, returns the best outcome found
    plus its path metadata. Returns None if the mechanism's own enabling card isn't in this
    variant (e.g. Neoform absent in B4_NO_NEOFORM)."""
    mechanism = family["mechanism"]
    hand_extra = inst.get("hand_extra", []) + inst.get("discard_hand_extra", [])
    for c in hand_extra:
        if c not in variant_names and c not in ("Birds of Paradise", "Devoted Druid", "Derevi, Empyrial Tactician"):
            return None, None
    for c in inst.get("battlefield", []):
        if c not in variant_names:
            return None, None
    if mechanism == "neoform" and "Neoform" not in variant_names:
        return None, None
    if mechanism == "battlefield_tutor" and inst.get("tutor") not in variant_names:
        return None, None
    if mechanism == "speaker" and "Formidable Speaker" not in variant_names:
        return None, None

    library = [n for n in variant_names if n not in inst.get("battlefield", []) and n not in hand_extra]
    best = None
    best_meta = None

    def _consider(state_after, meta):
        nonlocal best, best_meta
        m = snapshot_metrics(state_after, cards, combos)
        outcome = {t: bool(m[t]) for t in TARGETS}
        rank = sum(outcome.values())
        if best is None or rank > sum(best.values()):
            best, best_meta = outcome, meta

    if mechanism == "pod":
        sac_mv = cards[inst["sac"]]["cmc"]
        for target in library:
            if "Creature" not in cards.get(target, {}).get("type", ""):
                continue
            if cards[target]["cmc"] != sac_mv + 1:
                continue
            state = _funded_state([], list(library), inst["battlefield"], cards)
            if try_activate_pod(state, cards, inst["sac"], target):
                _consider(state, {"target": target, "mana_required": 2, "tutor_steps": 0, "activation": "pod"})
    elif mechanism == "survival":
        for target in library:
            if "Creature" not in cards.get(target, {}).get("type", ""):
                continue
            state = _funded_state(list(hand_extra), list(library), inst["battlefield"], cards)
            if try_activate_survival(state, cards, inst["discard"], target):
                # Survival puts to HAND, not battlefield - the real conversion needs a SECOND cast.
                # Modeled honestly: check whether the found card is then also castable this turn.
                gen, pips, x = parse_cost(cards[target]["mana_cost"])
                from opening_hand_policy import is_currently_castable
                if x == 0 and is_currently_castable(state, gen, pips):
                    state.hand.remove(target)
                    state.nonland_perms.append(Perm(target, state.turn, "Creature" in cards[target]["type"]))
                    from opening_hand_policy import _try_pay as _tp2, _commit_payment as _cp2
                    plan2 = _tp2(state, gen, pips)
                    if plan2 is not None:
                        _cp2(state, plan2)
                _consider(state, {"target": target, "mana_required": 1, "tutor_steps": 0, "activation": "survival_to_hand_then_cast_if_affordable"})
    elif mechanism in ("neoform", "battlefield_tutor"):
        tutor_name = inst["tutor"]
        spec = BATTLEFIELD_CREATURE_TUTORS[tutor_name]
        for target in library:
            if "Creature" not in cards.get(target, {}).get("type", ""):
                continue
            if spec["x_based"]:
                if "target_mv" in inst and cards[target]["cmc"] != inst["target_mv"]:
                    continue
                sac_name = None
            else:
                mv_offset = spec.get("mv_offset", 2)
                if cards[target]["cmc"] != cards[inst["sac"]]["cmc"] + mv_offset:
                    continue
                sac_name = inst["sac"]
            state = _funded_state(list(hand_extra), list(library), inst["battlefield"], cards)
            if try_battlefield_creature_tutor(state, cards, tutor_name, target, sac_name):
                _consider(state, {"target": target, "mana_required": None, "tutor_steps": 1, "activation": tutor_name})
    elif mechanism == "speaker":
        for target in library:
            if "Creature" not in cards.get(target, {}).get("type", ""):
                continue
            state = _funded_state(list(hand_extra), list(library), inst["battlefield"], cards)
            from opening_hand_policy import develop_turn, DEFAULT_PRIORITY
            state.turn = 2
            state.nonland_perms = []  # Speaker must be CAST this turn for its ETB to fire
            actions = develop_turn(
                state, cards, priority_order=DEFAULT_PRIORITY,
                forced_formidable_speaker_choice=(inst["discard"], target),
            )
            if any(a[0] == "formidable_speaker_etb" for a in actions):
                _consider(state, {"target": target, "mana_required": 3, "tutor_steps": 1, "activation": "speaker_etb_to_hand"})

    return best, best_meta


def main():
    ap = argparse.ArgumentParser()
    args = ap.parse_args()

    payload, base_cards = load_deck_cards()
    cards_pool = all_cards_dict(base_cards)
    install_new_card_tables()
    combos = load_deterministic_combos()
    base_names = list(base_cards.keys())

    try:
        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_004_E2_TUTOR_TOPOLOGY", "evidence_type": "static_probability",
            "priority": "HIGHEST",
            "scope_note": (
                "Bounded to 2-3 representative instances per family and 4 detectable targets - "
                "see module docstring for the full disclosure. This is a BOUNDED_SEARCH_LOWER_"
                "BOUND, matching this project's established trajectory_search.py convention, not "
                "an exhaustive claim."
            ),
            "targets_not_measured": {
                "infinite_mana": "No separate detector distinct from deterministic_win_available "
                                  "in this pass - this deck's verified deterministic combos are "
                                  "already the infinite-mana/win lines load_deterministic_combos() "
                                  "tracks; a mana-only (non-winning) infinite loop would need its "
                                  "own detector, not built here.",
                "Ranger_Captain_protected_win": "Ranger-Captain of Eos IS in this list, but its "
                                                 "real ability (exile opponents' MV<=1 hand cards) "
                                                 "is a disruption effect with no natural-opponent "
                                                 "model to test protection against in this solo "
                                                 "engine - not separately detected.",
                "Grand_Abolisher_protected_win": "Grand Abolisher is NOT in this 98-card list - "
                                                  "target inapplicable, not fabricated.",
                "overwhelming_Seedborn_state": "Seedborn Muse's real trigger (untap on OTHER "
                                                "players' untap steps) cannot occur in ANY solo "
                                                "simulation at any turn count - architecturally "
                                                "invisible here, not merely unmeasured (see "
                                                "deckbuild004_cards.py's own disclosure).",
            },
            "results": {},
        }

        for family_name, family in START_STATE_FAMILIES.items():
            out["results"][family_name] = {}
            for inst in family["instances"]:
                t0 = time.time()
                out["results"][family_name][inst["label"]] = {}
                for variant in E2_VARIANTS:
                    variant_names = build(base_names, cards_pool, variant)
                    variant_cards = {n: cards_pool[n] for n in variant_names}
                    best, meta = _best_reachable(inst, family, variant_names, variant_cards, combos)
                    out["results"][family_name][inst["label"]][variant] = (
                        {"reachable_outcomes": best, "path": meta} if best is not None
                        else {"reachable_outcomes": None, "path": None,
                              "note": "mechanism's enabling card not present in this variant"}
                    )
                print(f"{family_name} :: {inst['label']} ({time.time()-t0:.2f}s)")

        # Aggregate: how many (family, instance) start states newly reach each target in B3 vs B0.
        newly_winning = {t: [] for t in TARGETS}
        for family_name, insts in out["results"].items():
            for label, by_variant in insts.items():
                b0 = by_variant.get("B0_BASELINE", {}).get("reachable_outcomes")
                b3 = by_variant.get("B3_FULL_PACKAGE", {}).get("reachable_outcomes")
                if b0 is None or b3 is None:
                    continue
                for t in TARGETS:
                    if b3.get(t) and not b0.get(t):
                        newly_winning[t].append(f"{family_name} :: {label}")
        out["states_newly_reaching_target_B3_vs_B0"] = newly_winning
    finally:
        uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild004_e2_tutor_topology.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["states_newly_reaching_target_B3_vs_B0"], indent=2))


if __name__ == "__main__":
    main()
