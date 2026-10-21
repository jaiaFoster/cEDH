# Commander Doubles — Tournament-Sourced Specialist Deck Construction Agent

## Mandate
Build **nine high-strength, budget-legal two-headed-giant (2HG) teams** (18 separate Commander decks), using real tournament cEDH lists and genuine established Legacy/Modern/Vintage archetypes as **research foundations**, then adapting aggressively for 2HG. Optimize as strongly as possible inside the proposed **120-point combined team budget**, not for a generic casual deck aesthetic. These decks are the actual benchmarks the organizer will inspect to determine whether the resulting play experience is Bracket-3-adjacent. **Deliver in batches of THREE TEAMS** and preserve feedback for later batches. Do not claim tournament evidence proves a custom team pairing.

Repository: `jaiaFoster/cEDH`. Base branch: `commander-doubles-cutoff-recalibration`; use latest commit and branch off `commander-doubles-deck-benchmarks` (or a new numbered successor if name exists). Do not alter or activate official league rules, bans, or canonical pricing.

## Essential pinned sources
Read, in order:
1. `commander-doubles-cutoff-recalibration/benchmark_roster_locked_2026-10-20.md` (nine teams explicitly organizer-approved).
2. `commander-doubles-cutoff-recalibration/purpose_built_deck_benchmark_brief_v2.md` (correct partners, archetype identities, role separation).
3. `commander-doubles-cutoff-recalibration/recalibrated_point_schedule.csv` (baseline list; **DOES NOT YET APPLY NEWEST NUMERICAL CHANGES**).
4. `commander-doubles-cutoff-recalibration/organizer_premium_boundary_decisions_2026-10-20.md` (17 later explicit numeric construction overrides; MUST apply).
5. `commander-doubles-cutoff-recalibration/calibration_precedence.json`, `organizer_approval_queue.md`, `two_hg_rules_cache.jsonl`, `recalibration_executive_summary.md`.
6. Earlier `commander-doubles-final-audit/` analysis, adversarial deck cores, and the source Card/Oracle lookup and point-calculator scripts.

## Pricing and legality nonnegotiables
- Use the **>77.5 impact cutoff candidate**, nonlinear numeric schedule, and all recorded organizer-authorized location overrides, especially the 17 latest changes. Create a **frozen effective price snapshot** that overlays the new decisions on the recalibrated CSV by Oracle ID + exact zone. Preserve SHA-256/hash, source commit, exception history and version in each deck output.
- Prices are fixed additive costs per card identity, with **main 99 and CZ separate alternatives**. Partners each count separately in the command zone. No pairing/synergy surtax.
- Each player has a fully independent 100-card Commander deck: one commander + 99 or two Partners + 98. Verify eligible Partner pairs. Color identity, singleton, official commander/2HG bans, companion/rulebreaker corner cases. Both decks count toward team budget. Shared team turns/life ≠ shared mana, permanent control, graveyards, hands or libraries.
- **Budget rule:** <=120 combined; each deck <=72; nominal 60 per player with up to 12 unused points transferred from the teammate. Report reference allocations and actual costs. Prefer spending points efficiently near the cap but don't artificially add poor cards just to exhaust it.
- Do not use Primeval Titan in any official-legal benchmark. If desired, make a **clearly segregated experimental-unban sandbox**, not part of the 18 approved legal decks. Unknown/future rulebreaker permissions fail closed pending a documented ruling.
- Commander legal status and up-to-date Oracle need validation. If any named commander or strategy violates current rules, replace only the problematic component with a suitable legal equivalent, with clear justification and preserved archetype identity.

## Locked nine-team archetype roster
**Batch 1 — Baseline and free-commander stress tests**
A. **Blue Farm × Dawnwaker:** A1 Tymna the Weaver + Kraum, Ludevic's Opus — Blue Farm, tempo/card-farm/protected win; A2 Thrasios, Triton Hero + Bruse Tarl, Boorish Herder — Dawnwaker, dorks/activated-value/toolbox mana conversion. They are **two separate Partner decks**, not a single Tymna-and-Thrasios split.
B. **Warrior Tempo × Bant Pod:** B1 Najeela, the Blade-Blossom — Warrior Tempo/extra combats; B2 Derevi, Empyrial Tactician — Bant creature Pod/toolbox/untap. Validate shared-team extra combats, triggers and distinct control of creatures.
C. **Double Ninjas:** C1 Yuriko, the Tiger's Shadow — Ninja Tempo/Delver; C2 Yuriko, the Tiger's Shadow — Big-Flip Topdeck Combo. Individually legal decks, distinct 99s. Benchmark the actual reliability/opportunity cost of 60-life double-Yuriko explosive turns.

**Batch 2 — Life conversion, wheels, artifact-control**
D. **Mono-Black Storm × Soul Sisters:** D1 K'rrik, Son of Yawgmoth — Black Storm/Life-Mana; D2 Heliod, Sun-Crowned — Soul Sisters/Lifegain White Control.
E. **Grixis Wheels × Azorius Prison:** E1 Nekusar, the Mindrazer — Wheels/Draw Punishment; E2 Lavinia, Azorius Renegade — Prison/Draw-Go. Test both-opponent draw triggers, Narset/Notion Thief and wheel premiums.
F. **Artifact Prison × Dimir Draw-Go:** F1 Breya, Etherium Shaper — Artifact Control/Combo including Time Sieve; F2 Talion, the Kindly Lord — UB Draw-Go/Stack Control. Distinct resilience to counterspells versus permanent/graveyard disruption; no forced arbitrary combat subtheme.

