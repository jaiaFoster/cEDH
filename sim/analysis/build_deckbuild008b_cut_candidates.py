"""SIM-DECKBUILD-008b — standalone quality (brick rate) of every plausible flex / cut candidate.

Same classifier as the variants phase, on 6,000 paired goldfish games of v8 (which still contains Strix,
Stormdrake and Skyturtle) and of A_oracle_less. Writes deckbuild008b_work/cut_candidates.json.
"""
from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_deckbuild008b_experiments as bx  # noqa: E402

CANDIDATES = ["Strix Serenade", "Volatile Stormdrake", "Colossal Skyturtle", "Gilded Drake", "The Queen of Dale",
              "Gleaming Splendor", "Lotho, Corrupt Shirriff", "Esper Sentinel", "Delney, Streetwise Lookout",
              "Clever Impersonator", "Endurance", "Mental Misstep", "Swan Song", "Flusterstorm", "Faerie Mastermind",
              "Orcish Bowmasters", "Oboro Breezecaller", "Derevi, Empyrial Tactician", "Spellseeker"]


def main():
    bx.FOCUS = list(dict.fromkeys(bx.FOCUS + CANDIDATES))
    out = {"_design": {"n": 6000, "seed0": bx.BASE_SEED_B + 3_000_000, "classifier": "deckbuild008b_analysis"}}
    with mp.Pool(4) as pool:
        for key in ("V8_frozen", "A_oracle_less"):
            g = bx.run_cfg(bx.build(key), 6000, bx.BASE_SEED_B + 3_000_000, pool)
            dd, fq = bx.dead_opening(g), bx.focus_quality(g)
            out[key] = {c: {"dead_in_kept_hand": dd[c]["all_kept_hands"],
                            "t3": fq.get(c, {}).get("t3"), "t4": fq.get(c, {}).get("t4")}
                        for c in CANDIDATES if c in dd}
            for c, d in out[key].items():
                print(key, c, d["dead_in_kept_hand"]["p_dead"], flush=True)
    bx.save("cut_candidates", out)


if __name__ == "__main__":
    main()
