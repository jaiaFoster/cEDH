"""SIM-001 MULL-006 section 3 / 28 — writes engine_strength_prior.json, the required artifact
recording the pilot-supplied intrinsic engine-strength prior (see engine_strength_prior.py for the
full rationale and the FAERIE MASTERMIND / BIRTHING POD correction notes)."""
import json
from pathlib import Path

from engine_strength_prior import (
    ENGINE_STRENGTH_PRIOR, ENGINE_STRENGTH_RANK, STRENGTH_ORDER, STRENGTH_PROVENANCE,
    POD_ACTIVATION_COST, SURVIVAL_ACTIVATION_COST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    result = {
        "phase": "SIM_001_MULL_006_ENGINE_STRENGTH_PRIOR",
        "evidence_type": STRENGTH_PROVENANCE,
        "strength_order_strongest_first": STRENGTH_ORDER,
        "strength_rank": ENGINE_STRENGTH_RANK,
        "engine_strength_prior": ENGINE_STRENGTH_PRIOR,
        "functional_gates": {
            "Birthing Pod": (
                f"deployed (on battlefield, untapped) AND legal fodder (another creature on the "
                f"battlefield) AND the {POD_ACTIVATION_COST} activation currently payable. Does "
                f"NOT additionally verify the resulting found card is a genuine upgrade - a "
                f"disclosed simplification (see engine_strength_prior.functional_pod docstring)."
            ),
            "Survival of the Fittest": (
                f"deployed AND a discardable creature card actually in hand AND the "
                f"{SURVIVAL_ACTIVATION_COST} activation currently payable."
            ),
        },
        "deployment_required_for_every_entry": (
            "Every engine in this table requires being ON THE BATTLEFIELD, including Faerie "
            "Mastermind - the FAERIE MASTERMIND CORRECTION removes the ACTIVATION-support "
            "requirement MULL-005R imposed (its {3}{U} ability need not be payable), it does NOT "
            "remove the deployment requirement. A card sitting in hand has no live ability at all."
        ),
        "abhorrent_oculus_excluded": (
            "Abhorrent Oculus is deliberately NOT in this table - it remains a separate PREMIER "
            "DESTINATION per assignment section 3, never folded into the resource-engine strength "
            "ranking. Its trajectory quality is determined by deployment turn/route/resources "
            "consumed/resulting board/follow-up/resilience/agency, not an engine-strength label."
        ),
        "faerie_mastermind_correction": (
            "MULL-005R (REALIZE-001) required Mastermind's {3}{U} activated ability to be "
            "currently payable before granting ANY Tier-C credit, on the reasoning that its "
            "passive trigger is structurally unmeasurable by a solo/no-opponent model. MULL-006 "
            "explicitly overrides this for ENGINE-STRENGTH purposes only: Mastermind is proxy-"
            "credited as strength A on deployment alone, the same disclosed-proxy treatment "
            "already given to Rhystic Study/Mystic Remora/Smothering Tithe (equally unmeasurable "
            "opponent-triggered engines - TITHE-001's consistency argument, now extended). The "
            "activated ability remains real additional utility, not a prerequisite for the label. "
            "This does NOT retroactively change MULL-005R's own committed trajectory-tier grading "
            "(grade_trajectory()/trajectory_metrics.py's _tier_c_supported are untouched) - it is "
            "a new, additive strength-prior layer alongside the existing tier system, per the "
            "assignment's instruction to keep intrinsic strength and the legacy grading separate "
            "while the two are tested together (sections 3-5)."
        ),
        "note": (
            "This is a PILOT-SUPPLIED STRATEGIC PRIOR, not an empirical finding - never cite this "
            "ranking itself as 'simulation-proven'. Only its INTERACTIONS with deployment speed, "
            "seat, draw dependence, resilience, and pod context (tested in later MULL-006 "
            "artifacts) are simulation-derived."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "engine_strength_prior.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
