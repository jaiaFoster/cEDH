# Regression tests

Per charter "Regression testing": every discovered rules or major policy bug
becomes a permanent test here, so the system never repeatedly relearns the
same lesson. Nothing has been discovered yet (no gameplay exists), so this
directory currently holds only the **schema-conformance framework** that
every future gold board state, gold game, and data record will be checked
against — real, running tests, not placeholders.

## Running

```
pip install -r requirements.txt
pytest rules_tests/regression -v
```

## What's here now

- `test_schemas.py` — every file under `data/schemas/*.schema.json` is
  itself valid JSON Schema (Draft 2020-12), and every existing data file
  under `data/`, `interactions/`, `rules_tests/gold_board_states/`,
  `rules_tests/gold_games/`, and `coverage_backlog/backlog.jsonl` validates
  against its corresponding schema. Run this after adding *any* data file —
  a schema/data mismatch should fail CI immediately, not surface three
  layers deep during a simulation run.
- `test_backlog_sync.py` — `coverage_backlog/BACKLOG.md` and
  `coverage_backlog/backlog.jsonl` must reference the same set of entry IDs
  (per `coverage_backlog/README.md`'s requirement that they stay in sync).
- `conftest.py` — shared fixtures (repo root, schema loader).

## What goes here later

Once Gate 2 (gold board states) and Gate 3 (gold games) start, and once any
rules/policy bug is found during Gate 4+ simulation runs, add a dedicated
test file per bug (e.g. `test_GBS-0007_convoke_tapped_creature.py` or
similar, named after the coverage_backlog ID that tracked it) rather than
growing one giant file — each regression should be traceable back to the
backlog entry and gold fixture that caused it to be written.
