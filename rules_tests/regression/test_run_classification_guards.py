"""Permanent regression test for docs/RUN_CLASSIFICATION.md requirement 7:
proves a deck-backed run cannot initialize from a synthetic fixture, a
tampered/hash-mismatched deck, an unfrozen (no-hash) deck, a provisional
deck, or a deck referencing cards outside the declared oracle data version.

This is the single most safety-critical test in the suite: if any of these
guards regresses, a deck-backed simulation could silently run against the
wrong cards and produce results that look like real subject-deck evidence
but aren't.
"""
import copy
import json
import sys

from conftest import REPO_ROOT, load_json

sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from sim.validation.run_classification import (  # noqa: E402
    DeckHashMismatchError,
    MissingDeckHashError,
    PlaceholderCardError,
    ProvisionalDeckRejectedError,
    RunClass,
    SyntheticFixtureRejectedError,
    UnknownCardError,
    compute_deck_hash,
    format_run_banner,
    load_frozen_deck,
)

REAL_DECK_PATH = REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-v1.json"
CARDS_CACHE_DIR = REPO_ROOT / "data" / "cards_cache" / "oracle-2026-08-12"


@pytest.fixture(scope="module")
def real_deck_payload() -> dict:
    return load_json(REAL_DECK_PATH)


def test_load_frozen_deck_succeeds_for_the_real_frozen_subject_deck():
    result = load_frozen_deck(REAL_DECK_PATH, CARDS_CACHE_DIR)
    assert result["deck_version"] == "tymna-thrasios-treefarm-v1"
    assert len(result["cards"]) == 98
    assert set(result["commanders"]) == {"Tymna the Weaver", "Thrasios, Triton Hero"}


def test_load_frozen_deck_rejects_provisional_path():
    provisional_path = REPO_ROOT / "data" / "decklists" / "_provisional" / "tymna-thrasios-treefarm-v1.json"
    assert provisional_path.exists(), "fixture assumption: the provisional file still exists"
    with pytest.raises(ProvisionalDeckRejectedError):
        load_frozen_deck(provisional_path, CARDS_CACHE_DIR)


def test_load_frozen_deck_rejects_missing_hash(tmp_path, real_deck_payload):
    payload = copy.deepcopy(real_deck_payload)
    del payload["deck_hash"]
    p = tmp_path / "unfrozen.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(MissingDeckHashError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


def test_load_frozen_deck_rejects_hash_mismatch(tmp_path, real_deck_payload):
    payload = copy.deepcopy(real_deck_payload)
    payload["deck_hash"] = "0" * 64  # syntactically valid, semantically wrong
    p = tmp_path / "tampered.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(DeckHashMismatchError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


def test_load_frozen_deck_rejects_hash_mismatch_after_card_substitution(tmp_path, real_deck_payload):
    """The concrete 'silent substitution' scenario the review specifically called out: swap one
    card's scryfall_id for a different printing/card WITHOUT updating deck_hash. Must fail
    exactly like any other tamper - substitution is not a special case the guard misses.
    """
    payload = copy.deepcopy(real_deck_payload)
    payload["cards"][0]["scryfall_id"] = "00000000-0000-0000-0000-000000000000"
    p = tmp_path / "substituted.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(DeckHashMismatchError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


def test_load_frozen_deck_rejects_unknown_card_even_with_consistent_hash(tmp_path, real_deck_payload):
    """A stricter case than the above: the deck is INTERNALLY self-consistent (hash matches its
    own cards) but references a scryfall_id never actually ingested into the card cache - e.g.
    a hand-crafted or corrupted-at-the-source file. The hash check alone can't catch this;
    the cache cross-check must.
    """
    payload = copy.deepcopy(real_deck_payload)
    payload["cards"][0]["scryfall_id"] = "00000000-0000-0000-0000-000000000000"
    payload["deck_hash"] = compute_deck_hash(payload["commanders"], payload["cards"])
    p = tmp_path / "self_consistent_but_unknown.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(UnknownCardError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


def test_load_frozen_deck_rejects_placeholder_card_name(tmp_path, real_deck_payload):
    payload = copy.deepcopy(real_deck_payload)
    payload["cards"][0]["name"] = "Placeholder Card"
    payload["deck_hash"] = compute_deck_hash(payload["commanders"], payload["cards"])
    p = tmp_path / "placeholder.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(PlaceholderCardError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


@pytest.mark.parametrize("run_class", ["SYNTHETIC_GOLD_STATE", "SYNTHETIC_RULES_TEST"])
def test_load_frozen_deck_rejects_synthetic_run_class_marker(tmp_path, real_deck_payload, run_class):
    payload = copy.deepcopy(real_deck_payload)
    payload["run_class"] = run_class
    p = tmp_path / "synthetic_marked.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(SyntheticFixtureRejectedError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


def test_load_frozen_deck_rejects_representative_of_deck_draws_false(tmp_path, real_deck_payload):
    """Even without an explicit run_class field, the representative_of_deck_draws=false marker
    alone must be sufficient to reject - defense in depth per docs/RUN_CLASSIFICATION.md.
    """
    payload = copy.deepcopy(real_deck_payload)
    payload["representative_of_deck_draws"] = False
    p = tmp_path / "marked_non_representative.json"
    p.write_text(json.dumps(payload))
    with pytest.raises(SyntheticFixtureRejectedError):
        load_frozen_deck(p, CARDS_CACHE_DIR)


def test_compute_deck_hash_is_stable_under_reordering(real_deck_payload):
    forward = compute_deck_hash(real_deck_payload["commanders"], real_deck_payload["cards"])
    shuffled_cards = list(reversed(real_deck_payload["cards"]))
    shuffled_commanders = list(reversed(real_deck_payload["commanders"]))
    backward = compute_deck_hash(shuffled_commanders, shuffled_cards)
    assert forward == backward


def test_compute_deck_hash_changes_on_any_card_substitution(real_deck_payload):
    baseline = compute_deck_hash(real_deck_payload["commanders"], real_deck_payload["cards"])
    mutated_cards = copy.deepcopy(real_deck_payload["cards"])
    mutated_cards[0]["scryfall_id"] = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    mutated = compute_deck_hash(real_deck_payload["commanders"], mutated_cards)
    assert baseline != mutated


def test_format_run_banner_exact_format():
    banner = format_run_banner(RunClass.SYNTHETIC_GOLD_STATE, deck_representative=False, synthetic_mana=True)
    assert banner == "RUN_CLASS=SYNTHETIC_GOLD_STATE\nDECK_REPRESENTATIVE=false\nSYNTHETIC_MANA=true"


def test_format_run_banner_deck_backed_example():
    banner = format_run_banner(RunClass.DECK_BACKED_FOUR_PLAYER, deck_representative=True, synthetic_mana=False)
    assert "RUN_CLASS=DECK_BACKED_FOUR_PLAYER" in banner
    assert "DECK_REPRESENTATIVE=true" in banner
    assert "SYNTHETIC_MANA=false" in banner
