"""SIM-DECKBUILD-007 — card data + mechanics for the 4 genuinely new cards (Biomancer's Familiar,
Birthing Ritual, Dark Ritual, The Cabbage Merchant) plus Carpet of Flowers (comparison-only, not
in the actual 101 - needed for Workstream 1's Dark-Ritual-vs-Carpet comparison).

Oracle text verified via WebSearch (network egress to card-database domains remains blocked in
this environment). Merges deckbuild006_cards.py's own NEW_CARD_DATA so every prior task's card
mechanics (Lotho, Neoform, Talion, Seedborn Muse, Scalding Tarn, etc.) are available too.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402
from deckbuild006_cards import NEW_CARD_DATA as D6_NEW_CARD_DATA  # noqa: E402

DARK_RITUAL_NAME = "Dark Ritual"
DARK_RITUAL_RESIDUE_NAME = "Dark Ritual Residue"
CARPET_NAME = "Carpet of Flowers"

NEW_CARD_DATA = {
    "Biomancer's Familiar": {
        "type": "Creature — Mutant", "mana_cost": "{G}{U}", "cmc": 2,
        "text": "Activated abilities of creatures you control cost {2} less to activate. This "
                "effect can't reduce the mana in that cost to less than one mana. {T}: The next "
                "time target creature adapts this turn, it adapts as though it had no +1/+1 "
                "counters on it.",
    },
    "Birthing Ritual": {
        "type": "Enchantment", "mana_cost": "{1}{G}", "cmc": 2,
        "text": "At the beginning of your end step, if you control a creature, look at the top "
                "seven cards of your library. Then you may sacrifice a creature. If you do, you "
                "may put a creature card with mana value X or less from among those cards onto "
                "the battlefield, where X is 1 plus the sacrificed creature's mana value. Put "
                "the rest on the bottom of your library in a random order.",
    },
    DARK_RITUAL_NAME: {
        "type": "Instant", "mana_cost": "{B}", "cmc": 1,
        "text": "Add {B}{B}{B}.",
    },
    DARK_RITUAL_RESIDUE_NAME: {
        # Synthetic bookkeeping card for Dark Ritual's temporary net mana (see
        # try_cast_dark_ritual below) - never a real Magic card, never in any decklist.
        "type": "Ritual Residue (synthetic, not a real card)", "mana_cost": "", "cmc": 0, "text": "",
    },
    "The Cabbage Merchant": {
        "type": "Legendary Creature — Human Citizen", "mana_cost": "{2}{G}", "cmc": 3,
        "text": "Whenever an opponent casts a noncreature spell, create a Food token. Whenever a "
                "creature deals combat damage to you, sacrifice a Food token. Tap two untapped "
                "Foods you control: Add one mana of any color. (Food token: artifact, \"{2}, "
                "{T}, Sacrifice this token: You gain 3 life.\")",
    },
    CARPET_NAME: {
        # Comparison-only (Workstream 1) - not part of the frozen 101.
        "type": "Enchantment", "mana_cost": "{G}", "cmc": 1,
        "text": "At the beginning of each of your main phases, if you haven't added mana with "
                "this ability this turn, you may add X mana of any one color, where X is the "
                "number of Islands target opponent controls.",
    },
}
NEW_CARD_DATA.update(D6_NEW_CARD_DATA)

# Birthing Ritual and Carpet of Flowers are real PERMANENTS (Enchantments) - the generic greedy
# loop's existing "any permanent type -> create a Perm" cast-execution path already handles them
# correctly, so they're registered in ACCELERATION for normal auto-casting consideration.
#
# Dark Ritual is deliberately EXCLUDED from ACCELERATION/any auto-cast class. It's an Instant with
# a net-mana effect the generic cast-execution path has no logic for (that path's only two
# outcomes for a non-permanent-type card are "goes to graveyard" or the two hardcoded Mox Diamond/
# Chrome Mox special cases) - if auto-cast through the generic path, it would silently pay {B} for
# zero effect (the card discarded, no mana ever produced), a real correctness bug, not a design
# choice. Dark Ritual is castable ONLY via try_cast_dark_ritual() below (dedicated, forced-only,
# matching this project's established BATTLEFIELD_SEARCH_ONLY/Formidable-Speaker-style pattern for
# mechanics the generic loop cannot execute correctly on its own).
NEW_ENGINE_CLASSES = {}
NEW_ACCELERATION = {"Birthing Ritual", CARPET_NAME}

# Dark Ritual Residue reuses the exact Lotus-Petal-style one-shot MANA_SOURCES pattern (see
# deckbuild006_cards.py's own Treasure Token precedent) - 3 separate Perm objects, each good for
# 1 unit of B, vanish once tapped (or simply left unused -> "stranded", tracked by the caller).
NEW_MANA_SOURCES = {
    DARK_RITUAL_RESIDUE_NAME: {"colors": {"B"}, "creature": False, "one_shot": True},
}


def install_new_card_tables():
    for name, cls in NEW_ENGINE_CLASSES.items():
        ohm.ENGINES[name] = cls
    for name in NEW_ACCELERATION:
        ohm.ACCELERATION.add(name)
    for name, spec in NEW_MANA_SOURCES.items():
        ohm.MANA_SOURCES[name] = spec

    from deckbuild006_cards import install_new_card_tables as install_d6
    install_d6()


def uninstall_new_card_tables():
    for name in NEW_ENGINE_CLASSES:
        ohm.ENGINES.pop(name, None)
    for name in NEW_ACCELERATION:
        ohm.ACCELERATION.discard(name)
    for name in NEW_MANA_SOURCES:
        ohm.MANA_SOURCES.pop(name, None)

    from deckbuild006_cards import uninstall_new_card_tables as uninstall_d6
    uninstall_d6()


def all_cards_dict(base_cards):
    merged = dict(NEW_CARD_DATA)
    merged.update(base_cards)
    return merged


def try_cast_dark_ritual(state, cards):
    """Pays Dark Ritual's real {B} cost from currently-untapped sources, then adds 3 one-shot B
    "residue" permanents (net +2 available B mana this turn only - matches real Magic's
    turn-atomic, non-carrying-over mana pool, consistent with this engine's existing convention).
    Returns True if cast. Caller decides WHEN to call this (see build_deckbuild007_e1... - this
    project's engine has no built-in lookahead, so Ritual usage is evaluated by dedicated
    dry-run/what-if logic in the analysis scripts, not the generic greedy development loop)."""
    from opening_hand_policy import _try_pay, _commit_payment, Perm
    if DARK_RITUAL_NAME not in state.hand:
        return False
    plan = _try_pay(state, 0, ["B"])
    if plan is None:
        return False
    _commit_payment(state, plan)
    state.hand.remove(DARK_RITUAL_NAME)
    state.graveyard.append(DARK_RITUAL_NAME)
    state.cast_log.append((state.turn, DARK_RITUAL_NAME, "ritual"))
    for _ in range(3):
        state.nonland_perms.append(Perm(DARK_RITUAL_RESIDUE_NAME, state.turn, False))
    return True


def sweep_stranded_dark_ritual_residue(state, turn):
    """Call once, after a turn's development is fully complete. Removes any unused residue units
    from THAT turn (real Dark Ritual mana empties at end of turn, never carries over) and returns
    how many of the 3 were stranded (0-3) - the direct 'stranded Ritual rate' input metric."""
    stranded = [
        p for p in state.nonland_perms
        if p.name == DARK_RITUAL_RESIDUE_NAME and p.entered_turn == turn and not p.tapped
    ]
    for p in stranded:
        state.nonland_perms.remove(p)
    return len(stranded)
