"""SIM-DECKBUILD-004 phase_0 — reactive-slot screen sanity checks (cheap, no full simulation)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from build_deckbuild004_phase0_reactive_screen import CANDIDATES, INFORMATIONAL_ONLY  # noqa: E402


def test_every_real_candidate_is_a_minus_one_plus_one_swap():
    for name, spec in CANDIDATES.items():
        assert len(spec["remove"]) == 1, name
        assert spec["add"] == ["Formidable Speaker"], name


def test_an_offer_is_informational_only_not_a_real_cut_candidate():
    assert "An Offer You Can't Refuse" not in {c for spec in CANDIDATES.values() for c in spec["remove"]}
    info_spec = next(iter(INFORMATIONAL_ONLY.values()))
    assert info_spec["remove"] == []  # nothing removed - can't cut a card that isn't in the deck
    assert "An Offer You Can't Refuse" in info_spec["add"]


def test_all_four_reactive_candidates_are_the_ones_the_assignment_named():
    removed = {spec["remove"][0] for spec in CANDIDATES.values()}
    assert removed == {"Subtlety", "Misdirection", "Commandeer", "Mental Misstep"}
