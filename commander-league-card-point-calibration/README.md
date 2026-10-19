# Commander doubles card-point calibration

This executed study audits official paper precons and supplies an editable, deterministic card index. **Version 0.2 fails its small independent deck-strength validation. Use it for shadow scoring and manual refinement, not a binding league cap.** The 1,000-point Bracket 3 / 2,000-point team budget remains a design anchor, not a measured calibration.

## Start here

Open `precon_statistical_report.md` for actual results, annual statistics, 20 highest and 20 lowest decks, six representative breakdowns, validation failures, sensitivity, sources and recommendations.

Double-click `commander_doubles_calculator.html` to use the offline calculator. It embeds the complete retrieved Oracle catalog and needs no server, account, network or paid API. It has two deck inputs, commander/partner identification, configurable caps, normalized names, legality/singleton/color warnings, provisional estimates, top contributions, JSON overrides and report export. A partial known-card subtotal is labeled INCOMPLETE when names are unknown. It never accepts missing cards as zero-priced legal cards.

## Main outputs

* `commander_card_scores.csv`: one row per downloaded Oracle ID, including nonlegal records; filter `legality == legal` for the ordinary Commander pool. Numeric components are intermediate role estimates, not additive final charges. Floors, top-two-role selection, efficiency and overrides are explained in the report.
* `commander_precon_scores.csv`: deduplicated original paper lists with score, source, commander, percentile, release data, construction diagnostics and flags.
* `precon_statistical_report.md`: complete executed analysis and caveats.
* `precon_score_distributions.png`: overall and historical distributions.
* `commander_doubles_calculator.html`: self-contained local calculator.
* `experimental_unban_review.csv`: official named bans, category-banned Oracle cards and Lutri's companion-only restriction. `proposed_points` are separate hypothetical reserves; `legalized` is always false. All 42 individually named bans, including the seven requested cards, have individual functional and 2HG assessments from Oracle text. Price magnitudes remain analyst policy priors. Unreviewed rows are expressly provisional, defaulting to retain the ban.
* `scoring_config.json`: editable parameters, patterns, policy thresholds and overrides.

## Reproduce

Run from this directory with Python 3.11+ and Node.js 18+:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python acquire.py
.venv/bin/python pipeline.py
.venv/bin/python -m unittest -v test_pipeline.py
```

The analysis has already been run; execution is not left to the reader. `requirements.lock.txt` records the environment used for this run. `acquire.py` clones the taw source when absent and downloads only missing snapshots. `pipeline.py` runs without network access once snapshots exist. It writes every requested analysis output. The seeded bootstrap is deterministic with the recorded package versions; rendering fonts/platform differences can change PNG bytes.

`data/raw/source_manifest.json` contains source URLs, retrieval timestamps, SHA-256 hashes, bulk update timestamp and pinned taw commit. Cached snapshots are not silently refreshed. To make a later study, copy this directory, version the scoring configuration, deliberately replace the snapshots, and rerun acquisition and tests. Never mix new Oracle data with a claimed old snapshot. `bulk_index.json` can advertise either JSON bulk downloads or gzipped JSONL; both are supported. The downloaded Oracle JSONL is retained compressed to save space.

## Edit card prices

Do not edit a generated CSV as the authoritative source: the next pipeline run replaces it. Edit `scoring_config.json` instead. An override maps an Oracle ID (preferred) or exact canonical name to a nonnegative integer, or an object containing `points` and `reason`:

```json
{
  "overrides": {
    "6ad8011d-3471-4369-9d68-b264cc027487": {
      "points": 70,
      "reason": "League review: opening-hand acceleration",
      "evidence": "Local pilot testing; review date and sample size here"
    }
  }
}
```

Merge entries into the existing overrides object to preserve the other reviewed anchors. Oracle-ID overrides take precedence over name overrides. Absolute overrides replace the whole automatic estimate before the single global multiplier; they do not add to it. The shipped multiplier is 1.0. Keep points integers. Every change applies identically to every printing and deck. Card power is never multiplied by release year. `commander_adjustment` is reserved at zero; a nonzero commander surcharge is not implemented or validated.

After config edits, rerun `pipeline.py` and tests so the CSVs, report and embedded calculator remain synchronized. `base_points` and `automatic_estimate` expose the manual replacement. `override_delta` is the difference, not another charge. Confidence distinguishes assessed function from uncertain price magnitude. Automatic estimates are low-confidence, including zero or low prices for cards the regex cannot understand.

In the HTML, import a full `scoring_config.json` or a direct JSON mapping such as `{"Sol Ring":70}`. Imports **replace** the session override map; invalid/unknown/fractional/negative entries reject the whole import. This affects prices only. It does not unban anything, change the embedded role weights, or write back to disk. Export overrides before closing. To persist a calculator-imported override in the analysis, merge its mapping into config's `overrides` object and regenerate. Avoid defining the same card both by name and ID; ID wins in Python.

## Decklist input

```text
Commander
1 Hakbal of the Surging Soul

