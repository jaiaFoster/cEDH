See `../README.md`. Only interactions validated per Level 4 (rules citations
+, where possible, independent executable-engine reproduction) belong here.

**As of 2026-08-12, every entry also carries a `verification_level`** (see
`docs/VERIFICATION_LEVELS.md` for the full taxonomy, prompted by a real
incident with `INT-0012` below): `ENGINE_EXACT_VERIFIED` means the
interaction's own exact stated transition was reproduced end-to-end in an
executable engine; `ENGINE_COMPONENT_VERIFIED` means a downstream
consequence or necessary component was engine-reproduced but not the exact
transition itself; `RULES_VERIFIED` means CR/Oracle citations alone, no
engine evidence; `CONDITIONAL` means verified only under a stated
condition (most often, an opponent choice this deck doesn't control).
`status: verified` alone does not distinguish these — check the tag on
each entry below, not just its presence in this directory.

- **`INT-0002`** — `ENGINE_EXACT_VERIFIED`. Devoted Druid + Swift
  Reconfiguration → infinite green mana. Verified 2026-08-12: Comprehensive
  Rules citations (CR 613.1d layer 4 type-changing, CR 704.5f toughness-0
  SBA, CR 121 counters, CR 702.121 crew) plus independent reproduction in a
  from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DevotedDruidSwiftReconfigurationTest`,
  1/1 passing). Backing gold board state: `rules_tests/gold_board_states/GBS-0001.json`.
- **`INT-0013`** — `ENGINE_EXACT_VERIFIED`. Delney, Streetwise Lookout
  doubles Kinnan, Bonder Prodigy's own triggered mana ability → **+2 mana
  per qualifying nonland mana activation** (not a multiplier of the
  source's own output — see the correction note below). Verified
  2026-08-12: Comprehensive Rules citations (CR 603.2d triggers-additional-
  time mechanic, CR 605.1b criteria for a triggered ability to itself be a
  mana ability, CR 605.4/605.4a triggered mana abilities skip the stack)
  plus independent reproduction in the same from-source XMage build
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
- **`INT-0007`** — `ENGINE_EXACT_VERIFIED`. Delney, Streetwise Lookout
  doubles Orcish Bowmasters' compound ETB/opponent-draw trigger → 2 damage
  + Amass Orcs 2 (a single Army token with 2 +1/+1 counters, per CR
  701.47a) instead of 1 and 1. Verified 2026-08-12: Comprehensive Rules
  citations (CR 603.2d triggers-additional-time mechanic, CR 603.3b
  ordering simultaneously-pending triggered abilities, CR 701.47a amass)
  plus independent reproduction in the same from-source XMage build
  (`org.mage.test.cards.interactions.cedh.DelneyOrcishBowmastersDoubleTest`,
  1/1 passing). Backing gold board state:
  `rules_tests/gold_board_states/GBS-0004.json`.
- **`INT-0008`** — `ENGINE_EXACT_VERIFIED`. Delney doubles Esper Sentinel's
  tax trigger → two independent "draw unless the caster pays {X}"
  decisions per qualifying spell instead of one. Verified 2026-08-12 (CR
  603.2d, 603.3b; XMage `DelneyEsperSentinelDoubleTest`, 1/1). Backing gold
  board state: `GBS-0005.json`.
- **`INT-0009`** — `ENGINE_EXACT_VERIFIED`. Delney doubles Runic Armasaur's
  "may draw" trigger → two independent optional-draw decisions per
  qualifying opponent activation instead of one. Verified 2026-08-12 (CR
  603.2d, 603.3b; XMage `DelneyRunicArmasaurDoubleTest`, 1/1 on first
  attempt). Backing gold board state: `GBS-0006.json`.
- **`INT-0010`** — `ENGINE_EXACT_VERIFIED`. Delney doubles Spellseeker's
  ETB tutor trigger → two independently-targeted library searches per
  resolution, engine-confirmed capable of finding two *different* cards in
  one Spellseeker resolution. Verified 2026-08-12 (CR 603.2d, 603.3b; XMage
  `DelneySpellseekerDoubleTest`, 1/1 on first attempt, found Opt and Shock
  simultaneously). Backing gold board state: `GBS-0007.json`.
- **`INT-0014`** — `ENGINE_EXACT_VERIFIED`. Delney doubles Archivist of
  Oghma's mandatory life-gain-and-draw trigger → 2 life + 2 cards per
  qualifying opponent library search instead of 1 and 1 (no target/mode/
  choice to preserve here, unlike the other four Delney doublings).
  Verified 2026-08-12 (CR 603.2d, 603.3b; XMage
  `DelneyArchivistOfOghmaDoubleTest`, 1/1 on first attempt). Backing gold
  board state: `GBS-0008.json`.

**Modeling requirement for all five Delney-doubling interactions above**
(`INT-0007`, `0008`, `0009`, `0010`, `0014`), established 2026-08-12 per
user review and recorded in `docs/ARCHITECTURE.md` Layer 2: a future
Layer 5 (Simulation) encoding must represent each doubled trigger as two
genuinely independent instances — separate targets, separate optional
choices, separate ordering — not a single atomic "2x" aggregate effect.
The single-outcome gold board states above are valid evidence the
*results* reproduce correctly; they are not license to collapse the
decision tree when this is later encoded for policy/simulation.

- **`INT-0011`** — `ENGINE_EXACT_VERIFIED` *for the single-attacker case
  only*. Derevi, Empyrial Tactician + Gaea's Cradle → one bonus Cradle
  activation from a single connecting attacker (Derevi's combat-damage
  trigger untaps a previously-tapped Cradle, which is then tapped again
  for mana within the same combat damage step). Verified 2026-08-12 (CR
  500.5/106.4 mana-pool timing, CR 603.2c an ability triggers once per
  occurrence of its trigger event, CR 603.3b ordering of simultaneously-
  pending triggers, CR 117.3b the active player receives priority after
  each ability resolves — the specific mechanism that lets Cradle be
  tapped again between trigger resolutions; XMage `DereviGaeasCradleTest`,
  1/1). Backing gold board state: `GBS-0010.json`. **Scope note:** the
  original candidate writeup's claim that this "scales with attacker
  count" (N attackers → N untap cycles) is *not* itself engine-verified —
  a two-attacker extension attempt did not succeed within the effort
  budget for this interaction and is tracked as open item
  `coverage_backlog` `SIM-0012`. Treat the scaling claim as plausible
  (supported by the same CR mechanics cited above) but unconfirmed, not as
  established fact — this record's own `verification_level` and
  `result.summary` are scoped to only the single-attacker case that was
  actually reproduced.
- **`INT-0012`** — `ENGINE_COMPONENT_VERIFIED`, **not**
  `ENGINE_EXACT_VERIFIED` (corrected 2026-08-12 after user review — see
  below). Clever Impersonator copying Birthing Pod → a second,
  independently-activatable Birthing Pod (redundancy/throughput, not a new
  win condition). Rules-verified via CR 707.1/707.2 (copying acquires the
  original's copiable characteristics — including its Artifact card type
  and its activated ability — as values of the copy, not because Clever
  Impersonator's own printed text adds anything). Backing gold board
  state: `GBS-0009.json`.
  **Correction (2026-08-12):** two issues were caught by user review of
  the original writeup, both now fixed in `interactions/verified/INT-0012.json`:
  1. A factual rules-text error: the original said Clever Impersonator
     "becomes an artifact in addition to its other types" as part of its
     own text. That's wrong — Clever Impersonator's oracle text is only
     "You may have this creature enter as a copy of any nonland permanent
     on the battlefield." The Artifact type comes entirely from copying
     Birthing Pod's own copiable Artifact type (CR 707.2), not from any
     type-adding clause Clever Impersonator itself has.
  2. A validation-standard issue: the executable-engine test
     (`CleverImpersonatorBirthingPodTest`) does not reproduce Clever
     Impersonator's own copy transition (entering, choosing to copy
     Birthing Pod, becoming a functioning Pod) — it tests two literal
     Birthing Pod permanents instead, proving only the *downstream
     consequence* (two Pod-functioning permanents can each be
     independently activated in one turn). That's real, useful evidence,
     but it is not the same evidentiary strength as an exact reproduction
     of this interaction's own named transition, and the original record
     conflated the two. `verification_level: ENGINE_COMPONENT_VERIFIED`
     and `verification.executable_engine_check.exact_reproduction: false`
     now make this distinction explicit and machine-checkable (see
     `rules_tests/regression/test_verification_levels.py`, added as a
     permanent regression test for this exact incident). Per
     `docs/VERIFICATION_LEVELS.md`, this tier may inform an engine-driven
     simulation (where XMage/Forge actually plays out the real copy) but
     must not be hardcoded as a fixed transition in a native/lightweight
     tracker without further work.
  **Methodology note (preserved, still accurate):** driving the exact
  "cast Clever Impersonator, choose to copy" sequence through this
  project's usual setChoice/addTarget cost-payment approach proved
  unreliable for this specific `activateAbility()` call shape, which
  routes cost payment through an internal AI fallback (documented only in
  a `CardTestPlayerAPIImpl` source comment, not anywhere in XMage's own
  test-writing docs) — this is why the exact transition remains
  unreproduced rather than merely untried.

The other 5 candidates found so far (`interactions/candidate/`) remain
unverified — see `coverage_backlog/BACKLOG.md` `SIM-0007`.

## Tithe/Oboro group + final discovery sweep (2026-08-12)

- **`INT-0003`** — `RULES_VERIFIED`, `conditional: false`. Hazel's Brewmaster
  + Devoted Druid → infinite green mana on a Food token. Fully deck-
  controlled, no opponent dependency.
- **`INT-0001`** — `RULES_VERIFIED`, `conditional: true` (opponents must
  decline Smothering Tithe's tax on every draw). Faerie Mastermind +
  Smothering Tithe + Clever Impersonator (copying Tithe). Re-derived from
  primary Oracle text: mana-NEUTRAL at Spellbook's stated 2-opponent
  minimum (net 0 - repeatable "each player draws" engine, no accumulating
  mana); genuinely net-positive (+2/cycle) only at 3+ opponents.
- **`INT-0004`** — `RULES_VERIFIED`, `conditional: true`. Faerie Mastermind
  + Smothering Tithe + Kinnan. Net +2 mana/cycle at the stated 3-opponent
  threshold (Kinnan doubles each cracked Treasure).
- **`INT-0005`** — `RULES_VERIFIED`, `conditional: true`. Faerie Mastermind
  + Smothering Tithe + Training Grounds (reduces activation to {1}{U}). Net
  +1 mana/cycle at the stated 3-opponent threshold.
- **`INT-0006`** — `RULES_VERIFIED`, `conditional: false`. Oboro Breezecaller
  + Talon Gates of Madara + Gaea's Cradle. Corrected: mana-NEUTRAL (net =
  creatures - 5) at Spellbook's stated 5-creature threshold - infinite
  landfall/phase-out repetition holds there, but accumulating mana needs
  6+ creatures. Do not call the 5-creature case "infinite mana."
- **`INT-0015`** — `RULES_VERIFIED`, `conditional: false`. Delney doubles
  Badgermole Cub's triggered mana bonus → +2 green flat per creature-mana-
  tap (same shape as `INT-0013`). Found in the final discovery sweep.

All six of the above were re-derived directly from primary Oracle text
(not Commander Spellbook's paraphrase) with explicit per-cycle mana
arithmetic; none have yet been engine-reproduced (non-blocking for Gate 1
diagnostic-simulation sufficiency - see `docs/VALIDATION_GATES.md`).

**Zero interactions remain in `interactions/candidate/`.**
