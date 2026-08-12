# sim/

The instrument itself. Module layout mirrors the charter's six layers plus
two supporting layers (see `docs/ARCHITECTURE.md`):

| Module | Layer |
|---|---|
| `rules_engine/` | 1. Rules — legality, adapters to Forge/XMage, native Level 1-2 state tracker |
| `interactions/` | 2. Interactions — loads `interactions/verified/`, exposes deterministic transitions to simulation |
| `archetypes/` | 3. Archetypes — loads `data/archetypes/` |
| `policies/` | 4. Policies — decision logic per `docs/POLICY_FRAMEWORK.md`, loads `data/policies/` |
| `simulation/` | 5. Simulation — the four-player game loop |
| `validation/` | 6. Validation — gate runners: gold-state checker, gold-game checker, manual-inspection log tooling, sensitivity/regression harness |
| `ingestion/` | Card/ruling/tournament data adapters (Scryfall, MTGJSON, Commander Spellbook, TopDeck.gg, EDHTop16) |

## Status

Every module below is a docstring-only stub. No gameplay logic exists yet —
per the charter's initialization behavior, production simulation code isn't
written until there's a decklist to build it against and Gate 1 can start.
Writing a rules engine or policy layer today would mean building fidelity
nobody can validate against real cards, which is exactly the "trade
correctness for simulation volume" the charter forbids.

## Implementation language: not yet decided

Deliberately left open — see `docs/INFRASTRUCTURE_SURVEY.md` "Decisions NOT
made yet." The choice depends on:
- Whether Forge/XMage (both JVM) end up as the Level 4 (and possibly Level
  1-3) execution substrate, which would push toward a JVM-native `sim/` or a
  thin cross-process adapter from another language.
- Performance needs at Gate 6/7 scale (10,000-1,000,000+ games), which likely
  rules out launching a full external engine per game for anything above
  Level 2.

The regression-test tooling under `rules_tests/regression/` uses **Python +
pytest + jsonschema** right now, independent of that decision — it's
validating the schemas and data conventions in `data/schemas/`, which are
language-agnostic JSON, not the simulator itself. See
`rules_tests/regression/requirements.txt`.
