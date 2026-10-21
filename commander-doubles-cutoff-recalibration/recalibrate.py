"""Deterministic full-list recalibration from pinned repository inputs. No online calls.
--check recomputes all generated files in memory and compares their exact bytes.
"""
import argparse,collections,copy,gzip,hashlib,io,json,math,pathlib,re,sys
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'commander-doubles-final-audit'))
from audit_backend import proposed_price
from ranking import OracleIndex,eligibility,oracle_text
from data_sources import acquire_local
from recalibrated_backend import RecalibratedBackend
from review_inputs import *
from rules_cache import generate_rules
from adversarial_inputs import NEW_TEAMS,fixture,ADDITIONAL_COMBO_REVIEWS

def js(x):return json.dumps(x,indent=2,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n'
def table(rows,fields):
 def fmt(v):return str(round(v,3) if isinstance(v,float) else v).replace('|','/').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(fields)+' |','| '+' | '.join('---' for _ in fields)+' |']+['| '+' | '.join(fmt(r.get(k,'')) for k in fields)+' |' for r in rows])
def generate():
 out={}
 def text(n,s):
  if n.endswith('.md'):
   for a,b in [('Every9610','Every 9,610'),('every3510','every 3,510'),('and3510','and 3,510'),('of9610','of 9,610'),('All21','All 21'),('all50','all 50'),('The50','The 50'),('All13','All 13'),('and8 new','and 8 new'),('all1000','all 1,000'),('all21','all 21'),('All50','All 50'),("source's423","source's 423"),('the50','the 50'),('Every9610','Every 9,610'),('all13','all 13')]:s=s.replace(a,b)
  out[n]=s.encode()
 def csv(n,rows):
  df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
  text(n,df.to_csv(index=False,float_format='%.8g',lineterminator='\n'))
 prior=json.loads((ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text())
 anchor_doc=json.loads((ROOT/'commander-doubles-final-audit/human_calibration_anchors.json').read_text())
 original=pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv')
 frame=original.copy();cards=[json.loads(l) for l in gzip.open(HERE/'data/oracle_current.jsonl.gz','rt')];index=OracleIndex(cards)
 previous_config=json.loads((ROOT/'commander-doubles-final-audit/scoring_config.json').read_text())
 old=RecalibratedBackend(index,frame,previous_config,prior['combos'])
 combos=prior['combos']+ADDITIONAL_COMBO_REVIEWS
 text('pairing_review_rules.json',js(combos))
 effective={};history=[]
 def add(name,zone,points,authority,reason,bounds=None,source='review_inputs.py'):
  oid=index.resolve(name);key=(oid,zone)
  r={'oracle_id':oid,'card_name':index.cards[oid]['name'],'zone':zone,'working_price':int(points),'authority':authority,'reason':reason,'source':source,'approved_range':bounds,'activated':False}
  if key in effective:history.append({'superseded':effective[key],'replacement':r})
  effective[key]=r
 for a in prior['family']:add(a['card_name'],'main',a['main_deck_points'],'provisional_working_price',a['rationale'],source='prior audit family judgment')
 for a in prior['anchors']:add(a['card_name'],a['zone'],a['proposed_points'],'qualitative_zero_anchor' if a['tier']==0 else 'provisional_working_price',a['rationale'],source='original organizer qualitative tier plus assistant numeric choice')
 for a in prior['unbans']:add(a['card_name'],'main',a['hypothetical_main_deck_points'],'hypothetical_banned_price',a['assessment'],source='prior hypothetical unban review')
 for row in ORGANIZER:
  name,points,authority,reason,*rest=row
  add(name,'main',points,authority,reason,rest[0] if rest else None,source='organizer_calibration_2026-10-20.md')
 working=copy.deepcopy(effective)
 for name,points,reason in PROPOSALS:add(name,'main',points,'assistant_proposed_change_awaiting_approval',reason)
 for name,points,reason in CZ_PROPOSALS:add(name,'commanders',points,'assistant_proposed_change_awaiting_approval',reason)
 decisions=sorted(effective.values(),key=lambda r:(r['card_name'],r['zone']))
 ledger={'version':'season0-proposed','as_of':AS_OF,'authoritative_source':'../commander-doubles-final-audit/organizer_calibration_2026-10-20.md','precedence':['latest explicit organizer numerical decision','latest organizer approved numerical range/minimum','preserved original qualitative anchors (not numeric bands)','provisional working numeric choices','assistant proposals awaiting approval','immutable inherited impact and global curve'],
 'qualitative_tiers_are_not_construction_points':True,'removed_assistant_tier_intervals':previous_config['human_tier_price_intervals'],'numeric_band_enforcement':False,'original_50_qualitative_anchors':[{'oracle_id':a['oracle_id'],'card_name':a['card_name'],'zone':a['zone'],'tier':a['tier']} for a in prior['anchors']],'effective_location_decisions':decisions,'supersession_history':history}
 text('calibration_precedence.json',js(ledger));text('human_calibration_anchors.json',js(anchor_doc))
 config={k:v for k,v in previous_config.items() if k not in ('overrides','human_tier_price_intervals')}
 config.update(cutoff=RECOMMENDED_CUTOFF,price_curve=RECOMMENDED_CURVE,status='season0-proposed_not_activated',manual_override_policy='Fixed Oracle/location decisions with explicit authority; qualitative tiers are not numerical intervals.',rules_cache_version='2hg-cache-2026-10-20-v1')
 def override_map(source):
  m={}
  for r in source.values():m.setdefault(r['oracle_id'],{})['main_deck_points' if r['zone']=='main' else 'command_zone_points']=r['working_price']
  return m
 stages={'curve_only':{},'organizer_only':{k:r for k,r in working.items() if r['authority'] in ('explicit_organizer_price','organizer_approved_range','organizer_minimum_working_price','qualitative_zero_anchor')},'calibrated_working':working,'recommended':effective}
 config['overrides']=override_map(effective);text('scoring_config.json',js(config))
 backend=RecalibratedBackend(index,frame,config,combos,prior['anchors'],decisions)
 ids=sorted(set(frame.oracle_id)|{r['oracle_id'] for r in decisions});positions={o:i for i,o in enumerate(ids)};N=len(ids)
 look=frame.set_index('oracle_id').to_dict('index')
 main=np.array([look.get(o,{}).get('main_deck_impact',np.nan) for o in ids]);cz=np.array([look.get(o,{}).get('command_zone_impact',np.nan) for o in ids]);legal=np.array([index.cards[o].get('legalities',{}).get('commander')=='legal' and not index.cards[o]['name'].startswith('Erayo, Soratami Ascendant') for o in ids]);eligible=np.array([bool(eligibility(index.cards[o])) for o in ids])
 def prices(tau,curve,stage='recommended',shift=None,raw=False):
  ss=main.copy();cc=cz.copy()
  if raw:ss=np.array([look.get(o,{}).get('raw_main_deck_impact',np.nan) for o in ids])
  if shift is not None:ss+=shift[0];cc+=shift[1]
  def calc(arr):
   gap=np.maximum(0,np.nan_to_num(arr,nan=-100)-tau)
   if curve=='nonlinear':return np.ceil(15*(gap/25)**1.5).astype(int)
   if curve=='fine_integer':return np.ceil(.6*gap).astype(int)
   return np.select([gap<=0,gap<=5,gap<=10,gap<=15,gap<=20,gap<=25],[0,1,3,5,8,12],default=20).astype(int)
  vals=np.array([calc(ss),calc(cc)*eligible],dtype=int)
  for r in stages[stage].values():vals[0 if r['zone']=='main' else 1,positions[r['oracle_id']]]=r['working_price']
  return vals.reshape(-1)
 selected=prices(RECOMMENDED_CUTOFF,RECOMMENDED_CURVE);oldvalues=np.array([[old.card_price(o,z) for o in ids] for z in ('main','commanders')]).reshape(-1)
 # Every candidate, not merely every override, receives a transparent route/coverage review.
 reassessment=[];schedule=[];changes=[]
 screens={'extra_turn':r'extra turn','life_payment':r'pay .*life|pay life','life_total':r'life total|half .*life|double .*life','draw_denial':r"can.t draw|draw more than|would draw","team_permission":r'your team|teammate','tutor':r'search your library','repeat_resource':r'untap|add .*mana'}
 for i,oid in enumerate(ids):
  c=index.cards[oid];r=look.get(oid,{});m,cp=int(selected[i]),int(selected[N+i]);om,oc=int(oldvalues[i]),int(oldvalues[N+i]);tags=[k for k,pat in screens.items() if re.search(pat,oracle_text(c),re.I)]
  md=effective.get((oid,'main'));cd=effective.get((oid,'commanders'))
  row={'oracle_id':oid,'card_name':c['name'],'main_deck_points':m,'command_zone_points':cp,'previous_main_deck_points':om,'previous_command_zone_points':oc,'main_deck_impact_frozen':r.get('main_deck_impact'),'command_zone_impact_frozen':r.get('command_zone_impact'),'raw_main_impact_frozen':r.get('raw_main_deck_impact'),'specialist_floor_delta':r.get('specialist_floor_delta',0),'commander_eligibility':eligibility(c) or 'ineligible','commander_legality':c.get('legalities',{}).get('commander'),'league_card_legal':bool(legal[i]),'main_authority':md['authority'] if md else 'global_curve_proposal','command_zone_authority':cd['authority'] if cd else 'global_curve_proposal','main_reason':md['reason'] if md else r.get('valuation_explanation','Known identity awaiting impact assessment; no automatic source-cache price.'),'command_zone_reason':cd['reason'] if cd else r.get('command_zone_explanation','Unreviewed command access.'),'old_main_manual_assessment':r.get('manually_assessed',False),'old_cz_manual_assessment':r.get('command_zone_manually_assessed',False),'new_explicit_location_review':bool(md or cd),'text_screen_nomination_only':';'.join(tags),'game_changer':r.get('game_changer',False),'canadian_highlander_points':r.get('canadian_highlander_points',0),'confidence':('explicit_numeric_organizer_decision' if md and md['authority']=='explicit_organizer_price' else 'reviewed_policy_judgment' if md or cd else r.get('confidence','unreviewed')),'version':'season0-proposed','activated':False}
  reassessment.append(row)
  if legal[i] and (m or cp):schedule.append(row)
  for z,op,np_ in [('main',om,m),('commanders',oc,cp)]:
   if op!=np_:
    dec=effective.get((oid,z),{})
    changes.append({'oracle_id':oid,'card_name':c['name'],'zone':z,'previous_points':op,'new_points':np_,'change':np_-op,'authority':dec.get('authority','global_curve_proposal'),'reason':dec.get('reason','Global cutoff/curve change; inherited impact unchanged.'),'league_card_legal':bool(legal[i])})
 reassess=pd.DataFrame(reassessment);schedule=pd.DataFrame(schedule);change=pd.DataFrame(changes).sort_values(['change','card_name','zone'])
 csv('full_candidate_reassessment.csv',reassess);csv('recalibrated_point_schedule.csv',schedule);csv('price_changes.csv',change)
 csv('newly_pointed_cards.csv',change[(change.previous_points==0)&(change.new_points>0)&change.league_card_legal]);csv('newly_unpointed_cards.csv',change[(change.previous_points>0)&(change.new_points==0)&change.league_card_legal])
 csv('exceptions_ledger.csv',decisions)
 newcard=[]
 for oid,c in index.cards.items():
  if oid not in positions and oid not in set(frame.oracle_id):
   if c.get('legalities',{}).get('commander')=='legal':
    newcard.append({'oracle_id':oid,'card_name':c['name'],'status':'known_unpointed_unreviewed','commander_eligible':bool(eligibility(c)),'screen_nomination_only':';'.join(k for k,p in screens.items() if re.search(p,oracle_text(c),re.I)),'not_claimed_powerless':True})
 csv('outside_candidate_universe_review.csv',newcard)
 # Reuse exactly the archived cohorts, including weak/mislabelled lists and illegal archives.
 _,pools,_=acquire_local(ROOT);decks=[]
 for d in json.loads((ROOT/'commander-league-card-point-calibration/data/clean/precons.json').read_text()):
  cmd=set(d['commander_ids']);decks.append({'deck_name':d['name'],'cohort':'official_precons','main':{o:q for o,q in d['counts'].items() if o not in cmd},'commanders':{o:q for o,q in d['counts'].items() if o in cmd},'source':'taw/MTGJSON inherited archive'})
 for cohort,entries in pools.items():
  if cohort=='cedh_train':continue
  unique={}
  for d in entries:
   norm={z:{index.resolve(n):q for n,q in d[z].items()} for z in ('main','commanders')};key=json.dumps(norm,sort_keys=True)
   unique.setdefault(key,{'deck_name':cohort+'_'+hashlib.sha256(key.encode()).hexdigest()[:16],'cohort':cohort,'source':'https://topdeck.gg','event_id':d['event_id'],**norm})
  decks+=list(unique.values())
 assert collections.Counter(d['cohort'] for d in decks)=={'official_precons':174,'cedh_holdout':2520,'bracket3_declared':150}
 fixtures=json.loads((ROOT/'commander-doubles-final-audit/adversarial_decklists/fixtures.json').read_text());team_meta={t['id']:copy.deepcopy(t) for t in prior['teams']}
 team_meta['T08']['sequence']='Corrected basic-only line: A plays Mountain T1, Forest T2, Forest T3 and casts Najeela T3; Swamp T4 then casts Nature Will with 2GG; Island T5, Plains T6. Six lands now provide WUBRG. B has Rogue Passage plus four untapped basics and pays4/taps Passage to make Najeela unblockable. Attack connects, Nature Will untaps A lands, payWUBRG Najeela to repeat combats. Original five-basic T5 claim could not also supply GG for earlier Nature Will; nonbasic fixing could permit an optimized T5 sequence but is absent in this fixture.'
 team_meta['T08']['earliest_demonstrated_turn']=6
 for t in NEW_TEAMS:
  fixtures[t['id']]={who:fixture(t[who+'_cmd'],t[who+'_main'],t[who+'_basics']) for who in ('a','b')};team_meta[t['id']]=t
 for tid,pair in fixtures.items():
  for who,d in pair.items():
   decks.append({'deck_name':tid+'_'+who.upper(),'cohort':'adversarial_fixture','source':'legal padded fixture; not optimized',**{z:{index.resolve(n):q for n,q in d[z].items()} for z in ('main','commanders')}})
   text('adversarial_decklists/'+tid+'_'+who.upper()+'.txt','Commander\n'+'\n'.join(f'{q} {n}' for n,q in d['commanders'].items())+'\n\nDeck\n'+'\n'.join(f'{q} {n}' for n,q in d['main'].items())+'\n')
 text('adversarial_decklists/fixtures.json',js(fixtures))
 rows=[];cols=[];values=[]
 for di,d in enumerate(decks):
  for zi,z in enumerate(('main','commanders')):
   for o,q in d[z].items():
    if o in positions:rows.append(di);cols.append(positions[o]+zi*N);values.append(q)
    else:assert backend.card_price(o,z)==0
 X=csr_matrix((values,(rows,cols)),shape=(len(decks),2*N));cohorts=np.array([d['cohort'] for d in decks]);newtot=np.asarray(X@selected).reshape(-1);oldtot=np.asarray(X@oldvalues).reshape(-1)
 newcz=np.asarray(X[:,N:]@selected[N:]).reshape(-1);changed=pd.read_csv(ROOT/'commander-doubles-final-audit/updated_cohort_benchmarks.csv').set_index('deck_name')
 benches=[]
 for di,d in enumerate(decks):
  report=backend.score({z:d[z] for z in ('main','commanders')});assert report['total']==newtot[di]
  if d['cohort']!='adversarial_fixture':assert oldtot[di]==changed.loc[d['deck_name'],'audited_points'],d['deck_name']
  if d['cohort']=='adversarial_fixture':assert report['officially_legal'],(d['deck_name'],report['legality_issues'])
  pts=sorted((r['total'] for r in report['rows']),reverse=True)
  benches.append({'deck_name':d['deck_name'],'cohort':d['cohort'],'source':d['source'],'old_points':int(oldtot[di]),'new_points':int(newtot[di]),'change':int(newtot[di]-oldtot[di]),'command_zone_points':int(newcz[di]),'command_zone_share':newcz[di]/newtot[di] if newtot[di] else 0,'pointed_card_count':sum(r['quantity'] for r in report['rows'] if r['points_each']),'top3_point_share':sum(pts[:3])/newtot[di] if newtot[di] else 0,'officially_legal':report['officially_legal'],'legality_flags':';'.join(report['legality_issues'])})
 bench=pd.DataFrame(benches);csv('cohort_score_changes.csv',bench)
 from scipy.stats import spearmanr,kendalltau
 rank_comparison=[];cohort_overlap=[]
 for co,g in bench.groupby('cohort'):
  rank_comparison.append({'cohort':co,'n':len(g),'Spearman_old_new_cost_order':float(spearmanr(g.old_points,g.new_points).statistic),'Kendall_old_new_cost_order':float(kendalltau(g.old_points,g.new_points).statistic),'median_pointed_cards':float(g.pointed_card_count.median()),'median_command_zone_share':float(g.command_zone_share.median()),'median_top3_share':float(g.top3_point_share.median()),'interpretation':'Cost-rank stability only; neither schedule is a validated strength label.'})
 for hi,lo in [('cedh_holdout','bracket3_declared'),('bracket3_declared','official_precons'),('cedh_holdout','official_precons')]:
  a=bench[bench.cohort==hi].new_points.to_numpy();b=np.sort(bench[bench.cohort==lo].new_points.to_numpy());less=np.searchsorted(b,a,side='left');leq=np.searchsorted(b,a,side='right');cohort_overlap.append({'higher_label':hi,'lower_label':lo,'pairs':len(a)*len(b),'strict_cost_ordering_fraction':float(sum(less)/(len(a)*len(b))),'ties_half_cost_ordering_fraction':float(sum((less+leq)/2)/(len(a)*len(b))),'shared_observed_scores':len(set(a)&set(b)),'interpretation':'Cross-label cost overlap, not competitive predictive accuracy.'})
 csv('cohort_rank_stability.csv',rank_comparison);csv('cohort_cost_overlap.csv',cohort_overlap)

 def summary(v):return {'n':len(v),'min':int(np.min(v)),'p10':float(np.quantile(v,.1)),'p25':float(np.quantile(v,.25)),'median':float(np.median(v)),'mean':float(np.mean(v)),'p75':float(np.quantile(v,.75)),'p90':float(np.quantile(v,.9)),'max':int(np.max(v)),'unique_scores':len(set(v)),'zero_decks':int(sum(v==0))}
 distribution=[]
 rng=np.random.default_rng(20261020)
 for cohort in sorted(set(cohorts)):
  for method,totals in [('previous_audit',oldtot),('recalibrated',newtot)]:
   v=totals[cohorts==cohort];boots=np.median(v[rng.integers(0,len(v),(1000,len(v)))],axis=1)
   distribution.append({'cohort':cohort,'method':method,**summary(v),'bootstrap_median_low':float(np.quantile(boots,.025)),'bootstrap_median_high':float(np.quantile(boots,.975))})
 csv('cohort_distribution_summary.csv',distribution)
 # Explicit evidence/exception dependence and reviewed functional-family coverage.
 override_vector=np.zeros(2*N,dtype=int)
 for decision in decisions:
  j=positions[decision['oracle_id']]+(N if decision['zone']=='commanders' else 0);override_vector[j]=selected[j]
 override_tot=np.asarray(X@override_vector).reshape(-1)
 csv('exception_dependence.csv',[{'cohort':co,'median_total_points':float(np.median(newtot[cohorts==co])),'median_fixed_exception_points':float(np.median(override_tot[cohorts==co])),'aggregate_point_share_from_fixed_exceptions':float(sum(override_tot[cohorts==co])/sum(newtot[cohorts==co])),'interpretation':'All curve impacts and exceptions are judgments; this measures numerical dependence on fixed exceptions, not empirical evidence.'} for co in sorted(set(cohorts))])
 extra_rows=[]
 for oid,c in index.cards.items():
  if c.get('legalities',{}).get('commander')=='legal' and 'extra turn' in oracle_text(c).lower():
   dec=effective.get((oid,'main'),{})
   extra_rows.append({'oracle_id':oid,'card_name':c['name'],'main_points':backend.card_price(oid,'main'),'cz_points':backend.card_price(oid,'commanders'),'explicit_location_review':bool(dec),'authority':dec.get('authority','global_curve_proposal'),'reason':dec.get('reason','Needs explicit extra-turn family review.'),'nomination_only_not_automatic_tax':True})
 assert all(r['explicit_location_review'] for r in extra_rows),[r for r in extra_rows if not r['explicit_location_review']]
 csv('complete_extra_turn_family_review.csv',extra_rows)

 sensitivity=[];boundary=[];perdeck=[];policyissues=[];concentrations=[]
 for tau in CUTOFFS:
  for curve in ('existing_tiers','fine_integer','nonlinear'):
   for stage in stages:
    p=prices(tau,curve,stage);tot=np.asarray(X@p).reshape(-1);m,c=p[:N],p[N:];union=legal&((m>0)|(c>0))
    legalcount={'pointed_main_cards':int(sum(legal&(m>0))),'pointed_commander_options':int(sum(legal&(c>0))),'pointed_identities':int(sum(union)),'main_price_p50':float(np.median(m[legal&(m>0)])),'main_price_p90':float(np.quantile(m[legal&(m>0)],.9)),'main_price_max':int(max(m[legal]))}
    for cohort in sorted(set(cohorts)):
     v=tot[cohorts==cohort];sensitivity.append({'cutoff':tau,'curve':curve,'exception_stage':stage,'cohort':cohort,**legalcount,**summary(v)})
    if curve=='nonlinear':
     for di,d in enumerate(decks):perdeck.append({'deck_name':d['deck_name'],'cohort':d['cohort'],'cutoff':tau,'exception_stage':stage,'points':int(tot[di])})
    if stage=='recommended':
     for identity in sorted(set(str(look.get(o,{}).get('color_identity','')) for o in ids)):
      mask=np.array([str(look.get(o,{}).get('color_identity',''))==identity for o in ids])&legal
      concentrations.append({'cutoff':tau,'curve':curve,'color_identity':identity,'pointed_main':int(sum(mask&(m>0))),'pointed_cz':int(sum(mask&(c>0)))})
  for zone,ss in [('main',main),('commanders',cz)]:
   valid=np.where(legal&np.isfinite(ss)&(eligible if zone=='commanders' else True))[0]
   above=sorted([i for i in valid if ss[i]>tau],key=lambda i:(ss[i]-tau,index.cards[ids[i]]['name']))[:20]
   below=sorted([i for i in valid if ss[i]<=tau],key=lambda i:(tau-ss[i],index.cards[ids[i]]['name']))[:20]
   for stage in ('curve_only','recommended'):
    pp=prices(tau,'nonlinear',stage)
    for side,arr in [('above',above),('below_or_equal',below)]:
     for n,i in enumerate(arr,1):
      dec=effective.get((ids[i],zone),{})
      boundary.append({'cutoff':tau,'stage':stage,'zone':zone,'side':side,'nearest_rank':n,'card_name':index.cards[ids[i]]['name'],'oracle_id':ids[i],'frozen_impact':ss[i],'distance':abs(ss[i]-tau),'points':int(pp[i+(N if zone=='commanders' else 0)]),'authority':dec.get('authority','global_curve_proposal'),'reason':dec.get('reason','Unchanged inherited assessment, not an experimentally established boundary.')})
  rawp=prices(tau,'nonlinear','curve_only');fullp=prices(tau,'nonlinear','recommended')
  # Named counterexamples per tested threshold; no automatic claim that every ordinary category is undeserving.
  for name,points,reason in PROPOSALS:
   i=positions[index.resolve(name)]
   if rawp[i]>0 and points==0:policyissues.append({'cutoff':tau,'card_name':name,'issue':'ordinary_useful_card_tax_in_curve','curve_only_points':int(rawp[i]),'proposed_points':int(fullp[i]),'judgment':reason})
   if rawp[i]==0 and points>=3:policyissues.append({'cutoff':tau,'card_name':name,'issue':'reviewed_exceptional_engine_omitted_by_curve','curve_only_points':0,'proposed_points':int(fullp[i]),'judgment':reason})
 csv('cutoff_sensitivity.csv',sensitivity);csv('cutoff_before_after_boundaries.csv',boundary);csv('cutoff_per_deck_scores.csv',perdeck);csv('cutoff_policy_counterexamples.csv',policyissues);csv('cutoff_color_concentration.csv',concentrations)
 # Subjective-rating perturbation is scenario analysis, NOT a statistical confidence interval.
 perturb=[];stability=[]
 for scenario in range(100):
  shifts=(rng.uniform(-2,2,N),rng.uniform(-2,2,N));p=prices(RECOMMENDED_CUTOFF,RECOMMENDED_CURVE,shift=shifts);tot=np.asarray(X@p).reshape(-1)
  for tau in CUTOFFS:
   nominal=prices(tau,RECOMMENDED_CURVE);perturbed=prices(tau,RECOMMENDED_CURVE,shift=shifts)
   nominal_set=legal&((nominal[:N]>0)|(nominal[N:]>0));changed_set=legal&((perturbed[:N]>0)|(perturbed[N:]>0))
   stability.append({'scenario':scenario,'cutoff':tau,'membership_jaccard':float(sum(nominal_set&changed_set)/sum(nominal_set|changed_set)),'membership_flips':int(sum(nominal_set!=changed_set)),'pointed_identities':int(sum(changed_set))})
  for cohort in sorted(set(cohorts)):perturb.append({'scenario':scenario,'cohort':cohort,'median':float(np.median(tot[cohorts==cohort])),'legal_pointed_identities':int(sum(legal&((p[:N]>0)|(p[N:]>0)))),'interpretation':'Independent uniform +/-2 frozen impact perturbation; explicit price exceptions held fixed; not uncertainty probability.'})
 csv('impact_judgment_sensitivity.csv',perturb);csv('cutoff_membership_stability.csv',stability)
 nofloor=prices(RECOMMENDED_CUTOFF,RECOMMENDED_CURVE,raw=True);nf=np.asarray(X@nofloor).reshape(-1)
 csv('specialist_floor_control.csv',[{'cohort':cohort,'with_floor_median':float(np.median(newtot[cohorts==cohort])),'without_floor_median':float(np.median(nf[cohorts==cohort])),'changed_decks':int(sum(newtot[cohorts==cohort]!=nf[cohorts==cohort])),'note':'No retuning; explicit exceptions retained.'} for cohort in sorted(set(cohorts))])
 # One-point sensitivity of ten largest non-explicit main prices; no permanent new override.
 perturb_cards=[]
 movable=[r for r in schedule.to_dict('records') if r['main_authority']!='explicit_organizer_price' and r['main_deck_points']>0]
 for r in sorted(movable,key=lambda r:(-r['main_deck_points'],r['card_name']))[:10]:
  j=positions[r['oracle_id']]
  for delta in (-1,1):
   v=newtot+np.asarray(X[:,j].toarray()).reshape(-1)*delta
   for co in sorted(set(cohorts)):perturb_cards.append({'card_name':r['card_name'],'price_change':delta,'cohort':co,'median':float(np.median(v[cohorts==co])),'affected_decks':int(sum(np.asarray(X[:,j].toarray()).reshape(-1)[cohorts==co]>0))})
 csv('premium_price_sensitivity.csv',perturb_cards)
 # Exact all unordered distinct pairs: no Monte Carlo zero-pass claims.
 budget=[]
 for cohort in sorted(set(cohorts)-{'adversarial_fixture'}):
  for method,totals in [('previous',oldtot),('recalibrated',newtot)]:
   vv=np.sort(totals[cohorts==cohort]);n=len(vv)
   for ref in (40,50,60,70):
    for policy,cap in [('equal',ref),('transfer20',ref+ref//5),('pooled_only',None)]:
     admitted=0
     for i,a in enumerate(vv[:-1]):
      limit=min(2*ref-a,cap) if cap is not None else 2*ref-a
      if cap is None or a<=cap:admitted+=max(0,int(np.searchsorted(vv,limit,side='right'))-i-1)
     budget.append({'cohort':cohort,'method':method,'reference':ref,'team_cap':2*ref,'individual_cap':cap,'policy':policy,'all_distinct_pairs':n*(n-1)//2,'admitted':admitted,'admitted_fraction':admitted/(n*(n-1)//2)})
 csv('budget_stress_test.csv',budget)
 teams=[]
 for tid,pair in fixtures.items():
  report=backend.team(pair['a'],pair['b']);before=old.team(pair['a'],pair['b']);meta=team_meta[tid]
  teams.append({'team_id':tid,'a_commander':';'.join(pair['a']['commanders']),'b_commander':';'.join(pair['b']['commanders']),'previous_a':before['a']['total'],'previous_b':before['b']['total'],'previous_team':before['total'],'new_a':report['a']['total'],'new_b':report['b']['total'],'new_team':report['total'],'budget_compliant_60_120_72':report['budget_compliant'],'both_decks_legal':report['both_decks_legal'],'sequence':meta.get('sequence',meta.get('win_line',meta.get('line','See prior adversarial archetype narrative.'))),'risk':meta.get('risk',meta.get('issue_type','Prior controller-validated stress case')),'fixture_quality':'100-card legal basic-padded illustration, not optimized deck or probability estimate','turn_or_counterexample':meta.get('earliest_demonstrated_turn',meta.get('turn'))})
 csv('adversarial_retest_scores.csv',teams)
 # Explain point concentration and common expensive/free competitive cards; adoption is not power.
 usage=collections.Counter();pointed_usage=collections.Counter()
 for d in decks:
  if d['cohort']=='cedh_holdout':usage.update(d['main'].keys())
 for o,n in usage.items():
  if backend.card_price(o,'main'):pointed_usage[o]=n
 csv('competitive_card_cost_audit.csv',[{'oracle_id':o,'card_name':index.cards[o]['name'],'deck_inclusion':n,'share_of_2520':n/2520,'main_points':backend.card_price(o,'main'),'command_zone_points':backend.card_price(o,'commanders'),'meaning':'Observed archived inclusion; not independent power or applicability.'} for o,n in usage.most_common()])
 # Keep disagreement/risk queues explicit, including all 423 low-confidence tail entries.
 queue=[]
 for r in reassessment:
  why=[]
  if r['main_authority']=='assistant_proposed_change_awaiting_approval' or r['command_zone_authority']=='assistant_proposed_change_awaiting_approval':why.append('new_numeric_proposal')
  if r['league_card_legal'] and any(pd.notna(r[k]) and abs(r[k]-RECOMMENDED_CUTOFF)<=2.5 for k in ('main_deck_impact_frozen','command_zone_impact_frozen')):why.append('within_2_5_cutoff')
  if r['old_main_manual_assessment'] is False and look.get(r['oracle_id'],{}).get('main_deck_rank',10001)<=1000:why.append('top1000_low_confidence_tail')
  if why:queue.append({'oracle_id':r['oracle_id'],'card_name':r['card_name'],'main_points':r['main_deck_points'],'cz_points':r['command_zone_points'],'reasons':';'.join(why),'priority':'high' if 'new_numeric_proposal' in why else 'medium'})
 csv('manual_review_queue.csv',queue)
 cache=generate_rules(index,prior);text('two_hg_rules_cache.jsonl',''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in cache))
 text('two_hg_rules_cache.md',rules_report(cache))
 # Price changes for all premium functional comparisons, including admitted deliberate exceptions.
 text('card_family_reviews.md',family_report(index,backend,old,prior,decisions))
 text('adversarial_retest.md',adversarial_report(teams))
 text('organizer_approval_queue.md',approval_report(decisions,queue))
 report=cutoff_report(sensitivity,policyissues,distribution,perturb,concentrations,decisions)
 report+='\n\n## Fixed-exception dependence and near-floor stability\n\n'+table([{'cohort':co,'share_of_all_points_from_fixed_exceptions':float(sum(override_tot[cohorts==co])/sum(newtot[cohorts==co]))} for co in sorted(set(cohorts))],['cohort','share_of_all_points_from_fixed_exceptions'])
 report+='\n\n'+table([{'cutoff':tau,'median_membership_flips':float(np.median([r['membership_flips'] for r in stability if r['cutoff']==tau])),'median_membership_Jaccard':float(np.median([r['membership_jaccard'] for r in stability if r['cutoff']==tau]))} for tau in CUTOFFS],['cutoff','median_membership_flips','median_membership_Jaccard'])+'\n\nThe measured dominance of fixed exceptions limits what a cutoff alone accomplishes. This is a human-led candidate schedule, not a statistically learned power function.79.5 is a plausible smaller policy list if the organizer prefers sparsity over the stated perturbation margin;77.5 is recommended for the more stable starting pool, not because of an observed win-rate optimum.\n'
 text('cutoff_recalibration_report.md',report)
 text('recalibration_executive_summary.md',executive(schedule,change,distribution,teams,budget,decisions))
 text('proposed_team_budget_analysis.md',budget_report(budget,teams))
 text('README.md',readme())
 # Current Oracle changes and source provenance; no claim new card data is fully power-assessed.
 frozen_cards={c['oracle_id']:c for c in [json.loads(l) for l in gzip.open(ROOT/'commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz','rt')]}
 diff=[]
 for o,c in index.cards.items():
  before=frozen_cards.get(o)
  if before is None or before.get('oracle_text')!=c.get('oracle_text') or before.get('legalities')!=c.get('legalities'):
   diff.append({'oracle_id':o,'card_name':c['name'],'change':'new_current_identity' if before is None else 'Oracle_or_legality_changed','commander_legality':c.get('legalities',{}).get('commander'),'power_reassessment_status':'requires_review' if o not in effective else 'see_location_ledger'})
 csv('oracle_snapshot_changes.csv',diff)
 provenance=json.loads((HERE/'data/source_snapshot_manifest.json').read_text());provenance['starting_commit']='61fe3cbba32443e083af9d96bd7fe79405e79a8d';provenance['source_inventory']='../commander-card-power-research-v1/source_inventory.csv';provenance['licenses']='Scryfall service data is not an invented open-data license; Magic card text and official rules © Wizards. Prior project source/license notices preserved. Noncommercial local research; no images/market prices acquired.';provenance['input_sha256']={}
 for path in [ROOT/'commander-doubles-final-audit/organizer_calibration_2026-10-20.md',ROOT/'commander-doubles-final-audit/audit_inputs.json',ROOT/'commander-top1000-power-ranking/candidate_inventory.csv',HERE/'review_inputs.py',HERE/'adversarial_inputs.py',HERE/'rules_cache.py',HERE/'recalibrate.py',HERE/'recalibrated_backend.py',HERE/'audit_tests.py',HERE/'rules_arithmetic.py',ROOT/'commander-league-card-point-calibration/data/clean/precons.json',ROOT/'data/tournament_snapshots/topdeck/manifest.json']:
  provenance['input_sha256'][str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 provenance['method_limitations']=['All frozen impact coefficients are judgment, not measured power.','No new outcome labels or validated paired 2HG data.','All 9,610 candidate routes reevaluated, not 9,610 new expert ratings.','Known current identities outside candidate universe zero and explicitly unreviewed.','No cohort label used to fit prices or determine cutoff.']
 text('source_provenance.json',js(provenance))
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
 colors={'official_precons':'#2b8cbe','bracket3_declared':'#31a354','cedh_holdout':'#d95f0e'}
 for co,color in colors.items():
  vals=newtot[cohorts==co];ax[0,0].hist(vals,bins=np.arange(0,521,10),density=True,histtype='step',color=color,label=co,linewidth=1.7)
  rr=[r for r in sensitivity if r['cohort']==co and r['curve']=='nonlinear' and r['exception_stage']=='recommended'];ax[1,0].plot([r['cutoff'] for r in rr],[r['median'] for r in rr],marker='o',label=co,color=color)
 ax[0,0].set(xlabel='Construction points (not win probability)',ylabel='Density',title='Recalibrated archived cohorts');ax[0,0].legend(fontsize=8)
 for st in stages:
  rr=[r for r in sensitivity if r['cohort']=='official_precons' and r['curve']=='nonlinear' and r['exception_stage']==st];ax[0,1].plot([r['cutoff'] for r in rr],[r['pointed_identities'] for r in rr],marker='o',label=st)
 ax[0,1].axvline(RECOMMENDED_CUTOFF,color='black',ls='--');ax[0,1].set(xlabel='Frozen impact cutoff',ylabel='Legal pointed identities',title='Policy admission and explicit exceptions');ax[0,1].legend(fontsize=8)
 ax[1,0].set(xlabel='Frozen impact cutoff',ylabel='Median construction points',title='No deck/year normalization');ax[1,0].legend(fontsize=8)
 ax[1,1].bar([t['team_id'] for t in teams],[t['new_team'] for t in teams],color='#756bb1');ax[1,1].axhline(120,color='black',ls='--',label='Proposed120 team cap');ax[1,1].tick_params(axis='x',rotation=90);ax[1,1].set(ylabel='Team core points',title='Legal basic-padded illustrative team fixtures');ax[1,1].legend(fontsize=8)
 buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=150,metadata={'Software':'CommanderDoublesRecalibration'});plt.close(fig);out['recalibration_visualizations.png']=buffer.getvalue()

 text('generated_artifact_hashes.json',js({k:hashlib.sha256(v).hexdigest() for k,v in sorted(out.items())}))
 return out

def rules_report(cache):
 s='''# Persistent 2HG rules cache — v1, verified 2026-10-20

Pinned current Scryfall Oracle snapshot: 2026-10-20; official landing still links Comprehensive Rules effective September 25. Every JSONL interaction includes canonical identities, current full Oracle text and hash, exact rule references, required controllers/state, pricing implications, dates, sources and invalidators. This is a conditional rules interpretation, not judge certification or automatic state/combo recognition.

Primary sources: [CR](https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt), [official 2HG format](https://magic.wizards.com/en/formats/two-headed-giant), [rules landing](https://magic.wizards.com/en/rules), [banlist](https://magic.wizards.com/en/banned-restricted-list), [Oracle bulk API](https://scryfall.com/docs/api/bulk-data).

60 shared starting life follows official Commander/2HG format modifier. Fifteen shared poison:810.8d; proliferation selects at most one head per team:701.34b. First shared draw skipped:103.8b/810.6. Multiplayer first mulligan free:103.5c; individual choices:103.5d. Separate resources:810.5. Each head draws/plays land:805.4b,c; priority granted to teams:805.5, normal opponent response windows remain. Win/loss/cannot-win/cannot-lose propagate to team:810.8a. Life queries use team pool but life-gain/loss events remain player events:810.9/810.9a. Extra turns, skipped steps and controlling another player's turn apply to team:805.8. Ending turn is CURRENT **724**, not outdated 721 (which now concerns Station cards). Turn control is723.

**Unresolved documentation conflict:** CR903.10a/704.6c uses 21 combat damage to an individual head from one commander; format landing says team21. Recommend CR per-head tracking, then team loss, but organizer must approve written precedence. No silent custom aggregation.

**October freshness gap:** current downloaded903.5e still says no sideboards, while [October19 bulletin](https://magic.wizards.com/en/news/announcements/mystery-booster-commander-edition-update-bulletin) announces prospective rulebreaker changes. Fresh Oracle has79 additional identities versus old snapshot and one changed existing card, but no resolved Tolabow identity. Unknown names error and unsupported rulebreaker/color/companion construction is not auto-approved. Recheck linked CR/Oracle before league lock.

No experimental unbans activated. The seven previously discussed banned cards retain official illegality regardless of hypothetical points. Cache does not import official Bracket3 gameplay restrictions as league law, and no blanket infinite-combo or turn-seven rule is introduced.

'''
 s+=table([{'id':r['id'],'cards':'; '.join(c['card_name'] for c in r['cards']),'status':r['status'],'rules':'; '.join(r['exact_rule_references']),'ruling':r['ruling']} for r in cache],['id','cards','status','rules','ruling'])
 s+='\n\nInvalidate any record when its Oracle text/rule hash, controller split, starting life, team count, or relevant league permission changes. Rebuild from refresh_sources.py only deliberately: online refresh changes a versioned input; ordinary recalculation stays offline. Existence of cited rule numbers is automatically checked, while semantic applicability is a manual interpretation recorded here.\n'
 return s

def family_report(index,new,old,prior,decisions):
 groups={
 'Additional complete extra-turn and life-family pass':[r[0] for r in PROPOSALS if r[0] not in {x[0] for x in ORGANIZER}],
 'Fast mana and consistency':['Demonic Tutor','Vampiric Tutor','Enlightened Tutor','Imperial Seal','Mystical Tutor','Worldly Tutor','Gamble','Scheming Symmetry','Sol Ring','Mana Vault','Chrome Mox','Mox Diamond','Mox Opal','Lotus Petal','Dark Ritual','Elvish Spirit Guide','Simian Spirit Guide','Chancellor of the Tangle','Ancient Tomb'],
 'Win protection versus ordinary interaction':['Silence',"Orim's Chant",'Grand Abolisher','Ranger-Captain of Eos','Voice of Victory','Defense Grid','Fierce Guardianship','Force of Will','Counterspell','Abrupt Decay','Swords to Plowshares','Toxic Deluge','Veil of Summer',"Teferi's Protection","Angel's Grace"],
 'Extra team turns and converters':['Final Fortune','Last Chance',"Warrior's Oath",'Time Warp','Temporal Manipulation','Capture of Jingzhou','Savor the Moment','Stitch in Time','Chance for Glory',"Alchemist's Gambit",'Temporal Mastery','Temporal Trespass','Nexus of Fate','Walk the Aeons','Time Stretch','Expropriate','Time Sieve','Sage of Hours','Wanderwine Prophets','Timestream Navigator','Lighthouse Chronologist','Sundial of the Infinite','Mindslaver','Emrakul, the Promised End'],
 'Shared-life engines versus slow payoffs':['Necropotence','Necrodominance','Ad Nauseam',"Bolas's Citadel","K'rrik, Son of Yawgmoth",'Sylvan Library','Black Market Connections','Razaketh, the Foulblooded','Aetherflux Reservoir','Test of Endurance','Felidar Sovereign','Serra Ascendant','Sorin Markov','Heartless Hidetsugu','Fraying Omnipotence','Gray Merchant of Asphodel','Exsanguinate','Torment of Hailfire'],
 'Draw denial, wheels and ordinary engines':['Narset, Parter of Veils','Notion Thief','Wheel of Fortune','Timetwister','Windfall','Time Spiral','Consecrated Sphinx','Seedborn Muse','Rhystic Study','Mystic Remora','Esper Sentinel','Smothering Tithe','The One Ring'],
 'Symmetric hate versus asymmetric denial':['Collector Ouphe','Null Rod','Stony Silence','Rule of Law','Eidolon of Rhetoric','Ethersworn Canonist','Archon of Emeria','Deafening Silence','Drannith Magistrate','Opposition Agent','Cursed Totem','Trinisphere','Sphere of Resistance','Thorn of Amethyst','Winter Orb','Static Orb','Stasis','Humility','Blood Moon'],
 'Specialist enablers and interchangeable pieces':['Food Chain','Underworld Breach',"Thassa's Oracle",'Demonic Consultation','Training Grounds',"Biomancer's Familiar",'Zirda, the Dawnwaker','Agatha of the Vile Cauldron','Chain of Smog','Witherbloom Apprentice','Dualcaster Mage','Twinflame','Intruder Alarm','Steward of Solidarity','Helm of Obedience','Rest in Peace','Grapeshot','Tendrils of Agony',"Nature's Will"],
 'Command access audit':['Kinnan, Bonder Prodigy','Magda, Brazen Outlaw','Rograkh, Son of Rohgahh','Thrasios, Triton Hero','Tymna the Weaver','Sisay, Weatherlight Captain','Kenrith, the Returned King','Najeela, the Blade-Blossom','Inalla, Archmage Ritualist','Derevi, Empyrial Tactician',"Yuriko, the Tiger's Shadow",'Heartless Hidetsugu','Breena, the Demagogue','Tivit, Seller of Secrets','Obeka, Brute Chronologist']}
 s='''# Card-family consistency review

Every9610 original candidate identity and every3510 command-zone candidate passes the new authority/location/legality/threshold review route. This does **not** mean9610 new manual expert ratings: inherited unreviewed priors remain unreviewed. The full_candidate_reassessment.csv preserves both frozen impact values, evidence and every decision route. The full Oracle database is current and identifies known unpointed cards; outside_candidate_universe_review.csv explicitly lists legal identities still lacking a reviewed impact. Text screening only nominates cards; it assigns no strength coefficients or automatic price. No source popularity is treated as applicability and no combo count creates points.

The50 qualitative anchors are unchanged. The copied original anchor JSON is archival: its earlier proposed_points fields are not the current numeric schedule; calibration_precedence.json is authoritative for effective prices. Old numerical band enforcement was an assistant policy error and is removed. Later explicit prices/ranges supersede earlier working choices, not the underlying qualitative tiers. Same-qualitative-tier cards need not share a price.

'''
 for title,names in groups.items():
  s+='\n## '+title+'\n\n';rows=[]
  for name in names:
   o=index.resolve(name);d=next((d for d in decisions if d['oracle_id']==o and d['zone']=='main'),{})
   rows.append({'card':name,'old_main':old.card_price(o,'main'),'new_main':new.card_price(o,'main'),'old_CZ':old.card_price(o,'commanders') if eligibility(index.cards[o]) else '—','new_CZ':new.card_price(o,'commanders') if eligibility(index.cards[o]) else '—','authority':d.get('authority','inherited curve'),'reason':d.get('reason','Unchanged frozen assessment; see full candidate record.')})
  s+=table(rows,['card','old_main','new_main','old_CZ','new_CZ','authority','reason'])+'\n'
 s+='''
## Remaining deliberate exceptions and disagreements

Silence14 versus Chant12: Silence shuts both opposing heads out, Chant only targets one. The high Chant tier is organizer judgment, not a rules claim of equivalence. Voice12 is combat-only and prevents opposing activated abilities as well as spells; must attack, while Abolisher13 applies entire shared turn to spells and specified permanent activated abilities. These are related protections, not functional duplicates.

Conventional Time Warp/Manipulation/Capture all6; Final Fortune/Last Chance/Oath all7; Ouphe/Null Rod/Stony all2. These true family comparisons are aligned. ESG6 versus SSG5 is inherited working judgment (color/use breadth), Chancellor5 newly proposed despite opening-only restriction; this difference needs organizer playtest rather than a claim of empirically precise one-point superiority. Training Grounds1/Biomancer1 versus Zirda3 main is a documented broader-permanent scope exception; costs and minimum-one restriction remain.

Swords1, Toxic2 and Veil2 stay at prior chosen low prices even though several other ordinary answers are proposed free. Their qualitative human tiers are preserved; exact integer choices remain working judgments. A blanket free-interaction policy would contradict these positive qualitative anchors, so no silent extension is made.

Free CZ Kenrith/Najeela/Inalla/Derevi/Yuriko are authoritative qualitative zeros despite high prior access assessments and known competitive strategies. Adversarial counterexamples are preserved, not repriced away. Many normal tutors (Diabolic Tutor), ordinary counters and fetchlands stay free. Exceptional acceleration/tutors/engines remain priced. Interchangeable payoffs are not universally priced merely for combo membership: Apprentice/Twinflame/Steward may remain free while Chain/Dualcaster/Alarm are individually reviewed enablers.

Game Changers and Canadian Highlander nominate expert concern; neither list supplies correct2HG prices. Cyclonic Rift remains human free despite Game Changer/previous impact; ordinary control separation supports downgrade. Sol Ring15 versus independent Canadian Highlander relative points is a format-policy difference, not a conflict in identity. No official ban is undone by a score. New proposed prices and all borderline decisions remain in approval/manual-review queues.
'''
 return s

def adversarial_report(teams):
 s='''# Adversarial retest

All13 prior teams and8 new cases are rescored. Each fixture is exactly100 cards and Commander-legal under the checked snapshot, but filled with basics to isolate a line. These are not optimized full competitive builds, opening-hand probabilities, actual games, or claims of consistency. New teams14–21 include additional team turns, life manipulation, draw denial, same-controller Sieve, and resource-ownership counterexamples. No extra points are charged for interaction matches.

'''
 s+=table(teams,['team_id','a_commander','b_commander','previous_team','new_a','new_b','new_team','budget_compliant_60_120_72'])+'\n'
 for t in teams:s+='\n## '+t['team_id']+'\n\n'+str(t['sequence'])+'\n\n'+str(t['risk'])+'\n'
 s+='''
## Strong low-point constructions that remain

Double-Yuriko: both commanders are human free; T1 Changeling Outcast each, later commander ninjutsu plus own Brainstorm/topdeck Draco on T3. Two trigger resolutions each lose16 for both opposing heads, total64 shared loss. Requires two connected attackers and both stacked topdecks, not an automatic win probability. Instant creature removal, countering Brainstorm/trigger, prevention or blocking defeats line. No price on a teammate pairing is introduced.

Najeela/Derevi: both human-free CZ; Nature's Will and teammate Rogue's Passage can still assemble recurring combats. Nature's Will untaps its controller lands, Derevi can target teammate lands; actual combat connection and WUBRG payment are required. Removing Najeela/engine, blocking, land interaction or combat restrictions breaks line. Human zero is retained even when dangerous.

Chain of Smog A with Apprentice B: B must be the targeted discarder who chooses copies; copied spells trigger B magecraft. A does not need to control Apprentice. Thirty B-copy magecraft triggers drain60 against two opposing heads. T1 version requires both opening Chancellor reveals and correct own lands; Chancellor proposed5 each catches acceleration but ordinary T2 assembly remains cheap. No measured consistency given.

Dualcaster A/Twinflame B: B's original target must be B's creature. A-copy changes target to own Dualcaster to repeat. Leaving the original B target unchanged on a later copy can terminate the loop even though illegal for A, because copied target preservation follows707.10c. No opponent response windows are removed without separately priced protection.

Sieve/Tivit: five artifacts must be controlled by Sieve owner. A owns both in the working line; split controllers false positive. Additional team turns do not make summoning sickness, removal, combat connection or artifact costs disappear.

R14 extra-turn baseline can occur T2 plus its extra turn (A two Mountains casts Fortune; B Plains leaves one mana for Sundial). Conservative fixture turn label3 is not a claim it needs three turns. R20 two Savors with alternating mana availability demonstrate two draws/land drops per head, but the whole team skips untap, so no fabricated resource refresh.

R21 Krrik is explicitly a no-win-on-its-own resource test. Shared life is not shared mana. The prior report's cheap team cores remain strong enough that no positive total budget excludes all of them. This is an intended synergy-reward consequence to discuss openly, not evidence the cohort medians validate fairness.

Recommendation: price reviewed exceptional individual engines and acceleration; run recorded interactive Season0 games and require declarative strategy review for free-command-zone decks. Do not activate blanket infinite-combo, turn-seven, or widespread two-card-combination bans. If actual repetitive nonparticipation dominates, propose a named restriction with evidence for organizer approval. Existing official bans remain in force.
'''
 return s

def approval_report(decisions,queue):
 pending=[r for r in decisions if r['authority'] in ('assistant_proposed_change_awaiting_approval','provisional_working_price','organizer_minimum_working_price','organizer_approved_range','organizer_family_guidance_working_price')]
 s='''# Organizer approval queue — schedule not activated

| Urgency | Decision | Tradeoff / proposed action |
| --- | --- | --- |
| Critical | Free Kenrith, Najeela, Inalla, Derevi, Yuriko | Preserve authoritative zeros; explicitly accept residual optimized lines or revisit only by a new organizer decision. No pair surcharge. |
| Critical | Commander damage documentation conflict | Approve21 per individual head under detailedCR, or explicitly adopt team aggregation as a custom rule. |
| High | Admission cutoff77.5 and nonlinear curve | Policy sparsity compromise, no natural break or outcome calibration; approve complete list, not only threshold. |
| High | New shared-life and extra-team-turn engine prices | Review named exceptions, especially Hidetsugu8/12, Krrik8/12, Ad Nauseam15, Time Sieve8. |
| High | Provisional60/120/72,12transfer envelope | Controlled Season0 test only; does not screen every degenerate zero-price line. |
| High | Oracle/CR October freshness | Resolve rulebreaker support/Tolabow and wording conflict before strict release; no automatic new construction permissions. |
| Medium | Narrow approved numerical ranges | Working selections are legal within ranges but not independently singled-out approvals. |
| Medium | Chancellor5 versus ESG6/SSG5 and cheap support | Specialized opening acceleration tax needs real game validation. |
| Medium | Symmetric hate family1–2 | Preserve modest taxes; asymmetric lock effects reviewed separately. |

No broad combo/turn limit or experimental unban is activated. No approval is assumed from silence. Full pending location decisions follow.

'''
 s+=table(pending,['card_name','zone','working_price','authority','approved_range','reason'])+'\n\nManual review queue includes '+str(len(queue))+' identities, including low-confidence tail and boundary routes; it is a review burden, not proof of price correctness.\n'
 return s

def cutoff_report(sens,issues,dist,perturb,concentration,decisions):
 chosen=[r for r in sens if r['curve']=='nonlinear' and r['cohort']=='official_precons']
 s='''# Cutoff and numerical-curve comparison

Recommendation: **strict impact >77.5 in each location**, with the explicit exception ledger, nonlinear ceil(15*(max(0,s−tau)/25)^1.5). This is a policy choice to remove ordinary utility around75–77 while retaining most reviewed high-ceiling specialist80 floor entries. It is not an estimated natural break. At80 the inherited specialist floor itself falls free because comparison is strict>, exposing many specialized engine omissions. At70–72.5 ordinary fixing/utility receives costs. 75 still taxes ordinary interaction without exceptions. 77.5 is the highest tested threshold retaining a full two-point judgment-perturbation margin below the explicitly documented specialist floor80;79.5 is also tested but admits more membership flips under that perturbation; extra-turn/life converters are separately reviewed because inherited low ratings miss them at every tested threshold.

No impact value was modified to move a card across a boundary. The floor80 is inherited subjective admission policy, not measured ceiling; specialist_floor_control.csv removes it without fitting. Exact prices are policy choices and approved exceptions can reverse model ordering. Before/after boundary files show the same unedited impacts and20 nearest cards on each side per zone, cutoff and stage; changed price does not imply changed impact.

Four exception stages: curve_only (diagnostic, intentionally violates human anchors); organizer_only (explicit prices/ranges/minimum and zero qualitative anchors); calibrated_working (also previous assistant numbers and new working selections); recommended (also pending family/omission proposals). All stages use the same cohorts and frozen impact vectors. The organizer_only selected price within each range is a working implementation, not exact organizer approval. No coefficients were fitted to deck labels or reviewer rankings.

'''
 s+=table(chosen,['cutoff','exception_stage','pointed_main_cards','pointed_commander_options','pointed_identities','median','p90'])+'\n\n## Curve resolution at proposed threshold\n\n'
 comparison=[r for r in sens if r['cutoff']==RECOMMENDED_CUTOFF and r['exception_stage']=='recommended' and r['cohort']!='adversarial_fixture']
 s+=table(comparison,['curve','cohort','median','p10','p90','main_price_p50','main_price_p90','main_price_max'])
 s+='''

Existing tier bands are0/1/3/5/8/12 plus20 when the impact-minus-cutoff gap exceeds25. That20 band is unreachable at the recommended77.5 threshold but is reachable at70; it remains in the comparison. Fine integer is ceil(0.6*gap), maximum15 at cutoff75 or14 at77.5; nonlinear has same15-at100/75 anchor and finer low-tail progression, making strongest resources disproportionately costly. Explicit human working prices remain fixed across curves and cutoffs to isolate the rest of the list. A card barely above a cutoff costs at least one under all three: no statistical precision is implied by ceil. No per-deck rescaling.

Selected nonlinear price examples at tau77.5: frozen impact80→1;85→3;90→6;95→9;100→13. Demonic/Sol15 and other prices are explicit working/calibration exceptions, not secretly shifted impacts. Finer values are practical integers; coarse-tier jumps alone provide no validation. Pending15-point life engines can exceed global score-curve maximum13 deliberately.

## Named threshold counterexamples

'''
 s+=table([r for r in issues if r['cutoff']==RECOMMENDED_CUTOFF],['card_name','issue','curve_only_points','proposed_points','judgment'])
 s+='\n\n## Subjectivity sensitivity\n\n'
 for co in ['official_precons','bracket3_declared','cedh_holdout']:
  rr=[r for r in perturb if r['cohort']==co];vv=[r['median'] for r in rr];s+=f'{co}:100 independent ±2-impact scenarios, median deck score range {min(vv):g}–{max(vv):g}. '
 counts=[r['legal_pointed_identities'] for r in perturb];s+=f'Legal pointed-identity range {min(counts)}–{max(counts)} across those scenarios. These are sensitivity bounds from a chosen perturbation model, not confidence intervals. Overrides held fixed, so they mechanically reduce sensitivity.\n'
 s+='''

Card prices for ten largest non-explicit main prices are perturbed ±1 separately in premium_price_sensitivity.csv. This is a local numerical stress test, not an organizer-approved revision; approved bounds are not silently changed in the actual schedule. Exact all-pair budget comparisons in budget_stress_test.csv demonstrate both ordinary cohort overlap and residual low-cost competitive labels.

cutoff_color_concentration.csv reports color-identity counts at every cutoff and curve. This is actual identity distribution, not a requirement for equal color prices. Category/archetype labels in candidate metadata are nomination judgments; no reliable archetype win-rate cohort exists. Tribal/synergy lists may cost less intentionally, so no hidden archetype normalization is applied.

The source's423 low-confidence top1000 entries remain a material discovery gap. Reviewing all routing and functional nomination flags does not make those assessments independently sound. Current-card additions and all legal known identities outside the pool are exported for nomination; no rating is inferred from mere rarity or obscurity. Playtesting is needed before claiming complete exceptional-card capture.
'''
 return s

def budget_report(budget,teams):
 s='''# Season0 budget analysis

Propose testing **60 reference per player,120 combined,72 maximum per deck**, permitting transfer of up to12 unused partner points. Both team total and individual cap apply;72+48 fits,72+49 fails team total,73+47 fails individual/transfer. Independent fixed prices add across decks; no commander-pair or synergy premium. At reference60 the transfer20 envelope equals the72 cap; a further transfer term does not create extra budget.

This is a practical starting policy anchored to prior organizer preference and stress-tested constraints, not mathematically calibrated equal power. Exact counts below enumerate all unordered distinct archived list pairs, not observed teams; no actual coordinated2HG cohort was available. Illegal archive lists remain included for historical comparability and are flagged separately; they cannot be submitted legally merely because under cap.

'''
 s+=table([r for r in budget if r['reference']==60],['cohort','method','policy','all_distinct_pairs','admitted','admitted_fraction'])
 s+='\n\nAll '+str(len(teams))+' constructed team fixtures fit the120-point envelope: '+str(sum(t['budget_compliant_60_120_72'] for t in teams))+' admitted. Their padded cores do not measure optimized whole-deck cost. Strong free commanders and narrow low-priced enablers mean lowering the budget cannot reliably exclude the strongest interactive lines. Zero-cost double-Yuriko is a concrete counterexample.\n'
 s+='''

Budget alternatives40/80/48,50/100/60 and70/140/84 are included with equal allocations,20% transfer, and purely pooled caps. Pooled-only admits extreme concentration and removes the individual maximum; it is an experiment, not the recommendation. Allocation policy should reward teamwork but not accidentally allow120/0 when72 is intended. No blanket infinite-combo/turn-seven restriction is required or activated by this package. If actual league records reveal oppressive nonparticipation, return a narrowly evidenced rule proposal for organizer approval.
'''
 return s

def executive(schedule,changes,dist,teams,budget,decisions):
 n=len(schedule);m=int(sum(schedule.main_deck_points>0));c=int(sum(schedule.command_zone_points>0));new=changes[(changes.previous_points==0)&(changes.new_points>0)&changes.league_card_legal];free=changes[(changes.previous_points>0)&(changes.new_points==0)&changes.league_card_legal]
 s=f'''# Commander Doubles full-list recalibration — season0-proposed

**Recommendation: impact cutoff >{RECOMMENDED_CUTOFF}, nonlinear integer curve, {n} legal pointed identities ({m} main-deck prices, {c} command-zone options), with an explicit location/authority exception ledger.** This replaces the earlier321-identity proposal only if approved. It is not activated. The cutoff is a sparsity policy; no natural statistical break or win-probability calibration was demonstrated.

The coherent philosophy remains fixed additive prices with separate main/CZ alternatives and no synergy surcharge. Every9610 inherited candidate route, top1000 record and3510 command-zone candidates is reconsidered for price authority, legal identity, functional nomination and cutoff. That is not a claim of9610 new expert strength assessments. Original impact scores are immutable, all50 qualitative anchors preserved, all later explicit numerical corrections/ranges applied separately. The prior backend's tier→integer interval enforcement is removed because the organizer never approved those hard bands. Around97% of precon construction points and91% of cEDH-labelled points come from fixed calibration/family exceptions (exact shares in exception_dependence.csv), so changing a cutoff is not independent validation of the schedule.

## Cohort changes

'''
 s+=table([r for r in dist if r['cohort']!='adversarial_fixture'],['cohort','method','n','median','p10','p90','min','max','bootstrap_median_low','bootstrap_median_high'])
 s+='\n\nThese are construction costs, not measured power. DeclaredB3/cEDH event labels are imperfect; precons are historical products, not all currently legal or automatically Bracket2. Three known precon exceptions remain visible. No verified paired2HG outcome cohort supports strict balance claims. Bootstrap intervals describe resampling these lists, not price correctness.\n'
 s+=f'\n## Entry and exit\n\n{len(new)} location entries become pointed and {len(free)} become free, compared with the previous final-audit schedule. A card can leave main while stay pointed in CZ. Full lists carry reasons and approval categories.\n\n'
 s+=table(new.to_dict('records'),['card_name','zone','previous_points','new_points','authority'])+'\n\n'
 s+=table(free.to_dict('records'),['card_name','zone','previous_points','new_points','authority'])
 s+='\n\n## Ten consequential pricing decisions\n\n'
 names=['Necropotence','Ad Nauseam','Time Sieve','Heartless Hidetsugu','Final Fortune','Test of Endurance','Narset, Parter of Veils','Consecrated Sphinx',"Teferi's Protection",'Sorin Markov']
 rows=[]
 for name in names:
  r=schedule[schedule.card_name==name]
  if len(r):
   r=r.iloc[0];rows.append({'card':name,'old_main':int(r.previous_main_deck_points),'new_main':int(r.main_deck_points),'old_CZ':int(r.previous_command_zone_points),'new_CZ':int(r.command_zone_points),'authority':r.main_authority,'reason':r.main_reason})
 s+=table(rows,['card','old_main','new_main','old_CZ','new_CZ','authority','reason'])
 s+='''

Heavy taxes move to exceptional extra-team-turn and life converters. Ordinary removal is free through higher cutoff/proposals; symmetric hate generally1–2, and defensive Teferi3/Grace working4 remain below offensive engines. Last Chance/Warrior7 are explicit; Final Fortune7 is working above minimum6. Time Warp/Manipulation/Capture6 remain provisional. Necro15, Test7, premium wheels3 and Narset3 are working selections in approved ranges, not silently promoted exact approvals.

## Rules and functional-equivalent findings

805.8 makes extra turns/skip steps/team control material. Necro skips both heads' draw step; Expropriate two friendly time votes yield two team turns; Savor skips both untaps; Mindslaver controls whole opposing turn. Shared60 amplifies life engines but individual resources stay separate. Fixed exception prices dominate cohort totals (see exception_dependence.csv); apparent statistical separation does not independently validate those judgments. Sorin sets enemy pool10; Reservoir50 is not initial lethal. Hidetsugu/Fraying need survival asymmetry or can draw the game. Breena life comparison fails against equal opposing shared pool. Silence targets both opponents; Chant only one. Rift overload hits teammate permanents.

True premium equivalents reviewed: Time Warp/Manipulation/Capture6 and Final Fortune/Last Chance/Oath7 aligned; Ouphe/Null Rod/Stony2 aligned. ESG6/SSG5/Chancellor5 and Swords1 versus proposed free removal remain documented judgment differences. No model claim of measured one-point superiority. Spellbook-style split RIP/Helm works; split Bond/Blood, Oracle/Consultation, Kinnan/Basalt and Tivit/Sieve fail; copying/controller/rules prerequisites cached and checked separately.

## Residual low-point risks and budget

Kenrith/Najeela/Inalla/Derevi/Yuriko stay free in CZ under human anchors despite high access assessments. Double-Yuriko's demonstrated T3 stacked-Draco attack, Najeela supported combats (basic-only fixture corrected T5→T6 for GG/WUBRG feasibility), Chain/Apprentice, and Dualcaster/Twinflame remain cheap conditional cores. High prices on premium acceleration/tutors/protection buy consistency, but price alone does not remove every fast line. All21 constructed fixture teams are legal; exact points and prerequisites appear in adversarial_retest.md. No claim of consistent opening rates or optimized100-card construction.

Test **60 per-player reference /120 team /72 individual maximum, up to12 transfer** during recorded Season0. The budget has been stress-tested, not certified fair. No blanket infinite-combo or turn-seven ban is imposed. Official banned cards remain illegal; experimental prices confer no permission.

## Approval and readiness

Organizer approval required for cutoff/curve and complete schedule, all newly proposed numeric exceptions (especially Hidetsugu8 main/12CZ, Krrik8/12, Sieve8, Ad Nauseam15), selected values inside ranges, Season0 budget, and explicit acceptance/revisit of free competitive commanders. Resolve21 commander-damage CR-per-head versus format-page team wording and October rulebreaker freshness before strict league lock. Manual review of unreviewed tail/new cards and actual paired2HG game records remain essential. This is ready for organizer review and controlled testing, **not a locked official league system**.
'''
 return s

def readme():
 return '''# Full-list cutoff recalibration — season0-proposed

Read recalibration_executive_summary.md, then organizer_approval_queue.md. Earlier directories and branches are preserved. No schedule or new legality policy is activated.

From repository root, Python3.11+ with pandas,numpy,scipy,requests (existing requirements):

```sh
python -m pip install -r commander-doubles-cutoff-recalibration/requirements.txt
python commander-doubles-cutoff-recalibration/recalibrate.py
python commander-doubles-cutoff-recalibration/audit_tests.py
python commander-doubles-cutoff-recalibration/recalibrate.py --check
python commander-doubles-cutoff-recalibration/recalibrated_backend.py commander-doubles-cutoff-recalibration/adversarial_decklists/T09_A.txt --deck-b commander-doubles-cutoff-recalibration/adversarial_decklists/T09_B.txt --export team-report.json
```

Offline regeneration uses pinned current Oracle/rules, frozen prior9610 impacts, original50 anchors, organizer numerical ledger, reviewed exceptions and archived authorized TopDeck snapshots. No paid API or network calls for scoring. Entire original pool receives a price/evidence/functional-route reassessment; this is not a new expert score for every card. Known unpointed identities cost0; unknown names error, and known unrated identities get review flags. Main/CZ prices replace one another by location; partner prices sum. Banned legality is independent of hypothetical points. Commander pair/color/singleton/size checks remain; unsupported rulebreaker, companion and pregame-color permissions require manual review.

Edit review_inputs.py to change authoritative/working/proposed decisions or cutoff, then regenerate. Keep category/status and ranges accurate. Original impact scores must not be silently edited to force admission. Generated scoring_config.json contains effective fixed Oracle/location overrides and budget settings; temporary --config/--overrides experiments do not modify canonical review inputs. Explicit organizer prices/approved ranges/free anchors are validated. --export-overrides exports accepted config; --export exports complete submitted decks plus scores, and such exports can be imported again. Single-deck --individual-cap and team --team-cap/--individual-cap/--individual-reference/--transfer-fraction supported. No synergy adjustment or automatic combo certification.

To intentionally refresh online inputs:

```sh
python commander-doubles-cutoff-recalibration/refresh_sources.py
python commander-doubles-cutoff-recalibration/recalibrate.py
```

Refresh changes versioned inputs. Review all Oracle/legality changes, update dates/version/rules interpretation, and rerun tests before accepting refreshed artifacts. Original network source URLs, hashes and snapshot dates live in source_provenance.json and data/source_snapshot_manifest.json. Current CR text is compressed only as a small source snapshot for reproducible citation verification, with Wizards attribution; no invented data-license permission. Scryfall official bulk endpoint authorized download; card/Oracle text © Wizards, Scryfall API terms apply. Inherited external-cache licenses/notices and prior42-source inventory retained, no restricted new bulk scraping. Published cache ratings are not directly priced. No third-party evaluator output acquired in this sprint.

cutoff_sensitivity.csv:6cutoffs×3curves×4exceptionstages×4cohorts (includes79.5 to test near-floor fragility). cutoff_per_deck_scores.csv includes all nonlinear/stage/cutoff list totals. Boundaries list20 above/below with unchanged impact at each threshold and zone, before/after exceptions. Parameter coefficients are documented policy, not fitted outcome effects. Cohort labels and existing reviewer diagnostics are not true win-strength labels. Exact pair budget enumeration, fixed-seed bootstrap and subjective±2 sensitivity are distinct analyses. Specialist floor/no-floor and one-point premium sensitivity are exported separately. No verified paired2HG cohort or gameplay simulator was available.

The copied human_calibration_anchors.json preserves the earlier file verbatim; its historical proposed_points fields are not updated numerical decisions. Use calibration_precedence.json and recalibrated_point_schedule.csv for current effective prices.

All21 pair fixtures are legal100-card basic-padded illustrations, not optimized decklists; two are explicitly resource/turn counterexamples rather than wins. Rules cache covers conditional controller splits and false positives. Risk matches never establish game state or functionality. See unresolved commander-damage and October rulebreaker freshness in rules cache. No broad combo ban, turn limit, teammate surcharge or experimental unban is activated.
'''

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();outputs=generate()
 failures=[]
 for name,data in outputs.items():
  path=HERE/name
  if args.check:
   if not path.exists() or path.read_bytes()!=data:failures.append(name)
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 if failures:raise SystemExit('Non-reproducible artifacts: '+', '.join(failures))
 print(json.dumps({'generated_files':len(outputs),'reproduction_check':args.check,'status':'passed'}))
