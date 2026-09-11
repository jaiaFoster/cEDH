# META-007 — Creature Factory archetype fingerprint and matchup spread

**Prepared:** 2026-09-11
**Subject:** Creature Factory, Thrasios/Tymna
**Moxfield version:** 12
**Moxfield updated:** 2026-09-11T01:38:02.85Z
**Snapshot retrieved:** 2026-09-11T04:45:06.622496Z
**98 hash:** `ad92649a39432d2ca1d69d4c8ec7558a3e606a1c5f654dac5fb216c92b3355f8`
**Tournament weighting:** META-006 North Las Vegas forecast
**Scope:** construction fingerprint plus observed tournament matchup associations
**Explicit exclusions:** no gameplay simulation and no candidate-card tests

This is an informational handoff for the deck-builder. It does not independently change the 98.

## Executive conclusion

The most accurate archetype label is:

> **Engine-forward creature-toolbox midrange with stack-backstop interaction, a secondary slop/capture layer, and noncompact permanent-based conversion.**

“Midrange” is correct but insufficient. Creature Factory differs from conventional T&T in four ways that materially affect its matchup spread:

1. It uses substantially more creatures and a deeper permanent network.
2. It has strong stack participation but narrower post-resolution coverage.
3. It wins through overlapping creature, Pod, Cradle and activated-ability systems rather than a compact Oracle package.
4. It can survive and profit from a fight, but has fewer ways than conventional T&T or Blue Farm to convert at the exact end of that fight.

The deck is therefore not broadly weak or strong into “turbo” or “midrange.” Its matchup spread is directional:

- **Best structural environment:** spell-heavy tables that feed Remora, Rhystic, Lotho and Cabbage while giving the deck time to accumulate creatures and mana.
- **Most dangerous structural environment:** resolved commander/permanent engines plus sparse graveyard or battlefield interaction.
- **Most deceptive environment:** a permanent engine plus Blue Farm. Blue Farm can supply the missing answer, but generic T&T performs below baseline in blue-stack pods because the other blue deck often wins the recovery race.

## 1. Evidence and limits

META-007 uses three evidence layers:

1. **Exact construction:** the live version-12 98 and its functional packages.
2. **Observed matchup association:** 717 global Swiss pods containing T&T with all four commanders known, preserved by META-006.
3. **Tournament weighting:** the North Las Vegas commander forecast from META-006.

No sufficient tournament sample exists for this exact 98. Consequently:

- observed PPG belongs to the broader T&T population;
- construction grades describe how Creature Factory likely differs from that population;
- the report does not represent a construction grade as an exact win-rate adjustment;
- pilot, seat, event, co-opponents and internal archetype variation remain confounders.

## 2. Exact construction fingerprint

### Direct counts

| Feature | Version-12 count | Interpretation |
|---|---:|---|
| Creatures | 33 | Far above conventional midrange; core source of mana, engines, tutors and conversion |
| Dedicated lands | 27 | `Sink into Stupor` provides an additional modal land slot |
| Conventional counters/redirectors | 11 | Strong ability to participate on the stack without becoming full table police |
| Proactive protection/turn-control pieces | 6 | Grand Abolisher, Ranger-Captain, Silence, Teferi, Veil and Voice support protected turns |
| Copy effects | 2 | Clever Impersonator and Mockingbird; secondary slop package, not maximum slop |
| Direct search effects | 15 | Broad tutor optionality; Pod and Survival add repeatable selection beyond this count |
| Tagged resolved-creature answers | 5 | Meaningfully thinner than the stack layer |
| Tagged artifact/enchantment answers | 4 | Several are modal lands or expensive/conditional channel effects |
| Dedicated graveyard-interaction cards | 2 | Deathrite Shaman and Endurance; the clearest coverage bottleneck |
| Primary flash systems | 2 | Emergence Zone and Teferi; materially below flash-heavy T&T designs |

The current snapshot differs from META-006 by `Voice of Victory` replacing `Mox Amber`. That change increases protected-turn density and creature/Cradle material while reducing zero-mana acceleration and the utility of an early commander as a mana enabler.

### Construction scoring rubric

Scores are ordinal comparisons against successful contemporary midrange lists:

- `0` — deficient
- `1` — below the benchmark
- `2` — approximately benchmark level
- `3` — above benchmark
- `4` — defining strength

They are construction scores, not simulated outcome percentages.

