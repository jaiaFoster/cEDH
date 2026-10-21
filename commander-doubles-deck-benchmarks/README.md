# Commander Doubles deck benchmarks — Batch1

**season0-proposed; unactivated; six new, unplayed 2HG adaptations. Batch2 awaits organizer review.** These are deliberately strong budget-constrained candidates, not assurances of Bracket3 play or proven globally optimal lists. No official schedule, previous research, rules or bans is changed.

Read [the spoken team profiles](batch1/organizer_audio_review.md) first. Then inspect [the six complete lists](batch1/decks/), [team plans and counterplay](batch1/team_synergy_and_counterplay.md), and [conditional early-turn demonstrations](batch1/opening_hands_and_goldfish.md).

| Team | Head1 | Head2 | Points | Transfer |
|---|---|---|---|---|
| A | Tymna/Kraum Blue Farm | Thrasios/Bruse Dawnwaker |72 +48 =120|12 to A1|
| B | Najeela Warrior Tempo | Derevi Bant Pod |55 +65 =120|5 to B2|
| C | Yuriko Ninja Tempo | Yuriko Big-Flip Topdeck Combo |60 +60 =120|0|

All six are independently legal100-card submissions in the pinned current paper Commander database, with correct partners/colors/singleton/bans. Teammates may repeat identities across their separate decks. No experimental unbans. Passing construction checks does not grant approval for gameplay patterns.

## Results worth reviewing

- One free Scheming Symmetry can put each head’s own Draco atop its own library. Two independent Yuriko connections then lose64 opposing shared life. A conditional turn3 hand/mana sequence is documented; its frequency was not measured.
- Derevi can untap the other head’s mana sources; Najeela then pays its **own** WUBRG and adds a shared combat. The turn4 Bear Umbra line is controller-checked and depends on continued connections.
- A1 retains a compact Oracle win and broad control; A2 retains multiple independently assembled mana engines plus command-zone Thrasios. Free Teferi/Kutzil and Chant3 make team protection inexpensive. Bruse cannot target A1’s creatures.
- A1 Force has33 other blue cards, B2 Force19, C1 Force51. B1 rejected Force with only11 other blue cards, reallocating one extra point to Demonic Tutor15. B2 is still a clear pitch-density tradeoff. Full raw-hand numerators are published.
- C1 and C2 have distinct99s and different card profiles. C2’s expensive flip package imposes real hand costs; no made-up average turn or success rate is supplied.

## Files

All generated review artifacts are in `batch1/`:

- `price_snapshot.csv`, `PRICE_SNAPSHOT.md`, `price_override_history.json`, `latest_organizer_overrides.json`, `scoring_config.json`, `provenance.json`:31,069 known paper Commander-legal identities, strict impact cutoff>77.5, inherited location exceptions and the17 later exact-location numeric overrides. Original50 qualitative anchors remain separate. Known unreviewed zeros are marked; unknown names are errors.
- `decks/A1.txt` through `C2.txt`: Moxfield-importable Commander/Deck text; corresponding JSON wraps Oracle-keyed `submitted_deck` plus source/version/checksum metadata. Text imports were locally round-tripped through the existing Moxfield-format parser; no claim of a live website import test.
- `score_ledger.csv`:600 individual card rows including all8 commander slots, actual-zone price and alternative-zone prices. `teams.csv`, `legality_report.csv`, `reports/*.json`: complete per-card scores, legality, transfer and budget results.
- `sources.csv`, `research/foundations.json`, `source_comparison.csv`, `source_card_changes.csv`, `archetype_lineage.md`:12 complete factual tournament registrations (two per head), six published Moxfield lists, author/pilot distinctions, exact retained/cut/added cards and source price gaps.
- `budget_tradeoffs.md`, `construction_revision_log.csv`: meaningful premium choices, the pitch audit and construction iterations. The revision log is our draft history; **actual ancestor differences** are in `source_card_changes.csv`.
- `team_synergy_and_counterplay.md`, `stress_test.csv`: roles, independent wins and eight conditional adversarial probes, including negative results. These were desk checks, not played matches.
- `rules_interactions.jsonl` and `.md`:22 controller-sensitive cases with canonical Oracle text/IDs/hashes, exact CR references, prerequisites, limitations and source edition. No automatic combo certification. The inherited commander-damage editorial discrepancy remains unresolved; no sequence here relies on exploiting it.
- `deck_profiles.csv`, `deck_construction_profiles.md`, `opening_hand_diagnostics.csv`, `opening_examples.json`, `sequence_resource_checks.json`: land/MDFC, pitch-color, mana-value and finite resource checks.50,000 uniform raw sevens per deck, fixed seed20261020; no mulligans, colored-mana solving, opponents or win simulation. Spell/land MDFCs cannot be spent twice. The arithmetic checker is not a Magic rules engine.
- `organizer_audio_review.md`: three120–180-word spoken briefings and allocation table.
- `artifact_hashes.json`: checksums for every generated review file, excluding itself and research inputs (which have separate provenance checksums).

## Reproduce offline

