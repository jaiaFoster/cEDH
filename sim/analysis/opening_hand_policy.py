"""SIM-001 SOLO-002R — greedy deck-aware development policy + correct mana-source state.

CORRECTNESS-REPAIR NOTE (SOLO-002R): the original build of this module identified payment
sources via `_try_pay()` but never actually marked them spent for the rest of the turn -
`_consume_payment_sources()` only handled Elvish Spirit Guide and one-shot resources, so a land,
mana dork, Sol Ring, Mana Vault, Mox, etc. could be reused an unbounded number of times within
one turn. This is now fixed via real per-source `tapped` state (LandInPlay/Perm), a strict
search-then-commit payment protocol (`_try_pay` is a pure read-only search; `_commit_payment`
is the only thing that mutates tapped state), and an explicit untap step at the start of each
turn (`HandState.untap_all()`), with Mana Vault correctly excluded (its own Oracle text: "This
artifact doesn't untap during your untap step").

The policy is a single, hand-authored greedy heuristic (not a search/lookahead optimizer) - it is
explicitly NOT claimed to be a proven-optimal "expert" line, only a deck-aware sequencing better
than "play cards in random order," which is the actual bar this project needs to separate
"legally possible" from "what a reasonable player would do." Priority order is parameterized so
Part D's policy variants reuse this same engine. A separate bounded best-known-achievable search
(sim/analysis/achievable_search.py) tries alternate lines for a short list of named target
states, precisely because a single greedy line can under-report what a hand can actually do.
"""
import random
from opening_hand_model import (
    COLORS, parse_cost, LAND_COLOR_SETS, GENERIC_LANDS, ANCIENT_TOMB_LIFE_LOSS, FETCH_LANDS,
    FETCH_LAND_TARGET_TYPES, DUAL_LAND_BASIC_TYPES, BASIC_TYPE_COLOR,
    CRADLE, GEMSTONE_CAVERNS, EXOTIC_ORCHARD, CITY_OF_TRAITORS,
    MANA_SOURCES, ACCELERATION, TUTORS, INTERACTION_CASTABLE, ENGINES,
    PREMIUM_ONE_DROP_ENGINES, COMMANDERS,
)

DEFAULT_PRIORITY = ["free_accel", "paid_accel", "premium_engine", "commander", "engine", "tutor", "interaction"]

PERMANENT_TYPES = {"Creature", "Artifact", "Enchantment", "Planeswalker", "Land", "Battle"}


class LandInPlay:
    __slots__ = ("name", "tapped", "entered_turn", "has_luck_counter")

    def __init__(self, name, turn, tapped=False, has_luck_counter=False):
        self.name = name
        self.tapped = tapped
        self.entered_turn = turn
        self.has_luck_counter = has_luck_counter  # Gemstone Caverns only


class Perm:
    __slots__ = ("name", "entered_turn", "is_creature", "tapped", "never_untaps")

    def __init__(self, name, turn, is_creature, never_untaps=False):
        self.name = name
        self.entered_turn = turn
        self.is_creature = is_creature
        self.tapped = False
        self.never_untaps = never_untaps


def _is_land(name, cards):
    return "Land" in cards[name]["type"]


def _bottom_priority_score(name, cards):
    """Shared 'how much do we want to keep this card' scoring, used both for Gemstone Caverns'
    pregame exile choice and (via run_mulligan_sim.py's own copy) London mulligan bottoming.
    Higher = more worth keeping."""
    if name in TUTORS or name in ENGINES or name in PREMIUM_ONE_DROP_ENGINES:
        return 4
    if _is_land(name, cards) or name in ACCELERATION:
        return 3
    if name in INTERACTION_CASTABLE:
        return 2
    return 1


