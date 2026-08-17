"""SIM-DECKBUILD-004 — card data + engine hooks for the five candidate cards not in the current
98-card list: Neoform, Formidable Speaker, Talion the Kindly Lord, Seedborn Muse, An Offer You
Can't Refuse. Oracle text verified via WebSearch during this task (direct card-database fetches
were network-egress-blocked in this environment, same limitation as MANA-AUDIT-002) - moderate-
high confidence, not a raw authoritative pull. Mirrors mana_audit002_variants.py's pattern:
in-memory-only card rows, no fabricated scryfall_id anywhere real provenance is checked, global
tables extended in place (never overwritten) so opening_hand_policy.py's own aliases see them.

CRITICAL DISCLOSED LIMITATION (read before using Talion/Seedborn results): this project's T1-3
engine is a solo/no-opponent goldfish model (opening_hand_model.py's own docstring: "does NOT
model combat, opponents, the stack"). Talion's trigger source is "an opponent casts a spell with
mana value/power/toughness = the chosen number" - structurally absent here, same as Rhystic
Study/Smothering Tithe/Mystic Remora's existing opponent-triggered value (already handled by this
project's disclosed STRATEGIC_PRIOR_UNVALIDATED convention, see pod_realization_model.py).
Seedborn Muse is a STRICTLY HARDER case: its ability triggers ONLY on "each OTHER player's untap
step" - an event that cannot occur in ANY solo simulation at ANY turn count, not merely an
under-sampled one. Being "on the battlefield" in this engine's `any_engine_active` sense measures
CASTABILITY, not realized value, for both cards - but for Seedborn specifically, realized value is
100% architecturally invisible here, not merely uncertain. Every artifact this module's results
feed into carries this disclosure forward explicitly; see this task's final report.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402

NEW_CARD_DATA = {
    "Neoform": {
        "type": "Sorcery", "mana_cost": "{G}{U}", "cmc": 2,
        "text": "As an additional cost to cast this spell, sacrifice a creature. Search your "
                "library for a creature card with mana value equal to 1 plus the sacrificed "
                "creature's mana value, put that card onto the battlefield with an additional "
                "+1/+1 counter on it, then shuffle.",
    },
    "Formidable Speaker": {
        "type": "Creature — Elf Druid", "mana_cost": "{2}{G}", "cmc": 3,
        "text": "When this creature enters, you may discard a card. If you do, search your "
                "library for a creature card, reveal it, put it into your hand, then shuffle. "
                "{1}, T: Untap another target permanent.",
    },
    "Talion, the Kindly Lord": {
        "type": "Legendary Creature — Faerie Noble", "mana_cost": "{2}{U}{B}", "cmc": 4,
        "text": "Flying. As Talion, the Kindly Lord enters the battlefield, choose a number "
                "between 1 and 10. Whenever an opponent casts a spell with mana value, power, or "
                "toughness equal to the chosen number, that player loses 2 life and you draw a "
                "card.",
    },
    "Seedborn Muse": {
        "type": "Creature — Spirit", "mana_cost": "{3}{G}{G}", "cmc": 5,
        "text": "Untap all permanents you control during each other player's untap step.",
    },
    "An Offer You Can't Refuse": {
        "type": "Instant", "mana_cost": "{U}", "cmc": 1,
        "text": "Counter target noncreature spell. Its controller creates two Treasure tokens.",
    },
}

# ---- Neoform: reuses try_battlefield_creature_tutor's sac-required family exactly, generalized
# to a per-card mv_offset (Eldritch Evolution's hardcoded "+2" becomes the default; Neoform is the
# first card needing "+1", an EXACT target per its own real text, not "X or less" collapsed to a
# ceiling like Eldritch Evolution - functionally identical either way since a T1-3 search always
# wants the highest legal target).
NEOFORM_SPEC = {"base_cost": "{G}{U}", "sac_required": True, "x_based": False,
                 "post_zone": "exile", "mv_offset": 1}

# Talion/Seedborn: opponent-turn-dependent engines, added to the shared ENGINES taxonomy so
# T1-3 CASTABILITY registers correctly in any_engine_active/engine_count - realized value is a
# separate, disclosed question (see module docstring), never conflated with deployment.
# Formidable Speaker is ALSO added here (not just TUTORS below) so _card_class's engine-check
# (which runs BEFORE its tutor-check) recognizes it as a normal, generic-loop-castable permanent -
# it has real standalone body+untap-ability value, unlike Eldritch Evolution/Neoform, which do
# NOTHING useful cast through the generic loop and are correctly denylisted via
# BATTLEFIELD_SEARCH_ONLY below instead.
NEW_ENGINE_CLASSES = {
    "Talion, the Kindly Lord": "opponent_dependent_drain",
    "Seedborn Muse": "opponent_turn_untap_ARCHITECTURALLY_INVISIBLE_IN_SOLO_MODEL",
    "Formidable Speaker": "etb_tutor_to_hand_plus_untap_utility",
}

# Neoform requires a sacrifice as an additional cost and does NOTHING useful if cast through the
# generic priority-class loop's normal payment path (same reasoning as Eldritch Evolution/Chord/
# Finale/Nature's Rhythm/Crop Rotation, already denylisted in opening_hand_policy.BATTLEFIELD_
# SEARCH_ONLY) - reachable ONLY through its dedicated forced_battlefield_tutor mechanic.
NEOFORM_BATTLEFIELD_SEARCH_ONLY = {"Neoform"}

# An Offer You Can't Refuse: cheap hardcast-only counterspell (no pitch/alt-cost, unlike most of
# this deck's existing interaction suite), matching Flusterstorm/Swan Song/Silence's "cheap_stack"
# class - narrower than Force of Will/Negation (noncreature-only) and gives the countered
# controller 2 Treasures, a real, disclosed downside this project's interaction_model.py does not
# separately penalize (matches how Mana Vault/Ancient Tomb's life loss is tracked-but-never-
# blocking, not a claim the downside is irrelevant).
NEW_INTERACTION_CLASSES = {"An Offer You Can't Refuse": "cheap_stack"}


def install_new_card_tables():
    """Mutates opening_hand_model's shared tables IN PLACE (adds only). Idempotent.

    NOT called automatically at import time (unlike mana_audit002_variants.py's land-table
    install, which happened to never collide with any existing test's exact-set assertions) -
    ENGINES/TUTORS/INTERACTION_CASTABLE membership IS asserted exact-equal elsewhere in this
    suite (test_mull006_relevant_agency_model.py::test_every_interaction_castable_card_has_
    threat_axes), so leaking this module's additions into every OTHER test file that happens to
    import after this one - which is exactly what pytest's single-process collection does - broke
    that unrelated test on first contact. Callers (analysis scripts: call directly, once, at
    their own process's start; this task's own tests: use the `deckbuild004_tables` fixture
    below, which installs/uninstalls around each test so no mutation survives past this module's
    own test session)."""
    for name, cls in NEW_ENGINE_CLASSES.items():
        ohm.ENGINES[name] = cls
    for name, cls in NEW_INTERACTION_CLASSES.items():
        ohm.INTERACTION_CASTABLE[name] = cls
    ohm.TUTORS.add("Neoform")

    from pod_and_battlefield_tutors import BATTLEFIELD_CREATURE_TUTORS
    BATTLEFIELD_CREATURE_TUTORS["Neoform"] = NEOFORM_SPEC

    from opening_hand_policy import BATTLEFIELD_SEARCH_ONLY
    BATTLEFIELD_SEARCH_ONLY |= NEOFORM_BATTLEFIELD_SEARCH_ONLY


def uninstall_new_card_tables():
    """Exact inverse of install_new_card_tables() - removes only the keys this module added,
    restoring the shared tables to their pre-install state."""
    for name in NEW_ENGINE_CLASSES:
        ohm.ENGINES.pop(name, None)
    for name in NEW_INTERACTION_CLASSES:
        ohm.INTERACTION_CASTABLE.pop(name, None)
    ohm.TUTORS.discard("Neoform")

    from pod_and_battlefield_tutors import BATTLEFIELD_CREATURE_TUTORS
    BATTLEFIELD_CREATURE_TUTORS.pop("Neoform", None)

    from opening_hand_policy import BATTLEFIELD_SEARCH_ONLY
    BATTLEFIELD_SEARCH_ONLY -= NEOFORM_BATTLEFIELD_SEARCH_ONLY


def all_cards_dict(base_cards):
    merged = dict(NEW_CARD_DATA)
    merged.update(base_cards)
    return merged
