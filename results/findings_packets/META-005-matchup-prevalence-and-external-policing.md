# META-005 — Matchup Prevalence and External Policing

**Analysis date:** 2026-08-27  
**Primary region:** Arizona  
**Secondary comparisons:** Arizona–Las Vegas and global cEDH  
**Field window:** 2026-07-27 through 2026-08-26  
**Subject:** Creature Factory v173  
**98 hash:** `6e3880f5a959fa132c7f1e0ddc0acbad05ba34a2a1412a60a721b6529fce9111`  
**Purpose:** measure how often Creature Factory encounters structurally difficult opponents, how often another player can police them, and how often the deck can occupy its intended post-fight-beneficiary role

## Executive answer

The answer depends on how narrowly “bad matchup” is defined.

In the 67 Arizona entries with commander data:

| Definition | Field share | Chance at least one among three opponents |
|---|---:|---:|
| Narrow persistent engines | 8/67 = 11.9% | **32.1%** |
| Broad permanent/activation engines | 15/67 = 22.4% | **53.9%** |
| All must-answer creature/commander decks | 22/67 = 32.8% | **70.4%** |

The middle definition is the most useful for Creature Factory. It means that, on current disclosed Arizona evidence, a random pod is approximately **54% likely** to contain at least one opponent whose plan continues to function after resolving a creature or permanent engine. Because only 67 of 96 Arizona seats disclosed commanders and the sample is concentrated in four Tempe/Tucson events, the uncertainty is large: the transformed 95% field-share interval gives an approximate pod-risk range of **37%–71%**.

That does not mean 54% of pods are bad. In the Arizona lists with complete 98s, the two other opponents besides the problem deck collectively had, by their first nine cards:

- **67.5%** raw probability of at least one card that could counter or answer the creature before it began activating;
- **44.6%** raw probability of at least one card that could answer an already-resolved creature;
- **35.7%** raw probability of at least one answer to a resolved artifact/enchantment stax piece;
- only **8.6%** raw probability of dedicated graveyard hate.

These are availability ceilings. They do not account for mana, conditional free-counter requirements, a card already being spent, or the opponent refusing to use it.

The central result is therefore:

> Creature Factory can reasonably externalize the first answer to a visible commander cast. It cannot safely externalize the answer after that commander resolves, and it especially cannot assume someone else has graveyard hate.

## Governing table-role model

Creature Factory is not supposed to police every opponent. Its intended sequence is:

1. Deploy one or two engines.
2. Let the obvious threat force interaction from the rest of the table.
3. Contribute only the missing layer or backstop.
4. Profit from the noncreature spells, draws, Treasures, Foods, and resource depletion produced by the fight.
5. Convert immediately before opponents rebuild or reform a coalition.

This report therefore treats opponents' interaction as a table resource. A structurally difficult opponent is not automatically a bad pod if the other two opponents have live coverage and incentives to spend it.

## Definitions

### Narrow persistent-engine set

These are the highest-confidence cases from META-004:

- Kinnan
- Sisay
- Magda
- Tayam
- Lumra
- Arcum

Their common property is that ordinary noncreature stack interaction loses substantial value after the commander/engine resolves.

### Broad permanent/activation-engine set

The narrow set plus:

- Chatterfang
- Derevi
- Winota
- Marath
- Lonis
- Loot
- Oswald

This is the preferred prevalence definition. The additions vary in power and speed, but they create the same answer-allocation problem: another player must often interact with a resolved creature, artifact, combat engine, or activated ability rather than merely counter a noncreature win spell.

### Must-answer commander set

The broad set plus Scion, Godo, Krenko, and Zhulodok. This is a stress ceiling, not a claim that every listed commander is equally unfavorable. These decks demand held interaction or a rapid table response, but some are easier for Creature Factory's free counters and tempo pieces than Kinnan/Tayam are.

Ral, Crystal, Rograkh/Silas, and Blue Farm are not placed in the structural-bad set. They are dangerous, but Creature Factory's Remora/Sentinel/Lotho/Cabbage/free-counter architecture is explicitly designed to interact with and profit from their spell velocity.

## Arizona prevalence

### Individual narrow-set opponents