class HandState:
    def __init__(self, hand, library, on_play, rng, cards):
        self.hand = list(hand)
        self.library = list(library)
        self.on_play = on_play
        self.rng = rng
        self.cards = cards
        self.lands = []          # list[LandInPlay]
        self.nonland_perms = []  # list[Perm]
        self.graveyard = []
        self.exile = []
        self.life = 40
        self.turn = 0
        self.cast_log = []       # list of (turn, name, class)
        self.temp_mana_used_log = []  # (turn, source_name) - Lotus Petal only now (see MANA_SOURCES)
        self.mox_diamond_pending_discard = False
        self.landdrop_used = False
        # Captured right after the land drop, before any spell is cast this turn - "capacity this
        # turn" (how much mana/which colors this turn's board COULD produce in total). Distinct
        # from "currently affordable" (checked live against real remaining untapped sources after
        # some of this turn's mana has actually been spent) - see opening_hand_metrics.py for how
        # each is used. Both are legitimate, different questions; conflating them was part of the
        # original SOLO-002 approximation bug.
        self.turn_start_mana = 0
        self.turn_start_colors = set()
        self.command_zone = set(COMMANDERS.keys())
        _setup_gemstone_caverns(self)

    # ---- turn transitions ----
    def untap_all(self):
        """Real untap step. Mana Vault is correctly excluded (never_untaps) - it stays tapped
        until an explicit {4} untap-at-upkeep effect, which this T1-3 horizon model does not
        offer the policy (paying 4 mana to untap a rock that makes 3 is essentially never correct
        this early - documented simplification, not a missing feature)."""
        for land in self.lands:
            land.tapped = False
        for perm in self.nonland_perms:
            if not perm.never_untaps:
                perm.tapped = False

    # ---- mana availability (READ-ONLY - reflects only CURRENTLY UNTAPPED sources) ----
    def available_sources(self):
        """Returns [(ref, colors_or_None, count)] for untapped, non-sick sources only.
        colors_or_None=None -> pure generic mana, amount=count.
        colors_or_None=a set -> `count` mana this tap, each unit ONE color chosen from that set
        (count=1 for every source except Gaea's Cradle, whose count is live creature count -
        real Oracle text: "{T}: Add {G} for each creature you control")."""
        out = []
        for land in self.lands:
            if land.tapped:
                continue
            name = land.name
            if name == CRADLE:
                n = self.creature_count()
                if n > 0:
                    out.append((land, {"G"}, n))
                continue
            if name in GENERIC_LANDS:
                out.append((land, None, GENERIC_LANDS[name]))
                continue
            if name == EXOTIC_ORCHARD:
                # "Add one mana of any color that a land an opponent controls could produce" -
                # genuinely opponent-dependent; produces ZERO mana in this solo/no-opponent
                # structural model (documented choice, not an oversight - see module docstring
                # of opening_hand_model.py and the correctness-repair write-up for the
                # alternative of running explicit opponent-land-assumption scenarios instead).
                continue
            if name == GEMSTONE_CAVERNS:
                if land.has_luck_counter:
                    out.append((land, set(COLORS), 1))
                else:
                    out.append((land, None, 1))  # "{T}: Add {C}." - no luck counter case
                continue
            out.append((land, LAND_COLOR_SETS.get(name, set()), 1))
        controls_legendary = any(
            p.name in COMMANDERS or ("Legendary" in self.cards[p.name]["type"] and "Creature" in self.cards[p.name]["type"])
            for p in self.nonland_perms
        )
        for perm in self.nonland_perms:
            if perm.tapped:
                continue
            spec = MANA_SOURCES.get(perm.name)
            if not spec:
                continue
            if spec.get("creature") and perm.entered_turn == self.turn:
                continue  # summoning sick
            if spec.get("requires_legendary") and not controls_legendary:
                continue
            if "colors" in spec:
                out.append((perm, spec["colors"], 1))
            elif "generic" in spec:
                out.append((perm, None, spec["generic"]))
        # Elvish Spirit Guide: a zero-cost activated ability FROM HAND ("Exile this card from
        # your hand: Add {G}"), not a spell - modeled as a virtual untapped source while still in
        # hand, consumed (hand -> exile) only if actually used to pay for something.
        if "Elvish Spirit Guide" in self.hand:
            out.append(("__esg_virtual__", {"G"}, 1))
        return out

    def creature_count(self):
        return sum(1 for p in self.nonland_perms if p.name in COMMANDERS or "Creature" in self.cards[p.name]["type"])

    def total_mana_value(self):
        return sum(count for _, _, count in self.available_sources())

    def colors_available(self):
        colors = set()
        for _, c, _ in self.available_sources():
            if c is not None:
                colors |= c
        return colors


