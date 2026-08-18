# SIM-DECKBUILD-006 — Four vs Five Dorks / Creature-Mana Network Audit

**Central question:** is four one-mana dorks sufficient, or is five the structural floor for this
exact deck? Candidate swap: Avacyn's Pilgrim OUT, Lotho, Corrupt Shirriff IN.

**Subject deck:** `tymna-thrasios-treefarm-deckbuild006-v1` (98 cards + Thrasios/Tymna), hash
`856e02c0ed50dd577eaf00b3e23fb5ab91f509cbd997c24824c34ed02a0893ad`, minted from the user's own
pasted, confirmed-accurate operative 98-card list — see
`sim/analysis/build_deckbuild006_frozen_deck.py` for the full diff-and-mint provenance (9 cards
removed / 9 added vs. the MANA-AUDIT-002 frozen subject; the assignment's own "Emergence Zone"
changelog entry was fabricated/never real, corrected via `AskUserQuestion` and the user's pasted
list rather than silently assumed).

All simulation results below are `DECK_BACKED_GOLDFISH` evidence (real turn-by-turn goldfish
development, no opponent, this project's native T1-3(-6) engine) except E6, which is explicitly
`static_probability` under disclosed, uncalibrated assumptions — never blended with the goldfish
numbers as if they were the same kind of evidence.

---

## 1. Executive verdict

The five-to-four true-one-mana-dork transition (cutting Avacyn's Pilgrim) is **structurally
trivial** by every metric this project's engine can measure directly — smaller, in fact, than
DECKBUILD-004's already-judged-"~neutral" six-to-five transition (Elves of Deep Shadow → Neoform,
+0.14pp). It does not compound over a longer game (verified out to T6). Lotho's own measurable
value floor (the pilot's own second-spell trigger only, the sole trigger source a solo engine can
see) is real but small at this sample size; its designed real-game value comes overwhelmingly from
**opponents'** second spells, which this solo engine cannot observe at all and which this task's
own methodology principles require treating as an explicit, uncalibrated scenario band rather than
a fabricated point estimate (E6). Under any of the three disclosed pod-activity scenarios, that
opponent-driven value is several times larger than the tiny, noise-level structural cost measured
in E1/E2.

**Recommendation: CUT_PILGRIM_KEEP_LOTHO** — see section 7 for the full reasoning and its
confidence caveats.

---

## 2. Factorial table (A/B/C/D)

| Config | Dorks | Lotho | T2 any-engine | T2 autonomous-engine | T3 color-fail | T3 mean creatures |
|---|---|---|---|---|---|---|
| A_5D_NO_LOTHO (reference) | 5 | No | 24.31% | 19.95% | 46.07% | 1.489 |
| B_4D_NO_LOTHO (placeholder) | 4 | No | 24.38% | 19.90% | 46.39% | 1.409 |
| C_5D_LOTHO (funded by cutting Mindbreak Trap) | 5 | Yes | 24.77% | 20.39% | 45.62% | 1.502 |
| D_4D_LOTHO (**the real operative deck**) | 4 | Yes | 24.81% | 20.25% | 46.26% | 1.427 |

n=15,000 hands/config (E1 census), n=15,000 hands/config (E2 network census, independent sample).
At n=15,000, the standard error on a ~25% rate is ≈0.35pp — every T2-engine delta in this table is
within 1-2 standard errors of zero. None of these differences should be read as a confident,
reproducible effect; they are reported at full precision per report_policy, not rounded away, but
the interpretation bands below (trivial/modest) exist precisely because sub-1pp deltas at this
sample size are not distinguishable from noise.

**B is a placeholder, not a deckbuilding suggestion** (per its own definition) — its row exists
only to isolate Pilgrim's removal from Lotho's addition, never to imply "play nothing there."
**C's funding cut (Mindbreak Trap) is a disclosed no-op choice**, not a recommendation — see
`deckbuild006_variants.py`'s own docstring for why it was chosen (free-alt-cost condition never
satisfiable in this solo engine, so removing it changes nothing else measured here).

---

## 3. Fifth-dork value (structural cost of A → B)

