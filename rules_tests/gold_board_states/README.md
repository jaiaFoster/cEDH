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
- **`GBS-0005`** — Delney, Streetwise Lookout + Esper Sentinel (backs
  `INT-0008`). Doubled "draw unless pay {X}" tax, opponent unable to pay
  either instance: 2 draws instead of 1. 1/1 passing.
- **`GBS-0006`** — Delney, Streetwise Lookout + Runic Armasaur (backs
  `INT-0009`). Doubled optional "may draw" trigger off an opponent's
  non-mana land ability, both accepted: 2 draws instead of 1. 1/1 passing
  on the first attempt.
- **`GBS-0007`** — Delney, Streetwise Lookout + Spellseeker (backs
  `INT-0010`). Doubled ETB tutor trigger finds two *different* cards (Opt
  and Shock) via two independently-targeted searches — the strongest
  available demonstration that Delney's doubled instances are genuinely
  independent, not collapsible into one. 1/1 passing on the first attempt.
- **`GBS-0008`** — Delney, Streetwise Lookout + Archivist of Oghma (backs
  `INT-0014`). Doubled mandatory life-gain-and-draw trigger off an
  opponent's library search: 2 life + 2 cards instead of 1 and 1 (no
  target/mode/choice to preserve here, unlike the other four Delney
  doublings above). 1/1 passing on the first attempt.

**`GBS-0005`..`GBS-0008` are all subject to the decision-space-fidelity
modeling requirement in `docs/ARCHITECTURE.md` Layer 2**: each records one
valid outcome of a doubled trigger's decision tree (a specific choice of
targets/pay-or-decline/may-or-not), not license to encode the interaction
as a single atomic aggregate effect when it is later wired into Layer 5.
