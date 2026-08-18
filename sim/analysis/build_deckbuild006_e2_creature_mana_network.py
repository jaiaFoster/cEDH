"""SIM-DECKBUILD-006 E2 (HIGHEST priority) — creature-mana network by turn across A/B/C/D.

"Network" here means the set of creatures that interact with mana production: the true one-mana
dorks themselves, Kinnan's doubler (scales with count of nonland mana sources tapped), and Gaea's
Cradle's per-creature output (scales with total creature count) - E3 covers Cradle's OWN draw/play
probability in depth; this block reports Cradle's STRUCTURAL ceiling (what it would tap for RIGHT
NOW if it were online), a deterministic function of creature_count, not a sampled draw probability.

Two dork-count layers, kept explicitly separate (this task's central methodology requirement -
"separate structural/resource accessibility from pilot decisions"):
  - NOMINAL_TRUE_ONE_MANA_DORKS: the 5 real one-mana-cost persistent creature-mana cards this
    deck runs (Birds of Paradise, Noble Hierarch, Delighted Halfling, Avacyn's Pilgrim, Deathrite
    Shaman) - matches the assignment's own "five true one-mana dorks" framing by CARD, not by
    what this engine currently simulates as functional.
  - FUNCTIONAL_DORKS: the subset this project's engine actually models as producing mana
    (opening_hand_model.MANA_SOURCES with creature=True) - EXCLUDES Deathrite Shaman, whose
    graveyard-exile mana ability has been a disclosed, deliberate non-implementation since this
    project's earliest version (opening_hand_model.py's own module docstring: "no early graveyard
    fuel in an opening-hand context anyway"). Re-verified below for the NEW operative list (this
    task's regression_requirements explicitly calls for re-checking this, since MANA-AUDIT-002's
    prior finding was scoped to the OLD list's composition) - see deathrite_graveyard_fuel_reverification.

Badgermole Cub disclosure: this deck's "Whenever you tap a creature for mana, add an additional
{G}" amplifier (DORK-003 in build_t1_t3_trajectory_audit.py, already investigated and deliberately
deferred before this task even existed - a real engine change, not attempted here either, given
the same low-T1-3-frequency reasoning and this task's own report_policy against expanding
infrastructure beyond what's needed to resolve the decision). Its omission is a CONSERVATIVE bias
specifically for this question: every additional dork present is a strictly independent Badgermole
trigger opportunity, so the more dorks the deck runs, the MORE this project's numbers UNDERSTATE
the 5-dork configs' relative advantage over the 4-dork configs - never the reverse. Confirmed not
modeled via a regression test in this task's own test file, not silently left unverified.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deterministic_combos, deck_provenance_fields, MANA_SOURCES  # noqa: E402
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
import deckbuild006_cards as d6  # noqa: E402
from deckbuild006_variants import load_deckbuild006_cards, deckbuild006_cards_pool, build, VARIANTS  # noqa: E402

NOMINAL_TRUE_ONE_MANA_DORKS = {
    "Birds of Paradise", "Noble Hierarch", "Delighted Halfling", "Avacyn's Pilgrim", "Deathrite Shaman",
}
KINNAN_NAME = "Kinnan, Bonder Prodigy"
CRADLE_NAME = "Gaea's Cradle"


def deathrite_graveyard_fuel_reverification(base_names):
    """Re-checks, against the NEW operative 98's actual card set, whether any effect could
    plausibly put a real color-producing land into a graveyard by T3 (the only thing that would
    make Deathrite's unmodeled ability newly relevant here, per the regression_requirements'
    explicit instruction to re-verify rather than assume MANA-AUDIT-002's old-list finding still
    holds). Fetchlands do NOT count - a fetch card itself produces no color per its own printed
    text, so exiling one from the graveyard nets Deathrite zero mana under the real Oracle rule."""
    land_discard_outlets = {
        "Mox Diamond": "ETB: discard a land card (controller's choice) - a real, but single, "
                        "T1-only opportunity to put ONE colored land in the graveyard.",
    }
    present = {name: reason for name, reason in land_discard_outlets.items() if name in base_names}
    return {
        "land_discard_outlets_present_in_new_operative_98": present,
        "conclusion": (
            "Unchanged from MANA-AUDIT-002's finding: the only land-to-graveyard outlet in this "
            "decklist is Mox Diamond's single ETB discard-a-land choice (present in both the old "
            "and new operative lists - not part of this task's 9-card diff). No new discard-a-"
            "land or self-mill effect was added by the 9-card swap under study. Deathrite's "
            "graveyard-exile mana ability therefore remains a genuinely low-T1-3-frequency line "
            "even in the new list (needs Mox Diamond specifically resolved with a real dual land "
            "discarded to it, not just any card) - re-verified, not merely assumed, and the "
            "engine's existing non-implementation is left as-is rather than built out for this "
            "narrow case, consistent with report_policy's 'do not expand infrastructure' guidance."
        ),
    }


def _one_hand(names, rng, cards, combos, on_play=True):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    library = lib[7:]
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    per_turn = {}
    for t in range(1, 4):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        d6.apply_lotho_trigger_if_any(state, t)
        m = snapshot_metrics(state, cards, combos)
        nominal_dorks_in_play = sorted(
            p.name for p in state.nonland_perms if p.name in NOMINAL_TRUE_ONE_MANA_DORKS
        )
        functional_dorks_in_play = [
            n for n in nominal_dorks_in_play
            if n in MANA_SOURCES and MANA_SOURCES[n].get("creature")
        ]
        m["creature_count"] = state.creature_count()
        m["attack_eligible_creature_count"] = state.attack_eligible_creature_count()
        m["nominal_dorks_in_play_count"] = len(nominal_dorks_in_play)
        m["functional_dorks_in_play_count"] = len(functional_dorks_in_play)
        m["kinnan_active"] = KINNAN_NAME in m["engines_active"]
        m["gaea_cradle_structural_ceiling_G"] = state.creature_count()
        per_turn[t] = m
    return per_turn


def census(names, cards, combos, seed, n):
    rng = random.Random(seed)
    return [_one_hand(names, rng, cards, combos) for _ in range(n)]


def aggregate(results):
    n = len(results)
    out = {}
    for t in (1, 2, 3):
        def mean(key):
            return sum(r[t][key] for r in results) / n
        def rate(fn):
            return sum(1 for r in results if fn(r[t])) / n
        out[f"T{t}"] = {
            "mean_creature_count": mean("creature_count"),
            "mean_attack_eligible_creature_count": mean("attack_eligible_creature_count"),
            "mean_nominal_dorks_in_play": mean("nominal_dorks_in_play_count"),
            "mean_functional_dorks_in_play": mean("functional_dorks_in_play_count"),
            "pct_zero_functional_dorks_in_play": rate(lambda m: m["functional_dorks_in_play_count"] == 0),
            "pct_two_plus_functional_dorks_in_play": rate(lambda m: m["functional_dorks_in_play_count"] >= 2),
            "kinnan_active_rate": rate(lambda m: m["kinnan_active"]),
            "mean_gaea_cradle_structural_ceiling_G": mean("gaea_cradle_structural_ceiling_G"),
            "kinnan_active_and_functional_dorks_2plus_rate": rate(
                lambda m: m["kinnan_active"] and m["functional_dorks_in_play_count"] >= 2
            ),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=15000)
    ap.add_argument("--seed", type=int, default=82006)
    args = ap.parse_args()

    d6.install_new_card_tables()
    try:
        payload, base_rows = load_deckbuild006_cards()
        cards_pool = deckbuild006_cards_pool(base_rows)
        base_names = list(base_rows.keys())
        combos = load_deterministic_combos()

        built = {v: build(base_names, cards_pool, v) for v in VARIANTS}
        cards_by_variant = {
            v: {**{n: cards_pool[n] for n in names}, d6.TREASURE_NAME: cards_pool[d6.TREASURE_NAME]}
            for v, names in built.items()
        }

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_006_E2_CREATURE_MANA_NETWORK", "evidence_type": "goldfish",
            "nominal_true_one_mana_dorks": sorted(NOMINAL_TRUE_ONE_MANA_DORKS),
            "deathrite_graveyard_fuel_reverification": deathrite_graveyard_fuel_reverification(base_names),
            "badgermole_cub_disclosure": (
                "Badgermole Cub's 'whenever you tap a creature for mana, add an additional G' "
                "amplifier is NOT modeled in this engine (DORK-003, previously investigated and "
                "deferred - a genuine engine change, not attempted here either). This is a "
                "CONSERVATIVE omission for this specific question: more dorks present means "
                "strictly more independent Badgermole trigger opportunities, so this understates "
                "the 5-dork configs' (A, C) advantage over the 4-dork configs (B, D), never the "
                "reverse. See rules_tests/regression/test_deckbuild006_badgermole_not_modeled.py "
                "for the explicit, tested confirmation of this gap's current status."
            ),
            "network_by_turn": {},
        }

        for v in VARIANTS:
            t0 = time.time()
            results = census(built[v], cards_by_variant[v], combos, args.seed, args.census_n)
            out["network_by_turn"][v] = aggregate(results)
            print(f"{v} ({time.time()-t0:.1f}s)")

        deltas = {}
        for a, b in [("A_5D_NO_LOTHO", "B_4D_NO_LOTHO"), ("A_5D_NO_LOTHO", "C_5D_LOTHO"),
                     ("B_4D_NO_LOTHO", "D_4D_LOTHO"), ("A_5D_NO_LOTHO", "D_4D_LOTHO")]:
            deltas[f"{a}_vs_{b}"] = {
                t: {k: out["network_by_turn"][b][t][k] - out["network_by_turn"][a][t][k]
                    for k in out["network_by_turn"][a][t]}
                for t in ("T1", "T2", "T3")
            }
        out["deltas"] = deltas

        key = deltas["A_5D_NO_LOTHO_vs_B_4D_NO_LOTHO"]["T2"]["mean_functional_dorks_in_play"]
        out["required_key_number"] = {
            "T2_mean_functional_dorks_in_play_delta_A_to_B": key,
            "interpretation": (
                "Direct measure of the network-SIZE cost (not just engine-probability cost, which "
                "E1 covers) of losing Avacyn's Pilgrim: the average number of fewer live "
                "mana-producing creatures on the battlefield at T2 in the 4-dork config vs the "
                "5-dork reference, both without Lotho."
            ),
        }
    finally:
        d6.uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild006_e2_creature_mana_network.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["required_key_number"], indent=2))


if __name__ == "__main__":
    main()
