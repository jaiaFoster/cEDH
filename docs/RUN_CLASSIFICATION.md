# Run classification — synthetic vs. deck-backed provenance

Added 2026-08-12 in response to a review of the first XMage validation test
(`INT-0002`, Devoted Druid + Swift Reconfiguration), which used arbitrary
Forest/Plains as mana scaffolding. That fixture was correct — the mana
*source* wasn't material to the rule being tested — but the review
correctly identified a gap: nothing in the instrument's provenance model
distinguished "a laboratory fixture built to test one rules question" from
"a game played with the actual subject deck," which is exactly the
distinction the charter's non-negotiable rule 5 ("Simulation is not
tournament data") demands be preserved. This document closes that gap.

**Every executable run this instrument produces — a gold-state check, a
Level 4 interaction reproduction, a future goldfish run, a future
four-player simulation — must declare a `run_class` from the taxonomy
below, and the run's provenance record must make that classification
impossible to miss.**

## The taxonomy

| `run_class` | What it is | May it use synthetic mana/cards? | May it feed empirical deck statistics? |
|---|---|---|---|
| `SYNTHETIC_GOLD_STATE` | A hand-built board state testing one specific legality/sequencing question (Gate 2). | Yes, freely, where the substituted element isn't material to the question under test. | **Never.** |
| `SYNTHETIC_RULES_TEST` | A hand-built state testing a general rules interaction not tied to any specific deck (e.g. a Comprehensive Rules edge case). | Yes, freely. | **Never.** |
| `DECK_BACKED_GOLDFISH` | Subject deck only, no opponents, drawn/played out to answer deck-internal questions (mulligans, mana consistency, time-to-agency). | **No** — see hard requirements below. | Yes, for goldfish-labeled metrics only (never presented as matchup/tournament data). |
| `DECK_BACKED_SINGLE_PLAYER` | Subject deck played against a scripted/non-adversarial environment (e.g. isolating combo accessibility without opponent interaction). | **No.** | Yes, labeled as single-player/no-interaction data. |
| `DECK_BACKED_FOUR_PLAYER` | Full four-player pod, every seat deck-backed with an explicit archetype/list/policy version. | **No**, for any seat. | Yes — this is the only class that may produce matchup/seat/tournament-expectation statistics. |
| `TOURNAMENT_CALIBRATION` | Real tournament results (TopDeck.gg/EDHTop16 data), not simulated at all. | N/A — not a simulation. | Yes, labeled explicitly as tournament (not simulated) evidence. |
| `STATIC_ANALYSIS` | Level 0 hypergeometric/probability calculation, no gameplay. | N/A — no board state. | Yes, labeled as static-probability evidence. |

