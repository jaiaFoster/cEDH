"""SIM-ROGFARM-001 — Stage 1 machine-readable companion to results/solo_baseline/
rogfarm001_report_stage1.md. Re-derives the deck hashes/counts/diff assertions programmatically
(never hand-typed) and records the package-quality hard-failure count and rules-assertion summary
for audit-log purposes (Section 28: "Preserve complete machine-readable results and audit logs").
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))
sys.path.insert(0, str(REPO_ROOT))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402

DECKLISTS = REPO_ROOT / "data" / "decklists"

SYNERGY_ONLY_BLANKS_ADDED = []  # see rogfarm001_report_stage1.md section 4 - zero found

RULES_ASSERTIONS_VERIFIED = [
    "Fierce Guardianship: free with any 1 commander controlled, counters noncreature spells only.",
    "Deadly Rollick: free with any 1 commander controlled, exiles target creature.",
    "Flare of Duplication: alt cost = sacrifice a nontoken RED creature (Rograkh/Birgi both qualify).",
    "Hexing Squelcher: uncounterable self + your other spells uncounterable + Ward 2 on your other creatures.",
    "Narset, Parter of Veils: caps EACH OPPONENT at 1 card/turn (hard cap, not a replacement); controller unaffected.",
    "Notion Thief: TRUE replacement - redirects every non-first-per-draw-step opponent draw to controller (0 opponent cards from a wheel).",
    "Orcish Bowmasters: triggers once PER CARD an opponent draws beyond their first that turn (repeatable, not capped).",
    "Faerie Mastermind: triggers ONCE on an opponent's literal 2nd card of the turn only - not a per-card trigger.",
    "Payoff removed before wheel resolves -> wheel resolves with zero asymmetry (continuous effect requires source on battlefield).",
    "Multiple replacement effects -> the AFFECTED PLAYER chooses which applies (CR 616.1).",
    "Clone + legend rule: per-player: an opponent's clone of a legendary payoff doesn't violate OUR legend rule.",
    "Underworld Breach escape = mana cost + exile 3 OTHER graveyard cards; net -4 graveyard cards per LED+BrainFreeze loop.",
    "Wheel of Fortune/Windfall are discard-based -> REFILL Breach graveyard fuel.",
    "Timetwister shuffles hand+graveyard+library together -> ERASES Breach graveyard fuel (opposite effect).",
    "Will of the Jeskai: optional per-player 5-card wheel OR graveyard-flashback mode - a third distinct wheel type.",
]


def main():
    decks = {}
    for version in ("rogsi-valley-forge-2026-v1", "rogfarm-r1-minimal-v1", "bluefarm-control-2026-v1"):
        payload = json.loads((DECKLISTS / f"{version}.json").read_text(encoding="utf-8"))
        recomputed = compute_deck_hash(payload["commanders"], payload["cards"])
        assert recomputed == payload["deck_hash"]
        decks[version] = {
            "deck_hash": payload["deck_hash"], "commanders": payload["commanders"],
            "card_count": len(payload["cards"]),
        }

    stock_names = {c["name"] for c in json.loads((DECKLISTS / "rogsi-valley-forge-2026-v1.json").read_text())["cards"]}
    r1_names = {c["name"] for c in json.loads((DECKLISTS / "rogfarm-r1-minimal-v1.json").read_text())["cards"]}
    removed = sorted(stock_names - r1_names)
    added = sorted(r1_names - stock_names)

    out = {
        "phase": "SIM_ROGFARM_001_STAGE1_REPORT",
        "evidence_type": "static_probability",
        "deck_hashes": decks,
        "r1_diff": {"removed": removed, "added": added, "removed_count": len(removed), "added_count": len(added)},
        "package_audit": {
            "synergy_only_blanks_among_added_cards": SYNERGY_ONLY_BLANKS_ADDED,
            "synergy_only_blank_count": len(SYNERGY_ONLY_BLANKS_ADDED),
            "hard_failure_threshold": 2,
            "hard_failure_gate": "PASS" if len(SYNERGY_ONLY_BLANKS_ADDED) <= 2 else "FAIL",
        },
        "rules_assertions_verified": RULES_ASSERTIONS_VERIFIED,
        "stage2_status": "NOT_STARTED - disclosed scope, see report's final section",
    }
    out_path = REPO_ROOT / "results" / "solo_baseline" / "rogfarm001_stage1_report.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(out["package_audit"], indent=2))


if __name__ == "__main__":
    main()
