See `../README.md`. Only interactions validated per Level 4 (rules citations
+, where possible, independent executable-engine reproduction) belong here.

- **`INT-0002`** — Devoted Druid + Swift Reconfiguration → infinite green
  mana. Verified 2026-08-12: Comprehensive Rules citations (CR 613.1d layer
  4 type-changing, CR 704.5f toughness-0 SBA, CR 121 counters, CR 702.121
  crew) plus independent reproduction in a from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DevotedDruidSwiftReconfigurationTest`,
  1/1 passing). Backing gold board state: `rules_tests/gold_board_states/GBS-0001.json`.
- **`INT-0013`** — Delney, Streetwise Lookout doubles Kinnan, Bonder
  Prodigy's own mana-doubling trigger → tripled nonland mana. Verified
  2026-08-12: Comprehensive Rules citations (CR 603.2d triggers-additional-
  time mechanic, CR 605.1b criteria for a triggered ability to itself be a
  mana ability, CR 605.4/605.4a triggered mana abilities skip the stack)
  plus independent reproduction in the same from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DelneyKinnanTripleManaTest`, 1/1
  passing on the first attempt). Backing gold board state:
  `rules_tests/gold_board_states/GBS-0002.json`.

The other 12 candidates found so far (`interactions/candidate/`) remain
unverified — see `coverage_backlog/BACKLOG.md` `SIM-0007`.
