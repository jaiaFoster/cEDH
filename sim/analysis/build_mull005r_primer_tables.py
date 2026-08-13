"""SIM-001 MULL-005R section 25 — primer quick-reference table + pod-guidance table, corrected.

Thin wrapper over build_mull005_primer_tables.py: build_quick_reference_table()/
build_pod_guidance_table() and the ARCHETYPES/POD_MODIFIERS overlay are unchanged this phase (see
task #97's audit) - only the hand-size threshold SOURCE needs to point at the re-derived
mull005r_hand_size_thresholds.json (task #96) instead of MULL-005's original file. Monkeypatches
the one private function that reads that path rather than duplicating ~100 lines of unchanged
table-construction logic.
"""
import json
from pathlib import Path

import build_mull005_primer_tables as _orig

REPO_ROOT = Path(__file__).resolve().parents[2]


def _neutral_threshold_by_size_r():
    path = REPO_ROOT / "results" / "solo_baseline" / "mull005r_hand_size_thresholds.json"
    data = json.loads(path.read_text())
    table = data["keep_thresholds_by_assumed_mulligan_card_cost"]["1.0"]
    return {int(size): row["keep_at_or_above_tier"] for size, row in table.items()}


def main():
    _orig._neutral_threshold_by_size = _neutral_threshold_by_size_r
    quick_ref = _orig.build_quick_reference_table()
    pod_guidance = _orig.build_pod_guidance_table()

    result = {
        "phase": "SIM_001_MULL_005R_PRIMER_TABLES_CORRECTED",
        "primer_quick_reference_table": quick_ref,
        "pod_guidance_table": pod_guidance,
        "notes": (
            "primer_quick_reference_table's hand_size axis is SIMULATED (mull005r_hand_size_"
            "thresholds.json, the MULL-005R re-derivation - task #96). Its pod_speed axis is a "
            "disclosed qualitative adjustment, NOT simulated, except the MEDIUM row which applies "
            "no adjustment - unchanged this phase per task #97's audit (pod_archetypes.py's "
            "algorithm itself was preserved; only its real, simulated inputs needed correcting, "
            "which the CMDR-003 fix and this threshold rebase address). pod_guidance_table is "
            "entirely STRATEGIC_PRIOR_UNVALIDATED and contains no simulated percentages anywhere."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mull005r_primer_tables.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"quick_reference rows: {len(quick_ref)}")
    print(f"pod_guidance rows: {len(pod_guidance)}")


if __name__ == "__main__":
    main()
