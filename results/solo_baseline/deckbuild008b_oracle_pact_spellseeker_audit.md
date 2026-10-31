# SIM-DECKBUILD-008b — Oracle + Tainted Pact + Spellseeker (no Demonic Consultation)

Focused follow-up to `deckbuild008_oracle_package_audit.md`. **Question:** does Oracle + Tainted Pact + Spellseeker
capture enough of the Oracle package's conversion gain to be the better *whole deck* once standalone card
quality, interaction loss, slot cost and dead-draw burden are counted separately?

**Subject:** frozen v8 (`bcc611f4…de75`) with the mana-neutral **Deathrite Shaman → Avacyn's Pilgrim** in every
build except `V8_frozen`. All builds are exact, slot-preserving 98s.

Evidence classes (kept separate, never blended into one score):

- **[MC]** paired goldfish Monte Carlo on exact lists (no opponents).
- **[STATE]** per-state solver audits on goldfish states.
- **[SCEN]** log-derived or synthetic conversion windows (uncertainty-labelled; never "this game would have been won").
- **[STRUCT]** exact rules / hypergeometric.
- **[QUAL]** labelled judgement.

---

## 0. Decision table

These are measured axes, not a weighted score. "Det. T4" means a deterministic winning line is available by the
pilot's 4th turn in the goldfish. Δ is paired against A, pooled over replicates. The ± is the larger of the paired SE
and the between-replicate SE.

| Build (adds / cuts beyond Pilgrim) | Det. T4 | Δ vs A | Protected T4 | Post-fight CSA (main) | Bricks / 100 kept hands (Δ vs A) | Low-floor package cards | Pact fair-tutor utility | Interaction lost vs A | Architectural read |
|---|---|---|---|---|---|---|---|---|---|
| **A** Oracle-less (Spellseeker for Strix) | 4.01% | — | 1.43% | 1.67 | 131 (—) | 0 | — | — | One kill (Bowmasters + Mastermind), single-axis |
| **B** Oracle + **Pact** + Spellseeker − Strix, Stormdrake, Skyturtle | **6.14%** | **+2.12 ± 0.09** | 2.09% | **2.21** | 136 (+4.7 ± 0.2) | **1** (Oracle) | Pact material in 79–88% of held states, dead in 9.6% of kept hands | theft card 2→1, resolved-creature answers 5→3, regrowth 1→0 | Compact second axis, one brick added, real interaction cost |
| **B′** same package − Strix, **Gleaming Splendor, Queen of Dale** | 6.07% | +2.00 ± 0.09 | 2.17% | ≈B | 136 (+4.6 ± 0.3) | 1 | same | **none** (keeps Stormdrake + Skyturtle) | Same conversion, keeps every interaction category |
| **C** Oracle + **Consult** + Spellseeker (same cuts as B) | 7.34% | +3.33 ± 0.13 | 2.51% | 2.37 | 139 (+7.6 ± 0.2) | **2** (Oracle, Consult) | n/a | as B, plus theft-tutor access −5pp (no Pact) | More compression, one more brick |
| **D** Oracle + Consult + Pact (same cuts) | 7.07% | +3.12 ± 0.20 | 2.45% | — | 138 (+7.5 ± 0.2) | 2 | as B | as B | Dominated by C and E |
| **E** all four − Strix, Stormdrake, Skyturtle, Queen | **8.54%** | **+4.52 ± 0.17** | 2.98% | 2.97 | 139 (+7.9 ± 0.2) | 2 | as B | as B + Queen | Raw-conversion ceiling |
| F Oracle + Pact − Strix, Stormdrake | 5.13% | +1.18 ± 0.15 | 1.72% | — | 135 (+4.3 ± 0.3) | 1 | as B | theft 2→1 | B without Spellseeker: strictly worse than B |
| G Oracle alone − Strix | 3.84% | −0.18 ± 0.06 | 1.41% | — | 135 (+4.3 ± 0.2) | 1 | — | none | All brick, no gain: reject |
| V8 frozen (Deathrite, Strix) | 3.42% | −0.60 ± 0.07 | 1.22% | — | 130 | 0 | — | — | Reference |

State-level conversion surface (winning draws per non-winning T4 main-phase state, 1,200 games each): B 1.79,
C 2.21. P(any winning draw exists) 36.3% vs 38.7%.

---

## 1. Answers

1. **Is Oracle + Pact + Spellseeker quantitatively viable? Yes.**
   - Det. T4 4.01% → 6.14% (+2.12 ± 0.09pp, +53% relative); T3 1.03% → 1.58%; protected T4 1.43% → 2.09%.
   - Post-fight conversion surface +33% (1.67 → 2.21 winning draws per state).
   - It adds exactly one low-floor card (Oracle) and leaves keep-7, T2 mana and engine establishment within
     ±0.5pp.
