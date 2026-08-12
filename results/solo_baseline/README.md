# SIM-001 SOLO BASELINE v1

Subject deck: `tymna-thrasios-treefarm-v1`, hash
`4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a`
(recorded and hash-verified in every file this baseline produced). Current
Oracle/rules data: `data/cards_cache/oracle-2026-08-12/`. Current verified
interaction registry: `interactions/verified/` (15 entries, all resolved,
see `docs/VALIDATION_GATES.md` Gate 1).

**Scope discipline (per explicit instruction): this baseline makes no
claims about pod win rate, matchup performance, or cEDH competitiveness.**
It answers "how does this exact deck's own construction and the engine's
execution of it behave in isolation," nothing about opponents.

## A critical defect found and fixed while building this baseline

**All of today's earlier deck-backed engine runs — the 100-game
`GATE_4A_2P_DIAGNOSTIC` batch and the `INFRA-0006` four-player probes —
were run with the test harness's default `gameOptions.testMode = true`,
which makes `GameImpl.init()` **skip real hand-dealing entirely**
(`mulligan.drawHand()` only runs `if (!gameOptions.testMode)` -
`Mage/src/main/java/mage/game/GameImpl.java`). Direct probe confirmed
`handSize=0` at turn 1 upkeep under the old code path. Every prior game
was therefore played from a **genuinely empty starting hand**, refilled
only by normal per-turn draws (roughly 1 card/turn) - not a real 7-card
Magic opening hand, ever.

**Fixed**: both drivers (`sim/rules_engine/xmage_adapter/
SubjectDeckDiagnosticGameTest.java` and `sim/analysis/xmage_adapter/
SoloGoldfishSnapshotTest.java`) now call a new `executeWithRealHands()`
method that reimplements the inherited `execute()`'s short body with
`gameOptions.testMode = false`, restoring real hand-dealing. Verified by
direct probe: `handSize=7` at turn 1 upkeep after the fix, with a normal,
sensible-looking opening hand.

