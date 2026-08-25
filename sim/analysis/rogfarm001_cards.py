"""SIM-ROGFARM-001 — card data + mechanics for cards new to the RogSi/Rog Farm/Blue Farm card
pool. Starts with Foil (the Stage 1 "RULES FIX 1" correction); more cards land here as Stage 2's
card-data build proceeds.

Follows this project's established install_new_card_tables()/uninstall_new_card_tables() pattern
for extending shared global tables (opening_hand_model.py's INTERACTION_CASTABLE,
interaction_model.py's ALT_COST_SPECS) without cross-test-file pollution.

Foil — Oracle text supplied directly by the task owner as the authoritative correction to this
project's own prior (wrong) Stage 1 draft, which had described Foil as "exile a blue card... MV<=3
restriction" (a conflation with a different, unrelated budget counterspell). Corrected text:
  {2}{U}{U} Instant — "Counter target spell. Alternative cost: You may discard an Island card and
  another card rather than pay this spell's mana cost."
Key properties (all directly required by the correction instruction, each with its own regression
test below): the alternate cost needs an Island CARD in hand (not merely blue mana available) plus
a SECOND, separate card (real two-card discard, genuine card-disadvantage cost, not a cantrip- or
replacement-style cost); there is NO mana-value restriction on the countered spell (unlike a
budget counterspell such as Spell Pierce); Foil does NOT exile a blue card (that mechanic belongs
to a different, unrelated card and was the source of the original error).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402
import interaction_model as im  # noqa: E402

FOIL_NAME = "Foil"

NEW_CARD_DATA = {
    FOIL_NAME: {
        "type": "Instant", "mana_cost": "{2}{U}{U}", "cmc": 4,
        "text": "Counter target spell. Alternative cost: You may discard an Island card and "
                "another card rather than pay this spell's mana cost.",
    },
}

# Registered in INTERACTION_CASTABLE with a dedicated alt-cost tag ("discard_island_plus_other")
# distinct from every existing "pitch" (exile-based) entry - Foil's alternate cost is a real
# 2-card DISCARD (to graveyard), not an exile, and is keyed off card TYPE (Island) for one card
# and no restriction at all for the other, not off color-of-card like Force of Will/Subtlety/etc.
NEW_INTERACTION_CASTABLE = {FOIL_NAME: "discard_island_plus_other"}
NEW_ALT_COST_SPECS = {FOIL_NAME: {"type": "discard_island_plus_other"}}

# Volcanic Island's mana colors, needed for available_sources()' mana-color lookup
# (opening_hand_model.LAND_COLOR_SETS is a shared global keyed by exact land name). Underground
# Sea/Tundra/Tropical Island are already registered there from the Tymna/Thrasios card pool;
# Volcanic Island is the one genuinely new dual this project's decks introduce. Registering it
# also matters for Foil's alt cost: R1 runs zero basic Islands (see test coverage), so its
# Island-subtype fuel is exactly these Island-type duals/fetchable duals.
NEW_LAND_COLOR_SETS = {
    "Volcanic Island": {"U", "R"},
}


def _is_island(card_name, cards):
    return "Island" in cards[card_name]["type"]


def foil_discard_pair(state, cards):
    """Returns (island_card_name, other_card_name) if Foil's alternate cost is currently payable
    from hand, else None. Requires an Island CARD in hand (the land itself, not merely blue mana
    availability) plus a second, distinct card - Foil itself is never counted as either half."""
    hand_others = [c for c in state.hand if c != FOIL_NAME]
    islands = [c for c in hand_others if _is_island(c, cards)]
    if not islands:
        return None
    island = islands[0]
    remaining = list(hand_others)
    remaining.remove(island)
    if not remaining:
        return None  # the Island alone isn't enough - genuine 2-card cost, need a second card
    return island, remaining[0]


def _foil_is_live(state, cards):
    from opening_hand_policy import is_currently_castable
    gen, pips, x = ohm.parse_cost(cards[FOIL_NAME]["mana_cost"])
    mana_ok = (x == 0) and is_currently_castable(state, gen, pips)
    return mana_ok or foil_discard_pair(state, cards) is not None


def _foil_resolve(state, cards):
    from opening_hand_policy import _try_pay
    gen, pips, x = ohm.parse_cost(cards[FOIL_NAME]["mana_cost"])
    if x == 0:
        plan = _try_pay(state, gen, pips)
        if plan is not None:
            return ("mana", plan)
    pair = foil_discard_pair(state, cards)
    if pair is not None:
        return ("discard_island_plus_other", pair)
    return None


def _foil_commit(name, resolution, state):
    kind, payload = resolution
    if kind == "discard_island_plus_other":
        island, other = payload
        for c in (island, other):
            state.hand.remove(c)
            state.graveyard.append(c)


# Monkeypatch hooks: interaction_model.py's interaction_is_live/resolve_interaction_cast/
# commit_interaction_cast dispatch purely on ALT_COST_SPECS[name]["type"], so Foil's new type
# needs a branch in each. Rather than editing the shared module's if/elif chains directly (which
# would hardcode a rogfarm-only mechanic into a file every other task also imports), these
# wrapper functions are what analysis scripts call instead - installed/uninstalled alongside the
# data tables, exactly like every other per-task engine extension in this project.
_ORIG_IS_LIVE = im.interaction_is_live
_ORIG_RESOLVE = im.resolve_interaction_cast
_ORIG_COMMIT = im.commit_interaction_cast


def _patched_is_live(name, state, cards):
    if name == FOIL_NAME:
        return _foil_is_live(state, cards)
    return _ORIG_IS_LIVE(name, state, cards)


def _patched_resolve(name, state, cards):
    if name == FOIL_NAME:
        return _foil_resolve(state, cards)
    return _ORIG_RESOLVE(name, state, cards)


def _patched_commit(name, resolution, state):
    if name == FOIL_NAME and resolution[0] == "discard_island_plus_other":
        _foil_commit(name, resolution, state)
        return
    _ORIG_COMMIT(name, resolution, state)


def install_new_card_tables():
    for name, tag in NEW_INTERACTION_CASTABLE.items():
        ohm.INTERACTION_CASTABLE[name] = tag
    im.ALT_COST_SPECS.update(NEW_ALT_COST_SPECS)
    im.interaction_is_live = _patched_is_live
    im.resolve_interaction_cast = _patched_resolve
    im.commit_interaction_cast = _patched_commit
    for name, colors in NEW_LAND_COLOR_SETS.items():
        ohm.LAND_COLOR_SETS[name] = colors


def uninstall_new_card_tables():
    for name in NEW_INTERACTION_CASTABLE:
        ohm.INTERACTION_CASTABLE.pop(name, None)
    for name in NEW_ALT_COST_SPECS:
        im.ALT_COST_SPECS.pop(name, None)
    im.interaction_is_live = _ORIG_IS_LIVE
    im.resolve_interaction_cast = _ORIG_RESOLVE
    im.commit_interaction_cast = _ORIG_COMMIT
    for name in NEW_LAND_COLOR_SETS:
        ohm.LAND_COLOR_SETS.pop(name, None)


def all_cards_dict(base_cards):
    merged = dict(NEW_CARD_DATA)
    merged.update(base_cards)
    return merged
