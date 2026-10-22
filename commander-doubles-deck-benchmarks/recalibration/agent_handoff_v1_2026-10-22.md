# Agent handoff — Commander Doubles global Season 0 recalibration
**Date:** 2026-10-22 · **Status:** proposed research and scoring work, not active league rules · **Branch:** `commander-doubles-deck-benchmarks`

## Mission
Derive a **reproducible, explainable global card-pricing policy** from the organizer's nine-team (18-deck) card-by-card reviews; identify missed analogues and whole card *packages/families*; extend pricing proposals to previously unreviewed cards; then recompute scores for **all 18 unchanged benchmark decks** under a common candidate schedule.

**This is a recalibration task, not another deckbuilding task.** Do not rebuild decks to fit 120, edit archived decklists, alter official rules, activate the schedule, or treat working selections as organizer-locked prices. Make the broad candidate schedule and audit reproducible and submit it for organizer approval.

## Critical product constraints
- Competitive 2v2 Commander / two-headed giant, **60 shared starting life per team** (custom format setting).
- Combined construction budget **120**, nominally 60 per head; may transfer at most **12**, so **72 maximum on any individual**. Use current repo construction rules as controlling for subtleties.
- Exactly 100 cards per player (including commander[s]); normal commander identity/singleton restrictions and existing experimental ban policy. Do not introduce experimental unbans or assert playtest win rates not observed.
- Output candidate schedule as **`season0-proposed`, `activated=false`**. Historical/official/current league data, 50 qualitative anchors, and original scores remain immutable.
- One global main-deck price per Oracle card identity; separately priced command zone if eligible. Apply one price consistently across *every* deck using that card; MDFC faces share one card identity, not two point charges.

## Organizer's settled pricing objective (highest priority)
> Evaluate **the highest realistically achievable competitive power of a card in a deliberately optimized two-player team**, not average solo Commander utility, using **efficiency**, **conversion**, **opportunity cost**, and **2HG-specific interactions**.

Keep the scoring straightforward, integer-valued, understandable, and card-based, not a nonlinear per-deck combo tax.

### Four-lens decision rubric
1. **Efficiency:** mana/timing/activation cost; speed to meaningful advantage; reliability/access; asymmetry; immediate effect; resilience and stack windows.
2. **Conversion:** repeated or universal resource conversion into cards, mana, locks, extra turns or wins; can it win as engine rather than merely be a payoff; breadth of distinct lines.
3. **Opportunity cost:** card/land slot, color/curve, dead outside combo, number of otherwise bad support cards, slow setup, self-harm, deck restrictions, vulnerability and counterplay; low-cost, high-utility lands and command-zone cards need extra review.
4. **2HG delta:** two opposing heads, shared team turns and shared starting life, teammates casting spells/controlling permanents, opponent vs player vs controller vs each opponent, targeting, extra turns, life loss/gain, damage prevention and other head-specific effects. Verify Oracle text and the relevant comprehensive 2HG rules before pricing an edge case. Explicitly say what actually scales.

### Simple hybrid rule for combo prices
**Concentrate the combo premium on the broadly reusable enabler.** Narrow, weak, dead-outside-combo payoffs can remain **0**. Do not assign points to every member just because a combo exists; avoid pair-specific surcharges. Credit a payoff's independent power or unusual access where genuinely warranted. Organizer explicitly accepts **Aluren 4 / Acererak the Archlich 0** (cross-controller dungeon loop): Aluren is the reusable engine, Acererak is the otherwise weak payload. Likewise high KCI / Clock of Omens / Mystic Forge; not blanket charges to every artifact. If an enabler enables half a synergy deck, its price reflects that. *Highest plausible optimized ceiling* still requires setup/counterplay and legitimate rules, not imaginary goldfish outcomes.

### Preserve deliberate organizer exceptions
- Symmetrical Pox/Smallpox/Death Cloud and Contamination remain **0** despite their combos/denial: they hurt the friendly team too; charge asymmetric enablers (Bloodletter) rather than uniformly taxing symmetric effects.
- Life from the Loam, Exploration, Burgeoning, Dakmor Salvage, Thespian's Stage, typical narrow discard outlets, Dramatic Reversal, The Reality Chip, Scroll Rack, Expedition Map remain **0** where organizer explicitly left them. Consider comparable cards individually, do not automatically apply family taxes.
- The latest **Swan Song = 2**, **Basalt Monolith = 4**, **Opposition Agent = 6**, **Krark-Clan Ironworks = 10**, **Crop Rotation = 6**, **Lake of the Dead = 6**, **Aluren = 4** override old numbers. Latest **Tireless Provisioner = 1** (organizer reconsidered but settled on 1), **Serrra Ascendant = 1** [canonical spelling: Serra Ascendant].
- **Sheoldred, the Apocalypse**: main-deck 7, **CZ 13 working**. Premium commanders should generally cost more in command zone due guaranteed access, often approaching twice their main-deck price, **but do not blanket-double** all commanders; Chulane CZ2, other CZ cards need independent role and access review.
- Do not apply a blanket charge to every MDFC, every ritual, every utility land, all tutors equally, all discard outlets, or all parts of a combo.