| Opponent | Known Arizona entries | Field share | Chance among three opponents |
|---|---:|---:|---:|
| Tayam | 4/67 | 6.0% | **17.1%** |
| Kinnan | 2/67 | 3.0% | **8.9%** |
| Sisay | 1/67 | 1.5% | **4.5%** |
| Arcum | 1/67 | 1.5% | **4.5%** |
| Magda | 0/67 | 0% observed | Not observed; not evidence of true absence |
| Lumra | 0/67 | 0% observed | Not observed; not evidence of true absence |

Tayam is the distinctive Arizona pressure in this window. Globally, Kinnan and Sisay are much more prevalent; locally, repeated Tayam entries make graveyard/activation coverage unusually important.

### Tier totals

| Tier | Arizona entries | Exact three-opponent encounter probability |
|---|---:|---:|
| Narrow | 8/67 | **32.1%** |
| Broad | 15/67 | **53.9%** |
| Must-answer ceiling | 22/67 | **70.4%** |

Repeated pilots/decks count as entries because the intended quantity is the chance of sitting across from the deck, not the number of distinct deck designers.

### Arizona–Las Vegas check

Adding Las Vegas/Henderson produces 72 entries with commander data out of 290 total seats:

| Tier | Arizona–Las Vegas entries | Encounter probability |
|---|---:|---:|
| Narrow | 10/72 | **36.6%** |
| Broad | 17/72 | **56.0%** |
| Must-answer ceiling | 24/72 | **71.0%** |

The estimates barely move, but this should not be mistaken for strong Vegas confirmation. Most Vegas events supplied no structured commander/deck data; only five additional known entries drive the Arizona-to-regional comparison.

## Global comparison

The conservative global subset contains 212 event titles explicitly identifying themselves as cEDH, 6,075 seats, and 3,370 entries with commander data.

### Individual narrow-set opponents

| Opponent | Known global entries | Field share | Chance among three opponents |
|---|---:|---:|---:|
| Kinnan | 245 | 7.3% | **20.3%** |
| Sisay | 135 | 4.0% | **11.5%** |
| Magda | 79 | 2.3% | **6.9%** |
| Tayam | 66 | 2.0% | **5.8%** |
| Lumra | 38 | 1.1% | **3.3%** |
| Arcum | 35 | 1.0% | **3.1%** |

### Tier totals

| Tier | Global entries | Encounter probability |
|---|---:|---:|
| Narrow | 598/3,370 = 17.7% | **44.4%** |
| Broad | 675/3,370 = 20.0% | **48.9%** |
| Must-answer ceiling | 730/3,370 = 21.7% | **51.9%** |

Arizona and the global field therefore reach similar broad-engine pod risk by different routes:

- Arizona: more Tayam and a wider local fringe of permanent/commander engines.
- Global: much more Kinnan, Sisay, and Magda.

The Arizona broad estimate is 53.9%; the global estimate is 48.9%. Given Arizona's small sample, this is not evidence of a true five-point regional difference. The defensible conclusion is that **roughly half of pods** contain at least one opponent on the broad permanent/activation axis.

## External-policing coverage

### Method

For each submitted 90+ card mainboard, cards were tagged into four functional answer sets:

1. Counter/remove before activation.
2. Answer an already-resolved creature.
3. Remove a resolved artifact/enchantment stax piece.
4. Dedicated graveyard hate.

For a deck containing `k` tagged cards, raw access by the first nine cards is:

\[
P(\geq 1\ \text{answer}) = 1 - \frac{\binom{98-k}{9}}{\binom{98}{9}}
\]

The two-co-opponent result averages the actual deck-specific miss probabilities, rather than applying the formula only to the average card count.

This analysis uses 64 complete Arizona lists and 3,218 complete global lists. It does not model mulligans, tutors, mana, conditional text, prior use, hidden information, or willingness to act.

### Any two co-opponents

These are the two players other than Jaia and the identified problem deck.

| Coverage type | AZ avg cards/list | One AZ co-opponent | Two AZ co-opponents | Two global co-opponents |
|---|---:|---:|---:|---:|
| Counter/remove before activation | 6.11 | 43.0% | **67.5%** | **65.6%** |
| Remove resolved creature | 3.14 | 25.6% | **44.6%** | **43.8%** |
| Remove resolved artifact/enchantment | 2.34 | 19.8% | **35.7%** | **35.8%** |
| Dedicated graveyard hate | 0.48 | 4.4% | **8.6%** | **8.4%** |

