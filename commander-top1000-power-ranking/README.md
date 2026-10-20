# Commander Top1,000 Power Ranking — candidate v0.1

A reproducible main-deck candidate ranking, separate command-zone ranking and sparse construction-price experiment. Earlier project directories are unchanged.

The principal CSV contains exactly1,000 rows; the full candidate inventory contains 9610 identities. 423 top1,000 rows remain explicitly low-confidence priors. The candidate pointed union contains 339 identities, not a claim that the exact ordering or a strict cap is validated. Banned cards retain banned status. No price/team synergy premium is added.

## Reproduction

From the repository root, using Python3.12+ (tested with3.13.3):

```sh
python -m pip install -r commander-top1000-power-ranking/requirements.txt
python commander-top1000-power-ranking/pipeline.py
python commander-top1000-power-ranking/test_backend.py
python commander-top1000-power-ranking/score_decks.py deck-a.txt --deck-b deck-b.txt --export team-report.json
```

These commands use existing frozen Oracle, precon, cache and TopDeck snapshots. They require no paid API and make no network requests. For a Moxfield list, use Commander/Commanders and Deck/Mainboard headers, or explicit --commander-a/--commander-b names. The previous parser is reused unchanged. Unknown names error; they never silently become zero. Sideboard/companion sections require explicit separate review.

The pipeline produces all CSV/Markdown/PNG outputs, analysis_summary.json and source_provenance.json. ranking_visualizations.png requires a writable Matplotlib cache. A read-only analysis can call analyse(...,render_plot=False), but that does not produce the PNG or save files.

## Editable policy and overrides

scoring_config.json holds version, rubric weights, specialist policy floor, price thresholds, tier bands and prior constants. analyst_assessments.json holds independent main/CZ rubric judgments and rationale. Modify either and rerun; preserve prior versions when a league starts.

Point overrides are Oracle-ID keyed, alternative by location:

```json
{"overrides":{"ORACLE-ID":{"main_deck_points":3,"command_zone_points":8}}}
```

Use an actual Oracle ID from the CSV. A full config is accepted with --config. Overrides do not legalize a banned card or create commander eligibility. Team and individual caps are optional CLI parameters; none is empirically calibrated here. Scores are integer construction resources, not win probabilities. Existing HTML calculator is preserved; score_decks.py is the new offline backend interface.

## Files and caveats

Read card_ranking_methodology.md, point_cutoff_analysis.md and benchmark_analysis.md first. proposed_point_schedule.csv includes all pointed command-zone cards even outside the main top1,000. candidate_inventory.csv includes low-confidence evaluated candidates that missed the1,000. experimental_unban_ranking.csv is hypothetical research only. omission_audit.csv and manual_review_queue.csv expose unresolved work.

Source provenance includes current URLs, retrieval/snapshot date and local SHA-256. Existing source notices continue to apply: card text is Wizards material; MIT code/cache source notices are retained in prior directories; Canadian Highlander publication is expert reference, not an invented blanket open-data license; TopDeck.gg attribution is required. No restricted EDHREC bulk scraping or proprietary evaluator extraction was performed.

The independent rules review is qualitative. The backend checks deck size, commander eligibility/pairing, color identity, singleton/basic-type restrictions and present bans. It is not a complete rules engine, judge certification, companion validator or gameplay simulator. Pregame color-choice commanders are flagged for unresolved input. Update current Oracle/rules/ban snapshots before a league release; do not silently mutate a running list.

## Active configuration and final review

{
  "version": "top1000-v0.1-candidate",
  "main_threshold": 75,
  "commander_threshold": 75,
  "curve": "tiered"
}

Start with executive_summary.md. Run `python commander-top1000-power-ranking/verify_artifacts.py` after reproduction. See THIRD_PARTY_NOTICES.md, independent_review.md and two_headed_giant_rules_review.md for the audit scope and rules caveats. The source-name aliases encountered in this sample are shared by ingestion and the CLI; additional flavor/interchangeable names may require a verified mapping. source_exclusions.csv lists excluded records without player names. representative_deck_breakdowns.md explains the five difficult precons, with complete reports in JSON.

A ready-to-run example uses two actual archived precons:

```sh
python commander-top1000-power-ranking/score_decks.py commander-top1000-power-ranking/examples/explorers_of_the_deep.txt --deck-b commander-top1000-power-ranking/examples/necron_dynasties.txt --team-cap 30 --export team-report.json
python commander-top1000-power-ranking/test_cli.py
```

proposed_legal_point_schedule.csv contains only currently eligible league card identities; proposed_point_schedule.csv additionally retains explicitly marked hypothetical banned-card prices. A card-list legality flag does not replace the independent deck/pair legality checks.
