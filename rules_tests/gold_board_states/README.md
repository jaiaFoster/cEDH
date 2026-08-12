Gate 2 fixtures conforming to `data/schemas/gold_board_state.schema.json`.
Always `run_class: SYNTHETIC_GOLD_STATE` per `docs/RUN_CLASSIFICATION.md` —
these validate legality/sequencing and never contribute to empirical
deck-performance statistics, regardless of how deck-faithful their setup
looks.

- **`GBS-0001`** — Devoted Druid + Swift Reconfiguration (backs `INT-0002`,
  now `interactions/verified/`). Cross-checked against a from-source XMage
  build, 1/1 passing.
- **`GBS-0002`** — Delney, Streetwise Lookout + Kinnan, Bonder Prodigy +
  Devoted Druid, a 1-mana nonland source (backs `INT-0013`, now
  `interactions/verified/`). 1 → 3 mana. Cross-checked against the same
  from-source XMage build, 1/1 passing.
- **`GBS-0003`** — Same combo as `GBS-0002` but with Sol Ring, a 2-mana
  nonland source (also backs `INT-0013`). 2 → 4 mana, deliberately added
  to rule out a "triples all sources" misreading of `GBS-0002`'s result —
  the correct model is `+2` flat, not a multiplier. Cross-checked against
  the same from-source XMage build, 1/1 passing.
- **`GBS-0004`** — Delney, Streetwise Lookout + Orcish Bowmasters (backs
  `INT-0007`, now `interactions/verified/`). Casting Orcish Bowmasters
  (Flash) so its ETB genuinely fires, doubled by Delney: 2 damage + Amass
  Orcs 2 (a single Army token with 2 +1/+1 counters, per CR 701.47a).
  Cross-checked against the same from-source XMage build, 1/1 passing.
