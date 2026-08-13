# SIM-001 MULL-005R — Engine Realization Timing Analysis

18 ability entries across 15 cards. 5 proxy-credited on deployment alone, 6 fully simulatable, 8 can trigger on an opponent's turn per Oracle text, 4 structurally inert in this solo model (never credited, any board state).

Central finding (TITHE-001 generalized): opponent-dependence alone does NOT predict whether a card is credited. Every Tier-A engine (Rhystic/Remora/Tithe/Sentinel) is opponent-cast/opponent-draw triggered, unmeasurable by this solo model, and yet proxy-credited on deployment alone - deliberately and disclosed, not an oversight. Tier-C engines with the SAME opponent-dependence (Faerie Mastermind's passive, Archivist, Armasaur, Heartwood) get NO such proxy; their credit (if any) requires an explicit, currently-simulatable support condition instead, and four of them (TIER_C_STRUCTURALLY_INERT) get none at all, ever.

| Card | Ability | Tier | Mechanism | Opp-turn? | Simulatable? | Proxy-credited? | Inert? |
|---|---|---|---|---|---|---|---|
| Rhystic Study | primary | A | opponent_casts_spell | True | False | True | False |
| Mystic Remora | primary | A | opponent_casts_spell | True | False | True | False |
| Esper Sentinel | primary | A | opponent_casts_spell | True | False | True | False |
| Smothering Tithe | primary | A | opponent_draws_card | True | False | True | False |
| Sylvan Library | primary | A | controller_draw_step | False | True | True | False |
| Faerie Mastermind | passive_opponent_trigger | C | opponent_draws_second_card_each_turn | True | False | False | False |
| Faerie Mastermind | activated_ability | C | controller_activated_instant_speed | False | True | False | False |
| Archivist of Oghma | primary | C | opponent_searches_library | True | False | False | True |
| Runic Armasaur | primary | C | opponent_activates_nonmana_ability | True | False | False | True |
| Heartwood Storyteller | primary | C | any_player_casts_noncreature_spell | True | False | False | True |
| Delney, Streetwise Lookout | primary | C | combat_and_triggered_ability_dependent_not_modeled | False | False | False | True |
| Deathrite Shaman | land_graveyard_mana | C | graveyard_activated_ability_not_modeled | False | False | False | False |
| Deathrite Shaman | instant_sorcery_graveyard_drain | C | graveyard_activated_ability_not_modeled | False | False | False | False |
| Deathrite Shaman | creature_graveyard_lifegain | C | graveyard_activated_ability_not_modeled | False | False | False | False |
| Birthing Pod | primary | B | controller_activated_sorcery_speed | False | True | False | False |
| Survival of the Fittest | primary | B | controller_activated_instant_speed | False | True | False | False |
| Gaea's Cradle | primary | B | controller_activated_mana_ability | False | True | False | False |
| Training Grounds | primary | B | static_continuous_cost_reduction | False | True | False | False |

## Rhystic Study — primary
**Oracle text:** Whenever an opponent casts a spell, you may draw a card unless that player pays {1}.
**Notes:** No opponents exist in this solo/goldfish model, so this trigger can never literally fire here. Credited on battlefield presence alone by T2/T3 (grade_trajectory's PREMIUM_DESTINATIONS check) as a disclosed proxy for real-game value - this project's central, honestly-labeled compromise for the deck's whole card-draw-engine suite.

## Mystic Remora — primary
**Oracle text:** Cumulative upkeep {1}. Whenever an opponent casts a noncreature spell, you may draw a card unless that player pays {4}.
**Notes:** Also a PREMIUM_ONE_DROP_ENGINE (Tier S if cast T1) - the {4} tax and cumulative upkeep are real long-game costs this T1-T3 model does not track, but the draw trigger itself is proxy-credited identically to Rhystic Study for consistency (TITHE-001).

## Esper Sentinel — primary
**Oracle text:** Whenever an opponent casts their first noncreature spell each turn, draw a card unless that player pays {X}, where X is this creature's power.
**Notes:** Also a PREMIUM_ONE_DROP_ENGINE. Unlike Rhystic/Remora the draw is unconditional unless the opponent pays (no 'you may') - a stronger real trigger, not reflected as a magnitude difference anywhere in this model (all Tier-A engines are credited as a flat proxy, not weighted by expected value).

## Smothering Tithe — primary
**Oracle text:** Whenever an opponent draws a card, that player may pay {2}. If the player doesn't, you create a Treasure token.
**Notes:** MULL-005R TITHE-001 correction: previously zeroed out via TIER_C_STRUCTURALLY_INERT-equivalent treatment (excluded from ENGINE_TIER_A) despite being MECHANICALLY IDENTICAL in opponent-dependence to Rhystic Study. Promoted into ENGINE_TIER_A_PRIMARY_CARD_ADVANTAGE so it is now proxy-credited on the same basis as Rhystic/Remora/Sentinel instead of the previous inconsistent zero-credit treatment.

## Sylvan Library — primary
**Oracle text:** At the beginning of your draw step, you may draw two additional cards. If you do, choose two cards in your hand drawn this turn. For each of those cards, pay 4 life or put the card on top of your library.
**Notes:** The ONE Tier-A engine whose trigger is fully self-contained (controller's own draw step, no opponent action required) - can_simulate_realization is True here specifically because nothing about an opponent needs to be known. Ranked above the TIER_C_STRUCTURALLY_INERT cards for exactly this reason (REALIZE-002) even though this model does not currently distinguish Library's higher reliability from Rhystic/Remora/Tithe/Sentinel's proxy-credited-but-unmeasurable status in the tier score itself - both end up Tier A, a known, disclosed granularity limit, not an oversight.

## Faerie Mastermind — passive_opponent_trigger
**Oracle text:** Whenever an opponent draws their second card each turn, you draw a card.
**Notes:** Structurally identical opponent-dependence to Rhystic/Remora/Tithe, BUT NOT proxy-credited the way those Tier-A engines are: Mastermind is Tier C, and Tier-C credit is gated entirely on _tier_c_supported() finding an explicit, simulatable support condition. This passive ability is not what _tier_c_supported checks for Mastermind (see next entry) - mere battlefield presence never earns Mastermind any tier credit under this ability alone.

## Faerie Mastermind — activated_ability
**Oracle text:** {3}{U}: Each player draws a card.
**Notes:** This is the ability trajectory_metrics._tier_c_supported actually checks for Mastermind ('its own {3}{U} ability is the only solo-usable line') - fully simulatable (mana payable now), but credit still requires the SUPPORT CHECK to pass (mana available), not mere deployment; a Mastermind on the battlefield with no spare {3}{U} gets zero Tier-C credit, correctly.

## Archivist of Oghma — primary
**Oracle text:** Whenever an opponent searches their library, you gain 1 life and draw a card.
**Notes:** 'Opponent tutors' is rare enough in a T1-T3 window, and entirely opponent-decision-dependent, that MULL-005's decision to zero it out completely (rather than proxy-credit it like Tier A) is preserved unchanged (REALIZE-002) - not promoted, not demoted, just made explicit.

## Runic Armasaur — primary
**Oracle text:** Whenever an opponent activates an ability of a creature or land that isn't a mana ability, you may draw a card.
**Notes:** Same disclosed-zero treatment as Archivist - genuinely more niche than a spell-cast trigger in most metas, per the assignment's own instruction not to promote these.

## Heartwood Storyteller — primary
**Oracle text:** Whenever a player casts a noncreature spell, each of that player's opponents may draw a card.
**Notes:** Symmetric wording ('a player'/'that player's opponents'), but only benefits Heartwood's controller when an OPPONENT casts a noncreature spell - when the controller casts one, it is the OPPONENTS who may draw. Net-negative-leaning for a proactive controller in practice; zeroed out, not modeled as a downside either (disclosed simplification, not a claim of neutrality).

## Delney, Streetwise Lookout — primary
**Oracle text:** Creatures you control with power 2 or less can't be blocked by creatures with power 3 or greater. If a triggered ability of a creature you control with power 2 or less triggers, that ability triggers an additional time.
**Notes:** Not opponent-dependent at all, unlike the other three TIER_C_STRUCTURALLY_INERT members - it is COMBAT-dependent (evasion clause) and requires a second creature with an actually-relevant triggered ability to double, neither of which this no-combat, no-stack solo model represents. Grouped here because the practical effect (never credited) is identical, even though the structural reason differs from the opponent-action cards above.

## Deathrite Shaman — land_graveyard_mana
**Oracle text:** {T}: Exile target land card from a graveyard. Add one mana of any color. (Activate only as an instant.)
**Notes:** Not in TIER_C_STRUCTURALLY_INERT (that set is specifically for opponent/combat-dependent conditions) - Deathrite is a THIRD, distinct never-credited case: _tier_c_supported() returns False for it unconditionally, for the documented SOLO-002R reason that graveyard-mana abilities are not modeled in this engine at all (no representation of either player's graveyard contents as a mana source), independent of any opponent or combat dependency.

## Deathrite Shaman — instant_sorcery_graveyard_drain
**Oracle text:** {B}, {T}: Exile target instant or sorcery card from a graveyard. Each opponent loses 2 life.
**Notes:** Same not-modeled reason as the land-exile ability above; life-loss also isn't tracked by this engine at all (no life total state).

## Deathrite Shaman — creature_graveyard_lifegain
**Oracle text:** {G}, {T}: Exile target creature card from a graveyard. You gain 2 life.
**Notes:** Same not-modeled reason as the other two Deathrite abilities.

## Birthing Pod — primary
**Oracle text:** {1}{G/P}, {T}, Sacrifice a creature: Search your library for a creature card with mana value equal to 1 plus the sacrificed creature's mana value, put that card onto the battlefield, then shuffle. Activate only as a sorcery.
**Notes:** Fully self-contained and fully simulatable (pod_and_battlefield_tutors.try_activate_pod verifies real legality: mana, a sacrificeable creature, sorcery timing). Credited only when _tier_b_supported() finds an actual legal sacrifice body (state.creature_count()>=1), never on mere board presence - Pod with no creature to sacrifice earns zero Tier-B credit, correctly.

## Survival of the Fittest — primary
**Oracle text:** {G}, Discard a creature card: Search your library for a creature card, reveal that card, put it into your hand, then shuffle.
**Notes:** No sorcery-speed restriction in the real Oracle text (unlike Pod) - activatable on an opponent's turn too, though that distinction doesn't matter for THIS model's T1-T3-on-controller's-turns structure. Credited only when a discardable creature card is actually in hand (state-aware, per SURV-*/assignment section 2D - never scored as 'present = online').

## Gaea's Cradle — primary
**Oracle text:** {T}: Add {G} for each creature you control.
**Notes:** Fully simulatable and exactly quantifiable (creature_count() at time of tap). Credited only when creature_count()>=2 (a meaningful output), not merely being on the battlefield with 0-1 creatures.

## Training Grounds — primary
**Oracle text:** Activated abilities of creatures you control cost {2} less to activate. This effect can't reduce the mana in that cost to less than one mana.
**Notes:** Not a trigger at all - a static, always-on cost reduction, so 'realization timing' doesn't apply the same way; it only has an observable EFFECT in this deck when Thrasios (the only modeled creature with an activated mana cost) is also on the battlefield. Credited only in that co-presence, never on Training Grounds alone (see thrasios_activation_cost_generic).

