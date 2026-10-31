"""SIM-DECKBUILD-008 — state-conditioned deterministic-win solver and Conversion Surface Area.

Given a snapshot (hand, battlefield with summoning-sickness/tap state, graveyard, library,
command zone, land drop, timing window), decide whether a DETERMINISTIC win can be executed in
the current window, through which line families, at what minimum card/mana cost, and whether it
can be executed (a) at instant speed and (b) with protection.

This is NOT a gameplay simulator. There is no opponent, no stack, no combat. "Deterministic"
means: the line wins if no opponent interacts. Protection flags record whether the line can be
executed with a proactive shield (Silence / Grand Abolisher / Voice of Victory / Ranger-Captain)
or with a free counterspell held, not whether that protection would be sufficient.

Line families (each is a hyperedge: pieces x delivery x mana x colour x timing):
  oracle_consult  Thassa's Oracle enters + Demonic Consultation          {U}{U} + {B}
  oracle_pact     Thassa's Oracle enters + Tainted Pact                  {U}{U} + {1}{B}
  oracle_hermit   Oracle enters + Hermit Druid activation (non-sick, or Shang-Chi)   or
                  Hermit mills, then Finale of Devastation (graveyard) puts Oracle in play
  oracle_witch    Oracle enters + Divining Witch activation (non-sick or Shang-Chi), discard 1
  inf_oracle      infinite-mana engine + Thrasios draws the library + cast Oracle (needs UU)
  inf_bowmasters  infinite G+U engine + Orcish Bowmasters + Faerie Mastermind (Oracle-less kill)
  inf_finale      infinite mana + Finale of Devastation X>=10 (combat) — NONDETERMINISTIC
Infinite-mana engines:
  E1 Devoted Druid + Swift Reconfiguration (G)         E2 Hazel's Brewmaster exiling Druid (G)
  E3 Machine God's Effigy copying a creature Druid (G+U)
  E4 Oboro Breezecaller + Talon Gates + Gaea's Cradle with >=6 creatures (any colour)

Each piece is delivered by an explicit option: already in zone, cast from hand, or found by a
tutor (to hand, to top + a Thrasios draw, or to the battlefield) — with tutor-of-tutor chains to
depth 2 so that, e.g., Birthing Pod -> Spellseeker -> Demonic Consultation is represented.
"""
from __future__ import annotations

import itertools
from collections import Counter
from dataclasses import dataclass, field

import deckbuild008_cards as dc
from deckbuild008_cards import ANY, B, C, G, U, W

ORACLE = "Thassa's Oracle"
CONSULT = "Demonic Consultation"
PACT = "Tainted Pact"
HERMIT = "Hermit Druid"
WITCH = "Divining Witch"
SHANG = "Shang-Chi, Master of Kung Fu"
DRUID = "Devoted Druid"
SWIFT = "Swift Reconfiguration"
HAZEL = "Hazel's Brewmaster"
EFFIGY = "Machine God's Effigy"
THRASIOS = "Thrasios, Triton Hero"
TYMNA = "Tymna the Weaver"
FINALE = "Finale of Devastation"
BOWMASTERS = "Orcish Bowmasters"
MASTERMIND = "Faerie Mastermind"
SPELLSEEKER = "Spellseeker"
SURVIVAL = "Survival of the Fittest"
POD = "Birthing Pod"
KINNAN = "Kinnan, Bonder Prodigy"
BADGERMOLE = "Badgermole Cub"
DELNEY = "Delney, Streetwise Lookout"
VITALITY = "Enduring Vitality"
CRADLE = "Gaea's Cradle"

SHIELDS_ON_BF = {"Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos"}
LEGENDARY_COLORS = {
    THRASIOS: "GU", TYMNA: "WB", KINNAN: "GU", DELNEY: "W", "Derevi, Empyrial Tactician": "GWU",
    "Lotho, Corrupt Shirriff": "WB", "The Cabbage Merchant": "G", "The Queen of Dale": "W",
    "Teferi, Mage of Zhalfir": "U", SHANG: "G",
}
COST_REDUCERS = {"Training Grounds", "Biomancer's Familiar"}
SKYTURTLE = "Colossal Skyturtle"

# DECKBUILD-008b rule extensions. Both default OFF so DECKBUILD-008 results reproduce exactly.
#  FAIR_PACT_TUTOR: Tainted Pact is also a fair instant tutor ("any" card to hand). In a singleton
#    library with no duplicate names it always finds the named card, but every card above it is
#    exiled; a line that still needs to draw its outlet from the library after Pact is therefore
#    NOT deterministic (reported as the nondeterministic family "pact_exposed").
#  SKYTURTLE_REGROWTH: Colossal Skyturtle's channel {2}{G} (discard it: return target card from your
#    graveyard to your hand) is a delivery option for a line piece in the graveyard. Channel is an
#    activated ability from hand: instant speed, not a spell.
FAIR_PACT_TUTOR = False
SKYTURTLE_REGROWTH = False


