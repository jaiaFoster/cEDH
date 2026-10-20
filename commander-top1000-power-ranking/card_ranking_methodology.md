# Candidate ranking methodology — 2026-10-19

This is a provisional candidate ranking and reviewed sparse pricing experiment. It does not establish the true 1,000 strongest cards. 423 entries in the requested top 1,000 remain low-confidence external-cache priors. Top 100 main-deck entries, top 50 command-zone entries, all currently pointed entries, all 46 Canadian Highlander pointed cards and all 53 Oracle Game Changers have explicit agent-authored rubric assessments. Independent agent review checked rules and selected leading valuations; it is not independent performance validation or certification of every card.

## Evidence and provenance

Reuse the previous 42-source discovery rather than counting sites again. Source snapshots remain under the previous project and tournament directories; source_provenance.json records SHA-256. Oracle identities are used across printings. The frozen snapshot contains 38,861 records including tokens; same-name tokens do not replace playable identities. Representative-printing digital/game fields cannot exclude a real paper Oracle identity.

* [Canadian Highlander official list](https://canadianhighlander.ca/points-list/) nominates all 46 pointed cards. [Council explanation](https://canadianhighlander.ca/2026/08/31/fall-2026-points-update/) explicitly treats points as format/meta policy, not a direct universal power ordering. Its point amounts are retained as evidence and never fitted as Commander coefficients.
* [Wizards brackets update](https://magic.wizards.com/en/news/announcements/commander-brackets-beta-update-february-9-2026), [ban update](https://magic.wizards.com/en/news/announcements/commander-banned-and-restricted-february-9-2026), [current list](https://magic.wizards.com/en/banned-restricted-list): expert nomination and legality, not numerical strength.
* [Scryfall bulk Oracle](https://scryfall.com/docs/api/bulk-data): identities, text and properties. Wizards owns card text; Scryfall data is not an invented open-data license.
* [zarzak cache](https://github.com/zarzak/mtg-deck-builder/tree/2ccb39f3e0fa08d91e848c2c98851effa8fa1fb2): 32,075 published LLM ratings. MIT repository software; preserve existing notices. No independent empirical validation. Basic-land disparities make direct score use unsuitable.
* [TopDeck.gg](https://topdeck.gg): pre-existing authorized repository snapshots, attribution retained. No new service submissions or scraping. Usage counts nominate candidates and do not determine applicability, weights or prices.
* [Commander Spellbook](https://spacecowmedia.github.io/commander-spellbook-backend/): retain the previous integration for separate component/prerequisite/controller legality review. Combo count is not a card-power score and no combo/team premium is added.

## Auditable judgment rubric

For main-deck cards, s=5.5*C+2*A+1.5*T+R+H, clipped to 0–100. Each C/A/T/R is 0–10. These coefficients are policy judgments, not statistically estimated effects. Ceiling C assesses achievable competitive resource/win potential; applicability A assesses legal color/cost and strategic prerequisites, replacement options and breadth; tempo T assesses initial mana, timing, setup and resource expenditure; resilience R assesses disruption and timing. H records a separately explained 2HG-specific difference. Do not count raw adoption as A or generic 'power' in every dimension. The rubric still has correlated dimensions and uncertain judgment precision.

The specialist safeguard sets s at least 80 when C>=9.5. This is an explicit policy floor to retain exceptional narrow cards, not an observed break. raw_main_deck_impact and specialist_floor_delta preserve its effect. The no-floor benchmark is mandatory. 51 card assessments are changed by the floor.

The unreviewed tail maps external rating r to C=clip((r-35)/8,0,7.5); absent r defaults to60, and A/T/R remain neutral placeholders5. This caps unreviewed main impact at63.75, below the recommended75 cutoff. It supplies candidate ordering only, not reviewed strength. Unreviewed commander prior is min(69,main+4), also below cutoff. All basics, including snow-covered basics, have zero main impact/price. Those numerical fallback constants are editable in scoring_config.json. No source prior alone points a card under the recommended policy. Lower exploratory thresholds can expose those unreviewed priors and must not be adopted without review.

## Command zone

Separate assessments use the same numeric rubric but C includes guaranteed strategic access; A evaluates viable construction breadth/color implications; T includes deployment, summoning sickness and realistic activations; R includes repeated access, removal and generic recast tax. Scores are alternatives by location, never a surcharge. Examples include main-free Rograkh or Inalla but pointed command-zone access. Independent partner prices sum; no pairing/context/team premium is added. Omitted or unreviewed commanders remain a material uncertainty.

Eligibility follows front-face legendary creatures, current legendary Vehicle and qualifying Spacecraft rules, explicit permission planeswalkers, Grist, conditional Backgrounds, and matching current partner families. Pair compatibility is separate from eligibility and ban legality. Doctor's companion requires a legendary Time Lord Doctor without extra creature types. DFCs retain one Oracle identity; back faces do not independently confer eligibility.

## Pricing and uncertainty

Recommended candidate threshold is >75 in both locations; gap bands <=5/10/15/20/25 receive1/3/5/8/12 points. Linear and quadratic alternatives are benchmarked. 'Before cutoff points' are ceil(impact), a display-only initial scale, not a league budget. No per-deck/year normalization and no 1,000-point anchor are used. A quarter-point judgment at a band edge can change price substantially, so tier-boundary review is required. Manual Oracle-ID overrides are explicit exceptions. Equal-impact ties sort alphabetically only for deterministic CSV ranks; nearby ranks do not establish meaningful distinctions.

The schedule union contains 339 identities: 287 main-deck pointed and 90 command-zone pointed options, with overlap. 33 pointed command-zone options fall outside the main-deck top1,000 and remain included. Hypothetically scored banned cards retain banned status; category bans for ante, Conspiracy and offensive content are not experimental unban candidates.

## Statistical design

Coefficients were not optimized on the precon reviewer rankings. Reused six/five-deck and five-pair assessments are diagnostics already seen during development, not untouched final validation. cEDH-labelled October events are held out from the before-October frequency nominations, but ratings/judgment are not blinded to known competitive archetypes and this is not a trained win predictor. Complete deck and basic legality checks run independently. Bootstrap reviewer correlations use1,000 deck resamples with seed19026; tiny tied opinion samples have wide intervals. Sensitivity uses200 independent uniform +/-2 impact scenarios on reviewed cards; it is a scenario analysis, not a confidence interval. Missing standardized 2HG outcomes prevents win-rate calibration.

Separate players retain mana, hands and permanents. Shared turns/life are not shared resource ownership. Full rules subtleties beyond the backend's explicit sanity checks require judge review; no simulation was run.