The close Arizona/global agreement is important. Although regional commander prevalence is noisy, deckbuilders in both samples devote very similar space to these answer classes.

### Incentive/castability sensitivity

Availability is not realized coverage. If only a fraction of available answers are castable, preserved, and willingly spent, the external-policing probabilities fall approximately as follows:

| Answer class | Raw two-player availability | 75% realization | 50% realization |
|---|---:|---:|---:|
| Before activation | 67.5% | 50.6% | 33.7% |
| Resolved creature | 44.6% | 33.4% | 22.3% |
| Resolved artifact/enchantment | 35.7% | 26.8% | 17.9% |
| Graveyard hate | 8.6% | 6.5% | 4.3% |

This is a sensitivity table, not an estimate that willingness is actually 50% or 75%. It shows why table talk and interaction allocation remain central even when the cards exist.

## Blue Farm specifically

Blue Farm is a good co-policer before a commander resolves, but it is not a universal safety guarantee.

| Blue Farm coverage | AZ avg cards | Chance in first nine, one Blue Farm player | Global equivalent |
|---|---:|---:|---:|
| Counter/remove before activation | 7.4 | **52.2%** | 55.1% |
| Remove resolved creature | 3.4 | **28.2%** | 32.6% |
| Remove resolved artifact/enchantment | 2.8 | **23.8%** | 24.5% |
| Dedicated graveyard hate | 0.0 | **0% observed** | approximately 0% |

Blue Farm also is not present often enough to be the default externality:

| Field | Broad bad matchup + Blue Farm in same pod | Among broad-bad pods, Blue Farm also present |
|---|---:|---:|
| Arizona | **8.8% of all pods** | **16.3%** |
| Arizona–Las Vegas | 8.6% | 15.3% |
| Global | 7.9% | 16.2% |

So in roughly five out of six broad-bad pods, the possible co-policer is not Blue Farm. The safety net is the aggregate interaction of many archetypes, not a reliable Kraum/Tymna pairing.

## Tayam worked example

Arizona's observed Tayam share produces a **17.1%** chance that at least one of three opponents is Tayam.

Conditional on a Tayam pod:

- a Blue Farm opponent is also present only about **15.0%** of the time;
- the two non-Tayam opponents have only **8.6%** raw probability of seeing dedicated graveyard hate by nine cards;
- Creature Factory has two direct graveyard pieces, `Endurance` and `Deathrite Shaman`, for **17.6%** raw access by nine cards;
- counting `Summoner's Pact` as immediate access to Endurance raises that raw ceiling to **25.3%**, before accounting for mana/upkeep risk;
- combining the external pair with Creature Factory gives only about **24.7%–31.8%** raw direct graveyard coverage.

The correct Tayam plan is therefore not “Blue Farm will handle the graveyard.” It is:

1. Make the table answer Tayam or its enabling permanent before repeated activations begin.
2. Preserve Endurance/Deathrite/Pact as the backstop layer.
3. Do not spend the graveyard layer on low-leverage value unless the table retains another answer.
4. Convert immediately after the Tayam fight, because repeated recursion rapidly invalidates one-shot coverage.

Blue Farm still improves the pod because it is about 52% likely to see a cast-stage counter/removal card by nine cards and can bounce a stax piece. It does not materially improve the dedicated-graveyard-hate layer.

## Creature Factory's own coverage

The exact v173 list contains the following tagged answer densities:

| Coverage type | Tagged cards | Raw chance by first nine |
|---|---:|---:|
| Counter/remove before activation, broad ceiling | 10 | **63.7%** |
| Fast/free cast-stage core | 5 | **38.9%** |
| Resolved-creature answers, broad ceiling | 5 | **38.9%** |
| Fast resolved-creature core | 3 | **25.3%** |
| Resolved artifact/enchantment, broad ceiling | 3 | **25.3%** |
| Fast stax answer (`Boseiju`) | 1 | **9.2%** |
| Direct graveyard pieces | 2 | **17.6%** |
| Direct graveyard plus `Summoner's Pact` access | 3 | **25.3%** |

The broad ceilings include conditional or mana-intensive cards such as Fierce Guardianship, Flare, Otawara, Talon Gates, and Sowing Mycospawn. The fast cores exclude those that are unlikely to be live at the first relevant window.

### Combined table coverage

