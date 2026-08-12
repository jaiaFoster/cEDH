See `../README.md`. Only interactions validated per Level 4 (rules citations
+, where possible, independent executable-engine reproduction) belong here.

- **`INT-0002`** — Devoted Druid + Swift Reconfiguration → infinite green
  mana. Verified 2026-08-12: Comprehensive Rules citations (CR 613.1d layer
  4 type-changing, CR 704.5f toughness-0 SBA, CR 121 counters, CR 702.121
  crew) plus independent reproduction in a from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DevotedDruidSwiftReconfigurationTest`,
  1/1 passing). Backing gold board state: `rules_tests/gold_board_states/GBS-0001.json`.
- **`INT-0013`** — Delney, Streetwise Lookout doubles Kinnan, Bonder
  Prodigy's own triggered mana ability → **+2 mana per qualifying nonland
  mana activation** (not a multiplier of the source's own output — see the
  correction note below). Verified 2026-08-12: Comprehensive Rules
  citations (CR 603.2d triggers-additional-time mechanic, CR 605.1b
  criteria for a triggered ability to itself be a mana ability, CR
  605.4/605.4a triggered mana abilities skip the stack) plus independent
  reproduction in the same from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DelneyKinnanTripleManaTest` for a
  1-mana source, `...DelneyKinnanSolRingPlusTwoTest` for a 2-mana source,
  both 1/1 passing). Backing gold board states:
  `rules_tests/gold_board_states/GBS-0002.json` (Devoted Druid, 1 → 3) and
  `rules_tests/gold_board_states/GBS-0003.json` (Sol Ring, 2 → 4).
  **Correction (2026-08-12):** the initial writeup described this as
  "tripling nonland mana," generalized from the Devoted Druid (1-mana)
  case. That is wrong as a general model — Kinnan's granted trigger adds a
  flat one mana per instance regardless of the source's own output, so the
  correct model is `total = source's own mana + 2`. It only triples
  1-mana sources; Sol Ring (2 mana) yields 4, not 6, and Mana Vault
  (3 mana) yields 5, not 9. `GBS-0003.json` exists specifically to
  engine-verify this and prevent the "triples everything" abstraction
  from recurring.

The other 12 candidates found so far (`interactions/candidate/`) remain
unverified — see `coverage_backlog/BACKLOG.md` `SIM-0007`.
