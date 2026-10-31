"""SIM-DECKBUILD-008 regression tests: every rules assumption / combo topology that moves a result.

Each test pins an Oracle-text-derived behaviour of sim/analysis/deckbuild008_{cards,solver,goldfish}.py.
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

import deckbuild008_cards as dc  # noqa: E402
import deckbuild008_solver as sv  # noqa: E402
from deckbuild008_solver import Perm, Snapshot, solve  # noqa: E402
from deckbuild008_goldfish import hand_features, pay_take  # noqa: E402

BASE, BASE_HASH = dc.frozen_baseline()
PKG = ["Thassa's Oracle", "Demonic Consultation", "Tainted Pact"]


def snap(hand, bf, extra=(), gy=(), timing="main", land_drop=False, cmd=None):
    names = set(hand) | {p.name for p in bf} | set(gy)
    lib = [c for c in BASE + list(extra) if c not in names]
    if cmd is None:
        cmd = set(dc.COMMANDERS) - {p.name for p in bf}
    return Snapshot(list(hand), list(bf), lib, list(gy), cmd, {}, land_drop, timing, 3)


def L(*names):
    return [Perm(n) for n in names]


# ---- frozen deck / provenance -----------------------------------------------------------------

def test_frozen_baseline_hash_and_size():
    assert len(BASE) == 98 and len(set(BASE)) == 98
    assert BASE_HASH == "bcc611f4d4d9804a3cdec581ea25b9c8224b75177648a85614ab1a470145de75"


def test_registrations_match_moxfield_v8_and_borne_absent():
    d = json.loads((REPO_ROOT / "data/decklists/tymna-thrasios-creature-factory-deckbuild008-v1.json").read_text())
    regs = d["source"]["reconciliation"]["topdeck_registrations"]
    assert set(regs) == {"azms-cedh-qualifier-8", "eye-of-the-tiger-lion-cedh-tournament-win-a-lions-eye"}
    assert all(r["identical_to_moxfield_v8"] for r in regs.values())
    assert "Borne Upon a Wind" not in BASE
    assert "Strix Serenade" in BASE and "Deathrite Shaman" in BASE


def test_land_density_counts_soporific_springs():
    assert dc.is_land("Sink into Stupor // Soporific Springs")
    assert sum(dc.is_land(c) for c in BASE) == 28


# ---- mana rules ------------------------------------------------------------------------------------

def test_deathrite_is_not_a_mana_ability_and_needs_a_land_in_a_graveyard():
    assert "target land card" in dc.card("Deathrite Shaman")["text"]
    assert "Deathrite Shaman" in dc.NOT_A_MANA_ABILITY
    s = snap([], L("Kinnan, Bonder Prodigy", "Badgermole Cub", "Deathrite Shaman"))
    assert sum(sv.board_units(s).values()) == 0  # empty graveyard: no mana at all
    s = snap([], L("Kinnan, Bonder Prodigy", "Badgermole Cub", "Deathrite Shaman"), gy=["Flooded Strand"])
    assert sv.board_units(s) == Counter({dc.ANY: 1})  # one mana, no Kinnan/Badgermole bonus


def test_kinnan_and_badgermole_amplify_true_dorks():
    s = snap([], L("Kinnan, Bonder Prodigy", "Badgermole Cub", "Birds of Paradise"))
    # Birds: 1 any + Kinnan 1 any + Badgermole 1 G
    assert sum(sv.board_units(s).values()) == 3
    s = snap([], L("Kinnan, Bonder Prodigy", "Sol Ring"))
    assert sv.board_units(s)[dc.C] == 3  # Sol Ring 2 + Kinnan 1 (nonland permanent)
    s = snap([], L("Badgermole Cub", "Sol Ring"))
    assert sv.board_units(s)[dc.C] == 2  # Badgermole only for creatures
    s = snap([], L("Kinnan, Bonder Prodigy", "Devoted Druid"))
    assert sv.board_units(s)[dc.G] == 4  # two taps -> two Kinnan triggers


def test_avacyns_pilgrim_amplified_unlike_deathrite():
    s = snap([], L("Kinnan, Bonder Prodigy", "Avacyn's Pilgrim"))
    assert sv.board_units(s)[dc.W] == 2


def test_devoted_druid_two_mana_and_summoning_sickness():
    assert sv.board_units(snap([], L("Devoted Druid")))[dc.G] == 2
    assert sum(sv.board_units(snap([], [Perm("Devoted Druid", sick=True)])).values()) == 0
    # Shang-Chi lets creature abilities ignore summoning sickness.
    s = snap([], [Perm("Devoted Druid", sick=True), Perm("Shang-Chi, Master of Kung Fu", sick=True)])
    assert sv.board_units(s)[dc.G] == 2


def test_mox_amber_not_functional_mana_in_mulligan_features():
    f = hand_features(["Mox Amber", "Tropical Island", "Rhystic Study", "Silence", "Swan Song",
                       "Force of Will", "Mystic Remora"], True)
    assert f["mana_total"] == 1


def test_pay_respects_colours_and_phyrexian():
    u = Counter({frozenset("UB"): 1, frozenset("GU"): 1, frozenset("WU"): 1})
    assert sv.pay(u, (dc.U, dc.U, dc.B), 0)
    assert not sv.pay(u, (dc.B, dc.B), 0)
    assert sv.pay(Counter({dc.C: 1}), (frozenset({"G", "P"}),), 1)  # Pod activation with life
    assert pay_take(Counter({dc.C: 2, dc.ANY: 1}), (dc.U,), 2) == Counter()


# ---- tutor topology -----------------------------------------------------------------------------------

def test_spellseeker_targets():
    for t in ("Demonic Consultation", "Tainted Pact", "Demonic Tutor", "Vampiric Tutor", "Enlightened Tutor",
              "Silence", "Crop Rotation", "Swan Song", "Flusterstorm", "Finale of Devastation",
              "Nature's Rhythm", "Neoform", "Pact of Negation"):
        assert dc.tutor_can_find("Spellseeker", t), t
    for t in ("Swift Reconfiguration", "Chord of Calling", "Eldritch Evolution", "Commandeer",
              "Fierce Guardianship", "Thassa's Oracle"):
        assert not dc.tutor_can_find("Spellseeker", t), t


def test_green_only_tutors_cannot_find_oracle_or_spellseeker():
    for tutor in ("Green Sun's Zenith", "Summoner's Pact"):
        assert not dc.tutor_can_find(tutor, "Thassa's Oracle")
        assert not dc.tutor_can_find(tutor, "Spellseeker")
        assert dc.tutor_can_find(tutor, "Devoted Druid")
        assert dc.tutor_can_find(tutor, "Hermit Druid")


def test_spellseeker_is_human_so_kinnan_cannot_find_it():
    assert "Human" in dc.card("Spellseeker")["type"]
    assert "Human" not in dc.card("Thassa's Oracle")["type"]


def test_pod_rungs():
    assert dc.tutor_can_find("Birthing Pod", "Thassa's Oracle", sac_mv=1)
    assert not dc.tutor_can_find("Birthing Pod", "Thassa's Oracle", sac_mv=2)
    assert dc.tutor_can_find("Birthing Pod", "Spellseeker", sac_mv=2)
    assert dc.tutor_can_find("Eldritch Evolution", "Hazel's Brewmaster", sac_mv=2)


def test_hermit_druid_mills_whole_library_no_basics():
    assert "basic land" in dc.card("Hermit Druid")["text"]
    assert not any("Basic" in dc.card(c)["type"] for c in BASE)


# ---- win lines --------------------------------------------------------------------------------------

def test_oracle_consult_needs_uub():
    assert solve(snap(PKG[:2], L("Underground Sea", "Tropical Island", "Tundra"), PKG))["det"]
    assert not solve(snap(PKG[:2], L("Underground Sea", "Tropical Island"), PKG))["det"]
    assert not solve(snap(PKG[:2], L("Bayou", "Savannah", "Scrubland"), PKG))["det"]  # no blue


def test_pod_into_oracle_with_consult_is_sorcery_speed_only():
    bf = L("Underground Sea", "Tropical Island", "Savannah", "Birthing Pod", "Delighted Halfling")
    r = solve(snap(["Demonic Consultation"], bf, PKG))
    assert r["det"] and "oracle_consult" in r["families"]
    bf = L("Underground Sea", "Tropical Island", "Savannah", "Birthing Pod", "Delighted Halfling", "High Fae Trickster")
    r = solve(snap(["Demonic Consultation"], bf, PKG, timing="instant"))
    assert not r["det"]  # Pod: activate only as a sorcery; Chord etc. not in hand


def test_spellseeker_bridge_finds_consult():
    bf = L("Underground Sea", "Tropical Island", "Tundra", "Bayou", "Scrubland", "Savannah")
    r = solve(snap(["Spellseeker", "Thassa's Oracle"], bf, PKG + ["Spellseeker"]))
    assert r["det"] and r["min_cards"] == 3


def test_instant_window_needs_a_flash_enabler_for_oracle():
    bf = L("Underground Sea", "Tropical Island", "Tundra")
    assert not solve(snap(PKG[:2], bf, PKG, timing="instant"))["det"]
    assert solve(snap(PKG[:2], bf + L("Teferi, Mage of Zhalfir"), PKG, timing="instant"))["det"]
    assert solve(snap(PKG[:2], bf + L("High Fae Trickster"), PKG, timing="instant"))["det"]
    # Emergence Zone: {1}, T, sacrifice -> needs one more mana AND loses its own {C}
    assert not solve(snap(PKG[:2], bf + L("Emergence Zone"), PKG, timing="instant"))["det"]
    assert solve(snap(PKG[:2], bf + L("Emergence Zone", "Sol Ring"), PKG, timing="instant"))["det"]


def test_top_tutor_needs_thrasios_draw():
    bf = L("Underground Sea", "Tropical Island", "Tundra", "Bayou", "Scrubland", "Savannah")
    hand = ["Vampiric Tutor", "Thassa's Oracle"]
    # Vampiric (B) + Thrasios draw (4) + Consult (B) + Oracle (UU) = 8 > 6 lands
    assert not solve(snap(hand, bf + L("Thrasios, Triton Hero"), PKG))["det"]
    assert solve(snap(hand, bf + L("Thrasios, Triton Hero", "Training Grounds"), PKG))["det"]  # {2} draw: 6
    assert solve(snap(hand, bf + L("Thrasios, Triton Hero", "Sol Ring"), PKG))["det"]  # 8 mana exactly


def test_hermit_requires_non_sick_or_shang_chi():
    lands = L("Underground Sea", "Tropical Island", "Bayou")
    assert solve(snap(["Thassa's Oracle"], lands + L("Hermit Druid"), ["Thassa's Oracle", "Hermit Druid"]))["det"]
    assert not solve(snap(["Thassa's Oracle"], lands + [Perm("Hermit Druid", sick=True)],
                          ["Thassa's Oracle", "Hermit Druid"]))["det"]
    assert solve(snap(["Thassa's Oracle"], lands + [Perm("Hermit Druid", sick=True),
                                                    Perm("Shang-Chi, Master of Kung Fu", sick=True)],
                      ["Thassa's Oracle", "Hermit Druid", "Shang-Chi, Master of Kung Fu"]))["det"]


def test_witch_requires_a_discard():
    lands = L("Underground Sea", "Tropical Island", "Bayou", "Scrubland")
    assert solve(snap(["Thassa's Oracle", "Swan Song"], lands + L("Divining Witch"),
                      ["Thassa's Oracle", "Divining Witch"]))["det"]
    assert not solve(snap(["Thassa's Oracle"], lands + L("Divining Witch"),
                          ["Thassa's Oracle", "Divining Witch"]))["det"]


def test_druid_swift_converts_through_thrasios_and_oracle():
    bf = L("Savannah", "Tropical Island", "Scrubland", "Thrasios, Triton Hero")
    hand = ["Devoted Druid", "Swift Reconfiguration"]
    r = solve(snap(hand, bf, PKG))
    assert "inf_oracle" in r["families"]
    # Without Oracle in the deck, the deterministic kill needs the long Bowmasters chain.
    r0 = solve(snap(hand, bf))
    assert "inf_oracle" not in r0["families"]


def test_inf_oracle_requires_thrasios():
    bf = L("Savannah", "Tropical Island", "Scrubland")
    s = snap(["Devoted Druid", "Swift Reconfiguration"], bf, PKG, cmd=set())
    assert "inf_oracle" not in solve(s)["families"]


def test_effigy_copying_druid_supplies_infinite_blue():
    bf = L("Ancient Tomb", "Sol Ring", "Savannah", "Devoted Druid", "Thrasios, Triton Hero")
    s = snap(["Machine God's Effigy"], bf, PKG)
    s.library = [c for c in s.library if c not in ("Lotus Petal", "Mox Amber", "Chrome Mox", "Arcane Signet")]
    r = solve(s)
    assert "inf_oracle" in r["families"]


def test_tainted_pact_fair_mode_is_not_deterministic_access():
    # Pact alone with Oracle in library is not a deterministic win (Oracle would be exiled).
    bf = L("Underground Sea", "Tropical Island", "Tundra", "Bayou")
    assert not solve(snap(["Tainted Pact"], bf, PKG))["det"]


def test_protection_flags():
    bf = L("Underground Sea", "Tropical Island", "Tundra", "Scrubland")
    r = solve(snap(PKG[:2] + ["Silence"], bf, PKG))
    assert r["protected"] and r["shield"]
    r = solve(snap(PKG[:2], L("Underground Sea", "Tropical Island", "Tundra") + L("Grand Abolisher"), PKG))
    assert r["shield"]
    r = solve(snap(PKG[:2] + ["Force of Will", "Swan Song"], L("Underground Sea", "Tropical Island", "Tundra"), PKG))
    assert r["counter"]


# ---- census statistics ----------------------------------------------------------------------------

def test_fisher_and_census_exclude_subject():
    import build_deckbuild008_package_census as c
    assert abs(c.fisher_two_sided(5, 0, 0, 5) - 0.007937) < 1e-4
    assert c.fisher_two_sided(3, 3, 3, 3) == 1.0
    assert "bQ97iyjPFLUq4ZTFPgMhscb9PJG3" in c.SUBJECT_PILOT_IDS


def test_thrasios_cast_from_command_zone_needs_real_blue_before_dig():
    # Infinite G from Druid + Swift, Thrasios in the command zone, no blue source on board:
    # the dig cannot start, so Thrasios -> Oracle is unavailable.
    bf = L("Savannah", "Bayou", "Scrubland")
    hand = ["Devoted Druid", "Swift Reconfiguration"]
    s = snap(hand, bf, PKG)
    s.library = [c for c in s.library if c not in ("Lotus Petal", "Chrome Mox", "Elvish Spirit Guide")]
    assert "inf_oracle" not in solve(s)["families"]
    s = snap(hand, bf + L("Tundra"), PKG)
    assert "inf_oracle" in solve(s)["families"]


def test_veil_of_summer_counts_as_a_castable_shield():
    lands = L("Underground Sea", "Tropical Island", "Tundra")
    assert not solve(snap(PKG[:2] + ["Veil of Summer"], lands, PKG))["shield"]  # no spare G
    assert solve(snap(PKG[:2] + ["Veil of Summer"], lands + L("Bayou"), PKG))["shield"]
