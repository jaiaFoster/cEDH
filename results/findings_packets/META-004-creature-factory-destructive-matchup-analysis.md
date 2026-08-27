# META-004 — Creature Factory Destructive Matchup Analysis

**Analysis date:** 2026-08-27  
**Regional field window:** 2026-07-27 through 2026-08-26 (`US-SOUTHWEST-AZ-LV`)  
**Global field window:** 2026-07-27 through 2026-08-26 (`GLOBAL`)  
**Subject:** Creature Factory v173  
**Moxfield updated:** 2026-08-26  
**98 hash:** `6e3880f5a959fa132c7f1e0ddc0acbad05ba34a2a1412a60a721b6529fce9111`  
**Purpose:** informational handoff for the deck-builder; no automatic card changes

## Executive conclusion

Creature Factory is not generically “resilient” or “fragile.” Its resilience is highly directional.

It is unusually resilient against:

- noncreature spell chains;
- single counter wars;
- graveyard-based conversion;
- ordinary one-for-one creature removal;
- commander denial;
- games that pass through one large interaction exchange and continue.

It is materially less resilient against:

- a creature commander or permanent engine that resolves and immediately begins activating;
- `Cursed Totem`/`Grafdigger's Cage`-class effects that attack several internal systems at once;
- `Culling Ritual` or sweepers that simultaneously remove mana, engines, and conversion bodies;
- multiple fast opponents whose threats demand different answer types;
- compact wins that require a hard answer after the deck has tapped out for a three-to-five-mana permanent.

The cleanest one-sentence diagnosis is:

> Creature Factory is better at surviving the stack than at policing the battlefield.

That distinction matters because the Arizona–Las Vegas submitted-list sample is unusually rich in Ral, Rograkh/Silas, Crystal, Scion, Tayam, Kinnan, and Thrasios/Yoshimaru. Some of those reward the deck's anti-spell engines; Kinnan, Tayam, Magda-like decks, and other resolved-permanent engines attack its weakest response axis.

## What this report can and cannot measure

This is not a conventional one-versus-one matchup table. A four-player pod result depends on all four decks, seat, pilot, draw incentives, and which opponent spends interaction. “A T&T deck lost in a pod containing Kinnan” does not mean Kinnan defeated T&T head-to-head.

The seat confound is large enough to dominate small matchup samples: cEDH Stats' all-time T&T table reports a 27.6% win rate from seat 1 and 15.0% from seat 4. Matchup claims that do not control for seat should therefore remain directional.

The evidence is therefore separated into three grades:

1. **Observed:** actual Creature Factory tournament pods and 30-day T&T pod associations.
2. **Structural:** exact v173 card functions against the opposing deck's threat and defense axes.
3. **Hypothesis:** directional matchup grades that should guide testing, not be treated as win-rate estimates.

The global pod calculation uses 212 event titles explicitly identifying themselves as cEDH, 6,075 seats, and 3,370 entries with commander data. It is a conservative subset of META-003's 222-event confirmed pool. The regional field is the same 12-event, 290-seat pool used in META-002; only 72 seats disclosed structured commander/list data.

## Field pressure

### Arizona–Las Vegas known local decks

Among the 72 entries with usable commander data:

| Commander shell | Known entries | Primary pressure on Creature Factory |
|---|---:|---|
| Thrasios/Tymna | 5 | compact wins, mirror resource competition, flash/protection |
| Blue Farm | 5 | early spell chains, compact Oracle/Breach conversion |
| Crystal | 4 | resolved commander plus noncreature spell chain |
| Scion | 4 | commander-centric one-card conversion |
| Ral | 4 | storm turn and commander-mediated spell velocity |
| Tayam | 4 | graveyard recursion plus activated permanent engine |
| Rograkh/Silas | 4 | extreme speed, Breach, free interaction |
| Kinnan | 3 | activated commander engine and creature-based conversion |
| Thrasios/Yoshimaru | 3 | creature midrange, flash, compact conversion |

This is incomplete field coverage, but it shows why a single answer profile will not suffice locally. The same pod can contain a spell-chain deck, a graveyard engine, and a commander-activation deck.

### Global reference field

The largest known commander shells in the conservative 30-day cEDH subset were Blue Farm, Kinnan, Rograkh/Thrasios, Rograkh/Silas, Sisay, T&T, Ral, Crystal, Magda, Dargo/Tymna, Vivi, Nick Fury, Etali, Tayam, and Thrasios/Yoshimaru.

That field divides into two important superclasses:

- **Blue/spell velocity:** Blue Farm, Rograkh/Thrasios, Rograkh/Silas, Ral, Crystal, Vivi, Nick Fury.
- **Resolved permanent/activation:** Kinnan, Sisay, Magda, Tayam, Thrasios/Yoshimaru, creature-heavy T&T.

Creature Factory v173 is substantially better positioned into the first superclass than v165 was. It did not add a comparably strong answer to the second.

## Creature Factory's observed Arizona pods

| Round | Opposing shells | Result | What the result supports |
|---|---|---|---|
| 1 | Blue Farm / Godo / Ral | Draw | The deck survived a highly explosive pod and reached a state opponents would not allow it to untap from. This supports containment and inevitability, but not conversion. |
| 2 | River Song / Thrasios–Yoshimaru / unidentified submitted commander | Win | The deck can convert through a mixed creature/value pod. One game is not a matchup estimate. |
| 3 | Kinnan / Scion / Crystal | Draw | The deck again survived a permanent/commander-engine pod. The draw does not prove advantage; it reinforces the real-event pattern of reaching a dominant post-fight state without always closing. |
| 4 | Blue Farm / Ral / Nick Fury | Loss | Multiple fast spell-centric opponents can exhaust the deck's interaction or punish a tap-out. This is the most relevant stress case for the new `Swan Song`/Cabbage/Teferi package. |

Overall: 1 win / 2 draws / 1 loss. This supports the deck's long-game thesis, but four pods cannot estimate commander-pair matchups.

## Generic T&T pod-association guardrail

Across the conservative global 30-day subset, single-T&T pods had a baseline of **1.40 points per pod** under cEDH's 5/1/0 scoring. The following figures measure the T&T player's result when the named opposing commander was present. They are pod-composition associations, not causal or head-to-head win rates.

| Opponent present | Pods | T&T PPG | Difference from T&T baseline |
|---|---:|---:|---:|
| Sisay | 55 | 1.48 | +0.08 |
| Thrasios/Yoshimaru | 34 | 1.38 | -0.02 |
| Blue Farm | 103 | 1.26 | -0.14 |
| Kinnan | 102 | 1.28 | -0.12 |
| Ral | 44 | 1.23 | -0.17 |
| Rograkh/Silas | 65 | 1.19 | -0.21 |
| Vivi | 32 | 1.19 | -0.21 |
| Rograkh/Thrasios | 77 | 1.12 | -0.28 |
| Magda | 39 | 1.08 | -0.32 |
| Tayam | 24 | 1.00 | -0.40 |
| Nick Fury | 19 | 1.00 | -0.40 |
| Crystal | 38 | 0.81 | -0.58 |
| Lumra | 17 | 0.71 | -0.69 |

The smallest samples are noisy and all figures inherit co-opponent and pilot-selection effects. The useful pattern is the superclass, not the exact ordering: speed and engines that retain agency after resolving are the recurring pressure points.

## Matchup matrix for Creature Factory v173

Ratings are structural hypotheses: `good`, `playable`, `pressured`, or `bad`. They are deliberately not percentages.