def enable_008b_rules(fair_pact=True, skyturtle=True):
    global FAIR_PACT_TUTOR, SKYTURTLE_REGROWTH
    FAIR_PACT_TUTOR = fair_pact
    SKYTURTLE_REGROWTH = skyturtle
    if fair_pact:
        dc.TUTORS[PACT] = {"dest": "hand", "speed": "instant", "find": "any", "exiles_above": True}
    else:
        dc.TUTORS.pop(PACT, None)


@dataclass
class Perm:
    name: str
    sick: bool = False
    tapped: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class Snapshot:
    hand: list
    bf: list                     # list[Perm], lands included
    library: list                # ordered, top first (solver treats as a set)
    gy: list = field(default_factory=list)
    cmd: set = field(default_factory=lambda: set(dc.COMMANDERS))
    cmd_tax: dict = field(default_factory=dict)
    land_drop: bool = True
    timing: str = "main"         # "main" (own main phase, sorcery speed) | "instant"
    turn: int = 1
    units_override: object = None  # optional Counter of remaining mana units (goldfish pool)
    opp_gy_land: bool = False    # sensitivity: an opponent's graveyard holds a land (Deathrite)


# ---- mana ---------------------------------------------------------------------------------------

def _creature_count(bf):
    return sum(1 for p in bf if not dc.is_land(p.name) and dc.is_creature(p.name)) + \
        sum(1 for p in bf if p.extra.get("earthbent"))


def perm_units(p, snap, bfnames):
    """Mana units an UNTAPPED permanent provides this window (list of colour sets)."""
    n = p.name
    shang = SHANG in bfnames
    if dc.is_land(n) and n not in dc.MANA_PERMS:
        if p.tapped:
            return []
        spec = dc.LAND_UNITS.get(n, [C])
        if spec == "cradle":
            return [G] * _creature_count(snap.bf)
        if n == "Gemstone Caverns" and p.extra.get("luck"):
            return [ANY]
        return list(spec)
    if n not in dc.MANA_PERMS or p.tapped:
        if n == SHANG and not p.tapped:
            return []  # handled as a creature-ability credit, see shang_credit()
        if VITALITY in bfnames and not dc.is_land(n) and dc.is_creature(n) and (not p.sick or shang):
            return [ANY]
        return []
    kind, spec = dc.MANA_PERMS[n]
    if kind == "dork" and p.sick and not shang:
        return []
    if spec == "deathrite":
        has_land = any(dc.is_land(x) for x in snap.gy) or snap.opp_gy_land
        return [ANY] if has_land else []
    if spec == "arbor":
        forests = [q for q in snap.bf if q.name in dc.FOREST_LANDS]
        return [frozenset().union(*(dc.LAND_UNITS[q.name][0] for q in forests))] if forests else []
    if spec == "imprint":
        cols = p.extra.get("imprint", "")
        return [frozenset(cols)] if cols else []
    if spec == "amber":
        cols = "".join(LEGENDARY_COLORS.get(q.name, "") for q in snap.bf)
        return [frozenset(cols)] if cols else []
    if n == "Mana Vault" and p.extra.get("vault_tapped"):
        return []
    units = list(spec)
    if VITALITY in bfnames and kind == "dork":
        units = [ANY] * len(units)
    # Kinnan / Badgermole: only TRUE mana abilities from tapping a nonland permanent.
    # Both trigger per TAP (not per mana): Sol Ring tapped once for {C}{C} gets one extra {C};
    # Devoted Druid taps twice (tap, -1/-1 untap, tap) and gets two.
    if n not in dc.NOT_A_MANA_ABILITY:
        taps = 2 if n == DRUID else 1
        mult = 2 if DELNEY in bfnames else 1
        bonus = []
        if KINNAN in bfnames:
            bonus += [units[0]] * taps * mult
        if BADGERMOLE in bfnames and kind == "dork":
            bonus += [G] * taps * mult
        units = units + bonus
    return units


def board_units(snap):
    bfnames = {p.name for p in snap.bf}
    out = Counter()
    for p in snap.bf:
        for u in perm_units(p, snap, bfnames):
            out[u] += 1
    return out


