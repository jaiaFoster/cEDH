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
| 1 | Card & rule coverage | **In progress** | Network unblocked 2026-08-12; all 100 cards (98 + 2 commanders) bulk-ingested from Scryfall with full Oracle text, mana cost, color identity, and rulings (`data/cards_cache/oracle-2026-08-12/`, `data/decklists/tymna-thrasios-treefarm-v1.json`, now frozen with a canonical `deck_hash`). Ability classification is heuristic, not manually reviewed. Interaction discovery: 14 candidates found (Commander Spellbook + independent pairwise/manual scans), **2 (`INT-0002`, `INT-0013`) now Level 4 verified** (CR citations + independent XMage reproduction) — 12 remain (`SIM-0007`). Forge and XMage both confirmed 100/100 card coverage (`INFRA-0002`); XMage proven as a working Level 4 substrate (`INFRA-0003`, resolved). Still open before this gate can close: validate the remaining 12 candidates, expand independent interaction discovery further (Survival of the Fittest chains, deeper graveyard recursion, bounce/replay, remaining copy-effect targets), MTGJSON cross-validation (deliberately scoped out for now, see `docs/assignments/SIM-001.md`). | 2026-08-12 |
| 2 | Gold board states | **In progress** | 3/3 gold board states passing (`GBS-0001`, `GBS-0002`, `GBS-0003`, all cross-checked against a from-source XMage build), covering `combo_loop`/`activated_ability`. `GBS-0002`/`GBS-0003` are a matched pair (1-mana vs. 2-mana nonland source) specifically guarding against an over-generalized mana-model abstraction — see `interactions/verified/INT-0013.json`. Not yet closable — charter's Gate 2 minimum list (mana production, summoning sickness, convoke, pitch costs, tutors, Pod restrictions, graveyard movement, protection, stack interaction) needs many more fixtures first. | 2026-08-12 |
| 3 | Gold games | Not started | depends on Gate 2 | — |
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

## Current blocker

Everything downstream of Gate 1 is blocked on two things, tracked in
`coverage_backlog/BACKLOG.md`:
1. `ENV-0001` — no network path from this environment to any card/rules/
   tournament data source.
2. The subject decklist itself has not been supplied to this repository yet.

Neither is a reason to lower fidelity or fabricate placeholder data to "get
something running" — per charter, "current simulation fidelity is
insufficient to answer this question" is a valid and expected state right
now.
