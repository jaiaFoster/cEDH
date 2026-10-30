"""SIM-DECKBUILD-008 — goldfish development engine + London mulligan policies.

Plays turns 1..N of a single deck with NO opponent (run class DECK_BACKED_GOLDFISH). Each turn:
untap, draw, check for a deterministic win at sorcery speed (deckbuild008_solver), otherwise
develop greedily (land, free mana, mana sources, premium engines, commanders, other permanents),
then check the instant-speed window that exists during the opponents' turns using the mana left
untapped.

Simplifications (all variants share them, so comparisons are paired and fair):
  * No opponent draws/spells: Rhystic Study / Mystic Remora / Smothering Tithe / Tymna produce no
    cards. An optional `engine_draws` scenario adds +1 card per turn per deployed card-advantage
    engine (max 2) as a labeled sensitivity band.
  * Interaction is never cast in the goldfish; it matters only as protection for a found win.
  * Birthing Pod / Survival are not activated for incremental value; they are used by the solver
    when they complete a deterministic line.
  * Tutors: policy "engine_tutor" (default) lets Demonic Tutor / Imperial Seal / Vampiric Tutor
    fetch a premium engine on turns 1-2 when the hand has none; "hold" keeps every tutor for
    conversion. Both are reported.
"""
from __future__ import annotations

import random
from collections import Counter

import deckbuild008_cards as dc
from deckbuild008_cards import ANY, C, G, U, B, W
import deckbuild008_solver as sv
from deckbuild008_solver import Perm, Snapshot

FAST_MANA = {"Sol Ring", "Mana Vault", "Chrome Mox", "Mox Diamond", "Lotus Petal", "Elvish Spirit Guide",
             "Arcane Signet"}
DORKS = {n for n, (k, _) in dc.MANA_PERMS.items() if k == "dork"}
CA_ENGINES = {"Rhystic Study", "Mystic Remora", "Smothering Tithe", "Esper Sentinel"}
LEGENDARY_CREATURES = set(sv.LEGENDARY_COLORS)

# Development priority (lower index = cast first when affordable).
PRIORITY = [
    "Sol Ring", "Mana Vault", "Arcane Signet",
    "Birds of Paradise", "Noble Hierarch", "Delighted Halfling", "Deathrite Shaman",
    "Avacyn's Pilgrim", "Llanowar Elves", "Elvish Mystic", "Fyndhorn Elves", "Elves of Deep Shadow",
    "Arbor Elf", "Boreal Druid", "Gilded Goose",
    "Mystic Remora", "Esper Sentinel",
    "Birthing Pod", "Survival of the Fittest", "Rhystic Study", "Kinnan, Bonder Prodigy",
    "Smothering Tithe",
    "Thrasios, Triton Hero", "Tymna the Weaver",
    "Badgermole Cub", "Devoted Druid", "Enduring Vitality", "Delney, Streetwise Lookout",
    "Lotho, Corrupt Shirriff", "The Cabbage Merchant", "The Queen of Dale", "Faerie Mastermind",
    "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos", "Gleaming Splendor",
    "Training Grounds", "Biomancer's Familiar", "Seedborn Muse", "Shang-Chi, Master of Kung Fu",
    "Hermit Druid", "Divining Witch", "Oboro Breezecaller", "Derevi, Empyrial Tactician",
    "High Fae Trickster", "Teferi, Mage of Zhalfir",
]
PREMIUM = dc.PREMIUM_ENGINES - {"Abhorrent Oculus"}


def pay_take(units: Counter, pips, generic):
    """Pay and return the remaining pool (spends least-flexible units first), or None."""
    hard = sorted([p for p in pips if "P" not in p], key=len)
    pool = Counter(units)
    for pip in hard:
        cands = [k for k in pool if pool[k] and (k & pip)]
        if not cands:
            return None
        k = min(cands, key=len)
        pool[k] -= 1
    for _ in range(generic):
        cands = [k for k in pool if pool[k]]
        if not cands:
            return None
        k = min(cands, key=lambda k: (k != C, len(k)))
        pool[k] -= 1
    if not sv.pay(units, pips, generic):
        return None
    return +pool


# ---- mulligan policies ----------------------------------------------------------------------------

