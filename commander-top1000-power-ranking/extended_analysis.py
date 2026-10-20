"""Additional construction-cost sensitivity; no gameplay or outcome estimates."""
import collections,json,math
import numpy as np
import pandas as pd
from scipy import sparse,stats
from ranking import point_price

def extend_analysis(files,summary,index,frame,commands,benchmark,comparison,decks,config):
    ids=list(frame.oracle_id)
    for oid in config.get("overrides",{}):
        if oid not in ids:ids.append(oid)
    col={oid:i for i,oid in enumerate(ids)}
    lookup=frame.set_index("oracle_id").to_dict("index")
    def matrix(zone):
        rr=[];cc=[];vv=[]
        for i,d in enumerate(decks):
            for oid,q in d[zone].items():
                if oid in col:rr.append(i);cc.append(col[oid]);vv.append(q)
        return sparse.csr_matrix((vv,(rr,cc)),shape=(len(decks),len(ids)))
    xm,xc=matrix("main"),matrix("commanders")
    ms=np.array([lookup.get(o,{}).get("main_deck_impact",0) for o in ids],dtype=float)
    cs=np.array([lookup.get(o,{}).get("command_zone_impact") or 0 for o in ids],dtype=float)
    cs=np.nan_to_num(cs)
    def prices(scores,tau,curve,zone):
        return np.array([point_price(o,zone,float(s),config,float(tau),curve) for o,s in zip(ids,scores)],dtype=int)
    mp=prices(ms,config["main_threshold"],config["curve"],"main")
    cp=prices(cs,config["commander_threshold"],config["curve"],"commanders")
    baseline=np.asarray(xm@mp+xc@cp).ravel()
    groups={cohort:np.array([i for i,d in enumerate(decks) if d["cohort"]==cohort]) for cohort in sorted({d["cohort"] for d in decks})}
    manual_m=np.array([bool(lookup.get(o,{}).get("manually_assessed")) for o in ids])
    manual_c=np.array([bool(lookup.get(o,{}).get("command_zone_manually_assessed")) for o in ids])
    rng=np.random.default_rng(19126);perturbations=[]
    for run in range(200):
        pm=prices(np.clip(ms+rng.uniform(-2,2,len(ids))*manual_m,0,100),config["main_threshold"],config["curve"],"main")
        pc=prices(np.clip(cs+rng.uniform(-2,2,len(ids))*manual_c,0,100),config["commander_threshold"],config["curve"],"commanders")
        total=np.asarray(xm@pm+xc@pc).ravel()
        for cohort,ii in groups.items():
            rho=float(stats.spearmanr(baseline[ii],total[ii]).statistic) if np.std(total[ii]) and np.std(baseline[ii]) else None
            perturbations.append({"run":run,"cohort":cohort,"median_points":float(np.median(total[ii])),"median_abs_point_change":float(np.median(np.abs(total[ii]-baseline[ii]))),"max_abs_point_change":int(np.max(np.abs(total[ii]-baseline[ii]))),"spearman_vs_unperturbed":rho})
    perturb=pd.DataFrame(perturbations)
    files["deck_rating_sensitivity.csv"]=perturb.to_csv(index=False)
    summary["deck_rating_sensitivity"]={cohort:{"median_score_min":float(perturb[perturb.cohort==cohort].median_points.min()),"median_score_max":float(perturb[perturb.cohort==cohort].median_points.max()),"median_rank_correlation":float(perturb[perturb.cohort==cohort].spearman_vs_unperturbed.median())} for cohort in groups}
    card_changes=[]
    chosen=[(o,"main") for o in frame[(frame.commander_legality=="legal")&~frame.two_hg_specific_ban].head(10).oracle_id]
    chosen += [(o,"commanders") for o in commands[commands.commander_legality=="legal"].head(5).oracle_id]
    for oid,zone in chosen:
        vector=xm[:,col[oid]].toarray().ravel() if zone=="main" else xc[:,col[oid]].toarray().ravel()
        original=int(mp[col[oid]] if zone=="main" else cp[col[oid]])
        for delta in (-1,1):
            actual=max(0,original+delta)-original
            total=baseline+vector*actual
            for cohort,ii in groups.items():
                card_changes.append({"card_name":index.cards[oid]["name"],"zone":zone,"original_points":original,"changed_points":original+actual,"cohort":cohort,"decks_affected":int(sum(vector[ii]>0)),"median_before":float(np.median(baseline[ii])),"median_after":float(np.median(total[ii])),"max_abs_deck_change":int(np.max(np.abs(total[ii]-baseline[ii]))),"spearman_vs_unperturbed":float(stats.spearmanr(baseline[ii],total[ii]).statistic) if np.std(total[ii]) else None})
    files["individual_card_price_sensitivity.csv"]=pd.DataFrame(card_changes).to_csv(index=False)
    distributions=[];concentrations=[];boundaries=[];ranking=[]
    for policy,r in comparison.drop_duplicates("policy").set_index("policy").iterrows():
        sm=frame.raw_main_deck_impact.to_numpy() if not r.specialist_floor else ms[:len(frame)]
        for zone,scores,tau in (("main",sm,r.main_threshold),("commanders",cs[:len(frame)],r.command_zone_threshold)):
            p=prices(scores,tau,r.curve,zone)[:len(frame)]
            # Each frame row is one Oracle identity; command eligibility is independent.
            work=frame.copy();work["policy_points"]=p
            if zone=="commanders":work=work[work.command_zone_eligibility!="ineligible"]
            for cost,n in work.policy_points.value_counts().sort_index().items():distributions.append({"policy":policy,"zone":zone,"points":int(cost),"candidate_identities":int(n)})
            pointed=work[work.policy_points>0]
            for (ci,category),g in pointed.groupby(["color_identity","category"],dropna=False):concentrations.append({"policy":policy,"zone":zone,"color_identity":ci,"functional_category":category,"cards":len(g),"points":int(g.policy_points.sum())})
            field="main_deck_impact" if zone=="main" else "command_zone_impact"
            above=work[work.policy_points>0].sort_values([field,"card_name"],ascending=[True,True]).head(10)
            below=work[work.policy_points==0].sort_values([field,"card_name"],ascending=[False,True]).head(10)
            exceptional=work[(work.policy_points==0)&(work.competitive_ceiling>=9.5)] if zone=="main" else work[(work.policy_points==0)&(work.command_zone_competitive_ceiling>=9.5)]
            for status,g in (("lowest_pointed",above),("highest_free",below),("exceptional_ceiling_free",exceptional)):
                for row in g.to_dict("records"):boundaries.append({"policy":policy,"zone":zone,"status":status,"card_name":row["card_name"],"impact":row[field],"points":row["policy_points"],"legality":row["commander_legality"]})
        sub=benchmark[benchmark.policy==policy].set_index("deck_name")
        for cohort,ii in groups.items():
            vals=np.array([sub.loc[decks[i]["name"],"total_points"] for i in ii])
            ranking.append({"policy":policy,"cohort":cohort,"spearman_vs_recommended":float(stats.spearmanr(baseline[ii],vals).statistic) if np.std(vals) else None})
    files["cutoff_point_distributions.csv"]=pd.DataFrame(distributions).to_csv(index=False)
    files["cutoff_color_category_concentration.csv"]=pd.DataFrame(concentrations).to_csv(index=False)
    files["cutoff_boundary_cards.csv"]=pd.DataFrame(boundaries).to_csv(index=False)
    files["cutoff_rank_stability.csv"]=pd.DataFrame(ranking).to_csv(index=False)
    inversions=commands[commands.command_zone_points<commands.main_deck_points].copy()
    files["command_zone_price_inversions.csv"]=inversions.to_csv(index=False)
    premiums=commands.assign(command_zone_price_difference=commands.command_zone_points-commands.main_deck_points).sort_values(["command_zone_price_difference","command_zone_impact","card_name"],ascending=[False,False,True])
    files["command_zone_price_differences.csv"]=premiums.to_csv(index=False)
    summary["command_zone_price_inversions"]=inversions[["card_name","main_deck_points","command_zone_points","command_zone_explanation"]].to_dict("records")
    # Detailed reports use the backend's location-specific rows, not reconstructed subtotals.
    representative=json.loads(files["representative_deck_breakdowns.json"])
    sections=["# Representative deck construction breakdowns","All listed costs use alternative main/command-zone prices. These are resources, not strength predictions."]
    for name in ("Mutant Menace","Science!","Explorers of the Deep","Necron Dynasties","From Cute to Brute"):
        r=representative[name]["report"]
        sections += [f"## {name}",f"Total {r['total']}; command zone {r['command_zone_total']}; basic legality checks: {r['officially_legal']}."]
        rows=["| Card | Location | Qty | Points each | Total |","| --- | --- | ---: | ---: | ---: |"]
        rows += [f"| {row['card_name']} | {row['zone']} | {row['quantity']} | {row['points_each']} | {row['total']} |" for row in r["rows"] if row["total"]>0 or row["zone"]=="commanders"]
        sections.append("\n".join(rows))
        sections += ["All remaining recognized cards cost zero. Full inputs and every card row are in representative_deck_breakdowns.json."]
    files["representative_deck_breakdowns.md"]="\n\n".join(sections)+"\n"
    files["analysis_summary.json"]=json.dumps(summary,indent=2,allow_nan=False)
    files["point_cutoff_analysis.md"] += "\n## Deck and individual-price sensitivity\n\nThe supplementary deck_rating_sensitivity.csv uses 200 independent +/-2 impact scenarios in both locations (seed19126). These are judgment scenarios, not statistical confidence bounds. individual_card_price_sensitivity.csv changes each of ten leading legal main-deck cards and five leading commanders by +/-1 point. cutoff_rank_stability.csv measures rank changes across policies; point histograms and boundary/free-card audits cover every cutoff.\n\n"+json.dumps(summary["deck_rating_sensitivity"],indent=2)+"\n\nCommand-zone discounts are explicitly listed in command_zone_price_inversions.csv and remain mandatory manual-review cases; guaranteed access does not automatically eliminate colored construction, deployment or main-deck cheating differences.\n"
    def table(d,cols):
        d=d[cols]
        def f(x):return str(round(x,3)) if isinstance(x,float) else str(x).replace("|","/")
        return "\n".join(["| "+" | ".join(cols)+" |","| "+" | ".join(["---"]*len(cols))+" |"]+["| "+" | ".join(f(x) for x in row)+" |" for row in d.itertuples(index=False,name=None)])
    active=benchmark[benchmark.policy=="configured_policy"]
    pc=active[active.cohort=="official_precons"]
    cmp=comparison[comparison.policy=="configured_policy"]
    can=frame[frame.canadian_highlander_points>0]
    positive=frame[(frame.two_hg_adjustment>0)&frame.manually_assessed].sort_values(["two_hg_adjustment","main_deck_impact"],ascending=[False,False]).head(10)
    negative=frame[(frame.two_hg_adjustment<0)&frame.manually_assessed].sort_values(["two_hg_adjustment","main_deck_impact"],ascending=[True,False]).head(10)
    boundary=frame[(frame.main_deck_impact-config["main_threshold"]).abs()<=2].sort_values(["main_deck_impact","card_name"],ascending=[False,True]).head(20)
    text=f"""# Executive findings — candidate scoring schedule

## 1. Most impactful cards

The primary CSV ranks exactly1,000 main-deck candidates. This is a provisional judgment ranking, not a validated strongest-card census: {summary['top1000_unreviewed']} tail rows use explicitly low-confidence source priors. Reviewed leading cards and hypothetical banned cards are distinguishable below.

{table(frame.head(20),['main_deck_rank','card_name','main_deck_impact','main_deck_points','commander_legality'])}

The leading legal cards include Sol Ring, Demonic Tutor, Ad Nauseam, Force of Will and efficient Mox acceleration. Raw scores and point tiers are arbitrary units of construction resources; no1,000-point or2,000-point budget was fitted.

## 2. Comparison with Canadian Highlander

All{len(can)} pointed Canadian Highlander cards were nominated and explicitly reviewed; {int((can.main_deck_points>0).sum())} receive main-deck points here. The others are {', '.join(can[can.main_deck_points==0].card_name)}. This is not a claim those expert points are wrong: Canadian Highlander is a different format and its council explicitly does not publish a universal card-strength ranking. Banned PowerNine-style acceleration overlaps the top; format-specific engines and free protection differ.

## 3. Material 2HG changes

The adjustments below are documented judgments grounded in rules, not measured percentage changes in win rates. Extra team turns, two-head life effects and shared life differ from ordinary FFA. Own-controller limitations and only one opposing team turn matter just as much.

{table(positive,['card_name','two_hg_adjustment','two_hg_considerations'])}

{table(negative,['card_name','two_hg_adjustment','two_hg_considerations'])}

Read two_headed_giant_rules_review.md, particularly commander-damage documentation conflict, poison, individual life events and team cannot-lose effects.

## 4. Command-zone access

{table(premiums.head(15),['card_name','main_deck_points','command_zone_points','command_zone_price_difference','command_zone_impact'])}

These are alternative prices, not additional surcharges. Partners each pay their own fixed command-zone price. No partner-pair or teammate-context premium is charged. The companion ranking includes all eligible candidate identities, with manual-review flags and separate CZ rubric components; unreviewed commanders are not certified as weak.

## 5–6. How many cards and where to cut

Test the active >{config['main_threshold']} main / >{config['commander_threshold']} CZ policy with {config['curve']} pricing. The hypothetical-inclusive union contains{summary['pointed_union']} identities ({summary['main_pointed']} main-pointed,{summary['commander_pointed']} CZ-pointed). Its currently Commander-legal/2HG-legal portion contains **{summary['legal_2hg_pointed_union']} identities**, with {summary['legal_2hg_pointed_main']} main and {summary['legal_2hg_pointed_commanders']} command-zone prices. Zones overlap.

This is a policy cutoff, not an observed natural break. The specialist floor and coarse source tail create artificial score concentrations. Cutoffs near50/100 leave too many efficient enablers free;750/1,000 enter unreviewed priors. All quotas, ties, threshold grids, no-floor cases and linear/quadratic alternatives are in cutoff_comparison.csv. The configured-policy rows are reference duplicates when the config matches one of the fixed-grid policies, not extra independent observations.

## 7. Borderline and unresolved cases

{table(boundary,['card_name','main_deck_impact','main_deck_points','confidence'])}

Review all price-tier boundaries too. Price inversions, banned cards, high published-LLM-only ratings and omissions remain explicit queues. The absence of a point is not certification a card is safe or a combo acceptable.

## 8–9. Actual deck construction benchmarks

{table(cmp,['cohort','deck_count','legal_deck_count','median','p10','p90','median_pointed_cards','median_command_zone_share'])}

All174 precons were preserved, including historical ban/duplicate exceptions. Most of their points concentrate in Sol Ring and at most a few other cards. There are{int(cmp[cmp.cohort=='official_precons'].iloc[0].unique_totals)} distinct precon totals. This intentionally sparse system does not rank precon synergy well. The reused six-deck reviewer Spearman is{summary['validation'][0]['spearman']:.3f}; the five-deck Reddit diagnostic is{summary['validation'][1]['spearman']:.3f}. Those tiny opinion comparisons are not untouched validation and do not support competitive predictive accuracy.

The B3 sample contains self-declared/event labels, not verified ordinary Bracket3 power. The cEDH sample is selected by event names and complete structured submissions; at least one conspicuously weak Dosan registration was retained. Those are construction-cost distributions, not representative 2HG outcome samples. No verified upgraded/high-power/optimized intermediate cohorts or 2HG match outcomes were acquired. Card judgments were updated after error analysis, so temporal separation of frequency nominations is not a blinded final predictive test.

## 10. First league test

Use proposed_point_schedule.csv as a **candidate** and version-lock accepted overrides before play. Keep banned legality independent, adjudicate oppressive combos/controllers separately, and collect actual paired 2HG decklists and match context. Do not adopt a strict numeric cap from these medians alone. Preserve the old calculator, original v0.2 baseline, v1 benchmarks, frozen Oracle/precons and Spellbook integration.
"""
    files["executive_summary.md"]=text
    files["README.md"] += "\n## Active configuration and final review\n\n"+json.dumps({k:config[k] for k in ("version","main_threshold","commander_threshold","curve")},indent=2)+"\n\nStart with executive_summary.md. Run `python commander-top1000-power-ranking/verify_artifacts.py` after reproduction. See THIRD_PARTY_NOTICES.md, independent_review.md and two_headed_giant_rules_review.md for the audit scope and rules caveats. The source-name aliases encountered in this sample are shared by ingestion and the CLI; additional flavor/interchangeable names may require a verified mapping. source_exclusions.csv lists excluded records without player names. representative_deck_breakdowns.md explains the five difficult precons, with complete reports in JSON.\n"
    files["benchmark_analysis.md"] += "\n## Event-label outlier and review feedback\n\nThe lowest-cost cEDH-labelled registration is an intentionally weak-looking Dosan list with68 basic Forests and many inefficient cards, rather than an optimized competitive benchmark. It was retained rather than removed using the model score. This directly limits interpretation of event labels. Interchangeable-name repair recovered a few legitimate source lists; the exact final counts above supersede exploratory in-memory counts. Card assessments were revised following this audit, so these distributions are descriptive, not a blinded final outcome test.\n"
    ordered=pc.sort_values(["total_points","deck_name"],ascending=[False,True])
    files["precon_extremes.md"]="# Precon construction extremes\n\nTies sort alphabetically; this is a sparse construction-resource ranking, not relative gameplay strength.\n\n## Highest20\n\n"+table(ordered.head(20),["deck_name","total_points","command_zone_points","pointed_card_count"])+"\n\n## Lowest20\n\n"+table(pc.sort_values(["total_points","deck_name"]).head(20),["deck_name","total_points","command_zone_points","pointed_card_count"])+"\n"
    for name,slug in (("Explorers of the Deep","explorers_of_the_deep"),("Necron Dynasties","necron_dynasties")):
        d=next(d for d in decks if d["name"]==name)
        lines=["Commander"]+[f"{q} {index.cards[o]['name']}" for o,q in sorted(d["commanders"].items(),key=lambda item:index.cards[item[0]]["name"])]+["","Deck"]+[f"{q} {index.cards[o]['name']}" for o,q in sorted(d["main"].items(),key=lambda item:index.cards[item[0]]["name"])]
        files[f"examples/{slug}.txt"]="\n".join(lines)+"\n"
    files["README.md"] += "\nA ready-to-run example uses two actual archived precons:\n\n```sh\npython commander-top1000-power-ranking/score_decks.py commander-top1000-power-ranking/examples/explorers_of_the_deep.txt --deck-b commander-top1000-power-ranking/examples/necron_dynasties.txt --team-cap 30 --export team-report.json\npython commander-top1000-power-ranking/test_cli.py\n```\n\nproposed_legal_point_schedule.csv contains only currently eligible league card identities; proposed_point_schedule.csv additionally retains explicitly marked hypothetical banned-card prices. A card-list legality flag does not replace the independent deck/pair legality checks.\n"
    return files
