Gate 3 fixtures conforming to `data/schemas/gold_game.schema.json`. Small set
sufficient for diagnostic-simulation readiness (see `docs/VALIDATION_GATES.md`);
per that gate's own exit criteria, deliberately constructed opponent actions
are acceptable here - the purpose is proving whole-game sequencing, not
estimating win rate.

- **`GG-0001`** — Baseline sequencing sanity check: turn-1 draw skip,
  land-drop limit, first commander cast (no tax), summoning sickness in a
  live multi-turn context. No winner (not played to a conclusion).
- **`GG-0002`** — Full combo line to a real win: tutor, deploy, lose the
  piece to removal, recur it via Hazel's Brewmaster (`INT-0003`), loop
  infinite green mana, Finale of Devastation overrun, win by combat damage.
  Exercises tutoring, graveyard transitions, activated-ability looping,
  combat, and win recognition via state-based action, not assumed victory.
- **`GG-0003`** — Disrupted line, correct non-win: a Birthing Pod chain and
  an attempted Hazel's Brewmaster cast countered mid-stack. Proves the
  simulator doesn't hallucinate a win when a combo is legitimately stopped,
  and continues correctly afterward (second Pod activation still legal).

All three use `synthetic-generic-opponent-v1` as seat 2's deck version - a
non-ingested, deliberately constructed opponent, not a frozen decklist.
Deck-performance statistics must never cite these games (`run_class:
SYNTHETIC_RULES_TEST`, `representative_of_deck_draws: false`).
