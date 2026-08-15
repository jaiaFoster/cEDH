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

> **⚠️ STATUS: `SUPERSEDED_PENDING_CORRECTNESS_RERUN`.** Review of this section's commit found
> three semantic bugs: (1) `total_mana` in the failure classifier and the `t3_any_strong_state`
> headline was computed from post-cast LEFTOVER mana, not the turn's starting capacity, so a hand
> that spent its whole turn productively could still be labeled `insufficient_mana`; (2) combo
> proximity conflated a genuine tutor-backed or mana-backed "one action from a win" with a
> topdeck-dependent one, and counted a merely-in-hand (not castable) tutor as "live," inflating
> `credible_win_pressure`; (3) Tymna's attack-capacity metric counted summoning-sick creatures
> (including a same-turn Tymna) as able to attack. **Every number below that depends on
> `total_mana`, combo-proximity tiering, or Tymna's attack capacity is invalidated** - this
> includes the headline 56.7% two-land strong-state rate, the 33.7% credible-win-pressure figure,
> the 64.9% insufficient-mana figure, and the 36.0% genuinely-nonfunctional-hand figure. The
> corrected rerun, with all three bugs fixed, Kinnan's mana-doubling trigger implemented, and a
> newly-discovered commander cast-order non-determinism bug also fixed, is in the
> **"SIM-001 SOLO-003R"** section below. This section and its `solo003_*.json` files are retained
> for provenance only, per standing instruction not to delete superseded work.

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

---

# SIM-001 SOLO-003R — Metric Repair & Corrected Trajectory Census

A targeted repair pass on SOLO-003 Part A, in direct response to a code review of that section's
commit. The review found three real semantic bugs (two of them contaminating headline findings),
requested a **surgical metric repair, not another redesign**, plus implementing Kinnan's
mana-doubling trigger before any land-density conclusions, then rerunning the census before
starting mulligan-policy derivation. This section is exactly that: the four fixes, a
fifth fix discovered while validating the rerun, and the corrected 200,000-hand-plus census.
`run_class: DECK_BACKED_GOLDFISH` throughout, same subject deck/hash as above.

## What was actually wrong

**1. Mana capacity vs. utilization vs. shortfall, conflated into one number.**
`snapshot_metrics()`'s `total_mana` was `state.total_mana_value()` - LEFTOVER mana, queried
*after* `develop_turn()` had already spent the turn's mana on real casts - not the turn's
starting capacity. A hand that goldfished T1 dork → T2 engine → T3 commander, spending nearly
every mana it had on genuinely productive actions, could finish T3 with 0-1 untapped mana and get
labeled `insufficient_mana`. That is mana *utilization*, not a mana *failure*. Worse, this same
leftover value silently fed `t3_strong_mana_state` (and therefore `t3_any_strong_state`, the
metric behind the disputed 56.7% two-land headline), `t3_stalled`,
`tutor_plus_resources_to_deploy`, `no_proactive_development`, `color_failure`,
`interaction_heavy_slow_hand`, `genuinely_nonfunctional_hand`, and SOLO-002R's own
`classify_failure_mode` - not just the one outcome tag the review quoted. Fixing only that one
tag would have left the two-land headline sitting on the same flawed value it was raised to
re-validate, so the fix went to the root: `snapshot_metrics()` now reads `state.turn_start_mana`/
`state.turn_start_colors` (captured right after the land drop, before any casting - exactly the
capacity quantity the surrounding code's own comments already described wanting, but never
actually used) for `total_mana`/`colors_available`. The old leftover value is preserved,
explicitly named, as `mana_remaining_unused`/`colors_remaining_unused`, for anything that
specifically wants it. A genuinely new third concept was added: `mana_shortfall` - true only when
a desirable card actually in hand (a tutor, an engine of any tier, or an interaction spell) was
uncastable even against the turn's *full* capacity spent on nothing else. Only this third
quantity is real evidence of a mana bottleneck; capacity and utilization are not. (An early
version of this check also treated a still-uncast commander sitting in the command zone as
"desirable" - dropped after testing showed it fires on nearly every hand that hasn't assembled
all four commander colors by T1-T3, which is normal and not a bottleneck finding; commander
affordability is already tracked exactly by its own dedicated `{name}_castable` field.)
`classify_trajectory_failure`'s tags are renamed accordingly: `insufficient_mana`/
`insufficient_persistent_mana` (leftover-based) are replaced by `low_mana_capacity`
(capacity-based) and `mana_shortfall` (the real bottleneck signal).

**2. Combo proximity inflated "credible win pressure."** Two bugs stacked here. First,
`has_tutor_live` counted a tutor merely *sitting in hand* (`tutor_candidates_in_hand`) as
equivalent to a tutor that was actually *castable* (`tutor_live`) - exactly the live-vs-present
distinction this project has enforced everywhere else, defeated by one stray `or`. Second, the
single `one_action_away` tier collapsed three different situations into one label, and
`one_action_from_verified_win` (feeding "credible win pressure") counted all of them: a missing
piece already seen and only blocked by mana (a real, execution-dependent-only-on-mana signal); a
missing, unseen piece a *live, combo-reaching* tutor could fetch this turn (a real, concrete
action); and a missing, unseen piece with no such tutor, requiring a natural topdeck of the exact
card (a much weaker signal). All three were reported as "one action away." Fixed by splitting into
`one_mana_step_from_win` / `one_tutor_step_from_win` / `one_draw_step_from_win`, requiring a
counted tutor's own target-class reach to actually include `combo_piece` (a land-only tutor like
Sowing Mycospawn cannot fetch a creature combo piece and must not be treated as if it could), and
redefining `one_action_from_verified_win` to exclude the draw-dependent case entirely.

**3. Tymna's attack capacity ignored summoning sickness.** `tymna_attack_capacity()` said it
measured "creatures able to attack" but called `state.creature_count()`, which deliberately
includes summoning-sick creatures (correct for its other uses - Gaea's Cradle's per-creature mana
output, Birthing Pod/Survival of the Fittest sacrifice-fodder legality - none of which care about
attack eligibility). A same-turn Tymna, or a same-turn creature next to an older Tymna, was being
counted as an active attacker. Fixed with a new `HandState.attack_eligible_creature_count()`
(controlled continuously since the start of the turn - this decklist has no haste effects, so
`entered_turn != state.turn` is the complete legality check), wired into
`tymna_attack_capacity()`, `_tier_c_supported()`'s Tymna branch, and the
`tymna_supported`/`tymna_creatures_for_attack` fields SOLO-003's own `commander_conversion_hand`
family tag depends on. `creature_count()` itself is unchanged - still correct for the uses that
don't care about sickness.

**4. Kinnan, Bonder Prodigy's mana-doubling trigger, implemented.** Real Oracle text: "Whenever
you tap a nonland permanent for mana, add one mana of any type that permanent produced" - a
triggered ability with no cost or summoning-sickness check on Kinnan herself, only requiring
Kinnan on the battlefield. Now modeled in `available_sources()` by doubling a nonland mana
permanent's per-tap count while keeping its color set, explicitly excluding lands (Gaea's Cradle
is a land, untouched) and Elvish Spirit Guide (never a permanent - a zero-cost hand ability). This
was flagged as a prerequisite for trusting any land-density conclusion, since Kinnan being present
but its mana-doubling absent would have made "the deck needs more mana" a conclusion drawn from a
model that doesn't know one of the deck's own primary mana engines is under-producing.

**5. A newly-discovered non-determinism bug, found while validating this rerun.** Running the
*unmodified* pre-fix code twice with the identical `--seed 42` produced substantially different
results (Tymna's population-wide deployment rate swung from 60.5% to 70.0% across two runs of the
same code). Root cause: `develop_turn()`'s commander-casting branch built its candidate list via
`list(state.command_zone)` - iterating a bare Python `set` of strings, whose iteration order
depends on the interpreter's per-process string-hash seed (randomized by default; not fixed by
`random.Random(seed)`). When both commanders were castable but the turn's mana could only pay for
one, which one won the tie was silently process-dependent. This predates the current repair pass
and affects every prior census's commander-adjacent numbers, not just this one. Fixed by iterating
`COMMANDERS`' fixed declared order instead of the raw set; verified reproducible across 5+
consecutive same-seed reruns before and after. Devoted Druid's second-tap untap ability remains
un-modeled, as before - flagged by the review as a caution for mana-density conclusions specifically,
not one of the required fixes, and left out of this surgical pass.

All five fixes are covered by 14 new regression tests in
`rules_tests/regression/test_solo003r_metric_fixes.py` (77 total regression tests pass, up from
63).

## Corrected numbers

**Scale**: 100,000 hands on the play + 100,000 hands on the draw (keep-everything), seed 42,
~72-74s each (~1,360-1,400 hands/sec). Achievable-search supplement: 15,000 hands, seed 42, on
the play, ~59s (avg. 21.7 lines explored/hand).

### A. Trajectory table (T1 → T2 → T3), corrected

| Metric | On the play | On the draw | (was, SOLO-003) |
|---|---|---|---|
| T1: any Tier-A engine cast | 6.3% | 7.7%* | 6.3% / 7.1% |
| T1: engine deployed (any tier) | 18.6% | 23.2% | 18.6% |
| T3: strong card-advantage state | 18.1% | 21.4% | 18.1% / 21.4% |
| T3: strong mana state | 25.3%\*\* | 30.3%\*\* | 7.4% / 7.7% |
| T3: strong conversion state | 1.0% | 1.3% | 1.0% / 1.3% |
| T3: strong interaction state | 5.5% | 6.8% | 5.5% / 6.7% |
| T3: strong optionality (2+ at once) | 7.1% | 9.8% | 2.5% / 3.4% |
| **T3: credible win pressure** | **3.1%** | **4.1%** | **33.7% / 38.5%** |
| **T3: any strong state** | **43.8%** | **51.1%** | **49.9% / 55.6%** |
| T3: stalled | 26.9% | 19.5% | 45.3% / 39.9% |

