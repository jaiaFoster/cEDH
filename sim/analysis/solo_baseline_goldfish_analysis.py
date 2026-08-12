"""SIM-001 SOLO BASELINE v1 — ENGINE-GOLDFISH empirical accessibility.

Reads results/solo_baseline/*-raw_snapshots.json (real XMage games, real
7-card opening hands - see results/solo_baseline/README.md for the
hand-dealing defect this depends on having been fixed) and computes, from
actual game state (not AI recognition), empirical accessibility rates
comparable to the STATIC/COMBINATORIAL layer's predictions.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INTERACTIONS_DIR = REPO_ROOT / "interactions" / "verified"


def cards_ever_seen(rec):
    return set(rec["hand"]) | set(rec["battlefield"]) | set(rec["graveyard"]) | set(rec["exile"])


def main(snapshot_path):
    data = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    recs = data["snapshots"]
    turns = sorted(set(r["turn"] for r in recs))

    result = {
        "run_class": "DECK_BACKED_GOLDFISH",
        "phase": "SIM_001_SOLO_BASELINE_V1",
        "source_batch": data["batch_id"],
        "subject_deck_version": data["subject_deck_version"],
        "subject_deck_hash": data["subject_deck_hash"],
        "ai_skill": data["ai_skill"],
        "sample_size_per_turn": {},
        "empirical_cards_seen_by_turn": {},
        "commander_on_battlefield_by_turn": {},
        "deterministic_combo_all_pieces_seen_by_turn": {},
        "pod_survival_seen_by_turn": {},
    }

    for t in turns:
        turn_recs = [r for r in recs if r["turn"] == t]
        result["sample_size_per_turn"][str(t)] = len(turn_recs)
        result["empirical_cards_seen_by_turn"][str(t)] = sum(98 - r["library_size"] for r in turn_recs) / len(turn_recs)
        for commander in ("Tymna the Weaver", "Thrasios, Triton Hero"):
            hits = sum(1 for r in turn_recs if commander in r["battlefield"])
            result["commander_on_battlefield_by_turn"].setdefault(commander, {})[str(t)] = hits / len(turn_recs)

    for f in sorted(INTERACTIONS_DIR.glob("INT-*.json")):
        idata = json.loads(f.read_text(encoding="utf-8"))
        if idata.get("conditional") is not False:
            continue
        card_names = [c["name"] for c in idata.get("cards", [])]
        entry = {}
        for t in turns:
            turn_recs = [r for r in recs if r["turn"] == t]
            hits = sum(1 for r in turn_recs if set(card_names) <= cards_ever_seen(r))
            entry[str(t)] = hits / len(turn_recs)
        result["deterministic_combo_all_pieces_seen_by_turn"][idata["id"]] = {"cards": card_names, "p_all_pieces_seen": entry}

    for card in ("Birthing Pod", "Survival of the Fittest"):
        entry = {}
        for t in turns:
            turn_recs = [r for r in recs if r["turn"] == t]
            hits = sum(1 for r in turn_recs if card in cards_ever_seen(r))
            entry[str(t)] = hits / len(turn_recs)
        result["pod_survival_seen_by_turn"][card] = entry

    out_path = REPO_ROOT / "results" / "solo_baseline" / "engine_goldfish_empirical.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result["commander_on_battlefield_by_turn"], indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(REPO_ROOT / "results" / "solo_baseline" / "solo-goldfish-batch002-realhands-raw_snapshots.json"))
