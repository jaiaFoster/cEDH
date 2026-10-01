# META-010 — October cEDH Tournament metagame and readiness packet

**Prepared:** 2026-10-01T00:59:31Z  
**Target:** [October cEDH Tournament — Arcanum Sanctorum, Tucson](https://topdeck.gg/event/october-cedh-tournament), Sunday **2026-10-04**  
**Subject:** [Creature Factory](https://moxfield.com/decks/gvyGvOx0g0uJ7ultPy-pbw), Thrasios/Tymna  
**Purpose:** evidence package and an independent deck-list readiness rating for handoff to the deck builder  
**No automated deck edit or simulation was performed.**

## Executive read

**Deck-list readiness: 7.5/10 — tournament-ready, with identifiable but non-fatal coverage gaps.**

Creature Factory is well aligned with the expected room on development, stack participation, protected turns, creature-commanders, and recovery. The latest actual change, `Flash Photography` replacing `Sowing Mycospawn`, improves flash-speed copying and post-fight conversion—the exact area earlier reports identified as lagging successful compact T&T lists. It also removes one of the deck's few broad artifact/enchantment interaction lines. The list is therefore better positioned to exploit long, spell-heavy fights but more dependent on `Boseiju`, bounce, theft, counters, or other players when a noncreature permanent has already resolved.

The highest-confidence tournament forecast is **Kinnan plus a broad creature-engine field**, not a room dominated by one deck. Kinnan won both fully observed Arcanum monthlies in August and September, putting **4/5 known Kinnan entries into their cuts**. T&T was the most registered named shell across those two events at **6/66 known lists** and put two into the September Top 10. The wider four-event, high-coverage Arizona comparison has **117 seats, 115 known lists**, and is diverse: T&T 11, Kinnan 8, Blue Farm 5, then several four- and three-entry archetypes. Expect many one-of decks rather than a clean tier-only field.

The list's remaining preparation risks are concentrated rather than general:

1. resolved noncreature engines and hate pieces;
2. graveyard-dependent engines, especially Tayam;
3. compact Blue Farm/Rograkh conversion after the table's first exchange;
4. the need to identify which opening hands actually answer a resolved Kinnan/Sisay/Magda commander rather than merely counter a spell.

This rating is a construction judgment, not an estimated tournament win rate. The deck builder should independently decide whether the coverage trade made by `Flash Photography` is acceptable; this packet does not designate a cut.

## 1. Event verification

The [TopDeck event page](https://topdeck.gg/event/october-cedh-tournament) and [organizer product page](https://arcanumsanctorum.com/products/cedh-october-tournament) agree on the core logistics:

- Venue: The Arcanum Sanctorum, **3994 North Oracle Road, Tucson, Arizona**.
- Date/start: **Sunday, October 4, 2026**; registration at **9:00 a.m.**, first round at **10:00 a.m.**
- Entry: **$40**, with the store product currently listed in stock.
- Rules: multiplayer EDH at **Competitive REL**, TopDeck MTRA/IPGA, 80-minute rounds, fully proxy legal within the organizer's stated proxy-quality rules.
- Decklists and registration are required through TopDeck.
- Rounds and cut size depend on attendance.

The public bracket does not expose a pre-event roster or submitted decklists while signed out, so there is **no verified registration count or pre-registration commander sample** in this report. Attendance planning can use the last two comparable monthlies—27 and 40 seats—but **27–40 is an anchor, not a forecast interval**.

There is a live source discrepancy in first-place prizing: TopDeck says **Confetti Foil Rhystic Study**, while the organizer store says **Dwarvish non-foil Mox Amber**. Confirm with the organizer if prize identity matters; it does not affect the metagame analysis.

## 2. Canonical Creature Factory snapshot

The repository's [canonical current pointer](https://github.com/jaiaFoster/cEDH/blob/claude/cedh-simulation-research-k5afxg/data/deck_sources/moxfield/tymna-thrasios/current.json) was read before the tournament data:

- Moxfield version: **5**
- Moxfield `updated_at`: **2026-09-17T19:55:17.423Z**
- Repository retrieval time: **2026-09-17T21:25:11.752303Z**
- Content hash: **`ec14a002da5d11503a849f03fc673a13f45696b38cc6fb47f620afd46569341a`**
- Construction: **98 mainboard + Thrasios/Tymna**

The stored pointer is **13 days old** at report preparation. The research branch has fresh TopDeck data through September 30, but this run could not independently establish a post-September-17 successful Moxfield workflow check. The deck itself may be unchanged, but the correct health label is **snapshot usable; freshness unverified**. The deck builder should recheck the Moxfield page or sync workflow before locking the submitted list.

Relative to the preceding stored version, the exact one-card change is:

- **In:** `Flash Photography`
- **Out:** `Sowing Mycospawn`

`Flash Photography` can be cast as though it had flash when it targets a permanent you control, creates a token copy, and has flashback. In this list it supports flash-speed engine duplication, redundancy, and post-fight conversion. Removing `Sowing Mycospawn` reduces direct artifact/enchantment disruption and land-based utility. That is the central current-list tradeoff.

## 3. Methodology and denominators

### Rolling window

- Strict rolling 30 calendar dates: **2026-09-02 00:00:00 UTC through 2026-10-01 23:59:59 UTC**.
- The archive was current through its **2026-09-30T22:36:19Z** TopDeck sync commit (`60c9d6e`). No October 1 completed result existed at preparation time.

### Eligibility

- Arizona/Nevada: Magic: The Gathering, EDH, explicitly labeled cEDH/competitive Commander, confirmed event structure/location, excluding casual, precon, test, practice, low-bracket, and side-event records.
- Global verification cohort: same exclusions, explicit cEDH/competitive label, and at least 16 seats.
- The [cEDH Stats](https://cedhstats.org/stats) analytical layer is used for the broader current picture; repository TopDeck snapshots provide the reproducible custom counts below.

### Data-health rules

- **Seats/entries are not decklists.** Commander shares use known structured lists as their denominator.
- **Entries are not unique pilots.** A pilot can enter several events.
- **Swiss wins are not cut qualification.** `top_cut` records cut membership; cut sizes vary.
- **Raw conversion is not causal performance.** It is confounded by pilot strength, event size, seat, pod composition, list submission, and cut policy.
- **Known lists are not a random sample.** Do not treat known-list shares as unbiased room odds.
- **Local and global evidence remain separate.** Global scale does not replace the venue's repeated pilots and local deck preferences.

## 4. Arizona — strict rolling 30 days

Seven confirmed cEDH events produced **166 seats**, **78 structured lists/known commanders (47.0% coverage)**, and **96 unique pilot IDs/names**. There were 18 cut seats overall and 14 known-commanders in cuts. The all-seat cut baseline was **18/166 = 10.8%**; the known-list cut fraction was **14/78 = 17.9%**.

| Date | Event | Seats | Lists | Cut | Known winner |
|---|---|---:|---:|---:|---|
| Sep 4 | [Weekly cEDH at Arcanum](https://topdeck.gg/event/weekly-cedh-at-arcanum-4) | 19 | 5 | none | unknown |
| Sep 6 | [September cEDH Tournament at Arcanum](https://topdeck.gg/event/september-cedh-tournament-arcanum) | 40 | 39 | Top 10 | Kinnan |
| Sep 11 | [Weekly cEDH at Arcanum](https://topdeck.gg/event/weekly-cedh-arcanum) | 18 | 2 | none | unknown |
| Sep 18 | [Thursday Night cEDH at Arcanum](https://topdeck.gg/event/thursday-night-cedh-arcanum) | 19 | 3 | none | Blue Farm |
| Sep 20 | [AZMS Qualifier #7](https://topdeck.gg/event/azms-cedh-qualifier-7) | 20 | 20 | Top 4 | Jhoira |
| Sep 20 | [Flagstaff Win a Dwarven Mox Amber](https://topdeck.gg/event/september-cedh-win-a-dwarven-mox-amber) | 32 | 6 | Top 4 | unknown |
| Sep 25 | [cEDH at Arcanum](https://topdeck.gg/event/cedh-arcanum) | 18 | 3 | none | unknown |

| Deck | Entries / 78 | Known share | Cuts | Raw conversion | Known wins |
|---|---:|---:|---:|---:|---:|
| Kinnan | 7 | 9.0% | 4 | 57.1% | 1 |
| Blue Farm | 6 | 7.7% | 1 | 16.7% | 1 |
| T&T | 6 | 7.7% | 2 | 33.3% | 0 |
| Zirda | 4 | 5.1% | 0 | 0% | 0 |
| Etali / Glarb / Ob Nixilis / Raph & Mikey | 3 each | 3.8% each | 0 | 0% | 0 |
| Rograkh/Silas | 3 | 3.8% | 0 | 0% | 0 |
| Rograkh/Thrasios | 3 | 3.8% | 1 | 33.3% | 0 |
| Tayam | 3 | 3.8% | 0 | 0% | 0 |
| Sisay | 2 | 2.6% | 0 | 0% | 0 |
| Magda | 1 | 1.3% | 0 | 0% | 0 |

### Change from META-009

The preceding rolling report had 7 events, 166 seats, and 80 lists. The current window remains **7 events/166 seats**, but structured coverage is **78 rather than 80** after the August 28 weekly rolled out, September 25 rolled in, and archive corrections/backfill changed two list records. Coverage moved **48.2% → 47.0% (-1.2 percentage points)**. There is no new high-coverage Arizona major after AZMS #7; the September 25 weekly has only 3/18 lists. **Activity confidence: high. Commander-share confidence: medium-low.**

## 5. The most relevant past local tournaments

The cleanest forecast set is the two fully observed Arcanum monthlies plus AZMS #6 and #7: **117 seats, 115 known lists (98.3% coverage), 73 unique pilots, and 22 known cut seats**.

| Date | Event | Seats/lists | Cut | Winner |
|---|---|---:|---:|---|
| Aug 2 | Arcanum August monthly | 27/27 | Top 4 | Kinnan |
| Aug 16 | AZMS Qualifier #6 | 30/29 | Top 4 | Rograkh/Thrasios |
| Sep 6 | Arcanum September monthly | 40/39 | Top 10 | Kinnan |
| Sep 20 | AZMS Qualifier #7 | 20/20 | Top 4 | Jhoira |

Across those 115 known lists: T&T **11 (9.6%, 2 cuts)**, Kinnan **8 (7.0%, 6 cuts, 2 wins)**, Blue Farm **5 (4.3%, 1 cut)**, Ob Nixilis/Ral/Raph & Mikey/Tayam/Zirda **4 each**, and Glarb/Godo/Rograkh-Thrasios/Sisay/Thrasios-Yoshimaru **3 each**. Rograkh/Thrasios had two cuts and one win; Godo had two cuts. The remaining field was a long tail of mostly one- and two-entry decks.

The venue-specific signal is sharper. The two comparable Arcanum monthlies had **67 seats/66 lists**: T&T **6/66** with two cuts; Kinnan **5/66** with four cuts and **both wins**; Blue Farm **2/66** with one cut. This does not prove a Kinnan matchup advantage, but it makes Kinnan the highest-priority local commander to recognize and contain.

Public adjacent lists for the deck builder:

- [Brice Quarton's September-winning Kinnan](https://moxfield.com/decks/wra9JpKGSEqI1HXtjzglYQ)
- [Dakota Cline's September 8th-place T&T](https://moxfield.com/decks/AYB3Wun5aESqo54ErWjQLA)
- [Ross Donaldson's September 7th-place T&T](https://moxfield.com/decks/3S05d3DUuEW_IjoBtlG5yQ)
- [AZMS #7 winning Jhoira](https://topdeck.gg/deck/azms-cedh-qualifier-7/FDo9IZmyJHfY6ZsPYfEB7wX8Pbz2)

## 6. Southern Nevada — kept separate

Seven confirmed events produced **175 seats**, **28 structured lists (16.0% coverage)**, **78 unique pilots**, and 32 cut seats. Only 11 cut entries have known commanders. Activity is well observed; commander prevalence is not.

Known counts: Crystal **7/28** (3 cuts), Blue Farm **4/28** (2 cuts, 1 win), Kinnan **3/28** (2 cuts), T&T **2/28** (1 cut), and one each of Tayam, Tivit, Etali, and several singletons. The September 12 North Las Vegas event remains the only strong list-level record: 22 seats/21 lists, Blue Farm win, Kinnan second and tenth, Crystal third/seventh, another Blue Farm fourth, T&T sixth.

Versus META-009, Nevada is **+1 event, +22 seats, +3 lists**, while coverage moved **16.3% → 16.0%**. Do not blend these counts into Arizona probabilities.

## 7. Global — strict rolling 30-day verification cohort

The reproducible archive cohort contains **218 events, 5,999 seats, 3,502 structured lists/known commanders (58.4% coverage), 2,497 unknown commanders, and 4,237 unique pilots**. There were 1,068 cut seats overall (**17.8% of seats**) and 856 known-list cut entries (**24.4% of known lists**).

| Deck | Entries / 3,502 | Known share | Unique pilots | Cuts | Raw conversion | Wins |
|---|---:|---:|---:|---:|---:|---:|
| Kinnan | 308 | 8.80% | 260 | 91 | 29.5% | 16 |
| Blue Farm | 259 | 7.40% | 217 | 91 | 35.1% | 17 |
| Rograkh/Thrasios | 206 | 5.88% | 174 | 64 | 31.1% | 8 |
| Rograkh/Silas | 177 | 5.05% | 158 | 40 | 22.6% | 6 |
| Sisay | 166 | 4.74% | 145 | 55 | 33.1% | 14 |
| T&T | 104 | 2.97% | 94 | 25 | 24.0% | 2 |
| Vivi | 87 | 2.48% | 77 | 28 | 32.2% | 2 |
| Ral | 82 | 2.34% | 79 | 14 | 17.1% | 2 |
| Thrasios/Yoshimaru | 82 | 2.34% | 73 | 17 | 20.7% | 0 |
| Tayam | 81 | 2.31% | 68 | 10 | 12.3% | 1 |
| Magda | 77 | 2.20% | 72 | 23 | 29.9% | 3 |

The [cEDH Stats 1-month T&T page](https://cedhstats.org/commanders/thrasios-tymna?elite=0&min_players=16&period=1m) uses a broader analytical cohort and currently reports **203 entries, 2.8% share, 1.18 average PPG, 25.2% Swiss win rate, and 25.0% top-cut win rate**. Its [Blue Farm page](https://cedhstats.org/commanders/kraum-tymna?elite=0&min_players=16&period=1m) reports **534 entries, 7.0% share, 1.41 PPG, 31.9% Swiss win rate, and 28.5% top-cut win rate**. Those denominators differ from the conservative archive cohort and must not be merged.

### Week-over-week movement

Against META-009, the global archive cohort moved **232 → 218 events**, **6,549 → 5,999 seats**, **3,897 → 3,502 known lists**, and **59.5% → 58.4% coverage**. This is mainly rolling-window turnover and archive correction, not a claim that worldwide play collapsed in one week.

Named movement: Kinnan **325 → 308**, Blue Farm **296 → 259**, Rograkh/Thrasios **205 → 206**, Rograkh/Silas **195 → 177**, Sisay **177 → 166**, T&T **117 → 104**, Tayam **93 → 81**, Magda **91 → 77**. Rograkh/Thrasios is the only major named shell here whose entry count held flat/up while the cohort shrank. T&T cuts increased **21 → 25** despite fewer entries; that is encouraging association, not proof of a metagame edge.

## 8. October room forecast

This is a weighted inference from venue monthlies first, complete Arizona majors second, and global priors third. It is not a roster prediction.

| Expected pressure | Forecast | Why |
|---|---|---|
| Kinnan | **High** | Won both recent Arcanum monthlies; 4/5 venue entries cut; global #1 by entries |
| T&T mirrors | **High** | Largest named shell across the four high-coverage local events; 6/66 at venue monthlies |
| Blue Farm | **Medium-high** | Lower local count but strong global share/results; won a Tucson weekly and North Las Vegas major |
| Rograkh/Thrasios | **Medium-high** | AZMS #6 winner; 5.88% global known share and stable/up entry count |
| Rograkh/Silas | **Medium** | 5.05% global share; local registrations exist but are pilot-concentrated |
| Sisay / Tayam | **Medium** | Three/four entries in the high-coverage local cohort; structurally demanding for this list |
| Zirda / Raph & Mikey / Ob Nixilis / Ral | **Medium** | Repeated local presence and high local diversity |
| Magda | **Low-medium locally, material globally** | Only 1/115 in the high-coverage local set, but 77 global entries and 29.9% raw cut conversion |
| Novel one-offs | **High as a category** | More than half of the high-coverage local field sits outside the leading named shells |

Under a purely illustrative independent-draw model from the 115 known high-coverage local lists, a three-opponent pod would contain at least one T&T about **26%**, Kinnan **20%**, Blue Farm **12.5%**, and any of Tayam/Sisay/Rograkh-Thrasios/Rograkh-Silas/Magda about **30%**. Repeat pilots, pairings, deck changes, and event selection violate independence; use these only for scenario weighting.

## 9. Creature Factory versus the forecast

### Current construction strengths

- **Development/engines:** dense creature mana plus Kinnan, Badgermole Cub, Enduring Vitality, Delney, Tymna, Thrasios, Remora, Rhystic, Lotho, Cabbage, and Tithe.
- **Tutor access:** Pod, Survival, Chord, Green Sun's Zenith, Finale, Neoform, Eldritch Evolution, Demonic/Vampiric/Imperial/Enlightened Tutor.
- **Stack backstop:** Force suite, Fierce, Flare, Flusterstorm, Swan Song, Pact, Mindbreak, Mental Misstep, Commandeer, Misdirection, Subtlety.
- **Protected turns:** Silence, Grand Abolisher, Ranger-Captain, Voice of Victory, Teferi, Veil.
- **Resolved creature agency:** Gilded Drake, Volatile Stormdrake, Swift Reconfiguration, Subtlety, Otawara, and tutor access to several of those effects.
- **Resilience/overlap:** deterministic Devoted Druid lines, Brewmaster graveyard conversion, Cradle/Oboro/Talon development, and commanders that remain useful without a compact Oracle package.

### Remaining gaps

- **Noncreature permanent independence:** thinner after `Sowing Mycospawn` left. Boseiju and bounce remain important, but a resolved artifact/enchantment engine can force cooperation.
- **Graveyard independence:** Endurance plus Deathrite Shaman is still a narrow dedicated layer.
- **Compactness:** there is no Oracle/Consultation/Pact package; the deck often needs board material or a multi-step tutor sequence.
- **Post-fight speed:** `Flash Photography`, Emergence Zone, and Teferi improve this axis, but Blue Farm and Rograkh shells remain structurally more compact.
- **Board dependence:** sweepers, Cursed Totem-style effects, and multiple resolved engines can disable more of the deck than its counter count suggests.

### Matchup-readiness matrix

| Opponent cluster | Readiness | Construction read |
|---|---:|---|
| T&T / slower blue midrange | **8.0/10** | Strong engine and stack parity; current list is less compact than many Oracle/flash T&T lists |
| Blue Farm | **7.5/10** | Good resource capture and stack agency; Blue Farm usually wins the post-fight conversion race if both decks are depleted |
| Kinnan | **7.0/10** | Two Drake effects, Swift, Subtlety and counters are real; resolved/recast commander plus activation remains the main local stress test |
| Rograkh/Thrasios and Rograkh/Silas | **7.0/10** | Enough free interaction to participate; early speed and compact conversion punish engine-only hands |
| Sisay / Magda | **6.5/10** | Theft is meaningful, but commander recast and noncreature support pieces mean one answer is not full containment |
| Tayam / recursion engines | **6.0/10** | The deck's graveyard and resolved-permanent gaps overlap here |
| Stax / novel permanent engines | **6.5/10** | Broad tutor and bounce options help, but the lost Mycospawn slot is noticeable |

## 10. Readiness scorecard

Scores are ordinal deck-construction judgments against a serious cEDH tournament field, not simulated win percentages.

| Axis | Weight | Score / 10 | Evidence |
|---|---:|---:|---|
| Early development | 15% | 8.5 | Dense dorks/fast mana, Kinnan/Cub/Vitality, Cradle |
| Engine quality and recovery | 15% | 8.5 | Multiple independent draw/value engines and commander outlets |
| Stack agency | 15% | 8.5 | Deep free/cheap counter and redirect suite |
| Protected-attempt quality | 10% | 8.0 | Six major silence/turn-control effects |
| Resolved creature agency | 10% | 7.5 | Drake pair, Swift, Subtlety, Otawara, tutors |
| Noncreature permanent agency | 10% | 5.5 | Boseiju/bounce/conditional lines; Mycospawn removed |
| Graveyard agency | 5% | 5.0 | Endurance and Deathrite only |
| Conversion speed/compactness | 10% | 6.5 | Deterministic lines, but board-mediated and no Oracle package |
| Post-fight/flash conversion | 10% | 7.0 | Improved by Flash Photography; still below compact Blue Farm/T&T |
| **Weighted readiness** | **100%** | **7.5/10** | Tournament-ready; concentrated gaps remain |

### Rating confidence

- **High:** exact stored 98, interaction packages, local event sizes/cuts, high-coverage major commander counts.
- **Medium:** matchup-direction assessment, event archetype bands, readiness subscores.
- **Low:** exact October attendance/roster, causal benefit of any single card, precise win-rate prediction for this exact 98.

## 11. Deck-builder handoff

The deck builder should independently answer these questions before changing anything:

1. Does `Flash Photography` create enough immediate conversion or redundancy to justify losing `Sowing Mycospawn`'s noncreature-permanent role in a Kinnan/varied-engine room?
2. Which opening hands can answer a **resolved** Kinnan, Sisay, Magda, or Tayam rather than only their cast/protection stack?
3. Is Endurance plus Deathrite enough for Tayam/recursion, given the local Tayam repeat pilot and broader field diversity?
4. After the first counter war, how often does the current 98 have a tutorable same-turn win rather than another development step?
5. If a slot changes, which measured gap is being bought—noncreature permanent agency, graveyard agency, or conversion compactness—and what exact current strength is being sold?

No list change is required by the data alone. The rating supports entering the tournament with this shell; it does **not** claim the list is maximally tuned or that a specific swap has a measured win-rate gain.

## Source index

- [October event — TopDeck](https://topdeck.gg/event/october-cedh-tournament)
- [October event — organizer product page](https://arcanumsanctorum.com/products/cedh-october-tournament)
- [October public bracket](https://topdeck.gg/bracket/october-cedh-tournament)
- [cEDH Stats current dashboard](https://cedhstats.org/stats)
- [cEDH Stats T&T — 1 month](https://cedhstats.org/commanders/thrasios-tymna?elite=0&min_players=16&period=1m)
- [cEDH Stats Blue Farm — 1 month](https://cedhstats.org/commanders/kraum-tymna?elite=0&min_players=16&period=1m)
- [Repository TopDeck archive](https://github.com/jaiaFoster/cEDH/tree/claude/cedh-simulation-research-k5afxg/data/tournament_snapshots/topdeck/normalized)
- [Canonical Creature Factory snapshot](https://github.com/jaiaFoster/cEDH/blob/claude/cedh-simulation-research-k5afxg/data/deck_sources/moxfield/tymna-thrasios/current.json)
- [Supporting data](./supporting/META-010-data.json)
- [Public decklist index](./supporting/META-010-decklist-index.csv)