\* T1 numbers are structurally unaffected by the capacity/shortfall or combo fixes and match the
prior census within noise (Tymna/commander-adjacent T1 numbers can still shift slightly - see fix
#5). \*\* `t3_strong_mana_state` rose because it now checks real starting capacity
(`total_mana >= land_count + 2`) instead of leftover mana that was mechanically suppressed by
whatever the hand had already cast - the metric now measures what it always claimed to measure.

**Credible win pressure and strong-mana-state both moved in the direction the review predicted**:
win pressure collapsed from a hugely inflated 33.7%/38.5% to a real 3.1%/4.1% once the
draw-dependent case was excluded, and strong-mana-state rose because it's no longer artificially
suppressed by productive spending. **T3: any strong state fell from 49.9%/55.6% to 43.8%/51.1%**
- net lower, because the credible-win-pressure collapse outweighs the strong-mana-state rise.

### B. Failure taxonomy, corrected

| Outcome tag | On the play (was) |
|---|---|
| `stranded_tutor` | 60.2% (60.2%) |
| `stranded_or_unsupported_engine` | 56.3% (56.3%) |
| **`mana_shortfall`** (real bottleneck evidence - replaces `insufficient_mana`) | **49.8%** (was 64.9% as `insufficient_mana`) |
| `development_but_no_compounding_value` | 40.0% (18.2%) |
| `color_failure` | 18.5% (12.8%) |
| `no_proactive_development` | 18.4% (55.7%) |
| **`low_mana_capacity`** (capacity-based, replaces the old leftover check) | **15.8%** |
| `resource_destructive_acceleration_no_payoff` | 7.6% (6.5%) |
| `flooded_action_light` | 1.3% (1.3%) |

Causal diagnosis: `mana_shortfall` 49.8% (was `insufficient_persistent_mana` 64.9%,
tautologically matching the old outcome tag), `no_second_land` 24.9%. **Mana shortfall is still
this deck's single largest causal tag - the finding survives, at a materially lower and now
methodologically defensible rate** (49.8% vs. the old 64.9%, and now backed by an actual
"a desirable card was uncastable even at full capacity" check rather than a leftover-mana proxy).
`no_proactive_development` fell sharply (55.7% → 18.4%) because it previously double-triggered off
the same leftover-mana confusion at T1/T2; it's now measuring real early inaction.

### C. Land-count stratification, corrected - the central finding survives

| Opening-hand lands | % of population | T3 strong-state (play) | (was) | T3 strong-state (draw) | (was) |
|---|---|---|---|---|---|
| 0 | 9.7% | 20.9% | 23.5% | 31.5% | 33.0% |
| 1 | 28.0% | 43.1% | 47.0% | 51.6% | 53.9% |
| **2** | **33.0%** | **50.8%** | **56.7%** | **57.0%** | **60.6%** |
| 3 | 20.5% | 47.3% | 55.0% | 53.1% | 59.9% |
| 4 | 7.2% | 39.1% | 51.3% | 46.3% | 58.3% |
| 5+ | 1.6% | 29.2% | 47.5% | 33.5% | 52.1% |

**The review's own suspicion was right: the shape of the curve survives, even though every
absolute number is lower.** Two lands is still the peak (50.8% play / 57.0% draw), three is still
the closest near-equivalent (47.3%/53.1%), and the decline from 3→4→5+ is still monotonic in both
directions. The magnitude of the peak is smaller than the old 56.7%/60.6% (unsurprising - a chunk
of the old number was the now-removed draw-dependent combo-pressure inflation), but **"two lands,
three as an acceptable near-equivalent, four or more as a real cost" is unchanged as a
conclusion.** One-land-with-T1-acceleration is still a real, large effect: 60.9% strong-state rate
with T1 acceleration vs. 22.5% without - if anything a *wider* gap than the old 56.0%/36.6%.

### D. Two-land audit, corrected

Overall strong-state rate 50.8% (was 56.7%); **49.2% of two-land hands are still "deceptive"**
(was 43.3% - deceptive-hand share rose because the strong-state bar dropped along with the
combo-pressure fix). Full color coverage: 55.4% strong-state with full color vs. 42.7% color-screwed
- a real, larger gap than the old census found (57.4% vs. 56.5%, "barely moves the needle") - color
completeness matters more for two-land hands than the buggy version suggested, since it's no
longer being drowned out by inflated combo-pressure noise. Engine online by T2: 69.3% (69.3%,
unchanged - this metric never depended on the buggy fields).

### E. Tymna and Thrasios, corrected

Tymna: `not_deployed` 60.3%, `attack_capacity_medium` 18.3%, `attack_capacity_low` 19.5%,
`attack_capacity_high` 1.9% (was 16.9%/4.8%/18.0% respectively - `attack_capacity_low` rose
sharply and `attack_capacity_high` fell sharply, exactly as expected once summoning-sick
creatures stopped counting as attackers). `commander_conversion_hand` (a commander online with
real, sickness-respecting productivity) fell from 41.1% to 37.0% for the same reason. Thrasios
productivity: 2.8% play / 3.5% draw (was 2.7%/2.7%) - materially unchanged, since Thrasios's own
`{4}` activation check never depended on the buggy fields.

### F. Achievable-search supplement, corrected (15,000 hands)

| Target | policy_realized | best_known_achievable | gap | (old gap) |
|---|---|---|---|---|
| T1 premium engine | 6.1% | 6.7% | 0.6pp | 0.6pp |
| T1 any meaningful development | 25.3% | 31.2% | 5.9pp | 6.0pp |
| T2 engine | 56.4% | 61.8% | 5.3pp | 5.3pp |
| T3 Tymna supported | 35.3% | 44.8% | 9.6pp | 8.7pp |
| T3 Thrasios activation | 2.7% | 4.7% | 2.0pp | 2.0pp |
| T3 deterministic win | 0.3% | 0.9% | 0.6pp | 0.6pp |

Gaps are essentially unchanged from the old census (this search targets rules-state facts -
engine/commander/combo presence - that were never built on the buggy leftover-mana or
combo-proximity fields), confirming the sequencing-matters finding is independent of the metric
repair: the greedy policy remains a reasonable, not-wildly-suboptimal heuristic, and a hand should
not be written off as incapable purely because this one policy chose a different legal line.

## What this changes about the practical findings

- **"Mana remains this deck's dominant structural bottleneck" survives, at a corrected,
  defensible magnitude.** `mana_shortfall` (49.8%, the real "a desirable card failed specifically
  because mana generation was insufficient" signal) is still the largest single outcome/causal
  tag, materially lower than the old 64.9% but built on an actual bottleneck check now instead of
  a leftover-mana proxy that any productive turn would trip. Kinnan's mana-doubling is now
  modeled, so this conclusion no longer rests on a model that's blind to one of the deck's own
  central mana engines.
- **"Two lands is empirically the peak, three a near-equivalent, four+ a real cost" survives
  unchanged as a conclusion**, at corrected magnitudes (50.8%/57.0% peak vs. the old 56.7%/60.6%).
  This was the review's own stated expectation, and it held.
- **"One land plus real T1 acceleration is close to an average two-land keep" survives and is
  slightly stronger** (60.9% vs. 22.5%, a 38.4-point gap, vs. the old 56.0%/36.6%, a 19.4-point
  gap).
- **"33.7% credible win pressure" and "56.7% two-land strong-state rate" are retracted as stated.**
  The corrected figures are 3.1% and 50.8% respectively - both real numbers now, not artifacts,
  but neither should be cited at their old magnitude going forward.
- **"64.9% insufficient mana" and "36.0% genuinely nonfunctional" are retracted as stated.** The
  corrected figures are `mana_shortfall` 49.8% and `genuinely_nonfunctional_hand` 14.1%
  respectively (down sharply, since that tag's `total_mana < 2` check was previously almost never
  false under the old leftover semantics - most hands spend below 2 mana leftover at some point
  even when doing well).
- **A new, disclosed reproducibility caveat**: every prior census run (SOLO-002/002R/003, not
  just this one) was subject to the commander cast-order non-determinism described in fix #5.
  Metrics that never route through a commander-casting tie (land-count population shares, T1
  engine/acceleration rates, the mana/combo fixes themselves) are unaffected. Metrics sensitive to
  which commander wins a tied cast (Tymna's exact tier split, `commander_conversion_hand`'s exact
  rate) carry additional historical uncertainty in the pre-SOLO-003R files beyond what's disclosed
  above - not something this repair pass re-litigates for already-superseded sections, but worth
  knowing before treating any single historical number as more precise than it was.

## Scope note

This remains a **surgical metric repair**, not a new phase. Part B/C (mulligan-heuristic
derivation + London mulligan simulation), section 15/16 (feature-tradeoff analysis and
data-derived clustering), and the paired land/mana-density ablations are still not run - now
formally unblocked by this repair, per the review's own instruction to fix-then-rerun before
starting mulligan-policy derivation.

---

# SIM-001 SOLO-004 — Data-Derived Mulligan Heuristics & London Mulligan Optimization

Uses the validated SOLO-003R census to DERIVE mulligan heuristics, not to prove pre-decided ones.
Per the engagement's own binding constraint: no rule ("2 lands = keep," "keep any engine," "keep
tutor + mana") was assumed going in - each was tested, and several were falsified by the data (see
below). `run_class: DECK_BACKED_GOLDFISH` throughout, same subject deck/hash as above.

## Method summary

1. **Opener-visible feature extraction** (`opening_hand_features.py`) - 75 features computable
   from ONLY the seven-card hand plus known deck construction (fetch-target legality against the
   real remaining library), never future draws. Distinguishes a card being *in hand* from being
   *usable* - a mana dork cast T1 cannot tap until T2 (summoning sickness), so
   `t1_accel_executable_now` is tracked separately from mere presence.
2. **Multi-objective outcome dataset** (`run_solo004_dataset.py`) - 100,000 hands each, play and
   draw, joining opener features to the full outcome vector (development/agency/commander-
   conversion/engine-functionality/conversion/resources - never a single composite), plus a
   15,000-hand achievable-search-enabled variant per seat recording both the greedy-realized and
   best-known-achievable outcome for each hand.
3. **Land-population effect-size analysis** and **conditional outcome distributions** - for every
   opening-hand land count (0 through 5+) and a curated set of structural hand classes, measured
   actual lift and full conditional outcome vectors, not assumed correlations.
4. **Interpretable value models** - logistic regression (5-fold CV AUC 0.841) and a depth-4
   decision tree (CV AUC 0.774, holdout-checked), against a GBM upper-bound benchmark (CV AUC
   0.860) never used as the final heuristic.
5. **Five explicit, disclosed objective profiles** (DEVELOPMENT/AGENCY/SPEED/RESILIENCE_FIRST,
   BALANCED) - no profile declared correct; used to show how emphasis shifts.
6. **Machine-optimal keep frontiers** - keep-at-7 threshold = E[value of a fresh 7, optimally
   bottomed to 6] (what mulliganing actually gets you, not an idealized next hand).
7. **Real London mulligan mechanics + search-based bottoming** - exhaustive bottom search (all
   C(7,N) combinations) shown to meaningfully beat a fast heuristic, so it's used for all
   quantitative results.
8. **Three candidate policies run through 100,000 full mulligan sequences each**, play and draw:
   `MACHINE_OPTIMAL` (ceiling reference, 5k sample), `TREE_DEPTH4`, and `SIMPLE_RULES` (the
   primer-facing candidate).
9. **False-keep/false-mulligan audit**, **per-tutor and per-interaction-density analysis**, and a
   **play-vs-draw comparison**, all before finalizing anything.

## What separates good hands from bad (sections 3-4)

The land-count population itself is a weak predictor. Within EVERY land-count bucket from 0
through 5+, the dominant drivers are the same: acceleration density and engine access, not land
count. At 2 lands (33.0% of the population, the largest single bucket):

| Feature | Lift on t3_any_strong_state | With | Without |
|---|---:|---:|---:|
| T1 premium engine cast | +52.9pp | 100.0% (n=2304) | 47.1% |
| Sol Ring present | +47.6pp | 95.0% (n=2349) | 47.4% |
| Premium one-drop card present | +45.3pp | 89.8% (n=4529) | 44.6% |
| 2+ acceleration cards | +39.9pp | 81.6% (n=7504) | 41.7% |
| Tier-A engine card present | +33.8pp | 75.9% (n=8464) | 42.1% |
| **Interaction-only hand** | **-37.9pp** | 15.6% (n=2404) | 53.5% |

This same shape holds directionally at every land count tested (0/1/3/4/5+); the full breakdown
is in `solo004_land_population_analysis.json` and `solo004_conditional_hand_outcomes.json`.

**Two findings directly contradict hypotheses the engagement explicitly warned against assuming:**

- **"Tutor + mana = keep" is false.** `2_land_with_tutor` (no engine) succeeds only 43.5% of the
  time vs. 59.2% for its complement (-12.4pp). Zooming out to every individual tutor card in the
  deck (`solo004_tutor_interaction_analysis.json`): EVERY one of them, held in an opening hand,
  correlates with a LOWER strong-state rate (35.4%-38.9%) than having no tutor at all (51.6%).
  Stranded-tutor rate is 67%-95% for every tutor card - most opened tutors never go live in this
  3-turn window. A tutor is a real opportunity cost in the opener, not a keep-enabler, at any
  land count, full stop.
- **"4+ lands is safe but slow" is false; it's a real cost, and "an engine" doesn't fix it.**
  4+-land hands with a premium one-drop engine succeed 97.5% of the time; with any OTHER engine,
  30.5%; with no business at all, 17.6%. Flood is rescued specifically by a cheap, premium engine
  - not by "having an engine" generically.

Interaction density is monotonically bad in the opener: 0 interaction cards 52.1% strong-state, 1
card 44.6%, 2+ cards 34.3%, interaction-only hands 15.4%. But interaction that IS live and PAID
by T3 correlates with 92.4% strong-state (n=2151, 2.2% of hands) - a real positive signal, just
not one an opener-only decision can target (it's a symptom of an already-strong hand, not a cause).

## Interpretable value model (section 5)

Depth-4 decision tree (16 leaves, CV AUC 0.774, holdout AUC 0.771) splits, in order: premium
one-drop engine present → acceleration card count → Sol Ring present → executable T1 acceleration
→ color coverage → cards remaining after T1. This matches the logistic regression's top
standardized coefficients almost exactly (`accel_card_count` +0.989, `has_premium_one_drop_card`
+0.573, `has_sol_ring` +0.499, `has_tier_a_engine_card` +0.491) - two different methods converge
on the same short list of what matters. A GBM benchmark (never used as the final heuristic) tops
out at CV AUC 0.860; a depth-4 tree already captures 75.9% of its achievable gain over random,
depth-6 reaches 89.2%, depth-8 96.2% (`solo004_hand_value_models.json`'s depth sweep) - the
practical ceiling for a small rule list is well short of the black-box benchmark, and that gap is
exactly what gets traded away for memorability below.

## Multi-objective profiles (section 6) and keep frontiers (section 7)

Five explicit, disclosed profiles (formulas in `define_value_profiles.py`) show real divergence:
premium/Tier-A engine access correlates strongly with DEVELOPMENT_FIRST (r=+0.58) and SPEED_FIRST
(r=+0.55) but barely with AGENCY_FIRST (r=+0.05) or RESILIENCE_FIRST (r=+0.12); interaction
density is the only feature that flips sign entirely (positive under AGENCY_FIRST, negative
everywhere else). No profile is declared correct - the rest of this section uses BALANCED as the
default, consistently.

**The single most load-bearing finding of this audit**: under every profile tested, keeping an
average, UNMODIFIED random 7 is worse than mulliganing and optimally bottoming to 6
(BALANCED: 0.232 vs. 0.258; AGENCY_FIRST: 0.120 vs. 0.161). This is not a methodology artifact -
under real London mulligan rules, keeping at 7 means no bottoming at all, so "the average random
7, kept as-is" really is the correct alternative to "mulligan, then optimally trim one weak card
from a fresh 7." **This deck should not default to keeping a merely-average seven.** A specific
hand should still be kept whenever its own value clears the relevant threshold - see the keep-7
decision table below for what that looks like structurally.

## Bottoming (sections 8-9)

Real London mulligan mechanics: bottomed cards go to the bottom of the library (not reshuffled),
the rest of the library keeps its draw order. A fast fixed-priority bottoming heuristic (the one
previously used for Gemstone Caverns' exile choice and SOLO-002's mulligan sim) was tested against
exhaustive search and found wanting: only 35.1%/21.4%/15.1% "near-optimal" (within 0.01
profile-score points) at bottom-1/2/3, with the gap widening as more cards need bottoming. Search
is cheap enough (~1,750 hands/sec) to use directly instead, and does throughout this report.

**Data-derived bottoming guidance** (`solo004_bottoming_analysis.json`, by card class of the
optimally-bottomed card):

| Bottoming to... | Most bottomed | 2nd | 3rd | Premium engines bottomed |
|---|---|---|---|---:|
| 6 (1 card) | interaction (22.7%) | land (20.4%) | tutor (18.9%) | 0.8% |
| 5 (2 cards) | tutor (21.2%) | interaction (20.5%) | land (20.4%) | 0.7% |
| 4 (3 cards) | tutor (21.5%) | land (20.5%) | interaction (18.4%) | 0.4% |

Redundant interaction is usually the first bottom at six; by five and four, a spare tutor becomes
the single most commonly-correct bottom, matching the tutor finding above. Premium one-drop
engines are almost never the right bottom at any depth.

## Candidate policies and machine-optimal ceiling (sections 10-11)

Three policies, each traced to a specific finding (`candidate_mulligan_policies.py` documents
exact provenance per rule): `MACHINE_OPTIMAL` (keep iff simulated value clears the keep-at-7
threshold - not memorizable, used as the ceiling), `TREE_DEPTH4` (the learned tree, literally
translated), and `SIMPLE_RULES` (an 8-rule human-memorizable policy, re-derived by hand from the
same underlying findings so the reasoning stays legible at the table - not mechanically
simplified from the tree). A false-keep/false-mulligan audit (below) caught and fixed a real bug
in the first draft of `SIMPLE_RULES`: it originally let a bare tutor justify a keep at 2-3 lands,
directly contradicting the tutor finding above. Fixed before any of the numbers below.

## Full London mulligan simulation results (section 12), 100,000 sequences per policy per seat

| Policy | Play strong-state | Draw strong-state | Play avg. final hand | Draw avg. final hand |
|---|---:|---:|---:|---:|
| Keep-everything (no mulligan, SOLO-003R) | 43.8% | 51.1% | 7.00 | 7.00 |
| **SIMPLE_RULES** (primer-facing) | **58.9%** | **64.9%** | 6.35 | 6.37 |
| TREE_DEPTH4 (aggressive alternative) | 72.6% | 74.4% | 5.30 | 5.06 |
| MACHINE_OPTIMAL (ceiling, 5k sample) | 76.5% | 80.7% | 5.15 | 5.58 |

All three mulligan policies substantially beat keeping everything, at a real, quantified card cost.
`SIMPLE_RULES` is deliberately the conservative end of this range - it keeps 60-61% of hands
outright at 7 (vs. TREE_DEPTH4's 27-31%) and gives up real quality (58.9%/64.9% vs. TREE_DEPTH4's
72.6%/74.4%) for that practicality. A player willing to mulligan more aggressively at the table
should consider `TREE_DEPTH4`'s decision rule instead (available as a callable in
`candidate_mulligan_policies.py`) - this is a genuine risk-tolerance/practicality tradeoff, not a
case where one policy is simply better.

## Mulligan cost curve (section 13) - how expensive is one more mulligan

| Kept at (SIMPLE_RULES, play) | P(reached) | T2 engine | T3 strong state | T3 stalled |
|---|---:|---:|---:|---:|
| 7 | 60.0% | 26.2% | 58.3% | 17.2% |
| 6 | 24.0% | 31.7% | 61.1% | 15.0% |
| 5 | 9.6% | 32.9% | 61.1% | 14.2% |
| 4-or-fewer | 6.4% | 28.4% | 53.6% | 19.9% |

The pattern is consistent across all three policies and both seats: **one or two mulligans reliably
pay for themselves** (strong-state rate holds steady or improves from 7→6→5), but **a third
mulligan is a real, steep cliff** - e.g. MACHINE_OPTIMAL falls from 89.4% (kept at 5) to 55.0%
(kept at 4-or-fewer), and the stalled rate roughly triples for every policy at that depth. Full
tables for all three policies, both seats, in `solo004_mulligan_cost_curve.json`.

## Keep-7 decision table (section 14)

| Opening structure | Frequency | T3 strong-state | Recommendation |
|---|---:|---:|---|
| 4+ lands + premium engine | 0.7% | 97.5% | Snap keep |
| 2 lands + premium engine | 4.5% | 89.8% | Snap keep |
| 2 lands + dork/rock (2+ accel) | 7.5% | 81.6% | Snap keep |
| 1 land + T1 persistent acceleration | 9.6% | 63.4% | Keep |
| 3 lands + acceleration | 11.5% | 59.0% | Keep |
| 3 lands + engine | 12.2% | 50.0% | Conditional / lean keep |
| 2 lands + tutor (no engine) | 7.5% | 43.5% | Conditional / lean ship |
| 1 land + temporary acceleration only | 3.0% | 41.4% | Conditional / lean ship |
| 2 lands + interaction-heavy (2+) | 9.4% | 41.1% | Conditional / lean ship |
| 4+ lands, no premium engine | 8.1% | 32.2% | Usually ship |
| 1 land, no acceleration | 7.8% | 23.3% | Usually ship |
| 3 lands, weak business | 0.8% | 19.4% | Usually ship |
| 2 lands, no T1/T2 development | 2.7% | 16.0% | Usually ship |

Full table with confidence levels in `solo004_mulligan_cost_curve.json`. Notice land count alone
never anchors either end of this ranking - the top and bottom rows are both 2-land hands.

## False-keep / false-mulligan audit (section 15)

Fresh holdout sample (seed 777, distinct from the primary dataset's seed 42), n=8,000. A "false
keep" requires BOTH the actual simulated outcome to be poor AND the richer `TREE_DEPTH4` model to
independently disagree - filtering single-draw luck from genuine heuristic defects. Result:
**false-keep rate 19.5%, false-mulligan rate 0.7%** - `SIMPLE_RULES` is asymmetrically too
permissive, not too strict, which is the expected and acceptable direction of error for a
primer-facing policy (shipping a good hand by mistake is rare; keeping a bad one sometimes happens
in exchange for a memorable rule count). Representative false-keep hands cluster around a
recognizable pattern: an engine or tutor present but stranded/unsupported, frequently alongside
resource-destructive acceleration (Lotus Petal, Elvish Spirit Guide) spent without a real payoff.
Full examples in `solo004_false_keep_mulligan_audit.json`.

## Tutor- and interaction-specific analysis (sections 17-18)

Covered above (land-population section) - repeating the headline because it's the most
counterintuitive, best-supported finding in this audit: **every individual tutor's presence
correlates with a LOWER strong-state rate than no tutor at all**, and interaction density is
monotonically negative in the opener despite live-paid-interaction-at-T3 being one of the single
strongest positive signals once achieved. Full per-tutor table (14 tutors, frequency/T1
castability/stranded rate/strong-state rate each) in `solo004_tutor_interaction_analysis.json`.

## Play vs. draw (section 19)

At every opening-hand land count from 1 through 5+, the top-5 predictive opener features are
IDENTICAL between play and draw (mean overlap 4.7/5; land count 0 is the lone partial exception).
The draw is uniformly stronger by roughly the same margin everywhere (+7.1pp mean success-rate
delta across land counts; +1.8 to +5.9pp across all three mulligan policies) - one extra card,
same underlying logic, not a different set of what matters. **Conclusion: one heuristic, not
two** - the rules below apply identically on the play and the draw.

## Validation (section 21)

Regression suite: 77 passed, 3 skipped throughout this phase (unchanged from SOLO-003R).
Determinism: dataset generation and full mulligan simulation independently verified to produce
byte-identical output across repeated runs with the same seed. Holdout: both interpretable models
report holdout AUC alongside cross-validated AUC (logistic 0.840 holdout vs. 0.841 CV; tree 0.771
holdout vs. 0.774 CV - no meaningful gap, no overfitting to the training population); the
false-keep/false-mulligan audit itself used a fresh seed (777) never touched during derivation.
Manual search audit: representative strong/weak 1-land, strong/deceptive 2-land, strong 3-land,
flooded, tutor-heavy, and interaction-heavy hands were inspected turn-by-turn - all cast sequences
were legal (e.g. one audited hand correctly cracked Wooded Foothills for Tropical Island via
partial basic-type overlap, matching real fetch rules) and strategically coherent under the
existing DEFAULT_PRIORITY policy.

---

## CURRENT MULLIGAN HEURISTIC — SIM-001

*(Derived from the analysis above - see `solo004_final_human_heuristic.json` for the exact
callable, `candidate_mulligan_policies.policy_simple_rules`.)*

### At Seven

**Snap keeps**
- Mystic Remora or Esper Sentinel (the deck's two premium one-drop engines) in hand.
- Sol Ring in hand.
- 2 or more acceleration sources (mana dorks, rocks, Moxen, Lotus Petal, Elvish Spirit Guide) in
  hand, with at least 1 land.

**Conditional keeps**
- At 1 land: keep ONLY if you have a source that produces mana THIS turn without summoning
  sickness (Sol Ring / Mox family / Lotus Petal / Elvish Spirit Guide) - a mana dork alone at 1
  land is not enough on its own (it can't tap until turn 2).
- At 2-3 lands: keep if you have Rhystic Study, Sylvan Library, or either premium one-drop
  already covered above; any OTHER engine specifically at 3 lands is also a keep; any engine
  (even a non-premium one) at 2 lands is a real, if smaller, edge worth keeping.

**Usually ship**
- 0 lands, always (20.9% population success rate - the worst bucket, no exceptions).
- 4+ lands without a premium one-drop engine (30.5% with any other engine, 17.6% with none - an
  engine that isn't cheap does not rescue a flooded hand).
- An interaction-only hand (nothing but lands and interaction spells), at any land count.
- 2-3 lands with NO engine of any kind - even if a tutor is present. A bare tutor does not
  justify a keep on its own.

### At Six (after 1 mulligan)

Bottom the single weakest card. If you have redundant interaction (2+ copies of "protect the
plan" cards with nothing else going on), that's usually the correct first bottom; excess lands
and a spare tutor are close behind. Keep threshold loosens slightly from 7 - a hand that would
have been a marginal ship at 7 is often a correct keep at 6, since the alternative (mulligan to 5)
is worse on average than the marginal hand in front of you.

### At Five (after 2 mulligans)

Bottom two cards. A spare tutor becomes the single most commonly-correct card class to bottom at
this depth - by five cards, a card with under a 50% chance of ever being live is a luxury this
hand can't afford. Keep almost anything with real, immediate mana development.

### At Four

Keep almost anything that isn't actively incoherent (no legal color, or genuinely nothing to do).
Going this deep is a real, steep cost - strong-state rate falls from ~80-90% (kept at 5-6) to
~53-65% (kept at 4-or-fewer) across every policy tested, and the stalled rate roughly triples.
There is little further value in searching for a "better" four; the marginal value of one more
look is essentially gone by this point.

### One-land hands

Require a mana source that's usable THIS turn (not a summoning-sick dork) - 63.4% strong-state
with executable T1 acceleration vs. 23.3% without. "One land" alone is never the signal; "one
land plus real, immediate acceleration" is.

### Two-land hands

The largest single population (33.0%) and the most heterogeneous - both the single best (premium
engine, 89.8%) and one of the single worst (no development, 16.0%) structures in the entire
decision table are two-land hands. Judge on business, not land count: acceleration density and
engine access are what separate them, and a bare tutor does not count as business.

### Three-land hands

A real, near-equivalent alternative to two lands when they carry engine or acceleration business
(50.0%/59.0% respectively) - but "3 lands and nothing else" is a bottom-quartile hand (19.4%),
not a safe default. Land count buys mana capacity, not a keep by itself.

### Common traps

- **"I have a tutor, this must be a keep."** False - a tutor's mere presence correlates with
  WORSE outcomes than no tutor at all (35-39% vs. 51.6% strong-state); it gets stranded 67-95% of
  the time in this deck's first three turns.
- **"This hand has business, it just needs mana."** Watch for resource-destructive acceleration
  (Lotus Petal, Elvish Spirit Guide) spent with nothing real to show for it - a recurring pattern
  in the false-keep audit.
- **"Four lands is safe."** Flood without a specifically premium, cheap engine is a bottom-third
  outcome, not an average one.
- **"Interaction protects my plan."** A hand with 2+ interaction spells and nothing else drops to
  34.3% strong-state; interaction-only hands crater to 15.4%. Interaction is a real cost in the
  opener, even though live paid interaction at T3 is one of the strongest positive signals once
  actually achieved.

---

## PRIMER-FACING MULLIGAN PACKET

### Mulligan philosophy

This deck should not default to keeping a merely-average seven - across every objective profile
tested, the average random 7 kept as-is is worse than mulliganing and optimally trimming a fresh
6. Keep decisions should be judged on acceleration density and real engine access, not land count
or the presence of a tutor. One or two mulligans reliably pay for themselves; a third is a steep,
well-quantified cost, so use them, but don't chase a perfect four.

### Keep rules

See "CURRENT MULLIGAN HEURISTIC" above - snap keep on a premium one-drop engine, Sol Ring, or 2+
acceleration sources; ship 0-land hands, unsupported flood, interaction-only hands, and any
2-3-land hand with no engine (tutor alone does not count).

### Example keeps (from live simulation, `SIMPLE_RULES` policy, all reached a strong T3 state)

1. `Command Tower, Tropical Island` + Mystic Remora, Chord of Calling, Eldritch Evolution, King
   T'Challa, Pact of Negation - 2 lands, Tier-A engine present.
2. `City of Brass, Gemstone Caverns, Starting Town` + Mystic Remora, Mox Amber, Heartwood
   Storyteller, Spellseeker - 3 lands, premium engine.
3. `Boseiju, City of Traitors, Windswept Heath` + Birds of Paradise, Esper Sentinel, King
   T'Challa, Veil of Summer - 3 lands, T1 accel into T2 premium engine.
4. `Marsh Flats` + Abhorrent Oculus, Crop Rotation, Kinnan, Lotus Petal, Mental Misstep, Nature's
   Rhythm - 1 land, but Lotus Petal is usable this turn.

### Example mulligans (from live simulation, `SIMPLE_RULES` policy, all correctly shipped)

1. `Talon Gates of Madara` + Avacyn's Pilgrim, Derevi, Force of Will, Orcish Bowmasters, Subtlety,
   Survival of the Fittest - 1 land, only a summoning-sick dork for acceleration.
2. `Mana Confluence, Gaea's Cradle` + Endurance, Flusterstorm, Imperial Seal, Orcish Bowmasters,
   Veil of Summer - 2 lands, no engine, a tutor that won't be live in time.
3. `Starting Town, Tundra, Windswept Heath` + Badgermole Cub, Eldritch Evolution, Enduring
   Vitality, Mental Misstep - 3 lands, no real business.
4. `4 lands` (Boseiju, Tundra, Underground Sea, and two fetches) + Crop Rotation, Pact of
   Negation, Veil of Summer - flooded, no premium engine, color-screwed.

Full examples with outcome tags in `solo004_primer_example_hands.json`.

### Bottoming rules

At six: bottom redundant interaction first, then excess lands, then a spare tutor. At five: a
spare tutor is now the single most commonly-correct bottom - a card with under even odds of ever
being live is a luxury a five-card hand can't carry. Premium one-drop engines are almost never
the right card to bottom at any depth (under 1% of the time).

### Statistical evidence

- Keeping an average random 7 is worse than mulliganing to an optimally-bottomed 6, under every
  objective profile tested.
- `SIMPLE_RULES` reaches 58.9%/64.9% (play/draw) T3 strong-state vs. 43.8%/51.1% for keeping
  everything - a real, large improvement for a memorizable rule set.
- A more aggressive policy (`TREE_DEPTH4`) reaches 72.6%/74.4% but averages a full 1.3-1.7 fewer
  cards - a genuine tradeoff, not a strictly better option.
- One or two mulligans pay for themselves; a third drops strong-state rate by roughly 30
  percentage points and roughly triples the stalled rate, across every policy tested.

---

## Machine-readable outputs (section 24)

| Artifact | Contents |
|---|---|
| `solo004_opening_hand_dataset_{play,draw}.jsonl.gz` | 100k-hand opener-feature + outcome dataset per seat |
| `solo004_opening_hand_dataset_{play,draw}_achievable.jsonl.gz` | 15k-hand achievable-search-enabled variant per seat |
| `solo004_land_population_analysis.json` | Effect sizes by land count (sections 3-4) |
| `solo004_conditional_hand_outcomes.json` | Full conditional outcome vectors by structural class |
| `solo004_hand_value_models.json` | Logistic/tree/GBM models, depth sweep, holdout checks |
| `solo004_objective_profile_comparison.json` | Five value profiles + feature-disagreement analysis |
| `solo004_keep_thresholds_by_hand_size.json` | Machine-optimal keep frontiers per profile/hand size |
| `solo004_bottoming_analysis.json` | Search-vs-heuristic bottoming comparison + card-class distribution |
| `candidate_mulligan_policies.py` | The three candidate policies as callables |
| `solo004_london_mulligan_results_{play,draw}.json` | 100k full mulligan sequences per policy per seat |
| `solo004_mulligan_cost_curve.json` | Cost curve + keep-7 decision table |
| `solo004_false_keep_mulligan_audit.json` | False-keep/false-mulligan audit + examples |
| `solo004_tutor_interaction_analysis.json` | Per-tutor and interaction-density breakdowns |
| `solo004_play_draw_comparison.json` | Play vs. draw feature-ranking and outcome comparison |
| `solo004_primer_example_hands.json` | Concrete example keeps/mulligans for the primer |

All files carry `run_class: DECK_BACKED_GOLDFISH` provenance (`subject_deck_hash`,
`subject_deck_card_count`, `commander_identities`) per `docs/RUN_CLASSIFICATION.md`, and every
random sample is seeded and disclosed (primary seed 42, holdout audit seed 777).

## Critical questions answered (section 25)

1. **What separates the good ~half of two-land hands from the bad half?** Acceleration density
   and engine access, not land count - premium engine/Sol Ring/2+ accel/Tier-A engine are the top
   four positive drivers; interaction-only is the single largest negative.
2. **When is a one-land hand worth keeping?** Only with a mana source usable THIS turn (not a
   summoning-sick dork) - 63.4% vs. 23.3%.
3. **Is persistent T1 acceleration required for most good one-land keeps?** Effectively yes -
   persistent/immediate sources drive the keep; a creature dork alone does not (it can't tap T1).
4. **When is temporary fast mana sufficient?** Only about as often as persistent acceleration for
   the T1-executable check itself (both count as "executable now"); temporary-only hands trail
   persistent-accel hands on downstream metrics (41.4% vs. 61.2% at the population level).
5. **When does a three-land hand become too passive?** When it has no engine, no acceleration,
   and no tutor at all - 19.4% strong-state, the single worst 3-land structure measured.
6. **Are four-land hands ever systematically good?** Yes, specifically with a premium one-drop
   engine (97.5%) - never systematically good otherwise.
7. **How valuable is T1 engine access relative to T1 acceleration?** Comparable in magnitude
   (both among the top logistic-regression coefficients and top land-population lifts); premium
   engine access is marginally the single strongest individual signal at every land count tested.
8. **How much should a live tutor improve a keep decision?** It shouldn't, on its own - the
   opposite is true (see finding above). Only an already-live, combo/engine-reaching tutor (a T3
   fact, not an opener fact) is a real positive.
9. **How much should free interaction improve it?** Marginally at best in the opener; interaction
   density is net negative until it's actually live and paid at T3 (92.4% strong-state then, but
   that's a downstream fact, not a targetable opener feature).
10. **How bad are interaction-heavy hands without development?** Very - interaction-only hands
    reach strong-state only 15.4% of the time, the worst structural class measured.
11. **When should a mediocre seven be shipped for six?** Whenever the seven doesn't clear the
    keep-7 threshold - concretely, per the decision table, most 2-3-land hands with no engine and
    no 2+ acceleration.
12. **When should a mediocre six be shipped for five?** The keep bar loosens (the alternative -
    a fresh, optimally-bottomed five - is itself weaker than a fresh six), but a hand with no
    business at all should still ship.
13. **How much trajectory quality is actually lost at each mulligan?** Little to none for the
    first two mulligans (strong-state rate holds or improves 7→6→5 under every policy); a third
    mulligan costs roughly 30 points of strong-state rate and triples the stalled rate.
14. **What should usually be bottomed at six?** Redundant interaction, then excess lands, then a
    spare tutor.
15. **What should usually be bottomed at five?** A spare tutor becomes the single most
    commonly-correct bottom class.
16. **Does play/draw materially change the heuristic?** No - top-5 predictive features are
    identical at every land count from 1 through 5+; only the baseline success rate shifts
    uniformly upward on the draw.
17. **How close can a simple human heuristic get to the machine-derived frontier?** A depth-4 tree
    captures 75.9% of a GBM benchmark's achievable predictive gain; the primer-facing
    `SIMPLE_RULES` policy reaches 58.9%/64.9% strong-state against a 76.5%/80.7% machine-optimal
    ceiling - real value is left on the table for memorability, quantified and disclosed rather
    than hidden.
18. **Which hands fool the simple heuristic most often?** False keeps (19.5%, far more common
    than false mulligans at 0.7%) - typically an engine or tutor present but stranded, often
    alongside resource-destructive acceleration spent without a real payoff.
19. **Which individual cards most frequently change a mulligan decision?** Sol Ring and the two
    premium one-drop engines (Mystic Remora, Esper Sentinel) are the strongest single-card keep
    signals; every individual tutor is a (mild) ship signal on its own.
20. **What is the final primer-ready mulligan guide?** See "CURRENT MULLIGAN HEURISTIC" and
    "PRIMER-FACING MULLIGAN PACKET" above.

## Explicit scope disclosure

This completes SOLO-004's core mulligan-heuristic derivation (sections 1-19, 21-25) and the
required primary deliverable. Consistent with the assignment's own STOP CONDITION: **deckbuilding
ablations (land/mana-density changes to the 98) are not run here** - deck construction should be
evaluated under this competent mulligan policy, not the keep-everything population, and that is
now unblocked as the natural next phase. Also explicitly out of scope per the assignment's own
section 20: seat-specific/pod-position mulligan policies (turbo-pod, stax-pod, etc.) - those
require validated opponent/pod simulations this project doesn't yet have; the opener-feature
infrastructure built here is designed to later condition on pod/seat information once that
exists, but does not do so now.

---

# SIM-001 MULL-005 — Trajectory-First Mulligan Model + Pod-Conditioned Keep Guidance

The governing constraint for this phase, stated verbatim in the assignment: **"Pod context
modifies a structurally coherent hand. It does not rescue a hand with no credible engine
trajectory."** And the central discipline: **keep trajectories, not resources** - mana, a tutor,
interaction, and acceleration are none of them a reason to keep a hand on their own; they matter
only insofar as they produce or protect a real T1-T3 engine line. This phase does not replace
SOLO-004's infrastructure (London mulligan mechanics, search-based bottoming, dataset-generation
machinery are all reused, not rebuilt) - it replaces SOLO-004's *opener-evaluation logic*, which
graded a hand by which resource-presence features it happened to have, with trajectory-first
evaluation, which grades a hand by which actual T1-T3 line the engine can simulate for it.

## Method summary

1. **Real tutor resolution** (`opening_hand_policy.py`'s `forced_tutor_target` parameter): every
   tutor in this deck previously cast and fizzled - no target was ever fetched, in SOLO-002 through
   SOLO-004 alike. A tutor can now genuinely search the library and add a named card to hand,
   provably a no-op when unforced (regression-tested), so every prior committed result stays
   byte-for-byte reproducible.
2. **Bounded trajectory search** (`trajectory_search.py`): for a hand holding a tutor, tries
   forcing it toward a small disclosed candidate set (the four Tier-A engines, Sol Ring, Gaea's
   Cradle) under two priority-order variants - `DEFAULT_PRIORITY` and `TUTOR_FIRST_PRIORITY` (a
   tutor sitting behind "commander" in cast priority never gets cast at all whenever a commander is
   also affordable, so target-branching alone is pointless without also branching sequencing).
   `greedy_realized` (the single pre-MULL-005 line) and `best_known_achievable` are reported
   separately, per the assignment's explicit constraint never to conflate the two.
3. **Trajectory tier grading** (`trajectory_grading.py`): every simulated line is graded S/A/B/C/D/F
   from what the engine ACTUALLY did (its `cast_log`), not from opener-only proxy features, and
   tagged with a MECHANISM (`natural_engine`, `dork_to_engine`, `rock_to_engine`, `tutor_to_engine`,
   `tutor_plus_accel_to_engine`, `commander_engine`, `engine_to_second_engine`, `cradle_development`,
   `none`) plus a resource-cost breakdown (cards spent, mana consumed, cards/interaction/tutor
   retained).

## The two mandated corrections, both confirmed by simulation

**Correction (A): acceleration only matters with a destination.** SOLO-004's `SIMPLE_RULES` had an
unconditional "2+ acceleration = snap keep." Measured directly (`mull005_accel_without_payoff_
analysis.json`): hands with 2+ acceleration and a real destination (an engine in hand, or the mana
fuels a productive commander line) reach Tier S/A 44-55% of the time with 0-21% Tier D/F. Hands with
2+ acceleration and **truly no destination at all** - no engine, no cheap tutor, and not even
enough color access for Tymna/Thrasios - hit Tier D/F **58.8%** of the time (n=500) and Tier S/A
only **20.8%**, both *worse* than the under-2-acceleration baseline (18.3%/43.2%). The rule was
actively wrong for this subset, not merely imprecise.

**Correction (B): a T1 creature dork enabling a T2 engine is a premium line.** Directly measured
from simulated `cast_log`s (`mull005_tutor_dork_analysis.json`): the `dork_to_engine` mechanism
fires in 2,591/30,000 hands (8.6%) and reaches Tier A in **48.6%** of those - a summoning-sick T1
Birds of Paradise into a T2 Rhystic Study is graded exactly as favorably as a T1 Sol Ring into the
same T2 engine (`rock_to_engine`), because the grading reads the actual T2 board state, not
whether the accelerant itself could tap on turn 1.

## Tutor economics, measured per card (not as one "tutors" class)

SOLO-004 concluded "tutors are negative" as a blanket fact. The correct question, per the
assignment, is whether a *specific* tutor can legally and economically become a T1/T2 engine.
Bucketing every hand holding each tutor by what the bounded search's best line actually did with
it (`mull005_tutor_dork_analysis.json`, n≈2,050-2,280 hands/card):

| Tutor | CMC | Reaches T2 engine | Live but delayed | Stranded | Superseded by commander |
|---|---|---|---|---|---|
| Crop Rotation | 1 | 27.4% | 5.9% | 48.9% | 17.4% |
| Vampiric Tutor | 1 | 27.1% | 4.9% | 46.3% | 21.5% |
| Enlightened Tutor | 1 | 26.6% | 4.9% | 47.8% | 20.6% |
| Imperial Seal | 1 | 24.8% | 4.2% | 45.9% | 24.6% |
| Demonic Tutor | 2 | 11.5% | 6.0% | 44.4% | 38.1% |
| Spellseeker | 3 | 8.8% | 3.3% | 48.9% | 39.0% |
| Ranger-Captain of Eos | 3 | 8.1% | 2.5% | 51.6% | 37.8% |
| Eldritch Evolution | 3 | 7.7% | 2.7% | 52.2% | 37.3% |
| Nature's Rhythm | 3 | 7.5% | 2.7% | 53.5% | 36.2% |
| Birthing Pod | 3 | 7.4% | 3.2% | 54.7% | 34.7% |
| Finale of Devastation | 4+ | 7.4% | 1.8% | 50.8% | 40.0% |
| Sowing Mycospawn | 3 | 7.3% | 2.7% | 53.0% | 36.9% |
| Chord of Calling | X | 6.9% | 2.6% | 52.9% | 37.7% |
| Survival of the Fittest | 2 | 6.8% | 4.2% | 63.7% | 25.3% |

A sharp, CMC-driven split: every CMC1 tutor reaches a T2 engine roughly 25-27% of the time it's
held; every CMC2+ tutor manages only 7-12%. `pod_archetypes.py` and `trajectory_policies.py` both
encode this directly - `CHEAP_TUTORS_WITH_REAL_T2_CONVERSION` (Vampiric Tutor, Enlightened Tutor,
Imperial Seal, Crop Rotation) is the only tutor subset that earns any keep credit on its own; every
other tutor in this deck is not a keep signal by itself, matching SOLO-004's finding but now for
the *right, disaggregated* reason. Search value: the bounded search recovers a strictly better tier
than the pre-MULL-005 greedy line in 20.6% of all hands holding any tutor.

## Hand-size-specific trajectory thresholds (7/6/5/4)

`derive_hand_size_trajectory_thresholds.py` searches optimal London-mulligan bottoming of a fresh 7
down to each size and grades the result by trajectory tier (`mull005_hand_size_thresholds.json`).
**Important limitation, disclosed rather than smoothed over**: a T1-T3 trajectory grade has no
built-in penalty for holding fewer cards - bottoming a card that was never going to be cast is
tier-neutral, so raw expected tier value rises slightly as hand size shrinks (7→6→5→4:
1.72/2.12/2.25/2.40). This project has no full-game/4-player data to derive a real cost-of-mulligan
from, so thresholds are reported at several disclosed assumed per-card costs rather than one
invented "true" figure. At a moderate assumed cost of 1.0 tier-value-point per card:

| Hand size | Keep at or above | Mulligan-alternative EV (cost-adjusted) |
|---|---|---|
| 7 | Tier B | 1.12 |
| 6 | Tier C | 0.25 |
| 5 | Tier D (i.e. ship only Tier F) | -0.60 |
| 4 | no derived threshold (out of 7/6/5/4 scope) | - |

## TRAJECTORY_MACHINE / TRAJECTORY_TREE / TRAJECTORY_SIMPLE

Three policies (`trajectory_policies.py`), mirroring SOLO-004's machine/tree/simple pattern but
graded on trajectory tier:

- **TRAJECTORY_MACHINE** - the ceiling. Runs the bounded search and keeps iff the best tier clears
  the hand-size threshold above. Not memorizable at the table.
- **TRAJECTORY_TREE** - depth-4 decision tree fit on opener-visible features only, predicting
  TRAJECTORY_MACHINE's label (`mull005_trajectory_tree_policy.json`). Holdout AUC **0.832**,
  accuracy **0.739**. Dominant split: `distinct_colors_potential <= 1.5` - color access for a
  commander line is the single strongest opener-visible predictor of trajectory quality in this
  deck, ahead of any resource-presence feature SOLO-004 measured.
- **TRAJECTORY_SIMPLE** - a ≤10-rule human-usable ladder directly encoding both corrections above
  (full rule ladder and citations in `trajectory_policies.py`'s docstring). Validated against
  TRAJECTORY_MACHINE on 15,000 hands: 62.5% agreement, 91.8% recall (rarely mis-ships a hand the
  machine would keep), 56.2% precision (over-keeps some hands, mainly via its commander-colors
  fallback rule, whose true keep rate is ~56-59% on its own - a single opener-visible feature
  cannot fully predict commander productivity, and this is disclosed rather than hidden).

## Full London mulligan simulation: trajectory-first vs. resource-first, head-to-head

`run_mull005_london_mulligan_sim.py` runs real London mulligan sequences (20,000/policy, 1,500 for
the expensive MACHINE policy, both seats), bottoming scored uniformly by trajectory tier so only
the KEEP decision differs between policies compared - and re-runs SOLO-004's own `SIMPLE_RULES`/
`TREE_DEPTH4` through the identical loop, so this is a genuine head-to-head under one shared metric,
not two studies compared by eye. Because raw mean tier value structurally favors more-aggressive
mulliganing (see the hand-size-threshold limitation above), results are reported both raw and at
an assumed mulligan cost of 1.0 tier-value-point/card:

| Policy | Play (cost-adj.) | Draw (cost-adj.) | Play avg. final hand size |
|---|---|---|---|
| TRAJECTORY_MACHINE | **2.53** | **3.06** | 5.97 |
| TRAJECTORY_SIMPLE | 2.09 | 2.55 | 6.70 |
| TRAJECTORY_TREE | 1.97 | 2.35 | 6.19 |
| SOLO004_SIMPLE_RULES | 1.88 | 2.32 | 6.35 |
| SOLO004_TREE_DEPTH4 | 1.65 | 1.68 | 5.30 |

`SOLO004_TREE_DEPTH4` has the *highest raw* mean tier value of any cheap policy (3.35 play / 3.64
draw) but drops to *last place* once its aggressive over-mulliganing (avg. final hand size 5.30,
worst of any policy) is fairly priced in - it was winning by spending more cards, not by making
better decisions. Once that's corrected for, **`TRAJECTORY_SIMPLE` beats every SOLO-004 baseline,
including the more complex `TREE_DEPTH4`, on both seats**, while remaining the smallest, most
human-usable ruleset tested.

## Pod-conditioning overlay - explicitly non-simulated

`pod_archetypes.py` defines multi-dimensional tags (speed, primary resource axis, interaction
demand, resilience profile) and qualitative increase/decrease-value priors for ten named pod
archetypes: RogSi, Kinnan, Rog/Thras Tree Farm, Blue Farm, Sisay, Tayam, Tivit, Etali, stax-heavy
pods, and generic midrange/grind pods. **None of this is simulation output** - this project has run
no 4-player matchup data (out of scope this phase). `pod_conditioned_grade()` combines a REAL
`structural_hand_grade()` with bounded (+2/+1/0/-1/-2) per-archetype modifiers over nine disclosed
feature categories, and every result carries two separate, always-distinct confidence labels:
`structural_confidence: SIMULATED` and `pod_confidence: STRATEGIC_PRIOR_UNVALIDATED`. **A
structural SHIP can never be promoted into any keep band, regardless of total modifier** - enforced
in code (8 regression tests), not left as a documentation convention. Per the assignment's explicit
constraint, no pod-conditioned recommendation anywhere in this project claims a simulated
percentage (e.g. "wins 63% against RogSi") - only structural language ("against RogSi, live stack
interaction receives a positive keep modifier because...").

### Pod-guidance table (opponent archetype → mulligan pressure, no simulated numbers)

| Archetype | Speed | Mulligan pressure | Gains value | Loses value |
|---|---|---|---|---|
| RogSi | very fast | HIGH - mulligan toward speed/interaction | free/cheap interaction, T1-T2 development, redundant fast starts | pure card-advantage engines with no early defense, delayed tutors, durdly ramp |
| Sisay | fast-medium | MEDIUM-HIGH - be live early | stack interaction (ideally free), proactive speed | slow grindy plans that let Sisay out-tutor you |
| Kinnan | fast-medium | MEDIUM-HIGH | interaction that hits noncreature permanents, mana resilience, fast starts | zero-interaction hands |
| Rog/Thras Tree Farm | medium | BASELINE | engines that come online FASTER than theirs, synergy-piece-specific interaction, redundancy | racing on raw damage with no engine backing |
| Tayam | medium | BASELINE | graveyard interaction specifically, resilience/redundancy | purely proactive hands with no way to interact with recursion |
| Tivit | medium | BASELINE | interaction (esp. around extra-turn/blink triggers), card-advantage engines | hyper-aggressive plans with no staying power |
| midrange/grind | medium | BASELINE | card-advantage engines, redundancy | (closest archetype to this project's own solo baseline) |
| Etali | medium-slow | LOW-MEDIUM - punish their slow start | proactive fast starts, held interaction for their top end | purely reactive/passive hands |
| Blue Farm | slow | LOW - patience rewarded | your own card-advantage engines, mana resilience/patience | one-shot interaction with no follow-up, raw speed with no staying power |
| stax-heavy | slow by design | LOW BUT SHARP - must survive to execute | mana resilience, proactive plays BEFORE a lock resolves, tutors for your own answers | greedy multi-piece combo lines, fragile one-shot mana |

### Primer quick-reference table (excerpt - full 72-row table in `mull005_primer_tables.json`)

Trajectory tier × hand size × pod speed → KEEP/SHIP. Hand-size axis is SIMULATED; pod-speed axis is
a disclosed qualitative adjustment (FAST pods only credit on-time tiers S/A regardless of hand
size; SLOW pods relax the neutral bar by one tier step, but never as far as Tier F). At hand size 7:

| Trajectory tier | vs. FAST pod | vs. MEDIUM pod | vs. SLOW pod |
|---|---|---|---|
| S | KEEP | KEEP | KEEP |
| A | KEEP | KEEP | KEEP |
| B | SHIP | KEEP | KEEP |
| C | SHIP | SHIP | KEEP |
| D | SHIP | SHIP | SHIP |
| F | SHIP | SHIP | SHIP |

## Example sets (`mull005_annotated_examples.json`)

**10 snap keeps, 10 conditional keeps, 10 mulligans** - fully annotated with hand, land count,
structural grade + reason, and the bounded search's best-known tier/mechanism/engine/turn.

**5 misleading hands** - real disagreements between SOLO-004's old `SIMPLE_RULES` and the new
`TRAJECTORY_SIMPLE`, each confirmed correct by the bounded trajectory search (not invented
illustrations). All five are cases the OLD rule shipped and the NEW rule correctly keeps:

1. `City of Brass, Deathrite Shaman, Elves of Deep Shadow, King T'Challa, Ranger-Captain of Eos,
   Training Grounds, Volatile Stormdrake` - 1 land. Old rule ships (creature-only acceleration at 1
   land was never a keep signal). New rule keeps (correction B): best line reaches Tier A via a T2
   Tymna, the mana fueled by the two creature dorks.
2-5. Four more 1-3-land hands built around a T1 creature dork or a CMC1 tutor reaching an engine or
   a plausible commander line - `dork_to_engine`/`commander_engine` mechanisms, Tier A/B, all
   correctly reclassified from ship to keep. Full detail in the JSON file.

**17 pod-conditioned examples** across 10 distinct archetype/combo queries (including
`["Kinnan", "RogSi", "Tayam"]`, `["RogSi", "Sisay"]`, `["Blue Farm", "stax_heavy"]`), each showing
the structural grade, the pod modifier breakdown per archetype, and the pod-adjusted grade - with
the SHIP floor visibly holding on every SHIP-structural example regardless of the pod combination.

## A limitation found during validation, not corrected this phase (disclosed, not hidden)

Building the example set surfaced a real gap: `structural_hand_grade`'s "premium one-drop in hand"
rule (inherited unchanged from SOLO-004's `SIMPLE_RULES`) does not check color castability. Of the
2,138 dataset hands holding Mystic Remora or Esper Sentinel, **19.3% (412 hands) still reach best
Tier D or F** - almost entirely because the premium card has no reliable color source, not because
of anything the acceleration/tutor/commander corrections above touch. Both the old and new SIMPLE
rulesets share this blind spot; fixing it (a color-castability check on the snap-keep rule) is real,
quantified future work, explicitly not one of MULL-005's two mandated corrections and therefore not
addressed in this phase's rule ladder.

## Machine-readable outputs

| Artifact | Contents |
|---|---|
| `sim/analysis/trajectory_grading.py` | Tier S/A/B/C/D/F grading + mechanism tagging + resource cost |
| `sim/analysis/trajectory_search.py` | Bounded tutor-target × priority-order best-known trajectory search |
| `sim/analysis/trajectory_policies.py` | TRAJECTORY_MACHINE/SIMPLE + `structural_hand_grade()` |
| `sim/analysis/pod_archetypes.py` | Archetype tags + bounded pod modifiers + `pod_conditioned_grade()` |
| `mull005_trajectory_dataset_{play,draw}.jsonl.gz` | 15k-hand opener-feature + greedy-outcome + trajectory-graded dataset per seat |
| `mull005_tutor_dork_analysis.json` | Per-tutor-card conversion rates + dork-to-engine analysis |
| `mull005_accel_without_payoff_analysis.json` | Acceleration-without-destination analysis (correction A) |
| `mull005_hand_size_thresholds.json` | Trajectory-tier keep thresholds per hand size, cost-sensitivity swept |
| `mull005_trajectory_tree_policy.json` | Fitted depth-4 tree, holdout-checked |
| `mull005_london_mulligan_results_{play,draw}.json` | Full mulligan sim, 5 policies, cost-adjusted comparison |
| `mull005_annotated_examples.json` | Required example sets (snap keeps/conditional keeps/mulligans/misleading/pod-conditioned) |
| `mull005_primer_tables.json` | Primer quick-reference table + pod-guidance table |

All files carry `run_class: DECK_BACKED_GOLDFISH` provenance, and every random sample is seeded and
disclosed (primary seed 42; example generation seed 7). 38 new regression tests across 7 new test
files (`test_mull005_trajectory_engine.py`, `test_mull005_trajectory_grading.py`,
`test_mull005_trajectory_search.py`, `test_mull005_trajectory_policies.py`,
`test_mull005_pod_archetypes.py`, `test_mull005_examples.py`, `test_mull005_primer_tables.py`) -
full suite at 115 passed / 3 skipped.

## Key questions answered

1. **Does a tutor deserve any keep credit at all?** Yes, but only per-card, not as a class: CMC1
   tutors (Vampiric Tutor, Enlightened Tutor, Imperial Seal, Crop Rotation) reach a T2 engine
   ~25-27% of the time held; every CMC2+ tutor manages only 7-12% and is not a keep signal alone.
2. **Was SOLO-004's "tutors are negative" conclusion correct?** Directionally, for most tutors -
   but it collapsed a real, measured 4x spread (27% vs 7%) into one blanket verdict.
3. **Is a T1 creature dork into a T2 engine actually good, or just "acceleration with no
   payoff"?** Genuinely good - `dork_to_engine` reaches Tier A 48.6% of the time it fires, graded
   identically to a T1 rock into the same T2 engine.
4. **Was "2+ acceleration = snap keep" ever correct?** Only with a destination. With none at all,
   it's actively wrong - 58.8% Tier D/F, worse than the under-2-acceleration baseline.
5. **What single opener-visible feature best predicts trajectory quality?** Commander color access
   (`distinct_colors_potential`) - the depth-4 tree's root split, ahead of any resource-presence
   feature SOLO-004 measured.
6. **How much value does the bounded trajectory search recover over the pre-MULL-005 greedy
   line?** A strictly better tier in 20.6% of hands holding any tutor.
7. **Does a simple, human-usable rule set actually beat SOLO-004's more complex tree?** Yes, once
   mulligan cost is fairly priced in - `TRAJECTORY_SIMPLE` beats `SOLO004_TREE_DEPTH4` on both
   seats despite being far smaller, because the tree's apparent edge was mostly bought with extra
   mulligans.
8. **What is the true cost of one more mulligan under trajectory-first grading?** Unmeasurable as
   one number from this simulator alone (T1-T3 trajectory has no built-in per-card cost) - reported
   as a disclosed sensitivity sweep (0.0-2.0 tier-value-points/card) rather than one invented figure.
9. **What should be kept at each hand size, at a moderate assumed mulligan cost?** 7: Tier B+.
   6: Tier C+. 5: Tier D+ (ship only Tier F). 4: no data derived within this phase's scope.
10. **How good is a small (<10-rule) human policy compared to the simulated ceiling?**
    62.5% agreement with TRAJECTORY_MACHINE, 91.8% recall, 56.2% precision - it rarely mis-ships a
    good hand, but over-keeps some hands on its commander-colors fallback rule (~56-59% true keep
    rate on its own).
11. **Can pod context ever turn a genuinely bad hand into a keep?** No - enforced structurally
    (SHIP is a hard floor in `pod_conditioned_grade()`), not just claimed in prose.
12. **Is the pod-conditioning overlay simulated data?** No, and it says so on every single result
    (`pod_confidence: STRATEGIC_PRIOR_UNVALIDATED`) - it is disclosed strategic judgment, explicitly
    built to be edited, not measured fact.
13. **Which pods reward speed over resilience, and which reward the opposite?** RogSi and Sisay
    reward speed/interaction over card advantage; Blue Farm and stax-heavy pods reward patience,
    card advantage, and mana resilience over raw speed.
14. **Does this deck's own archetype (Tymna/Thrasios treefarm) have a named pod entry?** Yes -
    "Rog/Thras Tree Farm" - a mirror-match entry rewarding engine tempo and synergy-piece-specific
    interaction over racing on damage.
15. **Are all ten named archetypes measured with equal confidence?** No - all ten carry the
    identical `STRATEGIC_PRIOR_UNVALIDATED` label; none has been checked against pod simulation, and
    the write-up does not imply otherwise for any of them.
16. **What new, real engine capability did this phase add?** Genuine tutor library-search
    resolution (`forced_tutor_target`) - provably a no-op by default, so every SOLO-002 through
    SOLO-004 result stays reproducible.
17. **Did building the example set surface any new problems?** Yes - a real 19.3% false-keep rate
    on the "premium one-drop in hand" snap-keep rule, caused by unmodeled color castability,
    inherited unchanged from SOLO-004 and disclosed as future work rather than fixed here.
18. **Does play vs. draw change the trajectory-first ranking of policies?** No - the same ranking
    (MACHINE > SIMPLE > TREE > SOLO004_SIMPLE_RULES > SOLO004_TREE_DEPTH4, cost-adjusted) holds on
    both seats.
19. **Is a full 4-player matchup simulation part of this phase's deliverable?** No, explicitly out
    of scope per the assignment's stop condition - see below.
20. **What is the final trajectory-first primer guide?** See "TRAJECTORY_MACHINE / TRAJECTORY_TREE
    / TRAJECTORY_SIMPLE", the pod-guidance and primer quick-reference tables, and the example sets
    above.

## Explicit scope disclosure

This completes MULL-005 per its own stop condition: **a validated trajectory-first structural
mulligan policy plus a transparent qualitative pod-conditioning overlay.** Explicitly NOT run this
phase, per the assignment: full 4-player matchup simulation against any of the ten named
archetypes - the pod overlay is deliberately, permanently labeled as an unvalidated strategic prior
until that simulation exists. Deckbuilding ablations (SOLO-004's own stop condition, still
standing) remain out of scope. The "premium one-drop castability" gap found during example
generation (above) is real, quantified, and deliberately left for a future phase rather than folded
in here as scope creep beyond the assignment's two named corrections.

# SIM-001 MULL-005R — Trajectory Architecture Repair + Early-Game Destination Search

## 1. Executive Summary

MULL-005's own validation surfaced real gaps: the model was still too centered on conventional
card-draw engines, treated Abhorrent Oculus and Birthing Pod as afterthoughts rather than
first-class destinations, mismodeled Smothering Tithe and Mana Vault, used an arbitrarily small
fixed tutor-target list, and — most consequentially — credited generic commander access as if it
were a real mulligan destination. This phase re-audited all 98 cards' real Oracle text for T1-T3
relevance (26 findings, `t1_t3_trajectory_audit.json`), rebuilt the scoring/search engine against
that audit, proved every new mechanic with regression tests before any large-scale rerun (a
29-item BLOCKING gate, `mull005r_regression_gate.json`, `OPEN_FOR_PRODUCTION_RERUN`), then reran
the full production pipeline: a fresh 15,000-hand trajectory dataset per seat, destination and
named-trajectory censuses, a top-25 opener report, re-derived hand-size thresholds, rebuilt
TRAJECTORY_SIMPLE_R/TREE_R/MACHINE_R policies with a fresh London mulligan simulation, a holdout
false-keep/false-mulligan audit, a true paired comparison against MULL-005 on identical dealt
hands, an audited pod-conditioning overlay, and a regenerated primer example set.

**The single largest, most consequential finding of this entire phase**: MULL-005's generic
commander-access credit was extremely common. In a threshold-invariant paired comparison (tier
composition alone, holding the keep/mulligan bar fixed at S/A/B for both models), **2,024 of
15,000 hands (13.5%) drop out of a keep-worthy tier specifically because commander-access credit
was removed** — by far the dominant single effect of this whole correction phase, larger than
every genuine new-destination-understanding gain (Oculus, Pod, Survival, Tithe, dork chains, and
Thrasios's own narrowed concrete-benefit credit) combined. MULL-005R is a more conservative,
narrower, and — per every regression test and audit built to check it — more correct model of
what this deck's openers actually accomplish.

## 2. Subject, Provenance, and Regression Gate

Subject: `tymna-thrasios-treefarm-v1`, hash
`4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a` — verified unchanged from every
prior phase (section 0's provenance check, no discrepancy). Oracle text for every finding below is
pulled from `data/cards_cache/oracle-2026-08-12` for this exact deck, not recalled from general MTG
knowledge.

Per the assignment's own explicit ordering constraint ("do NOT begin the large-scale rerun until
the trajectory audit and resulting model changes have been documented and regression-tested"), the
audit (`t1_t3_trajectory_audit.json`) was committed first, engine corrections and their regression
tests second, and only then was every large-scale artifact generated. The final regression gate
(`mull005r_regression_gate.json`) explicitly enumerates 29 items — 10 PRESERVED SOLO-002R mana-
correctness properties the assignment says must not regress, 19 NEW MULL-005R corrections — each
naming the exact test(s) that prove it, all run by the gate script itself (not merely asserted):
**29/29 pass, full suite 187 passed / 3 skipped, `gate_status: OPEN_FOR_PRODUCTION_RERUN`.** Two
real engine bugs were found and fixed only by actually running the corrected engine at scale
(a Survival-of-the-Fittest/Elvish-Spirit-Guide double-use crash, and a discarded-fodder tier-credit
bug where a creature sacrificed to Survival could be misread as "cast" if its name also happened to
be a premium destination) — both are now GATE-26/GATE-27, and a third systemic gap (the legacy
`ENGINES` classification dict still crediting Tymna/Thrasios as generic engines one layer below the
tier-grading fix) is GATE-28, found while auditing the pod-conditioning overlay.

## 3. Governing Principle and Method Summary

**KEEP TRAJECTORIES, NOT RESOURCES**, expanded this phase: what powerful game state can this opener
legally establish, how early, what resources does that require, when does the resulting engine
begin producing value, and what agency remains afterward? Trajectory tier (S/A/B/C/D/F) is graded
per-hand from an actually-simulated T1-T3 line — either the single greedy `DEFAULT_PRIORITY` line,
or the best of a **bounded** search over 5 candidate families (hand/library-top tutor targets, Pod
activations, Survival activations, battlefield-creature tutors, battlefield-land tutors) — never a
resource-presence count. Every correction below is grounded in real Oracle text and proven by a
regression test before being trusted at scale, per this project's standing discipline.

## 4. T1-T3 Trajectory Audit (26 findings)

`t1_t3_trajectory_audit.json`: **19 VERIFIED, 1 REJECTED, 6 CANDIDATE** (deferred, disclosed —
mechanically real but low-T1-T3-frequency or genuinely engine-risky to implement correctly this
phase: Delighted Halfling's legendary-restricted color mana, Badgermole Cub's full mechanic,
Enduring Vitality's creature-mana-ability grant, Shang-Chi's haste/restricted-mana synergies,
Derevi/Clever-Impersonator doubling Pod activations, Chord of Calling's Convoke reduction). Key
finding families: `OCULUS-001..006`, `POD-001..003`, `SURV-001`, `TITHE-001..002`, `REALIZE-001..
002`, `DORK-001..005`, `CMDR-001..003`, `KINNAN-001`, `AGENCY-001`, `PREMIUM-001`, `COMBO-001`.

## 5. Destination Family Corrections

**Abhorrent Oculus** (`OCULUS-001..006`): real Oracle text is "As an ADDITIONAL cost to cast this
spell, exile six cards from your graveyard" — never a realistic T1-T3 hard-cast in this deck.
Enforced as permanently uncastable from hand (`uncastable_from_hand` classification, regression-
tested), reachable ONLY via 5 verified "put onto the battlefield" search routes that bypass both
mana cost and additional cost: Birthing Pod, Eldritch Evolution, Finale of Devastation, Nature's
Rhythm, Chord of Calling. Graded as a first-class Tier A/B destination once actually on the
battlefield (never merely found or in hand).

**Birthing Pod** (`POD-001..003`): modeled as a real activated ability
(`{1}{G/P}, T, Sacrifice a creature: search for a creature MV = sac's MV + 1, put it onto the
battlefield`), state-aware (requires a genuine sacrificeable creature, not "Pod in play = online").
Disclosed finding from the destination census: **the Pod-activation search family never won as the
best-known trajectory in a 15,000-hand sample (0 occurrences)** — not a bug (the mechanism is fully
regression-tested and provably reachable in targeted tests), but a real rarity finding: Pod's own
board presence already earns generic Tier B/C credit before an explicit activation is attempted,
and Pod's activation cost on top of its own `{3}{G/P}` cast is genuinely mana-heavy for a T1-T3
window.

**Survival of the Fittest**: modeled state-aware (requires a discardable creature card in hand,
never "present = online"), reachable via a real activation search family. Appears as the
`tier_engine` destination in 4.6% of the corrected dataset.

**Smothering Tithe / Mana Vault** (`TITHE-001..002`): Tithe's "whenever an opponent draws a card"
trigger is mechanically identical in opponent-dependence to Rhystic Study's "whenever an opponent
casts a spell" — MULL-005 zeroed Tithe out entirely while crediting Rhystic Study on deployment
alone, an inconsistency, not a principled distinction. Tithe is now promoted into
`ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE` and credited identically. In the corrected dataset Tithe
reaches Tier A 24 times per 15,000 hands where it previously reached Tier A zero times (see
section 14's paired comparison).

**T1 dorks** (`DORK-001..005`): MULL-005's "T1 dork → T2 engine is real" finding preserved, but
each mana creature audited individually against exact Oracle text. Devoted Druid's real ceiling
(2 mana/turn via its no-tap-symbol "-1/-1 counter: untap" ability, once not summoning sick) is now
modeled — a genuine correction, not previously represented at all.

**Kinnan, Bonder Prodigy** (`KINNAN-001`): confirmed never a standalone tier destination — it is
purely a mana-doubling mechanism (already correctly modeled in `available_sources()`) crediting
whatever OTHER destination it accelerates. Removed from `ENGINE_TIER_B_HIGH_LEVERAGE_INFRASTRUCTURE`.

## 6. Tutor Search Generalization

MULL-005's six-hand-tutor-target bottleneck removed. `trajectory_search.py`'s bounded search now
covers 5 mechanism families (hand/library-top tutor, Pod activation, Survival activation,
battlefield-creature tutor, battlefield-land tutor), each with a disclosed candidate set — not
exhaustive over the full ~90-card library, labeled `search_label` per result so every downstream
artifact can distinguish `greedy` from a specific forced search family. Mana Vault is now included
as a tutor target when legally tutorable. Dork-tutoring gets NO generic engine credit by design —
only when it solves a specific bottleneck the search is actually exploring.

## 7. Commander Credit Correction

Per the pilot's explicit directive, Tymna the Weaver receives **zero positive mulligan credit
anywhere** in trajectory grading (`CMDR-001`) — proven by regression test regardless of attack
support. Thrasios, Triton Hero is credited ONLY for a concrete, specific benefit — enabling Mox
Amber, turning Fierce Guardianship free, or genuine immediate `{4}`-activation productivity, always
requiring Thrasios actually ON the battlefield, never merely castable (`CMDR-002`). The generic
`commander_colors_plausible → keep` heuristic that MULL-005 still used as a Tier-A/A fallback in
`structural_hand_grade()`'s acceleration rules was deleted.

A **third, previously-undiscovered layer** of the same bias (`CMDR-003`) was found auditing the
pod-conditioning overlay: an older, broader `ENGINES` classification dict (predating the tier-based
corrections, feeding opener feature extraction and per-turn snapshot metrics) still listed both
commanders as `"commander_engine"`, silently reintroducing commander-access credit one layer below
where CMDR-001/002 were applied — concretely, a commander cast during the T1 feature-extraction
simulation could contaminate `has_any_engine_card`/`any_engine_active`/`engine_count` fields several
other modules read. Fixed by removing both commanders from that dict (Kinnan, a real castable
permanent rather than a commander, deliberately left in).

## 8. Retained Agency, Composite States, and Combo Proximity

Per section 9's requirement, interaction stays secondary to the primary destination — never the
keep reason alone — but a strong trajectory that retains relevant interaction is measurably better
than one that consumes everything. `ENGINE_PLUS_LIVE_FREE_INTERACTION`/
`ENGINE_PLUS_LIVE_PAID_INTERACTION` composite flags added to every graded trajectory's
`resource_cost`, both strictly gated on `has_real_destination` so interaction-only hands (no
engine) never set either flag. Verified combo proximity (`COMBO-001`) is wired in as an analogous
upside modifier (`ENGINE_PLUS_VERIFIED_COMBO_PROXIMITY`, sourced entirely from the existing
verified-combo registry, never a new speculative line) — `grade_trajectory()` never reads either
flag, so neither composite can promote a hand's tier on its own, satisfying "upside modifier only,
never the primary destination."

## 9. Engine Realization Timing

`engine_realization_analysis.json`: 16 ability entries across 15 cards, each with real Oracle text
and four independent fields MULL-005 conflated into one "engine active" flag — realization
mechanism, whether the trigger can fire on an opponent's turn (structural, from Oracle text alone),
whether THIS solo model can ever simulate the value firing, and whether the current grading model
credits it on deployment alone (a disclosed proxy) or requires an explicit support check. Central
finding, generalizing TITHE-001: opponent-dependence alone does not predict credit — every Tier-A
engine is opponent-triggered and unmeasurable, yet proxy-credited on deployment; Tier-C engines with
identical opponent-dependence (Faerie Mastermind's passive, Archivist, Armasaur, Heartwood) get no
such proxy, and four are zeroed out entirely regardless of board state.

## 10. Large-Scale Results

15,000-hand trajectory dataset per seat (`mull005r_trajectory_dataset_{play,draw}.jsonl.gz`).
**Destination census** (`destination_census.json`, 10 mutually-exclusive families): `secondary_engine`
36.6%, `no_premium_destination` 31.9%, `t2_other_premium_resource_engine` 12.3%,
`exceptional_composite_state` 5.5%, `t1_resource_engine` 5.5%, `survival_online` 4.6%,
`early_pod_online` 2.1%, `other_early_oculus` 1.4%, `t2_smothering_tithe` 0.2%,
`pod_to_oculus` 0.0% (0/15,000 — the disclosed Pod-route rarity from section 5). **Named-trajectory
census** (`named_trajectory_census.json`, ~20 multi-label tags): `no_destination_reached` 20.0%,
`acceleration_rich_destination_poor` 7.6%, `tutor_to_t2_premium_engine` 4.8%,
`survival_online` 4.9%, `t1_dork_to_t2_premium_engine` 3.1%, `t1_remora`/`t1_sentinel` ~2.9-3.0%
each, down to the rarest confirmed-real routes (`finale_to_oculus`/`natures_rhythm_to_oculus`
0.75% each). **Top-25 opener trajectories** (`top_25_opener_trajectories.json`): a fresh 3,000-hand
sample deduplicated to one representative per (tier, tier_engine, mechanism) bucket so the 25 span
the real range of destinations this deck reaches, each with `keep_at_{7,6,5}` recommendations from
the re-derived thresholds (section 11).

## 11. Hand-Size Policy Re-Derivation

Re-tested (not hard-coded) against the corrected engine, fresh seed (`mull005r_hand_size_
thresholds.json`). The corrected engine's expected tier value is measurably LOWER than MULL-005's
at every hand size (7-card EV 1.25 vs 1.72 previously; Tier-A rate 11.6% vs 22.5%) — expected, since
this greedy-only measurement (no bounded search, for tractability) no longer gets inflated Tier-A
credit from generic commander access or color-blind premium-one-drops, and doesn't benefit from the
new Pod/Oculus/Survival bounded-search routes (those only fire via the full search). At assumed
mulligan cost 1.0: **keep-at-7 shifted from Tier B to Tier C**, keep-at-6 from Tier C to Tier D,
keep-at-5 stays Tier D — a real, more mulligan-tolerant policy shift, reported plainly rather than
smoothed over.

## 12. Policy Rebuild and London Mulligan Simulation

`trajectory_policies.py`'s `_load_thresholds()` now reads the re-derived thresholds, making
`trajectory_simple_policy`/`structural_hand_grade` and `trajectory_machine_policy`
TRAJECTORY_SIMPLE_R/MACHINE_R by construction. `TRAJECTORY_TREE_R` refit against the corrected
15,000-hand dataset (AUC 0.806, holdout AUC 0.813, n=15,000, 64 features) — a materially different
split structure, leading with `distinct_colors_potential`/`t1_accel_executable_now` rather than raw
land/mana counts. Full London mulligan simulation, both seats, n=20,000 cheap-policy/1,500
machine-policy (mean tier value, cost-1.0-adjusted):

| Policy | Play | Draw |
|---|---|---|
| TRAJECTORY_MACHINE_R | 1.731 | 1.890 |
| TRAJECTORY_SIMPLE_R | 1.452 | 1.704 |
| TRAJECTORY_TREE_R | 1.436 | 1.675 |
| SOLO004_SIMPLE_RULES | 1.313 | 1.593 |
| SOLO004_TREE_DEPTH4 | 0.979 | 0.980 |

MULL-005's central finding ("trajectory-first heuristics beat resource-first heuristics under one
shared cost-adjusted metric") holds under the corrected engine on both seats — SOLO004_TREE_DEPTH4's
high raw S/A rate is fully offset by aggressive over-mulliganing (avg final hand ~5.0-5.3 cards vs
~6.6-6.8 for the trajectory policies) once mulligan cost is priced in at all.

## 13. Holdout Validation (False-Keep / False-Mulligan Audit)

Fresh holdout seed (unused by any prior artifact), TRAJECTORY_SIMPLE_R vs TRAJECTORY_MACHINE_R
(ground truth), n=3,000: **precision=0.8197, recall=0.8724, false_keep_rate=0.4830,
false_mulligan_rate=0.1276** — reported plainly, not accepted merely because recall looks
reasonable, per the assignment's explicit instruction. All 686 disagreements classified by cause:
`hand_size_threshold` (139/126 — the largest cluster, expected: borderline-tier hands at the
keep/ship boundary), `premium_one_drop_rule` (128/12), `tutor_conversion` (35/60),
`engine_realization_timing` (0/34), `retained_interaction` (21/10), `survival` (0/18),
`oculus` (0/11), `unclassified` (75/2), `mana_without_payoff` (0/1), `pod` (0/0). Manual inspection
of `premium_one_drop_rule` false-keeps surfaced a real, disclosed limitation in TRAJECTORY_MACHINE_R
itself: the bounded search never explores ALTERNATE FETCHLAND TARGETS (a fetch's crack target is
chosen by the greedy land-drop heuristic alone), so some of this cause's count reflects a
machine-side search gap, not a SIMPLE-side rule error — documented so this cluster isn't mistaken
for proof the premium-one-drop rule needs further tightening without a manual check.

## 14. Paired Comparison Against MULL-005

TRUE pairing (identical seed=42/n=15,000/deck, verified row-for-row identical opening hands via
`random.Random.shuffle`'s single-call-per-hand guarantee) between MULL-005's committed grading and
a fresh rerun of the exact same hands through the corrected engine. Reported at BOTH each dataset's
own derived threshold (conflates tier-composition change with the threshold itself moving) and a
fixed threshold (tier in {S,A,B} for both — isolates pure tier-composition change):

- **Threshold-invariant**: 766 hands (5.1%) newly reach S/A/B; **2,482 (16.6%) drop out** —
  dominated by `commander_access_removed` (2,024 of 2,482, 81.5%), confirming section 1's headline
  finding. Newly-kept causes: `thrasios_concrete_benefit_understood` 249, `oculus_understood` 188,
  `survival_understood` 109, `birthing_pod_generic_infra_credit_understood` 59,
  `dork_to_engine_understood` 54, `tutor_to_mana_vault_to_engine_understood` 30,
  `smothering_tithe_promoted` 19, `expanded_tutor_search_understood` 22, `other` 36 (4.7%, manually
  spot-checked as minor mechanism-label variance, not a distinct new cause).
- **Threshold-relative** (both models' own derived bar, B→C): 4,068 (27.1%) newly kept / 362 (2.4%)
  newly shipped — mostly reflecting the bar itself moving down (section 11), not pure engine
  understanding; reported separately and explicitly not to be cited as "X hands newly kept because
  the model understands Y" (that claim belongs to the threshold-invariant numbers above).
- Smothering Tithe's realization-timing promotion directly: tier distribution as `tier_engine`
  moved from `{C: 55}` (old — never reached Tier A) to `{C: 60, A: 24}` (new — 24 hands now
  correctly reach Tier A, identically to Rhystic Study/Mystic Remora).

## 15. Pod-Conditioning Overlay and Primer Materials

Per the assignment's explicit constraint, `pod_archetypes.py`'s own algorithm (ARCHETYPES/
POD_MODIFIERS qualitative priors, the hard SHIP floor, the two mandatory confidence labels) is
preserved unchanged — no full pod simulation was run, and `pod_confidence` remains
`STRATEGIC_PRIOR_UNVALIDATED` on every archetype. What was audited and fixed is whether the
overlay's real, simulated inputs are still correct under the corrected engine (the CMDR-003 fix,
section 7). 6 new regression tests prove the hard SHIP floor holds for every named archetype
(individually and all stacked together) under the corrected model, and that named worked examples
(RogSi, Tayam) still behave per their disclosed qualitative priors.

Primer example hands regenerated (`mull005r_annotated_examples.json`): 10 snap keeps, 10 ordinary
keeps (CONDITIONAL_KEEP robust across every archetype), **9/10** pod-dependent keeps (a real,
disclosed finding from an exhaustive 200,000-hand search, not a padded example — flipping a band
requires a net ±2 pod modifier, which most single-archetype category overlaps don't reach), 10
mulligans (demonstrating the hard SHIP floor explicitly per example), 10 misleading hands (SOLO-004
resource-first vs trajectory-first disagreements confirmed correct by the bounded search). Primer
quick-reference table rebuilt against the re-derived thresholds (`mull005r_primer_tables.json`,
72 rows) — construction logic itself unchanged, per this section's own finding that the overlay
needed no algorithmic correction.

## 16. Key Conclusions, Scope Disclosures, and Limitations/Next Questions

**Key conclusions:**
1. The single largest correction this phase makes is removing commander-access credit — it was
   the dominant driver of MULL-005's keep decisions, larger than every genuine destination-
   understanding gain combined (section 14).
2. Tithe/Rhystic/Remora/Sentinel are now scored consistently — all four are equally
   unmeasurable-by-simulation opponent-triggered engines, and all four are proxy-credited
   identically (section 9), closing a real, previously-arbitrary inconsistency.
3. Oculus, Pod, and Survival are now real, first-class, state-aware destinations rather than
   afterthoughts — but Pod's own activation search is disclosed as rare at natural T1-T3 frequency
   (0/15,000), a genuine finding about this deck's mana curve, not a modeling failure.
4. TRAJECTORY_SIMPLE_R still beats both SOLO-004 baselines under the corrected engine on both
   seats (section 12), but its own precision/recall profile (0.82/0.87) is real and imperfect,
   concentrated in specific, named, diagnosable causes (section 13) rather than uniform noise.
5. The bounded trajectory search is disclosed as non-exhaustive in a NEW, specific way found this
   phase: it never explores alternate fetchland targets (section 13) — a real scope limitation
   layered onto the already-disclosed non-exhaustiveness of every other bounded-search family.

**Scope disclosures** (unchanged from MULL-005, still standing): solo trajectory value is not
multiplayer win rate; opponent-triggered engine productivity is a disclosed proxy, not a simulated
fact; pod modifiers are strategic priors, never simulated; interaction value is understated by a
solo model with no real opponent turns; T1-T3 optimization does not capture full-game consequences;
hand-size cost has no single "true" figure from this simulator, reported as a sensitivity sweep;
the bounded search is bounded, not exhaustive, and this phase found and disclosed a specific new
instance of that (fetch-target alternatives) rather than assuming completeness.

**Explicitly NOT run this phase**, per the assignment's stop condition: full 4-player matchup
simulation against any named pod archetype (the pod overlay remains permanently
`STRATEGIC_PRIOR_UNVALIDATED` until that exists); deckbuilding ablations (still out of scope from
SOLO-004); exhaustive fetch-target search as a 6th bounded-search family (disclosed future work,
section 13, not implemented — a real, scoped engineering decision, not an oversight).

**Next questions**, for a future phase: (1) does adding alternate-fetch-target search meaningfully
change the false_keep_rate attributed to `premium_one_drop_rule`? (2) does Pod's true T1-T3
frequency change materially in a larger sample, or is 0/15,000 a stable structural fact about this
mana curve? (3) would a land-count floor on the premium-one-drop SNAP_KEEP rule (this phase's
holdout audit surfaced 1-land hands still unconditionally snap-keeping) measurably improve
TRAJECTORY_SIMPLE_R's precision without materially hurting recall? (4) full 4-player pod-conditioned
matchup simulation remains this project's largest genuinely unaddressed question.

---

# SIM-001 MULL-006 — Contextual Trajectory Valuation, Resilience & Mulligan Calibration

Subject: same as above (`tymna-thrasios-treefarm-v1`,
`4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a`), confirmed unchanged from
MULL-005R (`mull006_provenance.json`, `subject_matches_mull005r: true`). Predecessor: MULL-005R.
Regression gate: `mull006_regression_gate.json`, `full_suite_passed: true`,
`gate_status: OPEN_FOR_PRODUCTION_RERUN` (389 tests collected, 386 passed, 3 pre-existing skips,
199 of the passing tests are new this phase across 19 test files).

## 1. Executive Summary

MULL-005R answered "what can this hand legally do?" MULL-006 asked the harder question: "how GOOD
is the best legal trajectory in the context of an actual cEDH mulligan decision?" It built eight
new, independently-testable contextual dimensions (engine strength, relative deployment speed,
seat-adjusted timing, draw dependence/outs, trajectory fragility/recovery, pod-trigger realization,
relevant agency, and expanded engine-realization timing), assembled them into a multi-dimensional
trajectory object, and compared FOUR different ways of combining them (weighted, lexicographic,
gated, tree) rather than assuming any one formula was correct from the start.

**What changed from MULL-005R**: every trajectory now carries a CONTEXTUAL grade in addition to its
legacy tier — a grade that can differ from the legacy tier for reasons the model can explain (draw
dependence, resilience, seat exposure, pod realization). A real, pre-existing gap in the fetch-target
search was fixed (task #103) before any of this contextual work began, exactly as the assignment
required. A real gap in the London mulligan harness was also found and fixed mid-phase (task #117):
mulligan depth was never actually wired into the keep decision in the pre-existing simulation loop,
so every attempt was silently evaluated against the size-7 bar regardless of how many mulligans had
already been taken.

**Which previous conclusions survived**: the four primary destination families (resource engine,
early Oculus, functional Pod, functional Survival), the "acceleration is a means not a destination"
rule, the Tymna/Thrasios commander policy, and the FAERIE MASTERMIND CORRECTION's premise (passive
alone is the engine) all survive unchanged and are now load-bearing parts of the contextual model.

**Which reversed or were substantially qualified**: MULL-005R's Mastermind Tier-C activation
requirement is explicitly overridden for STRENGTH purposes (by direct instruction, not a new
finding) — but the contextual holdout validation (task #119) found this correction cannot be
validated against the (deliberately unmodified) legacy grader, since the two systems are designed to
diverge exactly here. More importantly, an UNPLANNED finding dominates this phase's disagreement
data: the gated architecture's `DRAW_DEPENDENCE_PROBABILITY_GATE_THRESHOLD=0.2` fires on 98.1% of
its 696 disagreements with the legacy grader (`contextual_holdout_validation.json`) — a strategic-
prior/threshold-tuning finding, not a rules failure, but a genuine reason not to treat the current
gated architecture's exact threshold as final. This is flagged, not silently fixed.

## 2. Correctness

**Fetch branching** (task #103, section 2 — required to be fixed FIRST): a 6th bounded-search
family now branches one fetchland's target per candidate, reusing the pre-existing but previously
unwired `forced_fetch_target` plumbing. `fetch_branching_validation.json`: 41.3% of sampled hands
had at least one fetch-target candidate; 8.28% of ALL sampled hands changed their best-known
trajectory as a result (20.0% among hands with a fetch candidate); 3.34% changed their mulligan
decision outright. Verified against the exact real-world failure case surfaced at the end of
MULL-005R (Wooded Foothills → Tropical Island reaching Tier S Mystic Remora where the greedy line
reached Tier F).

**Bugs discovered and fixed this phase**: (1) `engine_strength()`'s first draft returned a strength
label for any tracked card sitting in HAND, never checking battlefield presence — caught by its own
regression test (`test_mastermind_not_on_battlefield_returns_none`), fixed by adding an explicit
`on_battlefield` check. (2) `contextual_valuation_models.py`'s first draft built seat-timing and pod-
realization fields onto every trajectory object but never wired them into any of the four valuation
architectures — caught immediately by task #114's own smoke test (0 seat/pod flips across 200 real
hands, which should have been near-impossible), fixed by adding seat-exposure and pod-realization
gates to all four architectures. (3) A cosmetic ordering mismatch between
`DISAGREEMENT_CAUSES_ORDER` and the gated model's actual gate-check order was found and corrected
during task #119's own regression-test authoring.

**Regression status**: `mull006_regression_gate.json` — full suite green, all 9 assignment-named new-
mechanic test categories present with real coverage (fetch-target branching, engine-strength/speed
separation, Mastermind passive-engine, seat-order, draw-outs, one-land-trajectory, counterfactual-
removal/recovery, interaction-relevance, pod-realization-provenance).

## 3. Strength × Speed

`engine_strength_prior.json` and `relative_speed_model.json` establish the two axes independently
(PILOT_SUPPLIED_STRATEGIC_PRIOR, back-derived to exactly reproduce every worked example the
assignment itself gave). `strength_speed_matrix.json` combines them into the given 4×4 (+ a
disclosed extrapolated LATE column) matrix:

| strength \ speed | EXTREME | AHEAD | ON-TIME | BEHIND | LATE (extrapolated) |
|---|---|---|---|---|---|
| S | S+ | S | A | B | B- |
| A | S | A+ | A / B+ (ambiguous) | C+ | C |
| B | A+ | A | B | C | D |
| C | A | B+ | B- / C+ (ambiguous) | D | F |

`strength_speed_sensitivity.json` tested this against 2373/6000 real hands whose best trajectory
used a tracked engine: the A/ON-TIME ambiguous cell resolves to its PRIMARY grade ("A") 9× better
than the alternate (5.46% vs 0.62% band-match rate against the independent legacy grader, n=641);
the C/ON-TIME cell favors the ALTERNATE resolution but on only 5 samples — too few to trust.
**Boundary sensitivity finding**: shifting `expected_deployment_turn` by ±1 turn flips the speed
label for 85-100% of real samples for most engines — the classification is a sharp step function
over a narrow T1-T3 range and is NOT robust to a 1-turn prior error, independent of whether the
CURRENT values are correct.

Answering the report's own numbered questions directly: **(1)** yes — separating strength from speed
is what lets a T1 Mastermind (A+) clearly outrank a T2 Esper Sentinel (C+) even though Sentinel's
raw strength (A-) is comparable, a distinction a single conflated score could not make. **(2)** the
matrix table above; empirically, S-EXTREME/S-AHEAD and A-EXTREME cells behave like real S/A
trajectories in the sampled data (`top_25_contextual_trajectories.json`'s top ranks are exclusively
T1/T2 functional Pod and Smothering Tithe). **(5)** T1 Mastermind grades A+ on the new matrix, but
this specific comparison could NOT be validated against the legacy grader in `strength_speed_
sensitivity.json` (avg legacy rank 3.0 for T1 Mastermind vs 1.0 for T2 Remora, n=7 vs 133) — by
design, since the legacy grader still enforces the pre-correction activation requirement MULL-006
explicitly overrides. Whether T1 Mastermind's real value matches this prior remains
STRATEGIC_PRIOR_UNVALIDATED pending real multiplayer data. **(6)** T2 Remora/Sentinel are downgraded
from S/A (their intrinsic strength) to C+ (BEHIND-column penalty) — a full 5+ band drop from being
merely "cast one turn late."

## 4. Top 25 Contextual Trajectories

`top_25_contextual_trajectories.json` (3000 real hands sampled, gated architecture, seat 1,
`midrange_grind` reference archetype) is dominated by T1/T2 functional Birthing Pod and T1/T2
Smothering Tithe, both grading S+ at EVERY hand size (7 through 4) — fully self-contained, robust
trajectories with a real second destination or fodder, that don't degrade even under aggressive
bottoming. **(3)** T2 Tithe is confirmed among the deck's best realistic starts — it appears
repeatedly in the top 25 and the matrix places T2 Tithe at S (AHEAD column, S-strength row).
**(4)** functional early Pod is Tithe-level or better: both share the S intrinsic strength band and
both appear at the very top of the ranked list; Pod additionally shows up with richer SECONDARY
PLAN diversity (Survival of the Fittest, Esper Sentinel, Chord of Calling as realized fallbacks in
the table's rows 21-25) since its own mechanism (find another creature) naturally chains.

## 5. Seat Effects

`seat_adjusted_trajectory_census.json` establishes the exact game-structure arithmetic
(`opponent_turns_before(N, seat) = 3(N-1) + (seat-1)`) and the disclosed action-window convention.
Two structural findings: (a) the raw exposure delta between Seat 1 and Seat 4 is a CONSTANT 3 turns
for any deployment turn, but its RELATIVE severity shrinks as deployment turn increases (T1: 0→3,
infinite relative increase; T3: 6→9, only 50%) — T1 trajectories are the most seat-sensitive in
relative terms even though every trajectory shares the same absolute swing; (b) "value generated
before our next turn" is seat-INVARIANT — seat changes exposure magnitude, never the underlying
yes/no of whether realization structurally precedes our own next turn.

`seat_pod_matrix.json` (4000 real hands, gated architecture): **(7)** the most seat-sensitive
tracked engines are Esper Sentinel (59 flip-contributing hands), Thrasios (53), and Deathrite Shaman
(34) — notably the two tax-gated, opponent-triggered engines dominate, consistent with the seat-
exposure gate's interaction with FRAGILE/ALL_IN resilience. **(8)** seat alone changes the mulligan
decision for **9.09%** of tracked-destination hands (278/3057) — real, but secondary to draw
dependence in overall impact.

## 6. Draw Dependence / Outs

`draw_dependence_analysis.json` (4545/6000 real hands with a tracked trajectory): **48.58%**
SELF_CONTAINED, **9.61%** BROAD_OUTS, **41.80%** EXACT_OR_NEAR_EXACT, **0%** NARROW_OUTS observed —
a genuine, disclosed finding about this deck's land density (~27.5%), not a bug: land dependencies
land almost exclusively BROAD (avg 25.45 outs of the ~92-card remaining pool per `outs_analysis.
json`) while engine-card dependencies are always EXACT (singleton, outs_count=1 always), leaving
little room for a genuine middle category. **(10)** answering directly: **41.8%** of advertised T2+
trajectories in this sample are actually draw-dependent (not counting hand-tutor/fetch-sourced
lines, which are correctly excluded as SELF_CONTAINED). **(12)** the outs threshold distinguishing
reasonable speculation from a bad gamble, as implemented in the gated architecture, is
`probability_of_trajectory < 0.2` combined with NARROW/EXACT classification — but the holdout
validation (section 12 below) suggests this specific threshold may be too strict for the ROUTINE
"engine card was a natural draw" case, since that case's probability is essentially ALWAYS below
0.2 by construction (singleton copy).

`one_land_hand_audit.json`: **(11)** genuinely self-contained one-land + dork + T2-engine hands
are real but a minority of one-land openers — 134/1660 (8.1%) at hand size 7, with a **100%** keep
rate at every hand size once found; one-land hands are NOT rare in this deck (27.67% at size 7
rising to 42.20% at size 4, tracking its land density). Keep rate declines slightly from Seat 1/2
(47.2%) to Seat 3/4 (43.6%) even at hand size 7.

## 7. Fragility / Recovery

`trajectory_fragility_analysis.json` (4575 real hands): **72.9%** RECOVERABLE, **15.7%** FRAGILE,
**4.3%** ROBUST, **7.1%** ALL_IN. `trajectory_recovery_analysis.json` shows resilience classes are
clearly differentiated: ROBUST hands have a second destination ALREADY realized 100% of the time
(by construction) and 0-turn recovery; ALL_IN hands have **0%** live interaction remaining and a
2.82-turn average time to next development for the minority that have ANY known path forward at
all. **(15)** yes — resilience materially changes decisions: it is one of only two dimensions
(alongside draw dependence) with its own hard gate in the gated architecture, and the disclosed
finding that `creatures_sacrificed` is 0 across the ENTIRE sample (even when Birthing Pod itself is
`tier_engine`) revealed that Pod's own tier credit is earned via infrastructure-readiness, not an
already-executed exchange — a genuine, non-obvious consequence of how the legacy grader credits Pod.

`fragility_stress_test.json` (20000 hands, 13 named families): **(13)** the most fragile-by-name
families are the rare ones with small samples (T1 Archivist n=37, 2.7% strong-secondary rate; T1
Mastermind n=22, 9.1% strong-secondary); **(14)** T1/T2 Remora and Sentinel retain the strongest
recovery plans among common families (~18-19% strong-secondary-trajectory rate), consistent with
being drawn into hands that already carry other resources rather than being the hand's sole plan.

## 8. Pod Realization

`pod_realization_prior.json` (STRATEGIC_PRIOR_UNVALIDATED throughout, no fabricated trigger rates):
the 8×10 engine×archetype matrix is rule-derived from `pod_archetypes.py`'s existing archetype
descriptions, not invented fresh. **(16)** the greatest pod-realization variance belongs to the four
tax-gated engines (Rhystic Study, Mystic Remora, Esper Sentinel, Smothering Tithe), which swing from
VERY_HIGH (RogSi/stax_heavy, low tax-payment ability) to LOW (Kinnan/Etali, high tax-payment
ability) — a wider spread than the non-gated engines, since they're penalized on TWO axes
(trigger-density AND ability to pay through the tax) rather than one.

## 9. Relevant Agency

`relevant_agency_analysis.json`: this deck's interaction suite is majority stack/counter-based with
NO dedicated creature-removal or activation-disruption card — relevant agency against Kinnan/Sisay-
style creature-centric pods is structurally capped even when live agency is high. **(17)** live
interaction becomes irrelevant interaction whenever the opposing pod's threat axes don't intersect
the card's tags — concretely demonstrated by disagreement example F (a real hand whose one live
interaction card counts as relevant against RogSi but not Tayam). **(18)** relevant agency DOES
upgrade a marginal but coherent hand under all four architectures (the final agency-bonus step,
gated behind "no earlier downgrade gate fired"). **(19)** interaction does NOT ever rescue a
destination-less hand: the boundary check found 681/6000 D/F-tier hands still had live interaction
(136 had 2+), and every single one remained a mulligan — confirmed by construction, since the
contextual model never lets agency scores participate in tier grading at all.

## 10. Destination-Specific Findings

**Smothering Tithe**: S intrinsic strength; T1→S+, T2→S on the matrix; VERY_HIGH pod realization
against RogSi/stax_heavy, MODERATE against Kinnan/Blue Farm/Tivit/Etali — the tax-payment penalty
produces real spread even though land drops are near-universal. Appears repeatedly at the top of the
top-25 table.

**Birthing Pod**: S intrinsic strength ONLY when functional (deployed + fodder + payable activation
— disclosed as not verifying the found target is a genuine upgrade). T1→S+, T2→S. `creatures_
sacrificed` is 0 across the entire sampled population even when Pod itself is `tier_engine` — a
disclosed, non-bug finding about how the legacy grader credits Pod's own tier (infrastructure-ready,
not already-used).

**Abhorrent Oculus**: kept as a separate premier destination throughout, never folded into the
engine-strength ranking (no `expected_deployment_turn` entry, no pod-realization entry). Appears in
145/6000 sampled hands as the fragility-stress "early Oculus" family, 12.4% strong-secondary rate.

**Rhystic Study**: A+ intrinsic strength; T1 mid-engine curve (AHEAD at T1, ON-TIME at T2). VERY_HIGH
pod realization against RogSi/stax_heavy; the fetch-branching fix's own worked regression example
was specifically a Mystic Remora line, not Rhystic, but Rhystic shares the identical tax-gated
realization profile.

**Faerie Mastermind**: A intrinsic strength via the FAERIE MASTERMIND CORRECTION (passive trigger
alone, no activation requirement — but deployment is still required, confirmed by regression test).
LOW pod realization against RogSi/Kinnan/Sisay/Etali/stax_heavy, HIGH only against Blue Farm (a
draw-heavy control archetype whose opponents' own second-draw effects feed Mastermind's trigger).

**Mystic Remora**: A intrinsic strength; T1→B (ON-TIME), T2→C (BEHIND) — the assignment's own named
"T2 Remora should not receive premium-speed credit" example, confirmed. VERY_HIGH pod realization
against RogSi/stax_heavy, LOW against Kinnan/Etali.

**Esper Sentinel**: A- intrinsic strength; same T1/T2 timing profile and pod-realization pattern as
Remora (both tax-gated, noncreature-spell-driven). The single most seat- AND pod-sensitive tracked
engine in the entire sample (59 seat-flip-contributing hands, 49 pod-flip-contributing hands).

**Archivist of Oghma**: A- intrinsic strength; driven by tutor-search density, so realization is
HIGH against RogSi/Sisay (tutor-dense archetypes) and LOW against Tayam/Etali (tutor-light).

**Sylvan Library**: B+ intrinsic strength; the sole OWN_NEXT_DRAW_STEP realization class among
tracked engines — never realizes before our own next turn regardless of seat, and the pod
realization modifier structurally does not apply to it at all (not opponent-behavior-dependent).

**Survival of the Fittest**: B intrinsic strength ONLY when functional (deployed + creature fuel in
hand + payable {G} activation); its `expected_deployment_turn=2` is the one EXTRAPOLATED (not
back-derived) entry in `relative_speed_model.json`, disclosed as such.

**Heartwood Storyteller**: B- intrinsic strength; its driver dimension (noncreature-spell density)
is disclosed as a coarser proxy than its real single-target-spell-specific Oracle trigger.

**Runic Armasaur**: C+/B- boundary intrinsic strength (the one entry not cleanly in either band);
the only tracked engine whose realization driver is creature density rather than spell/tutor/draw
density — HIGH against Kinnan/Rog-Thras-Tree-Farm/Tayam (creature-heavy pods), LOW against RogSi/
Blue Farm/stax_heavy (spell-heavy pods).

## 11. London Mulligan Results

`contextual_london_results.json` (2000 sequences × 4 architectures, seed 6010) — **(21)/(22)/(23)/
(24)** answered together via the reused per-size thresholds (C@7, D@6, D@5, keep-everything@4,
carried over from `mull005r_hand_size_thresholds.json`, NOT re-derived on the new scale this phase —
see limitations): at 7, demand a contextual grade of C or better (a real, mostly self-contained,
on-time-or-better destination); at 6, D or better becomes acceptable (real secondary engines and
somewhat fragile lines); at 5, the SAME D-or-better bar applies but the population choosing from it
is weaker, so proportionally more hands clear it; at 4, keep essentially anything with a legal
destination — MULL-005R's own economics already found no threshold clears a 5th mulligan's cost.
gated/lexicographic/tree behave similarly (mean tier value 2.64-2.66, 1-1.4% reach 3+ mulligans);
**weighted** mulligans substantially more (6.35% reach 3+ mulligans) because it COMPOUNDS multiple
simultaneous penalties rather than applying one bounded step, trading final hand size (avg 6.25 vs
~6.42-6.45) for quality (mean tier value 2.72, S/A rate 33.6% vs 30-31% for the other three) — a
genuine, disclosed architecture-sensitivity finding, not a claim that weighted is "correct."

## 12. Contextual Disagreement Hands

`contextual_disagreement_examples.json` produced all 7 required examples (A-G) from real simulated
hands: A confirmed T1 Mastermind (A+) outranking T2 Sentinel (C+) on real data; B and E were reused
directly from `seat_pod_matrix.json`'s own validated real flips; C found a real hand whose "T2
Rhystic Study" was not actually in the opening 7 at all; D found two real hands reaching the SAME
destination (Esper Sentinel) with opposite resilience (ROBUST with 4 cards + a realized second
destination vs ALL_IN with 0 cards and a fully collapsed hand); F found a real hand whose live
interaction registers relevant against RogSi but not Tayam; G found a real hand whose contextual
grade (D) fails the size-7 bar but clears the size-6/5 bar with no bottoming needed at all.

`contextual_holdout_validation.json` (3000 fresh-seed hands, seed 9002, unused by any prior
artifact): **76.8%** agreement between the contextual (gated) and legacy machine decisions,
**23.2%** disagreement, entirely one-directional (contextual only ever mulligans MORE than legacy,
never the reverse, under the current gate design). **98.1%** of all 696 disagreements (683) trace to
ONE mechanism: the draw-dependence gate firing on essentially every "engine card was a natural
draw" hand regardless of the underlying engine's strength, since that case's hypergeometric
probability is always below the 0.2 threshold by construction (singleton copy in a large remaining
library). Flagged explicitly as a threshold-tuning candidate, not silently corrected, per the
assignment's own "do not assume these exact gates are correct."

## 13. Primer Decision Tree

`primer_mulligan_decision_tree_v1.md` — 5 questions (DESTINATION / TIMING / IS-IT-ALREADY-THERE /
IF-ANSWERED-AM-I-DONE / GOOD-ENOUGH-FOR-DEPTH), not the assignment's illustrative 7. Seat and pod are
folded into a single "fine-tuning" note rather than kept as full branches, since their measured flip
rates (9.1%/4.1%) are real but secondary to the four dominant factors. **(25)** the compact
heuristic: no destination is an automatic mulligan with no exceptions; timing is judged relative to
each engine's OWN curve, never raw turn number; a hand that "has an engine" only because a topdeck
happened to provide it should be discounted hard (the single most common trap this phase's data
surfaced); a trajectory that collapses entirely if answered needs an exceptional (S+/S) destination
to justify keeping; and the bar for all of the above loosens — but does not disappear — as mulligan
depth increases.

## 14. Primer Example-Hand Packet

`primer_mulligan_packet_v4.md` — 50 real hands (10 each: snap keeps, normal keeps, conditional
keeps, mulligans, deceptive hands), all 16 required fields per hand, seat and pod archetype cycled
for variety. Deceptive hands split into two real sub-types found organically: TRAP hands (5+ cards
remaining or 2+ live interaction, but grade D/F — no real destination underneath) and HIDDEN GEM
hands (2 or fewer cards remaining, but grade S+/S/A+/A — the destination alone carries the hand).
The TRAP examples organically reproduced section 12's draw-dependence-gate finding (Thrasios/
EXACT_OR_NEAR_EXACT hands recurring as "deceptive" D-grade mulligans) without being cherry-picked
for it. A "Similar Hands, One Variable Changed" appendix reuses the real B/E/G disagreement
examples directly.

## 15. Limitations

- **The gated architecture's specific thresholds are not validated, only tested for internal
  consistency.** The dominant holdout finding (section 12) is a live, disclosed candidate for
  re-tuning, not a settled conclusion.
- **Per-size contextual keep thresholds (C@7/D@6/D@5/keep-everything@4) are REUSED from MULL-005R's
  legacy-scale derivation, not re-derived for the new 11-band contextual scale.** A full EV-sweep
  re-derivation using the same methodology MULL-005R used is the single largest piece of disclosed
  future work from this phase.
- **Only one of the four valuation architectures (gated) was used for the seat×pod matrix, top-25
  table, one-land audit, and disagreement examples**, for tractability — the other three exist,
  are tested, and diverge measurably (section 11), but were not run through every downstream
  artifact.
- **Pod realization values remain STRATEGIC_PRIOR_UNVALIDATED** — no real multiplayer simulation or
  tournament data exists in this project to calibrate against; every number in `pod_realization_
  prior.json` is a disclosed, rule-derived judgment, not a measurement.
- **draw_dependence_model's outs-counting is a disclosed simplification**: land outs count EVERY
  remaining land regardless of color-fixing quality; engine-card outs never search for broader
  functional substitutes (only the exact singleton).
- **This phase does not model a real opponent's actual behavior, removal suite, or likelihood of
  disruption** — fragility/recovery work measures CONSEQUENCE IF ANSWERED, never a probability of
  being answered. Relevant-agency threat-axis tags are hand-derived from Oracle text and
  pod_archetypes.py's existing descriptions, not measured from real games.
- **Hand-size sampling for the one-land audit approximates smaller hand sizes by drawing N cards
  directly, not by modeling the real London-mulligan bottoming decision** from a 7-card draw.

## 16. Recommended Next Research

1. **Re-derive per-size contextual keep thresholds** via the same EV-sweep methodology MULL-005R
   used for the legacy scale, replacing the reused C@7/D@6/D@5 placeholders.
2. **Re-examine the draw-dependence gate's threshold** (currently 0.2) given the dominant holdout
   finding — likely candidates: raise the threshold, or treat "engine card is a natural draw" and
   "supporting land is a natural draw" as separately-thresholded cases rather than one shared rule.
3. **Run all four architectures (not just gated) through the seat×pod matrix, top-25 table, and
   disagreement examples**, to see whether the architecture choice changes which specific hands/
   engines are flagged as most seat- or pod-sensitive, not just the aggregate flip rates already
   measured in section 11.
4. **Extend the bounded fetch-target search to the FULL joint combination** across multiple
   simultaneous fetches in one hand (currently only one fetch's target branches per candidate) —
   disclosed as a still-standing BOUNDED_SEARCH_LOWER_BOUND limitation from task #103.
5. **Real 4-player pod-conditioned matchup simulation** remains this project's largest genuinely
   unaddressed question, and the only way to move any of section 8's pod-realization values or
   section 9's relevant-agency threat-axis tags out of STRATEGIC_PRIOR_UNVALIDATED status.

---

# SIM-001 MANA-AUDIT-002 — Mana-Base Decision Analysis

Full report: `results/solo_baseline/mana_audit_002_report.md`. Machine-readable artifacts:
`mana_audit_002_inventory.json` (A/B), `mana_audit_002_color_demand.json` (C),
`mana_audit_002_baseline.json` (D), `mana_audit_002_configs.json` (E/F, 20 counterfactual
configs), `mana_audit_002_pareto.json` (G), `mana_audit_002_external_sanity.json` (I).

Subject: new task-scoped frozen snapshot `tymna-thrasios-treefarm-manaaudit002-v1`
(content-identical to `tymna-thrasios-treefarm-v1`, independently recomputed hash, per the
assignment's own no-silent-reuse instruction). Reused MULL-005R/006's T1-3 engine and mulligan
machinery unchanged; no XMage runs. Found and fixed two correctness bugs along the way: Talon
Gates of Madara was modeled as a flat free rainbow land (real text is colorless-guaranteed,
colored mode costs an extra generic mana); `load_deck_cards()` read a nonexistent `cmc` cache key,
silently zeroing every card's mana value (fixed, filed as coverage-backlog `SIM-0018` — also
means Birthing Pod/Survival/battlefield-tutor sac-mv-matching search families, previously
silently non-functional, now work correctly; re-running MULL-005R/006's own historical datasets
with the fix is disclosed as follow-up, not done here). Confirmed Deathrite Shaman's mana ability
is structurally dead in this exact list (zero real basic land cards to exile).

**Headline recommendation:** adopt **+Scalding Tarn, −Talon Gates of Madara** (unchanged land
count) — the only tested configuration that improves both engine-deployment speed AND both
mulligan-quality metrics simultaneously versus the current 27-land baseline. The current 27-land
configuration is itself Pareto non-dominated (no tested alternative beats it on speed,
consistency, AND resilience/utility at once) — 27 is defensible, not wrong, and 28 lands is a
small, real, optional upgrade if a card can be found to cut for it. Full GAIN/COST reasoning per
recommendation, all 20 counterfactual configs' exact deltas, and confidence caveats (notably:
every external decklist-comparison source was network-egress-blocked, so Section I is low-
confidence) are in the full report.