def hand_features(hand, on_play):
    lands = [c for c in hand if dc.is_land(c)]
    nl = len(lands)
    fast = 0
    for c in hand:
        if c in ("Sol Ring", "Mana Vault", "Lotus Petal", "Arcane Signet"):
            fast += 1
        elif c == "Mox Diamond" and nl >= 2:
            fast += 1
        elif c == "Chrome Mox" and any(not dc.is_land(x) and x != c for x in hand):
            fast += 1
        elif c == "Elvish Spirit Guide":
            fast += 0.5
    dorks = sum(1 for c in hand if c in DORKS and c != "Devoted Druid")
    mana_total = nl + fast + dorks
    t1_mana = min(nl, 1) + fast
    t2_mana = min(nl, 2) + fast + (dorks if nl >= 1 else 0)
    t1_action = any((c in DORKS or c in ("Mystic Remora", "Esper Sentinel", "Sol Ring", "Mana Vault"))
                    and dc.mv(c) <= t1_mana for c in hand if not dc.is_land(c)) and nl >= 1
    eng_t2 = [c for c in hand if c in PREMIUM and dc.mv(c) <= t2_mana]
    conditional_only = bool(eng_t2) and set(eng_t2) <= {"Rhystic Study", "Smothering Tithe"}
    tutors = [c for c in hand if c in dc.TUTORS and c not in ("Crop Rotation",)]
    interaction = [c for c in hand if c in dc.INTERACTION or c in dc.PROACTIVE_PROTECTION]
    combo_pair = (("Thassa's Oracle" in hand and ({"Demonic Consultation", "Tainted Pact"} & set(hand)))
                  or ({"Devoted Druid", "Swift Reconfiguration"} <= set(hand)))
    return {"lands": nl, "mana_total": mana_total, "t1_action": t1_action, "eng_t2": eng_t2,
            "conditional_only": conditional_only, "tutors": len(tutors),
            "interaction": len(interaction), "combo_pair": bool(combo_pair), "t2_mana": t2_mana}


def proactive_score(f):
    s = 0.0
    if f["eng_t2"]:
        s += 1.0 if (f["conditional_only"] and not f["t1_action"] and not f["interaction"]) else 2.0
    if f["t1_action"]:
        s += 1.0
    if f["combo_pair"]:
        s += 2.0
    if f["tutors"] and f["t2_mana"] >= 2:
        s += 1.0
    if f["interaction"]:
        s += 0.5  # agency, never sufficient alone
    return s


POLICIES = {
    # (min mana, max mana, min proactive score) per kept hand size. Calibrated on the frozen
    # baseline: "pilot" keeps ~60% of first sevens (more aggressive than MULL-005R's fitted ~75%,
    # per the weekend's two loose-keep losses), "loose" ~ the MULL-005R rate, "strict" ~30%.
    "pilot": {7: (2, 5, 1.5), 6: (2, 5, 1.0), 5: (1, 5, 0.5), 4: (0, 9, 0)},
    "loose": {7: (1.5, 5.5, 1.0), 6: (1, 5.5, 0.5), 5: (1, 9, 0.0), 4: (0, 9, 0)},
    "strict": {7: (2, 5, 2.5), 6: (2, 5, 1.5), 5: (1, 5, 1.0), 4: (0, 9, 0)},
}


def keepable(hand, size, on_play, policy):
    lo, hi, pmin = POLICIES[policy][min(size, 7)]
    f = hand_features(hand, on_play)
    return lo <= f["mana_total"] <= hi and f["lands"] >= (1 if size >= 5 else 0) and proactive_score(f) >= pmin


def choose_bottom(hand, k, on_play):
    """Pick k cards to bottom maximising (keep-score, mana balance)."""
    import itertools
    best, best_key = None, None
    for combo in itertools.combinations(range(len(hand)), k):
        kept = [c for i, c in enumerate(hand) if i not in combo]
        f = hand_features(kept, on_play)
        bal = -abs(f["mana_total"] - 3)
        key = (proactive_score(f) + (1 if 2 <= f["mana_total"] <= 4 else 0), bal,
               -sum(dc.mv(c) for c in kept if not dc.is_land(c)))
        if best_key is None or key > best_key:
            best, best_key = kept, key
    return best


