# Rules verification supporting global v3

The current official [rules landing](https://magic.wizards.com/en/rules), [Comprehensive Rules](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt), [2HG overview](https://magic.wizards.com/en/formats/two-headed-giant), and [ban list](https://magic.wizards.com/en/banned-restricted-list) were retrieved October22,2026. Fresh linked CR bytes match the pinned archive exactly; see v3_inputs/current_rules_verification.json. Oracle text remains the pinned October20 dataset. This is a set of conditional interpretations, not match results or exhaustive automatic combo certification. The accompanying JSONL records exact Oracle IDs/text/hashes, configurations and invalidation criteria.

No existing format rule changes. The league keeps60 shared starting life and120/72/12 construction settings. The handoff calls60 a custom setting; the official Commander/2HG overview also specifies60. This terminology discrepancy does not alter the accepted setting. Commander damage, poison, mulligans, bans and legality policy remain untouched.

## team-turns

Time Warp, Temporal Manipulation, Capture of Jingzhou, Temporal Trespass, Temporal Mastery, Nexus of Fate, Time Stretch, Walk the Aeons. CR 805.8, 500.7.

Prerequisites: Caster resolves its spell; pay that card's own costs; targets must remain legal where required.

One awarded turn is a whole team turn, not two extra turns. Both heads receive their normal turn resources. Delve, miracle, exile and buyback still have their printed constraints.

Pricing: Propose the three five-mana equivalents at12; individually distinguish expensive/conditional alternatives.

## skip-step

Savor the Moment, Necropotence, Necrodominance. CR 805.8, 805.4b.

Prerequisites: At least one friendly head receives the instruction to skip the shared step.

Savor skips both friendly untaps. Necropotence/Necrodominance skip the shared draw step. Neither card merges hands or activates the other head's abilities.

Pricing: Savor4 rather than12; retain human Necro prices and document friendly cost.

## fortune-loss

Final Fortune, Last Chance, Warrior's Oath, Angel's Grace, Sundial of the Infinite. CR 805.8, 810.8a, 603.7, 724.1.

Prerequisites: Fortune-family turn resolves. To evade loss, resolve Grace during THAT extra turn or end that turn before the specified end-step loss resolves.

Extra team turn; one head's scheduled loss loses the team. Ending the specific extra turn before its end step skips that trigger; ending with it on stack removes it. Generic next-end-step triggers differ.

Pricing: Retain protected7-point values; flag comparison with proposed12-point safer turns instead of overriding organizer.

## expropriate

Expropriate. CR 805.8, 500.7.

Prerequisites: Both friendly players vote time; card resolves without vote-changing effects.

Each time vote creates a separate turn. Two friendly time votes therefore yield two extra team turns. Each money vote gives caster a permanent owned by that voter.

Pricing: Keep exact organizer8; cheaper-turn hierarchy is a documented tension, not an automatic change.

## sieve-ownership

Time Sieve, Tivit, Seller of Secrets. CR 701.21a, 805.8, 810.5.

Prerequisites: Same head controls Sieve and five expendable artifacts. Tivit has its normal extra vote in a four-player game.

Five votes create five artifacts controlled by Tivit's controller, split between Clues and Treasures according to votes. A teammate's Sieve cannot sacrifice them. Same-controller repeated Tivit damage can renew fuel, conditional on combat access.

Pricing: Keep Sieve8 pending organizer decision; propose Tivit CZ8. No cross-deck sacrifice assumption.

## silence-vs-chant

Silence, Orim's Chant, Abeyance, Grand Abolisher. CR 109.5, 810.5.

Prerequisites: Spells resolve while both enemy heads are opponents of their caster.

Silence forbids both enemies casting while ally remains free; Chant affects one target player. Abeyance restricts named spell types/abilities for one target, not all actions. These do not retroactively counter spells already on stack.

Pricing: Keep Silence14 versus Chant1/Abeyance1. Protection is strong, but not every defensive effect gets engine pricing.

## friendly-overload

Winds of Abandon, Cyclonic Rift. CR 109.5, 702.96a, 810.5.

Prerequisites: Friendly permanents remain controlled by teammate, not caster.

Overload changes target to each; permanents the caster does not control include ally permanents. Winds exiles allied creatures; Rift bounces allied nonland permanents. Non-overloaded Winds can also target an ally creature.

Pricing: Rift remains explicit0; Winds stays working5 with alternative2–3 in conflict queue, not silently applied.

## pox-bloodletter

Pox, Smallpox, Death Cloud, Bloodletter of Aclazotz, Fraying Omnipotence. CR 810.9, 810.9a, 109.5.

Prerequisites: Both pools60 before Pox, no other replacement; Bloodletter controlled by a friendly head during friendly shared turn.

Pox computes one-third rounded up for each head:20 each. Friendly pool becomes20. With one Bloodletter enemy losses double to40 each and enemy pool becomes-20. Without asymmetry both lose40; Fraying can reduce both60 pools to0. Shared turn qualifies as Bloodletter controller's turn.

Pricing: Keep Pox/Smallpox/Death Cloud0; Fraying proposed0; price asymmetric enabler, not every synergy.

## sorin-bloodletter

Sorin Markov, Bloodletter of Aclazotz, Tree of Perdition. CR 810.9a, 810.9c, 810.9e, 701.10.

Prerequisites: Affects one enemy head; no prevention; Bloodletter active on friendly turn. Tree exchange must succeed under its exchange rules.

Sorin60-to10 is50 life lost by that head; Bloodletter doubles to100 and pool becomes-40. Tree exchanges one enemy shared value with its actual toughness; it is not a fixed13-life effect if toughness changes. Teammates cannot exchange life totals with each other.

Pricing: Sorin retains5; Tree proposed3 for a summoning-delayed creature effect, not a universal cheap win.

## threshold-upkeep

Test of Endurance, Felidar Sovereign, Oloro, Ageless Ascetic. CR 810.9a, 603.4, 810.8a, 805.4.

Prerequisites: Own upkeep starts with shared pool at the printed threshold. No effect removes win permission.

Test checks50 at trigger and resolution; at49 it never triggers even if Oloro later gains2. Felidar checks40. Shared upkeep is one upkeep; Oloro gains2 once, not twice because there are two teammates. A successful individual win wins the team.

Pricing: Retain Test7 working and organizer Felidar5; Oloro CZ0 deliberate exception.

## reservoir

Aetherflux Reservoir. CR 810.9, 810.9a, 810.8a.

Prerequisites: Controller pays50 from shared pool and targets a head at an enemy pool60; no damage modifier.

One50-damage hit leaves enemy team10. Paying50 from friendly60 leaves10; it is not a free opening kill. Lifegain counts spells cast by its controller, not teammate casts.

Pricing: Retain organizer8; sixty life improves funding, not automatic lethality.

## split-life-false

Sanguine Bond, Exquisite Blood, Heliod, Sun-Crowned, Walking Ballista. CR 109.5, 810.9, 810.5.

Prerequisites: Enchantments or Heliod/Ballista split across teammates with no additional transfer effect.

Shared life value does not share life-gain events. Blood controller B gaining does not trigger A's Bond. Ballista controller B gains its lifelink event, not A for A's Heliod trigger. These split configurations do not sustain the usual same-controller loop.

Pricing: No tax or claimed kill merely from union matching; same-controller setups evaluated separately.

## shared-life-costs

Ad Nauseam, K'rrik, Son of Yawgmoth, Bolas's Citadel. CR 810.9a, 810.9b, 109.5, 903.8.

Prerequisites: Controller can pay/lose life; no prevention or cannot-pay effect.

Shared60 funds own effects, but cards/mana/casting permissions stay individual. Krrik substitutes only controller's black symbols, not generic commander tax or teammate spell costs.

Pricing: Keep calibrated premium individual prices; no additional team or pair surcharge.

## opponent-draw

Consecrated Sphinx, Smothering Tithe, Notion Thief, Narset, Parter of Veils. CR 805.4b, 109.5, 810.5.

Prerequisites: Enemy shared draw step, both heads draw normally; no other replacements.

Two enemy draws can offer Sphinx two triggers, each optionally drawing two:four cards for its controller. Tithe offers two tax triggers. Thief exempts each enemy's own first draw in its draw step. Narset caps each enemy separately; friendly draws are unaffected.

Pricing: Preserve Sphinx explicit1 despite proposed alternative7 in queue; Tithe8 working is not three-opponent scaling.

## own-cast-engines

Chulane, Teller of Tales, Displacer Kitten, Teferi, Time Raveler, Sol Ring. CR 109.5, 810.5, 606.3.

Prerequisites: Same controller owns/controls Kitten, Teferi and Ring. Resolve triggers individually; have sufficient library for required draws.

Cast Ring, Kitten blinks own Teferi before Ring resolves; reset Teferi can minus3 returning Ring and drawing. Existing Ring mana funds repetition. Ally casts do not trigger Kitten or Chulane. Finite library prevents calling this a safe unlimited draw line without another mechanism.

Pricing: Kitten proposed5 as reusable converter; no price on every cheap artifact. Preserve Chulane CZ2.

## chainer-line

Chainer, Dementia Master, K'rrik, Son of Yawgmoth, Gray Merchant of Asphodel, Ashnod's Altar. CR 109.5, 810.9, 810.5, 701.21a.

Prerequisites: One controller has Chainer, Krrik and colorless Altar; Gary in graveyard. Can pay9 life and has legal activation. No hate/replacements.

Krrik replaces BBB with6 life plus printed3:9 paid. Chainer3+Krrik3+Gary2 black devotion gives8; Gary drains both enemies8 and gains controller16. Net friendly life+7 per recycle, plus Altar mana, after sacrifice. A black sacrifice outlet adds devotion; do not count teammate devotion.

Pricing: Chainer main3/CZ6 proposed; Gary working range remains0–1. Actual engine/control prerequisites, not a split-player shortcut.

## aluren-payload

Aluren, Acererak the Archlich, Lost Mine of Phandelver. CR 109.5, 701.49, 810.9.

Prerequisites: A controls Aluren; B casts its own Acererak, has not completed Tomb, can safely take29 required temple draws, and chooses Lost Mine routes with Dark Pool.

Aluren permits either head and opponents to cast suitable creatures. Acererak returns to its owner and its controller ventures. Dark Pool drains both enemies1:119 resolved entries,30 Dark Pool visits and29 temple draws drain shared60. This is a finite kill with conditions, not blanket infinite safety.

Pricing: Retain Aluren4 / Acererak0, exactly the organizer enabler/payload policy.

## graveyard-global

Rest in Peace, Helm of Obedience. CR 109.5, 614.1, 701.21a.

Prerequisites: A controls Rest in Peace, B controls Helm; B pays at least1 and taps Helm, targeting enemy. No other replacements.

RIP globally replaces cards entering graveyards with exile; Helm sees neither a creature nor X cards actually put in that graveyard and processes the library. Empty library is not immediate loss: require a subsequent failed draw or another finishing condition. This functions across controllers.

Pricing: Controller split can be functional for global replacements; do not infer the same for shared-life triggers.

## land-target-support

Candelabra of Tawnos, Deserted Temple, Minamo, School at Water's Edge, Earthcraft. CR 109.5, 810.5, 602.2, 701.21a.

Prerequisites: Legal target land/permanent belongs to teammate. Activator pays its own mana/tap/creature cost.

Candelabra and Temple can target ally lands; Minamo can target an ally legendary permanent. Earthcraft taps own untapped creature as cost but may untap teammate's basic land. Untapped owner later taps for its own mana; pools never merge.

Pricing: Propose Candelabra4/Temple2/Minamo3; retain Earthcraft working price, no mana-transfer fiction.

## arcum-support

Arcum Dagsson. CR 109.5, 602.2, 701.21a, 810.5.

Prerequisites: A controls untapped non-summoning-sick Arcum; B controls an artifact creature; ability targets B's creature.

B sacrifices that creature and B may search B's library for a noncreature artifact to put on B's battlefield. It is NOT only an own-controller search. Targeting an enemy gives that enemy the optional search too.

Pricing: Propose CZ6 for guaranteed repeatable access; role can be allied support, no dynamic pair surcharge.

## malakir-target

Malakir Rebirth // Malakir Mire. CR 109.5, 603.7, 810.5.

Prerequisites: A casts Rebirth targeting B's creature. Creature dies this turn and return trigger resolves; no replacement/hate.

Oracle says target creature without own-control restriction. A loses2 life. Returned creature enters tapped under its OWNER's control, not necessarily previous controller. The land face is still the same Oracle identity charged once.

Pricing: Propose main1 for low land-slot cost and genuine ally protection, not blanket MDFC tax.

## spell-tax-controller

Daze. CR 109.5, 118.12, 810.5.

Prerequisites: A casts Daze on enemy C's spell; C's teammate D has spare mana but no explicit transfer permission.

Only C, the targeted spell's controller, may pay Daze's1. D cannot directly spend its own mana to satisfy C's payment. A's alternate-cost Island must be controlled by A.

Pricing: Propose1: weak soft counter and returned-land tempo cost, with exact payer constraint.

## ability-funding

Kinnan, Bonder Prodigy, Basalt Monolith, Freed from the Real, Bloom Tender. CR 109.5, 810.5, 602.2.

Prerequisites: Pieces split between teammates with no explicit resource transfer.

Kinnan only boosts its controller tapping a nonland for mana. B's Monolith gets no A-Kinnan bonus. Freed controller can pay its own U to untap ally creature, but ally mana cannot fund that payment directly: matching components alone does not self-fund a loop.

Pricing: Basalt latest4/Bloom Tender1 preserved. Flag unsupported split mana lines rather than applying combo points.

## eligibility

Shorikai, Genesis Engine, Tymna the Weaver, Malcolm, Keen-Eyed Navigator. CR 903.3, 903.4, 903.5, 702.124.

Prerequisites: Normal Commander construction plus approved same-head Partner combination; each deck separately legal.

Current903.3 includes eligible legendary Vehicles/Spacecraft, so Shorikai is eligible. Two ordinary Partner commanders consume two command-zone locations; teammate commanders never expand the other head's color identity.

Pricing: Price actual location once per identity; no main plus CZ surcharge and no cross-head color union.

## Scope and uncertainty

Primary rules establish behavior; they do not establish a numerical price. Spellbook [Kitten/Teferi/Ring](https://commanderspellbook.com/combo/1170-4761-5034/) and [Chainer/Krrik/Gary](https://commanderspellbook.com/combo/328-3260-4078-4448/) document mechanisms; no deck-union match or goldfish line proves real-game win probability. Additional state changes can invalidate any line. Prices and unresolved organizer conflicts are separately labelled.
