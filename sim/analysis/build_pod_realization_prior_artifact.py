"""SIM-001 MULL-006 section 9 / 28 — writes pod_realization_prior.json, the required artifact
recording the qualitative/ordinal pod-trigger realization model (see pod_realization_model.py for
the full rationale). This is a pure qualitative table, not derived from a simulated hand sample -
no --count/--seed arguments, unlike the other MULL-006 build scripts."""
import json
from pathlib import Path

from pod_archetypes import ARCHETYPES
from pod_realization_model import (
    ENGINE_DRIVER_DIMENSION, ARCHETYPE_BEHAVIOR_PROFILE, TAX_GATED_ENGINES, REALIZATION_ORDER,
    POD_REALIZATION_PROVENANCE, full_realization_table,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    result = {
        "phase": "SIM_001_MULL_006_POD_REALIZATION_PRIOR",
        "evidence_type": POD_REALIZATION_PROVENANCE,
        "note": (
            "EVERY value in this artifact is STRATEGIC_PRIOR_UNVALIDATED and stays that way until "
            "real multiplayer simulation/tournament calibration exists. No exact multiplayer "
            "trigger rate is fabricated anywhere in this artifact - only ordinal VERY_HIGH/HIGH/"
            "MODERATE/LOW/UNKNOWN labels, per the assignment's explicit instruction. This is a "
            "separate, ADDITIVE modifier layer - it does not rewrite engine_strength_prior.py's "
            "intrinsic strength table, and pod_archetypes.py (MULL-005's existing archetype work) "
            "is reused, not modified."
        ),
        "realization_order_best_first": REALIZATION_ORDER,
        "tracked_engines": sorted(ENGINE_DRIVER_DIMENSION),
        "engine_driver_dimension": ENGINE_DRIVER_DIMENSION,
        "tax_gated_engines": sorted(TAX_GATED_ENGINES),
        "tax_gated_engines_note": (
            "Rhystic Study, Mystic Remora, Esper Sentinel, and Smothering Tithe all have a real "
            "'unless that player pays {N}' clause - a high-tax-payment-ability archetype denies "
            "realization even when the driver dimension itself is high, so these four are "
            "additionally penalized by tax_payment_ability. Faerie Mastermind, Archivist of Oghma, "
            "Heartwood Storyteller, and Runic Armasaur have no such clause and are not penalized."
        ),
        "archetype_behavior_profiles": ARCHETYPE_BEHAVIOR_PROFILE,
        "archetype_behavior_profile_note": (
            "Each archetype's density values (LOW=0/MODERATE=1/HIGH=2) are hand-derived FROM "
            "pod_archetypes.ARCHETYPES's existing primary_resource_axis/interaction_demand/speed "
            "descriptions (already an established MULL-005 strategic prior, not new invention) - "
            "see pod_realization_model.py's module docstring for the per-archetype reasoning."
        ),
        "engine_x_archetype_realization_table": full_realization_table(),
        "archetype_source_descriptions": {
            arch: {
                "speed": spec["speed"],
                "primary_resource_axis": spec["primary_resource_axis"],
                "interaction_demand": spec["interaction_demand"],
            } for arch, spec in ARCHETYPES.items()
        },
        "example_relationships": {
            "runic_armasaur_favors_creature_heavy_pods": (
                "Kinnan/Rog-Thras-Tree-Farm/Tayam (creature_density=HIGH) realize HIGH; RogSi/"
                "Blue Farm/stax_heavy (creature_density=LOW) realize LOW - Armasaur punishes "
                "creatures entering the battlefield, so it is essentially dead against spell-"
                "heavy control/combo pods."
            ),
            "archivist_favors_tutor_dense_pods": (
                "RogSi/Sisay (tutor_search_density=HIGH) realize HIGH; Tayam/Etali (tutor_search_"
                "density=LOW) realize LOW - Archivist triggers on library searches specifically."
            ),
            "tax_gated_engines_punished_by_mana_rich_pods": (
                "Rhystic Study/Mystic Remora/Esper Sentinel/Smothering Tithe all realize LOWER "
                "against Kinnan/Blue Farm/Etali/Tivit (tax_payment_ability=HIGH) than against "
                "RogSi/stax_heavy (tax_payment_ability=LOW), even when noncreature spell density "
                "is comparable or higher - a mana-rich pod can simply pay through the tax."
            ),
        },
        "limitations": [
            "This model has NOT been validated against any real multiplayer data - it is a "
            "structural, disclosed strategic prior only.",
            "Heartwood Storyteller's driver dimension (noncreature_spell_density, treated as a "
            "proxy for single-target-spell density) is a coarser characterization than its real "
            "Oracle trigger condition - see pod_realization_model.py's docstring.",
            "Archetype behavior profiles are hand-authored ordinal judgments, not measured spell/"
            "tutor/creature counts from any real decklist or game log.",
            "The tax-payment penalty model is linear and uniform across all four tax-gated "
            "engines - real per-card tax amounts ({1} for Rhystic, an escalating {X} for Remora, "
            "{X}=power for Sentinel, {2} for Tithe) are not separately modeled.",
        ],
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "pod_realization_prior.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
