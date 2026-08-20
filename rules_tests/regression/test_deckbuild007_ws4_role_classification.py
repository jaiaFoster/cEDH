"""SIM-DECKBUILD-007 Workstream 4 — role classification completeness/consistency checks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sim" / "analysis"))

import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards  # noqa: E402
from build_deckbuild007_ws4_role_classification import ROLES  # noqa: E402


def test_every_real_deck_card_has_exactly_one_primary_role():
    d7.install_new_card_tables()
    try:
        _, rows = load_deckbuild007_cards()
    finally:
        d7.uninstall_new_card_tables()
    all_classified = []
    for cards in ROLES.values():
        all_classified.extend(cards)
    assert len(all_classified) == len(set(all_classified)), "a card appears in >1 primary role"
    assert set(all_classified) == set(rows.keys())
