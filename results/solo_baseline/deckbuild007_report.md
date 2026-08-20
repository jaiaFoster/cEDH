# SIM-DECKBUILD-007 — Current 101 Validation, Acceleration Audit, and Final Cut

**Subject:** `tymna-thrasios-treefarm-deckbuild007-v1` (99 main-deck cards + Thrasios/Tymna), hash
`ab704e30d1e660eca99e6dbf8cf2091e6c8906e8d817ea3c45289fca5c4c1d82`. Diff vs the prior frozen
subject: −An Offer You Can't Refuse / −Shang-Chi, Master of Kung Fu / −Training Grounds,
+Biomancer's Familiar / +Birthing Ritual / +Dark Ritual / +The Cabbage Merchant.

---

## 1. Blockers / important limitations

- **No true blockers** — all runnable work completed.
- **Mandatory correction applied, not merely verified:** the assignment's claim ("sacrificed
  fetchland → graveyard → Deathrite can exile it → one mana of any color") was checked against two
  independent web sources plus real competitive-Magic precedent (Legacy/Modern Jund decks run
  heavy fetches specifically to fuel Deathrite Shaman) and confirmed correct. Prior project
  modeling (MANA-AUDIT-002, DECKBUILD-006) had this wrong — it's now fixed at the core-engine level
  (`opening_hand_policy.py`), so every future task's simulations inherit the fix automatically, not
  just this one.
- **Badgermole Cub's creature-mana amplifier remains unmodeled** (a pre-existing, previously-
  disclosed engine gap — a real change with a documented correctness risk, not attempted again
  here). Conservative for every finding in this report that touches creature-mana density: real
  play only gets MORE value from more dorks/creatures than measured.
- **No opponent/combat/stack model exists in this engine.** Workstream 3's "post-fight states" are
  hand-built resource snapshots (a structured grid), not derived from a simulated fight; Lotho/
  Cabbage Merchant/Talion's opponent-triggered value is modeled via explicit, labeled, uncalibrated
  scenario bands (`evidence_type: static_probability`, confidence: low) — never blended with the
  real Monte Carlo goldfish numbers as if they were the same kind of evidence.
- **Carpet of Flowers metagame grounding is directional, not a decklist census** — per the
  assignment's own "do not over-research" instruction, its scenario bands are grounded in the
  well-established, stable fact that blue is cEDH's single most staple-dense color (not a specific
  2026 tournament sample), plus the real rules fact that original dual lands with the Island type
  count toward its trigger, not just basic Islands.

---

## 2. Executive verdict

**Is the current architecture aligned with the target strategy?** Yes, directionally. Workstream 3
found P(convert | Pod present) = 44.7% vs. P(convert | Pod absent) = 9.0% — Pod is clearly one of
the strongest conversion routes without the deck being purely dependent on it (a real, nonzero
non-Pod conversion rate exists via other engines/tutors). The 4→5 Pod rung is re-confirmed
Seedborn-Muse-unique in the new 101, exactly as before.

**Dark Ritual, Carpet, both, or neither?** **Neither, as currently built** — but not because either
card is broken. Dark Ritual's measured contribution to the four named premium-engine timings is
real but negligible (0.22% purposeful-use rate at n=25,000; every T2/T3 timing delta vs. removing
it is under 0.1pp). Carpet of Flowers is not in the current 101 and this task did not find a
compelling case to add it either: its own cast rate is low (≤8.5% on the battlefield by T4) and its
mana output is real only when BOTH it resolves AND an opponent has a qualifying Island-typed land —
a double-conditional that keeps its population-wide expected value small even in the TYPICAL-pod
band. Dark Ritual is this report's **weakest-marginal-value finding with the most direct
quantitative support** — see the final-cut ranking (section 5).

**Which experimental cards are earning their slots?** Biomancer's Familiar (a real, immediate,
unconditional cost reduction, functionally identical to the Training Grounds it replaced, with more
delivery roles as a creature) and Birthing Ritual (a real, if nondeterministic, repeatable value
engine — 88% mean any-hit rate, 21% mean premium-target rate across its four rungs) are both
carrying their weight. The Cabbage Merchant is real but structurally weaker than Lotho on both axes
this task could measure (exchange rate, volatility) — see card verdicts. Dark Ritual is the clear
laggard.

**Single recommended 101st-card cut: Dark Ritual.** See section 5 for the full ranking and
reasoning.

---

## 3. Key evidence table

