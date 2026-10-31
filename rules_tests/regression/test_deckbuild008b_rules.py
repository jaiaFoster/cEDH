"""SIM-DECKBUILD-008b regression tests: the new rules / metric assumptions behind the
Oracle + Tainted Pact + Spellseeker follow-up.

Pins: the fair Tainted Pact tutor and its exile-above exposure rule, Colossal Skyturtle channel regrowth,
the fair-Pact search arithmetic, and the Standalone Card Quality (brick) classifier.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

import deckbuild008_cards as dc  # noqa: E402
import deckbuild008_solver as sv  # noqa: E402
import deckbuild008b_analysis as an  # noqa: E402
from deckbuild008_solver import Perm, Snapshot, solve  # noqa: E402

BASE, _ = dc.frozen_baseline()
ORACLE, PACT, CONSULT, SEEKER = an.ORACLE, an.PACT, an.CONSULT, an.SEEKER
DUALS = ["Underground Sea", "Tundra", "Tropical Island", "Scrubland", "Bayou", "Savannah", "Volcanic Island"]


def snap(hand, bf, extra=(), gy=(), timing="main", land_drop=False, cmd=None):
    names = set(hand) | {p.name for p in bf} | set(gy)
    lib = [c for c in BASE + list(extra) if c not in names]
    if cmd is None:
        cmd = set(dc.COMMANDERS) - {p.name for p in bf}
    return Snapshot(list(hand), list(bf), lib, list(gy), cmd, {}, land_drop, timing, 3)


def L(*names):
    return [Perm(n) for n in names]


def lands(n):
    pool = ["Underground Sea", "Tundra", "Tropical Island", "Scrubland", "Bayou", "Savannah", "Command Tower",
            "City of Brass", "Mana Confluence"]
    return L(*pool[:n])


def with_rules(on):
    sv.enable_008b_rules(fair_pact=on, skyturtle=on)


# ---- rule flags ---------------------------------------------------------------------------------

def test_008b_rules_default_off_and_toggle():
    with_rules(False)
    assert PACT not in dc.TUTORS and not sv.FAIR_PACT_TUTOR and not sv.SKYTURTLE_REGROWTH
    with_rules(True)
    assert dc.TUTORS[PACT]["find"] == "any" and dc.TUTORS[PACT]["speed"] == "instant"
    assert dc.TUTORS[PACT]["dest"] == "hand"
    with_rules(False)
    assert PACT not in dc.TUTORS


def test_tainted_pact_text_is_singleton_safe():
    t = dc.card(PACT)["text"]
    assert "two cards with the same name" in t and dc.card(PACT)["cost"] == "{1}{B}"
    names = [c for c in BASE if not dc.is_land(c) or True]
    assert len(names) == len(set(names))  # singleton, no basics: Pact never stops on a duplicate


# ---- fair Pact as a line tutor --------------------------------------------------------------

def test_fair_pact_finds_effigy_for_druid_bowmasters_kill():
    """Druid on board, Bowmasters + Mastermind on board: Pact -> Effigy (copy Druid) = infinite G+U ->
    Mastermind draws / Bowmasters pings. Every outlet is already on the battlefield, so nothing Pact exiles
    can break the line: deterministic."""
    bf = L(sv.DRUID, sv.BOWMASTERS, sv.MASTERMIND, sv.THRASIOS) + lands(7)
    s = snap([PACT], bf)
    with_rules(False)
    assert not solve(s)["det"]
    with_rules(True)
    r = solve(s, want=("all",))
    assert r["det"] and "inf_bowmasters" in r["families"] and PACT in r["used_cards"]
    with_rules(False)


def test_fair_pact_line_exposed_when_outlet_still_in_library():
    """Pact -> Swift (Druid on board) makes infinite G, but the Oracle outlet would be drawn from the library
    AFTER Pact has exiled everything above Swift: not deterministic ("pact_exposed")."""
    bf = L(sv.DRUID, sv.THRASIOS) + lands(6)
    s = snap([PACT], bf, extra=[ORACLE])
    with_rules(True)
    r = solve(s, want=("all",))
    assert not r["det"]
    assert "pact_exposed" in r["families"] and r["nondet"]
    with_rules(False)


def test_oracle_pact_partner_line_unchanged_by_fair_rule():
    bf = lands(4)
    s = snap([ORACLE, PACT], bf)
    for on in (False, True):
        with_rules(on)
        r = solve(s)
        assert r["det"] and "oracle_pact" in r["families"]
    with_rules(False)


def test_pact_cannot_be_both_tutor_and_oracle_partner():
    """One Pact: if it is spent fetching Oracle it cannot also be the exile-library partner."""
    bf = lands(5)
    s = snap([PACT], bf, extra=[ORACLE])
    with_rules(True)
    r = solve(s, want=("all",))
    assert "oracle_pact" not in r["families"]
    with_rules(False)


# ---- Skyturtle channel regrowth ---------------------------------------------------------------

def test_skyturtle_regrows_effigy_for_infinite():
    bf = L(sv.DRUID, sv.BOWMASTERS, sv.MASTERMIND, sv.THRASIOS) + lands(8)
    s = snap([an.SKYTURTLE], bf, gy=[sv.EFFIGY])
    with_rules(False)
    assert not solve(s)["det"]
    with_rules(True)
    r = solve(s, want=("all",))
    assert r["det"] and an.SKYTURTLE in r["used_cards"]
    with_rules(False)


def test_skyturtle_channel_texts():
    t = dc.card(an.SKYTURTLE)["text"]
    assert "Channel — {2}{G}, Discard this card: Return target card from your graveyard to your hand." in t
    assert "Channel — {1}{U}, Discard this card: Return target creature to its owner's hand." in t
    assert dc.is_blue(an.SKYTURTLE) and dc.is_green(an.SKYTURTLE) and dc.is_creature(an.SKYTURTLE)


# ---- Spellseeker / tutor topology -------------------------------------------------------------------

def test_spellseeker_targets_include_pact_not_oracle():
    assert dc.tutor_can_find(SEEKER, PACT) and dc.tutor_can_find(SEEKER, CONSULT)
    assert not dc.tutor_can_find(SEEKER, ORACLE)
    for t in ("Demonic Tutor", "Vampiric Tutor", "Enlightened Tutor", "Silence", "Crop Rotation",
              "Flusterstorm", "Swan Song", "Imperial Seal", "Finale of Devastation", "Nature's Rhythm"):
        assert dc.tutor_can_find(SEEKER, t), t
    assert not dc.tutor_can_find(SEEKER, "Force of Will")  # MV 5


# ---- fair-Pact search arithmetic ----------------------------------------------------------------------

def test_pact_walk_real_order():
    lib = ["a", "b", ORACLE, "hit1", "c", "hit2"]
    exiled, hit = an.pact_walk(lib, {"hit1", "hit2"})
    assert hit == "hit1" and exiled == ["a", "b", ORACLE]
    exiled, hit = an.pact_walk(lib, {"zzz"})
    assert hit is None and exiled == lib  # no acceptable card: the whole library is exiled


def test_pact_closed_form_matches_simulation():
    rng = random.Random(1)
    N, k = 80, 6
    lib = [f"x{i}" for i in range(N - k)] + [f"h{i}" for i in range(k)]
    acc = {f"h{i}" for i in range(k)}
    ex_tot = spec = 0
    trials = 20000
    for _ in range(trials):
        rng.shuffle(lib)
        e, _h = an.pact_walk(lib, acc)
        ex_tot += len(e)
        spec += "x0" in e
    cf = an.pact_closed_form(N, k)
    assert abs(ex_tot / trials - cf["expected_exiled"]) < 0.25
    assert abs(spec / trials - cf["p_specific_card_exiled"]) < 0.01


# ---- brick classifier ---------------------------------------------------------------------------------

def _cls(card, hand, bf, land_drop=False, extra=()):
    s = snap(hand, bf, extra=extra, land_drop=land_drop)
    return an.classify_card(card, s, an.units_of(s), set())


def test_castable_ignores_x_for_non_x_cards():
    assert an.castable({dc.C: 4}, sv.EFFIGY, x=1)
    assert not an.castable({dc.C: 3}, sv.EFFIGY, x=1)


def test_oracle_castable_is_not_development():
    best, roles = _cls(ORACLE, [ORACLE], lands(3))
    assert "development" not in roles and best == "secondary" and "body" in roles
    best, roles = _cls(ORACLE, [ORACLE], [])
    assert best == "stranded"


def test_oracle_with_pact_in_hand_is_combo_pair():
    best, roles = _cls(ORACLE, [ORACLE, PACT], [])
    assert best == "material" and "combo_pair" in roles


def test_pact_is_a_fair_tutor_not_a_brick():
    best, roles = _cls(PACT, [PACT], lands(2))
    assert best == "material" and "fair_tutor" in roles
    best, _ = _cls(PACT, [PACT], [])
    assert best == "stranded"  # uncastable right now


def test_consult_fair_mode_is_low_floor():
    best, roles = _cls(CONSULT, [CONSULT], lands(2))
    assert best == "secondary" and "fair_risky" in roles and "fair_tutor" not in roles


def test_spellseeker_castable_is_material_tutor():
    best, roles = _cls(SEEKER, [SEEKER], lands(3))
    assert best == "material" and "fair_tutor" in roles


def test_skyturtle_channel_counts_as_held_interaction():
    best, roles = _cls(an.SKYTURTLE, [an.SKYTURTLE], lands(2))
    assert best == "material" and "interaction_held" in roles


def test_first_land_is_land_drop_second_is_extra():
    hand = ["Tundra", "Bayou"]
    assert _cls("Tundra", hand, [], land_drop=True)[1] >= {"land_drop"}
    assert "extra_land" in _cls("Bayou", hand, [], land_drop=True)[1]


def test_free_counters_need_pitch():
    bfn, bf = set(), []
    assert not an.free_castable("Force of Will", ["Force of Will"], bfn, bf, {})
    assert an.free_castable("Force of Will", ["Force of Will", "Spellseeker"], bfn, bf, {})
    assert an.free_castable("Pact of Negation", ["Pact of Negation"], bfn, bf, {})
    assert not an.free_castable("Fierce Guardianship", ["Fierce Guardianship"], bfn, bf, {})
    assert an.free_castable("Fierce Guardianship", ["Fierce Guardianship"], {sv.THRASIOS}, bf, {})
