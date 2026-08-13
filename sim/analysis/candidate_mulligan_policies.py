"""SIM-001 SOLO-004 sections 10-11 — candidate human-usable keep/mulligan policies.

Every policy here is traced to a specific finding already on record - none are invented first and
justified after. Provenance:
  - has_premium_one_drop_card as the dominant split: decision tree ROOT split
    (solo004_hand_value_models.json), and the single largest standardized logistic coefficient
    among boolean features after accel_card_count (+0.573).
  - has_sol_ring: standardized coefficient +0.499, and the tree's second-level split whenever
    premium engine is absent.
  - accel_card_count >= 2: largest standardized coefficient of any feature (+0.989), and the
    land-population analysis's top or near-top lift at every land count (e.g. +39.9pp at 2 lands).
  - has_tier_a_engine_card: coefficient +0.491, land-population lift +33.8pp at 2 lands.
  - 1-land hands needing EXECUTABLE T1 acceleration specifically (not just any accel card):
    solo004_conditional_hand_outcomes.json's 1_land_with_t1_dork (63.4%) vs
    1_land_temporary_accel_only (41.4%) vs 1_land_no_acceleration (23.3%).
  - interaction_only_hand as a mulligan signal: consistently the largest NEGATIVE lift across
    every land-count population (-37.9pp at 2 lands, -32.1pp at 1 land region via the complement
    framing, etc.) - see solo004_land_population_analysis.json / conditional_hand_outcomes.json.
  - 4+ lands needing a premium engine specifically: 4plus_land_premium_engine (97.5% strong-state)
    vs 4plus_land_any_engine_no_premium (30.5%) vs 4plus_land_no_business (17.6%) -
    solo004_conditional_hand_outcomes.json.
  - 0-land hands: population success rate 20.9%, the worst bucket - solo004_land_population_
    analysis.json.

Each policy is a pure function `opener_features_dict -> bool` (True = keep), operating ONLY on
opening_hand_features.py's opener__ namespace (never outcome fields) - i.e. exactly the
information a real mulligan decision has.
"""
from opening_hand_model import load_deck_cards, load_deterministic_combos
from opening_hand_features import extract_opener_features
from derive_keep_frontiers import ALL_PROFILES
from run_solo004_dataset import simulate_hand_outcome


def policy_machine_optimal_factory(cards, combos, on_play, profile_name="BALANCED", threshold=None):
    """The reference/ceiling policy: keep iff this hand's actual simulated value (under the
    chosen objective profile) clears the keep-at-7 threshold from derive_keep_frontiers.py (the
    expected value of instead mulliganing to an optimally-bottomed 6). NOT meant to be memorized
    by a human pilot - requires running the actual T1-T3 simulation - but used as the ceiling
    every simplified candidate below is measured against."""
    if threshold is None:
        threshold = {
            "BALANCED": 0.2580, "DEVELOPMENT_FIRST": 0.2617, "AGENCY_FIRST": 0.1605,
            "SPEED_FIRST": 0.1219, "RESILIENCE_FIRST": 0.5273,
        }[profile_name]
    fn = ALL_PROFILES[profile_name]

    def policy(hand, library):
        row = simulate_hand_outcome(hand, library, on_play, cards, combos)
        score, _ = fn(row)
        return score >= threshold

    return policy


def policy_tree_depth4(feats):
    """Literal translation of the depth-4 decision tree's learned splits
    (solo004_hand_value_models.json's rules_text) into a callable - the "learned rule list"
    (Policy H5), not hand-simplified further. 16 leaves; captures ~76% of the GBM benchmark's
    achievable AUC gain."""
    premium = feats["has_premium_one_drop_card"]
    accel_ct = feats["accel_card_count"]
    sol_ring = feats["has_sol_ring"]
    t1_accel_now = feats["t1_accel_executable_now"]
    colors_potential = feats["distinct_colors_potential"]
    colors_direct = feats["distinct_colors_direct"]
    cards_after = feats["t1_cards_in_hand_after"]
    nonland_ct = feats["nonland_count"]
    land_ct = feats["land_count"]
    t1_mana = feats["t1_mana_available_now"]

    if not premium:
        if accel_ct <= 1:
            if not sol_ring:
                return t1_mana > 2
            return t1_accel_now
        else:
            if cards_after <= 5:
                return colors_potential > 0
            else:
                return False
    else:
        if colors_potential <= 0:
            return False
        else:
            if cards_after <= 5:
                return True
            else:
                return nonland_ct <= 5


