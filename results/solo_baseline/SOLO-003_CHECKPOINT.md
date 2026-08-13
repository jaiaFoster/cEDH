# SIM-001 SOLO-003 — First-Deliverable Implementation Checkpoint

Per the SOLO-003 spec's explicit instruction: **"Before running the full 200k+ census, return a
short implementation checkpoint."** This is that checkpoint. Nothing below has been used to
produce a large-scale trajectory census yet — everything here is infrastructure, validated by
regression tests and small-sample smoke tests (500-3,000 hands), not a production run.

Code added this phase: `sim/analysis/interaction_model.py` (new), `sim/analysis/
trajectory_metrics.py` (new), `sim/analysis/opening_hand_model.py` (engine taxonomy extended),
`sim/analysis/opening_hand_policy.py` (real alternate-cost casting wired into the greedy policy),
`rules_tests/regression/test_interaction_alt_cost_model.py` (new, 9 tests). All of SOLO-002R's
mana-correctness regression tests (13 tests) still pass unmodified — this phase is additive, not
a rewrite of the corrected mana engine.

---

## 1. Revised engine taxonomy

`opening_hand_model.ENGINE_TIERS` (dict: card name → set of tier letters, a card may hold
several):

- **A — primary early card-advantage** (tracked individually, never collapsed): Mystic Remora,
  Esper Sentinel, Rhystic Study, Sylvan Library.
- **B — high-leverage infrastructure** (functionality is conditional on board state, not
  presence): Survival of the Fittest, Birthing Pod, Kinnan Bonder Prodigy, Gaea's Cradle,
  Training Grounds.
- **C — conditional/contextual value**: Tymna the Weaver, Faerie Mastermind, Heartwood
  Storyteller, Runic Armasaur, Archivist of Oghma, Delney Streetwise Lookout, Smothering Tithe,
  Deathrite Shaman.
- **D — mana/development infrastructure**: all of `ACCELERATION` (mana dorks/rocks/Moxen) plus
  Gaea's Cradle (dual-tagged B+D).