2. **Raw conversion given up vs Oracle + Consult + Spellseeker:**
   - −1.21pp det. T4 (B captures 64% of C's gain) and −0.49pp at T3 (53% of C's gain).
   - −0.42pp protected T4.
   - In the narrow windows the gap is smaller: post-fight CSA 2.21 vs 2.37 (77% of C's gain); low-hand / high-mana
     0.93 vs 1.04 (78%); Pod-online-no-outlet 20.0% vs 21.4% immediate conversion.
3. **Raw conversion given up vs all four:**
   - −2.40pp det. T4 (B captures 47%), −0.89pp protected T4.
   - Post-fight CSA 2.21 vs 2.97 (B captures 42% of E's post-fight gain).
4. **Does the lower brick burden plausibly justify that?** [QUAL on top of MC]
   - Consultation adds **+3.0 bricks per 100 kept hands** (C − B = +2.96 ± 0.2; dead in 71% of the kept hands that
     contain it).
   - For that it buys +1.21 goldfish det-T4 conversions per 100 games and +0.16 winning draws per post-fight state.
   - That is roughly 2.5 extra dead kept cards per extra goldfish conversion. Under an explicit "almost no bad cards"
     philosophy that is a defensible trade *against* Consultation: Consultation is the only card in either package
     that is both low-floor and dangerous to use fairly.
   - The all-four build is the honest counter-argument: for the same two low-floor cards as C it gives +1.19pp more
     than C. If the pilot ever accepts a second brick, E, not C, is the build to accept it for.
5. **How often is Pact useful fairly?**
   - Brick classifier [MC]: castable and usable as a fair tutor in **79% / 85% / 88%** of the T2 / T3 / T4 states
     where it is held. Dead in **9.6%** of kept hands (Oracle 85%, Consultation 71%).
   - Search audit [STATE, real library order]: whenever Pact is castable, an acceptable "stop a win" or "protect
     our win" hit exists in 100% of states. Pact exiles ~9–11 cards first and takes Oracle with it only 9–13% of the
     time.
   - Engine and mana searches always hit too (11 / 7 cards exiled, Oracle lost 16% / 12%).
   - "Win right now" through Pact alone exists in 6.6% of castable states.
6. **How costly is spending Pact before Oracle?**
   - Measured [MC ablation, n = 8,000 paired]: a B deck whose Pact is gone from the start converts 4.11% by T4 vs
     6.02% (−1.91pp), still **≥ the Oracle-less deck** (3.81% on the same seeds).
   - If Pact also exiled Oracle, the deck is exactly the Oracle-less deck (3.81%).
   - Non-Oracle deterministic wins are untouched (3.85% vs 3.86%).
   - Post-fight CSA with Pact spent ≈ Oracle-less (1.75 vs 1.67).
   - So spending Pact does **not** cost the deck its ability to win. It returns it to the pre-package baseline and
     turns Oracle into a brick until Thrasios-infinite or a Pod/creature line finds it.
   - With Oracle *in hand* and Pact gone, det. T4 is 3.18% vs 6.90% with Pact live (forced-opening design).
   - Inside a single state the cost is concentrated in the next turn: next-turn winning draws 2.75 (Pact live) →
     0.87 (spent) → 0.41 (spent fairly, exile included).
7. **Is Spellseeker still clearly worth its slot without Consultation? Yes.**
   - Removing it from B costs −1.04 ± 0.12pp det. T4, including −0.64pp of *non-Oracle* deterministic wins
     (Spellseeker → Finale / Rhythm / Neoform / DT feeds the Druid lines too).
   - It is dead in 13.6% of kept hands (materially useful in 77% / 84% of T3 / T4 held states).
   - B vs F (Oracle + Pact, Skyturtle kept): +0.94pp for Spellseeker at +0.4 bricks per 100 hands.
   - [STATE] With Spellseeker in hand, a high-quality fair target exists in 100% of states, and Silence is still
     available in 94%.
   - It gives immediate win access in 3.8% of states and next-turn win access in 10.7% (C: 6.3% / 14.9%).
8. **Are Strix, Stormdrake, Skyturtle defensible cuts? Strix yes; Stormdrake and Skyturtle only if the pilot values
   Gleaming Splendor and Queen of Dale more than creature answers.**
   - All three are among the deck's *best* standalone cards by the brick metric (dead in 3.7% / 5.7% / 4.0% of kept
     hands; material in 90–93% of T3 states).
   - The interaction-preserving alternative B′ (cut Strix, Gleaming Splendor, Queen of Dale) converts the same
     (+2.00 vs +2.12, inside noise) and keeps 0.9pp more 7-card hands than B.
   - B′ keeps both theft effects, every resolved-creature answer and the deck's only regrowth.
   - Queen (dead 14%) and Gleaming (11%) are worse standalone cards than any of the three proposed cuts.
9. **Largest real-game opportunity cost: Volatile Stormdrake**, then Skyturtle, then Strix.
   - Stormdrake is creature theft: priority #3 in the deck's identity, above emergency interaction and policing.
   - It has a fair floor Gilded Drake lacks: it keeps a body when there is no target or the target escapes; Gilded is
     sacrificed.
   - Measured: P(theft card in hand at T4) 17.3% → 8.9%; P(resolved-creature answer in hand at T4) 28.3% → 14.5% for
     the two-card cut (Stormdrake alone cut: → 21.0%).
   - Tutor access to theft is preserved (Pact itself becomes a theft tutor), but tutoring for Gilded costs a tutor
     and leaves one target.
   - Skyturtle is the deck's only regrowth and its only uncounterable instant creature bounce.
   - Strix's niche is real (Geekery R3) but covered at a higher price by Force of Will, Pact of Negation, Flare,
     Subtlety, Mindbreak and Sink into Stupor.
10. **Does the proposed build retain enough interaction?** [QUAL + STRUCT + MC]
    - It keeps every free counter (8), every creature-spell answer except Strix, all proactive protection and every
      flexible catch-all.
    - It **halves** answers to *resolved* creatures and loses regrowth.
    - It does not become a deck that cannot answer boards. But with the proposed cuts its only answers to a resolved
      Kinnan / Bowmasters / Oculus are Gilded Drake, Otawara and Sink into Stupor.
    - That is the edge of "enough", and B′ shows the edge is avoidable for free in conversion terms.
11. **Is there a better three-card package under the "almost no bad cards" philosophy?**
    - **Not a better package — a better funding of the same package.** Oracle + Pact + Spellseeker is the only
      tested 3-card configuration with a single low-floor card and positive conversion.
    - C and D add two low-floor cards each. F (Oracle + Pact) is strictly worse than B. G (Oracle alone) is negative.
    - The improvement available is in the *cuts*: B′.
12. **What should the pilot run?**
    - **Oracle / Pact / Spellseeker — funded by Strix Serenade, Gleaming Splendor and The Queen of Dale (B′)** if the
      pilot can part with those two policing cards.
    - Otherwise use the proposed cuts (B), knowingly paying the resolved-creature-answer cost.
    - Not "no Oracle": the Oracle-less deck has a single deterministic kill that dies to one removal on Bowmasters
      or Mastermind. Not Oracle/Consult/Spellseeker or Oracle/Consult/Pact: two bricks for less than E gives.
    - **All four** remains the right answer only if the pilot decides the brick budget can take Consultation, in which
      case E dominates C and D.

---

## 2. What was rerun and what changed in the model

- **Fair Tainted Pact (new rule, solver flag).** 008 treated Pact only as Oracle's partner.
  - In 008b, Pact is also an instant "find any card" tutor.
  - Exposure rule: in a singleton library Pact always finds the named card, but every card above it is exiled.
    A line whose outlet must still be drawn from the library afterwards is reported as non-deterministic
    (`pact_exposed`).
  - Measured effect on headline conversion: B 6.14% (new) vs 6.17% (legacy model, n = 20,000); E 8.54% vs 8.48%.
    The fair-tutor rule moves **zero** goldfish deterministic wins — its value is fair, not combo.
  - It does move access: with the rule, Pact is a creature-theft tutor (theft hand-or-tutor access at T4: B 53.6%
    vs legacy 48.6%).
- **Colossal Skyturtle channel regrowth (new rule, solver flag).** `{2}{G}` returns a line piece from the graveyard
  as an instant-speed delivery option. Goldfish value ≈ 0: B_keep_skyturtle +2.23 vs B +2.12, inside noise.
- **Both rules default OFF**, so DECKBUILD-008 numbers reproduce. Rules are pinned by
  `rules_tests/regression/test_deckbuild008b_rules.py` (20 tests).
- **Brick / standalone-quality classifier (new metric family).** Every card in hand at each main phase T1–T4 is
  classified:
  - **Material:** `combo_live` / `combo_pair` / `fair_tutor` / `development` / `interaction_held` / `land_drop`.
  - **Secondary only:** `fair_risky` / `body` / `pitch` / `extra_land`.
  - **Stranded.**
  - The assignment's priors are applied as code:
    - Oracle's and Consultation's castability is not development.
    - Consultation's fair mode is `fair_risky`.
    - Pact castable = fair tutor.
    - Spellseeker castable with a target = fair tutor.
    - Hazel / Swift castability is not development.
    - Oboro without Cradle = body only.
  - A **brick** is a kept card that never had a material role at any main phase T1–T4.
- **Design:**
  - Headline A–F: 3 independent replicates × 20,000 paired games for A/B/C/E, 2 × 20,000 for D/F.
  - Controls: 2 × 10,000 (B′ has an extra 20,000).
  - Seeds 9,000,000 + 1,000,000·r + i; paired within each replicate.
  - Ablations n = 8,000 paired; state audit 1,200 games per build (B, C); scenarios 500 states per cell.
  - Scenarios ran on separate cloud worker sessions, same code commit and seeds.

## 3. Conversion [MC]

Pooled across replicates; Δ vs A in percentage points.

| Metric | V8 | A | **B** | B′ | C | D | E | F | G |
|---|---|---|---|---|---|---|---|---|---|
| Det. win T2 | 0.05 | 0.05 | 0.08 | 0.08 | 0.20 | 0.22 | 0.22 | 0.08 | 0.07 |
| Det. win T3 | 0.95 | 1.03 | **1.58** | 1.59 | 2.07 | 2.28 | 2.42 | 1.46 | 1.10 |
| Det. win T4 | 3.42 | 4.01 | **6.14** | 6.07 | 7.34 | 7.07 | 8.54 | 5.13 | 3.84 |
| Protected det. T4 | 1.22 | 1.43 | **2.09** | 2.17 | 2.51 | 2.45 | 2.98 | 1.72 | 1.41 |
| Instant-window det. T4 | 0.50 | 0.50 | 0.57 | 0.65 | 0.62 | 0.65 | 0.70 | 0.55 | 0.51 |
| Oracle-route det. T4 | 0 | 0 | 6.13 | 6.06 | 7.33 | 7.07 | 8.53 | 5.12 | 3.83 |
| Non-Oracle det. T4 | 3.42 | 4.01 | 4.00 | 4.09 | 4.03 | 3.31 | 3.98 | 3.28 | 3.48 |

- **Between-replicate consistency.** Replicate deltas: B +1.99 / +2.29 / +2.09, C +3.25 / +3.57 / +3.16,
  E +4.48 / +4.84 / +4.26.
  - The spread is slightly larger than the paired SE predicts (Q = 3.6 / 5.2 / 7.1 on 2 df), so all ± above use the
    larger of the paired and between-replicate SEs.
  - Treat any difference under ~0.5pp as noise. That is why B, B′ and the B_keep_* variants are reported as equal.
- **Non-Oracle det. stays at A's level in B, B′, C and E**, so the package adds an axis without removing one.
- **The non-Oracle loss in D, F and G** comes from losing Spellseeker as a Druid-line tutor, not from Oracle.

## 4. Development and mulligans [MC]

| Metric | A | B | B′ | C | E |
|---|---|---|---|---|---|
| Keep 7 | 61.2% | 61.5% (+0.3) | 62.4% (+1.2) | 60.5% (−0.7) | 61.7% (+0.5) |
| Mean mulligans | 0.533 | 0.525 | 0.511 | 0.544 | 0.522 |
| T1 development | 54.5% | 53.9% (−0.7) | 53.8% | 54.3% | 53.8% |
| T2 ≥3 mana | 43.0% | 42.6% (−0.4) | 42.8% | 42.7% | 42.5% |
| Premium engine by T2 / T3 / T4 | 33.8 / 51.7 / 58.4 | 33.4 / 51.2 / 57.9 | 33.2 / 51.0 / 57.6 | 33.8 / 51.6 / 58.3 | 33.4 / 51.2 / 57.9 |

- Every Oracle build stays within ±0.7pp of A on development.
- B loses ~0.5pp of premium-engine establishment because Pact and Spellseeker take the slots of two cards the
  goldfish casts early.
- C is the only build with a measurable keep-7 cost (−0.7pp): Consultation is a dead card to the keep heuristic.

## 5. Brick burden / standalone card quality [MC]

### 5.1 Kept-hand brick distribution

| Build | Bricks per kept hand | Δ per 100 kept hands | 0 bricks | 1 brick | 2+ bricks | Stranded cards in hand T2 / T4 | Secondary-only cards in hand T3 |
|---|---|---|---|---|---|---|---|
| V8 | 1.299 | −0.5 | 30.4% | 32.3% | 37.3% | 1.451 / 0.783 | 0.712 |
| A | 1.310 | — | 30.1% | 32.2% | 37.6% | 1.463 / 0.788 | 0.730 |
| **B** | 1.356 | **+4.7 ± 0.2** | 28.4% | 32.4% | 39.2% | 1.486 / 0.807 | 0.785 |
| B′ | 1.356 | +4.6 ± 0.3 | 28.4% | 32.3% | 39.4% | 1.469 / 0.788 | 0.790 |
| C | 1.386 | +7.6 ± 0.2 | 27.4% | 32.4% | 40.2% | 1.482 / 0.808 | 0.841 |
| D | 1.381 | +7.5 ± 0.2 | 27.5% | 32.5% | 40.1% | 1.475 / 0.812 | 0.829 |
| E | 1.389 | +7.9 ± 0.2 | 27.3% | 32.4% | 40.3% | 1.484 / 0.811 | 0.838 |
| G (Oracle alone) | 1.347 | +4.3 ± 0.2 | 28.7% | 32.3% | 39.0% | 1.458 / 0.790 | 0.780 |

- **The deck-wide baseline is ~1.3 "bricks" per kept hand in every build.** These are mostly flood lands never
  played by T4 and slow cards: it is a common floor, not a package effect. Only the deltas are package effects.
- **Oracle alone (G) costs +4.3 bricks per 100 kept hands.** B costs +4.7, so Pact + Spellseeker together add only
  ~0.4.
- **Consultation adds another ~+3.0** (C − B), and the all-four build ~+3.3.

### 5.2 Per-card standalone quality (B unless noted)

Material = P(material role | in hand), and secondary = P(only secondary roles | in hand). Dead = P(brick | in the
kept hand).

| Card | T1 material | T2 material | T3 material | T4 material | Dead in kept hand (7 / 6 / 5) | Measured class | Main fair roles |
|---|---|---|---|---|---|---|---|
| Thassa's Oracle | 9% | 9% | 10% | 13% | **85%** (85 / 85 / 86) | dedicated low floor | body 71%, pitch 32%, combo pair 10% |
| Demonic Consultation (C) | 8% | 9% | 16% | 28% | **71%** (69 / 73 / 78) | dedicated low floor | fair-risky 70%, combo pair |
| **Tainted Pact** | 29% | **79%** | **85%** | **88%** | **9.6%** (9 / 10 / 11) | dual role | fair tutor 83%, combo pair 8%, combo live 4% |
| **Spellseeker** | 5% | 47% | 77% | 84% | **13.6%** (13 / 13 / 20) | strong standalone | fair tutor / development 76%, body, pitch |
| Hazel's Brewmaster (tolerated) | — | — | — | — | 91% | dedicated low floor | body |
| Oboro Breezecaller (tolerated) | — | — | — | — | 90% | dedicated low floor | body (no Cradle) |
| Swift Reconfiguration (tolerated) | — | — | — | — | 72% | dedicated low floor | combo pair only |

- **Effective package tax:**

  | Build | Dedicated low-floor | Dual-role | Strong standalone |
  |---|---|---|---|
  | B | 1 (Oracle) | 1 (Pact) | 1 (Spellseeker) |
  | C | 2 (Oracle, Consultation) | 0 | 1 (Spellseeker) |
  | E | 2 | 1 (Pact) | 1 (Spellseeker) |

- [QUAL] By this metric Oracle is as bad a draw as Hazel or Oboro (85% vs 90–91% dead in kept hands). B adds one
  such card. C and E add two.
- Consultation is slightly less dead than Oracle only because it is castable. Its fair mode is "exile your library
  until a named card", which the classifier counts as risky rather than useful.
- Early-dead rates (no material role by T2) are high for Spellseeker (50% in 7-card keeps) because it costs 3. It
  is a slow card, not a brick.

### 5.3 Standalone quality of the alternative cut candidates [MC, n = 6,000]

From `deckbuild008b_work/cut_candidates.json`:

| Card | Dead in kept hand |
|---|---|
| Clever Impersonator | 51% |
| Derevi | 43% |
| Lotho | 28% |
| Delney | 22% |
| Esper Sentinel | 16% |
| The Queen of Dale | 14% |
| Gleaming Splendor | 11% |
| Gilded Drake | 6.4% |
| **Volatile Stormdrake** | **5.7%** |
| **Colossal Skyturtle** | **4.0%** |
| **Strix Serenade** | **3.7%** |
| Flusterstorm | 4.1% |
| Endurance | 3.3% |
| Swan Song | 3.1% |
| Mental Misstep | 0% |

- **The three proposed cuts are three of the best standalone cards in the deck.** Under a "no bad cards" goal they
  are the wrong place to find slots unless their *function* is surplus.
- Clever Impersonator and Derevi score badly only because their value is copying or tapping *opponents'* permanents,
  which a goldfish cannot see. They are not recommended cuts on this evidence.

## 6. Tainted Pact fair-use audit [STATE]

Source: `deckbuild008b_fair_pact_analysis.json`. Method:

- The audit covers 1,200 goldfish games of B. Pact was in hand in 686 T2–T4 states, and **castable in 56%** of them.
- For every state where Pact is castable, each fair-search class is applied to the **real library order** (the
  goldfish library is the actual future order).
- The pilot stops on the first *acceptable* card, not on one named card.
- The closed form for a uniformly random order is E[exiled] = (N − k)/(k + 1), with P(a specific card exiled) =
  1/(k + 1). It is pinned by `test_pact_closed_form_matches_simulation` and agrees with the real-order walk.

| Fair-search class (acceptable hits, state-conditioned) | States | Acceptable cards in library (mean k) | P(hit) | Cards exiled before hit (closed form) | **P(Oracle exiled)** | P(any Druid-axis piece exiled) | P(any free counter exiled) | P(any protection exiled) |
|---|---|---|---|---|---|---|---|---|
| **Stop an opponent's win** — counter castable after paying `{1}{B}` (opponent's turn) | 95 | 7.5 | 100% | 10.7 (10.2) | **12.6%** | 32.6% | 16.8% | 26.3% |
| **Protect our win** — Silence / Abolisher / Voice / Ranger-Captain / castable counter | 289 | 8.9 | 100% | 9.4 (8.9) | **9.3%** | 39.8% | 19.4% | 19.4% |
| **Find an engine** — Pod / Survival / Rhystic / Remora / Tithe / Kinnan / Oculus | 289 | 6.4 | 100% | 11.3 (11.1) | **15.9%** | 39.8% | 53.3% | 34.6% |
| **Find mana / colour** — fast mana, dorks, Cradle | 289 | 10.8 | 100% | 7.1 (6.6) | **12.1%** | 24.9% | 36.3% | 25.3% |
| **Find a card that wins right now** | 289 | 1.2 | **6.6%** | 22.1 given a hit | — | — | — | — |

