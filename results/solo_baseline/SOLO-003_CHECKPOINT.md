# SIM-001 SOLO-003 — First-Deliverable Implementation Checkpoint

Per the SOLO-003 spec's explicit instruction: **"Before running the full 200k+ census, return a
short implementation checkpoint."** This is that checkpoint. Nothing below has been used to
produce a large-scale trajectory census yet — everything here is infrastructure, validated by
regression tests and small-sample smoke tests (500-3,000 hands), not a production run.

**Revision note**: this checkpoint was conditionally approved with six required corrections,
all applied and re-validated before the census ran: (1) the composite `"functional"` outcome tag
removed from the failure taxonomy entirely - see item 4; (2) the achievable-search expansion
(item 5) is now actually implemented (T1-T3 land/fetch branching with state dedup), not just
proposed; (3) explicit `trajectory_family_tags()` added (`trajectory_metrics.py`) covering the
section-4/section-16 named sequence and pattern families; (4) the Tymna metric is renamed
`tymna_attack_capacity` and reframed away from "productivity" - see item 2; (5) the Training
Grounds/Kinnan/Cradle wording is corrected - Training Grounds has no textual relationship to
either, see item 2; (6) the paired-ablation proposal (item 6) is redesigned to exclude the
solo-model-inert cards it originally (and wrongly) proposed cutting.

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
- **Trajectory-family tags** (`trajectory_family_tags`, sections 4 + 16, added per the checkpoint
  revision): rule-based, explicitly-labeled-as-such multi-label tags covering the named T1→T2
  sequence families (dork→Rhystic Study, dork→Survival, dork→Pod, accel→Kinnan, accel→commander,
  fast-mana→multiple-T2-actions, Remora→mana development, Sentinel→second engine, engine→tutor,
  engine→development+interaction, accel→premium T2 engine) and the section-16 hand-pattern
  families (T1 engine hand, tutor-conversion hand, interaction-heavy slow hand, explosive
  resource-destructive hand, commander-conversion hand, strong one-land hand, deceptive two-land
  hand, flooded hand, genuinely-nonfunctional hand, creature-swarm-to-Cradle). 2,000-hand smoke
  test: no exceptions, most common tags `commander_conversion_hand` (41.4%),
  `genuinely_nonfunctional_hand` (37.1%), `t1_accel_to_t2_commander` (22.5%) - a real,
  data-derived clustering pass remains future work (same disclosed reduction as SOLO-002R's
  archetype tags).
