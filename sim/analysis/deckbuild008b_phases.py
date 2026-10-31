"""SIM-DECKBUILD-008b phases other than `variants` (see build_deckbuild008b_experiments.py)."""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import random
from collections import Counter, defaultdict

import build_deckbuild008_experiments as ex
import build_deckbuild008b_experiments as bx
import deckbuild008_cards as dc
import deckbuild008_solver as sv
import deckbuild008b_analysis as an
from deckbuild008_goldfish import Game, pay_take

ORACLE, CONSULT, PACT, SEEKER = an.ORACLE, an.CONSULT, an.PACT, an.SEEKER

# ---- ablations: spent Pact / exiled Oracle / axis disabled -------------------------------------------
# (parent config, cards replaced by an uncastable blank, cards forced into the opening seven)
ABLATIONS = {
    "B_pact_spent": ("B_oracle_pact_seeker", [PACT], []),
    "B_pact_spent_oracle_exiled": ("B_oracle_pact_seeker", [PACT, ORACLE], []),
    "B_lose_oracle": ("B_oracle_pact_seeker", [ORACLE], []),
    "B_lose_spellseeker": ("B_oracle_pact_seeker", [SEEKER], []),
    "B_druid_axis_off": ("B_oracle_pact_seeker", [an.DRUID], []),
    "B_oboro_axis_off": ("B_oracle_pact_seeker", [an.OBORO], []),
    "B_bowmasters_axis_off": ("B_oracle_pact_seeker", [an.BOWMASTERS], []),
    "A_druid_axis_off": ("A_oracle_less", [an.DRUID], []),
    "A_oboro_axis_off": ("A_oracle_less", [an.OBORO], []),
    "A_bowmasters_axis_off": ("A_oracle_less", [an.BOWMASTERS], []),
    "C_consult_spent": ("C_oracle_consult_seeker", [CONSULT], []),
    "C_druid_axis_off": ("C_oracle_consult_seeker", [an.DRUID], []),
    "E_druid_axis_off": ("E_all_four", [an.DRUID], []),
}
# conditional designs: the named card forced into the opening seven, parent forced the same way
FORCED = {
    "B_forced_oracle": ("B_oracle_pact_seeker", [], [ORACLE]),
    "B_forced_oracle_pact_spent": ("B_oracle_pact_seeker", [PACT], [ORACLE]),
    "C_forced_oracle": ("C_oracle_consult_seeker", [], [ORACLE]),
    "C_forced_oracle_consult_spent": ("C_oracle_consult_seeker", [CONSULT], [ORACLE]),
    "B_forced_pact": ("B_oracle_pact_seeker", [], [PACT]),
    "C_forced_consult": ("C_oracle_consult_seeker", [], [CONSULT]),
    "B_forced_spellseeker": ("B_oracle_pact_seeker", [], [SEEKER]),
    "C_forced_spellseeker": ("C_oracle_consult_seeker", [], [SEEKER]),
    "A_forced_spellseeker": ("A_oracle_less", [], [SEEKER]),
}


def blanked(deck, cards):
    out = list(deck)
    for c in cards:
        out[out.index(c)] = dc.BLANK
    return out


def phase_ablations(a):
    seed0 = bx.BASE_SEED_B + 5_000_000
    res = {"_design": {"n": a.n, "seed0": seed0, "note": "each ablation is paired with its parent on identical seeds; "
                       "blank = uncastable placeholder (the card is gone: spent, exiled or answered)"}}
    with mp.Pool(a.procs) as pool:
        parents = {}
        for name, (parent, blanks, force) in list(ABLATIONS.items()) + list(FORCED.items()):
            pkey = (parent, tuple(force))
            if pkey not in parents:
                parents[pkey] = bx.run_cfg(bx.build(parent), a.n, seed0, pool, kw={"force_opening": force})
                res[f"_parent::{parent}::forced={'+'.join(force) or 'none'}"] = bx.summarize(parents[pkey])
            ref = parents[pkey]
            g = bx.run_cfg(blanked(bx.build(parent), blanks), a.n, seed0, pool, kw={"force_opening": force}) \
                if blanks else ref
            res[name] = {"parent": parent, "blanked": blanks, "forced_opening": force, **bx.summarize(g, ref)}
            print("abl", name, res[name]["det_win_by_t4"], flush=True)
            bx.save("ablations", res)
    return res


# ---- per-state audit: Spellseeker + fair Tainted Pact + CSA + resilience ----------------------------------