Readings:

- **Pact is a reliable fair tutor.** For every fair class with a broad acceptable set, it always finds a hit, exiling
  ~7–11 cards. That is typically ~0.4–0.6 Druid-axis pieces and ~0.3–1.1 free counters. Oracle is lost **9–16%** of
  the time.
- **"Pact for the win now" is rarely available.** Only 6.6% of castable-Pact states have any card that would win this
  window. When one exists it is usually deep (22 cards exiled), and 79% of those hits still convert after the exile
  (5.2% of states).
- **Residual conversion after a fair Pact** (206 T3/T4 main-phase states; next-turn state, conversion surface =
  winning draws per state):

  | Next-turn state | P(already winning) | Mean winning draws |
  |---|---|---|
  | Pact still live | 13.1% | 2.75 |
  | Pact spent, nothing exiled | 1.9% | 0.87 |
  | Pact spent fairly for an engine | 1.9% | 0.41 |

  Spending Pact gives up most of the *immediate* conversion surface it represents. The exile itself costs a further
  ~0.46 winning draws, the pieces Pact walks past. The engine found by the search is not visible inside a one-turn
  surface.
- [QUAL] **Fair Pact is worth using when the class is "stop a win" or "protect our win"**: ~9–13% Oracle risk, and the
  game is decided by that stack. As an engine or mana tutor it is a real but expensive card: it spends the deck's
  compact kill to find something a Demonic Tutor would also find.

