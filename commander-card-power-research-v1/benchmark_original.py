import json,sys,gzip,math,collections,warnings
import pandas as pd,numpy as np
from scipy import stats
warnings.filterwarnings('ignore',category=RuntimeWarning)
ext=json.loads(sys.argv[1])
cards={c['oracle_id']:c for c in (json.loads(l) for l in gzip.open('data/raw/oracle_cards.jsonl.gz','rt')) if c.get('oracle_id')}
decks=json.load(open('data/clean/precons.json'))
old=pd.read_csv('commander_precon_scores.csv').set_index('name')
oidlist=sorted({o for d in decks for o in d['counts']}); oi={o:i for i,o in enumerate(oidlist)}
X=np.zeros((len(decks),len(oidlist)))
for i,d in enumerate(decks):
 for o,n in d['counts'].items():X[i,oi[o]]=n
s=np.linalg.svd(X,compute_uv=False);rank=int(sum(s>max(X.shape)*s[0]*np.finfo(float).eps))
groups=collections.Counter(tuple(X[:,j].astype(int)) for j in range(X.shape[1]))
R=max(c.get('edhrec_rank') or 0 for c in cards.values())
creature={c['oracle_id']:c['points'] for c in ext['creature']}
xr=ext['xmage']; row=[]
def xm(c):
 lines=c.get('oracle_text','').splitlines()+[l for f in c.get('card_faces',[]) for l in f.get('oracle_text','').splitlines()]
 flags={}
 for rule in xr['rules']:
  flags[rule['flag']]=flags.get(rule['flag'],False) or any(any(all((needle in line.lower())==positive for needle,positive in clause) for clause in rule['or']) for line in lines)
 flags['xCost']='{X}' in c.get('mana_cost','') or any('{X}:' in l for l in lines)
 p=max([0]+[w for k,w in xr['weights'].items() if flags.get(k)])
 if 'Planeswalker' in c['type_line']:p=max(p,6)
 n=c['name'].split(' // ')[0].lower()
 for sp in xr['special']:
  if n in sp['names']:p=max(p,sp['weight'])
 if n in xr['special'][1]['names']:p+=18
 return p
weights={}
for o,c in cards.items():
 r=c.get('edhrec_rank')
 cp=ext['canlander'].get(c['name'],ext['canlander'].get(c['name'].split(' // ')[0],0))
 weights[o]=dict(baseline_v02=0,canlander=cp,official_gc=int(bool(c.get('game_changer'))),xmage_card_adapter=xm(c),adoption_log_proxy=math.log((R+1)/r) if r else None,expert_flag_votes=int(cp>0)+int(bool(c.get('game_changer'))),creature_published_partial=creature.get(o))
for d in decks:
 r={'deck':d['name'],'year':d['release_year']}
 for method in next(iter(weights.values())):
  if method=='baseline_v02':r[method]=int(old.loc[d['name'],'total_points']);continue
  known=sum(n for o,n in d['counts'].items() if weights[o][method] is not None)
  r[method]=sum(weights[o][method]*n for o,n in d['counts'].items() if weights[o][method] is not None)
  r[method+'_covered_cards']=known
 row.append(r)
df=pd.DataFrame(row).set_index('deck')
rng=np.random.default_rng(20261019)
def rankmetrics(names,y,method):
 p=df.loc[names,method].to_numpy();y=np.asarray(y);ii,jj=np.tril_indices(len(y),-1)
 mask=y[ii]!=y[jj];sg=np.sign(y[ii[mask]]-y[jj[mask]])*np.sign(p[ii[mask]]-p[jj[mask]])
 boots=[]
 for _ in range(1500):
  k=rng.integers(0,len(y),len(y))
  if len(set(y[k]))>1 and len(set(p[k]))>1:boots.append(float(stats.spearmanr(y[k],p[k]).statistic))
 return {'spearman':float(stats.spearmanr(y,p).statistic) if len(set(p))>1 else None,'kendall':float(stats.kendalltau(y,p).statistic) if len(set(p))>1 else None,'pairwise_accuracy':float(np.mean((sg>0)+.5*(sg==0))),'pairs':int(len(sg)),'spearman_bootstrap95':np.quantile(boots,[.025,.975]).tolist() if boots else None}
methods=list(next(iter(weights.values())))
ed=pd.read_csv('data/clean/validation.csv');red=pd.read_csv('data/clean/reddit_validation.csv')
metrics={}
for method in methods:
 metrics[method]={'edhrec6':rankmetrics(ed.name.tolist(),-ed.community_rank.to_numpy(),method),'reddit5':rankmetrics(red.name.tolist(),-red.author_rank.to_numpy(),method),'annual_median':{str(y):float(g[method].median()) for y,g in df.groupby('year')}}
 pairvals=[]
 for a,b in ext['pairs']:
  if a not in df.index or b not in df.index:raise Exception('unmatched pair '+a+' / '+b)
  delta=df.loc[a,method]-df.loc[b,method];pairvals.append({'stronger':a,'weaker':b,'difference':float(delta),'credit':float(delta>0)+.5*float(delta==0)})
 metrics[method]['new_year_matched_pairs']=pairvals;metrics[method]['new_pair_accuracy']=float(np.mean([p['credit'] for p in pairvals]))
 vals=[weights[o][method] for o in oidlist] if method!='baseline_v02' else [0]*len(oidlist)
 metrics[method]['unique_precon_cards_with_value']=sum(v is not None for v in vals)
 if method!='baseline_v02':metrics[method]['complete_decks']=int(sum(df[method+'_covered_cards']==100))
 metrics[method]['median_score']=float(df[method].median())
dfout=df.reset_index()
result={'n_decks':len(decks),'n_precon_oracle_cards':len(oidlist),'matrix_rank':rank,'nullity_lower_bound':len(oidlist)-rank,'cards_appearing_in_one_deck':int(sum((X>0).sum(0)==1)),'identical_column_groups_gt1':sum(n>1 for n in groups.values()),'cards_in_identical_column_groups':sum(n for n in groups.values() if n>1),'creature_published_rows':len(ext['creature']),'creature_unique_ids':len(creature),'methods':metrics,'difficult_cases':dfout[dfout.deck.isin(['Mutant Menace','Science!','Explorers of the Deep','Necron Dynasties','From Cute to Brute'])].to_dict('records'),'benchmark_rows':dfout.to_dict('records')}
print(json.dumps(result,allow_nan=False))
