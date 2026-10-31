"""SIM-DECKBUILD-008b — interaction coverage (category coverage, not interaction count).

Static, exact analysis over the exact 98-card configurations:
* which cards cover each interaction category (deckbuild008b_analysis.CATEGORIES, from Oracle text);
* how many in-deck tutors can directly deliver a card of that category (hand or battlefield);
* exact hypergeometric P(at least one category card seen) by T2/T3/T4 (on the draw, 7 + t draws, no
  mulligan), and P(a category card OR a tutor that reaches one) seen;
* a per-card audit of the three proposed cuts (Strix Serenade, Volatile Stormdrake, Colossal Skyturtle)
  quoting the rules text that matters, including the Stormdrake vs Gilded Drake differences.

Writes results/solo_baseline/deckbuild008b_interaction_coverage.json. The goldfish-measured access rates
(category card castable in hand / reachable by a castable tutor at T3/T4) come from the variants phase.
"""
from __future__ import annotations

import json
import sys
from math import comb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

import build_deckbuild008b_experiments as bx  # noqa: E402
import deckbuild008_cards as dc  # noqa: E402
import deckbuild008_solver as sv  # noqa: E402
import deckbuild008b_analysis as an  # noqa: E402

OUT = REPO_ROOT / "results" / "solo_baseline" / "deckbuild008b_interaction_coverage.json"
KEYS = ["V8_frozen", "A_oracle_less", "B_oracle_pact_seeker", "C_oracle_consult_seeker", "D_oracle_consult_pact",
        "E_all_four", "B_keep_interaction", "B_keep_stormdrake", "B_keep_skyturtle", "E_008_build3"]


def p_at_least_one(N, K, n):
    """Hypergeometric P(X >= 1) drawing n of N with K successes."""
    if K <= 0:
        return 0.0
    if n >= N:
        return 1.0
    return 1 - comb(N - K, n) / comb(N, n)


def direct_tutors(deck, card):
    """In-deck tutors able to deliver `card` (to hand, top or battlefield) — static topology."""
    out = []
    creatures_mv = {dc.mv(c) for c in deck if dc.is_creature(c) and not dc.is_land(c)}
    for t in dc.TUTORS:
        if t not in deck or t == card:
            continue
        f = dc.TUTORS[t]["find"]
        if f == "land":
            continue  # Crop Rotation puts lands onto the battlefield: a channel land is then not in hand
        if f == "creature_sac_plus1":
            ok = dc.is_creature(card) and (dc.mv(card) - 1) in creatures_mv
        elif f == "creature_sac_plus2":
            ok = dc.is_creature(card)
        elif f in ("creature_x", "green_creature_x"):
            ok = dc.is_creature(card) and (f == "creature_x" or dc.is_green(card))
            if ok and dc.TUTORS[t]["dest"] == "bf" and card == an.SKYTURTLE:
                ok = False  # Skyturtle's value is channel FROM HAND; X-tutors put it onto the battlefield
        else:
            ok = dc.tutor_can_find(t, card, sac_mv=9)
        if ok:
            out.append(t)
    return sorted(out)


def coverage(deck):
    res = {}
    N = len(deck)
    for cat, cards in an.CATEGORIES.items():
        present = sorted(cards & set(deck))
        tut = sorted({t for c in present for t in direct_tutors(deck, c)})
        res[cat] = {"cards": present, "n_cards": len(present), "n_direct_tutors": len(tut), "tutors": tut,
                    **{f"p_seen_by_t{t}": round(p_at_least_one(N, len(present), 7 + t), 4) for t in (2, 3, 4)},
                    **{f"p_card_or_tutor_seen_by_t{t}": round(p_at_least_one(N, len(set(present) | set(tut)), 7 + t), 4)
                       for t in (2, 3, 4)}}
    return res


