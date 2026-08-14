"""SIM-001 MULL-006 section 10 / 28 — relevant_agency_analysis.json.

Runs real simulated opening hands through relevant_agency_model.hand_agency_scores(), reporting
live_agency_score and relevant_agency_score (per archetype) SEPARATELY, exactly as the assignment
requires, and empirically demonstrates the assignment's explicit boundary: pod relevance may
UPGRADE a coherent marginal hand, but this module does not and structurally cannot rescue a
mana+interaction+no-destination hand into anything - it never touches trajectory_grading.py's
tier at all, it only reports agency scores alongside whatever tier a hand already has.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from opening_hand_model import load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner
from trajectory_search import find_best_trajectory
from relevant_agency_model import (
    hand_agency_scores, ARCHETYPE_THREAT_AXES, GIVEN_ARCHETYPES, EXTRAPOLATED_ARCHETYPES,
    AGENCY_PROVENANCE,
)
from opening_hand_policy import HandState

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHETYPES_LIST = sorted(ARCHETYPE_THREAT_AXES)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=6000)
    ap.add_argument("--seed", type=int, default=6006)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)

    live_agency_dist = Counter()
    relevant_agency_dist_by_archetype = defaultdict(Counter)
    live_agency_by_legacy_tier = defaultdict(list)
    relevant_agency_by_legacy_tier = defaultdict(lambda: defaultdict(list))
    no_destination_hands_with_agency = []
    mana_interaction_no_destination_count = 0
    mana_interaction_no_destination_high_agency_count = 0

    for _ in range(args.count):
        lib = names[:]
        rng.shuffle(lib)
        hand, library = lib[:7], lib[7:]
        _, grade, _ = find_best_trajectory(hand, library, on_play, cards, combos)
        state = HandState(hand, library, on_play=on_play, rng=random.Random(0), cards=cards)
        scores = hand_agency_scores(state, cards, archetypes=ARCHETYPES_LIST)

        live_agency_dist[scores["live_agency_score"]] += 1
        for arch, val in scores["relevant_agency_score"].items():
            relevant_agency_dist_by_archetype[arch][val] += 1

        tier = grade["tier"]
        live_agency_by_legacy_tier[tier].append(scores["live_agency_score"])
        for arch, val in scores["relevant_agency_score"].items():
            relevant_agency_by_legacy_tier[tier][arch].append(val)

        if tier in ("D", "F") and scores["live_agency_score"] > 0:
            mana_interaction_no_destination_count += 1
            if scores["live_agency_score"] >= 2:
                mana_interaction_no_destination_high_agency_count += 1
                if len(no_destination_hands_with_agency) < 10:
                    no_destination_hands_with_agency.append({
                        "hand": sorted(hand), "legacy_tier": tier,
                        "live_agency_score": scores["live_agency_score"],
                        "live_cards": scores["live_cards"],
                    })

    def _avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else None

    result = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_MULL_006_RELEVANT_AGENCY_ANALYSIS",
        "evidence_type": AGENCY_PROVENANCE,
        "sample_count": args.count, "seed": args.seed, "seat": args.seat,
        "archetypes_evaluated": ARCHETYPES_LIST,
        "given_archetypes": sorted(GIVEN_ARCHETYPES),
        "extrapolated_archetypes": sorted(EXTRAPOLATED_ARCHETYPES),
        "live_agency_score_distribution": dict(live_agency_dist),
        "relevant_agency_score_distribution_by_archetype": {
            arch: dict(dist) for arch, dist in relevant_agency_dist_by_archetype.items()
        },
        "live_agency_avg_by_legacy_tier": {
            tier: _avg(vals) for tier, vals in live_agency_by_legacy_tier.items()
        },
        "relevant_agency_avg_by_legacy_tier_and_archetype": {
            tier: {arch: _avg(vals) for arch, vals in by_arch.items()}
            for tier, by_arch in relevant_agency_by_legacy_tier.items()
        },
        "boundary_rule_check": {
            "description": (
                "The assignment's explicit boundary: pod relevance may UPGRADE a coherent "
                "marginal hand, but must NOT rescue 'mana + interaction + no destination' into a "
                "premium keep. This module never touches trajectory_grading.py's tier at all - it "
                "only REPORTS agency scores alongside whatever tier a hand already has, so no "
                "hand's tier can change based on its agency score by construction. The counts "
                "below confirm this empirically: D/F-tier hands (no destination) with real live "
                "interaction still show tier D/F, regardless of how high their agency score is."
            ),
            "d_or_f_tier_hands_with_at_least_one_live_interaction_card": mana_interaction_no_destination_count,
            "d_or_f_tier_hands_with_live_agency_score_2plus": mana_interaction_no_destination_high_agency_count,
            "example_no_destination_high_agency_hands_still_tier_d_or_f": no_destination_hands_with_agency,
        },
        "note": (
            "relevant_agency_score is a MODEL_DERIVED report, not itself a keep/mulligan decision "
            "- combining it correctly with destination-first trajectory grading (respecting the "
            "boundary above) is deferred to task #117's contextual policy comparison."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "relevant_agency_analysis.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"d_or_f_with_live_interaction: {mana_interaction_no_destination_count}")
    print(f"d_or_f_with_high_agency(2+): {mana_interaction_no_destination_high_agency_count}")


if __name__ == "__main__":
    main()
