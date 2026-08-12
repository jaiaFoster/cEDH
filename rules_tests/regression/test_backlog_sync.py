"""coverage_backlog/README.md requires BACKLOG.md and backlog.jsonl to stay
in sync by hand. This test catches drift immediately instead of letting the
two files silently diverge over time.
"""
import re

from conftest import REPO_ROOT, load_jsonl

BACKLOG_MD = REPO_ROOT / "coverage_backlog" / "BACKLOG.md"
BACKLOG_JSONL = REPO_ROOT / "coverage_backlog" / "backlog.jsonl"

# Matches only the ID *column* of a table row (start of line, first cell),
# e.g. "| SIM-0007 | INTERACT | ...". Deliberately does NOT match an ID
# mentioned in prose elsewhere in a row (e.g. a SIM-* row's summary text
# referencing an unrelated INT-* interaction ID) - see the incident this
# guarded against: SIM-0007's summary mentions INT-0001/INT-0006, which are
# interaction registry IDs, not backlog entries, and must not be required to
# exist in backlog.jsonl.
ID_PATTERN = re.compile(r"^\|\s*([A-Z]+-\d{4,})\s*\|", re.MULTILINE)


def _ids_in_markdown() -> set[str]:
    text = BACKLOG_MD.read_text(encoding="utf-8")
    return set(ID_PATTERN.findall(text))


def _ids_by_markdown_section() -> dict[str, set[str]]:
    """Splits BACKLOG.md on its '## Open' / '## Resolved' headers and returns the set of IDs
    found under each, so a status/section mismatch (an entry marked resolved in backlog.jsonl
    but still sitting in the '## Open' table, or vice versa) can be caught mechanically instead
    of only by a human noticing during review — see the SIM-0006 incident this guards against:
    it was marked resolved in backlog.jsonl but left in BACKLOG.md's Open table (and missing
    from Resolved entirely), which the earlier, section-blind version of this test suite did
    not catch.
    """
    text = BACKLOG_MD.read_text(encoding="utf-8")
    sections: dict[str, set[str]] = {}
    current = None
    buffer: list[str] = []
    for line in text.splitlines():
        header = re.match(r"^##\s+(Open|Resolved)\s*$", line)
        if header:
            if current is not None:
                sections[current] = set(ID_PATTERN.findall("\n".join(buffer)))
            current = header.group(1)
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = set(ID_PATTERN.findall("\n".join(buffer)))
    return sections


def _ids_in_jsonl() -> set[str]:
    return {record["id"] for record in load_jsonl(BACKLOG_JSONL)}


def _status_by_id_in_jsonl() -> dict[str, str]:
    return {record["id"]: record["status"] for record in load_jsonl(BACKLOG_JSONL)}


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


def test_resolved_status_entries_are_in_the_resolved_markdown_section():
    """Permanent regression test for the SIM-0006 incident: an entry marked resolved in
    backlog.jsonl must appear in BACKLOG.md's '## Resolved' table, not (only, or at all) in
    '## Open'.
    """
    sections = _ids_by_markdown_section()
    status_by_id = _status_by_id_in_jsonl()
    open_ids = sections.get("Open", set())
    resolved_ids = sections.get("Resolved", set())

    wrongly_in_open = {i for i in open_ids if status_by_id.get(i) == "resolved"}
    assert not wrongly_in_open, (
        f"These entries are status=resolved in backlog.jsonl but appear in BACKLOG.md's "
        f"'## Open' table: {wrongly_in_open}"
    )

    missing_from_resolved = {i for i, s in status_by_id.items() if s == "resolved"} - resolved_ids
    assert not missing_from_resolved, (
        f"These entries are status=resolved in backlog.jsonl but are missing from BACKLOG.md's "
        f"'## Resolved' table: {missing_from_resolved}"
    )


def test_open_status_entries_are_in_the_open_markdown_section():
    sections = _ids_by_markdown_section()
    status_by_id = _status_by_id_in_jsonl()
    resolved_ids = sections.get("Resolved", set())
    open_ids = sections.get("Open", set())

    wrongly_in_resolved = {i for i in resolved_ids if status_by_id.get(i) != "resolved"}
    assert not wrongly_in_resolved, (
        f"These entries appear in BACKLOG.md's '## Resolved' table but are NOT status=resolved "
        f"in backlog.jsonl: {wrongly_in_resolved}"
    )

    non_resolved_ids = {i for i, s in status_by_id.items() if s != "resolved"}
    missing_from_open = non_resolved_ids - open_ids
    assert not missing_from_open, (
        f"These entries are not status=resolved in backlog.jsonl but are missing from "
        f"BACKLOG.md's '## Open' table: {missing_from_open}"
    )