| Opponent class | Examples | Rating | Why | Best cards | Underperformers / liabilities |
|---|---|---|---|---|---|
| Noncreature turbo/farm | Blue Farm, Rograkh/Silas, Nick Fury turbo | **Playable; improves sharply after T1** | Eleven cheap/free stack pieces plus Remora/Sentinel/Lotho/Cabbage punish spell volume. Endurance disrupts Breach. Their advantage is earlier compact conversion and efficient bounce. | `Mystic Remora`, `Esper Sentinel`, `Lotho`, `The Cabbage Merchant`, `Swan Song`, `Flusterstorm`, `Mindbreak Trap`, `Endurance`, `Silence`, `Ranger-Captain` | `Birthing Ritual`, slow Pod turns, `Sowing Mycospawn`, uncastable `Abhorrent Oculus` in hand |
| Blue Farm specifically | Kraum/Tymna | **Approximately even, seat-sensitive** | Creature Factory has strong taxation and graveyard defense, but lacks Oracle's compactness and can lose engines to one-mana bounce. Kraum also helps turn on Gleaming/Bowmasters. | Cabbage, Gleaming, Bowmasters, Endurance, Swan, Flusterstorm, Teferi, Abolisher | Slow creature tutors without a live conversion window; five-mana Teferi in early games |
| Temur turbo | Rograkh/Thrasios | **Pressured** | Their speed and free commander enable protection before the Factory is established. If the first attempt fails, Factory's engines and black/white interaction overtake them. | Mindbreak, Misstep, Remora, Endurance, Silence, Ranger-Captain, Veil | Tithe and other four/five-mana development; reactive creature answers are often irrelevant |
| Spell-storm commander | Ral, Crystal, Vivi | **Playable but commander-critical** | Cabbage and spell-tax engines are excellent after deployment; Mindbreak is premium. If the commander resolves and survives, the deck's noncreature counters lose leverage against subsequent triggered/activated value. | Cabbage, Remora, Sentinel, Lotho, Mindbreak, Flusterstorm, Gilded Drake, Swift Reconfiguration, Subtlety | Pod/Ritual development while the commander remains active; Force of Negation cannot answer a creature commander |
| Kinnan | Kinnan | **Bad unless Kinnan is stopped or stolen** | Kinnan converts mana and activated abilities through ordinary stack-tax plans. Creature Factory has several tempo answers but little unconditional creature removal. Kinnan also outscales Thrasios quickly. | Gilded Drake, Swift Reconfiguration, Subtlety, Otawara, Force/Flare on cast, Boseiju on enabling artifacts | Cabbage, Gleaming, Flusterstorm after Kinnan resolves, slow tutor chains |
| Sisay | Sisay | **Pressured but manageable** | Sisay must remain in play and activate, giving Gilded Drake/Swift/Subtlety windows. The weakness is that one activation can produce a protective or winning legend, and the deck lacks redundant hard removal. | Gilded Drake, Swift, Subtlety, Otawara, Boseiju, Teferi, Silence before a protected conversion | Cabbage and noncreature-only counters after Sisay resolves |
| Magda/artifact activation | Magda, Arcum, Oswald | **Bad** | These decks win through creature/artifact activations and make much of the free noncreature counter suite situational. Boseiju is excellent but singular. | Boseiju, Gilded Drake, Swift, Otawara, Subtlety, Sowing Mycospawn where land denial matters | Flusterstorm, Cabbage against creature-heavy hands, slow engines without interaction |
| Graveyard permanent engine | Tayam, Lumra | **Pressured; Endurance-dependent** | Endurance and Deathrite are excellent, and creature tutors can find Endurance. However, repeated permanent/commander activations outlast one-shot stack interaction. | Endurance, Deathrite, Gilded Drake, Swift, Subtlety, Cabbage against noncreature setup, instant-speed creature tutors | Force of Negation after the engine resolves; graveyard interaction if Endurance is spent too early |
| Creature midrange / T&T neighbor | T&T, Thrasios/Yoshimaru | **Playable; favors whoever establishes engines and flash first** | Factory has greater engine and tutor depth, clones, Pod conversion, and better inevitability. Conventional lists often have more flash, unconditional removal, and compact Oracle wins. | Pod, Survival, Thrasios, Tithe, Gleaming, Cabbage, Teferi, Gilded Drake, Clever Impersonator | Tap-out engines into a flash opponent; insufficient answers to an opposing protected creature |
| Combat/stax | Winota, hatebear shells | **Mixed** | Creature density blocks Tymna pressure and Pod can operate under some Rule-of-Law effects. The deck is highly exposed to Totem/Cage and broad sweepers. | Boseiju, Otawara, Swift, Gilded Drake, Pod under Rule of Law, creature mana | Cursed Totem, Grafdigger's Cage, Linvala effects, Culling Ritual, sweepers |
| Godo / one-card commander | Godo and similar | **Playable only with held interaction** | The deck has enough free counters and creature tempo to stop the first cast, but tapping out is dangerous and many value engines do nothing on the critical turn. | Subtlety, Force, Flare, Pact, Mindbreak where applicable, Gilded Drake/Swift if priority permits | Tithe, Ritual, slow tutors when they consume the interaction window |

## What makes the deck resilient

### 1. Interaction is split across rule systems

The deck does not rely exclusively on counterspells:

- Stack: `Force of Will`, `Force of Negation`, `Fierce Guardianship`, `Flare of Denial`, `Pact of Negation`, `Mindbreak Trap`, `Commandeer`, `Misdirection`, `Mental Misstep`, `Swan Song`, `Flusterstorm`.
- Creature cast/tempo: `Subtlety`.
- Resolved creature: `Gilded Drake`, `Swift Reconfiguration`, `Otawara`.
- Artifact/enchantment/land: `Boseiju`.
- Graveyard: `Endurance`, `Deathrite Shaman`.
- Uncounterable/timing-resistant utility: Boseiju, Otawara, `Colossal Skyturtle`, `Talon Gates of Madara`.