**Batch 3 — Endurance, creature combo, lands**
G. **Mono-Black Pox × Enchantress Lifegain:** G1 Sheoldred, the Apocalypse — Mono-Black Pox/Sorin Control; G2 Oloro, Ageless Ascetic — Esper Lifegain/Test of Endurance Enchantress Control.
H. **Esper Draw-Go × Bant Aluren:** H1 Tymna the Weaver + Malcolm, Keen-Eyed Navigator — Esper Tempo-Farm/Draw-Go; H2 Chulane, Teller of Tales — Bant Aluren Creature-Combo Value. Note Dream Halls requires a distinct appropriate alternative archetype; do not force it into this list.
I. **Gitrog Lands × Azorius Stoneblade:** I1 The Gitrog Monster — Lands/Loam/Dakmor/recursion; I2 appropriate eligible Azorius commander researched from established Stoneblade/control traditions, preferably with an actual published pedigree. Explicitly document commander choice. No Primeval Titan in legal list.

Archetype labels identify the *deck's engine*, not simply a generic category. For each head list ancestry, specific cards that implement it, primary/redundant wins, early plays, and likely opposing hate. When stronger than original archetype constraints, explain 2HG improvement rather than blindly copy staples.

## Research process
1. Locate and cite **actual decklist URLs**, authors, dates, player registration/event if available, result where verified, and retrieval dates for each head's closest archetype. Prioritize recent cEDH tournament listings (TopDeck.gg, Moxfield decklists linked to events), then well-established cEDH primers; use authentic Legacy/Modern/Vintage list history for archetype analogy. Don't invent results, entries or exact lists. If no event pedigree exists, label it adapted/invented and explain.
2. Gather at least 2 credible list foundations per head if available, note disagreements and derive core packages. More research for novel 2HG builds where no direct precedent exists.
3. Build and validate each head as a **real complete legal 100-card list**; do not pad with arbitrary zero-cost cards. Keep mana, land count, color requirements, tutors, draw, interaction, card economy and win lines intentional. Commander partners use 98-card library.
4. Score each candidate from pinned effective schedule, estimate cost gap versus competitive ancestor, then iteratively remove the **least essential points-per-strategic-value** cards and replace with best zero/low cost alternatives to reach individual/team envelope. Explain notable removals, upgrades, price traps and alternatives. Consider a 48/72 asymmetrical distribution where strategically superior.
5. Check every cross-teammate interaction with exact Oracle/controller rules. Separate legal synergy from false split-owner combos. For wins cite necessary state/priority windows, interruption points and required same-controller restrictions. No imaginary shared card pools.
6. Stress-test each 2HG team against representative interactive and proactive opponent pairs, assess major shared vulnerabilities, landbase pressure, ability to play through removal/stax, and 2HG-specific early-win ceiling. If simulations/goldfish/mulligan sampling are run, publish seeds/sample sizes and methodology. Otherwise explain turn-sequence *possibilities* only—never invent win rates, average turns, or observed gameplay.
7. **Stop after finishing each three-team batch** with fully validated outputs and submit its review packet for organizer assessment. Do not start the next batch before organizer feedback. If a tool has no actual asynchronous/stop capability, finish currently permitted batch in one execution and clearly hand off.

## Per-batch required deliverables
Directory `commander-doubles-deck-benchmarks/`:
- `price_snapshot.csv` plus `PRICE_SNAPSHOT.md` with effective overriding logic, source SHA, effective prices for all known legal identities, exact cutoff and checksum.
- `sources.csv`: source URL, author, archetype, date/event/result if verified, deck/head linked, how used and trust level.
- `teams.csv`, `decks/<id>.txt` (Moxfield-importable), `decks/<id>.json` (Oracle keyed with commander slots), and full `score_ledger.csv` (every individual card and points, CZ alternative for each).
- `legality_report.csv`: card count, singleton, color identity, allowed card database version, bans, partner eligibility, budget pass/fail, no unknown-card silent zeros.
- `archetype_lineage.md`: ancestral deck packages, kept/cut/replaced, reasons, and impact of new pricing.
- `team_synergy_and_counterplay.md`: exact two-head controller-aware plan, independent wins, anticipated hate and counterplay.
- `budget_tradeoffs.md`: individual and team totals, efficiency of premium picks, unused points; why each card over ~5 points survived price pressure.
- `opening_hands_and_goldfish.md`: labeled demonstrations, not pseudo-measured success statistics.
- `organizer_audio_review.md`: **spoken, concise 120–180-word briefing per team** explaining both actual archetypes, how the pair wins, what an early/midgame looks like, interaction, weak points, and whether it appears too weak, target-like or potentially problematic. Provide a short tabular quick-compare too.
- `tests/` and script to regenerate prices and validity. Commit exact batch revisions without overwriting earlier approved batches.

## Success gates
- Three exact chosen teams and six fully populated decks per batch, no missing slots, no invented tournament results.
- Decks are genuinely *optimized for power within the budget*, not weak decklists designed to reassure the organizer.
- No failed deck/legal/budget check or unresolved Oracle name is presented as passing.
- Output the three team profiles first for spoken review, then concise summaries and GitHub links.
- Each batch remains `season0-proposed` until organizer approval.
- After organizer gives qualitative judgments, create v2 candidates/reprice diagnostics if needed and advance to next batch.

**Begin Batch 1 (A–C) now.** Research base lists, produce six complete legal decks and all checks, commit them, and report source-specific findings. Do not begin Batch 2 until organizer responds.