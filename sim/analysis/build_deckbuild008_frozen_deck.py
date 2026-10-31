"""SIM-DECKBUILD-008 — freeze the baseline subject deck (Creature Factory, Moxfield v8).

Reconciliation performed before freezing (all checks are re-run by this script, fail-closed):
  1. Live Moxfield fetch on 2026-10-30 returned the unchanged v8 snapshot
     (content_hash 635940777a53..., moxfield_updated_at 2026-10-15T15:50:53Z).
  2. The TopDeck.gg registrations for BOTH weekend events - AZMS cEDH Qualifier #8 (2026-10-17)
     and Eye of the Tiger (Lion) cEDH, Flagstaff (2026-10-18, the "Geekery Games LED" event) -
     were imported from the same Moxfield URL and are card-for-card identical to v8 (98 cards).
  3. The Geekery round-3 photo transcription lists "Borne Upon a Wind". Borne appears in NO
     Moxfield snapshot in the repository's history and in NEITHER TopDeck registration. The
     registered list therefore did not contain Borne; the transcription is either a misread or a
     physical-deck discrepancy that the registration does not reflect. Every other card named in
     either weekend's hand transcriptions is in v8 ("Buried Catacombs" = Verdant Catacombs).
  => Baseline = Moxfield v8 exactly. Borne Upon a Wind is treated as a CANDIDATE, not baseline.

Card identities resolve against the fresh Oracle cache data/cards_cache/oracle-2026-10-30/
(pulled from Scryfall this task; no synthetic placeholder IDs).
"""
import gzip
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402

MOXFIELD_CURRENT = REPO_ROOT / "data" / "deck_sources" / "moxfield" / "tymna-thrasios" / "current.json"
TOPDECK = REPO_ROOT / "data" / "tournament_snapshots" / "topdeck"
REGISTRATIONS = {
    "azms-cedh-qualifier-8": "2026-10-17",
    "eye-of-the-tiger-lion-cedh-tournament-win-a-lions-eye": "2026-10-18",
}
SUBJECT_PLAYER_ID = "bQ97iyjPFLUq4ZTFPgMhscb9PJG3"
CACHE = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-10-30"
OUT_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-creature-factory-deckbuild008-v1.json"
EXPECTED_MOXFIELD_HASH = "635940777a53f5e8a7b27156cf7caec22694f7935b1faf0f83f5677a96f39148"


def registered_list(tid):
    manifest = json.loads((TOPDECK / "manifest.json").read_text(encoding="utf-8"))["events"]
    raw = json.load(gzip.open(TOPDECK / manifest[tid]["raw_snapshot"]))
    for s in raw["standings"]:
        if s.get("id") == SUBJECT_PLAYER_ID:
            return s["deckObj"]
    raise SystemExit(f"subject registration not found in {tid}")


def cache_ids():
    out = {}
    for p in CACHE.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        out[d["name"]] = d["scryfall_id"]
    return out


def main():
    mox = json.loads(MOXFIELD_CURRENT.read_text(encoding="utf-8"))
    assert mox["content_hash"] == EXPECTED_MOXFIELD_HASH, "Moxfield source changed - re-reconcile"
    mox_names = {c["name"] for c in mox["cards"]}
    assert len(mox_names) == 98

    reconciliation = {}
    for tid, date in REGISTRATIONS.items():
        deck = registered_list(tid)
        names = set(deck["Mainboard"])
        assert names == mox_names, f"{tid} registration differs from Moxfield v8"
        reconciliation[tid] = {"date": date, "identical_to_moxfield_v8": True,
                               "imported_from": deck["metadata"].get("importedFrom"),
                               "mainboard_count": sum(v["count"] for v in deck["Mainboard"].values())}
    assert "Borne Upon a Wind" not in mox_names

    ids = cache_ids()
    cards = []
    for c in sorted(mox["cards"], key=lambda c: c["name"]):
        assert c["name"] in ids, f"{c['name']} missing from oracle cache"
        cards.append({"scryfall_id": c["scryfall_id"], "name": c["name"], "quantity": 1})
    commanders = [c["name"] for c in mox["commanders"]]
    deck_hash = compute_deck_hash(commanders, cards)
    payload = {
        "deck_version": "tymna-thrasios-creature-factory-deckbuild008-v1",
        "deck_name": "Creature Factory (Thrasios / Tymna) — SIM-DECKBUILD-008 frozen baseline",
        "commanders": commanders,
        "archetype_id": None,
        "role": "subject",
        "cards": cards,
        "source": {
            # decklist.schema.json enum: the pilot's own public Moxfield list is user-supplied.
            "type": "user_supplied",
            "reference": mox["source"]["url"],
            "date": mox["moxfield_updated_at"][:10],
            "platform": "moxfield_public_deck",
            "moxfield_version": mox["moxfield_version"],
            "moxfield_updated_at": mox["moxfield_updated_at"],
            "moxfield_content_hash": mox["content_hash"],
            "live_refetch": "2026-10-30 (unchanged)",
            "reconciliation": {
                "topdeck_registrations": reconciliation,
                "borne_upon_a_wind": (
                    "Named in the Geekery/Flagstaff round-3 photo transcription only. Absent from all "
                    "11 stored Moxfield snapshots and from both TopDeck registrations; not baseline. "
                    "Evaluated as a candidate add (variant E)."),
            },
        },
        "ingested": {"oracle_data_version": "scryfall-live-2026-10-30", "ingested_date": "2026-10-30",
                     "cards_cache_path": "data/cards_cache/oracle-2026-10-30/"},
        "deck_hash": deck_hash,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}\ndeck_hash={deck_hash}")


if __name__ == "__main__":
    main()
