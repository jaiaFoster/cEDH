"""SIM-DECKBUILD-008b — does Oracle + Tainted Pact + Spellseeker (no Demonic Consultation) make the
better whole deck?

Focused follow-up to results/solo_baseline/deckbuild008_oracle_package_audit.md. Reuses the 008 goldfish,
solver, card registry, frozen baseline, metric definitions, state jobs and scenario jobs. New here:
* Tainted Pact modeled as a fair instant tutor, and Colossal Skyturtle channel regrowth (solver flags,
  switched on for every 008b configuration unless a config is explicitly marked "legacy_model");
* the Brick Burden / standalone-quality metric family, interaction-category access, non-Oracle and
  Oracle-specific deterministic wins, all recorded from the same paired games;
* replicates: replicate r uses seeds BASE_SEED_B + r * 1_000_000 + i (paired across configs).

Phases (each writes results/solo_baseline/deckbuild008b_work/<phase>.json):
  variants   exact 98-card configurations x replicates (headline Monte Carlo + brick + access)
  ablations  spent-Pact / exiled-Oracle / axis-disabled single-card blanks
  audit      per-state Spellseeker audit and fair Tainted Pact search audit (real library order)
  states     008 state_job (CSA, tutor leverage, resilience) on the 008b configurations
  scenarios  008 tournament + synthetic scenario cells on the 008b configurations
  assemble   final artifacts
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

import build_deckbuild008_experiments as ex  # noqa: E402
import deckbuild008_cards as dc  # noqa: E402
import deckbuild008_solver as sv  # noqa: E402
import deckbuild008b_analysis as an  # noqa: E402
from deckbuild008_goldfish import Game, hand_features  # noqa: E402

OUT = REPO_ROOT / "results" / "solo_baseline"
WORK = OUT / "deckbuild008b_work"
BASE_SEED_B = 9_000_000
MAX_TURN = ex.MAX_TURN
DORK = "Avacyn's Pilgrim"
ORACLE, CONSULT, PACT, SEEKER = an.ORACLE, an.CONSULT, an.PACT, an.SEEKER
STRIX, STORM, SKY = "Strix Serenade", "Volatile Stormdrake", "Colossal Skyturtle"
QUEEN, GLEAM = "The Queen of Dale", "Gleaming Splendor"

# (adds, cuts) relative to v8 with Deathrite -> Avacyn's Pilgrim.  Slot-preserving.
CONFIGS = {
    "A_oracle_less": ([SEEKER], [STRIX]),
    "B_oracle_pact_seeker": ([ORACLE, PACT, SEEKER], [STRIX, STORM, SKY]),
    "C_oracle_consult_seeker": ([ORACLE, CONSULT, SEEKER], [STRIX, STORM, SKY]),
    "D_oracle_consult_pact": ([ORACLE, CONSULT, PACT], [STRIX, STORM, SKY]),
    "E_all_four": ([ORACLE, CONSULT, PACT, SEEKER], [STRIX, STORM, SKY, QUEEN]),
    "F_oracle_pact": ([ORACLE, PACT], [STRIX, STORM]),
    "G_oracle_only": ([ORACLE], [STRIX]),
    "B_keep_interaction": ([ORACLE, PACT, SEEKER], [STRIX, GLEAM, QUEEN]),
    "B_keep_stormdrake": ([ORACLE, PACT, SEEKER], [STRIX, SKY, QUEEN]),
    "B_keep_skyturtle": ([ORACLE, PACT, SEEKER], [STRIX, STORM, QUEEN]),
    "E_008_build3": ([ORACLE, CONSULT, PACT, SEEKER], [STRIX, STORM, GLEAM, QUEEN]),
}
HEADLINE = ["A_oracle_less", "B_oracle_pact_seeker", "C_oracle_consult_seeker", "D_oracle_consult_pact",
            "E_all_four", "F_oracle_pact"]
LEGACY = {"B_legacy_model": "B_oracle_pact_seeker", "E_legacy_model": "E_all_four"}
FOCUS = [ORACLE, CONSULT, PACT, SEEKER, an.HAZEL, an.OBORO, an.SWIFT, an.EFFIGY, an.DRUID,
         an.BOWMASTERS, an.MASTERMIND, "Gilded Drake", STORM, STRIX, SKY, "Imperial Seal",
         "Demonic Tutor", "Vampiric Tutor", "Enlightened Tutor", "Crop Rotation", "Birthing Pod"]


def base_deck():
    return ex.with_dork(ex.baseline()[0], DORK)


def build(key):
    if key == "V8_frozen":
        return list(ex.baseline()[0])
    if key in LEGACY:
        key = LEGACY[key]
    adds, cuts = CONFIGS[key]
    return ex.swap(base_deck(), cuts, adds)


def set_rules(legacy):
    sv.enable_008b_rules(fair_pact=not legacy, skyturtle=not legacy)


# ---- per-game worker ------------------------------------------------------------------------------

FAM_ORACLE_ANY = {"oracle_consult", "oracle_pact", "oracle_hermit", "oracle_witch", "inf_oracle"}
FAM_NON_ORACLE_DET = {"inf_bowmasters"}


def _first(rec, pred):
    return ex._first(rec, pred)


def play_b(args):
    deck, seed, kw, legacy, deck_cards = args
    set_rules(legacy)
    g = Game(deck, seed=seed, on_play=(seed % 4 == 0), max_turn=MAX_TURN, record_snapshots=True, **kw)
    rec = g.play()
    op = g.opening
    f = hand_features(op, g.on_play)
    eng = 0
    for t in range(1, MAX_TURN + 1):
        r = rec["turns"].get(t)
        if r and r.get("end", {}).get("premium_on_bf"):
            eng = t
            break
    t1, t2 = rec["turns"].get(1, {}), rec["turns"].get(2, {})
    out = {
        "m": rec["mulligans"], "hs": len(op), "fm": f["mana_total"], "ln": f["lands"],
        "c1": t1.get("colors", ""), "c2": t2.get("colors", ""),
        "a1": t1.get("mana_avail", 0), "a2": t2.get("mana_avail", 0),
        "d1": t1.get("nonland_cast", 0), "d2": t2.get("nonland_cast", 0), "eng": eng,
        "w": _first(rec, lambda s: s["det"]),
        "wp": _first(rec, lambda s: s["det"] and s["protected"]),
        "wi": _first(rec, lambda s: s["det"] and s.get("instant")),
        "wo": _first(rec, lambda s: bool(s["families"] & ex.FAM_ORACLE)),
        "wf": _first(rec, lambda s: bool(s["families"] & ex.FAM_INF)),
        "wn": _first(rec, lambda s: s["nondet"]),
        "wO": _first(rec, lambda s: bool(s["families"] & FAM_ORACLE_ANY)),
        "wx": _first(rec, lambda s: bool(s["families"] & FAM_NON_ORACLE_DET)),
        "fam": [],
    }
    if out["w"]:
        t = int(out["w"])
        s = rec["turns"][t]["main"] if out["w"] == t else rec["turns"][t]["instant"]
        out["fam"] = sorted(s["families"] - set(sv.NONDET_FAMILIES))
        out["mc"] = s["min_cards"]
        out["ms"] = s["min_spells"]
    # ---- brick burden: classify every card in hand at each main phase T1..T4
    kept = list(op)
    cls = {}
    per_turn = {}
    for t in range(1, MAX_TURN + 1):
        snap = g.snapshots.get((t, "main"))
        if snap is None:
            continue
        live = set()
        if rec["turns"][t]["main"]["det"]:
            live = sv.solve(snap, want=("det", "all"))["used_cards"]
        c = an.classify_hand(snap, live)
        cls[t] = {k: v[0] for k, v in c.items()}
        per_turn[t] = {
            "n_hand": len(snap.hand),
            "n_material": sum(1 for v in c.values() if v[0] == "material"),
            "n_secondary": sum(1 for v in c.values() if v[0] == "secondary"),
            "n_stranded": sum(1 for v in c.values() if v[0] == "stranded"),
            "focus": {k: (v[0], sorted(v[1])) for k, v in c.items() if k in FOCUS},
        }
    # A kept card is a BRICK if it never had a material role at any main phase T1..T4 while in hand
    # (a card cast or used was material at the snapshot before it left). EARLY-DEAD: no material
    # role at T1 or T2 (slow-but-real cards such as a 4-mana engine are early-dead, not bricks).
    bricks, early = [], []
    for card in kept:
        seen = {t: cls[t][card] for t in cls if card in cls[t]}
        if not any(v == "material" for v in seen.values()):
            bricks.append(card)
        if not any(seen.get(t) == "material" for t in (1, 2)):
            early.append(card)
    out["brick"] = {"kept": kept, "bricks": bricks, "early_dead": early, "per_turn": per_turn}
    # ---- interaction-category access at the start of T2..T4 main phases
    acc = {}
    for t in (2, 3, 4):
        snap = g.snapshots.get((t, "main"))
        if snap is None:
            continue
        units = an.units_of(snap)
        acc[t] = {cat: an.category_access(snap, units, cat, deck_cards) for cat in an.CATEGORIES}
    out["access"] = acc
    return out


def _init(legacy=False):
    set_rules(legacy)


def run_cfg(deck, n, seed0, pool, kw=None, legacy=False):
    kw = kw or {}
    dset = frozenset(deck)
    args = [(deck, seed0 + i, kw, legacy, dset) for i in range(n)]
    return pool.map(play_b, args, chunksize=100)


# ---- metrics --------------------------------------------------------------------------------------

def by(x, t):
    return ex.by(x, t)


METRICS = dict(ex.METRIC_FNS)
for _t in (2, 3, 4):
    METRICS[f"oracle_any_by_t{_t}"] = (lambda t: lambda g: by(g["wO"], t))(_t)
    METRICS[f"non_oracle_det_by_t{_t}"] = (lambda t: lambda g: by(g["wx"], t))(_t)
METRICS["bricks_in_kept_hand_mean"] = lambda g: len(g["brick"]["bricks"])
METRICS["kept_hand_0_bricks"] = lambda g: len(g["brick"]["bricks"]) == 0
METRICS["kept_hand_1_brick"] = lambda g: len(g["brick"]["bricks"]) == 1
METRICS["kept_hand_2plus_bricks"] = lambda g: len(g["brick"]["bricks"]) >= 2
METRICS["early_dead_in_kept_hand_mean"] = lambda g: len(g["brick"]["early_dead"])
for _t in (1, 2, 3, 4):
    METRICS[f"stranded_cards_in_hand_t{_t}"] = (
        lambda t: lambda g: g["brick"]["per_turn"].get(t, {}).get("n_stranded", 0))(_t)
    METRICS[f"secondary_only_cards_in_hand_t{_t}"] = (
        lambda t: lambda g: g["brick"]["per_turn"].get(t, {}).get("n_secondary", 0))(_t)
for _cat in an.CATEGORIES:
    for _t in (3, 4):
        METRICS[f"access_{_cat}_in_hand_t{_t}"] = (
            lambda c, t: lambda g: bool(g["access"].get(t, {}).get(c, (False, False))[0]))(_cat, _t)
        METRICS[f"access_{_cat}_hand_or_tutor_t{_t}"] = (
            lambda c, t: lambda g: any(g["access"].get(t, {}).get(c, (False, False))))(_cat, _t)
MEANS = {"mean_mulligans", "bricks_in_kept_hand_mean", "early_dead_in_kept_hand_mean"} | {k for k in METRICS if k.startswith(("stranded_", "secondary_only_"))}


def summarize(games, ref=None):
    n = len(games)
    out = {"n": n}
    for k, fn in METRICS.items():
        vals = [float(fn(g)) for g in games]
        mean = sum(vals) / n
        row = {"value": round(mean, 5)}
        if k not in MEANS:
            row["ci95"] = ex.wilson(int(round(sum(vals))), n)
        else:
            sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(1, n - 1))
            row["se"] = round(sd / math.sqrt(n), 5)
        if ref is not None:
            rv = [float(fn(g)) for g in ref]
            d = [a - b for a, b in zip(vals, rv)]
            md = sum(d) / n
            sd = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1))
            row["delta_vs_ref"] = round(md, 5)
            row["delta_se"] = round(sd / math.sqrt(n), 5)
        out[k] = row
    fam = Counter(f for g in games for f in g["fam"])
    out["first_win_family_counts"] = dict(fam)
    out["focus_card_quality"] = focus_quality(games)
    out["dead_opening_draw"] = dead_opening(games)
    return out


def focus_quality(games):
    """Per focus card and turn: P(in hand), and the distribution of its best class when in hand,
    plus role frequencies (fair-use availability)."""
    res = {}
    for card in FOCUS:
        row = {}
        for t in (1, 2, 3, 4):
            cnt = Counter()
            roles = Counter()
            for g in games:
                e = g["brick"]["per_turn"].get(t, {}).get("focus", {}).get(card)
                if e:
                    cnt[e[0]] += 1
                    for r in e[1]:
                        roles[r] += 1
            held = sum(cnt.values())
            if not held:
                continue
            row[f"t{t}"] = {"p_in_hand": round(held / len(games), 5), "n_held": held,
                            "material": round(cnt["material"] / held, 4),
                            "secondary_only": round(cnt["secondary"] / held, 4),
                            "stranded": round(cnt["stranded"] / held, 4),
                            "roles": {r: round(v / held, 4) for r, v in sorted(roles.items())}}
        if row:
            res[card] = row
    return res


def dead_opening(games):
    """Per focus card: P(card is a brick | card in the kept hand), split by mulligans taken."""
    res = {}
    for card in FOCUS:
        row = {}
        for m, label in ((0, "opening_7"), (1, "kept_6_after_second_7"), (2, "kept_5")):
            held = [g for g in games if g["m"] == m and card in g["brick"]["kept"]]
            if len(held) >= 20:
                dead = sum(1 for g in held if card in g["brick"]["bricks"])
                early = sum(1 for g in held if card in g["brick"]["early_dead"])
                row[label] = {"n": len(held), "p_dead": round(dead / len(held), 4),
                              "ci95": ex.wilson(dead, len(held)), "p_early_dead": round(early / len(held), 4)}
        held = [g for g in games if card in g["brick"]["kept"]]
        if held:
            dead = sum(1 for g in held if card in g["brick"]["bricks"])
            row["all_kept_hands"] = {"n": len(held), "p_dead": round(dead / len(held), 4),
                                     "ci95": ex.wilson(dead, len(held))}
            res[card] = row
    return res


def save(name, obj):
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f"{name}.json").write_text(json.dumps(obj, indent=1, default=list) + "\n")


def load(name):
    return json.loads((WORK / f"{name}.json").read_text())


# ---- phases -------------------------------------------------------------------------------------

def phase_variants(keys, n, reps, procs, tag):
    res = {"_design": {"n_per_replicate": n, "replicates": reps, "base_seed": BASE_SEED_B,
                       "seed_rule": "replicate r, game i: BASE_SEED_B + r*1_000_000 + i; on the play iff seed % 4 == 0",
                       "reference": "A_oracle_less (same replicate, same seeds)",
                       "rules": "fair Tainted Pact tutor + Skyturtle channel regrowth ON (008b) except *_legacy_model"}}
    with mp.Pool(procs) as pool:
        for r in range(reps):
            seed0 = BASE_SEED_B + r * 1_000_000
            t0 = time.time()
            ref = run_cfg(build("A_oracle_less"), n, seed0, pool)
            for k in keys:
                legacy = k in LEGACY
                g = ref if k == "A_oracle_less" else run_cfg(build(k), n, seed0, pool, legacy=legacy)
                s = summarize(g, ref)
                res.setdefault(k, {})[f"rep{r}"] = s
                print(tag, f"rep{r}", k, s["det_win_by_t4"], round(time.time() - t0), flush=True)
            save(f"variants_{tag}", res)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    ap.add_argument("--keys", default=",".join(HEADLINE))
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--tag", default="headline")
    a = ap.parse_args()
    t0 = time.time()
    keys = [k for k in a.keys.split(",") if k]
    if a.phase == "variants":
        phase_variants(keys, a.n, a.reps, a.procs, a.tag)
    else:
        import deckbuild008b_phases as ph
        ph.run_phase(a.phase, a, keys)
    print("phase", a.phase, a.tag, "done in", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
