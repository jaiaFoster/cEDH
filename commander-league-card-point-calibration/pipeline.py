"""Run the cached-source cleaning, fixed scoring, statistics, audits and reports."""
from pathlib import Path
import json,gzip,re,collections,hashlib,math,copy
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from model import load_config,score
ROOT=Path(__file__).parent
RAW=ROOT/'data/raw'; CLEAN=ROOT/'data/clean';CLEAN.mkdir(exist_ok=True)
def norm(s):return re.sub(r'\s+',' ',s.replace('’',"'").replace('Æ','Ae').replace('æ','ae')).strip().casefold()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=lambda v:v.item() if isinstance(v,np.generic) else str(v)))
def csv(p,x):pd.DataFrame(x).to_csv(p,index=False)
def md(df):
 def fmt(v):return str(v).replace('|','/').replace('\n',' ')
 return '| '+' | '.join(df.columns)+' |\n|'+'|'.join(['---']*len(df.columns))+'|\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))
def oracle():
 p=RAW/'oracle_cards.jsonl.gz'
 return [json.loads(l) for l in gzip.open(p,'rt')] if p.exists() else json.loads((RAW/'oracle_cards.json').read_text())
def main():
 cfg=load_config();cards=oracle();byid={c['oracle_id']:c for c in cards if c.get('oracle_id')};names={}
 priority=lambda c:({'legal':0,'banned':1,'restricted':1}.get(c['legalities'].get('commander'),2),c.get('layout') in ['token','art_series','double_faced_token'],c['oracle_id'])
 ordered=sorted(byid.values(),key=priority)
 for c in ordered:names.setdefault(norm(c['name']),c['oracle_id'])
 for c in ordered:
  for n in [c['name'],c.get('flavor_name','')]+[f.get('name','') for f in c.get('card_faces',[])]+[f.get('flavor_name','') for f in c.get('card_faces',[])]:
   if n:names.setdefault(norm(n),c['oracle_id'])
 # Alias only exact face/name matches; do not fuzzy-resolve to a different card.
 taw=json.loads((ROOT/'data/taw/decks_v2.json').read_text());mtg=json.loads((RAW/'mtg_decklist.json').read_text())
 schema={k:{'present':sum(k in d for d in taw),'types':sorted(set(type(d[k]).__name__ for d in taw if k in d))} for k in sorted(set(k for d in taw for k in d))}
 schema['card_entry_schema']={k:sorted(set(type(c[k]).__name__ for d in taw for sec in ['cards','commander','sideboard','displayCommander','planarDeck','schemeDeck','tokens'] for c in d.get(sec,[]) if k in c)) for k in sorted(set(k for d in taw for sec in ['cards','commander','sideboard','displayCommander','planarDeck','schemeDeck','tokens'] for c in d.get(sec,[]) for k in c))}
 dump(CLEAN/'schema_audit.json',schema)
 paper=[d for d in taw if d['type']=='Commander Deck' and 'commander' in (d['format'] or '') and d['category']=='deck']
 mtgp=[d for d in mtg['data'] if d['type']=='Commander Deck']
 tk={(norm(d['name']),d['set_code'].lower()) for d in paper};mk={(norm(d['name']),d['code'].lower()) for d in mtgp}
 coverage={'taw_records':len(taw),'paper_records':len(paper),'mtgjson_paper_records':len(mtgp),'missing_from_taw':[list(k) for k in sorted(mk-tk)],'missing_from_mtgjson':[list(k) for k in sorted(tk-mk)],'mtgjson_meta':mtg['meta'],'dependency_note':'taw contains MTGJSON UUIDs; matching coverage is not independent verification of card-level truth.'}
 dump(CLEAN/'coverage_audit.json',coverage)
 excluded=[dict(name=d['name'],set_code=d['set_code'],release_date=d['release_date'],reason='Digital-only Commander product (analyzed separately only)' if d['type']=='MTGO Commander Deck' else 'Not a paper Commander Deck product',type=d['type']) for d in taw if d not in paper]
 seen={};decks=[];aliases=[];issues=[]
 for d in paper:
  counts=collections.Counter();unresolved=[];entries=[];flags=[]
  for section in ['cards','commander']:
   for a in d[section]:
    oid=names.get(norm(re.sub(r' \(Prepared\)$','',a['name'])));entries.append(dict(**a,section=section,oracle_id=oid))
    if oid:counts[oid]+=a['count']
    else:unresolved.append(a['name'])
  size=sum(a['count'] for a in entries)
  key=tuple(sorted((a['name'],a['count']) for a in entries)) # replace with aggregated canonical multiset below
  if not unresolved:key=tuple(sorted(counts.items()))
  if size!=100:flags.append('size_'+str(size))
  if unresolved:flags.append('unresolved:'+','.join(unresolved))
  for oid,n in counts.items():
   c=byid[oid]
   if n>1 and 'Basic' not in c['type_line'] and not re.search(r'deck can have (?:any number|up to)',c.get('oracle_text',''),re.I):flags.append('duplicate_nonbasic:'+c['name'])
  commanders=[a['oracle_id'] for a in entries if a['section']=='commander' and a['oracle_id']]
  ci=set().union(*(set(byid[o]['color_identity']) for o in commanders))
  for oid in counts:
   if not set(byid[oid]['color_identity'])<=ci:flags.append('color_identity:'+byid[oid]['name'])
  rec=dict(name=d['name'],product=d['set_name'],set_code=d['set_code'],release_date=d['release_date'],release_year=int(d['release_date'][:4]),source=d.get('source'),commander='; '.join(byid[o]['name'] for o in commanders),commander_ids=commanders,card_count=size,counts=dict(counts),entries=entries,expanded_cards=[a['oracle_id'] for a in entries for _ in range(a['count'])],quality_flags=flags,original=d)
  if key in seen:
   aliases.append(dict(name=d['name'],product=d['set_name'],release_date=d['release_date'],canonical_name=seen[key]['name'],canonical_date=seen[key]['release_date'],reason='Identical canonical 100-card multiset; printing/language not scored'))
   excluded.append(dict(name=d['name'],set_code=d['set_code'],release_date=d['release_date'],reason='Exact multiset duplicate / reprint / alternate edition',type=d['type']))
  else:seen[key]=rec;decks.append(rec)
  issues.append(dict(name=d['name'],product=d['set_name'],size=size,unresolved='; '.join(unresolved),flags='; '.join(flags)))
 dump(CLEAN/'precons.json',decks);csv(CLEAN/'excluded_records.csv',excluded);csv(CLEAN/'deck_aliases.csv',aliases);csv(CLEAN/'deck_quality_audit.csv',issues)
 if any('unresolved:' in f for d in decks for f in d['quality_flags']):
  print('UNRESOLVED',[(d['name'],d['quality_flags']) for d in decks if any('unresolved:' in f for f in d['quality_flags'])]);return
 scores={o:score(c,cfg) for o,c in byid.items()};csv('commander_card_scores.csv',list(scores.values()));dump(CLEAN/'game_changers.json',[c['name'] for c in byid.values() if c.get('game_changer')])
 official_soup=BeautifulSoup((RAW/'brackets_2025.html').read_text(),'html.parser');official_names=[s.strip() for s in official_soup.find('deck-list',attrs={'deck-title':'Game Changers – October 2025'}).find('main-deck').get_text().splitlines() if s.strip()]+['Farewell','Biorhythm']
 official_gc={names[norm(n)] for n in official_names};oracle_gc={o for o,c in byid.items() if c.get('game_changer')}
 dump(CLEAN/'game_changer_reconciliation.json',dict(official_names=official_names,official_count=len(official_gc),oracle_count=len(oracle_gc),official_only=sorted(official_gc-oracle_gc),oracle_only=sorted(oracle_gc-official_gc),method='October 2025 deck-list element plus two additions explicitly stated in February 2026 update.'))
 rows=[];detail=[]
 for d in decks:
  counts=d['counts']; gc=[scores[o]['card_name'] for o in counts if scores[o]['game_changer']];banned=[scores[o]['card_name'] for o in counts if scores[o]['legality']!='legal'];exception=d['set_code'] in ['m3c','sld','cmm','scd']
  group='quality_exception' if d['quality_flags'] else 'historical_nonlegal' if banned else 'starter' if d['set_code'] in ['scd','fdc'] else 'premium_exception' if exception else 'game_changer_exception' if gc else 'core_candidate_unverified'
  row={k:d[k] for k in ['name','product','set_code','release_date','release_year','source','commander','card_count']}
  row.update(total_points=sum(scores[o]['base_points']*n for o,n in counts.items()),initial_points=sum(score(byid[o],cfg,initial=True)['base_points']*n for o,n in counts.items()),high_impact_cards=sum(n for o,n in counts.items() if scores[o]['base_points']>=cfg['high_impact_threshold']),game_changers='; '.join(gc),game_changer_count=len(gc),current_nonlegal_cards='; '.join(banned),classification=group,quality_flags='; '.join(d['quality_flags']),land_points=sum(scores[o]['base_points']*n for o,n in counts.items() if 'Land' in byid[o]['type_line'].split(' // ')[0]),nonland_mean_mv=np.mean([byid[o]['cmc'] for o,n in counts.items() for _ in range(n) if 'Land' not in byid[o]['type_line'].split(' // ')[0]]),manually_reviewed_points=sum(scores[o]['base_points']*n for o,n in counts.items() if scores[o]['manually_reviewed']))
  for role in cfg['role_weights']:row[role+'_cards']=sum(n for o,n in counts.items() if scores[o][role+'_component']>0)
  rows.append(row)
  for o,n in counts.items():detail.append(dict(deck=d['name'],release_year=d['release_year'],oracle_id=o,card_name=scores[o]['card_name'],count=n,points_each=scores[o]['base_points'],points_total=n*scores[o]['base_points'],section='commander' if o in d['commander_ids'] else 'mainboard'))
 df=pd.DataFrame(rows);df['percentile']=df.total_points.rank(method='average',pct=True)*100;df=df.sort_values('total_points',ascending=False);df.to_csv('commander_precon_scores.csv',index=False);pd.DataFrame(detail).to_csv(CLEAN/'deck_card_points.csv',index=False)
 annual=[]
 for y,g in df.groupby('release_year'):
  a=g.total_points;annual.append(dict(year=y,count=len(g),mean=a.mean(),median=a.median(),std=a.std(ddof=1),iqr=a.quantile(.75)-a.quantile(.25),p5=a.quantile(.05),p10=a.quantile(.1),p25=a.quantile(.25),p75=a.quantile(.75),p90=a.quantile(.9),p95=a.quantile(.95),min=a.min(),max=a.max(),high_impact_mean=g.high_impact_cards.mean(),high_impact_median=g.high_impact_cards.median()))
 an=pd.DataFrame(annual).set_index('year').reindex(range(df.release_year.min(),df.release_year.max()+1)).reset_index();an['count']=an['count'].fillna(0).astype(int);an.to_csv(CLEAN/'annual_statistics.csv',index=False)
 rng=np.random.default_rng(cfg['seed'])
 def boot_median(a):return np.quantile(np.median(rng.choice(a,(5000,len(a))),axis=1),[.025,.975]).tolist()
 early=df[df.release_year<=2015];modern=df[df.release_year>=2024];a=early.total_points.to_numpy();b=modern.total_points.to_numpy()
 delta=np.median(rng.choice(b,(5000,len(b))),axis=1)-np.median(rng.choice(a,(5000,len(a))),axis=1)
 reg=stats.linregress(df.release_year,df.total_points)
 # Year-cluster bootstrap avoids treating decks from a shared release year as independent.
 yrs=sorted(df.release_year.unique());cluster=[]
 for _ in range(3000):
  sample=pd.concat([df[df.release_year==y] for y in rng.choice(yrs,len(yrs))]);cluster.append(stats.linregress(sample.release_year,sample.total_points).slope)
 metrics=dict(unique_precons=len(df),oracle_records=len(byid),years=[int(df.release_year.min()),int(df.release_year.max())],median=df.total_points.median(),median_ci=boot_median(df.total_points.to_numpy()),recent_year=int(df.release_year.max()),recent_n=int(sum(df.release_year==df.release_year.max())),recent_median=df[df.release_year==df.release_year.max()].total_points.median(),early_n=len(early),modern_n=len(modern),early_median=np.median(a),modern_median=np.median(b),difference=float(np.median(b)-np.median(a)),difference_ci=np.quantile(delta,[.025,.975]).tolist(),slope=reg.slope,slope_ci=np.quantile(cluster,[.025,.975]).tolist(),r_squared=reg.rvalue**2,high_impact_distribution=df.high_impact_cards.value_counts().sort_index().to_dict(),overall_percentiles={str(p):df.total_points.quantile(p) for p in [.05,.1,.25,.5,.75,.9,.95]},core_candidate_n=int(sum(df.classification=='core_candidate_unverified')),core_candidate_range=df[df.classification=='core_candidate_unverified'].total_points.quantile([.1,.9]).tolist(),land_share_median=(df.land_points/df.total_points).median())
 latest=df[df.release_date==df.release_date.max()];metrics.update(latest_release_date=df.release_date.max(),latest_release_n=len(latest),latest_release_median=float(latest.total_points.median()))
 # Independent assessment labels frozen from EDHREC before reading model scores. Not training data.
 holdout=[('Mutant Menace',1),('Animated Army',2),('Miracle Worker',3),('Creative Energy',4),('Death Toll',5),('Science!',6)]
 val=[]
 for n,r in holdout:
  z=df[df.name==n].iloc[0];val.append(dict(name=n,community_rank=r,model_points=int(z.total_points),source='https://cloudflare.edhrec.com/articles/the-best-commander-precons-of-2024',assessment='Author top-five ranking; Science! explicitly described as worst. Not win rates.'))
 v=pd.DataFrame(val);v['model_rank']=v.model_points.rank(ascending=False,method='average');v.to_csv(CLEAN/'validation.csv',index=False)
 rho=stats.spearmanr(-v.community_rank,v.model_points);concordant=sum((v.iloc[i].community_rank-v.iloc[j].community_rank)*(v.iloc[i].model_points-v.iloc[j].model_points)<0 for i in range(len(v)) for j in range(i))
 metrics.update(validation_spearman=float(rho.statistic),validation_p=float(rho.pvalue),validation_concordant=concordant,validation_pairs=15)
 # A second, explicitly anecdotal rank order from the Reddit original post; not pooled with EDHREC.
 redd=[]
 for r,n in enumerate(['Exit from Exile','Explorers of the Deep','Necron Dynasties','Cavalry Charge','Eldrazi Unbound'],1):
  z=df[df.name==n].iloc[0];redd.append(dict(name=n,author_rank=r,model_points=int(z.total_points),source='https://www.reddit.com/r/EDH/comments/1eetahl/redhs_best_precon_commanders_of_all_time/',retrieval='Search/browser text; direct HTTP snapshot was an access challenge, not article content.'))
 csv(CLEAN/'reddit_validation.csv',redd);metrics['reddit_spearman']=float(stats.spearmanr([-r['author_rank'] for r in redd],[r['model_points'] for r in redd]).statistic)
 sens=[]
 for param in list(cfg['role_weights'])+['game_changer_floor','basic_land','efficiency_decay','second_role_fraction']:
  for factor in [.75,1.25]:
   alt=copy.deepcopy(cfg)
   if param in cfg['role_weights']:alt['role_weights'][param]*=factor
   else:alt[param]*=factor
   ss={o:score(c,alt)['base_points'] for o,c in byid.items()};tot={d['name']:sum(ss[o]*n for o,n in d['counts'].items()) for d in decks};t=df.name.map(tot);r0=df.total_points.rank(ascending=False);r1=t.rank(ascending=False)
   sens.append(dict(parameter=param,factor=factor,median_score=float(t.median()),median_absolute_change=float(np.median(abs(t-df.total_points))),max_absolute_change=float(max(abs(t-df.total_points))),spearman=float(stats.spearmanr(df.total_points,t).statistic),max_rank_shift=float(max(abs(r0-r1)))))
 csv(CLEAN/'sensitivity.csv',sens)
 # Card-specific perturbation is exactly count times delta, no hidden team interaction.
 perturb=[]
 for n in ['Sol Ring','Arcane Signet','Farewell','Rhystic Study']:
  oid=names[norm(n)];changes=[10*d['counts'].get(oid,0) for d in decks];perturb.append(dict(card=n,point_delta=10,decks_affected=sum(x>0 for x in changes),max_deck_delta=max(changes),mean_deck_delta=np.mean(changes)))
 csv(CLEAN/'card_perturbations.csv',perturb)
 # Composition model is explanatory, not a causal power estimate.
 predictors=['release_year','nonland_mean_mv','game_changer_count','land_points'];X=np.column_stack([np.ones(len(df))]+[df[p].to_numpy()-df[p].mean() for p in predictors]);coef=np.linalg.lstsq(X,df.total_points,rcond=None)[0];csv(CLEAN/'composition_regression.csv',[dict(term=p,coefficient=float(c)) for p,c in zip(['intercept']+predictors,coef)])
 # Unban worksheet preserves official bans, and compares current Oracle legality with official text.
 from unbans import build_unbans
 ub=build_unbans(byid,scores,RAW);csv('experimental_unban_review.csv',ub)
 banned_ids={u['oracle_id'] for u in ub if u['official_status']=='banned'};oracle_banned={o for o,c in byid.items() if c['legalities'].get('commander')=='banned'}
 dump(CLEAN/'legality_reconciliation.json',dict(official_named_bans=len(banned_ids),oracle_banned_count=len(oracle_banned),oracle_only=[byid[o]['name'] for o in sorted(oracle_banned-banned_ids)],official_only=[byid[o]['name'] for o in sorted(banned_ids-oracle_banned)]))
 dump(CLEAN/'summary.json',metrics)
 # Preserve compact current card catalog sufficient for offline validation and scoring.
 catalog=[]
 for o,c in byid.items():
  s=scores[o];catalog.append(dict(id=o,n=c['name'],p=s['base_points'],legal=s['legality'],gc=s['game_changer'],reviewed=s['manually_reviewed'],ci=c['color_identity'],type=c['type_line'],text=s['oracle_text'],aliases=[n for n in [c.get('flavor_name','')]+[f.get('name','') for f in c.get('card_faces',[])]+[f.get('flavor_name','') for f in c.get('card_faces',[])] if n]))
 dump(CLEAN/'calculator_cards.json',catalog)
 fig,axs=plt.subplots(2,2,figsize=(15,10));fig.suptitle('Official Commander precons — fixed card-point model v0.2 (provisional)',fontsize=16)
 axs[0,0].hist(df.total_points,bins=22,color='#247c8c',edgecolor='white');axs[0,0].axvline(df.total_points.median(),color='#bb4e26',label=f'Median {df.total_points.median():.1f}');axs[0,0].legend();axs[0,0].set(xlabel='Deck points',ylabel='Unique precons')
 groups=[df[df.release_year==y].total_points for y in yrs];axs[0,1].boxplot(groups,tick_labels=yrs,showfliers=True);axs[0,1].tick_params(axis='x',rotation=60);axs[0,1].set(ylabel='Deck points',title='Release year is not a scoring feature')
 axs[1,0].plot(an.year,an['median'],'o-',label='Annual median');axs[1,0].fill_between(an.year,an.p10,an.p90,alpha=.2,label='10th–90th percentiles');axs[1,0].set(xlabel='Original release year',ylabel='Deck points');axs[1,0].legend()
 sc=axs[1,1].scatter(df.release_year,df.high_impact_cards,c=df.game_changer_count,cmap='viridis',alpha=.6);axs[1,1].set(xlabel='Original release year',ylabel='Cards costing ≥30',title='Color indicates Game Changer count');fig.colorbar(sc,ax=axs[1,1],label='Game Changers')
 fig.tight_layout();fig.savefig('precon_score_distributions.png',dpi=170);plt.close(fig)
 from report import write_report
 write_report(df,an,v,pd.DataFrame(sens),metrics,cfg,scores,decks,pd.DataFrame(detail),coverage)
 from calculator import build_html
 build_html(catalog,cfg,decks)
 print(json.dumps(metrics,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else float(x)))
if __name__=='__main__':main()
