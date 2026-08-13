"""SIM-001 SOLO-004 — opener-feature + multi-objective-outcome dataset generator.

For each random seven, joins:
  - opener-visible features (opening_hand_features.py) - land/accel/engine/tutor/interaction/
    structural facts computable from the 7 cards + known deck construction only;
  - the GREEDY-POLICY-REALIZED T1-T3 outcome vector, spanning every dimension SOLO-004 section 1
    requires (development, agency, commander conversion, engine functionality, conversion,
    resources) - built almost entirely from the already-validated SOLO-003R trajectory_metrics.py
    functions (t1_metrics/t2_quality_metrics/t3_strong_state_metrics/compounding_state_metrics/
    tymna_attack_capacity/thrasios_productivity/classify_trajectory_failure/trajectory_family_
    tags), plus a small number of genuinely new fields section 1 asks for that no prior phase
    computed (T2 premium engine, T2 2+ actions, live PAID interaction specifically, an approximate
    protection-agency signal, Cradle >=4, and "card investment" - cards spent by T3 relative to
    the starting 7).

Per SOLO-004's explicit "IMPORTANT CONSTRAINT": the greedy-realized outcome is NOT the only
signal recorded. `--achievable` additionally runs the bounded T1-T3 achievable search
(achievable_search.py) and records BOTH policy_realized and best_known_achievable for its target
list, so a later derivation step can distinguish "this hand is actually weak" from "the greedy
policy just sequenced it badly." The achievable search is ~20x more expensive per hand (matching
the SOLO-003R precedent of using a smaller sample for it), so it is opt-in and typically run at a
smaller --count than the main greedy-only pass.

Output is JSONL (one compact JSON object per hand) rather than one giant JSON array/object - at
100k+ hands x ~150 fields, a single pretty-printed JSON document would be unwieldy to write, read,
or diff. A small provenance/summary JSON is written alongside it.
"""
import argparse
import gzip
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opening_hand_model import (
    load_deck_cards, load_deterministic_combos, deck_provenance_fields, print_run_banner,
    PREMIUM_ONE_DROP_ENGINES,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY
from opening_hand_metrics import snapshot_metrics
from opening_hand_features import raw_hand_features, t1_executable_features_from_state, derive_structural_features
from achievable_search import compute_policy_realized_and_best_known_achievable, TARGETS as ACHIEVABLE_TARGETS
import trajectory_metrics as tm

REPO_ROOT = Path(__file__).resolve().parents[2]


def _new_outcome_fields(state, m1, m2, m3, t3s, comp):
    cast_t2 = [(t, n, c) for (t, n, c) in state.cast_log if t == 2]
    t2_premium_engine = any(n in PREMIUM_ONE_DROP_ENGINES for (t, n, c) in cast_t2)
    t2_actions_2plus = len(cast_t2) >= 2
    live_paid_interaction = m3["has_live_interaction"] and not m3["free_or_alt_cost_interaction_live"]
    # Protection agency: approximate signal (disclosed, section 18's "conditional interaction
    # must retain its real conditions" standard applies) - a tutor that can FETCH a protection
    # spell, OR a live interaction card already in hand (this deck's whole interaction suite -
    # Force of Will/Fierce Guardianship/Flusterstorm/Silence/Swan Song/etc. - functions
    # protectively for the combo/commander plan, so "has live interaction" is a reasonable proxy
    # for "has protection agency" in THIS decklist specifically, not a general claim).
    protection_agency = ("protection" in m3["tutor_targets_accessible"]) or m3["has_live_interaction"]
    return {
        "t2_premium_engine_cast": t2_premium_engine,
        "t2_actions_2plus": t2_actions_2plus,
        "t3_live_paid_interaction": live_paid_interaction,
        "t3_protection_agency": protection_agency,
        "t3_cradle_4plus": m3["cradle_output_if_deployed"] >= 4,
        "cards_invested_by_t3": 7 - m3["cards_in_hand"],
    }


def run_one_hand(names, rng, cards, combos, on_play, run_achievable, max_turn=3):
    lib = names[:]
    rng.shuffle(lib)
    hand = lib[:7]
    lib_after_deal = lib[7:]

    raw = raw_hand_features(hand, lib_after_deal, cards)

    state = HandState(hand, lib_after_deal, on_play=on_play, rng=rng, cards=cards)
    snaps = {}
    for t in range(1, max_turn + 1):
        develop_turn(state, cards, priority_order=DEFAULT_PRIORITY)
        snaps[t] = snapshot_metrics(state, cards, combos)
        if t == 1:
            t1 = t1_executable_features_from_state(state, cards)
    m1, m2, m3 = snaps[1], snaps[2], snaps[3]

    t1m = tm.t1_metrics(state, cards, m1)
    t2q = tm.t2_quality_metrics(state, cards, m2)
    t3s = tm.t3_strong_state_metrics(state, cards, m3)
    comp = tm.compounding_state_metrics(state, cards, m3)
    tymna = tm.tymna_attack_capacity(state, cards, None)
    thras = tm.thrasios_productivity(state, cards, m3)
    outcome_tags, causal_tags = tm.classify_trajectory_failure(m1, m2, m3, state, cards)
    family_tags = tm.trajectory_family_tags(state, cards, m1, m2, m3)
    extra = _new_outcome_fields(state, m1, m2, m3, t3s, comp)

    row = {}
    row.update({f"opener__{k}": v for k, v in raw.items()})
    row.update({f"opener__{k}": v for k, v in t1.items()})
    row.update({f"opener__{k}": v for k, v in derive_structural_features(raw, t1).items()})
    row["opening_hand_land_count"] = raw["land_count"]
    row.update({f"out_t1__{k}": v for k, v in t1m.items()})
    row.update({f"out_t2__{k}": v for k, v in t2q.items()})
    row.update({f"out_t3__{k}": v for k, v in t3s.items()})
    row.update({f"out_comp__{k}": v for k, v in comp.items()})
    row.update({f"out_tymna__{k}": v for k, v in tymna.items()})
    row.update({f"out_thras__{k}": v for k, v in thras.items()})
    row.update({f"out_extra__{k}": v for k, v in extra.items()})
    row["outcome_tags"] = outcome_tags
    row["causal_tags"] = causal_tags
    row["family_tags"] = family_tags
    row["out__deterministic_win_available"] = m3["deterministic_win_available"]
    row["out__deterministic_win_protected"] = m3["deterministic_win_protected"]
    row["out__one_action_from_verified_win"] = m3["one_action_from_verified_win"]
    row["out__tutor_castable_t3"] = m3["tutor_castable"]
    row["out__mana_shortfall_t3"] = m3["mana_shortfall"]
    row["out__total_mana_capacity_t3"] = m3["total_mana"]
    row["out__all_wubg_t3"] = m3["all_wubg"]
    row["out__cards_in_hand_t3"] = m3["cards_in_hand"]
    row["out__temporary_resources_consumed_t3"] = m3["temporary_resources_consumed"]

    if run_achievable:
        policy_realized, best_known, lines = compute_policy_realized_and_best_known_achievable(
            hand, lib_after_deal, on_play, cards, combos, max_turn=max_turn
        )
        row.update({f"achv_realized__{k}": v for k, v in policy_realized.items()})
        row.update({f"achv_best_known__{k}": v for k, v in best_known.items()})
        row["achv_lines_explored"] = lines

    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seat", choices=["play", "draw"], default="play")
    ap.add_argument("--achievable", action="store_true", help="also run the bounded achievable search per hand (~20x slower)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print_run_banner()
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    combos = load_deterministic_combos()
    on_play = args.seat == "play"
    rng = random.Random(args.seed)

    out_path = Path(args.out) if args.out else (
        REPO_ROOT / "results" / "solo_baseline" / f"solo004_opening_hand_dataset_{args.seat}"
        f"{'_achievable' if args.achievable else ''}.jsonl.gz"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # gzip directly: the raw JSONL routinely exceeds GitHub's 100MB file limit at 100k+ rows (the
    # repeated key names dominate size, so gzip compresses ~40x) - see .gitignore. Fully
    # regeneratable from --seed regardless, so nothing is lost by not keeping the raw file.
    t0 = time.time()
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        for i in range(args.count):
            row = run_one_hand(names, rng, cards, combos, on_play, args.achievable)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if (i + 1) % 10000 == 0:
                elapsed = time.time() - t0
                print(f"  {i + 1}/{args.count} ({(i + 1) / elapsed:.1f} hands/sec)", file=sys.stderr)
    elapsed = time.time() - t0

    summary = {
        **deck_provenance_fields(payload),
        "phase": "SIM_001_SOLO_004_DATASET",
        "sample_count": args.count,
        "seed": args.seed,
        "seat": args.seat,
        "on_play": on_play,
        "achievable_search_included": args.achievable,
        "elapsed_seconds": elapsed,
        "hands_per_second": args.count / elapsed,
        "dataset_file": str(out_path),
    }
    summary_path = Path(str(out_path).replace(".jsonl.gz", ".summary.json"))
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({args.count} hands in {elapsed:.1f}s, {args.count / elapsed:.1f} hands/sec)")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
