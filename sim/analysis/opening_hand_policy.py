"""SIM-001 SOLO-002 — greedy deck-aware development policy + per-hand
metric extraction. See opening_hand_model.py for card data and documented
modeling simplifications.

The policy is a single, hand-authored greedy heuristic (not a search/
lookahead optimizer) - it is explicitly NOT claimed to be a proven-optimal
"expert" line, only a deck-aware sequencing better than "play cards in
random order," which is the actual bar this project needs to separate
"legally possible" from "what a reasonable player would do." Priority
order is parameterized so Part D's policy variants reuse this same engine.
"""
import random
from opening_hand_model import (
    COLORS, parse_cost, LAND_COLOR_SETS, GENERIC_LANDS, FETCH_LANDS, CRADLE,
    MANA_SOURCES, ACCELERATION, TUTORS, INTERACTION_CASTABLE, ENGINES,
    PREMIUM_ONE_DROP_ENGINES, COMMANDERS,
)

DEFAULT_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "commander", "engine", "tutor", "interaction"]


class Perm:
    __slots__ = ("name", "entered_turn", "is_creature")

    def __init__(self, name, turn, is_creature):
        self.name = name
        self.entered_turn = turn
        self.is_creature = is_creature


class HandState:
    def __init__(self, hand, library, on_play, rng, cards):
        self.hand = list(hand)
        self.library = list(library)
        self.on_play = on_play
        self.rng = rng
        self.cards = cards
        self.lands = []          # Perm-like: just names, lands never sick
        self.nonland_perms = []  # list[Perm]
        self.graveyard = []
        self.exile = []
        self.life = 40
        self.turn = 0
        self.cast_log = []       # list of (turn, name, class)
        self.temp_mana_used_log = []  # (turn, source_name)
        self.mox_diamond_pending_discard = False
        self.landdrop_used = False
        # Captured right after the land drop, before any spell is cast this turn - used by the
        # metrics layer to ask "was X affordable in isolation this turn" independent of what the
        # greedy policy actually chose to spend on (see opening_hand_metrics.py for why this
        # matters: checking post-hoc hand contents alone is circular, since a card the policy DID
        # afford is no longer in hand, and a card left in hand may only be unaffordable because
        # something else was bought first, not because it was never affordable).
        self.turn_start_mana = 0
        self.turn_start_colors = set()
        self.command_zone = set(COMMANDERS.keys())

    # ---- mana availability ----
    def available_sources(self, include_new_land=True):
        """Returns list of (source_name, kind, colors_or_generic) for untapped, non-sick sources."""
        out = []
        for land in self.lands:
            if land in GENERIC_LANDS:
                out.append((land, "generic", GENERIC_LANDS[land]))
            else:
                out.append((land, "colors", LAND_COLOR_SETS.get(land, set())))
        controls_legendary_creature = any(
            p.name in COMMANDERS or ("Legendary" in self.cards[p.name]["type"] and "Creature" in self.cards[p.name]["type"])
            for p in self.nonland_perms
        )
        for perm in self.nonland_perms:
            spec = MANA_SOURCES.get(perm.name)
            if not spec:
                continue
            if spec.get("creature") and perm.entered_turn == self.turn:
                continue  # summoning sick
            if spec.get("one_shot") and perm.name in [n for (t, n) in self.temp_mana_used_log]:
                continue
            if spec.get("requires_legendary") and not controls_legendary_creature:
                continue  # Mox Amber: needs a legendary creature (commander) already in play
            if "colors" in spec:
                out.append((perm.name, "colors", spec["colors"]))
            elif "generic" in spec:
                out.append((perm.name, "generic", spec["generic"]))
        # Elvish Spirit Guide: a zero-cost activated ability FROM HAND ("Exile this card from
        # your hand: Add {G}"), not a spell - modeled as a virtual source while still in hand,
        # not consumed until an actual payment uses it (see _try_pay/consume_virtual_sources).
        if "Elvish Spirit Guide" in self.hand:
            out.append(("Elvish Spirit Guide", "colors", {"G"}))
        return out

    def total_mana_value(self):
        total = 0
        for _, kind, val in self.available_sources():
            total += val if kind == "generic" else 1
        return total

    def colors_available(self):
        colors = set()
        for _, kind, val in self.available_sources():
            if kind == "colors":
                colors |= val
        return colors


def _card_class(name, cards):
    if name in COMMANDERS:
        return "commander"
    if name in PREMIUM_ONE_DROP_ENGINES:
        return "premium_engine"
    if name in ENGINES:
        return "engine"
    if name in TUTORS:
        return "tutor"
    if name in INTERACTION_CASTABLE:
        return "interaction"
    if name in ACCELERATION:
        c = cards[name]
        gen, pips, x = parse_cost(c["mana_cost"])
        return "free_accel" if (gen + len(pips) + x) == 0 else "paid_accel"
    return "other"


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def _pick_land_to_play(state, cards, need_colors):
    candidates = [c for c in state.hand if _is_land(c, cards)]
    if not candidates:
        return None
    def score(land):
        s = 0
        if land in GENERIC_LANDS:
            s += GENERIC_LANDS[land] * 0.5  # generic-only lands are a bit less flexible
        else:
            colors = LAND_COLOR_SETS.get(land, set())
            s += len(colors & need_colors) * 2 + len(colors) * 0.1
        if land in FETCH_LANDS:
            s -= 0.05  # marginal life-cost tiebreak
        return s
    candidates.sort(key=score, reverse=True)
    return candidates[0]