SEEKER_HQ = {"tutor": {"Tainted Pact", "Demonic Consultation", "Demonic Tutor", "Vampiric Tutor", "Enlightened Tutor",
                       "Imperial Seal", "Finale of Devastation", "Nature's Rhythm", "Neoform", "Crop Rotation",
                       "Mystical Tutor", "Worldly Tutor"},
             "protection": {"Silence", "Orim's Chant", "Veil of Summer", "Autumn's Veil"},
             "interaction": {"Swan Song", "Flusterstorm", "Mental Misstep", "Pact of Negation", "Strix Serenade",
                             "Dispel"}}
STOP_WIN = (an.CATEGORIES["free_counter"] | {"Swan Song", "Flusterstorm", "Mental Misstep", "Strix Serenade"})
PROTECT = {"Silence", "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos"}
ENGINE = {"Birthing Pod", "Survival of the Fittest", "Rhystic Study", "Mystic Remora", "Smothering Tithe",
          "Kinnan, Bonder Prodigy", "Abhorrent Oculus"}
MANA = {"Sol Ring", "Mana Vault", "Chrome Mox", "Mox Diamond", "Lotus Petal", "Ancient Tomb", "City of Traitors",
        "Birds of Paradise", "Noble Hierarch", "Delighted Halfling", "Avacyn's Pilgrim", "Gaea's Cradle"}


def _clone(s, **kw):
    return ex._clone(s, **kw)


def _paid(units, name):
    g, pips = dc.cost_of(name)
    return pay_take(units, pips, g)


def seeker_audit(s):
    units = an.units_of(s)
    lib = set(s.library)
    targets = sorted(c for c in lib if dc.tutor_can_find(SEEKER, c))
    cats = {k: sorted(v & lib) for k, v in SEEKER_HQ.items()}
    left = _paid(units, SEEKER)
    out = {"castable": left is not None, "n_targets": len(targets),
           "has_hq_target": any(cats.values()), "has_protection_target": bool(cats["protection"]),
           "has_interaction_target": bool(cats["interaction"]), "has_tutor_target": bool(cats["tutor"]),
           "pact_target": PACT in lib, "immediate_win": False, "next_turn_win": False}
    hand = [h for h in s.hand if h != SEEKER]
    for t in targets:
        if left is not None and not out["immediate_win"]:
            s2 = _clone(s, hand=hand + [t], library=[c for c in s.library if c != t],
                        bf=s.bf + [sv.Perm(SEEKER, sick=True)], units_override=left, land_drop=s.land_drop)
            # units_override replaces the board pool, so the land drop is still added by the solver
            if sv.solve(s2, want=("det",))["det"]:
                out["immediate_win"] = True
        if not out["next_turn_win"]:
            s3 = _clone(s, hand=hand + [t], library=[c for c in s.library if c != t],
                        bf=s.bf + [sv.Perm(SEEKER)], units_override=None, land_drop=True)
            if sv.solve(s3, want=("det",))["det"]:
                out["next_turn_win"] = True
        if out["immediate_win"] and out["next_turn_win"]:
            break
    return out


def _castable_now(card, hand, bf, units):
    bfn = {p.name for p in bf}
    return an.castable(units, card, x=1) or an.free_castable(card, hand, bfn, bf, units)


