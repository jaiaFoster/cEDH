"""SIM-DECKBUILD-008: materialise the exact 98-card main decks for the reported builds.

Each build is the frozen v8 baseline with the mana-neutral dork swap (Deathrite Shaman ->
the dork chosen in the dork audit) plus the slot-preserving adds/cuts in
deckbuild008_work/verify_sets.json. Writes deckbuild008_final_lists.json.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_deckbuild008_experiments as ex  # noqa: E402
import deckbuild008_cards as dc  # noqa: E402
from build_deckbuild008_frozen_deck import cache_ids  # noqa: E402
from sim.validation.run_classification import compute_deck_hash  # noqa: E402

WORK = ex.OUT / "deckbuild008_work"


def main() -> None:
    dork = json.loads((WORK / "dork.json").read_text())["_chosen"]
    base_names, base_hash = ex.baseline()
    ids = cache_ids()
    # Printings registered in the frozen baseline take precedence, so the v8 hash reproduces exactly.
    frozen = json.loads((ex.REPO_ROOT / "data" / "decklists" / "tymna-thrasios-creature-factory-deckbuild008-v1.json").read_text())
    ids.update({c["name"]: c["scryfall_id"] for c in frozen["cards"]})
    assert compute_deck_hash(frozen["commanders"], frozen["cards"]) == base_hash
    base = ex.with_dork(base_names, dork)
    out = {"task": "SIM-DECKBUILD-008", "artifact": "deckbuild008_final_lists.json",
           "baseline_hash": base_hash, "dork_swap": {"cut": "Deathrite Shaman", "add": dork}, "builds": {}}
    for s in json.loads((WORK / "verify_sets.json").read_text()):
        deck = ex.swap(base, s["cuts"], s["adds"])
        assert len(deck) == 98 and len(set(deck)) == 98, s["label"]
        cat = collections.Counter()
        for c in deck:
            cat["land" if dc.is_land(c) else "creature" if dc.is_creature(c) else "other"] += 1
        out["builds"][s["label"]] = {
            "adds_vs_v8": [dork] + s["adds"], "cuts_vs_v8": ["Deathrite Shaman"] + s["cuts"],
            "deck_hash": compute_deck_hash(["Thrasios, Triton Hero", "Tymna the Weaver"],
                                           [{"name": c, "scryfall_id": ids[c], "quantity": 1} for c in deck]), "type_counts": dict(cat),
            "structure": ex.structure(deck), "mainboard": sorted(deck)}
    (ex.OUT / "deckbuild008_final_lists.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out["builds"].items():
        print(k, v["deck_hash"][:16], v["type_counts"])


if __name__ == "__main__":
    main()
