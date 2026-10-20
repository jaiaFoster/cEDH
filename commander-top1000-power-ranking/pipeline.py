"""Reproduce frozen-source rankings, cutoffs and reports. No paid APIs or network."""
import base64,json,pathlib
from ranking import *
from backend import SparseBackend
from data_sources import acquire_local


def analyse(root,seeds,config,render_plot=True):
    import io,base64,scipy.stats as st
    configure_model(config)
    def configured_price(oid,zone,s,tau,curve):
        return point_price(oid,zone,s,config,tau,curve)
    result,pools,cards=acquire_local(root)
    ext=json.load(open(root/"commander-card-power-research-v1/data/zarzak_cache.json"))
    can=json.load(open(root/"commander-card-power-research-v1/data/benchmark_inputs.json"))["canlander"]
    index,frame,commands,rejected=build_candidates(cards,ext,seeds["main"],seeds["commanders"],can,result["frequencies"],config.get("overrides"))
    assert not rejected,rejected
    if set(config.get("overrides",{}))-set(frame.oracle_id):raise ValueError("Overrides for excluded card categories need separate review")
    frame["main_deck_points_before_cutoff"]=np.ceil(frame.main_deck_impact).astype(int)
    frame["command_zone_points_before_cutoff"]=[math.ceil(s) if pd.notna(s) else None for s in frame.command_zone_impact]
    frame["main_deck_points"]=[configured_price(o,"main",s,config["main_threshold"],config["curve"]) for o,s in zip(frame.oracle_id,frame.main_deck_impact)]
    frame["command_zone_points"]=[configured_price(o,"commanders",s,config["commander_threshold"],config["curve"]) if pd.notna(s) else 0 for o,s in zip(frame.oracle_id,frame.command_zone_impact)]
    frame["recommended_point_bearing_status"]=np.select([(frame.main_deck_points>0)&(frame.command_zone_points>0),frame.main_deck_points>0,frame.command_zone_points>0],["both","main_deck","command_zone"],default="unpointed")
    frame["league_card_legal"]=(frame.commander_legality=="legal")&~frame.two_hg_specific_ban
    frame.loc[~frame.league_card_legal&(frame.recommended_point_bearing_status!="unpointed"),"recommended_point_bearing_status"]="hypothetical_banned_"+frame.loc[~frame.league_card_legal&(frame.recommended_point_bearing_status!="unpointed"),"recommended_point_bearing_status"]
    mb=price_boundaries(config["main_threshold"],config["curve"]);cb=price_boundaries(config["commander_threshold"],config["curve"])
    frame["nearest_main_price_boundary_distance"]=[min(abs(s-b) for b in mb) for s in frame.main_deck_impact]
    frame["nearest_commander_price_boundary_distance"]=[min(abs(s-b) for b in cb) if pd.notna(s) else None for s in frame.command_zone_impact]
    frame.loc[(frame.nearest_main_price_boundary_distance<=.5)|(frame.nearest_commander_price_boundary_distance<=.5),"manual_review_priority"]="high"
    frame["rank_certainty"]="provisional_tied_or_close_judgment"
    frame.loc[~frame.manually_assessed,"rank_certainty"]="low_unreviewed_tail_prior"
    frame["point_list_version"]=config["version"]
    commands=frame[frame.command_zone_impact.notna()].sort_values(["command_zone_impact","card_name"],ascending=[False,True]).copy()
    commands["command_zone_rank"]=range(1,len(commands)+1)
    lookup=frame.set_index("oracle_id").to_dict("index")
    precons=json.load(open(root/"commander-league-card-point-calibration/data/clean/precons.json"))
    pdmeta=pd.read_csv(root/"commander-league-card-point-calibration/commander_precon_scores.csv").set_index("name").to_dict("index")
    decks=[]
    for d in precons:
        cmd=set(d["commander_ids"])
        decks.append({"name":d["name"],"main":{o:q for o,q in d["counts"].items() if o not in cmd},"commanders":{o:q for o,q in d["counts"].items() if o in cmd},"cohort":"official_precons","event_id":"","source":d.get("source",""),"year":d["release_year"] if "release_year" in d else d.get("year",pdmeta[d["name"]]["release_year"])})
    cohort_counts={}
    for cohort,entries in pools.items():
        if cohort=="cedh_train":continue
        unique={}
        for d in entries:
            normalized={k:{index.resolve(n):q for n,q in d[k].items()} for k in ("main","commanders")}
            key=json.dumps(normalized,sort_keys=True)
            unique.setdefault(key,{"name":cohort+"_"+hashlib.sha256(key.encode()).hexdigest()[:16],"cohort":cohort,"event_id":d["event_id"],"source":"https://topdeck.gg","year":int(d["date"][:4]),**normalized})
        decks+=list(unique.values())
        cohort_counts[cohort]={"registrations":len(entries),"unique_lists":len(unique)}
    policies=[]
    for k in (50,100,200,300,400,500,750,1000):
        tau=float(frame.iloc[k-1].main_deck_impact)-1e-5
        policies.append((f"rank_{k}_include_ties",tau,tau,"tiered",False))
    for tau in (65,70,75,80,85,90):
        for curve in ("linear","tiered","quadratic"):
            policies.append((f"threshold_{tau}_{curve}",tau,tau,curve,False))
    policies.append(("threshold_75_tiered_no_specialist_floor",75,75,"tiered",True))
    policies.append(("configured_policy",config["main_threshold"],config["commander_threshold"],config["curve"],False))
    policies.append(("configured_policy_no_specialist_floor",config["main_threshold"],config["commander_threshold"],config["curve"],True))
    backend=SparseBackend(index,frame,config)
    legality={}
    for d in decks:
        r=backend.score(d);legality[d["name"]]=r
    def score_deck(d,tau,ctau,curve,raw=False):
        contributions=[];cmdpoints=0;pointed=0
        for zone in ("main","commanders"):
            for oid,q in d[zone].items():
                row=lookup.get(oid,{})
                field="command_zone_impact" if zone=="commanders" else "raw_main_deck_impact" if raw else "main_deck_impact"
                s=row.get(field);points=configured_price(oid,zone,s if s is not None and pd.notna(s) else 0,ctau if zone=="commanders" else tau,curve)
                contributions.append(points*q);pointed+=q*(points>0)
                if zone=="commanders":cmdpoints+=points*q
        total=sum(contributions)
        return {"total_points":total,"command_zone_points":cmdpoints,"pointed_card_count":pointed,"command_zone_share":cmdpoints/total if total else 0,"top3_point_share":sum(sorted(contributions,reverse=True)[:3])/total if total else 0}
    bench=[];comparisons=[]
    for label,tau,ctau,curve,raw in policies:
        basefield="raw_main_deck_impact" if raw else "main_deck_impact"
        for d in decks:
            r=score_deck(d,tau,ctau,curve,raw)
            bench.append({"policy":label,"deck_name":d["name"],"cohort":d["cohort"],"release_year":d["year"],"source":d["source"],"event_id":d["event_id"],"officially_legal":legality[d["name"]]["officially_legal"],"legality_flags":";".join(legality[d["name"]]["legality_issues"]),**r})
        for cohort in ("official_precons","cedh_holdout","bracket3_declared"):
            rows=[r for r in bench if r["policy"]==label and r["cohort"]==cohort]
            vals=np.array([r["total_points"] for r in rows])
            legalvals=[r["total_points"] for r in rows if r["officially_legal"]]
            main_count=sum(configured_price(o,"main",s,tau,curve)>0 for o,s in zip(frame.oracle_id,frame[basefield]))
            cmd_count=sum(configured_price(o,"commanders",s,ctau,curve)>0 for o,s in zip(commands.oracle_id,commands.command_zone_impact))
            comparisons.append({"policy":label,"cohort":cohort,"main_threshold":tau,"command_zone_threshold":ctau,"curve":curve,"specialist_floor":not raw,"main_pointed_cards":main_count,"pointed_commander_options":cmd_count,"deck_count":len(vals),"legal_deck_count":len(legalvals),"legal_deck_median":float(np.median(legalvals)) if legalvals else None,"median":float(np.median(vals)),"mean":float(vals.mean()),"p10":float(np.quantile(vals,.1)),"p25":float(np.quantile(vals,.25)),"p75":float(np.quantile(vals,.75)),"p90":float(np.quantile(vals,.9)),"std":float(vals.std(ddof=1)),"minimum":int(vals.min()),"maximum":int(vals.max()),"zero_decks":int(sum(vals==0)),"unique_totals":len(set(vals)),"median_pointed_cards":float(np.median([r["pointed_card_count"] for r in rows])),"median_command_zone_share":float(np.median([r["command_zone_share"] for r in rows])),"median_top3_share":float(np.median([r["top3_point_share"] for r in rows]))})
    benchmark=pd.DataFrame(bench);comparison=pd.DataFrame(comparisons)
    recommended=benchmark[benchmark.policy=="configured_policy"]
    pc=recommended[recommended.cohort=="official_precons"]
    valrows=[]
    for filename,col in [("validation.csv","community_rank"),("reddit_validation.csv","author_rank")]:
        v=pd.read_csv(root/"commander-league-card-point-calibration/data/clean"/filename)
        scores=np.array([float(pc.set_index("deck_name").loc[n].total_points) for n in v.name])
        strengths=-v[col].to_numpy(dtype=float)
        pairs=[(i,j) for i in range(len(scores)) for j in range(i+1,len(scores))]
        accuracy=np.mean([.5 if scores[i]==scores[j] else float((scores[i]-scores[j])*(strengths[i]-strengths[j])>0) for i,j in pairs])
        rho=float(st.spearmanr(scores,strengths).statistic) if len(set(scores))>1 else None
        tau=float(st.kendalltau(scores,strengths).statistic) if len(set(scores))>1 else None
        rng=np.random.default_rng(19026);boot=[]
        for _ in range(1000):
            ix=rng.integers(0,len(scores),len(scores))
            if len(set(scores[ix]))>1 and len(set(strengths[ix]))>1:boot.append(float(st.spearmanr(scores[ix],strengths[ix]).statistic))
        valrows.append({"source":filename,"n":len(scores),"spearman":rho,"kendall":tau,"pairwise_ties_half_credit":float(accuracy),"bootstrap_rho_p025":float(np.quantile(boot,.025)) if boot else None,"bootstrap_rho_p975":float(np.quantile(boot,.975)) if boot else None,"independence":"reused diagnostic, not untouched validation; only four-player reviewer opinions","decks":[{"name":n,"points":int(s)} for n,s in zip(v.name,scores)]})
    # Shared card perturbations, fixed seed: uncertainty scenarios, not sampling CIs.
    rng=np.random.default_rng(19026);sensitivity=[]
    current=set(frame.loc[frame.main_deck_points>0,"oracle_id"])
    manual=frame.manually_assessed.to_numpy()
    baseline_scores=frame.main_deck_impact.to_numpy()
    for _ in range(200):
        noise=rng.uniform(-2,2,len(frame));noise[~manual]=0
        pert=np.clip(baseline_scores+noise,0,100)
        pointed=set(o for o,s in zip(frame.oracle_id,pert) if configured_price(o,"main",s,config["main_threshold"],config["curve"])>0)
        sensitivity.append({"pointed_main":len(pointed),"jaccard":len(current&pointed)/len(current|pointed)})
    changed_main=frame[frame.specialist_floor_delta>0]
    mandatory=frame[(frame.canadian_highlander_points>0)|frame.game_changer]
    assert mandatory.manually_assessed.all()
    assert frame.oracle_id.is_unique
    assert frame.head(100).manually_assessed.all()
    assert commands.head(50).command_zone_manually_assessed.all()
    assert all(index.cards[o]["legalities"]["commander"] in ("legal","banned") for o in frame.oracle_id)
    assert len(pc)==174
    for d in decks:assert sum(d["main"].values())+sum(d["commanders"].values())==100
    summary={"as_of":"2026-10-19","candidate_count":len(frame),"main_manual_assessments":int(frame.manually_assessed.sum()),"commander_manual_assessments":int(commands.command_zone_manually_assessed.sum()),"command_zone_options":len(commands),"top1000_unreviewed":int((~frame.head(1000).manually_assessed).sum()),"main_pointed":int((frame.main_deck_points>0).sum()),"commander_pointed":int((frame.command_zone_points>0).sum()),"pointed_union":int(((frame.main_deck_points>0)|(frame.command_zone_points>0)).sum()),"official_named_bans":int((frame.commander_legality=="banned").sum()),"canlander_count":int((frame.canadian_highlander_points>0).sum()),"game_changer_count":int(frame.game_changer.sum()),"cohorts":cohort_counts,"ingestion":{k:v for k,v in result.items() if k not in ("pools","events","frequencies","exclusion_records")},"validation":valrows,"sensitivity":{"runs":200,"main_point_count_min":min(r["pointed_main"] for r in sensitivity),"main_point_count_max":max(r["pointed_main"] for r in sensitivity),"median_jaccard":float(np.median([r["jaccard"] for r in sensitivity])),"scenario":"independent uniform impact +/-2 on manually assessed cards, no rerating of raw cache tail"},"specialist_floor_affected_cards":len(changed_main),"recommended_cohorts":comparison[comparison.policy=="configured_policy"].to_dict("records"),"top_legal_main":frame[frame.commander_legality=="legal"].head(15)[["card_name","main_deck_impact","main_deck_points"]].to_dict("records"),"top_commanders":commands.head(20)[["card_name","main_deck_points","command_zone_impact","command_zone_points","commander_legality"]].to_dict("records")}
    files={}
    def csv(name,df):files[name]=df.to_csv(index=False)
    csv("candidate_inventory.csv",frame)
    csv("top_1000_main_deck_cards.csv",frame.head(1000))
    csv("top_commanders.csv",commands)
    csv("proposed_point_schedule.csv",frame[(frame.main_deck_points>0)|(frame.command_zone_points>0)])
    csv("proposed_legal_point_schedule.csv",frame[frame.league_card_legal&((frame.main_deck_points>0)|(frame.command_zone_points>0))])
    csv("cutoff_comparison.csv",comparison)
    csv("precon_cutoff_benchmarks.csv",benchmark[benchmark.cohort=="official_precons"])
    csv("additional_deck_cutoff_benchmarks.csv",benchmark[benchmark.cohort!="official_precons"])
    csv("annual_precon_statistics.csv",pc.groupby("release_year").total_points.agg(["count","mean","median","std","min","max"]).reset_index())
    csv("cutoff_boundary_review.csv",frame[abs(frame.main_deck_impact-config["main_threshold"])<=5])
    csv("price_tier_boundary_review.csv",frame[(frame.nearest_main_price_boundary_distance<=.5)|(frame.nearest_commander_price_boundary_distance<=.5)])
    csv("manual_review_queue.csv",frame[(frame.manual_review_priority=="high")|((frame.main_deck_impact-config["main_threshold"]).abs()<=5)|((frame.command_zone_impact-config["commander_threshold"]).abs()<=5)])
    csv("source_exclusions.csv",pd.DataFrame(result["exclusion_records"]))
    csv("specialist_floor_sensitivity.csv",changed_main[["card_name","raw_main_deck_impact","main_deck_impact","specialist_floor_delta","main_deck_points"]])
    csv("color_and_archetype_concentration.csv",frame[frame.main_deck_points>0].groupby(["color_identity","category"]).agg(cards=("oracle_id","count"),points=("main_deck_points","sum")).reset_index())

    old=pd.read_csv(root/"commander-league-card-point-calibration/experimental_unban_review.csv")
    bans=frame[frame.commander_legality=="banned"].merge(old[["oracle_id","assessment","effect_2hg","early_win_or_lock","recommendation"]],on="oracle_id",how="left",validate="one_to_one")
    bans["legalized"]=False;bans["price_confidence"]="low_provisional_judgment";bans["legality_source"]="https://magic.wizards.com/en/banned-restricted-list"
    csv("experimental_unban_ranking.csv",bans)
    legalmask=(frame.commander_legality=="legal")&~frame.two_hg_specific_ban
    summary["legal_2hg_pointed_main"]=int((legalmask&(frame.main_deck_points>0)).sum())
    summary["legal_2hg_pointed_commanders"]=int((legalmask&(frame.command_zone_points>0)).sum())
    summary["legal_2hg_pointed_union"]=int((legalmask&((frame.main_deck_points>0)|(frame.command_zone_points>0))).sum())
    summary["precon_legality_flags"]=[{"name":d["name"],"issues":legality[d["name"]]["legality_issues"]} for d in decks if d["cohort"]=="official_precons" and not legality[d["name"]]["officially_legal"]]
    details={cohort:recommended[recommended.cohort==cohort].sort_values("total_points").iloc[[0,-1]][["deck_name","total_points"]].to_dict("records") for cohort in ("cedh_holdout","bracket3_declared")}
    wanted={row["deck_name"] for rows in details.values() for row in rows}|{"Mutant Menace","Science!","Explorers of the Deep","Necron Dynasties","From Cute to Brute"}
    files["representative_deck_breakdowns.json"]=json.dumps({d["name"]:{"input":{k:d[k] for k in ("main","commanders")},"report":legality[d["name"]]} for d in decks if d["name"] in wanted},indent=2)
    summary["additional_cohort_extremes"]=details
    summary["unreviewed_cache_only_pointed"]=int(((~frame.manually_assessed)&(frame.main_deck_points>0)).sum())
    summary["tier_boundary_review_cards"]=int(((frame.nearest_main_price_boundary_distance<=.5)|(frame.nearest_commander_price_boundary_distance<=.5)).sum())
    # Reused pair assessments were already inspected in v1; diagnostic, never independent final validation.
    pairdata=json.load(open(root/"commander-card-power-research-v1/data/benchmark_inputs.json"))["pairs"]
    scoremap=pc.set_index("deck_name").total_points.to_dict()
    summary["reused_pair_checks"]=[{"stronger":x,"weaker":y,"points_stronger":int(scoremap[x]),"points_weaker":int(scoremap[y]),"credit":float(scoremap[x]>scoremap[y]) if scoremap[x]!=scoremap[y] else .5} for x,y in pairdata]
    summary["reused_pair_accuracy"]=float(np.mean([p["credit"] for p in summary["reused_pair_checks"]]))
    # Audit omitted high-adoption cards, without using adoption as a scoring feature.
    omission=frame[(frame.main_deck_rank>1000)&(frame.competitive_registration_count>0)].sort_values("competitive_registration_count",ascending=False).head(100)
    csv("omission_audit.csv",omission)
    source_paths=["commander-top1000-power-ranking/data/rules_source.json","commander-top1000-power-ranking/data/name_aliases.json","commander-top1000-power-ranking/data/name_alias_provenance.json","commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz","commander-league-card-point-calibration/data/clean/precons.json","commander-card-power-research-v1/data/zarzak_cache.json","commander-card-power-research-v1/data/benchmark_inputs.json","data/tournament_snapshots/topdeck/manifest.json"]
    manifest={p:{"sha256":hashlib.sha256((root/p).read_bytes()).hexdigest(),"source_snapshot_as_of":"2026-10-19"} for p in source_paths}
    manifest["notes"]="TopDeck raw-snapshot paths and content-addressed hashes remain in the existing manifest. No API calls or paid services required for reproduction."
    import platform,importlib.metadata
    manifest["execution_environment"]={"python":platform.python_version(),"packages":{n:importlib.metadata.version(n) for n in ("numpy","pandas","scipy","matplotlib")}}
    manifest["config_sha256"]=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    manifest["assessment_sha256"]=hashlib.sha256(json.dumps(seeds,sort_keys=True).encode()).hexdigest()
    here=pathlib.Path(__file__).resolve().parent
    manifest["implementation_sha256"]={name:hashlib.sha256((here/name).read_bytes()).hexdigest() for name in ("ranking.py","backend.py","data_sources.py","pipeline.py","extended_analysis.py","score_decks.py","requirements.txt")}
    manifest["source_urls"]={"oracle":"https://scryfall.com/docs/api/bulk-data","precons":"https://github.com/taw/magic-preconstructed-decks-data","published_ratings":"https://github.com/zarzak/mtg-deck-builder/tree/2ccb39f3e0fa08d91e848c2c98851effa8fa1fb2","canadian_points":"https://canadianhighlander.ca/points-list/","tournament_snapshots":"https://topdeck.gg","rules":"https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt"}
    files["source_provenance.json"]=json.dumps(manifest,indent=2)
    files["analysis_summary.json"]=json.dumps(summary,indent=2,allow_nan=False)
    if not render_plot:return files,summary,index,frame,commands,benchmark,comparison,decks
    # Figure rendered directly to bytes; no pyplot cache or output file required.
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig=Figure(figsize=(13,9),layout="constrained");FigureCanvasAgg(fig)
    ax=fig.subplots(2,2)
    ax[0,0].plot(frame.main_deck_rank.iloc[:1500],frame.main_deck_impact.iloc[:1500]);ax[0,0].axhline(config["main_threshold"],color="red",linestyle="--");ax[0,0].set(xlabel="Main-deck rank (ties alphabetic)",ylabel="Judgment impact",title="No demonstrated natural break; tail prior is coarse")
    for cohort in ("official_precons","bracket3_declared","cedh_holdout"):
        vals=recommended[recommended.cohort==cohort].total_points
        ax[0,1].hist(vals,bins=30,alpha=.45,label=cohort)
    ax[0,1].set(xlabel="Tiered construction points",ylabel="Decks",title="Different cohorts; not win probabilities");ax[0,1].legend(fontsize=8)
    t=comparison[(comparison.cohort=="official_precons")&(comparison.curve=="tiered")&comparison.policy.str.startswith("threshold_")&comparison.specialist_floor]
    ax[1,0].plot(t.main_threshold,t["median"],marker="o");ax[1,0].set(xlabel="Impact threshold",ylabel="Median precon points",title="Threshold policy changes the scale")
    a=pc.groupby("release_year").total_points.agg(["median","mean"])
    ax[1,1].plot(a.index,a["median"],label="median",marker="o");ax[1,1].plot(a.index,a["mean"],label="mean");ax[1,1].set(xlabel="Release year",ylabel="Precon points",title="Fixed card prices across years");ax[1,1].legend()
    png=io.BytesIO();fig.savefig(png,format="png",dpi=150)
    files["ranking_visualizations.png"]={"base64":base64.b64encode(png.getvalue()).decode()}
    return files,summary,index,frame,commands,benchmark,comparison,decks

