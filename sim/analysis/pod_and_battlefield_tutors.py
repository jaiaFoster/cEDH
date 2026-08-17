"""SIM-001 MULL-005R — Birthing Pod / Survival of the Fittest activation + battlefield-destination
tutors (Eldritch Evolution, Finale of Devastation, Nature's Rhythm, Chord of Calling, Crop
Rotation).

All of these are, mechanically, "put a card onto the battlefield/hand via a search effect that
this project's generic priority-class cast loop cannot express" - either because they're an
ACTIVATED ABILITY of an already-resolved permanent (Pod, Survival - not a card being cast from
hand at all), or because they're an X-cost spell the generic loop explicitly and correctly skips
for every OTHER card ('X spells not modeled in this greedy dev policy' - opening_hand_policy.py).
Rather than complicating that generic loop, each mechanic here is its own small, explicit,
INERT-BY-DEFAULT function - exactly the pattern SOLO-002R's fetchlands and MULL-005's tutor
resolution already established: nothing here fires unless trajectory_search.py's bounded search
explicitly forces a specific choice, so develop_turn's byte-for-byte default (pre-MULL-005R)
behavior is unaffected when these new parameters are omitted.

Disclosed simplification: Chord of Calling's Convoke (creatures may pay for {1} or one mana of
their color instead of mana) is NOT modeled - Chord's cost is paid in pure mana here, which only
UNDER-states its real castability, never over-states it (a conservative, disclosed choice -
t1_t3_trajectory_audit.json's Chord finding).
"""
from opening_hand_model import parse_cost

POD_NAME = "Birthing Pod"
SURVIVAL_NAME = "Survival of the Fittest"
POD_ACTIVATION_COST = "{1}{G/P}"
SURVIVAL_ACTIVATION_COST = "{G}"

# name -> (mana_cost_str, requires_sacrifice, mv_formula) where mv_formula(sac_mv) -> required
# target mv (exact for Eldritch Evolution's "X or less" collapsed to "= sac_mv+2" since a T1-T3
# search always wants the highest legal target, never a smaller one) or None if X-based (target
# mv IS X, chosen by the search itself, not derived from a sacrifice).
BATTLEFIELD_CREATURE_TUTORS = {
    "Eldritch Evolution": {"base_cost": "{1}{G}{G}", "sac_required": True, "x_based": False, "post_zone": "exile"},
    "Finale of Devastation": {"base_cost": "{G}{G}", "sac_required": False, "x_based": True, "post_zone": "graveyard"},
    "Nature's Rhythm": {"base_cost": "{G}{G}", "sac_required": False, "x_based": True, "post_zone": "graveyard"},
    "Chord of Calling": {"base_cost": "{G}{G}{G}", "sac_required": False, "x_based": True, "post_zone": "graveyard"},
}
BATTLEFIELD_LAND_TUTORS = {
    "Crop Rotation": {"cost": "{G}", "sac_required": True},
}


def try_activate_pod(state, cards, sac_name, target_name):
    """One Birthing Pod activation: sacrifice `sac_name` (a creature on the battlefield), search
    for `target_name` (mana value exactly sac's mv + 1) and put it onto the battlefield. Returns
    True/False; mutates state only on success. Called at most once per develop_turn invocation -
    a second activation the same turn is reached by simply calling develop_turn again next turn
    with the appropriate forced params (matches this deck's real T1-T3 mana constraints: two
    activations in one turn needs {3}{G/P}+{1}{G/P}x2 = ~8 mana, essentially never available this
    early)."""
    pod = next((p for p in state.nonland_perms if p.name == POD_NAME and not p.tapped), None)
    if pod is None:
        return False
    sac_perm = next(
        (p for p in state.nonland_perms if p.name == sac_name and "Creature" in cards[p.name]["type"] and p is not pod),
        None,
    )
    if sac_perm is None:
        return False
    if target_name not in state.library:
        return False
    sac_mv = cards[sac_name]["cmc"]
    target_mv = cards[target_name]["cmc"]
    if target_mv != sac_mv + 1:
        return False

    from opening_hand_policy import _try_pay, _commit_payment, Perm

    gen, pips, x = parse_cost(POD_ACTIVATION_COST)
    plan = _try_pay(state, gen, pips)
    if plan is None:
        return False
    _commit_payment(state, plan)
    pod.tapped = True
    state.nonland_perms.remove(sac_perm)
    state.graveyard.append(sac_perm.name)
    state.library.remove(target_name)
    state.nonland_perms.append(Perm(target_name, state.turn, True))
    state.cast_log.append((state.turn, target_name, "pod_found"))
    return True


