# Controller-aware conditional review

Current linked CR2026-09-25 checked2026-10-21. Exact Oracle text/hash and rule IDs in JSONL. No automated gameplay certification.

## G-life — support

G1 owns Sheoldred; Oloro belongs to G2.

Two enemy normal draws cause4 enemy shared loss. G1's draw gains2; G2's draw does not trigger Sheoldred. Oloro gains2 once each friendly upkeep.

Limits: G1 gaining life does not trigger G2's battlefield Oloro. Shared totals do not merge gain events.

CR 810.9, 810.9a, 805.4b, 603.3a.

## G-pox — same_controller

G1 controls Bloodletter on its shared turn; both pools60 before Pox.

Pox assigns20 loss to each head simultaneously. Friendly total60-40=20; doubled enemy loss40 per head gives60-80=-20. Complete the spell's other instructions before checking state-based actions.

Limits: Friendly hands/creatures/lands also suffer. Recompute for actual life totals and replacements. Pox loses life, rather than setting a total under810.9d.

CR 810.9, 810.9a, 805.6, 608.2c, 614.1.

## G-sorin — same_controller

G1 owns both, activates-3 targeting an enemy at shared60 on friendly turn.

Without Bloodletter the targeted head loses50 to make its team10. Bloodletter replaces this with100 loss; team ends-40.

Limits: Six mana for Sorin plus existing Bloodletter; ability counters, target hexproof and removal can stop it.

CR 810.9c, 614.1, 805.4a.

## G-wound — cross_controller

G1 resolves Sorin at enemy60; G2 controls Reflection through end step.

Only the targeted head lost50; Reflection adds another50 at the shared end step. Plain Pox from60 makes each head lose20; Reflection adds40 total later.

Limits: One Reflection trigger per shared end step, not two. Enemy gains can affect survival; remove enchantment before its trigger exists.

CR 810.9, 810.9c, 805.4d, 603.3a.

## G-endurance — same_controller

G2 controls its alternate win before friendly upkeep.

Test checks shared>=50 at trigger AND resolution; Felidar checks>=40. One head winning wins the team. Oloro gain may resolve above an already-triggered win check.

Limits: At49 Test never triggers: later Oloro gain cannot create it retroactively. Pox can defeat your own upkeep-win plan.

CR 810.9a, 810.8a, 603.4, 805.7.

## G-drain — split_false_positive

One head must own Blood and its own Bond/Vito/Tenacity to repeat.

Enemy loss triggers that head's Blood gain, which triggers its own payoff, which causes enemy loss. Either deck has a valid own-controller package.

Limits: G1 Blood plus G2 Bond does NOT repeat because G2 did not gain life. Life-gain prohibitions can stop the team gaining.

CR 109.5, 603.3a, 810.9, 810.8a.

## G-peer — same_controller

G1 controls Sheoldred and targets one enemy with Peer.

That head draws ceil(library/2), then loses ceil(sharedlife/2). Each draw queues a2-loss trigger; they go on the stack after Peer resolves.

Limits: Seven-mana spell, not an automatic immediate loss during the draws. Responses to the spell or queued triggers remain relevant.

CR 810.9a, 121.2, 603.3, 117.5.

## G-denial — friendly_hazard

G1 has renewable own fodder; G2 has colored nonland mana or an established win.

All players' tapped lands produce onlyB. Ophiomancer triggers once each shared upkeep if G1 has no Snake. G1 sacrifices its own creature to upkeep Contamination.

Limits: Can strand G2's white/blue spells. Nonland mana and activated abilities bypass it; deploy only with a plan for G2.

CR 810.5, 805.4d, 106.3, 603.4.

## G-protection — cross_controller

G2 resolves Protection before G1 Pox/Death Cloud.

Fixed friendly shared life cannot change. Only G2's own permanents phase out; G1's board and hand remain exposed.

Limits: Not protection for G1's permanents. Poison, library-loss and alternate wins remain separate.

CR 810.9a, 810.9g, 810.9h, 101.2.

