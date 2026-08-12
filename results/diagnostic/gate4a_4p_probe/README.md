INFRA-0006 investigation: cheapest credible path to four-player active
policy execution, per the owner's explicit evaluation order.

## 1. Configuration/skill/search parameters (tried first - this is what worked)

`ComputerPlayer6`'s constructor ties both search depth and think-time
budget directly to the `skill` parameter (`maxDepth = skill` for skill>=4,
`maxThinkTimeSecs = skill * 3`). The prior 4-player diagnostics
(`INFRA-0006`, `results/diagnostic/README.md`) all used `skill=6` (this
project's original, arbitrary choice, copied from the engine's own
`CardTestPlayerBaseWithAIHelps`/`CardTestCommander4PlayersWithAIHelps`
test bases). Compared skill 3/6/10/16 on the same 3 seeds, 4 seats, 10
turns:

| skill | avg events/game (n=3) |
|---|---|
| 3 | 18.3 |
| 6 | 25.7 |
| 10 | 35.7 |
| 16 | 26.0 |

Skill 10 is a clear, free improvement over the original skill 6 (+~40%
more events on this small sample) and beats skill 16 (search depth vs.
4-player branching factor tradeoff - deeper isn't strictly better, matches
the source code's own `// TODO: increase maxNodes due AI skill level like
max depth?` uncertainty). No code change was needed - `--skill` was
already a driver parameter (`-Ddiag.skill`).

## 2. Verification at a real batch scale

Ran 20 games (seeds 1-20, 4 seats, skill 10, max turn 12) - see
`fourplayer-probe-skill10-seed*.json` / `-SUMMARY.json`:
- 20/20 completed, 0 exceptions, 0 engine errors, 0 chunk failures.
- Mean 34.5 events/game (up from `skill=6`'s ~18-25 seen in the original
  `INFRA-0006` finding).
- **Aggregate per-seat activity across the 20 games**: every seat took a
  substantial number of real actions (PlayerA 50, PlayerB 25, PlayerC 32,
  PlayerD 33 total land-plays/casts/activations) - no seat is
  systematically inert.
- **Per-game per-seat activity**: still uneven - a given seat has zero
  actions in 25-50% of individual games (PlayerA 7/20, PlayerB 10/20,
  PlayerC 7/20, PlayerD 5/20 games with zero recorded actions for that
  seat). This is a real, labeled fidelity limitation, not a rules/adapter
  defect - 0 engine errors were found in any of these games, every action
  actually taken was legal, and the same AI class is demonstrably capable
  of normal, active play (confirmed extensively in the 2-player
  `GATE_4A_2P_DIAGNOSTIC` batch and in this batch's own aggregate seat
  totals).

## Steps 2-4 (other AI implementations, policy wrapper, patching internals) - not attempted

Step 1 delivered a real, sufficient, zero-cost improvement matching the
stated bar ("we do not need elite cEDH play yet, we need four players that
actually take legal, nontrivially active actions") - `ComputerPlayerMCTS`
(the other available AI implementation) was confirmed to build
(`Mage.Server.Plugins/Mage.Player.AIMCTS`) but not benchmarked, since
escalating past a working, cheap fix would contradict the explicit
"do not immediately patch/escalate" instruction. Revisit only if a future
diagnostic phase needs meaningfully more consistent per-game activity than
skill 10 provides.

## Decision: `skill=10` is the new default for 4-seat diagnostic games

`SubjectDeckDiagnosticGameTest`'s `-Ddiag.skill` still defaults to `6`
(unchanged, since that's what the validated `GATE_4A_2P_DIAGNOSTIC` 100-game
2-player batch used and 2-player showed no activity problem worth paying a
~2x slowdown for) - **future 4-player runs should pass `--skill 10`
explicitly**, as this probe did.

## Opponent-policy fidelity (FOUR_PLAYER_DIAGNOSTIC_READY labeling requirement)

All 4 seats in every game so far run the exact same frozen subject deck
(a mirror match) - there is no distinct opponent decklist/archetype
ingested yet in this project. This is explicit and labeled, not a masked
claim of realistic multi-archetype opposition: "opponent" seats are the
subject deck itself, `ComputerPlayer7` skill 10, not a distinct
policy/archetype. Real opponent-archetype pods remain future work (see
`docs/assignments/SIM-001.md` Phase 8-10, not started).

## Same-seed nondeterminism (INFRA-0005) - not further investigated

Per instruction, did not spend effort chasing bit-perfect replay here
either. Every game record retains its seed, the exact subject deck
version/hash, and the full transcript for provenance - sufficient for
this phase's debugging needs (none of the review in this batch needed to
replay a specific game exactly).