Deck
1 Sol Ring (LCC) 313
1 Arcane Signet
...
```

Use a Commander section, Moxfield's `[Commander{top}]` marker, or the separate commander field. Separate partners with `;`. The separate field adds a commander only if it is absent from the pasted list; it does not silently add a second copy. Mainboard cards and commanders together must total 100. Quantities, printing suffixes, curly apostrophes and exact face aliases are normalized. Known full names take precedence over face aliases, and playable cards over identically named tokens/art-series objects. `(Prepared)` suffixes are accepted as printing-style annotations. Sideboard/maybeboard/companion entries are explicitly excluded and warned about. No companion rules are fully adjudicated; Lutri as companion remains banned.

Partner pairing has checks for generic Partner, named partners, Friends forever, Doctor's companion and Backgrounds. Novel pairing mechanics still require review. Deck warnings are checks, not a full rules engine: card-specific deck-count exceptions, conditional commander eligibility, combos, mass land denial and turn-speed intent need human review. The app does not infer a bracket from points. Caps constrain only arithmetic, and a warning prevents presenting a deck as fully checked. Teammate card overlap is allowed; no unified construction or synergy penalty is imposed.

## Intermediate datasets and audits

`data/clean/precons.json` retains original product records, original and canonical names, all source printing entries, an expanded 100-ID list, main/command sections, counts, original release dates and quality flags. `deck_aliases.csv` preserves collapsed reprints and Collector's Editions. `excluded_records.csv` accounts for every other source record and gives reasons. `schema_audit.json` inventories all observed top-level and card-entry keys/types.

`coverage_audit.json` compares taw's paper Commander inventory to MTGJSON's published DeckList inventory. They share upstream information; this is not an independent 100-card content verification. `deck_quality_audit.csv` checks all 198 paper product records before deduplication. Upgrades Unleashed has the official two-Mossfire-Valley printing error, preserved and flagged. Historical Political Puppets and Mystic Intellect include currently banned cards; they remain in the historical precon population but outside Core candidates. Introductory, premium, GC-bearing, nonlegal and quality-exception cohorts are separated. Absence of a Game Changer does not certify Core.

`deck_card_points.csv`, `annual_statistics.csv`, `summary.json`, `composition_regression.csv`, `card_contributions.csv`, `validation.csv`, `reddit_validation.csv`, `sensitivity.csv` and `card_perturbations.csv` preserve the underlying calculations. `game_changer_reconciliation.json` checks official October 2025 names plus February 2026 additions against Scryfall flags. `legality_reconciliation.json` records named-ban matches versus broader Oracle category bans. Complete nonlegal Oracle objects in the card CSV should not all be confused with individually named Commander bans.

## Research limits and engineering verification

Official sources define legality and bracket guidance. EDHREC and Reddit assessments are opinion labels and are never described as measured card strength. Direct Reddit HTTP downloads were challenge responses; the validation original post was read via web search/browser text. Moxfield returned an app shell. TopDeck and Spellbook were consulted for data scope; no standardized casual/2HG outcome dataset was obtained. URLs and access status are preserved. No win rates are invented.

Automated tests independently sum all deck/card rows, verify complete Oracle coverage and integer scores, check exact sizes and known duplicate exception, prove printing/year invariance, reconcile named bans, and run the shared JavaScript engine against every precon. Additional parser tests cover unknown names, sideboards, suffixes, commander counting, duplicates, banned cards and invalid overrides. A DOM harness exercises the actual embedded HTML script and its score/import/export controls without making network calls. The distribution PNG was visually inspected. Browser visual QA of the local HTML was blocked by the browser tool's file-URL policy; no browser rendering pass is claimed.

This code uses functional text patterns, not a semantic Magic rules interpreter. Its weak held-out rank correlation and specific engine/tribal errors are material findings. Card coefficients remain policy priors, and bootstrap intervals condition on them. A strict league cap requires a better reviewed card taxonomy and independent gameplay evidence.
