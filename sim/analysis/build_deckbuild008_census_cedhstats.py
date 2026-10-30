"""SIM-DECKBUILD-008 — external 6-month / 1-month census cross-check via cedhstats.org.

The repository's TopDeck archive only reaches back to 2026-07-27 (~3 months). cedhstats.org's
public decklist search (Thrasios/Tymna, events >=16 players) supports `with=<oracle_id>` and
`without=<oracle_id>` filters and reports a result count. Two counts per card per period give the
full 2x2 table against Thassa's Oracle:
    n(X)            = with=X
    n(X & no Oracle) = with=X & without=Oracle
    n(X & Oracle)   = n(X) - n(X & no Oracle)
Oracle / no-Oracle denominators come from with=Oracle and without=Oracle.

(Observed behaviour, 2026-10-30: repeating `with` keeps only the last value, so the subtraction
form is used rather than a two-card `with` query.)

This is an independent population built by a third party (oracle-normalized through Scryfall),
used only to check that the repository census is not an artefact of its shorter window. It
supplies no top-cut data. Results are cached so the report is reproducible without re-querying.
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
from build_deckbuild008_package_census import FOCUS, fisher_two_sided, log_or, wilson  # noqa: E402

OUT = REPO_ROOT / "results" / "solo_baseline" / "deckbuild008_census_cedhstats.json"
BASE = "https://cedhstats.org/decklists?commander_id=16&min_players=16&period={period}&{q}"
ORACLE_NAME = "Thassa's Oracle"
PERIODS = ["6m", "1m"]
COUNT_RE = re.compile(r"([0-9,]+) results?\b")


_CACHE_PATH = REPO_ROOT / "results" / "solo_baseline" / ".deckbuild008_cedhstats_query_cache.json"
_CACHE = json.loads(_CACHE_PATH.read_text()) if _CACHE_PATH.exists() else {}


def _get(url):
    if url in _CACHE:
        return _CACHE[url]
    for attempt in range(6):
        out = subprocess.run(["curl", "-sSL", "--max-time", "60", url], capture_output=True,
                             text=True, timeout=90).stdout
        m = COUNT_RE.search(out)
        if m:
            _CACHE[url] = int(m.group(1).replace(",", ""))
            _CACHE_PATH.write_text(json.dumps(_CACHE))
            return _CACHE[url]
        time.sleep(5 * 2 ** attempt)
    raise RuntimeError(f"no result count for {url}")


def oracle_id(name):
    url = "https://api.scryfall.com/cards/named?exact=" + urllib.parse.quote(name)
    out = subprocess.run(["curl", "-sS", "--max-time", "30", url], capture_output=True, text=True).stdout
    time.sleep(0.12)
    return json.loads(out)["oracle_id"]


def main():
    cards = []
    for group in FOCUS.values():
        for c in group:
            if c not in cards:
                cards.append(c)
    ids = {c: oracle_id(c) for c in cards}
    o = ids[ORACLE_NAME]
    result = {"task": "SIM-DECKBUILD-008", "artifact": "census_cedhstats_crosscheck",
              "source": "https://cedhstats.org/decklists (Thrasios / Tymna, min_players=16)",
              "retrieved": time.strftime("%Y-%m-%d", time.gmtime()), "oracle_ids": ids,
              "periods": {}}
    for period in PERIODS:
        n_o = _get(BASE.format(period=period, q=f"with={o}"))
        n_no = _get(BASE.format(period=period, q=f"without={o}"))
        rows = []
        for c in cards:
            if c == ORACLE_NAME:
                continue
            n_x = _get(BASE.format(period=period, q=f"with={ids[c]}"))
            time.sleep(0.6)
            n_x_no = _get(BASE.format(period=period, q=f"with={ids[c]}&without={o}"))
            time.sleep(0.6)
            a, cc = n_x - n_x_no, n_x_no
            b, d = n_o - a, n_no - cc
            lor, lo, hi = log_or(a, b, cc, d)
            rows.append({"card": c, "k_with_oracle": a, "k_without_oracle": cc,
                         "p_with_oracle": a / n_o, "p_with_oracle_ci95": wilson(a, n_o),
                         "p_without_oracle": cc / n_no, "p_without_oracle_ci95": wilson(cc, n_no),
                         "diff_pp": 100 * (a / n_o - cc / n_no), "log_or": lor,
                         "log_or_ci95": [lo, hi], "fisher_p": fisher_two_sided(a, b, cc, d)})
            print(period, c, a, cc, flush=True)
        result["periods"][period] = {"n_oracle": n_o, "n_no_oracle": n_no,
                                     "oracle_inclusion": n_o / (n_o + n_no), "rows": rows}
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