CUT_AUDIT = {
    "Strix Serenade": {
        "cost": "{U} instant",
        "text": "Counter target artifact, creature, or planeswalker spell. Its controller creates a 2/2 blue Bird.",
        "unique_coverage": "the deck's only 1-mana hard counter for CREATURE spells. Remaining creature-spell "
                           "answers: Force of Will, Pact of Negation, Flare of Denial (pitch a blue creature), "
                           "Mindbreak Trap (conditional), Subtlety (evoke, top/bottom), Sink into Stupor "
                           "(3-mana bounce). Every remaining one costs a card, a creature, a future turn, or "
                           "4+ mana. Artifact-spell coverage stays wide (9 answers incl. FoN, Fierce Guardianship).",
        "goldfish_value": "0 (counters only opponents' spells)",
        "tournament_evidence": "Geekery R3: Strix (paid with Lotho Treasure) countered Kinnan's Phyrexian Metamorph.",
        "census": "1.1% of Oracle T&T lists / 0.5% of non-Oracle lists (DECKBUILD-008): pilot tech in both.",
    },
    "Volatile Stormdrake": {
        "cost": "{1}{U} creature — Drake (no flash)",
        "text": "Flying, hexproof from activated and triggered abilities. ETB: exchange control of this and target "
                "creature an opponent controls. If you do, you get EEEE, then sacrifice that creature unless you "
                "pay E equal to its mana value.",
        "vs_gilded_drake": [
            {"situation": "target MV <= 4 (almost every cEDH engine creature: Kinnan, Thrasios, Tymna, "
                          "Rograkh, Dockside, Bowmasters, Oculus, Hermit, Druid...)",
             "stormdrake": "steal and keep", "gilded_drake": "steal and keep", "edge": "equal"},
            {"situation": "target MV >= 5",
             "stormdrake": "steal, then sacrifice it (removal, not theft)", "gilded_drake": "steal and keep",
             "edge": "Gilded"},
            {"situation": "target gains hexproof / is sacrificed / bounced in response",
             "stormdrake": "ability fizzles; you KEEP a 2-mana flyer", "gilded_drake":
             "'still resolves... if you don't or can't make an exchange, sacrifice this creature' -> you lose it",
             "edge": "Stormdrake"},
            {"situation": "no opposing creature (e.g. cast as Pod / Chord / Neoform fodder or Cradle count)",
             "stormdrake": "no exchange; keeps a body", "gilded_drake": "sacrificed (up to one target, "
             "no exchange)", "edge": "Stormdrake (real fair floor)"},
            {"situation": "what the opponent receives",
             "stormdrake": "a flyer with hexproof from activated and triggered abilities (harder for THEM to "
                           "sacrifice/bounce with their own abilities)", "gilded_drake": "a 3/3 flyer",
             "edge": "context"},
        ],
        "tutor_access": "both are 2-MV blue creatures: Chord (X=2, instant), Survival (instant), Finale / Nature's "
                        "Rhythm (X=2), Pod from a 1-drop, Neoform from a 1-drop, Eldritch, DT / Vampiric / Seal / "
                        "Pact. Cutting Stormdrake halves the number of theft TARGETS, not the number of tutors "
                        "that reach theft.",
        "one_drake_enough": "with one Drake the category survives through tutors (the same ~11 tutors still "
                            "reach Gilded), but a fair-floor theft card that never bricks is replaced by one "
                            "that is sacrificed when there is no target and fails if the target escapes.",
    },
    "Colossal Skyturtle": {
        "cost": "{4}{G}{G}{U} enchantment creature (7 MV) — used for its channel abilities",
        "text": "Channel {2}{G}: return target card from your graveyard to your hand. Channel {1}{U}: return target "
                "creature to its owner's hand. Flying, ward {2}.",
        "roles": {
            "instant_bounce": "{1}{U}, an ACTIVATED ability from hand: cannot be hit by ordinary counterspells "
                              "(Stifle effects only). The only remaining creature bounce is Otawara ({3}{U} minus "
                              "legends) and Sink into Stupor ({1}{U}{U}, counterable spell).",
            "regrowth": "{2}{G}: the deck's ONLY regrowth — rebuys a spent Force of Will / Pact of Negation / "
                        "Silence / tutor, or a destroyed Devoted Druid / Swift / Effigy (now a measured solver "
                        "delivery option under the 008b rules).",
            "pitch": "blue (Force of Will, Force of Negation, Misdirection, Subtlety, Commandeer) AND green "
                     "(Endurance evoke) pitch fuel.",
            "survival_typing": "a creature card: Survival of the Fittest fetches it to hand at instant speed, so "
                               "Survival + Skyturtle is a repeatable bounce / regrowth access line.",
            "endurance_recursion": "Skyturtle can return Endurance (or anything) to hand; Endurance can put the "
                                   "graveyard back into the library. No deterministic win line in this deck "
                                   "depends on that loop; it is grind / anti-graveyard-hate value.",
            "tutor_x_caveat": "Chord / Finale / Nature's Rhythm put it onto the battlefield (7 MV) — its useful "
                              "modes need it in HAND (Survival, DT, Vampiric, Seal, Pact, Worldly).",
        },
        "what_is_lost": "the deck's only regrowth and its only uncounterable instant creature bounce.",
    },
}


def main():
    sv.enable_008b_rules()
    res = {"task": "SIM-DECKBUILD-008b", "artifact": "deckbuild008b_interaction_coverage.json",
           "evidence_type": "STRUCTURAL (Oracle-text categories, exact hypergeometric) + qualitative audit",
           "category_definitions": {k: sorted(v) for k, v in an.CATEGORIES.items()},
           "hypergeometric_note": "on the draw, no mulligan: 7 + t cards seen by turn t",
           "configs": {}, "cut_audit": CUT_AUDIT}
    v8 = bx.build("V8_frozen")
    for k in KEYS:
        deck = bx.build(k)
        cov = coverage(deck)
        lost = sorted(set(v8) - set(deck))
        added = sorted(set(deck) - set(v8))
        res["configs"][k] = {"adds_vs_v8": added, "cuts_vs_v8": lost, "coverage": cov}
    # Who reaches theft after the cut?
    b = bx.build("B_oracle_pact_seeker")
    res["theft_tutor_access"] = {k: {c: direct_tutors(bx.build(k), c) for c in an.CATEGORIES["creature_theft"]
                                     if c in bx.build(k)} for k in ("A_oracle_less", "B_oracle_pact_seeker")}
    res["proposed_build_losses"] = {cat: {"before_A": res["configs"]["A_oracle_less"]["coverage"][cat]["n_cards"],
                                          "after_B": res["configs"]["B_oracle_pact_seeker"]["coverage"][cat]["n_cards"]}
                                    for cat in an.CATEGORIES}
    assert "Gilded Drake" in b
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    for cat, d in res["proposed_build_losses"].items():
        print(f"{cat:40} A={d['before_A']} B={d['after_B']}")


if __name__ == "__main__":
    main()
