# SIM-DECKBUILD-008 — Thassa's Oracle Package Audit (Creature Factory, Thrasios / Tymna)

**Subject:** `tymna-thrasios-creature-factory-deckbuild008-v1` (Moxfield `gvyGvOx0g0uJ7ultPy-pbw`, version 8,
98 main + Thrasios, Triton Hero / Tymna the Weaver). Frozen deck hash
`bcc611f4d4d9804a3cdec581ea25b9c8224b75177648a85614ab1a470145de75`.
**Data cutoff:** 2026-10-30. **Oracle text:** Scryfall, pulled 2026-10-30 (`data/cards_cache/oracle-2026-10-30/`).

Evidence classes are kept separate throughout and labelled:

- **[MEASURED-MC]** — paired Monte Carlo goldfish (no opponents) on exact 98-card lists; n, seed rule and SE given.
- **[MEASURED-CENSUS]** — counts over real tournament decklists; n, Fisher p / BH q and CIs given.
- **[STRUCTURAL]** — exact enumeration over Oracle text (tutor graph, rules).
- **[SCENARIO]** — hand-built or log-derived states with explicit uncertainty labels; *not* win rates.
- **[INTERPRETATION]** — judgement, flagged as such.

Nothing here is a multiplayer win rate. "Det. win by T4" means *a deterministic winning line is available in the
goldfish by the pilot's 4th turn* — a measure of conversion capability, not of games won.

---

## 0. Executive answers (§18)

