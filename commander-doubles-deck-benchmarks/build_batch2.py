"""Generate Batch2 artifacts offline from frozen factual inputs; --check never writes."""
import argparse,collections,csv,gzip,hashlib,io,json,math,pathlib,re,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from pricing_batch2 import load,parse_inputs,VERSION,SOURCE_COMMIT
from pricing import BASE,ROOT,eligibility,oracle_text
def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def digest(s):return hashlib.sha256(s.encode() if isinstance(s,str) else s).hexdigest()
def csvtext(rows,fields=None):
 rows=list(rows);fields=fields or list(rows[0]);f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows);return f.getvalue()
def jt(v):return json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
def table(rows,fields):return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'')).replace('|','/') for k in fields)+' |\n' for r in rows)
def read_inputs():
 p=HERE/'batch2'
 return {'raw':json.loads((p/'deck_inputs.json').read_text()),'notes':json.loads((p/'research/calibration_documents.json').read_text()),'foundations':json.loads((p/'research/foundations.json').read_text()),'checks':json.loads((p/'research/source_checks.json').read_text()),'edits':json.loads((p/'research/construction_changes.json').read_text()),'content':json.loads((p/'review_content.json').read_text())}
def colors(card):
 c=(card.get('card_faces') or [card])[0]
 return set(c.get('colors',card.get('colors',[]))) or set(re.findall('[WUBRG]',c.get('mana_cost','')))