## Authoritative inputs (read all, reconcile latest-over-earlier)
1. **Consolidated main/CZ working price overlay (166 records):** `recalibration/organizer_effective_price_overlay_v2_2026-10-22.csv`. Its `authority` column distinguishes organizer selections, approximate values, and working picks; inherited B1/B2 authority requires reading original review notes.
2. **B1–B2 previous accepted overlay and last 12-deck rescoring:** `accepted_working_price_overrides_2026-10-21.csv`, `accepted_working_price_summary_2026-10-21.md`, `retotal_12_decks_2026-10-21.csv`, `retotal_full_card_ledger_2026-10-21.csv`. This snapshot is *pre-Batch3*, so **not** the new canonical score for A–F.
3. **Organizer decisions and caveats:**
   - `team_A_organizer_calibration_2026-10-21.md`
   - `batch1/team_B_repricing_preview_2026-10-21.md`
   - `batch1/team_C_organizer_calibration_2026-10-21.md`
   - `organizer_batch1_price_lock_2026-10-21.md`
   - `batch2/team_D_organizer_calibration_2026-10-21.md`
   - `batch2/team_E_organizer_calibration_2026-10-21.md`
   - `batch2/team_F_organizer_calibration_2026-10-21.md`
   - `batch3/team_G_organizer_calibration_2026-10-21.md`
   - `batch3/team_G_followup_prices_2026-10-21.md`
   - `batch3/team_H_organizer_calibration_2026-10-21.md`
   - `batch3/team_I_organizer_calibration_2026-10-21.md`
4. **Original untouched 18 complete decklists/score ledgers:** `batch1/`, `batch2/`, `batch3/`, decks **A1–I2**. Batch3 published commit `72a213548189782ffb0471fd59c31c21f3ad6a8b`; commit provides reproducible source state.
5. **Earlier premium-boundary and point schedule research:** `../commander-doubles-cutoff-recalibration/recalibrated_point_schedule.csv` (~321 card entries), `../commander-doubles-cutoff-recalibration/organizer_premium_boundary_decisions_2026-10-20.md`. Review but **newest organizer decisions override** this old schedule. Preserve 50 historical qualitative anchors.

## Proposed agent work, in required order

### Phase 1 — extract *why* cards changed (reason and package audit)
Produce an evidence-backed `decision_taxonomy.md` and machine-readable `decision_lineage.csv` for all organizer-selected/working changed cards. For each entry, preserve (Oracle ID, zone, initial and effective points, exact/approx/assistant-working status, latest dated source, reasons, 2HG modifier, exceptions). Resolve naming (e.g. Shifting Woodland, Tireless Provisioner, Staff of Compleation, Icetill Explorer) by authoritative card identity. No guessed Oracle IDs. Explicitly reconcile later-over-earlier reversals and nonchanges.