| Metric | Value | Source |
|---|---|---|
| Dark Ritual purposeful-use rate (n=25,000) | 0.224% | WS1 |
| Dark Ritual mean stranded units when used | 1.70 / 3 | WS1 |
| Dark Ritual T2 delta vs. removed, all 4 targets | all < 0.1pp | WS1 |
| Carpet on-battlefield rate by T4 | 8.5% | WS1 |
| Carpet TYPICAL-pod expected mana if resolved, by T4 | ~2.1 | WS1 (scenario) |
| Birthing Ritual mean P(any legal hit) across 4 rungs | 88.1% | WS2 |
| Birthing Ritual mean P(premium target) across 4 rungs | 21.1% | WS2 |
| Biomancer's Familiar / Training Grounds reduction | functionally identical text | WS2 |
| Cabbage Merchant TYPICAL-pod expected mana, T3–T6 | ~2.03 | WS2 (scenario) |
| Lotho TYPICAL-pod expected mana, T3–T6 (DECKBUILD-006, reused) | 3.6 | DECKBUILD-006 E6 |
| Seedborn Muse extra mana before own next turn (4-player pod) | 3 × current mana base, exact | WS2 |
| P(convert \| Pod present) | 44.7% | WS3 |
| P(convert \| Pod absent) | 9.0% | WS3 |
| P(protected convert \| Pod present) | 27.6% | WS3 |
| Pod 4→5 rung, unique key-target hit rate | 100% (Seedborn only) | WS3 (re-verified) |
| Dominant failure mode across the WS3 grid | missing_outlet (54.8%) | WS3 |