| Axis | Creature Factory | Creature/CHUDS T&T | Conventional T&T | Blue Farm | High-slop T&T |
|---|---:|---:|---:|---:|---:|
| Early development | 3 | 3 | 2 | 3 | 2 |
| First-attempt speed | 1 | 2 | 3 | 4 | 2 |
| Protected-attempt quality | 2 | 2 | 3 | 4 | 3 |
| Post-fight conversion | 1 | 2 | 3 | 4 | 3 |
| Stack agency | 3 | 2 | 3 | 3 | 3 |
| Resolved-board agency | 1 | 2 | 2 | 2 | 2 |
| Recovery/resilience | 3 | 3 | 2 | 2 | 3 |
| Opponent-resource capture | 2 | 2 | 1 | 2 | 4 |
| Conversion compactness | 1 | 2 | 4 | 4 | 2 |
| Self-sufficiency across answer types | 1 | 2 | 3 | 3 | 2 |

### What the fingerprint means

Creature Factory is not slow at **doing something**. It is slower at turning development into a protected, compact win. That distinction is the heart of the archetype.

- The deck's development score comes from dorks, fast mana, Cradle, premium engines and an unusually dense tutor network.
- Its low attempt/compactness scores come from multi-card, board-mediated conversion rather than Oracle/Consultation or Breach.
- Its resilience comes from overlapping engines, commander outlets, redundant creature tutors and lines that can pivot between Pod, Survival, Cradle and activated abilities.
- Its self-sufficiency score is held down by resolved-permanent and graveyard coverage, not by lack of stack interaction.
- Its slop score is moderate. It profits from opposing spells and resources, but two copy effects do not make the deck a dedicated clone shell.

## 3. Benchmark comparison

The prior global top-ten comparison found:

| Cohort | Average creatures | Average total interaction | Average protection | Average tutors | Average engines | Average flash tools | Average clones |
|---|---:|---:|---:|---:|---:|---:|---:|
| Creature Factory, earlier baseline | 33 | 19 | 4 | 16 | 15 | 1 | 2 |
| Top-ten T&T | 26.8 | 19.0 | 5.8 | 13.6 | 13.0 | 3.0 | 3.9 |
| Top-ten Blue Farm | 16.0 | 18.3 | 4.4 | 11.4 | 9.7 | 1.1 | 1.6 |

Version 12 has moved away from the earlier maximum-engine posture:

- Birthing Ritual, Seedborn Muse and Sylvan Library are no longer present.
- Swan Song and Sink increased interaction breadth.
- Teferi and Voice increased protected-turn density.
- Spellseeker became Talion, trading deterministic tutor access for an independent engine.
- Mox Amber became Voice, trading acceleration for protection.

The deck is now closer to contemporary T&T on interaction/protection, but it remains farther away on flash density and conversion compactness. It is also still substantially more creature-dependent.

## 4. Observed T&T matchup baseline

The global T&T baseline was **1.289 PPG** across 717 fully observed Swiss pods.

| Opposing condition | Pods | T&T win rate | Draw rate | PPG | Versus baseline |
|---|---:|---:|---:|---:|---:|
| Broad permanent engine present | 343 | 21.3% | 23.9% | 1.303 | +0.014 |
| Narrow commander engine present | 315 | 20.6% | 24.8% | 1.279 | -0.009 |
| Blue-stack deck present | 429 | 18.6% | 28.2% | 1.214 | -0.074 |
| Permanent engine plus blue stack | 180 | 18.9% | 28.9% | 1.233 | -0.055 |
| Two broad-engine opponents | 72 | 23.6% | 22.2% | 1.403 | +0.114 |

The aggregate result does not support “all permanent-engine pods are bad for T&T.” It does support two narrower conclusions:

1. individual commander engines such as Tayam, Magda and Sisay can still be difficult;
2. adding another blue-stack player does not automatically improve T&T's tournament result, even when that player improves the table's answer coverage.

## 5. Specific matchup spread

### Rubric

Two deck-specific mechanism scores are added to the observed baseline:

- **Containment:** how well Creature Factory can help prevent or interrupt the opponent's primary conversion.
- **Cash-out:** how well Creature Factory can turn the resulting exchange into its own win before that opponent or a policing player rebuilds.

Both use the same `0–4` construction rubric. The final directional grade is deliberately broader than a false-precision win percentage.

