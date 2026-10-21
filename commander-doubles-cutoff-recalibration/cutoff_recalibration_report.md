# Cutoff and numerical-curve comparison

Recommendation: **strict impact >77.5 in each location**, with the explicit exception ledger, nonlinear ceil(15*(max(0,s−tau)/25)^1.5). This is a policy choice to remove ordinary utility around75–77 while retaining most reviewed high-ceiling specialist80 floor entries. It is not an estimated natural break. At80 the inherited specialist floor itself falls free because comparison is strict>, exposing many specialized engine omissions. At70–72.5 ordinary fixing/utility receives costs. 75 still taxes ordinary interaction without exceptions. 77.5 is the highest tested threshold retaining a full two-point judgment-perturbation margin below the explicitly documented specialist floor80;79.5 is also tested but admits more membership flips under that perturbation; extra-turn/life converters are separately reviewed because inherited low ratings miss them at every tested threshold.

No impact value was modified to move a card across a boundary. The floor80 is inherited subjective admission policy, not measured ceiling; specialist_floor_control.csv removes it without fitting. Exact prices are policy choices and approved exceptions can reverse model ordering. Before/after boundary files show the same unedited impacts and20 nearest cards on each side per zone, cutoff and stage; changed price does not imply changed impact.

Four exception stages: curve_only (diagnostic, intentionally violates human anchors); organizer_only (explicit prices/ranges/minimum and zero qualitative anchors); calibrated_working (also previous assistant numbers and new working selections); recommended (also pending family/omission proposals). All stages use the same cohorts and frozen impact vectors. The organizer_only selected price within each range is a working implementation, not exact organizer approval. No coefficients were fitted to deck labels or reviewer rankings.

| cutoff | exception_stage | pointed_main_cards | pointed_commander_options | pointed_identities | median | p90 |
| --- | --- | --- | --- | --- | --- | --- |
| 70 | curve_only | 388 | 135 | 487 | 22.0 | 30.0 |
| 70 | organizer_only | 386 | 130 | 485 | 21.0 | 29.7 |
| 70 | calibrated_working | 397 | 130 | 496 | 17.0 | 26.0 |
| 70 | recommended | 434 | 133 | 533 | 17.0 | 26.7 |
| 72.5 | curve_only | 289 | 107 | 364 | 18.0 | 24.0 |
| 72.5 | organizer_only | 289 | 102 | 364 | 18.0 | 24.0 |
| 72.5 | calibrated_working | 302 | 102 | 377 | 16.0 | 24.0 |
| 72.5 | recommended | 342 | 106 | 417 | 16.5 | 24.0 |
| 75 | curve_only | 252 | 84 | 304 | 15.0 | 20.0 |
| 75 | organizer_only | 255 | 79 | 307 | 15.0 | 20.0 |
| 75 | calibrated_working | 270 | 79 | 322 | 16.0 | 22.0 |
| 75 | recommended | 310 | 83 | 362 | 16.0 | 23.0 |
| 77.5 | curve_only | 176 | 63 | 222 | 12.0 | 15.0 |
| 77.5 | organizer_only | 184 | 58 | 226 | 12.0 | 15.0 |
| 77.5 | calibrated_working | 215 | 58 | 257 | 16.0 | 20.7 |
| 77.5 | recommended | 278 | 64 | 320 | 16.0 | 22.0 |
| 79.5 | curve_only | 166 | 44 | 196 | 10.0 | 12.0 |
| 79.5 | organizer_only | 174 | 39 | 200 | 10.0 | 12.7 |
| 79.5 | calibrated_working | 206 | 39 | 232 | 16.0 | 20.0 |
| 79.5 | recommended | 271 | 46 | 298 | 16.0 | 21.0 |
| 80 | curve_only | 117 | 40 | 152 | 10.0 | 11.0 |
| 80 | organizer_only | 127 | 35 | 157 | 10.0 | 11.0 |
| 80 | calibrated_working | 165 | 35 | 195 | 16.0 | 20.0 |
| 80 | recommended | 235 | 42 | 265 | 16.0 | 21.0 |

## Curve resolution at proposed threshold

