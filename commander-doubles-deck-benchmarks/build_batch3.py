"""Generate Batch3 from immutable factual inputs. --check compares bytes without writing."""
import argparse,csv,gzip,hashlib,io,json,math,pathlib,re,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from pricing_batch3 import load,parse_inputs,VERSION,SOURCE_COMMIT
from pricing import BASE,ROOT,eligibility,oracle_text
from build_batch2 import canon,digest,csvtext,jt,table,colors
ORDER=['G1','G2','H1','H2','I1','I2']
EXPECTED=[49,71,69,51,54,66]
def read_inputs():
 p=HERE/'batch3'
 return {'raw':json.loads((p/'deck_inputs.json').read_text()),'content':json.loads((p/'review_content.json').read_text()),'foundations':json.loads((p/'research/foundations.json').read_text()),'checks':json.loads((p/'research/source_checks.json').read_text()),'overrides':list(csv.DictReader((p/'research/accepted_working_price_overrides_2026-10-21.csv').read_text().splitlines()))}
def full_snapshot(b):
 rows=[]
 for oid,c in sorted(b.index.cards.items(),key=lambda kv:(kv[1]['name'].casefold(),kv[0])):
  if c['legalities'].get('commander')!='legal' or c.get('digital') or 'paper' not in c.get('games',[]):continue
  e=eligibility(c)
  rows.append({'oracle_id':oid,'card_name':c['name'],'main_deck_points':b.card_price(oid,'main'),'command_zone_points':b.card_price(oid,'commanders') if e else '', 'command_zone_eligibility':e or ''})
 return rows
