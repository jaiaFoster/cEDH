"""Runs a batch of real, deck-backed diagnostic games through XMage in as
few JVM/Maven invocations as possible (SubjectDeckDiagnosticGameTest loops
over -Ddiag.seeds internally, calling reset() between games - see that
file's own docstring), splits the combined magetest.log into per-game
transcripts on the ===DIAG_GAME_START/END=== markers, and writes one JSON
record per game plus a batch summary.

GATE_4A_2P_DIAGNOSTIC scope: rules-engine/adapter/basic-policy stress
testing, not empirical cEDH evidence. See results/diagnostic/README.md.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from sim.rules_engine.xmage_adapter.deck_to_dck import load_and_verify, to_dck  # noqa: E402
from sim.rules_engine.xmage_adapter.run_diagnostic_game import (  # noqa: E402
    LOG_LINE_RE,
    GAME_LOG_RE,
    install_driver,
)

START_RE = re.compile(r"^===DIAG_GAME_START seed=(\d+)===$")
END_RE = re.compile(r"^===DIAG_GAME_END seed=(\d+) status=(\w+) elapsedMs=(\d+)(?: exceptionClass=(\S+) exceptionMsg=(.*))?===$")


def run_chunk(mage_dir: Path, seeds: list, max_turn: int, seats: int, deck_name: str, skill: int, timeout_s: int) -> str:
    cmd = [
        "mvn", "-q", "-o", "-pl", "Mage.Tests", "test",
        "-Dtest=SubjectDeckDiagnosticGameTest",
        f"-Ddiag.seeds={','.join(str(s) for s in seeds)}",
        f"-Ddiag.maxTurn={max_turn}",
        f"-Ddiag.seats={seats}",
        f"-Ddiag.deck={deck_name}",
        f"-Ddiag.skill={skill}",
    ]
    log_path = mage_dir / "Mage.Tests" / "magetest.log"
    if log_path.exists():
        log_path.unlink()
    try:
        proc = subprocess.run(cmd, cwd=str(mage_dir), capture_output=True, text=True, timeout=timeout_s)
        maven_ok = proc.returncode == 0
        maven_tail = (proc.stdout[-4000:] + proc.stderr[-4000:]) if not maven_ok else ""
    except subprocess.TimeoutExpired:
        maven_ok = False
        maven_tail = f"CHUNK TIMEOUT after {timeout_s}s - Maven process killed"
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    if not maven_ok and not log_text:
        log_text = "===CHUNK_FAILED===\n" + maven_tail
    return log_text


def split_games(raw_log: str) -> list:
    """Returns a list of dicts: {seed, status, elapsed_ms, exception, events, engine_errors}."""
    games = []
    current = None
    for line in raw_log.splitlines():
        m = LOG_LINE_RE.match(line)
        level, msg = (m.group("level"), m.group("msg")) if m else (None, line)

        sm = START_RE.match(msg) if msg else None
        if sm:
            current = {"seed": int(sm.group(1)), "status": None, "elapsed_ms": None,
                       "exception": None, "events": [], "engine_errors": []}
            games.append(current)
            continue
        em = END_RE.match(msg) if msg else None
        if em and current is not None:
            current["status"] = em.group(2)
            current["elapsed_ms"] = int(em.group(3))
            if em.group(4):
                current["exception"] = f"{em.group(4)}: {em.group(5)}"
            continue

        if current is None:
            continue
        if level == "ERROR":
            current["engine_errors"].append(msg)
            continue
        gm = GAME_LOG_RE.match(msg) if msg else None
        if gm:
            current["events"].append({"turnstep": gm.group("turnstep"), "text": gm.group("text")})
    return games


def winner_from_events(events: list) -> str:
    for ev in events:
        m = re.search(r"(\w+) has (?:won|lost) the game", ev["text"])
        if m:
            return ev["text"]
    return None


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decklist", default=str(REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-v1.json"))
    ap.add_argument("--mage-dir", required=True)
    ap.add_argument("--seed-start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--chunk-size", type=int, default=10)
    ap.add_argument("--max-turn", type=int, default=10)
    ap.add_argument("--seats", type=int, default=2, choices=[2, 3, 4])
    ap.add_argument("--skill", type=int, default=6)
    ap.add_argument("--batch-id", default=None)
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "results" / "diagnostic" / "gate4a_2p"))
    ap.add_argument("--chunk-timeout", type=int, default=280)
    args = ap.parse_args()

    decklist_path = Path(args.decklist)
    mage_dir = Path(args.mage_dir)
    mage_tests_dir = mage_dir / "Mage.Tests"
    dck_name = "TymnaThrasiosTreefarm.dck"

    payload = load_and_verify(decklist_path)
    dck_path = mage_tests_dir / dck_name
    dck_path.write_text(to_dck(payload), encoding="utf-8")
    install_driver(mage_tests_dir)

    all_seeds = list(range(args.seed_start, args.seed_start + args.count))
    batch_id = args.batch_id or f"gate4a-2p-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_games = []
    chunk_failures = []
    for chunk_idx, seed_chunk in enumerate(chunked(all_seeds, args.chunk_size)):
        raw_log = run_chunk(mage_dir, seed_chunk, args.max_turn, args.seats, dck_name, args.skill, args.chunk_timeout)
        parsed_games = split_games(raw_log)
        found_seeds = {g["seed"] for g in parsed_games}
        missing = [s for s in seed_chunk if s not in found_seeds]
        if missing:
            chunk_failures.append({"chunk_index": chunk_idx, "seeds_requested": seed_chunk, "seeds_missing": missing})
            for s in missing:
                all_games.append({"seed": s, "status": "CHUNK_LOST", "elapsed_ms": None,
                                   "exception": "entire chunk failed/timed out before this game's markers appeared",
                                   "events": [], "engine_errors": []})
        all_games.extend(parsed_games)
        print(f"chunk {chunk_idx}: requested {len(seed_chunk)} seeds, recovered {len(parsed_games)} game records"
              + (f", MISSING {missing}" if missing else ""))

    gate_phase = "GATE_4A_2P_DIAGNOSTIC" if args.seats == 2 else "FOUR_PLAYER_DIAGNOSTIC_PROBE"

    game_records = []
    for g in all_games:
        game_id = f"{batch_id}-seed{g['seed']}"
        record = {
            "game_id": game_id,
            "purpose": f"{gate_phase}: rules-engine/adapter/basic-policy stress testing, NOT cEDH metagame inference or any strategic evidence",
            "run_class": "SYNTHETIC_DIAGNOSTIC_GAMEPLAY",
            "gate_phase": gate_phase,
            "subject_deck_version": payload["deck_version"],
            "subject_deck_hash": payload["deck_hash"],
            "seats": args.seats,
            "mirror_match": True,
            "ai_skill": args.skill,
            "random_seed": g["seed"],
            "max_turn_requested": args.max_turn,
            "status": g["status"] or "UNKNOWN",
            "elapsed_ms": g["elapsed_ms"],
            "exception": g["exception"],
            "engine_errors": g["engine_errors"],
            "winner_line": winner_from_events(g["events"]),
            "event_count": len(g["events"]),
            "events": g["events"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        game_records.append(record)
        (out_dir / f"{game_id}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "batch_id": batch_id,
        "gate_phase": gate_phase,
        "subject_deck_version": payload["deck_version"],
        "subject_deck_hash": payload["deck_hash"],
        "seats": args.seats,
        "ai_skill": args.skill,
        "requested_game_count": len(all_seeds),
        "seed_range": [args.seed_start, args.seed_start + args.count - 1],
        "games_completed_ok": sum(1 for g in game_records if g["status"] == "OK"),
        "games_exception": sum(1 for g in game_records if g["status"] == "EXCEPTION"),
        "games_chunk_lost": sum(1 for g in game_records if g["status"] == "CHUNK_LOST"),
        "games_with_engine_errors": sum(1 for g in game_records if g["engine_errors"]),
        "total_events": sum(g["event_count"] for g in game_records),
        "avg_events_per_game": (sum(g["event_count"] for g in game_records) / len(game_records)) if game_records else 0,
        "avg_elapsed_ms": (sum(g["elapsed_ms"] for g in game_records if g["elapsed_ms"]) / max(1, sum(1 for g in game_records if g["elapsed_ms"]))),
        "games_with_winner_detected": sum(1 for g in game_records if g["winner_line"]),
        "chunk_failures": chunk_failures,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / f"{batch_id}-SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