def best_land_drop(snap):
    """Colour set (and unit count) of the land drop most useful for colour; None if no drop."""
    if not snap.land_drop or snap.timing != "main":
        return []
    lib = set(snap.library)
    best = []
    for n in snap.hand:
        if not dc.is_land(n):
            continue
        if n in dc.FETCH_TARGETS:
            cols = frozenset()
            for d, types in dc.DUAL_TYPES.items():
                if d in lib and types & dc.FETCH_TARGETS[n]:
                    cols |= dc.LAND_UNITS[d][0]
            cand = [cols] if cols else []
        elif n == "Starting Town":
            cand = [ANY] if snap.turn <= 3 else []
        elif n == "Sink into Stupor // Soporific Springs":
            cand = [U]
        else:
            spec = dc.LAND_UNITS.get(n, [C])
            cand = [G] * (_creature_count(snap.bf)) if spec == "cradle" else list(spec)
        if (len(cand), sum(len(c) for c in cand)) > (len(best), sum(len(c) for c in best)):
            best = cand
    return best


def hand_free_mana(snap, reserved=frozenset()):
    """Zero-cost mana a hand can produce this window (Petal, ESG, Moxen)."""
    out = []
    hand = [h for h in snap.hand if h not in reserved]
    bfnames = {p.name for p in snap.bf}
    lands_in_hand = sum(1 for h in hand if dc.is_land(h))
    for h in hand:
        if h == "Lotus Petal":
            out.append(ANY)
        elif h == "Elvish Spirit Guide":
            out.append(G)
        elif h == "Mox Diamond" and lands_in_hand >= (2 if snap.land_drop else 1) and snap.timing == "main":
            out.append(ANY)
        elif h == "Chrome Mox" and snap.timing == "main":
            cols = set()
            for x in hand:
                if x != h and not dc.is_land(x) and "Artifact" not in dc.card(x)["type"]:
                    cols |= set(c for c in dc.card(x)["cost"] if c in "WUBG")
            if cols:
                out.append(frozenset(cols))
        elif h == "Mox Amber" and snap.timing == "main":
            cols = "".join(LEGENDARY_COLORS.get(n, "") for n in bfnames)
            if cols:
                out.append(frozenset(cols))
    return out


def pay(units: Counter, pips, generic):
    """Can `units` pay `pips` (tuple of acceptable-colour sets; 'P' = Phyrexian) + `generic`?"""
    total = sum(units.values())
    hard = [p for p in pips if "P" not in p]
    if total < len(hard) + generic:
        return False
    hard.sort(key=len)
    keys = list(units.keys())
    counts = [units[k] for k in keys]

    def rec(i):
        if i == len(hard):
            return sum(counts) >= generic
        pip = hard[i]
        tried = set()
        for j, k in enumerate(keys):
            if counts[j] and (k & pip) and k not in tried:
                tried.add(k)
                counts[j] -= 1
                if rec(i + 1):
                    counts[j] += 1
                    return True
                counts[j] += 1
        return False
    return rec(0)


# ---- delivery options ------------------------------------------------------------------------------

@dataclass(frozen=True)
class Opt:
    pips: tuple = ()
    generic: int = 0
    uses: frozenset = frozenset()      # cards consumed (pieces, tutors, discards, sacrifices)
    flash: int = 0                     # 0 none, 1 creature spell needs flash, 2 noncreature needs flash
    sorcery_only: bool = False         # e.g. Birthing Pod (activate only as a sorcery)
    spells: int = 0                    # spells cast (counter exposure)
    thr: int = 0                       # Thrasios draws required
    convoke: int = 0                   # convoke credit usable
    cab: int = 0                       # creature-ability mana required (Shang-Chi can pay)
    path: tuple = ()

    def __add__(self, o):
        return Opt(self.pips + o.pips, self.generic + o.generic, self.uses | o.uses,
                   max(self.flash, o.flash), self.sorcery_only or o.sorcery_only,
                   self.spells + o.spells, self.thr + o.thr, self.convoke + o.convoke,
                   self.cab + o.cab, self.path + o.path)


def _spell_opt(name, x=0, path=None):
    g, pips = dc.cost_of(name, x)
    if name in ("Swift Reconfiguration",) or "Flash" in dc.card(name)["text"].split("\n")[0]:
        fl = 0
    elif dc.is_creature(name):
        fl = 1
    elif dc.is_instant(name):
        fl = 0
    else:
        fl = 2
    return Opt(pips, g, frozenset({name}), fl, False, 1, path=(path or (f"cast {name}",)))


