"""Generate statistical reports from executed artifacts and curated source annotations."""
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def table(frame):
    def show(value):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return "—"
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value).replace("|", "/").replace("\n", " ")
    header = "| " + " | ".join(map(str, frame.columns)) + " |\n"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |\n"
    return header + rule + "\n".join("| " + " | ".join(show(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None))


def main():
    catalog = json.loads((ROOT / "data/source_inventory_seed.json").read_text())
    with (ROOT / "source_inventory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(catalog[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(catalog)
    metrics = json.loads((ROOT / "data/benchmark_metrics.json").read_text())
    scores = pd.read_csv(ROOT / "benchmark_results.csv")
    annual = pd.read_csv(ROOT / "data/annual_distributions.csv")
    candidates = pd.read_csv(ROOT / "card_scoring_candidates.csv")
    primary = scores[(scores.method == "zarzak_cached_llm") & scores.complete]
    summary = []
    for method, data in metrics["methods"].items():
        summary.append({"method": method, "complete decks": data["complete_decks"],
            "EDHREC n": data["edhrec6"]["n_complete"], "EDHREC rho": data["edhrec6"]["spearman"],
            "EDHREC tau": data["edhrec6"]["kendall"], "EDHREC pair accuracy": data["edhrec6"]["pairwise_accuracy"],
            "Reddit n": data["reddit5"]["n_complete"], "Reddit rho": data["reddit5"]["spearman"],
            "Reddit tau": data["reddit5"]["kendall"], "Reddit pair accuracy": data["reddit5"]["pairwise_accuracy"],
            "new pair accuracy": data["new_pair_accuracy"], "new complete pairs": data["new_pairs_complete"]})
    pd.DataFrame(summary).to_csv(ROOT / "data/method_metrics.csv", index=False)
    difficult = pd.read_csv(ROOT / "data/difficult_cases.csv")
    sensitivity = pd.read_csv(ROOT / "data/price_sensitivity.csv")
    inverse = pd.read_csv(ROOT / "data/inverse_emulation.csv")
    missing = pd.read_csv(ROOT / "data/missing_precon_ratings.csv")
    land = pd.read_csv(ROOT / "data/land_contributions.csv")
    intervals = []
    for method, result in metrics["methods"].items():
        for sample in ("edhrec6", "reddit5"):
            item = result[sample]
            intervals.append({"method": method, "sample": sample, "n": item["n_complete"],
                "bootstrap95 rho": str(item.get("spearman_bootstrap95", "not estimated"))})
    m = metrics["methods"]["zarzak_cached_llm"]
    basic_names = ["Mountain", "Plains", "Island", "Wastes", "Forest", "Swamp"]
    basic = candidates[candidates.name.isin(basic_names)][["name", "zarzak_cached_llm", "zarzak_basic_equalized"]]
    report = f"""# Executed benchmark analysis
Research and snapshot date: 2026-10-19. No values were fitted to reviewer labels. Baseline files remain unchanged.

## Coverage and score meaning
The frozen baseline has {metrics['n_decks']} decks and {metrics['n_precon_oracle_cards']:,} distinct Oracle IDs. Nine methods/controls were executed, producing {len(scores):,} deck-method rows. A complete score is emitted only when all 100 entries have a defined value. Incomplete methods retain a diagnostic known-card subtotal and a blank score.

The published cache contains {metrics['cached_names']:,} names. It matches {metrics['cached_names_matched_oracle']:,} cards in the frozen Oracle snapshot, including {m['covered_precon_oracle_ids']:,} precon IDs. Unique first-face aliases resolve the two meld cards; all other missing ratings remain missing. It fully scores {m['complete_decks']} decks and leaves {174-m['complete_decks']} incomplete. The 35 missing precon IDs are listed in data/missing_precon_ratings.csv. Coverage gaps include older AFR cards, banned cards and newer products: they are not merely recency gaps.

Among its {len(primary)} complete decks, the raw cache has median **{primary.score.median():.1f}**, mean {primary.score.mean():.2f}, sample SD {primary.score.std():.2f}, IQR {primary.score.quantile(.75)-primary.score.quantile(.25):.2f}, and range {primary.score.min():.0f}–{primary.score.max():.0f}. These are sums of source 0–100 judgments, not calibrated league points. No 1,000-point anchor, per-deck normalization or per-year normalization was used. The median subtotal including incomplete decks is {m['median_known_subtotal']:.1f}; it must not be confused with the complete-deck median.

The Canlander and Game Changer controls define unlisted cards as zero by policy. That definition is different from assuming that an unknown external rating is zero. Creature and adoption subtotals do not yield a complete deck-price model.

## External opinion comparisons
{table(pd.DataFrame(summary))}

Higher scores are compared to lower reviewer rank numbers. Pair accuracy gives ties half credit. The EDHREC sample contains six decks, the original Reddit sample five. For the cached source only four Reddit decks are complete: Exit from Exile is missing Danse Macabre. Its reported +0.400 is therefore a four-deck result and is not directly comparable to another method's five-deck +0.400. The preliminary +0.300 using five partial subtotals is explicitly superseded and is not a valid full-coverage result.

Added evaluation: five within-year pairs (2021–2025), ten decks, from Josh Nelson's [best](https://edhrec.com/articles/the-five-best-commander-precons-of-the-last-five-years) and [worst](https://cloudflare.edhrec.com/articles/the-five-worst-commander-precons-of-the-last-five-years) articles. They are not one ten-deck ordering. Theme/value and power are mixed in editorial assessments, and different reviewers disagree. These pairs were frozen before acquiring the new cache; no weights or individual prices were optimized on them. Public reviews could nevertheless be represented in an LLM's training, so strict training-set independence cannot be established.

{table(pd.DataFrame(m['new_year_matched_pairs']))}

Four/five is promising but weak evidence: one changed opinion changes accuracy by 20 percentage points. It is not a win-rate estimate or statistically established superiority. The raw cache still puts Painbow 565 points above Necron Dynasties.

## Bootstrap and sample sensitivity
Paired deck bootstrap, 1,500 resamples, seed 20261019, percentile intervals. Degenerate resamples are omitted. Small samples, ties and repeated observations make these intervals unstable; they describe conditional opinion-sample variation, not actual competitive strength uncertainty. In sparse controls, even an apparently one-sided interval is driven by very few score levels.

{table(pd.DataFrame(intervals))}

Leave-one-out rank ranges are in data/sample_sensitivity.csv. The validation samples share some products; do not sum pair counts as independent games. No standardized Commander outcome dataset or 2HG outcome dataset was obtained. Archetype conclusions are individual error cases, not powered subgroup estimates.

## Required difficult cases
{table(difficult[['deck','baseline_v02','xmage_card_adapter','zarzak_cached_llm','zarzak_basic_equalized','zarzak_cached_llm_covered_cards']])}

Mutant Menace and Science! differ by only one raw-cache point despite their large gap in one reviewer ordering. Tribal/synergy-driven Necron Dynasties remains underrated by the added review comparison. Explorers of the Deep also demonstrates why synergistic tribal performance need not be captured by individual standalone prices. From Cute to Brute is the highest complete raw-cache deck, which may partly reflect individual staples and nonbasic mana rather than coherent deck performance. The league intentionally permits synergy to exceed its construction price; these errors are relevant without implying a synergy surcharge is desirable.

## A disqualifying card-level consistency problem
{table(basic)}

Thirty Swamps versus thirty Mountains differ by **1,200 raw points**, far more than one Sol Ring at 98. These prices cannot be deployed without review. The equalized-basic control fixes rated basics at 30 globally as an explicit color-neutral assumption. It is a sensitivity diagnostic, not an empirically fitted or accepted replacement. Snow/other basic lands also use the same rule when rated; missing cards remain missing.

Basic equalization changes the six-deck Spearman from +0.200 to {metrics['methods']['zarzak_basic_equalized']['edhrec6']['spearman']:+.3f} and added-pair accuracy from 4/5 to {metrics['methods']['zarzak_basic_equalized']['new_pair_accuracy']*5:.0f}/5. The seemingly better raw result is therefore sensitive to an implausible land convention. This does not establish a causal explanation for every ranking error, but it weakens any claim that 4/5 validates the source. Summing an anchored 0–100 judgment scale also assumes cardinal differences and additivity; those assumptions have not been outcome-calibrated.

Land points are not neglected by the cache: median collective land fraction is {land.land_fraction.median():.3f} among complete decks. Detailed contributions are in data/land_contributions.csv. A large land share alone is not evidence of correct land pricing. Source values also omit Dockside Extortionist, Jeweled Lotus, Primeval Titan and Prophet of Kruphix; those remain missing, never silently legal or zero.

## Historical behavior
Statistics below use complete raw-cache decks only. Counts show both total cohort size and complete coverage. Missingness can bias recent and older comparisons. Release year is explanatory, never a card-price modifier. Same Oracle ID always keeps the same source value.

{table(annual[annual.method=='zarzak_cached_llm'].drop(columns='method'))}

All method/cohort statistics are in data/annual_distributions.csv. The baseline's annual medians run from 772 in 2011 to 939 in 2026, but a flawed price model cannot establish actual power creep. Neither this trajectory nor the external cache proves a change in observed win probability. Product composition, land pricing, identity coverage and source bias require resolution before interpreting cohort trends causally.

## Exact price sensitivity
Among complete raw-cache decks, adjust one globally fixed price by ±20, recompute totals, and compare ranks. No deck-specific normalization or refitting is performed.

{table(sensitivity)}

Near-universal Sol Ring provides almost no information about its relative coefficient from precon totals alone. A team or deck interaction premium is absent throughout. Stability under a staple edit does not validate the underlying prices. The basic-land control is a stronger structural perturbation than a small staple edit.

## Additive inverse problem: executed chronological holdout
Matrix rank {metrics['matrix_rank']}; nullity at least {metrics['nullity_lower_bound']:,}; {metrics['cards_appearing_in_one_deck']:,} one-deck cards; {metrics['identical_column_groups_gt1']} multi-card identical-column groups containing {metrics['cards_in_identical_column_groups']:,} cards. We cannot recover unique individual prices from these totals.

Ridge labels below are permitted raw-cache additive sums, not a hosted evaluator or independent power measurement. Train through 2023, test complete 2024–2026 decks. Alpha values are declared diagnostic settings; none is chosen using reviewer labels.

{table(inverse)}

Poor future-deck emulation and many negative coefficients illustrate the problem even when the labels were generated by a truly additive function. Ridge is not promoted to card prices. NNLS/nonnegative priors could constrain signs but cannot eliminate the null space. Nonlinear external evaluators would add another approximation error.

## Highest and lowest complete source totals
These are rankings under the raw source, not claims of actual strongest/weakest decks.

### Highest 20
{table(primary.sort_values('score',ascending=False).head(20)[['deck','release_year','score']])}

### Lowest 20
{table(primary.sort_values('score').head(20)[['deck','release_year','score']])}

## Decision
Keep the baseline and original calculator intact. The published cache saves substantial initial annotation work, but basic-land inconsistencies, missing cards and weak/conflicting validation prevent direct adoption. Use it as a reviewable prior, not a mathematical proof of relative power. Expand independent unseen deck/pod evidence before a strict cap. The additive-only design has a structural gap from holistic deck strength that is consistent with the league's chosen philosophy; no numerical ceiling on agreement can be estimated from these samples.
"""
    (ROOT / "benchmark_analysis.md").write_text(report)
    live = json.loads((ROOT / "data/spellbook/summary.json").read_text())
    rows = []
    for entry in live:
        if "categories" in entry:
            rows.append({"deck": entry['deck'], "included": entry['categories'].get('included',0),
                         "almost": entry['categories'].get('almostIncluded',0),
                         "almost with extra colors": entry['categories'].get('almostIncludedByAddingColors',0),
                         "identical repeat": entry['deterministic_repeat']})
    spell = f"""# Commander Spellbook integration: executed results
Official [API documentation](https://spacecowmedia.github.io/commander-spellbook-backend/api.html), [backend](https://github.com/SpaceCowMedia/commander-spellbook-backend), [website](https://commanderspellbook.com/). Data credited to Commander Spellbook.

## Live tests
Five full precons were submitted by Oracle ID to POST /find-my-combos/?limit=1000 on 2026-10-19. Each request was repeated once. All succeeded and all repeats matched exactly at this snapshot. This does not guarantee future database stability.

{table(pd.DataFrame(rows))}

Science!'s included variant is [2047-6465](https://commanderspellbook.com/combo/2047-6465/): James, Wandering Dad // Follow Him plus Mechanized Production. The API describes casting Follow Him while an upkeep trigger is pending, with up to ten mana plus possible commander tax and relevant battlefield setup. The outcome is Win the game. A component match does not prove early access, valid attachment, sufficient mana, successful timing or resistance to interaction. We flag a potential win outcome and leave early-win status unestablished.

The other four precons have no included variants in this snapshot. That means no recognized included variant was returned, not proof they contain no combo, no lock or no potent synergy. Almost matches retain missing-component/color/commander categories. No bracket label was used as strength validation, and the bracket-estimation endpoint was not benchmarked.

## Cross-team positive control
A two-card fixture splits Exquisite Blood and Sanguine Bond between hypothetical players. API variant [690-3966](https://commanderspellbook.com/combo/690-3966/) is included in the union. The prototype marks cross-deck components required, controller review required, and functionality unverified. This fixture is not a legal complete deck or evidence that all union-detected combinations work across controllers.

Check who controls each trigger, what “you” refers to, affected opponents, zones, ownership, mana, commander access and 2HG replacements/rules. Components may need one controller or transfers not present in either list. A union can generate false positives; it is a candidate generator only. No cross-controller rules solver is implemented.

## Client behavior
Local names are resolved against the complete frozen Oracle snapshot; unknown names raise an error rather than being silently dropped by the API. The CLI supports explicit Commander/Main sections, printing annotations and two deck files. It retains required component quantities, zones, templates, commander requirements, prerequisites, mana, outcomes, variant IDs and links.

Response partitions distinguish included, commander-role changes, near matches and added-color cases. Included variants with templates or concealed/null prerequisites remain unresolved. Even the component_complete label means only complete components, never executed gameplay. Template/executable state resolution and natural-language prerequisites are manual.

Potential win/lock/mass-land-denial flags use outcome wording as a conservative review aid. They are incomplete heuristics, not a comprehensive legality classifier. Mana value needed is not a win-turn prediction. Unsupported or unusual situations retain raw API fields. Every record has construction_point_adjustment=0.

Timeouts, named User-Agent, bounded 429/502/503/504 backoff, safe pagination hosts and pagination-cycle checks are implemented. Pagination preserves the POST body. API schema changes fail explicitly rather than silently making an empty success. Ten unit tests exercise client behavior; eight additional research tests verify identity, missing data, safe pickle decoding, additivity, basic-land consistency and the absence of combo point surcharges.

## Limits and reuse
The browsable root advertised API 7.2.0; a cached variants view showed 7.1.9. Frozen raw responses and UTC retrieval times are retained in data/spellbook, with payload/response hashes. No sensitivity/specificity is claimed: our fixtures do not supply complete adjudicated true-positive/false-positive labels.

The official docs recommend sparse unauthenticated requests, a named User-Agent, about 80 requests/minute as a safe level, and backoff on 429. We used sparse requests. For full local indexing, use the documented https://json.commanderspellbook.com/variants.json.gz bulk artifact with timestamp/version/aliases, not REST pagination to export the database. That bulk artifact was researched, not downloaded in this sprint.

The backend code is MIT and its full notice is retained. API documentation permits consumption and asks for credit/linking; an independent blanket data-redistribution license was not conclusively verified. Do not interpret MIT code licensing as automatically covering every third-party datum. Popularity is supplied by EDHREC and is not an independent card-strength measurement. No combo degree, salt, bracket or popularity feature is added to construction prices.
"""
    (ROOT / "spellbook_integration_report.md").write_text(spell)
    print("Generated source inventory and two statistical/live-integration reports")


if __name__ == "__main__":
    main()
