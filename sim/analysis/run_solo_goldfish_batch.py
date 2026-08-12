"""SIM-001 SOLO BASELINE v1 — ENGINE-GOLDFISH layer runner.

Runs SoloGoldfishSnapshotTest (real XMage, exact frozen deck, AI-piloted
PlayerA vs. an inert goldfish PlayerB) across many seeds x turn-checkpoints,
parses the SOLO_SNAPSHOT/DIAG_GAME markers, and computes empirical
accessibility statistics from actual game state (hand/battlefield/
graveyard/exile card names) - not from whether the AI "recognized" or
executed any particular line. run_class: DECK_BACKED_GOLDFISH.

Methodological note (see results/solo_baseline/README.md): calling
execute() twice on one game object without reset() between calls does not
continue the game - each (seed, checkpoint) pair is therefore an
independent reset()+execute() run to that turn, not a shared trajectory.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from sim.rules_engine.xmage_adapter.deck_to_dck import load_and_verify, to_dck  # noqa: E402
from sim.rules_engine.xmage_adapter.run_diagnostic_game import LOG_LINE_RE, install_driver  # noqa: E402

START_RE = re.compile(r"^===DIAG_GAME_START seed=(\d+) checkpointTurn=(\d+)===$")
END_RE = re.compile(r"^===DIAG_GAME_END seed=(\d+) status=(\w+) elapsedMs=(\d+)(?: exceptionClass=(\S+) exceptionMsg=(.*))?===$")
SNAPSHOT_RE = re.compile(
    r"^===SOLO_SNAPSHOT seed=(\d+) turn=(\d+) life=(-?\d+) librarySize=(\d+) "
    r"HAND\[(.*?)\] BATTLEFIELD\[(.*?)\] GRAVEYARD\[(.*?)\] EXILE\[(.*?)\]===$"
)


def install_solo_driver(mage_tests_dir: Path) -> None:
    src = REPO_ROOT / "sim" / "analysis" / "xmage_adapter" / "SoloGoldfishSnapshotTest.java"
    dst_dir = mage_tests_dir / "src" / "test" / "java" / "org" / "mage" / "test" / "commander" / "duel"
    dst_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(src, dst_dir / src.name)


def run_chunk(mage_dir: Path, seeds, turns, deck_name: str, skill: int, timeout_s: int) -> str:
    cmd = [
        "mvn", "-q", "-o", "-pl", "Mage.Tests", "test",
        "-Dtest=SoloGoldfishSnapshotTest",
        f"-Ddiag.seeds={','.join(str(s) for s in seeds)}",
        f"-Ddiag.turns={','.join(str(t) for t in turns)}",
        f"-Ddiag.deck={deck_name}",
        f"-Ddiag.skill={skill}",
    ]
    log_path = mage_dir / "Mage.Tests" / "magetest.log"
    if log_path.exists():
        log_path.unlink()
    try:
        subprocess.run(cmd, cwd=str(mage_dir), capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        pass
    return log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""


def parse_snapshots(raw_log: str):
    records = []
    for line in raw_log.splitlines():
        m = LOG_LINE_RE.match(line)
        msg = m.group("msg") if m else line
        sm = SNAPSHOT_RE.match(msg) if msg else None
        if sm:
            records.append({
                "seed": int(sm.group(1)), "turn": int(sm.group(2)), "life": int(sm.group(3)),
                "library_size": int(sm.group(4)),
                "hand": [c for c in sm.group(5).split("|") if c],
                "battlefield": [c for c in sm.group(6).split("|") if c],
                "graveyard": [c for c in sm.group(7).split("|") if c],
                "exile": [c for c in sm.group(8).split("|") if c],
            })
    return records


def cards_ever_seen(rec):
    """Union of card names that have been in hand/battlefield/graveyard/exile at this checkpoint -
    i.e. everything drawn (or fetched) up to this point, regardless of what happened to it since."""
    return set(rec["hand"]) | set(rec["battlefield"]) | set(rec["graveyard"]) | set(rec["exile"])


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decklist", default=str(REPO_ROOT / "data" / "decklists" / "tymna-thrasios-treefarm-v1.json"))
    ap.add_argument("--mage-dir", required=True)
    ap.add_argument("--seed-start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--turns", default="1,3,5,7,10")
    ap.add_argument("--chunk-size", type=int, default=10)
    ap.add_argument("--skill", type=int, default=6)
    ap.add_argument("--batch-id", default=None)
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "results" / "solo_baseline"))
    ap.add_argument("--chunk-timeout", type=int, default=280)
    args = ap.parse_args()

    decklist_path = Path(args.decklist)
    mage_dir = Path(args.mage_dir)
    mage_tests_dir = mage_dir / "Mage.Tests"
    dck_name = "TymnaThrasiosTreefarm.dck"
    turns = [int(t) for t in args.turns.split(",")]

    payload = load_and_verify(decklist_path)
    (mage_tests_dir / dck_name).write_text(to_dck(payload), encoding="utf-8")
    install_solo_driver(mage_tests_dir)

    batch_id = args.batch_id or f"solo-goldfish-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    seeds = list(range(args.seed_start, args.seed_start + args.count))

    all_records = []
    for chunk_idx, seed_chunk in enumerate(chunked(seeds, args.chunk_size)):
        raw_log = run_chunk(mage_dir, seed_chunk, turns, dck_name, args.skill, args.chunk_timeout)
        recs = parse_snapshots(raw_log)
        all_records.extend(recs)
        print(f"chunk {chunk_idx}: {len(seed_chunk)} seeds x {len(turns)} turns -> {len(recs)} snapshots recovered")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_out = out_dir / f"{batch_id}-raw_snapshots.json"
    raw_out.write_text(json.dumps({
        "batch_id": batch_id, "run_class": "DECK_BACKED_GOLDFISH",
        "subject_deck_version": payload["deck_version"], "subject_deck_hash": payload["deck_hash"],
        "ai_skill": args.skill, "seed_start": args.seed_start, "count": args.count, "turns": turns,
        "snapshots": all_records,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {raw_out} ({len(all_records)} snapshots)")


if __name__ == "__main__":
    main()