def _setup_gemstone_caverns(state):
    """Pregame action, real Oracle text: 'If this card is in your opening hand and you're not
    the starting player, you may begin the game with Gemstone Caverns on the battlefield with a
    luck counter on it. If you do, exile a card from your hand.' Only relevant on the draw -
    modeled as a policy decision (exiling a card is a real cost), not automatic: declines if the
    hand is already land-heavy enough that the exile isn't worth it."""
    if state.on_play or GEMSTONE_CAVERNS not in state.hand:
        return
    other_lands = sum(1 for c in state.hand if c != GEMSTONE_CAVERNS and _is_land(c, state.cards))
    if other_lands >= 4:
        return
    exile_candidates = [c for c in state.hand if c != GEMSTONE_CAVERNS]
    if not exile_candidates:
        return
    worst = min(exile_candidates, key=lambda c: _bottom_priority_score(c, state.cards))
    state.hand.remove(GEMSTONE_CAVERNS)
    state.hand.remove(worst)
    state.exile.append(worst)
    state.lands.append(LandInPlay(GEMSTONE_CAVERNS, 0, tapped=False, has_luck_counter=True))


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


# ---- fetchlands: real search over the deck's actual legal targets ----

def _legal_fetch_targets(state, fetch_name):
    types_wanted = FETCH_LAND_TARGET_TYPES.get(fetch_name, frozenset())
    return [
        name for name, types in DUAL_LAND_BASIC_TYPES.items()
        if (types & types_wanted) and name in state.library
    ]


def _fetch_potential_colors(state, fetch_name):
    """Colors reachable via this fetch's remaining legal targets right now - used only for
    land-drop SCORING (which land is worth playing), not for mana production itself."""
    colors = set()
    for name in _legal_fetch_targets(state, fetch_name):
        colors |= {BASIC_TYPE_COLOR[t] for t in DUAL_LAND_BASIC_TYPES[name]}
    return colors


def _crack_fetch(state, fetch_name, need_colors):
    """Real fetch resolution: search library for a legal target (by the fetch's actual printed
    basic types, not an assumed color pair), put it onto the battlefield untapped, sacrifice the
    fetch, lose 1 life, then the library's remaining order stands (removing one card from an
    already-uniformly-shuffled remainder is statistically equivalent to a fresh shuffle for a
    single Monte Carlo trial - no explicit reshuffle needed)."""
    targets = _legal_fetch_targets(state, fetch_name)
    if not targets:
        # No legal target left in the library (rare - would require this hand to have already
        # drawn/fetched every dual of the needed types). A real player wouldn't crack a whiffing
        # fetch; modeled as: the fetch enters battlefield inert (produces nothing, isn't
        # sacrificed) rather than losing the land drop outright.
        state.lands.append(LandInPlay(fetch_name, state.turn, tapped=True))
        return

    def score(name):
        colors = {BASIC_TYPE_COLOR[t] for t in DUAL_LAND_BASIC_TYPES[name]}
        return len(colors & need_colors) * 2 + len(colors) * 0.1

    targets.sort(key=score, reverse=True)
    chosen = targets[0]
    state.library.remove(chosen)
    state.lands.append(LandInPlay(chosen, state.turn, tapped=False))
    state.graveyard.append(fetch_name)
    state.life -= 1


def _maybe_sacrifice_city_of_traitors(state):
    """Real Oracle text: 'When you play another land, sacrifice this land.' Fires once, at most,
    per turn's land drop (a fetch's SEARCHED land does not itself count as 'playing a land', only
    the land played from hand does)."""
    for land in list(state.lands):
        if land.name == CITY_OF_TRAITORS:
            state.lands.remove(land)
            state.graveyard.append(CITY_OF_TRAITORS)


def _pick_land_to_play(state, cards, need_colors):
    candidates = [c for c in state.hand if _is_land(c, cards)]
    if not candidates:
        return None

    def score(land):
        if land in FETCH_LANDS:
            colors = _fetch_potential_colors(state, land)
            if not colors:
                return -10.0  # no legal target left - strongly avoid unless it's the only land
            return len(colors & need_colors) * 2 + len(colors) * 0.1 - 0.05  # marginal life-cost tiebreak
        if land == EXOTIC_ORCHARD:
            return -5.0  # produces zero mana in this solo model - avoid unless nothing else
        if land == GEMSTONE_CAVERNS:
            return 0.5  # colorless-only once played this way (no luck counter via a normal drop)
        if land in GENERIC_LANDS:
            return GENERIC_LANDS[land] * 0.5  # generic-only lands are a bit less flexible
        colors = LAND_COLOR_SETS.get(land, set())
        return len(colors & need_colors) * 2 + len(colors) * 0.1

    candidates.sort(key=score, reverse=True)
    return candidates[0]


