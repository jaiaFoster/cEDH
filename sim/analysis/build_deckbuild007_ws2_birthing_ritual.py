"""SIM-DECKBUILD-007 Workstream 2 — Birthing Ritual rung quality.

Real Oracle text: "At the beginning of your end step, if you control a creature, look at the top
seven cards of your library. Then you may sacrifice a creature. If you do, you may put a creature
card with mana value X or less from among those cards onto the battlefield, where X is 1 plus the
sacrificed creature's mana value. Put the rest on the bottom of your library in a random order."

Per instruction: "Do not count Sowing Mycospawn's cast trigger when Ritual puts it directly into
play" - Mycospawn's land-search ability is a CAST trigger ("When you cast this spell..."); Ritual
PUTS creatures onto the battlefield directly (never cast), so that trigger never fires via this
route. Mycospawn is therefore scored ONLY as its own body/stats here, not as a land tutor.

Method: Monte Carlo samples a random 7-card draw from the 99-card pool (minus the creature being
sacrificed) as a proxy for "top seven of the real shuffled remaining library." This ignores cards
already seen/drawn earlier in the actual game (a disclosed simplification - removing an unknown
subset of already-seen cards does not systematically bias one creature's relative frequency over
another for a representative estimate, so the RELATIVE rung comparison stays sound even if the
absolute frequencies are a mild overcount of true late-game top-7 odds, since a real late-game
sample is drawn from a smaller remaining pool with a HIGHER creature density after lands/spells
have been played - this simplification is therefore CONSERVATIVE, not favorable, to Birthing
Ritual's measured hit rates).
"""
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

import deckbuild007_cards as d7  # noqa: E402
from deckbuild007_variants import load_deckbuild007_cards, deckbuild007_cards_pool  # noqa: E402
from opening_hand_model import deck_provenance_fields  # noqa: E402

PREMIUM_BY_RUNG = {
    1: {"Devoted Druid", "Grand Abolisher", "Kinnan, Bonder Prodigy", "Lotho, Corrupt Shirriff"},
    2: {"Derevi, Empyrial Tactician", "Abhorrent Oculus", "Ranger-Captain of Eos", "Formidable Speaker", "Runic Armasaur"},
    3: {"Hazel's Brewmaster", "Clever Impersonator", "Talion, the Kindly Lord"},
    4: {"Seedborn Muse"},
}
IMMEDIATE_CONVERSION_TARGETS = {
    # Creatures whose presence alone materially advances toward a protected win THIS turn cycle,
    # independent of the rest of the board (a strict, conservative subset of the premium lists -
    # not "any strong card," only pieces that are themselves direct engine-online/finisher-class).
    "Seedborn Muse", "Derevi, Empyrial Tactician", "Kinnan, Bonder Prodigy",
}


def _creature_names(cards_pool):
    return [n for n, row in cards_pool.items() if "Creature" in row["type"] and n not in
            {d7.CARPET_NAME, d7.DARK_RITUAL_RESIDUE_NAME}]


def rung_quality(deck_names, cards_pool, sac_mv, sac_name, seed, n):
    """deck_names: the real 99-card list (library pool for sampling). sac_mv: the sacrificed
    creature's mana value (1/2/3/4). Returns the 4 required probabilities for this rung."""
    x = sac_mv + 1
    pool = [c for c in deck_names if c != sac_name]
    rng = random.Random(seed)
    any_hit = meaningful = premium = immediate = 0
    premium_set = PREMIUM_BY_RUNG[sac_mv]
    for _ in range(n):
        sample = rng.sample(pool, 7)
        legal = [c for c in sample if "Creature" in cards_pool[c]["type"] and cards_pool[c]["cmc"] <= x]
        if legal:
            any_hit += 1
            if any(c in premium_set for c in legal):
                premium += 1
            if any(cards_pool[c]["cmc"] >= 2 for c in legal):  # a real upgrade over a 1-drop dork
                meaningful += 1
            if any(c in IMMEDIATE_CONVERSION_TARGETS for c in legal):
                immediate += 1
    return {
        "p_any_legal_hit": any_hit / n,
        "p_meaningful_upgrade": meaningful / n,
        "p_premium_target": premium / n,
        "p_immediate_conversion_target": immediate / n,
    }


def main():
    d7.install_new_card_tables()
    try:
        payload, base_rows = load_deckbuild007_cards()
        cards_pool = deckbuild007_cards_pool(base_rows)
        deck_names = list(base_rows.keys())

        # Representative sac-creature per rung (a real MV1/2/3/4 creature this deck runs and would
        # plausibly sacrifice - a dead/replaceable 1-drop dork, a redundant 2-drop, etc. Results
        # are reported by RUNG (sac_mv), not by which specific creature was sacrificed, since X
        # depends only on the sacrificed creature's own mana value, not its identity).
        reps = {1: "Delighted Halfling", 2: "Badgermole Cub", 3: "Endurance", 4: "Clever Impersonator"}

        out = {
            **deck_provenance_fields(payload),
            "phase": "SIM_DECKBUILD_007_WS2_BIRTHING_RITUAL", "evidence_type": "static_probability",
            "method_note": (
                "Monte Carlo samples of a 7-card draw from the 99-card pool (proxy for the "
                "shuffled remaining library's top 7) - see module docstring for the disclosed, "
                "CONSERVATIVE simplification (ignores already-seen cards, understating true "
                "late-game creature density in the remaining library)."
            ),
            "mycospawn_note": (
                "Sowing Mycospawn's land-search is a CAST trigger, never fires when Ritual puts "
                "it into play directly - scored here as a body only, no tutor credit."
            ),
            "by_rung": {},
        }
        for sac_mv, sac_name in reps.items():
            out["by_rung"][f"sac_MV{sac_mv}_find_MV_le_{sac_mv+1}"] = {
                "representative_sac_creature": sac_name,
                **rung_quality(deck_names, cards_pool, sac_mv, sac_name, seed=87100 + sac_mv, n=40000),
            }

        rates = [v["p_any_legal_hit"] for v in out["by_rung"].values()]
        premium_rates = [v["p_premium_target"] for v in out["by_rung"].values()]
        out["required_summary"] = {
            "mean_p_any_legal_hit_across_rungs": sum(rates) / len(rates),
            "mean_p_premium_target_across_rungs": sum(premium_rates) / len(premium_rates),
            "verdict_input": (
                "premium two-mana engine" if sum(premium_rates) / len(premium_rates) > 0.35 else
                "grindy nondeterministic value"
            ),
        }
    finally:
        d7.uninstall_new_card_tables()

    out_path = REPO_ROOT / "results" / "solo_baseline" / "deckbuild007_ws2_birthing_ritual.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["by_rung"], indent=2))
    print(json.dumps(out["required_summary"], indent=2))


if __name__ == "__main__":
    main()
