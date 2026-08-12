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
- **`INT-0007`** — Delney, Streetwise Lookout doubles Orcish Bowmasters'
  compound ETB/opponent-draw trigger → 2 damage + Amass Orcs 2 (a single
  Army token with 2 +1/+1 counters, per CR 701.47a) instead of 1 and 1.
  Verified 2026-08-12: Comprehensive Rules citations (CR 603.2d
  triggers-additional-time mechanic, CR 603.3b ordering simultaneously-
  pending triggered abilities, CR 701.47a amass) plus independent
  reproduction in the same from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DelneyOrcishBowmastersDoubleTest`,
  1/1 passing). Backing gold board state:
  `rules_tests/gold_board_states/GBS-0004.json`.
- **`INT-0008`** — Delney doubles Esper Sentinel's tax trigger → two
  independent "draw unless the caster pays {X}" decisions per qualifying
  spell instead of one. Verified 2026-08-12 (CR 603.2d, 603.3b; XMage
  `DelneyEsperSentinelDoubleTest`, 1/1). Backing gold board state:
  `GBS-0005.json`.
- **`INT-0009`** — Delney doubles Runic Armasaur's "may draw" trigger →
  two independent optional-draw decisions per qualifying opponent
  activation instead of one. Verified 2026-08-12 (CR 603.2d, 603.3b; XMage
  `DelneyRunicArmasaurDoubleTest`, 1/1 on first attempt). Backing gold
  board state: `GBS-0006.json`.
- **`INT-0010`** — Delney doubles Spellseeker's ETB tutor trigger → two
  independently-targeted library searches per resolution, engine-confirmed
  capable of finding two *different* cards in one Spellseeker resolution.
  Verified 2026-08-12 (CR 603.2d, 603.3b; XMage
  `DelneySpellseekerDoubleTest`, 1/1 on first attempt, found Opt and Shock
  simultaneously). Backing gold board state: `GBS-0007.json`.
- **`INT-0014`** — Delney doubles Archivist of Oghma's mandatory
  life-gain-and-draw trigger → 2 life + 2 cards per qualifying opponent
  library search instead of 1 and 1 (no target/mode/choice to preserve
  here, unlike the other four Delney doublings). Verified 2026-08-12 (CR
  603.2d, 603.3b; XMage `DelneyArchivistOfOghmaDoubleTest`, 1/1 on first
  attempt). Backing gold board state: `GBS-0008.json`.

**Modeling requirement for all five Delney-doubling interactions above**
(`INT-0007`, `0008`, `0009`, `0010`, `0014`), established 2026-08-12 per
user review and recorded in `docs/ARCHITECTURE.md` Layer 2: a future
Layer 5 (Simulation) encoding must represent each doubled trigger as two
genuinely independent instances — separate targets, separate optional
choices, separate ordering — not a single atomic "2x" aggregate effect.
The single-outcome gold board states above are valid evidence the
*results* reproduce correctly; they are not license to collapse the
decision tree when this is later encoded for policy/simulation.

The other 7 candidates found so far (`interactions/candidate/`) remain
unverified — see `coverage_backlog/BACKLOG.md` `SIM-0007`.
