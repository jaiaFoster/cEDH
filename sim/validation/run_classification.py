"""Run classification and fail-closed deck-loading guards.

Implements docs/RUN_CLASSIFICATION.md. This module is the ONLY sanctioned
way to load a decklist for a DECK_BACKED_* run — nothing else in this
codebase should read data/decklists/*.json directly for that purpose.

Nothing here does anything beyond load-time verification: no game logic,
no simulation. sim/simulation/ and sim/rules_engine/ are expected to call
load_frozen_deck() before touching a deck for any deck-backed run, and to
call format_run_banner() as the first thing any run prints.
"""
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RunClass(str, Enum):
    SYNTHETIC_GOLD_STATE = "SYNTHETIC_GOLD_STATE"
    SYNTHETIC_RULES_TEST = "SYNTHETIC_RULES_TEST"
    DECK_BACKED_GOLDFISH = "DECK_BACKED_GOLDFISH"
    DECK_BACKED_SINGLE_PLAYER = "DECK_BACKED_SINGLE_PLAYER"
    DECK_BACKED_FOUR_PLAYER = "DECK_BACKED_FOUR_PLAYER"
    TOURNAMENT_CALIBRATION = "TOURNAMENT_CALIBRATION"
    STATIC_ANALYSIS = "STATIC_ANALYSIS"


SYNTHETIC_RUN_CLASSES = {RunClass.SYNTHETIC_GOLD_STATE, RunClass.SYNTHETIC_RULES_TEST}
DECK_BACKED_RUN_CLASSES = {
    RunClass.DECK_BACKED_GOLDFISH,
    RunClass.DECK_BACKED_SINGLE_PLAYER,
    RunClass.DECK_BACKED_FOUR_PLAYER,
}

# Names that must never appear in a frozen decklist's card list unless they
# are genuinely part of that deck's own declared list (checked separately
# via hash match) — this is a defense-in-depth denylist for the case where
# someone hand-edits a "frozen" file without updating its hash, or feeds
# load_frozen_deck() a dict assembled at runtime rather than read from disk.
PLACEHOLDER_CARD_PATTERNS = ("Test Card", "Placeholder", "TODO", "TBD", "UNKNOWN")


class RunClassificationError(Exception):
    """Base class for all fail-closed guard rejections in this module."""


class SyntheticFixtureRejectedError(RunClassificationError):
    """Raised when the input to load_frozen_deck() carries synthetic-fixture markers."""


class MissingDeckHashError(RunClassificationError):
    """Raised when a decklist has no deck_hash field — it is not frozen."""


class DeckHashMismatchError(RunClassificationError):
    """Raised when the recomputed hash doesn't match the stored deck_hash."""


class UnknownCardError(RunClassificationError):
    """Raised when a card's scryfall_id isn't present in the declared oracle_data_version cache."""


class PlaceholderCardError(RunClassificationError):
    """Raised when a denylisted placeholder card name appears in the deck."""


class ProvisionalDeckRejectedError(RunClassificationError):
    """Raised when a path under data/decklists/_provisional/ is used where a frozen deck is required."""


def compute_deck_hash(commanders: list[str], cards: list[dict]) -> str:
    """Canonical SHA-256 over sorted commander names + sorted (name, scryfall_id, quantity)
    tuples, so the hash is stable regardless of field/list ordering in the source file and
    changes if a card is silently swapped for a different printing/oracle ID.
    """
    canonical = {
        "commanders": sorted(commanders),
        "cards": sorted(
            (c["name"], c["scryfall_id"], c["quantity"]) for c in cards
        ),
    }
    blob = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def freeze_decklist(decklist: dict) -> dict:
    """Compute and attach deck_hash to an in-memory decklist dict. Does not write to disk —
    callers write the result to data/decklists/<deck_version>.json themselves, per
    docs/VERSIONING.md's immutability rule (a new file, never editing an existing frozen one).
    """
    frozen = dict(decklist)
    frozen["deck_hash"] = compute_deck_hash(decklist["commanders"], decklist["cards"])
    return frozen