def render_reports(files,summary,frame,commands,benchmark,comparison,decks,config):
    def table(df,cols=None,limit=None):
        d=df if cols is None else df[cols]
        if limit is not None:d=d.head(limit)
        def fmt(x):
            if isinstance(x,float):return f"{x:.3f}" if math.isfinite(x) else ""
            return str(x).replace("|","/").replace("\n"," ")
        return "\n".join(["| "+" | ".join(map(str,d.columns))+" |","| "+" | ".join(["---"]*len(d.columns))+" |"]+["| "+" | ".join(fmt(v) for v in row)+" |" for row in d.itertuples(index=False,name=None)])
    recommendation=comparison[(comparison.policy=="configured_policy")]
    pc=benchmark[(benchmark.policy=="configured_policy")&(benchmark.cohort=="official_precons")]
    quotas=comparison[(comparison.cohort=="official_precons")&comparison.policy.str.startswith("rank_")]
    fixed=comparison[(comparison.cohort=="official_precons")&(comparison.curve=="tiered")&comparison.policy.str.startswith("threshold_")]
    schedule=frame[(frame.main_deck_points>0)|(frame.command_zone_points>0)]
    boundary=frame[(frame.main_deck_impact-config["main_threshold"]).abs()<=2].sort_values(["main_deck_impact","card_name"],ascending=[False,True])
    md_count=int((frame.main_deck_points>0).sum());cz_count=int((frame.command_zone_points>0).sum())
    outside=int(((schedule.main_deck_rank>1000)&(schedule.command_zone_points>0)).sum())
    files["card_ranking_methodology.md"]=f"""# Candidate ranking methodology — 2026-10-19

This is a provisional candidate ranking and reviewed sparse pricing experiment. It does not establish the true 1,000 strongest cards. {summary['top1000_unreviewed']} entries in the requested top 1,000 remain low-confidence external-cache priors. Top 100 main-deck entries, top 50 command-zone entries, all currently pointed entries, all 46 Canadian Highlander pointed cards and all 53 Oracle Game Changers have explicit agent-authored rubric assessments. Independent agent review checked rules and selected leading valuations; it is not independent performance validation or certification of every card.

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

The specialist safeguard sets s at least 80 when C>=9.5. This is an explicit policy floor to retain exceptional narrow cards, not an observed break. raw_main_deck_impact and specialist_floor_delta preserve its effect. The no-floor benchmark is mandatory. {summary['specialist_floor_affected_cards']} card assessments are changed by the floor.

The unreviewed tail maps external rating r to C=clip((r-35)/8,0,7.5); absent r defaults to60, and A/T/R remain neutral placeholders5. This caps unreviewed main impact at63.75, below the recommended75 cutoff. It supplies candidate ordering only, not reviewed strength. Unreviewed commander prior is min(69,main+4), also below cutoff. All basics, including snow-covered basics, have zero main impact/price. Those numerical fallback constants are editable in scoring_config.json. No source prior alone points a card under the recommended policy. Lower exploratory thresholds can expose those unreviewed priors and must not be adopted without review.

## Command zone

Separate assessments use the same numeric rubric but C includes guaranteed strategic access; A evaluates viable construction breadth/color implications; T includes deployment, summoning sickness and realistic activations; R includes repeated access, removal and generic recast tax. Scores are alternatives by location, never a surcharge. Examples include main-free Rograkh or Inalla but pointed command-zone access. Independent partner prices sum; no pairing/context/team premium is added. Omitted or unreviewed commanders remain a material uncertainty.

Eligibility follows front-face legendary creatures, current legendary Vehicle and qualifying Spacecraft rules, explicit permission planeswalkers, Grist, conditional Backgrounds, and matching current partner families. Pair compatibility is separate from eligibility and ban legality. Doctor's companion requires a legendary Time Lord Doctor without extra creature types. DFCs retain one Oracle identity; back faces do not independently confer eligibility.

## Pricing and uncertainty

Recommended candidate threshold is >75 in both locations; gap bands <=5/10/15/20/25 receive1/3/5/8/12 points. Linear and quadratic alternatives are benchmarked. 'Before cutoff points' are ceil(impact), a display-only initial scale, not a league budget. No per-deck/year normalization and no 1,000-point anchor are used. A quarter-point judgment at a band edge can change price substantially, so tier-boundary review is required. Manual Oracle-ID overrides are explicit exceptions. Equal-impact ties sort alphabetically only for deterministic CSV ranks; nearby ranks do not establish meaningful distinctions.

The schedule union contains {len(schedule)} identities: {md_count} main-deck pointed and {cz_count} command-zone pointed options, with overlap. {outside} pointed command-zone options fall outside the main-deck top1,000 and remain included. Hypothetically scored banned cards retain banned status; category bans for ante, Conspiracy and offensive content are not experimental unban candidates.

## Statistical design

Coefficients were not optimized on the precon reviewer rankings. Reused six/five-deck and five-pair assessments are diagnostics already seen during development, not untouched final validation. cEDH-labelled October events are held out from the before-October frequency nominations, but ratings/judgment are not blinded to known competitive archetypes and this is not a trained win predictor. Complete deck and basic legality checks run independently. Bootstrap reviewer correlations use1,000 deck resamples with seed19026; tiny tied opinion samples have wide intervals. Sensitivity uses200 independent uniform +/-2 impact scenarios on reviewed cards; it is a scenario analysis, not a confidence interval. Missing standardized 2HG outcomes prevents win-rate calibration.

Separate players retain mana, hands and permanents. Shared turns/life are not shared resource ownership. Full rules subtleties beyond the backend's explicit sanity checks require judge review; no simulation was run.
"""
    files["point_cutoff_analysis.md"]=f"""# Point cutoff experiments

Recommendation: test the active {config['curve']} policy with main threshold >{config['main_threshold']} and command-zone threshold >{config['commander_threshold']} as a versioned candidate schedule, not a strict validated cap. It selects {md_count} main-deck cards and {cz_count} command-zone options ({len(schedule)} identities in their union, including hypothetical banned cards). The currently Commander-legal and 2HG-legal portion contains {summary['legal_2hg_pointed_union']} identities ({summary['legal_2hg_pointed_main']} main and {summary['legal_2hg_pointed_commanders']} command-zone). No convincing empirical natural break was demonstrated. The specialist floor and coarse source priors create artificial concentrations; they cannot justify a natural threshold.

The policy separates exceptional resource access from ordinary utility and leaves most known cards free. Top50–100 policies leave many efficient specialist engines free and collapse most precons to Sol Ring alone. Top750–1,000 policies reach unreviewed source priors and inflate apparent precision. The middle range is a policy tradeoff, not an optimum inferred from precon separation.

## Rank-quota policies (all ties included)

{table(quotas,['policy','main_threshold','main_pointed_cards','pointed_commander_options','median','p10','p90','unique_totals'])}

Rank quotas use the main-deck threshold for both locations. They do not force the commander count to equal the quota.

## Fixed cutoffs and no-floor check

{table(fixed,['policy','main_pointed_cards','pointed_commander_options','median','p10','p90','unique_totals'])}

Linear max(0,ceil(s-tau)) and quadratic ceil(20*((s-tau)/(100-tau))**2) are in cutoff_comparison.csv. Their units differ; comparing raw totals is not evidence one predicts strength better. No deck/year-specific normalization was applied.

## Recommended-policy cohort construction costs

{table(recommendation,['cohort','deck_count','legal_deck_count','median','p10','p90','median_pointed_cards','median_command_zone_share','median_top3_share'])}

The B3 labels are event/user declarations, not Wizards-verified brackets. cEDH event names are a selection heuristic; no identified data demonstrate maximum 2HG competitive outcomes. Events require at least one completed pod, not proof the entire event completed. Temporal filtering excludes future events; absent structured decklists are excluded, not filled with zeros.

## Boundary review

{table(boundary,['card_name','main_deck_impact','main_deck_points','category'],40)}

See full cutoff_boundary_review.csv, price_tier_boundary_review.csv and manual_review_queue.csv. The price band boundaries at80/85/90/95 need as much review as75. Examples of unpointed specialized conversion pieces are Squirrel Nest, ordinary win payoffs and narrow enablement without exceptional independent conversion; Spellbook membership alone is not priced. Thassa's Oracle, Underworld Breach and efficient specialty tutors remain pointed. Lock/early-loss cards need separate legality review even if cheap under the rubric.

## Sensitivity and limitations

{summary['sensitivity']['runs']} +/-2 judgment-impact scenarios yield {summary['sensitivity']['main_point_count_min']}–{summary['sensitivity']['main_point_count_max']} main-deck pointed cards, median set Jaccard {summary['sensitivity']['median_jaccard']:.3f}. This does not capture correlated judgment error or omitted strategies. No-floor results expose the explicit safeguard's effect. Equal functional cycles, basic lands and Oracle duplication are automated checks. Color/archetype concentration is in color_and_archetype_concentration.csv; categories are analyst labels, not measured archetype balance.

A strict team cap is premature. Start by collecting real paired 2HG lists, match context and legal combo adjudications under a frozen version; inspect zero-point competitive examples and boundary disputes. Do not turn observed cohort medians into official bracket cutoffs or a 2,000-point team budget.
"""
    annual=pc.groupby("release_year").total_points.agg(["count","mean","median","std","min","max"]).reset_index()
    val=pd.DataFrame([{k:v for k,v in x.items() if k!="decks"} for x in summary["validation"]])
    representative=pc[pc.deck_name.isin(["Mutant Menace","Science!","Explorers of the Deep","Necron Dynasties","From Cute to Brute"])]
    bad=pc[~pc.officially_legal][["deck_name","legality_flags"]]
    files["benchmark_analysis.md"]=f"""# Candidate schedule benchmark

All174 archived precons were scored at fixed Oracle-ID prices, including their separate command zones. They are official product lists, not automatically all Bracket2. Precon guidance was decoupled from Bracket2, and current Game Changer/ban status is preserved separately.

{table(recommendation,['cohort','deck_count','median','p10','p90','mean','std','unique_totals','median_pointed_cards'])}

Of174 precons,171 pass this backend's current basic legality checks. Flags are reported rather than dropping historical products:

{table(bad)}

The precon median is concentrated in ubiquitous Sol Ring; the median top-three contribution share is100%. There are only {int(recommendation[recommendation.cohort=='official_precons'].iloc[0].unique_totals)} distinct precon totals. This is consistent with sparse resource pricing but a poor tool for ranking synergy-driven precon effectiveness.

## Existing reviewer diagnostics

{table(val)}

Six-deck assessment source: https://cloudflare.edhrec.com/articles/the-best-commander-precons-of-2024 . Five-deck assessment source: https://www.reddit.com/r/EDH/comments/1eetahl/redhs_best_precon_commanders_of_all_time/ . These are existing cached opinions, not win records. Tie credit is one half in pairwise accuracy. No improvement is claimed when a tiny diagnostic fails. Five previously inspected comparative pairs give accuracy {summary['reused_pair_accuracy']:.3f}; full cases are in analysis_summary.json.

## Difficult representative cases

{table(representative,['deck_name','total_points','command_zone_points','pointed_card_count','top3_point_share'])}

Mutant Menace, Explorers and Necrons can be strong through synergy that the budget intentionally leaves uncharged. Science! being tied with or above them is a known resource-score/holistic-strength discrepancy, not concealed evidence of a successful power predictor.

## Historical fixed-price trend

{table(annual)}

Year is not an input to card prices. Small annual cohorts and uneven product selection prevent a simple causal power-creep claim. Detailed distributions, quota sensitivities, no-floor checks, external labelled cohorts and versioned prices are in the CSV outputs. Original v0.2 and v1 research remain untouched for comparison.

## Data access, exclusions and generalization

TopDeck.gg attribution: https://topdeck.gg . Existing manifest entries={summary['ingestion']['event_manifest_count']}; eligible name/date/size/pod event candidates={summary['ingestion']['eligible_event_count']}. Training registrations={summary['ingestion']['cohort_deck_counts']['cedh_train']}; holdout registrations={summary['cohorts']['cedh_holdout']['registrations']}, deduplicated lists={summary['cohorts']['cedh_holdout']['unique_lists']}; declared-B3 registrations={summary['cohorts']['bracket3_declared']['registrations']}, lists={summary['cohorts']['bracket3_declared']['unique_lists']}. Missing structured decks and unresolved/not100 records are excluded with exact counts in analysis_summary.json. No synthetic placeholder-ID repository deck was treated as an empirical sample.

Holdout means October lists were excluded from frequency nomination data. No weights were trained on tournament outcomes. Deck identities can recur across time; deduplication is within cohort, so this is not a commander/archetype-isolated predictive holdout. Missing decks, submitted-list quality and event selection create selection bias. No reliable intermediate 'upgraded precon/high-power/optimized' labelled cohorts were verified; the available B3 declarations cannot fill that gap. No 2HG match outcomes were obtained.

## Initial league test

Use the candidate schedule only after reviewing current legality, the high-priority queue and actual team lists. Preserve zero teammate/in-deck synergy premiums, but adjudicate controller-specific combos and team-turn locks independently. A construction budget cannot make intrinsically unacceptable play patterns acceptable.
"""
    files["README.md"]=f"""# Commander Top1,000 Power Ranking — candidate v0.1

A reproducible main-deck candidate ranking, separate command-zone ranking and sparse construction-price experiment. Earlier project directories are unchanged.

The principal CSV contains exactly1,000 rows; the full candidate inventory contains {len(frame)} identities. {summary['top1000_unreviewed']} top1,000 rows remain explicitly low-confidence priors. The candidate pointed union contains {len(schedule)} identities, not a claim that the exact ordering or a strict cap is validated. Banned cards retain banned status. No price/team synergy premium is added.

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
{{"overrides":{{"ORACLE-ID":{{"main_deck_points":3,"command_zone_points":8}}}}}}
```

Use an actual Oracle ID from the CSV. A full config is accepted with --config. Overrides do not legalize a banned card or create commander eligibility. Team and individual caps are optional CLI parameters; none is empirically calibrated here. Scores are integer construction resources, not win probabilities. Existing HTML calculator is preserved; score_decks.py is the new offline backend interface.

## Files and caveats

Read card_ranking_methodology.md, point_cutoff_analysis.md and benchmark_analysis.md first. proposed_point_schedule.csv includes all pointed command-zone cards even outside the main top1,000. candidate_inventory.csv includes low-confidence evaluated candidates that missed the1,000. experimental_unban_ranking.csv is hypothetical research only. omission_audit.csv and manual_review_queue.csv expose unresolved work.

Source provenance includes current URLs, retrieval/snapshot date and local SHA-256. Existing source notices continue to apply: card text is Wizards material; MIT code/cache source notices are retained in prior directories; Canadian Highlander publication is expert reference, not an invented blanket open-data license; TopDeck.gg attribution is required. No restricted EDHREC bulk scraping or proprietary evaluator extraction was performed.

The independent rules review is qualitative. The backend checks deck size, commander eligibility/pairing, color identity, singleton/basic-type restrictions and present bans. It is not a complete rules engine, judge certification, companion validator or gameplay simulator. Pregame color-choice commanders are flagged for unresolved input. Update current Oracle/rules/ban snapshots before a league release; do not silently mutate a running list.
"""
    return files

def main():
    here=pathlib.Path(__file__).resolve().parent
    seeds=json.load(open(here/"analyst_assessments.json"))
    config=json.load(open(here/"scoring_config.json"))
    files,summary,index,frame,commands,benchmark,comparison,decks=analyse(here.parent,seeds,config)
    render_reports(files,summary,frame,commands,benchmark,comparison,decks,config)
    from extended_analysis import extend_analysis
    extend_analysis(files,summary,index,frame,commands,benchmark,comparison,decks,config)
    for name,content in files.items():
        destination=here/name;destination.parent.mkdir(parents=True,exist_ok=True)
        if isinstance(content,dict) and "base64" in content:destination.write_bytes(base64.b64decode(content["base64"]))
        else:destination.write_text(content)
    print(json.dumps(summary,indent=2,allow_nan=False))
if __name__=="__main__":main()
