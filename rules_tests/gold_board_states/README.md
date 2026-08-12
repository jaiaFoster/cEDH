Gate 2 fixtures conforming to `data/schemas/gold_board_state.schema.json`.
Always `run_class: SYNTHETIC_GOLD_STATE` per `docs/RUN_CLASSIFICATION.md` —
these validate legality/sequencing and never contribute to empirical
deck-performance statistics, regardless of how deck-faithful their setup
looks.

- **`GBS-0001`** — Devoted Druid + Swift Reconfiguration (backs `INT-0002`,
  now `interactions/verified/`). Cross-checked against a from-source XMage
  build, 1/1 passing.
