"""Converts a frozen project decklist (data/decklists/*.json) to XMage's
native .dck format, for loading into a real XMage game (not a hand-authored
fixture). Part of INFRA-0004's adapter: "load exact versioned decklists".

Card lines deliberately use an invalid set/number ([XXX:0]) so XMage's
DckDeckImporter always falls through to its name-based lookup
(CardRepository.findPreferredCoreExpansionCard) rather than trusting a set/
number this project doesn't track per-card. This is intentional, not a
placeholder to fix later - the frozen decklist's identity of record is the
card NAME plus its Scryfall id already verified in Gate 1 ingestion, not a
particular printing.

Verifies the deck hash before conversion so a tampered or stale decklist
file can never silently produce a .dck (same guard family as
sim/validation/run_classification.py).
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from sim.validation.run_classification import compute_deck_hash  # noqa: E402


def load_and_verify(decklist_path: Path) -> dict:
    payload = json.loads(decklist_path.read_text(encoding="utf-8"))
    expected = payload.get("deck_hash")
    if not expected:
        raise ValueError(f"{decklist_path}: no deck_hash - refusing to convert an unfrozen decklist")
    actual = compute_deck_hash(payload["commanders"], payload["cards"])
    if actual != expected:
        raise ValueError(
            f"{decklist_path}: deck_hash mismatch (file claims {expected}, recomputed {actual}) "
            "- refusing to convert a tampered/stale decklist"
        )
    return payload


def to_dck(payload: dict) -> str:
    commanders = set(payload["commanders"])
    lines = [f"NAME:{payload['deck_name']}"]
    for card in payload["cards"]:
        name = card["name"]
        if name in commanders:
            continue
        lines.append(f"{card['quantity']} [XXX:0] {name}")
    for commander_name in payload["commanders"]:
        lines.append(f"SB: 1 [XXX:0] {commander_name}")
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: deck_to_dck.py <decklist.json> <output.dck>", file=sys.stderr)
        raise SystemExit(2)
    decklist_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    payload = load_and_verify(decklist_path)
    out_path.write_text(to_dck(payload), encoding="utf-8")
    print(f"wrote {out_path} ({len(payload['cards'])} mainboard + {len(payload['commanders'])} commander(s)), deck_hash verified OK")


if __name__ == "__main__":
    main()
