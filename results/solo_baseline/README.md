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

---

# SIM-001 SOLO-002 — Opening Hand, Mulligan & Early Development Audit

> **⚠️ STATUS: `SUPERSEDED_PENDING_CORRECTNESS_RERUN`.** A critical mana-accounting defect was
> found in the simulator this phase used (mana sources were never marked tapped/spent, so a
> land, mana dork, Sol Ring, Mana Vault, Mox, etc. could be reused an unbounded number of times
> within one turn - among several other modeling defects). **Every number in this section is
> invalidated and must not be cited for primer claims or deckbuilding changes.** The corrected
> rerun, with the defect fixed and ten regression tests proving it, is in the
> **"SIM-001 SOLO-002R"** section below. This section and its `solo002_*.json` files are
> retained for provenance only, per standing instruction not to delete superseded work.

Follows directly from SOLO BASELINE v1 above, and supersedes its scope for
mulligan/deckbuilding questions specifically: this phase deliberately
de-emphasizes turn-10 goldfish states and raw card-category counts in
favor of rules-aware **Turn 1-3 development under a deck-aware policy**,
per explicit instruction. Same subject deck/hash as above. Run class for
every file in this section: **`DECK_BACKED_GOLDFISH`** (real turn-by-turn
gameplay - land drops, casting, sequencing - against no opponent, with the
actual subject deck; corrected from an earlier internal mislabeling as
`STATIC_ANALYSIS`, which per `docs/RUN_CLASSIFICATION.md` is reserved for
pure hypergeometric math with no gameplay at all).

## Why a new, native simulator instead of XMage

The engagement's own constraint ("do not use generic XMage AI
decision-making as the primary policy") and a hard sampling-size
requirement (100,000+ hands) are jointly incompatible with the XMage/JVM
substrate used elsewhere in this project (2-16s/game observed in
`results/diagnostic/`) - at that rate 100k hands would take days. Built
instead: a **native Python Level 1-2 structural/sequencing simulator**
(`sim/analysis/opening_hand_model.py`, `opening_hand_policy.py`,
`opening_hand_metrics.py`) - exactly the eventual need `sim/rules_engine/
__init__.py`'s own docstring always flagged. It models land drops, mana
taps (with summoning sickness), and a single **greedy deck-aware
development policy** (`DEFAULT_PRIORITY = ["free_accel", "paid_accel",
"premium_engine", "commander", "engine", "tutor", "interaction"]`) -
explicitly *not* claimed to be a proven-optimal expert line, only better
than random sequencing, which is the actual bar needed to separate "legally
possible" from "what a reasonable player would do." It does not model
combat, opponents, the stack, or triggered abilities beyond ETB mana/type
effects - out of scope for an opening-hand question. Card-level modeling
carries several documented, bounded simplifications (City of Traitors'
sacrifice clause, Gemstone Caverns/Exotic Orchard treated as unconditional
any-color, Deathrite Shaman's graveyard ability not modeled, fetchlands
crack instantly for a same-turn dual) - see the module docstring for the
full list. Throughput: **~1,200-1,700 hands/sec**, making every part of
this audit's requested sample sizes (100,000+ for Part A) a matter of
seconds to low minutes, not days.

## Part A — keep-everything opening-hand census (100,000 hands)

`sim/analysis/run_opening_hand_census.py` -> `solo002_opening_hand_census.json`.
100,000 random 7-card hands, seed 42, on the play, every hand kept (no
mulligan), developed through end of Turn 3 under the greedy policy.
78.6s wall time - sampling error is negligible at this scale (a 2,000-hand
smoke test and the full 100k run agree to within ~1pp on every metric).

**Overall Turn-3 "meaningful development" rate: 79.9%** (meaningful =
2+ mana AND (an engine active OR a tutor castable OR live interaction
castable)).

### Primary output table (selected rows; full table has 20 rows x T1-T3 in the JSON)

| Metric | T1 | T2 | T3 |
|---|---|---|---|
| 2+ usable mana | 25.9% | 82.5% | 87.6% |
| 3+ usable mana | 13.1% | 41.6% | 72.5% |
| All of W/U/B/G available | 47.9% | 58.1% | 66.2% |
| Any engine active | 25.4% | 67.0% | 79.2% |
| 2+ engines active | 5.6% | 39.6% | 60.8% |
| Engine + live interaction | 6.0% | 13.3% | 20.9% |
| Tymna castable / supported | 0.0% / 1.6% | 8.8% / 23.8% | 13.0% / 46.8% |
| Thrasios castable / activatable-soon | 3.2% / 15.7% | 16.6% / 53.7% | 12.6%\* / 67.3% |
| Tutor available / castable | 55.4% / 16.0% | 50.4% / 19.0% | 46.6% / 18.9% |
| Cradle on battlefield / 3+ creatures | 1.7% / 0.1% | 4.3% / 0.9% | 6.9% / 2.8% |
| Zero-step deterministic win available | 0.1% | 1.2% | 2.9% |
| One action from a verified win | 16.9% | 40.8% | 53.5% |

\* Thrasios "castable" *drops* T2->T3 because by T3 more hands have
already cast it (moving it from "castable" to "on battlefield") -
confirmed intentional, not a bug (see `activatable-soon`, which rises
monotonically, for the underlying trend).

**A methodology note on combo accessibility, because it changed a real
number**: the first implementation of "zero-step win available" counted a
combo piece as "available" if it was anywhere the hand had ever put it,
**including the graveyard and exile** - i.e. exactly the "natural
co-location" trap the engagement spec explicitly warned against ("Stop
measuring only natural co-location of two named cards"). Fixed before the
100k run: `zero_step` now requires every piece to be either already
deployed on the battlefield, or in hand and individually affordable from
the turn's mana pool. This dropped the reported rate from an inflated
4.5-6.7% (T1-T3) to the 0.1-2.9% shown above, which is much closer to a
back-of-envelope hypergeometric estimate for two ~0.76%-likelihood 2-card
combos sharing a piece (Devoted Druid) plus one much rarer 3-card combo -
i.e., the corrected number is the trustworthy one.

### Critical secondary output — ranked failure-mode table (dominant reason, % of all 100k hands)

| Failure mode | % of all hands | % of failures |
|---|---|---|
| Insufficient persistent mana (<2 by T3) | 12.4% | 61.6% |
| Tutor present but no viable sequencing | 3.3% | 16.2% |
| No meaningful T1-T2 development at all | 1.2% | 6.0% |
| Color failure (missing a required pip) | ~2.7% combined | ~17.5% combined |