def policy_simple_rules(feats):
    """SOLO-004 section 11's target: a small (<=8-rule), human-memorizable heuristic, distilled
    from the SAME statistical findings the tree/logistic model surfaced (see module docstring for
    exact provenance of each rule) - not simplified from the tree mechanically, but re-derived by
    hand from the underlying findings so the reasons stay legible to a pilot at the table.

    Evaluated top-to-bottom; first matching rule decides.
    """
    premium = feats["has_premium_one_drop_card"]
    sol_ring = feats["has_sol_ring"]
    accel_ct = feats["accel_card_count"]
    tier_a = feats["has_tier_a_engine_card"]
    interaction_only = feats["interaction_only_hand"]
    land_ct = feats["land_count"]
    t1_accel_now = feats["t1_accel_executable_now"]
    has_tutor = feats["has_tutor_card"]
    has_engine = feats["has_any_engine_card"]

    # 1. Snap keeps.
    if premium:
        return True
    if sol_ring:
        return True
    if accel_ct >= 2 and land_ct >= 1:
        return True

    # 2. Land-count-conditioned rules (each grounded in its own land-bucket finding).
    if land_ct == 0:
        return False  # 20.9% population success rate - the worst bucket, no exception carved out
    if land_ct == 1:
        return t1_accel_now  # 63.4% with executable T1 accel vs 23.3% without
    if land_ct >= 4:
        return premium  # already False here since premium was checked above -> ship
    # land_ct in {2, 3} from here on.

    # 3. Usually-ship signal, checked before the generic engine/tutor keep below.
    if interaction_only:
        return False  # largest negative lift at every land count tested

    # 4. Conditional keeps at 2-3 lands.
    if tier_a:
        return True
    if has_engine and land_ct == 3:
        return True  # 3_land_with_engine: 50.0% vs 43.5% complement
    if has_tutor and land_ct == 3:
        return True  # tutor is negative specifically AT 2 LANDS, not at 3 - see below

    # 5. Tutor at exactly 2 lands is a documented NEGATIVE signal on its own - do not let a bare
    #    tutor rescue an otherwise-thin 2-land hand.
    if has_tutor and land_ct == 2 and not has_engine:
        return False

    # 6. "Weak business" at 2-3 lands (no engine, no tutor, and not enough acceleration to have
    #    already triggered rule 1) is a real, measured negative outcome - 3_land_weak_business
    #    succeeds only 19.4% of the time (vs. 48.4% complement) - land count alone, with nothing
    #    else going on, is NOT a keep signal at 2 or 3 lands.
    if not has_engine and not has_tutor:
        return False

    # 7. Any remaining engine/tutor presence at 2-3 lands not already resolved above (e.g. a
    #    non-Tier-A engine at 2 lands, or a tutor alongside an engine) - the land-population
    #    analysis's has_any_engine_card / has_tutor_card lifts are net positive at this point.
    return True


CANDIDATE_POLICIES_STATIC = {
    "TREE_DEPTH4": policy_tree_depth4,
    "SIMPLE_RULES": policy_simple_rules,
}


def keep_policy_from_features(policy_fn):
    """Adapts a feats->bool policy into a hand,library->bool policy (computing opener features
    internally) for use by the mulligan simulation loop."""
    def wrapped(hand, library, on_play, cards):
        feats = extract_opener_features(hand, library, on_play, cards)
        return policy_fn(feats)
    return wrapped


if __name__ == "__main__":
    # quick self-check: agreement rate between SIMPLE_RULES and TREE_DEPTH4 on a small sample
    import random
    payload, cards = load_deck_cards()
    names = list(cards.keys())
    rng = random.Random(1)
    n, agree = 0, 0
    keep_rates = {"TREE_DEPTH4": 0, "SIMPLE_RULES": 0}
    for _ in range(2000):
        lib = names[:]
        rng.shuffle(lib)
        hand = lib[:7]
        library = lib[7:]
        feats = extract_opener_features(hand, library, True, cards)
        a = policy_tree_depth4(feats)
        b = policy_simple_rules(feats)
        n += 1
        agree += int(a == b)
        keep_rates["TREE_DEPTH4"] += int(a)
        keep_rates["SIMPLE_RULES"] += int(b)
    print(f"n={n} agreement={agree/n:.1%}")
    print({k: v / n for k, v in keep_rates.items()})