## G-gix — cross_controller

G1 controls Gix and a friendly creature hits an enemy head.

That creature's controller may pay1 from shared life and draw into its own hand. G2's creature can earn G2 cards.

Limits: Does not put all cards in G1's hand; excessive payments threaten Test.

CR 810.9, 109.5, 603.3a.

## H-aluren — cross_controller

H2 controls Aluren; H1 owns Acererak and has not completed Tomb of Annihilation.

Global permission lets H1 cast MV3 Acererak for0 repeatedly. ETB returns it and ventures. Repeated Lost Mine of Phandelver paths visit Dark Pool; each visit drains each enemy1. Thirty Dark Pools cover60 team life. With fully resolved dungeon rooms this uses119 Acererak casts and29 Temple draws before the thirtieth Dark Pool; H1 must have at least29 library cards remaining for this simple line.

Limits: Each spell/ETB/room permits interaction. Enemies also get Aluren. Never complete Tomb, which stops the return ability. No commander required. The finite-library condition is explicit: this is a sufficient finite kill from the opening state, not a claim of safely drawing indefinitely.

CR 601.2b, 601.2f, 701.49, 309.5, 309.6, 309.7, 810.8a.

## H-chulane — same_controller

H2 controls Chulane/Aluren, owns Drake and gets Lab Maniac onto battlefield before an empty-library draw.

Free self-returning Drake casts draw and optionally place H2's lands. Chulane trigger resolves BEFORE the creature. With one card left, casting Maniac draws it, then Maniac enters; another Drake cast can win.

Limits: With zero cards and Maniac still in hand, its cast triggers a losing draw BEFORE it enters. H1 Acererak casts do not trigger H2 Chulane.

CR 109.5, 603.3, 603.3a, 614.1a, 810.8a.

## H-earthcraft — cross_controller_support

H2 controls Earthcraft/Drake; either friendly head owns a basic land.

Tap newly entered own Drake while its bounce trigger waits: Earthcraft's cost is not Drake's T ability. It can target ANY basic, including H1's, or untap H2 Island to fund another Drake.

Limits: Cannot tap H1 creatures for the cost. Mandatory Chulane draws still limit repetitions.

CR 602.2, 302.6, 109.5, 810.5.

## H-alarm — cross_controller_support

H2 controls Alarm and a nonsick Speaker; any creature enters.

Alarm untaps ALL creatures including enemies, and prevents normal creature untaps. Speaker pays1 and taps to untap another target permanent, possibly H1's land/rock.

Limits: Not automatically infinite mana. Seedborn untaps H2's own permanents once per opposing shared untap, not twice.

CR 109.5, 302.6, 603.3a, 805.4d.

## H-combat — cross_controller_support

H1 owns both partners; attacks are assigned to enemy heads.

Tymna sees distinct enemy players hit, including by H2 creatures: max2 here. Malcolm sees only H1 Pirates and makes H1 Treasure, up to2 opponents per simultaneous damage event.

Limits: Damage to one head is not both for these triggers. Either enemy's creatures can block for either head.

CR 805.10b, 805.10d, 805.4d, 603.3a.

## H-oracle — same_controller

H1 casts Oracle then Consultation with Oracle ETB on stack, naming a card absent from its library.

Consultation exiles H1's library; resolving Oracle compares H1 devotion and library. Its win wins the team.

Limits: Trigger counters or forced empty-library draw can beat this. Removal alone does not beat an existing Oracle trigger when library0.

CR 603.3, 810.8a, 121.4.

## I-dakmor — conditional_engine

All belong to I1; Dakmor in hand, Gitrog and discard outlet on board, >=2 cards to dredge.

Discard Dakmor triggers Gitrog. Dredge mills2, returning Dakmor. If the batch mills one or more lands, ONE extra Gitrog draw triggers. Skirge makes ownB per discard; grave-shufflers recycle.

Limits: Unknown order, shuffle triggers and mandatory draws need explicit management. Not automatically a deterministic win; a separate fully specified Woodland mana route is documented.