Derive prioritized **packages/families** and their boundary cases, with concrete similar cards:
- Universal and restricted tutors (hand, graveyard, battlefield, command zone, land; sacrifice costs; instant speed; transmute; artifact/enchantment/creature/equipment packages).
- Mana acceleration (free rituals, sac-lands, repeatable untaps, mana sinks, color fixing); utility lands vs spell slots; fetch/original dual land burden.
- Universally reusable combo engines (Aluren, KCI, Clock, Mystic Forge, Earthcraft, Scepter/Monolith, Pod, reanimation, Graveyard/Breach); narrow payoffs vs redundant engine substitutes.
- Free interaction and protection, must evaluate controller/team targeting (Orim's Chant, Abeyance, Force-family, red blasts, removal); interaction-as-win-denial vs generic value disruption.
- Command zone premium, reliable engines, commanders active even when uncast; partner pairs; high impact vs fair synergy.
- Card draw/engines, conditional theft, treasure, opponent count and team turn structure.
- Alternate wins and 60-life threshold cards, opponent-specific life loss, 2HG shared-life math; symmetrical attrition vs asymmetric doublers.
- MDFCs and specific lands with nearly free spell effects; don't infer a full family without card-level support.
Document **counterexamples with intentionally low price**, not just reasons to add points.

### Phase 2 — systematic extrapolation to missing cards
Audit **every card in the existing ~321-row candidate schedule**, every unique card in all **18 benchmark decks**, then perform *targeted additional discovery* across the currently legal card pool (Oracle-text searches, competitive lists, analogous effects, high-ceiling 2HG interactions, relevant format literature). Give coverage counts: reviewed in schedule, in benchmark lists, newly discovered. This is not permission to assign a point to every Commander-legal card.

Create `family_coverage_audit.csv` (family, exemplars, reviewed analogues, missed/zero-price candidates, reason, proposed points, confidence, rules source or combo proof, counterexample, review priority), and `unpriced_high_risk_queue.csv`. Flag likely loopholes in dynamic tutor packages, multiplicative combo enablers, reusable engines, head-specific text, land slot mana, command access, and niche but reproducible cross-controller wins. For each new proposed price, include why it is stronger/weaker than a nearby organizer anchor. Do not silently rewrite accepted organizer exact prices because of an agent theory; propose conflicts separately.

### Phase 3 — issue *candidate* global points schedule
Produce `candidate_point_schedule_v3.csv`, one row per verified Oracle identity/zone with at least old effective, proposed price, organizer-versus-agent authority, exact-vs-working status, concise reason, family, 2HG notes, evidence, uncertainty, status. Preserve pre-review schedule and v2 overlay unmodified. Represent additional agent proposals distinctly from organizer-approved numbers. Keep all points nonnegative integers and command-zone/main-deck fields separate. Set `season0-proposed`, `activated=false`.

Maintain an `exception_and_conflict_queue.md` with proposed alternative values for any organizer-locked price the research questions; include real evidence and no unilateral override. Explicitly revisit **Time Sieve 8 (organizer considered higher, unchosen)**, **Winds of Abandon 5 (organizer's conditional premise that overload avoided friendly creatures was false)**, and disputed/unspecified commander CZ premiums. Avoid converting approximate/range selections into falsely approved exacts.

### Phase 4 — rescore all 18 *unchanged* benchmark decks
Reproduce original deck identities/quantities from the three Batch source folders. Produce **two comparable rescorings**: (A) organizer v2 overlay applied globally, defaulting to existing schedule where no override; (B) fully extrapolated candidate v3 schedule. For each deck and team show original submitted points, A, B, point delta, per-head value, point transfer, team over/under 120, 72-seat cap flag, top scoring drivers, all changed cards. Print team-level A–I rankings/differences and explain why high-scoring historical full-power decks need cuts but **do not change lists**.

Positive qualitative benchmark: organizer considered original **Nekusar × Lavinia (Team E)** an appropriately balanced, strong-Bracket-3-feeling concept. This is subjective deck-quality feedback, **not** a mandate to force its repriced points to 120. Old B1/B2 effective example: Team E 163 and A/B 446/501. At Batch3 review stage, Team G 202, H 136, I 162 with their then-latest corrections; these are **cross-check examples**, *not* guaranteed final v3 totals because globally shared price edits can update multiple teams (e.g. Basalt Monolith, Swan Song, Crop Rotation, Force of Despair, Sylvan Safekeeper, Lake of the Dead).

### Phase 5 — test, explain, and publish for review
Write stable, deterministic tests and run original suites (Batch3 agent previously reported **56 tests passing**) plus new tests: exact 100-card inventory, combined 1800 cards, correct quantities/basic lands, color identities and partner legality, one Oracle identity per pricing zone, consistency of price across deck copies and historic B1/B2/B3, no main/CZ leakage, MDFC once, properly applied latest-price precedence, negative/no-match guard, 60-life 2HG math checks, nonactivation, point-transfer calculation, 120 and 72 budget flags. Preserve legible error reporting and reproducible inputs with source commit hashes.

Deliver a short `organizer_audio_summary.md`: top ~15 proposed misses with one-line "why", price examples and counterexamples, before/after all nine teams, unresolved rules/prices, and recommendation on next deck-building test. This must be easy to read aloud. No interactive deck-list UI. Include links to sources and concrete combo/rules verification; distinguish proved rules from hypothesized strength and goldfish examples. **No fabricated match data.**

## Acceptance criteria
- Every **explicit** organizer price (including late Batch3 reversals), exception and working-value caveat is represented, traceable and consistently applied across card copies and source batches.
- The extrapolated price proposals follow efficiency/conversion/opportunity-cost/2HG and concentrate premiums on reusable enablers. Narrow weak payoffs such as Acererak may remain zero. Meaningful **counterexamples** exist for each family, showing agent didn't mechanically tax everything.
- The candidate schedule is immutable/versioned relative to prior schedule; source 18 decks and existing league rules are unchanged.
- All 18 complete decks correctly rescored for the two candidates, with team arithmetic and budget violations surfaced rather than hidden.
- Reports include a prioritized organizer review queue and a transparent explicit-versus-proposal distinction.
- Only after tests and review, propose future work to rebuild within points. **Do not activate or publish rules as official**.

## Work delivery / agent instruction
Work on a new feature branch based on `commander-doubles-deck-benchmarks`; commit your research, machine-readable files, tests and summaries there, and open a pull request back to that branch for organizer review. Reference the originating GitHub issue and this handoff. Do not merge into production/official league rules.

**Keep the model explainable.** The output is a practical card points list, not a complex per-deck optimizer with dynamic combo surcharges.
