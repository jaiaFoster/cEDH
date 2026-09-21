# META-009 — Weekly cEDH metagame data update — 2026-09-21

Prepared 2026-09-21T16:32:30Z. Descriptive data handoff only: no deck edits, simulations, candidate-card tests, construction recommendations, or tuning verdicts.

## Subject snapshot and workflow health

The identified subject is [Creature Factory](https://moxfield.com/decks/gvyGvOx0g0uJ7ultPy-pbw), read first from the repository's [canonical pointer](https://github.com/jaiaFoster/cEDH/blob/claude/cedh-simulation-research-k5afxg/data/deck_sources/moxfield/tymna-thrasios/current.json):

- Moxfield version: **5**
- Moxfield `updated_at`: **2026-09-17T19:55:17.423Z**
- Repository retrieval time: **2026-09-17T21:25:11.752303Z**
- Content hash: **`ec14a002da5d11503a849f03fc673a13f45696b38cc6fb47f620afd46569341a`**
- Construction count: **98 mainboard + Thrasios/Tymna**

The pointer is four days old as a stored snapshot, but it is **not evidence of a failed sync**. The scheduled Moxfield workflow [succeeded at 2026-09-21 12:53 UTC](https://github.com/jaiaFoster/cEDH/actions/runs/35602164071) against branch head `22a24de`; it created no deck commit because the content was unchanged. The previous scheduled run also [succeeded at 2026-09-21 05:00 UTC](https://github.com/jaiaFoster/cEDH/actions/runs/35562912040). Thus the content hash is current as of the latest successful check, although its immutable retrieval timestamp remains September 17. **Workflow confidence: high.**

## Windows and eligibility

- Strict rolling window: **2026-08-23T00:00:00Z through 2026-09-21T23:59:59Z** (30 UTC calendar dates; local Arizona events are included by their recorded event start).
- Arizona and Nevada: TopDeck records whose event metadata identifies the state, game as Magic: The Gathering, format as EDH, and whose organizer label and event structure establish cEDH. The Surprise precon event is excluded.
- Global verification cohort: archived TopDeck records in the same date window with game `Magic: The Gathering`, format `EDH`, at least 16 seats, an explicit `cEDH` or `competitive EDH/Commander` label, and none of `test`, `casual`, `precon`, `bracket`, `practice`, or `side event` in the name. The cEDH label is not used alone: the game/format, field, standings, and event metadata must also be present. This conservative cohort omits some genuine cEDH events whose names are not explicit.
- Archive freshness: repository head **`36e54c0`**, TopDeck sync committed **2026-09-21T13:18:47Z**. Source: [TopDeck normalized archive](https://github.com/jaiaFoster/cEDH/tree/claude/cedh-simulation-research-k5afxg/data/tournament_snapshots/topdeck/normalized).

## Arizona — strict rolling 30 days

Seven confirmed cEDH events produced **166 seats/entries**, **80 submitted and structured decklists (48.2% coverage)**, and **99 unique pilot IDs/names**. There are **80 known commander registrations and 86 unknown**. Repeat pilots count once per event in commander entries but once in the unique-pilot total. Three events used a formal cut: 18 cut seats in all, of which 14 had known commanders. The raw cut baseline is **18/166 = 10.8% of all seats**; within known commanders it is **14/80 = 17.5%**. These denominators are not interchangeable.

| Date | Event | Seats | Structured lists | Cut | Winner / data note |
|---|---|---:|---:|---:|---|
| Aug 28 | [Weekly cEDH at Arcanum](https://topdeck.gg/event/weekly-cedh-at-arcanum-3) | 18 | 5 | none | winner commander unknown |
| Sep 4 | [Weekly cEDH at Arcanum](https://topdeck.gg/event/weekly-cedh-at-arcanum-4) | 19 | 5 | none | winner commander unknown |
| Sep 6 | [September cEDH Tournament at Arcanum](https://cedhstats.org/tournaments/september-cedh-tournament-arcanum) | 40 | 39 | Top 10 | **Kinnan** won; Blue Farm 2nd; another Kinnan 3rd; T&T 7th and 8th |
| Sep 11 | [Weekly cEDH at Arcanum](https://topdeck.gg/event/weekly-cedh-arcanum) | 18 | 2 | none | winner commander unknown |
| Sep 18 | [Thursday Night cEDH at Arcanum](https://topdeck.gg/event/thursday-night-cedh-arcanum) | 19 | 3 | none | known winner: **Blue Farm** |
| Sep 20 | [AZMS cEDH Qualifier #7](https://topdeck.gg/event/azms-cedh-qualifier-7) | 20 | 20 | Top 4 | **Jhoira, Ageless Innovator** won; Godo 2nd, Rograkh/Thrasios 3rd, Kinnan 4th |
| Sep 20 | [Flagstaff Win a Dwarven Mox Amber](https://topdeck.gg/event/september-cedh-win-a-dwarven-mox-amber) | 32 | 6 | Top 4 | all four cut commanders and winner commander unknown |

### Known-commander counts

Shares below use **80 known commanders**, not 166 seats. Raw conversion uses the deck's known entries. The 17.5% known-commander baseline is included only as context; list submission and event cut size are highly non-random.

| Deck | Entries / 80 | Known share | Cut | Raw conversion | Known wins |
|---|---:|---:|---:|---:|---:|
| Kinnan | 6 | 7.5% | 4 | 66.7% | 1 |
| T&T | 6 | 7.5% | 2 | 33.3% | 0 |
| Blue Farm | 6 | 7.5% | 1 | 16.7% | 1 |
| Tayam | 4 | 5.0% | 0 | 0% | 0 |
| Zirda | 4 | 5.0% | 0 | 0% | 0 |
| Rograkh/Thrasios | 3 | 3.8% | 1 | 33.3% | 0 |
| Rograkh/Silas | 3 | 3.8% | 0 | 0% | 0 |
| Raph & Mikey | 3 | 3.8% | 0 | 0% | 0 |
| Ob Nixilis | 3 | 3.8% | 0 | 0% | 0 |
| Glarb | 3 | 3.8% | 0 | 0% | 0 |
| Maralen | 3 | 3.8% | 0 | 0% | 0 |
| Etali | 3 | 3.8% | 0 | 0% | 0 |
| Sisay | 2 | 2.5% | 0 | 0% | 0 |
| Godo | 2 | 2.5% | 2 | 100% | 0 |

AZMS #7 is the highest-confidence new local result because it has **20/20 structured lists**. Its field had two Kinnan, two T&T, two Zirda, two Ob Nixilis, and one each of Rograkh/Thrasios, Jhoira, Godo, Hulk, Raph & Mikey, Zhulodok, Helga, Dargo/Silas, Glarb, Krenko, Ishai/Rograkh, and Atraxa. The [winning Jhoira list](https://topdeck.gg/deck/azms-cedh-qualifier-7/FDo9IZmyJHfY6ZsPYfEB7wX8Pbz2) is public.

### Change from META-008

The preceding report's strict Arizona window had **5 events, 117 seats, and 58 known/structured lists**. The new window has **7 events, 166 seats, and 80 known/structured lists**: **+2 events, +49 seats, +22 usable lists**, while coverage moved from 49.6% to **48.2% (-1.4 percentage points)**. The August 21 Tucson weekly rolled out; September 18 Tucson, AZMS #7, and Flagstaff rolled in. The main new result is Jhoira's fully observed AZMS #7 win. Flagstaff added 32 seats but only six lists and no identified Top 4 commander, so it increases activity evidence more than commander-share evidence. **Arizona field/count confidence: high; commander-share confidence: medium-low; individual conversion confidence: low.**

## Southern Nevada — separate rolling window

Six confirmed events produced **153 seats/entries**, **25 structured lists (16.3% coverage)**, and **71 unique pilot IDs/names**. There are 25 known commander registrations and 128 unknown. Formal cuts account for 32 seats overall; 10 cut entries have known commanders. The all-seat cut baseline is **32/153 = 20.9%**, while the known-list cut fraction is **10/25 = 40.0%** because 21 of the 25 known lists come from the September 12 event with a Top 10.

| Date | Event | Seats | Structured lists | Cut |
|---|---|---:|---:|---:|
| Aug 26 | [Stomping Grounds Weekly](https://topdeck.gg/event/stomping-grounds-weekly-cedh-196) | 21 | 3 | none |
| Aug 28 | [Natural Twenty's Weekly](https://topdeck.gg/event/natural-twentys-weekly-cedh-948) | 23 | 0 | Top 4 |
| Sep 4 | [Natural Twenty's Weekly](https://topdeck.gg/event/natural-twentys-weekly-cedh-529) | 32 | 0 | Top 10 |
| Sep 11 | [Natural Twenty's Weekly](https://topdeck.gg/event/natural-twentys-weekly-cedh-204) | 28 | 0 | Top 4 |
| Sep 12 | [Hobbit Collector Box, North Las Vegas](https://cedhstats.org/tournaments/september-cedh-event) | 22 | 21 | Top 10 |
| Sep 18 | [Natural Twenty's Weekly](https://topdeck.gg/event/natural-twentys-weekly-cedh-480) | 27 | 1 | Top 4 |

Known counts are Crystal **4/25** (2 cuts), Blue Farm **4/25** (2 cuts, 1 win), Kinnan **2/25** (2 cuts), and T&T **2/25** (1 cut); Tayam and Sisay each appear once. Rograkh/Thrasios, Rograkh/Silas, and Magda have no known registrations in this low-coverage sample. The September 12 event remains the only strong list-level evidence: Blue Farm won, Kinnan finished 2nd and 10th, Crystal 3rd and 7th, another Blue Farm 4th, and T&T 6th. The September 18 weekly adds 27 seats but only one structured list. **Activity confidence: high; commander prevalence confidence: low.**

## Global — strict rolling 30-day verification cohort

The reproducible TopDeck cohort contains **232 events, 6,549 seats/entries, 3,897 submitted and structured lists/known commanders (59.5% coverage), 2,652 unknown commanders, and 4,603 unique pilots**. It records **1,143 cut seats** overall (17.5% of seats), of which **934** have known commanders (24.0% of known lists), and 232 event-winner flags. Entries are event registrations; pilots can enter multiple events.

The [cEDH Stats analytical layer](https://cedhstats.org/stats) independently describes current TopDeck data and identifies recent movement such as Zhulodok, Derevi, and Tivit gaining result momentum, while Hashaton and Urza show registration breakouts. Its commander pages use a broader event-selection model than this explicit-name verification cohort. For example, its current 1-month pages report [T&T](https://cedhstats.org/commanders/thrasios-tymna?elite=0&min_players=16&period=1m) at 234 entries, 3.7% share, and 1.27 PPG, and [Blue Farm](https://cedhstats.org/commanders/kraum-tymna?elite=0&min_players=16&period=1m) at 517 entries, 7.4% share, and 1.40 PPG. Those figures should not be mixed with the archive denominators below.

| Deck | Entries / 3,897 | Known share | Unique pilots | Cut | Raw conversion | Wins |
|---|---:|---:|---:|---:|---:|---:|
| Kinnan | 325 | 8.34% | 279 | 101 | 31.1% | 20 |
| Blue Farm | 296 | 7.60% | 246 | 96 | 32.4% | 18 |
| Rograkh/Thrasios | 205 | 5.26% | 173 | 63 | 30.7% | 8 |
| Rograkh/Silas | 195 | 5.00% | 167 | 49 | 25.1% | 6 |
| Sisay | 177 | 4.54% | 158 | 56 | 31.6% | 14 |
| T&T | 117 | 3.00% | 106 | 21 | 17.9% | 2 |
| Dargo/Tymna | 101 | 2.59% | 88 | 23 | 22.8% | 2 |
| Vivi | 98 | 2.51% | 86 | 24 | 24.5% | 2 |
| Tayam | 93 | 2.39% | 71 | 15 | 16.1% | 2 |
| Magda | 91 | 2.34% | 83 | 31 | 34.1% | 3 |
| Ral | 90 | 2.31% | 85 | 19 | 21.1% | 3 |
| Thrasios/Yoshimaru | 70 | 1.80% | 59 | 18 | 25.7% | 0 |
| Nick Fury | 67 | 1.72% | 56 | 24 | 35.8% | 2 |
| Crystal | 64 | 1.64% | 58 | 20 | 31.3% | 4 |

Raw conversion reflects unlike cut sizes and non-random list submission. It is descriptive association, not an estimated causal deck effect or a matchup win rate.

### Week-over-week movement against published META-008

META-008 reported 215 events, 6,595 seats, and 3,986 known lists (60.4%). The current rolling cohort is **+17 events, -46 seats, -89 known lists, and -0.9 percentage points coverage**. These changes combine the rolling-window shift with subsequent archive backfill/corrections.

Among named decks: Kinnan moved **337→325** entries and 8.5%→8.34% known share; Blue Farm **327→296** and 8.2%→7.60%; Rograkh/Silas **212→195** and 5.3%→5.00%; Rograkh/Thrasios **197→205** and 4.9%→5.26%; Sisay **170→177** and 4.3%→4.54%; T&T **134→117** and 3.4%→3.00%; Tayam **87→93** and 2.2%→2.39%. The clearest positive count/cut movement is Rograkh/Thrasios (**52→63 cuts**) and Sisay (**44→56 cuts**); the clearest negative count movement is Blue Farm, while it still has 18 wins and 32.4% raw conversion in the current cohort.

## Functional context and public comparison lists

- **T&T:** 117 known entries, 21 cuts, two wins. Its largest win in-window was Jorman Antigua's 1st place in a 52-seat event; [public winning list](https://topdeck.gg/deck/cedh-monthly-hobbit-collector-box/HqOhjsyNE6P6iV4QsbWeejO0iXU2). T&T also put two lists into Tucson's Top 10 but neither AZMS #7 T&T list made Top 4.
- **Blue Farm:** 296 entries, 96 cuts, 18 wins. It won a 70-seat PDX event; [Eric V's public winning list](https://topdeck.gg/deck/guardian-games-cedh-monthly-pdx/ihW7aupIQ5TV7qfJl9vJPHJjQXi1). It also won the North Las Vegas major and the September 18 Tucson weekly.
- **Kinnan:** leads entries (325) and wins (20) in the verification cohort, with 101 cuts. It won the 156-seat UK Open; [Ryley Evans's public winning list](https://topdeck.gg/deck/cedh-uk-open-benfest-iii/cM7QfCcVxvVhd6VgTRlAVOpyLhv1), and won Tucson on September 6.
- **Rograkh/Thrasios:** 205 entries, 63 cuts, eight wins; count, share, and cuts increased from META-008. It made the AZMS #7 final and finished third.
- **Rograkh/Silas:** 195 entries, 49 cuts, six wins; count/share fell modestly from META-008 while cuts were essentially flat.
- **Sisay:** 177 entries, 56 cuts, 14 wins. It won the 123-seat Nacional de CEDH; [Gustavo's public winning list](https://topdeck.gg/deck/nacional-de-cedh-100k-1/Dq0VcdTa8aNUZvy7EBsC7QLbio42).
- **Tayam:** 93 entries, 15 cuts, two wins. Its 16.1% raw conversion is below the cohort's 24.0% known-list cut fraction, but cEDH Stats also labels it a recent result-momentum decliner; neither source controls for pilot, field, or cut-size mix.
- **Magda:** 91 entries, 31 cuts, three wins; 34.1% raw conversion. It won the 64-seat German Nationals Invitational; [David Schumacher's public winning list](https://topdeck.gg/deck/cedh-nationals-deutschland-invitational/VIhuNuODhtR3xoe5kf4nsoJPL9B3).
- **Other material decks:** Dargo/Tymna, Vivi, Ral, Thrasios/Yoshimaru, Nick Fury, and Crystal each account for 1.6%–2.6% of known lists. cEDH Stats' current trend layer separately flags Zhulodok, Derevi, and Tivit for improving points-per-pilot and Hashaton/Urza for registration growth; those signals are broader than the conservative archive cohort and do not imply local Arizona growth.

The comparison lists above are evidence of public, successful configurations. Their inclusion does not imply that Creature Factory should copy any card or package.

## Data health and unresolved gaps

- **Seats versus lists:** Arizona has 166 seats but only 80 lists; Nevada 153/25; global 6,549/3,897. Known-list shares are conditional on submission and are not unbiased field shares.
- **Known versus unknown commanders:** unknown seats remain 51.8% in Arizona, 83.7% in Nevada, and 40.5% globally. Flagstaff's entire Top 4 is unknown.
- **Swiss versus cut:** `top_cut` flags count cut qualification, not Swiss wins. Cut sizes vary from none to Top 4/10/16; raw conversion is therefore not directly comparable across events.
- **Entries versus pilots:** global 6,549 entries represent 4,603 unique pilots; repeated pilots/decks create correlated observations. Arizona has 99 unique pilots across 166 entries, Nevada 71 across 153.
- **Baseline:** the global all-seat cut rate is 17.5%, while the known-list cut fraction is 24.0%. The difference is partly missingness: submitted lists are more common at structured majors and among successful entries.
- **Wins:** an event can have a winner flag whose commander is unknown. Archetype win totals count only known commanders and therefore undercount when coverage is incomplete.
- **Association:** commander counts, cuts, and wins do not establish that the commander caused the result. Pilot experience, seat, pod composition, event size, cut policy, and list submission all confound the observed association.
- **Local versus global:** AZMS #7 is complete local evidence but only 20 seats. The global cohort is much larger but cannot be substituted for a particular Arizona room.
- **cEDH Stats versus archive:** cEDH Stats is the broader analytical layer; the repository cohort is a transparent, conservative verification slice. Their denominators and filters differ, so their counts should be compared directionally rather than merged.

## Source index

- [cEDH Stats — current analytical dashboard](https://cedhstats.org/stats)
- [cEDH Stats — commander meta](https://cedhstats.org/commanders)
- [cEDH Stats — Arizona](https://cedhstats.org/regions/Arizona)
- [cEDH Stats — Nevada](https://cedhstats.org/regions/Nevada)
- [TopDeck tournament archive in the repository](https://github.com/jaiaFoster/cEDH/tree/claude/cedh-simulation-research-k5afxg/data/tournament_snapshots/topdeck/normalized)
- [TopDeck.gg](https://topdeck.gg)
- [Creature Factory canonical snapshot](https://github.com/jaiaFoster/cEDH/blob/claude/cedh-simulation-research-k5afxg/data/deck_sources/moxfield/tymna-thrasios/current.json)

