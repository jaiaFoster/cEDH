# META-006 — Hobbit Collector Box pre-tournament metagame update

**Prepared:** 2026-09-09
**Tournament:** MTG: cEDH “The Hobbit Collector Box” Tournament
**Date and venue:** Saturday, 2026-09-12, Power 9 Games, North Las Vegas, Nevada
**Region key:** `US-SOUTHWEST-AZ-LV`
**Subject deck:** Creature Factory, Moxfield version 6, updated 2026-09-09
**Content hash:** `694a366eeca3c8d62be93b4c33afd5f79ebd9b8fb5055125fd696ad81661f71c`

This is an informational handoff for Jaia and the deck-builder. It does not prescribe changes to the 98.

## Executive read

The best forecast is not “prepare for one dominant deck.” It is “prepare for a small, heterogeneous field whose most likely clusters are Blue Farm/T&T, Kinnan and other resolved-permanent engines, plus a venue-specific tail of Kefka and artifact commanders.”

- The live event page showed **15 registered of 34 possible players** on September 9, but no public roster, commander declarations or submitted decklists. Every commander projection below is therefore a forecast, not a registration claim.[^event][^event-state]
- The event uses **four Swiss rounds and a Top 10**, with the top two seeds receiving byes into the final pod. At 34 players, 10/34 (29.4%) advance; if attendance resembles the venue's prior 18-player event, more than half advance. The top-two bye makes clean wins and avoiding preventable draws unusually valuable.[^event]
- The latest disclosed Arizona field is engine-heavy. At the September 6 Arcanum event, Kinnan occupied three of the top six places and won; two T&T lists reached the Top 10.[^arcanum]
- In the 30-day disclosed AZ/LV sample, Blue Farm and T&T were each 8.0%, Tayam 6.8%, and Kinnan, RogSi and T&Yoshi each 5.7%. However, Nevada decklist coverage is extremely poor: only three Las Vegas lists were structured, so these shares describe the **known local lists**, mostly Arizona, not the complete Nevada field.
- Globally, Blue Farm and Kinnan remain the two clear population leaders. cEDH Stats' broader one-month sample has Blue Farm at 7.5% and Kinnan at 7.0%; T&T is 3.6%. The repository's conservative TopDeck sample agrees on ordering: 7.8%, 7.6% and 3.7%, respectively.[^commanders]
- The current Creature Factory list has moved toward cheap interaction since the earlier reports: Mental Misstep replaced Birthing Ritual. It has also changed its green tutor and engine configuration: Green Sun's Zenith replaced Summoner's Pact, and Talion replaced Spellseeker.

The matchup thesis needs one correction. Across 717 fully observed global T&T Swiss pods, T&T did **not** underperform when a permanent-engine deck was present: 1.30 points per game (PPG) versus a 1.29 baseline. It did underperform when another blue-stack deck was present: 1.21 PPG, with a higher draw rate. A Blue Farm player may help answer a Tayam permanent, but also competes to win, draws cards from the same fight and can convert first. “External answer exists” and “the pod is favorable” are different measurements.

## 1. Event facts and uncertainty

| Item | Confirmed state |
|---|---|
| Start | Saturday, September 12, 10:00 a.m. local time |
| Venue | Power 9 Games, 2575 E. Craig Rd., North Las Vegas |
| Entry | $30, paid onsite |
| Structure | Four Swiss rounds, Top 10; top two seeds bye directly to final pod |
| Decklists | Due through TopDeck before round one |
| Prize | Winner: sealed Hobbit Collector Booster Box; other final-pod players: one collector booster each |
| Live registration check | 15 registered, 34 cap, 19 seats remaining |
| Public roster/decks | None visible as of the check |

The schedule is doors at 9:00, rounds at 10:00 and 11:45, lunch at 1:30, rounds at 2:15 and 4:00, and Top 10 at 5:45.[^event][^power9]

Because decklists are not due until round one, an exact preregistered metagame cannot yet be reconstructed. The report therefore uses three layers:

