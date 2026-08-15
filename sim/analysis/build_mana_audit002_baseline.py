"""MANA-AUDIT-002 section D — baseline metrics for the CURRENT 27-land configuration.

Reuses run_opening_hand_census.py's run_one_hand/aggregate machinery unchanged (same policy,
same snapshot_metrics fields) rather than rebuilding a parallel census pipeline, and ADDS the
metrics this audit specifically asks for that the SOLO-002 census didn't compute: exact
hypergeometric opening-land-count distribution, 1-land-hand outcome breakdown, Mox Diamond/Chrome
Mox/Deathrite functional rates, and an explicit RESOURCE ACCESSIBLE vs REALIZED-BY-POLICY gap
metric per turn (this project's own T1-3 policy engine standing in for "actual resource use," per
assignment section H - "use the project's validated lightweight state model," not XMage's AI).
"""
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deterministic_combos, deck_provenance_fields, COMMANDERS  # noqa: E402
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics, classify_failure_mode  # noqa: E402
from run_opening_hand_census import run_one_hand, aggregate as census_aggregate  # noqa: E402
from mana_audit002_variants import all_cards_dict  # noqa: E402
from sim.validation.run_classification import load_frozen_deck  # noqa: E402

MANAAUDIT_DECKLIST_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-manaaudit002-v1.json"
CARDS_CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"


def load_manaaudit_deck_cards():
    """load_deck_cards() equivalent, but pointed at THIS task's minted frozen subject rather
    than opening_hand_model.py's hardcoded DECKLIST_PATH constant - same verification path
    (load_frozen_deck: hash match, non-provisional, no synthetic markers)."""
    payload = load_frozen_deck(MANAAUDIT_DECKLIST_PATH, CARDS_CACHE)
    cards_by_id = {}
    for p in CARDS_CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        cards_by_id[d["scryfall_id"]] = d
    rows = {}
    for c in payload["cards"]:
        card = cards_by_id[c["scryfall_id"]]
        rows[c["name"]] = {
            "name": c["name"], "type": card.get("type_line", ""), "text": card.get("oracle_text", "") or "",
            "mana_cost": card.get("mana_cost") or "", "cmc": card.get("mana_value") or 0,
        }
    return payload, rows


def exact_hypergeometric_land_distribution(deck_size, land_count, hand_size=7):
    """Exact P(exactly k lands in an opening hand_size draw), k=0..hand_size, closed-form
    (no sampling noise) - deck's actual land count and total size, generalizes across variants."""
    dist = {}
    for k in range(0, hand_size + 1):
        if k > land_count or (hand_size - k) > (deck_size - land_count):
            dist[k] = 0.0
            continue
        dist[k] = (math.comb(land_count, k) * math.comb(deck_size - land_count, hand_size - k)) / math.comb(deck_size, hand_size)
    return dist


def _one_land_outcome(hand, library, cards, on_play, rng, combos):
    """Classifies a 1-opening-land hand: does it have USABLE acceleration (a dork/rock/Mox that
    can actually be deployed off that one land), and does it then genuinely fail by T3 anyway?"""
    state = HandState(hand, library, on_play=on_play, rng=rng, cards=cards)
    for t in range(1, 4):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
    m3 = snapshot_metrics(state, cards, combos)
    fail = classify_failure_mode(m3, state, cards)
    used_accel = any(name in {"Chrome Mox", "Lotus Petal", "Mox Amber", "Mox Diamond", "Sol Ring",
                               "Mana Vault", "Avacyn's Pilgrim", "Birds of Paradise",
                               "Delighted Halfling", "Devoted Druid", "Elves of Deep Shadow",
                               "Noble Hierarch", "Elvish Spirit Guide"}
                      for (t, name, cls) in state.cast_log if t == 1)
    return {"used_t1_acceleration": used_accel, "genuinely_failed_by_t3": bool(fail),
            "final_lands": len(state.lands), "final_mana_t3": m3["total_mana"]}


def _mox_functional_rate(names, count, seed, cards, combos):
    """Fraction of hands where the named zero-mana accelerant is actually CAST by turn 3 under
    the greedy policy - distinct from merely being drawn (a hand that never draws it is 'not
    functional' the same as a hand that draws but can't/doesn't cast it - both are captured by
    checking the real cast_log, not hand membership)."""
    rng = random.Random(seed)
    hits = {n: 0 for n in names}
    for _ in range(count):
        lib = list(cards.keys())
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        state = HandState(hand, library, on_play=True, rng=rng, cards=cards)
        for t in range(1, 4):
            develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        cast_names = {name for (t, name, cls) in state.cast_log}
        for n in names:
            if n in cast_names:
                hits[n] += 1
    return {n: hits[n] / count for n in names}


