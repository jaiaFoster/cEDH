# SIM-ROGFARM-001 — Report B (Stage 2: Paired Opening-Hand / T1–T3 Monte Carlo + Gate Decision)

**Decision: STOP — `ROG_FARM_FALSIFIED_OR_REDESIGN`.** R1 Minimal Rog Farm clearly fails 3 of the
5 Section 9 falsification gates under every one of the 3 pre-registered mulligan policies (4/5
under P1 and P3, 3/5 under P2), well past the "≥2 clear failures" stop rule. Per the assignment's
own instruction ("Do not proceed to wheel simulations merely because the archetype is
interesting"), this task does **not** continue into the mechanism ablations or Stage 3's
controlled wheel-state laboratory.

---

## Method

Deck hashes (frozen, hash-verified before this run — `sim/analysis/rogfarm001_variants.py`):

| Deck | Hash |
|---|---|
| Stock RogSi | `535bde31b8c7d0aefe9700650fe4549558c7b50632f56e310aa551878460ca56` |
| R1 Minimal Rog Farm | `e8aaed0c97d002ab29c0d3cf684b79f0441e49087aca4ea88797208a303a51d8` |
| Blue Farm Control | `c08cc939993b28f2b3a69ec23e2c69fa2c9577769506ce71c77e3d0a1c3fe959` |

50,000 paired T1–T3 opening sequences per deck × per policy (450,000 trials total; common random
numbers via seed = trial index, applied independently per deck so each trial index draws from the
same "fortune tier" across decks). Three pre-registered policies (`rogfarm001_mulligan_policies.py`):
**P1 ENGINE_FORWARD**, **P2 BALANCED**, **P3 TURBO_RESPECTFUL** — each a disclosed rule-based
heuristic operationalizing the assignment's own literal Section 6 priority lists (not a claim of
machine-optimal play), with multiplayer free mulligan + card-dependent London bottoming.

Two deterministic combos registered via the engine's existing generic combo-status
infrastructure (`opening_hand_metrics.snapshot_metrics`'s `combo_status`/`deterministic_win_available`,
no new combo-checking code needed): **THORACLE** (Thassa's Oracle + Demonic Consultation/Tainted
Pact — Stock/Blue Farm only, absent from R1 by construction) and **BREACH_LOOP** (Underworld
Breach + Lion's Eye Diamond + Brain Freeze — piece-access only; the loop's own infinite-iteration
math is separately validated in `rogfarm001_breach_loop.py`/its 18 regression tests, not
re-simulated per opening hand).

**Scope disclosure (Tier B solo/no-opponent model):** the wheel-opportunity metric checks wheel
castability + a real asymmetry mechanism (payoff **already on the battlefield**, not merely in
hand) + sufficient mana + retained interaction as a protection proxy. It does **not** verify
Section 8 point 6 ("wheel outcome not obviously improving opponents more than us") — that requires
actual opponent states and is Stage 3's job, never reached here. Interaction-readiness numbers are
understated across all three decks: this engine's generic greedy loop casts any castable
interaction card immediately rather than holding it up reactively (a pre-existing, disclosed
engine limitation, not something introduced for this task) — the loop reports "cards remaining
live" *after* the loop's own proactive spending, not "cards a human would have held."

---

## Primary table (Report B format, Section 24)

Values shown are **P2_BALANCED** (the primary policy for the headline decision — the middle-ground
policy among the three pre-registered options); the full per-policy breakdown follows below since
the direction of every non-trivial finding is materially the same or worse under P1/P3.

