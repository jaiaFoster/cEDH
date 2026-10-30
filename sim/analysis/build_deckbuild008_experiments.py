"""SIM-DECKBUILD-008 — variant metrics, dork audit, Strix-slot screen, package comparison,
cut ablation + Pareto frontier, Conversion Surface Area, tutor graph, resilience, tournament
scenarios.

Run classes: DECK_BACKED_GOLDFISH (Monte Carlo development, paired common-random-number design)
and STATIC_ANALYSIS (tutor graph, role counts). Nothing here simulates opponents; no win RATE is
produced. Every probability is "a deterministic line is available in this window if nobody
interacts", reported with a 95% interval.

Pairing: every variant is the frozen baseline with slot-preserving swaps (an added card takes
its cut card's slot), and game i uses seed BASE_SEED + i for every variant. Differences between
variants are therefore paired and their standard errors come from per-game differences.

Usage:
    python3 sim/analysis/build_deckbuild008_experiments.py --phase all [--n 20000] [--procs 4]
Phases: dork, strix, packages, marginals, verify, depth, states, graph, scenarios, assemble
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild008_cards as dc  # noqa: E402
import deckbuild008_solver as sv  # noqa: E402
from deckbuild008_goldfish import Game  # noqa: E402

OUT = REPO_ROOT / "results" / "solo_baseline"
WORK = OUT / "deckbuild008_work"
BASE_SEED = 8_000_000
MAX_TURN = 4

ORACLE, CONSULT, PACT, SEEKER = "Thassa's Oracle", "Demonic Consultation", "Tainted Pact", "Spellseeker"
DRS = "Deathrite Shaman"
STRIX = "Strix Serenade"

# Cards whose removal must clear an unusually high bar (assignment section 4). They are never
# placed in the default cut pool; Imperial Seal appears only as a labeled stress test.
PROTECTED = {
    "Birthing Pod", "Abhorrent Oculus", "Devoted Druid", "Hazel's Brewmaster", "Swift Reconfiguration",
    "Machine God's Effigy", "Nature's Rhythm", "The Cabbage Merchant", "Mockingbird", "Flash Photography",
    "High Fae Trickster", "Teferi, Mage of Zhalfir", "Emergence Zone", "Crop Rotation", "Silence",
    "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos", "Force of Will", "Force of Negation",
    "Fierce Guardianship", "Flare of Denial", "Pact of Negation", "Mindbreak Trap", "Misdirection",
    "Commandeer", "Subtlety", "Imperial Seal", "Vampiric Tutor", "Demonic Tutor",
}
CUT_POOL = [
    "Faerie Mastermind", "The Queen of Dale", "Delney, Streetwise Lookout", "Swan Song", "Flusterstorm",
    "Mental Misstep", "Clever Impersonator", "Colossal Skyturtle", "Volatile Stormdrake", "Gilded Drake",
    "Gleaming Splendor", "Lotho, Corrupt Shirriff", "Oboro Breezecaller", "Derevi, Empyrial Tactician",
    "Endurance", "Esper Sentinel", "Orcish Bowmasters",
]
STRESS_POOL = ["Imperial Seal"]
# Package comparisons use goldfish-inert cuts (never cast or tutored in this model) so that the
# package effect is not confounded with a cut effect; real cuts are chosen by the ablation.
INERT_CUTS = ["Volatile Stormdrake", "Colossal Skyturtle", "Gilded Drake", "Endurance"]
DORKS = ["Avacyn's Pilgrim", "Llanowar Elves", "Elvish Mystic", "Fyndhorn Elves", "Elves of Deep Shadow",
         "Arbor Elf", "Boreal Druid", "Gilded Goose"]
STRIX_SCREEN = [SEEKER, "Worldly Tutor", "Mystical Tutor", "Green Sun's Zenith", "Summoner's Pact",
                "Training Grounds", "Veil of Summer", "Biomancer's Familiar", "Seedborn Muse",
                "Sylvan Library", "Borne Upon a Wind", "Shang-Chi, Master of Kung Fu"]


# ---- variant construction --------------------------------------------------------------------------

def baseline():
    names, h = dc.frozen_baseline()
    return names, h


def swap(deck, cuts, adds):
    assert len(cuts) == len(adds), (cuts, adds)
    out = list(deck)
    for c, a in zip(cuts, adds):
        assert c in out, f"{c} not in deck"
        assert a == dc.BLANK or a not in out, f"{a} already in deck"
        out[out.index(c)] = a
    assert len(out) == 98
    return out


def with_dork(deck, dork):
    return swap(deck, [DRS], [dork]) if dork != DRS else list(deck)


# ---- Monte Carlo worker ------------------------------------------------------------------------------

FAM_ORACLE = {"oracle_consult", "oracle_pact", "oracle_hermit", "oracle_witch"}
FAM_INF = {"inf_oracle", "inf_bowmasters"}


def _first(rec, pred):
    for t in range(1, MAX_TURN + 1):
        r = rec["turns"].get(t)
        if not r:
            continue
        if pred(r["main"]):
            return t
        if "instant" in r and pred(r["instant"]):
            return t + 0.5
    return 0


def play_one(args):
    deck, seed, kw = args
    g = Game(deck, seed=seed, on_play=(seed % 4 == 0), max_turn=MAX_TURN, **kw)
    rec = g.play()
    op = g.opening
    from deckbuild008_goldfish import hand_features
    f = hand_features(op, g.on_play)
    eng = 0
    for t in range(1, MAX_TURN + 1):
        r = rec["turns"].get(t)
        if r and r.get("end", {}).get("premium_on_bf"):
            eng = t
            break
    t1 = rec["turns"].get(1, {})
    t2 = rec["turns"].get(2, {})
    out = {
        "m": rec["mulligans"], "hs": len(op), "fm": f["mana_total"], "ln": f["lands"],
        "c1": t1.get("colors", ""), "c2": t2.get("colors", ""),
        "a1": t1.get("mana_avail", 0), "a2": t2.get("mana_avail", 0),
        "d1": t1.get("nonland_cast", 0), "d2": t2.get("nonland_cast", 0), "eng": eng,
        "w": _first(rec, lambda s: s["det"]),
        "wp": _first(rec, lambda s: s["det"] and s["protected"]),
        "wi": _first(rec, lambda s: s["det"] and s.get("instant")),
        "wo": _first(rec, lambda s: bool(s["families"] & FAM_ORACLE)),
        "wf": _first(rec, lambda s: bool(s["families"] & FAM_INF)),
        "wn": _first(rec, lambda s: s["nondet"]),
        "fam": [],
    }
    if out["w"]:
        t = int(out["w"])
        s = rec["turns"][t]["main"] if out["w"] == t else rec["turns"][t]["instant"]
        out["fam"] = sorted(s["families"] - set(sv.NONDET_FAMILIES))
        out["mc"] = s["min_cards"]
        out["ms"] = s["min_spells"]
    return out


def run(deck, n, procs, kw=None, pool=None):
    kw = kw or {}
    args = [(deck, BASE_SEED + i, kw) for i in range(n)]
    if pool is not None:
        return pool.map(play_one, args, chunksize=200)
    return [play_one(a) for a in args]


def wilson(k, n):
    if n == 0:
        return [None, None]
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 5), round(c + h, 5)]


def by(x, t):
    return 1 if (x and x <= t + 0.5) else 0


METRIC_FNS = {
    "keep7": lambda g: g["m"] == 0,
    "mean_mulligans": lambda g: g["m"],
    "kept_hand_fm0": lambda g: g["fm"] < 1,
    "kept_hand_fm1": lambda g: 1 <= g["fm"] < 2,
    "kept_hand_fm2plus": lambda g: g["fm"] >= 2,
    "t1_has_W": lambda g: "W" in g["c1"], "t1_has_U": lambda g: "U" in g["c1"],
    "t1_has_B": lambda g: "B" in g["c1"], "t1_has_G": lambda g: "G" in g["c1"],
    "t2_all_four_colors": lambda g: len(g["c2"]) == 4,
    "t2_three_plus_colors": lambda g: len(g["c2"]) >= 3,
    "t1_mana_ge2": lambda g: g["a1"] >= 2, "t2_mana_ge3": lambda g: g["a2"] >= 3,
    "t1_development": lambda g: g["d1"] >= 1,
    "t2_development": lambda g: (g["d1"] + g["d2"]) >= 2 or (g["eng"] and g["eng"] <= 2),
    "premium_engine_by_t2": lambda g: bool(g["eng"]) and g["eng"] <= 2,
    "premium_engine_by_t3": lambda g: bool(g["eng"]) and g["eng"] <= 3,
    "premium_engine_by_t4": lambda g: bool(g["eng"]) and g["eng"] <= 4,
}
for _t in (2, 3, 4):
    METRIC_FNS[f"det_win_by_t{_t}"] = (lambda t: lambda g: by(g["w"], t))(_t)
    METRIC_FNS[f"det_protected_by_t{_t}"] = (lambda t: lambda g: by(g["wp"], t))(_t)
    METRIC_FNS[f"det_instant_window_by_t{_t}"] = (lambda t: lambda g: by(g["wi"], t))(_t)
    METRIC_FNS[f"oracle_line_by_t{_t}"] = (lambda t: lambda g: by(g["wo"], t))(_t)
    METRIC_FNS[f"infinite_line_by_t{_t}"] = (lambda t: lambda g: by(g["wf"], t))(_t)
    METRIC_FNS[f"any_incl_nondet_by_t{_t}"] = (lambda t: lambda g: by(g["wn"], t))(_t)
KEY_METRICS = ["det_win_by_t3", "det_win_by_t4", "det_protected_by_t4", "det_instant_window_by_t4",
               "oracle_line_by_t4", "infinite_line_by_t4", "premium_engine_by_t2", "premium_engine_by_t3",
               "keep7", "mean_mulligans", "kept_hand_fm2plus", "t1_development", "t2_mana_ge3",
               "t2_all_four_colors"]


def summarize(games, ref=None):
    n = len(games)
    out = {"n": n}
    for k, fn in METRIC_FNS.items():
        vals = [float(fn(g)) for g in games]
        mean = sum(vals) / n
        row = {"value": round(mean, 5)}
        if k != "mean_mulligans":
            row["ci95"] = wilson(int(round(sum(vals))), n)
        if ref is not None:
            rv = [float(fn(g)) for g in ref]
            d = [a - b for a, b in zip(vals, rv)]
            md = sum(d) / n
            sd = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1))
            row["delta_vs_ref"] = round(md, 5)
            row["delta_se"] = round(sd / math.sqrt(n), 5)
        out[k] = row
    fam = Counter()
    for g in games:
        for f in g["fam"]:
            fam[f] += 1
    out["first_win_family_counts"] = dict(fam)
    wins = [g for g in games if g["w"]]
    out["first_win_mean_cards"] = round(sum(g.get("mc") or 0 for g in wins) / len(wins), 3) if wins else None
    out["first_win_mean_spells"] = round(sum(g.get("ms") or 0 for g in wins) / len(wins), 3) if wins else None
    return out


# ---- descriptive structure -----------------------------------------------------------------------------

def structure(deck):
    roles = Counter()
    for c in deck:
        for r in dc.roles(c):
            roles[r] += 1
    lands = sum(1 for c in deck if dc.is_land(c))
    rocks = sum(1 for c in deck if c in dc.MANA_PERMS and dc.MANA_PERMS[c][0] in ("rock", "oneshot")
                and c not in ("Mox Amber", "Machine God's Effigy"))
    dorks = sum(1 for c in deck if c in dc.MANA_PERMS and dc.MANA_PERMS[c][0] == "dork")
    return {
        "lands_incl_mdfc": lands,
        "mana_density_functional": lands,  # the assignment's 28-slot land count
        "fast_mana_rocks_excl_amber": rocks, "mox_amber": int("Mox Amber" in deck),
        "esg": int("Elvish Spirit Guide" in deck), "dorks": dorks,
        "creatures": sum(1 for c in deck if not dc.is_land(c) and dc.is_creature(c)),
        "interaction": sum(1 for c in deck if c in dc.INTERACTION),
        "free_counters": sum(1 for c in deck if c in dc.FREE_COUNTERS),
        "proactive_protection": sum(1 for c in deck if c in dc.PROACTIVE_PROTECTION),
        "tutor_access": sum(1 for c in deck if c in dc.TUTORS or c == PACT),
        "card_advantage": roles["card_advantage"], "premium_engines": sum(1 for c in deck if c in dc.PREMIUM_ENGINES),
        "timing": roles["timing"], "combo_components": roles["combo_component"],
        "blue_cards": sum(1 for c in deck if not dc.is_land(c) and dc.is_blue(c)),
        "roles": dict(roles),
    }


# ---- phases -------------------------------------------------------------------------------------------

def load_work(name):
    p = WORK / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_work(name, obj):
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"{name}.json").write_text(json.dumps(obj, indent=1, default=list) + "\n")


def phase_dork(n, pool):
    base, _ = baseline()
    ref = run(base, n, 0, pool=pool)
    res = {"baseline_deathrite": summarize(ref)}
    ref_opp = run(base, n, 0, {"opp_gy_land_from": 2}, pool=pool)
    res["baseline_deathrite_opp_graveyard_land_from_t2"] = summarize(ref_opp, ref)
    for d in DORKS:
        res[d] = summarize(run(with_dork(base, d), n, 0, pool=pool), ref)
        print("dork", d, res[d]["det_win_by_t4"], res[d]["t1_development"], flush=True)
    # Conditional design: the candidate is in the opening seven (no mulligan), every other card
    # identical across candidates. Isolates "how good is this dork when you have it".
    cond = {}
    for d in [DRS] + DORKS:
        deck = with_dork(base, d)
        kw = {"force_opening": [d], "mulligan": False}
        cond[d] = summarize(run(deck, n, 0, kw, pool=pool))
        print("cond", d, cond[d]["t1_mana_ge2"], cond[d]["t2_mana_ge3"], flush=True)
    ref_c = run(base, n, 0, {"force_opening": [DRS], "mulligan": False, "opp_gy_land_from": 2}, pool=pool)
    cond["Deathrite Shaman (opponent graveyard land from T2)"] = summarize(ref_c)
    res["conditional_in_opening_hand"] = cond
    res["_rules_table"] = DORK_RULES
    save_work("dork", res)


DORK_RULES = {
    # name: colours, true mana ability (Kinnan/Badgermole), T1 castable off, creature type, notes
    "Deathrite Shaman": {"colors": "WUBG (needs a land card in a graveyard)", "true_mana_ability": False,
                         "cast_with": "B or G (hybrid)", "pod_mv": 1, "elf": True,
                         "note": "targets -> not a mana ability: no Kinnan/Badgermole; dead with empty graveyards"},
    "Avacyn's Pilgrim": {"colors": "W", "true_mana_ability": True, "cast_with": "G", "pod_mv": 1, "elf": False,
                         "note": "only white dork; W is the Swift/Silence/Tymna colour"},
    "Llanowar Elves": {"colors": "G", "true_mana_ability": True, "cast_with": "G", "pod_mv": 1, "elf": True, "note": ""},
    "Elvish Mystic": {"colors": "G", "true_mana_ability": True, "cast_with": "G", "pod_mv": 1, "elf": True,
                      "note": "functionally identical to Llanowar Elves"},
    "Fyndhorn Elves": {"colors": "G", "true_mana_ability": True, "cast_with": "G", "pod_mv": 1, "elf": True,
                       "note": "functionally identical to Llanowar Elves"},
    "Elves of Deep Shadow": {"colors": "B", "true_mana_ability": True, "cast_with": "G", "pod_mv": 1, "elf": True,
                             "note": "1 damage per tap; B is the Consult/Pact/DT colour"},
    "Arbor Elf": {"colors": "copy of a Forest-typed dual", "true_mana_ability": False, "cast_with": "G",
                  "pod_mv": 1, "elf": True, "note": "untap ability is not a mana ability; needs Bayou/Savannah/Trop"},
    "Boreal Druid": {"colors": "C", "true_mana_ability": True, "cast_with": "G", "pod_mv": 1, "elf": True, "note": ""},
    "Gilded Goose": {"colors": "any, once (then {1}{G} per Food)", "true_mana_ability": True, "cast_with": "G",
                     "pod_mv": 1, "elf": False, "note": "sacrifice-Food mana; not a repeatable dork"},
}


def best_dork():
    res = load_work("dork")
    if not res:
        return "Avacyn's Pilgrim"
    return res.get("_chosen", "Avacyn's Pilgrim")


def phase_strix(n, pool, dork):
    base = with_dork(baseline()[0], dork)
    ref = run(base, n, 0, pool=pool)
    res = {"reference": {"dork": dork, **summarize(ref)}}
    for c in STRIX_SCREEN:
        res[c] = summarize(run(swap(base, [STRIX], [c]), n, 0, pool=pool), ref)
        print("strix", c, res[c]["det_win_by_t4"], res[c]["premium_engine_by_t3"], flush=True)
    save_work("strix", res)


def package_variants(dork, a_card):
    base0 = baseline()[0]
    base = with_dork(base0, dork)
    S = STRIX
    V = {}
    V["BASELINE_v8"] = (base0, "frozen Moxfield v8 (Deathrite, Strix)")
    V["A_oracle_less"] = (swap(base, [S], [a_card]), f"DRS->{dork}; Strix->{a_card}")
    V["B_oracle_consult"] = (swap(base, [S, INERT_CUTS[0]], [ORACLE, CONSULT]), "Oracle + Consultation")
    V["B2_oracle_pact"] = (swap(base, [S, INERT_CUTS[0]], [ORACLE, PACT]), "Oracle + Tainted Pact")
    V["C_oracle_core3"] = (swap(base, [S] + INERT_CUTS[:2], [ORACLE, CONSULT, PACT]), "Oracle + Consult + Pact")
    V["D_core3_spellseeker"] = (swap(base, [S] + INERT_CUTS[:3], [ORACLE, CONSULT, PACT, SEEKER]),
                                "Oracle + Consult + Pact + Spellseeker")
    V["D2_oracle_consult_spellseeker"] = (swap(base, [S] + INERT_CUTS[:2], [ORACLE, CONSULT, SEEKER]),
                                          "Oracle + Consult + Spellseeker (no Pact)")
    for extra in ("Borne Upon a Wind", "Training Grounds", "Mystical Tutor", "Allosaurus Shepherd",
                  "Worldly Tutor", "Veil of Summer"):
        key = "E_D_plus_" + extra.split(",")[0].replace(" ", "_").replace("'", "")
        V[key] = (swap(base, [S] + INERT_CUTS[:4], [ORACLE, CONSULT, PACT, SEEKER, extra]), f"D + {extra}")
    V["F_oracle_hermit"] = (swap(base, [S, INERT_CUTS[0]], [ORACLE, "Hermit Druid"]), "Oracle + Hermit Druid")
    V["F_oracle_hermit_shangchi"] = (swap(base, [S] + INERT_CUTS[:2], [ORACLE, "Hermit Druid", "Shang-Chi, Master of Kung Fu"]),
                                     "Oracle + Hermit Druid + Shang-Chi")
    V["F_oracle_witch"] = (swap(base, [S, INERT_CUTS[0]], [ORACLE, "Divining Witch"]), "Oracle + Divining Witch")
    V["F_oracle_witch_shangchi"] = (swap(base, [S] + INERT_CUTS[:2], [ORACLE, "Divining Witch", "Shang-Chi, Master of Kung Fu"]),
                                    "Oracle + Divining Witch + Shang-Chi")
    V["F_oracle_consult_hermit"] = (swap(base, [S] + INERT_CUTS[:2], [ORACLE, CONSULT, "Hermit Druid"]),
                                    "Oracle + Consult + Hermit Druid")
    V["F_oracle_hermit_witch_shangchi"] = (swap(base, [S] + INERT_CUTS[:3], [ORACLE, "Hermit Druid", "Divining Witch", "Shang-Chi, Master of Kung Fu"]),
                                           "Oracle + Hermit + Witch + Shang-Chi")
    V["G_oracle_only"] = (swap(base, [S], [ORACLE]), "Oracle alone (Thrasios-infinite outlet only)")
    return V


HEADLINE = ["BASELINE_v8", "A_oracle_less", "B_oracle_consult", "B2_oracle_pact", "C_oracle_core3",
            "D_core3_spellseeker", "F_oracle_hermit_shangchi", "G_oracle_only"]


def phase_packages(n, pool, dork, a_card, policies=("pilot",)):
    V = package_variants(dork, a_card)
    if policies != ("pilot",):
        V = {k: v for k, v in V.items() if k in HEADLINE}
    res = {}
    for policy in policies:
        kw = {"policy": policy}
        ref = run(V["A_oracle_less"][0], n, 0, kw, pool=pool)
        out = {}
        for k, (deck, desc) in V.items():
            g = ref if k == "A_oracle_less" else run(deck, n, 0, kw, pool=pool)
            out[k] = {"description": desc, "structure": structure(deck), **summarize(g, ref)}
            print(policy, k, out[k]["det_win_by_t4"]["value"], out[k].get("det_win_by_t4", {}).get("delta_vs_ref"), flush=True)
        res[policy] = out
    save_work("packages_" + "_".join(policies), res)


def phase_sensitivity(n, pool, dork, a_card):
    """Tutor policy (hold) and engine-draw scenario band on the headline variants."""
    V = package_variants(dork, a_card)
    keys = ["A_oracle_less", "B_oracle_consult", "C_oracle_core3", "D_core3_spellseeker"]
    res = {}
    for label, kw in (("hold_tutors", {"tutor_policy": "hold"}), ("engine_draws", {"engine_draws": True}),
                      ("no_mulligan_raw7", {"mulligan": False})):
        ref = run(V["A_oracle_less"][0], n, 0, kw, pool=pool)
        res[label] = {}
        for k in keys:
            g = ref if k == "A_oracle_less" else run(V[k][0], n, 0, kw, pool=pool)
            res[label][k] = summarize(g, ref)
            print(label, k, res[label][k]["det_win_by_t4"], flush=True)
    save_work("sensitivity", res)


def superdeck(dork, extra_adds=(ORACLE, CONSULT, PACT, SEEKER)):
    """Baseline (with dork fix) plus the Oracle package: 98 + len(adds) cards. Used only for
    single-card marginal ablation (each candidate -> BLANK), never as a recommended list."""
    return with_dork(baseline()[0], dork) + list(extra_adds)


def phase_marginals(n, pool, dork):
    res = {}
    for label, adds in (("oracle_context_D", (ORACLE, CONSULT, PACT, SEEKER)),
                        ("oracle_less_context", ())):
        deck = superdeck(dork, adds)
        ref = run(deck, n, 0, pool=pool)
        out = {"_reference": summarize(ref)}
        for c in [STRIX] + CUT_POOL + STRESS_POOL + ["Demonic Tutor", "Vampiric Tutor", "Survival of the Fittest",
                                                     "Chord of Calling", "Finale of Devastation", "Eldritch Evolution",
                                                     "Neoform", "Birthing Pod", "Enlightened Tutor", "Worldly Tutor"
                                                     if "Worldly Tutor" in deck else "Nature's Rhythm"] + \
                ([SEEKER, PACT, CONSULT] if adds else []):
            if c not in deck:
                continue
            d2 = list(deck)
            d2[d2.index(c)] = dc.BLANK
            out[c] = summarize(run(d2, n, 0, pool=pool), ref)
            print(label, c, out[c]["det_win_by_t4"], flush=True)
        res[label] = out
    save_work("marginals", res)


def phase_verify(n, pool, dork, frontier_sets, a_card):
    base = with_dork(baseline()[0], dork)
    ref = run(swap(base, [STRIX], [a_card]), n, 0, pool=pool)
    res = {}
    for label, adds, cuts in frontier_sets:
        deck = swap(base, cuts, adds)
        res[label] = {"adds": adds, "cuts": cuts, "structure": structure(deck), **summarize(run(deck, n, 0, pool=pool), ref)}
        print("verify", label, res[label]["det_win_by_t4"], flush=True)
    save_work("verify", res)


# ---- tutor / access graph (static) ---------------------------------------------------------------------

GRAPH_PIECES = [ORACLE, CONSULT, PACT, SEEKER, "Devoted Druid", "Swift Reconfiguration", "Hazel's Brewmaster",
                "Machine God's Effigy", "Hermit Druid", "Divining Witch", "Shang-Chi, Master of Kung Fu",
                "Birthing Pod", "Silence", "Grand Abolisher", "Emergence Zone", "High Fae Trickster",
                "Teferi, Mage of Zhalfir", "Orcish Bowmasters", "Faerie Mastermind", "Finale of Devastation",
                "Nature's Rhythm", "Demonic Tutor"]


def access_edges(deck):
    """tutor -> target edges among cards in `deck` (commanders excluded), with delivery details."""
    edges = []
    creatures = [c for c in deck if not dc.is_land(c) and dc.is_creature(c)]
    for t in deck:
        if t not in dc.TUTORS:
            continue
        spec = dc.TUTORS[t]
        for target in deck:
            if target == t or target == dc.BLANK:
                continue
            if spec["find"] in ("creature_sac_plus1", "creature_sac_plus2"):
                if not dc.is_creature(target) or dc.is_land(target):
                    continue
                if spec["find"] == "creature_sac_plus1":
                    fodder = [c for c in creatures if dc.mv(c) == dc.mv(target) - 1 and c != target]
                else:
                    fodder = [c for c in creatures if dc.mv(c) >= dc.mv(target) - 2 and c != target]
                if not fodder:
                    continue
                extra = {"fodder_in_deck": len(fodder), "fodder_examples": sorted(fodder)[:6]}
            else:
                if not dc.tutor_can_find(t, target):
                    continue
                extra = {}
            if spec["dest"] == "bf" and spec["find"] == "land":
                pass
            g, pips = dc.cost_of(t, dc.mv(target) if spec.get("x_cost") else 0)
            if spec.get("on_bf"):
                g, pips = spec["activation"]
            mana = g + len([p for p in pips if "P" not in p])
            if spec["dest"] == "top":
                mana_to_usable = mana + 4 + dc.mv(target)  # + Thrasios draw, then cast
            elif spec["dest"] == "hand":
                mana_to_usable = mana + (0 if dc.is_instant_or_sorcery(target) else 0) + dc.mv(target)
            else:
                mana_to_usable = mana
            edges.append({"tutor": t, "target": target, "dest": spec["dest"], "speed": spec["speed"],
                          "tutor_cost_mana": mana, "mana_to_resolved_target": mana_to_usable, **extra})
    return edges


def access_graph(deck, label):
    edges = access_edges(deck)
    into = defaultdict(list)
    for e in edges:
        into[e["target"]].append(e)
    pieces = {}
    for p in GRAPH_PIECES:
        if p not in deck:
            continue
        direct = sorted({e["tutor"] for e in into[p]})
        two_step = set()
        for e in into[p]:
            for e2 in into[e["tutor"]]:
                two_step.add((e2["tutor"], e["tutor"]))
        pieces[p] = {
            "direct_tutors": direct, "n_direct": len(direct),
            "two_step_paths": sorted(f"{a} -> {b}" for a, b in two_step), "n_two_step": len(two_step),
            "effective_copies_1step": 1 + len(direct),
            "cheapest_direct": min((e["mana_to_resolved_target"] for e in into[p]), default=None),
            "instant_speed_direct": sorted({e["tutor"] for e in into[p] if e["speed"] in ("instant", "ability")}),
        }
    # Package effective copies: distinct (card or one-step tutor) ways to put each half in hand/play.
    seeker = None
    if SEEKER in deck:
        tg = [e for e in edges if e["tutor"] == SEEKER]
        seeker = {
            "targets": sorted(e["target"] for e in tg),
            "targets_by_role": {
                "oracle_package": sorted(e["target"] for e in tg if e["target"] in (CONSULT, PACT)),
                "tutors": sorted(e["target"] for e in tg if e["target"] in dc.TUTORS),
                "protection_interaction": sorted(e["target"] for e in tg if e["target"] in dc.INTERACTION
                                                 or e["target"] in dc.PROACTIVE_PROTECTION),
                "other": sorted(e["target"] for e in tg if e["target"] not in dc.TUTORS and e["target"] not in
                                (CONSULT, PACT) and e["target"] not in dc.INTERACTION
                                and e["target"] not in dc.PROACTIVE_PROTECTION),
            },
            "accessed_by": sorted({e["tutor"] for e in into[SEEKER]}),
            "pod_2_to_3_fodder": sorted(c for c in deck if not dc.is_land(c) and dc.is_creature(c) and dc.mv(c) == 2),
            "kinnan_can_hit": False,  # Spellseeker is a Human Wizard; Kinnan puts non-Human creatures
            "creature_tutors_reaching_spellseeker": sorted({e["tutor"] for e in into[SEEKER] if e["dest"] in ("bf",)} |
                                                           ({"Survival of the Fittest"} & {e["tutor"] for e in into[SEEKER]})),
        }
    return {"label": label, "n_edges": len(edges), "pieces": pieces, "spellseeker_audit": seeker,
            "edges": edges}


def phase_graph(dork, a_card):
    V = package_variants(dork, a_card)
    out = {"task": "SIM-DECKBUILD-008", "artifact": "tutor_graph", "run_class": "STATIC_ANALYSIS",
           "rules_notes": [
               "Spellseeker: instant/sorcery MV<=2; X spells have MV 2 in library (Finale, Nature's Rhythm).",
               "Birthing Pod/Neoform: exactly MV+1; Eldritch Evolution: MV<=sac+2; Chord/Finale/Rhythm: X>=MV.",
               "Top-of-library tutors need a draw: modeled as one Thrasios activation ({4}, {2} with Training Grounds).",
               "Kinnan's activation can find Oracle (Merfolk) but not Spellseeker (Human); random -> nondeterministic.",
               "Green Sun's Zenith / Summoner's Pact find green creatures only: neither finds Oracle or Spellseeker.",
           ],
           "variants": {}}
    for k in ("BASELINE_v8", "A_oracle_less", "C_oracle_core3", "D_core3_spellseeker",
              "F_oracle_hermit_shangchi", "F_oracle_witch_shangchi"):
        out["variants"][k] = access_graph(V[k][0], k)
    (OUT / "deckbuild008_tutor_graph.json").write_text(json.dumps(out, indent=1) + "\n")


# ---- state-conditioned analyses: CSA, tutor leverage, dead cards, resilience ---------------------------

UNLIMITED = Counter({dc.ANY: 14})
RELEVANT_EXTRA = {"Silence", "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos"}


def _clone(s, **kw):
    d = dict(hand=list(s.hand), bf=[sv.Perm(p.name, p.sick, p.tapped, dict(p.extra)) for p in s.bf],
             library=list(s.library), gy=list(s.gy), cmd=set(s.cmd), cmd_tax=dict(s.cmd_tax),
             land_drop=s.land_drop, timing=s.timing, turn=s.turn, units_override=s.units_override,
             opp_gy_land=s.opp_gy_land)
    d.update(kw)
    return sv.Snapshot(**d)


def disruptions(s):
    """Simplified disruption classes -> modified snapshots (no opponent behaviour modeled)."""
    out = {}
    creatures = [p for p in s.bf if not dc.is_land(p.name) and dc.is_creature(p.name)]
    out["board_wipe_creatures"] = _clone(s, bf=[p for p in s.bf if p not in creatures],
                                         gy=s.gy + [p.name for p in creatures], units_override=None)
    arts = [p for p in s.bf if not dc.is_land(p.name) and "Artifact" in dc.card(p.name)["type"]
            and not dc.is_creature(p.name)]
    out["artifact_removal_all"] = _clone(s, bf=[p for p in s.bf if p not in arts], units_override=None)
    out["graveyard_exiled"] = _clone(s, gy=[])
    # Cursed-Totem-style: activated abilities of creatures (incl. creature mana abilities) off.
    def no_creature_abilities(snap):
        return _clone(snap, bf=[sv.Perm(p.name, p.sick, True if (dc.is_creature(p.name) and not dc.is_land(p.name)) else p.tapped,
                                        dict(p.extra)) for p in snap.bf], units_override=None)
    out["creature_abilities_suppressed"] = no_creature_abilities(s)
    out["lose_thrasios"] = _clone(s, bf=[p for p in s.bf if p.name != sv.THRASIOS],
                                  cmd=set(s.cmd) - {sv.THRASIOS}, units_override=None)
    out["lose_pod"] = _clone(s, bf=[p for p in s.bf if p.name != "Birthing Pod"],
                             hand=[h for h in s.hand if h != "Birthing Pod"], units_override=None)
    return out


def single_piece_loss(s, used):
    """Remove each used piece in turn; fraction of removals after which a det line remains."""
    pieces = [u for u in used if u not in dc.COMMANDERS]
    if not pieces:
        return None
    ok = 0
    for p in pieces:
        s2 = _clone(s, hand=[h for h in s.hand if h != p], bf=[q for q in s.bf if q.name != p],
                    library=[c for c in s.library if c != p], units_override=None)
        ok += sv.solve(s2, want=("det",))["det"]
    return ok / len(pieces)


def csa_relevant(s, deck_set):
    rel = set(dc.TUTORS) | dc.COMBO_PIECES | set(dc.MANA_PERMS) | dc.FAST_MANA_FROM_HAND | dc.TIMING | \
        RELEVANT_EXTRA | {SEEKER, "Training Grounds", "Biomancer's Familiar", "Kinnan, Bonder Prodigy",
                          "Badgermole Cub", "Enduring Vitality", "Lotus Petal", "Delney, Streetwise Lookout",
                          "Borne Upon a Wind", "Mockingbird", "Clever Impersonator", "Flash Photography"}
    lib = [c for c in s.library]
    keep = [c for c in set(lib) if c in rel or (dc.is_land(c) and s.land_drop)]
    base = sv.solve(s)
    out = {"library": len(lib), "already_winning": base["det"], "already_protected": base["protected"],
           "already_instant": base.get("instant", False), "win_draws": 0, "protected_draws": 0,
           "piece_draws": 0, "tutor_draws": 0, "nondet_draws": 0, "cards": []}
    if base["det"]:
        return out
    for c in keep:
        s2 = _clone(s, hand=s.hand + [c], library=[x for x in lib if x != c])
        r = sv.solve(s2, want=("det", "protected"))
        if r["det"]:
            out["win_draws"] += 1
            out["cards"].append(c)
            out["protected_draws"] += r["protected"]
            if c in dc.TUTORS or c == SEEKER:
                out["tutor_draws"] += 1
            else:
                out["piece_draws"] += 1
        elif r["nondet"]:
            out["nondet_draws"] += 1
    return out


TUTOR_ENGINE_TARGETS = dc.PREMIUM_ENGINES
TUTOR_PROTECTION_TARGETS = dc.PROACTIVE_PROTECTION | {"Force of Will", "Fierce Guardianship", "Pact of Negation"}


def tutor_leverage(s):
    rows = {}
    tutors = [t for t in s.hand if t in dc.TUTORS or t == PACT]
    if not tutors:
        return rows
    now = sv.solve(s, want=("all",))
    setup = sv.solve(_clone(s, units_override=UNLIMITED, land_drop=False), want=("all",))
    lib = set(s.library)
    for t in tutors:
        if t == PACT:
            fair = True
            eng = bool(lib & TUTOR_ENGINE_TARGETS)
            prot = bool(lib & TUTOR_PROTECTION_TARGETS)
        else:
            # Access semantics: sacrifice-based tutors are judged by target class (fodder assumed).
            can = (lambda x: dc.is_creature(x)) if dc.TUTORS[t]["find"].startswith("creature_sac") else \
                (lambda x: dc.tutor_can_find(t, x))
            eng = any(can(x) for x in lib & TUTOR_ENGINE_TARGETS)
            prot = any(can(x) for x in lib & TUTOR_PROTECTION_TARGETS)
        rows[t] = {"immediate_win": t in now["used_cards"], "one_turn_setup_win": t in setup["used_cards"],
                   "engine_access": eng, "protection_access": prot}
    return rows


PACKAGE_CARDS = [ORACLE, CONSULT, PACT, SEEKER, "Hermit Druid", "Divining Witch", "Shang-Chi, Master of Kung Fu"]


def dead_cards(s):
    """Package cards in hand that no deterministic line can use even with unlimited mana."""
    out = {}
    held = [c for c in PACKAGE_CARDS if c in s.hand]
    if not held:
        return out
    r = sv.solve(_clone(s, units_override=UNLIMITED, land_drop=False), want=("all",))
    for c in held:
        out[c] = {"live_in_det_line": c in r["used_cards"]}
    return out


def state_job(args):
    deck, seed, label = args
    g = Game(deck, seed=seed, on_play=(seed % 4 == 0), max_turn=MAX_TURN, record_snapshots=True)
    g.play()
    deck_set = set(deck)
    res = {"seed": seed}
    for t in (1, 2, 3, 4):
        for timing in ("main", "instant"):
            s = g.snapshots.get((t, timing))
            if s is None:
                continue
            key = f"t{t}_{timing}"
            c = csa_relevant(s, deck_set)
            c.pop("cards")
            res[key] = c
            if timing == "main" and t in (3, 4):
                res[key + "_tutors"] = tutor_leverage(s)
                base = sv.solve(s, want=("all",))
                if base["det"]:
                    dis = {}
                    for name, s2 in disruptions(s).items():
                        dis[name] = sv.solve(s2, want=("det",))["det"]
                    dis["single_piece_loss_survival"] = single_piece_loss(s, base["used_cards"])
                    res[key + "_resilience"] = dis
        if (t, "end_hand") in g.snapshots and t == 4:
            hand, bf = g.snapshots[(t, "end_hand")]
            s = sv.Snapshot(hand, bf, list(g.library), list(g.gy), set(g.cmd), {}, False, "main", t)
            res["t4_dead"] = dead_cards(s)
    return res


def aggregate_states(rows):
    out = {}
    for t in (1, 2, 3, 4):
        for timing in ("main", "instant"):
            key = f"t{t}_{timing}"
            vals = [r[key] for r in rows if key in r]
            if not vals:
                continue
            n = len(vals)
            alive = [v for v in vals if not v["already_winning"]]
            mean = lambda f, xs: (sum(f(v) for v in xs) / len(xs)) if xs else None  # noqa: E731
            out[key] = {
                "n_states": n,
                "p_already_winning": round(mean(lambda v: v["already_winning"], vals), 4),
                "p_already_protected": round(mean(lambda v: v["already_protected"], vals), 4),
                "mean_library": round(mean(lambda v: v["library"], vals), 2),
                "csa_win_draws_mean": round(mean(lambda v: v["win_draws"], alive), 3) if alive else None,
                "csa_piece_draws_mean": round(mean(lambda v: v["piece_draws"], alive), 3) if alive else None,
                "csa_tutor_draws_mean": round(mean(lambda v: v["tutor_draws"], alive), 3) if alive else None,
                "csa_protected_draws_mean": round(mean(lambda v: v["protected_draws"], alive), 3) if alive else None,
                "csa_nondet_draws_mean": round(mean(lambda v: v["nondet_draws"], alive), 3) if alive else None,
                "p_next_draw_wins": round(mean(lambda v: v["win_draws"] / max(1, v["library"]), alive), 4) if alive else None,
                "p_any_winning_draw_exists": round(mean(lambda v: v["win_draws"] > 0, alive), 4) if alive else None,
            }
    tut = defaultdict(Counter)
    for r in rows:
        for key in ("t3_main_tutors", "t4_main_tutors"):
            for t, d in r.get(key, {}).items():
                tut[t]["n"] += 1
                for k, v in d.items():
                    tut[t][k] += int(bool(v))
    out["tutor_leverage_t3_t4"] = {t: {"n_states_held": c["n"], **{k: round(c[k] / c["n"], 4) for k in c if k != "n"}}
                                   for t, c in sorted(tut.items())}
    res = defaultdict(list)
    for r in rows:
        for key in ("t3_main_resilience", "t4_main_resilience"):
            for k, v in r.get(key, {}).items():
                if v is not None:
                    res[k].append(float(v))
    out["resilience_given_det_win"] = {k: {"n": len(v), "p_still_det": round(sum(v) / len(v), 4)} for k, v in res.items()}
    dead = defaultdict(Counter)
    for r in rows:
        for c, d in r.get("t4_dead", {}).items():
            dead[c]["held"] += 1
            dead[c]["dead"] += int(not d["live_in_det_line"])
    out["dead_card_t4"] = {c: {"held_at_end_t4": v["held"], "p_dead_even_with_unlimited_mana": round(v["dead"] / v["held"], 4)}
                           for c, v in dead.items()}
    return out


def phase_states(m, pool, dork, a_card, keys):
    V = package_variants(dork, a_card)
    res = load_work("states")
    for k in keys:
        rows = pool.map(state_job, [(V[k][0], BASE_SEED + i, k) for i in range(m)], chunksize=10)
        res[k] = aggregate_states(rows)
        print("states", k, res[k].get("t3_main"), flush=True)
        save_work("states", res)


# ---- tournament-derived and synthetic state generators ----------------------------------------------
# Each generator returns a Snapshot. Known cards come from the player's logs (data/player_tournaments);
# unknown hand cards are sampled from the variant's own library, so the result is "fraction of
# plausible states", never a claim about the historical game. Cards a variant does not contain are
# dropped from the template (e.g. Strix Serenade once cut).

def _mk(deck, rng, hand_known, n_unknown, bf_names, gy=(), timing="main", turn=5, cmd=None,
        tapped=(), sick=(), land_drop=False, lib_remove=(), extra_units=None):
    deck_set = set(deck)
    bf = []
    for n in bf_names:
        if n in dc.COMMANDERS or n in deck_set or n in ("Noble Hierarch",):
            bf.append(sv.Perm(n, sick=n in sick, tapped=n in tapped))
    used = {p.name for p in bf} | set(gy) | set(lib_remove)
    hand = [h for h in hand_known if h in deck_set and h not in used]
    used |= set(hand)
    lib = [c for c in deck if c not in used]
    rng.shuffle(lib)
    hand += lib[:n_unknown]
    lib = lib[n_unknown:]
    if cmd is None:
        cmd = set(dc.COMMANDERS) - {p.name for p in bf}
    units = None
    if extra_units:
        tmp = sv.Snapshot(hand, bf, lib, [g for g in gy if g in deck_set or g in dc.COMMANDERS], cmd, {},
                          land_drop, timing, turn)
        units = sv.board_units(tmp) + Counter(extra_units)
    return sv.Snapshot(hand, bf, lib, [g for g in gy if g in deck_set], cmd, {}, land_drop, timing, turn,
                       units_override=units)


LANDS4 = ["Underground Sea", "Tropical Island", "Tundra", "Bayou"]
SCENARIOS = {
    "S01_azms8_r1_mana_rich_low_cards": dict(
        source="AZMS #8 R1 (draw): big mana (Kinnan copy, Tithe, Mox Diamond), repeatedly low on cards",
        uncertainty="board reconstructed from narrative; Thrasios presence assumed; treasures modeled as 3 any-colour units",
        gen=lambda d, r: _mk(d, r, [], 1, ["Starting Town", "Ancient Tomb", "Tropical Island", "Bayou", "Scrubland",
                                            "Birds of Paradise", "Mox Diamond", "Smothering Tithe", "Kinnan, Bonder Prodigy",
                                            "Thrasios, Triton Hero"], extra_units={dc.ANY: 3})),
    "S02_azms8_r2_pod_engine_no_outlet": dict(
        source="AZMS #8 R2 (win): Pod + Effigy-as-Badgermole + Delney + Derevi + Tymna",
        uncertainty="lands approximated; two unknown cards in hand",
        gen=lambda d, r: _mk(d, r, [], 2, ["City of Traitors", "Underground Sea", "Bayou", "Savannah", "Tropical Island",
                                            "Birthing Pod", "Machine God's Effigy", "Badgermole Cub",
                                            "Delney, Streetwise Lookout", "Derevi, Empyrial Tactician", "Tymna the Weaver"],
                             turn=5)),
    "S03_geekery_r4_cradle_board_low_colour": dict(
        source="Geekery R4 (loss): Cradle + Badgermole + DRS + Mockingbird-as-Noble + Thrasios, Finale drawn",
        uncertainty="colourless/green-heavy land set assumed; Ranger-Captain already sacrificed",
        gen=lambda d, r: _mk(d, r, ["Finale of Devastation", "Orcish Bowmasters"], 1,
                             ["Gaea's Cradle", "Gemstone Caverns", "Sink into Stupor // Soporific Springs", "Ancient Tomb",
                              "Badgermole Cub", "Deathrite Shaman", "Noble Hierarch", "Mockingbird",
                              "Thrasios, Triton Hero"], gy=["Ranger-Captain of Eos"], turn=5)),
    "S04_natures_rhythm_countered": dict(
        source="Geekery R2/R4: Nature's Rhythm countered with Druid in play",
        uncertainty="post-counter remaining mana fixed at 2 untapped lands",
        gen=lambda d, r: _mk(d, r, [], 2, ["Tropical Island", "Savannah", "Bayou", "Command Tower", "Ancient Tomb",
                                            "Devoted Druid", "Thrasios, Triton Hero"], gy=["Nature's Rhythm"],
                             tapped=["Bayou", "Command Tower", "Ancient Tomb"], turn=4)),
    "S05_shields_down_after_stopping_a_win": dict(
        source="Geekery R1: opponent Oracle attempt stopped; our instant window on their turn",
        uncertainty="our untapped resources assumed (4 duals, Birds, Thrasios); 3 unknown cards",
        gen=lambda d, r: _mk(d, r, [], 3, LANDS4 + ["Birds of Paradise", "Thrasios, Triton Hero"], timing="instant")),
    "S06_shields_down_high_fae_active": dict(
        source="as S05 with High Fae Trickster on the battlefield",
        uncertainty="as S05",
        gen=lambda d, r: _mk(d, r, [], 3, LANDS4 + ["Birds of Paradise", "Thrasios, Triton Hero", "High Fae Trickster"],
                             timing="instant")),
    "S07_shields_down_teferi_active": dict(
        source="as S05 with Teferi, Mage of Zhalfir on the battlefield",
        uncertainty="as S05",
        gen=lambda d, r: _mk(d, r, [], 3, LANDS4 + ["Birds of Paradise", "Thrasios, Triton Hero",
                                                     "Teferi, Mage of Zhalfir"], timing="instant")),
    "S08_crop_rotation_for_emergence_zone": dict(
        source="Crop Rotation in hand, Emergence Zone in library, opponent's turn",
        uncertainty="4 duals + Sol Ring untapped; 2 unknown cards",
        gen=lambda d, r: _mk(d, r, ["Crop Rotation"], 2, LANDS4 + ["Sol Ring", "Thrasios, Triton Hero"],
                             timing="instant")),
    "S09_engine_partially_disrupted": dict(
        source="engine developed then board partially removed (Pod, Druid, Badgermole in graveyard)",
        uncertainty="generic reconstruction across logs",
        gen=lambda d, r: _mk(d, r, [], 3, LANDS4 + ["Command Tower", "Thrasios, Triton Hero", "Rhystic Study"],
                             gy=["Birthing Pod", "Devoted Druid", "Badgermole Cub"])),
    "S10_low_card_mulligan_state": dict(
        source="mulligan to five, turn 3",
        uncertainty="generic",
        gen=lambda d, r: _mk(d, r, [], 2, ["Tropical Island", "Scrubland", "Underground Sea", "Sol Ring"], turn=3)),
    "S11_empty_board_tutors_and_mana": dict(
        source="near-empty board, tutors + mana remain (Thrasios in command zone)",
        uncertainty="generic",
        gen=lambda d, r: _mk(d, r, ["Demonic Tutor", "Vampiric Tutor"], 1, LANDS4 + ["Sol Ring"], turn=4)),
    "S12_geekery_r2_druid_plus_enlightened": dict(
        source="Geekery R2 (win): Druid line found via Enlightened Tutor after a countered Rhythm",
        uncertainty="lands approximated; Thrasios assumed on battlefield",
        gen=lambda d, r: _mk(d, r, ["Enlightened Tutor"], 1, ["Scrubland", "Savannah", "Gemstone Caverns", "Boseiju, Who Endures",
                                                               "Tropical Island", "Devoted Druid", "Tymna the Weaver",
                                                               "Thrasios, Triton Hero", "Deathrite Shaman"],
                             gy=["Nature's Rhythm", "Lotus Petal"])),
    "S13_geekery_r3_oculus_threatened": dict(
        source="Geekery R3 (draw): T2-3 Oculus engine, Kinnan's Gilded Drake about to take it",
        uncertainty="hand = registered cards from photo (Mindbreak, Swan Song) + 1 unknown; Borne removed (not registered)",
        gen=lambda d, r: _mk(d, r, ["Mindbreak Trap", "Swan Song"], 1, ["Gemstone Caverns", "Tropical Island", "Chrome Mox",
                                                                         "Abhorrent Oculus", "Lotho, Corrupt Shirriff"],
                             turn=3, timing="instant", sick=["Abhorrent Oculus"])),
}


def _synthetic(kind, deck, rng, timing_enabler, timing):
    lands = [c for c in deck if dc.is_land(c) and c not in dc.FETCH_TARGETS]
    creatures = [c for c in deck if not dc.is_land(c) and dc.is_creature(c)]
    nonland = [c for c in deck if not dc.is_land(c)]
    rng.shuffle(lands), rng.shuffle(creatures), rng.shuffle(nonland)
    extra = ["High Fae Trickster"] if timing_enabler else []
    if kind == "post_fight":
        bf = lands[:5] + creatures[:2] + ["Thrasios, Triton Hero", "Tymna the Weaver"] + extra
        nhand = 3
    elif kind == "low_hand_high_mana":
        rocks = [c for c in ("Sol Ring", "Mana Vault", "Arcane Signet") if c in deck][:1]
        bf = lands[:6] + rocks + ["Thrasios, Triton Hero"] + extra
        nhand = 1
    elif kind == "high_board_low_colour":
        cl = [c for c in ("Gaea's Cradle", "Ancient Tomb", "City of Traitors", "Boseiju, Who Endures") if c in deck]
        bf = cl + [c for c in creatures if c not in dc.MANA_PERMS][:4] + ["Thrasios, Triton Hero"] + extra
        nhand = 3
    else:
        raise ValueError(kind)
    bf = [c for c in dict.fromkeys(bf)]
    return _mk(deck, rng, [], nhand, bf, timing=timing, turn=6)


def scenario_job(args):
    import random
    deck, name, seed = args
    rng = random.Random(seed)
    if name in SCENARIOS:
        s = SCENARIOS[name]["gen"](deck, rng)
    else:
        kind, te, timing = name.split("|")
        s = _synthetic(kind, deck, rng, te == "enabler", timing)
    c = csa_relevant(s, set(deck))
    r = sv.solve(s, want=("all",))
    return {"det": r["det"], "protected": r["protected"], "families": sorted(r["families"]),
            "win_draws": c["win_draws"], "library": c["library"], "protected_draws": c["protected_draws"],
            "nondet": r["nondet"]}


SYNTH = [f"{k}|{te}|{tm}" for k in ("post_fight", "low_hand_high_mana", "high_board_low_colour")
         for te in ("none", "enabler") for tm in ("main", "instant")]


def phase_scenarios(m, pool, dork, a_card, keys):
    V = package_variants(dork, a_card)
    out = load_work("scenarios")
    for k in keys:
        deck = V[k][0]
        out[k] = {}
        for name in list(SCENARIOS) + SYNTH:
            rows = pool.map(scenario_job, [(deck, name, BASE_SEED + i) for i in range(m)], chunksize=20)
            n = len(rows)
            fam = Counter(f for r in rows for f in r["families"])
            alive = [r for r in rows if not r["det"]]
            out[k][name] = {
                "n": n, "p_det_now": round(sum(r["det"] for r in rows) / n, 4),
                "p_det_now_ci95": wilson(sum(r["det"] for r in rows), n),
                "p_protected_now": round(sum(r["protected"] for r in rows) / n, 4),
                "p_nondet_or_det_now": round(sum(r["nondet"] for r in rows) / n, 4),
                "family_counts": dict(fam),
                "csa_mean_win_draws_if_not_winning": round(sum(r["win_draws"] for r in alive) / len(alive), 3) if alive else None,
                "p_next_draw_wins_if_not_winning": round(sum(r["win_draws"] / max(1, r["library"]) for r in alive) / len(alive), 4) if alive else None,
            }
            print("scen", k, name, out[k][name]["p_det_now"], out[k][name]["csa_mean_win_draws_if_not_winning"], flush=True)
        save_work("scenarios", out)


# ---- cut enumeration + Pareto frontier -------------------------------------------------------------------

GOLDFISH_AXES = ["det_win_by_t4", "det_protected_by_t4", "det_instant_window_by_t4", "premium_engine_by_t3",
                 "keep7"]
SECONDARY_KILL = {"Faerie Mastermind", "Orcish Bowmasters", "Clever Impersonator", "Oboro Breezecaller",
                  "Gleaming Splendor"}


def role_losses(cuts):
    return {
        "interaction_lost": sum(c in dc.INTERACTION for c in cuts),
        "free_counters_lost": sum(c in dc.FREE_COUNTERS for c in cuts),
        "card_advantage_lost": sum(c in dc.CARD_ADVANTAGE for c in cuts),
        "creatures_lost": sum(dc.is_creature(c) and not dc.is_land(c) for c in cuts),
        "blue_pitch_fuel_lost": sum(dc.is_blue(c) for c in cuts),
        "secondary_kill_redundancy_lost": sum(c in SECONDARY_KILL for c in cuts),
        "premium_engines_lost": sum(c in dc.PREMIUM_ENGINES for c in cuts),
    }


def dominates(a, b, keys):
    return all(a[k] <= b[k] for k in keys) and any(a[k] < b[k] for k in keys)


def phase_pareto():
    marg = load_work("marginals")["oracle_context_D"]
    rows = []
    for c, m in marg.items():
        if c.startswith("_"):
            continue
        row = {"card": c, "context": "oracle_D_superdeck"}
        for k in GOLDFISH_AXES:
            row[f"contribution_{k}"] = -m[k]["delta_vs_ref"]  # value lost if cut
            row[f"contribution_{k}_se"] = m[k]["delta_se"]
        row.update(role_losses([c]))
        row["protected_card"] = c in PROTECTED
        rows.append(row)
    less = load_work("marginals").get("oracle_less_context", {})
    for c, m in less.items():
        if c.startswith("_"):
            continue
        row = {"card": c, "context": "oracle_less_superdeck"}
        for k in GOLDFISH_AXES:
            row[f"contribution_{k}"] = -m[k]["delta_vs_ref"]
            row[f"contribution_{k}_se"] = m[k]["delta_se"]
        row.update(role_losses([c]))
        row["protected_card"] = c in PROTECTED
        rows.append(row)
    with (OUT / "deckbuild008_cut_ablation.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()})
    contrib = {r["card"]: r for r in rows if r["context"] == "oracle_D_superdeck"}
    frontier_rows = []
    objective_keys = [f"loss_{k}" for k in GOLDFISH_AXES] + list(role_losses([]).keys())
    for p, label in ((2, "B_minimal"), (3, "C_core3"), (4, "D_core3_spellseeker")):
        for pool_name, pool_cards in (("default", CUT_POOL), ("stress_with_imperial_seal", CUT_POOL + STRESS_POOL)):
            cands = []
            for extra in itertools.combinations(pool_cards, p - 1):
                if pool_name.startswith("stress") and "Imperial Seal" not in extra:
                    continue
                cuts = (STRIX,) + extra
                row = {"package": label, "pool": pool_name, "cuts": " | ".join(cuts)}
                for k in GOLDFISH_AXES:
                    row[f"loss_{k}"] = round(sum(contrib[c][f"contribution_{k}"] for c in cuts if c in contrib), 5)
                    row[f"loss_{k}_se"] = round(math.sqrt(sum(contrib[c][f"contribution_{k}_se"] ** 2 for c in cuts
                                                              if c in contrib)), 5)
                row.update(role_losses(cuts))
                cands.append(row)
            front = [r for r in cands if not any(dominates(o, r, objective_keys) for o in cands if o is not r)]
            for r in front:
                r["frontier_size"] = len(front)
                r["candidates_enumerated"] = len(cands)
                frontier_rows.append(r)
    with (OUT / "deckbuild008_pareto_frontier.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(frontier_rows[0].keys()))
        w.writeheader()
        for r in frontier_rows:
            w.writerow(r)
    print("pareto rows", len(frontier_rows))


# ---- assembly ----------------------------------------------------------------------------------------------

def provenance(n_note):
    names, h = baseline()
    return {
        "task": "SIM-DECKBUILD-008",
        "run_class": "DECK_BACKED_GOLDFISH (Monte Carlo) + STATIC_ANALYSIS",
        "subject_deck_version": "tymna-thrasios-creature-factory-deckbuild008-v1",
        "subject_deck_hash": h,
        "oracle_data_version": "scryfall-live-2026-10-30",
        "base_seed": BASE_SEED, "seed_rule": "game i uses seed BASE_SEED + i for every variant (paired CRN)",
        "seat_rule": "on the play iff seed % 4 == 0 (one seat in four)",
        "max_turn": MAX_TURN, "trials": n_note,
        "not_a_win_rate": "All probabilities are availability of a deterministic line if no opponent interacts.",
    }


def phase_assemble(dork, a_card):
    V = package_variants(dork, a_card)
    vm = {"provenance": provenance("see per-section n"), "chosen": {"dork": dork, "strix_slot_oracle_less": a_card},
          "dork_audit": load_work("dork"), "strix_slot_screen": load_work("strix"),
          "packages": load_work("packages_pilot"), "packages_policy_sensitivity": load_work("packages_loose_strict"),
          "sensitivity": load_work("sensitivity"), "verified_builds": load_work("verify"),
          "variant_decklists": {k: {"description": d, "adds": sorted(set(deck) - set(baseline()[0])),
                                    "cuts": sorted(set(baseline()[0]) - set(deck))} for k, (deck, d) in V.items()},
          "marginals": load_work("marginals")}
    (OUT / "deckbuild008_variant_metrics.json").write_text(json.dumps(vm, indent=1, default=list) + "\n")
    st = load_work("states")
    sc = load_work("scenarios")
    csa_out = {"provenance": provenance("states: per-variant goldfish games with snapshots; synthetic: per-cell samples"),
               "definition": {
                   "win_draws": "library cards that, added to hand now, give a deterministic win this window",
                   "piece_draws": "winning draws that are not tutors (the card is used as a line piece/mana/enabler)",
                   "tutor_draws": "winning draws that are tutors (tutor-equivalent outs)",
                   "protected_draws": "winning draws whose line can be shielded or counter-backed",
                   "nondet_draws": "draws that only enable a nondeterministic finish (Finale X>=10 combat)",
                   "instant windows": "timing=instant: opponents' turns, untapped resources only, flash enablers required",
                   "already_winning": "state has a deterministic line before drawing (CSA counted only for non-winning states)"},
               "goldfish_states": st,
               "synthetic_states": {k: {n: v for n, v in sc.get(k, {}).items() if "|" in n} for k in sc}}
    (OUT / "deckbuild008_conversion_surface.json").write_text(json.dumps(csa_out, indent=1, default=list) + "\n")
    ts = {"provenance": provenance("per scenario: n samples of unknown cards"),
          "caveat": "Scenario states are reconstructed from player logs with unknown cards sampled from the variant's "
                    "library. They estimate the fraction of plausible states with a deterministic line; they do NOT "
                    "claim any historical game would have been won.",
          "scenarios": {n: {"source": d["source"], "uncertainty": d["uncertainty"]} for n, d in SCENARIOS.items()},
          "results": {k: {n: v for n, v in sc.get(k, {}).items() if "|" not in n} for k in sc}}
    (OUT / "deckbuild008_tournament_scenarios.json").write_text(json.dumps(ts, indent=1, default=list) + "\n")
    print("assembled")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--dork", default=None)
    ap.add_argument("--a-card", default=None)
    ap.add_argument("--sets", default=None)
    ap.add_argument("--keys", default="BASELINE_v8,A_oracle_less,B_oracle_consult,C_oracle_core3,D_core3_spellseeker")
    a = ap.parse_args()
    dork = a.dork or best_dork()
    a_card = a.a_card or load_work("strix").get("_chosen", SEEKER)
    t0 = time.time()
    with Pool(a.procs) as pool:
        if a.phase == "dork":
            phase_dork(a.n, pool)
        elif a.phase == "strix":
            phase_strix(a.n, pool, dork)
        elif a.phase == "packages":
            phase_packages(a.n, pool, dork, a_card)
        elif a.phase == "packages_policy":
            phase_packages(a.n, pool, dork, a_card, policies=("loose", "strict"))
        elif a.phase == "sensitivity":
            phase_sensitivity(a.n, pool, dork, a_card)
        elif a.phase == "marginals":
            phase_marginals(a.n, pool, dork)
        elif a.phase == "scenarios":
            phase_scenarios(a.n, pool, dork, a_card, a.keys.split(","))
        elif a.phase == "pareto":
            phase_pareto()
        elif a.phase == "verify":
            sets = json.loads(Path(a.sets).read_text())
            phase_verify(a.n, pool, dork, [(x["label"], x["adds"], x["cuts"]) for x in sets], a_card)
        elif a.phase == "assemble":
            phase_assemble(dork, a_card)
        elif a.phase == "graph":
            phase_graph(dork, a_card)
        elif a.phase == "states":
            phase_states(a.n, pool, dork, a_card, a.keys.split(","))
        else:
            raise SystemExit(f"unknown phase {a.phase}")
    print(f"phase {a.phase} done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
