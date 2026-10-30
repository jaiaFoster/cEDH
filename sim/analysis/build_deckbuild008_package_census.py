"""SIM-DECKBUILD-008 — Thassa's Oracle package census for Thrasios/Tymna.

Empirical package discovery: which cards travel WITH Thassa's Oracle in current T&T lists, which
are ordinary T&T staples that do not depend on Oracle, and which are enriched in top cuts.

Source: the repository's own immutable TopDeck.gg raw snapshots (full structured decklists).
Data cutoff = the latest event start date in the archive, never later than DATA_CUTOFF.

Eligibility tiers (mirrors META-010's documented rules, extended):
  strict  - event name explicitly says cEDH / competitive, >=16 seats, no exclusion keyword.
  broad   - >=16 seats, no exclusion keyword, and EITHER the strict label OR >=50% of seats with a
            known commander use a commander in the EDHTop16 six-month top-100 (stored snapshot
            data/tournament_snapshots/commanders_SIX_MONTHS.json).
Exclusion keywords: casual, precon, budget, bracket, test, practice, sealed, draft, league casual,
"$100" budget formats, highlander, etc. (see EXCLUDE_RE).

The subject pilot's own lists are EXCLUDED (they are the deck under study, not the population).

Statistics, per card X and population P:
  P(X | Oracle), P(X | no Oracle), difference, Haldane-corrected log odds ratio with Wald 95% CI,
  two-sided Fisher exact p, Benjamini-Hochberg q across the discovery scan, and Beta(1,1)-shrunk
  conditional rates. Top-cut enrichment = P(top cut | X) / P(top cut | not X) within the same
  population, with Fisher p. Small cells are reported, never hidden; |log OR| with n<10 per arm is
  flagged LOW_N.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAP = REPO_ROOT / "data" / "tournament_snapshots" / "topdeck"
OUT_DIR = REPO_ROOT / "results" / "solo_baseline"
TOP100_PATH = REPO_ROOT / "data" / "tournament_snapshots" / "commanders_SIX_MONTHS.json"

DATA_CUTOFF = "2026-10-30"
WINDOW_30D_START = "2026-09-30"
TT = frozenset({"Thrasios, Triton Hero", "Tymna the Weaver"})
SUBJECT_PILOT_IDS = {"bQ97iyjPFLUq4ZTFPgMhscb9PJG3"}  # Jaia Foster (TopDeck player id)
ORACLE = "Thassa's Oracle"

STRICT_RE = re.compile(r"c-?edh|competitive", re.I)
EXCLUDE_RE = re.compile(
    r"casual|precon|budget|bracket|\btest\b|practice|sealed|draft|highlander|chaos|"
    r"pauper|\bpdh\b|oathbreaker|\$\s?\d{2,3}\b(?!,|k)|league casual|learn to|beginner|"
    r"brawl\b(?!.*cedh)|duel|1v1|1 v 1", re.I)

# Cards whose relationship to Oracle the assignment asks about explicitly (in report order).
FOCUS = {
    "core": ["Thassa's Oracle", "Demonic Consultation", "Tainted Pact"],
    "access_bridge": ["Spellseeker", "Demonic Tutor", "Vampiric Tutor", "Imperial Seal",
                      "Mystical Tutor", "Enlightened Tutor", "Worldly Tutor", "Gamble",
                      "Survival of the Fittest", "Birthing Pod", "Chord of Calling",
                      "Finale of Devastation", "Eldritch Evolution", "Neoform",
                      "Nature's Rhythm", "Green Sun's Zenith", "Summoner's Pact",
                      "Ranger-Captain of Eos", "Intuition", "Lim-Dûl's Vault"],
    "timing": ["Borne Upon a Wind", "High Fae Trickster", "Emergence Zone",
               "Teferi, Mage of Zhalfir", "Crop Rotation", "Alchemist's Refuge",
               "Leyline of Anticipation", "Vedalken Orrery"],
    "protection": ["Silence", "Grand Abolisher", "Voice of Victory", "Ranger-Captain of Eos",
                   "Allosaurus Shepherd", "Veil of Summer", "Autumn's Veil", "Deflecting Swat",
                   "Fierce Guardianship", "Flare of Denial", "Pact of Negation",
                   "Force of Will", "Force of Negation", "Mindbreak Trap", "Misdirection",
                   "Swan Song", "Flusterstorm", "Mental Misstep", "Snapback", "Cloud of Faeries",
                   "Orim's Chant", "Destiny Spinner"],
    "creature_library_empty": ["Hermit Druid", "Divining Witch", "Shang-Chi, Master of Kung Fu",
                               "Tasha's Hideous Laughter", "Jace, Wielder of Mysteries",
                               "Laboratory Maniac", "Spellseeker"],
    "creature_factory_shell": ["Devoted Druid", "Swift Reconfiguration", "Hazel's Brewmaster",
                               "Machine God's Effigy", "Nature's Rhythm", "The Cabbage Merchant",
                               "Mockingbird", "Flash Photography", "Abhorrent Oculus",
                               "Oboro Breezecaller", "Gaea's Cradle", "Kinnan, Bonder Prodigy",
                               "Delney, Streetwise Lookout", "Faerie Mastermind",
                               "The Queen of Dale", "Strix Serenade", "Deathrite Shaman",
                               "Training Grounds", "Biomancer's Familiar", "Seedborn Muse",
                               "Formidable Speaker", "Springheart Nantuko", "Derevi, Empyrial Tactician",
                               "Badgermole Cub", "Clever Impersonator", "Volatile Stormdrake"],
}


TURBO_MARKERS = frozenset({"Ad Nauseam", "Necropotence", "Lion's Eye Diamond", "Reanimate",
                           "Culling the Weak", "Bolas's Citadel"})
SUBJECT_SOURCE = REPO_ROOT / "data" / "deck_sources" / "moxfield" / "tymna-thrasios" / "current.json"


def subject_cardset():
    return frozenset(c["name"] for c in json.loads(SUBJECT_SOURCE.read_text(encoding="utf-8"))["cards"])


def _latest_raw(entry):
    return SNAP / entry["raw_snapshot"]


def load_top100():
    d = json.loads(TOP100_PATH.read_text(encoding="utf-8"))
    names = set()
    for c in d["commanders"][:100]:
        names.add(frozenset(p.strip() for p in c["name"].split(" / ")))
    return names


def classify_event(norm, top100):
    name = norm["name"]
    if norm["start_date_utc"][:10] > DATA_CUTOFF:
        return None  # misdated future events in the feed (e.g. 2027/2030) are dropped
    if norm["field_size"] < 16:
        return None
    if EXCLUDE_RE.search(name):
        return None
    strict = bool(STRICT_RE.search(name))
    known = [frozenset(e["commanders"]) for e in norm["entries"] if e["commanders"]]
    share = (sum(1 for k in known if k in top100) / len(known)) if known else 0.0
    if strict:
        return "strict"
    if len(known) >= 8 and share >= 0.5:
        return "broad"
    return None


def load_population():
    manifest = json.loads((SNAP / "manifest.json").read_text(encoding="utf-8"))["events"]
    top100 = load_top100()
    rows = []
    events = {}
    for tid, e in sorted(manifest.items()):
        norm = json.loads((SNAP / e["normalized_event"]).read_text(encoding="utf-8"))
        tier = classify_event(norm, top100)
        if tier is None:
            continue
        flags = {s["player_id"]: s for s in norm["entries"]}
        raw = None
        for s in norm["entries"]:
            if frozenset(s["commanders"]) != TT or not s["structured_deck_present"]:
                continue
            if raw is None:
                raw = json.load(gzip.open(_latest_raw(e)))
                raw_by_id = {r.get("id"): r for r in raw["standings"]}
            r = raw_by_id.get(s["player_id"])
            if not r or not isinstance(r.get("deckObj"), dict):
                continue
            mb = r["deckObj"].get("Mainboard") or {}
            if sum(v.get("count", 1) for v in mb.values()) < 95:
                continue  # partial/unparseable registrations
            rows.append({
                "tid": tid, "event": norm["name"], "date": norm["start_date_utc"][:10],
                "field_size": norm["field_size"], "tier": tier,
                "player_id": s["player_id"], "standing": s["standing"],
                "top_cut": bool(s["top_cut"]), "winner": bool(s["winner"]),
                "subject": s["player_id"] in SUBJECT_PILOT_IDS,
                "cards": frozenset(mb.keys()),
            })
        events[tid] = {"name": norm["name"], "tier": tier, "date": norm["start_date_utc"][:10],
                       "field_size": norm["field_size"], "top_cut_size": norm.get("top_cut_size")}
        del flags
    return rows, events


# ---- statistics ---------------------------------------------------------------------------

def _logfact(n):
    return math.lgamma(n + 1)


def fisher_two_sided(a, b, c, d):
    """Exact two-sided Fisher p for [[a,b],[c,d]] (sum of tables with prob <= observed)."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2

    def p(x):
        return math.exp(_logfact(r1) + _logfact(r2) + _logfact(c1) + _logfact(n - c1)
                        - _logfact(n) - _logfact(x) - _logfact(r1 - x) - _logfact(c1 - x)
                        - _logfact(r2 - c1 + x))
    lo, hi = max(0, c1 - r2), min(r1, c1)
    p0 = p(a)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= p0 * (1 + 1e-9)))


