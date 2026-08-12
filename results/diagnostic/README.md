See also: `gate4a_2p/README.md` (the 100-game `GATE_4A_2P_DIAGNOSTIC` batch)
and `gate4a_4p_probe/README.md` (the `INFRA-0006` four-player investigation)
for the larger, later diagnostic phases. This top-level file covers the
original hand-run 7-game batch that first proved the adapter out.

Real, deck-backed diagnostic gameplay records (2026-08-12), produced by
`sim/rules_engine/xmage_adapter/run_diagnostic_game.py` driving
`SubjectDeckDiagnosticGameTest.java` against a prepared XMage checkout, with
`ComputerPlayer7` (skill 6) making genuine AI decisions - not the scripted
JSON fixtures under `rules_tests/`.

**These are diagnostic records, not empirical evidence.** Every file's
`run_class` is `SYNTHETIC_DIAGNOSTIC_GAMEPLAY` and its `purpose` field says
so explicitly - none of these may be cited for win-rate, matchup,
mulligan, or turn-speed claims (per the owner's explicit instruction for
this phase and `docs/RUN_CLASSIFICATION.md`'s provenance discipline). Both/
all seats always run the exact same frozen `tymna-thrasios-treefarm-v1`
deck (a mirror match) - there is no real opponent deck yet.

## Batch of 7 (2026-08-12)

| file | seats | seed | max turn | events | engine errors |
|---|---|---|---|---|---|
| `diag-20260812-seed1-t10-2p.json` | 2 | 1 | 10 | 24 | 0 |
| `diag-20260812-seed7-t12-2p.json` | 2 | 7 | 12 | 57 | 0 |
| `diag-20260812-seed13-t10-2p.json` | 2 | 13 | 10 | 51 | 0 |
| `diag-20260812-seed21-t15-2p.json` | 2 | 21 | 15 | 128 | 0 |
| `diag-20260812-seed3-t10-4p.json` | 4 | 3 | 10 | 25 | 0 |
| `diag-20260812-seed9-t10-4p.json` | 4 | 9 | 10 | 18 | 0 |
| `diag-20260812-seed17-t8-4p.json` | 4 | 17 | 8 | 19 | 0 |

## Review findings

Reviewed every event in all 7 games against the defect checklist (illegal
actions, impossible/incorrect mana, commander tax/zone handling, timing,
summoning sickness, tutor targets, Pod, Survival, priority, counterspell/
protection, win recognition, trigger ordering, opponent-choice handling,
conditional-combo handling, graveyard/zone transitions, interaction-record
scope). **Zero rules-correctness defects found.** Specifically confirmed
correct: fetchland pay-life/sacrifice/search/shuffle sequencing (Marsh
Flats, Windswept Heath, Wooded Foothills, Misty Rainforest, Polluted
Delta), Chrome Mox's Imprint (hand, not graveyard), Mox Diamond's
discard-a-land-or-sacrifice replacement cost, Evoke's pay-alternate-cost +
mandatory post-resolution self-sacrifice trigger (Endurance, Subtlety) -
the deck's actual pitch/free-interaction cards, not yet exercised by any
prior gold fixture, City of Brass's tap-for-damage trigger, Nature's Rhythm's
X-value-bounded search, combat damage/blocking/simultaneous-damage
resolution, and commander casting at printed cost with no false tax on
first casts. No false or missed win was recorded in any game (none reached
0 life within the turn windows tested, consistent with the low combat
totals observed - correctly not claimed as a win).

## Three real findings (not rules defects) - see `coverage_backlog/BACKLOG.md`

1. **Fixed**: `RandomUtil.setSeed()` called from the `@Test` body ran too
   late - JUnit's `@Before` (deck load + shuffle) had already executed with
   unseeded entropy, so the same `--diag.seed` produced a different game
   every run. Moved to a `@BeforeClass` static setup in
   `SubjectDeckDiagnosticGameTest.java` so it runs before any setup.
2. **Known limitation, not fixed (out of proportion for this phase)**: even
   after the fix above, re-running the same seed still does not reproduce
   an identical game line-for-line - `ComputerPlayer7`'s simulation-based
   decision search appears to have its own internal nondeterminism (likely
   hash-order/thread-scheduling-dependent), independent of the shuffle
   RNG. The seed still fixes the opening shuffle and is retained on every
   record for provenance, but bit-exact replay of a past diagnostic game is
   not currently guaranteed. Patching XMage's own AI search internals for
   full determinism would be a large upstream change, not a narrow fix -
   logged as `INFRA-0005`, not blocking.
3. **Known limitation, not fixed**: `ComputerPlayer7` is dramatically more
   passive in 4-player `CommanderFreeForAll` than in 2-player
   `CommanderDuel` - two of three 4-player games show one or more seats
   taking literally zero actions (no land drops, no spells) across 5+ of
   their own turns, versus consistently active play in every 2-player game
   tested. This is a policy/AI-quality limitation of the engine's default
   AI in wider multiplayer, not a rules-engine defect (no illegal action or
   incorrect rule was ever observed) - logged as `INFRA-0006`. Per the
   owner's explicit instruction, this is recorded as a fidelity limitation
   rather than faked: **the near-term Gate 4 diagnostic/manually-inspected
   batch should use 2-player Commander Duel**, where the AI substrate is
   demonstrably reliable; 4-player remains available but flagged as
   lower-fidelity until this is investigated further.
4. **Informational, not a defect**: `Stack push (top: Cast Fierce
   Guardianship)` lines appeared twice in `diag-...-seed21-...json` with no
   matching "casts"/"puts onto the battlefield" line - i.e., the opponent's
   AI appears to internally construct/evaluate a hypothetical response
   (Fierce Guardianship's commander-cast alternate cost) while deciding
   whether to interact, and that evaluation leaks into the same printed log
   stream as the real game. The actual game state was unaffected (the real
   spell on the stack, Nature's Rhythm, resolved normally with correct
   downstream effects). Documented here as a transcript-reading caveat for
   any future reviewer of these logs, not logged as a coverage_backlog item
   since it doesn't affect game correctness.
