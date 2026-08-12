# rules_tests/

Validation Gates 2-4 (`docs/VALIDATION_GATES.md`) and the permanent
regression suite.

- `gold_board_states/` — Gate 2 fixtures (`data/schemas/gold_board_state.schema.json`). Empty; blocked on the subject decklist.
- `gold_games/` — Gate 3 fixtures (`data/schemas/gold_game.schema.json`). Empty; blocked on Gate 2.
- `regression/` — permanent tests for every discovered rules/policy bug, plus the schema-conformance framework that's already running (see `regression/README.md`).
