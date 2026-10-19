# Commander card-power research v1
Executed research and engineering sprint, 2026-10-19. Dedicated branch: commander-card-power-research-v1. The previous calibration directory is unchanged.

Start with [benchmark_analysis.md](benchmark_analysis.md), [recommended_scoring_architecture.md](recommended_scoring_architecture.md), and [source_research_report.md](source_research_report.md).

## Reproduce
From the repository root, Python 3.13 was used:

```sh
python3 -m venv .venv
.venv/bin/pip install -r commander-card-power-research-v1/requirements.txt
.venv/bin/python commander-card-power-research-v1/run_benchmarks.py
.venv/bin/python commander-card-power-research-v1/build_reports.py
.venv/bin/python -m unittest discover -s commander-card-power-research-v1 -p 'test_*.py' -v
```

Those steps use committed inputs and need no paid API or network. The original calibration directory must remain alongside this directory because its Oracle and precon snapshots are the benchmark inputs.

Optional source refresh (changes the acquired snapshot; inspect diffs and commit a new version):

```sh
.venv/bin/python commander-card-power-research-v1/acquire_research.py
```

The source cache is a pickle. Our importer rejects executable global and persistent references, validates primitive records, and converts the data to JSON. Ordinary benchmarks read JSON. Do not replace this with unrestricted pickle.load on downloaded files.

Optional live Spellbook refresh, subject to the official documented sparse-use policy:

```sh
.venv/bin/python commander-card-power-research-v1/run_spellbook_checks.py
.venv/bin/python commander-card-power-research-v1/build_reports.py
```

Analyze a deck with explicit Commander/Main sections:

```sh
.venv/bin/python commander-card-power-research-v1/spellbook_integration.py deck.txt --output combos.json
.venv/bin/python commander-card-power-research-v1/spellbook_integration.py deck-a.txt --team-b deck-b.txt --output team-candidates.json
```

The client uses the neighboring frozen Oracle dataset, rejects unknown names, ignores comments, normalizes printing annotations, and refuses side/maybeboard sections. Commanders must be identified explicitly; the prototype does not guess commander roles from legendary cards. The two-deck command checks candidate components only and does not validate a legal 100-card team deck, controller sharing or combo functionality.

## Deliverables
- source_inventory.csv: 42 curated source entries with access, terms, scope, uncertainty and review depth.
- source_research_report.md: detailed reviews, excluded/blocked methods, expert versus community evidence.
- recurring_data_sources.md: authorized refresh and snapshot architecture.
- scoring_methods_comparison.md: nine executed controls/candidates and inverse-model reasoning.
- benchmark_results.csv: 174 rows per method; blank full score if any card is missing; separate known subtotal.
- benchmark_analysis.md: correlations, intervals, cohorts, difficult cases, sensitivity and limitations.
- card_scoring_candidates.csv: Oracle-ID evidence table; external candidates do not overwrite league prices.
- spellbook_integration.py and spellbook_integration_report.md: working client, live results and cross-team caveats.
- recommended_scoring_architecture.md: direct answers and rollout recommendation.
- data/: frozen source seed, benchmark parameters, raw licensed code/data, manifests, metrics and live response fixtures.

data/initial_benchmark_results.json is the historical pre-cache exploratory run. Its partial diagnostic correlations are superseded by data/benchmark_metrics.json, which restricts validation to complete deck coverage and records the usable sample size.

Manual point overrides remain in the original calculator's versioned scoring configuration. This research does not alter that configuration or the existing score database. Any future accepted override must be global per Oracle ID and documented; changing a score must not silently legalize a card.

## Sources and licenses
Source URLs and pinned Git commits are in data/acquisition_manifest.json. The 42-entry catalog carries 2026-10-19 review dates; metadata-only leads are labeled. Static research annotations are curated evidence, not automatically measured facts. The source catalog is rebuilt from data/source_inventory_seed.json.

Third-party notices are retained under data/raw/<project>/LICENSE or LICENSE.txt and summarized in THIRD_PARTY_NOTICES.md. MIT code is not a blanket license to all upstream services' data. No restricted EDHREC scraping, undocumented hosted evaluator API, paid model invocation or CommanderSalt workaround was used.

The original benchmark inputs include community rankings with source provenance in the neighboring calibration directory. Added five within-year comparisons are documented in the statistical report; they are opinions, not win-rate data. We do not force scores to 1,000 or normalize each year.