**Impact assessment**: this does **not** invalidate the rules-correctness
conclusions from the earlier batches (fetchlands, Force of Will vs. Veil
of Summer, Birthing Pod math, commander tax, Evoke) - those interactions
were executed correctly by the engine whenever they occurred, independent
of how thin the hand was. What it **does** undermine is any claim about
realistic pacing/activity/representativeness: the earlier "AI passivity"
characterization was confounded by every game being played essentially
hellbent-topdeck from turn 1. **Rerun with the fix** (smaller samples than
originally planned, due to the time this investigation and refix consumed
- see below): `GATE_4A_2P_DIAGNOSTIC` v2 (40 games,
`results/diagnostic/gate4a_2p_v2/`) and the four-player probe v2 (10
games, 8 completed, `results/diagnostic/gate4a_4p_probe_v2/`). Both show
**dramatically higher, more balanced activity** (2-player: 50.6 -> 102.6
events/game; 4-player: several previously-zero-action seats now
consistently active, 33/41/35/33 total actions across 4 seats in 6 games
vs. the old 50/25/32/33 across 20 with frequent per-seat zeros) and
**zero new rules/adapter/transcript defects**. `INFRA-0007` (the AI never
pays Pact of Negation's deferred cost) is **confirmed to persist** under
real hands - all 3 wins in the v2 batch trace to the identical mechanism,
strengthening rather than undermining that finding. Logged as `INFRA-0008`
in `coverage_backlog/backlog.jsonl`.

Old (empty-hand) batches remain in `results/diagnostic/gate4a_2p/` and
`gate4a_4p_probe/` for provenance, but are **superseded** by the `_v2`
directories for any activity/pacing conclusion.

## STATIC/COMBINATORIAL (`sim/analysis/solo_baseline_static.py`)

Pure hypergeometric math over the exact 98-card library (commanders cast
from command zone, not drawn) - `results/solo_baseline/static_combinatorial.json`.
No sampling; every figure is an exact closed-form probability. Card
classification is heuristic oracle-text matching with manual
spot-correction (documented in the script), not exhaustive manual review.

Headline numbers:
- **27/98 lands (27.6%)** - notably below the ~40% "usual" EDH guideline.
  Expected lands in a 7-card opener: **1.93**, `P(>=2 lands)` = **62.4%**,
  `P(>=3 lands)` = **29.4%**. This deck leans hard on its 13 acceleration
  pieces (mana dorks/rocks) and heavy fetch/dual density (most of the 27
  lands produce 2+ colors) to compensate for genuine land scarcity - a
  real, deckbuilding-relevant structural finding, not previously
  quantified anywhere in this project.
- 13 acceleration, 14 tutors, 21 interaction pieces (heuristic
  classification - see script for exact card lists).
- Commander castability (land-count + color-source approximation, turn 3
  on the play): Tymna (`{1}{W}{B}`) ~30-47% depending on which bound you
  read (land-count-only vs. color-only), Thrasios (`{G}{U}`) ~75-77%
  (cheaper, easier color pair given 21 G sources / 16 B sources) -
  deliberately reported as a bounded range, not a false-precision point
  estimate (independence assumption between land-count and color-coverage
  is flagged in the script, not silently corrected).
- Deterministic (`conditional: false`) 2-card combo piece co-location
  (e.g. `INT-0002` Devoted Druid + Swift Reconfiguration): 0.4-2.5%
  by turn 10 depending on play/draw - **natural draw only, deliberately
  excluding this deck's own 14 tutors' contribution**, since successful
  tutoring is a policy-dependent action, not static combinatorics. The
  true accessibility including correct tutor use is substantially higher
  but is not a number this layer can honestly produce - see
  POLICY-DEPENDENT below.

## ENGINE-GOLDFISH (`sim/analysis/run_solo_goldfish_batch.py` + `solo_baseline_goldfish_analysis.py`)

Real XMage games: subject deck (`ComputerPlayer7`, skill 6) vs. a
deliberately inert opponent (the plain do-nothing `ComputerPlayer` - see
`sim/rules_engine/xmage_adapter/README.md`'s known-defect log; that
"defect" is exactly a goldfish-mode opponent here, not reused as a bug).
Each (seed, turn-checkpoint) pair is an **independent** `reset()`+run to
that turn (found and documented: calling `execute()`/`executeWithRealHands()`
twice on the same game object without an intervening `reset()` does not
continue the game correctly - it re-triggers a spurious reshuffle/restart;
see the method docstrings). 15 seeds x 5 turn checkpoints (1/3/5/7/10) = 75
independent samples, `results/solo_baseline/solo-goldfish-batch002-realhands-raw_snapshots.json`.
Accessibility is read directly from game-state zone contents (hand/
battlefield/graveyard/exile card names), **not** from whether the AI
recognized or executed a line - a card counts as "seen" the moment it's
ever been in any of those zones.

Headline numbers (n=15 per checkpoint - small, explicitly not
statistically strong; point estimates with wide uncertainty):
- Empirical cards seen by turn 10: mean 14.3 (vs. the STATIC layer's
  naive 7+9=16 on-the-play formula - close but below, consistent with
  some early-game card-disadvantage effects, e.g. Chrome Mox
  imprint/Force of Will-style exile costs removing cards from the "seen
  and still relevant" pool in ways the raw draw-count formula doesn't
  capture).
- **Commander-on-battlefield by turn 10: Tymna 26.7%, Thrasios 26.7%**
  (both, n=15). This is **materially lower** than the STATIC layer's
  land/color-availability approximation alone would suggest, confirming
  the STATIC layer's own documented caveat that it "ignores actual
  land-drop sequencing/tapping decisions and nonland accel's
  contribution" - real accessibility requires the AI to actually
  prioritize and successfully sequence the cast, which it doesn't always
  do even with resources available. This is the single clearest
  "materially changed vs. naive expectation" finding of this baseline.
- Deterministic combo piece co-location and Birthing Pod/Survival
  "seen" rates at n=15 are too small to report a meaningful point
  estimate differentiated from zero for most entries (most 2-card 1-of
  combos were never both seen in 15 samples, consistent with the STATIC
  layer's own <3%-by-turn-10 prediction - not a contradiction, a
  confirmation, just underpowered to show a nonzero count at this N).

**Honest limitation**: n=15/checkpoint is small (time-boxed given how much
of this session the hand-dealing investigation and refix consumed) - wide
confidence intervals, reported as point estimates with explicit sample
size, not smoothed or dressed up. A follow-up batch at n=100+ would
sharpen every ENGINE-GOLDFISH number here without changing the
methodology.

## POLICY-DEPENDENT (explicitly not quantified)

The following depend materially on mulligan/tutor-targeting/sequencing
decisions this project has no policy layer for yet (`sim/policies/` is
empty) - computing numbers here with the current default AI would silently
conflate "this deck's structural accessibility" with "how good XMage's
generic AI happens to be," which `INFRA-0007` (the Pact of Negation
finding) already shows can be badly misleading:
- Mulligan keep/mull decision quality (distinct from the STATIC layer's
  structural "keepable hand" threshold, which is a fixed definition, not
  a decision).
- Tutor target selection correctness and timing.
- Successful assembly/execution of a combo (vs. this baseline's piece
  *accessibility*, which is state-based and policy-independent).
- Sequencing quality (optimal play order, resource allocation).

These remain open, explicitly deferred - not silently approximated with
today's default AI's numbers.

## Comparison against prior project estimates

No prior file-backed numeric solo-deck baseline existed in this repo
before this phase (`results/raw/` and `results/findings_packets/` were
both empty placeholders) - this is a first baseline, not primarily a
revision of stated numbers. The one place a genuine prior *quantitative*
claim existed is this project's own `interactions/verified/*.json` combo
math (e.g. `INT-0001`'s "3+ opponents needed," `INT-0006`'s "5-creature
threshold") - those are about *pod-level opponent behavior*, out of scope
for a solo baseline, and are unaffected by anything here.

**Confirmed**: `INFRA-0007` (Pact of Negation AI blind spot) - persists
identically after the hand-dealing fix, strengthening confidence it's a
real, structural AI-policy limitation rather than a hand-size artifact.

**Materially changed / newly established**: the land-count deficit (27.6%,
below the usual ~40% guideline) and the gap between STATIC commander-
castability approximations and ENGINE-GOLDFISH's actual observed
commander-on-battlefield rates - both are new findings this project had
not quantified before.

**Invalidated by higher-fidelity modeling**: the *activity-level*
characterization from the original (empty-hand) `GATE_4A_2P_DIAGNOSTIC`
and `INFRA-0006` batches - not their rules-correctness conclusions, which
stand.
