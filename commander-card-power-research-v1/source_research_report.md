# Commander power research sprint
Research date: 2026-10-19. Repository baseline: commander-league-card-point-calibration at 01ced67d322f0898b4eb968df76b9c03881c65f0.

## Scope and evidence standard
The inventory contains 42 source entries, including related projects and multiple assessments from the same publisher. These are not 42 independent power measurements. Nine entries received technical review; the remaining entries range from documentation review to explicitly marked discovery leads. Unknown access, licensing, coverage and validation fields remain unknown. No source was treated as a measured card-strength database merely because its interface prints a number.

The baseline contains 174 decks spanning 2011–2026. This sprint reuses that frozen cohort; it does not certify that it is the complete population of all Commander products. Source code, allowed data, frozen inputs and checksums are retained. No paid model calls were made.

## The strongest discovery: a reusable intrinsic-power cache
[zarzak/mtg-deck-builder](https://github.com/zarzak/mtg-deck-builder) publishes an MIT-licensed scorer and a committed cache. We downloaded and safely decoded 32,075 cached names. The source rubric asks for commander-independent, standalone power on an integer 0–100 scale. Price, rarity and popularity are explicitly excluded from the prompt; the contextual synergy scorer is a different component.

The scorer uses claude-sonnet-4-6, batches up to 100 cards, temperature zero, explicit score-band anchors, and a model-specific cache keyed by name and a 16-character card-text hash. Cached snapshots are deterministic; a new model invocation is not guaranteed to recreate them. The cached value does not include a written justification, confidence interval, replicate agreement or outcome-derived calibration. The implementation does not put the rubric itself in each card's cache hash, so rubric/version changes need additional invalidation in our pipeline.

Exact-name matching plus unique first-face aliases for meld cards maps 6,394 of 6,429 precon Oracle IDs and fully covers 164 decks. The 35 remaining precon IDs stay missing. No values are inferred from their names. Current Oracle-text freshness has not been verified against the exact upstream MTGJSON-to-Card formatter; the upstream text hash is retained rather than mislabeled as a Scryfall hash.

This is a usable research prior, not a ready league price list. The cache assigns Mountain 10, Plains/Island/Wastes 30, Forest 40 and Swamp 50. Thirty Mountains versus thirty Swamps therefore differ by 1,200 points before any spells. That inconsistency alone rules out directly adopting the raw cache. Command Tower is 92 and Temple of the False God 52. Commander-dependent land applicability also needs review. The observed medians near 5,000 are simply sums of its 0–100 ratings; they do not establish a league scale.

The root MIT notice is retained with the downloaded cache and source. No separate cache restriction was found in the inspected repository. This does not remove Wizards' rights in card text or imply that third-party community data used by other parts of that deckbuilder is freely reusable. We did not use its EDHREC collection code.

## Technical evaluations
### Commander Spellbook
[Official API documentation](https://spacecowmedia.github.io/commander-spellbook-backend/api.html), [MIT backend](https://github.com/SpaceCowMedia/commander-spellbook-backend).
The REST API exposes cards, features, templates, variants, aliases, find-my-combos and estimate-bracket. The documented bulk variant file is the appropriate mechanism for large local combo analysis; exporting the database by paginating REST is explicitly discouraged.

We inspected request parsing, variant models/serializers and find-my-combos. Card inputs accept Oracle identifiers. Unknown names may be dropped server-side, so our client validates every name locally. Responses separate included components from variants missing cards, colors or commander roles. Templates, zones, mana and textual prerequisites remain necessary execution conditions. Example variants can conceal detailed prerequisites and must remain unresolved.

Variant popularity is supplied by EDHREC; salt is perceived unpleasantness; bracket tags are curated categories. None is a validated continuous card-strength effect. A card's combo degree primarily measures combo-enabling and curation patterns. Charging every indexed combo would violate the league's intended synergy reward.

Five precons and a two-card cross-team positive control were tested live. Full results are in spellbook_integration_report.md. Separate data-redistribution terms are not conclusively established merely by the backend's MIT license. Official bulk consumption is documented; retain attribution and avoid assuming unlimited redistribution rights.

### XMage
[Source](https://github.com/magefree/mage), pinned source and MIT LICENSE.txt retained.
The inspected Commander evaluator has 57 text flags, weighted by category maxima, plus name lists for salt, combo pieces and an older Game Changers list. Its card component credits each listed combo piece by an additional fixed 18 regardless of whether the rest of a combo is present. Original commander-zone bonuses are excluded from our globally fixed adapter.

A cost-reduction test uses OR across the words cost/less/each and can mistake unrelated text for cost reduction. A draw test looks for a literal plural phrase and misses common singular phrasing. List staleness and Java-rendered rules versus Oracle text also matter. Our result is an Oracle-text adapter, not an exact run of native XMage. It provides a reproducible open-code control, not evidence that another regex heuristic solves card valuation.

### EDHPowerLevel
[About](https://edhpowerlevel.com/about/), [changelog](https://edhpowerlevel.com/changelog/).
Public output includes card impacts and deck scores, making the presentation close to the desired calculator. Published explanations and changes discuss demand, price, popularity, CMC and land treatment. These are not all independent-power measurements. No approved bulk scoring API, redistributable full ratings export or complete source implementation was verified. A third-party gist exposing constants is not authorization to reuse the publisher's service or data. No deck scores from this service were acquired.

### CommanderSalt
[Public issue tracker](https://github.com/commandersalt-com/commandersalt-issues-tracking).
The issue tracker is not the scoring source. Website extraction returned JavaScript shells, and direct browser access was denied during this session. We did not route around that denial. Older developer discussions describe tournament-informed scoring, but current formula, per-card export, license and approved batch API remain unverified. No live benchmark scores were obtained.

### EDHREC
[Terms](https://edhrec.com/terms).
The reviewed terms prohibit automated agents/scripts generating requests. We did not bulk scrape EDHREC or treat public-looking JSON endpoints as permission. Existing Scryfall-cached edhrec_rank was used only as a clearly labeled adoption diagnostic, not causal power. Salt, inclusion, contextual synergy/lift and global adoption are distinct variables. Multiple wrappers and Spellbook popularity do not provide independent corroboration of the same upstream statistic.

### Canadian Highlander
[Official points](https://canadianhighlander.ca/points-list/).
This is an actual fixed additive construction budget with expert-curated costs, but for a different 100-card singleton format. The retrieved list contains 46 pointed names. All unlisted cards cost zero by that format's definition, not because a missing power rating was silently imputed. Precons mostly tie at three, so it is useful as a sparse high-impact reference, not a comprehensive Commander pricing system. No broad open redistribution license was verified.

### AgentSamSA creature projects
[Current parser](https://github.com/AgentSamSA/mtg-mechanics-parser), [predecessor](https://github.com/AgentSamSA/Creature-Power-Creep-in-MtG).
Both repositories identify MIT licensing. The current parser uses structured ability segmentation and weighted features; its README distinguishes this from ML-based detection and lists drawbacks/DFC limitations. The published legacy CSV has 857 rows and 855 unique Oracle IDs; the two duplicate IDs have consistent values. It covers only 126 of our precon cards and no full deck. Its legacy processing lineage must not be conflated with ratings freshly generated by the current parser. Partial sums are diagnostic only. The two projects are one research lineage.

### Contextual and simulation projects
[LlamaAdam/commander-builder](https://github.com/LlamaAdam/commander-builder) is MIT and exposes Forge A/B simulations and detailed contextual scoring. The inspected CardScore module intentionally does not claim to be global card power and documents failed validation gates with the component off by default. Its validation discipline is more useful than importing its contextual prices. Bot mistakes, turn caps, politics and Commander multiplayer choices constrain simulation validity.

[mwisnowski's builder](https://github.com/mwisnowski/mtg_python_deckbuilder) offers MIT functional tags and role/theme machinery. It is a taxonomy prospect, not outcome-validated fixed prices.
[sjlillian's tournament experiment](https://github.com/sjlillian/MTG_tournament_guesser) contains Java/SMILE/PostgreSQL tooling and data, but no detected license or verified deployable validated model. Inspection is not reuse authorization.
[tramsey19's analysis](https://github.com/tramsey19/mtg-cardanalysis) trains on labels produced by its own subjective text-score rules. Its reported classifier accuracy measures imitation of those labels, not Commander win prediction. No license was detected.

### Other statistical research and data
[MtGDraftEncoder](https://github.com/akulen/MtGDraftEncoder) and its [2026 paper](https://arxiv.org/abs/2607.04782) learn contextual Limited representations. No repository license was detected. Draft outcomes do not transfer directly to Commander prices.
[MTG-card2vec](https://github.com/afreefaw/MTG-card2vec) represents co-occurrence/similarity rather than scalar power; source deck provenance and reuse need separate checks.
[Stanford card-balance research](https://cs230.stanford.edu/projects_spring_2021/reports/19.pdf) is a research lead, not a verified comprehensive Commander export.
[MODSIM World 2025](https://www.modsimworld.org/papers/2025/MODSIM_2025_paper_57.pdf) compares several deck-evaluation approaches and describes a small player survey, not a validated global card database.
[CubeCobra](https://github.com/dekkerglen/CubeCobra) has Apache-2.0 code and draft-pick Elo/preference features. Rating data licensing and a bulk export were not verified. Pick preference is not Commander win impact.

[cEDHstats](https://cedhstats.org/about) documents a rolling six-month, same-commander card-present versus card-absent points-per-game association with sample gates and Bayesian uncertainty. This is substantially more informative than raw adoption, but remains observational and competitive-format-specific. [TopDeck](https://topdeck.gg/docs/tournaments-v2) is an access-key API prospect; no new tournament dataset was acquired. [EDHTop16](https://edhtop16.com/staples) shares tournament upstreams, so it is not an independent vote.

[Playgroup](https://playgroup.gg/commander/power-level) publishes large aggregate claims and an October 2026 page date, but no licensed raw dataset was acquired. Its prose and table give inconsistent Game Changer effect descriptions. Pod normalization, reporting selection and pilot effects must be checked before using these as causal coefficients.
[17Lands](https://www.17lands.com/public_datasets), [Untapped](https://untapped.gg/en), and [Draftsim](https://draftsim.com/ratings) are useful methodological references in their own formats. Dataset-specific licenses and Commander transferability are unresolved; no Limited win rate was imported as Commander strength.

## Additional discovery and blocked methods
The inventory also records CardsRealm, ScryCheck, EDHCheck, Affinity, MTGonCurve, Moxfield, Archidekt, MTGGoldfish, a historical cmdrdeckrank project and CommanderAI. These range from mana diagnostics and contextual recommendation to hosted evaluators and user labels. Their exact API, rating coverage and reuse status remain explicitly unverified where appropriate. They are not counted as acquired scoring datasets.

Moxfield/Archidekt bracket labels are user declarations. An evaluator placing every precon in Bracket 2 could be applying product policy rather than estimating relative strength; no such label was used as independent strength validation. Public interfaces do not establish permission for 174 automated submissions.

## Official versus community versus modeling assumptions
Wizards' bracket and Game Changer guidance is expert format policy, not a regression target or proof of a continuous card-price scale. Read the [October 2025 update](https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-october-21-2025) alongside the current rules source when refreshing. The Game Changer control uses the frozen baseline Oracle snapshot, not an assertion that every online policy field remains unchanged forever.

Community reviews supply external opinions with conflicting criteria. Our fixed-price sums, basic-land equality control, tie half-credit, bootstrap design and regression diagnostics are modeling choices. No team or in-deck synergy surcharge is introduced. Historical cohort differences reflect card lists and source ratings, never a release-year card-price multiplier.
