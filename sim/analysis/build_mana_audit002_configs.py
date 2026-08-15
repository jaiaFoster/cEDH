"""MANA-AUDIT-002 sections E+F — mulligan sim + counterfactual mana-base configs.

For the baseline (CURRENT 27) plus every Section F counterfactual, runs BOTH:
  - D-style metrics (census: run_opening_hand_census.run_one_hand/aggregate, reused unchanged)
  - E-style metrics (contextual London mulligan sim using gated_model - the SAME single reference
    architecture seat_pod_matrix.json already established as this project's one-fixed-rule
    comparison baseline, reused unchanged from run_contextual_london_mulligan_sim.py)
for the SAME variant card pool, so every config is graded by the identical methodology.

Land-count variants (26/28/29) deliberately change total deck size (a neutral proxy land,
"Command Tower (proxy copy)", is added/removed rather than swapping a specific nonland) - per the
assignment's own instruction to report land count's PURE MARGINAL benefit "independent of which
nonland is cut." This is NOT a legal 98-card decklist for those 3 configs; it is a controlled
isolation of land count alone, explicitly disclosed, never presented as a buildable list.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deterministic_combos, deck_provenance_fields  # noqa: E402
from run_opening_hand_census import run_one_hand, aggregate as census_aggregate  # noqa: E402
from run_contextual_london_mulligan_sim import make_contextual_keep_policy, run_policy, aggregate as mull_aggregate  # noqa: E402
from mana_audit002_variants import all_cards_dict, build_variant  # noqa: E402
from build_mana_audit002_baseline import load_manaaudit_deck_cards, exact_hypergeometric_land_distribution  # noqa: E402

PROXY_LAND = "Command Tower (proxy copy)"

CONFIGS = {
    "A_CURRENT_27": {"add": [], "remove": [], "land_count": 27, "deck_size": 98,
                      "desc": "Baseline - the exact current 98-card list, unchanged."},

    # ---- fetch density ----
    "B_PLUS_SCALDING_TARN_MINUS_CITY_OF_TRAITORS": {
        "add": ["Scalding Tarn"], "remove": ["City of Traitors"], "land_count": 27, "deck_size": 98,
        "desc": "+8th fetch (Scalding Tarn), -City of Traitors."},
    "C_PLUS_SCALDING_TARN_MINUS_TALON_GATES": {
        "add": ["Scalding Tarn"], "remove": ["Talon Gates of Madara"], "land_count": 27, "deck_size": 98,
        "desc": "+8th fetch (Scalding Tarn), -Talon Gates of Madara."},
    "D_PLUS_SCALDING_TARN_MINUS_SHIFTING_WOODLAND": {
        "add": ["Scalding Tarn"], "remove": ["Shifting Woodland"], "land_count": 27, "deck_size": 98,
        "desc": "+8th fetch (Scalding Tarn), -Shifting Woodland."},
    "E_PLUS_ARID_MESA_MINUS_CITY_OF_TRAITORS": {
        "add": ["Arid Mesa"], "remove": ["City of Traitors"], "land_count": 27, "deck_size": 98,
        "desc": "+Arid Mesa (W/R fetch, reaches Savannah/Scrubland/Tundra via its W half only), "
                "-City of Traitors."},
    "F_PLUS_BLOODSTAINED_MIRE_MINUS_TALON_GATES": {
        "add": ["Bloodstained Mire"], "remove": ["Talon Gates of Madara"], "land_count": 27, "deck_size": 98,
        "desc": "+Bloodstained Mire (B/R fetch, reaches Bayou/Scrubland/Underground Sea via its B "
                "half only), -Talon Gates of Madara."},

    # ---- rainbow candidates ----
    "G_RAINBOW_GEMSTONE_MINE_MINUS_CITY_OF_TRAITORS": {
        "add": ["Gemstone Mine"], "remove": ["City of Traitors"], "land_count": 27, "deck_size": 98,
        "desc": "+Gemstone Mine (3-use rainbow, modeled as flat rainbow within the T1-3 horizon), "
                "-City of Traitors."},
    "H_RAINBOW_TARNISHED_CITADEL_MINUS_TALON_GATES": {
        "add": ["Tarnished Citadel"], "remove": ["Talon Gates of Madara"], "land_count": 27, "deck_size": 98,
        "desc": "+Tarnished Citadel (rainbow-for-3-life, like City of Brass/Mana Confluence but "
                "pricier), -Talon Gates of Madara."},
    "I_RAINBOW_FORBIDDEN_ORCHARD_MINUS_SHIFTING_WOODLAND": {
        "add": ["Forbidden Orchard"], "remove": ["Shifting Woodland"], "land_count": 27, "deck_size": 98,
        "desc": "+Forbidden Orchard (free rainbow, real downside - opponent token every tap - "
                "NOT modeled in this solo/no-opponent engine, qualitative-only), -Shifting Woodland."},

    # ---- land count (pure marginal benefit - neutral proxy land, deck size deliberately changes) ----
    "J_LAND_COUNT_26": {"add": [], "remove": ["Talon Gates of Madara"], "land_count": 26, "deck_size": 97,
                         "desc": "26 lands: -1 land (Talon Gates, the weakest single land per "
                                 "Section B's own finding), no backfill. Deck size drops to 97 - "
                                 "an isolation of land count's pure marginal cost, not a legal list."},
    "K_LAND_COUNT_28": {"add": [PROXY_LAND], "remove": [], "land_count": 28, "deck_size": 99,
                         "desc": "28 lands: +1 neutral rainbow proxy land, no nonland cut. Deck "
                                 "size rises to 99 - isolates land count's pure marginal benefit "
                                 "from any specific nonland-cut choice, per the assignment's own "
                                 "instruction; not a legal 98-card list."},
    "L_LAND_COUNT_29": {"add": [PROXY_LAND, PROXY_LAND + " 2"], "remove": [], "land_count": 29, "deck_size": 100,
                         "desc": "29 lands: +2 neutral rainbow proxy lands, no nonland cut. Deck "
                                 "size rises to 100 - same pure-marginal isolation as K."},

    # ---- fast-mana ablations (both = baseline A; these cover the other 3 combinations) ----
    "M_FASTMANA_TOMB_ONLY": {"add": [], "remove": ["City of Traitors"], "land_count": 26, "deck_size": 97,
                              "desc": "Ancient Tomb kept, City of Traitors removed, no backfill."},
    "N_FASTMANA_CITY_ONLY": {"add": [], "remove": ["Ancient Tomb"], "land_count": 26, "deck_size": 97,
                              "desc": "City of Traitors kept, Ancient Tomb removed, no backfill."},
    "O_FASTMANA_NEITHER": {"add": [], "remove": ["Ancient Tomb", "City of Traitors"], "land_count": 25, "deck_size": 96,
                            "desc": "Both fast-mana lands removed, no backfill."},

    # ---- utility-land ablations ----
    "P_ABLATE_SHIFTING_WOODLAND": {"add": [], "remove": ["Shifting Woodland"], "land_count": 26, "deck_size": 97, "desc": "Shifting Woodland removed."},
    "Q_ABLATE_TALON_GATES": {"add": [], "remove": ["Talon Gates of Madara"], "land_count": 26, "deck_size": 97, "desc": "Talon Gates of Madara removed."},
    "R_ABLATE_MINAMO": {"add": [], "remove": ["Minamo, School at Water's Edge"], "land_count": 26, "deck_size": 97, "desc": "Minamo removed."},
    "S_ABLATE_BOSEIJU": {"add": [], "remove": ["Boseiju, Who Endures"], "land_count": 26, "deck_size": 97, "desc": "Boseiju removed."},
    "T_ABLATE_OTAWARA": {"add": [], "remove": ["Otawara, Soaring City"], "land_count": 26, "deck_size": 97, "desc": "Otawara removed."},
}


def _install_proxy_land(cards_pool):
    import opening_hand_model as ohm
    cards_pool[PROXY_LAND] = {"name": PROXY_LAND, "type": "Land", "text": "", "mana_cost": "", "cmc": 0}
    cards_pool[PROXY_LAND + " 2"] = {"name": PROXY_LAND + " 2", "type": "Land", "text": "", "mana_cost": "", "cmc": 0}
    ohm.LAND_COLOR_SETS[PROXY_LAND] = set(ohm.COLORS)
    ohm.LAND_COLOR_SETS[PROXY_LAND + " 2"] = set(ohm.COLORS)


def run_config(name, spec, base_names, cards_pool, census_n, mull_n, seed):
    variant_names = build_variant(base_names, cards_pool, add=spec["add"], remove=spec["remove"])
    assert len(variant_names) == spec["deck_size"], (name, len(variant_names), spec["deck_size"])
    land_ct = sum(1 for n in variant_names if "Land" in cards_pool[n]["type"])
    assert land_ct == spec["land_count"], (name, land_ct, spec["land_count"])

    combos = load_deterministic_combos()
    rng = random.Random(seed)
    t0 = time.time()
    census_results = [run_one_hand(variant_names, rng, cards_pool, combos, on_play=True) for _ in range(census_n)]
    census_elapsed = time.time() - t0
    census_agg = census_aggregate(census_results)

    policy = make_contextual_keep_policy("gated")
    mull_results, mull_elapsed = run_policy(policy, mull_n, seed + 1, "play", cards_pool, combos)
    mull_agg = mull_aggregate(mull_results)

    land_dist = exact_hypergeometric_land_distribution(spec["deck_size"], spec["land_count"], hand_size=7)
    land_dist_grouped = {
        "0": land_dist[0], "1": land_dist[1], "2": land_dist[2], "3": land_dist[3],
        "4+": sum(land_dist[k] for k in range(4, 8)),
    }

    return {
        "description": spec["desc"], "land_count": spec["land_count"], "deck_size": spec["deck_size"],
        "not_a_legal_98_card_list": spec["deck_size"] != 98,
        "added_cards": spec["add"], "removed_cards": spec["remove"],
        "opening_hand_land_count_distribution": land_dist_grouped,
        "census_sample_size": census_n, "census_elapsed_seconds": census_elapsed,
        "primary_outcomes": census_agg["primary_outcomes"],
        "primary_table": census_agg["primary_table"],
        "failure_table": census_agg["failure_table"],
        "mulligan_sample_size": mull_n, "mulligan_elapsed_seconds": mull_elapsed,
        "mulligan_gated_model": mull_agg,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=12000)
    ap.add_argument("--mull-n", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=51002)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    payload, base_cards = load_manaaudit_deck_cards()
    cards_pool = all_cards_dict(base_cards)
    _install_proxy_land(cards_pool)
    base_names = list(base_cards.keys())

    configs_to_run = {k: v for k, v in CONFIGS.items() if args.only is None or k in args.only}

    out = {
        **deck_provenance_fields(payload),
        "phase": "MANA_AUDIT_002_SECTIONS_E_F",
        "evidence_type": "goldfish",
        "method_note": (
            "Every config uses the SAME methodology: run_opening_hand_census's keep-everything "
            "T1-3 census (D-style metrics) plus run_contextual_london_mulligan_sim's gated_model "
            "contextual London mulligan simulation (E-style metrics, the same single reference "
            "architecture seat_pod_matrix.json already used project-wide for one-fixed-rule "
            "comparisons). Land-count configs (J/K/L) deliberately change total deck size via a "
            "neutral proxy land rather than swapping a specific nonland - see module docstring."
        ),
        "gated_model_note": (
            "gated_model is used as Section E/F's single mulligan-decision architecture, not "
            "because MULL-006 declared it correct (task #113 explicitly declined to assert any "
            "of its four architectures correct) - reused here for exactly the reason "
            "seat_pod_matrix.json already reused it: comparing many configs needs one fixed "
            "grading rule so 'the same hand's recommendation changed' is well-defined."
        ),
        "configs": {},
    }

    for name, spec in configs_to_run.items():
        t0 = time.time()
        result = run_config(name, spec, base_names, cards_pool, args.census_n, args.mull_n, args.seed)
        out["configs"][name] = result
        print(f"{name}: land={spec['land_count']} deck_size={spec['deck_size']} "
              f"({time.time()-t0:.1f}s) t3_2plus_engines={result['primary_outcomes'].get('t3_2plus_engines'):.4f} "
              f"S_or_A={result['mulligan_gated_model']['fraction_tier_S_or_A']:.4f} "
              f"D_or_F={result['mulligan_gated_model']['fraction_tier_D_or_F']:.4f}")

    out_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_configs.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