## 7. The "spent Pact" question [MC ablations, n = 8,000 paired]

| State | Det. T3 | Det. T4 | Δ T4 vs parent | Oracle-route T4 | Non-Oracle T4 |
|---|---|---|---|---|---|
| B (parent) | 1.50% | 6.02% | — | 6.01% | 3.86% |
| **Pact spent before the game** | 1.03% | **4.11%** | −1.91 ± 0.15 | 4.10% | 3.85% |
| Pact spent and it exiled Oracle | 0.94% | 3.81% | −2.21 ± 0.17 | 0 | 3.81% |
| Oracle answered / exiled, Pact live | 0.94% | 3.82% | −2.20 ± 0.16 | 0 | 3.82% |
| Oracle-less A (same seeds) | 0.94% | 3.81% | — | 0 | 3.81% |
| B with Oracle forced into the opening seven | 1.85% | 6.90% | — | 6.81% | 2.86% |
| …and Pact spent | 0.75% | 3.18% | −3.72 ± 0.22 | 3.07% | 2.93% |
| C with Consultation spent (same deck as "B Pact spent") | 1.03% | 4.11% | −3.09 ± 0.19 | 4.10% | 3.85% |

- **A spent Pact is not a deck that cannot win.** It is the Oracle-less deck plus a small residual:
  - Oracle-via-Thrasios-infinite is still worth +0.30pp T4 over A.
  - Every non-Oracle axis is intact (3.85% vs 3.86%).
  - The marginal cost of a fair Pact is the package's own gain (≈ −1.9pp T4), not more.