def log_or(a, b, c, d):
    a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    lor = math.log((a * d) / (b * c))
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return lor, lor - 1.96 * se, lor + 1.96 * se


def wilson(k, n):
    if n == 0:
        return (None, None)
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (centre - half, centre + half)


def bh(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    q = [0.0] * len(pvals)
    prev = 1.0
    m = len(pvals)
    for rank, i in reversed(list(enumerate(order, start=1))):
        prev = min(prev, pvals[i] * m / rank)
        q[i] = prev
    return q


def conditional_row(card, pop):
    with_o = [r for r in pop if ORACLE in r["cards"]]
    without_o = [r for r in pop if ORACLE not in r["cards"]]
    a = sum(card in r["cards"] for r in with_o)
    b = len(with_o) - a
    c = sum(card in r["cards"] for r in without_o)
    d = len(without_o) - c
    lor, lo, hi = log_or(a, b, c, d)
    p_with = a / len(with_o) if with_o else None
    p_without = c / len(without_o) if without_o else None
    has = [r for r in pop if card in r["cards"]]
    hasnt = [r for r in pop if card not in r["cards"]]
    tc_a = sum(r["top_cut"] for r in has)
    tc_c = sum(r["top_cut"] for r in hasnt)
    tc_has = tc_a / len(has) if has else None
    tc_hasnt = tc_c / len(hasnt) if hasnt else None
    win_has = sum(r["winner"] for r in has)
    return {
        "card": card,
        "n_lists": len(pop), "n_oracle": len(with_o), "n_no_oracle": len(without_o),
        "inclusion_all": len(has) / len(pop) if pop else None,
        "k_with_oracle": a, "k_without_oracle": c,
        "p_with_oracle": p_with, "p_with_oracle_ci95": wilson(a, len(with_o)),
        "p_without_oracle": p_without, "p_without_oracle_ci95": wilson(c, len(without_o)),
        "p_with_oracle_shrunk": (a + 1) / (len(with_o) + 2),
        "p_without_oracle_shrunk": (c + 1) / (len(without_o) + 2),
        "diff_pp": (None if p_with is None or p_without is None else 100 * (p_with - p_without)),
        "lift": (None if not p_without else (p_with / p_without if p_with is not None else None)),
        "log_or": lor, "log_or_ci95": (lo, hi),
        "fisher_p_oracle": fisher_two_sided(a, b, c, d),
        "low_n": min(a + c, b + d, len(with_o), len(without_o)) < 10,
        "top_cut_rate_with_card": tc_has, "top_cut_rate_without_card": tc_hasnt,
        "top_cut_enrichment": (None if not tc_hasnt or tc_has is None else tc_has / tc_hasnt),
        "top_cut_fisher_p": fisher_two_sided(tc_a, len(has) - tc_a, tc_c, len(hasnt) - tc_c),
        "n_top_cut_with_card": tc_a, "n_winners_with_card": win_has,
    }


def density_by_oracle(pop, role_sets):
    out = {}
    for label, sub in (("oracle", [r for r in pop if ORACLE in r["cards"]]),
                       ("no_oracle", [r for r in pop if ORACLE not in r["cards"]])):
        dens = {}
        for role, names in role_sets.items():
            vals = [len(r["cards"] & names) for r in sub]
            dens[role] = {"mean": (sum(vals) / len(vals)) if vals else None, "n": len(vals)}
        out[label] = dens
    return out


# Role sets used for package-density comparisons. Hand-classified, deliberately narrow; see
# report section on census caveats.
ROLE_SETS = {
    "tutors_any": {"Demonic Tutor", "Vampiric Tutor", "Imperial Seal", "Mystical Tutor",
                   "Enlightened Tutor", "Worldly Tutor", "Gamble", "Spellseeker",
                   "Survival of the Fittest", "Birthing Pod", "Chord of Calling",
                   "Finale of Devastation", "Eldritch Evolution", "Neoform", "Nature's Rhythm",
                   "Green Sun's Zenith", "Summoner's Pact", "Ranger-Captain of Eos",
                   "Crop Rotation", "Intuition", "Lim-Dûl's Vault", "Tainted Pact",
                   "Merchant Scroll", "Personal Tutor", "Sylvan Tutor", "Eladamri's Call",
                   "Beseech the Mirror", "Wishclaw Talisman", "Diabolic Intent",
                   "Grim Tutor", "Recruiter of the Guard", "Recruiter of the Gaurd"},
    "proactive_protection": {"Silence", "Grand Abolisher", "Voice of Victory",
                             "Ranger-Captain of Eos", "Allosaurus Shepherd", "Veil of Summer",
                             "Autumn's Veil", "Orim's Chant", "Destiny Spinner", "Defense Grid"},
    "free_counters": {"Force of Will", "Force of Negation", "Fierce Guardianship",
                      "Flare of Denial", "Pact of Negation", "Mindbreak Trap", "Misdirection",
                      "Commandeer", "Subtlety", "Deflecting Swat", "Snapback"},
    "timing_enablers": {"Borne Upon a Wind", "High Fae Trickster", "Emergence Zone",
                        "Teferi, Mage of Zhalfir", "Alchemist's Refuge",
                        "Leyline of Anticipation", "Vedalken Orrery"},
    "oracle_core": {"Thassa's Oracle", "Demonic Consultation", "Tainted Pact"},
    "cf_infinite_shell": {"Devoted Druid", "Swift Reconfiguration", "Hazel's Brewmaster",
                          "Machine God's Effigy", "Training Grounds", "Biomancer's Familiar",
                          "Springheart Nantuko", "Oboro Breezecaller"},
}


def summarise(pop, label):
    focus_cards = []
    for group in FOCUS.values():
        for c in group:
            if c not in focus_cards:
                focus_cards.append(c)
    focus = [conditional_row(c, pop) for c in focus_cards]
    # Discovery scan: every card seen in >=10 lists of this population (excluding Oracle).
    cnt = Counter(c for r in pop for c in r["cards"])
    scan_cards = sorted(c for c, k in cnt.items() if k >= 10 and c != ORACLE)
    scan = [conditional_row(c, pop) for c in scan_cards]
    qs = bh([r["fisher_p_oracle"] for r in scan])
    for r, q in zip(scan, qs):
        r["bh_q_oracle"] = q
    scan.sort(key=lambda r: (r["fisher_p_oracle"], -abs(r["log_or"])))
    oracle_n = sum(ORACLE in r["cards"] for r in pop)
    core3 = sum(all(c in r["cards"] for c in ("Thassa's Oracle", "Demonic Consultation", "Tainted Pact")) for r in pop)
    o_c_only = sum(("Thassa's Oracle" in r["cards"] and "Demonic Consultation" in r["cards"]
                    and "Tainted Pact" not in r["cards"]) for r in pop)
    o_p_only = sum(("Thassa's Oracle" in r["cards"] and "Tainted Pact" in r["cards"]
                    and "Demonic Consultation" not in r["cards"]) for r in pop)
    o_neither = sum(("Thassa's Oracle" in r["cards"] and "Tainted Pact" not in r["cards"]
                     and "Demonic Consultation" not in r["cards"]) for r in pop)
    return {
        "label": label,
        "n_lists": len(pop),
        "n_events": len({r["tid"] for r in pop}),
        "n_unique_pilots": len({r["player_id"] for r in pop}),
        "date_range": [min(r["date"] for r in pop), max(r["date"] for r in pop)] if pop else None,
        "n_oracle_lists": oracle_n,
        "oracle_inclusion": oracle_n / len(pop) if pop else None,
        "oracle_inclusion_ci95": wilson(oracle_n, len(pop)),
        "core_structure": {"oracle+consult+pact": core3, "oracle+consult_only": o_c_only,
                           "oracle+pact_only": o_p_only, "oracle_without_consult_or_pact": o_neither},
        "n_top_cut": sum(r["top_cut"] for r in pop),
        "n_winners": sum(r["winner"] for r in pop),
        "focus": focus,
        "discovery_scan_top": scan[:60],
        "discovery_scan_size": len(scan),
        "density_by_oracle": density_by_oracle(pop, ROLE_SETS),
    }


def _fmt(x, nd=3):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def main():
    rows, events = load_population()
    subject_rows = [r for r in rows if r["subject"]]
    pop_all = [r for r in rows if not r["subject"]]
    pops = {
        "broad_archive": pop_all,
        "strict_archive": [r for r in pop_all if r["tier"] == "strict"],
        "broad_30d": [r for r in pop_all if r["date"] >= WINDOW_30D_START],
        "broad_top_cut": [r for r in pop_all if r["top_cut"]],
        "broad_large_events_64plus": [r for r in pop_all if r["field_size"] >= 64],
    }
    # Within-archetype strata. The raw T&T population mixes a turbo/Ad-Nauseam cluster (almost
    # always Oracle) with a creature/slop cluster (often Oracle-less) - the subject deck's own
    # family. Conditional rates are therefore also reported inside creature-shell lists so that
    # "what do Oracle lists cut?" is not answered by comparing two different archetypes.
    subject_names = subject_cardset()
    pops["creature_shell_no_turbo"] = [
        r for r in pop_all if "Devoted Druid" in r["cards"] and not (r["cards"] & TURBO_MARKERS)]
    pops["high_overlap_75plus"] = [r for r in pop_all if len(r["cards"] & subject_names) >= 75]
    # Pilot-deduplicated sensitivity: most recent list per pilot.
    latest = {}
    for r in sorted(pop_all, key=lambda r: r["date"]):
        latest[r["player_id"]] = r
    pops["broad_archive_pilot_dedup"] = list(latest.values())

    result = {
        "task": "SIM-DECKBUILD-008",
        "artifact": "package_census",
        "run_class": "STATIC_ANALYSIS",
        "evidence_type": "tournament_decklist_census",
        "source": "TopDeck.gg raw snapshots stored in data/tournament_snapshots/topdeck/raw "
                  "(provided by TopDeck.gg; attribution retained)",
        "data_cutoff": DATA_CUTOFF,
        "archive_note": "The repository archive begins 2026-07-27, so the 'archive' window is "
                        "~3 months, not 6. The 6-month view is supplied separately by the "
                        "cedhstats.org cross-check (deckbuild008_census_cedhstats.json).",
        "eligibility": {"strict": STRICT_RE.pattern, "exclude": EXCLUDE_RE.pattern,
                        "broad_rule": ">=16 seats, not excluded, strict label OR >=50% of known "
                                      "commanders in EDHTop16 six-month top-100 (>=8 known)",
                        "n_events_eligible": len(events),
                        "n_events_strict": sum(e["tier"] == "strict" for e in events.values())},
        "subject_pilot_lists_excluded": [{"event": r["event"], "date": r["date"],
                                          "has_oracle": ORACLE in r["cards"]} for r in subject_rows],
        "role_sets": {k: sorted(v) for k, v in ROLE_SETS.items()},
        "populations": {k: summarise(v, k) for k, v in pops.items()},
    }
    out_json = OUT_DIR / "deckbuild008_package_census.json"
    out_json.write_text(json.dumps(result, indent=1, default=list) + "\n", encoding="utf-8")

    out_csv = OUT_DIR / "deckbuild008_package_census.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "card", "n_lists", "n_oracle", "n_no_oracle", "inclusion_all",
                    "p_with_oracle", "p_without_oracle", "diff_pp", "lift", "log_or",
                    "log_or_lo", "log_or_hi", "fisher_p", "low_n", "top_cut_rate_with",
                    "top_cut_rate_without", "top_cut_enrichment", "top_cut_fisher_p"])
        for pname, summ in result["populations"].items():
            for r in summ["focus"]:
                w.writerow([pname, r["card"], r["n_lists"], r["n_oracle"], r["n_no_oracle"],
                            _fmt(r["inclusion_all"]), _fmt(r["p_with_oracle"]),
                            _fmt(r["p_without_oracle"]), _fmt(r["diff_pp"], 1), _fmt(r["lift"], 2),
                            _fmt(r["log_or"], 2), _fmt(r["log_or_ci95"][0], 2),
                            _fmt(r["log_or_ci95"][1], 2), _fmt(r["fisher_p_oracle"], 4),
                            r["low_n"], _fmt(r["top_cut_rate_with_card"]),
                            _fmt(r["top_cut_rate_without_card"]), _fmt(r["top_cut_enrichment"], 2),
                            _fmt(r["top_cut_fisher_p"], 4)])
    for k, s in result["populations"].items():
        print(f"{k}: n={s['n_lists']} events={s['n_events']} pilots={s['n_unique_pilots']} "
              f"oracle={s['n_oracle_lists']} ({_fmt(s['oracle_inclusion'])}) core={s['core_structure']}")
    print(f"wrote {out_json}\nwrote {out_csv}")


if __name__ == "__main__":
    sys.exit(main())
