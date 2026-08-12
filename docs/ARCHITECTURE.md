# Architecture

Six layers, per `docs/CHARTER.md`. This document maps each layer to its
concrete home in the repository and states what exists today vs. what is
scaffolded-but-empty pending the subject decklist and a network-capable
environment.

```
                     ┌──────────────────────────────────────────┐
                     │              6. VALIDATION                │
                     │  gold states · gold games · gates 1-7     │
                     │  sim/validation/, rules_tests/             │
                     └───────────────▲────────────────────────────┘
                                      │ trust must be earned before scaling
┌─────────────┐   ┌─────────────┐   ┌┴────────────┐   ┌─────────────┐   ┌─────────────┐
│  1. RULES    │──▶│2. INTERACT. │──▶│ 5. SIMULATION│◀──│ 4. POLICIES │◀──│3. ARCHETYPES│
│ legality     │   │ verified /  │   │ 4-player     │   │ legal→chosen│   │ empirical   │
│ CR+Oracle+   │   │ candidate   │   │ games, seats,│   │ per-archetype│  │ metagame    │
│ Forge/XMage  │   │ interactions│   │ hidden info  │   │ heuristics   │  │ census      │
│ sim/rules_   │   │ /verified,  │   │ sim/          │  │ sim/policies/│  │ data/       │
│ engine/      │   │ /candidate  │   │ simulation/   │  │             │   │ archetypes/ │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

## 1. Rules — `sim/rules_engine/`

Determines what is legal. This layer is an *interface*, not a from-scratch
reimplementation of Magic — see `docs/INFRASTRUCTURE_SURVEY.md` for the
Forge vs. XMage evaluation. Planned responsibilities:

- Adapter(s) to drive an executable engine (Forge and/or XMage) for exact-line
  validation (Level 4) and gold-board-state/gold-game checks (Gates 2–3).
- A lighter-weight native state tracker for Level 1–2 structural/sequencing
  simulation, used where driving a full external engine per-game would be too
  slow for Level 3 four-player Monte Carlo runs. This native tracker's
  behavior on any rules-material question must be checked against the
  executable engine before it is trusted (see Gate 2).
- Nothing in this layer encodes strategy. It answers "is this legal", never
  "is this good."

**Status: not yet implemented.** No code has been written because there is no
subject decklist to build against yet, and this environment currently cannot
reach any of the candidate rules-engine repositories or MTG data APIs (see
`docs/SOURCES.md`). `sim/rules_engine/` contains only a module-layout stub.

## 2. Interactions — `interactions/verified/`, `interactions/candidate/`

- `interactions/verified/<id>.json` — an interaction that has been checked
  against Comprehensive Rules + Oracle text and, where possible, independently
  reproduced in an executable engine. Only these may be used as deterministic
  transitions anywhere in simulation - but see the verification-level caveat
  below, since not every `status: verified` entry carries the same strength
  of evidence.
- `interactions/candidate/<id>.json` — sourced from Commander Spellbook,
  primers, or discovery passes, not yet validated. Simulation must never treat
  a candidate interaction as guaranteed.
- Schema: `data/schemas/interaction.schema.json`.

**Verification-level requirement (established 2026-08-12, from `INT-0012`,
full taxonomy in `docs/VERIFICATION_LEVELS.md`):** `status: verified` alone
does not distinguish an interaction whose own exact stated transition was
reproduced end-to-end in an executable engine (`ENGINE_EXACT_VERIFIED`) from
one where only a downstream consequence or necessary component was
engine-reproduced (`ENGINE_COMPONENT_VERIFIED`) or where only Comprehensive
Rules citations exist (`RULES_VERIFIED`) or where verification only holds
under a stated condition, most often an opponent choice this deck doesn't
control (`CONDITIONAL`). Every `interactions/verified/<id>.json` record
carries an explicit `verification_level` field for this reason. Only
`ENGINE_EXACT_VERIFIED` entries may be hardcoded as a fixed hop in a native
(non-engine-driven) Layer 5 tracker; the other three tiers may inform an
engine-driven simulation (where XMage/Forge itself plays out the real
cards, so the untested exact transition is handled live by the real engine)
but must not be hardcoded as if their exact transition were itself proven.

**Status:** empty; populated once the decklist arrives and the interaction
discovery pass (charter section "Interaction discovery pass") runs.

**Decision-space fidelity requirement (established 2026-08-12, from
`INT-0007`):** when a verified interaction's mechanism causes a triggered
ability to trigger multiple times — Delney, Streetwise Lookout's clause is
the concrete example, but the same applies to any future "triggers an
additional time"/copy-effect interaction — Layer 5 (Simulation) must encode
it as multiple genuinely independent instances of that ability, each with
its own target choice, optional-cost decision, mode choice, and stack
position, not as a single atomic aggregate effect (e.g. "deal 2 damage and
amass 2" instead of "deal 1 damage to any target; then amass Orcs 1,
resolving twice with two separately-targeted instances and an explicit
trigger-ordering choice per CR 603.3b"). A gold board state's single
recorded outcome (e.g. `GBS-0004`'s "both instances targeted the same
player, 2 total damage") is valid evidence that the *result* is reproduced
correctly, but it is not license to collapse the interaction's actual
decision tree when it is later encoded for policy/simulation — targets,
optional payments, modes, ordering, and any opponent choices along the way
remain strategically meaningful and must stay selectable, not pre-baked.

## 3. Archetypes — `data/archetypes/`

Empirical registry built from tournament data (TopDeck.gg, EDHTop16), not a
hand-picked list of famous commanders. Each archetype record separates
commander(s), strategic architecture, prevalence (with tournament-window
provenance), and a pointer to its policy definition.

Schema: `data/schemas/archetype.schema.json`.

**Status:** empty; blocked on tournament-data access (see `docs/SOURCES.md`).

## 4. Policies — `sim/policies/`, `data/policies/`

Given a legal-action set from Layer 1, decide what a competent pilot of a
given archetype would plausibly do. Policy *definitions and their evidence*
live in `data/policies/<archetype>.json` (deterministic heuristics,
probabilistic branch weights, forward-search triggers, cited primers/reports);
the *executable* policy logic lives in `sim/policies/`. These are kept
separate so that policy assumptions are auditable independent of code.

Schema: `data/schemas/policy.schema.json`.

**Status:** not yet implemented — depends on the archetype registry (Layer 3)
and the subject deck's own policy, which needs the decklist.

## 5. Simulation — `sim/simulation/`

The four-player game loop: seats, hidden/public information, stack, win
attempts, responses, resource expenditure. Consumes Layers 1–4. Config for
any run (deck versions, policy versions, seed, pod sampling method) is
recorded per `docs/VERSIONING.md` and written alongside `results/raw/`.

**Status:** not yet implemented (correctly — per the charter, no production
simulation before Gates 1–3 pass, and Gate 1 requires the subject decklist).

## 6. Validation — `sim/validation/`, `rules_tests/`

Gate machinery (see `docs/VALIDATION_GATES.md`): gold board states, gold
games, the 100-game manual inspection pass, and the sensitivity/regression
harness for Gates 5–7. `rules_tests/regression/` accumulates a permanent test
per discovered bug so the system never relearns the same lesson twice.

This layer also owns the **synthetic-vs-deck-backed provenance boundary**
(`docs/RUN_CLASSIFICATION.md`): `sim/validation/run_classification.py`'s
`load_frozen_deck()` is the only sanctioned way anything in `sim/` may load
a decklist for an empirical (`DECK_BACKED_*`) run, and it fails closed on a
missing/mismatched deck hash, a provisional deck, an unknown/substituted
card, or synthetic-fixture markers — see
`rules_tests/regression/test_run_classification_guards.py`. Gold board
states and gold games (`rules_tests/gold_board_states/`,
`rules_tests/gold_games/`) are always `SYNTHETIC_*`-classed and structurally
barred from feeding empirical statistics, regardless of how deck-faithful
their setup looks.

**Status:** card ingestion exists (`data/cards_cache/`), the subject deck
is frozen with a canonical hash (`data/decklists/tymna-thrasios-treefarm-v1.json`),
and one real Level 4 reproduction has been run against XMage (Devoted
Druid's core ability, 3/3 passing). No `rules_tests/gold_board_states/` or
`rules_tests/gold_games/` JSON records exist in this repo yet — the first
XMage test files live in an external clone (not committed; XMage itself is
GPL-licensed engine code, not this project's own artifact) and still need
to be formalized as committed gold-state records per the schema.

## Supporting layers not in the charter's core six

- `sim/ingestion/` — card/ruling/tournament ingestion adapters (Scryfall,
  MTGJSON, Commander Spellbook, TopDeck.gg, EDHTop16). One adapter module per
  source, each producing records conforming to the schemas in
  `data/schemas/`, each stamped with a pull timestamp and source version.
- `coverage_backlog/` — the unknown-state/missing-capability tracker (see
  `coverage_backlog/README.md`). Feeds back into Layers 1–2.
- `results/` — `raw/` (full provenance-tagged output) and `findings_packets/`
  (primer-facing distillation, per the charter's Findings Packet format).

## Why so little code exists yet

The charter's initialization behavior is explicit: establish the instrument,
do not begin production simulation. Writing a rules engine or policy layer
against a deck that doesn't exist yet (the exact list is "supplied
separately") would mean building fidelity nobody can validate against real
cards. The scaffold here is deliberately structure + schemas + conventions,
so that the moment the decklist and a research assignment arrive, work starts
at Gate 1 (card ingestion) instead of at "what directories do we even use."