- **"Oracle in hand, Pact gone" is the real failure case:** the Oracle becomes a brick (3.18% T4) until infinite mana
  plus Thrasios or a creature line finds a use for it.
- **Consultation is less spendable.** In C the same "partner spent" state costs −3.09pp, because Consultation was the
  cheaper, more frequently used kill; and Consultation has no comparable fair mode.

**State-level view** (from the per-state audit; resilience of a deterministic-win state at T3/T4, n = 90 states in B):

| Event | B | C | Note |
|---|---|---|---|
| Pact spent | 67% still deterministic [57–76] | — | C has no Pact |
| Pact spent and Oracle exiled | 51% [41–61] | — | |
| Oracle lost | 51% [41–61] | 42% [33–51] | B is *less* Oracle-dependent than C |

## 8. Spellseeker audit [STATE + STRUCT]

Legal targets in B: every instant/sorcery with MV ≤ 2 in the list. Pinned by
`test_spellseeker_targets_include_pact_not_oracle`.

| Kind | Targets |
|---|---|
| Win / tutor | **Tainted Pact**, Demonic Tutor, Vampiric Tutor, Enlightened Tutor, Imperial Seal, Finale of Devastation (X=0 → MV 2), Nature's Rhythm, Neoform, Crop Rotation |
| Protection | Silence |
| Interaction | Swan Song, Flusterstorm, Mental Misstep, Pact of Negation |

In C, Demonic Consultation replaces Tainted Pact as the win target.

Measured [STATE]: 347 T2–T4 main-phase states with Spellseeker in hand in B, and 350 in C.

| Spellseeker in hand | B (no Consultation) | C (Consultation) |
|---|---|---|
| Castable now | 72.6% | 72.9% |
| Stranded (not castable now) | 27.4% | 27.1% |
| ≥ 1 high-quality fair target in library (tutor / protection / interaction) | **100%** | 100% |
| Tutor target available | 100% | 100% |
| Protection target (Silence) available | 93.7% | 93.7% |
| Interaction target available | 100% | 100% |
| Tainted Pact still in library | 93.4% | — |
| **Immediate win access** (cast it, fetch, win this window) | **3.8%** | 6.3% |
| **Next-turn win access** (fetch now, win next turn without drawing) | **10.7%** | 14.9% |
| Mean legal targets | 12.9 | 12.9 |

- Spellseeker's fair floor is unchanged by removing Consultation: it always has a protection, interaction or tutor
  target.
- Its *win* access drops by ~1/3 because Pact (2 mana) is a costlier fetched partner than Consultation (1 mana).
- **Tutor leverage at T3–T4** (P(one-turn setup win | held)):

  | Tutor | B | C |
  |---|---|---|
  | Spellseeker | 75.1% | 74.5% |
  | Tainted Pact (as a tutor) | 61.8% (highest immediate-win rate of any tutor, 10.4%) | — |
  | Demonic Tutor | 77.2% | 76.8% |
  | Vampiric Tutor | 77.8% | 76.5% |
  | Nature's Rhythm | 78.1% | 78.2% |
  | Chord of Calling | 74.7% | 73.1% |