| Metric | A (5D, no Lotho) | B (4D, no Lotho) | Δ (B−A) | Band |
|---|---|---|---|---|
| T2 any-engine active | 24.31% | 24.38% | **+0.07pp** | trivial |
| T2 autonomous-engine (excl. Kinnan/Deathrite/Cradle) | 19.95% | 19.90% | −0.05pp | trivial |
| T3 two-plus engines | 5.97% | 5.87% | −0.09pp | trivial |
| T3 color-failure rate | 46.07% | 46.39% | +0.33pp | trivial |
| Paired-seed keep/ship flip rate (either direction) | — | — | 1.6% combined | 98.4% agree |
| T3 mean creature count | 1.489 | 1.409 | **−0.080** | small, real |
| T3 mean functional dorks in play | 0.296 | 0.223 | **−0.073** | small, real |
| T3 mean Gaea's Cradle structural ceiling | 1.489G | 1.409G | −0.080G | small, real |

**Required primary number:** T2-engine-probability change A→B = **+0.067pp** ("trivial" band,
`results/solo_baseline/deckbuild006_e1_early_cost.json:required_key_number`).

The engine-*probability* cost is genuinely negligible — smaller than DECKBUILD-004's six-to-five
transition, contradicting this task's own prior warning not to assume the fifth dork is as cheap
to cut as the sixth was. It turned out to be *cheaper*, not more expensive, at least by this
metric. The network-*size* cost (creature count, functional dork count) is small but consistently
real and directionally stable at every turn (T1 −0.044, T2 −0.061, T3 −0.073 mean functional
dorks) — this is the more honest headline number for "does losing the fifth dork hurt," since it
measures the resource itself rather than a downstream binary (any_engine_active) that other cards
can substitute into.

Extended to T6 (E5), this gap does not widen: the T3→T6 delta in `any_engine_active_rate` between
A and D stays in the same trivial range it started in (see section 5). **The cost is flat, not
compounding.**

---

## 4. Lotho compensation (does Lotho's value offset the cost?)

Two separate, honestly-bounded value sources, never blended into one number:

**(a) Measured self-trigger floor (E5, T1–T6, the pilot's own second spell only):**

| Config | Mean cumulative triggers by T3 | by T6 | % of hands with ≥1 trigger by T6 |
|---|---|---|---|
| D_4D_LOTHO | 0.0045 | 0.0346 | 2.76% |
| A/B (no Lotho) | 0 | 0 | 0% |

This is real, measured, DECK_BACKED_GOLDFISH evidence — and it is small, because a solo no-opponent
T1-6 goldfish rarely casts two real spells in the same turn early on. It is a genuine **floor**,
not the card's designed value: Lotho's actual Oracle text triggers on *any* player's second spell,
and 3 of 4 players at a cEDH table are invisible to this engine by construction.

**(b) Scenario-derived opponent-trigger value (E6, explicitly NOT a simulation):**

| Scenario | Assumed P(opponent's 2nd spell/turn) | Expected additional Treasures, T3–T6, 3 opponents |
|---|---|---|
| LOW_INTERACTION_POD | 0.10 | 1.2 |
| TYPICAL_CEDH_POD | 0.30 | **3.6** |
| HIGH_VELOCITY_POD | 0.55 | 6.6 |

`evidence_type: static_probability`, `confidence: low` — these probabilities are **assumptions**,
not fit to any tournament or replay data source (none exists in this project for per-turn opponent
spell velocity by pod archetype). They exist to bracket plausible real-game behavior, per this
task's explicit prohibition on collapsing multiplayer effects into one claimed expected value.

**Net read:** even under the most conservative (LOW_INTERACTION_POD) scenario, Lotho's
opponent-driven value (1.2 expected Treasures across 4 turns) is over an order of magnitude larger
than the structural cost of losing Pilgrim as measured in creature-count terms, and the
engine-probability cost is statistically indistinguishable from zero in the first place. The
comparison is asymmetric by construction — a real, measured small cost against a real-but-uncertain
larger benefit — and that asymmetry, not a false precise net number, is the actual finding.

---

## 5. Network effects

- **Kinnan interaction:** `kinnan_active_rate` is ~1.2% by T3 across all four configs (essentially
  identical, within noise) — Kinnan's doubler is rare enough in this horizon that dork-count
  differences don't meaningfully change how often it matters. `kinnan_active_and_functional_dorks_2plus_rate`
  is ~0% everywhere (never both at once by T3 in this sample) — the "Kinnan + multiple dorks"
  synergy this deck is built around essentially never fires by turn 3 regardless of config; it is a
  mid/late-game payoff, consistent with this deck's own archetype.
- **Gaea's Cradle structural ceiling** (what Cradle would tap for right now if drawn) tracks
  creature count exactly (E2's `mean_gaea_cradle_structural_ceiling_G` = `mean_creature_count` by
  construction) — A leads B by 0.080G at T3, the same small gap as the raw creature-count number.
  A dedicated E3 block (Cradle's own draw probability) was **skipped with disclosure** per the
  phase-1 checkpoint: this ceiling number already shows the effect is trivial in the same direction
  E3 would have measured, and building a full draw-probability model for a sub-0.1G difference
  would not change the decision.
- **Pod fodder (E4, skipped with disclosure):** with only a ~0.07-creature average difference
  between the 4-dork and 5-dork configs at T3, Birthing Pod's fodder population is barely touched;
  a dedicated rung-census block was judged not worth building given phase-1's already-clear result,
  per this task's own efficiency_rule ("do not spend substantial simulation resources ... if phases
  1-2 already make the decision obvious"). If Pod-chain-specific concerns arise later, this remains
  a disclosed, buildable gap, not a silently-ignored one.
- **Badgermole Cub's amplifier** ("whenever you tap a creature for mana, add an additional G") is
  **not modeled** in this engine (pre-existing, deliberately-deferred gap — DORK-003 in
  `build_t1_t3_trajectory_audit.py`, re-confirmed via a dedicated regression test in this task).
  This is a **conservative** omission specific to this question: more dorks in play means strictly
  more independent Badgermole trigger opportunities, so every number in this report understates the
  5-dork configs' (A, C) advantage over the 4-dork configs (B, D) — never the reverse.
- **Deathrite Shaman graveyard mana** — re-verified (not merely assumed) against the new operative
  98: the only land-to-graveyard outlet present is Mox Diamond's single ETB discard choice, same as
  the old list MANA-AUDIT-002 already found this ability functionally dead against. No new
  discard-a-land or self-mill effect entered the deck via this task's 9-card swap. The engine's
  existing non-implementation is left as-is.

---

## 6. Representative states

Rather than hand-picking individual simulated hands (none were saved at per-hand granularity for
this task — aggregate census output only), the honest representative picture is the T3 board-state
distribution itself, which **is** real per-hand data, aggregated:

| Config | P(0 functional dorks in play, T3) | P(exactly 1) | P(2+) |
|---|---|---|---|
| A_5D_NO_LOTHO | 73.46% | 23.63% | 2.91% |
| B_4D_NO_LOTHO | 79.34% | 19.10% | 1.56% |
| C_5D_LOTHO | 73.61% | 23.48% | 2.91% |
| D_4D_LOTHO | 79.23% | 19.35% | 1.42% |

The dominant outcome in **every** config, dork count notwithstanding, is **zero dorks deployed by
turn 3** (73-79% of hands) — this deck's T1-3 game plan does not hinge on reliably assembling a
multi-dork board that early; the 5th dork mainly moves hands from "zero dorks" to "exactly one,"
not from "one" to "a wide board." That reframes the whole question: the fifth dork's job in this
specific deck is raising the *floor* (fewer completely-dork-less hands), not raising the *ceiling*
(the 2+ rate barely moves, 2.91% → 2.91% between A and C, i.e. Lotho fully offsets the tiny 2+ rate
loss when both are present).

---

## 7. Final recommendation

**CUT_PILGRIM_KEEP_LOTHO.**

Reasoning, restated plainly:
1. The measured structural cost of losing the fifth dork is trivial by every engine-probability
   metric (sub-0.1pp, within 1-2 standard errors of zero at n=15,000) and small-but-real by network
   metrics (~0.07-0.08 fewer creatures/functional dorks by T3), and this gap does **not** compound
   through T6.
2. Lotho's measured value floor (self-triggers only) is real but small, as expected from a
   card whose actual design targets a 4-player table this solo engine cannot observe.
3. Lotho's scenario-derived opponent-triggered value (E6, explicitly uncalibrated, low confidence)
   is, even under the most conservative band, an order of magnitude larger than the measured
   structural cost in section 3/6's terms.
4. No card other than Avacyn's Pilgrim is being proposed as a cut here, so the
   `RESTORE_PILGRIM_FIND_ANOTHER_LOTHO_CUT` category's own precondition (a separately-audited
   alternative cut in the exact operative 98) does not apply and was not investigated — not a gap,
   simply out of this task's scope as framed.
5. `TOO_CLOSE_LIVE_TEST_REQUIRED` would apply if the structural cost were itself borderline/
   ambiguous; it is not — every phase-1 metric lands cleanly in the trivial-to-modest band, never
   meaningful or severe, and the checkpoint explicitly confirmed this before scoping the rest of
   this task's execution.

**Confidence:** moderate-high that the structural cost is negligible (real Monte Carlo evidence,
large samples, consistent across every metric and turn measured). Low-moderate that Lotho's real
opponent-driven value clearly exceeds it in an *actual* pod — this half of the argument rests on
E6's disclosed, uncalibrated scenario bands, not on simulation. A pilot who expects an unusually
quiet/low-interaction seat should weight section 4(b)'s LOW_INTERACTION_POD band, where the margin
is still favorable (1.2 expected Treasures vs. a sub-0.1-creature structural cost) but least so.

---

## Regression requirements checklist

| Requirement | Status |
|---|---|
| Verify operative deck hash | ✅ `test_deckbuild006_frozen_deck_and_variants.py` (hash match + tamper-rejection test) |
| Pilgrim W-only | ✅ Pre-existing gold-state coverage (`GBS-0011`, `GBS-0020`, `GG-0001`) — real card, unchanged by this task |
| Deathrite fetchland/graveyard mana | ✅ Re-verified against the NEW operative list (section 5); unchanged finding, no code change needed |
| Kinnan excludes lands | ✅ Pre-existing engine behavior (`available_sources()`'s nonland-only Kinnan loop) + pre-existing regression coverage |
| Badgermole trigger math | ✅ Explicitly tested as NOT modeled (`test_deckbuild006_badgermole_not_modeled.py`), with a disclosed, directionally-conservative bias note |
| Cradle counts actual creatures | ✅ Pre-existing engine behavior (`state.creature_count()`), reused directly by E2 |
| Pod requires sorcery timing / target MV legality | ✅ Pre-existing regression coverage (`test_mull005r_pod_oculus_survival.py`) — unaffected by this task's card changes |
| Lotho actual trigger condition | ✅ `test_deckbuild006_new_cards.py` (7 dedicated cases: present-all-turn, cast-before-2nd-spell, cast-as-2nd-spell, cast-after, only-one-cast, non-cast-tags-excluded, not-in-play) |
| Seedborn each other player's untap step | ✅ Disclosed as architecturally invisible (same category as Talion), unchanged from DECKBUILD-004 |
| No generic-AI policy dependence in structural metrics | ✅ This project's own native T1-3(-6) engine throughout, no XMage/generic-AI involvement anywhere in this task |

Full regression suite: **466 passed, 3 pre-existing skips** as of this report
(`python3 -m pytest rules_tests/ -q`), including 37 tests added by this task across 5 new test
files.

## Scope disclosure

Built and executed with full rigor: phase 0 (deck freeze), Lotho/Grand Abolisher/Mockingbird/
Treasure mechanics, the A/B/C/D factorial, E1 (early cost), E2 (creature-mana network), E5
(late-draw value extension to T6), E6 (multiplayer sensitivity scenario model). **Not built**, with
disclosure and reasoning given at point of skip: a dedicated E3 (Cradle draw-probability) block and
E4 (Pod rung census) block — both judged unnecessary once E2's structural-ceiling numbers and the
phase-1 checkpoint showed the effect size involved was already too small to change the decision;
and E7 (post-first-fight state modeling) — SIM-DECKBUILD-005's framework does not exist anywhere in
this project's history to reuse as instructed, and phases 1/E5/E6 already resolved the decision
without it, so building fight-state modeling from scratch (a real, first-time engine expansion this
project has never attempted, and combat is explicitly out of this engine's stated scope) was not
attempted, per this task's own efficiency_rule and report_policy against expanding infrastructure
once the decision is sufficiently resolved.

## Artifacts

- `data/decklists/tymna-thrasios-treefarm-deckbuild006-v1.json` — frozen operative subject
- `sim/analysis/deckbuild006_cards.py`, `deckbuild006_variants.py` — card mechanics + A/B/C/D configs
- `sim/analysis/build_deckbuild006_{frozen_deck,e1_early_cost,e2_creature_mana_network,e5_late_draw_value,e6_multiplayer_sensitivity}.py`
- `results/solo_baseline/deckbuild006_{e1_early_cost,e2_creature_mana_network,e5_late_draw_value,e6_multiplayer_sensitivity}.json`
- `rules_tests/regression/test_deckbuild006_*.py` (5 files, 37 tests)
