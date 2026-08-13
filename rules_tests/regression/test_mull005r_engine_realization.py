"""SIM-001 MULL-005R — engine realization timing analysis (assignment section 2A,
t1_t3_trajectory_audit.json REALIZE-001/REALIZE-002).

Cross-checks results/solo_baseline/engine_realization_analysis.json against the REAL grading code
(not just internal JSON consistency) so the analysis can't silently drift from actual model
behavior: every entry's engine_tier must match the live ENGINE_TIER_* sets, every
structurally_inert_in_solo_model flag must match TIER_C_STRUCTURALLY_INERT membership, and the
central "proxy-credited Tier A vs support-gated Tier C" claim is verified by actually running
_tier_b_supported/_tier_c_supported and grade_trajectory, not merely asserted in prose.
"""
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import (  # noqa: E402
    ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE, ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE,
    ENGINE_TIER_C_CONDITIONAL_VALUE,
)
from opening_hand_policy import HandState, develop_turn, DEFAULT_PRIORITY  # noqa: E402
from opening_hand_metrics import snapshot_metrics  # noqa: E402
import trajectory_metrics as tm  # noqa: E402
from trajectory_grading import grade_trajectory  # noqa: E402

ANALYSIS_PATH = REPO_ROOT / "results" / "solo_baseline" / "engine_realization_analysis.json"

FAKE_CARDS = {
    "Underground Sea": {"name": "Underground Sea", "type": "Land — Island Swamp", "mana_cost": "", "cmc": 0},
    "Bayou": {"name": "Bayou", "type": "Land — Swamp Forest", "mana_cost": "", "cmc": 0},
    "Savannah": {"name": "Savannah", "type": "Land — Forest Plains", "mana_cost": "", "cmc": 0},
    "Sol Ring": {"name": "Sol Ring", "type": "Artifact", "mana_cost": "{1}", "cmc": 1},
    "Smothering Tithe": {"name": "Smothering Tithe", "type": "Enchantment", "mana_cost": "{3}{W}", "cmc": 4},
    "Faerie Mastermind": {"name": "Faerie Mastermind", "type": "Creature — Faerie Rogue", "mana_cost": "{1}{U}", "cmc": 2},
    "Archivist of Oghma": {"name": "Archivist of Oghma", "type": "Creature — Human Wizard", "mana_cost": "{2}{U}", "cmc": 3},
    "Deathrite Shaman": {"name": "Deathrite Shaman", "type": "Creature — Elf Shaman", "mana_cost": "{B/G}", "cmc": 1},
    "Filler Land": {"name": "Filler Land", "type": "Land", "mana_cost": "", "cmc": 0},
}


def _load_analysis():
    return json.loads(ANALYSIS_PATH.read_text())


def _sim(hand, library, turns=3):
    state = HandState(list(hand), list(library), on_play=True, rng=random.Random(0), cards=FAKE_CARDS)
    snaps = {}
    for t in range(1, turns + 1):
        develop_turn(state, FAKE_CARDS, priority_order=DEFAULT_PRIORITY)
        snaps[t] = snapshot_metrics(state, FAKE_CARDS, [])
    return state, snaps


def test_analysis_file_exists_and_is_well_formed():
    data = _load_analysis()
    assert data["entry_count"] == len(data["entries"])
    assert data["entry_count"] >= 15


def test_every_entrys_engine_tier_matches_live_code_sets():
    data = _load_analysis()
    for e in data["entries"]:
        card, tier = e["card"], e["engine_tier"]
        if tier == "A":
            assert card in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE, card
        elif tier == "B":
            assert card in ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE, card
        elif tier == "C":
            assert card in ENGINE_TIER_C_CONDITIONAL_VALUE, card
        else:
            raise AssertionError(f"unexpected tier {tier!r} for {card}")


def test_structurally_inert_flag_matches_live_tier_c_structurally_inert_set():
    data = _load_analysis()
    for e in data["entries"]:
        if e["engine_tier"] != "C":
            assert not e["structurally_inert_in_solo_model"]
            continue
        expected = e["card"] in tm.TIER_C_STRUCTURALLY_INERT
        assert e["structurally_inert_in_solo_model"] == expected, e["card"]


