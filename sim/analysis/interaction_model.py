"""SIM-001 SOLO-003 — real alternate-cost interaction model.

SOLO-002R (and the original SOLO-002) checked interaction castability using ONLY each card's
printed mana cost (`cards[name]["mana_cost"]`), ignoring every free/pitch/sacrifice alternate
cost entirely. That understated live-interaction rates for exactly the cards this deck plays
interaction for in the first place (Force of Will, Fierce Guardianship, etc. are only premium
because of their alternate costs). This module is the authoritative "is this card live right
now" check for every piece of INTERACTION_CASTABLE, covering each card's REAL Oracle text
(verified against data/cards_cache/oracle-2026-08-12, see the correctness-repair conversation
this module was built in response to).

Two structural limitations, disclosed rather than silently approximated:
  - This is a solo/no-opponent Level 1-2 model: there is no opponent turn, no opponent spell
    stack, and no observable opponent action count. Any alternate cost or trigger condition that
    depends on those (Force of Negation's "if it's not your turn", Mindbreak Trap's "if an
    opponent cast three or more spells this turn") is therefore STRUCTURALLY NEVER available
    here - not a missing feature, a genuine consequence of the model's scope. Both cards still
    have their real printed mana cost checked normally.
  - "Live" here means "payable" (mana or alternate cost), not "has a legal target" - none of
    these interaction spells' actual targets (an opponent's spell, permanent, etc.) exist in a
    solo goldfish model. A hand's "live interaction" count is therefore an upper bound on
    genuinely useful interaction, not a claim that a target would exist in a real game at that
    exact moment. Disclosed in every write-up that cites this metric.
"""
from opening_hand_model import parse_cost, card_colors, COMMANDERS

# type: "pitch" (exile N cards of a color from hand, not counting the card itself),
#       "sac_creature" (sacrifice a nontoken creature of a color),
#       "free_if_commander" (Fierce Guardianship),
#       "structurally_unavailable" (real alt cost exists but its condition can never be true in
#           this solo/no-opponent model - printed mana cost is the only live path),
#       "always_via_life" (Phyrexian mana with a life-payment half - modeled as always payable
#           given this model's life totals never approach the danger zone in a T1-4 window)
ALT_COST_SPECS = {
    "Force of Will": {"type": "pitch", "color": "U", "n": 1, "life": 1},
    "Force of Negation": {"type": "structurally_unavailable"},  # "if it's not your turn"
    "Fierce Guardianship": {"type": "free_if_commander"},
    "Flare of Denial": {"type": "sac_creature", "color": "U"},
    "Subtlety": {"type": "pitch", "color": "U", "n": 1},
    "Mindbreak Trap": {"type": "structurally_unavailable"},  # "if an opponent cast 3+ spells"
    "Misdirection": {"type": "pitch", "color": "U", "n": 1},
    "Commandeer": {"type": "pitch", "color": "U", "n": 2},
    "Endurance": {"type": "pitch", "color": "G", "n": 1},
    "Mental Misstep": {"type": "always_via_life"},
    # Pact of Negation needs no alt-cost entry: its printed cost is already {0}, so the normal
    # mana-cost path already correctly reports it as always castable. What it's MISSING is the
    # deferred-obligation TRACKING, handled separately (see pact_of_negation_obligation below) -
    # per the correctness-repair instruction to account for castability and downstream
    # obligation SEPARATELY, not as a gate on castability.
}

PACT_DEFERRED_COST = "{3}{U}{U}"


def _pitchable_cards(name, state, cards, color, n):
    others = [c for c in state.hand if c != name and color in card_colors(c, cards)]
    return others[:n] if len(others) >= n else None


def _sacrificeable_creature(name, state, cards, color):
    from opening_hand_model import COMMANDERS
    for p in state.nonland_perms:
        if p.name in COMMANDERS:
            continue  # commanders aren't in `cards` (they're not library cards) - and shouldn't be sac fodder anyway
        if "Creature" in cards[p.name]["type"] and color in card_colors(p.name, cards):
            return p
    return None


def interaction_is_live(name, state, cards):
    """Metrics-facing check: is this card castable RIGHT NOW via its printed mana cost or a
    real, actually-available alternate cost? Does not mutate state."""
    from opening_hand_policy import is_currently_castable
    gen, pips, x = parse_cost(cards[name]["mana_cost"])
    mana_ok = (x == 0) and is_currently_castable(state, gen, pips)
    spec = ALT_COST_SPECS.get(name)
    if not spec:
        return mana_ok
    t = spec["type"]
    if t == "structurally_unavailable":
        return mana_ok
    if t == "always_via_life":
        return mana_ok or (state.life > 2)
    if t == "free_if_commander":
        return mana_ok or any(p.name in COMMANDERS for p in state.nonland_perms)
    if t == "pitch":
        return mana_ok or _pitchable_cards(name, state, cards, spec["color"], spec["n"]) is not None
    if t == "sac_creature":
        return mana_ok or _sacrificeable_creature(name, state, cards, spec["color"]) is not None
    return mana_ok


def resolve_interaction_cast(name, state, cards):
    """Cast-time resolution for develop_turn's real casting loop: returns a descriptor of HOW to
    pay (so the caller can apply the correct side effects), preferring real mana payment when
    available, falling back to the alternate cost only when mana payment fails. Returns None if
    uncastable via any path right now.

    Descriptor shapes: ("mana", plan) | ("pitch", [cards]) | ("sac", perm) | ("free", None)
    """
    from opening_hand_policy import _try_pay
    gen, pips, x = parse_cost(cards[name]["mana_cost"])
    if x == 0:
        plan = _try_pay(state, gen, pips)
        if plan is not None:
            return ("mana", plan)
    spec = ALT_COST_SPECS.get(name)
    if not spec:
        return None
    t = spec["type"]
    if t == "always_via_life" and state.life > 2:
        return ("free", None)  # Mental Misstep's life-payment half: no mana, no exile/sac needed
    if t == "free_if_commander" and any(p.name in COMMANDERS for p in state.nonland_perms):
        return ("free", None)
    if t == "pitch":
        pitched = _pitchable_cards(name, state, cards, spec["color"], spec["n"])
        if pitched is not None:
            return ("pitch", pitched)
    if t == "sac_creature":
        target = _sacrificeable_creature(name, state, cards, spec["color"])
        if target is not None:
            return ("sac", target)
    return None


def commit_interaction_cast(name, resolution, state):
    """Applies the non-mana side effects of an alternate-cost interaction cast. Mana-path
    ("mana", plan) commits are handled by the normal _commit_payment() call in develop_turn -
    this function only handles the alternate-cost branches."""
    kind, payload = resolution
    if kind == "pitch":
        for c in payload:
            if c in state.hand:
                state.hand.remove(c)
                state.exile.append(c)
    elif kind == "sac":
        if payload in state.nonland_perms:
            state.nonland_perms.remove(payload)
            state.graveyard.append(payload.name)
    elif kind == "free":
        pass  # Fierce Guardianship (commander) / Mental Misstep (life) - no further cost
    if name == "Pact of Negation":
        state.pact_of_negation_obligations.append({
            "cast_turn": state.turn, "due_turn": state.turn + 1, "cost": PACT_DEFERRED_COST,
        })