# ---- payment: strict search (read-only) / commit (mutates) / rollback (undoes) ----

def _try_pay(state, cost_generic, cost_pips):
    """Pure read-only search over CURRENTLY UNTAPPED sources. Returns a payment plan
    [(ref, units)] if payable right now, else None. Never mutates state - callers that intend a
    real cast MUST call _commit_payment() with the returned plan; callers that only want to know
    "is this affordable right now" (a metrics dry-run) simply discard the plan."""
    avail = state.available_sources()
    used = {}  # id(ref) -> units already allocated within this attempt

    def capacity(ref, total):
        return total - used.get(id(ref), 0)

    remaining_pips = list(cost_pips)
    for pip in list(remaining_pips):
        need = pip if isinstance(pip, frozenset) else {pip}
        for (ref, colors, count) in avail:
            if colors is None or not (colors & need):
                continue
            if capacity(ref, count) > 0:
                used[id(ref)] = used.get(id(ref), 0) + 1
                remaining_pips.remove(pip)
                break
        else:
            return None
    if remaining_pips:
        return None

    remaining_generic = cost_generic
    for (ref, colors, count) in avail:
        if remaining_generic <= 0:
            break
        cap = capacity(ref, count)
        take = min(cap, remaining_generic)
        if take > 0:
            used[id(ref)] = used.get(id(ref), 0) + take
            remaining_generic -= take
    if remaining_generic > 0:
        return None

    ref_by_id = {id(ref): ref for (ref, colors, count) in avail}
    return [(ref_by_id[rid], units) for rid, units in used.items()]


def _commit_payment(state, plan):
    """The ONLY function that actually taps/consumes mana sources. A source's FULL count is
    spent the moment it's tapped at all (matches real Magic - you can't 'partially tap' a
    permanent), so any unit not needed for this specific payment is simply not produced/tracked
    beyond this call, consistent with this model's turn-atomic (not phase-by-phase) mana pool."""
    for ref, units in plan:
        if ref == "__esg_virtual__":
            if "Elvish Spirit Guide" in state.hand:
                state.hand.remove("Elvish Spirit Guide")
                state.exile.append("Elvish Spirit Guide")
                state.temp_mana_used_log.append((state.turn, "Elvish Spirit Guide"))
            continue
        if isinstance(ref, LandInPlay):
            ref.tapped = True
            if ref.name == "Ancient Tomb":
                state.life -= ANCIENT_TOMB_LIFE_LOSS
            continue
        if isinstance(ref, Perm):
            spec = MANA_SOURCES.get(ref.name)
            if spec and spec.get("one_shot"):
                if ref in state.nonland_perms:
                    state.nonland_perms.remove(ref)
                    state.graveyard.append(ref.name)
                    state.temp_mana_used_log.append((state.turn, ref.name))
            else:
                ref.tapped = True


def _rollback_payment(state, plans):
    """Undoes one or more _commit_payment() calls, in reverse order - used only by read-only
    joint-payability dry runs (can_pay_jointly), never by a real cast."""
    for plan in reversed(plans):
        for ref, units in plan:
            if ref == "__esg_virtual__":
                if "Elvish Spirit Guide" in state.exile:
                    state.exile.remove("Elvish Spirit Guide")
                    state.hand.append("Elvish Spirit Guide")
                    if (state.turn, "Elvish Spirit Guide") in state.temp_mana_used_log:
                        state.temp_mana_used_log.remove((state.turn, "Elvish Spirit Guide"))
                continue
            if isinstance(ref, LandInPlay):
                ref.tapped = False
                if ref.name == "Ancient Tomb":
                    state.life += ANCIENT_TOMB_LIFE_LOSS
                continue
            if isinstance(ref, Perm):
                spec = MANA_SOURCES.get(ref.name)
                if spec and spec.get("one_shot"):
                    if ref.name in state.graveyard:
                        state.graveyard.remove(ref.name)
                    if (state.turn, ref.name) in state.temp_mana_used_log:
                        state.temp_mana_used_log.remove((state.turn, ref.name))
                    ref.tapped = False
                    if ref not in state.nonland_perms:
                        state.nonland_perms.append(ref)
                else:
                    ref.tapped = False