| curve | cohort | median | p10 | p90 | main_price_p50 | main_price_p90 | main_price_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| existing_tiers | bracket3_declared | 61.5 | 18.0 | 133.1 | 3.0 | 9.0 | 15 |
| existing_tiers | cedh_holdout | 266.0 | 151.0 | 421.0 | 3.0 | 9.0 | 15 |
| existing_tiers | official_precons | 16.0 | 15.0 | 22.0 | 3.0 | 9.0 | 15 |
| fine_integer | bracket3_declared | 68.0 | 19.0 | 144.1 | 3.0 | 9.0 | 15 |
| fine_integer | cedh_holdout | 285.0 | 164.0 | 444.0 | 3.0 | 9.0 | 15 |
| fine_integer | official_precons | 16.0 | 15.0 | 22.7 | 3.0 | 9.0 | 15 |
| nonlinear | bracket3_declared | 62.5 | 17.9 | 132.1 | 3.0 | 9.0 | 15 |
| nonlinear | cedh_holdout | 265.0 | 150.9 | 420.1 | 3.0 | 9.0 | 15 |
| nonlinear | official_precons | 16.0 | 15.0 | 22.0 | 3.0 | 9.0 | 15 |

Existing tier bands are0/1/3/5/8/12 plus20 when the impact-minus-cutoff gap exceeds25. That20 band is unreachable at the recommended77.5 threshold but is reachable at70; it remains in the comparison. Fine integer is ceil(0.6*gap), maximum15 at cutoff75 or14 at77.5; nonlinear has same15-at100/75 anchor and finer low-tail progression, making strongest resources disproportionately costly. Explicit human working prices remain fixed across curves and cutoffs to isolate the rest of the list. A card barely above a cutoff costs at least one under all three: no statistical precision is implied by ceil. No per-deck rescaling.

Selected nonlinear price examples at tau77.5: frozen impact80→1;85→3;90→6;95→9;100→13. Demonic/Sol15 and other prices are explicit working/calibration exceptions, not secretly shifted impacts. Finer values are practical integers; coarse-tier jumps alone provide no validation. Pending15-point life engines can exceed global score-curve maximum13 deliberately.

## Named threshold counterexamples

| card_name | issue | curve_only_points | proposed_points | judgment |
| --- | --- | --- | --- | --- |
| Drannith Magistrate | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Asymmetric nonhand casting denial plus opposing commander access; lock review separate. |
| Temporal Mastery | reviewed_exceptional_engine_omitted_by_curve | 0 | 7 | Two-mana miracle team turn requires topdeck/timing; normal seven mana. |
| Savor the Moment | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Three mana extra team draw/land/combat but whole friendly untap skipped. |
| Time Stretch | reviewed_exceptional_engine_omitted_by_curve | 0 | 6 | Ten mana for two team turns; slower deployment than cheap extra turns. |
| Walk the Aeons | reviewed_exceptional_engine_omitted_by_curve | 0 | 6 | Six mana team turn; buyback sacrifices three own Islands. |
| Part the Waterveil | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Six mana sorcery team turn, self-exile; awakened land optional expensive mode. |
| Karn's Temporal Sundering | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Six mana legendary sorcery requires own legendary permanent. |
| Chance for Glory | reviewed_exceptional_engine_omitted_by_curve | 0 | 7 | Three mana instant team turn; delayed loss affects team, all own creatures indestructible. |
| Stitch in Time | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Three mana expected half extra team turn; coin failure remains real. |
| Time Sieve | reviewed_exceptional_engine_omitted_by_curve | 0 | 8 | Repeatable two-mana team-turn converter; five own artifacts each activation. |
| Wanderwine Prophets | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Six mana champion creature; combat and own Merfolk sacrifice setup. |
| Sage of Hours | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Repeatable counter-to-team-turn converter; removes five own counters. |
| Timestream Navigator | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Ascend, untapped creature and four mana needed; summoning sickness and recursion matter. |
| Lighthouse Chronologist | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Nine mana total level investment; opponent end step awards team turn, not two. |
| Black Market Connections | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Repeat repeatable life-for-cards/token resources; sixty gives a larger reservoir. |
| Doom Whisperer | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Repeatable shared-life surveil for own library; five mana deployment. |
| Zirda, the Dawnwaker | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Broad permanent activation reduction; own permanents only, specialized loop ceiling. |
| Chancellor of the Tangle | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Opening-hand reveal supplies own green on first shared main phase; near ESG one-shot acceleration with opening-only constraint. |
| Alrund's Epiphany | reviewed_exceptional_engine_omitted_by_curve | 0 | 5 | Seven mana or foretell setup plus six; one team turn and two bodies, self-exile. |
| Beacon of Tomorrows | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Eight-mana one team turn, recyclable but no free repeat. |
| Seedtime | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Two-mana instant team turn only during own turn after opposing blue spell; reactive setup limits applicability. |
| Magistrate's Scepter | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Repeatable team-turn converter requires own three counters, tap and substantial charging/setup. |
| Gonti's Aether Heart | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Six-mana energy converter, eight energy plus self-exile for team turn. |
| Notorious Throng | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Six-mana prowl plus prior Rogue damage; extra team turn and tokens require actual combat setup. |
| Medomai the Ageless | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Six-mana combat-damage team turn; cannot attack during extra turns, recursion/cloning not free. |
| Kang the Conqueror | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Four-mana creature plus power-up investment; extra turn shuts power-up activation for that turn. |
| Timesifter | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Five-mana global topdeck contest; friendly manipulation can bias recurring team turns, opponents may win too. |
| Ugin's Nexus | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Five-mana sacrifice/exile converter with extra-turn prevention while on board; recurring requires setup. |
| Rise of the Eldrazi | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Twelve mana including CCC; uncounterable broad impact plus one team turn, not cheap acceleration. |
| Stranglehold | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Four-mana asymmetric opposing search/extra-turn denial; below cheap proactive protection. |
| Hatred | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Five-mana instant can pay shared life to make lethal unblocked attacker; needs combat/survival and is disruptable. |
| Unspeakable Symbol | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Three-mana repeat life-to-own-creature counters; shared sixty enables commander-damage threat, setup remains. |
| Nature's Will | reviewed_exceptional_engine_omitted_by_curve | 0 | 4 | Four-mana repeated whole-land untap plus opposing-head land tap; exceptional combat-resource engine, not an interchangeable payoff. |
| Bear Umbra | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Four-mana Aura grants repeat whole-land untap on attack, no combat connection needed; granted trigger belongs to creature controller. |
| Sword of Feast and Famine | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Three mana plus equip two, repeat land untap/discard on connection; trigger belongs to equipment controller even on friendly creature. |
| Druids' Repository | reviewed_exceptional_engine_omitted_by_curve | 0 | 3 | Three-mana repeat attack-to-any-color mana store; token/extra-combat setup needed, but exceptional resource conversion. |