class Ctx:
    def __init__(self, snap: Snapshot, depth=2):
        self.s = snap
        self.hand = set(snap.hand)
        self.bfnames = {p.name for p in snap.bf}
        self.lib = set(snap.library)
        self.gy = set(snap.gy)
        self.depth = depth
        self.creatures_bf = [p for p in snap.bf if not dc.is_land(p.name) and dc.is_creature(p.name)]
        self.thr_on_bf = THRASIOS in self.bfnames
        self.thr_cost = 2 if (self.bfnames & COST_REDUCERS) else 4
        self.shang = SHANG in self.bfnames and any(p.name == SHANG and not p.tapped for p in snap.bf)
        self._cache = {}

    def reachable(self, piece):
        """In hand or library, or (008b) in the graveyard with Skyturtle's channel regrowth in hand."""
        if piece in self.hand or piece in self.lib:
            return True
        return SKYTURTLE_REGROWTH and piece in self.gy and SKYTURTLE in self.hand

    # Thrasios available to draw? (on battlefield, or castable from command zone)
    def thrasios_opt(self):
        if self.thr_on_bf:
            return Opt()
        if THRASIOS in self.s.cmd:
            tax = self.s.cmd_tax.get(THRASIOS, 0)
            return Opt((G, U), tax, frozenset(), 1, False, 1, path=("cast Thrasios",))
        return None

    def sac_candidates(self, mv_pred, reserved):
        return [p.name for p in self.creatures_bf if p.name not in reserved and mv_pred(dc.mv(p.name))]

    def tutor_opts(self, tutor, depth, reserved):
        """Ways to have `tutor` available to use this window: (opt, how)."""
        t = dc.TUTORS[tutor]
        out = []
        if t.get("on_bf"):
            if tutor in self.bfnames:
                perm = next(p for p in self.s.bf if p.name == tutor)
                if not perm.tapped or tutor == SURVIVAL:
                    out.append(Opt(uses=frozenset({tutor}) if tutor == POD else frozenset()))
            elif tutor in self.hand:
                out.append(_spell_opt(tutor))
            return out
        if tutor in self.hand:
            out.append(Opt(uses=frozenset({tutor})))  # cast cost added by caller
        elif depth > 0 and tutor in self.lib and tutor not in reserved:
            if tutor == SPELLSEEKER or dc.is_creature(tutor):
                for o in self.enter_opts(tutor, depth - 1, reserved | {tutor}, as_tutor=True):
                    out.append(o + Opt(uses=frozenset({"__seeker_cast__" + tutor})))
            else:
                for o in self.hand_opts(tutor, depth - 1, reserved | {tutor}):
                    out.append(o)
        return out

    def hand_opts(self, piece, depth, reserved):
        """Options that put `piece` into hand (not cast)."""
        key = ("hand", piece, depth, reserved)
        if key in self._cache:
            return self._cache[key]
        out = []
        if piece in self.hand:
            out.append(Opt())
        elif SKYTURTLE_REGROWTH and piece in self.gy and SKYTURTLE in self.hand and \
                SKYTURTLE not in reserved and piece != SKYTURTLE:
            out.append(Opt((G,), 2, frozenset({SKYTURTLE}), 0, False, 0,
                           path=(f"Skyturtle channel regrow {piece}",)))
        elif piece in self.lib:
            for tutor in dc.TUTORS:
                if tutor == piece or tutor in reserved:
                    continue
                t = dc.TUTORS[tutor]
                if t["dest"] not in ("hand", "top") or not dc.tutor_can_find(tutor, piece):
                    continue
                if tutor not in self.hand and tutor not in self.bfnames and depth == 0:
                    continue
                for avail in self.tutor_opts(tutor, depth, reserved | {piece}):
                    o = avail
                    if t.get("on_bf"):  # Survival
                        discards = [h for h in self.hand if h not in reserved and h != piece
                                    and dc.is_creature(h) and h not in o.uses]
                        if not discards:
                            continue
                        o = o + Opt((G,), 0, frozenset({discards[0]}), 0, False, 0, cab=0,
                                    path=(f"Survival discard {discards[0]} -> {piece}",))
                    elif tutor in (SPELLSEEKER, "Ranger-Captain of Eos"):
                        if tutor in self.hand:
                            o = o + _spell_opt(tutor)
                        o = o + Opt(path=(f"{tutor} ETB -> {piece}",))
                    else:
                        o = o + _spell_opt(tutor, path=(f"{tutor} -> {piece}",))
                    if t["dest"] == "top":
                        th = self.thrasios_opt()
                        if th is None:
                            continue
                        o = o + th + Opt(generic=self.thr_cost, thr=1, cab=self.thr_cost,
                                         path=("Thrasios draw",))
                    out.append(o)
        self._cache[key] = out
        return out

    def cast_opts(self, piece, depth, reserved):
        return [o + _spell_opt(piece) for o in self.hand_opts(piece, depth, reserved)]

    def enter_opts(self, piece, depth, reserved, as_tutor=False):
        """Options under which creature/artifact `piece` ENTERS the battlefield this window."""
        key = ("enter", piece, depth, reserved, as_tutor)
        if key in self._cache:
            return self._cache[key]
        out = [o + _spell_opt(piece) for o in self.hand_opts(piece, depth, reserved)]
        if piece in self.lib and dc.is_creature(piece):
            pmv = dc.mv(piece)
            for tutor, t in dc.TUTORS.items():
                if t["dest"] != "bf" or tutor in reserved or tutor == piece or t["find"] == "land":
                    continue
                if t["find"].startswith("green") and not dc.is_green(piece):
                    continue
                avails = []
                if t.get("on_bf"):
                    avails = self.tutor_opts(tutor, 0, reserved)
                elif tutor in self.hand or (depth > 0 and tutor in self.lib):
                    for a in (self.tutor_opts(tutor, depth, reserved | {piece}) if tutor not in self.hand
                              else [Opt(uses=frozenset({tutor}))]):
                        avails.append(a)
                for a in avails:
                    if t["find"] in ("creature_x", "green_creature_x"):
                        o = a + _spell_opt(tutor, x=pmv, path=(f"{tutor} X={pmv} -> {piece}",))
                        if t.get("convoke"):
                            o = o + Opt(convoke=1)
                        out.append(o)
                    else:
                        if t["find"] == "creature_sac_plus1":
                            sacs = self.sac_candidates(lambda m: m == pmv - 1, reserved | {piece})
                        else:
                            sacs = self.sac_candidates(lambda m: m >= pmv - 2, reserved | {piece})
                        if not sacs:
                            continue
                        sac = sacs[0]
                        if tutor == POD:
                            g, pips = t["activation"]
                            o = a + Opt(pips, g, frozenset({sac}), 0, True, 0,
                                        path=(f"Pod sac {sac} -> {piece}",))
                        else:
                            o = a + _spell_opt(tutor, path=(f"{tutor} sac {sac} -> {piece}",)) + \
                                Opt(uses=frozenset({sac}))
                        out.append(o)
        self._cache[key] = out
        return out


