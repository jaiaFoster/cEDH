# Commander Doubles — Purpose-built 2HG deck benchmark plan

Status: BENCHMARK DESIGN, NOT FINISHED DECKLISTS; Season 0 proposals unactivated.
Source schedule: recalibrated_point_schedule.csv at commit 4809836; apply newer organizer_premium_boundary_decisions_2026-10-20.md **as overlay** before pricing. Freeze resulting snapshot and cite hash in every scored team.

## Goal
Construct competitive but plausible 2HG teams under proposed 60 reference/player, 120 team, 72 individual maximum, with at most 12 points transferred. These are intended as qualitative power-level anchors that organizer may assess for desired Bracket-3-adjacent gameplay. No paired 2HG win-rate data; do not claim actual metagame validation. The decklists must be fully legal Commander decks: individually 100 cards including eligible commanders, singleton except basics and explicit exceptions, color identities satisfied, official banned cards removed. Verify card availability/current Oracle and rulebreaker permissions; unknown cards fail closed. No artificial filler: every card requires a strategic role. Partner commanders individually cost CZ prices.

## Benchmark roster (8 independent teams; 16 decks; 1600 total card slots)

| ID | Player A | Player B | Question tested |
| --- | --- | --- | --- |
| T-A | Tymna, the Weaver value/combat | Thrasios, Triton Hero activated value | Classic two-engine midrange; can two moderate standalone decks cooperate without oppressive early combo? |
| T-B | Najeela, the Blade-Blossom combat | Derevi, Empyrial Tactician untap/tempo | Free commander access, extra-combat potential, attack-trigger vs own resource control |
| T-C | Yuriko, the Tiger's Shadow topdeck | Yuriko, the Tiger's Shadow topdeck | Explicitly test free-CZ double-Yuriko high-CMC stacked reveals vs 60 life; actual reliability and opportunity cost |
| T-D | K'rrik, Son of Yawgmoth life-mana | White defensive/lifegain partner led by Heliod, Sun-Crowned | Shared-life budgeting; individual controller limits; does teammate support enable explosive turns? |
| T-E | Narset, Parter of Veils wheel/control as card in a legal Grixis/Esper commander shell | A separate draw-based attrition/control commander | Draw denial pricing and symmetry; test Wheel of Fortune / Windfall / Timetwister choices and Notion Thief |
| T-F | Artifact engine under a legal artifact commander (e.g. Breya, Etherium Shaper) | Creature-based combat deck with limited artifact dependency | Time Sieve, artifact density, extra team turns; enough costs to prevent effortless loops? |
| T-G | Aggressive tokens/combat commander | Life-total manipulation Sorin Markov / Test of Endurance black-white shell | Six-cost Sorin vs seven-cost Test, life thresholds, combat clock, interaction windows |
| T-H | Spell-control commander with lots of free/ordinary counters | Creature-combo/enchantment commander with Aluren or Dream Halls | Are free ordinary answers sufficient? Quantify Silence vs Chant, Misdirection/Shoal, and cross-controller combo constraints |

Commander examples are design starting points, not mandatory choices; adjust legality, color identity and feasibility. For T-A, do NOT mistakenly treat two decks each using Tymna/Thrasios as one partner deck; individual players independently select commanders. Confirm unusual repeated commanders legal across teammate decks under league rules.

## Construction requirements
- Build real complete 100-card lists for **every one of 16 seats**, with designated commanders and 99 totals accordingly (if partners, 98 main cards), exact names/Oracle IDs.
- Each paired team is a coherent competitive build with its own win architecture, mana, draw, interaction, threats and coordinated roles. Do not form an invalid combo by simply splitting a self-controlled loop across teammates.
- Create **three test levels**: (i) full-budget optimized legal roster near 120 total; (ii) same archetype with 20%-30% lower points to expose substitutions; (iii) at least 2 intentionally adversarial builds exploiting zeros. Full written lists for all main roster decks, then focused substitutions/variant files for levels ii/iii.
- Ensure contrast: 2 slow value teams, 2 combat-centric, 2 combo-centric, 2 control/denial-centric; tags may overlap.
- Include 2HG controller interaction reference for each key synergy, exact effect and disruption window. Propose explicit start-hand assumptions only when describing theoretical goldfish, never pretend empirical rates.
- For each deck: complete points ledger (main per card, zone alternate, exact total), legality validation, mana curve, lands, colored sources, ramp, draw, removal, counters, tutors, win conditions, expensive/flex slots; cite price source version.
- Budget guardrails: combined <=120, each <=72, transfers from unused 60 baseline <=12. Prefer diversified distribution (e.g. 60/60, 72/48, 50/70).
- Propose targeted playtest matchups and 5-10 opening-hand trial/mulligan decisions per team; label any results simulations if actually executed.
- Never assume free commanders mean weak decks or that theoretical earliest win proves consistency.
- Separate model feedback from organizer's human "felt like intended B3" judgment.

## Required repository outputs
Create fresh branch commander-doubles-deck-benchmarks based on latest recalibration branch. Directory commander-doubles-deck-benchmarks/:
README.md; PRICE_SNAPSHOT.md; teams.csv; decks/{TA_A,TA_B,...}.txt in Moxfield-friendly format; scored_decks.csv; role_matrix.csv; legality_report.csv; matchup_plan.md; 2hg_combo_review.md; budget_analysis.md; organizer_review_guide.md; generator/validation scripts and tests.

The organizer_review_guide.md should lead with short spoken descriptions for each **team**, emphasizing what it actually does, average reasonable winning turn under *unsupported hypothesis* where no playtests exist, primary failure modes and why it might feel above/below intended power. Do not invent observed wins or turn averages; give only sequencing estimates with explicit uncertainty.

Deliver all actual completed decklists and score them. If a proposed commander/cross-team effect proves invalid, replace it and document why. Do not modify or activate league rules, banned policy or canonical point schedule.