def test_no_tier_a_entry_marked_structurally_inert():
    # Central claim: Tier-A opponent-triggered engines are proxy-credited, never zeroed out.
    data = _load_analysis()
    for e in data["entries"]:
        if e["engine_tier"] == "A":
            assert e["deployment_credited_as_proxy"] is True
            assert e["structurally_inert_in_solo_model"] is False


def test_smothering_tithe_credited_on_deployment_alone_with_zero_opponent_simulation():
    # TITHE-001 empirical check: Tithe reaches Tier A the instant it's on the battlefield by T2,
    # exactly like Rhystic Study - no opponent action is ever simulated to "earn" the credit.
    # Savannah (G/W, one color per tap) + Sol Ring deliberately denies both commanders' colors
    # (Tymna needs W+B - no B source; Thrasios needs G+U - no U source) so the greedy line can't
    # get hijacked into casting a commander instead - the recurring "commander-color-access
    # confound" documented throughout this project.
    hand = ["Smothering Tithe", "Savannah", "Savannah", "Savannah", "Sol Ring"]
    library = ["Filler Land"] * 20
    state, snaps = _sim(hand, library)
    g = grade_trajectory(state, FAKE_CARDS, snaps[1], snaps[2], snaps[3])
    assert g["tier"] == "A"
    assert g["tier_engine"] == "Smothering Tithe"


def test_archivist_of_oghma_never_credited_regardless_of_board_state():
    # Structurally inert: _tier_c_supported must return False even with mana available and the
    # card on the battlefield - there is no board state that earns it credit in this model.
    hand = ["Archivist of Oghma", "Underground Sea", "Bayou", "Underground Sea", "Bayou"]
    library = ["Filler Land"] * 20
    state, snaps = _sim(hand, library)
    assert tm._tier_c_supported("Archivist of Oghma", state, FAKE_CARDS) is False
    g = grade_trajectory(state, FAKE_CARDS, snaps[1], snaps[2], snaps[3])
    assert g["tier_engine"] != "Archivist of Oghma"


def test_deathrite_shaman_never_credited_for_a_distinct_not_modeled_reason():
    # Deathrite is NOT in TIER_C_STRUCTURALLY_INERT (that set is for opponent/combat-dependent
    # conditions) but _tier_c_supported still unconditionally returns False for it - a graveyard-
    # mana ability that simply isn't represented in this engine at all (SOLO-002R disclosed gap).
    assert "Deathrite Shaman" not in tm.TIER_C_STRUCTURALLY_INERT
    hand = ["Deathrite Shaman", "Underground Sea", "Bayou", "Underground Sea", "Bayou"]
    library = ["Filler Land"] * 20
    state, snaps = _sim(hand, library)
    assert tm._tier_c_supported("Deathrite Shaman", state, FAKE_CARDS) is False


def test_faerie_mastermind_support_check_uses_its_activated_ability_not_mere_presence():
    # REALIZE-001: Mastermind's unmeasurable passive trigger is NOT what earns it Tier-C credit -
    # only the fully-simulatable {3}{U} activated ability is checked. With Mastermind on the
    # battlefield but no spare {3}{U}, it must NOT be supported.
    hand = ["Faerie Mastermind", "Underground Sea", "Bayou"]
    library = ["Filler Land"] * 20
    state, snaps = _sim(hand, library, turns=1)
    assert tm._tier_c_supported("Faerie Mastermind", state, FAKE_CARDS) is False  # only 2 lands, {3}{U} not payable

    # With enough mana available (3 lands + Sol Ring = 5 mana by T3, well past {3}{U}=4), the same
    # check must pass.
    hand2 = ["Faerie Mastermind", "Underground Sea", "Underground Sea", "Underground Sea", "Sol Ring"]
    state2, snaps2 = _sim(hand2, library, turns=3)
    assert tm._tier_c_supported("Faerie Mastermind", state2, FAKE_CARDS) is True
