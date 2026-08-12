"""coverage_backlog/README.md requires BACKLOG.md and backlog.jsonl to stay
in sync by hand. This test catches drift immediately instead of letting the
two files silently diverge over time.
"""
import re

from conftest import REPO_ROOT, load_jsonl

BACKLOG_MD = REPO_ROOT / "coverage_backlog" / "BACKLOG.md"
BACKLOG_JSONL = REPO_ROOT / "coverage_backlog" / "backlog.jsonl"

ID_PATTERN = re.compile(r"\b([A-Z]+-\d{4,})\b")


def _ids_in_markdown() -> set[str]:
    text = BACKLOG_MD.read_text(encoding="utf-8")
    return set(ID_PATTERN.findall(text))


def _ids_in_jsonl() -> set[str]:
    return {record["id"] for record in load_jsonl(BACKLOG_JSONL)}


def test_every_jsonl_entry_appears_in_markdown():
    md_ids = _ids_in_markdown()
    jsonl_ids = _ids_in_jsonl()
    missing = jsonl_ids - md_ids
    assert not missing, f"backlog.jsonl has entries not present in BACKLOG.md: {missing}"


def test_every_markdown_entry_appears_in_jsonl():
    md_ids = _ids_in_markdown()
    jsonl_ids = _ids_in_jsonl()
    missing = md_ids - jsonl_ids
    assert not missing, f"BACKLOG.md has entries not present in backlog.jsonl: {missing}"


def test_jsonl_has_no_duplicate_ids():
    records = load_jsonl(BACKLOG_JSONL)
    ids = [r["id"] for r in records]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"duplicate IDs in backlog.jsonl: {dupes}"