| Opponent | Forecast pod encounter | Generic T&T pods | Generic T&T PPG | Containment | Cash-out | Creature Factory direction | Confidence |
|---|---:|---:|---:|---:|---:|---|---|
| Blue Farm | 19.5% | 146 | 1.199 | 4 | 2 | Slightly unfavorable | Medium-high |
| T&T mirror | 17.3% | 67 | 1.403 | 3 | 2 | Approximately even | Medium |
| Kinnan | 17.0% | 166 | 1.410 | 2 | 3 | Volatile/even, structural danger | Medium-high |
| Kefka | 15.9% | 21 | 1.571 | 4 | 3 | Favorable direction | Low |
| Urza | 13.0% | 13 | 1.154 | 2 | 2 | Slightly unfavorable | Low |
| RogSi | 9.5% | 88 | 1.000 | 4 | 2 | Unfavorable | Medium |
| Tayam | 9.2% | 35 | 0.943 | 1 | 3 | Unfavorable | Medium-low |
| Magda | 9.2% | 45 | 0.911 | 2 | 3 | Unfavorable | Medium |
| Sisay | 6.5% | 74 | 1.095 | 2 | 2 | Unfavorable | Medium |
| Ral | 5.5% | 48 | 1.042 | 4 | 2 | Slightly unfavorable despite good tools | Medium |
| Rograkh/Thrasios | 5.3% | 83 | 0.843 | 3 | 1 | Strongly unfavorable | Medium-high |
| Crystal | 4.0% | 35 | 1.057 | 4 | 2 | Slightly unfavorable | Medium-low |
| Nick Fury | 2.6% | 34 | 0.706 | 3 | 2 | Unfavorable, uncertain archetype | Low |

### Matchup reads

#### Blue Farm

Creature Factory is well equipped to participate in its stack fights and profit from its spell volume. The weakness is not initial containment. It is that Blue Farm's compact conversion, flash access and recovery can beat Creature Factory to the post-fight cash-out. `Cabbage`, `Lotho`, Remora and Rhystic improve the resource contest; they do not by themselves solve conversion latency.

#### Kinnan

The large observed sample is better than the structural story would predict. Generic T&T scored 1.410 PPG across 166 Kinnan pods. Creature Factory has Subtlety, Gilded Drake, Swift Reconfiguration, Sink, Otawara and counters for the first layer, and its own creature economy performs well in longer games.

The matchup remains volatile because many of those answers are tempo or conditional, and a protected activation changes the game immediately. This should not be called a proven bad matchup; it should be called a high-exposure matchup in which the cost of one answer-allocation error is unusually high.

#### Tayam

This is the cleanest structural weakness. Tayam attacks the deck's two thinnest axes simultaneously: resolved-permanent interaction and graveyard interaction. A Blue Farm player improves cast/protection coverage but may not answer an established noncreature permanent or recursion loop. Creature Factory's cash-out can be good after Tayam is contained, but getting to that state is the problem.

#### Magda and Sisay

Both reward answering the commander before or at the first consequential activation. Creature Factory has enough relevant cards to participate, but not enough unconditional post-resolution removal to assume it can carry the role alone. They remain unfavorable even though the deck can out-resource them after a successful table response.

#### RogSi and Rograkh/Thrasios

Creature Factory has strong stack tools, but these decks compress the setup window. Rograkh/Thrasios was the worst large-sample opponent for generic T&T. Creature Factory's deeper board development and slower conversion make the speed mismatch more—not less—important. The matchup asks for early agency plus a real development trajectory; an interaction-only keep merely delays the loss.

#### Kefka, Ral, Crystal and Nick Fury

These decks generally produce the spell volume and longer exchanges Creature Factory is designed to exploit. Yet Ral, Crystal and Nick Fury all showed below-baseline generic T&T results. The likely explanation is not lack of relevant interaction but failure to convert before their commander/value engines retake control. Kefka's positive result is promising but based on only 21 pods and should not be generalized.

## 6. Tournament-weighted pressure index

The pressure index is:

`forecast encounter probability × max(0, T&T baseline PPG − opponent-conditioned PPG)`

It measures how much an observed negative matchup contributes to this event's expected burden. It is normalized so the highest measured burden equals 100. It does not include Creature Factory's qualitative mechanism adjustment.

