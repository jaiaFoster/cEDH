"""Reproduce the final audit from frozen repository inputs; no network required.
Outputs are season0-proposed and do not activate league rules.
"""
import collections,copy,gzip,hashlib,io,json,math,pathlib,sys
import numpy as np
import pandas as pd
from scipy import stats
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/"commander-top1000-power-ranking"))
from ranking import OracleIndex,eligibility,oracle_text
from backend import SparseBackend
from data_sources import acquire_local
from audit_backend import AuditBackend,proposed_price

def mdtable(rows,cols):
    def fmt(v):
        if isinstance(v,float):return str(round(v,3))
        return str(v).replace("|","/").replace("\n"," ")
    return "\n".join(["| "+" | ".join(cols)+" |","| "+" | ".join("---" for _ in cols)+" |"]+
                     ["| "+" | ".join(fmt(r.get(c,"")) for c in cols)+" |" for r in rows])
def serial(v):
    return json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+"\n"
def generate(root,inputs):
    root=pathlib.Path(root);files={}
    result,pools,cards=acquire_local(root);index=OracleIndex(cards)
    frame=pd.read_csv(root/"commander-top1000-power-ranking/candidate_inventory.csv")
    base=SparseBackend(index,frame)
    inputs=copy.deepcopy(inputs)
    # Resolve every nominated identity; no unknown card may silently become zero.
    for a in inputs["anchors"]+inputs["family"]+inputs["unbans"]:a["oracle_id"]=index.resolve(a["card_name"])
    for c in inputs["combos"]:
        c["oracle_ids_A"]=[index.resolve(n) for n in c["cards_A"]]
        c["oracle_ids_B"]=[index.resolve(n) for n in c["cards_B"]]
    for t in inputs["teams"]:
        for field in ("main_A","main_B","commanders_A","commanders_B"):
            for n in t[field]:index.resolve(n)
    overrides={};reasons={}
    for a in inputs["family"]:
        overrides.setdefault(a["oracle_id"],{})["main_deck_points"]=a["main_deck_points"]
        reasons[(a["oracle_id"],"main")]=a["rationale"]
    for a in inputs["anchors"]:
        field="main_deck_points" if a["zone"]=="main" else "command_zone_points"
        overrides.setdefault(a["oracle_id"],{})[field]=a["proposed_points"]
        reasons[(a["oracle_id"],a["zone"])]=a["rationale"]
    for a in inputs["unbans"]:
        overrides.setdefault(a["oracle_id"],{})["main_deck_points"]=a["hypothetical_main_deck_points"]
        reasons[(a["oracle_id"],"main")]="Hypothetical banned evaluation: "+a["assessment"]
    config={"version":"season0-proposed","status":"organizer_review_required_not_activated","as_of":inputs["as_of"],
            "cutoff":75,"price_curve":"nonlinear","nonlinear_scale":15,"nonlinear_power":1.5,"fine_scale":.6,
            "team_cap":120,"individual_reference":60,"individual_cap":72,"transfer_fraction":.2,
            "overrides":overrides,"manual_override_policy":"Oracle-ID keyed location alternatives. Human tiers are preserved and numeric tier intervals enforced.",
            "human_tier_price_intervals":{"0":[0,0],"1":[1,2],"2":[3,4],"3":[5,7],"4":[8,10],"5":[11,15]},
            "synergy_adjustment":0,"experimental_unbans":False,"gameplay_policy_activated":False}
    models={"old":base}
    for name,curve in (("calibrated_existing_tiers","existing_tiers"),("fine_integer","fine_integer"),("audited","nonlinear")):
        cfg={**config,"price_curve":curve}
        models[name]=AuditBackend(index,frame,cfg,inputs["combos"],inputs["anchors"])
    audited=models["audited"];ids=set(frame.oracle_id)|set(overrides)
    lookup=frame.set_index("oracle_id").to_dict("index")
    rows=[];changes=[]
    for oid in sorted(ids,key=lambda o:index.cards[o]["name"]):
        card=index.cards[oid];r=lookup.get(oid,{})
        oldm,oldc=base.card_price(oid,"main"),base.card_price(oid,"commanders")
        m,c=audited.card_price(oid,"main"),audited.card_price(oid,"commanders")
        legal=card.get("legalities",{}).get("commander")=="legal" and not card["name"].startswith("Erayo, Soratami Ascendant")
        if m or c or oldm or oldc:
            row={"oracle_id":oid,"card_name":card["name"],"main_deck_points":m,"command_zone_points":c,
                 "old_main_deck_points":oldm,"old_command_zone_points":oldc,"commander_eligibility":eligibility(card) or "ineligible",
                 "commander_legality":card.get("legalities",{}).get("commander"),"league_card_legal":legal,
                 "main_impact":r.get("main_deck_impact"),"command_zone_impact":r.get("command_zone_impact"),
                 "game_changer":r.get("game_changer",False),"canadian_highlander_points":r.get("canadian_highlander_points",0),
                 "confidence":"human_tier_calibrated_or_family_judgment" if oid in overrides else r.get("confidence","provisional_judgment"),
                 "main_rationale":reasons.get((oid,"main"),"Inherited reviewed impact, global nonlinear curve; exact rank remains judgment."),
                 "command_zone_rationale":reasons.get((oid,"commanders"),r.get("command_zone_explanation","Inherited independently assessed commander access.")),
                 "version":"season0-proposed","legalized_by_points":False}
            rows.append(row)
        for z,old,new in (("main",oldm,m),("commanders",oldc,c)):
            if old!=new:changes.append({"oracle_id":oid,"card_name":card["name"],"zone":z,"old_points":old,"new_points":new,
                                       "change":new-old,"reason":reasons.get((oid,z),"Global monotonic curve refinement; not fitted to deck outcomes."),
                                       "league_card_legal":legal})
    schedule=pd.DataFrame(rows)
    pointed=schedule[(schedule.main_deck_points>0)|(schedule.command_zone_points>0)]
    legalpointed=pointed[pointed.league_card_legal]
    changes.sort(key=lambda r:(-abs(r["change"]),r["card_name"],r["zone"]))
    def csv(name,data):
        d=data if isinstance(data,pd.DataFrame) else pd.DataFrame(data)
        for col in d.columns:
            if any(isinstance(v,(list,dict)) for v in d[col] if v is not None):
                d=d.copy();d[col]=d[col].map(lambda v:json.dumps(v,sort_keys=True) if isinstance(v,(list,dict)) else v)
        files[name]=d.to_csv(index=False)
    csv("audited_point_schedule.csv",legalpointed)
    csv("hypothetical_inclusive_point_schedule.csv",pointed)
    csv("audited_legal_point_schedule.csv",legalpointed)
    csv("point_price_changes.csv",changes)
    csv("newly_pointed_cards.csv",[r for r in changes if r["old_points"]==0 and r["new_points"]>0])
    csv("newly_unpointed_cards.csv",[r for r in changes if r["old_points"]>0 and r["new_points"]==0])
    files["human_calibration_anchors.json"]=serial({"scale":{str(k):v for k,v in enumerate(["Free","Minor","Moderate","Major","Elite","Exceptional"])},"anchors":inputs["anchors"],
                                                  "authority":"Organizer exact qualitative tiers; provisional integer prices are analyst judgments.",
                                                  "revisions":{"The One Ring":"Use4, supersedes3.","Smothering Tithe":"4 retained; relative2HG value provisional."}})
    csv("human_anchor_comparison.csv",[{"card_name":a["card_name"],"oracle_id":a["oracle_id"],"zone":a["zone"],"human_tier":a["tier"],"old_points":base.card_price(a["oracle_id"],a["zone"]),"proposed_points":a["proposed_points"],"canadian_highlander_points":lookup.get(a["oracle_id"],{}).get("canadian_highlander_points",0),"game_changer":lookup.get(a["oracle_id"],{}).get("game_changer",False),"rationale":a["rationale"]} for a in inputs["anchors"]])
    files["scoring_config.json"]=serial(config)
    files["audit_inputs.json"]=serial(inputs)
    decks=[]
    for d in json.load(open(root/"commander-league-card-point-calibration/data/clean/precons.json")):
        cmd=set(d["commander_ids"])
        decks.append({"deck_name":d["name"],"cohort":"official_precons","event_id":"","main":{o:q for o,q in d["counts"].items() if o not in cmd},
                      "commanders":{o:q for o,q in d["counts"].items() if o in cmd},"source":"taw archive/MTGJSON inherited clean data"})
    for cohort,entries in pools.items():
        if cohort=="cedh_train":continue
        unique={}
        for d in entries:
            normalized={z:{index.resolve(n):q for n,q in d[z].items()} for z in ("main","commanders")}
            key=json.dumps(normalized,sort_keys=True);unique.setdefault(key,{"deck_name":cohort+"_"+hashlib.sha256(key.encode()).hexdigest()[:16],"cohort":cohort,
                                                                       "event_id":d["event_id"],"source":"https://topdeck.gg",**normalized})
        decks.extend(unique.values())
    assert collections.Counter(d["cohort"] for d in decks)=={"official_precons":174,"cedh_holdout":2520,"bracket3_declared":150}
    def fixture(t,who):
        main=collections.Counter(t["main_"+who]);cmd=collections.Counter(t["commanders_"+who])
        remaining=100-sum(main.values())-sum(cmd.values());cycle=t["basic_cycle_"+who]
        for n in range(remaining):main[cycle[n%len(cycle)]]+=1
        return {"main":dict(main),"commanders":dict(cmd)}
    fixtures={};team_reports=[]
    for t in inputs["teams"]:
        a,b=fixture(t,"A"),fixture(t,"B");fixtures[t["id"]]={"a":a,"b":b}
        old=base.team(a,b);new=audited.team(a,b)
        assert old["both_decks_legal"],(t["id"],old["a"]["legality_issues"],old["b"]["legality_issues"])
        assert new["both_decks_legal"],(t["id"],new["a"]["legality_issues"],new["b"]["legality_issues"])
        for who,d in (("A",a),("B",b)):
            name=t["id"]+"_"+who
            decks.append({"deck_name":name,"cohort":"adversarial_fixture","event_id":"","source":"new explicitly illustrative legal fixture",**{z:{index.resolve(n):q for n,q in d[z].items()} for z in d}})
            text="Commander\n"+"\n".join(str(q)+" "+n for n,q in d["commanders"].items())+"\n\nDeck\n"+"\n".join(str(q)+" "+n for n,q in d["main"].items())+"\n"
            files["adversarial_decklists/"+name+".txt"]=text
        t.update({"old_A_points":old["a"]["total"],"old_B_points":old["b"]["total"],"old_team_points":old["total"],
                  "audited_A_points":new["a"]["total"],"audited_B_points":new["b"]["total"],"audited_team_points":new["total"],
                  "within_proposed_budget":new["budget_compliant"]})
        team_reports.append({**{k:v for k,v in t.items() if k not in ("basic_cycle_A","basic_cycle_B")},"component_candidates":new["combo_review_candidates"]})
    csv("adversarial_team_scores.csv",team_reports)
    files["adversarial_decklists/fixtures.json"]=serial(fixtures)
    # Fixed identity/location lookup; scores are sums, no context terms.
    maps={name:{z:{oid:b.card_price(oid,z) for oid in ids} for z in ("main","commanders")} for name,b in models.items()}
    def scores(d,model):
        return sum(q*maps[model][z].get(o,0) for z in ("main","commanders") for o,q in d[z].items())
    bench=[];mainfreq=collections.Counter();freefreq=collections.Counter();priceds=collections.Counter()
    for d in decks:
        vals={name:scores(d,name) for name in models}
        r=audited.score({z:d[z] for z in ("main","commanders")})
        assert r["total"]==vals["audited"]
        points=[row["total"] for row in r["rows"]]
        bench.append({k:d[k] for k in ("deck_name","cohort","event_id","source")}|
                     {k+"_points":v for k,v in vals.items()}|
                     {"delta":vals["audited"]-vals["old"],"command_zone_points":r["command_zone_total"],
                      "command_zone_share":r["command_zone_total"]/r["total"] if r["total"] else 0,
                      "pointed_card_count":sum(row["quantity"] for row in r["rows"] if row["points_each"]>0),
                      "top3_point_share":sum(sorted(points,reverse=True)[:3])/r["total"] if r["total"] else 0,
                      "officially_legal":r["officially_legal"],"legality_flags":";".join(r["legality_issues"])})
        if d["cohort"]=="cedh_holdout":
            mainfreq.update(d["main"].keys())
            freefreq.update(o for o in d["main"] if maps["audited"]["main"].get(o,0)==0)
            priceds.update(o for o in d["main"] if maps["audited"]["main"].get(o,0)>0)
    benchmark=pd.DataFrame(bench);csv("updated_cohort_benchmarks.csv",benchmark)
    concentration=[]
    for cohort,g in benchmark.groupby("cohort",sort=True):
        concentration.append({"cohort":cohort,"n":len(g),"median_command_zone_share":float(g.command_zone_share.median()),
                              "median_pointed_cards":float(g.pointed_card_count.median()),"median_top3_share":float(g.top3_point_share.median()),
                              "legal_lists":int(g.officially_legal.sum())})
    csv("cohort_point_concentration.csv",concentration)
    ordering=[]
    for higher,lower in (("bracket3_declared","official_precons"),("cedh_holdout","official_precons"),("cedh_holdout","bracket3_declared")):
        for method in ("old","audited"):
            hh=benchmark[benchmark.cohort==higher][method+"_points"].to_numpy()
            ll=np.sort(benchmark[benchmark.cohort==lower][method+"_points"].to_numpy())
            wins=sum(int(np.searchsorted(ll,v,side="left")) for v in hh)
            ties=sum(int(np.searchsorted(ll,v,side="right")-np.searchsorted(ll,v,side="left")) for v in hh)
            pairs=len(hh)*len(ll)
            ordering.append({"higher_label":higher,"lower_label":lower,"method":method,"pairs":pairs,"strictly_higher":wins,"ties":ties,
                             "cost_ordering_ties_half":(wins+ties*.5)/pairs,"meaning":"construction-cost ordering only; labels not verified strength"})
    csv("cohort_cost_ordering.csv",ordering)
    outliers=[]
    for cohort,g in benchmark.groupby("cohort",sort=True):
        if cohort=="adversarial_fixture":continue
        chosen=g.sort_values(["audited_points","deck_name"]).head(5).assign(extreme="lowest")
        chosen=pd.concat([chosen,g.sort_values(["audited_points","deck_name"],ascending=[False,True]).head(5).assign(extreme="highest")])
        for r in chosen.to_dict("records"):
            d=next(d for d in decks if d["deck_name"]==r["deck_name"])
            outliers.append({**r,"commanders":"; ".join(index.cards[o]["name"] for o in d["commanders"]),
                             "basic_land_count":sum(q for o,q in d["main"].items() if "Basic Land" in index.cards[o].get("type_line","")),
                             "note":"Retained archived list; event label is not certification of optimization or2HG strength."})
    csv("cohort_cost_outliers.csv",outliers)
    rng=np.random.default_rng(20261020);dist=[]
    for cohort,g in benchmark.groupby("cohort",sort=True):
        for method in models:
            vals=g[method+"_points"].to_numpy();n=len(vals)
            boots=np.median(vals[rng.integers(0,n,(1000,n))],axis=1)
            dist.append({"cohort":cohort,"method":method,"n":n,"median":float(np.median(vals)),"mean":float(np.mean(vals)),
                         "p10":float(np.quantile(vals,.1)),"p25":float(np.quantile(vals,.25)),"p75":float(np.quantile(vals,.75)),"p90":float(np.quantile(vals,.9)),
                         "min":int(vals.min()),"max":int(vals.max()),"zero":int(sum(vals==0)),"bootstrap_median_low":float(np.quantile(boots,.025)),
                         "bootstrap_median_high":float(np.quantile(boots,.975)),"unique_scores":len(set(vals))})
    csv("cohort_distribution_summary.csv",dist)
    auditdist=[r for r in dist if r["method"]=="audited"]
    csv("common_expensive_cards.csv",[{"oracle_id":o,"card_name":index.cards[o]["name"],"main_deck_points":maps["audited"]["main"][o],
                                      "holdout_lists":n,"share":n/2520} for o,n in priceds.most_common(60)])
    free=[]
    nominated=set(o for c in inputs["combos"] for z in ("oracle_ids_A","oracle_ids_B") for o in c[z])
    for o in set(freefreq)|nominated|{a["oracle_id"] for a in inputs["anchors"] if a["tier"]==0}:
        if maps["audited"]["main"].get(o,0)==0 or (eligibility(index.cards[o]) and audited.card_price(o,"commanders")==0):
            free.append({"oracle_id":o,"card_name":index.cards[o]["name"],"main_deck_points":audited.card_price(o,"main"),
                         "command_zone_points":audited.card_price(o,"commanders"),"eligible_commander":bool(eligibility(index.cards[o])),
                         "cedh_holdout_main_inclusion":freefreq[o],"interaction_nominated":o in nominated,
                         "note":"No point is not a safety certification; ordinary synergy/payoff may intentionally remain free."})
    free.sort(key=lambda r:(-r["cedh_holdout_main_inclusion"],r["card_name"]));csv("unpointed_high_power_cards.csv",free)
    # Equal, transferable and entirely pooled allocation scenarios: samples are synthetic, not observed teams.
    budget=[]
    for cohort,g in benchmark.groupby("cohort",sort=True):
        if cohort=="adversarial_fixture":continue
        vals=g.audited_points.to_numpy();n=len(vals)
        ia=rng.integers(0,n,10000);ib=rng.integers(0,n-1,10000);ib+=ib>=ia
        aa,bb=vals[ia],vals[ib]
        for ref in (30,40,50,60,75,100):
            for policy,fraction in (("equal",0),("transfer20",.2),("combined_only",None)):
                totalok=aa+bb<=2*ref
                ok=totalok if fraction is None else totalok&(np.maximum(aa,bb)<=math.floor(ref*(1+fraction)))
                budget.append({"scenario":"synthetic_same_cohort_pairing","cohort_or_team":cohort,"reference":ref,"team_cap":2*ref,
                               "allocation_policy":policy,"individual_max":"" if fraction is None else math.floor(ref*(1+fraction)),
                               "pairs":10000,"admitted":int(sum(ok)),"admitted_fraction":float(np.mean(ok))})
    for t in inputs["teams"]:
        aa,bb=t["audited_A_points"],t["audited_B_points"]
        for ref in (0,10,30,40,50,60,75,100):
            for policy,fraction in (("equal",0),("transfer20",.2),("combined_only",None)):
                cap=None if fraction is None else math.floor(ref*(1+fraction))
                ok=aa+bb<=2*ref and (cap is None or max(aa,bb)<=cap)
                budget.append({"scenario":"constructed_adversarial_fixture","cohort_or_team":t["id"],"reference":ref,"team_cap":2*ref,
                               "allocation_policy":policy,"individual_max":"" if cap is None else cap,"pairs":1,"admitted":int(ok),"admitted_fraction":float(ok)})
    # Enumerate all unordered distinct list pairs exactly; not observed teams.
    for cohort,g in benchmark.groupby("cohort",sort=True):
        if cohort=="adversarial_fixture":continue
        vv=np.sort(g.audited_points.to_numpy());n=len(vv);denom=n*(n-1)//2
        for ref in (30,40,50,60,75,100):
            for policy,fraction in (("equal",0),("transfer20",.2),("combined_only",None)):
                cap=None if fraction is None else math.floor(ref*(1+fraction));admitted=0
                for pos,v in enumerate(vv):
                    if cap is not None and v>cap:continue
                    upper=2*ref-int(v)
                    if cap is not None:upper=min(upper,cap)
                    admitted+=max(0,int(np.searchsorted(vv,upper,side="right"))-pos-1)
                budget.append({"scenario":"exact_unordered_distinct_cohort_pairs","cohort_or_team":cohort,"reference":ref,"team_cap":2*ref,
                               "allocation_policy":policy,"individual_max":"" if cap is None else cap,"pairs":denom,
                               "admitted":admitted,"admitted_fraction":admitted/denom})
    csv("budget_stress_test.csv",budget)
    grid=[]
    legalids=[o for o in ids if index.cards[o].get("legalities",{}).get("commander")=="legal" and not index.cards[o]["name"].startswith("Erayo, Soratami Ascendant")]
    for tau in (70,72.5,75,77.5,80):
        for curve in ("existing_tiers","fine_integer","nonlinear"):
            b=AuditBackend(index,frame,{**config,"cutoff":tau,"price_curve":curve},inputs["combos"],inputs["anchors"])
            mm={o:b.card_price(o,"main") for o in ids};cc={o:b.card_price(o,"commanders") for o in ids}
            for cohort in ("official_precons","bracket3_declared","cedh_holdout"):
                dd=[d for d in decks if d["cohort"]==cohort]
                vv=np.array([sum(q*(mm if z=="main" else cc).get(o,0) for z in ("main","commanders") for o,q in d[z].items()) for d in dd])
                grid.append({"cutoff":tau,"curve":curve,"cohort":cohort,"n":len(dd),"median":float(np.median(vv)),"p10":float(np.quantile(vv,.1)),
                             "p90":float(np.quantile(vv,.9)),"legal_main_pointed":sum(mm[o]>0 for o in legalids),"legal_cz_pointed":sum(cc[o]>0 for o in legalids),
                             "legal_union":sum(mm[o]>0 or cc[o]>0 for o in legalids)})
    csv("cutoff_curve_comparison.csv",grid)
    sensitivity=[]
    for o,n in priceds.most_common(10):
        for delta in (-1,1):
            for cohort in ("official_precons","bracket3_declared","cedh_holdout"):
                ii=[k for k,d in enumerate(decks) if d["cohort"]==cohort]
                oldvals=benchmark.iloc[ii].audited_points.to_numpy()
                vv=oldvals+np.array([decks[k]["main"].get(o,0)*delta for k in ii])
                sensitivity.append({"card_name":index.cards[o]["name"],"price_delta":delta,"cohort":cohort,
                                    "decks_affected":sum(decks[k]["main"].get(o,0)>0 for k in ii),
                                    "median_before":float(np.median(oldvals)),"median_after":float(np.median(vv)),
                                    "spearman":float(stats.spearmanr(oldvals,vv).statistic),"max_abs_deck_change":int(np.max(abs(vv-oldvals)))})
    csv("single_card_sensitivity.csv",sensitivity)
    # Boundary sample uses the original impact, but explicit anchors/overrides can cross this policy boundary.
    boundary=[]
    for r in frame.to_dict("records"):
        for z,field in (("main","main_deck_impact"),("commanders","command_zone_impact")):
            s=r.get(field)
            if pd.notna(s) and abs(float(s)-75)<=3:
                boundary.append({"card_name":r["card_name"],"oracle_id":r["oracle_id"],"zone":z,"impact":s,
                                 "audited_points":audited.card_price(r["oracle_id"],z),
                                 "explicit_override":r["oracle_id"] in overrides,"confidence":r.get("confidence")})
    csv("cutoff_boundary_review.csv",boundary)
    csv("team_combo_database.csv",inputs["combos"])
    csv("two_hg_edge_case_matrix.csv",inputs["edge_cases"])
    unban=[]
    for a in inputs["unbans"]:
        unban.append({**a,"current_legality":index.cards[a["oracle_id"]].get("legalities",{}).get("commander"),
                      "hypothetical_command_zone_points":audited.card_price(a["oracle_id"],"commanders") if eligibility(index.cards[a["oracle_id"]]) else 0})
    csv("experimental_unban_review.csv",unban)
    priorpre=benchmark[benchmark.cohort=="official_precons"]
    priorb3=benchmark[benchmark.cohort=="bracket3_declared"]
    priorcedh=benchmark[benchmark.cohort=="cedh_holdout"]
    summary={"version":"season0-proposed","legal_pointed_identities":len(legalpointed),
             "legal_main_pointed":int(sum(legalpointed.main_deck_points>0)),"legal_command_zone_pointed":int(sum(legalpointed.command_zone_points>0)),
             "hypothetical_inclusive_pointed_identities":len(pointed),"price_changes":len(changes),
             "newly_pointed_zones":sum(r["old_points"]==0 and r["new_points"]>0 for r in changes),
             "newly_free_zones":sum(r["old_points"]>0 and r["new_points"]==0 for r in changes),
             "anchor_count":len(inputs["anchors"]),"family_reviews":len(inputs["family"]),"combo_candidates":len(inputs["combos"]),
             "verified_cross_team_records":sum(c["status"]=="verified_cross_team" for c in inputs["combos"]),
             "false_split_records":sum(c["status"].startswith("false") for c in inputs["combos"]),
             "adversarial_teams":len(inputs["teams"]),"legal_scoring_fixtures":len(inputs["teams"])*2,
             "cohort_distributions":auditdist,
             "budget_reference60_transfer20":[r for r in budget if r["reference"]==60 and r["allocation_policy"]=="transfer20" and r["scenario"]=="synthetic_same_cohort_pairing"],
             "exact_budget_reference60_transfer20":[r for r in budget if r["reference"]==60 and r["allocation_policy"]=="transfer20" and r["scenario"]=="exact_unordered_distinct_cohort_pairs"],
             "zero_point_adversarial_teams":[t["id"] for t in inputs["teams"] if t["audited_team_points"]==0],
             "expected_cohort_counts":{"official_precons":174,"bracket3_declared":150,"cedh_holdout":2520},
             "benchmark_decks_including_fixtures":len(decks),"no_verified_2hg_match_cohort":True,
             "sampling_interval_warning":"Bootstrap conditions on biased labelled samples and fixed judgment prices; not win-rate, rating or population confidence.",
             "source_exclusions":result["exclusions"]}
    files["analysis_summary.json"]=serial(summary)
    # Reports preserve uncertainties and expose counterexamples instead of calling opinions empirical strengths.
    sections=["# Adversarial teams — illustrative cores and complete scoring fixtures",
              "Each text list has100 legal cards but basic padding intentionally isolates the core. These are not optimized complete competitive decks. Turn lines are conditional feasible sequences, not goldfish medians or win probabilities. No paid API or gameplay simulator used."]
    for t in inputs["teams"]:
        sections+=["## "+t["id"]+" — "+t["title"],"A: "+", ".join(t["commanders_A"])+"; B: "+", ".join(t["commanders_B"])+".",
                   "Roles/core A: "+", ".join(t["main_A"])+"; B: "+", ".join(t["main_B"])+".",
                   f"Old A/B/team: {t['old_A_points']}/{t['old_B_points']}/{t['old_team_points']}. Proposed: {t['audited_A_points']}/{t['audited_B_points']}/{t['audited_team_points']}.",
                   "Demonstrated conditional turn "+str(t["earliest_demonstrated_turn"])+": "+t["sequence"],
                   "Prerequisites: "+t["prerequisites"],"Disruption: "+t["disruption"],
                   "Classification: "+t["issue_classification"]+". Recommendation: "+t["recommendation"]]
    files["adversarial_team_archetypes.md"]="\n\n".join(sections)+"\n"
    files["low_point_exploit_report.md"]="# Low-point exploits\n\n"+mdtable(team_reports,["id","title","old_team_points","audited_team_points","earliest_demonstrated_turn"])+"\n\nTwo baseline zero-point counterexamples were independently reproduced with the original backend (T01/T03), without human commander discounts. T02 costs2 in baseline, not0. Repricing Chain/Dualcaster does not eliminate equivalent engines or the organizer's free commander strategies. A numeric budget cannot certify intended gameplay.\n\nT09's damage arithmetic uses two opponents, two Yuriko triggers total,16 each:64 shared life. T08's teammate land supplies evasion, not mana. T07 keeps mana/Aura/Kenrith control together. These are actual controller distinctions, not cosmetic descriptions.\n"
    files["score_distribution_comparison.md"]="# Actual frozen-cohort recalculation\n\n"+mdtable(dist,["cohort","method","n","median","p10","p90","min","max","zero"])+"\n\nAll174/150/2520 archived lists were rescored at their actual card locations;26 new legal padded fixtures are a separate cohort. Historical exceptions remain; see legality flags. TopDeck.gg attribution retained. Event labels, especially B3 and cEDH, are declarations rather than strength certification. No verified paired2HG outcomes or upgraded-deck sample was available.\n\nThe1,000-resample intervals in cohort_distribution_summary.csv are conditional sampling intervals, not uncertainty in prices or predictions. Single-card +/-1 tests and cutoff/curve grids show construction-price sensitivity. No weight was fitted to these final cohorts, and no correlation with point totals is represented as a win-rate result.\n"
    files["score_distribution_comparison.md"]+="\n## Point concentration and label-cost ordering\n\n"+mdtable(concentration,["cohort","n","median_pointed_cards","median_command_zone_share","median_top3_share","legal_lists"])+"\n\n"+mdtable(ordering,["higher_label","lower_label","method","pairs","cost_ordering_ties_half"])+"\n\nCost ordering is not a prediction metric. Low/high lists with commander/basic counts are in cohort_cost_outliers.csv. Extremely basic-heavy cEDH-labelled registrations remain included; no label cleanup was fitted to improve apparent separation.\n"
    files["cutoff_finalization_report.md"]="# Cutoff finalization — policy, not discovered discontinuity\n\nRetain75 as inherited reviewed-impact admission policy, with explicit human and family exceptions. Scores near75 and the specialist floor are judgments; there is no independently established natural break. Most low-confidence tail priors remain below all tested cutoffs. Human zero anchors override the admission policy.\n\n"+mdtable([r for r in grid if r["curve"]=="nonlinear"],["cutoff","cohort","median","p10","p90","legal_main_pointed","legal_cz_pointed","legal_union"])+"\n\nTested curves: original0/1/3/5/8/12 tier bands; fine ceil(0.6*max(0,s-tau)); nonlinear ceil(15*(max(0,s-tau)/25)^1.5). Chosen nonlinear curve has finer low-end resolution and steeper premium for exceptional scores. Human intervals0,1-2,3-4,5-7,8-10,11-15 constrain the50 anchors, but individual prices differ within a tier. Family changes are explicit reviewable exceptions. These policy curves are not estimated causal coefficients.\n\n"+str(len(legalpointed))+" legal identities receive some points. New/free lists are location-specific; an identity can remain pointed in the other zone. No thousands-card tax. Grapeshot, Tendrils of Agony and Frantic Search are newly free ordinary payoff/filtering cards; their prior1-point charge was not supported by exceptional independent resource advantage. Near-boundary decisions remain provisional and unreviewed tail absence is not a safety finding.\n"
    files["proposed_team_budget_analysis.md"]="# Season0 provisional budget\n\nTest60 reference per player,120 combined, maximum72 per deck (20% of reference=12 transferable points). A60/60 pair,72/48 and48/72 fit;73/47 fails transfer/individual envelope even though total120. Purely pooled120 would permit120/0, concentrating premium protection and conversion. Transfers consume the teammate's unused reference allocation, not extra budget.\n\n"+mdtable(summary["budget_reference60_transfer20"],["cohort_or_team","reference","team_cap","individual_max","pairs","admitted","admitted_fraction"])+"\n\nExact unordered distinct-pair counts are also in budget_stress_test.csv; a zero rate in10,000 samples does not prove no admitted pair exists. These10,000 pairings/cohort are synthetic samples of distinct submitted deck identities, not observed teams or match outcomes. budget_stress_test.csv also tests equal,20% and unrestricted pooled allocations at references30/40/50/60/75/100, and concrete exploit fixtures including reference0. The60 choice is a deliberately restrictive Season0 policy pilot, not an estimate derived solely from a cohort median.\n\nEvery low-cost exploit that fits must still fail or pass the separate registered-line policy. No positive budget reliably excludes all intentional combos, and free commander anchors ensure that a point-only season cannot promise Bracket3 intent. Begin monitored playtests only after organizer approves gameplay restrictions, not merely this budget.\n"
    anchorchanges=[r for r in changes if any(a["oracle_id"]==r["oracle_id"] and a["zone"]==r["zone"] for a in inputs["anchors"])]
    files["calibration_disagreements.md"]="# Calibration disagreements and preserved authority\n\nAll50 organizer tiers are preserved exactly, including Ring4, Tithe4 and five free commanders. Proposed integer prices are not organizer-approved numbers.\n\n"+mdtable(anchorchanges,["card_name","zone","old_points","new_points","change"])+"\n\nLargest conceptual disagreements: Orim's Chant only shuts one head's spells while Silence shuts both; it nevertheless stays exceptional per organizer. Kicker prohibits all attacks that turn. Free Kenrith/Najeela/Inalla/Derevi/Yuriko retain guaranteed engines and access, despite previous5-8-point command prices. They are not proven safe; T06-T09 demonstrate risks. Skullclamp1/Pod2/Training1 are intentionally minor despite high specialized ceilings. Cyclonic Rift0 remains powerful with a spell/combo-focused teammate or useful ordinary bounce mode; bouncing a teammate reduces asymmetry but does not make it objectively weak. Tithe8 reflects an elite human judgment despite fewer opposing draw steps.\n\nCanadian Highlander is a different format; its points and current Game Changer flags are preserved alongside prices in audited_point_schedule.csv. Sol Ring is exceptional here despite not being a Game Changer. Food Chain remains exceptional despite removal from Game Changers. GC is a curated experience category, not a quantitative strength scale. This system does not enforce the official3-Game-Changer B3 cap unless organizer separately adopts it; therefore call it a custom league with B3-like intent.\n"
    files["card_family_consistency_audit.md"]="# Pairwise family audit\n\n"+mdtable(inputs["family"],["card_name","main_deck_points","rationale"])+"\n\nFast mana: Chrome/Diamond14, Opal10, Amber8, Petal9, ESG6, SSG5, Dark9/Culling8/Rite2. Different card/board costs explain differences; no release-date modifier. Tutors: Demonic15 > Vamp10/Enlightened9 > Imperial8; instant/sorcery, type restrictions and topdeck delay are explicit. Proactive protection: Silence14 > Abolisher/Ranger13 > Chant/Voice12; abilities differ, all human exceptional tiers retained. Force14 > Fierce13 > Negation/Pact8; legal timings and delayed payment matter.\n\nOrdinary equivalents remain free unless exceptional: Twinflame/Heat Shimmer payoffs do not acquire a mechanical combo tax; ordinary creature producers and mana dorks stay free. Global untapper Alarm4 and repeatable copy enablers Chain3/Dualcaster3 are specifically reviewed exceptions. Freed/Pemmin2 match untap functionality; Drake0 is not priced solely for combo membership. Basics/snow basics are all0. Common mana fixing such as Command Tower and Arcane Signet remains0.\n\nNot every old pointed card has a fresh independent individual assessment: inherited prices not addressed in this table remain provisional and retain manual-review flags. Do not interpret deterministic arithmetic as human agreement on every row.\n"
    files["team_combo_rules_analysis.md"]="# Controller-checked interaction audit\n\n"+mdtable(inputs["combos"],["id","cards_A","cards_B","status","outcome","rules_citations"])+"\n\nA/B are teammates; C/D opponents. CSV records required state, exact controller split, investment, sequence, disruption, confidence and stable identities. Verified means the stated conditional interaction follows text, not that deck union establishes state or a guaranteed win. No source supplies measured2HG combo win rates.\n\nRest in Peace A plus Helm B works because replacement is global. X>=1 mills through library without putting cards in graveyard; it still needs failed draw. Bond A plus Blood B does not loop: B gains life, not A. Similarly split Kinnan/Basalt, Oracle/Consultation, Heliod/Ballista, Tivit/Sieve, Deadeye/Drake and friendly Sphinx loops fail. Displacer A plus Drake B CAN work because Drake targets any five lands; B untaps A's mana sources, and returned Drake still belongs to B.\n\nPrior Spellbook union fixture690-3966 is now explicitly a false positive under the ownership split. Prior live API responses are preserved, not silently reclassified as executed games. New variants query was inaccessible through the web tool; no new API response or bulk download is claimed. Reuse official client for permitted queries; do not bulk-export unverified licensed data. See original spellbook_integration_report.md and API docs.\n"
    files["official_2hg_rules_verification.md"]="# Official rules verification —2026-10-20\n\nSources: [current rules landing](https://magic.wizards.com/en/rules), [linked September25 CR](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt), [Commander2HG format modifier](https://magic.wizards.com/en/formats/two-headed-giant), [Commander/bans](https://magic.wizards.com/en/banned-restricted-list).\n\nFour players/two teams:810.1. Shared turns:810.2/805.4. Official format webpage specifies Commander60 shared life and no unified construction: each player brings independently legal100-card deck,1 commander or compatible pair. CR810.4 gives ordinary2HG30 and903.7 ordinary Commander40, so60 is the published combination modifier, not a standalone text in those general clauses. Separate resources/control:810.5. Each head draws and can play a land:805.4b,c. Teams get priority, either head acts, opponents retain response windows:805.5. Trigger ordering:805.7, primary-player tie choice805.2.\n\nFirst multiplayer mulligan free103.5c; individual keep choices despite consultation103.5d/805.3a. Starting team skips first shared draw step103.8b/810.6. Extra turns/phases and skipped steps are teamwide805.8, as is controlling another player's turn. Attack targets declared per creature/head805.10b; either defending head can block805.10d.\n\nLife damage/loss/gain events remain individual810.9; queried life is shared810.9a. Cannot-gain/cannot-lose-life effects extend to team810.9g,h. Team victory/loss/cannot-win/cannot-lose810.8a; one empty-library failed draw704.5b can lose team. Fifteen poison810.8d; shared poison810.10; proliferate onlyone/team/action701.34b.\n\n**Commander-damage documentation conflict:**903.10a/704.6c say21 combat damage to an individual head from the same commander, whereas the format webpage says team21. Recommended precedence is detailedCR per-head tracking, followed by team loss810.8a. Keep21 threshold; do not silently aggregate across heads. Organizer must approve written precedence or explicitly call aggregation a custom rule.\n\nBans remain independent of prices, including category bans and companion-only Lutri restriction. Erayo additionally appears in Constructed2HG bans. Current Game Changer policy allows up to3 in officialB3, but custom points are not a validated substitute for that rule. February2026 update adds Farewell and preserves prior bracket intent; October2025 explains six full turns before victory means seventh turn and merely holding early combos is not compliance.\n\n**Freshness limitation discovered in final audit:** October19 [Mystery Booster update bulletin](https://magic.wizards.com/en/news/announcements/mystery-booster-commander-edition-update-bulletin) announces planned rulebreaker903.5e/Oracle changes. The current landing still links September25 CR and bulletin defers to actual rules. Frozen Oracle does not resolve Tolabow. Unknown cards error, not free; newly supported rulebreaker permissions require manual adjudication and updated snapshot before release. No unsupported construction permission is auto-approved.\n\nThis review uses exact rule numbers and current Oracle for the examined cards; it is not judge certification or a full gameplay engine. two_hg_edge_case_matrix.csv contains40 phrase/event cases.\n"
    files["two_hg_power_outliers.md"]="# Material2HG outliers\n\nSilence protects both friendly casters against both opposing spell casters forW. Chant only targets one head (kicker prohibits all attacking). Abolisher/Voice apply on shared own turn, with different ability coverage. Rift overload returns B's nonlands too; keep organizer0 but note B may be spell-focused. Ring protection is individual. Tithe sees two opposing draws per normal opposing shared step, not three independent opposing turns.\n\nHidetsugu at even60 is30+30 damage to each team; Grace or Protection supplied by teammate can make it asymmetric. Sorin one-head setting changes full pool to10. Felidar/Test thresholds start met but require deployment and an upkeep window. Yuriko16 triggers hit both opponents and each removes32 shared life. Extra turns and turn control affect whole teams. Shared life does not create shared gain events; split Bond/Blood fails.\n\nNajeela/Derevi can support extra team combats but Derevi's own creatures must connect and untap actual A lands. Kinnan only multiplies own tapped nonland permanents. Seedborn has only one opposing untap window; skipped untap is not restored. Breena compares the two opponents\u0027 equal shared totals, so its strict-more-life trigger normally cannot fire. Angel of Destiny uses starting60 and needs75, not55. Curse of Opulence can reward its own controller when a teammate attacks, but does not give that teammate the additional Gold reserved for opponents. All of these are qualitative rules-driven assessments, not measured win-rate adjustments.\n"
    files["proposed_league_legality_policy.md"]="# Proposed league legality policy — organizer approval required\n\n"+inputs["policy_text"]+"\n\n| Class | Proposed treatment |\n| --- | --- |\n| Allowed | Finite synergies, ordinary ramp/interaction, coordinated roles and teammate support without surcharge. |\n| Point-regulated | Exceptional independently priced mana, tutors, protection and engines; actual zone determines fixed cost. |\n| Restricted by rule | Registered repeatable win/resource/extra-combat engines; repeated extra turns/control of opponents; intentional severe participation locks and mass land denial. |\n| Banned | Current official Commander/category/Constructed2HG bans; no experimental unbans. |\n\nThe shortest enforceable implementation is a published prohibited-line register with controller/state prerequisites, applied to BOTH submitted decks, plus an organizer appeals process. C01/C02/C07/C11/C12/C13 and T06-T08 are initial engine-review entries; C08-C10 are initial participation-lock entries. Add lines only by recorded ruling, not automatic name-union detection. A pool lock has ability/attack outs but still presents sustained participation denial.\n\nEarly-win intent review is necessarily less objective than card identity: test demonstrated lines and observed play frequency; do not call every perfect opening reliable. T02's two-Chancellor opener is an extreme possibility, while T01 is a cheap two-piece distributed line. This draft is not ready for automatic enforcement until organizer defines loop, lock, mass denial and appeals boundaries. No custom penalty or gameplay-loss rule has been activated by software.\n\nDo not add a pre-turn7 cannot-lose shield or combat exemption: they distort Pact/Final Fortune/Ad Nauseam and admit Dualcaster/Najeela attacks. Count shared team turns; extra turns do not legitimize an otherwise prohibited engine. Official brackets are conversation guidance; numerical cap plus these custom restrictions is not literal officialB3 certification.\n"
    files["experimental_unban_review.md"]="# Experimental unban review — no legality changes\n\n"+mdtable(unban,["card_name","current_legality","hypothetical_main_deck_points","hypothetical_command_zone_points","two_hg_change","assessment","recommendation"])+"\n\nAll seven remain banned in normal deck validation. Prices are hypothetical independent judgments, not permission or evidence that a ban's underlying experience concern is solved. Commander prices use inherited independent commander rubric; no automatic main-plus-premium. Test separately only after organizer explicit exception, with new version and controller-specific early/lock review.\n"
    files["highest_priority_balance_risks.md"]="# Unresolved decisions ranked by urgency\n\n| Priority | Decision/risk | Supporting counterexample |\n| --- | --- | --- |\n| P0 | Adopt separate repeatable-engine/lock policy before cap | Baseline zero-point T01 and T03; tiny reprices still fit normal budgets. |\n| P0 | Free commander anchors are deliberate access subsidies | T06 Inalla, T07 Kenrith, T08 Najeela, T09 double Yuriko; do not silently reprice. |\n| P0 | Resolve commander-damage documentation precedence | CR per-head21 vs format-page team21. |\n| P0 | Approve practical lock/loop definitions and appeals | Name unions include11+ false positives; cannot auto-disqualify. |\n| P1 | Confirm fresh rulebreaker/Oracle snapshot | October19 bulletin, September linkedCR; Tolabow unknown to frozen data. |\n| P1 | Approve60/120/72 pilot and transfers | Empirical cost overlap and cheap constructed counterexamples persist. |\n| P1 | Review high protection tiers and cheap substitutes | Chant only one head; Conqueror/Dosan/City set up differently. |\n| P1 | Playtest specialized enabler prices | Chain3, Dualcaster3, Alarm4, Scepter3, Helm2 are provisional. |\n| P2 | Resolve423 low-confidence tail judgments | Inherited absence of points cannot establish all omissions harmless. |\n| P2 | Collect paired actual2HG decklists, turn traces and match context | No verified outcomes or calibrated win probabilities acquired. |\n"
    # Review queue preserves inherited uncertainty; explicit new omissions/boundaries are visible.
    queue=[]
    pointedids=set(pointed.oracle_id)
    commandrows=[]
    for r in frame.to_dict("records"):
        oid=r["oracle_id"]
        if audited.card_price(oid,"commanders")>0 or any(a["oracle_id"]==oid and a["zone"]=="commanders" for a in inputs["anchors"]):
            commandrows.append({"oracle_id":oid,"card_name":r["card_name"],"old_command_zone_points":base.card_price(oid,"commanders"),"audited_command_zone_points":audited.card_price(oid,"commanders"),"eligible":eligibility(index.cards[oid]),"legality":index.cards[oid].get("legalities",{}).get("commander"),"rationale":reasons.get((oid,"commanders"),r.get("command_zone_explanation")),"review_status":"human_anchor" if any(a["oracle_id"]==oid and a["zone"]=="commanders" for a in inputs["anchors"]) else "inherited_individual_assessment_recomputed_not_new_human_endorsement"})
    csv("command_zone_consistency_audit.csv",commandrows)
    for r in frame.to_dict("records"):
        if (not r.get("manually_assessed",False) and r.get("main_deck_rank",99999)<=1000) or r["oracle_id"] in overrides or r["oracle_id"] in pointedids or any(b["oracle_id"]==r["oracle_id"] for b in boundary):
            queue.append({"oracle_id":r["oracle_id"],"card_name":r["card_name"],"main_points":audited.card_price(r["oracle_id"],"main"),
                          "command_zone_points":audited.card_price(r["oracle_id"],"commanders"),"priority":"high" if r["oracle_id"] in overrides else "boundary_or_inherited_tail",
                          "reason":reasons.get((r["oracle_id"],"main"),"Inherited tail/boundary; exact judgment not independently validated.")})
    csv("manual_review_queue.csv",queue)
    # Limits and direct decision package.
    anchors_table=mdtable(anchorchanges[:10],["card_name","zone","old_points","new_points","change"])
    overview=mdtable(auditdist,["cohort","n","median","p10","p90","min","max"])
    files["final_audit_executive_summary.md"]="# Final audit decision package — season0-proposed\n\n**Not ready for a permanent league lock. Ready for organizer review and a monitored Season0 pilot only after separate line/lock policy is approved.** Fixed additive prices are internally coherent as construction resources, but cannot enforce Bracket3 intent. The audit found actual zero-budget early wins under the saved backend with ordinary free commanders.\n\n"+overview+"\n\n1. Philosophy: coherent; fixed location prices, no synergy surcharge. It intentionally leaves synergistic advantages uncharged.\n2. Largest anchor effects: Chant/Food Chain/proactive protection increase; five commanders become free; Tithe becomes elite. Qualitative tiers all preserved, numbers provisional.\n3. Ten largest human-anchor reprices:\n\n"+anchors_table+"\n\n4. Exceptional free resources remain: Kenrith/Najeela/Inalla/Derevi/Yuriko command access, many ordinary interchangeable payoffs, utility fixing and some high-ceiling specialized cards. See unpointed_high_power_cards.csv.\n5. Clear removal: Rift main becomes0 per human authority; five commander prices become0. Skullclamp reduced. Other inherited marginal1-point utility lacks strong evidence; review queue is not hidden.\n6. Largest free-commander risks: Inalla copy engine, Kenrith outlet/counter engine, Najeela repeat combat, double Yuriko damage; Derevi supports untapping/locks without shared mana.\n7. Genuine split combos include Chain/Apprentice, Dualcaster/Twinflame, RIP/Helm, Painter/Grindstone, Alarm/token producer, Displacer/Drake and active Ascension/Mindcrank. Bond/Blood, Kinnan/Basalt and Oracle/Consultation split fail.\n8. Most severe constructed examples: baseline T01 zero-costT2 drain; T03 zero-costT3 hasty army; T02 cost2T1 Chancellor line. These are possible conditional openings, not measured reliability. Current proposed costs are in adversarial_team_scores.csv.\n9. Material rules: separate event/control/resource ownership, both-opponent drain, shared turns/extra turns/control, Grace team cannot-lose vs Protection shared-life lock, per-head commander damage conflict.\n10. Individual enablers can be repriced (Chain/Dualcaster3, Alarm4, tutors/fast mana/protection); prices alone cannot remove all equivalent combinations.\n11. Repeatable engines, early reliable deterministic lines and severe participation/land locks need separate written legality review. No early invulnerability or combat loophole.\n12. Recommended pointed size: "+str(len(legalpointed))+" currently legal identities ("+str(summary["legal_main_pointed"])+" main, "+str(summary["legal_command_zone_pointed"])+" command-zone; overlap allowed). This is policy, not a natural optimum.\n13. Pilot budget:60 reference each,120 team,72 individual maximum, at most12 transferred from teammate's unused reference. Do not adopt without separate gameplay policy.\n14. Uncertainty: biased labelled cohorts, no paired2HG outcomes, hypothetical opening consistency,423 inherited low-confidence tail rows, subjective boundary/price judgments and fresh rulebreaker coverage.\n15. Permanent lock: no. Version all approvals and run actual paired playtests first.\n\n| Urgency | Organizer approval needed | Proposed decision |\n| --- | --- | --- |\n| P0 | Gameplay legality scope | Published controller-aware prohibited-line register and appeal process; explicit engine/lock/early-line review. |\n| P0 | Commander damage | DetailedCR:21 to individual head; disclose website conflict. |\n| P0 | Free commander risks | Preserve all human zeros; approve separate strategy restrictions or knowingly accept them. |\n| P1 | Numeric schedule and budget | season0-proposed;60/120/72 with20% transfer, not official activation. |\n| P1 | Current snapshot release | Refresh/resolve rulebreaker and missing new cards before accepting such decks. |\n| P2 | Experimental unbans | None approved; keep all official bans. |\n"
    decisions=[{"decision":"D01","urgency":"P0","question":"Permanent lock or pilot?","recommendation":"Pilot only; season0-proposed remains unactivated.","reason":"Zero-point and tiny-cost early team lines persist.","cases":"T01,T03,T08,T09"},{"decision":"D02","urgency":"P0","question":"Commander-damage tracking?","recommendation":"21 combat damage from one commander to one individual head, then team loses.","reason":"DetailedCR903.10a/704.6c conflicts with official format-page aggregate wording; choosing aggregate must be explicit custom rule.","cases":"rules matrix Commander damage"},{"decision":"D03","urgency":"P0","question":"Repeatable engines?","recommendation":"Prohibit registered arbitrarily repeatable net-resource/win/extra-combat engines across either or both decks.","reason":"Finite high-N declarations must not evade infinite-loop rule; ordinary naturally consumable resources remain finite.","cases":"C01,C02,C07,C11,C12,C13;T06,T07,T08"},{"decision":"D04","urgency":"P0","question":"Sustained opponent casting locks?","recommendation":"Prohibit registered C08-C10 configurations, regardless price or turn.","reason":"Ability/attack outs exist but sustained participation denial is unsuitable for proposed social intent.","cases":"C08,C09,C10"},{"decision":"D05","urgency":"P0","question":"Fast non-loop zero-point commander teams?","recommendation":"Keep human prices0; explicitly review T09 double-Yuriko64-damage turn3 and accept competitiveness or reject reliably early construction.","reason":"A blanket loop ban does not catch this finite combat line. No hidden synergy tax or silent human override.","cases":"T09"},{"decision":"D06","urgency":"P1","question":"Pilot budget?","recommendation":"60 individual reference,120 team,72 maximum/individual,12 maximum transfer from unused reference.","reason":"Policy pilot; exact pairing enumeration and concrete exploits show no cap alone solves gameplay.","cases":"budget_stress_test.csv,T13"},{"decision":"D07","urgency":"P1","question":"Mass denial and turn-control boundaries?","recommendation":"Publish specific prohibited-line register and examples before play; allow ordinary targeted removal and one finite extra turn subject to review.","reason":"Current draft does not justify a universal automatic lock detector. Repeated turns/control/intentional mass denial require recorded rulings.","cases":"C08-C10;Mindslaver;extra-turn engines"},{"decision":"D08","urgency":"P1","question":"Fresh rulebreaker/missing-card submissions?","recommendation":"Manual adjudication and new pinned Oracle/rules snapshot before accepting such decks.","reason":"October19 bulletin is newer than linkedCR; Tolabow absent from frozen Oracle.","cases":"official_2hg_rules_verification.md"},{"decision":"D09","urgency":"P1","question":"Specialized enabler prices?","recommendation":"Playtest Chain3,Dualcaster3,Alarm4,Helm2,Scepter3; retain ordinary interchangeable payoffs free.","reason":"Explicit judgments from functionality; no outcome-calibrated causal strength.","cases":"card_family_consistency_audit.md"},{"decision":"D10","urgency":"P2","question":"Experimental unbans?","recommendation":"None; keep all official bans.","reason":"Hypothetical prices do not resolve original ban concerns.","cases":"experimental_unban_review.md"}]
    csv("organizer_decisions.csv",decisions)
    files["final_audit_executive_summary.md"]+="\n\nThe default audited_point_schedule.csv contains only legal pointed identities. Hypothetical banned prices are isolated in hypothetical_inclusive_point_schedule.csv and experimental_unban_review.csv. Organizer approval questions, exact options and supporting cases are in organizer_decisions.csv. D05 explicitly addresses the finite double-Yuriko line, which an infinite-loop ban alone would miss.\n"
    sources={}
    paths=["commander-top1000-power-ranking/candidate_inventory.csv","commander-top1000-power-ranking/analyst_assessments.json",
           "commander-top1000-power-ranking/scoring_config.json","commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz",
           "commander-league-card-point-calibration/data/clean/precons.json","data/tournament_snapshots/topdeck/manifest.json",
           "commander-card-power-research-v1/data/spellbook/cross_team_positive_control.json"]
    for p in paths:sources[p]={"sha256":hashlib.sha256((root/p).read_bytes()).hexdigest(),"kind":"inherited frozen input"}
    rules=root/"commander-top1000-power-ranking/data/rules_source.json"
    sources["rules_metadata"]=json.load(open(rules))
    files["source_provenance.json"]=serial({"base_commit":inputs["base_commit"],"as_of":"2026-10-20","sources":inputs["sources"],"inputs":sources,
                                          "seeds":{"bootstrap_and_pairing":20261020},"third_party_notice":"Credit TopDeck.gg and Commander Spellbook. Oracle text Wizards; prior software/data licenses retained. New API request inaccessible; no new bulk data claimed."})
    files["README.md"]="# Commander Doubles final audit — season0-proposed\n\nRead final_audit_executive_summary.md first. This is a review package, not activated official rules. Previous project directories/branches are preserved.\n\nFrom repository root:\n\n\u0060\u0060\u0060sh\npython -m pip install -r commander-top1000-power-ranking/requirements.txt\npython commander-doubles-final-audit/audit_pipeline.py\npython commander-doubles-final-audit/audit_tests.py\npython commander-doubles-final-audit/audit_backend.py commander-doubles-final-audit/adversarial_decklists/T01_A.txt --deck-b commander-doubles-final-audit/adversarial_decklists/T01_B.txt --export team-report.json\n\u0060\u0060\u0060\n\nUses existing Python environment/requirements from commander-top1000-power-ranking, complete Oracle snapshot, prior resolver/legality checks/Moxfield parser, frozen precons and authorized TopDeck.gg snapshots. No paid API or ordinary network calls. All50 human tiers live separately in human_calibration_anchors.json/audit_inputs.json; proposed numeric prices are editable Oracle-ID overrides in scoring_config.json. To regenerate overrides from judgments edit audit_inputs.json. Rerunning pipeline resets scoring_config from audit_inputs: direct config edits are for calculator experiments unless copied into inputs. Human tier bounds are enforced. Main/CZ prices are alternatives, partners charged individually.\n\nKnown verified unpointed cards default0; unknown identities error. Banned cards keep legality failures at any hypothetical price. Team caps/individual reference/20% transfer envelope configurable. JSON decks import/export via main/commanders maps; Moxfield Commander/Deck sections supported. Scored exports include submitted deck maps and can be imported for recalculation; --overrides imports an Oracle-ID map and --export-overrides exports it. Companion, rulebreaker and pregame-color-choice permissions require explicit manual review.\n\n42 interactions include verified conditional splits, support and explicit false unions; automated matching reports candidates only.26 padded legal fixtures cover13 archetypes and are not optimized decklists or measured consistency. No simulator, true2HG performance dataset or verified paired cohort was available.\n\nThe delivery session generated and tested files in memory because local writes were disabled, then committed through the authorized GitHub connector. Two inherited tests requiring temporary files could not run locally;35 inherited read-only tests passed. The new audit tests and full new artifacts were exercised in memory; see test_results.json. Reproduction requires writable output directory. Artifact hashes/checks and deterministic regeneration are tested without altering earlier versions.\n"
    context={"index":index,"frame":frame,"config":config,"inputs":inputs,"backend":audited,"models":models,"fixtures":fixtures,"decks":decks,
             "schedule":pointed,"benchmarks":benchmark,"summary":summary}
    for name in list(files):
        if name.endswith(".md"):
            for before,after in (("Bracket3","Bracket 3"),("Season0","Season 0"),("Commander2HG","Commander 2HG"),("paired2HG","paired 2HG"),("verified2HG","verified 2HG"),("ordinary2HG","ordinary 2HG"),("zero-costT2","zero-point turn-two"),("zero-costT3","zero-point turn-three"),("cost2T1","2-point turn-one")):
                files[name]=files[name].replace(before,after)
    return files,context

if __name__=="__main__":
    inputs=json.loads((HERE/"audit_inputs.json").read_text())
    files,context=generate(ROOT,inputs)
    for name,content in files.items():
        path=HERE/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    print(json.dumps(context["summary"],indent=2))
