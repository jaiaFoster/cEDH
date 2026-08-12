# Validation gates

Per charter ("Validation-first development"). This document tracks gate
status for the instrument as a whole. Each gate must pass before the next is
attempted; a gate is "passed" only when its exit criteria are met and
recorded here with a date and a link to the evidence (test run output, PR,
inspection notes).

**No production simulation (Gate 7, or arguably any gate past 1) may be
described as producing publishable evidence until this file shows Gates 1–6
passed for the specific model version and deck version in question.**

## Gate status

| Gate | Description | Status | Evidence | Date |
|---|---|---|---|---|
| 1 | Card & rule coverage | **Sufficient for diagnostic simulation** | All 100 cards (98 + 2 commanders) bulk-ingested from Scryfall with full Oracle text, mana cost, color identity, and rulings (`data/cards_cache/oracle-2026-08-12/`, `data/decklists/tymna-thrasios-treefarm-v1.json`, frozen with a canonical `deck_hash`). Zero color-identity violations. Interaction discovery: 15 candidates found and ALL resolved to `status: verified` - zero remain in `interactions/candidate/`. 9 `ENGINE_EXACT_VERIFIED`/`ENGINE_COMPONENT_VERIFIED` (XMage-reproduced), 6 `RULES_VERIFIED` (exact primary-Oracle-text mana accounting, not yet engine-reproduced but non-blocking - see `docs/VERIFICATION_LEVELS.md`). `conditional: true` + `conditions` on the 3 Smothering Tithe lines (`INT-0001`/`0004`/`0005`) makes their opponent-dependence machine-checkable rather than silently assumed. Forge and XMage both confirmed 100/100 card coverage (`INFRA-0002`); XMage proven as a working Level 4 substrate. Residual, non-blocking: `SIM-0012` (Derevi multi-attacker scaling, narrowly scoped, base case solid), `INT-0012`'s exact copy-transition gap (component-verified only), MTGJSON cross-validation (deliberately scoped out, see `docs/assignments/SIM-001.md`). Ability classification is heuristic, not manually reviewed - acceptable for diagnostic play; would need tightening before production claims. | 2026-08-12 |
| 2 | Gold board states | **Sufficient for diagnostic simulation** | 20/20 gold board states passing (`GBS-0001`..`GBS-0020`). `GBS-0001`..`GBS-0010` (engine-cross-checked against a from-source XMage build) cover the Delney-doubling cluster, `INT-0002`/`0011`/`0012`/`0013` and the matched 1-mana/2-mana source pair guarding against an over-generalized mana model. `GBS-0011`..`GBS-0020` (rules-grounded, undisputed CR applications, no engine check required per this gate's own exit criteria) close every remaining charter minimum-list item: summoning sickness, convoke, pitch costs, tutor restrictions, Pod restriction boundary, graveyard movement, protection (via hexproof/ward — the deck's actual analogue), stack interaction, plus the opponent-tax "pay" branch, win recognition, and commander-zone behavior. `GBS-0005`..`GBS-0008` remain subject to the decision-space-fidelity modeling requirement in `docs/ARCHITECTURE.md` Layer 2. | 2026-08-12 |
| 3 | Gold games | **Sufficient for diagnostic simulation** | 3/3 gold games in `rules_tests/gold_games/` (`GG-0001`..`GG-0003`), constructed against the real subject deck (`tymna-thrasios-treefarm-v1`) with a deliberately-constructed synthetic opponent per this gate's own exit criteria. `GG-0001` proves baseline turn/priority/commander-tax/summoning-sickness sequencing; `GG-0002` proves a full combo-to-win line (tutor → removal → `INT-0003` recursion → infinite mana → overrun → win-recognition-by-state-based-action, not assumed victory); `GG-0003` proves the negative case - a legitimately countered combo attempt correctly yields no winner. Together these exercise every item on the charter's Gate 3 list except direct Chord-of-Calling-into-Pod sequencing and multi-opponent seating, both non-blocking for a diagnostic-scale first run. | 2026-08-12 |
| 4 | ~100 manually inspected games | Not started | depends on Gate 3 | — |
| 5 | ~1,000 game validation run | Not started | depends on Gate 4 | — |
| 6 | ~10,000 game medium run | Not started | depends on Gate 5 | — |
| 7 | 100,000+ / million-game production run | Not started | depends on Gate 6 | — |

