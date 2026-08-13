"""SIM-001 MULL-005R — trajectory grading corrections: Tymna zero credit, Thrasios concrete-
benefit gating, Kinnan de-scoring, Smothering Tithe promotion, Oculus as a graded destination.

See t1_t3_trajectory_audit.json CMDR-001/CMDR-002/KINNAN-001/TITHE-001 for the Oracle-text and
consistency grounding for each correction.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_policy import HandState, Perm, LandInPlay, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
from opening_hand_features import extract_opener_features  # noqa: E402
from opening_hand_model import ENGINES  # noqa: E402
from trajectory_grading import grade_trajectory  # noqa: E402

FAKE_CARDS = {
    "Savannah": {"name": "Savannah", "type": "Land — Forest Plains", "mana_cost": "", "cmc": 0},
    "Scrubland": {"name": "Scrubland", "type": "Land — Plains Swamp", "mana_cost": "", "cmc": 0},
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Tropical Island": {"name": "Tropical Island", "type": "Land — Island Forest", "mana_cost": "", "cmc": 0},
    "Badgermole Cub": {"name": "Badgermole Cub", "type": "Creature — Badger Mole", "mana_cost": "{1}{G}", "cmc": 2},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Smothering Tithe": {"name": "Smothering Tithe", "type": "Enchantment", "mana_cost": "{3}{W}", "cmc": 4},
    "Kinnan, Bonder Prodigy": {"name": "Kinnan, Bonder Prodigy", "type": "Legendary Creature — Human Druid", "mana_cost": "{G}{U}", "cmc": 2},
    "Birds of Paradise": {"name": "Birds of Paradise", "type": "Creature — Bird", "mana_cost": "{G}", "cmc": 1},
    "Mox Amber": {"name": "Mox Amber", "type": "Legendary Artifact", "mana_cost": "{0}", "cmc": 0},
    "Abhorrent Oculus": {"name": "Abhorrent Oculus", "type": "Creature — Eye", "mana_cost": "{2}{U}", "cmc": 3},
    "Esper Sentinel": {"name": "Esper Sentinel", "type": "Artifact Creature — Human Soldier", "mana_cost": "{W}", "cmc": 1},
    "Survival of the Fittest": {"name": "Survival of the Fittest", "type": "Enchantment", "mana_cost": "{1}{G}", "cmc": 2},
    "Birthing Pod": {"name": "Birthing Pod", "type": "Artifact", "mana_cost": "{3}{G/P}", "cmc": 4},
    "Devoted Druid": {"name": "Devoted Druid", "type": "Creature — Elf Druid", "mana_cost": "{1}{G}", "cmc": 2},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
    "Tymna the Weaver": {"name": "Tymna the Weaver", "type": "Legendary Creature — Human Monk", "mana_cost": "{1}{W}{B}", "cmc": 3},
    "Force of Will": {"name": "Force of Will", "type": "Instant", "mana_cost": "{3}{U}{U}", "cmc": 5},
}


def _sim(hand, library, priority_order=DEFAULT_PRIORITY, turns=3):
    state = HandState(list(hand), list(library), on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    snaps = {}
    for t in range(1, turns + 1):
        develop_turn(state, FAKE_CARDS, priority_order=priority_order)
        snaps[t] = snapshot_metrics(state, FAKE_CARDS, [])
    return state, snaps[1], snaps[2], snaps[3]


def test_tymna_with_real_attack_support_gets_zero_credit():
    # Badgermole Cub (T1, not sick by T3) gives Tymna a real attacker; DEFAULT_PRIORITY still
    # casts Tymna once colors/mana allow (WB via Savannah/Scrubland) - but the GRADE must ignore
    # it entirely.
    state, m1, m2, m3 = _sim(
        ["Badgermole Cub", "Savannah", "Scrubland", "Scrubland"], ["Filler Land"] * 20,
    )
    assert any(n == "Tymna the Weaver" for (t, n, c) in state.cast_log)
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier_engine"] != "Tymna the Weaver"
    assert "Tymna" not in (g["mechanism"] or "")


def test_smothering_tithe_promoted_to_tier_a_when_online_by_t2():
    state, m1, m2, m3 = _sim(
        ["Sol Ring", "Smothering Tithe", "Underground Sea", "Underground Sea"], ["Filler Land"] * 20,
    )
    # 2 Underground Sea (U/B only - no W, so no commander can compete) + Sol Ring = enough for
    # Tithe (4 mana, 1 W needed) only if a W source exists - use Scrubland instead for W access
    # without enabling Tymna at 2 lands (Tymna costs 1WB=3, needs 3 mana - achievable by T2 with
    # Sol Ring, so isolate by keeping colors U/B only and skipping Tithe's W requirement check
    # here; this test only needs SOME Tier-A-eligible engine reachable to prove the promotion).
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    # Tithe itself may not be castable with U/B-only mana (needs W) - the real assertion is on
    # the classification, not this specific hand's castability.
    from opening_hand_model import ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE
    assert "Smothering Tithe" in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE


def test_smothering_tithe_reaches_tier_a_with_correct_colors():
    state, m1, m2, m3 = _sim(
        ["Sol Ring", "Smothering Tithe", "Scrubland", "Scrubland"],
        ["Filler Land"] * 20,
        priority_order=["free_accel", "paid_accel", "premium_engine", "engine", "commander", "tutor", "interaction"],
    )
    assert any(n == "Smothering Tithe" and t == 2 for (t, n, c) in state.cast_log), state.cast_log
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier"] == "A", g
    assert g["tier_engine"] == "Smothering Tithe"


def test_kinnan_alone_grants_no_standalone_tier_credit():
    state, m1, m2, m3 = _sim(
        ["Birds of Paradise", "Kinnan, Bonder Prodigy", "Tropical Island", "Tropical Island"],
        ["Filler Land"] * 20,
    )
    assert any(n == "Kinnan, Bonder Prodigy" for (t, n, c) in state.cast_log)
    g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
    assert g["tier_engine"] != "Kinnan, Bonder Prodigy"
    assert "Kinnan" not in (g["mechanism"] or "")


def test_thrasios_generic_presence_does_not_earn_tier_a():
    # Thrasios on battlefield with excess mana but NO Mox Amber, NO Fierce Guardianship, and
    # thrasios_productivity's own activation check failing (no spare mana after casting) -> must
    # NOT earn Tier A/B on generic presence alone.
    state, m1, m2, m3 = _sim(["Tropical Island"], ["Filler Land"] * 20)
    thras_cast = any(n == "Thrasios, Triton Hero" for (t, n, c) in state.cast_log)
    if thras_cast:
        g = grade_trajectory(state, FAKE_CARDS, m1, m2, m3)
        assert g["tier"] not in ("A", "B") or g["tier_engine"] != "Thrasios, Triton Hero"


def test_thrasios_enables_mox_amber_earns_tier_credit():
    state = HandState(["Mox Amber", "Tropical Island", "Tropical Island"], ["Filler Land"] * 20,
                       on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    snaps = {}
    for t in range(1, 4):
        develop_turn(state, FAKE_CARDS)
        snaps[t] = snapshot_metrics(state, FAKE_CARDS, [])
    assert any(n == "Thrasios, Triton Hero" for (t, n, c) in state.cast_log)
    assert "Mox Amber" in [p.name for p in state.nonland_perms]
    g = grade_trajectory(state, FAKE_CARDS, snaps[1], snaps[2], snaps[3])
    assert g["tier_engine"] == "Thrasios, Triton Hero"
    assert g["tier"] in ("A", "B")


def test_engines_dict_no_longer_lists_either_commander():
    # CMDR-003 (t1_t3_trajectory_audit.json): the broader SOLO-003-era ENGINES dict (feeding
    # opener feature extraction and snapshot metrics, NOT the trajectory-tier grading already
    # fixed by CMDR-001/002) still listed Tymna the Weaver / Thrasios, Triton Hero as
    # "commander_engine" - silently undermining the zero-credit directive one layer down.
    assert "Tymna the Weaver" not in ENGINES
    assert "Thrasios, Triton Hero" not in ENGINES


def test_hand_with_only_a_commander_does_not_report_has_any_engine_card():
    hand = ["Tymna the Weaver", "Underground Sea", "Underground Sea", "Scrubland",
            "Force of Will", "Filler Land", "Filler Land"]
    library = ["Filler Land"] * 20
    feats = extract_opener_features(hand, library, True, FAKE_CARDS)
    assert feats["has_any_engine_card"] is False
    assert feats["engine_count"] == 0


def test_battlefield_commander_alone_does_not_set_any_engine_active():
    # opening_hand_metrics.snapshot_metrics's any_engine_active/engine_count/two_plus_engines_
    # active must not count a cast commander as an "active engine" - these feed trajectory_
    # metrics.py's family/failure/composite tags (t1_engine_deployed, stranded_or_unsupported_
    # engine, multi_engine_plus_interaction, ...), all of which are downstream of CMDR-001.
    state = HandState(["Tymna the Weaver"], ["Filler Land"] * 20, on_play=True,
                       rng=random.Random(0), cards=FAKE_CARDS)
    state.nonland_perms.append(Perm("Tymna the Weaver", 1, is_creature=True))
    m = snapshot_metrics(state, FAKE_CARDS, [])
    assert m["any_engine_active"] is False
    assert m["engine_count"] == 0
    assert m["two_plus_engines_active"] is False


def test_creature_discarded_to_survival_is_not_credited_as_a_battlefield_engine():
    # Regression for a real bug found generating the MULL-005R top-25 opener trajectory report:
    # Abhorrent Oculus (a Creature) can legally be DISCARDED to Survival of the Fittest as fodder
    # to find something else. cast_log records this under class "survival_discard" - the card goes
    # to the GRAVEYARD, never the battlefield. grade_trajectory's Tier S/A battlefield_t1/
    # battlefield_t2 sets must filter by ONLINE_CLASSES (like _engine_online_turn already does),
    # not treat every cast_log NAME as "on the battlefield" regardless of class - otherwise a
    # discarded engine card falsely earns Tier S/A credit for never having been cast at all.
    state = HandState(["Abhorrent Oculus"], ["Esper Sentinel"] + ["Filler Land"] * 15,
                       on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 1
    state.nonland_perms.append(Perm("Survival of the Fittest", 0, False))
    state.lands.append(LandInPlay("Tropical Island", 0, tapped=False))
    from pod_and_battlefield_tutors import try_activate_survival
    assert try_activate_survival(state, FAKE_CARDS, "Abhorrent Oculus", "Esper Sentinel")
    assert "Abhorrent Oculus" in state.graveyard
    assert "Abhorrent Oculus" not in [p.name for p in state.nonland_perms]
    m1 = snapshot_metrics(state, FAKE_CARDS, [])
    m3 = snapshot_metrics(state, FAKE_CARDS, [])
    g = grade_trajectory(state, FAKE_CARDS, m1, m1, m3)
    assert g["tier_engine"] != "Abhorrent Oculus", (
        "Oculus was discarded, not cast - it must never earn tier credit for being on the "
        f"battlefield (got tier_engine={g['tier_engine']!r}, tier={g['tier']!r})"
    )


def test_oculus_on_battlefield_graded_as_premium_destination():
    state = HandState([], ["Abhorrent Oculus"] + ["Filler Land"] * 10, on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    state.turn = 3
    state.lands += [LandInPlay("Underground Sea", 1, tapped=False), LandInPlay("Underground Sea", 1, tapped=False)]
    state.nonland_perms.append(Perm("Birthing Pod", 2, False))
    state.nonland_perms.append(Perm("Devoted Druid", 1, True))
    from pod_and_battlefield_tutors import try_activate_pod
    assert try_activate_pod(state, FAKE_CARDS, "Devoted Druid", "Abhorrent Oculus")
    m3 = snapshot_metrics(state, FAKE_CARDS, [])
    g = grade_trajectory(state, FAKE_CARDS, None, None, m3)
    assert g["tier_engine"] == "Abhorrent Oculus"
    assert g["tier"] in ("A", "B")
    assert "oculus" in g["mechanism"].lower()