CR 702.52, 603.3, 121.2, 810.5.

## I-woodland — same_controller_deterministic

I1 owns Resources/Spelunking, Woodland+3Forests+1Swamp. Grave has Analyst and persistent creature/instant/sorcery/enchantment types. Gitrog is absent (earlier High Market sacrifice if needed).

Tap Woodland/3Forests/Swamp for4G+B, sacrifice the three Forests and Swamp to Resources for3G+B: total7G+2B. Pay4G for Woodland's2GG copy ability. Pay3G+B for the copied Analyst's3G sacrifice ability. Return all5 own lands; Spelunking makes them untapped. State resets plusB. Repeat32 times then Exsanguinate X30 drains two enemy heads60.

Limits: Copying does not ETB/mill3; zone change resets copy. Keep four grave types after lands return. Gitrog still present adds mandatory draws and invalidates unlimited repetition. Grave hate/removal interrupt it.

CR 707.2, 614.1, 117.5, 603.3, 810.5.

## I-depths — same_controller

I1 controls both, pays2 and taps Stage to copy Depths.

Keep the zero-counter copy through legend rule, then sacrifice it to its trigger for Marit Lage.

Limits: 20 ordinary damage is only one-third of60, not commander damage. Both enemies can block; exile/bounce/edicts remain answers.

CR 707.2, 704.5j, 603.4, 805.10d.

## I-gear — same_controller

I2 owns Equipment, threats and Pilots. Shorikai is eligible legendary Vehicle under current903.3.

Stoneforge tutors Equipment and later puts it in play; Aid/Puresteel/Stonehewer suit up own threats. Sword untaps only I2 lands. Shorikai draws/discards/makes Pilots for I2.

Limits: No normal equip/Aid onto I1 Gitrog or Marit Lage. Shared blocking reduces simple combat clocks. Shorikai is an artifact until crewed.

CR 702.6a, 301.5, 109.5, 805.10d, 903.3.

## I-reversal — same_controller

I2 owns Scepter imprinted with Reversal and nonland mana sources producing>2 per round.

Own Basalt3 plus Signet/Fellwar can accumulate mana. Reversal untaps only I2 nonlands; Ballista converts own mana, Shorikai can draw bounded cards.

Limits: I1 resources cannot pay I2 costs. Do not draw past own library. Artifact hate stops the engine.

CR 109.5, 601.2, 810.5.

## I-rings — same_controller

I2 owns both and can seed first untap3 plus copy2.

Copy Basalt untap; after copy resolves tap for3 before original resolves; after original resolves tap for3 again. Six produced per5 spent; Ballista X60 costs120 and shoots60.

Limits: Rings does not copy an ally's ability. Demonstrate seed mana; Basalt has no ordinary untap.

CR 602.2, 603.3a, 117.3.

## I-hate — friendly_hazard

Compare Shorikai source stax with I1 graveyard/dork plan.

RIP, Cage, Totem and Humility were omitted because they attack I1 engines. Lantern can instead target an enemy grave card or exile only opponents' graveyards.

Limits: Lantern ETB can target any graveyard: choose carefully. No broad assertion that all graveyard hate is teammate-safe.

CR 109.5, 810.5.

## all-protection — cross_controller_support

Friendly head targets one enemy with Chant/Abeyance while teammate acts.

Chant stops that enemy's spells; Abeyance stops its instants/sorceries and nonmana activated abilities. Barracuda stops enemies casting on its controller's friendly shared turn.

Limits: Other enemy and already-stacked objects remain. Barracuda costs4 and is not made free by Aluren.

CR 109.5, 805.5, 805.5a.

## all-turns — rules_scope

Use shared-team turns and separate resources.

Sorin ultimate controlling a player controls that player's team for that turn. Skip-draw would skip friendly team's whole draw step. Extra turns would be extra team turns.

Limits: Necropotence is absent from all six. No blanket infinite-combo/early-win prohibition or unban activated.

CR 805.8, 810.5, 810.8a.