# ---- flash / protection ---------------------------------------------------------------------------

def flash_extra(ctx, opt, units):
    """Extra cost to make `opt` executable at instant speed, or None if impossible."""
    if opt.sorcery_only:
        return None
    need = opt.flash
    if need == 0:
        return Opt()
    if "High Fae Trickster" in ctx.bfnames:
        return Opt()
    if need == 1 and "Teferi, Mage of Zhalfir" in ctx.bfnames:
        return Opt()
    cands = []
    zone = [p for p in ctx.s.bf if p.name == "Emergence Zone" and not p.tapped]
    if zone:
        cands.append(Opt(generic=1, path=("Emergence Zone",)) + Opt(uses=frozenset({"__zone__"})))
    if "Borne Upon a Wind" in ctx.hand and "Borne Upon a Wind" not in opt.uses:
        cands.append(_spell_opt("Borne Upon a Wind"))
    if "High Fae Trickster" in ctx.hand and "High Fae Trickster" not in opt.uses:
        cands.append(_spell_opt("High Fae Trickster"))
    if need == 1 and "Teferi, Mage of Zhalfir" in ctx.hand and "Teferi, Mage of Zhalfir" not in opt.uses:
        cands.append(_spell_opt("Teferi, Mage of Zhalfir"))
    return cands or None


BLUE_PITCH_EXCLUDE = {"Force of Will"}


def counter_backup(ctx, opt, units, total):
    """A counterspell castable after the line is paid (free or with leftover mana)."""
    spare = [h for h in ctx.s.hand if h not in opt.uses]
    blue = [h for h in spare if dc.is_blue(h)]
    cmdr_on_bf = bool({THRASIOS, TYMNA} & ctx.bfnames)
    if "Pact of Negation" in spare:
        return True
    if "Fierce Guardianship" in spare and cmdr_on_bf:
        return True
    if "Force of Will" in spare and len([b for b in blue if b != "Force of Will"]) >= 1:
        return True
    if "Misdirection" in spare and len([b for b in blue if b != "Misdirection"]) >= 1:
        return True
    if "Commandeer" in spare and len([b for b in blue if b != "Commandeer"]) >= 2:
        return True
    if "Flare of Denial" in spare and any(dc.is_blue(p.name) and p.name not in opt.uses
                                          for p in ctx.creatures_bf):
        return True
    if "Force of Negation" in spare and ctx.s.timing == "instant" and \
            len([b for b in blue if b != "Force of Negation"]) >= 1:
        return True
    for paid in ("Swan Song", "Flusterstorm", "Dispel"):
        if paid in spare and pay(units, total.pips + (U,), total.generic):
            return True
    return False


def shield(ctx, opt, units, total):
    if ctx.s.timing == "main" and (SHIELDS_ON_BF & ctx.bfnames) - set(opt.uses):
        return True
    for card, pip in (("Silence", W), ("Orim's Chant", W), ("Veil of Summer", G), ("Autumn's Veil", G)):
        if card in ctx.s.hand and card not in opt.uses and pay(units, total.pips + (pip,), total.generic):
            return True
    return False