def resource_accessible_vs_realized(results):
    """Per turn: mean RESOURCE ACCESSIBLE (turn_start_mana, this turn's total capacity) vs mean
    REALIZED-BY-POLICY (capacity minus what's left untapped after the greedy line finishes this
    turn = mana actually spent). The gap is capacity the deck-aware policy left on the table -
    NOT deck insufficiency, a policy-realization gap, kept explicitly distinct per the
    assignment's own instruction."""
    out = {}
    for t in (1, 2, 3):
        accessible = [r[t]["total_mana"] for r in results]
        leftover = [r[t]["mana_remaining_unused"] for r in results]
        realized = [a - l for a, l in zip(accessible, leftover)]
        n = len(results)
        out[str(t)] = {
            "mean_resource_accessible": sum(accessible) / n,
            "mean_realized_by_policy": sum(realized) / n,
            "mean_capacity_left_unused": sum(leftover) / n,
            "pct_hands_with_unused_capacity": sum(1 for l in leftover if l > 0) / n,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=42002)
    args = ap.parse_args()

    payload, base_cards = load_manaaudit_deck_cards()
    cards = all_cards_dict(base_cards)  # installs no new lands (baseline has none), but keeps a
    # single code path identical to variant runs for Section F
    combos = load_deterministic_combos()
    names = list(base_cards.keys())
    rng = random.Random(args.seed)

    t0 = time.time()
    results = [run_one_hand(names, rng, cards, combos, on_play=True) for _ in range(args.count)]
    elapsed = time.time() - t0
    agg = census_aggregate(results)

    land_dist = exact_hypergeometric_land_distribution(deck_size=98, land_count=27, hand_size=7)
    land_dist_grouped = {
        "0": land_dist[0], "1": land_dist[1], "2": land_dist[2], "3": land_dist[3],
        "4+": sum(land_dist[k] for k in range(4, 8)),
    }

    # 1-land opening hands (exact land count in OPENING 7, not post-development) - genuine subset
    one_land_outcomes = []
    rng2 = random.Random(args.seed + 1)
    attempts = 0
    target_n = 3000
    while len(one_land_outcomes) < target_n and attempts < target_n * 200:
        attempts += 1
        lib = names[:]
        rng2.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        n_lands = sum(1 for c in hand if "Land" in cards[c]["type"])
        if n_lands != 1:
            continue
        one_land_outcomes.append(_one_land_outcome(hand, library, cards, True, rng2, combos))
    one_land_n = len(one_land_outcomes)
    one_land_summary = {
        "sample_size": one_land_n,
        "usable_acceleration_rate": sum(1 for r in one_land_outcomes if r["used_t1_acceleration"]) / one_land_n,
        "genuine_failure_rate_by_t3": sum(1 for r in one_land_outcomes if r["genuinely_failed_by_t3"]) / one_land_n,
        "genuine_failure_rate_given_no_t1_acceleration": (
            sum(1 for r in one_land_outcomes if r["genuinely_failed_by_t3"] and not r["used_t1_acceleration"])
            / max(1, sum(1 for r in one_land_outcomes if not r["used_t1_acceleration"]))
        ),
        "genuine_failure_rate_given_used_t1_acceleration": (
            sum(1 for r in one_land_outcomes if r["genuinely_failed_by_t3"] and r["used_t1_acceleration"])
            / max(1, sum(1 for r in one_land_outcomes if r["used_t1_acceleration"]))
        ),
    }

    mox_rates = _mox_functional_rate(
        ["Chrome Mox", "Mox Diamond", "Deathrite Shaman"], count=8000, seed=args.seed + 2,
        cards=cards, combos=combos,
    )

    out = {
        **deck_provenance_fields(payload),
        "phase": "MANA_AUDIT_002_SECTION_D",
        "evidence_type": "goldfish",
        "section": "D_baseline_metrics_current_27_lands",
        "config_name": "A_CURRENT_27",
        "sample_count": args.count,
        "seed": args.seed,
        "elapsed_seconds": elapsed,
        "opening_hand_land_count_distribution_exact_hypergeometric": land_dist_grouped,
        "opening_hand_land_count_distribution_exact_full": land_dist,
        "primary_outcomes": agg["primary_outcomes"],
        "primary_table": agg["primary_table"],
        "failure_table": agg["failure_table"],
        "one_land_hand_outcomes": one_land_summary,
        "mox_diamond_chrome_mox_deathrite_functional_rates": {
            "note": "Fraction of hands where the card is actually CAST (not merely drawn/kept) "
                    "by T3 under the deck-aware greedy policy - a CASTING-reliability rate, not "
                    "(for Deathrite Shaman specifically) a MANA-ABILITY-usage rate. Section B's "
                    "special-case finding already established Deathrite's mana ability is "
                    "structurally dead in this exact 98-card list (zero basic land cards to "
                    "exile) - the rate below is Deathrite's rate of being cast as a 1/2 creature "
                    "body only, included for completeness of the section D dork-reliability "
                    "table, not as evidence its mana ability ever functions.",
            "rates": mox_rates,
        },
        "resource_accessible_vs_realized_by_policy": resource_accessible_vs_realized(results),
        "resource_accessible_vs_realized_note": (
            "RESOURCE ACCESSIBLE = mean total_mana capacity this turn (right after the land drop, "
            "before any spell decisions) - the primary mana-audit metric per the assignment. "
            "REALIZED-BY-POLICY = capacity minus what's left untapped after this project's own "
            "validated T1-3 greedy policy finishes its turn (this project's line-level equivalent "
            "of 'actual resource use', standing in for a generic XMage AI per assignment section "
            "H's own instruction to prefer the validated lightweight state model over expensive "
            "XMage runs). A gap here is a POLICY realization gap (the greedy line didn't spend "
            "everything available), not proof the mana base itself is short - kept explicitly "
            "distinct from mana INSUFFICIENCY, which mana_2plus/3plus/all_wubg failures measure."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mana_audit_002_baseline.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({args.count} hands in {elapsed:.1f}s)")
    print("land_dist:", land_dist_grouped)
    print("one_land_summary:", one_land_summary)
    print("mox_rates:", mox_rates)
    print("resource gap T1-3:", out["resource_accessible_vs_realized_by_policy"])


if __name__ == "__main__":
    main()
