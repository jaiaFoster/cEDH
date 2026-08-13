# SIM-001 MULL-005R — Full 98-Card T1-T3 Trajectory Audit

Subject: `tymna-thrasios-treefarm-v1` (deck_hash `4edee0fc60768fcd759a2e9fd3c34277d9d37c0d6a27a663ea7beff76b05e20a`), matches the frozen 98 used throughout SOLO-002 through MULL-005 - no discrepancy found, per section 0.

Findings: 25 total — VERIFIED: 17, REJECTED: 1, CANDIDATE: 7

Every finding below is grounded in real Oracle text pulled from `data/cards_cache/oracle-2026-08-12` for this exact deck (see `t1_t3_trajectory_audit.json` for the structured version). Status legend: VERIFIED (confirmed, either a real correction or confirmed-already-correct), CANDIDATE (mechanically real, deferred as low-T1-T3-frequency, disclosed), BLOCKED (unreachable given this simulator's scope), REJECTED (investigated, not material).

## OCULUS-001 — Abhorrent Oculus
**Status:** VERIFIED

**Mechanic:** Real Oracle text: 'As an ADDITIONAL cost to cast this spell, exile six cards from your graveyard.' (Not an alternative cost, as the assignment's prose puts it - the practical conclusion is identical: it is unconditionally required on top of {2}{U}, confirmed by ruling 'Abhorrent Oculus's additional cost must be paid even if it's cast without paying its mana cost or for any alternative cost.') A T1-T3 opener has essentially never accumulated 6 graveyard cards through only 3 turns of normal development, so hard-casting Oculus from hand is not a realistic T1-T3 line in this deck regardless of mana.

**Legal prerequisites:** 6 cards in graveyard + {2}{U} mana; unreachable via normal T1-T3 play in this deck.
**Earliest relevant turn:** None
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Oculus was not classified into ENGINES/TUTORS/ACCELERATION/INTERACTION_CASTABLE, so the greedy policy's _card_class() returned 'other', which has no bucket in DEFAULT_PRIORITY - Oculus was therefore NEVER hard-cast, but by ACCIDENT (an unhandled classification), not because its additional cost was understood. This is a correctness risk: adding Oculus to ENGINES for any future reason would silently start hard-casting it for {2}{U} alone, ignoring the graveyard requirement entirely.
**Expected direction of bias:** None today (accidentally correct) - but a real landmine for future changes.
**Resolution:** Made explicit: uncastable-from-hand rule enforced in code (OCULUS_HAND_CASTABLE=False path) with a regression test, not left as an accident of classification.

## OCULUS-002 — Birthing Pod, Abhorrent Oculus
**Status:** VERIFIED

**Mechanic:** Birthing Pod: '{1}{G/P}, T, Sacrifice a creature: Search your library for a creature card with mana value equal to 1 plus the sacrificed creature's mana value, PUT THAT CARD ONTO THE BATTLEFIELD, then shuffle.' Putting a card onto the battlefield via a search effect completely bypasses its own mana cost AND any additional cost (the exile-6 requirement is a cost of CASTING Oculus, and Pod never casts it). Sacrificing any MV2 creature (Archivist of Oghma, Badgermole Cub, Devoted Druid, Faerie Mastermind, Gilded Drake, Kinnan, Oboro Breezecaller, Orcish Bowmasters, Shang-Chi, Voice of Victory, Volatile Stormdrake) finds Oculus (MV3) directly.

**Legal prerequisites:** Pod on battlefield + {1}{G/P} (payable as {1} + 2 life) + a MV2 creature to sacrifice + sorcery timing (main phase, empty stack).
**Earliest relevant turn:** 3
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Pod's activated ability was never simulated at all in any prior phase - Pod, once cast, was inert.
**Expected direction of bias:** MULL-005 substantially UNDER-rated Birthing Pod and never credited Oculus access through it.
**Resolution:** Built as POD_TO_OCULUS named trajectory - see pod_trajectory_registry.json / oculus_route_registry.json.

## OCULUS-003 — Eldritch Evolution, Abhorrent Oculus
**Status:** VERIFIED

**Mechanic:** 'As an additional cost to cast this spell, sacrifice a creature. Search your library for a creature card with mana value X or less, where X is 2 plus the sacrificed creature's mana value. PUT THAT CARD ONTO THE BATTLEFIELD.' Sacrificing ANY MV1 creature (Avacyn's Pilgrim, Birds of Paradise, Deathrite Shaman, Delighted Halfling, Elves of Deep Shadow, Esper Sentinel, Noble Hierarch) gives X=3, finding Oculus directly for a total of {1}{G}{G} (3 mana) plus a 1-drop already in play. This is the CHEAPEST verified Oculus route in the deck - cheaper than Pod, since it needs no prior investment beyond a T1 mana dork.

**Legal prerequisites:** {1}{G}{G} (3 mana) + a MV1 creature on battlefield to sacrifice.
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Eldritch Evolution was in TUTORS but its target search was never resolved (forced_tutor_target only ever added a card to HAND, not battlefield) - this specific route was invisible to every prior phase.
**Expected direction of bias:** MULL-005 substantially undercounted Oculus reachability - this is likely the single most common T2-T3 Oculus line in the deck given how many cheap 1-drop dorks it plays.
**Resolution:** Built as ELDRITCH_EVOLUTION_TO_OCULUS route in oculus_route_registry.json.

## OCULUS-004 — Finale of Devastation, Nature's Rhythm, Chord of Calling, Abhorrent Oculus
**Status:** VERIFIED

**Mechanic:** All three: 'Search your library [and/or graveyard] for a creature card with mana value X or less, PUT IT ONTO THE BATTLEFIELD.' X=3 finds Oculus. Finale/Rhythm cost {X}{G}{G} (5 total mana for X=3); Chord costs {X}{G}{G}{G} but has Convoke (creatures can help pay, reducing the real mana needed when board-developed).

**Legal prerequisites:** 5+ generic/G mana (Finale/Rhythm) or convoke-reduced mana + creatures to tap (Chord).
**Earliest relevant turn:** 3
**Already represented in MULL-005:** Named in the assignment's own suspected list (Finale, Rhythm) but never actually simulated as battlefield-search - MULL-005's forced_tutor_target put the card in HAND, not onto the battlefield, for every tutor uniformly.
**MULL-005 mis-model/omission:** X-cost spells were explicitly unsupported by the greedy dev policy ('X spells not modeled in this greedy dev policy' - opening_hand_policy.py) - Finale/Rhythm/Chord could never be cast AT ALL by the prior engine, for any purpose, regardless of tutor-target logic.
**Expected direction of bias:** MULL-005 could not reach these lines even in principle - a structural gap, not just a scoring gap.
**Resolution:** X-spell casting added for these three specific cards in the Oculus/Pod-chain context (bounded, not a general X-spell solver - see module docstring's own X-spell-avoidance note, preserved for all OTHER X spells).

## OCULUS-005 — Ranger-Captain of Eos, Spellseeker, Demonic Tutor, Vampiric Tutor, Imperial Seal, Enlightened Tutor, Crop Rotation, Sowing Mycospawn
**Status:** REJECTED

**Mechanic:** None of these put a card onto the battlefield - Ranger-Captain/Spellseeker put a found card into HAND (and only search MV<=1 creatures / instants&sorceries respectively, neither of which is Oculus at MV3 anyway); Demonic Tutor puts into hand; Vampiric Tutor/Imperial Seal/Enlightened Tutor put on TOP OF LIBRARY (delayed to next draw, and Enlightened Tutor can only find artifacts/enchantments - Oculus is a creature, illegal target); Crop Rotation/Sowing Mycospawn only search lands. NONE of these are legal Oculus routes.

**Legal prerequisites:** N/A - not legal targets/effects for Oculus.
**Earliest relevant turn:** None
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** None - correctly excluded.
**Expected direction of bias:** None.
**Resolution:** Explicitly excluded from oculus_route_registry.json's VERIFIED route list.

## OCULUS-006 — Kinnan, Bonder Prodigy, Abhorrent Oculus
**Status:** CANDIDATE

**Mechanic:** Kinnan's {5}{G}{U} ability: 'Look at the top five cards of your library. You may put a non-Human creature card from among them onto the battlefield.' Oculus (an Eye, non-Human) legally qualifies and would also bypass its cost if found this way - but this is a random top-5 LOOK, not a search, and costs 7 total mana.

**Legal prerequisites:** 7 mana + Kinnan on battlefield + Oculus randomly among the top 5 cards looked at.
**Earliest relevant turn:** 4
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Not modeled; not previously considered.
**Expected direction of bias:** Negligible - 7 mana is essentially unreachable by T3, and the find is non-deterministic. Not built this phase.
**Resolution:** Deferred, disclosed. Not a T1-T3-relevant route.

## POD-001 — Birthing Pod
**Status:** VERIFIED

**Mechanic:** Full activation legality: '{1}{G/P}, T, Sacrifice a creature: Search... put onto battlefield... Activate only as a sorcery.' Requires Pod untapped, a legal creature to sacrifice (commanders are NOT legal Pod fodder - they aren't library cards and Pod's search targets the LIBRARY, and sac'ing a commander would be legal but pointless since commanders have no mana value chain target relevance here), and sorcery-speed timing (already implicitly satisfied by this model's turn-based, no-stack structure).

**Legal prerequisites:** Pod on battlefield, untapped; {1}{G/P} payable; a non-commander creature on battlefield to sacrifice.
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Entirely unmodeled - Pod's activated ability was never invoked.
**Expected direction of bias:** MULL-005 treated Pod as a dead card once cast; every downstream Pod trajectory (not just Oculus) was invisible.
**Resolution:** Built full Pod activation model (cast, activate, chain up to fodder availability) - see pod_trajectory_registry.json.

## POD-002 — Birthing Pod, {3}{G/P}, {1}{G/P}
**Status:** VERIFIED

**Mechanic:** Both Pod's cast cost and activation cost use Phyrexian mana ({G/P}: pay G OR 2 life). This project's existing parse_cost() drops the Phyrexian alternative entirely and treats {G/P} as a forced-G pip (parts = [p for p in t.split('/') if p in COLORS] silently discards the 'P' half). This is a pre-existing correctness bug, not new to MULL-005R, that materially undercounts Pod's real castability whenever G is unavailable but life is not a constraint (this model's life totals, per opening_hand_model.py's own documented philosophy, 'never block a line').

**Legal prerequisites:** N/A - a payment-engine bug, not a card-legality question.
**Earliest relevant turn:** None
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Pre-existing bug in parse_cost(), inherited unchanged through every prior phase (SOLO-002 through MULL-005). Only 2 cards in the deck use Phyrexian mana (Birthing Pod's {G/P}x2, Mental Misstep's {U/P} - the latter already has its own dedicated 'always_via_life' override in interaction_model.py's ALT_COST_SPECS, so it was NOT actually affected by this bug in practice).
**Expected direction of bias:** UNDER-counts Pod castability in G-starved hands specifically (a real but narrow effect, since this deck's mana base is not badly G-light).
**Resolution:** Fixed generally in parse_cost()/the payment engine (phyrexian pips payable via life), not special-cased only for Pod - benefits any future Phyrexian-mana card too.

## POD-003 — Derevi, Empyrial Tactician, Clever Impersonator, Birthing Pod
**Status:** CANDIDATE

**Mechanic:** Derevi's ETB/combat-damage trigger ('you may tap or untap target permanent') could untap Pod for an extra activation same turn. Clever Impersonator ('enter as a copy of any nonland permanent') could copy an already-resolved Pod for a second Pod body. Both are mechanically real.

**Legal prerequisites:** Derevi: {G}{W}{U} hard-cast (3 specific colors) or {1}{G}{W}{U} from command zone, PLUS Pod already resolved and activated once, PLUS enough mana/fodder for a second activation, all by T3 - a 4-5+ card, 3-color, multi-permanent convergence. Impersonator: {2}{U}{U} PLUS Pod already resolved PLUS a second full activation's worth of mana/fodder, also by T3.
**Earliest relevant turn:** 3
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Not modeled; not previously considered.
**Expected direction of bias:** Real but expected to be a negligible-frequency T1-T3 event (multiple specific cards + heavy mana simultaneously) - consistent with the assignment's own 'do not require exhaustive late-game Pod-tree solving' allowance. Not built as a general simulation this phase; flagged for a future phase if census data shows it matters more than expected.
**Resolution:** Deferred, disclosed. Both cards are correctly castable in the base engine (Derevi already a normal 3-color legendary creature cast, Impersonator already a normal creature cast); only the SPECIFIC 'copy/untap Pod for a second activation same turn' combo sequencing is not specially modeled.

## SURV-001 — Survival of the Fittest
**Status:** VERIFIED

**Mechanic:** '{G}, Discard a creature card: Search your library for a creature card, reveal it, put it into your hand, then shuffle.' Repeatable (no tap symbol - only mana + a creature card discard), so multiple activations per turn are legal if enough mana and creature cards in hand exist. Found card goes to HAND, not battlefield - Survival does NOT bypass a found creature's cast cost (unlike Pod/Chord/Finale/Rhythm/Eldritch Evolution).

**Legal prerequisites:** Survival on battlefield; {G} per activation; a creature card in hand (OTHER than the one being discarded is not required - discarding the only creature card in hand is legal and simply removes Survival's own future fuel).
**Earliest relevant turn:** 2
**Already represented in MULL-005:** Presence-gated in _tier_b_supported (a discardable creature in hand), but never activated - the engine never actually discarded a creature and fetched anything.
**MULL-005 mis-model/omission:** Same class of omission as Pod - the activated ability itself was never invoked, only its precondition checked.
**Expected direction of bias:** MULL-005 under-credited any hand where Survival could productively convert an excess/redundant creature into a needed one.
**Resolution:** Built full Survival activation model (repeatable while mana+fuel allow) - see survival_trajectory_registry.json.

## TITHE-001 — Smothering Tithe
**Status:** VERIFIED

**Mechanic:** 'Whenever an opponent draws a card, that player may pay {2}. If the player doesn't, you create a Treasure token.' This trigger is 100% opponent-draw-dependent and can NEVER fire in this project's solo/no-opponent goldfish model - mechanically identical in this respect to Rhystic Study ('whenever an opponent casts a spell') and Mystic Remora ('whenever an opponent casts a noncreature spell'), both of which are ALREADY in ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE and credited on deployment alone (no opponent-action support-check gate). Tithe, by contrast, was placed in TIER_C_STRUCTURALLY_INERT (SOLO-003) and explicitly zeroed out in every trajectory metric - an INCONSISTENCY, not a principled distinction: both categories of card are equally un-simulatable by this model, since neither this nor any prior phase has ever modeled opponent behavior.

**Legal prerequisites:** N/A - a scoring-consistency question, not a legality question.
**Earliest relevant turn:** None
**Already represented in MULL-005:** Deliberately zeroed (TIER_C_STRUCTURALLY_INERT), inherited unchanged from SOLO-003 through MULL-005.
**MULL-005 mis-model/omission:** Genuine inconsistency: Rhystic Study/Mystic Remora (also opponent-cast-triggered) get full deployment-credit; Smothering Tithe (opponent-draw-triggered) gets zero credit. No mechanical distinction justifies treating these differently - both are 'assume productive once deployed, because in any real 4-player pod the triggering opponent action is a near-certainty' modeling assumptions, not simulated facts.
**Expected direction of bias:** MULL-005 substantially UNDER-rated Smothering Tithe - exactly the assignment's complaint #4.
**Resolution:** Smothering Tithe moved OUT of TIER_C_STRUCTURALLY_INERT and into the same deployment-credited treatment as Rhystic Study/Mystic Remora, resolving the inconsistency by extending Rhystic's own precedent rather than inventing a new rule. Explicitly disclosed in every output: 'engine deployed' is a proxy for real-game value assumed from the pilot's strategic knowledge, not a simulated fact, for ALL FOUR of these opponent-triggered engines uniformly (Rhystic, Remora, Tithe, and the activated-ability half of Faerie Mastermind's dual-track treatment below).

## TITHE-002 — Mana Vault, Smothering Tithe
**Status:** VERIFIED

**Mechanic:** Mana Vault: cast for {1}, 'T: Add {C}{C}{C}', 'doesn't untap during your untap step' (stays tapped once used until an explicit, expensive {4}-upkeep untap this model never offers this early). Sequencing: T1 land -> cast Vault (uses the land's mana) -> Vault sits UNTAPPED, unused. T2: land drop (2nd land) + Vault's first-ever tap (CCC) = up to 5 mana with 2 real colored sources from the 2 lands - enough for Smothering Tithe ({3}{W}=4 total, 1 W needed) if either land produces W. Tapping Vault prematurely on T1 (rather than holding it) forfeits this specific line.

**Legal prerequisites:** T1: 1 land producing enough for Vault's {1}; do NOT tap Vault T1. T2: 2nd land (ideally W-producing) + Vault's held charge.
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** The underlying payment engine ALREADY correctly supports this sequencing (Vault, once resolved, sits available/untapped until something actually needs its mana - nothing pre-emptively taps it), but (a) Smothering Tithe was zeroed out (see TITHE-001) so reaching it was never credited, and (b) this specific trajectory was never NAMED or reported separately from generic 'acceleration' - the assignment's explicit ask (section 3) for a T1_MANA_VAULT_TO_TITHE named trajectory did not exist.
**Expected direction of bias:** MULL-005 could reach this line mechanically but never recognized or credited it as a distinct, valuable trajectory.
**Resolution:** Added an explicit named trajectory tag + regression test confirming the hold-then-combine sequencing actually happens under the existing engine (not assumed).

## REALIZE-001 — Faerie Mastermind
**Status:** VERIFIED

**Mechanic:** TWO distinct abilities with different realization profiles: (1) 'Whenever an opponent draws their second card each turn, you draw a card' - passive, opponent-turn-triggered, 100% unmeasurable by this solo model (structurally identical to Tithe/Rhystic's issue above) - but STRUCTURALLY notable because, unlike Rhystic/Remora/Tithe (which all trigger on the CONTROLLER's own future draw step or an opponent's cast, i.e. asynchronous to a fixed clock), Mastermind's passive trigger specifically fires DURING an opponent's turn, a structural fact about the card derivable from Oracle text alone, independent of whether opponent behavior is simulated. (2) '{3}{U}: Each player draws a card' - a real, always-available activated ability, fully simulatable, that already existed in ENGINE_TIER_C's _tier_c_supported() check ('its own {3}{U} ability is the only solo-usable line').

**Legal prerequisites:** Ability 2: Mastermind on battlefield + {3}{U} payable.
**Earliest relevant turn:** 3
**Already represented in MULL-005:** Ability 2 already correctly gated in _tier_c_supported; ability 1's opponent-turn timing was never tracked as a structural fact.
**MULL-005 mis-model/omission:** Not a bug - MULL-005's existing treatment of Mastermind was already correct within its own scope. This finding adds a NEW structural flag ('can this engine's trigger condition occur during an opponent's turn, per Oracle text') for the engine-realization-timing report the assignment explicitly requests, distinguishing Mastermind from Sylvan Library (whose value only updates on the CONTROLLER's own draw step) even though neither is functionally different in what this simulator can measure - both remain equally opponent-behavior-dependent for ACTUAL realization.
**Expected direction of bias:** None (correctness enhancement to the realization-timing report, not a scoring change).
**Resolution:** engine_realization_analysis.json tracks a can_trigger_on_opponent_turn structural flag (from Oracle text) separately from can_simulate_realization (whether THIS model can ever confirm the value fired).

## REALIZE-002 — Sylvan Library, Rhystic Study, Mystic Remora, Smothering Tithe, Archivist of Oghma, Runic Armasaur, Heartwood Storyteller
**Status:** VERIFIED

**Mechanic:** Sylvan Library's card selection only updates at the CONTROLLER's own draw step (not opponent-turn-reachable) and is otherwise fully self-contained/reliable - matches the assignment's explicit instruction that Library sits generically ABOVE Heartwood/Armasaur (both remain in TIER_C_STRUCTURALLY_INERT, unpromoted - the assignment did not ask to promote these, and their trigger conditions - an opponent activating a non-mana ability [Armasaur], any player casting a noncreature spell [Heartwood] - remain genuinely more niche/rare than a spell-cast or draw-step trigger).

**Legal prerequisites:** N/A
**Earliest relevant turn:** None
**Already represented in MULL-005:** True
**MULL-005 mis-model/omission:** None - Library's relative ranking above Heartwood/Armasaur was already correct.
**Expected direction of bias:** None.
**Resolution:** No change - Archivist of Oghma (opponent tutors - rare) and Runic Armasaur/Heartwood Storyteller remain TIER_C_STRUCTURALLY_INERT.

## DORK-001 — Devoted Druid
**Status:** VERIFIED

**Mechanic:** 'T: Add G.' + 'Put a -1/-1 counter on this creature: Untap this creature.' The second ability has NO tap symbol, so it's usable even the turn Devoted Druid enters (summoning sickness blocks the FIRST ability only). Net effect: T1 (if cast), Druid produces 0 mana (summoning sick, can't use the T: ability at all). From the turn after it resolves onward, Druid can tap for G, then immediately untap itself via the counter ability (no tap cost), then tap again for a second G - 2 mana/turn from one card, not the flat 1 this project's MANA_SOURCES model currently gives it.

**Legal prerequisites:** Druid on battlefield, not summoning sick, willing to accept a permanent -1/-1 counter.
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** MANA_SOURCES flattens Devoted Druid to {'colors': {'G'}, 'creature': True} - a plain 1-mana dork, understating its real 2-mana-per-turn (post-summoning-sickness) ceiling.
**Expected direction of bias:** UNDER-rates hands with Devoted Druid specifically for any T2+ line needing 2+ green.
**Resolution:** Modeled as a second untapped-source unit from the turn after it resolves (not T1, matching real summoning sickness).

## DORK-002 — Delighted Halfling
**Status:** CANDIDATE

**Mechanic:** TWO abilities: 'T: Add C' (unconditional) and 'T: Add one mana of any color. Spend this mana only to cast a legendary spell, and that spell can't be countered' (restricted). This project's payment engine (_try_pay/available_sources) has no concept of cost-restricted mana (usable only for a specific spell being cast) - adding it would require threading the identity of the spell being paid for through every payment call site (is_currently_castable, can_pay_jointly, the main develop_turn cast loop, achievable_search.py, trajectory_search.py, bottoming_search.py - a broad, invasive change for a narrow-value fix).

**Legal prerequisites:** Halfling on battlefield, not summoning sick; restricted ability only for legendary spells (this deck's commanders, Kinnan, Derevi, King T'Challa, Delney, Shang-Chi).
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Halfling is flattened to {'generic': 1, 'creature': True} - it currently produces ONLY colorless mana, never any color, understating its ceiling in legendary-heavy (commander) lines specifically.
**Expected direction of bias:** UNDER-rates Halfling specifically for commander-casting/legendary-spell trajectories.
**Resolution:** Deferred, disclosed. Halfling's unconditional colorless half is already correctly modeled; only the restricted-any-color half is missing. Not fixed this phase - flagged as a known, bounded simplification for a future phase, matching this project's established practice of disclosed rather than silently-absorbed gaps.

## DORK-003 — Badgermole Cub
**Status:** CANDIDATE

**Mechanic:** 'When this creature enters, earthbend 1' (animates a land into a 1/1 haste land-creature) + 'Whenever you tap a creature for mana, add an additional G' - a flat creature-mana amplifier, structurally similar to Kinnan's doubler but +1 instead of x2, and specific to creature sources.

**Legal prerequisites:** Badgermole Cub on battlefield; another creature mana source tapped.
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Not modeled at all.
**Expected direction of bias:** Minor under-rating in narrow creature-heavy-mana hands; a niche 2-drop, low expected T1-T3 frequency.
**Resolution:** Deferred (earthbend land-animation), disclosed. The creature-mana-amplifier half is a clean parallel to Kinnan's existing multiplier code and IS implemented (small, low-risk addition).

## DORK-004 — Enduring Vitality
**Status:** CANDIDATE

**Mechanic:** 'Creatures you control have "T: Add one mana of any color."' Turns every creature into a mana dork while in play.

**Legal prerequisites:** Enduring Vitality on battlefield ({1}{G}{G}, MV3) + other creatures already on battlefield to benefit from the grant.
**Earliest relevant turn:** 3
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Not modeled.
**Expected direction of bias:** Low T1-T3 frequency (needs a 3-mana enchantment creature online PLUS other creatures already present to matter) - deferred, disclosed.
**Resolution:** Deferred, disclosed.

## DORK-005 — Shang-Chi, Master of Kung Fu, Kinnan, Bonder Prodigy
**Status:** CANDIDATE

**Mechanic:** 'You may activate abilities of creatures you control as though they had haste' + 'T: Add two mana of any one color, only for creature-source ability activation.' Could fund Kinnan's {5}{G}{U} activation.

**Legal prerequisites:** Shang-Chi on battlefield + another expensive creature-sourced activated ability (Kinnan) + a lot of mana, by T3.
**Earliest relevant turn:** 3
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** Not modeled.
**Expected direction of bias:** Negligible T1-T3 frequency (needs two specific creatures plus 7+ mana). Deferred, disclosed.
**Resolution:** Deferred, disclosed.

## CMDR-001 — Tymna the Weaver
**Status:** VERIFIED

**Mechanic:** Pilot's explicit strategic directive: Tymna receives zero positive mulligan credit by default - the pilot does not mulligan toward early Tymna.

**Legal prerequisites:** N/A - a scoring policy, not a legality question.
**Earliest relevant turn:** None
**Already represented in MULL-005:** MULL-005's trajectory_grading.py DID credit Tymna: Tier A if 'attack_eligible_creature_count() >= 1' by T2, Tier B if attack-capacity medium/high. structural_hand_grade()'s 'commander_colors_plausible' fallback rule also generically rewarded WB/GU color access without checking WHICH commander or WHY.
**MULL-005 mis-model/omission:** Tymna credit existed and is exactly the pilot's named correction target.
**Expected direction of bias:** MULL-005 OVER-rated Tymna-enabling hands.
**Resolution:** Tymna removed from all positive tier-grading paths; commander_colors_plausible generic fallback removed/replaced (see CMDR-002).

## CMDR-002 — Thrasios, Triton Hero, Mox Amber, Fierce Guardianship
**Status:** VERIFIED

**Mechanic:** Mox Amber requires a legendary creature/PW ON THE BATTLEFIELD (already correctly gated in the existing engine via `controls_legendary` checking state.nonland_perms, NOT state.command_zone - confirmed correct, no bug). Fierce Guardianship's 'free_if_commander' is ALREADY correctly gated to `any(p.name in COMMANDERS for p in state.nonland_perms)` in interaction_model.py - also confirmed correct, no bug. BOTH mechanically already require the commander to be a real battlefield permanent, not merely castable - the underlying engine was already right; only the MULLIGAN SCORING never specifically credited 'Thrasios cast -> Mox Amber/Fierce Guardianship turns on' as a distinguished, valuable composite state.

**Legal prerequisites:** Thrasios actually cast onto the battlefield (not merely castable).
**Earliest relevant turn:** 2
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** The base engine's gating was already correct; the trajectory GRADER never specifically checked for this composite (Thrasios-enables-Amber / Thrasios-enables-free-Fierce-Guardianship) - it only credited generic Thrasios productivity/activation.
**Expected direction of bias:** MULL-005 under-recognized these two SPECIFIC concrete Thrasios benefits as distinguished positive signals (though it did not over-credit them either, since they weren't credited at all).
**Resolution:** Added explicit THRASIOS_ENABLES_MOX_AMBER / THRASIOS_ENABLES_FREE_INTERACTION composite checks; generic 'commander castable' credit removed.

## KINNAN-001 — Kinnan, Bonder Prodigy
**Status:** VERIFIED

**Mechanic:** Already correctly modeled as a pure mana-doubling trigger in available_sources() (applies to every nonland mana source, doubling its per-tap count) - the underlying MECHANIC was already right (SOLO-003R). The GRADING problem is separate: trajectory_grading.py's Tier A path gave Kinnan its own standalone tier credit merely for being deployed+supported (a mana dork present), rather than crediting whatever BETTER destination Kinnan's doubled mana actually reaches.

**Legal prerequisites:** N/A - a scoring policy, not a legality question.
**Earliest relevant turn:** None
**Already represented in MULL-005:** True
**MULL-005 mis-model/omission:** Kinnan itself was treated as a Tier A destination; it should only ever be a mechanism/multiplier feeding some OTHER destination's trajectory.
**Expected direction of bias:** MULL-005 could over-credit a hand that deploys Kinnan with no further payoff, and under-credit the SPECIFIC destination Kinnan's mana actually unlocks (since that destination's own trajectory wasn't separately re-evaluated with Kinnan's doubling in the loop).
**Resolution:** Kinnan's standalone Tier A/B grading path removed; Kinnan now only participates as a doubling mechanism inside the bounded trajectory search, credited via whatever destination it helps reach.

## AGENCY-001 — Force of Will, Force of Negation, Fierce Guardianship, Flare of Denial, Mindbreak Trap, Mental Misstep, Pact of Negation, Flusterstorm, Swan Song, Silence, Veil of Summer, Subtlety, Commandeer, Misdirection, Endurance
**Status:** VERIFIED

**Mechanic:** Interaction should be a SECONDARY modifier to a real destination, never the primary keep reason on its own - already MULL-005's own stated design intent, but not enforced with an explicit composite metric distinguishing free vs paid live interaction retained alongside a real destination.

**Legal prerequisites:** interaction_is_live() (already correctly models real alternate costs, per interaction_model.py's own SOLO-003 build).
**Earliest relevant turn:** None
**Already represented in MULL-005:** Partially - trajectory_grading.py already appended '+interaction'/'+tutor_retained' suffixes to mechanism tags, but did not distinguish FREE from PAID retained interaction as separate metrics.
**MULL-005 mis-model/omission:** No explicit ENGINE_PLUS_LIVE_FREE_INTERACTION / ENGINE_PLUS_LIVE_PAID_INTERACTION split.
**Expected direction of bias:** Minor - a reporting granularity gap, not a scoring direction bias.
**Resolution:** Added explicit split metrics in the composite-state layer.

## PREMIUM-001 — Mystic Remora, Esper Sentinel
**Status:** VERIFIED

**Mechanic:** MULL-005's structural_hand_grade() snap-keeps unconditionally on 'premium one-drop in hand' with no color-castability check.

**Legal prerequisites:** N/A - a scoring rule investigation.
**Earliest relevant turn:** None
**Already represented in MULL-005:** True
**MULL-005 mis-model/omission:** MULL-005's OWN validation (found while building its example set, disclosed in its write-up) already measured a 19.3% (412/2,138) false-keep rate on this exact rule - hands with a premium one-drop that still reach Tier D/F, almost entirely from missing color sources. This audit re-confirms that finding and resolves it (see PREMIUM-001 resolution) rather than carrying it forward disclosed-but-unfixed a second time.
**Expected direction of bias:** MULL-005 (and now, unless fixed, MULL-005R) over-keeps premium-one-drop hands with no real color access.
**Resolution:** SNAP_KEEP rule for a premium one-drop now additionally requires the source producing its own color to already be present/reachable (color-coherence check) - see structural_hand_grade_r() below.

## COMBO-001 — Devoted Druid, Swift Reconfiguration, Hazel's Brewmaster, Enduring Vitality, Training Grounds, Shang-Chi, Master of Kung Fu
**Status:** CANDIDATE

**Mechanic:** None of these five form a VERIFIED deterministic combo among only these cards within a T1-T3 window per this project's existing interactions/verified/ registry - checked against load_deterministic_combos() (INT-*.json files with conditional=False). This audit does not invent new combo lines; it only checks what's already verified.

**Legal prerequisites:** N/A
**Earliest relevant turn:** None
**Already represented in MULL-005:** False
**MULL-005 mis-model/omission:** combo_proximity metrics (trajectory_metrics.py's existing combo-adjacent tags) already exist from SOLO-003R and are reused unchanged; no new verified combo was found this phase among the assignment's named example cards.
**Expected direction of bias:** None - this audit did not discover a new deterministic combo to add.
**Resolution:** Reuse existing verified-combo infrastructure (interactions/verified/) as the sole source of truth for combo-proximity credit; no new speculative combo lines added.