## 9. Interaction opportunity cost [STRUCT + MC + QUAL]

### 9.1 Category coverage (cards in the list)

From `deckbuild008b_interaction_coverage.json`:

| Category | V8 | A | **B** | B′ | C / E |
|---|---|---|---|---|---|
| Free counters | 8 | 8 | 8 | 8 | 8 |
| Paid counters (Swan Song, Flusterstorm, Misstep, Strix) | 4 | 3 | 3 | 3 | 3 |
| Creature-spell answers | 7 | 6 | 6 | 6 | 6 |
| Artifact-spell answers | 9 | 8 | 8 | 8 | 8 |
| **Creature theft** | 2 | 2 | **1** | 2 | 1 |
| **Answers to a resolved creature** (Drakes, Skyturtle, Otawara, Sink into Stupor) | 5 | 5 | **3** | 5 | 3 |
| Resolved artifact / enchantment answers | 3 | 3 | 3 | 3 | 3 |
| Graveyard interaction | 1 | 1 | 1 | 1 | 1 |
| Proactive protection | 4 | 4 | 4 | 4 | 4 |
| **Regrowth of spent resources** | 1 | 1 | **0** | 1 | 0 |
| Flexible catch-alls | 5 | 5 | 5 | 5 | 5 |

### 9.2 Measured access at T4 [MC]

Rate of having the answer *castable in hand* or *reachable by a castable tutor* at the start of T4:

| Access at T4 | A | **B** | B′ | B_keep_stormdrake | B_keep_skyturtle | C |
|---|---|---|---|---|---|---|
| Theft card castable in hand | 17.3% | **8.9%** | 16.9% | 16.8% | 8.8% | 8.8% |
| Theft in hand or via a castable tutor | 53.8% | 53.6% | 57.9% | 57.6% | 53.6% | 48.5% |
| Resolved-creature answer castable in hand | 28.3% | **14.5%** | 28.0% | 21.9% | 21.0% | 14.4% |
| Resolved-creature answer in hand or via tutor | 68.1% | 60.9% | 71.1% | 64.3% | 68.2% | 56.5% |
| Regrowth available in hand | 7.4% | 0 | 7.5% | 0 | 7.5% | 0 |
| Creature-spell answer castable in hand | 38.4% | 38.5% | 38.6% | 38.5% | 38.6% | 38.5% |
| Free counter castable in hand | 50.7% | 50.8% | 50.8% | 50.6% | 50.9% | 50.6% |

Note: the replicate spread of the access metrics is larger than their paired SE (|z| up to 3.4), so read them to
±0.5pp.

### 9.3 Per-card audit (Oracle text in the JSON)

**Strix Serenade** — `{U}`: counter an artifact, creature or planeswalker spell.
- It is the only 1-mana hard counter for creature spells.
- Remaining creature-spell answers cost a card (FoW, Subtlety), a creature (Flare), a future upkeep (Pact of
  Negation), a condition (Mindbreak) or three mana (Sink into Stupor).
- Tournament use: Geekery R3, countering Kinnan's Phyrexian Metamorph.
- Goldfish value 0 by construction. Dead in 3.7% of kept hands.
- **Smallest of the three real costs.**

**Volatile Stormdrake** — `{1}{U}`, no flash. ETB: exchange control with target opposing creature, get EEEE, then
sacrifice the stolen creature unless you pay E equal to its MV.

| Situation | Stormdrake | Gilded Drake |
|---|---|---|
| Target MV ≤ 4 (almost every cEDH engine creature) | steal and keep | steal and keep |
| Target MV ≥ 5 | steal, then sacrifice it (removal, not theft) | keeps it |
| Target escapes in response (hexproof / sacrifice / bounce) | ability fizzles; **you keep a 2-mana flyer** | "still resolves… if you can't make an exchange, sacrifice this" — lost |
| No opposing creature (cast as Pod / Chord / Neoform fodder, Cradle count) | keeps a body | sacrificed |

- **One Drake preserves the category's tutor reach**, because the same ~11 tutors find Gilded and Pact adds one
  more. **It halves the targets**, and keeps the one with the worse fair floor.
- Theft is identity priority #3, above emergency interaction and policing.
- **This is the largest real-game opportunity cost of the three cuts.**

**Colossal Skyturtle** — 7 MV, played for channel:
- `{1}{U}` instant bounce of a creature: an activated ability from hand, so ordinary counterspells cannot stop it.
- `{2}{G}` regrowth: the deck's **only** regrowth (spent FoW / Pact of Negation / Silence / tutor, or a destroyed
  Druid / Swift / Effigy).
- Blue *and* green pitch fuel (Endurance evoke).
- A creature card, so Survival finds it to hand at instant speed. Chord / Finale / Rhythm put it onto the battlefield
  and waste it.
- No deterministic line depends on the Skyturtle / Endurance recursion. Its loss is grind and recovery value. The
  measured goldfish recovery value of the regrowth rule is ≈0 (B_keep_skyturtle +2.23 vs B +2.12).
- What the build loses: regrowth entirely, plus its uncounterable creature bounce (Otawara remains at `{3}{U}` minus
  legends).

### 9.4 Has B crossed into "too little ability to answer opposing boards"? [QUAL]

- **Not across, but onto the line.** Stack interaction is untouched: free counters, creature-spell answers, protection.
- What changes is the ability to deal with a creature that has **already resolved**.
  - Cards for it: 5 → 3. In hand at T4: 28% → 14.5%.
  - The remaining answers are a sacrifice-on-failure Drake, a 4-mana land and a 3-mana Sink.
- For a deck whose plan is "survive the first fight, then convert", the first fight is often a resolved engine
  creature (Kinnan, Rograkh / Thrasios, Bowmasters, Oculus). The tournament logs record exactly such boards (AZMS R1,
  Geekery R3).
- B′ removes this concern at no measured conversion cost.

## 10. Conversion windows [SCEN, n = 500 states per cell]

