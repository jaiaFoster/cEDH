"""SIM-001 MULL-006 section 9 — pod-trigger realization, new dimension #4.

Proves the qualitative/ordinal realization model is internally consistent (reuses
pod_archetypes.py's existing archetype set, never fabricates a number, always returns one of the
five required labels), the tax-gated-vs-not distinction is applied correctly, and a handful of
intuitive engine x archetype relationships hold (Runic Armasaur punishes creature-heavy pods;
Archivist of Oghma rewards tutor-dense pods; Rhystic Study/Remora/Sentinel are strongest against
low-tax-payment, spell-dense pods).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from pod_archetypes import ARCHETYPES  # noqa: E402
from pod_realization_model import (  # noqa: E402
    pod_trigger_realization, full_realization_table, TRACKED_POD_ENGINES, TAX_GATED_ENGINES,
    ENGINE_DRIVER_DIMENSION, ARCHETYPE_BEHAVIOR_PROFILE, REALIZATION_ORDER, REALIZATION_RANK,
    POD_REALIZATION_PROVENANCE,
)


def test_every_tracked_engine_has_a_driver_dimension():
    assert set(ENGINE_DRIVER_DIMENSION) == TRACKED_POD_ENGINES
    assert len(TRACKED_POD_ENGINES) == 8


def test_archetype_profiles_cover_every_existing_pod_archetype():
    # reuses pod_archetypes.py's existing archetype set exactly - no new archetypes invented.
    assert set(ARCHETYPE_BEHAVIOR_PROFILE) == set(ARCHETYPES)


def test_every_realization_value_is_a_known_label():
    table = full_realization_table()
    for engine, by_arch in table.items():
        for arch, label in by_arch.items():
            assert label in REALIZATION_ORDER


def test_unknown_engine_or_archetype_returns_unknown():
    assert pod_trigger_realization("Not A Real Engine", "RogSi") == "UNKNOWN"
    assert pod_trigger_realization("Rhystic Study", "Not A Real Archetype") == "UNKNOWN"


def test_tax_gated_engines_are_exactly_the_four_with_unless_pay_clauses():
    assert TAX_GATED_ENGINES == {"Rhystic Study", "Mystic Remora", "Esper Sentinel", "Smothering Tithe"}
    non_gated = TRACKED_POD_ENGINES - TAX_GATED_ENGINES
    assert non_gated == {"Faerie Mastermind", "Archivist of Oghma", "Heartwood Storyteller", "Runic Armasaur"}


def test_rhystic_remora_sentinel_share_identical_realization_per_archetype():
    # All three share the exact same driver dimension AND tax-gated status, so they must always
    # agree with each other archetype-for-archetype (a consistency check on the model, not a
    # claim that the three cards are identical in any other respect).
    for arch in ARCHETYPE_BEHAVIOR_PROFILE:
        r1 = pod_trigger_realization("Rhystic Study", arch)
        r2 = pod_trigger_realization("Mystic Remora", arch)
        r3 = pod_trigger_realization("Esper Sentinel", arch)
        assert r1 == r2 == r3


def test_runic_armasaur_favors_high_creature_density_archetypes():
    kinnan = pod_trigger_realization("Runic Armasaur", "Kinnan")     # creature_density=2
    rogsi = pod_trigger_realization("Runic Armasaur", "RogSi")       # creature_density=0
    assert REALIZATION_RANK[kinnan] < REALIZATION_RANK[rogsi]


def test_archivist_favors_high_tutor_density_archetypes():
    sisay = pod_trigger_realization("Archivist of Oghma", "Sisay")   # tutor_search_density=2
    tayam = pod_trigger_realization("Archivist of Oghma", "Tayam")   # tutor_search_density=0
    assert REALIZATION_RANK[sisay] < REALIZATION_RANK[tayam]


def test_tax_gated_engine_is_hurt_by_high_tax_payment_ability():
    # RogSi (tax_payment_ability=0) vs Etali (tax_payment_ability=2), holding the driver dimension
    # roughly comparable, should show the low-tax-ability archetype realizing MORE for a tax-gated
    # engine - the model must not ignore the "unless they pay" clause.
    low_tax_arch_score = pod_trigger_realization("Rhystic Study", "RogSi")
    high_tax_arch_score = pod_trigger_realization("Rhystic Study", "Etali")
    assert REALIZATION_RANK[low_tax_arch_score] < REALIZATION_RANK[high_tax_arch_score]


def test_non_tax_gated_engine_ignores_tax_payment_ability():
    # Faerie Mastermind has no "unless they pay" clause - its realization must depend only on
    # second_draw_density, never shift due to tax_payment_ability alone.
    import pod_realization_model as prm
    profile_a = dict(prm.ARCHETYPE_BEHAVIOR_PROFILE["RogSi"])
    profile_b = dict(profile_a)
    profile_b["tax_payment_ability"] = 2  # only the tax field differs
    prm.ARCHETYPE_BEHAVIOR_PROFILE["_test_variant"] = profile_b
    try:
        base = pod_trigger_realization("Faerie Mastermind", "RogSi")
        variant = pod_trigger_realization("Faerie Mastermind", "_test_variant")
        assert base == variant
    finally:
        del prm.ARCHETYPE_BEHAVIOR_PROFILE["_test_variant"]


def test_realization_order_is_worst_last():
    assert REALIZATION_ORDER == ["VERY_HIGH", "HIGH", "MODERATE", "LOW", "UNKNOWN"]
    for i in range(len(REALIZATION_ORDER) - 1):
        assert REALIZATION_RANK[REALIZATION_ORDER[i]] < REALIZATION_RANK[REALIZATION_ORDER[i + 1]]


def test_provenance_label_is_strategic_prior_unvalidated():
    assert POD_REALIZATION_PROVENANCE == "STRATEGIC_PRIOR_UNVALIDATED"