| # | Question | Answer |
|---|---|---|
| 1 | Add Thassa's Oracle? | **Yes.** It is the single largest conversion improvement available without touching mana, engines or protection. Build 3 vs the best Oracle-less build: det. win by T4 **4.20% → 8.23% (+4.03pp, SE 0.16)**, by T3 **0.97% → 2.26% (+1.29pp, SE 0.09)**, protected det. win by T4 **1.47% → 2.75% (+1.28pp, SE 0.09)** [MEASURED-MC, n=15,000 paired]. Keep-7 rate, T2 mana and T3 engine establishment move by ≤0.2pp (within ~2 SE). |
| 2 | Package size 2 / 3 / 4+? | **4 slots: Oracle + Demonic Consultation + Tainted Pact + Spellseeker.** Each step is positive: Oracle+Consult (+1.49pp), +Spellseeker (+1.48pp more), +Pact (+1.16pp more). A 5th card (Borne, Training Grounds, Mystical, Worldly, Allosaurus, Veil) adds 0.00 ± 0.15pp of conversion [MEASURED-MC, n=20,000]. |
| 3 | Spellseeker in it? | **Yes — it is the best 3rd card, ahead of Pact.** Oracle+Consult+Spellseeker 7.25% vs Oracle+Consult+Pact 6.94% (n=20,000, same slot count). Spellseeker is also the best Strix replacement in the Oracle-less deck (+0.88pp, SE 0.09). Structurally it turns Consultation and Pact from 3–4 direct tutors into 4 direct + 19 two-step paths, because all seven creature tutors now reach them. |
| 4 | Is Pact worth the third slot? | **Worth the fourth, not the third.** As the 2nd card Pact (+0.83pp) is clearly worse than Consultation (+1.49pp): it costs 3 mana vs 1, and its fair mode is not deterministic. Added on top of Oracle+Consult+Spellseeker it still adds +1.16pp (D vs D2), and the census shows 94.5% of Oracle lists play it. |
| 5 | Does Borne add beyond High Fae / Teferi / Zone / Crop Rotation? | **No measurable conversion, and no census signal.** +Borne on top of the 4-card package: −0.03 ± 0.15pp det., +0.02pp protected. Census: 68.3% of Oracle lists vs 69.4% of non-Oracle lists (p = 0.79) — Borne is a T&T staple independent of Oracle, not part of the package. Its instant-window value is already covered by the deck's three timing enablers. |
| 6 | Are Hermit Druid / Divining Witch / Shang-Chi competitive? | **No.** The best creature-pure build (Oracle + Hermit + Shang-Chi) gives +0.79pp (SE 0.07) vs +4.03pp for Build 3 in the same 4 slots; Witch variants are ≤0. Census: Hermit in 3.9% of Oracle lists, Witch in 0%, Shang-Chi *under*-represented in Oracle lists (−6pp). Hermit only helps when paired with Consultation (Oracle+Consult+Hermit +2.08pp, still behind Oracle+Consult+Spellseeker +2.97pp). |
| 7 | Exact best cuts? | **Strix Serenade, Volatile Stormdrake, Gleaming Splendor, The Queen of Dale** (plus the separate, mana-neutral **Deathrite Shaman → Avacyn's Pilgrim**). This set is on the Pareto frontier (§12), costs 0 free counters, 0 proactive protection, 0 tutors, 0 timing pieces, 0 lands, and exactly one interaction card (Volatile Stormdrake, an energy-limited theft). Frontier-equivalent alternatives: Lotho in place of Queen (−0.04pp, within noise), or Gilded Drake in place of Gleaming Splendor (census-preferred, but measurably worse for mulligans: keep-7 −0.6pp). |
| 8 | Which package loses slots? | **Policing / value (−2: Gleaming Splendor, Queen of Dale) and creature theft (−1: Volatile Stormdrake), plus the flex removal slot (−1: Strix).** Engines, protection, tutors, free interaction, timing and mana are untouched. Priorities 1–2 of the strategic identity (win; copy engines) are untouched. |
| 9 | Does it damage any package? | **Not in any goldfish-measurable way** — see §11 deltas. The real costs are goldfish-invisible: one less 2-mana creature-steal (Stormdrake), Strix's cheap answer to an artifact/creature, and two policing pieces. Creatures 33 → 32 (Pod/Chord/Survival chains still 32 bodies), blue pitch fuel unchanged at 28. |
| 10 | Does conversion improve without worsening mana / mulligans / engines / protection / resilience? | **Yes, within measurement error.** Deltas for Build 3 vs Build 1 [MEASURED-MC]: keep-7 −0.09 ± 0.06pp; mean mulligans +0.0007; T2 ≥3 mana −0.19 ± 0.06pp; T2 all four colours +0.11 ± 0.07pp; premium engine by T3 −0.11 ± 0.06pp. Resilience improves: the Oracle-less deck has exactly **one** deterministic kill (Bowmasters + Faerie Mastermind) — removing either card deletes 100% of measured deterministic wins; Build 3 has two independent outlets (§11.5). |
| 11 | Which tutors / cards gain the most value? | **Eldritch Evolution (+0.08 → +0.90pp, ×11), Birthing Pod (+0.72 → +1.98pp), Demonic Tutor (+0.38 → +0.88pp), Neoform (+0.30 → +0.66pp), Chord (+0.26 → +0.50pp), Survival (+0.08 → +0.26pp)** — leave-one-out value in the Oracle-less vs the Oracle context [MEASURED-MC, n=5,000]. The creature tutors gain most because Oracle and Spellseeker are both creatures. Enlightened Tutor is the only tutor that *loses* value (+0.16 → +0.04pp). |
| 12 | Recommended final 98? | **Build 3** (§16.3), deck hash `914b7f881d0e01acfa8ac48b4ce93936dc9c8ac4399f4a4de1d3176fcfbf9851` — see `deckbuild008_final_lists.json`. |

---

## 1. Frozen baseline and reconciliation (§1)

- **Moxfield** re-synced live on 2026-10-30. Version 8 (updated 2026-10-15T15:50:53Z) is unchanged, content hash
  `635940777a53f5e8a7b27156cf7caec22694f7935b1faf0f83f5677a96f39148`, identical to
  `data/deck_sources/moxfield/tymna-thrasios/current.json`.
- **TopDeck registrations** for both events (AZMS cEDH Qualifier #8, 2026-10-17; Geekery Games "Eye of the Tiger (Lion)"
  LED event, 2026-10-18) were pulled from the stored raw snapshots, standings → `deckObj.Mainboard`. Both are
  imported from the same Moxfield URL and are **card-for-card identical to v8** (98 cards each).
- **Borne Upon a Wind discrepancy — resolved.** Borne appears only in the Geekery round-3 photo transcription
  ("Borne Upon a Wind; Gemstone Caverns; Chrome Mox; Neoform; Mindbreak Trap; Strix's Serenade; Swan Song"). It is
  absent from all 11 stored Moxfield snapshots and from both TopDeck registrations. **The registered list is v8; Borne
  is not in the baseline.** The most likely explanation is a transcription error; a proxy or a late physical swap
  cannot be excluded from the stored data. Borne is evaluated as a candidate add (variant E; answer to Q5).
- **Frozen file:** `data/decklists/tymna-thrasios-creature-factory-deckbuild008-v1.json`, built and asserted by
  `sim/analysis/build_deckbuild008_frozen_deck.py`. The hash is `compute_deck_hash` (sorted commanders + sorted
  name/scryfall_id/quantity).
- **Prior work** (DECKBUILD-005/006/007, MANA-AUDIT-002) was read as historical evidence only. No numbers are reused.
  One prior modeling claim is corrected here (§3.2).

## 2. Strategic identity used for every judgement (§2)

Develop engines → survive the first fight → convert. Priority when choosing what a slot does:
**winning > copying an opponent's engine > stealing creatures > cheap emergency interaction > policing.**
This is applied as an explicit, disclosed tie-break *only* where goldfish measurements cannot distinguish cut
candidates (§12). It is not hidden inside a score. The package is evaluated as a way to convert more of the deck's
engine states, not as a move toward a control deck. No interaction or protection density was spent.

## 3. Mana (§3)

### 3.1 Density is preserved

All builds keep **28 functional land slots**: 27 lands + Sink into Stupor // Soporific Springs, which counts as a land
per the assignment. Fast-mana rocks excluding Mox Amber: 5. Mox Amber is tracked separately and is **not** counted as
a land or as mana in mulligan scoring (enforced by `hand_features`; regression test
`test_mox_amber_not_counted_in_mulligan_features`). Dorks: 5. No Oracle-package card is paid for with mana.

### 3.2 Rules correction — Deathrite Shaman

Oracle text: *"{T}: Exile target land card from a graveyard. Add one mana of any color."* The ability **targets**, so
under CR 605.1a it is **not a mana ability**. It uses the stack and can be responded to, and it **does not count as
"tapping a permanent for mana"** (CR 106.12). Consequences, all encoded and tested:

- Kinnan, Bonder Prodigy and Badgermole Cub give **no bonus** for Deathrite (`NOT_A_MANA_ABILITY`;
  `test_deathrite_not_amplified_by_kinnan_or_badgermole`).
- Deathrite needs a land card in *some* graveyard (yours from fetches, or an opponent's). It is not mana on turn 1
  without one (`test_deathrite_needs_graveyard_land`).
- True dorks *are* amplified, per tap: Pilgrim + Kinnan = 2, Devoted Druid + Kinnan = 4 (two taps), Delney doubles
  the Kinnan/Badgermole trigger (`test_kinnan_bonus_per_tap`, `test_pilgrim_amplified`).

### 3.3 Dork sensitivity audit (separate, mana-neutral change outside the Oracle cut budget)

The design measures each dork *conditional on being in the opening seven* (`force_opening`, n=12,000 per dork), because
an unconditional comparison of a single slot is lost in noise. Results are [MEASURED-MC] with reference = Deathrite.

| Dork (forced in opening 7) | Det. win by T4 | T2 ≥3 mana | T2 all 4 colours | Premium engine by T3 |
|---|---|---|---|---|
| Deathrite Shaman (no opponent graveyard land) | 4.66% | 45.0% | 64.5% | 41.0% |
| Deathrite Shaman (opponent land in graveyard from T2: optimistic band) | 6.12% | 63.0% | 72.6% | 46.3% |
| **Avacyn's Pilgrim** | **5.76%** | **61.0%** | 56.8% | 42.6% |
| Llanowar Elves = Elvish Mystic = Fyndhorn Elves | 5.37% | 61.0% | 53.6% | 42.5% |
| Elves of Deep Shadow | 5.22% | 61.0% | 57.6% | 42.5% |
| Boreal Druid | 4.79% | 61.0% | 53.6% | 41.7% |
| Arbor Elf | 4.46% | 47.0% | 53.6% | 39.8% |
| Gilded Goose (over-credited, see note) | 6.13% | 61.0% | 69.3% | 44.9% |

- **Choice: Avacyn's Pilgrim.** Rule: highest conditional det. win by T4 among repeatable true dorks, tie-break
  four-colour T2. Pilgrim's W fixes the colour that the deck's T1 hands lack most often (T1 W 60% vs G 79%).
- Deathrite's T1 development is 2.7pp *higher* (it costs hybrid B/G), but on T2 the deck has ≥3 mana 45% of the time
  with Deathrite vs 61% with a true dork.
- **Gilded Goose is excluded.** The engine models it as a repeatable any-colour dork. In reality it is one free mana
  plus a food-limited repeat, so its row is an upper bound (disclosed, not fixed).
- Flat, unconditional deltas are tiny, as expected for a single slot: +1.9pp T2 ≥3 mana, −0.3pp T1 development.
  The swap is mana-neutral (28 lands unchanged; 5 dorks unchanged).
- [INTERPRETATION] If the local meta reliably fills opponents' graveyards with lands early (fetch-heavy blue decks),
  Deathrite's optimistic band (6.12%) is competitive with Pilgrim. Pilgrim is the robust choice, not a
  dominating one.

## 4. Protected cards (§4)

The following were **never put in the cut pool**:

- Core: Birthing Pod, Abhorrent Oculus, Devoted Druid, Hazel's Brewmaster, Swift Reconfiguration, Machine God's Effigy,
  Nature's Rhythm, The Cabbage Merchant, Mockingbird, Flash Photography.
- Timing: High Fae Trickster, Teferi, Emergence Zone, Crop Rotation.
- Proactive protection: Silence, Grand Abolisher, Voice of Victory, Ranger-Captain.
- Free interaction: FoW, FoN, Fierce Guardianship, Flare of Denial, Pact of Negation, Mindbreak Trap, Misdirection,
  Commandeer, Subtlety.

**Imperial Seal** appears only in a stress pool. **Delney** was in the cut pool but modeled fairly (its trigger
doubling feeds Kinnan/Badgermole, and Tymna draws are not modeled, so its floor is understated, not overstated). The
measurements back the protection: in the Oracle context, leave-one-out losses are Birthing Pod 1.98pp, Nature's Rhythm
0.22pp, and Pod is the single most valuable non-package card in both contexts.

## 5. Strix Serenade (§5)

Strix is the first donor in every build. **Measured opportunity cost** [MEASURED-MC]: leave-one-out det. win loss
**−0.10 ± 0.05pp** (Oracle context) / −0.02 ± 0.02pp (Oracle-less). The goldfish cannot see what Strix answers.

[SCENARIO] The tournament logs give a concrete example of that value: Geekery R3, Strix (paid with Lotho's Treasure)
countered Kinnan's Phyrexian Metamorph. Cutting Strix leaves Swan Song, Flusterstorm, Mental Misstep and the nine free
counters as the 1-mana-or-free answers.

Census: Strix is in 1.1% of Oracle lists and 0.5% of non-Oracle lists, so it is a personal tech choice in both
populations. The best non-Oracle replacement for the slot, by screen (n=12,000), is **Spellseeker +0.88pp (SE 0.09)**;
then Summoner's Pact +0.60, Green Sun's Zenith +0.40; everything else ≈0 (Worldly, Mystical, Training Grounds, Veil,
Biomancer's Familiar, Seedborn, Sylvan Library, Borne, Shang-Chi).

## 6. Package census (§6) [MEASURED-CENSUS]

### 6.1 Sources and populations

- **TopDeck archive** (`data/tournament_snapshots/topdeck/raw/`): every Thrasios/Tymna list with a registered
  decklist at eligible events, 2026-07-29 → 2026-10-26.
  - Eligibility: ≥16 seats, not casual/precon/budget/etc. (regex in JSON), and either a cEDH label or ≥50% of known
    commanders in the EDHTop16 six-month top-100. That gives 902 eligible events, 690 with a strict cEDH label.
  - The subject pilot's six lists are excluded.
  - **The repository archive starts 2026-07-27, so the "archive" window is ~3 months, not 6.** The 6-month view comes
    from cedhstats.org (Thrasios/Tymna decklists, ≥16 players, `with=`/`without=` oracle-id filters, retrieved
    2026-10-30).

| Population | Lists | Events | Pilots | Oracle inclusion (95% CI) | Top-cut lists | Winners |
|---|---|---|---|---|---|---|
| Broad archive (~3 mo) | 644 | 322 | 367 | 68.0% (64.3–71.5) | 158 | 17 |
| Strict cEDH label | 382 | 194 | 255 | 70.7% (65.9–75.0) | 96 | 10 |
| Broad, last 30 days | 220 | 118 | 168 | 61.4% (54.8–67.6) | 52 | 7 |
| Top cut only | 158 | 130 | 102 | 69.0% (61.4–75.7) | 158 | 17 |
| 64+ player events | 186 | 45 | 133 | 68.8% | 33 | 2 |
| Creature shell, no turbo (Devoted Druid, no Ad Nauseam/Necro/LED…) | 468 | 275 | 276 | 61.1% | 111 | 12 |
| **High overlap with subject (≥75% of 98)** | **295** | 208 | 172 | **44.4% (38.8–50.1)** | 79 | 10 |
| Pilot-deduplicated | 367 | 223 | 367 | 65.4% | 75 | 5 |
| cedhstats 6 months | 1,240 | — | — | 76.6% | — | — |
| cedhstats 1 month | 234 | — | — | 61.1% | — | — |

- **Oracle is the T&T default, and it is not a top-cut signal by itself.** Top-cut enrichment is 1.05 in the broad
  archive and 1.66 in the high-overlap stratum (small n).
- **Inclusion is falling.** cedhstats shows 76.6% over 6 months vs 61.1% over the last month; the archive shows 61.4%
  over the last 30 days.
- Among creature-factory lists closest to the subject, it is roughly a coin flip (44%). The decision therefore has to
  rest on structure and measurement, not popularity.

### 6.2 Package structure (broad archive, 438 Oracle lists)

| Structure | Lists |
|---|---|
| Oracle + Consultation + Pact | 340 (78%) |
| Oracle + Pact only | 74 |
| Oracle + Consultation only | 20 |
| Oracle with neither | 4 |

### 6.3 Discovery table (§15)

- **P(c|O)**, **P(c|¬O)**: share of Oracle and non-Oracle lists playing the card. Values are broad archive / high-overlap
  stratum / cedhstats 6 months where shown.
- **Lift**: difference in percentage points (pp).
- **Top-cut enrichment (TC)**: P(top cut | card) / P(top cut | ¬card).
- **Floor**: what the card does without Oracle.
- p values are two-sided Fisher exact. CSV columns also carry the Haldane log-OR with Wald CI, Wilson CIs, Beta(1,1)
  shrinkage and BH q.

| Card | P(c\|O) | P(c\|¬O) | Lift (pp), p | TC | Structural role | Independent floor | Verdict |
|---|---|---|---|---|---|---|---|
| Thassa's Oracle | 1.00 | 0 | — | 1.05 | Outlet. 10 direct tutors / 35 two-step; Thrasios-infinite or Consult/Pact | 2-mana blue creature: Pod/Chord rung, scry 2 | **Add** |
| Demonic Consultation | 0.82 / 0.86 / 0.85 | 0 | +82 | 1.07 | 1-mana instant exile-library, UUB total with Oracle | Instant tutor (fair mode) | **Add** |
| Tainted Pact | 0.95 / 0.94 / 0.96 | 0.02 | +92 | 1.16 | 2-mana instant; fair mode not deterministic (singleton) | Weak tutor | **Add (4th card)** |
| Spellseeker | 0.26 / 0.15 / 0.22 | 0.13 / 0.09 / 0.14 | **+12.9, p=2e-4**; 6 mo +8.2, p=0.002 | **1.33** | Creature-tutor bridge to Consult/Pact/DT/Vamp/ET/Seal/Finale/Rhythm/Neoform/Crop/Silence | Best Strix replacement even without Oracle (+0.88pp) | **Add** |
| Borne Upon a Wind | 0.68 / 0.69 / 0.63 | 0.69 / 0.74 / 0.67 | −1.2, p=0.79 | 1.11 | 4th instant-window enabler | Flash-all + draw | **Do not add**: not package-associated; 0 conversion gain |
| Allosaurus Shepherd | 0 | 0 | — | — | Uncounterable green; no line | Nil here | Reject |
| Training Grounds | 0.59 / **0.74** | 0.44 / 0.40 | +15.2, p=4e-4; high-overlap **+34** | 1.05 | Thrasios {2} activation | Pod/engine discount | Not needed: +0.00pp on top of package. Watch-list |
| Mystical Tutor | 0.21 / 0.01 | 0.05 / 0.01 | +15.9 (broad); +0.2 (high-overlap) | 0.84 | Finds Consult/Pact/Seal at instant | Instant top-tutor | Reject: association is turbo-list driven (vanishes in high-overlap) |
| Worldly Tutor | 0.23 / 0.04 | 0.08 / 0.04 | +14.4 (broad); +0.2 (high-overlap) | 0.62 | Creature top-tutor | Same | Reject: same confound |
| Grand Abolisher | 0.58 / 0.44 / 0.66 | 0.20 / 0.16 / 0.25 | **+38, p<1e-10** | 1.02 | Proactive protection for sorcery-speed Oracle | Already in deck | Keep (protected) |
| Voice of Victory | 0.75 / 0.59 / 0.84 | 0.38 / 0.35 / 0.40 | **+37** | 0.82 | Same | Already in deck | Keep (protected) |
| Swift Reconfiguration | 0.88 / 0.90 | 0.41 / 0.40 | **+47** | 1.12 | Druid → infinite → Thrasios dig to Oracle | Already in deck | Keep (protected). Strongest co-signal |
| Silence | 1.00 | 0.99 | +0.5 | 0.98 | Shield | Already in deck | Keep |
| Veil of Summer | 0.81 | 0.85 | −4.4, p=0.18 | 0.81 | Shield vs blue counters | Already common | Not needed: +0.18pp protected only |
| High Fae Trickster | 0.50 / 0.84 / 0.48 | 0.84 / 0.91 / 0.83 | −34 (broad); −7, p=0.08 (high-overlap) | 0.97 | Instant window for everything | Already in deck | Keep. Oracle lists drop it mainly in turbo shells |
| Teferi, Mage of Zhalfir | 0.16 / 0.45 | 0.50 / 0.63 | −34 / −18 (p=0.003) | 1.06 | Creature instant window | Already in deck | Keep (protected); the one timing cut Oracle peers make |
| Emergence Zone | 0.69 / 0.92 | 0.91 / 0.96 | −22 / −3 | 1.62 | Land-slot instant window | Already in deck | Keep |
| Hermit Druid | 0.04 / 0.01 / 0.04 | 0 | +3.9, p=0.002 | 1.21 | Mill-all, Oracle from graveyard needs a reanimation/Finale route | 2-mana creature | Reject (§8 F) |
| Divining Witch | 0 | 0 | — | — | Exile library; {1}{B} + discard | Nil | Reject |
| Shang-Chi | 0.29 / 0.24 / 0.17 | 0.35 / 0.29 / 0.30 | −6.2, p=0.12 (6 mo −13.7) | 1.14 | Haste for creature lines | Value creature | Reject |
| Imperial Seal | 0.64 / 0.73 / 0.68 | 0.77 / 0.85 / 0.75 | **−12.8, p=0.001** | 1.12 | Sorcery top-tutor | Essential engine access | **Keep**: stress test §12 shows it is not free |
| Volatile Stormdrake | 0.24 / 0.48 / 0.16 | 0.66 / 0.77 / 0.65 | **−41.6, q=2e-22** | 1.04 | Theft (energy-limited) | 2-mana blue body | **Cut** |
| Gilded Drake | 0.22 / 0.54 | 0.63 / 0.77 | **−40.5, q=1e-21** | 0.93 | Permanent theft | 2-mana blue body | Keep in Build 3; alternative cut |
| Clever Impersonator | 0.36 / 0.61 / 0.30 | 0.66 / 0.76 / 0.66 | −29.9, q=1e-11 | 0.89 | Copies opponent engines (priority 2) | Copy | Keep (identity priority) |
| Endurance | 0.37 / 0.52 | 0.67 / 0.77 | −29.1, q=5e-11 | 0.84 | Graveyard hate, flash body | — | Keep: interaction density |
| Gleaming Splendor | 0.59 | 0.82 | −22.2, q=7e-8 | 1.12 | Policing; treasure | Policing | **Cut** |
| The Queen of Dale | 0.22 (6 mo) | 0.31 (6 mo) | −9.7, p=0.001 (6 mo) | — | Policing; looting | Policing | **Cut** |
| Faerie Mastermind | 0.81 / 0.99 / 0.78 | 0.98 / 0.99 / 0.98 | −17 / −1 | 1.00 | Half of the Oracle-less kill | Policing draw | Keep: secondary kill + Pod rung |
| Misdirection / Commandeer / Subtlety / Flash Photography | — | — | −26 / −34 / −46 / −30 | 0.9–1.6 | Free interaction / copy | Protected | Keep (protected) |
| Seedborn Muse | 0.34 / 0.15 | 0.15 / 0.09 | +19 / +7 | 0.65 | Untap engine | Not in deck | Not tested in MC (Seedborn not modeled) |
| Deathrite Shaman | 0.84 / 0.88 | 0.78 / 0.79 | +6.6, p=0.05 | 1.21 | Dork | — | Replaced for mana reasons (§3), not for Oracle |

**Density by Oracle status (broad archive):**

| Mean per list | Oracle lists | Non-Oracle lists |
|---|---|---|
| Tutors | 12.6 | 12.5 |
| Proactive protection | 4.5 | 4.1 |
| Free counters | 5.6 | 6.9 |
| Timing enablers | 2.05 | 2.97 |

- [INTERPRETATION] Oracle peers pay for the package mostly with theft creatures, copy effects and free interaction, not
  with tutors.
- This build pays with theft and policing instead, keeping free interaction and timing, which matches the subject's
  identity.
- The Oracle population is mixed with turbo lists (Ad Nauseam/Necro/LED). The high-overlap and no-turbo strata are the
  relevant comparison, and several "Oracle cuts timing" signals shrink there (High Fae −7, Zone −3; Teferi −18 remains).

## 7. Spellseeker audit and tutor / access graph (§7, §9) [STRUCTURAL]

Rules encoded and tested:

- Spellseeker finds an instant or sorcery with MV ≤2. X spells count X=0 in the library, so Finale of Devastation
  and Nature's Rhythm (MV 2) are legal.
- Spellseeker is a **Human Wizard**, so Kinnan cannot find it.
- Green Sun's Zenith and Summoner's Pact find **green** creatures only, so neither finds Oracle or Spellseeker
  (`test_gsz_summoners_cannot_find_blue`).
- Pod/Neoform need exactly MV+1; Eldritch needs ≤ sac+2; Chord/Finale/Rhythm need X ≥ MV.
- Top-of-library tutors need a draw, modeled as one Thrasios activation ({4}, or {2} with Training Grounds or
  Biomancer's Familiar).

**Spellseeker's targets in Build 3:**

| Kind | Targets |
|---|---|
| Win / package | Demonic Consultation, Tainted Pact |
| Tutors | Demonic Tutor, Vampiric Tutor, Enlightened Tutor, Imperial Seal, Finale of Devastation, Nature's Rhythm, Neoform, Crop Rotation |
| Protection / interaction | Silence, Swan Song, Flusterstorm, Mental Misstep, Pact of Negation |

**Spellseeker's own access** is the same as Oracle's, 10 direct tutors:

- Pod (from a 2-drop), Neoform (sac a 2), Eldritch Evolution, Chord (X=3), Finale (X=3), Nature's Rhythm (X=3),
  Survival, Demonic Tutor, Vampiric Tutor, Imperial Seal.

**Access counts per piece** (direct tutors / two-step paths) — `deckbuild008_tutor_graph.json`:

| Piece | v8 | A (Oracle-less + Spellseeker) | C (core 3, no Spellseeker) | **D = Build 3** | F (Oracle + Hermit + Shang-Chi) |
|---|---|---|---|---|---|
| Thassa's Oracle | — | — | 10 / 29 | **10 / 35** | 10 / 29 |
| Demonic Consultation | — | — | 3 / 6 | **4 / 19** | — |
| Tainted Pact | — | — | 3 / 6 | **4 / 19** | — |
| Spellseeker | — | 10 / 35 | — | **10 / 35** | — |
| Silence | 3 / 6 | 4 / 19 | 3 / 6 | **4 / 19** | 3 / 6 |
| Devoted Druid | 10 / 29 | 10 / 35 | 10 / 29 | 10 / 35 | 10 / 29 |
| Swift Reconfiguration / Effigy / Pod / Emergence Zone | 4 / 9 | 4 / 13 | 4 / 9 | 4 / 13 | 4 / 9 |

- **Instant-speed direct access to Oracle:** Chord of Calling, Survival of the Fittest, Vampiric Tutor.
- **Cheapest one-tutor Oracle win** from hand: Vampiric/Seal → Oracle with a Thrasios infinite, or Spellseeker →
  Consultation → Oracle (UUB + 3).

**Does Spellseeker increase effective copies while keeping a floor? Yes.**

- *Copies:* Consultation and Pact each go from 3 direct / 6 two-step to 4 direct / 19 two-step. The seven creature
  tutors become Consult/Pact tutors, and Silence gains the same reach.
- *Measured:* leave-one-out value in the Oracle context is +1.34pp (SE 0.17), third behind Pod and Consultation.
- *Floor:* even without Oracle it is the best Strix replacement (+0.88pp). It is a 3-mana blue creature (Pod rung 3,
  blue for Thrasios/Flare pitch) that fetches Silence, Swan Song or a tutor.
- *Why the census and the measurement both point the same way:* Spellseeker is the only package-associated card with
  positive top-cut enrichment (1.33).

### 7.1 Win-line hypergraph (§9)

Line families the solver enumerates (`deckbuild008_solver.py`). Each line is a set of required cards plus mana/colour
and a timing class:

| Family | Requires | Deterministic | Timing |
|---|---|---|---|
| `oracle_consult` | Oracle + Consultation, UUB (+ draw-safe) | yes | Consult instant, Oracle needs a flash enabler for instant-window |
| `oracle_pact` | Oracle + Pact, UU + 2B | yes | same |
| `inf_oracle` | Engine E1–E4 → infinite G (+U) → Thrasios digs to Oracle, cast with UU | yes | sorcery for Pod lines; activations at instant speed |
| `inf_bowmasters` | Infinite G+U + Orcish Bowmasters + Faerie Mastermind (draw-all → amass pings) | yes | instant possible |
| `inf_finale` | Infinite G → Finale X≥10 combat | **no** (blockers / fog) | sorcery |
| `oracle_hermit` / `oracle_witch` | Hermit mill-all (+ Finale/Rhythm from graveyard) / Witch exile | yes | sorcery, Hermit has summoning sickness unless Shang-Chi |

Engines: **E1** Druid + Swift; **E2** Hazel's Brewmaster exiling Druid; **E3** Druid + Effigy (copy must be a creature —
a Swift-ed Druid is a noncreature, so Effigy cannot copy it: `test_swift_druid_not_copyable_by_effigy`); **E4** Oboro
Breezecaller + Talon Gates + Cradle with ≥6 creatures.

[STRUCTURAL] Without Oracle, **every** deterministic kill passes through `inf_bowmasters`, so the deck's
deterministic win is a 2-card single point of failure (Bowmasters + Mastermind). With Oracle there are three independent
outlet families (Consult, Pact, Thrasios-infinite → Oracle), sharing only the Oracle card itself and its 10 tutors.

## 8. Variants (§8) [MEASURED-MC]

**Design:**

- Paired common random numbers: game *i* uses seed 8,000,000 + *i* for every variant.
- On the play iff seed mod 4 = 0, giving one seat in four.
- Slot-preserving swaps, so the same library positions are compared.
- London mulligan under the pilot policy: keeps ~59% of sevens, mean 0.55 mulligans.
- Tutor policy "engine_tutor"; goldfish horizon 4 turns.
- n = 20,000 per variant.
- Δ and its SE are paired against A.

The variant cuts here are the goldfish-inert cards Stormdrake / Skyturtle / Gilded Drake / Endurance. The exact
recommended cuts are re-verified in §16.

| Variant | Det. win T2 | T3 | **T4 (Δ vs A ± SE)** | Protected T4 | Instant-window T4 | Oracle line T4 | Incl. non-det T4 | Keep 7 |
|---|---|---|---|---|---|---|---|---|
| BASELINE v8 (Deathrite, Strix) | 0.06% | 0.98% | 3.43% (−0.84 ± 0.07) | 1.21% | 0.46% | 0 | 4.16% | 60.5% |
| **A** Oracle-less (Pilgrim, Spellseeker) | 0.08% | 1.04% | **4.27%** | 1.47% | 0.48% | 0 | 4.96% | 61.3% |
| B Oracle + Consult | 0.27% | 1.93% | 5.77% (+1.49 ± 0.12) | 2.03% | — | — | — | 59.8% |
| B2 Oracle + Pact | 0.12% | 1.43% | 5.10% (+0.83 ± 0.10) | 1.76% | — | — | — | 59.8% |
| C Oracle + Consult + Pact | 0.27% | 2.25% | 6.94% (+2.67 ± 0.14) | 2.40% | 0.64% | 3.61% | 7.35% | 59.5% |
| D2 Oracle + Consult + Spellseeker | 0.27% | 1.97% | 7.25% (+2.97 ± 0.13) | 2.44% | — | — | — | 60.6% |
| **D Oracle + Consult + Pact + Spellseeker** | 0.27% | 2.32% | **8.41% (+4.14 ± 0.15)** | 2.78% | 0.64% | 4.75% | 8.81% | 60.2% |
| E: D + Borne Upon a Wind | 0.27% | 2.31% | 8.38% (+4.12) | 2.81% | — | — | — | 59.7% |
| E: D + Training Grounds | — | — | 8.38% (+4.11) | 2.79% | — | — | — | 59.7% |
| E: D + Mystical Tutor | — | — | 8.38% (+4.11) | 2.82% | — | — | — | 60.8% |
| E: D + Worldly Tutor | — | — | 8.36% (+4.09) | 2.79% | — | — | — | 60.8% |
| E: D + Allosaurus Shepherd | — | — | 8.40% (+4.13) | 2.78% | — | — | — | 60.2% |
| E: D + Veil of Summer | — | — | 8.38% (+4.11) | **2.96%** | — | — | — | 60.2% |
| F Oracle + Hermit | 0.08% | 1.14% | 4.41% (+0.14 ± 0.09) | 1.58% | — | — | — | 59.7% |
| F Oracle + Hermit + Shang-Chi | 0.08% | 1.13% | 4.45% (+0.18 ± 0.09) | 1.60% | 0.54% | 0.68% | 4.91% | 59.3% |
| F Oracle + Witch | — | — | 4.11% (−0.17 ± 0.08) | 1.41% | — | — | — | 59.7% |
| F Oracle + Witch + Shang-Chi | — | — | 4.19% (−0.08 ± 0.08) | 1.44% | — | — | — | 59.3% |
| F Oracle + Consult + Hermit | 0.27% | 2.03% | 6.35% (+2.08 ± 0.13) | 2.24% | — | — | — | 59.4% |
| F Oracle + Hermit + Witch + Shang-Chi | — | — | 4.86% (+0.60 ± 0.10) | 1.70% | — | — | — | 58.8% |
| G Oracle alone (Thrasios-infinite only) | 0.08% | 1.08% | 3.83% (−0.44 ± 0.07) | 1.37% | — | — | — | 60.1% |

**Readings:**

- **Oracle alone is negative.** It costs a slot and only adds the `inf_oracle` route, which the deck already converts
  via Bowmasters.
- **Consultation is what makes Oracle work.** Its 1-mana instant line accounts for most of B's gain, including a
  T2/T3 tripling.
- **Diminishing but positive returns to the 4th card; zero for the 5th.**
- **Every E card ties D.** The Veil row gains only in protected wins (+0.18pp).
- **The creature-pure family fails** because Hermit/Witch are sorcery-speed, summoning-sick creatures with no
  free-mana enabler. They also replace an instant 1-mana outlet with a 2-mana creature that dies to the first removal.
- **No variant changes T2 mana or engine establishment by more than 0.5pp.** Premium engine by T3 stays 52.0–52.8%
  everywhere.

### 8.1 Sensitivity [MEASURED-MC]

| Setting (n) | A det. T4 | B Δ | C Δ | **D Δ** | D keep-7 Δ |
|---|---|---|---|---|---|
| Pilot policy, engine_tutor (20,000) | 4.27% | +1.49 | +2.67 | **+4.14** | −1.11 |
| Hold tutors (6,000) | 4.62% | +1.47 | +2.53 | **+3.65** | −0.75 |
| Engine-draw band, optimistic Rhystic/Tymna draws (6,000) | 5.32% | +1.82 | +3.22 | **+4.97** | −0.75 |
| No mulligan, raw 7 (6,000) | 3.85% | +1.60 | +2.73 | **+4.20** | — |
| Loose keep policy (6,000) | 4.45% | +1.40 | +2.60 | **+4.30** | +0.33 |
| Strict keep policy (6,000) | 3.90% | +1.38 | +2.43 | **+3.67** | −0.50 |

- The ranking A < B2 < B < C < D is the same in every setting, and the creature-pure F stays at ≈0 under both
  loose and strict keeps.
- The −1pp keep-7 cost in the variant runs comes from their inert cuts (Stormdrake/Skyturtle/Gilded are counted as
  interaction by the keep heuristic).
- With the recommended cuts it falls to −0.09pp (§16).

## 9. Conversion surface area (§10)

<!--FILL_CSA-->

## 10. Single-card ablation (§12 input) [MEASURED-MC]

Leave-one-out loss in deterministic win by T4 when the card is replaced by an uncastable blank (n=5,000 each, paired).

- **Oracle context:** baseline-with-Pilgrim + Oracle + Consult + Pact + Spellseeker, reference 7.12%.
- **Oracle-less context:** baseline-with-Pilgrim, reference 3.32%.

| Card | Oracle context | Oracle-less context |
|---|---|---|
| Birthing Pod | **+1.98 ± 0.21** | +0.72 ± 0.12 |
| Demonic Consultation | **+1.66 ± 0.18** | — |
| Spellseeker | **+1.34 ± 0.17** | — |
| Tainted Pact | +0.90 ± 0.14 | — |
| Eldritch Evolution | +0.90 ± 0.14 | +0.08 ± 0.07 |
| Demonic Tutor | +0.88 ± 0.15 | +0.38 ± 0.11 |
| Neoform | +0.66 ± 0.12 | +0.30 ± 0.09 |
| Chord of Calling | +0.50 ± 0.12 | +0.26 ± 0.08 |
| Finale of Devastation | +0.28 ± 0.09 | +0.12 ± 0.07 |
| Survival of the Fittest | +0.26 ± 0.10 | +0.08 ± 0.06 |
| Nature's Rhythm | +0.22 ± 0.09 | +0.08 ± 0.05 |
| Vampiric Tutor | +0.14 ± 0.10 | +0.08 ± 0.07 |
| Imperial Seal (stress) | +0.14 ± 0.11 | +0.02 ± 0.08 |
| Enlightened Tutor | +0.04 ± 0.08 | +0.16 ± 0.07 |
| **Faerie Mastermind** | +0.04 ± 0.04 | **+3.32 ± 0.25** |
| **Orcish Bowmasters** | −0.02 ± 0.06 | **+3.32 ± 0.25** |
| Esper Sentinel | +0.12 ± 0.09 | +0.04 ± 0.06 |
| Derevi | +0.08 ± 0.04 | −0.00 ± 0.03 |
| Clever Impersonator / Skyturtle / Endurance | +0.04 ± 0.03–0.04 | ≈0 |
| Queen of Dale / Delney / Swan Song / Lotho / Gleaming Splendor | −0.00 ± 0.00–0.05 | ≈0 |
| Flusterstorm / Misstep / Stormdrake / Gilded Drake / Oboro | −0.02 to −0.06 ± 0.03–0.04 | ≈0 |
| Strix Serenade | −0.10 ± 0.05 | −0.02 ± 0.02 |

- Bowmasters and Mastermind each carry the *entire* Oracle-less deterministic kill: 3.32pp = 100% of the reference.
- With Oracle, they become goldfish-redundant. They keep their real-game floor (Bowmasters vs draw / wheels;
  Mastermind as a 2-drop flash body and Pod rung), so neither is a recommended cut.
- In the Oracle context, every card in the 17-card cut pool is within ±0.12pp, i.e. indistinguishable from a blank in the
  goldfish. The choice among them has to come from roles, the census and identity (§12), and this report says so rather
  than presenting noise as a ranking.

## 11. Metrics (§11) — Build 3 vs Build 1 [MEASURED-MC, n=15,000 paired]

### 11.1 Mana integrity

| Metric | Build 1 | Build 3 | Δ ± SE |
|---|---|---|---|
| Lands (incl. MDFC) | 28 | 28 | 0 |
| Fast rocks excl. Mox Amber | 5 | 5 | 0 |
| T2 ≥3 mana | 42.60% | 42.41% | −0.19 ± 0.06 |
| T2 all four colours | 64.02% | 64.13% | +0.11 ± 0.07 |

### 11.2 Mulligans

| Metric | Build 1 | Build 3 | Δ ± SE |
|---|---|---|---|
| Keep 7 (pilot policy) | 61.39% | 61.31% | −0.09 ± 0.06 |
| Mean mulligans | 0.536 | 0.537 | +0.001 |
| Keep-policy sensitivity (loose / strict) | §8.1 | §8.1 | same ordering |

### 11.3 Engine establishment

| Metric | Build 1 | Build 3 | Δ ± SE |
|---|---|---|---|
| Premium engine by T3 | 52.16% | 52.05% | −0.11 ± 0.06 |

### 11.4 Conversion

| Metric | Build 1 | Build 3 | Δ ± SE |
|---|---|---|---|
| Det. win by T2 | 0.08% | 0.27% | +0.19 ± 0.04 |
| Det. win by T3 | 0.97% | 2.26% | +1.29 ± 0.09 |
| **Det. win by T4** | **4.20%** | **8.23%** | **+4.03 ± 0.16** |
| Protected det. win by T4 | 1.47% | 2.75% | +1.28 ± 0.09 |
| Instant-window det. win by T4 | 0.47% | 0.63% | +0.16 ± 0.03 |
| Oracle line by T4 | 0 | 4.61% | +4.61 ± 0.17 |
| Creature-infinite line by T4 | 4.20% | 4.41% | +0.21 ± 0.05 |
| Incl. non-deterministic by T4 | 4.93% | 8.66% | +3.73 ± 0.16 |

**Instant-window conversion barely moves (+0.16pp).**

- Oracle is a creature, so an instant-speed Oracle win still needs High Fae, Teferi, Emergence Zone (or Borne).
- The package mainly adds *main-phase* conversion, which the protection suite (Silence / Abolisher / Voice /
  Ranger-Captain) is built to cover.
- This is also why Borne measures at zero: the binding constraint is the line, not the window.

### 11.5 Tutor leverage, dead cards, role multiplicity, resilience

<!--FILL_STATES-->

## 12. Cut optimisation and Pareto frontier (§12)

**Objectives** (all minimised, no weights):

- Goldfish losses from §10: det. T4, protected T4, instant-window T4, premium engine T3, keep 7.
- Role losses:
  - interaction
  - free counters
  - card advantage
  - creatures
  - blue pitch fuel
  - secondary-kill redundancy (Bowmasters, Mastermind, Clever Impersonator, Oboro, Gleaming Splendor)
  - premium engines

**Enumeration:**

- Strix + every (p−1)-subset of the 17-card pool, for package sizes p = 2, 3, 4.
- A stress pool forces Imperial Seal into the set.
- Losses are additive in the single-card marginals and screened for dominance.
- Chosen sets are then **re-verified exactly** as full 98-card decks (§16).

Files:

- `deckbuild008_cut_ablation.csv`: per-card contributions and SEs, both contexts.
- `deckbuild008_pareto_frontier.csv`: every non-dominated set with its full objective vector.

| Package size | Candidate sets | Frontier size (default) | Frontier size (stress, with Seal) |
|---|---|---|---|
| 2 | 17 | 12 | 1 |
| 3 | 136 | 65 | 12 |
| 4 | 680 | 216 | 65 |

**The frontier is wide** because goldfish losses are all within noise (§10). Dominance is therefore decided almost
entirely by role counts, and there are many incomparable trade-offs.

**Disclosed tie-break among frontier sets**, in this order:

1. Zero loss of free counters, proactive protection, tutors, timing, lands, premium engines.
2. Strategic-identity priority (§2): cut policing before emergency interaction before theft before copy effects.
3. Census displacement in the high-overlap stratum.
4. Mulligan neutrality in exact verification.

**Result:**

| Size | Cuts | On frontier | Why |
|---|---|---|---|
| 3 | Strix, **Volatile Stormdrake**, **Gleaming Splendor** | yes | Stormdrake has the strongest Oracle-displacement signal of any card (−42pp broad, −29pp high-overlap, 6 mo −48pp) and is an energy-limited theft. Gleaming Splendor is policing and its "two players draw" kill needs W the infinite engines do not make. |
| 4 | + **The Queen of Dale** | yes | Lowest identity priority (policing/looting). 6-month census −9.7pp. Leave-one-out −0.00 ± 0.05pp. |

**Rejected or alternative 4th cuts:**

| Cut | Status | Reason |
|---|---|---|
| Lotho | Frontier-equivalent | Exact Δ −0.04pp vs Queen, within noise. Not chosen because Lotho's Treasure develops engines; the Geekery R3 log has Lotho Treasure → Strix and Neoform → T2 Oculus. |
| Gilded Drake | Dominated on role axes (interaction) | Census-preferred (−40pp) but costs keep-7 −0.6pp in exact verification. Permanent theft also ranks above policing by identity. |
| Clever Impersonator | Kept | Copies opponent engines (priority 2). |
| Endurance | Kept | Graveyard interaction density. |
| Faerie Mastermind / Bowmasters | Kept | Secondary kill and anti-draw floor. |
| Swan Song / Flusterstorm / Misstep | Kept | Cheap emergency interaction outranks policing. |
| Imperial Seal (stress) | **Rejected** | §16.3b: det. T4 −0.19pp vs Build 3; **keep-7 −1.22 ± 0.10pp**; **premium engine by T3 −2.46 ± 0.15pp**. It is the deck's best sorcery engine tutor and is measurably not expendable. |

## 13. Tournament-derived scenarios (§13) [SCENARIO]

<!--FILL_SCENARIOS-->

## 14. Builds (§16) [MEASURED-MC exact verification, n=15,000 paired vs Build 1]

All builds: v8 with **Deathrite Shaman → Avacyn's Pilgrim** (mana-neutral, §3) and **Strix Serenade out**. Exact 98s and
hashes are in `deckbuild008_final_lists.json` (generator `sim/analysis/build_deckbuild008_final_lists.py`).

| Build | Adds (beyond Pilgrim) | Cuts (beyond Deathrite) | Lands | Creatures | Interaction | Free ctr | Tutors | Proactive prot. | Timing | Det. T3 | **Det. T4** | Prot. T4 | Keep 7 | Hash |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1 Optimised Oracle-less** | Spellseeker | Strix | 28 | 33 | 20 | 9 | 14 | 4 | 3 | 0.97% | **4.20%** | 1.47% | 61.4% | `6c71fb35…` |
| **2 Minimum efficient Oracle** | Spellseeker, Oracle, Consultation | Strix, Volatile Stormdrake, Gleaming Splendor | 28 | 33 | 19 | 9 | 14 | 4 | 3 | 1.89% | **7.17%** (+2.97 ± 0.14) | 2.41% | 61.2% (−0.22) | `fee85d4b…` |
| **3 Recommended Oracle** | Spellseeker, Oracle, Consultation, Tainted Pact | Strix, Volatile Stormdrake, Gleaming Splendor, The Queen of Dale | 28 | 32 | 19 | 9 | 15 | 4 | 3 | 2.26% | **8.23%** (+4.03 ± 0.16) | 2.75% | 61.3% (−0.09) | `914b7f88…` |
| 3a variant (Lotho for Queen) | same | Strix, Stormdrake, Gleaming, Lotho | 28 | 32 | 19 | 9 | 15 | 4 | 3 | 2.14% | 8.19% (+3.99) | 2.72% | 61.3% | `f8d6478c…` |
| 3b census cuts (Gilded Drake) | same | Strix, Stormdrake, Gilded Drake, Gleaming | 28 | 32 | 18 | 9 | 15 | 4 | 3 | 2.19% | 8.15% (+3.95) | 2.79% | 60.8% (−0.61) | `90d130a8…` |
| 3c stress: cut Imperial Seal | same | Strix, Stormdrake, Gleaming, Imperial Seal | 28 | 33 | 19 | 9 | 14 | 4 | 3 | 2.23% | 8.04% (+3.84) | 2.75% | 60.2% (−1.22) | `d890fe4e…` |
| 4 Creature-pure Oracle | Spellseeker, Oracle, Hermit Druid, Shang-Chi | Strix, Stormdrake, Gleaming, Queen | 28 | 34 | 19 | 9 | 14 | 4 | 3 | 1.11% | 4.99% (+0.79 ± 0.07) | 1.83% | 61.0% (−0.40) | `fe05168d…` |

**Win packages:**

| Build | Win packages |
|---|---|
| 1 | Creature-infinite (E1–E4) → Bowmasters + Mastermind; Finale X≥10 (non-deterministic) |
| 2 | + Oracle/Consultation; + Thrasios-infinite → Oracle |
| 3 | + Oracle/Pact |
| 4 | Creature-infinite → Bowmasters or → Oracle; Hermit → Oracle (sorcery, needs haste or a turn) |

Mana metrics for every build are within ±0.3pp of Build 1 except 3c (T2 ≥3 mana +0.75pp, because Seal costs 1 and
does nothing on T1–2 in the goldfish).

### 14.3 Recommended final 98 (Build 3)

Commanders: Thrasios, Triton Hero; Tymna the Weaver. **New cards in bold.**

- **Lands (28 incl. MDFC) — 28:** Ancient Tomb; Bayou; Boseiju, Who Endures; City of Brass; City of Traitors; Command Tower; Emergence Zone; Exotic Orchard; Flooded Strand; Gaea's Cradle; Gemstone Caverns; Mana Confluence; Marsh Flats; Misty Rainforest; Otawara, Soaring City; Polluted Delta; Savannah; Scrubland; Sink into Stupor // Soporific Springs; Starting Town; Talon Gates of Madara; Tarnished Citadel; Tropical Island; Tundra; Underground Sea; Verdant Catacombs; Windswept Heath; Wooded Foothills
- **Creatures — 32:** Abhorrent Oculus; Avacyn's Pilgrim **(new)**; Badgermole Cub; Birds of Paradise; Clever Impersonator; Colossal Skyturtle; Delighted Halfling; Delney, Streetwise Lookout; Derevi, Empyrial Tactician; Devoted Druid; Elvish Spirit Guide; Endurance; Enduring Vitality; Esper Sentinel; Faerie Mastermind; Gilded Drake; Grand Abolisher; Hazel's Brewmaster; High Fae Trickster; Kinnan, Bonder Prodigy; Lotho, Corrupt Shirriff; Mockingbird; Noble Hierarch; Oboro Breezecaller; Orcish Bowmasters; Ranger-Captain of Eos; Spellseeker **(new)**; Subtlety; Teferi, Mage of Zhalfir; Thassa's Oracle **(new)**; The Cabbage Merchant; Voice of Victory
- **Instants / sorceries — 25:** Chord of Calling; Commandeer; Crop Rotation; Demonic Consultation **(new)**; Demonic Tutor; Eldritch Evolution; Enlightened Tutor; Fierce Guardianship; Finale of Devastation; Flare of Denial; Flash Photography; Flusterstorm; Force of Negation; Force of Will; Imperial Seal; Mental Misstep; Mindbreak Trap; Misdirection; Nature's Rhythm; Neoform; Pact of Negation; Silence; Swan Song; Tainted Pact **(new)**; Vampiric Tutor
- **Artifacts / enchantments — 13:** Birthing Pod; Chrome Mox; Lotus Petal; Machine God's Effigy; Mana Vault; Mox Amber; Mox Diamond; Mystic Remora; Rhystic Study; Smothering Tithe; Sol Ring; Survival of the Fittest; Swift Reconfiguration

**Out vs v8:** Deathrite Shaman, Strix Serenade, Volatile Stormdrake, Gleaming Splendor, The Queen of Dale.
**In vs v8:** Avacyn's Pilgrim, Spellseeker, Thassa's Oracle, Demonic Consultation, Tainted Pact.

## 15. Limitations and disclosures

- **No opponent model.** Goldfish conversion is necessary-not-sufficient for winning. The value of cut cards that act
  on opponents (theft, Strix, policing) is invisible by construction and is handled qualitatively and through the
  census, never by inventing a number.
- **Not modeled:**
  - Rhystic Study / Mystic Remora / Tymna draws, beyond the "engine_draws" band.
  - Sylvan Library and Seedborn Muse.
  - Combat (other than Finale, which is labelled non-deterministic).
  - Delney's combat clause.
- **Exotic Orchard** is assumed to tap for any colour.
- **Gilded Goose** is over-credited (§3.3) and excluded from the choice.
- **Census:**
  - The TopDeck archive covers only ~3 months (2026-07-29 → 2026-10-26); the 6-month view is cedhstats.
  - Oracle lists include turbo shells; strata are reported so the confound is visible.
  - Card associations are not causal.
- **Sample sizes:**
  - 20,000 (packages), 15,000 (exact builds), 12,000 (dork and Strix screens), 5,000 (single-card ablation),
    6,000 (sensitivity / keep policies).
  - States and scenarios use hundreds of states each, as given in §9/§11.5/§13.
  - All SEs are paired.
  - A first queue hit the 2-hour background limit during ablation; ablation, sensitivity and policy were rerun at the
    smaller n shown, and nothing was spliced.
- **Pareto frontier:** losses are additive approximations, and the chosen sets are then verified exactly.
- **Seeds:** BASE_SEED = 8,000,000; game *i* = seed + *i*; the seat rule is seed mod 4 = 0.

## 16. Artifacts

| File | Content |
|---|---|
| `results/solo_baseline/deckbuild008_oracle_package_audit.md` | this report |
| `deckbuild008_package_census.json` / `.csv` | TopDeck census, 8 populations, all statistics |
| `deckbuild008_census_cedhstats.json` | cedhstats 6-month / 1-month replication |
| `deckbuild008_variant_metrics.json` | every MC variant, sensitivity, keep policies, exact builds, provenance |
| `deckbuild008_cut_ablation.csv` | single-card contributions (both contexts) + role losses |
| `deckbuild008_pareto_frontier.csv` | non-dominated cut sets per package size and pool |
| `deckbuild008_conversion_surface.json` | CSA by state class, enabler, timing |
| `deckbuild008_tutor_graph.json` | direct / two-step access per piece per variant |
| `deckbuild008_tournament_scenarios.json` | log-derived and synthetic states with uncertainty labels |
| `deckbuild008_final_lists.json` | exact 98s + hashes for Builds 1–4 |
| `deckbuild008_work/*.json` | raw phase outputs (dork, strix, packages, marginals, sensitivity, policies, verify, states, scenarios) |
| `data/decklists/tymna-thrasios-creature-factory-deckbuild008-v1.json` | frozen baseline |
| `sim/analysis/deckbuild008_{cards,solver,goldfish}.py`, `build_deckbuild008_*.py` | code |
| `rules_tests/regression/test_deckbuild008_rules.py` | regression tests for every rules assumption |

**Reproduce:** `python3 sim/analysis/build_deckbuild008_experiments.py --phase <dork|strix|graph|packages|marginals|pareto|sensitivity|packages_policy|verify|states|scenarios|assemble> --n N`.