This forces opponents to defend on more than one axis.

### 2. The deck is not commander-dependent

Drannith effects and commander tax are less damaging here than in Kinnan, Sisay, Magda, or Rograkh-enabled free-counter shells. Pod, Survival, Druid/Hazel, Cabbage, Tithe, and the other engines function without either commander.

### 3. Its wins and setup use permanents and activated abilities

Pod, Survival, Devoted Druid, Hazel's Brewmaster, Thrasios, and the Cradle/Oboro/Talon line do not ask the deck to resolve a long spell chain on the winning turn. This is valuable after the first counter war and under some spell-limiting effects.

### 4. Protection is redundant and asymmetrical

`Silence`, `Ranger-Captain of Eos`, `Grand Abolisher`, `Teferi, Mage of Zhalfir`, `Veil of Summer`, Emergence Zone, Delighted Halfling, and the free counters give several ways to create a protected conversion window.

### 5. It converts opposing velocity into resources

Remora, Sentinel, Rhystic, Lotho, Cabbage, Gleaming Splendor, Bowmasters, Faerie Mastermind, and Smothering Tithe cover different opponent behaviors. No single opposing payment decision turns all of them off.

## What breaks the deck's resilience

### 1. A resolved creature commander exposes the answer gap

The deck has no `Deadly Rollick`, `Swords to Plowshares`, `Chain of Vapor`, or equivalent broad one-mana hard-removal suite. Gilded Drake and Swift are powerful, but they are singletons with targeting and timing constraints. Subtlety and Otawara are tempo, not permanent removal.

This is why Kinnan/Magda/Sisay/Tayam are different problems from Blue Farm/Ral. Adding more counters does not fully solve them.

### 2. Several hate pieces attack multiple packages

- `Cursed Totem`: mana creatures, Thrasios, Devoted Druid, Kinnan, Deathrite, Oboro, and utility creatures.
- `Grafdigger's Cage`: Pod and library-to-battlefield creature tutoring.
- Graveyard exile: Hazel's Druid line and Endurance-based recycling.
- `Opposition Agent`: the unusually dense tutor/search network.
- `Culling Ritual`: mana rocks/dorks plus multiple engines and conversion pieces.

Boseiju is the cleanest answer to several of these, but one land cannot carry the entire resolved-permanent matchup.

### 3. Resilience is expensive to deploy

Teferi, Tithe, Pod plus activation, Ritual, Sowing Mycospawn, Clever Impersonator, and Formidable Speaker ask the deck to tap meaningful mana. Against three fast decks, the failure mode is not lack of interaction in the 98; it is having the wrong portion of the deck in hand while needing to remain untapped.

### 4. Recovery is stronger through commanders than through recursion

The deck can restart with Thrasios/Tymna and redundant engines, but it has little direct permanent recursion. If Pod, Survival, or a developed creature board is swept, rebuilding requires drawing or tutoring a new engine rather than simply recurring the destroyed one.

## Matchup value of the current cards

### Premium against spell-chain and blue decks

| Card | Matchups improved | Specific contribution | Limitation |
|---|---|---|---|
| Mystic Remora | Blue Farm, Rograkh shells, Ral, Crystal, Vivi | Punishes early noncreature velocity | Weak into creature-heavy permanent engines |
| Esper Sentinel | Same | Early tax plus creature body for Tymna/Cradle/Pod | Payment scales badly in late game |
| Lotho, Corrupt Shirriff | Turbo/farm and counter wars | Converts multi-spell turns into mana | Dies to broad low-cost removal/sweepers |
| The Cabbage Merchant | Blue Farm, Ral, Crystal, Vivi, Nick Fury | Creates Foods from every opponent noncreature spell; converts pairs into mana | Combat damage consumes Foods; poor against creature/activation-heavy decks |
| Gleaming Splendor | Kraum/Tymna, Rhystic/Remora tables, draw engines | Converts second draws into Treasures and can force draws | Does not stop the draw; three-mana activation is slow |
| Orcish Bowmasters | Wheels, Kraum/Faerie/Rhystic draw turns, x/1 boards | Punishment plus creature removal pressure | Does not answer most larger commanders |
| Swan Song | Turbo, Breach, tutors, protection | Efficient hard interaction while developing | Cannot counter commanders/creatures |
| Flusterstorm | Storm and counter wars | High efficiency and protection scaling | Dead against resolved permanents and creatures |
| Mindbreak Trap | Ral/storm, protected spell chains | Exile and multi-spell leverage | Often unavailable against one-card creature wins |
| Endurance | Breach, Tayam, Lumra, recursion | Free graveyard reset and tutorable creature | Timing-sensitive; one use may not beat repeated recursion |

