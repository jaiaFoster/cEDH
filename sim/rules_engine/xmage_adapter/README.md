The real INFRA-0004 orchestration adapter: drives genuine, deck-backed
AI-vs-AI games through XMage, seeded and machine-logged - the piece that
was missing when `xmage_tests/` (single hand-scripted interaction proofs)
was the only committed engine artifact.

## One-time setup (not committed - see `xmage_tests/README.md`'s same note)

```
git clone --depth 1 https://github.com/magefree/mage.git mage
cp sim/rules_engine/xmage_adapter/SubjectDeckDiagnosticGameTest.java mage/Mage.Tests/src/test/java/org/mage/test/commander/duel/
cd mage && mvn -q -o -pl Mage,Mage.Sets,Mage.Tests,Mage.Server.Plugins/Mage.Player.AI.MAD -am install -DskipTests
```

(JDK 21, Maven 3.9+. `Mage.Player.AI.MAD` is required - it holds
`ComputerPlayer7`, the real simulation-based AI; the plain `ComputerPlayer`
in `Mage.Player.AI` is a do-nothing stub, see "known-defect log" below.)

## Running a diagnostic game

```
python3 sim/rules_engine/xmage_adapter/run_diagnostic_game.py \
  --mage-dir /path/to/mage --seed 1 --max-turn 10 --seats 2 \
  --out-dir results/diagnostic
```

`--seats` is 2, 3, or 4 (`CommanderDuel`/`CommanderFreeForAll` at the real
Commander life total, 40 - not the reusable test-harness base classes'
convenience default of 20). Output is one JSON record per game; see
`results/diagnostic/README.md` for the schema and the first batch's
findings.

## Running a batch (GATE_4A_2P_DIAGNOSTIC and later)

`run_diagnostic_batch.py` runs many games per Maven/JVM invocation
(`SubjectDeckDiagnosticGameTest.runDiagnosticBatch` loops over
`-Ddiag.seeds` internally, calling `reset()` between games) instead of
paying JVM startup cost per game - this is what made a 100-game batch
practical:

```
python3 sim/rules_engine/xmage_adapter/run_diagnostic_batch.py \
  --mage-dir /path/to/mage --seed-start 1 --count 100 --chunk-size 10 \
  --max-turn 12 --seats 2 --skill 6 \
  --out-dir results/diagnostic/gate4a_2p
```

`--skill` controls `ComputerPlayer7`'s search depth/think-time
(`maxDepth`/`maxThinkTimeSecs` both scale with it). **Use `--skill 6` for
2-player, `--skill 10` for 4-player** - see
`results/diagnostic/gate4a_4p_probe/README.md` for why. `--chunk-size`
bounds how many games share one JVM/Maven process (smaller chunks mean a
hung/crashed chunk loses fewer games - each chunk has its own
`--chunk-timeout`, default 280s). Writes one JSON per game plus a
`<batch-id>-SUMMARY.json` with operational statistics only (games
completed, exceptions, engine errors, event counts, timing) - see
`results/diagnostic/gate4a_2p/README.md` for why those numbers, including
any win count, must not be read as strategic/matchup evidence.

## Adapter responsibility checklist (INFRA-0004)

- [x] load exact versioned decklists - `deck_to_dck.py`
- [x] verify deck hashes - reuses `sim/validation/run_classification.py`'s
      `compute_deck_hash`; refuses to convert an unfrozen/tampered decklist
- [x] initialize seats (2/3/4) - `SubjectDeckDiagnosticGameTest`
- [x] control/randomize shuffle seeds - `RandomUtil.setSeed()` in a
      `@BeforeClass`, so it applies before deck load/shuffle (**best-effort
      only** - see limitation #2 in `results/diagnostic/README.md`: the
      AI's own decision search has independent nondeterminism, so a seed
      fixes the opening shuffle but does not currently guarantee a
      bit-exact replay of a past game)
- [x] execute games - `run_diagnostic_game.py` + Maven/JUnit
- [x] expose/log decisions and state transitions - `parse_transcript()`
      turns XMage's own `[LOG][GAME]` lines into structured JSON events
- [x] capture winners/non-winners - `winner_line` (regex on "has won/lost
      the game", confirmed against the real log-message source in
      `PlayerImpl.java`; not yet observed in practice since no diagnostic
      game so far has run long enough to end)
- [~] capture unknown/unsupported states - `engine_errors` captures
      ERROR-level engine log lines and nonzero Maven exit codes; there is
      no separate "this card/mechanic isn't implemented" detector beyond
      that (none was needed in the first batch - zero engine errors across
      7 games)
- [x] retain reproducible seeds - every record's `random_seed` field,
      though see the best-effort caveat above
- [x] distinguish engine decisions from project policy decisions - this
      project has no policy layer yet (`sim/policies/` is empty), so there
      is nothing to conflate with engine output; the distinction that
      exists today is XMage's own rules engine (proven correct in every
      game reviewed) vs. XMage's own default AI (`ComputerPlayer7`, proven
      unreliable specifically in 4-player - see `INFRA-0006`), which the
      diagnostic review explicitly separated rather than treating a passive
      AI turn as a rules bug
- [x] emit machine-readable game logs - the JSON records themselves

Scaling/distributed execution (running many games in parallel, a batch
runner, result aggregation) is explicitly out of scope for this layer per
the owner's instruction - `run_diagnostic_game.py` runs exactly one game
per invocation.

## Known-defect log (this adapter's own debugging, 2026-08-12)

- Plain `mage.player.ai.ComputerPlayer.priority()` is `// minimum
  implementation for do nothing` - it just passes. Early smoke tests using
  it (and `TestComputerPlayer`, which wraps it) showed total passivity
  across 6+ turns even with `setAIPlayer(true)`. Fixed by switching to
  `TestComputerPlayer7` wrapping `mage.player.ai.ComputerPlayer7` (skill
  level 6), the same AI class this engine's own
  `CardTestCommander4PlayersWithAIHelps`/`CardTestPlayerBaseWithAIHelps`
  test bases use.
- `RandomUtil.setSeed()` in the `@Test` method body ran after `@Before`
  had already loaded and shuffled both decks - fixed via `@BeforeClass`
  (see `results/diagnostic/README.md` finding #1).