def pact_audit(s, deck_set, do_residual):
    """Fair Tainted Pact from this state, walking the REAL library order (the goldfish library is the
    actual future order), for each acceptable-hit class."""
    units = an.units_of(s)
    left = _paid(units, PACT)
    if left is None:
        return {"castable": False}
    hand = [h for h in s.hand if h != PACT]
    lib = list(s.library)
    classes = {}
    if s.timing == "instant":
        classes["stop_opponent_win"] = {c for c in STOP_WIN if c in deck_set and _castable_now(c, hand, s.bf, left)}
    else:
        classes["protect_our_win"] = {c for c in PROTECT | STOP_WIN
                                      if c in deck_set and _castable_now(c, hand, s.bf, left)}
        classes["find_engine"] = ENGINE & deck_set
        classes["find_mana"] = MANA & deck_set
        conv = set()
        for c in set(lib):
            s2 = _clone(s, hand=hand + [c], library=[x for x in lib if x != c], gy=s.gy + [PACT], units_override=left)
            if sv.solve(s2, want=("det",))["det"]:
                conv.add(c)
        classes["find_conversion_now"] = conv
    out = {"castable": True, "timing": s.timing, "library": len(lib), "classes": {}}
    for name, acc in classes.items():
        k = len(acc & set(lib))
        exiled, hit = an.pact_walk(lib, acc)
        row = {"k_acceptable": k, "hit": hit is not None, "n_exiled": len(exiled),
               "oracle_exiled": ORACLE in exiled,
               "closed_form": an.pact_closed_form(len(lib), k),
               "critical_exiled": {ax: len(set(exiled) & cards) for ax, cards in an.CRITICAL.items()}}
        if name == "find_conversion_now" and hit is not None:
            s2 = _clone(s, hand=hand + [hit], library=[x for x in lib if x != hit and x not in exiled],
                        gy=s.gy + [PACT], units_override=left)
            row["converts_after_exile"] = sv.solve(s2, want=("det",))["det"]
        out["classes"][name] = row
    if do_residual and s.timing == "main":
        # next-turn conversion surface: Pact still live vs spent (no exile) vs spent fairly for an engine
        nxt = dict(units_override=None, land_drop=True)
        live = _clone(s, **nxt)
        spent = _clone(s, hand=hand, gy=s.gy + [PACT], **nxt)
        exiled, hit = an.pact_walk(lib, classes["find_engine"])
        fair = _clone(s, hand=hand + ([hit] if hit else []),
                      library=[x for x in lib if x != hit and x not in exiled], gy=s.gy + [PACT], **nxt)
        res = {}
        for lab, st in (("pact_live", live), ("pact_spent_no_exile", spent), ("pact_spent_fair_engine", fair)):
            c = ex.csa_relevant(st, deck_set)
            res[lab] = {"already_winning": c["already_winning"], "win_draws": c["win_draws"],
                        "library": c["library"]}
        res["oracle_exiled_by_engine_search"] = ORACLE in exiled
        out["residual_next_turn"] = res
    return out


def extra_disruptions(s):
    out = {}
    def drop(names):
        return _clone(s, hand=[h for h in s.hand if h not in names], bf=[p for p in s.bf if p.name not in names],
                      library=[c for c in s.library if c not in names], units_override=None)
    out["lose_oracle"] = drop({ORACLE})
    out["pact_spent"] = _clone(drop({PACT}), gy=s.gy + ([PACT] if PACT in set(s.hand) | set(s.library) else []))
    out["pact_spent_oracle_exiled"] = drop({PACT, ORACLE})
    out["druid_axis_disabled"] = drop({an.DRUID})
    out["oboro_axis_disabled"] = drop({an.OBORO})
    out["bowmasters_axis_disabled"] = drop({an.BOWMASTERS})
    return out


def state_job_b(args):
    deck, seed, key, legacy = args
    bx.set_rules(legacy)
    g = Game(deck, seed=seed, on_play=(seed % 4 == 0), max_turn=bx.MAX_TURN, record_snapshots=True)
    g.play()
    deck_set = set(deck)
    res = {"seed": seed}
    for t in (2, 3, 4):
        for timing in ("main", "instant"):
            s = g.snapshots.get((t, timing))
            if s is None:
                continue
            k = f"t{t}_{timing}"
            if (t, timing) != (2, "instant"):
                c = ex.csa_relevant(s, deck_set)
                c.pop("cards")
                res[k] = c
            if timing == "main" and t in (3, 4):
                res[k + "_tutors"] = ex.tutor_leverage(s)
                base = sv.solve(s, want=("all",))
                if base["det"]:
                    dis = {n: sv.solve(s2, want=("det",))["det"] for n, s2 in ex.disruptions(s).items()}
                    dis.update({n: sv.solve(s2, want=("det",))["det"] for n, s2 in extra_disruptions(s).items()})
                    dis["single_piece_loss_survival"] = ex.single_piece_loss(s, base["used_cards"])
                    res[k + "_resilience"] = dis
            if SEEKER in s.hand and timing == "main":
                res[k + "_seeker"] = seeker_audit(s)
            if PACT in s.hand:
                res[k + "_pact"] = pact_audit(s, deck_set, do_residual=(t in (3, 4)))
    return res


def _mean(xs):
    xs = [float(x) for x in xs]
    return round(sum(xs) / len(xs), 4) if xs else None