### Premium against resolved creatures and permanent engines

| Card | Matchups improved | Specific contribution | Limitation |
|---|---|---|---|
| Gilded Drake | Kinnan, Sisay, Magda, Ral, Crystal, Vivi, Godo | Permanent theft; turns commander dependence against opponent | Sorcery speed without Teferi/Emergence; target/ETB vulnerable |
| Swift Reconfiguration | Same plus own Druid line | One-mana flash neutralization that bypasses toughness | Artifact/enchantment removal can restore the creature; crew interactions exist |
| Subtlety | Commander cast turns, Godo, creature tutors | Free tempo without needing mana | Does not permanently answer the card |
| Otawara, Soaring City | Any resolved nonland permanent | Uncounterable channel tempo | Expensive; opponent can replay the threat |
| Boseiju, Who Endures | Totem/Cage, artifact combo, stax | Uncounterable answer from a land slot | Cannot answer creature commanders and gives replacement land |
| Colossal Skyturtle | Resolved permanent or recursion need | Uncounterable channel modes; Survival synergy | Four-mana channel is expensive |
| Talon Gates of Madara | Protected creature/combat or own-creature protection | Land-channel phase-out bypasses normal counters | Temporary and mana-intensive from hand |
| Deathrite Shaman | Breach/Tayam/Lumra | Repeatable graveyard pressure plus mana | Needs appropriate card types and is vulnerable to removal/Totem |

### Protection and conversion-window cards

| Card | Best opposing defenses | Contribution | Limitation |
|---|---|---|---|
| Silence | Blue tables and multi-player counter wars | Prevents new spells for the turn | Does not stop existing permanents/abilities |
| Ranger-Captain of Eos | Same | Tutorable body plus delayed Silence | Three-mana setup; sacrifice is visible |
| Grand Abolisher | Blue interaction | Strong active-turn shield | Must resolve and survive; white mana requirement |
| Teferi, Mage of Zhalfir | Blue interaction, flash mirrors | Opponents cast only at sorcery speed; creatures gain flash | Five mana and triple blue make it a late-game card, not early defense |
| Veil of Summer | Blue/black interaction | Efficient protection and replacement | Narrow by color and does not stop abilities |
| Emergence Zone | End-step setup and surprise conversion | Moves sorcery-speed creature infrastructure to instant timing | One-shot land sacrifice |
| Delighted Halfling | Counter-heavy pods | Makes legendary creatures uncounterable | Does not protect nonlegendary combo bodies |

### Engines that improve long games but create early matchup risk

| Card/package | What it beats | What punishes it |
|---|---|---|
| Birthing Pod | Long creature games; deterministic tutor ladders | Cage, artifact removal, Culling Ritual, tapping out before activation |
| Birthing Ritual | Attrition and creature-rich boards | Removal before end step, Cage-like effects, low creature density after sweep |
| Survival of the Fittest | Creature toolbox and graveyard setup | Opposition Agent, graveyard hate, enchantment removal |
| Smothering Tithe | Draw-heavy midrange and long counter wars | Fast wins before the investment repays; Boseiju/removal |
| Rhystic Study | Any spell-dense long game | Fast pods that win before cards can be converted |
| Faerie Mastermind | Draw-engine tables | Low-trigger creature pods; mana-intensive activation |
| Archivist of Oghma | Tutor/fetch-heavy tables | Opponents sequencing searches before it resolves; weak clock |
| Thrasios | Stalled and mana-rich games | Totem, Bowmasters pressure, games ending before activation matters |
| Tymna | Creature mirrors without blockers | Token boards, large blockers, combat denial |

### Conversion network: resilience and failure points

| Package | Resilience gained | Matchup exposure |
|---|---|---|
| Devoted Druid + Swift Reconfiguration | Compact creature tutor access; Swift is independently interactive | Creature removal in response; enchantment/artifact disruption; Totem |
| Devoted Druid in graveyard + Hazel's Brewmaster | Converts a removed/discarded Druid into a deterministic line | Graveyard exile; ETB prevention; Food/artifact disruption; Totem-like ability denial |
| Pod/Derevi/Oculus/Clever network | Threat diversity, tutor chaining, value after first fight | Cage, artifact removal, high setup mana, Oculus stranded in hand |
| Cradle + Oboro + Talon board line | Land-based pieces resist normal counters | Requires a developed creature board and is weak to sweepers/Totem |
| Finale/Chord/Eldritch/Neoform/Nature's Rhythm/Summoner's Pact | Exceptional access to the correct creature branch | Opposition Agent, Cage, Silence timing, tutor taxes; Pact creates an upkeep liability |