# ---- line families ------------------------------------------------------------------------------

def _combine(lists):
    for combo in itertools.product(*lists):
        uses = Counter()
        ok = True
        for o in combo:
            for u in o.uses:
                if u.startswith("__"):
                    continue
                uses[u] += 1
                if uses[u] > 1:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            total = Opt()
            for o in combo:
                total = total + o
            yield total


def _active_opts(ctx, creature, reserved):
    """Options to have a tap-ability creature able to activate now."""
    out = []
    for p in ctx.s.bf:
        if p.name == creature and not p.tapped and (not p.sick or ctx.shang):
            out.append(Opt())
    if not out:
        for o in ctx.enter_opts(creature, ctx.depth, reserved):
            if ctx.shang:
                out.append(o)
            elif SHANG in ctx.hand:
                out.append(o + _spell_opt(SHANG))
    return out


def oracle_lines(ctx):
    """Yield (family, total_opt) for every Oracle line combination."""
    if not ctx.reachable(ORACLE) and ORACLE not in ctx.bfnames:
        return
    res = frozenset({ORACLE})
    oracle_in = ctx.enter_opts(ORACLE, ctx.depth, frozenset()) if ctx.reachable(ORACLE) else []
    if ORACLE in ctx.bfnames:  # re-trigger by copying the Oracle already in play
        for cp in ("Mockingbird", "Clever Impersonator", "Flash Photography"):
            if cp in ctx.hand:
                x = 1 if cp == "Mockingbird" else 0
                oracle_in = oracle_in + [_spell_opt(cp, x=x)]
    if not oracle_in:
        return
    for piece, fam in ((CONSULT, "oracle_consult"), (PACT, "oracle_pact")):
        if ctx.reachable(piece):
            for t in _combine([oracle_in, ctx.cast_opts(piece, ctx.depth, res | {piece})]):
                yield fam, t
    for creature, fam, act in ((HERMIT, "oracle_hermit", Opt((G,), 0, cab=1)),
                               (WITCH, "oracle_witch", Opt((B,), 1, cab=2))):
        if creature in ctx.bfnames or creature in ctx.hand or creature in ctx.lib:
            actives = _active_opts(ctx, creature, res | {creature})
            if not actives:
                continue
            if creature == WITCH:
                discards = [h for h in ctx.s.hand if h not in (ORACLE, WITCH)]
                if not discards:
                    continue
                act = act + Opt(uses=frozenset({discards[-1]}))
            for t in _combine([oracle_in, actives]):
                yield fam, t + act + Opt(uses=frozenset({creature}))
    # Hermit mills Oracle; Finale of Devastation returns it from the graveyard.
    if HERMIT in ctx.bfnames | ctx.hand | ctx.lib and ORACLE in ctx.lib:
        actives = _active_opts(ctx, HERMIT, res | {HERMIT})
        finale = [o + _spell_opt(FINALE, x=2) for o in ctx.hand_opts(FINALE, ctx.depth, res | {HERMIT})]
        if actives and finale:
            for t in _combine([actives, finale]):
                yield "oracle_hermit", t + Opt((G,), 0, frozenset({HERMIT}), cab=1)


def engine_lines(ctx):
    """Yield (engine, opt, infinite_blue) for infinite-mana engines assemblable now."""
    res = frozenset({DRUID})
    druid_bf = [Opt()] if any(p.name == DRUID for p in ctx.s.bf) else \
        (ctx.enter_opts(DRUID, ctx.depth, frozenset({SWIFT, HAZEL, EFFIGY})) if ctx.reachable(DRUID) else [])
    if druid_bf and ctx.reachable(SWIFT):
        for t in _combine([druid_bf, ctx.cast_opts(SWIFT, ctx.depth, res | {SWIFT})]):
            yield "E1_druid_swift", t + Opt(uses=frozenset({DRUID})), False
    if druid_bf and ctx.reachable(EFFIGY):
        for t in _combine([druid_bf, ctx.enter_opts(EFFIGY, ctx.depth, res | {EFFIGY})]):
            yield "E3_druid_effigy", t + Opt(uses=frozenset({DRUID})), True
    if HAZEL in ctx.hand or HAZEL in ctx.lib:
        hz = ctx.enter_opts(HAZEL, ctx.depth, res | {HAZEL})
        if DRUID in ctx.gy:
            for t in hz:
                yield "E2_hazel_druid", t, False
        if DRUID in ctx.hand and SURVIVAL in ctx.bfnames:
            if HAZEL in ctx.lib:
                yield "E2_hazel_druid", Opt((G,), 0, frozenset({DRUID})) + _spell_opt(HAZEL), False
        if any(p.name == DRUID for p in ctx.s.bf) and HAZEL in ctx.lib:
            for o in ctx.cast_opts("Eldritch Evolution", ctx.depth, res | {HAZEL}) \
                    if "Eldritch Evolution" in ctx.hand | ctx.lib else []:
                yield "E2_hazel_druid", o + Opt(uses=frozenset({DRUID, HAZEL})), False
    if {"Oboro Breezecaller", CRADLE} <= ctx.bfnames and \
            ("Talon Gates of Madara" in ctx.bfnames or "Talon Gates of Madara" in ctx.hand) and \
            len(ctx.creatures_bf) >= 6:
        yield "E4_breezecaller_cradle", Opt(), True