def aggregate_b(rows):
    out = {}
    for k in ("t2_main", "t3_main", "t3_instant", "t4_main", "t4_instant"):
        vals = [r[k] for r in rows if k in r]
        alive = [v for v in vals if not v["already_winning"]]
        out[k] = {"n_states": len(vals), "p_already_winning": _mean(v["already_winning"] for v in vals),
                  "p_already_protected": _mean(v["already_protected"] for v in vals),
                  "csa_win_draws_mean": _mean(v["win_draws"] for v in alive),
                  "csa_protected_draws_mean": _mean(v["protected_draws"] for v in alive),
                  "csa_nondet_draws_mean": _mean(v["nondet_draws"] for v in alive),
                  "p_any_winning_draw_exists": _mean(v["win_draws"] > 0 for v in alive),
                  "p_next_draw_wins": _mean(v["win_draws"] / max(1, v["library"]) for v in alive)}
    tut = defaultdict(Counter)
    for r in rows:
        for k in ("t3_main_tutors", "t4_main_tutors"):
            for t, d in r.get(k, {}).items():
                tut[t]["n"] += 1
                for kk, v in d.items():
                    tut[t][kk] += int(bool(v))
    out["tutor_leverage_t3_t4"] = {t: {"n_states_held": c["n"], **{kk: round(c[kk] / c["n"], 4) for kk in c if kk != "n"}}
                                   for t, c in sorted(tut.items())}
    res = defaultdict(list)
    for r in rows:
        for k in ("t3_main_resilience", "t4_main_resilience"):
            for kk, v in r.get(k, {}).items():
                if v is not None:
                    res[kk].append(float(v))
    out["resilience_given_det_win"] = {kk: {"n": len(v), "p_still_det": round(sum(v) / len(v), 4),
                                            "ci95": ex.wilson(int(round(sum(v))), len(v))}
                                       for kk, v in res.items()}
    sk = [r[k] for r in rows for k in ("t2_main_seeker", "t3_main_seeker", "t4_main_seeker") if k in r]
    if sk:
        out["spellseeker_audit"] = {"n_states": len(sk), **{f: _mean(x[f] for x in sk) for f in
                                    ("castable", "has_hq_target", "has_tutor_target", "has_protection_target",
                                     "has_interaction_target", "pact_target", "immediate_win", "next_turn_win")},
                                    "stranded_not_castable": _mean(not x["castable"] for x in sk),
                                    "mean_targets": _mean(x["n_targets"] for x in sk)}
    pk = [r[k] for r in rows for k in r if k.endswith("_pact")]
    if pk:
        cast = [p for p in pk if p["castable"]]
        agg = {"n_states_pact_in_hand": len(pk), "p_castable": _mean(p["castable"] for p in pk), "classes": {}}
        names = sorted({c for p in cast for c in p["classes"]})
        for c in names:
            rs = [p["classes"][c] for p in cast if c in p["classes"]]
            hits = [x for x in rs if x["hit"]]
            row = {"n_states": len(rs), "p_any_acceptable": _mean(x["k_acceptable"] > 0 for x in rs),
                   "mean_k_acceptable": _mean(x["k_acceptable"] for x in rs),
                   "p_hit": _mean(x["hit"] for x in rs),
                   "mean_exiled_given_hit": _mean(x["n_exiled"] for x in hits),
                   "closed_form_mean_exiled": _mean(x["closed_form"]["expected_exiled"] for x in rs if x["k_acceptable"]),
                   "p_oracle_exiled": _mean(x["oracle_exiled"] for x in rs),
                   "p_hit_without_exiling_oracle": _mean(x["hit"] and not x["oracle_exiled"] for x in rs),
                   "p_any_critical_exiled": {ax: _mean(x["critical_exiled"][ax] > 0 for x in rs) for ax in an.CRITICAL},
                   "mean_critical_exiled": {ax: _mean(x["critical_exiled"][ax] for x in rs) for ax in an.CRITICAL}}
            if c == "find_conversion_now":
                row["p_converts_after_exile"] = _mean(x.get("converts_after_exile", False) for x in rs)
            agg["classes"][c] = row
        resid = [p["residual_next_turn"] for p in cast if "residual_next_turn" in p]
        if resid:
            agg["residual_next_turn"] = {
                "n_states": len(resid),
                **{lab: {"p_already_winning": _mean(x[lab]["already_winning"] for x in resid),
                         "mean_win_draws": _mean(x[lab]["win_draws"] for x in resid)}
                   for lab in ("pact_live", "pact_spent_no_exile", "pact_spent_fair_engine")},
                "p_oracle_exiled_by_engine_search": _mean(x["oracle_exiled_by_engine_search"] for x in resid)}
        out["fair_pact_audit"] = agg
    return out