All rates above n≥12,000 unless noted as a scenario band. Sub-1pp deltas are reported at full
precision but should be read as "trivial," not as confidently-directional effects (see
DECKBUILD-006's established interpretation-band convention, reused here).

---

## 4. Card verdicts

- **Birthing Ritual — KEEP.** A real repeatable value engine reachable off any creature sacrifice
  (88% any-hit, 21% premium across all 4 rungs); "grindy nondeterministic value" is a fair
  description of the median outcome, but the ceiling outcomes are real and it never fully whiffs
  (0% dead-rung rate across sac-MV 1–4).
- **Biomancer's Familiar — KEEP.** Functionally identical cost reduction to the Training Grounds it
  replaced, but delivered as a creature — more roles (Pod/Chord/Cradle fodder, tutor-accessible,
  live the turn it enters since the reduction is a static ability, not gated by summoning
  sickness). Carrying its slot.
- **Dark Ritual — CUT (see section 5).** Real, measured, and small: 0.22% purposeful-use rate for
  the four named premium-engine timings, with no material color-failure or engine-retention cost to
  removing it (T3 color-failure rate is actually 0.34pp LOWER — i.e. slightly better — with Ritual
  removed than with it present: 46.52% vs. 46.85%, a noise-level difference in the direction of "no
  cost to cutting it," not a reason to keep it). Highly redundant in an already-deep fast-mana
  category.
- **Lotho — KEEP.** Reuses DECKBUILD-006's own validated result: structural cost of the dork it
  replaced is trivial (+0.067pp T2-engine change), and its real value (opponent-triggered, scenario-
  modeled) is an order of magnitude larger than that cost even in the most conservative band.
- **Seedborn Muse — KEEP.** Deterministic, not scenario-dependent: 3 additional full mana-refresh
  events before the controller's own next turn in a 4-player pod, scaling with the existing mana
  base. Functions as both a near-term conversion accelerator and a long-game multiplier — not an
  either/or, and directly relevant to "survive the fight → convert" since its value starts at the
  very next opponent's untap step. Also the sole resolver of the confirmed-unique Pod 4→5 rung.
- **Talion — KEEP / LIVE TEST.** Uses this task's given default number (2) rather than a re-derived
  one; its trigger (an opponent casting a spell) remains architecturally invisible to this solo
  engine, same category as DECKBUILD-004's original INCONCLUSIVE_NEEDS_POD_VALIDATION verdict. No
  new structural finding this task changes that; real-pod data is the only way to resolve it
  further.
- **The Cabbage Merchant — BORDERLINE.** Real card-engine/mana-engine value, but measurably weaker
  than Lotho on both axes this task could check: half the exchange rate (2 Foods → 1 mana vs. 1
  Treasure → 1 mana) and a real attrition risk Lotho's Treasures don't share (combat damage strips
  Foods). Not a clear cut — it's a real body with card-advantage upside beyond pure mana — but not
  a clear standout either.
- **Runic Armasaur — BORDERLINE.** Architecturally invisible trigger (opponent activates a non-mana
  ability) in an already 6-deep card-advantage-engine category (Archivist/Esper Sentinel/Mystic
  Remora/Rhystic Study/Smothering Tithe/Sylvan Library all independently generate advantage). Not
  this task's #1 cut candidate only because its real-game trigger condition, when it does fire, can
  be genuinely punishing against activated-ability-heavy stax/combo pods — a real, if situational,
  strength this solo engine cannot itself confirm.

**Currently-absent cards — structurally reasonable to leave out:**
- **Training Grounds** — reasonable. Biomancer's Familiar already delivers functionally identical
  value with more roles; re-adding both would be pure redundancy, not an upgrade.
- **Avacyn's Pilgrim** — reasonable, reaffirming DECKBUILD-006's own already-settled verdict
  (CUT_PILGRIM_KEEP_LOTHO); not reopened here per this task's own instruction.
- **An Offer You Can't Refuse** — reasonable; this task found no evidence its absence creates an
  interaction-coverage hole (13 real interaction cards remain, none of which this analysis flagged
  as a gap).
- **Shang-Chi, Master of Kung Fu** — reasonable; its main value (haste-granting for activated
  abilities, funding Kinnan's activation) is a narrow, situational combo enabler this task's
  workstreams never surfaced as a binding constraint anywhere in the conversion-architecture grid.

---

## 5. Final-cut ranking

Five least-damaging candidates, ranked (most to least recommended to cut):

1. **Dark Ritual** — role: mana_acceleration (36-deep category, the single most saturated role in
   the deck). Measurable cost of cutting: none found — every WS1 delta from removing it is
   noise-level (<0.1pp on all 4 named target timings, T3 color-failure rate actually improves
   slightly). Redundancy remaining: extremely deep (5 dorks, Sol Ring, Mana Vault, Ancient Tomb,
   City of Traitors, 3 Moxen, Lotus Petal, Chrome Mox, and the mana base itself). Creates no
   interaction-coverage hole (Ritual is not interaction) and does not touch Pod-independence.
2. **Birthing Ritual** — role: tutor_conversion. Real, measured value (88%/21% hit/premium rates)
   clearly ahead of Dark Ritual's; would be a real loss of a repeatable value-engine reach, not
   recommended over Ritual's near-zero measured contribution.
3. **The Cabbage Merchant** — role: card_engine/mana_engine. Measurably weaker than Lotho on both
   checked axes, but still a real body with upside this task didn't fully quantify (card-advantage-
   adjacent value beyond mana); a live-test-first cut rather than a confident one.
4. **Mindbreak Trap** — role: interaction. This project has now independently found its free-
   alt-cost condition (opponent has cast 3+ spells this turn) essentially unusable within a
   structural model TWICE (once in DECKBUILD-006's own funding-cut reasoning, reused again here in
   WS1's BOTH_FLEX_CUT config for the identical reason) — a real, recurring signal, not a
   coincidence. Ranked below Cabbage Merchant only because it is real interaction (per the
   assignment's own Subtlety example, interaction coverage should not be cut merely for a low
   generic contribution rate) and this task did not build a dedicated interaction-coverage census
   to confirm removing it is truly safe.
5. **Runic Armasaur** — role: card_engine (6-deep category). Architecturally invisible to this
   engine's own measurement, in the deck's single most redundant non-mana role cluster; ranked
   last only because its real trigger condition (punishing activated-ability-heavy opponents) is a
   genuine strength this solo model cannot rule out.

**Recommended cut: Dark Ritual.** It is the only candidate on this list with a directly measured,
near-zero marginal contribution to the deck's own stated primary objective (accelerating the four
named premium engines toward the establish → survive → convert plan), no offsetting role this
task's workstreams found elsewhere (it is not interaction, not a tutor, not a body), and the
deepest role-redundancy of any card examined.

---

## 6. Remaining uncertainty

- **Dark Ritual's true value outside the T1-4 opening-hand window is not measured here.** Its real
  utility may lean more toward funding a reactive post-fight play when topdecked later in the game
  — a genuinely different question from "does it accelerate deployment," which this task answered
  cleanly (no) but which does not fully close the book on the card.
- **Cabbage Merchant and Runic Armasaur's opponent-triggered value is scenario-modeled, not
  measured** — real pod data (or a future multiplayer-capable engine) would sharpen both verdicts
  meaningfully more than another round of scenario-band tuning would.
- **Talion remains genuinely unresolved**, exactly as DECKBUILD-004 left it — this task did not
  attempt to change that, per its own given-default-number instruction.
- **Whether Mindbreak Trap specifically (vs. some other interaction piece) is the deck's weakest
  interaction card was not directly tested** — this task's finding is about its usability within
  THIS structural model, not a full ranking of the 13-card interaction suite.

---

## Artifacts

- `data/decklists/tymna-thrasios-treefarm-deckbuild007-v1.json`
- `sim/analysis/deckbuild007_cards.py`, `deckbuild007_variants.py` — card mechanics + config builder
- `sim/analysis/build_deckbuild007_{frozen_deck,ws1_ritual_carpet,ws2_birthing_ritual,ws2_biomancers_familiar,ws2_multiplayer_scenarios,ws3_conversion_architecture,ws4_role_classification,regression_gate}.py`
- `results/solo_baseline/deckbuild007_{ws1_ritual_carpet,ws2_birthing_ritual,ws2_biomancers_familiar,ws2_multiplayer_scenarios,ws3_conversion_architecture,ws4_role_classification,regression_gate}.json`
- `rules_tests/regression/test_deckbuild007_*.py` (8 files)
- Mandatory correction: Deathrite Shaman graveyard-fetch mana, implemented directly in
  `sim/analysis/opening_hand_policy.py`'s core engine (not scoped to this task alone).