## Subjectivity sensitivity

official_precons:100 independent ±2-impact scenarios, median deck score range 16–16. bracket3_declared:100 independent ±2-impact scenarios, median deck score range 62–64. cedh_holdout:100 independent ±2-impact scenarios, median deck score range 264–270.5. Legal pointed-identity range 315–330 across those scenarios. These are sensitivity bounds from a chosen perturbation model, not confidence intervals. Overrides held fixed, so they mechanically reduce sensitivity.


Card prices for ten largest non-explicit main prices are perturbed ±1 separately in premium_price_sensitivity.csv. This is a local numerical stress test, not an organizer-approved revision; approved bounds are not silently changed in the actual schedule. Exact all-pair budget comparisons in budget_stress_test.csv demonstrate both ordinary cohort overlap and residual low-cost competitive labels.

cutoff_color_concentration.csv reports color-identity counts at every cutoff and curve. This is actual identity distribution, not a requirement for equal color prices. Category/archetype labels in candidate metadata are nomination judgments; no reliable archetype win-rate cohort exists. Tribal/synergy lists may cost less intentionally, so no hidden archetype normalization is applied.

The source's 423 low-confidence top1000 entries remain a material discovery gap. Reviewing all routing and functional nomination flags does not make those assessments independently sound. Current-card additions and all legal known identities outside the pool are exported for nomination; no rating is inferred from mere rarity or obscurity. Playtesting is needed before claiming complete exceptional-card capture.


## Fixed-exception dependence and near-floor stability

| cohort | share_of_all_points_from_fixed_exceptions |
| --- | --- |
| adversarial_fixture | 1.0 |
| bracket3_declared | 0.89 |
| cedh_holdout | 0.907 |
| official_precons | 0.973 |

| cutoff | median_membership_flips | median_membership_Jaccard |
| --- | --- | --- |
| 70 | 31.0 | 0.943 |
| 72.5 | 41.0 | 0.908 |
| 75 | 21.0 | 0.944 |
| 77.5 | 13.0 | 0.96 |
| 79.5 | 21.5 | 0.929 |
| 80 | 27.0 | 0.905 |

The measured dominance of fixed exceptions limits what a cutoff alone accomplishes. This is a human-led candidate schedule, not a statistically learned power function.79.5 is a plausible smaller policy list if the organizer prefers sparsity over the stated perturbation margin;77.5 is recommended for the more stable starting pool, not because of an observed win-rate optimum.