- **Tymna** (`tymna_attack_capacity`, section 9, renamed from an earlier "conditional
  productivity" framing): not scored as success, and explicitly **not** labeled as productivity
  at all — it measures ATTACK CAPACITY (creatures currently able to attack), not confirmed card
  draw. This model does not simulate combat, blocks, or opponent removal, so it has no way to
  know how many of those attackers would actually connect, and Tymna's trigger is defined in
  terms of "opponents dealt combat damage this turn" - a downstream fact this model cannot
  observe. Classified `attack_capacity_low` (0-1 creatures) / `attack_capacity_medium` (2) /
  `attack_capacity_high` (3+). Smoke-test distribution (3,000 hands, on the play): 68.8% no
  Tymna deployed by T3, 15.8% high, 13.0% medium, 2.5% low capacity — i.e. **when Tymna does
  come down, it usually has real attack capacity already**, which is itself a finding worth
  flagging once validated at scale (early Tymna casts in this greedy policy tend to happen only
  once a real board already exists, since commander priority sits behind acceleration/
  premium-engine but the policy still needs the mana first).
- **Thrasios** (`thrasios_productivity`, section 10): productivity is defined as
  `thrasios_activation_now` (a real, live `{4}` payment check — reduced to `{2}` when Training
  Grounds is in play, per its actual Oracle text, floor of 1 mana never reached here) — not mere
  battlefield presence. **Correction from the first pass of this checkpoint**: Training Grounds
  has no relationship to Kinnan or Cradle at all - its real text ("Activated abilities of
  creatures you control cost {2} less") only ever discounts an activated ability of a creature.
  In this deck that's Thrasios's own `{4}` (modeled) and, separately, Kinnan's own `{5}{G}{U}`
  tutor ability if Kinnan is in play (not modeled - no metric tracks Kinnan's own activation).
  Training Grounds' text cannot apply to Kinnan's mana-doubling ability (a triggered ability with
  no mana cost to discount) or to Gaea's Cradle (a land, not a creature) under any circumstance.
  What Kinnan and Cradle actually contribute to affording Thrasios's activation is a completely
  different, also-unmodeled mechanism: Kinnan can double a mana dork's output when tapped
  (`available_sources()` has no Kinnan check), and Cradle is simply more raw mana already
  reflected in `total_mana`. Both are recorded as board-state co-presence diagnostics only, never
  as a claim that either mechanism's magnitude is modeled.

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
  `flooded_action_light`, `insufficient_mana`. **Correction from the first pass**: no composite
  "functional"/"no negative tag applies" label is emitted anymore - a hand with an empty
  outcome-tag list means no diagnosed failure, which is not itself a success claim, and per
  instruction no single composite score of any kind may exist for mulligan-policy optimization to
  latch onto. A positive signal, when one is actually needed, comes from the explicitly-named
  flags in `t3_strong_state_metrics`/`compounding_state_metrics` instead - never from the absence
  of a failure tag.
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
`resource_destructive_acceleration_no_payoff` 6.4%. Only 2.1% of hands carry no outcome tag at
all (an absence-of-diagnosed-failure count, reported here purely for context - **not** the
composite success label it would have been under the first pass of this checkpoint, since that
label has been removed; `t3_any_strong_state` was 50.3% in the same batch and is the metric that
actually answers "did this hand reach a strong state," independent of failure-tag presence). This
failure-tag picture is *harsher* than SOLO-002R's `meaningful_development_rate_t3` (23.4%)
because `t3_any_strong_state` sets a materially higher bar than SOLO-002R's "2+ mana AND (any
engine OR tutor OR interaction)" — by design, per the SOLO-003 instruction not to treat
commander/any-engine presence as success.

## 5. Bounded-search expansion plan

**Implemented** (this was "proposed, not yet built" in the first pass of this checkpoint;
`achievable_search.py` now does this): a frontier/BFS-style search across all three turns,
branching each turn on land choice × top-2 legal fetch targets (when the chosen land is a fetch)
× 3 priority orderings, capped at `MAX_BRANCHES_PER_STATE=6` branches tried per surviving state
and `MAX_FRONTIER_STATES=8` states carried into the next turn - with **state deduplication**: two
branches reaching an identical `(lands, battlefield, hand, life, command_zone)` signature are
merged, so equivalent lines are never re-explored. Measured cost: ~21 lines/hand on average (far
below the ~400-line worst case, because dedup collapses many priority-variant branches that
happen to reach the same board state) at ~280 hands/sec - a 20,000-hand run now takes about a
minute. `policy_realized` is still the exact single default-greedy line, reported alongside
`best_known_achievable` exactly as before (unchanged contract). Validated against the prior
T1-only search: T2/T3 achievable-vs-realized gaps grew as expected (e.g. `t3_tymna_supported`'s
gap widened from 6.2pp to 9.4pp on a comparable sample), confirming the expansion finds real
additional lines rather than just spending more cycles on equivalent ones.

Still not included (disclosed, real limitations, not oversights):
- Alternate acceleration sequencing (which specific mana source pays for what, when several
  untapped sources could each cover the same cost) - the payment search already picks
  deterministically, not exhaustively, among equally-valid sources.
- Tutor-timing variants (cast a tutor T1 vs. deliberately hold it for T2 with more mana) are not
  a separate explored axis - the priority-order variants change *relative* casting order but
  don't model "choose to pass with mana up."
- The state-signature dedup does not track exact remaining library composition beyond "same
  hand" (see achievable_search.py's docstring for the caveat and why it's judged acceptable for
  a bounded, non-exhaustive search).

## 6. Proposed initial paired land/mana ablations (redesigned)

**The first pass of this checkpoint proposed Smothering Tithe and Runic Armasaur as the cut
candidates for every land-addition variant. That was a real methodological error, caught before
any run was executed**: both cards are only "weak" in this project's own data because they're
`TIER_C_STRUCTURALLY_INERT` — an artifact of the solo/no-opponent model, not a fact about the
cards' real power level (both are perfectly good pod cards). Using them as the cut would have
biased every "+1/+2 land" result upward for a reason that would evaporate the moment this same
question was asked in a real pod context. **Redesigned below, with the biased candidates
explicitly banned from consideration.**

**Banned from cut-candidacy for this specific question** (their apparent weakness is a modeling
artifact, not a power-level fact — using any of them would repeat the exact error just described):
Heartwood Storyteller, Runic Armasaur, Archivist of Oghma, Smothering Tithe, Delney Streetwise
Lookout (all `TIER_C_STRUCTURALLY_INERT` or combat-dependent), and **Exotic Orchard** (its "zero
mana in solo" modeling is the same class of artifact — Exotic Orchard is a strong land in a real
pod with diverse opponent manabases; cutting it *because our model can't see that value* would be
the identical bias applied to a land instead of a spell).

**Redesigned priority order, least biased first:**

1. **Land-for-land quality swaps (primary, lowest bias risk)** — the cleanest way to isolate "does
   more/better mana help" without touching action density (tutor/engine/interaction count) at
   all. Candidate: swap one of the narrow-ability Legendary utility lands (Boseiju/Minamo/
   Otawara/Talon Gates of Madara/Starting Town - each a modal, situational land whose ability is
   independent of opponent count) for a land that reliably taps for a needed color every turn.
   This tests mana *reliability* in complete isolation from the nonland-card-cut problem above,
   since no spell slot changes at all.
2. **+1 / +2 land via nonland cut, restricted to solo-and-pod-independent weakness evidence** —
   candidates limited to cards whose narrowness is a fact about the card's own design, not about
   opponent-absence: Sowing Mycospawn and Crop Rotation (both land-only tutors — the narrowest
   target class in SOLO-002R's own tutor-target-accessibility data, a fact true in any seat count)
   and Nature's Rhythm (the deck's most situational tutor by the same data). Run as **separate,
   non-competing variants** rather than one chosen "representative" cut - report each on its own,
   consistent with the multi-variant discipline already used elsewhere in this project. Every
   variant still carries real judgment risk (this project has no exhaustive pod-power model for
   any card) and that risk is disclosed in each run's `ablation_justification`, not hidden by
   picking only one.
3. **+1 persistent accelerant** — deferred until a specific real card is named for the swap (no
   synthetic cards outside the already-approved Part-E infrastructure demo), using the same
   land-only-tutor cut candidates from (2) as the donor slot if pursued.

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