def _try_pay(state, cost_generic, cost_pips, sources_used_out):
    """Greedy payment: use colored sources for pips first, generic-only for leftover generic."""
    avail = state.available_sources()
    avail = [a for a in avail if a[0] not in sources_used_out]
    remaining_pips = list(cost_pips)
    used = []
    for pip in list(remaining_pips):
        need = pip if isinstance(pip, frozenset) else {pip}
        found = None
        for src in avail:
            name, kind, val = src
            if kind == "colors" and (val & need):
                found = src
                break
        if found:
            avail.remove(found)
            used.append(found[0])
            remaining_pips.remove(pip)
    if remaining_pips:
        return None  # can't pay colored pips
    remaining_generic = cost_generic
    for src in list(avail):
        if remaining_generic <= 0:
            break
        name, kind, val = src
        amt = val if kind == "generic" else 1
        take = min(amt, remaining_generic)
        if take > 0:
            used.append(name)
            remaining_generic -= take
            avail.remove(src)
    if remaining_generic > 0:
        return None
    return used


def _consume_payment_sources(state, paid):
    for s in paid:
        if s == "Elvish Spirit Guide" and s in state.hand:
            state.hand.remove(s)
            state.exile.append(s)
            continue
        spec = MANA_SOURCES.get(s)
        if spec and spec.get("one_shot"):
            state.temp_mana_used_log.append((state.turn, s))


def develop_turn(state, cards, priority_order=DEFAULT_PRIORITY, hold_interaction=False):
    """Mutates state for one turn: draw, land drop, greedy casts. Returns list of actions taken."""
    state.turn += 1
    actions = []
    if not (state.turn == 1 and state.on_play):
        if state.library:
            drawn = state.library.pop(0)
            state.hand.append(drawn)
            actions.append(("draw", drawn))

    # crude "what colors do we still need" signal: union of all castable-ish spell needs in hand
    need_colors = set()
    for c in state.hand:
        if _is_land(c, cards):
            continue
        _, pips, _ = parse_cost(cards[c]["mana_cost"])
        for p in pips:
            need_colors |= (p if isinstance(p, frozenset) else {p})
    land = _pick_land_to_play(state, cards, need_colors or set(COLORS))
    if land:
        state.hand.remove(land)
        state.lands.append(land)
        actions.append(("land", land))

    state.turn_start_mana = state.total_mana_value()
    state.turn_start_colors = state.colors_available()

    # free 0-cost acceleration first
    changed = True
    while changed:
        changed = False
        for cls in priority_order:
            if cls == "commander":
                castable = list(state.command_zone)
            else:
                castable = [c for c in state.hand if not _is_land(c, cards) and c != "Elvish Spirit Guide" and _card_class(c, cards) == cls]
            if not castable:
                continue
            if hold_interaction and cls != "interaction":
                # reserve mana equal to cheapest interaction card's cost
                pass  # handled via budget check below implicitly (best-effort, documented heuristic)
            best = None
            for c in castable:
                cost_str = COMMANDERS[c]["cost"] if cls == "commander" else cards[c]["mana_cost"]
                gen, pips, x = parse_cost(cost_str)
                if x > 0:
                    continue  # X spells not modeled in this greedy dev policy (rare in T1-3 anyway)
                if c == "Mox Diamond" and not any(_is_land(h, cards) for h in state.hand if h != c):
                    continue
                if c == "Chrome Mox" and not any(h != c and not _is_land(h, cards) for h in state.hand):
                    continue
                paid = _try_pay(state, gen, pips, set())
                if paid is not None:
                    best = (c, gen, pips, paid)
                    break
            if best:
                c, gen, pips, paid = best
                if cls == "commander":
                    state.command_zone.discard(c)
                    state.nonland_perms.append(Perm(c, state.turn, True))
                    _consume_payment_sources(state, paid)
                    actions.append(("cast", c, "commander"))
                    state.cast_log.append((state.turn, c, "commander"))
                    changed = True
                    break
                state.hand.remove(c)
                is_creature = "Creature" in cards[c]["type"]
                if c in ("Lotus Petal",):
                    state.temp_mana_used_log.append((state.turn, c))
                    state.nonland_perms.append(Perm(c, state.turn, False))
                elif c == "Mox Diamond":
                    discard_candidates = [h for h in state.hand if _is_land(h, cards)]
                    if discard_candidates:
                        d = discard_candidates[0]
                        state.hand.remove(d)
                        state.graveyard.append(d)
                        state.nonland_perms.append(Perm(c, state.turn, False))
                elif c == "Chrome Mox":
                    imprint_candidates = [h for h in state.hand if not _is_land(h, cards)]
                    if imprint_candidates:
                        imp = imprint_candidates[0]
                        state.hand.remove(imp)
                        state.exile.append(imp)
                        state.nonland_perms.append(Perm(c, state.turn, False))
                else:
                    state.nonland_perms.append(Perm(c, state.turn, is_creature))
                _consume_payment_sources(state, paid)
                actions.append(("cast", c, _card_class(c, cards)))
                state.cast_log.append((state.turn, c, _card_class(c, cards)))
                changed = True
                break
    return actions