def generate(inputs):
 b,h=load(inputs['overrides']);raw=inputs['raw'];ds=parse_inputs(raw);reports={k:b.score(d) for k,d in ds.items()}
 assert [reports[k]['total'] for k in ORDER]==EXPECTED
 assert all(r['officially_legal'] for r in reports.values()),{k:r['legality_issues'] for k,r in reports.items()}
 tr={t:b.team(ds[t+'1'],ds[t+'2']) for t in 'GHI'}
 assert all(r['budget_compliant'] and r['total']==120 for r in tr.values())
 files={};snap=full_snapshot(b);files['price_snapshot.csv']=csvtext(snap);ph=digest(files['price_snapshot.csv'])
 prov=dict(inputs['checks'],version=VERSION,status='season0-proposed',source_commit=SOURCE_COMMIT,price_snapshot_sha256=ph,oracle_archive_sha256=digest((BASE/'data/oracle_current.jsonl.gz').read_bytes()),rules_archive_sha256=digest(gzip.open(BASE/'data/comprehensive_rules.gz','rb').read()),known_legal_identities=len(snap),inputs_sha256={k:digest(canon(v)) for k,v in inputs.items()},team_cap=120,individual_cap=72,reference_each=60,transfer_limit=12,synergy_surcharge=0)
 files['provenance.json']=jt(prov)
 files['effective_price_override_history.json']=jt(h[-len(inputs['overrides']):])
 files['scoring_config.json']=jt({'version':VERSION,'status':'season0-proposed','source_commit':SOURCE_COMMIT,'team_cap':120,'individual_cap':72,'reference_each':60,'transfer_fraction':.2,'cutoff':77.5,'cutoff_operator':'>','snapshot_sha256':ph,'unknown_policy':'error','synergy_surcharge':0,'adapter':'../pricing_batch3.py'})
 authority={(r['oracle_id'],r['zone']):r for r in b.precedence}
 ledger=[];profiles=[];legal=[];paid=[]
 for did in ORDER:
  d=ds[did];r=reports[did];norm={z:{b.index.resolve(n):q for n,q in v.items()} for z,v in d.items()}
  roles={b.index.resolve(re.sub(r'^\d+ ','',n)):role for role,ns in raw[did]['roles'].items() for n in ns.splitlines() if n.strip()}
  main=[b.index.cards[o] for o,q in norm['main'].items() for _ in range(q)]
  frontland=lambda c:'Land' in (c.get('card_faces') or [c])[0]['type_line']
  slots=sum(frontland(c) or (c.get('layout')=='modal_dfc' and 'Land' in c.get('type_line','')) for c in main)
  N=len(main);blue=sum('U' in colors(c) for c in main);force='Force of Will' in d['main']
  p={'deck_id':did,'title':raw[did]['title'],'main_cards':N,'commanders':'; '.join(raw[did]['commanders']),'physical_lands':sum(frontland(c) for c in main),'land_slots_with_mdfc':slots,'blue_pitch_cards':blue,'raw7_2to4_lands':round(sum(math.comb(slots,k)*math.comb(N-slots,7-k) for k in range(2,5))/math.comb(N,7),6),'force_support_given_force_raw7':round(1-math.comb(N-blue,6)/math.comb(N-1,6),6) if force else '', 'points':r['total'],'command_zone_points':r['command_zone_total']}
  profiles.append(p)
  files['decks/'+did+'.txt']='Commander\n'+''.join(str(q)+' '+b.index.cards[o]['name']+'\n' for o,q in norm['commanders'].items())+'\nDeck\n'+''.join(str(q)+' '+b.index.cards[o]['name']+'\n' for o,q in sorted(norm['main'].items(),key=lambda x:b.index.cards[x[0]]['name']))
  files['decks/'+did+'.json']=jt({'submitted_deck':norm,'metadata':dict(p,version=VERSION,status='season0-proposed',snapshot_sha256=ph,source_commit=SOURCE_COMMIT,source_ids=[s['id'] for s in inputs['foundations'] if s['head']==did])})
  files['reports/'+did+'.json']=jt(dict(r,price_snapshot_sha256=ph,automatic_combo_certification=False))
  ci=set().union(*(set(b.index.cards[o]['color_identity']) for o in norm['commanders']))
  banned=set(inputs['checks']['official_named_commander_bans'])
  legal.append({'deck_id':did,'total_cards':N+sum(norm['commanders'].values()),'main_cards':N,'commander_count':sum(norm['commanders'].values()),'official_legality_pass':r['officially_legal'],'singleton_pass':not any('singleton_limit' in s for s in r['legality_issues']),'color_identity_pass':all(set(b.index.cards[o]['color_identity'])<=ci for z in norm.values() for o in z),'named_bans_clear':not bool(set(n for z in d.values() for n in z)&banned),'unknowns':0,'points':r['total'],'individual_cap':72,'individual_pass':r['within_individual_cap'],'team_pass':tr[raw[did]['team']]['budget_compliant'],'status':'season0-proposed','issues':';'.join(r['legality_issues'])})
  for row in r['rows']:
   oid=row['oracle_id'];zone=row['zone'];e=eligibility(b.index.cards[oid]);a=authority.get((oid,zone),{})
   for copy in range(1,row['quantity']+1):
    ledger.append({'deck_id':did,'team':raw[did]['team'],'zone':zone,'oracle_id':oid,'card_name':row['card_name'],'copy_index':copy,'quantity':1,'points_each':row['points_each'],'total':row['points_each'],'main_deck_alternative':b.card_price(oid,'main'),'command_zone_alternative':b.card_price(oid,'commanders') if e else '','role':roles.get(oid,'command_zone'),'authority':a.get('authority','inherited_curve_proposal'),'snapshot_sha256':ph})
   if row['points_each']:paid.append({'deck_id':did,'card':row['card_name'],'zone':zone,'quantity':row['quantity'],'points_each':row['points_each'],'subtotal':row['total']})
 assert len(ledger)==600
 files['score_ledger.csv']=csvtext(ledger);files['legality_report.csv']=csvtext(legal);files['deck_profiles.csv']=csvtext(profiles)
 teams=[]
 for t,r in tr.items():
  teams.append({'team':t,'deck_a':t+'1','deck_b':t+'2','points_a':r['a']['total'],'points_b':r['b']['total'],'total':r['total'],'team_cap':120,'individual_cap':72,'reference_each':60,'transfer_limit':12,'points_transferred':r['points_transferred'],'transfer_to':t+'1' if r['a']['total']>60 else t+'2','budget_pass':r['budget_compliant'],'both_decks_legal':r['both_decks_legal'],'synergy_surcharge':0,'gameplay_legality_approved':False,'status':'season0-proposed'})
  files['reports/team_'+t+'.json']=jt(dict(r,price_snapshot_sha256=ph))
 files['teams.csv']=csvtext(teams)
 fs=inputs['foundations'];comparisons=[];changes=[];sources=[]
 for s in fs:
  did=s['head'];old={z:{b.index.resolve(n):q for n,q in v.items()} for z,v in s['deck'].items()};oldr=b.score(old);a=set(old['main']);ours={b.index.resolve(n) for n in ds[did]['main']}
  sources.append({k:s.get(k,'') for k in ['id','head','author','author_role','date','event_name','event_id','standing','field','record','url','player_id','source_path','source_sha256','captured_at','retrieval_date','source_hash_rechecked','source_type']})
  comparisons.append({'source_id':s['id'],'deck_id':did,'source_points_current_diagnostic':oldr['total'],'source_legal_current':oldr['officially_legal'],'source_issues':canon(oldr['legality_issues']),'new_points':reports[did]['total'],'retained_main_identities':len(a&ours),'removed':len(a-ours),'added':len(ours-a),'url':s['url']})
  for tag,ids in [('retained',a&ours),('removed',a-ours),('added',ours-a)]:
   for o in sorted(ids,key=lambda o:b.index.cards[o]['name']):changes.append({'source_id':s['id'],'deck_id':did,'change':tag,'oracle_id':o,'card_name':b.index.cards[o]['name'],'current_main_points':b.card_price(o,'main')})
 files['sources.csv']=csvtext(sources);files['source_comparison.csv']=csvtext(comparisons);files['source_card_changes.csv']=csvtext(changes);files['supplementary_sources.csv']=csvtext(inputs['content']['sources_supplementary'])
 cr=gzip.open(BASE/'data/comprehensive_rules.gz','rt').read();rr=[]
 for case in inputs['content']['rules']:
  x=dict(case);x['card_details']=[]
  for ref in x['rules']:assert re.search('^'+re.escape(ref)+'(?:[. ]|$)',cr,re.M),ref
  for n in x['cards']:
   oid=b.index.resolve(n);text=oracle_text(b.index.cards[oid]);x['card_details'].append({'oracle_id':oid,'name':b.index.cards[oid]['name'],'oracle_text':text,'oracle_text_sha256':digest(text)})
  x.update(verification_date='2026-10-21',rules_url=inputs['checks']['rules_url'],status='analyst_controller_review_conditional_not_automatic_proof')
  rr.append(x)
 files['rules_interactions.jsonl']=''.join(canon(x)+'\n' for x in rr)
 files['rules_interactions.md']='# Controller-aware conditional review\n\nCurrent linked CR2026-09-25 checked2026-10-21. Exact Oracle text/hash and rule IDs in JSONL. No automated gameplay certification.\n\n'+''.join('## '+r['id']+' — '+r['classification']+'\n\n'+r['state']+'\n\n'+r['operation']+'\n\nLimits: '+r['caution']+'\n\nCR '+', '.join(r['rules'])+'.\n\n' for r in rr)
 for name,text in inputs['content']['docs'].items():files[name]=text.rstrip()+'\n'
 files['archetype_lineage.md']+='\n## Exact source registrations\n\n'+table(sources,['id','author','date','standing','field','record','url'])+'\n## Repriced source diagnostics\n\n'+table(comparisons,['source_id','source_points_current_diagnostic','source_legal_current','new_points','retained_main_identities'])+'\nSource failures/overages are diagnostics; no source standing is assigned to a new2HG deck.\n'
 files['budget_tradeoffs.md']+='\n## Every charged card\n\n'+table(paid,['deck_id','card','zone','quantity','points_each','subtotal'])
 files['organizer_audio_review.md']='# Batch3 spoken review\n\n'+''.join('## Team '+t+'\n\n'+inputs['content']['audio'][t]+'\n\n' for t in 'GHI')+table(teams,['team','points_a','points_b','total','points_transferred'])+'\nAll season0-proposed; no rules/prices activated.\n'
 files['opening_examples.json']=jt(inputs['content']['openings'])
 files['deck_construction_profiles.md']='# Mana and pitch diagnostics\n\n'+table(profiles,['deck_id','physical_lands','land_slots_with_mdfc','blue_pitch_cards','force_support_given_force_raw7','raw7_2to4_lands','points'])+'\nHypergeometric raw7 only, not a mulligan or mana-sequencing simulation. Force support conditional on drawing Force=1-C(N-B,6)/C(N-1,6); B counts printed blue main cards including Force. Land count does not certify untapped colored sources; MDFC cannot be both land and spell simultaneously.\n'
 files['PRICE_SNAPSHOT.md']='# Frozen Batch3 effective prices\n\nVersion '+VERSION+'; source commit '+SOURCE_COMMIT+'. Complete known legal paper identities '+str(len(snap))+'. SHA256 '+ph+'. Sparse additive schedule; known unpointed cards explicitly zero; unknowns error. Zone alternative replaces main price.\n\nPrecedence: preserved recalibration -> seventeen Oct20 corrections -> Batch1/B2 working adapter -> frozen consolidated accepted_working_price_overrides_2026-10-21.csv. Exact vs range_working/CZ_working authority retained. KCI10 supersedes12; Reservoir8, Coffers9, Sheoldred MAIN7, Boseiju/Otawara6. Sheoldred CZ remains0 because the main correction is not a CZ instruction. No silent human-tier changes or pairing premiums. Existing snapshots remain intact.\n'
 # Correct descriptive README to match the complete CSV actually produced.
 files['README.md']=files['README.md'].replace('price_snapshot.csv is sparse: every known legal card with any nonzero actual-zone price is present. All other verified legal paper Oracle identities in the hashed archive are zero; unknown names remain errors.','price_snapshot.csv includes all31069 known legal paper Oracle identities, including explicit zeros; unknown names remain errors.').replace('emit_full_price_snapshot.py can export the full table when desired, avoiding a duplicated31069-row source artifact. ','')
 for path,text in list(files.items()):
  if path.endswith('.md'):files[path]=text.rstrip()+'\n'
 files['artifact_hashes.json']=jt({p:digest(s) for p,s in sorted(files.items())})
 return files
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();fs=generate(read_inputs());out=HERE/'batch3'
 if a.check:
  bad=[p for p,s in fs.items() if not (out/p).exists() or (out/p).read_bytes()!=s.encode()]
  if bad:raise SystemExit('Different/missing: '+', '.join(bad))
  print('All Batch3 generated artifacts reproduce byte-for-byte.')
 else:
  for p,s in fs.items():
   f=out/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(s.encode())
  print('Generated',len(fs),'Batch3 artifacts.')
if __name__=='__main__':main()
