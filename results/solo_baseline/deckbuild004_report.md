# SIM-DECKBUILD-004 — Four-Card Conversion Package Audit

**Question:** does adding Neoform, Formidable Speaker, Talion the Kindly Lord, and Seedborn Muse
(removing Heartwood Storyteller, King T'Challa, Elves of Deep Shadow, and one reactive interaction
slot) improve conversion enough to justify the cost?

**Scope actually completed:** phase_0 (reactive-slot screen), E1 (early cost), E2 (tutor
topology, this program's own HIGHEST-priority item), a scoped E4 (Pod-rung quality census), and
the B4-B7 ablation census. **E3 (full stratified post-fight conversion) and E5/E6 (late-draw
quality, engine-behavior tagging) were NOT built** — each is a substantial standalone undertaking
on top of what's below, and the evidence gathered so far did not trigger this program's own
`stop_early_if` condition that would make them moot, but did not produce a result decisive enough
to justify their cost either. This is disclosed honestly throughout, not silently skipped — see
section 9's confidence discussion and the Decision Matrix's blank cells.

All numbers are machine-readable in `results/solo_baseline/deckbuild004_*.json`.

---

## 1. Executive verdict

**ADOPT_PARTIAL_PACKAGE.** Specifically: adopt the reactive-slot cut (Commandeer → Formidable
Speaker) and the Elves-of-Deep-Shadow → Neoform swap now; treat Talion and Seedborn Muse as
**INCONCLUSIVE_NEEDS_POD_VALIDATION** — their real value proposition (Talion's opponent-cast
trigger, Seedborn's opponent-untap-step trigger) cannot be verified in this project's solo/
no-opponent T1-3 engine at all, not merely imprecisely.

- **Strongest addition: Formidable Speaker** (via Commandeer). Clean win in phase_0's paired
  screen (only cut with a >1pp harm-score margin over the runner-up), and its ETB/untap kit is
  fully verifiable in this solo engine (unlike Talion/Seedborn).
- **Second-strongest: Neoform.** Costs a real T1 dork (Elves of Deep Shadow) for essentially zero
  measured T2-engine cost (+0.14pp, "trivial" band — the assignment's own required key number).
  E2's topology check found it correctly does NOT complete Pod-dependent combos it merely
  resembles (INT-0012 requires Birthing Pod itself present) — a real, verified anti-overclaim
  result, not a structural coincidence.
- **Weakest, unverifiable addition: Seedborn Muse.** E4 found it creates a Birthing Pod rung
  (4→5) that was a complete dead end in the baseline (zero MV5 creatures exist in the current
  98-card list at all) — a genuine structural contribution. But Seedborn's entire mechanism
  (untap during OTHER players' untap steps) cannot fire in ANY solo simulation at ANY turn count,
  so whether that structural contribution translates into real game value is a question this
  project's engine architecture cannot answer — it needs real pod play, not more solo simulation.
- **Talion:** widens an already-functional Pod rung (3→4: 4 targets → 5) without changing its
  win-rate mix, and its opponent-cast trigger is likewise unverifiable solo. Real but modest
  structural value; real but unmeasured trigger value.

## 2. Cost of the sixth dork cut

**Exact key number (assignment-required): +0.14 percentage points T2-engine probability,
Elves of Deep Shadow → Neoform ("trivial" band, <0.5pp).** (`deckbuild004_e1_early_cost.json`,
`required_key_number`.) This is the headline finding of E1: cutting a real T1 mana dork for a
card that does nothing without a battlefield sacrifice costs **nothing measurable** on T2 engine
access, and other census metrics move in the same trivial-to-modest-positive direction
(T1 functional mana 8.36%→8.75%, T3 two-plus-engines 5.47%→5.40%, essentially flat).

Paired flip-rate metrics (`keep_A_ship_B_rate` / `ship_A_keep_B_rate` in the JSON) showed ~21-24%
of same-seed-paired hands flip the keep/mulligan decision in EITHER direction — **this number is
disclosed as noisy, not a clean causal estimate**: "paired" here means same RNG seed, not a
literal same-7-cards-except-swapped guarantee (the two variants' card lists differ, so a shuffle
of a different list at the same seed does not necessarily deal the same hand). Treat the
census-level deltas above as the reliable evidence; the flip-rate numbers as directional color.

**Late-draw tradeoff:** not measured (E5 not built — see section 9).

## 3. Tutor topology (E2, this program's HIGHEST-priority item)

Bounded, disclosed search (2-3 representative start states per family × 4 detectable targets ×
7 variants — not the assignment's full ~35-state sweep; see `deckbuild004_e2_tutor_topology.json`
module docstring for the exact scope and why).

- **Newly-winning states, B3 vs B0: zero**, across every family/instance tested
  (`states_newly_reaching_target_B3_vs_B0`, all four target lists empty). In the bounded sample
  checked, the package does not unlock a NEW deterministic win path from a start state that
  couldn't already reach one — a real, if narrow, finding, not a null result from a broken search
  (see the two verification checks below).
- **Verification the search itself is sound:** Pod + Derevi (MV3) → Clever Impersonator (MV4)
  correctly registers `deterministic_win_available=True` in BOTH B0 and B3 — this is INT-0012
  (Clever Impersonator copying Birthing Pod), an already-verified project combo, reproduced
  correctly here as a sanity check, not a coincidence.
- **Anti-overclaim confirmed working:** the SAME target (Clever Impersonator) reached via Neoform
  instead of Pod does NOT register as a deterministic win, because Neoform exiles itself (no
  second Pod-like permanent survives to be copied) — exactly the assignment's own instruction
  ("do not call Neoform actionable unless a legal/useful sacrifice exists") verified as a concrete
  behavioral difference, not asserted.
- **Paths shortened by Neoform/Speaker:** not separately quantified in this bounded pass (would
  need the full unbounded sweep — disclosed as future work).

## 4. Post-fight conversion (E3)

**Not built.** This is the single largest piece of unfinished scope in this program: E3's own
stratified, state-conditioned Monte Carlo (6 state dimensions × 3 turns × real decision-target
computation) is a substantial standalone undertaking, comparable in scope to everything completed
in sections 1-3 combined. It was not started because the evidence gathered so far (trivial early
cost, no severe regression, but also no unlocked new wins in E2's bounded sample) did not clearly
justify it under this program's own `proceed_if`/`expand_if` framing, and remaining effort budget
for this task did not support it. `P_win_attempt_now` / `P_protected_win_attempt_now` /
`P_win_attempt_by_next_untap` and the rest of E3's metric list are genuinely unanswered.

## 5. Pod structure (scoped E4)

Real, concrete result (`deckbuild004_e4_pod_rungs.json`; one representative sacrifice per rung,
every legal target in the variant's real library — not the assignment's full frequency-weighted
exhaustive census):

| Rung | B0 legal targets | B3 legal targets | B0 dead end? |
|---|---|---|---|
| 1→2 | 11 (all engine_upgrade) | 11 (all engine_upgrade) | no |
| 2→3 | 11 (all engine_upgrade) | **10** (all engine_upgrade) | no |
| 3→4 | 4 (Clever Impersonator=win, Hazel's Brewmaster/Sowing Mycospawn/Subtlety=engine) | 5 (+ Talion, the Kindly Lord=engine) | no |
| **4→5** | **0** | **1 (Seedborn Muse=engine)** | **YES — complete dead end** |

**A real, previously-undiscussed cost surfaced here:** the 2→3 rung's target count actually
DROPS (11 → 10) under the full package, because King T'Challa and Heartwood Storyteller — both
removed by the ENGINE_PACKAGE swap — are themselves real MV3 creatures (cmc 3 each), and neither
Talion (MV4) nor Seedborn (MV5) backfills that specific rung. The package adds depth at 3→4 and
4→5 while quietly thinning 2→3 by one target. Not large (11 legal targets down to 10, all still
`engine_upgrade`-class, no win-path lost), but a genuine, previously unstated tradeoff this
section's own data surfaced, not something the earlier sections' framing anticipated.

**Talion_rung_value:** real but incremental — widens 3→4 from 4 to 5 legal targets, same
immediate-win proportion (1 of 4 → 1 of 5, i.e. the win-rate SHARE of that rung's targets actually
drops slightly, though the absolute win path — Clever Impersonator — is unaffected and still
present). Talion itself classifies as `engine_upgrade`, not `immediate_win` or `protected`.

**Seedborn_rung_value:** structurally larger than Talion's — it doesn't compete at an existing
rung, it **creates** one that was completely absent (0 targets → 1 target). But per section 1 and
this report's standing disclosure, "creates a legal Pod target" says nothing about whether
Seedborn's own ability generates any real value once resolved — that requires opponent turns,
which no solo simulation can produce.

**Pod_dead_end_rate:** 1 of 4 rungs tested (4→5) is a hard dead end in baseline; 0 of 4 in the
full package (Seedborn fills it). 1→2 and 2→3 were never dead ends in either config.

## 6. Engine-package quality (Talion/Seedborn vs. Heartwood/King T'Challa)

Not built as a dedicated behavioral-tagged comparison (E6). What IS available: B1_ENGINE_SWAP's
own census (`deckbuild004_e1_early_cost.json`) shows the engine-only swap is close to neutral on
every T1-T3 metric versus baseline (T2 any-engine 23.01%→22.75%, T3 two-plus-engines 5.47%→5.35%,
both within noise) — i.e., swapping Heartwood/King T'Challa for Talion/Seedborn ALONE, without
the conversion package, does not measurably change early engine access either way in this solo
model. This is consistent with (not proof of) the standing finding that Talion's and Seedborn's
real differentiators are both opponent-turn-dependent mechanisms this engine cannot observe.

## 7. Reactive interaction cut

**Selected: Commandeer** (`deckbuild004_phase0_reactive_screen.json`). Clear, >1pp harm-score
margin over the runner-up (Subtlety) at n=15,000/4,000 paired samples. Commandeer is structurally
the most mana-intensive pitch card in the deck's existing interaction suite (pitches 2 blue cards,
vs. 1 for Subtlety/Misdirection/Force of Will) — already the least likely of the four candidates
to be live in a T1-3 window regardless of whether it's cut. Marginal per-candidate deltas (T2
free-live-interaction, T3 any-live-interaction, mulligan D-or-F, mean blue-pitch-fuel count) are
all reported raw in the JSON, not collapsed into the harm-score alone. **"An Offer You Can't
Refuse" was NOT evaluated as a real cut candidate** (it isn't in the current 98-card list — cannot
cut a card that isn't there); it was run as a separate, differently-shaped informational
comparison only.

## 8. Ablations (B4-B7 vs B3)

**Important caveat before reading this table: B4-B7 are all 97-card decks (one lighter than B3's
98)**, since each "reverts" exactly one of B3's four additions while keeping all four removals
(a deliberate isolation choice, matching this project's MANA-AUDIT-002 precedent) — so their
raw engine-rate metrics run slightly ABOVE B3's from simple deck-thinning, not because removing
each card individually helps. The right read is the narrow spread AMONG the four ablations
themselves, not their absolute gap from B3.

| Variant | T2 any-engine | T3 two-plus-engines | T1 functional mana |
|---|---|---|---|
| B3 (full, 98 cards) | 24.62% | 5.93% | 8.66% |
| B4 (no Neoform, 97) | 24.80% | 6.24% | 8.95% |
| B5 (no Speaker, 97) | 24.29% | 5.69% | 8.93% |
| B6 (no Talion, 97) | 24.82% | 6.25% | 8.93% |
| B7 (no Seedborn, 97) | 24.74% | 6.21% | 8.95% |

On these T1-T3 census metrics alone, the four ablations cluster within roughly a 0.5pp band of
each other — none of the four cards shows a dramatically different marginal contribution to raw
early engine access. **The real differentiation between the four cards is NOT in this table** —
it's in section 3 (Neoform's verified, non-overclaimed topology contribution), section 5 (Talion's
incremental vs. Seedborn's rung-creating Pod value), and section 7 (Speaker winning the reactive-
slot screen outright). Whether-card-is-redundant / whether-removal-breaks-conversion-graph:
Speaker is the least redundant (phase_0's own clean win); Neoform is not redundant (E1's near-zero
cost makes it a clear keep even before topology is considered); Talion and Seedborn are each
real-but-narrow, unverifiable-in-full contributions per section 5/6.

## 9. Confidence / remaining uncertainty

- **High confidence:** Phase 0's Commandeer selection (>1pp margin, n=15,000/4,000); E1's Elves→
  Neoform trivial-cost finding (n=15,000/8,000); E2's INT-0012 verification and the Neoform
  anti-overclaim check (exact, no sampling); E4's 4→5 dead-end finding (exact — zero MV5 creatures
  in the 98-card list is a programmatically-confirmed fact, not a sampled estimate).
- **Moderate confidence:** the census-level B0/B1/B2/B3 comparative deltas in sections 2 and 8
  (n=15,000 each, sufficient to resolve the ~1pp differences discussed).
- **Low confidence / explicitly unmeasured:** E2's "zero newly-winning states" result is from a
  BOUNDED, non-exhaustive sample (2-3 instances per family) — it should not be read as "the
  package never unlocks a new win," only as "not found in this specific bounded check." The
  paired flip-rate metrics in section 2 (noisy, same-seed-not-same-hand). All of E3 (post-fight
  conversion) and E5/E6 (late-draw quality, engine-behavior tagging) — genuinely not measured.
- **Structurally unmeasurable in this project's current engine, not merely low-confidence:**
  Talion's real opponent-cast trigger rate and Seedborn Muse's real value once resolved. Both
  require actual opponent turns, which this project's solo/no-opponent T1-3 goldfish engine has
  never simulated (the same standing gap MULL-006's own "Recommended Next Research" section
  already flagged as the project's largest open item: real 4-player pod-conditioned matchup
  simulation). This is why Talion and Seedborn specifically are marked
  INCONCLUSIVE_NEEDS_POD_VALIDATION rather than adopted or rejected on the evidence here.

## 10. Decision matrix

| Variant | Early speed | Mulligan quality | Interaction density | Conversion graph density | Protected win conversion | Pod quality | Late-draw quality |
|---|---|---|---|---|---|---|---|
| B0_BASELINE | baseline | baseline (keep_7=51.2%) | baseline (Commandeer weakest link) | baseline; 4→5 Pod rung dead | not measured (E3) | 1/4 rungs dead | not measured (E5) |
| B1_ENGINE_SWAP | ≈ baseline (trivial deltas) | ≈ baseline | unchanged | not separately topology-tested | not measured | not separately tested | not measured |
| B2_CONVERSION_SWAP | modest + (T2 engine +1.3pp) | keep_7 -1.3pp (worse) | Commandeer→Speaker (net + per phase_0) | 0 newly-winning in bounded E2 sample | not measured | not separately tested | not measured |
| B3_FULL_PACKAGE | modest + (T2 engine +1.6pp) | keep_7 -1.5pp (worse) | net + (Speaker in, Commandeer out) | 0 newly-winning in bounded E2 sample | not measured | 4→5 rung created, 3→4 widened | not measured |
| B4_NO_NEOFORM | ≈ B3 (97-card thinning confound) | not measured | ≈ B3 minus Neoform's own (trivial) value | Neoform's specific verified-anti-overclaim contribution lost | not measured | unaffected (Neoform isn't a Pod target) | not measured |
| B5_NO_SPEAKER | ≈ B3 (thinning confound), slightly lower than B4/B6/B7 | not measured | loses phase_0's clean-win card | untested by E2 (Speaker not a Pod-topology piece) | not measured | unaffected | not measured |
| B6_NO_TALION | ≈ B3 (thinning confound) | not measured | unaffected | unaffected | not measured | 3→4 rung reverts to 4 targets (B0 level) | not measured |
| B7_NO_SEEDBORN | ≈ B3 (thinning confound) | not measured | unaffected | unaffected | not measured | 4→5 rung reverts to dead end | not measured |

**Final decision category: ADOPT_PARTIAL_PACKAGE** (Formidable Speaker via Commandeer, and
Neoform via Elves of Deep Shadow — both clean, low-risk, evidence-backed changes) **+
INCONCLUSIVE_NEEDS_POD_VALIDATION for Talion and Seedborn Muse specifically** (real, measured
structural contributions exist; their actual gameplay value cannot be assessed by this project's
current solo engine at all, and would require real multiplayer pod data, not a larger solo
simulation, to resolve).