1. the same venue's previous event as the venue prior;
2. disclosed Arizona plus Las Vegas/Henderson lists from the last 30 days;
3. the global 30-day field as a stabilizer.

## 2. Event-specific forecast

The forecast weights the previous same-venue event 40%, the disclosed AZ/LV 30-day lists 40%, and the global 30-day lists 20%. This is a transparent judgmental blend, not a fitted predictive model. It intentionally gives local behavior more weight than global popularity.

| Commander | Forecast share | Expected at 18 | Expected at 24 | Expected at 34 | Chance among three opponents* |
|---|---:|---:|---:|---:|---:|
| Blue Farm | 7.0% | 1.3 | 1.7 | 2.4 | 19.5% |
| Tymna/Thrasios | 6.1% | 1.1 | 1.5 | 2.1 | 17.3% |
| Kinnan | 6.0% | 1.1 | 1.4 | 2.0 | 17.0% |
| Kefka | 5.6% | 1.0 | 1.3 | 1.9 | 15.9% |
| Urza | 4.5% | 0.8 | 1.1 | 1.5 | 13.0% |
| RogSi | 3.3% | 0.6 | 0.8 | 1.1 | 9.5% |
| Rakdos, the Muscle | 3.2% | 0.6 | 0.8 | 1.1 | 9.3% |
| Tayam | 3.2% | 0.6 | 0.8 | 1.1 | 9.2% |
| Magda | 3.2% | 0.6 | 0.8 | 1.1 | 9.2% |
| T&Yoshi | 2.6% | 0.5 | 0.6 | 0.9 | 7.7% |
| Ishai/Rograkh | 2.5% | 0.4 | 0.6 | 0.8 | 7.2% |
| Tivit | 2.5% | 0.4 | 0.6 | 0.8 | 7.2% |

\*The opponent probability is `1-(1-share)^3`; it assumes independent random seats and should be read as a planning estimate.

At the strategic-family level, the model forecasts approximately:

| Family | Forecast field share | Chance at least one among three opponents |
|---|---:|---:|
| Broad permanent/activated engine | 17.6% | 44.0% |
| Narrow commander-centric engine | 15.8% | 40.2% |
| Blue-stack deck | 31.7% | 68.1% |

These categories overlap where strategically appropriate. The practical forecast is that **a permanent/activation problem appears in roughly two of five pods, while a blue-stack player appears in roughly two of three**. That makes the mixed pod—one engine deck, one blue-stack deck, one other deck—the central preparation case.

### Venue prior

Power 9's previous recorded cEDH tournament used the same four-Swiss/Top-10 structure and had 18 players. The field included two Urza, two Kefka, and one each of Tivit, Kinnan, Rakdos Muscle, Kenrith, Magda, Iroh, Aang, Gwenom, Ishai/Rograkh, Francisco/Thrasios, T&T, Najeela, Yuriko and Blue Farm. Tivit won.[^venue-prior]

This is too small and old to establish stable shares. It is still the strongest evidence that this venue's tail may contain more artifact/control and Kefka shells than an Arizona-only sample predicts.

## 3. Local metagame: previous 30 days

### Data health

- Window: August 10 through September 9, 2026.
- Eligibility: imported TopDeck events with at least 16 players and titles explicitly indicating cEDH, competitive EDH or an appropriate qualifier.
- Excluded: casual, bracket 1–3, precon, budget, test, dummy and dry-run records.
- Result: **11 events, 282 seats, 88 structured commander/deck records and 254 pod records**.
- The 88 known lists are only 31.2% of all local seats. Arizona accounts for nearly all usable deck evidence; several Las Vegas/Henderson weekly events published standings but no structured decklists.

Accordingly, the `Known share` below is the observed distribution among disclosed lists. The `All-seat floor` treats every missing list as some other commander and is the conservative minimum.