| Metric | Stock RogSi | R1 Rog Farm | Blue Farm |
|---|---|---|---|
| T2 engine online | 45.8% | 47.7% | 37.5% |
| Protected T2 engine (engine + live interaction, ever by T2) | 14.3% | 15.0% | 10.9% |
| T2 engine + interaction (same-turn) | — | 15.0% | — |
| T3 defensive readiness (has live interaction) | 7.2% | 7.8% | 7.6% |
| Protected asymmetric wheel by T3 | 0.00% | **0.02%** | 0.00% |
| Identity-card stranded rate (per card seen, R1's 6 identity cards) | N/A (runs none) | **45.5%** | 90.0%¹ |
| Meaningful mana/color failure (kept hands) | 8.9% | 8.0% | 6.7% |
| Earliest credible deterministic win by T3 | ~0.01% (both) | ~0.01% | 0.00% |
| Oracle-redundancy loss rate | 0.00% | n/a (no Oracle pkg) | n/a |
| Mean mulligans to keep | 1.66 | 1.50 | 1.19 |

¹ Blue Farm's figure is inflated by a disclosed model artifact, not a real archetype finding — see
"Conditional burden" below.

---

## Gate-by-gate (P2_BALANCED; P1/P3 in the appendix table)

| Gate | Threshold | R1 result | PASS/FAIL |
|---|---|---|---|
| 1. Engine advantage | Protected T2 ≥ Blue Farm +7pp, OR (T2 engine ≥ Blue Farm +10pp AND interaction not >5pp worse) | Protected +4.06pp (miss path A); T2 engine +10.22pp with interaction +0.15pp (clears path B) | **PASS** (narrow) |
| 2. RogSi defensive retention | Interaction readiness no worse than Stock by >5pp | +0.58pp (R1 slightly *better*) | **PASS** |
| 3. Conditional burden | Identity stranded-card rate no worse than Stock by >4pp | +45.47pp (Stock's baseline is structurally 0 — R1 runs cards Stock doesn't) | **FAIL** |
| 4. Mana | Kept-hand meaningful mana/color failure <5%, and no worse than Stock by >3pp | 8.0% absolute (exceeds the 5% ceiling; the relative delta vs. Stock is actually −0.86pp, i.e. R1 is mana-*safer* than Stock) | **FAIL** |
| 5. Wheel emergence | Protected asymmetric wheel by T3 ≥ 12% of kept hands | 0.02% | **FAIL** |

**Fail count: 3/5 → stop rule triggered** (≥2 required). Under P1 and P3, gate 1 also fails
(protected-engine deltas of only +3.19pp and +1.70pp, engine deltas of +7.88pp and +4.49pp — never
clearing +10pp), giving 4/5 failures there. **R1 fails the stop-rule threshold under every single
pre-registered policy**, not just the primary one — this is not a policy-selection artifact.

---

## What the numbers actually say

**Gate 1 (engine advantage) is the one genuinely close, policy-sensitive result**, and it leans
mildly *in R1's favor*: replacing Oracle/Consult/Pact/Strike It Rich/Final Fortune/Dramatic
Reversal with Faerie Mastermind/Narset/Notion Thief/Force of Negation/Foil/Subtlety does measurably
speed up "an engine is on the battlefield by T2" — a real, if narrow, effect. The thesis's *first*
claim (deploy a persistent engine unusually early) has partial support.

**Gate 2 (defensive retention) is a clean pass in all three policies.** R1 does not trade away
interaction to gain its engine — a genuine, non-trivial finding given the deckbuilding intuition
that "more engine slots" usually costs something. This partially clears the thesis's second claim.

**Gate 3 (conditional burden) fails by a wide margin (41–42pp over the 4pp threshold in every
policy).** Roughly 44–46% of R1's own identity-package cards, when drawn, sit uncastable/unused
through T3. Caveat: part of this is a disclosed model artifact, not a novel archetype finding —
Force of Negation's real alternate cost ("if it's not your turn") is structurally unverifiable in
this solo, no-opponent model (`interaction_model.py` already marks it `structurally_unavailable`,
a pre-existing limitation from an earlier task, not introduced here), so it is measured only at its
expensive {3}{U}{U} hardcast floor and strands very often — this is *also* why Blue Farm's own
Force of Negation copies show an even higher 90% stranded rate despite that card being an
independently-justified staple there, unrelated to any "Rog Farm identity package" framing. Even
setting Force of Negation aside, though, Foil (needs an Island-type card plus a second card, or
{2}{U}{U}) and the three wheel-payoff creatures (real bodies, castable whenever mana allows) are
genuinely conditional-to-variable-value adds compared to the raw acceleration/rituals they
displaced — the qualitative direction of this finding (R1's package carries real conditional
burden) survives the caveat even if the exact magnitude is inflated by one card's known-unmeasurable
mechanic.

**Gate 4 (mana) fails on the assignment's absolute <5% ceiling, not on R1 being worse than
Stock — R1 is measurably *better* than Stock on this exact metric in every policy** (deltas of
−0.05, −0.86, and −1.05pp). Both RogSi variants exceed the 5% absolute ceiling; this reads as a
property of the archetype's demanding UB/UUU-ish requirements generally (real for a Grixis
combo-control shell running this much colored-mana-hungry interaction), not a defect specific to
R1's added package.