def _reject_if_synthetic_markers(payload: dict) -> None:
    run_class = payload.get("run_class")
    if run_class in {c.value for c in SYNTHETIC_RUN_CLASSES}:
        raise SyntheticFixtureRejectedError(
            f"Refusing to load as a deck-backed source: input carries run_class={run_class!r}, "
            "which is a synthetic-fixture marker (docs/RUN_CLASSIFICATION.md). A synthetic "
            "fixture can never be the deck source for a deck-backed run."
        )
    if payload.get("representative_of_deck_draws") is False:
        raise SyntheticFixtureRejectedError(
            "Refusing to load as a deck-backed source: input carries "
            "representative_of_deck_draws=false, a synthetic-fixture marker "
            "(docs/RUN_CLASSIFICATION.md)."
        )


def load_frozen_deck(deck_version_path: Path, cards_cache_dir: Path) -> dict:
    """Load and verify a decklist for use in a DECK_BACKED_* run. Raises (never warns, never
    falls back) on any of the fail-closed conditions in docs/RUN_CLASSIFICATION.md requirement 3.

    Returns the verified decklist dict on success.
    """
    deck_version_path = Path(deck_version_path)
    cards_cache_dir = Path(cards_cache_dir)

    if "_provisional" in deck_version_path.parts:
        raise ProvisionalDeckRejectedError(
            f"{deck_version_path} is under a _provisional/ directory — provisional decklists "
            "are never eligible to back a DECK_BACKED_* run. Use the frozen "
            "data/decklists/<deck_version>.json file instead."
        )

    payload = json.loads(deck_version_path.read_text())

    _reject_if_synthetic_markers(payload)

    stored_hash = payload.get("deck_hash")
    if not stored_hash:
        raise MissingDeckHashError(
            f"{deck_version_path} has no deck_hash field — it is not frozen. Only a file with "
            "a deck_hash (produced by freeze_decklist()) may back a DECK_BACKED_* run."
        )

    recomputed_hash = compute_deck_hash(payload["commanders"], payload["cards"])
    if recomputed_hash != stored_hash:
        raise DeckHashMismatchError(
            f"{deck_version_path}: stored deck_hash={stored_hash} does not match recomputed "
            f"hash={recomputed_hash} of its own commanders+cards. The file was edited after "
            "being frozen (docs/VERSIONING.md forbids this — a changed list is a new file), or "
            "its contents were tampered with / partially substituted."
        )

    oracle_data_version = payload["ingested"]["oracle_data_version"]
    known_scryfall_ids: set[str] = set()
    for cache_file in cards_cache_dir.glob("*.json"):
        card = json.loads(cache_file.read_text())
        if card.get("source_version") == oracle_data_version:
            known_scryfall_ids.add(card["scryfall_id"])

    for card in payload["cards"]:
        for pattern in PLACEHOLDER_CARD_PATTERNS:
            if pattern.lower() in card["name"].lower():
                raise PlaceholderCardError(
                    f"{deck_version_path}: card {card['name']!r} matches placeholder pattern "
                    f"{pattern!r} — refusing to treat as a real deck card."
                )
        if card["scryfall_id"] not in known_scryfall_ids:
            raise UnknownCardError(
                f"{deck_version_path}: card {card['name']!r} (scryfall_id={card['scryfall_id']}) "
                f"is not present in the card cache for oracle_data_version={oracle_data_version!r}. "
                "Either the deck references a card that was never ingested, or a card was "
                "silently substituted after freezing."
            )

    return payload


@dataclass(frozen=True)
class RunBanner:
    run_class: RunClass
    deck_representative: bool
    synthetic_mana: bool

    def render(self) -> str:
        return (
            f"RUN_CLASS={self.run_class.value}\n"
            f"DECK_REPRESENTATIVE={str(self.deck_representative).lower()}\n"
            f"SYNTHETIC_MANA={str(self.synthetic_mana).lower()}"
        )


def format_run_banner(run_class: RunClass, deck_representative: bool, synthetic_mana: bool) -> str:
    """The exact three-line banner docs/RUN_CLASSIFICATION.md requires as the first output of
    any run. Nothing should hand-roll its own version of this text.
    """
    return RunBanner(run_class, deck_representative, synthetic_mana).render()