The first two rows are **laboratory fixtures**: their entire purpose is
answering "is this legal / does this sequence resolve the way we think it
does," and the charter's own Gate 2 explicitly authorizes hand-built states
for exactly this ("gold board states... test mana production, summoning
sickness, convoke... combo loops"). The remaining rows are **empirical
runs**: their purpose is answering "how well/often does the actual subject
deck do X," which per the charter's Phase 26/"Deck accessibility"
distinction requires the actual deck, not a stand-in.

## Requirement 1 — every synthetic fixture records

Conforming to `data/schemas/gold_board_state.schema.json` /
`gold_game.schema.json` (both updated with these fields):

- `run_class`: `SYNTHETIC_GOLD_STATE` or `SYNTHETIC_RULES_TEST`.
- `representative_of_deck_draws`: always `false` for this class — present
  explicitly (not just omitted) so a reader never has to infer it.
- `synthetic_mana`: `true`/`false` — whether mana sources in the fixture are
  arbitrary stand-ins rather than the subject deck's actual mana base.
- `artificial_state_elements`: free-text list of exactly which parts of the
  state are intentionally not deck-representative (e.g. "Plains/Forest
  count and presence are arbitrary scaffolding, not the subject deck's
  actual land base").
- `interaction_under_test`: the specific rule/interaction being validated —
  an `INT-####` ID where applicable, or a Comprehensive Rules citation for
  a rules-only test.
- `material_characteristics` / `abstracted_characteristics`: two lists —
  what about the state *does* matter to the result (must be faithful) vs.
  what's deliberately simplified because it doesn't affect the question
  being asked. A fixture that gets this split wrong (abstracting something
  that actually matters) is a validation bug, not a scope choice, and
  should become a `coverage_backlog` entry if discovered.

## Requirement 2 — every deck-backed run hard-requires

Conforming to `data/schemas/simulation_result.schema.json` (updated):

- `subject_deck_version` (already required) — must resolve to a **frozen**
  decklist file (`data/decklists/<version>.json`), never
  `data/decklists/_provisional/`.
- `subject_deck_hash` — the canonical hash (see below) of the loaded deck,
  checked against the frozen file's own `deck_hash` at load time.
- `subject_deck_card_count` — exact card count, checked against the frozen
  file.
- `commander_identities` — checked against the frozen file's `commanders`.
- `basics_substituted`: `false` by default. May only be `true` if
  `ablation_justification` is also present and non-empty, explaining what's
  being tested by the substitution and why — an ablation is a declared
  experiment, not a silent shortcut (charter: "never silently simplify").
- Once opponent simulation exists: `opponent_deck_versions` and
  `opponent_deck_hashes`, one pair per seat, same hash-check requirement.

## Canonical deck hash

Computed by `sim/validation/run_classification.py`'s `compute_deck_hash()`:
SHA-256 over a canonical JSON serialization of
`{commanders: sorted(names), cards: sorted([(name, scryfall_id, quantity)])}`
— sorted so the hash is stable regardless of field ordering in the source
file, and keyed on `scryfall_id` (not just name) so a silent card-data
substitution (same name, different printing/oracle ID slipped in) also
changes the hash. Stored as `deck_hash` in the decklist file itself once
frozen; `data/decklists/_provisional/` files never carry a `deck_hash` field
— its absence is itself part of what marks them non-frozen.

## Requirement 3 — fail-closed guards

`sim/validation/run_classification.py`'s `load_frozen_deck()` is the only
sanctioned way to load a deck for a `DECK_BACKED_*` run, and it raises
(does not warn, does not fall back) on:

1. **Hash mismatch** — the recomputed hash of the loaded card list doesn't
   match the frozen file's stored `deck_hash`.
2. **Missing hash** — the target file has no `deck_hash` field at all (this
   is how loading `_provisional/` data for a run that requires a frozen
   deck fails: provisional files are never given a hash).
3. **Silent substitution** — any card in the loaded list whose
   `scryfall_id` doesn't match a card present in `data/cards_cache/` for
   the deck's declared `oracle_data_version`.
4. **Unknown placeholder cards** — any card name matching a denylist of
   known placeholder/test patterns (`Test Card`, `Placeholder`, generic
   `Forest`/`Island`/`Plains`/`Swamp`/`Mountain`/`Wastes` appearing in a
   *subject* deck's card list outside of the deck's own declared basic-land
   count — the subject deck's real basics are fine; a basic that wasn't in
   the frozen list is not).
5. **Explicit synthetic-fixture markers present** — if the input carries
   `run_class` in `{SYNTHETIC_GOLD_STATE, SYNTHETIC_RULES_TEST}` or
   `representative_of_deck_draws: false`, `load_frozen_deck()` refuses
   outright — a synthetic fixture can never be the deck source for a
   deck-backed run, structurally, not just by convention.

See `rules_tests/regression/test_run_classification_guards.py` for the
permanent regression test proving all five fail closed, per this review's
requirement 7.

## Requirement 4 — isolation from empirical outputs

`SYNTHETIC_GOLD_STATE` and `SYNTHETIC_RULES_TEST` runs must never
contribute to: mulligan statistics, color-source statistics, mana
consistency, development speed, combo-accessibility frequency, matchup win
rate, seat effects, tournament expectation, or any other deck-performance
statistic. Mechanically enforced two ways:

- `simulation_result.schema.json`'s `evidence_type` enum
  (`docs/VERSIONING.md`) already separates `simulation` from other types;
  now cross-checked against `run_class` — any aggregation/reporting code
  must filter on `run_class in {DECK_BACKED_GOLDFISH, DECK_BACKED_SINGLE_PLAYER, DECK_BACKED_FOUR_PLAYER}`
  before computing a deck-performance statistic, never just on
  `evidence_type == "simulation"` alone (a synthetic gold-state check is
  also technically "simulation" evidence type in the loose sense, which is
  exactly the ambiguity this taxonomy exists to remove).
- Directory separation: gold states/games live under `rules_tests/`, never
  under `results/raw/` (which is reserved for `DECK_BACKED_*` and
  `TOURNAMENT_CALIBRATION`/`STATIC_ANALYSIS` output).

## Requirement 5/6 — visible in logs and reports

Any tool in this repo that prints a run's outcome (test runners, future
simulation-summary tooling) must emit, as the first lines of output for
that run:

```
RUN_CLASS=<value>
DECK_REPRESENTATIVE=<true|false>
SYNTHETIC_MANA=<true|false>
```

exactly matching the field names above, so a reader scanning terminal
output or a log file can tell a laboratory fixture from a shuffled-deck
game without opening the underlying JSON. `sim/validation/run_classification.py`
provides `format_run_banner()` to produce this consistently; nothing should
hand-roll its own version of this banner.

## What this does NOT change

This is a provenance/labeling layer, not a new capability. It doesn't
retroactively make any existing gold-state test wrong — the Forest/Plains
choice in the `INT-0002` XMage test was correct scoping (mana source isn't
material to whether Devoted Druid dies to its own -1/-1 counters), and
remains correct under this taxonomy: it's now explicitly tagged
`run_class: SYNTHETIC_GOLD_STATE`, `representative_of_deck_draws: false`,
`synthetic_mana: true`. The charter's validation gates, source hierarchy,
and non-negotiable rules are unchanged — this document operationalizes
"simulation is not tournament data" one level more precisely, distinguishing
*laboratory* evidence from *simulated-game* evidence within what was
previously just "simulation."