def try_activate_survival(state, cards, discard_name, target_name):
    """One Survival of the Fittest activation: discard `discard_name` (a creature card in hand),
    search for ANY creature `target_name`, reveal, put into HAND (not battlefield - Survival does
    NOT bypass the found creature's own cast cost, unlike Pod/Chord/Eldritch Evolution/Finale/
    Nature's Rhythm). Repeatable per real Oracle text (no tap symbol) - callers may invoke this
    multiple times in the same develop_turn call if mana and fuel allow, mirroring how the
    trajectory search explores multi-activation lines."""
    survival = next((p for p in state.nonland_perms if p.name == SURVIVAL_NAME), None)
    if survival is None:
        return False
    if discard_name not in state.hand or "Creature" not in cards[discard_name]["type"]:
        return False
    if target_name not in state.library:
        return False

    from opening_hand_policy import _try_pay, _commit_payment

    gen, pips, x = parse_cost(SURVIVAL_ACTIVATION_COST)
    plan = _try_pay(state, gen, pips)
    if plan is None:
        return False
    # Elvish Spirit Guide is a real Creature (type line "Creature — Elf Spirit"), so it's a legal
    # Survival discard target by card type - but it is ALSO this engine's only hand-based mana
    # source ("Exile this card from your hand: Add {G}."). A payment plan that pays this
    # activation's own {G} cost by exiling discard_name itself is illegal: the card would already
    # be gone from hand by the time the discard cost needs to be paid, so it can't fund its own
    # discard. Reject rather than double-remove it from state.hand.
    if discard_name == "Elvish Spirit Guide" and any(ref == "__esg_virtual__" for ref, _ in plan):
        return False
    _commit_payment(state, plan)
    state.hand.remove(discard_name)
    state.graveyard.append(discard_name)
    state.library.remove(target_name)
    state.hand.append(target_name)
    state.cast_log.append((state.turn, discard_name, "survival_discard"))
    return True


def try_battlefield_creature_tutor(state, cards, tutor_name, target_name, sac_name=None):
    """Casts one of Eldritch Evolution / Finale of Devastation / Nature's Rhythm / Chord of
    Calling for exactly the X (or sacrifice) needed to legally find `target_name`, and puts it
    onto the battlefield - bypassing the target's own cast cost (including any additional cost,
    e.g. Abhorrent Oculus's exile-six-graveyard-cards), exactly like Birthing Pod. Only fires if
    `tutor_name` is currently in hand."""
    spec = BATTLEFIELD_CREATURE_TUTORS.get(tutor_name)
    if spec is None or tutor_name not in state.hand or target_name not in state.library:
        return False
    if "Creature" not in cards[target_name]["type"]:
        return False

    from opening_hand_policy import _try_pay, _commit_payment, Perm

    target_mv = cards[target_name]["cmc"]
    gen, pips, _ = parse_cost(spec["base_cost"])

    sac_perm = None
    if spec["sac_required"]:
        # Eldritch Evolution: X = 2 + sacrificed creature's mv (mv_offset default, backward
        # compatible). SIM-DECKBUILD-004's Neoform is the same mechanism shape with a real,
        # different offset (+1, exact per its own Oracle text, not "X or less") - generalized here
        # via an explicit mv_offset so this one function serves both cards correctly, rather than
        # hardcoding Eldritch Evolution's own number. A T1-3 search always wants the highest legal
        # target, so the search itself picks the sac creature that makes this equality exact
        # rather than exploring "X or less" targets below the ceiling (true for both cards' real
        # text: Eldritch Evolution's is an explicit "or less"; Neoform's is already an exact
        # match, so this collapsing is a no-op for Neoform, not an approximation).
        if sac_name is None:
            return False
        mv_offset = spec.get("mv_offset", 2)
        sac_perm = next((p for p in state.nonland_perms if p.name == sac_name and "Creature" in cards[p.name]["type"]), None)
        if sac_perm is None or target_mv != cards[sac_name]["cmc"] + mv_offset:
            return False
    elif spec["x_based"]:
        # X = target's own mv exactly, for the same reason - never overpay past the target found.
        if target_mv < 0:
            return False
        gen += int(target_mv)

    plan = _try_pay(state, gen, pips)
    if plan is None:
        return False
    _commit_payment(state, plan)
    state.hand.remove(tutor_name)
    if sac_perm is not None:
        state.nonland_perms.remove(sac_perm)
        state.graveyard.append(sac_perm.name)
    (state.exile if spec["post_zone"] == "exile" else state.graveyard).append(tutor_name)
    state.library.remove(target_name)
    state.nonland_perms.append(Perm(target_name, state.turn, True))
    state.cast_log.append((state.turn, target_name, "battlefield_tutor_found"))
    state.cast_log.append((state.turn, tutor_name, "tutor"))
    return True


def try_battlefield_land_tutor(state, cards, tutor_name, target_name):
    """Crop Rotation: sacrifice a land, search any land, put onto battlefield untapped."""
    spec = BATTLEFIELD_LAND_TUTORS.get(tutor_name)
    if spec is None or tutor_name not in state.hand or target_name not in state.library:
        return False
    if "Land" not in cards[target_name]["type"]:
        return False
    if not state.lands:
        return False

    from opening_hand_policy import _try_pay, _commit_payment, LandInPlay

    gen, pips, x = parse_cost(spec["cost"])
    plan = _try_pay(state, gen, pips)
    if plan is None:
        return False
    sac_land = state.lands[0]  # deterministic choice: sacrifice the first untapped-or-not land
    _commit_payment(state, plan)
    state.hand.remove(tutor_name)
    state.lands.remove(sac_land)
    state.graveyard.append(sac_land.name)
    state.graveyard.append(tutor_name)
    state.library.remove(target_name)
    state.lands.append(LandInPlay(target_name, state.turn, tapped=False))
    state.cast_log.append((state.turn, target_name, "battlefield_land_tutor_found"))
    state.cast_log.append((state.turn, tutor_name, "tutor"))
    return True
