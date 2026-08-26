"""Schema-conformance regression tests.

These are real, running checks (not placeholders): every schema file must
itself be valid JSON Schema, and every data file that currently exists in
the repo (there isn't much yet - mainly coverage_backlog/backlog.jsonl) must
validate against the schema that governs it. As data/decklists/,
data/cards_cache/, interactions/, rules_tests/gold_board_states/, etc. get
populated in future sessions, this file's directory->schema map is what
keeps them honest - add a new mapping entry rather than a one-off test when
a new artifact type's directory goes from empty to populated.
"""
import glob
from pathlib import Path

import jsonschema
import pytest

from conftest import load_json, load_jsonl, REPO_ROOT, SCHEMAS_DIR

# (glob pattern relative to repo root, schema filename, loader)
# loader is "json" for one-object-per-file, "jsonl" for one-object-per-line.
DIRECTORY_SCHEMA_MAP = [
    ("data/decklists/*.json", "decklist.schema.json", "json"),
    ("data/deck_sources/**/current.json", "deck_source_snapshot.schema.json", "json"),
    ("data/deck_sources/**/history/*.json", "deck_source_snapshot.schema.json", "json"),
    ("data/tournament_snapshots/topdeck/normalized/*.json", "topdeck_tournament.schema.json", "json"),
    ("data/cards_cache/**/*.json", "card.schema.json", "json"),
    ("data/archetypes/**/*.json", "archetype.schema.json", "json"),
    ("data/policies/**/*.json", "policy.schema.json", "json"),
    ("interactions/verified/*.json", "interaction.schema.json", "json"),
    ("interactions/candidate/*.json", "interaction.schema.json", "json"),
    ("rules_tests/gold_board_states/*.json", "gold_board_state.schema.json", "json"),
    ("rules_tests/gold_games/*.json", "gold_game.schema.json", "json"),
    ("results/raw/*/config.json", "simulation_result.schema.json", "json"),
    ("coverage_backlog/backlog.jsonl", "coverage_backlog_entry.schema.json", "jsonl"),
]


def _all_schema_files():
    return sorted(SCHEMAS_DIR.glob("*.schema.json"))


@pytest.mark.parametrize("schema_path", _all_schema_files(), ids=lambda p: p.name)
def test_schema_itself_is_valid_json_schema(schema_path: Path):
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)


def _iter_data_files_for(pattern: str):
    matches = glob.glob(str(REPO_ROOT / pattern), recursive=True)
    return sorted(Path(m) for m in matches)


@pytest.mark.parametrize("pattern,schema_name,loader", DIRECTORY_SCHEMA_MAP,
                          ids=[m[0] for m in DIRECTORY_SCHEMA_MAP])
def test_existing_data_files_conform_to_schema(pattern, schema_name, loader):
    schema_path = SCHEMAS_DIR / schema_name
    assert schema_path.exists(), f"referenced schema {schema_name} does not exist"
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)

    data_files = _iter_data_files_for(pattern)
    if not data_files:
        pytest.skip(f"no files matching {pattern} yet - nothing to validate")

    for data_file in data_files:
        if loader == "json":
            instance = load_json(data_file)
            errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
            assert not errors, (
                f"{data_file} fails {schema_name}:\n"
                + "\n".join(f"  - {'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors)
            )
        elif loader == "jsonl":
            records = load_jsonl(data_file)
            for i, record in enumerate(records):
                errors = sorted(validator.iter_errors(record), key=lambda e: e.path)
                assert not errors, (
                    f"{data_file} line {i + 1} fails {schema_name}:\n"
                    + "\n".join(f"  - {'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors)
                )
        else:
            raise ValueError(f"unknown loader {loader!r}")