| Commander | Entries | Known share | All-seat floor | Pod encounter | PPG | Top cuts / eligible | Event wins |
|---|---:|---:|---:|---:|---:|---:|---:|
| Blue Farm | 7 | 8.0% | 2.5% | 22.2% | 1.19 | 1/4 | 0 |
| Tymna/Thrasios | 7 | 8.0% | 2.5% | 22.2% | 1.35 | 2/7 | 0 |
| Tayam | 6 | 6.8% | 2.1% | 19.3% | 0.95 | 0/3 | 0 |
| Kinnan | 5 | 5.7% | 1.8% | 16.3% | 2.18 | 4/5 | 1 |
| RogSi | 5 | 5.7% | 1.8% | 16.3% | 0.64 | 0/1 | 0 |
| T&Yoshi | 5 | 5.7% | 1.8% | 16.3% | 1.65 | 1/3 | 0 |
| Maralen | 4 | 4.5% | 1.4% | 13.2% | 1.79 | 0/1 | 1 |
| Ral | 3 | 3.4% | 1.1% | 10.0% | 1.85 | 1/3 | 0 |
| Sisay | 3 | 3.4% | 1.1% | 10.0% | 0.69 | 0/2 | 0 |
| Crystal | 2 | 2.3% | 0.7% | 6.7% | 2.43 | 0/1 | 0 |
| Godo | 2 | 2.3% | 0.7% | 6.7% | 2.10 | 1/2 | 0 |
| Kefka | 2 | 2.3% | 0.7% | 6.7% | 1.55 | 1/2 | 0 |
| Rakdos Muscle | 2 | 2.3% | 0.7% | 6.7% | 2.00 | 0/1 | 0 |
| Rograkh/Thrasios | 2 | 2.3% | 0.7% | 6.7% | 2.00 | 1/2 | 1 |

The sample is too small for rankings by PPG to be stable. The actionable signal is the combination of **presence and architecture**: Blue Farm/T&T are common, while Kinnan/Tayam/Sisay/Magda and adjacent permanent engines collectively form a much larger problem than any single name.

### Latest high-information Arizona event

The September 6 Arcanum event in Tucson had 40 players and 39 submitted lists. Its Top 10 was:

| Finish | Commander | Pilot | Decklist |
|---:|---|---|---|
| 1 | Kinnan | Brice Quarton | [Moxfield](https://moxfield.com/decks/wra9JpKGSEqI1HXtjzglYQ) |
| 2 | Blue Farm | Zach Gable | [Moxfield](https://moxfield.com/decks/b8RZsIyaK0y0Ju6j3UyJYg) |
| 3 | Kinnan | Brandon Lee | [Moxfield](https://moxfield.com/decks/onSgAWEUmHS4vwOcOYi9rA) |
| 4 | T&Yoshi | Kenjamin | [Moxfield](https://moxfield.com/decks/AdDY88ZnGUyxfidYb4FSmA) |
| 5 | Godo | Jordan Larson | [Moxfield](https://moxfield.com/decks/48Q0ZRbjJkSM8gKSDNJSiQ) |
| 6 | Kinnan | Gemein Cho | [Moxfield](https://moxfield.com/decks/DsByH8iavUSTjMkBZSOgyQ) |
| 7 | T&T | Ross Donaldson | [Moxfield](https://moxfield.com/decks/3S05d3DUuEW_IjoBtlG5yQ) |
| 8 | T&T | Dakota Cline | [Moxfield](https://moxfield.com/decks/AYB3Wun5aESqo54ErWjQLA) |
| 9 | Kefka | Ryan Osoy | [Moxfield](https://moxfield.com/decks/yDe7DnCgBEePcnVn-wZiqQ) |
| 10 | Bruce Banner | Jesse Feliciano | [Moxfield](https://moxfield.com/decks/v-XNBjrX10m8n2Two2Mcpw) |

The full event page and standings are on cEDH Stats.[^arcanum] The most concrete local preparation signal is Kinnan: three Top-6 finishes and the event win. The broader Top 15 also included Winota, Rakdos Muscle, Sisay, Derevi and Tayam, reinforcing the resolved-permanent theme.

## 4. Global metagame

### Primary one-month baseline: cEDH Stats

| Commander | Entries | Meta share | PPG | Top-cut rate | Three-opponent encounter |
|---|---:|---:|---:|---:|---:|
| Blue Farm | 517 | 7.5% | 1.40 | 28% | 20.9% |
| Kinnan | 483 | 7.0% | 1.36 | 27% | 19.6% |
| Rograkh/Thrasios | 310 | 4.5% | 1.33 | 24% | 12.9% |
| RogSi | 316 | 4.6% | 1.16 | 18% | 13.2% |
| Sisay | 281 | 4.1% | 1.37 | 24% | 11.8% |
| Tymna/Thrasios | 249 | 3.6% | 1.23 | 21% | 10.4% |
| Ral | 154 | 2.2% | 1.23 | 23% | 6.5% |
| Crystal | 147 | 2.1% | 1.43 | 35% | 6.2% |
| Magda | 146 | 2.1% | 1.29 | 25% | 6.2% |
| Nick Fury | 135 | 2.0% | 1.50 | 30% | 5.9% |
| Tayam | 128 | 1.9% | 1.34 | 25% | 5.6% |
| T&Yoshi | 108 | 1.6% | 1.33 | 24% | 4.7% |
| Arcum | 62 | 0.9% | 1.51 | 29% | 2.7% |

cEDH Stats is the primary generic-metagame source because its one-month sample is broader and already applies its published eligibility/methodology.[^commanders][^method]

Compared with its three-month baseline:

- T&T grew from 3.2% to 3.6%, but PPG fell from 1.30 to 1.23 and top-cut rate from 27% to 21%.
- Blue Farm stayed essentially stable and strong: 7.3% to 7.5%, 1.39 to 1.40 PPG.
- Kinnan's share eased from 7.2% to 7.0%, while PPG and top-cut rate improved from 1.32/25% to 1.36/27%.
- Crystal rose from 1.8% to 2.1% and 29% to 35% top-cut rate.
- Nick Fury rose from 1.5% to 2.0% and retained elite 1.50 PPG, though the archetype is newer and has less accumulated evidence.[^stats]

### Repository verification sample

The conservative TopDeck filter found **240 events, 7,254 seats, 4,298 structured lists and 7,373 pod records**. This sample is narrower than cEDH Stats because it requires explicit competitive event naming; its purpose is exact pod and decklist analysis, not replacement of the broader baseline.

Its top six were Blue Farm 7.8%, Kinnan 7.6%, RogSi 4.9%, Rograkh/Thrasios 4.4%, Sisay 4.2% and T&T 3.7%. Broad permanent/activation decks made up 20.7% of known lists, producing an estimated 50.2% chance of at least one such opponent in a random pod. Blue-stack decks made up 29.3%, producing a 64.7% encounter estimate.

## 5. The real T&T matchup spread

These figures use Swiss pods with all four commanders known. They measure how **generic T&T entries** performed when an opponent appeared, not how Creature Factory specifically performed and not causal card effects.

### Global conditional results

| Pod condition | T&T pods | Win rate | Draw rate | PPG | Difference from baseline |
|---|---:|---:|---:|---:|---:|
| All observed T&T pods | 717 | 20.6% | 25.7% | 1.289 | — |
| Broad permanent engine present | 343 | 21.3% | 23.9% | 1.303 | +0.014 |
| Narrow commander engine present | 315 | 20.6% | 24.8% | 1.279 | -0.009 |
| Blue-stack deck present | 429 | 18.6% | 28.2% | 1.214 | -0.074 |
| Permanent engine + blue stack | 180 | 18.9% | 28.9% | 1.233 | -0.055 |
| Two broad-engine opponents | 72 | 23.6% | 22.2% | 1.403 | +0.114 |

This does not prove that engine pods are good. It rejects the simple version of “T&T necessarily loses to decks it cannot personally remove.” Multiplayer composition matters: engines may police one another, attract early resources or slow conversion enough for T&T to recover.

### Common individual opponents

| Opponent | T&T pods | T&T PPG | Read |
|---|---:|---:|---|
| Kinnan | 166 | 1.410 | Above baseline; not evidence that Kinnan is harmless |
| Blue Farm | 146 | 1.199 | Below baseline, more competition for the same post-fight window |
| RogSi | 88 | 1.000 | Fast stack deck; significantly below baseline |
| Rograkh/Thrasios | 83 | 0.843 | Lowest large-sample matchup in this table |
| Sisay | 74 | 1.095 | Below baseline; permanent commander conversion remains demanding |
| T&T mirror | 67 | 1.403 | Above baseline in this sample |
| Ral | 48 | 1.042 | Below baseline |
| Magda | 45 | 0.911 | Below baseline; compact commander activation pressure |
| T&Yoshi | 43 | 1.349 | Near/above baseline |
| Tayam | 35 | 0.943 | Below baseline and strategically relevant, but small |
| Crystal | 35 | 1.057 | Below baseline; rising global archetype |
| Nick Fury | 34 | 0.706 | Very low directional result; new/small sample |

The local T&T subset contains only 32 pods. Its baseline was 1.44 PPG; Kinnan pods were 1.17 (n=6), Blue Farm 0.33 (n=6), and Tayam 0.33 (n=3). These are useful warning signals, not estimates precise enough to rank matchups.

## 6. How often will someone have the missing answer?

This section converts decklist contents into a first-nine-card access estimate: opening seven plus two draws, without mulligans, tutors, card draw, mana, timing or willingness to spend the card. The card tags are deliberately conservative and are documented in the supporting JSON.

| Problem | Creature Factory: tagged cards | Ours sees one by card 9 | Two random local opponents: at least one | Combined ceiling |
|---|---|---:|---:|---:|
| Counter/remove commander before or just after activation | 7 | 50.2% | 47.8% | 74.0% |
| Remove a resolved creature | 5 | 38.9% | 36.5% | 61.2% |
| Remove artifact/enchantment | 4 | 32.4% | 37.9% | 58.0% |
| Interact with graveyard | 2 | 17.6% | 10.5% | 26.2% |

“Combined ceiling” is `1-(1-ours)*(1-two-opponents)`. It assumes independence and availability. It is emphatically **not** the chance the table successfully stops the threat. Cards can be spent earlier, stranded by mana or protected through; opponents can decline to act.

The useful conclusion is narrower:

- For a commander entering or activating, the pod usually has a plausible first-nine resource somewhere.
- After a creature or artifact/enchantment resolves, the combined coverage falls to about 58–61% even before accounting for mana and incentives.
- Graveyard coverage is genuinely sparse. Tayam plus a protected recursion engine is therefore not merely “someone else will get it” territory.
- The best table-talk question is not “does anyone have interaction?” It is “who can answer the resolved permanent, and who can stop protection?” This separates layers and keeps Jaia in the backstop role.

## 7. Matchup and pod plan for Creature Factory

| Opposing family | Estimated event exposure | What must be stopped | Best current resources | External-policing policy | Failure mode |
|---|---:|---|---|---|---|
| Kinnan | ~17% pod encounter | Kinnan activation with sufficient mana; Basalt/Monolith lines; protected payoff | Subtlety, Gilded Drake, Swift Reconfiguration, Sink, Otawara, counters | Ask the other blue player to cover cast/stack; retain a post-resolution layer if possible | Treating Kinnan itself as harmless ramp and allowing an activation window |
| Tayam | ~9% forecast; ~19% in disclosed local pods | Tayam activation, Rule of Law/protection pieces, graveyard setup | Endurance, Deathrite, Gilded Drake, Swift, Sink, Boseiju/Otawara | Blue player can cover cast/protection; do not assume blue can remove a resolved noncreature permanent | Graveyard and permanent answers are the thinnest shared resource |
| Sisay/Magda/Arcum/Urza | Family contributes heavily to 40–44% engine encounter | First meaningful commander activation or deterministic artifact line | Gilded Drake, Subtlety, Swift, Sink, Boseiju, Otawara, Colossal Skyturtle | Assign commander and payoff layers explicitly | Passing priority because an opponent “has blue” when the problem is already a permanent |
| Blue Farm/RogSi/RogThras | ~68% chance of some blue-stack deck | Early protected win; post-fight conversion | Free counters, Misstep, Mindbreak, Commandeer, Veil, Ranger-Captain, Teferi | Let them spend first when their incentive is aligned, but preserve a way to win or stop their pivot | Helping them win the resource exchange, then failing to convert before they do |
| Crystal/Nick Fury/Kefka/Ral | Rising/venue-relevant control-combo cluster | Commander/value snowball and compact conversion | Early engine development, creature pressure, targeted commander answers, backstop stack interaction | Do not let novelty obscure the commander as engine | Long games that become their inevitability while the table trades inefficiently |
| T&T/T&Yoshi | T&T ~17%; T&Yoshi ~8% forecast | Competing engines and superior conventional post-fight package | Faster engine density, Pod/Survival network, protected conversion | Police only actual wins; count their silence/tutor density before choosing a window | A conventional list finds Oracle/Consult or a tutor chain faster after the first fight |
| Godo/K'rrik/Rakdos and other nonblue turbo | Low individually, meaningful tail | Early all-in attempt | Mindbreak, Force/Pact, Subtlety where applicable, grave interaction, Ranger-Captain | Blue seats should spend, but seat order may make Jaia the only legal backstop | Keeping an engine-only hand because the table appears interactive |

### Role discipline

Creature Factory's intended sequence remains coherent:

1. establish one or two engines without appearing to volunteer as table police;
2. let visible threats force the players whose plans require interaction to spend it;
3. supply only the missing layer or final backstop;
4. profit from the exchange;
5. convert immediately after the first major fight.

The empirical amendment is step 5. Blue-stack presence correlated with **lower**, not higher, T&T performance. If Blue Farm stops Tayam, that is not permission to return to setup; it is the cue to assess whether the conversion window is open before Blue Farm untaps or rebuilds.

## 8. Current 98 versus successful comparison lists

### Version changes

Relative to META-005's subject snapshot, the live 98 has:

- added Green Sun's Zenith, Sink into Stupor, Talion and Tarnished Citadel;
- removed Birthing Ritual, Scalding Tarn, Spellseeker and Summoner's Pact.

The last three live changes were Mental Misstep over Birthing Ritual (September 5), Green Sun's Zenith over Summoner's Pact (September 8), and Talion over Spellseeker (September 9).

Directional interpretation:

- **Misstep over Ritual** increases early interaction and reduces a slow, structurally dependent engine. This aligns with the event's four-round/top-two-bye pressure.
- **GSZ over Pact** improves card economy and permanent development but loses instant-speed, zero-mana access. Which is better depends on whether the target is setup or an emergency conversion piece.
- **Talion over Spellseeker** adds an independent engine and metagame punishment but removes a deterministic tutor body. For this deck's stated role, the key test is not Talion's raw value; it is whether the deck can still convert promptly after the first stack fight.
- **Sink into Stupor** is especially relevant because it raises both land count flexibility and resolved-permanent coverage, the weakest shared interaction layer.

### Current global T&T cohort

The ten result-weighted, event-stratified global T&T designs overlap 71–81 cards with Creature Factory. The most common omissions from our list were:

| Card absent from Creature Factory | Top-10 T&T inclusion | What it represents |
|---|---:|---|
| Deadly Rollick | 8/10 | Free resolved-creature removal |
| High Fae Trickster | 8/10 | Flash deployment / timing compression |
| Tataru Taru | 8/10 | Current conventional shell infrastructure |
| Wan Shi Tong, Librarian | 8/10 | Current conventional value/conversion package |
| An Offer You Can't Refuse | 6/10 | Cheap stack density |
| Borne Upon a Wind | 6/10 | Post-fight flash conversion |
| Flash Photography | 6/10 | Timing and flash infrastructure |
| Orim's Chant | 6/10 | Proactive protection / turn denial |
| Voice of Victory | 6/10 | Protected conversion |

Creature Factory's distinctive cards remained rare in that cohort: Abhorrent Oculus and Birthing Pod each appeared in 1/10, Colossal Skyturtle and Talion in 0/10, and Formidable Speaker in 2/10. This does not invalidate the package. It identifies the cost: the list is spending slots on recursive creature-engine depth rather than the conventional shell's free removal, flash access and protected compact conversion.

The local T&T cohort is only four complete designs. Three of four used Oracle, Consultation, Tainted Pact, An Offer, Training Grounds and several newer conventional pieces absent from Creature Factory. Again, this is an architecture comparison rather than a recommendation to adopt Oracle.

## 9. Decklists to study before Saturday

### Local and directly relevant

- [Kinnan — Brice Quarton, 1st/40, September Arcanum](https://moxfield.com/decks/wra9JpKGSEqI1HXtjzglYQ)
- [Kinnan — Brandon Lee, 3rd/40](https://moxfield.com/decks/onSgAWEUmHS4vwOcOYi9rA)
- [Kinnan — Gemein Cho, 6th/40](https://moxfield.com/decks/DsByH8iavUSTjMkBZSOgyQ)
- [Blue Farm — Zach Gable, 2nd/40](https://moxfield.com/decks/b8RZsIyaK0y0Ju6j3UyJYg)
- [T&T — Ross Donaldson, 7th/40](https://moxfield.com/decks/3S05d3DUuEW_IjoBtlG5yQ)
- [T&T — Dakota Cline, 8th/40](https://moxfield.com/decks/AYB3Wun5aESqo54ErWjQLA)
- [T&Yoshi — Kenjamin, 4th/40](https://moxfield.com/decks/AdDY88ZnGUyxfidYb4FSmA)
- [Godo — Jordan Larson, 5th/40](https://moxfield.com/decks/48Q0ZRbjJkSM8gKSDNJSiQ)
- [Kefka — Ryan Osoy, 9th/40](https://moxfield.com/decks/yDe7DnCgBEePcnVn-wZiqQ)
- [Sisay — 13th/40](https://moxfield.com/decks/V6yeAURsiH-gIFmt-SraQw)
- [Tayam — recent Arcanum list](https://moxfield.com/decks/bG2llrQpH0evNKPrpXx-VQ)
- [Crystal — recent Las Vegas list](https://moxfield.com/decks/-xafAR6oinGDIJum3cJLOw)

### Global winning/reference lists

- [Blue Farm — Sam Thompson, September 6 winner](https://moxfield.com/decks/kLkSKygG6kmpRqRe7K7ZOw)
- [Blue Farm — Eric V, 70-player winner](https://moxfield.com/decks/cnKgATiUsXOvlAKNaKM-Gg)
- [Kinnan — Jayden Davis, 56-player winner](https://moxfield.com/decks/KC--hk82dUScsdB-unOuHA)
- [T&T — Jacob Graham, event winner](https://moxfield.com/decks/9RygAVh9LnSBzdWGiu16QQ)
- [T&T/CHUDS — Eli, runner-up](https://moxfield.com/decks/jnWZz3B260qooVWvuJbBnQ)
- [Sisay — Janos, 65-player winner](https://moxfield.com/decks/yws7SDjUrUmhFrhEpszA)
- [Sisay — Gustavo, 123-player winner](https://moxfield.com/decks/pdmfAe-FknWWFkOqNOVmQA)
- [RogSi — Joseph, 97-player winner](https://moxfield.com/decks/g0h_xyKIgEKWy-u0cy6mJA)
- [Crystal — Robert R., 64-player winner](https://moxfield.com/decks/b2BMOOl01Ei8UcK3g9tgpA)
- [Tayam — Matthew Schaefer, 2nd/81](https://moxfield.com/decks/OtieAcFdHXiWphDhJSNSig)
- [Magda — Sebastian, 1st/53](https://moxfield.com/decks/iVX9xTqkEUuqFnwfFwijVw)

The machine-readable [decklist index](supporting/META-006-decklist-index.csv) contains the best five located lists per tracked commander and scope, with event, finish, record and source URL. The [supporting JSON](supporting/META-006-data.json) preserves every aggregate, exact cohort list and card set used here.

## 10. Tournament-day priorities

### Mulligan by pod, not by abstract power

- **Known commander-engine pod:** keep development plus access to a commander/resolved-permanent layer. A beautiful engine-only seven is fragile if no one can remove Kinnan, Sisay, Tayam or Magda after resolution.
- **Two blue-stack opponents:** prioritize a compact engine and a credible post-fight conversion path. Extra generic stack pieces can make Jaia the fourth person trading one-for-one while another blue deck wins the recovery race.
- **Nonblue turbo seat before Jaia:** keep a genuinely live early backstop; do not price in the two later blue players if priority order prevents them from acting at the necessary time.
- **Slow permanent-heavy pod:** a strong development hand is appropriate, but identify graveyard and artifact/enchantment responsibility before the first engine lands.

### Seat order

cEDH Stats' six-month seat data shows a pronounced decline from seat one to seat four (approximately 1.69, 1.38, 1.14 and 0.91 PPG). Seat order is therefore a material matchup variable, not flavor.[^stats]

- Early seat: advance the engine while preserving the ability to force later seats to expose their interaction.
- Late seat: value information and mana efficiency; be explicit about which earlier player must act first.
- Against a commander engine immediately before Jaia: Jaia may be the first player with full information and the last safe backstop. Plan mana accordingly.

### Communication script

Use layer-specific questions:

- “I can cover the protection spell; who can answer the commander if it resolves?”
- “Can you cover the activation? I can cover the payoff.”
- “If I spend here, who stops the next player?”
- “Does anyone have graveyard interaction specifically?”

This reveals coverage without announcing the exact card and reinforces the intended helper/backstop role.

### The conversion checkpoint

Immediately after the first major exchange, ask:

1. Which opponent gained cards or mana from that fight?
2. Which silence/protection effects were spent?
3. Can Creature Factory present a win or insurmountable engine before the best blue deck rebuilds?
4. If not, is deploying Talion/Thrasios/Pod actually recovery, or merely giving the table another full cycle?

That checkpoint is the most important behavioral implication of this report.

## 11. Confidence and limitations

- **High confidence:** event logistics; current 98/version/hash; global population leaders; latest Arizona event results and linked decklists.
- **Medium confidence:** broad local architectural mix; global conditional T&T pod results; event strategic-family forecast.
- **Low confidence:** exact event commander counts; Nevada-specific commander shares; individual local matchup PPG.
- Registration can change before Saturday, and the public event page did not expose player or commander identities.
- Missing Nevada lists are not missing at random; pilots or organizers that submit structured lists may differ from those that do not.
- Commander presence is not deck identity. Kinnan, T&T and Blue Farm lists contain meaningful internal variation.
- Conditional pod results are observational. Pilot skill, seat, event strength, list construction and co-opponents all confound them.
- First-nine answer coverage is a ceiling model, not a game-win model.

## Sources

[^event]: [TopDeck — MTG: cEDH “The Hobbit Collector Box” Tournament](https://topdeck.gg/event/september-cedh-event)
[^event-state]: [TopDeck public event-state record](https://firestore.googleapis.com/v1/projects/eminence-1b40b/databases/(default)/documents/otherEvents/september-cedh-event), checked 2026-09-09.
[^power9]: [Power 9 Games — event listing](https://www.power9games.com/catalog/event-upcoming_events/mtg_cedh_the_hobbit_collector_box_tournament/622257)
[^venue-prior]: [cEDH Stats — cEDH Four Duals 2026 Tournament](https://cedhstats.org/tournaments/cedh-four-duals-2026-tournament)
[^arcanum]: [cEDH Stats — September cEDH Tournament at Arcanum](https://cedhstats.org/tournaments/september-cedh-tournament-arcanum)
[^commanders]: [cEDH Stats — one-month commander statistics](https://cedhstats.org/commanders?min_players=16&period=1m)
[^stats]: [cEDH Stats — trends, performance and seat statistics](https://cedhstats.org/stats)
[^method]: [cEDH Stats — methodology and limitations](https://cedhstats.org/about)