Each cell is P(deterministic win now) / mean winning draws if not already winning. The CSA SE is ≈ 0.05–0.15.

| Window | A | **B** | C | E | B, Pact spent | B, Pact exiled Oracle |
|---|---|---|---|---|---|---|
| **Post-fight, main, no enabler** | 3.6% / 1.67 | 3.4% / **2.21** | 4.0% / 2.37 | 4.2% / 2.97 | 2.8% / 1.75 | 3.6% / 1.94 |
| Post-fight, instant, no enabler | 1.6% / 0.40 | 2.0% / 0.62 | 2.2% / 0.63 | 0.8% / 0.79 | 1.6% / 0.54 | 1.6% / 0.55 |
| Post-fight, main, High Fae | 2.4% / 1.90 | 3.0% / 2.42 | 3.4% / 2.57 | 5.2% / 3.05 | 2.6% / 1.95 | 2.6% / 2.17 |
| Post-fight, instant, High Fae | 2.4% / 1.68 | 3.0% / 2.11 | 3.4% / 2.21 | 4.6% / 2.71 | 2.6% / 1.73 | 2.6% / 1.93 |
| Low hand / high mana, main | 0 / 0.55 | 0 / 0.93 | 0 / 1.04 | 0 / 1.09 | 0 / 0.64 | 0 / 0.59 |
| Low hand / high mana, instant, enabler | 0 / 0.67 | 0 / 0.92 | 0 / 0.97 | 0 / 1.11 | 0 / 0.67 | 0 / 0.65 |
| High board / low colour, main | 1.2% / 0.93 | 2.0% / 1.22 | 2.0% / 1.22 | 1.8% / 1.33 | 1.8% / 1.11 | 1.6% / 1.23 |
| S02 Pod engine, no outlet (AZMS R2) | 0 / 0.0 | **20.0% / 7.9** | 21.4% / 8.9 | 24.4% / 10.0 | 5.6% / 3.0 | 0 / 0.0 |
| S09 engine partly destroyed | 0 / 0.0 | **10.4% / 4.0** | 11.4% / 4.2 | 11.6% / 4.4 | 10.4% / 3.9 | 0 / 0.0 |
| S11 empty board, tutors + mana | 1.8% / 2.0 | 3.8% / 4.0 | 3.8% / 4.1 | 4.8% / 5.1 | 1.8% / 2.0 | 1.8% / 2.0 |
| S04 Nature's Rhythm countered | 4.8% / 2.2 | 6.8% / 3.2 | 6.8% / 3.2 | 6.8% / 3.2 | 6.8% / 3.2 | 4.8% / 2.2 |
| S06 shields down, High Fae on board | 0.6% / 0.51 | 0.6% / 0.78 | 0.8% / 1.09 | 1.2% / 1.35 | 0.6% / 0.52 | 0.6% / 0.52 |
| S05 / S08 / S10 / S13 | ≈0 for every build | | | | | |

**Readings:**

- **The package's value concentrates where the strategic case says it should:**
  - an engine online but no outlet (S02: 0 → 20%);
  - an engine partly destroyed (S09: 0 → 10%);
  - tutors and mana with little board (S11: 2.0 → 4.0 winning draws);
  - post-fight states (+33% CSA).
- **In those windows B is within ~1pp of C** (S02 20.0 vs 21.4, S09 10.4 vs 11.4), much closer than the generic T4
  goldfish gap. Consultation's extra value is mostly *early-turn* (T2–T3) speed rather than narrow-window conversion.
- **Pact spent:** the windows fall back to Oracle-less levels, except S09, where Oracle via the remaining line still
  converts.
- **Timing:** opponent's-turn windows stay weak for every build without an enabler on board, because Oracle is a
  creature. High Fae lifts instant-window CSA by ~3–4×.

## 11. Win-axis redundancy [MC ablations + STRUCT]

| Axis disabled (card blanked) | A det. T4 | B det. T4 | C det. T4 | E det. T4 |
|---|---|---|---|---|
| None | 3.81% | 6.02% | 7.20% | 8.18% |
| Devoted Druid axis (Druid) | **0 (−3.81)** | 2.22% (−3.80) | 3.65% (−3.55) | 4.78% (−3.40) |
| Oboro axis (Oboro) | 3.80% (−0.01) | 6.02% (0.00) | — | — |
| Bowmasters / Mastermind kill (Bowmasters) | **0 (−3.81)** | 6.02% (**0.00**) | — | — |
| Oracle (lose Oracle) | — | 3.82% (−2.20) | — | — |
| Spellseeker | — | 4.99% (−1.04) | — | — |

- **Druid axis:** every Oracle-less deterministic win needs the Druid line *and* the Bowmasters kill.
  - **Oracle turns the Bowmasters/Mastermind kill from a single point of failure into a goldfish-redundant backup.**
    In B, blanking Bowmasters costs 0.00pp.
  - Bowmasters and Mastermind keep their fair value (anti-draw, flash 2-drops, Pod rungs). They are not cut
    candidates.
  - Without Druid, B still converts 2.2% through Oracle + Pact directly. That is a genuinely independent axis.
- **Oboro axis:** the dedicated cost is Oboro alone (Cradle, Talon Gates and Thrasios are independently desired).
  Its goldfish conversion contribution is ~0 at T1–T4, because ≥6 creatures plus Cradle plus Talon is a late-game
  state. It is neither threatened nor helped by the package.
- **Endurance / recursion:** no deterministic line depends on it. Skyturtle's removal does not collapse a win axis;
  it removes grind value.
- **Finale:** non-deterministic in this model (X ≥ 10 combat), reported separately everywhere.
- [QUAL] **Healthy resilience, not overloading.** Oracle adds an axis that survives the loss of the Druid axis or of
  the Bowmasters kill. The overlap it creates is with Bowmasters/Mastermind, whose fair value stays.

**Resilience given a deterministic-win state at T3/T4** [STATE]. Each cell is P(still deterministic after the
event), with Wilson 95% CIs.

