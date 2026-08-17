"""SIM-DECKBUILD-004 E2 — tutor-topology graph search sanity checks (fast, deterministic)."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from opening_hand_model import load_deck_cards, load_deterministic_combos  # noqa: E402
from deckbuild004_cards import all_cards_dict, install_new_card_tables, uninstall_new_card_tables  # noqa: E402
from deckbuild004_variants import build  # noqa: E402
from build_deckbuild004_e2_tutor_topology import _best_reachable, START_STATE_FAMILIES  # noqa: E402

_PAYLOAD, BASE_CARDS = load_deck_cards()
COMBOS = load_deterministic_combos()


@pytest.fixture(autouse=True)
def _installed_card_tables():
    install_new_card_tables()
    yield
    uninstall_new_card_tables()


def _built(variant):
    cards_pool = all_cards_dict(BASE_CARDS)
    names = build(list(BASE_CARDS.keys()), cards_pool, variant)
    return names, {n: cards_pool[n] for n in names}


def test_neoform_mechanism_absent_in_baseline_returns_none():
    names, cards = _built("B0_BASELINE")
    fam = START_STATE_FAMILIES["Neoform"]
    inst = fam["instances"][0]
    best, meta = _best_reachable(inst, fam, names, cards, COMBOS)
    assert best is None and meta is None


def test_neoform_mechanism_present_in_conversion_swap_returns_a_real_result():
    names, cards = _built("B2_CONVERSION_SWAP")
    fam = START_STATE_FAMILIES["Neoform"]
    inst = fam["instances"][0]
    best, meta = _best_reachable(inst, fam, names, cards, COMBOS)
    assert best is not None
    assert meta["activation"] == "Neoform"


def test_speaker_mechanism_absent_in_no_speaker_ablation_returns_none():
    names, cards = _built("B5_NO_SPEAKER")
    fam = START_STATE_FAMILIES["Formidable_Speaker"]
    inst = fam["instances"][0]
    best, meta = _best_reachable(inst, fam, names, cards, COMBOS)
    assert best is None and meta is None


def test_pod_reaches_a_real_verified_deterministic_win_from_a_known_state():
    """Pod + Derevi (MV3) -> Clever Impersonator (MV4) is INT-0012 (Clever Impersonator copies
    Birthing Pod) - a real, already-verified combo this project promoted in interactions/verified/.
    Confirms the graph search's deterministic_win_available detection actually fires on a case
    known to be genuinely true, not just structurally plausible."""
    names, cards = _built("B0_BASELINE")
    fam = START_STATE_FAMILIES["Birthing_Pod"]
    inst = next(i for i in fam["instances"] if "Derevi" in i["label"])
    best, meta = _best_reachable(inst, fam, names, cards, COMBOS)
    assert best is not None
    assert best["deterministic_win_available"] is True
    assert meta["target"] == "Clever Impersonator"


def test_neoform_alone_does_not_falsely_claim_the_pod_dependent_combo():
    """The SAME target (Clever Impersonator) reached via Neoform (which does NOT leave Birthing
    Pod on the battlefield - Neoform is exiled, not a permanent) must NOT show
    deterministic_win_available=True, since INT-0012 requires Pod itself present to copy - a
    direct check of the assignment's own anti_overclaim instruction ("do not call Neoform
    actionable unless a legal/useful sacrifice exists" - and, more specifically here, unless the
    resulting board state actually satisfies the combo's real requirements)."""
    names, cards = _built("B2_CONVERSION_SWAP")
    fam = START_STATE_FAMILIES["Neoform"]
    inst = next(i for i in fam["instances"] if "Derevi" in i["label"])
    best, meta = _best_reachable(inst, fam, names, cards, COMBOS)
    assert best is not None
    if meta["target"] == "Clever Impersonator":
        assert best["deterministic_win_available"] is False