def can_pay_jointly(state, costs):
    """costs: list of (generic, pips) tuples. Returns True only if ALL are simultaneously
    payable from CURRENTLY UNTAPPED sources via one real allocation (sequential greedy commit,
    then roll back before returning) - a genuine joint check, not independent per-cost isolation.
    This is what publication-facing combination metrics (engine+interaction, multi-piece combo
    zero-step, commander+activation) must use instead of checking each cost against the same
    unmodified pool, which can silently double-count a single shared source."""
    plans = []
    ok = True
    for gen, pips in costs:
        plan = _try_pay(state, gen, pips)
        if plan is None:
            ok = False
            break
        _commit_payment(state, plan)
        plans.append(plan)
    _rollback_payment(state, plans)
    return ok


def is_currently_castable(state, gen, pips):
    """Single-cost read-only affordability check against CURRENT remaining untapped sources
    (i.e., what's actually left after whatever has already been cast this turn) - the correct
    replacement for the old turn-start-pool 'isolation' approximation. See
    individually_affordable_from_turn_capacity in opening_hand_metrics.py for the explicitly
    weaker, clearly-labeled diagnostic that checks against the turn's full starting capacity
    instead (never presented as simultaneous/current availability)."""
    return _try_pay(state, gen, pips) is not None


def develop_turn(state, cards, priority_order=DEFAULT_PRIORITY, hold_interaction=False, forced_land=None):
    """Mutates state for one turn: untap, draw, land drop, greedy casts. Returns actions taken.
    forced_land: if given (and present in hand), overrides the greedy land-choice heuristic -
    used only by achievable_search.py's bounded alternate-line search, never by the default
    policy_realized line."""
    state.turn += 1
    state.untap_all()
    actions = []
    if not (state.turn == 1 and state.on_play):
        if state.library:
            drawn = state.library.pop(0)
            state.hand.append(drawn)
            actions.append(("draw", drawn))

    need_colors = set()
    for c in state.hand:
        if _is_land(c, cards):
            continue
        _, pips, _ = parse_cost(cards[c]["mana_cost"])
        for p in pips:
            need_colors |= (p if isinstance(p, frozenset) else {p})
    if forced_land is not None and forced_land in state.hand and _is_land(forced_land, cards):
        land = forced_land
    else:
        land = _pick_land_to_play(state, cards, need_colors or set(COLORS))
    if land:
        state.hand.remove(land)
        _maybe_sacrifice_city_of_traitors(state)
        if land in FETCH_LANDS:
            _crack_fetch(state, land, need_colors or set(COLORS))
        else:
            state.lands.append(LandInPlay(land, state.turn))
        actions.append(("land", land))

    state.turn_start_mana = state.total_mana_value()
    state.turn_start_colors = state.colors_available()

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
                plan = _try_pay(state, gen, pips)
                if plan is not None:
                    best = (c, gen, pips, plan)
                    break
            if best:
                c, gen, pips, plan = best
                if cls == "commander":
                    state.command_zone.discard(c)
                    state.nonland_perms.append(Perm(c, state.turn, True))
                    _commit_payment(state, plan)
                    actions.append(("cast", c, "commander"))
                    state.cast_log.append((state.turn, c, "commander"))
                    changed = True
                    break
                state.hand.remove(c)
                is_creature = "Creature" in cards[c]["type"]
                if c == "Mox Diamond":
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
                elif any(t in cards[c]["type"] for t in PERMANENT_TYPES):
                    never_untaps = MANA_SOURCES.get(c, {}).get("never_untaps", False)
                    state.nonland_perms.append(Perm(c, state.turn, is_creature, never_untaps=never_untaps))
                else:
                    # Instant/Sorcery: resolves and goes to the graveyard, not the battlefield -
                    # it must never linger in nonland_perms (would corrupt engine/creature-count/
                    # persistent-resource accounting for every interaction spell and most tutors).
                    state.graveyard.append(c)
                _commit_payment(state, plan)
                actions.append(("cast", c, _card_class(c, cards)))
                state.cast_log.append((state.turn, c, _card_class(c, cards)))
                changed = True
                break
    return actions