STATE_KEYS = ["A_oracle_less", "B_oracle_pact_seeker", "C_oracle_consult_seeker", "D_oracle_consult_pact",
              "E_all_four", "F_oracle_pact"]


def phase_audit(a, keys):
    keys = keys if keys and keys != bx.HEADLINE else STATE_KEYS
    seed0 = bx.BASE_SEED_B + 7_000_000
    out = {"_design": {"n_games": a.n, "seed0": seed0}}
    try:
        out.update(bx.load(f"audit_{a.tag}"))
    except FileNotFoundError:
        pass
    with mp.Pool(a.procs) as pool:
        for k in keys:
            rows = pool.map(state_job_b, [(bx.build(k), seed0 + i, k, k in bx.LEGACY) for i in range(a.n)], chunksize=4)
            out[k] = aggregate_b(rows)
            print("audit", k, out[k]["t4_main"], flush=True)
            bx.save(f"audit_{a.tag}", out)
    return out


# ---- scenarios (008 generators, larger n) -----------------------------------------------------------

def _scen(args):
    deck, name, seed, legacy = args
    bx.set_rules(legacy)
    return ex.scenario_job((deck, name, seed))


SCEN_DECKS = {"A_oracle_less": None, "B_oracle_pact_seeker": None, "C_oracle_consult_seeker": None,
              "E_all_four": None, "B_pact_spent": ("B_oracle_pact_seeker", [PACT]),
              "B_pact_spent_oracle_exiled": ("B_oracle_pact_seeker", [PACT, ORACLE])}


def phase_scenarios(a, keys):
    keys = keys if keys and keys != bx.HEADLINE else list(SCEN_DECKS)
    seed0 = bx.BASE_SEED_B + 8_000_000
    out = {"_design": {"n": a.n, "seed0": seed0, "caveat": "states reconstructed from logs / synthetic classes; "
                       "unknown cards sampled from each deck; NOT claims about historical games"}}
    try:
        out.update(bx.load(f"scenarios_{a.tag}"))
    except FileNotFoundError:
        pass
    names = list(ex.SCENARIOS) + ex.SYNTH
    with mp.Pool(a.procs) as pool:
        for k in keys:
            spec = SCEN_DECKS.get(k)
            deck = bx.build(k) if spec is None else blanked(bx.build(spec[0]), spec[1])
            out[k] = {}
            for name in names:
                rows = pool.map(_scen, [(deck, name, seed0 + i, False) for i in range(a.n)], chunksize=10)
                n = len(rows)
                alive = [r for r in rows if not r["det"]]
                det = sum(r["det"] for r in rows)
                out[k][name] = {
                    "n": n, "p_det_now": round(det / n, 4), "p_det_now_ci95": ex.wilson(det, n),
                    "p_protected_now": round(sum(r["protected"] for r in rows) / n, 4),
                    "p_nondet_or_det_now": round(sum(r["nondet"] for r in rows) / n, 4),
                    "family_counts": dict(Counter(f for r in rows for f in r["families"])),
                    "csa_mean_win_draws_if_not_winning": round(sum(r["win_draws"] for r in alive) / len(alive), 3) if alive else None,
                    "csa_se": round(math.sqrt(sum((r["win_draws"] - sum(x["win_draws"] for x in alive) / len(alive)) ** 2
                                                  for r in alive) / max(1, len(alive) - 1)) / math.sqrt(len(alive)), 3) if len(alive) > 1 else None,
                    "p_next_draw_wins_if_not_winning": round(sum(r["win_draws"] / max(1, r["library"]) for r in alive) / len(alive), 4) if alive else None,
                }
                print("scen", k, name, out[k][name]["p_det_now"], out[k][name]["csa_mean_win_draws_if_not_winning"], flush=True)
            bx.save(f"scenarios_{a.tag}", out)
    return out


def run_phase(phase, a, keys):
    if phase == "ablations":
        return phase_ablations(a)
    if phase == "audit":
        return phase_audit(a, keys)
    if phase == "scenarios":
        return phase_scenarios(a, keys)
    if phase == "assemble":
        import deckbuild008b_assemble as asm
        return asm.assemble()
    raise SystemExit(f"unknown phase {phase}")
