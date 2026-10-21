# Conditional controller review

Current linked Sept25 CR rechecked2026-10-21; exact references and Oracle hashes are in JSONL. No automated proof of combo execution or judge certification.

## D01 — mixed_functional_and_false_split

K’rrik D1 pays own life costs from the shared pool. Children belongs to D2.

D2 may benefit from a higher shared total, but Children counts life D2 actually lost, not D1 payments. A friendly cannot-lose-life effect prevents nonzero payments teamwide.

Caution: Children omitted; no refund inferred from shared-total delta. Life payment must be affordable.

CR 119.4a, 810.9, 810.9a, 810.9h.

## D02 — functional_support

D2 controls Sister/Heliod; D1 casts/reanimates creatures.

Generic other-creature Sister triggers can make D2 gain life and put counters on D2 own permanents. Daxos requires D2 creatures; Authority requires enemy creatures.

Caution: D1’s own life gain does not itself trigger D2 Heliod.

CR 109.5, 603.3a, 805.7, 810.9.

## D03 — same_controller_combo

All four D1 controlled. Gary can enter uncast from D1 grave; enough shared life and no ETB/life-gain suppression.

Pay9 for Chainer when BBB replaced. Devotion8 gives16 loss/gain across two enemy heads; own Seer recycles Gary. Net7 friendly life per repeat.

Caution: Remove Chainer/Gary/K’rrik, counter ability, exile grave or stop life gain. Counter changes/devotion changes require recomputation.

CR 107.4, 700.5, 701.21a, 810.5, 810.9.

## D04 — own_combo_split_false

D2 controls Heliod and own Ballista with at least2 counters, grants lifelink for1W.

D2 damage/lifelink causes own Heliod counter trigger and replaces each spent counter. Triskelion starts with counters and base toughness.

Caution: Heliod may target teammate creature for lifelink, but resulting D1 gain does not trigger D2 Heliod, and D2 cannot put its counter on D1 Ballista.

CR 109.5, 117.5, 704.5f, 810.9.

## D05 — verified_nonbo

Either enchantment controlled by D1.

Skipping D1 draw step skips the team draw step. Necrodominance additionally exiles D1 graveyard resources.

Caution: Both omitted. Black draw text is not teamwide card access.

CR 614.10, 805.8.

## D06 — same_controller_with_shared_finisher_support

D1 controls Citadel/Top and its own Reservoir; life permits initial casts; no spell-count restriction.

Top can be cast for1 life through Citadel, tapped to draw and put itself atop library, and recast. Reservoir gains increasing life from own spells. D2 separately may spend shared life on D2 Reservoir.

Caution: Do not draw past available library or assume one50-damage shot kills60; life costs/control remain exact.

CR 109.5, 119.4a, 810.5, 810.9a.

## E01 — functional_team_turn_draw

E1 controls Nekusar; no draw-denial/replacement.

Each player in active team normally draws. Nekusar’s that-player draw-step triggers occur for each applicable player; two enemy heads can each draw an additional card.

Caution: Shared draw step is not one shared card and is not two full turns.

CR 121.1, 805.4b, 805.4d, 810.9.

## E02 — same_controller_burn

E1 controls all three creatures. Each enemy actually draws7; no damage prevention or ability suppression.

Prodigy doubles Wizard Nekusar’s1-damage triggers. Each one triggers Ghyrson for2. Capacity7*2*3 per enemy=84 teamwide.

Caution: Ghyrson is not Wizard; its trigger is not doubled by Prodigy. Game ends before unnecessary later events resolve.

CR 603.2, 603.3a, 810.9.

## E03 — denial_damage_tradeoff

Narset on E2 or Thief on E1; both have same enemies.

Denied/replaced enemy draws never happen and do not trigger opposing-draw damage/loss. Thief gives its own controller replacement draws, not ally cards.

Caution: Use denial as alternative strategy; do not claim seven-card wheel damage while draws are replaced. Ordinary first draw exception still matters.

CR 101.2, 614.6, 810.5.

## E04 — conditional_prison

E2 Lavinia/Pool, optionally Teferi. Enemy hand spell and Pool trigger resolve as specified.

Pool exiles hand spell and offers another linked card for free. Lavinia counters enemy casts on which no mana was spent. Teferi independently denies those casts during resolution.

Caution: Paid additional taxes can bypass Lavinia’s no-mana trigger. Abilities/non-hand casts/preexisting stack objects are not all stopped. Friendly casts are permitted.

CR 101.2, 601.2, 603.3a, 607, 810.5.

## E05 — conditional_draw_denial

E2 controls Narset/Box; enemy reaches shared draw step and normal draws consume each one-draw allowance.

Order active enemy triggers with correct ownership; Box can bottom enemy hands and fail to draw replacements under Narset. Sanitarium is a separate ability-based draw/discard tool.

Caution: Friendly draws are not denied by own Narset. Timing, instant responses and hostile replacement effects matter; no one combined hand.

CR 504.1, 805.4b, 805.4d, 805.7.

## E06 — verified_cross_controller_candidate

E1 or F2 owns Ascension with3 quest counters; ally may own Mindcrank; initiate enemy loss/card in grave and no replacement exile.

