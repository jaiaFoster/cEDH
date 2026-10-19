from pathlib import Path
import json
import pandas as pd
import numpy as np
def table(df):
 df=df.copy()
 for c in df:
  if pd.api.types.is_float_dtype(df[c]):df[c]=df[c].map(lambda v:'—' if pd.isna(v) else f'{v:.2f}')
 return '| '+' | '.join(map(str,df.columns))+' |\n|'+'|'.join(['---']*len(df.columns))+'|\n'+'\n'.join('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in r)+' |' for r in df.itertuples(index=False,name=None))
def write_report(df,annual,val,sens,m,cfg,scores,decks,detail,coverage):
 sources=json.loads(Path('data/raw/source_manifest.json').read_text());source_urls={s['key']:s['url'] for s in sources}
 topcols=['name','release_year','total_points','percentile','classification']
 agg=detail.groupby(['oracle_id','card_name']).agg(total_contributed=('points_total','sum'),deck_appearances=('deck','nunique'),points_each=('points_each','first')).reset_index().sort_values('total_contributed',ascending=False)
 agg.to_csv('data/clean/card_contributions.csv',index=False)
 latest=df[df.release_year==m['recent_year']];candidate=df[df.classification=='core_candidate_unverified']
 body=f'''# Commander League calibration — executed research snapshot

Analysis date: {cfg['as_of']}. Scoring version: {cfg['version']}. This is an exploratory fixed-card resource index, **not a validated measure of Commander power**. It is ready for manual refinement and shadow scoring; it does not support a strict league cap yet.

## Executive answers

1. **{m['unique_precons']} unique paper Commander precons**, deduplicated from {coverage['paper_records']} product records. All 100 playable entries, command zones, source metadata and original records are retained in `data/clean/precons.json`.
2. Original releases cover **{m['years'][0]}–{m['years'][1]}**. Coverage is bounded by the retrieved archives, not a promise that every released product has been independently found.
3. Overall median: **{m['median']:.1f} points**; resampled-deck 95% median interval {m['median_ci'][0]:.0f}–{m['median_ci'][1]:.0f}.
4. Most recent annual cohort ({m['recent_year']}, n={m['recent_n']}): median **{m['recent_median']:.0f}**. The latest individual release is {m['latest_release_date']} (n={m['latest_release_n']}, median {m['latest_release_median']:.1f}); annual and release-product cohorts are different.
5. Early releases (2011–2015, n={m['early_n']}) median {m['early_median']:.0f}; modern releases (2024 onward, n={m['modern_n']}) median {m['modern_median']:.0f}; difference **{m['difference']:+.0f}** (deck bootstrap 95% interval {m['difference_ci'][0]:+.0f} to {m['difference_ci'][1]:+.0f}). Linear slope {m['slope']:+.2f} points/year; year-cluster bootstrap interval {m['slope_ci'][0]:+.2f} to {m['slope_ci'][1]:+.2f}; descriptive R² {m['r_squared']:.3f}.
6. Largest aggregate contributors: {', '.join(agg.head(5).card_name)}. These aggregate contributions reflect inclusion and count as well as price; they were **not used to set prices**.
7. Thought Vessel (29) is implausibly above reviewed Arcane Signet (14), while The Wise Mothman and Kappa Cannoneer get only 2 each. These are concrete extraction/anchor-consistency failures, not evidence of true relative strength. Every automatic estimate is marked provisional.
8. Independent EDHREC six-deck assessment: Spearman **{m['validation_spearman']:.3f}**, {m['validation_concordant']}/{m['validation_pairs']} correctly ordered pairs. This small, selected opinion sample cannot establish broad predictive accuracy. An independent Reddit author's five-deck ordering gives rho {m['reddit_spearman']:.3f}.
9. Resolve feature extraction errors, collect actual Bracket 2/3 labels and controlled league outcomes, review commander access and 2HG effects, and pre-register a broader validation set before imposing a binding cap. Card sums intentionally omit deck and teammate synergy.
10. Provisional **Core-candidate reference interval: {m['core_candidate_range'][0]:.0f}–{m['core_candidate_range'][1]:.0f} points** (10th–90th percentile, n={m['core_candidate_n']}). This is a shadow-scoring comparison band, not an official Bracket 2 range. No quantitative Bracket 2/3 separation has been established; 1,000 and 2,000 remain design anchors.

## Data acquisition and quality control

The pinned taw commit is `{next(s['commit'] for s in sources if s['key']=='taw')}`. The complete schema audit records every top-level and nested card key and observed Python type. The archive separates `cards` (mainboard) from `commander`; adding these is essential. `displayCommander`, sideboard, tokens, schemes and planes are preserved but excluded from the playable 100. No product was selected by a name substring or 100-card size alone: selection requires type `Commander Deck`, category `deck` and a Commander format. MTGO-only products are explicitly excluded from the paper baseline.

{coverage['paper_records']} selected records all total 100. Canonical Oracle multiset deduplication collapses {coverage['paper_records']-len(df)} identical records, preserving alias dates/products separately and using the earliest archived appearance for cohort statistics. This collapses Commander Anthology reprints and Collector's Editions. Different lists remain separate even if deck names match. Original 100 entries retain printing UUIDs, names, quantities and command-zone sections. Nonbasic multiplicities, missing names, size, commander color identity and current nonlegal cards are audited; legitimate any-number card exceptions are recognized.

The MTGJSON DeckList contains {coverage['mtgjson_paper_records']} Commander Deck records; name+set comparison finds {len(coverage['missing_from_taw'])} missing from taw and {len(coverage['missing_from_mtgjson'])} missing from MTGJSON. **These are related sources:** taw includes MTGJSON UUIDs, so agreement does not independently verify every card. Full MTGJSON per-deck contents were not independently downloaded; this is a coverage cross-check. The all-decks HTML is client-rendered, so its published DeckList endpoint supplies the cross-check.

Oracle resolution prefers exact full names over face aliases, preventing art-series cards such as `Plains // Plains` from taking the place of Plains. The source's `(Prepared)` suffix is removed solely for exact prepared-card name matching; original strings remain saved. No fuzzy substitutions or zero-valued missing-card fallbacks are used. The snapshot contains {m['oracle_records']:,} Oracle-ID records, including nonlegal objects for clear calculator rejection. New cards after the snapshot require reacquisition and review. `source_manifest.json` stores URLs, dates, hashes and access failures. Direct Reddit responses were challenge pages; the original-post validation labels were retrieved through the browser search text, documented separately. Moxfield returned an application shell, not a usable validated deck.

## Official guidance versus the model

Wizards' October 2025 update describes Core as unoptimized, straightforward and incrementally winning; its expected eight completed turns contrast with Upgraded's strong card quality, synergy and expected six completed turns. It removed general tutor restrictions and **decoupled precons from Core**. February 2026 reaffirmed this and added Farewell and Biorhythm to Game Changers. Searches found no later bracket update; this describes the latest official guidance retrieved, not an assertion that no later unpublished change exists. [October update]({source_urls['brackets_2025']}); [February update]({source_urls['brackets_2026']}).

The construction guidance uses zero Game Changers for Core and up to three for Upgraded, alongside restrictions on land denial, extra turns and game-ending combos. Presence or absence alone does not measure intent or speed. The October 2025 embedded official deck-list plus the two February additions reconciles exactly with Oracle; `game_changer_reconciliation.json` records the check. The downloaded Oracle snapshot flags {sum(s['game_changer'] for s in scores.values())} Game Changers; the full list is in `data/clean/game_changers.json`. MH3, Secret Lair and Commander Masters are separated as premium review cohorts; Starter decks are separate. Other zero-GC lists are only **Core candidates**, without a completed combo, turn-speed or gameplay audit. GC-bearing precons are exceptions, never silently treated as Core. Current banned cards in historical decks are flagged rather than removed from their original list. Upgrades Unleashed is a separate quality exception: its two Mossfire Valleys violate singleton. Wizards confirms the printing error and recommends replacing one with a basic or another land. The archived list is preserved without a silent correction. Foundations Commander (2026) is grouped with introductory products, following its official description.

For Commander 2HG, Wizards' format page specifies 60 shared starting life, no unified construction, 100 cards per player, and team loss at 21 damage from a single commander or 15 poison. Shared turns do not share hands or mana. Effects on each opponent apply to each player separately; there are two opponents, versus three in ordinary four-player FFA. These changes are card-specific and not a universal multiplier. The Commander 2HG format page and the general Comprehensive Rules need to be read together. [2HG format]({source_urls['two_headed']}); [Comprehensive Rules snapshot]({source_urls['rules']}).

Current official bans are captured in `experimental_unban_review.csv`, including category bans and Lutri's companion-only restriction. The snapshot reconciles official named bans against Oracle legality in `legality_reconciliation.json`. Biorhythm and Lutri are no longer blanket banned; do not copy obsolete ban lists. The October 12, 2026 announcement's Yuriko commander ban concerns Competitive Brawl, not multiplayer Commander. [Official banned list]({source_urls['banned']}).

## Mathematical model and coefficients

Each Oracle card gets one fixed nonnegative integer. Printing, year, monetary price, EDHREC rank and precon frequency are excluded. There is **no fitted card-power response variable**. Coefficients are explicit analyst priors motivated by functional resource access and Wizards' emphasis on efficient engines, interaction and tutors. Descriptive regression and bootstrap results test properties of this index; they do not transform its inputs into objective power ratings.

For nonlands, define binary role matches from reminder-stripped Oracle text. Each role is counted at most once; a repeatable acceleration, draw or board role is multiplied by {cfg['repeat_multiplier']}; sufficiently broad removal by {cfg['broad_interaction_multiplier']}. The role weights are:

{table(pd.DataFrame([dict(role=k,weight=v) for k,v in cfg['role_weights'].items()]))}

Let r₁ and r₂ be the two largest role values. Automatic nonland points before rounding are `2 + (r₁ + 0.35*r₂)/(1 + 0.22*max(0,mana_value−2))`. The primary role captures useful function; the second, discounted role credits flexibility. Remaining roles do not add points, limiting double counting. Raw body stats only supply a capped board role when power+toughness exceeds twice mana value. It is not a mana-value reward: expensive spells face a larger discount. No separate efficiency bonus duplicates the role value.

Land points are separate: basics {cfg['basic_land']}; nonbasics {cfg['nonbasic_land']} plus {cfg['land_fixing_bonus']} for broad fixing, minus {cfg['land_tapped_discount']} for a matched tapped-entry clause, plus {cfg['land_utility_bonus']} for matched utility, floored at zero. Land text is not also given acceleration or tutor role points. This is an absolute land allowance; relative land quality, not a tax on using land, is what matters when comparing normal 100-card decks. Median collective land share is {100*m['land_share_median']:.1f}% of deck totals. Modal land faces and conditional tapped clauses need human review.

Game Changer status imposes a floor of {cfg['game_changer_floor']}, **not an additive bonus**, avoiding a duplicate charge for the same engine. Reviewed cards replace the whole estimate with a documented absolute override; they are not additive bonuses. There are {sum(s['manually_reviewed'] for s in scores.values())} overrides. The global multiplier is {cfg['global_multiplier']}; no observed deck/year is normalized. Final rounding is floor(value+0.5), consistent with integer overrides. Component columns explain estimated roles; because only the largest two enter the formula and floors/overrides replace it, **component columns must not simply be summed**.

The previous candidate v0.1 omitted the mana-value discount; v0.2 discounts expensive effects to address the conceptual risk of overpricing splashy cards. The change was specified before inspecting held-out scores and was not tuned to their rank. `initial_points` and `total_points` preserve both versions. Median deck change: {(df.total_points-df.initial_points).median():+.0f}; largest absolute change: {abs(df.total_points-df.initial_points).max():.0f}. This is a transparent structural revision, not empirically optimized calibration. Magnitudes remain uncertain. Optional commander adjustment defaults to zero; adding one requires new commander-specific evidence. Teammate synergy is never a scoring input.

## Observed distributions

{table(annual)}

Overall score percentiles:

{table(pd.DataFrame([dict(percentile=int(float(k)*100),points=v) for k,v in m['overall_percentiles'].items()]))}

High-impact cards (≥{cfg['high_impact_threshold']} points) per deck:

{table(pd.DataFrame([dict(cards=k,decks=v) for k,v in m['high_impact_distribution'].items()]))}

Product-cohort contrasts:

{table(df.groupby('classification').total_points.agg(['count','mean','median','std','min','max']).reset_index())}

Each precon is part of a finite observed archive, so its score is exact conditional on this configuration. Bootstrap intervals describe sensitivity to resampling cohorts, **not uncertainty in true card power**. Deck bootstraps assume sampled decks are exchangeable; yearly cluster bootstraps retain within-year dependence but have only {df.release_year.nunique()} clusters. No causal or significance claim follows from a positive or negative time trend. Shared reprints, changing color mix, different product tiers and current Oracle text confound release-year comparisons. This analysis uses current text/legality for historical lists; it does not reconstruct historical play environments.

The largest adjacent annual median movements, including product mix changes, are:

{table(annual.assign(median_change=annual['median'].diff()).dropna(subset=['median_change']).assign(abs_change=lambda x:abs(x.median_change)).nlargest(5,'abs_change')[['year','count','median','median_change']])}

A composition regression of score on year, nonland mean mana value, GC count and land points is saved separately. It describes the scoring formula and deck mix, not independent causal predictors of wins. Annual role counts and mana values are in the deck CSV, allowing construction-based inspection without assuming creep beforehand.

## Independent validation and error analysis

The frozen holdout comes from Andy Zupke's published 2024 list: his five ordered favorites plus Science!, explicitly described as worst. Labels are **one author's assessments**, mixing quality and play experience; neither community consensus nor measured results. No coefficients or overrides were fitted to these outcomes. [Assessment source]({source_urls['edhrec_validation']}).

{table(val[['name','community_rank','model_points','model_rank']])}

Spearman rho {m['validation_spearman']:.3f}; approximate two-sided p={m['validation_p']:.3f} is provided for completeness, with n=6 and selection bias making conventional significance inference unsuitable. Pair agreement {m['validation_concordant']}/15. Validation failure must lead to review, not retrospectively fitting these decks and reporting them as holdouts. The Reddit original post supplies a second five-deck personal ordering; rho {m['reddit_spearman']:.3f}. It is a noisy restricted-range check, not a larger independent trial. Reddit commenters disagree; vote counts cannot substitute for outcomes.

Relevant qualitative context: r/CompetitiveEDH discussions emphasize efficient mana, tutors and interaction, supporting categories without supplying coefficients. EDHREC popularity is not a strength measurement. Commander Spellbook is a combo registry, useful for a separate gameplay audit rather than a synergy surcharge. TopDeck documents tournament data access but this run did not acquire a comparable Bracket 2/3 2HG outcome sample. Moxfield labels are user declarations and its retrieved shell did not furnish reliable validation data. [cEDH discussion]({source_urls['cedh_context']}); [Spellbook]({source_urls['spellbook']}); [TopDeck]({source_urls['topdeck']}).

Known failure modes:

* **Tribal and synergy decks:** standalone tribal enablers may get only a board role or base points while the deck performs very well. Explorers of the Deep, Mutant Menace and Cavalry Charge are diagnostic examples. This is partly intentional under the access-to-card-power philosophy; deck win ranking is therefore not the sole objective. Do not remedy this by taxing teammate synergy.
* **Efficient tutors/fast mana:** anchors correct Sol Ring, efficient tutors, mana rocks and dorks. Automatic regexes miss named mana symbols, indirect cost cheating or restricted tutors, and can mistake conditional text for reliable effects. Unknown/obscure cards do not get an automatic novelty premium; low provisional prices could nevertheless create a loophole. Require pre-league review of novel cards, rather than assume they are accurately priced.
* **Splashy spells:** discounting mana cost is directionally sensible, but alternative costs, discounts and free casting can make this excessive. Blasphemous Act is manually corrected. Cyclonic Rift is corrected for its split utility. Commander access and prepare costs are not modeled accurately.
* **Land quality:** basics contribute collectively; tapped fixing and premium lands have different points. Generic conditional-tap regexes may penalize lands that usually enter untapped. Fetch, shock, original dual, fast, battle and filter cycles need a full reviewed land taxonomy.
* **Engines and compact combos:** conditional draw phrases are not expected-card calculations; Thassa's Oracle's floor reflects combo risk rather than standalone body value. Game Changers are a policy signal, not a cardinal power scale. Infinite loops and locks require a separate gameplay policy regardless of points.
* **Archetype testing:** tribal, graveyard, spellslinger, artifact and energy strategies lack adequate independent labels. A small ranked sample cannot quantify systematic archetype bias. Published rank disagreement below is evidence to investigate, not proof of any deck's win rate.

Reviewed-versus-automatic discrepancies (largest absolute adjustments among cards appearing in precons):

{table(pd.DataFrame([scores[o] for o in detail.oracle_id.unique()]).assign(abs_delta=lambda x:abs(x.override_delta)).nlargest(12,'abs_delta')[['card_name','automatic_estimate','base_points','override_delta','notes']])}

These discrepancies identify extraction and functional-context problems. Overrides improve known cards but create uneven evidence coverage; most of the complete catalog remains low confidence.

## Sensitivity

Every feature weight, the GC floor, basic land allowance, mana decay and secondary-role credit was changed independently ±25%; absolute manual overrides stayed fixed. Integer rounding is applied again to every card. This isolates each parameter but understates uncertainty if manual anchors are wrong together. No year/deck normalization occurs.

{table(sens)}

Card perturbations are also saved: increasing any single card by 10 adds exactly 10×its count to each deck containing it and zero to decks without it. A team adds both individual changes. No cross-deck term exists. Since Sol Ring is widespread, its absolute price often shifts totals more than ranks. Published sensitivity is conditional on the fixed manual set; before cap adoption also perturb manually reviewed engines and land cycles jointly.

## Twenty highest-scoring precons

{table(df.head(20)[topcols])}

## Twenty lowest-scoring precons

{table(df.tail(20).sort_values('total_points')[topcols])}

## Representative deck breakdowns
'''
 selected=['Counterpunch','Explorers of the Deep','Science!','Mutant Menace']
 selected += [df[df.classification=='starter'].iloc[0]['name'],latest.iloc[0]['name']]
 for name in dict.fromkeys(selected):
  row=df[df.name==name].iloc[0];ds=detail[detail.deck==name].sort_values('points_total',ascending=False)
  body+=f"\n### {name} ({row.release_year})\n\nCommander: {row.commander}. Product: {row['product']}. Total **{row.total_points}**, percentile {row.percentile:.1f}; land contribution {row.land_points}; high-impact cards {row.high_impact_cards}; Game Changers {row.game_changer_count}; classification `{row.classification}`. Nonland mean mana value {row.nonland_mean_mv:.2f}. Reviewed cards contribute {row.manually_reviewed_points} points.\n\n"+table(ds.head(12)[['card_name','count','points_each','points_total','section']])+f"\n\nRemaining {int(ds['count'].sum()-ds.head(12)['count'].sum())} cards contribute {int(ds.points_total.sum()-ds.head(12).points_total.sum())} points. Full 100-card detail is in `deck_card_points.csv`. Role matches: "+', '.join(f'{k} {row[k+"_cards"]}' for k in cfg['role_weights'])+'. Role counts can overlap and are not independent contributions.\n'
 body+='''
## Experimental banned-card evaluation

The separate worksheet contains every named ban matched to Oracle plus Oracle category-banned cards and Lutri's companion restriction. All 42 individually named bans, including the seven requested cards, have individual functional and 2HG assessments grounded in current Oracle text. Price magnitudes remain analyst policy priors. Generic unreviewed category-ban rows are explicitly low-confidence reserves, not researched final prices; they default to retaining the ban. Proposed points are separate hypothetical testing values and **never change legality or the main model**. A 100-point allowance cannot make collusive draw, early locks, non-game mechanics or explosive opening mana appropriate. Prophet's untap count differs in shared turns; Dockside counts only opposing permanents; Trade Secrets can target a teammate. These require distinct testing protocols.

## Recommendations before a strict cap

1. Use this build to shadow-score league decks and inspect cheap automatic cards, keeping overrides versioned. Review lands and prepare/modal cards first, then fast mana, tutors, free spells and engines.
2. Gather a preregistered, independently labeled deck sample spanning Core and Upgraded. Include low/high standalone strength and low/high synergy separately. Do not train and evaluate on the same decks.
3. Record turn of first credible win attempt, mulligans, seats, pilots, archetypes, teammate pairings and game length. Use mixed-effects or matched analyses to distinguish card access, pilots and synergy; do not turn the teammate synergy estimate into a budget surcharge.
4. Fit only coefficients supported by the data, with shrinkage and out-of-sample validation. Obtain uncertainty for card values, not only archive medians. Many cards will remain weakly identified.
5. Keep ban legality and combo/lock policy separate from card totals. Establish commander-access adjustments only after dedicated tests. Validate a global unit conversion against actual Bracket 3 decks before treating 1,000 points as an empirical average.

The result is a reproducible precon index and an editable calculator. It is not yet an accurate cardinal calibration of Core or Upgraded power, and a strict 2,000-point team cap would be premature.
'''
 body+='\n## Source ledger\n\n'+table(pd.DataFrame([dict(key=s['key'],url=s['url'],retrieved=s.get('retrieved_at',s.get('status','')),status=s.get('status','pinned git')) for s in sources]))+'\n'
 Path('precon_statistical_report.md').write_text(body)