FREE_BLUE_FROM_DIG = ("Lotus Petal", "Mox Amber", "Chrome Mox", EFFIGY, "Arcane Signet")


def kill_after_infinite(ctx, eopt, inf_blue, units):
    """Given an assembled infinite-mana engine `eopt`, which kill outlets complete the win?"""
    kills = []
    used = eopt.uses
    pact_tutored = FAIR_PACT_TUTOR and any(st.startswith(PACT + " -> ") for st in eopt.path)
    thr = ctx.thrasios_opt()
    reachable = set(ctx.hand) | (ctx.lib if (thr is not None) else set())
    reachable -= used
    # Free blue sources once Thrasios has drawn the library (or already in hand).
    def free_blue():
        n = sum(1 for c in FREE_BLUE_FROM_DIG if c in reachable)
        if VITALITY in reachable:
            n += sum(1 for p in ctx.creatures_bf if not p.sick and p.name not in dc.MANA_PERMS)
        return n
    # K1: Thrasios + Oracle (library emptied by Thrasios draws).
    if thr is not None and (ORACLE in ctx.lib or ORACLE in ctx.hand) and ORACLE not in used:
        # Casting Thrasios from the command zone needs one real {U} BEFORE the dig; the free blue
        # sources drawn by the dig can only pay for the Oracle afterwards.
        need_first = 0 if (inf_blue or THRASIOS in ctx.bfnames) else 1
        need_after = 0 if inf_blue else max(0, 2 - free_blue())
        tot = eopt + Opt(tuple([U] * (need_first + need_after)))
        if pay(units, tot.pips, tot.generic):
            fam = "pact_exposed" if (pact_tutored and ORACLE in ctx.lib) else "inf_oracle"
            kills.append((fam, tot + Opt(spells=1 + (1 if THRASIOS not in ctx.bfnames else 0))))
    # K2: Bowmasters + Faerie Mastermind with infinite blue (Oracle-less deterministic kill).
    have_bm = BOWMASTERS in reachable or BOWMASTERS in ctx.bfnames
    have_fm = MASTERMIND in reachable or MASTERMIND in ctx.bfnames
    if have_bm and have_fm:
        blue_ok = inf_blue
        if not blue_ok and eopt.path and any("Swift" in s for s in eopt.path):
            blue_ok = EFFIGY in reachable and ({"Clever Impersonator", "Flash Photography"} & reachable) \
                and free_blue() >= 2
        if blue_ok:
            b_free = any(c in reachable for c in ("Lotus Petal", "Chrome Mox")) or \
                (TYMNA in ctx.bfnames and "Mox Amber" in reachable) or \
                ({"Nature's Rhythm", FINALE, "Chord of Calling"} & reachable)
            tot = eopt if (b_free or BOWMASTERS in ctx.bfnames) else eopt + Opt((B,))
            if not inf_blue and THRASIOS not in ctx.bfnames:
                tot = tot + Opt((U,))
            if pay(units, tot.pips, tot.generic):
                exposed = pact_tutored and ((BOWMASTERS in ctx.lib) or (MASTERMIND in ctx.lib))
                kills.append(("pact_exposed" if exposed else "inf_bowmasters", tot + Opt(spells=3)))
    # K3: Finale X>=10 combat (nondeterministic), own main phase only.
    if ctx.s.timing == "main" and (FINALE in reachable):
        if pay(units, eopt.pips, eopt.generic):
            kills.append(("inf_finale", eopt + Opt(spells=1)))
    return kills


DET_FAMILIES = ("oracle_consult", "oracle_pact", "oracle_hermit", "oracle_witch", "inf_oracle",
                "inf_bowmasters")
NONDET_FAMILIES = ("inf_finale", "pact_exposed")


def _units_for(ctx, snap):
    if snap.units_override is not None:
        units = Counter(snap.units_override)
    else:
        units = board_units(snap)
    for u in best_land_drop(snap):
        units[u] += 1
    for u in hand_free_mana(snap):
        units[u] += 1
    return units