Both controllers share enemies. Enemy loss mills that player; enemy card in grave triggers Ascension loss/gain, which retriggers ally Crank.

Caution: One quest counter at each shared end step, not one per head. Exile replacements and exhausted libraries can halt chain before life lethal; force a draw if needed.

CR 603.4, 805.4, 810.9.

## E07 — verified_cross_controller_candidate

E1 Guildmage, E2 Crank, own E1 mana1UB to set effect; initiating enemy life loss or card to grave.

Guildmage’s turn effect and ally Crank respond to the same enemies, so loss/mill can repeat across controllers.

Caution: No pooling mana. Requires real initiation, graveyard entries and enough remaining library/life for stated kill; draw may still be required.

CR 109.5, 810.5, 810.9.

## E08 — poison_threshold_check

E1 Nekusar has infect; no replacements/prevention; each enemy draws7.

Fourteen1-damage events produce14 shared poison; threshold is15. Another qualifying draw or damage event is required.

Caution: Not a fresh-team one-wheel kill. Ghyrson does not inherit infect.

CR 702.90, 810.8d, 810.10.

## E09 — same_controller_combo

E2 owns imprint, Scepter and ready nonland mana output>2; owns available outlet.

Activation2 casts own Reversal copy, untapping own nonland permanents. Basalt/Signet produce4 per cycle. Store own mana or trigger own Reservoir; Stroke enemy beyond library for team loss.

Caution: No allied mana/untaps. Canonist/Rule of Law can stop repetition; mono-C loop still needs actual U for Stroke.

CR 106.4, 109.5, 707, 810.5.

## F01 — same_controller_engine_shared_turn

F1 controls Sieve/Assembly; no other own Thopters at each intervening-if check; repeatable6 own mana.

Return Assembly, create5, sacrifice5 own artifacts to Sieve, recast6. Extra turn is shared with F2.

Caution: Breya/Sai tokens can invalidate trigger; clear or withhold them. F2 artifacts cannot pay Sieve. Assembly itself returns rather than being consumed.

CR 603.4, 701.21a, 805.8, 810.5.

## F02 — same_controller_combo_split_false

F1 owns Foundry and Sword graveyard/board, with own Urza or own sacrifice-mana outlet.

Foundry/Sword alone costs1 per token. Urza taps own Sword/new Thopter to sustain netU and tokens; Altar/KCI sacrifices produced token for netC. Mana/life belong to F1.

Caution: Sword on F2 grave does not return for F1 creature entry; no ally sacrifice. Orb/yard exile/ability hate can interrupt.

CR 109.5, 605, 701.21a, 810.5.

## F03 — same_controller_combo

F1 controls all and leaves its commander in own grave for Mantle.

Sacrifice Breya and2 Thopters for6, Mantle4 returns Breya and makes2, net2. Bank mana then retain excess tokens for own Breya damage.

Caution: Choosing CZ prevents this reanimation. Graveyard/exile/ETB/activation hate matter. Breya still needs own colors if cast first.

CR 109.5, 603.3a, 701.21a, 903.9.

## F04 — same_controller_non_graveyard_combo

Own Basalt/Rings, own startup mana and Ballista.

Pay3 untap and2 Rings-copy. Tap Basalt between resolutions; subsequent cycles produce6 for5 spent. Cast Ballista with real X counters.

Caution: Rings does not copy mana ability; it copies the nonmana untap. Artifact activation suppression stops it.

CR 106, 603.3a, 605, 810.5.

## F05 — conditional_team_untap_support

F1 has genuine tap-off resource before shared friendly untap; plan exact number of Orb releases.

Tapping relevant own Orbs before friendly untap can free both heads. Urza may tap multiple own artifacts without a T cost on Urza. Clock untaps F1 artifacts on enemy shared untap.

Caution: Prototype also has its own T cost; not unlimited taps. One Barrier normally releases only one Orb. Enemy Clock untap does not also untap F2 cards; not doubled per enemy head.

CR 502.2, 805.4a, 810.5.

## F06 — support_not_automatic_trigger

F2 owns Talion, chooses number; F1 activates own Sieve.

Matching enemy casts lose2 for that enemy and draw1 for F2. Extra shared turns give normal own draws/untaps.

Caution: F1 spells never become enemy Talion triggers; no pooling draws or artifacts.

CR 102.3, 805.8, 810.5.

## R01 — channel_vs_spell

Channel card in actual own hand, correct own mana, eligible target.

Channel is activated ability rather than casting a spell, relevant under spell-only prison. Working price6 per identity in main; Boseiju’s G identity excludes it from all six lists.

Caution: Played land cannot also be discarded from hand; no general target-permanent permission for Boseiju. Other channel lands not automatically repriced.

CR 602, 810.5.

## R02 — target_scope_check

Actual own casting/activation costs and chosen player.

Chant/Abeyance target only one player. Wishclaw’s new controller must be an opponent, not teammate.

Caution: Do not claim single Chant protects against both heads, Abeyance stops every spell, or Wishclaw can be handed to an ally.

CR 102.3, 109.5, 810.5.