Combining the two external co-opponents with Creature Factory's fast-core-to-broad-ceiling range gives:

| Threat stage | Chance at least one table answer exists by nine cards |
|---|---:|
| Before the permanent engine begins activating | **80%–88%** |
| After a creature engine has resolved | **59%–66%** |
| After an artifact/enchantment stax piece resolves | **42%–52%** |
| Direct graveyard coverage | **25%–32%** |

Again, these are raw-card availability estimates, not “the table successfully stops the win” probabilities.

Applied to Arizona's 53.9% broad-engine encounter rate:

- only about **6%–11% of all pods** contain a broad engine while the first nine cards of the entire rest of the table show no tagged pre-activation answer;
- about **18%–22% of all pods** contain a broad engine while the rest of the table shows no tagged answer once that creature has resolved.

This quantifies the importance of timing. The pod is usually coverable before resolution. It becomes substantially more dangerous if everyone passes priority or spends the wrong layer.

## Probability of occupying the intended slop role

Creature Factory has nine cards that directly profit from the kinds of actions generated by a table fight:

- Mystic Remora
- Esper Sentinel
- Rhystic Study
- Lotho
- The Cabbage Merchant
- Gleaming Splendor
- Faerie Mastermind
- Smothering Tithe
- Orcish Bowmasters

The raw probability of seeing at least one by the first nine cards is **59.6%**, before mulligan selection.

Conditional on a broad permanent-engine opponent being present:

| Desired state by first nine | Raw probability |
|---|---:|
| Slop engine + at least one external pre-activation answer | **40.2%** |
| Slop engine + at least one external resolved-creature answer | **26.6%** |
| Slop engine + any table pre-activation answer, including Jaia | **48%–53%** |
| Slop engine + any table resolved-creature answer | **35%–39%** |
| Slop engine + direct graveyard coverage somewhere at table | **15%–19%** |

This is the first quantitative approximation of the deck's intended table role. It suggests that the “profit while someone else handles it” state is common enough to be a real strategy before the threat resolves, but not reliable enough to justify passing through an uncovered activation.

## Strategic interpretation

### What the data supports

- Do not mulligan or construct as though Creature Factory must solo-police every pod.
- A visible Kinnan/Sisay/Magda-style cast will often have external coverage.
- Use table talk to allocate the primary answer and preserve Creature Factory as backup.
- Engines that pay for opponents casting interaction are structurally aligned with the field.
- Convert immediately after the fight; external policing makes Creature Factory the likely post-fight beneficiary only until opponents recognize that fact.

### What the data does not support

- Passing priority merely because a blue deck is present.
- Assuming Blue Farm has removal after the commander resolves.
- Assuming any opponent has graveyard hate for Tayam/Lumra.
- Treating “the answer exists in a 98” as equivalent to “the player can and will use it.”
- Cutting all resolved-permanent coverage because aggregate table coverage looks high.

## Next measurement

The remaining unknown is post-fight conversion, not prevalence. The next simulation should estimate:

\[
P(\text{engine active} \cap \text{external answer spent} \cap \text{Jaia preserves backstop} \cap \text{win within one turn cycle})
\]

It should compare at least three pod classes:

1. Broad permanent engine + two interactive opponents.
2. Broad permanent engine + one interactive opponent + one low-interaction opponent.
3. Two broad permanent engines, where external coverage is divided and free-rider incentives worsen.

The deck-building decision is not “how many answers does Jaia need?” It is the minimum backstop density that keeps the uncovered-pod rate acceptable while maximizing the probability of a protected post-first-fight conversion.

## Limits and provenance

- Arizona: four events, 96 seats, 67 commander records, 64 complete 90+ card lists.
- Arizona–Las Vegas: 12 events, 290 seats, 72 commander records.
- Global conservative subset: 212 cEDH-titled events, 6,075 seats, 3,370 commander records, 3,218 complete 90+ card lists.
- Missing decklists are not assumed random.
- Commander repetitions are counted as entries.
- Hypergeometric hand estimates use nine cards seen from the 98-card library and no mulligans/tutors.
- Card tags are functional approximations; several answers are conditional, tempo-only, or too expensive for the first window.
- No numerical willingness-to-interact estimate is claimed.
- Source data: TopDeck normalized/raw snapshots, META-002, META-003, META-004, and Creature Factory Moxfield v173.