## Exit criteria per gate

### Gate 1 — Card & rule coverage
- Subject deck (and, once assigned, opponent decks) resolved to current
  Oracle data with rulings ingested.
- Every card classified: types, abilities (activated/triggered/static/
  replacement/mana), tutor restrictions, zone dependencies, timing
  restrictions, alternative costs.
- Interaction discovery pass complete: known combos/loops identified via
  Commander Spellbook + independent pair/triple/higher-order search.
- `interactions/candidate/` populated; nothing yet required in
  `interactions/verified/` at this gate.
- **Exit:** a card-rules cache file per deck version in `data/cards_cache/`,
  and a discovery-pass report attached to this gate's evidence column.

### Gate 2 — Gold board states
- Hand-authored states in `rules_tests/gold_board_states/` covering (at
  minimum, per charter): mana production, summoning sickness, convoke, pitch
  costs, tutors, Pod-style restrictions, activated abilities, graveyard
  movement, at least one full combo loop, protection, stack interaction.
- Each state has a manually-determined expected legal-action set and/or
  expected outcome, and (where the interaction is legality-disputed or
  complex) independent agreement from an executable engine per
  `docs/SOURCES.md` Tier 2.
- **Exit:** simulator reproduces the expected legal actions/outcomes for
  every gold board state, with mismatches either fixed or logged to
  `coverage_backlog/BACKLOG.md` and blocking gate closure if the mismatch is
  in a state relevant to the modeled deck.

### Gate 3 — Gold games
- A small set (target: high single digits to low double digits) of
  manually-reviewed full game sequences in `rules_tests/gold_games/`.
- Verified: legal actions throughout, mana correctness, zone changes,
  sequencing, commander-specific behavior (color identity, tax, command
  zone movement), interaction resolution, correct win recognition.
- **Exit:** simulator reproduces each gold game's sequence of legal
  states/actions exactly, or documented deviations are understood and
  acceptable (e.g. policy choosing a different *legal* line than the
  human-authored one — that's a policy question, not a rules failure, and
  must be labeled as such rather than treated as a bug).

### Gate 4 — Manually inspected simulations (~100 games)
- Run ~100 games at the target rules-awareness level.
- Manual inspection log covering: illegal actions, nonsensical tutors,
  absurd counterspell usage, missed obvious wins, impossible mana, commander
  misuse, broken priority logic, incorrect threat assessment.
- **Exit:** systemic problems found are fixed (not patched around) and,
  where they represent a rules or policy bug, a permanent regression test is
  added to `rules_tests/regression/` before re-running.

### Gate 5 — Small validation run (~1,000 games)
- Distributions analyzed against expected archetype behavior and any
  available observable tournament patterns.
- Extreme contradictions (not just any disagreement) investigated to a
  mechanistic explanation before proceeding.
- **Exit:** either agreement is understood, or disagreement is documented as
  a finding-in-progress with a stated hypothesis for the cause.

### Gate 6 — Medium run (~10,000 games)
- Policy sensitivity analysis, matchup sanity checks, seat sanity checks,
  interaction audits, unknown-state analysis.
- **Exit:** sensitivity results recorded; no open high-impact unknown-state
  backlog items from this run's own logging.

### Gate 7 — Large run (100,000+ / million-game)
- Only attempted after Gates 1–6 pass for the exact model+deck version being
  scaled.
- **Exit:** output may be cited as publishable model output, always still
  carrying its full confidence-reporting block per `docs/VERSIONING.md`.

