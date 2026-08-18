"""SIM-DECKBUILD-006 — card data for the new cards in the user-confirmed operative 98
(Lotho, Corrupt Shirriff / Grand Abolisher / Mockingbird), plus reuse of every other new card
already modeled in deckbuild004_cards.py (Neoform, Formidable Speaker, Talion the Kindly Lord,
Seedborn Muse, An Offer You Can't Refuse) and mana_audit002_variants.py (Scalding Tarn).

Oracle text verified via WebSearch during this task (same network-egress limitation as prior
tasks - direct card-database fetches blocked). "La abundancia de Yucahú" (the user's pasted list)
is a Spanish-language Secret Lair alt-name printing of Sylvan Library, already modeled under its
English name - normalized at ingestion, not a new card.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import opening_hand_model as ohm  # noqa: E402
from deckbuild004_cards import NEW_CARD_DATA as D4_NEW_CARD_DATA  # noqa: E402
from mana_audit002_variants import NEW_LAND_CARDS as MA002_NEW_LAND_CARDS  # noqa: E402

LOTHO_NAME = "Lotho, Corrupt Shirriff"
TREASURE_NAME = "Treasure Token"

NEW_CARD_DATA = {
    LOTHO_NAME: {
        "type": "Legendary Creature — Halfling Rogue", "mana_cost": "{W}{B}", "cmc": 2,
        "text": "Whenever a player casts their second spell each turn, you lose 1 life and "
                "create a Treasure token. (Spells cast before Lotho was on the battlefield still "
                "count toward that player's total, but a spell only triggers Lotho if Lotho was "
                "already on the battlefield when the SPECIFIC second-spell-of-the-turn event "
                "happened - see LOTHO_SPEC's implementation note.)",
    },
    "Grand Abolisher": {
        "type": "Creature — Human Cleric", "mana_cost": "{W}{W}", "cmc": 2,
        "text": "During your turn, your opponents can't cast spells or activate abilities of "
                "artifacts, creatures, or enchantments.",
    },
    "Mockingbird": {
        # Real cost is {X}{U}; this project's engine does not model X-spells in the generic
        # development loop (a long-standing, disclosed limitation - "X spells not modeled in
        # this greedy dev policy", already applied project-wide to Chord/Finale/Nature's Rhythm).
        # Modeled here at its X=0 floor - real mana value off the stack is 1 (just {U}, X=0 per
        # CR 706.3) - matching the assignment's own MV1_pool classification exactly. At X=0 it
        # has no legal copy target (mana value <= 0), so it is modeled as a vanilla 1/1 flying
        # Bird for T1-3 purposes - a real, disclosed floor value, not its full potential.
        "type": "Creature — Bird Bard", "mana_cost": "{U}", "cmc": 1,
        "text": "Flying. (X=0 floor modeling only - see module docstring; real card has an "
                "additional {X} cost and a copy-a-creature ETB choice not modeled here.)",
    },
    TREASURE_NAME: {
        "type": "Artifact", "mana_cost": "", "cmc": 0,
        "text": "T, Sacrifice: Add one mana of any color.",
    },
}
NEW_CARD_DATA.update(D4_NEW_CARD_DATA)
NEW_CARD_DATA.update(MA002_NEW_LAND_CARDS)

# Lotho and Grand Abolisher are real value/body engines - added to the shared ENGINES taxonomy
# so the generic loop casts them normally and any_engine_active/engine_count register correctly.
# Grand Abolisher's real protection effect (opponents can't act on your turn) is, like Talion's
# trigger, opponent-dependent and invisible to this solo engine - disclosed, not modeled as a
# combat/interaction-blocking effect. Mockingbird is deliberately NOT added to ENGINES (it's
# vanilla-body value at its modeled X=0 floor, not an engine).
NEW_ENGINE_CLASSES = {
    LOTHO_NAME: "self_and_opponent_triggered_treasure_drain",
    "Grand Abolisher": "opponent_dependent_protection",
}

# Treasure Token: a one-shot, any-color mana source - EXACTLY Lotus Petal's existing modeled
# behavior, reused verbatim (see MANA_SOURCES["Lotus Petal"]).
NEW_MANA_SOURCES = {
    TREASURE_NAME: {"colors": set(ohm.COLORS), "creature": False, "one_shot": True},
}

# Real spell-cast tags in state.cast_log (see opening_hand_policy.py / pod_and_battlefield_
# tutors.py) vs. non-cast tags (a found/discarded card, not a cast spell) - needed to correctly
# count "this player's Nth spell this turn" for Lotho's trigger. Land drops are never logged to
# cast_log at all (confirmed by inspection), so they never need excluding here.
NOT_A_SPELL_CAST_TAGS = {"pod_found", "battlefield_tutor_found", "battlefield_land_tutor_found", "survival_discard"}


def install_new_card_tables():
    """Mutates opening_hand_model's shared tables IN PLACE (adds only). NOT auto-installed at
    import time - see deckbuild004_cards.py's own docstring for why (a real cross-test-file
    pollution bug was found and fixed there; the same discipline applies here)."""
    for name, cls in NEW_ENGINE_CLASSES.items():
        ohm.ENGINES[name] = cls
    for name, spec in NEW_MANA_SOURCES.items():
        ohm.MANA_SOURCES[name] = spec
        ohm.ACCELERATION.add(name)

    from deckbuild004_cards import install_new_card_tables as install_d4
    install_d4()

    from mana_audit002_variants import install_new_land_tables as install_ma002
    install_ma002()


def uninstall_new_card_tables():
    for name in NEW_ENGINE_CLASSES:
        ohm.ENGINES.pop(name, None)
    for name in NEW_MANA_SOURCES:
        ohm.MANA_SOURCES.pop(name, None)
        ohm.ACCELERATION.discard(name)

    from deckbuild004_cards import uninstall_new_card_tables as uninstall_d4
    uninstall_d4()


def all_cards_dict(base_cards):
    merged = dict(NEW_CARD_DATA)
    merged.update(base_cards)
    return merged


def lotho_triggers_this_turn(state, turn):
    """True iff Lotho, Corrupt Shirriff (already on the battlefield BEFORE the relevant spell
    resolved) saw the CONTROLLING PLAYER's real "second spell" of `turn` resolve while it was in
    play. Real Oracle text triggers on ANY player's second spell each turn (not opponent-only) -
    in this solo T1-3 engine, the only player who ever casts a spell IS the pilot, so this is
    exactly the self-trigger case; a real multiplayer table's OPPONENT second-spell triggers are
    handled separately and qualitatively in E6 (this function only ever models the pilot's own
    second spell, which is real, always-available value, not a scenario estimate)."""
    lotho_perm = next((p for p in state.nonland_perms if p.name == LOTHO_NAME), None)
    if lotho_perm is None:
        return False
    real_casts_this_turn = [
        (i, name) for i, (t, name, cls) in enumerate(state.cast_log)
        if t == turn and cls not in NOT_A_SPELL_CAST_TAGS
    ]
    if len(real_casts_this_turn) < 2:
        return False
    second_spell_index = real_casts_this_turn[1][0]
    if lotho_perm.entered_turn < turn:
        return True  # Lotho already existed all turn - sees every real cast that turn
    lotho_index = next(
        (i for i, (t, name, cls) in enumerate(state.cast_log) if t == turn and name == LOTHO_NAME),
        None,
    )
    if lotho_index is None:
        return False
    return lotho_index < second_spell_index


def apply_lotho_trigger_if_any(state, turn):
    """Call once, after a turn's develop_turn() completes. Adds a Treasure (available starting
    the FOLLOWING develop_turn call - this post-hoc, end-of-turn check cannot retroactively fund
    THIS turn's already-completed payment decisions, a disclosed conservative simplification that
    can only UNDERSTATE Lotho's true same-turn value, never overstate it) and applies the
    controller's real 1-life cost. Returns True if it fired."""
    from opening_hand_policy import Perm
    if not lotho_triggers_this_turn(state, turn):
        return False
    state.nonland_perms.append(Perm(TREASURE_NAME, turn, False))
    state.life -= 1
    return True