Run from the repository root. Tested with Python3.13.3, pandas3.0.6, NumPy2.5.4 and requests2.34.2. The generation/scoring commands do not call external services or require paid APIs.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r commander-doubles-deck-benchmarks/requirements.txt
.venv/bin/python commander-doubles-deck-benchmarks/build_batch1.py
.venv/bin/python commander-doubles-deck-benchmarks/build_batch1.py --check
.venv/bin/python -m unittest discover -s commander-doubles-deck-benchmarks/tests -v
.venv/bin/python commander-doubles-cutoff-recalibration/audit_tests.py
```

`--check` regenerates into a temporary directory and compares every generated byte. Do not change an output CSV directly: edit `deck_inputs.py` for a new proposed deck revision, document the reason, rebuild and rerun tests. Future organizer price changes require an explicitly versioned successor snapshot, not silently mutating these submitted totals. Fixed total assertions deliberately make that a review event.

Score/import/export one head or a team:

```sh
.venv/bin/python commander-doubles-deck-benchmarks/score_batch1.py commander-doubles-deck-benchmarks/batch1/decks/A1.txt --summary
.venv/bin/python commander-doubles-deck-benchmarks/score_batch1.py commander-doubles-deck-benchmarks/batch1/decks/B1.txt --deck-b commander-doubles-deck-benchmarks/batch1/decks/B2.json --summary --export /tmp/team-B.json
```

Defaults120 team /72 deck /60 reference /20% unused transfer. CLI allows explicit alternative budgets for diagnostics, never edits official prices. Exit0 means construction/legal pass,1 means failed legality/budget,2 means unknown/invalid input or mismatched frozen dependency. Full JSON reports carry proposed flags; `gameplay_legality_approved` stays false. The calculator verifies effective prices against the snapshot and the pinned full Oracle archive before scoring.

## Research provenance, access and refresh

Pinned base commit `db3b8e8ce97e789ee967398cfe6f024e677d2a60`. Prior directories are read-only dependencies for this branch. Frozen research facts are sufficient for offline regeneration; network scripts are optional source-refresh tools, **not part of routine reproduction**.

- TopDeck: reuse the repository’s previously acquired permitted archived registration/event snapshots in `data/tournament_snapshots/topdeck/`. `research_foundations.py` enumerates relevant pre-as-of events; `select_sources.py` freezes the selected exact factual lists and original snapshot hashes. No fresh bulk TopDeck access was required. A registration links to its actual event’s bracket/decklist container with pilot locator, not a fabricated individual permalink. Standings/records are as archived; ordinary Commander results do not belong to these 2HG decks. Pilot is not asserted original deck designer. One Dawnwaker registration is47th/54, explicitly disclosed.
- Moxfield: six public, unauthenticated deck v3 endpoints returned200 using a normal research user agent (`fetch_primers.py`). Only factual card/count, publication metadata and source references are committed. Full primer prose was unavailable (loading HTML; one tested primer endpoint404). Raw responses contain unnecessary copyrighted prose/profile/image metadata and remain ignored locally. Do not infer public-data bulk redistribution permission or scrape through restrictions. The collaborative tempo page is explicitly OUTDATED; DJCor/PKCore Dawnwaker is historical; JacobParis’s returned combo list has94cards and is labeled incomplete. Full valid source registrations supplement these limitations.
- Oracle: full38940-identity pinned archive in `commander-doubles-cutoff-recalibration/data/oracle_current.jsonl.gz`. Scryfall’s current bulk metadata was rechecked2026-10-20 and matches the pinned timestamp. Snapshot includes31,069 paper Commander-legal identities; banned/other known identities remain recognized by the underlying backend. See [Scryfall bulk docs](https://scryfall.com/docs/api/bulk-data) and original source attribution/terms; no claim to own card text.
- Rules: [official landing](https://magic.wizards.com/en/rules) still links the [Sept25,2026 CR](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt). Download hash matched the pinned archive at verification. The inherited October rulebreaker announcement/CR gap is recorded, not silently resolved. None of these lists uses that unsupported permission.
- Organizer: exact source is `organizer_premium_boundary_decisions_2026-10-20.md`, backed by all earlier calibration precedence. Latest17 override records preserve both original ledger numbers and actual baseline CSV numbers where those differ. We did not introduce a new point override to fit a deck.

For an explicit source refresh, inspect `verify_current_sources.py`, `fetch_primers.py`, `research_foundations.py` and `select_sources.py` first. Freshness checks fail if Oracle/CR changed; updating future editions needs a new version and controller/legality review. Do not rerun acquisition scripts as a way to claim inaccessible primers were read. No full-source prose or images are redistributed here; underlying game text, site data and event records retain their original rights.

## Validation scope

New suite17 tests; inherited recalibration suite38 tests. Export round trips,600-row sums, all17 overrides/all50 preserved qualitative anchors/other exact decisions/ranges, invalid colors/partners/singletons/bans/unknowns, budget edges, snapshot hashes, current-Oracle text and rule references, source completeness warnings, and controller/resource arithmetic are covered. A passing test suite does not prove a combo will survive opponents or validate a human interpretation as a tournament judge ruling. No actual paired games were played and no win rates were fabricated. All three teams are plausible high-power stress tests; organizer review and real games should determine whether they suit the intended league.
