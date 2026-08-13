"""SIM-001 MULL-006 section 0 — subject/provenance record.

Confirms the frozen subject is UNCHANGED from MULL-005R before any MULL-006 simulation begins, per
the assignment's explicit "if the frozen subject differs, STOP and report" instruction. Run first;
every other MULL-006 artifact cites this file's deck_hash for cross-checking.
"""
import json
import subprocess
from pathlib import Path

from opening_hand_model import load_deck_cards, deck_provenance_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
MULL005R_DECK_HASH = "4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a"
MULL005R_DECK_VERSION = "tymna-thrasios-treefarm-v1"


def main():
    payload, cards = load_deck_cards()
    prov = deck_provenance_fields(payload)

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    oracle_snapshots = sorted(p.name for p in (REPO_ROOT / "data" / "cards_cache").iterdir() if p.is_dir())

    discrepancy = (
        prov["subject_deck_hash"] != MULL005R_DECK_HASH
        or prov["subject_deck_version"] != MULL005R_DECK_VERSION
    )

    result = {
        "phase": "SIM_001_MULL_006_PROVENANCE",
        **prov,
        "mull005r_reference_deck_hash": MULL005R_DECK_HASH,
        "mull005r_reference_deck_version": MULL005R_DECK_VERSION,
        "subject_matches_mull005r": not discrepancy,
        "git_commit": commit,
        "git_branch": branch,
        "oracle_rules_snapshot": oracle_snapshots,
        "mull005r_policy_version": "trajectory_policies.py @ commit 8ba0e33 (TRAJECTORY_SIMPLE_R/TREE_R/MACHINE_R, mull005r_hand_size_thresholds.json)",
        "mull006_policy_version": "in progress - this commit",
        "mull005r_regression_gate_status": json.loads((REPO_ROOT / "results" / "solo_baseline" / "mull005r_regression_gate.json").read_text())["gate_status"],
        "note": (
            "Every MULL-006 artifact must cite subject_deck_hash from this file. seeds/sample_"
            "sizes/seat/play-draw/pod assumptions/search limits/heuristic priors are recorded "
            "per-artifact in that artifact's own JSON (this file only fixes the DECK identity, "
            "which is shared across all of them) - see each artifact's own provenance block."
        ),
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "mull006_provenance.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"subject_matches_mull005r: {result['subject_matches_mull005r']}")
    if discrepancy:
        print("STOP: subject deck differs from MULL-005R's recorded subject - do not proceed.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