def generate(inputs):
 b,history=load(inputs['notes']);raw=inputs['raw'];decks=parse_inputs(raw);fs=inputs['foundations'];check=inputs['checks'];auth={(r['oracle_id'],r['zone']):r for r in b.precedence}
 reports={k:b.score(d) for k,d in decks.items()}
 assert [reports[k]['total'] for k in ('D1','D2','E1','E2','F1','F2')]==[72,48,56,64,57,63]
 assert all(r['officially_legal'] for r in reports.values()),{k:r['legality_issues'] for k,r in reports.items()}
 tr={t:b.team(decks[t+'1'],decks[t+'2']) for t in 'DEF'}
 assert all(r['budget_compliant'] and r['total']==120 for r in tr.values())
 files={};snap=[]
 for oid,c in sorted(b.index.cards.items(),key=lambda kv:(kv[1]['name'].casefold(),kv[0])):
  if c['legalities'].get('commander')!='legal' or c.get('digital') or 'paper' not in c.get('games',[]):continue
  e=eligibility(c)
  snap.append({'oracle_id':oid,'card_name':c['name'],'main_deck_points':b.card_price(oid,'main'),'command_zone_points':b.card_price(oid,'commanders') if e else '', 'command_zone_eligibility':e or ''})
 files['price_snapshot.csv']=csvtext(snap);price_sha=digest(files['price_snapshot.csv'])
 provenance=dict(check,scoring_version=VERSION,price_snapshot_sha256=price_sha,known_legal_identities=len(snap),oracle_archive_sha256=digest((BASE/'data/oracle_current.jsonl.gz').read_bytes()),pinned_rules_sha256=digest(gzip.open(BASE/'data/comprehensive_rules.gz','rb').read()),cutoff=77.5,cutoff_operator='>',team_cap=120,individual_cap=72,reference_each=60,transfer_limit=12,input_canonical_json_sha256={k:digest(canon(v)) for k,v in inputs.items()},authority_note='Explicit organizer decisions, ranges and provisional family selections remain separate; no activation.')
 files['provenance.json']=jt(provenance);files['price_override_history.json']=jt(history)
 files['effective_price_authority.json']=jt(sorted(auth.values(),key=lambda r:(r['card_name'],r['zone'])))
 files['scoring_config.json']=jt({'version':VERSION,'status':'season0-proposed_not_activated','source_commit':SOURCE_COMMIT,'team_cap':120,'individual_cap':72,'individual_reference':60,'transfer_fraction':.2,'global_cutoff':77.5,'curve':'inherited nonlinear plus explicit location overrides','pricing_adapter':'../pricing_batch2.py','calibration_documents':'research/calibration_documents.json','snapshot_sha256':price_sha,'unknown_policy':'error','synergy_surcharge':0})
 ledger=[];legal=[];profiles=[];review=[];paid=[]
 for did,d in decks.items():
  r=reports[did];desc=raw[did];norm={z:{b.index.resolve(n):q for n,q in v.items()} for z,v in d.items()}
  role={b.index.resolve(re.sub('^\\d+ ','',n)):cat for cat,ns in desc['roles'].items() for n in ns.splitlines() if n.strip()}
  frontland=lambda c:'Land' in (c.get('card_faces') or [c])[0]['type_line']
  land=lambda c:frontland(c) or (c.get('layout')=='modal_dfc' and 'Land' in c.get('type_line',''))
  maincards=[b.index.cards[o] for o,q in norm['main'].items() for _ in range(q)]
  lands=sum(frontland(c) for c in maincards);slots=sum(land(c) for c in maincards);blue=sum('U' in colors(c) for c in maincards);N=len(maincards)
  force=b.index.resolve('Force of Will') in norm['main']
  profile={'deck_id':did,'title':desc['title'],'main_cards':N,'commanders':'; '.join(desc['commanders']),'physical_lands':lands,'planned_land_slots_including_mdfc':slots,'blue_pitch_cards':blue,'force_raw7_other_blue_given_force':round(1-math.comb(N-blue,6)/math.comb(N-1,6),6) if force else '', 'raw7_2to4_land_slots':round(sum(math.comb(slots,k)*math.comb(N-slots,7-k) for k in range(2,5))/math.comb(N,7),6),'total_points':r['total'],'command_zone_points':r['command_zone_total']}
  profiles.append(profile)
  text='Commander\n'+''.join(str(q)+' '+b.index.cards[o]['name']+'\n' for o,q in norm['commanders'].items())+'\nDeck\n'+''.join(str(q)+' '+b.index.cards[o]['name']+'\n' for o,q in sorted(norm['main'].items(),key=lambda x:b.index.cards[x[0]]['name']))
  files['decks/'+did+'.txt']=text
  files['decks/'+did+'.json']=jt({'submitted_deck':norm,'metadata':dict(profile,version=VERSION,status='season0-proposed',price_snapshot_sha256=price_sha,source_commit=SOURCE_COMMIT,source_ids=[s['id'] for s in fs if s['head']==did],price_history='../price_override_history.json',actual_tournament_result_for_this_adaptation=None)})
  files['reports/'+did+'.json']=jt(dict(r,price_snapshot_sha256=price_sha,controller_review='rules_interactions.jsonl',automatic_combo_certification=False))
  ci=set().union(*(set(b.index.cards[o]['color_identity']) for o in norm['commanders']))
  banned=set(check['official_named_commander_bans'])
  legal.append({'deck_id':did,'cards':N+sum(norm['commanders'].values()),'main_cards':N,'command_zone_count':sum(norm['commanders'].values()),'points':r['total'],'command_zone_points':r['command_zone_total'],'official_legality_pass':r['officially_legal'],'singleton_pass':not any('singleton_limit' in e for e in r['legality_issues']),'color_identity_pass':all(set(b.index.cards[o]['color_identity'])<=ci for z in norm.values() for o in z),'official_named_bans_clear':not bool(set(n for z in d.values() for n in z)&banned),'unknown_cards':0,'individual_cap':72,'individual_budget_pass':r['within_individual_cap'],'team_budget_pass':tr[desc['team']]['budget_compliant'],'experimental_unbans':False,'status':'season0-proposed','issues':'; '.join(r['legality_issues'])})
  for row in r['rows']:
   oid=row['oracle_id'];zone=row['zone'];e=eligibility(b.index.cards[oid]);a=auth.get((oid,zone),{});base={k:v for k,v in row.items() if k not in ('quantity','total','price_authority')}
   for copy in range(1,row['quantity']+1):
    ledger.append(dict(deck_id=did,team=desc['team'],copy_index=copy,quantity=1,**base,total=row['points_each'],role=role.get(oid,'command_zone'),main_deck_alternative=b.card_price(oid,'main'),command_zone_alternative=b.card_price(oid,'commanders') if e else '',price_authority=a.get('authority','global_curve_proposal'),approved_range=canon(a.get('approved_range')),price_snapshot_sha256=price_sha))
   if row['points_each']>0:paid.append({'deck_id':did,'card':row['card_name'],'zone':zone,'quantity':row['quantity'],'points_each':row['points_each'],'subtotal':row['total']})
   card=b.index.cards[oid]
   if card.get('layout')=='modal_dfc' and not frontland(card) and 'Land' in card.get('type_line',''):
    review.append({'deck_id':did,'card_name':card['name'],'current_main_points':b.card_price(oid,'main'),'approval_issue':'Individual flexible MDFC review requested; baseline value is not an exact zero approval.','one_point_scenario_deck_points':r['total']+max(0,1-b.card_price(oid,'main')),'fallback':'Undying Malice (loses land flexibility)'})
 assert len(ledger)==600
 files['score_ledger.csv']=csvtext(ledger);files['legality_report.csv']=csvtext(legal);files['deck_profiles.csv']=csvtext(profiles)
 teams=[]
 for t,r in tr.items():
  teams.append({'team':t,'deck_a':t+'1','deck_b':t+'2','points_a':r['a']['total'],'points_b':r['b']['total'],'total':r['total'],'team_cap':120,'individual_cap':72,'reference_each':60,'transfer_limit':12,'points_transferred':r['points_transferred'],'transfer_to':t+'1' if r['a']['total']>60 else t+'2' if r['b']['total']>60 else 'none','budget_pass':r['budget_compliant'],'both_decks_legal':r['both_decks_legal'],'teammate_synergy_adjustment':0,'gameplay_legality_approved':False,'status':'season0-proposed'})
  files['reports/team_'+t+'.json']=jt(dict(r,price_snapshot_sha256=price_sha))
 files['teams.csv']=csvtext(teams);files['mdfc_review_queue.csv']=csvtext(review)
 sources=[];comparisons=[];changes=[]
 for s in fs:
  ds={z:{b.index.resolve(n):q for n,q in v.items()} for z,v in s['deck'].items()};sr=b.score(ds);did=s['head'];a=set(ds['main']);ours={b.index.resolve(n) for n in decks[did]['main']};kept=a&ours
  sources.append({k:s.get(k,'') for k in ['id','head','author','author_role','date','event_name','event_id','standing','field','record','url','player_id','source_sha256','captured_at','source_hash_rechecked','retrieval_date','source_type']})
  comparisons.append({'source_id':s['id'],'deck_id':did,'source_author':s['author'],'source_points_current_diagnostic':sr['total'],'source_legality_current':sr['officially_legal'],'source_issues':canon(sr['legality_issues']),'new_points':reports[did]['total'],'point_difference':sr['total']-reports[did]['total'],'retained_main_identities':len(kept),'removed_main_identities':len(a-ours),'added_main_identities':len(ours-a),'source_url':s['url']})
  for tag,ids in [('retained',kept),('removed',a-ours),('added',ours-a)]:
   for o in sorted(ids,key=lambda o:b.index.cards[o]['name']):changes.append({'source_id':s['id'],'deck_id':did,'change':tag,'oracle_id':o,'card_name':b.index.cards[o]['name'],'current_main_points':b.card_price(o,'main')})
 files['sources.csv']=csvtext(sources);files['source_comparison.csv']=csvtext(comparisons);files['source_card_changes.csv']=csvtext(changes)
 files['supplementary_sources.csv']=csvtext(inputs['content']['sources_supplementary'])
 files['construction_revision_log.csv']=csvtext(inputs['edits'])
 cr=gzip.open(BASE/'data/comprehensive_rules.gz','rt').read();rc=[]
 for cid,team,names,refs,status,state,op,caution in inputs['content']['rules']:
  for ref in refs:assert re.search('^'+re.escape(ref)+'(?:[. ]|$)',cr,re.M),ref
  rc.append({'id':cid,'team':team,'classification':status,'required_controllers_and_state':state,'operation':op,'limitations':caution,'rules':refs,'rules_url':check['rules_url'],'verification_date':'2026-10-21','status':'analyst_controller_checked_conditional_not_automatic_certification','cards':[{'oracle_id':b.index.resolve(n),'card_name':n,'oracle_text':oracle_text(b.index.cards[b.index.resolve(n)]),'oracle_text_sha256':digest(oracle_text(b.index.cards[b.index.resolve(n)]))} for n in names]})
 files['rules_interactions.jsonl']=''.join(canon(x)+'\n' for x in rc)
 files['rules_interactions.md']='# Conditional controller review\n\nCurrent linked Sept25 CR rechecked2026-10-21; exact references and Oracle hashes are in JSONL. No automated proof of combo execution or judge certification.\n\n'+''.join('## '+r['id']+' — '+r['classification']+'\n\n'+r['required_controllers_and_state']+'\n\n'+r['operation']+'\n\nCaution: '+r['limitations']+'\n\nCR '+', '.join(r['rules'])+'.\n\n' for r in rc)
 for name,text in inputs['content']['docs'].items():files[name]=text.rstrip()+'\n'
 files['archetype_lineage.md']+='\n## Exact registered sources\n\n'+table(sources,['id','author','date','standing','field','record','url'])+'\n## Source price/retention diagnostics\n\n'+table(comparisons,['source_id','source_points_current_diagnostic','source_legality_current','new_points','retained_main_identities'])+'\nIllegal/incomplete source totals are diagnostics, not accepted construction budgets. No original result is assigned to these new lists.\n'
 files['budget_tradeoffs.md']+='\n## Actual charged cards\n\n'+table(paid,['deck_id','card','zone','quantity','points_each','subtotal'])
 files['organizer_audio_review.md']='# Batch2 spoken team review\n\n'+''.join('## Team '+t+'\n\n'+inputs['content']['audio'][t]+'\n\n' for t in 'DEF')+table(teams,['team','points_a','points_b','total','points_transferred'])+'\nseason0-proposed. Stop before Batch3.\n'
 files['opening_examples.json']=jt(inputs['content']['openings'])
 files['deck_construction_profiles.md']='# Mana and raw-hand diagnostics\n\n'+table(profiles,['deck_id','physical_lands','planned_land_slots_including_mdfc','blue_pitch_cards','force_raw7_other_blue_given_force','raw7_2to4_land_slots','total_points'])+'\nExact hypergeometric raw seven-card composition only: no mulligans, source sequencing, decisions, draws, opponent simulation or wins. Force conditional support=1-C(N-B,6)/C(N-1,6), where B includes Force. Blue uses printed color, not land color identity. A spell/land MDFC cannot simultaneously be pitched and played as a land. Mana bases have actual conditional sources; these counts do not certify colors or untapped deployment.\n'
 files['PRICE_SNAPSHOT.md']='# Effective Batch2 working snapshot\n\nVersion '+VERSION+'; source commit '+SOURCE_COMMIT+'. Full known paper Commander-legal identity table: '+str(len(snap))+'. SHA256 '+price_sha+'. All known unpointed identities are explicit zeros; unknowns still error. Ineligible CZ values are blank; actual-zone prices replace rather than add.\n\nRead ordered calibration_documents, price_override_history and effective_price_authority. Historical50 tiers remain unchanged; later numeric decisions can differ. Boseiju/Otawara6 are working selections within5–6, not exact individual approvals. Lavinia main2/CZ1 scope and rainbow/multiplayer working selections are disclosed for organizer review. No blanket MDFC/channel-land tax. Main prices identical across printings.\n\nPinned Oracle Oct20; full Oct21 bulk refresh unavailable via web403. Current official named bans and current linked CR edition rereadOct21. No unbans or unsupported rulebreaker permissions. CSV per-row version/source repetition is omitted in favor of this hashed global manifest.\n'
 files['README.md']='# Commander Doubles Batch2 — season0-proposed\n\nRead organizer_audio_review.md first, then decks/, teams.csv, score_ledger.csv, team_synergy_and_counterplay.md and opening_hands_and_goldfish.md. Six complete independently legal100-card decks; no actual paired games or win rates claimed.\n\n'+table(teams,['team','deck_a','deck_b','points_a','points_b','total','points_transferred'])+'\n## Reproduce from repository root\n\nUse the existing Python environment/requirements. No paid API or network is needed.\n\n~~~sh\npython commander-doubles-deck-benchmarks/build_batch2.py\npython commander-doubles-deck-benchmarks/build_batch2.py --check\npython -m unittest discover -s commander-doubles-deck-benchmarks/tests -p test_batch2.py -v\npython commander-doubles-deck-benchmarks/score_batch2.py commander-doubles-deck-benchmarks/batch2/decks/D1.txt --deck-b commander-doubles-deck-benchmarks/batch2/decks/D2.json --summary\n~~~\n\nInputs: deck_inputs.json, review_content.json and research/ frozen facts/authorities. Build does not acquire new external data. --check compares generated bytes without writing. JSON decks wrap Oracle-keyed submitted_deck plus version/checksum metadata; text uses Commander/Deck sections. Editing a CSV is not a price override: revise the versioned adapter only after organizer decisions. Full card/location authority and checksums are supplied.\n\nSource reuse is limited to permitted existing factual event snapshots, attributed primary research and original analysis. No full source primers/images are redistributed. Public Moxfield shells were not passed off as read primers. Standings belong to ordinary Commander source lists, not these unplayed adaptations. No experimental unbans, price activation or combo surcharge. Earlier Batch1 artifacts are preserved. Batch3 awaits organizer review.\n\nThe original historical calculator remains intact; use score_batch2.py for these latest working prices. Local construction was read-only/in-memory; GitHub connector publication does not synchronize the local checkout.\n'
 for p,s in list(files.items()):
  if p.endswith('.md'):files[p]=s.rstrip()+'\n'
 files['artifact_hashes.json']=jt({p:digest(v) for p,v in sorted(files.items())})
 return files

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args();fs=generate(read_inputs());out=HERE/'batch2'
 if args.check:
  bad=[p for p,s in fs.items() if not (out/p).exists() or (out/p).read_bytes()!=s.encode()]
  if bad:raise SystemExit('Different or missing artifacts: '+', '.join(bad))
  print('All generated Batch2 artifacts reproduce byte-for-byte; no writes.')
 else:
  for p,s in fs.items():
   f=out/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(s.encode())
  print('Generated',len(fs),'Batch2 artifacts.')
if __name__=='__main__':main()