- **E — tutor/conversion infrastructure**: all of `TUTORS` (Birthing Pod and Survival of the
  Fittest are dual-tagged B+E, matching the spec's own examples).

**A genuinely important finding surfaced while building this taxonomy, not assumed going in**:
four of the eight Tier-C cards key off **opponent actions this solo/no-opponent model never
simulates** — Heartwood Storyteller ("whenever a player casts a noncreature spell, each of
that player's opponents may draw" — only benefits the pilot if an *opponent* casts, which never
happens here; casting it yourself only helps opponents), Runic Armasaur ("whenever an opponent
activates a non-mana ability"), Archivist of Oghma ("whenever an opponent searches"), and
Smothering Tithe (needs opponents making treasures). These are marked
`TIER_C_STRUCTURALLY_INERT` in `trajectory_metrics.py` and **never count as "supported" in any
trajectory metric**, even if drawn and cast — a real, disclosed structural fact about this deck's
card choices in a solo-goldfish context, not a modeling gap. Deathrite Shaman is also treated as
inert here (its graveyard-mana ability is an unmodeled SOLO-002R simplification, unchanged).
Delney is treated as inert for trajectory purposes too (its power-2-or-less triggered-ability
doubling needs a combat step this model doesn't simulate). That leaves **Tymna** (attacker-based,
modeled via its own dedicated conditional-productivity tiers, see item 2/9 below — explicitly
*not* folded into generic "engine active" metrics) and **Faerie Mastermind** (its own `{3}{U}:
each player draws a card` ability is directly usable solo, unlike its opponent-keyed passive) as
the only two Tier-C cards that can register as "supported" here.

## 2. Primary trajectory metric definitions (`trajectory_metrics.py`)

- **T1** (`t1_metrics`): exact Tier-A engine cast (one flag per card), accelerated two-drop,
  mana creature cast, persistent rock cast, 2+ persistent mana sources, burst-mana used,
  acceleration-while-retaining-4+-cards, and `t1_compound_development` (2+ of {engine, mana dev,
  live interaction} simultaneously true).
- **T2** (`t2_quality_metrics`): `t2_primary_engine_online` (a Tier-A card actually on the
  battlefield), `t2_infrastructure_online_supported` (a Tier-B card on the battlefield **and**
  its real support condition holds — Cradle needs 2+ creatures, Pod needs a sac body, Survival
  needs a discardable creature in hand, Kinnan needs a mana dork on board to double, Training
  Grounds needs Thrasios in play to actually discount anything), `t2_development_plus_interaction`
  (real development AND live interaction, using the corrected alternate-cost interaction model).
- **T3 strong states** (`t3_strong_state_metrics`, section 7): card-advantage (Tier-A online OR a
  *non-Tymna* supported Tier-C card), mana (`total_mana >= lands + 2` or Cradle output 3+),
  conversion (a tutor live **and** its reachable target class includes engine/combo-piece, not
  merely "a tutor exists"), interaction (live interaction retained alongside real development),
  optionality (2+ of the above simultaneously), credible win-pressure
  (`deterministic_win_available` or `one_action_from_verified_win`, reusing SOLO-002R's
  joint-verified combo checks unchanged). `t3_stalled` = none of the above and total mana < 3.
- **Compounding-state combinations** (`compounding_state_metrics`, section 8): all ten named
  pairs (card-engine+mana-engine, card-engine+interaction, card-engine+tutor, mana-engine+tutor,
  Cradle+creature-infrastructure, Survival-supported, Pod-supported, tutor+resources-to-deploy,
  engine+win-conversion, multi-engine+interaction).
- **Tymna** (`tymna_conditional_productivity`, section 9): not scored as success. Deployed +
  creature count only, classified `tymna_low` (0-1 attackers) / `tymna_medium` (2) / `tymna_high`
  (3+). Smoke-test distribution (3,000 hands, on the play): 68.8% no Tymna deployed by T3, 15.8%
  high, 13.0% medium, 2.5% low — i.e. **when Tymna does come down, it's usually well-supported**,
  which is itself a finding worth flagging once validated at scale (early Tymna casts in this
  greedy policy tend to happen only once a real board already exists, since commander priority
  sits behind acceleration/premium-engine but the policy still needs the mana `first`).
- **Thrasios** (`thrasios_productivity`, section 10): productivity is defined as
  `thrasios_activation_now` (a real, live `{4}` payment check — reduced to `{2}` when Training
  Grounds is in play, per its actual Oracle text, floor of 1 mana never reached here) — not mere
  battlefield presence. Kinnan/Cradle co-presence are recorded as diagnostic flags (their precise
  mana-doubling interaction with Thrasios's activation is *not* fully modeled - see item 8).

## 3. Live-interaction implementation status (`interaction_model.py`)

Every card in `INTERACTION_CASTABLE`, checked against real Oracle text
(`data/cards_cache/oracle-2026-08-12`):

| Card | Real alt cost | Status |
|---|---|---|
| Force of Will | pay 1 life + exile a blue card | **Modeled** (pitch, regression-tested) |
| Fierce Guardianship | free if you control a commander | **Modeled** (regression-tested) |
| Flare of Denial | sacrifice a nontoken blue creature | **Modeled** (regression-tested) |
| Subtlety | Evoke — exile a blue card | **Modeled**, including the evoke-vs-hardcast graveyard/battlefield distinction (regression-tested) |
| Misdirection | exile a blue card | **Modeled** (regression-tested) |
| Commandeer | exile **two** blue cards | **Modeled**, exact count (regression-tested) |
| Endurance | Evoke — exile a green card | **Modeled** (same pitch mechanism as Subtlety) |
| Mental Misstep | `{U/P}` — 2 life | **Modeled** as always-live given this model's life totals (documented simplification, not a full Phyrexian-mana rewrite of `parse_cost`) |
| Pact of Negation | `{0}` always, deferred `{3}{U}{U}` obligation | **Modeled**: castability via the normal `{0}` mana path (unchanged), deferred obligation now tracked separately in `state.pact_of_negation_obligations` (found and fixed a real bug here mid-checkpoint: the obligation wasn't being recorded at all on the `{0}` cast path — see regression test) |
| Force of Negation | free "if it's not your turn" | **Structurally never available** in this solo model (every snapshot is taken on the pilot's own turn) — real mana cost `{1}{U}{U}` is the only live path, regression-tested to confirm the alt cost never fires |
| Mindbreak Trap | free "if an opponent cast 3+ spells this turn" | **Structurally never available** (no opponents modeled) — real `{2}{U}{U}` only, regression-tested |
| Swan Song, Flusterstorm, Silence, Veil of Summer | none | Plain mana cost only (no alt cost exists on these cards) |

**Structural limitation, disclosed in every trajectory finding that cites live interaction**:
"live" means *payable* (mana or alt cost), not *has a legal target*. None of these spells'
actual targets (an opponent's spell/permanent) exist in a solo goldfish model, so live-interaction
counts are an upper bound on genuinely useful interaction, not a same-moment guarantee a target
would exist in a real game.

## 4. Revised failure taxonomy (`classify_trajectory_failure`)

Two separate, multi-label tag sets per hand (never collapsed into one):

- **Outcome** (what went wrong): `no_proactive_development`, `development_but_no_compounding_value`,
  `stranded_or_unsupported_engine`, `stranded_tutor`, `stranded_interaction` (live earlier, dead
  and never cast by T3), `color_failure`, `resource_destructive_acceleration_no_payoff`,
  `flooded_action_light`, `insufficient_mana`, `functional` (no negative tag applies).
- **Causal** (why): reuses/extends SOLO-002R's granular diagnosis (`no_second_land`,
  `insufficient_persistent_mana`, Mox-dependency, no-Cradle-fodder, no-Chrome-Mox-fodder,
  no-Mox-Diamond-land, color-specific misses).

Not yet implemented from the full section-20 list: `sequencing/policy_failure` (needs the
achievable-search expansion in item 5 wired into failure classification specifically, not just
target-state reporting) and `unsupported_conditional_engine` as its own explicit tag (currently
folded into `stranded_or_unsupported_engine`) — flagged as remaining work, not silently dropped.

3,000-hand smoke distribution (on the play, informational only, **not a production number**):
`insufficient_mana` 64.4%, `stranded_tutor` 59.8%, `stranded_or_unsupported_engine` 54.6%,
`no_proactive_development` 53.8% (heavily overlapping - most failing hands carry several tags),
`development_but_no_compounding_value` 18.9%, `color_failure` 12.7%,
`resource_destructive_acceleration_no_payoff` 6.4%, `functional` only 2.1%. This is *harsher*
than SOLO-002R's `meaningful_development_rate_t3` (23.4%) because `t3_any_strong_state` sets a
materially higher bar than SOLO-002R's "2+ mana AND (any engine OR tutor OR interaction)" — by
design, per the SOLO-003 instruction not to treat commander/any-engine presence as success.

## 5. Bounded-search expansion plan

Current state (SOLO-002R, unchanged so far): `achievable_search.py` explores turn-1 land-drop
choice × 3 priority orderings, capped at 12 lines/hand (~6x the cost of a single greedy line).

Proposed expansion for SOLO-003, **not yet implemented** (this checkpoint stops short of it,
flagged as the next concrete build step once the trajectory metric definitions above are
confirmed):
- Alternate T2/T3 land choice, not just T1 — the highest-value addition, since SOLO-002R's own
  gap analysis showed `t1_any_meaningful_development` had the largest achievable-vs-realized gap
  (8.4pp), suggesting later-turn land sequencing may matter too.
- Alternate fetch target (currently the fetch always takes the need-colors-scored best target -
  trying the 2nd/3rd-best target when it changes what's castable next turn).
- Alternate acceleration sequencing (which mana source pays for what, when several exist).
- Alternate engine-vs-commander priority variants beyond the current 3 (e.g. a "tutor-first"
  ordering, a "commander-never" ordering to isolate Tymna/Thrasios's true opportunity cost).
- Tutor-timing variants (cast a tutor T1 vs. hold for T2 with more mana).
- **State deduplication**: two lines that reach an identical (lands, battlefield, hand-set,
  mana-available) tuple should be merged rather than re-explored — not yet implemented; without
  it, expanding the branch factors above multiplies cost roughly geometrically. This is the
  single most important addition needed before a 3-4x larger branching factor becomes affordable
  at 100k+ scale.
- Every metric this expanded search touches must keep reporting `policy_realized` alongside
  `best_known_achievable` exactly as SOLO-002R already does (unchanged contract).

## 6. Proposed initial paired land/mana ablations

Per the instruction not to cherry-pick a cut that makes an addition look favorable, and to run
multiple variants when no neutral cut exists: this decklist has no obviously "free" cut (every
nonland card was chosen for a reason), so the proposal below is **explicitly multiple candidate
variants**, not one judgment call presented as neutral.

- **+1 land, variant A**: cut Smothering Tithe (Tier-C, one of the four cards this checkpoint
  found to be structurally inert in a solo model — the least defensible cut *for this specific
  solo-goldfish question*, though it would matter in a real pod).
  Add a land, e.g. another WUBG-flexible untapped dual chosen for color-need balance.
- **+1 land, variant B**: cut Runic Armasaur (also structurally inert here, same caveat).
- **+2 lands**: cut both Smothering Tithe and Runic Armasaur.
- **+1 persistent accelerant**: add a second copy of an existing mana-dork *effect* is not legal
  in a singleton deck, so this variant instead swaps a narrow/rarely-live card (candidate:
  Nature's Rhythm, the deck's most situational tutor per SOLO-002R's tutor-target data) for a
  proposed dork not currently in the list — deferred until a specific card is named, since
  inventing a new card for a paired test needs the same real-card-data discipline as everything
  else in this pipeline (no synthetic cards except the already-approved Part-E infrastructure
  demo).
- **+1 high-quality colored land / utility-land substitution**: candidate is swapping Exotic
  Orchard (modeled as producing zero mana in this solo context, per SOLO-002R) for a real
  colored dual — directly testable and arguably the least judgment-laden swap of the set, since
  Exotic Orchard already contributes nothing to solo mana totals.

All variants use the existing `run_paired_comparison.py` harness (seed-matched, real Oracle-text
card data, `basics_substituted`/`ablation_justification` provenance fields) - no new
infrastructure needed, just new `--remove`/target arguments once the trajectory metrics above are
confirmed as the comparison basis.

## 7. New regression tests

`rules_tests/regression/test_interaction_alt_cost_model.py` (9 tests, all passing): Force of
Will pitch-or-mana, Commandeer's exact 2-blue-card requirement, Fierce Guardianship's
commander-gated free cast, Flare of Denial's blue-creature-sacrifice requirement, Mindbreak
Trap's alt cost never firing solo, Pact of Negation's castability-vs-obligation separation (this
test caught and fixed a real bug — the obligation wasn't recorded on the `{0}` path), Misdirection's
pitch cost, Subtlety's evoke-vs-hardcast graveyard/battlefield distinction, Force of Negation's
alt cost never firing solo. Combined with SOLO-002R's 13 mana-correctness tests: **63 passed, 3
skipped** (pre-existing, unrelated) across the full `rules_tests/regression` suite.

## 8. Remaining model limitations that could materially bias mulligan conclusions

Disclosed explicitly, not silently absorbed:

- **No opponent/target modeling at all** (structural, inherited from SOLO-002R): "live
  interaction" is an upper bound (payable, not "has a target"); four Tier-C engines and
  Smothering Tithe are functionally dead; combo "protection" checks verify mana, not that a real
  counter-worthy threat exists.
- **Bounded search is still turn-1-only** (item 5) — a hand's `best_known_achievable` may still
  understate true achievability via better T2/T3 sequencing until the expansion lands.
- **Training Grounds' interaction with Kinnan and Cradle is not modeled** — only its Thrasios
  interaction is (the one concrete, clearly-scoped case). A hand with Training Grounds + Kinnan
  + a mana dork could realistically enable more than this pass credits it for.
- **Mental Misstep's "always live via life" and Birthing Pod's `{G/P}` are both blanket
  Phyrexian-mana approximations**, not a general Phyrexian-mana rewrite of the payment engine -
  fine given this model's life totals never approach danger in a T1-4 window, but disclosed as
  a simplification rather than a completeness proof.
- **Devoted Druid's self-untap ability and Mana Vault's pay-{4}-to-untap option remain
  unmodeled** (unchanged from SOLO-002R) - both could matter for T3 mana-state trajectories in
  hands that specifically draw them.
- **The T3 "strong state" thresholds themselves are hand-authored, not derived** (e.g. `total_mana
  >= lands + 2` for "strong mana state") - reasonable starting definitions, explicitly offered
  for revision before the large census, not claimed as uniquely correct cutoffs.
- **Tier-B "supported" checks are single-condition heuristics** (e.g. Cradle "supported" = 2+
  creatures, not a claim about how much mana that actually produces relative to the turn's other
  needs) - directionally right, not a precision claim.

---

## Status

All code compiles, all 63 regression tests pass, 3,000-hand smoke tests run clean with no
exceptions across both play/draw seats and produce internally-consistent numbers (e.g. this
checkpoint's `t3_credible_win_pressure` derivation reproduces SOLO-002R's already-validated
`one_action_from_verified_win`/`deterministic_win_available` almost exactly, as it should, since
it's built directly on those unchanged functions). **Nothing here has been scaled to the 100k-
200k+ hand census yet** — that's the next step once this checkpoint is reviewed.
