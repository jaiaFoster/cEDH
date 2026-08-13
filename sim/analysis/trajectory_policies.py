"""SIM-001 MULL-005 — TRAJECTORY_MACHINE / TRAJECTORY_TREE / TRAJECTORY_SIMPLE keep policies.

Three policies at decreasing cost and increasing human-usability, mirroring SOLO-004's
policy_machine_optimal / policy_tree_depth4 / policy_simple_rules pattern but built on trajectory
tier instead of a multi-objective composite score - the whole point of MULL-005 being that a
hand's value is what T1-T3 LINE it can reach, not which resource-presence features it happens to
have.

  TRAJECTORY_MACHINE - the ceiling: runs the actual bounded trajectory search
    (trajectory_search.find_best_trajectory) and keeps iff the best tier clears the hand-size-
    specific threshold derived in derive_hand_size_trajectory_thresholds.py (mull005_hand_size_
    thresholds.json, assumed-mulligan-card-cost=1.0 - a disclosed, moderate point on that
    sensitivity sweep, not a claimed "true" cost). Not memorizable by a human pilot.

  TRAJECTORY_TREE - a shallow (depth<=4) decision tree fit on OPENER-VISIBLE FEATURES ONLY to
    predict TRAJECTORY_MACHINE's label at hand size 7, using mull005_trajectory_dataset_{play,
    draw}.jsonl.gz (which already has trajectory_best__tier per hand, so this reuses the existing
    dataset rather than re-running the search). Fit lives in fit_trajectory_tree_policy.py; this
    module just defines the callable shape shared with SIMPLE.

  TRAJECTORY_SIMPLE - <=10 human-memorizable rules, each traced to a specific finding already on
    record from this phase (see inline citations), directly encoding MULL-005's two corrections
    over SOLO-004's SIMPLE_RULES:
      (A) acceleration only matters WITH a destination (mull005_accel_without_payoff_analysis.json:
          truly-stranded 2+-accel hands hit Tier D/F 58.8% of the time, vs 18.3% baseline) - no
          unconditional "2+ accel = keep" or "has_sol_ring = keep" rule here.
      (B) a T1 creature dork enabling a T2 engine is a premium (Tier A) line
          (mull005_tutor_dork_analysis.json: dork_to_engine reaches Tier A 48.6% of the time it
          fires) - NOT downgraded merely because the creature can't tap T1.
    Tutor economics are read PER-CARD (mull005_tutor_dork_analysis.json): only the four CMC1
    tutors (Vampiric Tutor, Enlightened Tutor, Imperial Seal, Crop Rotation) get any keep credit
    (~25-27% reach a T2 engine outright), never a blanket "has_tutor_card" signal - CMC2+ tutors
    convert to a T2 engine only 7-12% of the time and are NOT a keep signal on their own.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CHEAP_TUTORS_WITH_REAL_T2_CONVERSION = {
    "Vampiric Tutor", "Enlightened Tutor", "Imperial Seal", "Crop Rotation",
}  # CMC1, ~25-27% tutor_to_t2_engine in mull005_tutor_dork_analysis.json; every other tutor in
   # this deck is CMC2+ and converts to a T2 engine only 7-12% of the time - not a keep signal here.

TIER_RANK = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}


def _load_thresholds(assumed_cost="1.0"):
    path = REPO_ROOT / "results" / "solo_baseline" / "mull005_hand_size_thresholds.json"
    data = json.loads(path.read_text())
    table = data["keep_thresholds_by_assumed_mulligan_card_cost"][assumed_cost]
    return {int(size): row["keep_at_or_above_tier"] for size, row in table.items()}


_THRESHOLDS = None


def _thresholds():
    global _THRESHOLDS
    if _THRESHOLDS is None:
        _THRESHOLDS = _load_thresholds()
    return _THRESHOLDS


def trajectory_machine_policy(hand, library, on_play, cards, combos):
    """The reference/ceiling policy - keep iff the bounded search's best-known trajectory clears
    this hand size's keep threshold (assumed mulligan-card-cost=1.0, see module docstring)."""
    from trajectory_search import find_best_trajectory

    hand_size = len(hand)
    thresholds = _thresholds()
    keep_tier = thresholds.get(hand_size)
    if keep_tier is None:
        keep_tier = "D"  # sizes outside the derived 7/6/5/4 table: fall back to "ship only F"
    _, best, _ = find_best_trajectory(hand, library, on_play, cards, combos)
    return TIER_RANK[best["tier"]] <= TIER_RANK[keep_tier]