| Rank | Opponent | Pressure index | Why it matters to this exact deck |
|---:|---|---:|---|
| 1 | Magda | 100 | Activation commander plus narrow post-resolution coverage |
| 2 | Tayam | 92 | Battlefield and graveyard coverage fail together |
| 3 | RogSi | 78 | Early speed compresses engine setup and conversion |
| 4 | Rograkh/Thrasios | 68 | Worst large-sample generic T&T opponent; faster comparable mana shell |
| 5 | Blue Farm | 50 | Very common; policing help is offset by post-fight competition |
| 6 | Urza | 50 | Venue-relevant artifact engine, but only 13 observed T&T pods |
| 7 | Nick Fury | 43 | Poor observed result but low event exposure and immature sample |
| 8 | Ral | 39 | Tools align, but observed cash-out result remains below baseline |
| 9 | Sisay | 36 | Commander activation and protection burden |
| 10 | Crystal | 27 | Lower exposure; value-recovery race remains relevant |

Kinnan receives a zero formula score because its observed T&T PPG was above baseline. It should nevertheless remain a **high preparation priority** because it is projected in 17% of pods and directly attacks Creature Factory's weaker response layer. The formula measures historical performance burden, not punishment severity after a misplay.

## 7. Table-composition effects

### Permanent engine plus Blue Farm

This is the central mixed-pod case.

- Blue Farm increases the chance that the engine's cast or protection spell is answered.
- Creature Factory can conserve a counter and develop an engine.
- Blue Farm also has the most compact post-fight conversion package at the table.
- Generic T&T scored 1.233 PPG in engine-plus-blue pods, below its 1.289 baseline.

The correct role is not “let Blue Farm handle it.” It is:

1. identify which player covers the commander/permanent;
2. cover only the missing protection or payoff layer;
3. track which Blue Farm conversion/protection cards were spent;
4. evaluate an immediate conversion before returning to setup.

### Two permanent engines

Generic T&T performed well in the 72 observed pods containing two broad engines. The likely mechanism is mutual threat pressure and more predictable resource allocation, not inherent safety. Creature Factory's durable engines and tutor optionality are useful here, provided it does not volunteer to answer both opponents.

### Two blue-stack opponents

This is not automatically a safe pod. It often creates more answers but also more draws, more competing engines and two opponents capable of converting after the first fight. Creature Factory should prioritize a compact development hand and preserve a cash-out path rather than accumulate redundant generic interaction.

## 8. Deck-builder implications without card tests

META-007 does not select additions or cuts. It narrows the construction problem to three role gaps:

1. **Resolved-board independence:** the list has much less unconditional battlefield coverage than stack coverage.
2. **Post-fight conversion latency:** protection has improved, but flash access and compactness remain below successful T&T.
3. **Graveyard independence:** two dedicated pieces leave Tayam and recursion tables highly dependent on opponent cooperation.

Any proposed change should state which of those gaps it addresses and what existing strength it costs. Adding another generic value engine does not address the measured problems. Moving toward a true high-slop shell would require materially more than one additional clone; it would be an archetype decision, not a free upgrade.

## 9. Final matchup classification

| Tier | Matchups |
|---|---|
| Favorable direction | Kefka; spell-heavy slower tables where engines resolve and the first fight does not immediately end the game |
| Approximately even / volatile | T&T mirror; Kinnan; creature-midrange mirrors |
| Slightly unfavorable | Blue Farm; Ral; Crystal; Urza |
| Unfavorable | Tayam; Magda; Sisay; RogSi; Nick Fury pending more evidence |
| Strongly unfavorable | Rograkh/Thrasios; compositions with multiple fast opponents and no reliable resolved-permanent coverage |

The final diagnosis is:

> Creature Factory is a resilient, engine-forward midrange deck with above-benchmark stack agency and tutor flexibility. Its matchup losses are concentrated not in an inability to participate, but in two transitions: stopping a threat after it becomes a permanent, and converting before the player who helped stop it wins the recovery race.

## Sources and linked evidence

- [META-006 — Hobbit Collector Box pre-tournament update](META-006-hobbit-collector-box-pre-tournament-meta-update.md)
- [META-006 supporting data](supporting/META-006-data.json)
- [META-005 — matchup prevalence and external policing](META-005-matchup-prevalence-and-external-policing.md)
- [META-004 — destructive matchup analysis](META-004-creature-factory-destructive-matchup-analysis.md)
- [META-003 — global 30-day comparison](META-003-global-30d-deck-comparison.md)
- [Current canonical Moxfield snapshot](../../data/deck_sources/moxfield/tymna-thrasios/current.json)
- [Tournament event page](https://topdeck.gg/event/september-cedh-event)

