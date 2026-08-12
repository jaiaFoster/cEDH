"""Orchestrates one real, deck-backed diagnostic game through XMage: loads
the exact frozen decklist (hash-verified), converts it to .dck, drives
sim/rules_engine/xmage_adapter/SubjectDeckDiagnosticGameTest.java against a
prepared XMage checkout with a controlled random seed, parses the engine's
own game log into a machine-readable transcript, and writes a diagnostic
game record.

This is explicitly the diagnostic-gameplay phase (docs/VALIDATION_GATES.md
Gate 3->4 transition), NOT an empirical simulation run - records land in
results/diagnostic/, never results/raw/, and are never eligible input to
any win-rate/matchup/mulligan/turn-speed statistic. See
docs/RUN_CLASSIFICATION.md for why that boundary is load-bearing.

Requires a prepared XMage checkout (see xmage_adapter/README.md for the
one-time setup) - this script does not clone/build XMage itself, matching
the existing "drop-in test file" pattern used by xmage_tests/.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from sim.rules_engine.xmage_adapter.deck_to_dck import load_and_verify, to_dck  # noqa: E402

LOG_LINE_RE = re.compile(
    r"^(?P<level>\S+)\s+(?P<ts>\d{4}-\d{2}-\d{2} [\d:,]+)\s+(?P<msg>.*?)\s+=>\["
)
GAME_LOG_RE = re.compile(r"^\[LOG\]\[GAME\]\s+(?P<turnstep>\S+):\s+(?P<text>.*)$")


def build_dck(decklist_path: Path, mage_tests_dir: Path, dck_name: str) -> Path:
    payload = load_and_verify(decklist_path)
    dck_path = mage_tests_dir / dck_name
    dck_path.write_text(to_dck(payload), encoding="utf-8")
    return dck_path


def install_driver(mage_tests_dir: Path) -> None:
    src = REPO_ROOT / "sim" / "rules_engine" / "xmage_adapter" / "SubjectDeckDiagnosticGameTest.java"
    dst_dir = mage_tests_dir / "src" / "test" / "java" / "org" / "mage" / "test" / "commander" / "duel"
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst_dir / src.name)


def run_maven(mage_dir: Path, seed: int, max_turn: int, seats: int, deck_name: str) -> tuple[int, str]:
    cmd = [
        "mvn", "-q", "-o", "-pl", "Mage.Tests", "test",
        "-Dtest=SubjectDeckDiagnosticGameTest",
        f"-Ddiag.seed={seed}",
        f"-Ddiag.maxTurn={max_turn}",
        f"-Ddiag.seats={seats}",
        f"-Ddiag.deck={deck_name}",
    ]
    log_path = mage_dir / "Mage.Tests" / "magetest.log"
    if log_path.exists():
        log_path.unlink()
    proc = subprocess.run(cmd, cwd=str(mage_dir), capture_output=True, text=True, timeout=280)
    game_log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    return proc.returncode, proc.stdout + "\n" + proc.stderr + "\n" + game_log


def parse_transcript(raw_log: str) -> dict:
    events = []
    errors = []
    for line in raw_log.splitlines():
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        level, msg = m.group("level"), m.group("msg")
        if level == "ERROR":
            errors.append(msg)
            continue
        gm = GAME_LOG_RE.match(msg)
        if gm:
            events.append({"turnstep": gm.group("turnstep"), "text": gm.group("text")})
    winner = None
    for ev in events:
        m = re.search(r"(\w+) has (?:won|lost) the game", ev["text"])
        if m:
            winner = ev["text"]
    return {"events": events, "engine_errors": errors, "winner_line": winner}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decklist", default=str(REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-v1.json"))
    ap.add_argument("--mage-dir", required=True, help="path to a prepared, built XMage checkout")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--max-turn", type=int, default=10)
    ap.add_argument("--seats", type=int, default=2, choices=[2, 3, 4])
    ap.add_argument("--game-id", default=None)
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "results" / "diagnostic"))
    args = ap.parse_args()

    decklist_path = Path(args.decklist)
    mage_dir = Path(args.mage_dir)
    mage_tests_dir = mage_dir / "Mage.Tests"
    dck_name = "TymnaThrasiosTreefarm.dck"

    build_dck(decklist_path, mage_tests_dir, dck_name)
    install_driver(mage_tests_dir)

    returncode, raw_log = run_maven(mage_dir, args.seed, args.max_turn, args.seats, dck_name)
    parsed = parse_transcript(raw_log)

    payload = load_and_verify(decklist_path)
    game_id = args.game_id or f"diag-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-seed{args.seed}"
    record = {
        "game_id": game_id,
        "purpose": "engine/rules diagnostic only - NOT empirical evidence, must never be cited for win-rate/matchup/mulligan/turn-speed statistics",
        "run_class": "SYNTHETIC_DIAGNOSTIC_GAMEPLAY",
        "subject_deck_version": payload["deck_version"],
        "subject_deck_hash": payload["deck_hash"],
        "seats": args.seats,
        "mirror_match": True,
        "random_seed": args.seed,
        "max_turn_requested": args.max_turn,
        "maven_exit_code": returncode,
        "engine_errors": parsed["engine_errors"],
        "winner_line": parsed["winner_line"],
        "event_count": len(parsed["events"]),
        "events": parsed["events"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{game_id}.json"
    out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(parsed['events'])} events, exit={returncode}, errors={len(parsed['engine_errors'])})")


if __name__ == "__main__":
    main()