def _apply(units, ctx, opt):
    u = Counter(units)
    if opt.convoke:
        for p in ctx.creatures_bf:
            if p.name not in dc.MANA_PERMS and not p.tapped:
                u[G if dc.is_green(p.name) else C] += 1
    if ctx.shang and opt.cab:
        u[ANY] += min(2, opt.cab)
    return u


def solve(snap: Snapshot, depth=2, want=("det", "instant", "protected")):
    ctx = Ctx(snap, depth)
    units = _units_for(ctx, snap)
    res = {"det": False, "nondet": False, "instant": False, "protected": False, "shield": False,
           "counter": False, "families": set(), "det_instant_families": set(),
           "min_cards": None, "min_mana": None, "min_spells": None, "used_cards": set()}

    def consider(fam, opt, u):
        if snap.timing == "instant":
            if opt.sorcery_only:
                return
            ext = flash_extra(ctx, opt, u)
            if ext is None:
                return
            exts = ext if isinstance(ext, list) else [ext]
            ok = False
            for e in exts:
                t = opt + e
                uu = Counter(u)
                if "__zone__" in t.uses:
                    if uu.get(C, 0):
                        uu[C] -= 1
                    else:
                        continue
                if pay(uu, t.pips, t.generic):
                    opt, u, ok = t, uu, True
                    break
            if not ok:
                return
        elif not pay(u, opt.pips, opt.generic):
            return
        if fam in NONDET_FAMILIES:
            res["nondet"] = True
            res["families"].add(fam)
            return
        res["det"] = res["nondet"] = True
        res["families"].add(fam)
        if snap.timing == "instant":
            res["instant"] = True
            res["det_instant_families"].add(fam)
        real = {x for x in opt.uses if not x.startswith("__")}
        if "all" in want:
            res["used_cards"] |= real
        ncards = len(real)
        mana = len(opt.pips) + opt.generic
        if res["min_cards"] is None or ncards < res["min_cards"]:
            res["min_cards"] = ncards
        if res["min_mana"] is None or mana < res["min_mana"]:
            res["min_mana"] = mana
        if res["min_spells"] is None or opt.spells < res["min_spells"]:
            res["min_spells"] = opt.spells
        if "protected" in want and not res["protected"]:
            sh = shield(ctx, opt, u, opt)
            co = counter_backup(ctx, opt, u, opt)
            res["shield"] |= sh
            res["counter"] |= co
            res["protected"] = res["shield"] or res["counter"]

    for fam, opt in oracle_lines(ctx):
        consider(fam, opt, _apply(units, ctx, opt))
        if _done(res, want, ctx):
            break
    if not _done(res, want, ctx):
        for eng, eopt, inf_blue in engine_lines(ctx):
            u = _apply(units, ctx, eopt)
            for fam, kopt in kill_after_infinite(ctx, eopt, inf_blue, u):
                consider(fam, kopt, u)
            if _done(res, want, ctx):
                break
    return res


def _done(res, want, ctx):
    if "all" in want or not res["det"]:
        return False
    if "protected" in want and not res["protected"]:
        return False
    return len(res["families"]) >= 3


# ---- Conversion Surface Area -------------------------------------------------------------------

def csa(snap: Snapshot, depth=2, base=None):
    """Count library cards that, if drawn now, produce a deterministic win this window.

    Returns counts of: raw winning draws (the card itself is a line piece), tutor-equivalent
    winning draws (any role), protected winning draws, plus the library size, and whether the
    state is already winning without a draw.
    """
    base = base if base is not None else solve(snap, depth)
    out = {"library": len(snap.library), "already_winning": base["det"],
           "already_protected": base["protected"], "win_draws": 0, "raw_piece_draws": 0,
           "protected_draws": 0, "nondet_draws": 0, "winning_cards": []}
    if base["det"]:
        return out
    pieces = {ORACLE, CONSULT, PACT, HERMIT, WITCH, DRUID, SWIFT, HAZEL, EFFIGY, SHANG,
              BOWMASTERS, MASTERMIND}
    for cardname in set(snap.library):
        if dc.is_land(cardname) and cardname not in (CRADLE, "Emergence Zone"):
            relevant = snap.land_drop
        else:
            relevant = True
        if not relevant:
            continue
        lib = [c for c in snap.library if c != cardname]
        s2 = Snapshot(snap.hand + [cardname], snap.bf, lib, snap.gy, snap.cmd, snap.cmd_tax,
                      snap.land_drop, snap.timing, snap.turn, snap.units_override, snap.opp_gy_land)
        r = solve(s2, depth, want=("det", "protected"))
        if r["det"]:
            out["win_draws"] += 1
            out["winning_cards"].append(cardname)
            if cardname in pieces:
                out["raw_piece_draws"] += 1
            if r["protected"]:
                out["protected_draws"] += 1
        elif r["nondet"]:
            out["nondet_draws"] += 1
    out["winning_cards"].sort()
    return out