### Extended breakdowns (category 2-15 requests, beyond the primary table)

- **T1 engine class** (not one broad `engine=true` label): premium
  1-drop (Mystic Remora/Esper Sentinel) 8.5% of hands, engine cast via
  acceleration 7.2%, plain 2-mana engine 3.1%.
- **T3 engine-count histogram**: 0 engines 20.8%, 1 engine 18.4%, 2
  engines 27.5%, **3+ engines 33.2%** - most hands that get going get
  going hard.
- **Most frequent T3 live-engine combination**: {Thrasios, Tymna} both
  active, ahead of either commander alone - full ranked list (top 15) in
  the JSON's `t3_top_engine_combinations`.
- **Resource efficiency at T3**: mean 3.88 persistent nonland permanents
  vs. mean 0.09 one-shot/temporary resources consumed (Lotus Petal/Elvish
  Spirit Guide/etc.) - only 9.1% of hands ever burn a one-shot resource at
  all, meaning fast starts in this shell are overwhelmingly *not* coming
  at the cost of resource destruction.
- **Full granular failure taxonomy** (multi-label, % of the 20,084 hands
  actually classified as failed): tutor-stuck 76.3%, insufficient mana
  61.6%, no second land 61.3%, **Mox-family dependency 22.9%**, no land to
  discard to Mox Diamond 12.0%, no creature for a drawn Cradle <1%
  (essentially never the binding constraint).
- **Tutor target-class accessibility** (heuristic per-tutor mapping, not
  "equivalent to every card"): at T1, a castable tutor most often reaches
  land/Cradle/engine-class targets (~11-13% each); by T3 creature/engine/
  combo-piece targets dominate (~9-13% each) as Pod/Survival/Chord become
  live.
- **Archetype tags** (rule-based starting taxonomy, not a data-derived
  clustering - explicitly scoped down, see below): engine hand 79.2%,
  commander-supported hand 56.1%, combo-adjacent hand 53.7%, tutor hand
  32.2%, creature-development hand 28.3%, interaction-heavy hand 6.6%,
  nonfunctional hand 20.1% (multi-label, sums >100%).

## Part B — candidate mulligan heuristics, derived from Part A

`sim/analysis/derive_mulligan_heuristics.py` -> `solo002_mulligan_heuristics.json`
(100k hands, same seed/policy). Correlates features observable **from the
raw 7 cards alone, before any land drop** (the only information a real
mulligan decision has) against Turn-3 outcomes from the same simulated
hands. Reported as lift = P(outcome | feature) - P(outcome | not feature).

**Headline, and the single most actionable finding of this audit**: land
count dominates everything else, and several features that sound like
"good cards to keep" are actually *anti-correlated* with success because
they compete with lands for the same 7 slots in this mana-hungry shell:

| Feature (in the raw 7) | Lift on "meaningful T3" | Prevalence |
|---|---|---|
| 2+ lands | **+0.41** | 62.3% |
| All 4 colors represented in lands | +0.27 | 46.2% |
| 3+ lands | +0.27 | 29.3% |
| 5+ nonland cards (light on lands) | -0.27 | 70.7% |
| 2+ creatures in hand | -0.13 | 77.1% |
| Has castable-class interaction | -0.10 | 69.9% |
| Has a tutor | -0.09 | 67.0% |
| Has any engine card | -0.04 | 67.3% |
| Has acceleration | +0.02 | 64.5% |

Four candidate keep policies were encoded from this (used unchanged by
Parts C/D): **A (Engine-first)** = 2+ lands AND (engine or accel);
**B (Agency-first)** = A AND (interaction or tutor present too);
**C (Speed-first)** = 2+ lands OR accel (loosest); **D (Tutor-inclusive)**
= A but tutor also counts toward the "access" requirement.

## Part C — London mulligan simulation

`sim/analysis/run_mulligan_sim.py` -> `solo002_mulligan_simulation.json`
(25,000 hands per policy = 100,000 total, real London mulligan: fresh 7 at
each look, bottom N cards heuristically on keep, forced keep after 4
mulligans - never actually reached at these keep rates).

| Policy | Keep 7 | Keep 6 | Keep 5 | 4-or-lower | Avg start size | Expected card disadvantage |
|---|---|---|---|---|---|---|
| A Engine-first | 54.0% | 24.8% | 11.4% | 9.7% | 6.19 | 0.81 |
| B Agency-first | 48.0% | 24.8% | 13.1% | 14.0% | 5.99 | 1.01 |
| C Speed-first | 89.9% | 9.0% | 1.0% | 0.1% | 6.89 | 0.11 |
| D Tutor-inclusive | 59.6% | 24.0% | 9.7% | 6.6% | 6.34 | 0.66 |

## Part D — mulligan policy comparison (the tradeoff table)

`sim/analysis/build_part_d_comparison.py` -> `solo002_part_d_policy_comparison.json`.
Policy E (seat-aware) is **explicitly deferred to pod simulations**, per
the engagement's own instruction - not compared here.

| Policy | Keep-7% | Avg hand | Engine T1/T2/T3 | Dev+interaction T3 | Tutor castable T3 | Meaningful T3 |
|---|---|---|---|---|---|---|
| A Engine-first | 54.0% | 6.19 | 30.1/80.0/90.1% | 22.1% | 19.5% | 91.6% |
| B Agency-first | 48.0% | 5.99 | 28.0/77.3/87.9% | 21.9% | 20.1% | 89.2% |
| C Speed-first | 89.9% | 6.89 | 26.2/70.6/82.3% | 23.9% | 19.7% | 83.9% |
| D Tutor-inclusive | 59.6% | 6.34 | 27.8/79.2/90.7% | 23.6% | 21.4% | **92.6%** |

**No universally optimal policy, as expected** - but a genuine tradeoff
worth flagging: **D (tutor-inclusive) keeps *more* hands than A
(engine-first) (59.6% vs 54.0%) while also reaching a slightly *higher*
T3 success floor (92.6% vs 91.6%)**. That's not a contradiction: D is a
strict superset of A's keeps (same criteria, plus "2+ lands and a tutor
with no engine/accel"), and those additional hands still develop well
because a tutor reliably finds an engine downstream in this list. C
(speed-first, loosest filter) keeps the most cards (avg 6.89, essentially
never mulligans below 6) but has the lowest post-mulligan success floor
(83.9%) - the clearest illustration of the resource-vs-selectivity
tradeoff the engagement asked to surface, not resolve.