| Event | B (n = 90) | C (n = 110) |
|---|---|---|
| Creature board wipe | 8% [4–15] | 10% [6–17] |
| All artifacts removed | 73% [63–81] | 71% [62–79] |
| Graveyard exiled | 100% | 100% |
| Creature activated abilities suppressed | 48% [38–58] | 55% [45–64] |
| Lose Thrasios | 38% [28–48] | 49% [40–58] |
| Lose Birthing Pod | 84% [76–90] | 80% [72–87] |
| Lose Oracle | 51% [41–61] | 42% [33–51] |
| Pact spent | 67% [57–76] | — |
| Pact spent and Oracle exiled | 51% [41–61] | — |
| Druid axis disabled | 41% [31–51] | 55% [45–64] |
| Oboro axis disabled | 100% | 100% |
| Bowmasters axis disabled | 100% | 100% |
| Single used piece removed (mean) | 14% | 14% |

- B's winning states are slightly *more* Thrasios- and Druid-dependent than C's: Pact lines need more mana and more
  often run through an infinite engine.
- They are *less* Oracle-dependent than C's.
- All B-vs-C differences overlap their 95% CIs. The direction is consistent, though: B leans on the Druid axis, C on
  Oracle.

## 12. Falsification tests

| Attempt to prove B wrong | Result |
|---|---|
| Does cutting Stormdrake create unacceptable creature-answer holes? | **Partly confirmed.** Resolved-creature answers in hand at T4 halve (28% → 14.5%). Not "unacceptable" — theft tutor reach is intact — but it is the largest real cost, and it is avoidable (B′). |
| Does cutting Skyturtle worsen recovery after a stack fight? | **Not in conversion terms** (goldfish recovery value of regrowth ≈ 0; post-fight cells unchanged). **Yes in grind terms:** the deck's only regrowth is gone. |
| Is Pact too often spent fairly, leaving Oracle stranded? | Spending it returns the deck to Oracle-less strength (4.11% vs 3.81%), not below. Oracle held with Pact gone is a brick (3.18% T4 with Oracle forced). Fair Pact loses Oracle only 9–16% of the time. The real cost of a fair Pact is next-turn conversion (2.75 → 0.41 winning draws), so it should be spent fairly on the stack, not for value. |
| Does Oracle create enough dead hands to negate the gain? | Oracle costs +4.3 bricks per 100 kept hands; keep-7 does not fall (+0.3pp in B). The conversion gain (+2.1pp T4, +33% post-fight CSA) is not negated. |
| Is B materially worse than Oracle + Consult + Spellseeker? | **Yes in raw conversion** (−1.21pp T4, −0.49pp T3). In narrow windows only ~1pp worse. C costs +3.0 bricks per 100 hands, −0.96pp keep-7 vs B, and −5pp theft-tutor access. |
| Is the four-card package still obviously better after brick cost? | **On conversion, yes** (+2.40pp T4 over B). On the brick axis it is C's burden (+3.3 per 100 vs B). Whether that is "better" is the pilot's brick-budget decision, not a measured fact. |
| Is Oracle not worth running at all under the low-brick philosophy? | **Rejected.** The Oracle-less deck's deterministic kill is a two-card single point of failure. B's single brick buys an independent axis and +53% T4 conversion. |

## 13. Limitations

- **Goldfish only:** no opponents, stack, combat or removal. Interaction value is measured as *access*, not as games
  saved.
- **Brick classifier rules are explicit and test-pinned, but they are rules.**
  - A held counterspell counts as material whenever castable.
  - Pitch and body are secondary roles.
  - Extra lands are secondary.
  - The deck-wide ~1.3 bricks per kept hand floor is mostly flood and slow cards common to every build.
- **The fair-Pact search classes are defined from the actual decklist and state.**
  - "Stop a win" means a counter castable after paying `{1}{B}`, with Mindbreak Trap assumed castable for free.
  - "Find conversion" means any card that wins now after Pact resolves.
  - Pilots will sometimes stop earlier on a "good enough" card. The real-order walk gives the cost of the *first
    acceptable* hit.
- **Replicate heterogeneity** slightly exceeds paired SE; ± uses the larger. Access metrics are noisier still.
- **Where the runs happened.** Scenarios ran on two cloud worker sessions; the B/C state audit ran locally. Both used
  identical code (commit `8459e3d` or later, no code changes) and identical seeds. A worker reran the full per-state
  audit (A–F) and reproduced the local B/C numbers exactly. A/D/E/F state results are in the JSON artifacts, e.g.
  T4 main-phase conversion surface (winning draws per non-winning state): A 1.28 · F 1.49 · **B 1.79** · D 2.16 ·
  C 2.21 · E 2.73.
- **Moxfield sync.** On 2026-10-31 the live Moxfield list moved to version 10. It is card-for-card the primary build B
  evaluated here (−Deathrite, Strix, Stormdrake, Skyturtle; +Pilgrim, Oracle, Pact, Spellseeker).

## 14. Artifacts

| File | Content |
|---|---|
| `deckbuild008b_oracle_pact_spellseeker_audit.md` | this report |
| `deckbuild008b_variant_metrics.json` | every configuration, pooled + per replicate, ablations, provenance |
| `deckbuild008b_brick_burden.json` | brick distributions, per-card quality by turn, dead-draw by mulligan depth, package tax |
| `deckbuild008b_fair_pact_analysis.json` | per-state fair-Pact search audit + spent-Pact ablations |
| `deckbuild008b_interaction_coverage.json` | category coverage, tutor reach, hypergeometric seen-rates, per-card cut audit |
| `deckbuild008b_conversion_surface.json` | state CSA, Spellseeker audit, tutor leverage, resilience, synthetic windows |
| `deckbuild008b_scenarios.json` | all tournament and synthetic scenario cells |
| `deckbuild008b_final_comparison.csv` | one row per build |
| `deckbuild008b_work/*.json` | raw phase outputs (variants per replicate, ablations, audit, scenarios, cut candidates) |
| `sim/analysis/build_deckbuild008b_*.py`, `deckbuild008b_{analysis,phases,assemble}.py`; solver flags in `deckbuild008_solver.py` | code |
| `rules_tests/regression/test_deckbuild008b_rules.py` | 20 tests for every new rule and metric assumption |

**Reproduce:** `python3 sim/analysis/build_deckbuild008b_experiments.py --phase <variants|ablations|audit|scenarios|assemble> ...`
(see each phase's docstring for n, seeds and tags).
