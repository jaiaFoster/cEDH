"""SIM-ROGFARM-001 — frozen input deck provenance checks (Stage 1 / pre-registration)."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "sim" / "analysis"))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402

DECKLISTS = REPO_ROOT / "data" / "decklists"

EXPECTED = {
    "rogsi-valley-forge-2026-v1": ["Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"],
    "rogfarm-r1-minimal-v1": ["Rograkh, Son of Rohgahh", "Silas Renn, Seeker Adept"],
    "bluefarm-control-2026-v1": ["Tymna the Weaver", "Kraum, Ludevic's Opus"],
}

R1_MUST_BE_ABSENT = {
    "Thassa's Oracle", "Demonic Consultation", "Tainted Pact", "Strike It Rich",
    "Final Fortune", "Dramatic Reversal",
}
R1_MUST_BE_PRESENT = {
    "Faerie Mastermind", "Narset, Parter of Veils", "Notion Thief",
    "Force of Negation", "Foil", "Subtlety",
}


def _load(version):
    return json.loads((DECKLISTS / f"{version}.json").read_text(encoding="utf-8"))


def test_all_three_decks_have_98_unique_mainboard_cards_and_2_commanders():
    for version, commanders in EXPECTED.items():
        payload = _load(version)
        assert len(payload["cards"]) == 98, version
        names = [c["name"] for c in payload["cards"]]
        assert len(names) == len(set(names)), f"{version}: singleton violation"
        assert payload["commanders"] == commanders, version


def test_all_three_hashes_match_recomputed():
    for version in EXPECTED:
        payload = _load(version)
        assert payload["deck_hash"] == compute_deck_hash(payload["commanders"], payload["cards"])


def test_r1_diff_assertions_exact():
    stock_names = {c["name"] for c in _load("rogsi-valley-forge-2026-v1")["cards"]}
    r1_names = {c["name"] for c in _load("rogfarm-r1-minimal-v1")["cards"]}
    assert stock_names - r1_names == R1_MUST_BE_ABSENT
    assert r1_names - stock_names == R1_MUST_BE_PRESENT
    assert len(stock_names - r1_names) == 6
    assert len(r1_names - stock_names) == 6


def test_no_deck_silently_reuses_a_tymna_thrasios_subject_hash():
    """A distinct-project sanity check: none of the 3 new hashes may collide with any prior
    frozen Tymna/Thrasios subject's hash (would indicate an accidental identical-content reuse)."""
    prior_hashes = set()
    for p in DECKLISTS.glob("tymna-thrasios-*.json"):
        prior_hashes.add(json.loads(p.read_text(encoding="utf-8"))["deck_hash"])
    for version in EXPECTED:
        assert _load(version)["deck_hash"] not in prior_hashes


def test_synthetic_ids_never_collide_with_a_real_cached_scryfall_id():
    cache_ids = set()
    for p in (REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12").glob("*.json"):
        cache_ids.add(json.loads(p.read_text(encoding="utf-8"))["scryfall_id"])
    for version in EXPECTED:
        for c in _load(version)["cards"]:
            if c["scryfall_id"].startswith("deadbeef-rog0-"):
                assert c["scryfall_id"] not in cache_ids