## Part E — paired-seed deckbuilding harness (infrastructure check)

`sim/analysis/run_paired_comparison.py` -> `solo002_part_e_paired_demo.json`.
Demonstrates (50,000 paired hands) that the same simulator supports
**seed-matched paired reruns** for a proposed card swap: two card-pool
variants are shuffled with identically-seeded RNGs, which - because
`Random.shuffle` is a pure index permutation - guarantees the swapped
card lands in the *same hand, same position* in both variants, so a swap's
effect can be isolated via a per-hand sign test rather than compared as
two independent samples that could disagree by sampling luck alone. The
demo swap (Birthing Pod -> a synthetic basic Forest, `basics_substituted:
true` with an explicit `ablation_justification`, per
`docs/RUN_CLASSIFICATION.md` requirement 2) is **infrastructure proof
only, not a deckbuilding recommendation** - it shows a small, correctly-
signed, monotonic effect (net +411/50,000 hands favoring the extra land on
"meaningful T3", net +188 on "2+ mana by T1"), exactly what's expected of
a low-impact utility creature vs. an unconditional mana source. A real
proposed swap would use two real cards from `data/cards_cache/` in place
of the synthetic row.

## Explicit scope disclosure

Per this project's established practice of disclosing scope reductions
rather than silently omitting them (see the `GATE_4A_2P_DIAGNOSTIC` v2
rerun above): the full engagement spec (Parts A-E across 15 metric
categories) is enormous, and the following were **deliberately scoped
down**, not silently skipped:

- **Archetype clustering (category 15)**: delivered as a **rule-based
  starting taxonomy** (8 tags, see Part A), not a data-derived clustering
  pass (e.g. k-means/hierarchical over the full per-hand feature vector).
  The spec itself invites this ("Do not force these clusters in advance if
  the data suggests better categories") - a real clustering pass is future
  work, not done here.
- **Part E**: one infrastructure-proof swap, not a battery of real
  proposed deckbuilding changes. The harness is confirmed working; using
  it for actual card-swap decisions is the next natural step, not part of
  this audit.
- **Tutor target-class mapping** (category 8) and **failure-mode
  taxonomy** (category 14) use hand-authored heuristic classifications
  (documented in `opening_hand_model.py`/`opening_hand_metrics.py`), not
  an exhaustive manually-reviewed card-by-card pass - consistent with this
  project's existing Gate 1 standard ("heuristic classification, acceptable
  for diagnostic purposes").
- **Joint mana payability** for combination metrics (`engine_plus_interaction`,
  combo "zero-step" with 2+ hand pieces) is approximated per-card against
  the turn's total mana pool, not proven via a full joint-payment search
  across a shared pool - documented inline at each call site.
- **On-the-draw** was not run as a separate population (on-the-play only,
  matching the format's actual default) - a full draw/play split is a
  cheap follow-up (`--on-play` flag already exists) if wanted.

## Answering the engagement's own success-condition checklist

- **T1 two-drop engine rate**: 25.4% any engine active, split 8.5%
  premium 1-drop / 7.2% accelerated / 3.1% plain 2-mana (see Part A).
- **Tymna actually supported vs. merely castable**: T3 castable 13.0% vs.
  supported (on battlefield with 1+ attacker) 46.8% - most Tymnas in play
  by T3 got there before T3 and already have backup.
- **Birthing Pod's legal/useful activation rate**: tracked per-hand via
  `birthing_pod.usable_now` in every snapshot (JSON field, not
  aggregated into a headline number here given Pod's low overall
  prevalence in this 100k population - see `engine_identity_by_turn` for
  its raw presence rate, ~0.3-0.9%).
- **Most common seven-card failure reasons**: insufficient mana (61.6% of
  failures), a stuck tutor (76.3% of failures - overlapping, multi-label),
  and no second land specifically (61.3% of failures) - see the granular
  failure taxonomy above.
- **Best mulligan rule for engine/interaction/resource balance**: no
  single winner by design (Part D) - **D (tutor-inclusive)** for the best
  combined keep-rate/success-floor tradeoff, **A (engine-first)** as a
  close, slightly more conservative alternative, **C (speed-first)** only
  if card count matters more than raw success rate (e.g. grindy pods).

---

# SIM-001 SOLO-002R — Correctness Repair & Rerun

Corrects the SOLO-002 phase above per an explicit correctness-repair review. Same subject
deck/hash. **This section's numbers are the trustworthy ones for this audit's questions -** the
SOLO-002 section above is superseded and retained only for provenance.

## The critical defect, and why the fix moved every number this much

**Root cause**: `_try_pay()` identified which mana sources would cover a cost, but
`_consume_payment_sources()` only ever marked Elvish Spirit Guide and one-shot resources (Lotus
Petal) as spent - a land, mana dork, Sol Ring, Mana Vault, Mox, etc. was never marked tapped, so
it could pay for an unbounded number of spells within the same turn. Every T1-3 development
percentage the simulator produced was computed against this phantom, unlimited mana pool.

**Fixed**: real per-source state. Lands became `LandInPlay` objects and nonland mana sources
gained a `tapped` flag; the payment protocol was split into a pure read-only search (`_try_pay`,
never mutates), a real commit (`_commit_payment`, the ONLY thing that taps/consumes a source),
and a rollback (`_rollback_payment`, used only by read-only joint-payability dry runs) - so a
real cast can never double-spend, and a metrics dry-run can never leave state mutated. An
explicit untap step (`HandState.untap_all()`) runs at the start of every turn, correctly
excluding Mana Vault (real Oracle text: "This artifact doesn't untap during your untap step" -
this project's model does not offer the policy the option to pay {4} at upkeep to untap it, since
doing so is essentially always mana-negative this early - documented simplification, not a
missing feature).

**Scale of the correction** (100k hands, on the play, otherwise identical methodology to
SOLO-002):

| Metric | SOLO-002 (buggy) | SOLO-002R (corrected) |
|---|---|---|
| `mana_2plus` @ T3 | 87.6% | **33.4%** |
| `mana_3plus` @ T3 | 72.5% | **15.1%** |
| `any_engine_active` @ T3 | 79.2% | 74.8% (largely unaffected - see why below) |
| `two_plus_engines_active` @ T3 | 60.8% | **45.3%** |
| `development_plus_interaction` @ T3 | 22.7% | **2.1%** |
| `tutor_castable` @ T3 | 18.9% | **1.4%** |
| secondary `meaningful_development_rate_t3` | 79.9% | **23.4%** |

Engine deployment alone is the least-affected figure because engines are mostly 1-2 mana cards
that a genuinely-tapped-correctly board can often still afford once; it's the *combination* and
*follow-up* metrics (a second engine, a tutor ALSO castable on top of what was already spent,
retained interaction) that collapse hardest - exactly the pattern predicted by "a shared pool
being double-spent inflates joint/compound claims far more than single-card ones."

## A second bug found while fixing the first: Gaea's Cradle

Real Oracle text: `{T}: Add {G} for each creature you control.` The original model treated
Cradle as a flat 1-green-mana land, identical to any basic. Fixed: `available_sources()` now
computes Cradle's tap value from `state.creature_count()` live, every time - `cradle_output_if_
deployed` and `cradle_3plus` already reported the right creature-count-conditioned threshold
language, but the mana it actually produced for payment purposes was wrong until this fix.

## Other mana-source corrections (per real Oracle text, verified against `data/cards_cache`)

- **Gemstone Caverns**: `{T}: Add {C}. If Gemstone Caverns has a luck counter on it, instead add
  one mana of any color.` A luck counter is only obtainable via the pregame action ("if this
  card is in your opening hand and you're not the starting player, you may begin the game with
  Gemstone Caverns on the battlefield with a luck counter, exile a card from your hand") - i.e.
  **only relevant on the draw**. Modeled as a real policy decision (`_setup_gemstone_caverns`):
  on the draw, if the hand isn't already land-heavy, exile the worst card and start with an
  untapped any-color Caverns; on the play, or once the opening-hand window has passed, it's a
  plain colorless land. This is exactly why Part A now runs both a **play** and a **draw**
  baseline - the draw baseline is the only one where this card's real behavior is exercised.
- **City of Traitors**: `When you play another land, sacrifice this land. {T}: Add {C}{C}.`
  Implemented as a real trigger (`_maybe_sacrifice_city_of_traitors`) - it survives being played
  itself, and is sacrificed the moment any *other* land enters from a land drop.
- **Exotic Orchard**: `{T}: Add one mana of any color that a land an opponent controls could
  produce.` Genuinely opponent-dependent and undefined in a true solo/no-opponent structural run
  - modeled as producing **zero mana** here (one of the two options the repair instruction
  offered; running explicit opponent-land-assumption scenarios instead is future work, not done
  in this pass). It can still be played as a land (counts toward land-count metrics), just
  contributes nothing to mana totals.
- **Fetchlands**: previously modeled as static, already-fixed 2-color lands that never touched
  the library at all - exactly the "assign the fetchland's apparent color pair directly" anti-
  pattern the repair instruction named. Fixed: each fetch's two real search types (from its own
  Oracle text, e.g. Flooded Strand = "a Plains or Island card") are matched against the deck's
  actual land subtypes. This deck has **zero true basic lands** - the only fetchable cards are
  the six ABUR duals, each of which genuinely carries two basic land types (e.g. Bayou is
  "Land — Swamp Forest"). Cracking a fetch now really searches the remaining library for a legal
  target, removes it, puts it onto the battlefield untapped, sacrifices the fetch, and costs 1
  life - not a static color assignment.

## Joint payment search (the "don't approximate simultaneity" fix)

The original SOLO-002 build already had one approximation pass (`_affordable_in_isolation`,
checking a cost against the turn's *starting* mana total/colors) specifically to avoid an even
worse bug (checking post-hoc hand contents after the greedy policy had already spent the
relevant mana). That approximation is retained, explicitly renamed and labeled
(`_individually_affordable_from_turn_capacity` in `opening_hand_metrics.py`), for exactly the
single-card "capacity" questions it's honestly answering (e.g. "Tymna castable" in the original
spec's sense of "legally castable this turn," independent of what the greedy policy prioritized
instead) - **never presented as a simultaneity claim**.

For every metric that actually asks about simultaneous/joint availability, a real check replaces
it:
- **`is_currently_castable()`** - a genuine read-only payment search against whatever is
  *currently* still untapped, used for "retained interaction," "tutor also castable," and
  Thrasios's `{4}` activation check (now correctly reflects real remaining mana, not the turn's
  original total - regression test #10 proves this directly: activation reads True with 4
  untapped sources, then False once 2 of those 4 are tapped by something else, on the exact same
  snapshot).
- **`can_pay_jointly()`** - a real multi-cost dry-run (tentative commit, then roll back before
  returning), used for combo "zero-step" status when 2+ pieces are still sitting in hand. This
  directly fixes the "natural co-location" trap: two combo pieces that are each individually
  affordable from the same untouched pool, but not jointly (because they'd need the same single
  source), now correctly fail to register as a live deterministic win - proven in regression test
  #9 using the deck's real `INT-0002` (Devoted Druid + Swift Reconfiguration) line.
- A new **`deterministic_win_protected`** metric extends this further: while a zero-step
  combo's mana is still tentatively committed, the search additionally checks whether a live
  interaction card is *also* jointly payable, before rolling everything back - a real joint
  check across "can I go off" and "can I protect it," not two independent isolated checks.

A related bug caught in the same pass (not named in the original report, but the same root
cause: mana/resource state correctness): cast instants and sorceries (most interaction and most
tutors) were being left in `state.nonland_perms` forever instead of resolving to the graveyard,
which would have corrupted the `persistent_nonland_permanents` resource-efficiency metric. Fixed
alongside the rest (only genuinely permanent-typed cards - creature/artifact/enchantment/
planeswalker/land/battle - stay on the battlefield after being cast).

## Ten regression tests (`rules_tests/regression/test_opening_hand_mana_correctness.py`)

All required proofs pass (13 tests total - two of the ten were split into a positive/negative
pair for sharper coverage):

1. one land cannot pay for two one-mana spells in the same turn
2. Sol Ring cannot be tapped twice
3. Mana Vault cannot be tapped twice, and never auto-untaps (survives a real untap step while a
   normal land untaps normally in the same check)
4. a mana dork cannot tap on its entry turn, and can the very next turn
5. a used source becomes available again after the normal untap step
6. City of Traitors survives its own land drop and sacrifices on the next different land played
   (both a direct unit test and a full `develop_turn` end-to-end sequence)
7. Gemstone Caverns stays in hand on the play; on the draw with a land-light hand it takes the
   luck-counter action and produces any color, untapped, immediately
8. engine + interaction only passes when jointly payable, not when each is merely individually
   affordable from the same untouched pool (both the failing and passing case are proven, plus
   that a failed dry run leaves no tapped sources behind)
9. two combo pieces (the deck's real `INT-0002`) only register `zero_step` when the whole line is
   jointly executable, not when each piece is merely individually affordable
10. Thrasios's `{4}` activation reads correctly against real remaining mana, not a stale
    turn-start total

Full suite: 54 passed, 3 skipped (unrelated pre-existing skips).

## Bounded `best_known_achievable` search (`sim/analysis/achievable_search.py`)

Not a full game-tree search - deliberately out of scope for this project's declared Level 1-2
model (no held priority, no opponent interaction modeled). Instead: a small, fixed, documented
set of alternative lines per hand (every turn-1 land-drop choice in the opening 7, crossed with
3 priority orderings, capped at 12 lines/hand) is explored, and a named target counts as
`best_known_achievable` if *any* explored line reaches it - regardless of whether the single
default greedy line (`policy_realized`, the exact same line the main census uses) got there.
Run at 20,000 hands (disclosed reduced sample - each hand costs ~6x a normal single-line hand):

| Target | policy_realized | best_known_achievable | gap |
|---|---|---|---|
| T1 premium engine | 6.2% | 6.7% | 0.6pp |
| T1 two-drop engine | 3.1% | 3.5% | 0.4pp |
| T1 any meaningful development | 32.2% | 40.7% | **8.4pp** |
| T2 engine | 57.2% | 62.1% | 4.9pp |
| T2 engine + interaction | 0.9% | 1.2% | 0.3pp |
| T3 supported Tymna | 30.1% | 36.3% | 6.2pp |
| T3 Thrasios activation | 3.0% | 4.3% | 1.4pp |
| T3 Pod functional | 0.05% | 0.19% | 0.1pp |
| T3 Survival functional | 1.2% | 2.4% | 1.2pp |
| T3 Cradle 3+ | 1.4% | 1.7% | 0.4pp |
| T3 deterministic win | 0.3% | 0.9% | 0.6pp |

The gaps are modest (0.1-8.4 percentage points) - confirms the greedy policy is a reasonably
good, not wildly suboptimal, development heuristic, while still proving it is not optimal and
should not be the sole basis for calling a hand "incapable." `t1_any_meaningful_development` has
the largest gap by far, meaning the biggest real lever this search finds is simply *which land
to play turn 1* - consistent with Part B's finding below that land count dominates everything
else.

## Redesigned success metrics - no single composite headline

Per the repair instruction, `meaningful_development_rate_t3` is now reported only under
`secondary_convenience_metrics` (23.4% on the play, 25.5% on the draw) - **not** the principal
target. The primary, separately-reported outcomes (`primary_outcomes` in
`solo002r_opening_hand_census_{play,draw}.json`), on the play / on the draw:

| Outcome | On the play | On the draw |
|---|---|---|
| T1 premium engine | 5.9% | 7.1% |
| T1 two-drop engine | 3.1% | 3.4% |
| T2 engine | 57.4% | 65.3% |
| T2 engine + interaction | 0.9% | 1.0% |
| T3 2+ engines | 45.3% | 55.7% |
| T3 supported Tymna | 39.3% | 48.6% |
| T3 Thrasios engine active (on battlefield) | 46.3% | 52.6% |
| T3 Cradle 3+ | 1.5% | 2.1% |
| T3 tutor-convertible | 1.4% | 1.7% |
| T3 deterministic-win accessible | 0.3% | 0.4% |
| T3 Pod functional | 0.04% | 0.08% |
| T3 Survival functional | 1.0% | 1.3% |
| Mean hand/resources remaining T3 | 4.65 cards | 5.06 cards |

The draw baseline is uniformly stronger (extra card + Gemstone Caverns' real value both help),
most visibly on T3 2+ engines (+10.4pp) and supported Tymna (+9.2pp).

### Ranked failure-mode table (100k hands, on the play)

| Failure mode | % of all hands | % of failures |
|---|---|---|
| Insufficient persistent mana (<2 by T3) | **66.6%** | 86.9% |
| Tutor present but no viable sequencing | 4.2% | 5.4% |
| No meaningful T1-T2 development at all | 1.6% | 2.1% |
| Color failure (missing a required pip, all colors combined) | ~3% | ~4% |

The dominant failure mode moved from a modest 12.4% (SOLO-002, buggy) to **66.6%** (corrected) -
the single clearest signal that the original report's mana picture was badly overstated, and
that mana availability (not engine density, tutor density, or interaction density) is this
deck's real, primary bottleneck in the T1-3 window.

## Part B — mulligan heuristics, recomputed on the corrected census (100k hands)

Same feature set as SOLO-002 Part B (raw-7-card features only, before any land drop), recomputed
against the corrected `meaningful_t3` outcome. **Land count remains completely dominant**, and by
an even larger relative margin now that mana is the binding constraint:

| Feature (in the raw 7) | Lift on "meaningful T3" |
|---|---|
| 2+ lands | still the largest positive lift by a wide margin |
| Has any engine card | now **negative** lift (has_cheap_engine ≈ -0.025) |

(Full ranked table in `solo002r_mulligan_heuristics.json`.) The same four candidate policies
(A/B/C/D) from SOLO-002 were reused unchanged - Part B's job is deriving *features*, not
redefining the policies, and the land-count-dominant conclusion did not change in kind, only in
how much more decisive it now looks.

## Part C/D — London mulligan simulation and policy comparison, rerun (100k hands total for C)

| Policy | Keep-7% | Avg hand | Engine T1/T2/T3 | Dev+interaction T3 | Tutor castable T3 | Secondary meaningful T3 |
|---|---|---|---|---|---|---|
| A Engine-first | 54.0% | 6.19 | 23.7/69.8/86.6% | 2.4% | 1.9% | 30.8% |
| B Agency-first | 48.0% | 5.99 | 22.7/67.5/84.2% | 2.3% | 1.8% | 28.8% |
| C Speed-first | 89.9% | 6.89 | 19.4/60.4/78.3% | 2.0% | 1.6% | 26.0% |
| D Tutor-inclusive | 59.6% | 6.34 | 21.8/68.7/86.9% | 2.4% | 1.8% | 29.9% |

The keep-rate/avg-hand-size numbers are **identical** to SOLO-002's Part C, because the London
mulligan decision itself is made on raw hand features before any mana is tapped - only the
downstream T1-3 development numbers shift. The relative ranking of policies is preserved (D
slightly edges A on both keep rate and success floor; C keeps the most cards but has the weakest
floor), but every absolute development number is far lower than SOLO-002 reported, consistent
with the corrected census above.

## What SOLO-002R did NOT redo

- **Part E**: not rerun as part of the *required* rerun protocol (only A-D were named), but was
  rerun anyway for consistency (`solo002r_part_e_paired_demo.json`) since the harness itself
  needed no changes - the corrected engine just makes its paired comparison more trustworthy too.
- **Alternate turn-2/turn-3 land choices and alternate fetch targets** are not explored by the
  bounded `best_known_achievable` search (disclosed scope reduction in
  `achievable_search.py`'s own docstring) - only turn-1 land choice and priority-order
  variation are. A hand could in principle achieve more via a turn-2/3 land choice this search
  doesn't try.
- **Mana Vault's {4}-untap-at-upkeep option** is still not offered to the policy (documented
  simplification, unchanged from SOLO-002) - essentially never correct this early, but a true
  completeness proof would need to consider it.
- **Devoted Druid's own untap ability** ("Put a -1/-1 counter on this creature: Untap this
  creature") is not modeled as a double-tap mana source - out of scope for this pass; the
  deterministic combo it enables (`INT-0002`) is still tracked correctly via the verified
  combo-dependency-graph check, which doesn't require simulating the loop itself.
- **Exotic Orchard's opponent-dependent mana** is modeled as zero rather than run as explicit
  opponent-land-assumption scenarios (the repair instruction's alternative option) - a real,
  disclosed scope choice, not an oversight.

All seven corrected files (`solo002r_opening_hand_census_play.json`,
`solo002r_opening_hand_census_draw.json`, `solo002r_mulligan_heuristics.json`,
`solo002r_mulligan_simulation.json`, `solo002r_part_d_policy_comparison.json`,
`solo002r_achievable_search.json`, `solo002r_part_e_paired_demo.json`) carry `run_class:
DECK_BACKED_GOLDFISH` provenance (`subject_deck_hash`, `subject_deck_card_count`,
`commander_identities`) per `docs/RUN_CLASSIFICATION.md`, and the original SOLO-002 files are
marked `status: SUPERSEDED_PENDING_CORRECTNESS_RERUN` with a `superseded_by` pointer, retained
for provenance, not deleted.

---

# SIM-001 SOLO-003 — Early-Game Trajectory & Mulligan Quality Audit (Part A: Trajectory Census)

Builds on SOLO-002R's corrected mana/rules engine. Per the engagement's own central correction:
**this section does not use "any engine active" or "Tymna supported" as headline success
measures.** Every finding below is built from `sim/analysis/trajectory_metrics.py`'s velocity/
compounding-advantage/agency/conversion metrics - see `results/solo_baseline/
SOLO-003_CHECKPOINT.md` for the full engine-taxonomy, interaction-model, and failure-taxonomy
design (revised per checkpoint review before this census ran). Same subject deck/hash as above.
`run_class: DECK_BACKED_GOLDFISH` throughout.

**Scale**: 100,000 hands on the play + 100,000 hands on the draw (keep-everything, no mulligan
yet), ~76-80s each. A 15,000-hand bounded achievable-search supplement (T1-T3 land/fetch
sequencing with state deduplication) ran separately, per established practice of using a smaller
sample for the ~20x-more-expensive search pass.

## A. What random sevens actually do (T1 → T2 → T3)

| Metric | On the play | On the draw |
|---|---|---|
| T1: any Tier-A engine (Remora/Sentinel/Rhystic/Sylvan) cast | 6.3% | 7.1%\* |
| T1: engine deployed (any tier) | 18.6% | - |
| T1: live interaction | 22.8% | - |
| T1: compound development (2+ of engine/mana-dev/interaction) | 19.4% | - |
| T2: primary (Tier-A) engine online | 18.0% | - |
| T2: infrastructure (Tier-B, *supported*) online | 4.5% | - |
| T2: development + live interaction (real alt-cost model) | 2.0% | - |
| T3: strong card-advantage state | 18.1% | 21.4% |
| T3: strong mana state | 7.4% | 7.7% |
| T3: strong conversion state (tutor live + reaches engine/combo) | 1.0% | 1.3% |
| T3: strong interaction state | 5.5% | 6.7% |
| T3: strong optionality (2+ strong states at once) | 2.5% | 3.4% |
| T3: credible win pressure (deterministic or one-action-away) | 33.7% | 38.5% |
| **T3: any strong state** | **49.9%** | **55.6%** |
| T3: stalled | 45.3% | 39.9% |

\* on-play numbers not independently re-quoted for T1 breakdown to save space - see the raw
`solo003_trajectory_census_{play,draw}.json` files for full parity.

The draw is uniformly stronger (extra card + a chance at Gemstone Caverns' real value), most
visibly on strong card-advantage (+3.4pp) and credible win pressure (+4.8pp). Development +
interaction is rare in absolute terms (~2%) even with the corrected real alternate-cost model -
this deck's actual bottleneck (per SOLO-002R and confirmed again here) is mana, not interaction
density, so "developed while holding up interaction" is inherently a high bar most hands don't
clear by T3.

## B. Most common strong/notable opening sequences (rule-based trajectory families)

Top families by frequency (on the play, multi-label, see `trajectory_family_tags` in the
checkpoint for the full rule set - explicitly a starting taxonomy, not a data-derived clustering):

| Family | % of hands |
|---|---|
| `commander_conversion_hand` (a commander online with real productivity, not just presence) | 41.1% |
| `genuinely_nonfunctional_hand` (no strong state AND <2 mana) | 36.0% |
| `t1_accel_to_t2_commander` | 23.1% |
| `creature_board_supports_cradle_chord_infrastructure` (3+ creatures) | 22.8% |
| `t1_engine_hand` | 18.6% |
| `deceptive_two_land_hand` (2 lands, no strong state) | 14.3% |
| `strong_one_land_hand` (1 land, strong state anyway) | 13.2% |
| `t1_fast_mana_to_t2_multiple_actions` | 11.7% |
| `t1_accel_to_t2_premium_engine` | 9.2% |
| `flooded_hand` (4+ opening-hand lands) | 8.8% |

The rarest named sequences are the most specific engine-to-engine chains (`t1_dork_to_t2_pod`
0.05%, `t1_dork_to_t2_rhystic_study` 0.11%, `t1_accel_to_t2_kinnan` 0.13%) - these are real,
just naturally uncommon given they require two specific cards to co-occur in one 7-9 card window.

## C. Most common bad opening sequences (revised failure taxonomy)

Two separate tag sets, never collapsed into one score (outcome = what went wrong; causal = why):

| Outcome tag | % of hands |
|---|---|
| `insufficient_mana` | 64.9% |
| `stranded_tutor` (tutor in hand, never live) | 60.2% |
| `stranded_or_unsupported_engine` | 56.3% |
| `no_proactive_development` | 55.7% |
| `development_but_no_compounding_value` | 18.2% |
| `color_failure` | 12.8% |
| `resource_destructive_acceleration_no_payoff` | 6.5% |
| `flooded_action_light` | 1.3% |

(Heavily overlapping by design - most failing hands carry several tags simultaneously; there is
no `"functional"` catch-all tag, per the checkpoint correction - a hand's absence of a failure
tag is read from the strong-state flags in section A instead, never from tag absence itself.)
Causal diagnosis is dominated by `insufficient_persistent_mana` (64.9%, tautologically matching
the outcome tag) and `no_second_land` (24.9%) - mana remains this deck's central, structural
bottleneck in the T1-3 window, exactly as SOLO-002R found and this larger, richer census confirms
again from a different angle.

## D. What land count actually means (0/1/2/3/4/5+ stratification)

**The central, clean finding of this census**: strong-compounding-state rate as a function of
*opening-hand* land count (not lands played - that's structurally capped at 3 by turn 3 and
would hide this entirely; see the checkpoint's disclosed fix for why this distinction matters):

| Opening-hand lands | % of population | T3 strong-state rate (play) | T3 strong-state rate (draw) |
|---|---|---|---|
| 0 | 9.7% | 23.5% | 33.0% |
| 1 | 28.0% | 47.0% | 53.9% |
| **2** | **33.0%** | **56.7%** | **60.6%** |
| 3 | 20.5% | 55.0% | 59.9% |
| 4 | 7.2% | 51.3% | 58.3% |
| 5+ | 1.6% | 47.5% | 52.1% |

**Two lands is empirically the peak, not just "the usual advice"** - the strong-state rate rises
sharply from 0→1→2 lands, essentially plateaus from 2→3 (56.7%→55.0% play, 60.6%→59.9% draw -
within noise), and then *declines* at 4 and clearly declines at 5+. This directly answers the
engagement's own question ("Is two lands actually the ideal baseline?") with a yes, for this
exact 27-land, acceleration-dense list - three is a legitimate, nearly-equivalent keep, and four
or more measurably costs the hand real strong-state probability without buying back enough
consistency to compensate (mean cards remaining at T3 climbs from 3.38 at 2 lands to 3.72 at 4 to
4.34 at 5+, i.e. those extra lands are mostly just sitting dead in hand past the 3rd land drop).

## E. What makes a one-land hand keepable

1-land hands split sharply by whether Turn 1 acceleration (a mana creature, a persistent rock, or
burst mana) was available and used:

- **With T1 acceleration**: 56.0% reach a T3 strong state.
- **Without T1 acceleration**: 36.6% reach a T3 strong state.

A **19.4-percentage-point gap** - a one-land hand with real T1 acceleration performs close to an
*average* two-land hand (56.7%), while a one-land hand with no acceleration is closer to the
0-land tier. Practical finding: **"one land" is not itself a keep/mulligan signal - "one land plus
a genuine T1 mana source" is.** 25.1% of 1-land hands had a mana creature available, 28.3% had a
persistent rock, 11.0% had burst mana (Lotus Petal/Elvish Spirit Guide) - these categories
overlap (a hand can have more than one).

## F. What makes a two-land hand good

The single largest hand class (33.0% of the population) is also the most heterogeneous:

- Overall strong-state rate: 56.7% - but **43.3% of two-land hands are "deceptive"** (2 lands,
  no strong state reached) - a large minority of the "ideal" land count still underperforms.
- Full color coverage (all of W/U/B/G reachable by some point in T1-3) barely moves the needle on
  this coarse strong-state flag: 57.4% with full color vs. 56.5% without - suggesting that at 2
  lands, raw mana quantity/engine access dominates over color completeness for *this* metric
  (color could still matter more for specific colored spells not captured by the broad
  strong-state flag - a finer color-specific breakdown is future work).
- 69.3% of two-land hands get *some* engine online by T2 (a looser bar than "primary Tier-A
  engine," which is part of why this doesn't match section A's 18.0% population-wide T2
  primary-engine rate).
- Tutor-convertible by T3: only 1.9%. Live interaction retained by T3: only 6.6%. Two lands alone
  is not remotely enough to also hold up interaction or convert a tutor in this list.

## G. When three or more lands become costly (opportunity cost)

| Opening-hand lands | T1 engine rate | Tutor-convertible T3 | Live interaction T3 | Mean cards remaining T3 | Strong-state rate | Stalled rate |
|---|---|---|---|---|---|---|
| 3 | 21.2% | 2.0% | 6.7% | 3.24 | 55.0% | 38.0% |
| 4 | 19.3% | 2.0% | 6.7% | 3.72 | 51.3% | 42.3% |
| 5+ | 14.3% | 1.6% | 5.2% | 4.34 | 47.5% | 47.2% |

A clean, monotonic story: every action-density metric (T1 engine rate, strong-state rate) declines
as opening-hand land count climbs past 3, while cards-remaining and stalled-rate both climb -
extra lands beyond 3 are consistently *more mana this hand didn't need* rather than *more
consistency this hand was short on*. Combined with section D: **the practical land-count target
for a keepable seven in this list is 2, with 3 an acceptable near-equivalent; 4+ is a real,
measurable cost, not merely "safe but slow."**

## H. Development + interaction (real alternate-cost model)

Using the corrected alternate-cost interaction model (Force of Will/Fierce Guardianship/Flare of
Denial/Subtlety/Misdirection/Commandeer/Endurance's real alt costs, Force of Negation/Mindbreak
Trap confirmed structurally unavailable solo - see checkpoint item 3), T2 development +
interaction sits at only 2.0% of the population. This is a real number, not an artifact of an
undercounted interaction model (the alt-cost fix, if anything, pushes this *up* relative to a
naive mana-only check) - it reflects that by T2, most hands that developed anything meaningful
have already spent the mana that would have paid for interaction, exactly the mana-scarcity
story sections C/D/G already tell from other angles.

Compounding-state combination rates (T3, population-wide): `card_engine_plus_mana_engine` 10.9%,
`engine_plus_win_conversion` 9.3%, `multi_engine_plus_interaction` 2.6%, `cradle_plus_creature_
infrastructure` 3.0%, `survival_supported` 3.4%, `mana_engine_plus_tutor` 1.2%,
`card_engine_plus_interaction` 1.0%, `tutor_plus_resources_to_deploy` 0.9%, `card_engine_plus_
tutor` 0.1%, `pod_supported` 0.05% (Pod is rarely both deployed and actually functional this
early - consistent with SOLO-002R's near-zero Pod-functional rate).

## I. Tymna and Thrasios (conditional metrics only, never headline success)

**Tymna** is measured as attack capacity (creatures able to attack), explicitly not confirmed
card productivity - this model doesn't simulate combat/blocks, so it cannot know how many
attacks would connect: `not_deployed` 60.3%, `attack_capacity_high` (3+ creatures) 18.0%,
`attack_capacity_medium` (2) 16.9%, `attack_capacity_low` (0-1) 4.8%. **When Tymna is deployed,
it usually already has real attack capacity** (34.9 of the 39.7% deployed rate is medium-or-high)
- consistent with the greedy policy's commander-priority sitting behind acceleration/premium-
engine, so by the time enough mana exists to cast Tymna, a board often already exists too.

**Thrasios** productivity (real `{4}` activation check, `{2}` when Training Grounds is out per
its actual Oracle text - Training Grounds has no relationship to Kinnan's mana-doubling trigger
or to Gaea's Cradle, both corrected in the checkpoint after an initial wording error) is
**2.7%** of the population by T3 - i.e. Thrasios being *on the battlefield* is common (SOLO-002R
found ~46-53% battlefield presence), but Thrasios being *productive* (able to actually activate)
is rare. This is exactly the gap the engagement asked this audit to surface: presence and
productivity are very different numbers for this commander.

## Bounded achievable-search supplement (15,000 hands, T1-T3 land/fetch dedup search)

| Target | policy_realized | best_known_achievable | gap |
|---|---|---|---|
| T1 premium engine | 6.1% | 6.7% | 0.6pp |
| T1 two-drop engine | 3.0% | 3.5% | 0.4pp |
| T1 any meaningful development | 31.9% | 37.9% | 6.0pp |
| T2 engine | 56.4% | 61.8% | 5.3pp |
| T2 engine + interaction | 4.0% | 4.9% | 0.9pp |
| T3 Tymna supported | 39.7% | 48.4% | 8.7pp |
| T3 Thrasios activation | 2.6% | 4.6% | 2.0pp |
| T3 Pod functional | 0.04% | 0.19% | 0.15pp |
| T3 Survival functional | 0.9% | 2.5% | 1.5pp |
| T3 Cradle 3+ | 1.3% | 1.8% | 0.5pp |
| T3 deterministic win | 0.3% | 0.9% | 0.6pp |

Gaps are modest (0.15-8.7pp) and land-choice/fetch-target sequencing (not just priority order)
now demonstrably matters more than SOLO-002R's T1-only search found (`t3_tymna_supported`'s gap
widened from 6.2pp to 8.7pp with the expanded search) - the greedy policy remains a reasonable,
not-wildly-suboptimal heuristic, while confirming a hand should not be written off as incapable
purely because this one policy chose a different legal line.

## Practical findings (primer-facing, per the engagement's own requested format)

- **Two lands is not itself the keep rule, but it is empirically the right target**: strong-state
  rate peaks at 2 opening-hand lands (56.7% play / 60.6% draw), 3 lands is a near-equivalent
  (55.0%/59.9%), and 4+ lands is a measurable, monotonic cost (51.3%→47.5% play as lands climb
  from 4 to 5+), not just "safe but slow."
- **One-land hands containing genuine Turn-1 acceleration perform close to an average two-land
  keep** (56.0% strong-state rate vs. 56.7% for the 2-land population overall), while one-land
  hands without any T1 acceleration underperform badly (36.6%) - "one land" alone is not a
  meaningful keep/mulligan signal; "one land plus real T1 mana development" is.
- **Two-land hands are not uniformly good** - 43.3% of them reach no T3 strong state at all,
  meaning land count alone is a weak predictor within this bucket; color completeness barely
  moves this particular metric, so the real differentiator is more likely mana quantity/engine
  access (a finer feature breakdown is the natural next analysis, not yet run - see below).
  - **Commander presence and commander productivity are different facts.** Thrasios is on the
  battlefield far more often than it is actually able to activate (2.7% real activation vs.
  SOLO-002R's ~46-53% presence); Tymna's productivity (attack capacity) is concentrated in hands
  where it was cast late enough to already have board support, not evenly spread across all
  deployments.
- **Mana remains this deck's dominant, structural bottleneck** in the T1-3 window across every
  lens this audit applied (raw failure taxonomy, land-count stratification, one/two-land audits,
  development+interaction rarity) - not engine density, not tutor density, not interaction
  density, consistent with and further sharpened from SOLO-002R's own headline finding.

## Explicit scope disclosure

Consistent with this project's standing practice of disclosing reductions rather than silently
omitting them: **this write-up completes SOLO-003 Part A (the trajectory census) and its
required first-deliverable checkpoint, plus a supplementary achievable-search pass.** The
following later phases of the SOLO-003 spec are **not yet run**, flagged as the natural next
phase rather than silently skipped:

- **Part B/C (candidate mulligan-heuristic derivation + London mulligan simulation)** - this
  census is exactly the input Part B needs ("do not begin by deciding keep rules - derive them
  from the census"), but deriving and then simulating new trajectory-informed keep policies
  against the existing SOLO-002R policies is a distinct, substantial next step not executed here.
- **Section 15 (opening-hand feature-tradeoff analysis)** and **section 16's data-derived
  clustering** (as opposed to the rule-based `trajectory_family_tags` delivered above) - both
  flagged as future work in the checkpoint.
- **Paired land/mana-density ablations** - the checkpoint redesigned the candidate proposal (to
  avoid the solo-model-inert-card bias its first draft had) but did not execute any ablation run.
- **Sections J/K/L of the "required primary report" structure** (mulligan-policy comparison,
  mana-density ablations, consolidated practical findings beyond what's stated above) depend on
  the above and are correspondingly not yet written.

All trajectory-census and achievable-search files carry `run_class: DECK_BACKED_GOLDFISH`
provenance (`subject_deck_hash`, `subject_deck_card_count`, `commander_identities`) per
`docs/RUN_CLASSIFICATION.md`. Regression suite: 63 passed, 3 skipped (pre-existing, unrelated).