## What changed from v165 and which matchups moved

v173 added:

- `Swan Song`
- `The Cabbage Merchant`
- `Teferi, Mage of Zhalfir`
- `Summoner's Pact`

It removed:

- `Biomancer's Familiar`
- `Seedborn Muse`
- `Sylvan Library`
- `Talion, the Kindly Lord`

Directional effect:

| Matchup family | v173 movement | Reason |
|---|---|---|
| Blue Farm / Rograkh-Silas | **Improved** | Swan is live immediately; Cabbage punishes spell volume; Teferi creates a late protected window |
| Ral / Crystal / Vivi | **Improved** | Cabbage directly taxes their noncreature chain; Swan/Mindbreak improve containment |
| T&T / blue midrange | **Improved in protection, reduced in passive long-game value** | Teferi and Swan matter more in fights; Seedborn/Biomancer/Talion cuts reduce generic Thrasios scaling |
| Kinnan / Sisay / Magda | **Approximately unchanged** | None of the four additions is redundant hard creature removal; Cabbage is weaker here |
| Tayam / Lumra | **Approximately unchanged** | Endurance/Deathrite remain the critical cards; Summoner's Pact modestly improves access to Endurance but creates risk |
| Post-first-fight conversion | **Likely improved** | Summoner's Pact adds immediate creature access and Teferi protects a later creature conversion, but Teferi itself is expensive |

This is a sensible response to META-002/003's finding that v165 was overinvested in slow engines and underinvested in stack/flash tools. It does not close the report's separate resolved-permanent interaction gap.

## Deck-builder handoff: questions to answer next

1. Is the remaining resolved-creature suite—Gilded Drake, Swift Reconfiguration, Subtlety, Otawara, Talon Gates, and conditional counters—enough for the expected number of Kinnan/Sisay/Magda/Tayam-style opponents?
2. Which current slot is intended to be the second unconditional answer when Gilded Drake is unavailable or invalid?
3. Does `Summoner's Pact` find a matchup-changing answer often enough to justify the upkeep liability, especially when it cannot find Gilded Drake, Subtlety, or most stack interaction?
4. Is five-mana triple-blue Teferi reliably deployable before the relevant second fight, or is it primarily a win-more protection layer?
5. Against a mixed Arizona pod—one turbo deck, one permanent engine, one blue midrange deck—what mulligan rule guarantees both meaningful development and at least one answer that remains live after a creature resolves?
6. Should the next simulation compare answer portfolios rather than isolated cards: current suite versus one additional unconditional creature answer versus one additional universal bounce/removal spell?

## Final matchup thesis

Creature Factory v173 is built to let opponents expend spells, turn that activity into mana/cards, survive the first major fight with free interaction, and then convert through a permanent or activated-ability line. That is a coherent and locally validated plan.

Its bad matchups are not simply “faster decks.” They are decks that invalidate the form of interaction it is holding:

- a creature commander when the hand contains noncreature counters;
- an activated permanent when the hand contains Silence/Flusterstorm;
- a graveyard engine after Endurance has already been spent;
- a hate piece that simultaneously disables mana, tutors, and conversion;
- a second fast opponent after the deck has paid four or five mana for resilience.

The destructive metagame question for the deck-builder is therefore not whether Creature Factory needs more interaction in the abstract. It is whether the current 98 contains the correct **distribution of answer types** for Arizona's mixed pods and the global field's dominant Blue Farm/Kinnan/Rograkh/Sisay axis.

## Sources and provenance

- `META-002-arizona-vegas-30d-deck-comparison.md`
- `META-003-global-30d-deck-comparison.md`
- GitHub TopDeck normalized snapshots through 2026-08-27
- Moxfield canonical import `current.json`, v173
- [cEDH Stats T&T page](https://cedhstats.org/commanders/thrasios-tymna?elite=0&min_players=16&period=1m)
- [cEDH Stats methodology](https://cedhstats.org/about)
- [cEDH Stats field and battle statistics](https://cedhstats.org/stats)