**Gate 5 (wheel emergence) is the clearest, largest, most policy-invariant failure: 0.00–0.04%
against a 12% target.** This is the core of the falsification. The compound state Section 8
requires (wheel castable + a real asymmetry mechanism already deployed + sufficient mana + retained
interaction, all simultaneously, by T3) essentially never occurs in a 3-turn window for any of the
three decks tested — wheels cost 3–4 mana and a payoff creature/planeswalker needs to already be
on the battlefield ahead of it. Whether this is "genuinely rare" or partly a "T3-horizon floor
effect that would resolve by T4–T5" cannot be distinguished from this stage alone; either reading
still falsifies the specific claim under test ("R1 creates a genuinely asymmetric wheel state" as
a T1–T3-relevant, reproducible mechanism) — a wheel-control identity whose signature play almost
never becomes available within the game's opening third is not the mechanism its own deckbuilding
thesis describes.

**Oracle-redundancy loss is uninformative at this horizon** (0.00% for Stock across every policy)
— the Thoracle combo essentially never reaches full assembly-and-payability by T3 in this Monte
Carlo, so R1's removal of that package cannot be shown to cost anything *specifically within a
3-turn window*; this metric would need a longer horizon (Stage 3/4) to say anything real, and is
reported here as a disclosed null result, not evidence for or against R1.

---

## Appendix: full per-policy gate table

| Gate | P1 ENGINE_FORWARD | P2 BALANCED | P3 TURBO_RESPECTFUL |
|---|---|---|---|
| 1. Engine advantage | FAIL (path A +3.19pp, path B +7.88pp/+10 needed) | **PASS** (path B, narrow) | FAIL (path A +1.70pp, path B +4.49pp) |
| 2. Defensive retention | PASS (+0.28pp) | PASS (+0.58pp) | PASS (+0.14pp) |
| 3. Conditional burden | FAIL (+44.05pp) | FAIL (+45.47pp) | FAIL (+46.22pp) |
| 4. Mana | FAIL (5.20% abs., −0.05pp rel.) | FAIL (7.99% abs., −0.86pp rel.) | FAIL (16.08% abs., −1.05pp rel.) |
| 5. Wheel emergence | FAIL (0.04%) | FAIL (0.02%) | FAIL (0.02%) |
| **Fail count** | **4/5** | **3/5** | **4/5** |

---

## Provenance

- Harness: `sim/analysis/build_rogfarm001_stage2_harness.py` (450,000 trials, ~200s/50,000-trial
  deck×policy batch).
- Gate evaluator: `sim/analysis/build_rogfarm001_stage2_gates.py` — exact Section 9 thresholds
  recovered **verbatim** from the pre-compaction session transcript (not reconstructed from
  memory, per the assignment's own explicit prohibition on reconstructing its own specification).
- Raw results: `results/solo_baseline/rogfarm001_stage2_results.json`.
- Gate results: `results/solo_baseline/rogfarm001_stage2_gates.json`.
- 38 new regression tests covering the mulligan policies, the deck-scoping/dispatch-visibility bug
  found and fixed while smoke-testing the harness, and all 5 gate formulas against synthetic data
  (`rules_tests/regression/test_rogfarm001_{cards,mulligan_policies,stage2_gates}.py`).
- A real unit-mismatch bug in `identity_card_stranded_rate` (conflating "mean stranded cards per
  hand," which can exceed 1.0, with a true [0,1] rate) was caught while reading this run's first
  gate output and fixed before this report was finalized — see
  `build_rogfarm001_stage2_harness.py`'s `aggregate()` docstring note. The numbers in this report
  are from the corrected rerun.

---

## Final classification

Per Section 27: **`ROG_FARM_FALSIFIED_OR_REDESIGN`**. The brew has not demonstrated the specific,
reproducible wheel-control mechanism its own thesis describes within the T1–T3 window this stage
tests — engine-timing and defensive-retention both show real, if modest, support, but the
conditional burden of R1's own identity package and (most importantly) the near-total absence of
the archetype's signature "protected asymmetric wheel" state make the current R1 build
non-viable as specified. This does **not** mean wheel-control-RogSi is impossible — a redesign
that (a) reduces the conditional-burden load (e.g., a lighter wheel-payoff package, or swapping
Force of Negation for a card whose alt cost this solo model can actually verify would need
re-testing to confirm) and (b) finds a way to reach a real protected-wheel state faster than T3
would need a fresh PASS 1/PASS 2 cycle under a new deck version, per the assignment's own
versioning rule — not a patch to this run.