def structural_hand_grade(feats):
    """The same rule ladder as trajectory_simple_policy(), but returning a labeled grade + reason
    instead of a bare bool - this is the "structural confidence" half of MULL-005's later pod-
    conditioning overlay (which pairs a REAL, simulation-derived structural grade with a SEPARATE,
    non-simulated pod confidence - see the assignment's explicit two-confidence-label requirement).
    Grades: SNAP_KEEP (premium T1), CONDITIONAL_KEEP (a real trajectory, but not guaranteed -
    the ~56-92% precision band measured against TRAJECTORY_MACHINE, see module-level validation
    note in the write-up), MARGINAL (borderline - land-floor cases with no other qualifying
    signal), SHIP (fails every keep test)."""
    premium = feats["has_premium_one_drop_card"]
    land_ct = feats["land_count"]
    t1_accel_now = feats["t1_accel_executable_now"]
    has_engine = feats["has_any_engine_card"]
    tier_a = feats["has_tier_a_engine_card"]
    interaction_only = feats["interaction_only_hand"]
    accel_ct = feats["accel_card_count"]
    colors_potential = feats["distinct_colors_potential"]
    cheap_tutor = any(t in CHEAP_TUTORS_WITH_REAL_T2_CONVERSION for t in feats["tutor_names"])

    # A commander (Tymna 1WB / Thrasios GU) is a real destination for acceleration even with no
    # engine card in hand - it's always available from the command zone. Approximated here as
    # "enough color access to plausibly cast one of the two color pairs" without hand-simulating.
    commander_colors_plausible = colors_potential >= 2

    # 1. Snap keep: premium T1 engine.
    if premium:
        return "SNAP_KEEP", "premium one-drop engine (Mystic Remora/Esper Sentinel) - Tier S trajectory"

    # 2. T1-executable acceleration is only a keep signal WITH a destination (correction A) - an
    #    engine already in hand, a CMC1 tutor that can reach one, or enough color access to plausibly
    #    cast a commander. This also covers T1 creature dorks leading into a T2 engine (correction
    #    B) - a creature dork still counts as "T1-executable acceleration" for THIS rule's purpose
    #    even though it can't tap the turn it's cast, because the destination check is what's being
    #    verified, not immediate tap-ability.
    if t1_accel_now or feats["t1_accel_creature_only"]:
        if has_engine:
            return "SNAP_KEEP", "acceleration with an engine destination already in hand (rock/dork_to_engine)"
        if cheap_tutor:
            return "CONDITIONAL_KEEP", "acceleration + CMC1 tutor able to fetch an engine"
        if commander_colors_plausible:
            return "CONDITIONAL_KEEP", "acceleration fuels a plausible T2 commander line"

    # 3. Acceleration with NO destination at all is NOT a keep signal (correction A) -
    #    mull005_accel_without_payoff_analysis.json: truly-stranded 2+-accel hands hit Tier D/F
    #    58.8% of the time, worse than the no-acceleration baseline (18.3%).
    if accel_ct >= 2 and not (has_engine or cheap_tutor or commander_colors_plausible):
        return "SHIP", "2+ acceleration with no engine/tutor/commander destination - 58.8% Tier D/F measured"

    # 4. Land-count floors.
    if land_ct == 0:
        return "SHIP", "0 lands"
    if land_ct == 1:
        return "SHIP", "1 land with no qualifying executable acceleration"
    if land_ct >= 4:
        if has_engine or premium:
            return "SNAP_KEEP", "4+ lands with a real engine"
        if commander_colors_plausible:
            return "CONDITIONAL_KEEP", "4+ lands, commander colors plausible, no card engine"
        return "SHIP", "4+ lands with no business at all"

    # land_ct in {2, 3} from here on.
    if interaction_only:
        return "SHIP", "interaction-only hand - largest negative lift measured at every land count"

    if tier_a:
        return "SNAP_KEEP", "Tier-A engine card (Rhystic Study/Sylvan Library) online by T2"
    if has_engine:
        return "CONDITIONAL_KEEP", "an engine card present at 2-3 lands"
    if cheap_tutor:
        return "CONDITIONAL_KEEP", "CMC1 tutor at 2-3 lands - ~25-27% direct T2-engine conversion"
    if commander_colors_plausible:
        return "CONDITIONAL_KEEP", "commander colors plausible at 2-3 lands - dominant best-tier mechanism overall"

    return "SHIP", "2-3 lands with no engine, no cheap tutor, no plausible commander colors"


def trajectory_simple_policy(feats):
    """Pure opener-feature function (no simulation) - evaluated top to bottom, first match wins.
    Thin wrapper over structural_hand_grade(): keep iff SNAP_KEEP or CONDITIONAL_KEEP."""
    grade, _ = structural_hand_grade(feats)
    return grade in ("SNAP_KEEP", "CONDITIONAL_KEEP")
