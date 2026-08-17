"""SIM-DECKBUILD-004 — B4-B7 ablation census (reuses E1's census machinery, no new engine code).

Cheap reuse of build_deckbuild004_e1_early_cost.py's census_metrics/aggregate_census for the four
single-card-revert ablations, directly serving the assignment's own required "Ablations" final-
report section (marginal_contribution_each_card / whether_card_is_redundant).
"""
import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build  # noqa: E402
from build_deckbuild004_e1_early_cost import census_metrics, aggregate_census  # noqa: E402

ABLATIONS = ["B4_NO_NEOFORM", "B5_NO_SPEAKER", "B6_NO_TALION", "B7_NO_SEEDBORN"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census-n", type=int, default=15000)
    ap.add_argument("--seed", type=int, default=91004)
    args = ap.parse_args()

    payload, base_cards = load_deck_cards()
    cards_pool = all_cards_dict(base_cards)
    install_new_card_tables()
    base_names = list(base_cards.keys())
    combos = load_deterministic_combos()

    try:
        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_004_ABLATION_CENSUS", "evidence_type": "goldfish",
            "note": "Reuses E1's exact census methodology for B4-B7 (each = B3 minus one "
                    "addition, 97 cards) - directly comparable to B3_FULL_PACKAGE and "
                    "B0_BASELINE's own census figures already in deckbuild004_e1_early_cost.json.",
            "census_by_variant": {},
        }
        for v in ABLATIONS:
            t0 = time.time()
            names = build(base_names, cards_pool, v)
            cards = {n: cards_pool[n] for n in names}
            results = census_metrics(names, cards, combos, args.seed, args.census_n)
            out["census_by_variant"][v] = aggregate_census(results)
            print(f"{v} ({time.time()-t0:.1f}s)")
    finally:
        uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild004_ablation_census.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