def london(library_order, on_play, policy, max_mulls=3, rng=None):
    """Returns (kept hand, library remainder, mulligans taken). Each mulligan reshuffles."""
    lib = list(library_order)
    for m in range(0, max_mulls + 1):
        if m:
            rng.shuffle(lib)
        seven = lib[:7]
        rest = lib[7:]
        if m == 0:
            kept = seven
        else:
            kept = choose_bottom(seven, m, on_play)
        size = 7 - m
        if keepable(kept, size, on_play, policy) or m == max_mulls:
            bottom = [c for c in seven if c not in kept]
            return kept, rest + bottom, m
    raise AssertionError


# ---- game -----------------------------------------------------------------------------------------

class Game:
    def __init__(self, deck, seed, on_play=True, policy="pilot", tutor_policy="engine_tutor",
                 max_turn=4, engine_draws=False, mulligan=True, record_snapshots=False,
                 opp_gy_land_from=None, force_opening=()):
        self.rng = random.Random(seed)
        order = list(deck)
        self.rng.shuffle(order)
        for c in force_opening:  # conditional designs: put these cards in the opening seven
            order.remove(c)
            order.insert(0, c)
        self.on_play = on_play
        self.tutor_policy = tutor_policy
        self.engine_draws = engine_draws
        self.max_turn = max_turn
        self.opp_gy_land_from = opp_gy_land_from
        if mulligan:
            self.hand, self.library, self.mulls = london(order, on_play, policy, rng=self.rng)
        else:
            self.hand, self.library, self.mulls = order[:7], order[7:], 0
        self.opening = list(self.hand)
        self.bf: list[Perm] = []
        self.gy: list[str] = []
        self.cmd = set(dc.COMMANDERS)
        self.turn = 0
        self.record = {"mulligans": self.mulls, "hand_size": len(self.hand), "turns": {}}
        self.record_snapshots = record_snapshots
        self.snapshots = {}
        if "Gemstone Caverns" in self.hand and not on_play:
            self.hand.remove("Gemstone Caverns")
            self.bf.append(Perm("Gemstone Caverns", extra={"luck": True}))
            if self.hand:
                worst = max(self.hand, key=lambda c: (dc.is_land(c), dc.mv(c)))
                self.hand.remove(worst)  # exiled to Caverns' cost

    # -- helpers --
    def bfnames(self):
        return {p.name for p in self.bf}

    def snap(self, timing, units=None, land_drop=False):
        bf = [Perm(p.name, p.sick, p.tapped, dict(p.extra)) for p in self.bf]
        return Snapshot(list(self.hand), bf, list(self.library), list(self.gy), set(self.cmd), {},
                        land_drop, timing, self.turn, units,
                        opp_gy_land=(self.opp_gy_land_from is not None and self.turn >= self.opp_gy_land_from))

    def draw(self, n=1):
        for _ in range(n):
            if self.library:
                self.hand.append(self.library.pop(0))

    def pool_from_board(self):
        return sv.board_units(self.snap("main"))

    def play_land(self, pool):
        lands = [c for c in self.hand if dc.is_land(c)]
        if not lands:
            return pool
        have = set().union(*pool.keys()) if pool else set()
        demand = Counter()
        for c in self.hand:
            if not dc.is_land(c):
                for pip in dc.parse_cost(dc.card(c)["cost"])[1]:
                    for col in pip:
                        if col in "WUBG":
                            demand[col] += 1
        for cmdr in self.cmd:
            for col in dc.card(cmdr)["cost"]:
                if col in "WUBG":
                    demand[col] += 1

        def land_value(n):
            if n in dc.FETCH_TARGETS:
                cols = set()
                for d, t in dc.DUAL_TYPES.items():
                    if d in self.library and t & dc.FETCH_TARGETS[n]:
                        cols |= dc.LAND_UNITS[d][0]
                units = [frozenset(cols)] if cols else []
            elif n == "Starting Town":
                units = [ANY] if self.turn <= 3 else []
            elif n == "City of Traitors" and len(lands) > 1:
                units = [C]
            elif n == "Gaea's Cradle":
                units = [G] * sum(1 for p in self.bf if dc.is_creature(p.name) and not dc.is_land(p.name))
            else:
                units = list(dc.LAND_UNITS.get(n, [C]))
            new_cols = set().union(*units) - have if units else set()
            return (sum(demand[c] for c in new_cols if c in "WUBG"), len(units),
                    -(n in ("Emergence Zone", "Gaea's Cradle", "Boseiju, Who Endures", "Otawara, Soaring City")))
        land = max(lands, key=land_value)
        self.hand.remove(land)
        if any(p.name == "City of Traitors" for p in self.bf):
            city = next(p for p in self.bf if p.name == "City of Traitors")
            self.bf.remove(city)
            self.gy.append("City of Traitors")
        if land in dc.FETCH_TARGETS:
            self.gy.append(land)
            duals = [d for d, t in dc.DUAL_TYPES.items() if d in self.library and t & dc.FETCH_TARGETS[land]]
            if not duals:
                return pool
            d = max(duals, key=lambda d: sum(demand[c] for c in dc.LAND_UNITS[d][0] - have))
            self.library.remove(d)
            land = d
        perm = Perm(land)
        if land == "Starting Town" and self.turn > 3:
            perm.tapped = True
        self.bf.append(perm)
        pool = Counter(pool)
        for u in sv.perm_units(perm, self.snap("main"), self.bfnames()):
            pool[u] += 1
        return pool

    def cast_permanent(self, name, pool, x=0):
        g, pips = dc.cost_of(name, x)
        new = pay_take(pool, pips, g)
        if new is None:
            return None
        if name in self.hand:
            self.hand.remove(name)
        else:
            self.cmd.discard(name)
        perm = Perm(name, sick=dc.is_creature(name))
        self.bf.append(perm)
        # Mana rocks enter untapped and add their mana immediately.
        if name in dc.MANA_PERMS and dc.MANA_PERMS[name][0] in ("rock", "oneshot"):
            for u in sv.perm_units(perm, self.snap("main"), self.bfnames()):
                new[u] += 1
        if name == "Ranger-Captain of Eos":
            for d in ("Birds of Paradise", "Noble Hierarch", "Delighted Halfling", "Avacyn's Pilgrim",
                      "Llanowar Elves", "Elvish Mystic", "Fyndhorn Elves", "Deathrite Shaman"):
                if d in self.library:
                    self.library.remove(d)
                    self.hand.append(d)
                    break
        return new

    def free_mana(self, pool):
        pool = Counter(pool)
        legend_on_bf = self.bfnames() & LEGENDARY_CREATURES
        for c in list(self.hand):
            # Lotus Petal and Elvish Spirit Guide stay in hand: one-shot mana is reserved for
            # conversion (the solver counts it from hand), never spent on development.
            if c == "Mox Diamond":
                lands = [x for x in self.hand if dc.is_land(x)]
                if len(lands) >= 1 and (len(lands) >= 2 or any(dc.is_land(p.name) for p in self.bf)):
                    self.hand.remove(c)
                    worst = min(lands, key=lambda l: len(dc.LAND_UNITS.get(l, [C])[0]) if isinstance(dc.LAND_UNITS.get(l, [C]), list) else 0)
                    self.hand.remove(worst)
                    self.gy.append(worst)
                    self.bf.append(Perm(c))
                    pool[ANY] += 1
            elif c == "Chrome Mox":
                fodder = [x for x in self.hand if x != c and not dc.is_land(x)
                          and "Artifact" not in dc.card(x)["type"] and x not in dc.COMBO_PIECES
                          and x not in dc.TUTORS and x not in PREMIUM and x not in dc.FREE_COUNTERS]
                if fodder:
                    imp = max(fodder, key=lambda x: (dc.mv(x), len(set(dc.card(x)["cost"]) & set("WUBG"))))
                    cols = "".join(ch for ch in dc.card(imp)["cost"] if ch in "WUBG")
                    if cols:
                        self.hand.remove(c)
                        self.hand.remove(imp)
                        self.bf.append(Perm(c, extra={"imprint": cols}))
                        pool[frozenset(cols)] += 1
            elif c == "Mox Amber" and legend_on_bf:
                self.hand.remove(c)
                p = Perm(c)
                self.bf.append(p)
                for u in sv.perm_units(p, self.snap("main"), self.bfnames()):
                    pool[u] += 1
        return pool

    def engine_tutor(self, pool):
        if self.tutor_policy != "engine_tutor" or self.turn > 2:
            return pool
        if (self.bfnames() | set(self.hand)) & PREMIUM:
            return pool
        for t in ("Demonic Tutor", "Imperial Seal", "Vampiric Tutor"):
            if t in self.hand:
                g, pips = dc.cost_of(t)
                new = pay_take(pool, pips, g)
                if new is None:
                    continue
                creature_avail = any(dc.is_creature(p.name) and not dc.is_land(p.name) for p in self.bf) or \
                    any(dc.is_creature(h) and not dc.is_land(h) for h in self.hand)
                target = None
                for cand in (["Birthing Pod"] if creature_avail else []) + ["Rhystic Study", "Mystic Remora",
                                                                              "Smothering Tithe", "Survival of the Fittest"]:
                    if cand in self.library:
                        target = cand
                        break
                if target is None:
                    return pool
                self.hand.remove(t)
                self.gy.append(t)
                self.library.remove(target)
                if t == "Demonic Tutor":
                    self.hand.append(target)
                else:
                    self.library.insert(0, target)
                self.record.setdefault("engine_tutor_used", t)
                return new
        return pool

    def develop(self, pool):
        progress = True
        while progress:
            progress = False
            for name in PRIORITY:
                src = name in self.hand or (name in self.cmd and name in dc.COMMANDERS)
                if not src:
                    continue
                if name == "Mana Vault" and sum(pool.values()) < 1:
                    continue
                if name in ("Devoted Druid",) and self.turn == 1 and sum(pool.values()) < 2:
                    continue
                new = self.cast_permanent(name, pool)
                if new is not None:
                    pool = new
                    progress = True
                    break
        return pool

    # -- main loop --
    def play(self, solve_fn=sv.solve):
        for t in range(1, self.max_turn + 1):
            self.turn = t
            for p in self.bf:
                p.sick = False
                if p.name != "Mana Vault":
                    p.tapped = False
            if not (t == 1 and self.on_play):
                self.draw()
            if self.engine_draws and t >= 2:
                n = min(2, sum(1 for p in self.bf if p.name in CA_ENGINES))
                self.draw(n)
            pool = self.pool_from_board()
            rec = {}
            main = solve_fn(self.snap("main", units=pool, land_drop=True))
            rec["main"] = main
            if self.record_snapshots:
                self.snapshots[(t, "main")] = self.snap("main", units=Counter(pool), land_drop=True)
            if main["det"] and "win_turn" not in self.record:
                self.record["win_turn"] = t
            pool = self.play_land(pool)
            pool = self.free_mana(pool)
            avail = set()
            for k, v in pool.items():
                if v:
                    avail |= k
            rec["colors"] = "".join(c for c in "WUBG" if c in avail)
            rec["mana_avail"] = sum(pool.values())
            n_before = sum(1 for p in self.bf if not dc.is_land(p.name))
            pool = self.engine_tutor(pool)
            pool = self.develop(pool)
            rec["nonland_cast"] = sum(1 for p in self.bf if not dc.is_land(p.name)) - n_before
            for p in self.bf:
                if p.name == "Mana Vault":
                    p.tapped = True  # doesn't untap; the goldfish never pays {4} to untap it
            rec["end"] = {"premium_on_bf": sorted(self.bfnames() & PREMIUM),
                          "n_lands": sum(1 for p in self.bf if dc.is_land(p.name)),
                          "n_mana_perms": sum(1 for p in self.bf if p.name in dc.MANA_PERMS),
                          "hand_size": len(self.hand)}
            inst_snap = self.snap("instant", units=Counter(pool))
            rec["instant"] = solve_fn(inst_snap)
            if self.record_snapshots:
                self.snapshots[(t, "instant")] = inst_snap
                self.snapshots[(t, "end_hand")] = (list(self.hand), [Perm(p.name, p.sick, p.tapped, dict(p.extra)) for p in self.bf])
            self.record["turns"][t] = rec
            if rec["instant"]["det"] and "win_turn" not in self.record:
                self.record["win_turn"] = t + 0.5
        return self.record
