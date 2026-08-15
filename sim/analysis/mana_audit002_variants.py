"""MANA-AUDIT-002 section F infrastructure — counterfactual mana-base variant builder.

Reuses opening_hand_model.py/opening_hand_policy.py's shared engine unchanged (per the
assignment: "infrastructure is already validated, do not rebuild it"). This module only ADDS
card data for 6 lands not present in the frozen subject (verified via web search where network
access allowed it, see NEW_LAND_CARDS docstrings below) and extends the shared classification
tables IN PLACE (so opening_hand_policy.py's own `from opening_hand_model import X` aliases see
the same additions - see module docstring note in each table below), then builds variant card
pools by adding/removing card names from the real 98-card baseline.

Every "add" card exists ONLY in-memory for a given variant's simulation - never written into
data/decklists/ or data/cards_cache/, and never presented as a real Scryfall-verified card record
(no fabricated scryfall_id is used anywhere real provenance is checked). Counterfactual configs
are explicitly NOT frozen subjects - they carry no deck_hash and are never loaded through
load_frozen_deck().
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402

# ---- new card data (not in the frozen subject) --------------------------------------------
# Oracle text verified via WebSearch during this task (api.scryfall.com and gatherer.wizards.com
# were both network-egress-blocked in this environment - corroborated via search-engine results
# citing scryfall.com/mtgsalvation/gatherer page titles, moderate-high confidence, not a direct
# authoritative fetch). Standard fetchlands (Scalding Tarn/Arid Mesa/Bloodstained Mire) follow the
# exact, well-established pattern of the 7 fetches already in the frozen subject and were not
# separately re-verified beyond that pattern match.
NEW_LAND_CARDS = {
    "Scalding Tarn": {"type": "Land", "text": "T, Pay 1 life, Sacrifice: Search your library for "
                       "an Island or Mountain card, put it onto the battlefield, then shuffle.",
                       "mana_cost": "", "cmc": 0},
    "Arid Mesa": {"type": "Land", "text": "T, Pay 1 life, Sacrifice: Search your library for a "
                   "Plains or Mountain card, put it onto the battlefield, then shuffle.",
                   "mana_cost": "", "cmc": 0},
    "Bloodstained Mire": {"type": "Land", "text": "T, Pay 1 life, Sacrifice: Search your library "
                           "for a Swamp or Mountain card, put it onto the battlefield, then "
                           "shuffle.", "mana_cost": "", "cmc": 0},
    "Gemstone Mine": {"type": "Land", "text": "Gemstone Mine enters the battlefield with three "
                       "mining counters on it. T, Remove a mining counter: Add one mana of any "
                       "color. If there are no mining counters on it, sacrifice it.",
                       "mana_cost": "", "cmc": 0},
    "Tarnished Citadel": {"type": "Land", "text": "T: Add C. T: Add one mana of any color. This "
                           "land deals 3 damage to you.", "mana_cost": "", "cmc": 0},
    "Forbidden Orchard": {"type": "Land", "text": "T: Add one mana of any color. Whenever you "
                           "tap this land for mana, target opponent creates a 1/1 colorless "
                           "Spirit creature token.", "mana_cost": "", "cmc": 0},
}

NEW_FETCH_TARGET_TYPES = {
    "Scalding Tarn": frozenset({"Island", "Mountain"}),
    "Arid Mesa": frozenset({"Plains", "Mountain"}),
    "Bloodstained Mire": frozenset({"Swamp", "Mountain"}),
}

NEW_FETCHES = {"Scalding Tarn", "Arid Mesa", "Bloodstained Mire"}

# Gemstone Mine: 3 mining counters, T1-3 horizon never taps it more than 3x total (at most once
# per turn, 3 turns) - modeled as a flat rainbow source for this audit's horizon, sacrifice-on-
# empty is a real T4+ concern out of scope here (disclosed, not silently ignored).
# Tarnished Citadel: pain-for-color like City of Brass/Mana Confluence/Starting Town (3 life,
# not 1) - same established "life tracked, never blocks a line" treatment as those.
# Forbidden Orchard: no life cost; its real downside (opponent token EVERY tap) has zero
# mechanical representation in this solo/no-opponent model, exactly like Exotic Orchard's own
# disclosed solo-model limitation - flagged qualitatively in the F-section writeup, not modeled.
NEW_RAINBOW_LANDS = {"Gemstone Mine", "Tarnished Citadel", "Forbidden Orchard"}


def install_new_land_tables():
    """Mutates opening_hand_model's shared, already-imported-by-reference tables IN PLACE (adds
    only - never removes or overwrites an existing baseline-deck key), so opening_hand_policy.py's
    own aliases (bound at ITS import time to the same dict/set objects) see the additions too.
    Idempotent - safe to call more than once."""
    for name in NEW_RAINBOW_LANDS:
        ohm.LAND_COLOR_SETS[name] = set(ohm.COLORS)
    ohm.FETCH_LANDS |= NEW_FETCHES
    ohm.FETCH_LAND_TARGET_TYPES.update(NEW_FETCH_TARGET_TYPES)


def all_cards_dict(base_cards):
    """base_cards ∪ NEW_LAND_CARDS, base takes precedence on any name collision (none expected)."""
    merged = dict(NEW_LAND_CARDS)
    merged.update(base_cards)
    return merged


def build_variant(base_names, cards_pool, add=(), remove=()):
    """Returns a new list of card names: base_names with `remove` names each removed ONCE (not
    all copies - this decklist is all-singleton so it's equivalent) and `add` names appended.
    Every name in `add` must exist in cards_pool (from all_cards_dict()) or the baseline itself."""
    names = list(base_names)
    for r in remove:
        assert r in names, f"cannot remove {r!r}, not present in base list"
        names.remove(r)
    for a in add:
        assert a in cards_pool, f"cannot add {a!r}, no card data available"
        names.append(a)
    return names


install_new_land_tables()
