#!/usr/bin/env python3
"""Offline deterministic Batch1 build from frozen factual inputs. No network calls."""
import argparse,csv,collections,gzip,hashlib,json,pathlib,re,sys,tempfile
import numpy as np
from pricing import HERE,ROOT,BASE,load,eligibility,oracle_text
from deck_inputs import DECKS,REVISIONS
from interactions import CASES
from content import AUDIO,LINEAGE,SYNERGY,GOLDFISH,TRADEOFFS,PITCH_RISK

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def csvwrite(p,rows,fields=None):
 rows=list(rows);fields=fields or list(rows[0]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def jwrite(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
def mdtable(rows,fields):
 return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'' )).replace('|','/') for k in fields)+' |\n' for r in rows)
def deck_objects(b):
 return {did:{'commanders':{b.index.resolve(n):1 for n in d['commanders']},'main':{b.index.resolve(n):1 for ns in d['categories'].values() for n in ns}} for did,d in DECKS.items()}
def printed_colors(c):
 return set(c.get('colors',[])) or set((c.get('card_faces') or [{}])[0].get('colors',[])) or set(re.findall(r'[WUBRG]',(c.get('card_faces') or [c])[0].get('mana_cost','')))
def color_counts(b,deck):
 return {c:sum(c in printed_colors(b.index.cards[o]) for o in deck['main']) for c in 'WUBRG'}
def build(out):
 b,latest=load();checks=json.loads((HERE/'batch1/research/current_source_checks.json').read_text());foundations=json.loads((HERE/'batch1/research/foundations.json').read_text())
 out.mkdir(parents=True,exist_ok=True);decks=deck_objects(b);reports={k:b.score(d) for k,d in decks.items()};teamreports={t:b.team(decks[t+'1'],decks[t+'2']) for t in 'ABC'}
 assert [reports[k]['total'] for k in DECKS]==[72,48,55,65,60,60]
 assert all(r['officially_legal'] for r in reports.values())
 assert all(r['budget_compliant'] and r['total']==120 for r in teamreports.values())
 precedence={(r['oracle_id'],r['zone']):r for r in b.precedence}
 snapshot=[]
 for oid,c in sorted(b.index.cards.items(),key=lambda t:(t[1]['name'].casefold(),t[0])):
  if c['legalities'].get('commander')!='legal' or c.get('digital') or 'paper' not in c.get('games',[]):continue
  e=eligibility(c);row={'oracle_id':oid,'card_name':c['name'],'main_deck_points':b.card_price(oid,'main'),'command_zone_eligibility':e or '', 'command_zone_points':b.card_price(oid,'commanders') if e else '', 'commander_legality':c['legalities']['commander'],'color_identity':''.join(c['color_identity']),'known_identity':True,'main_price_authority':precedence.get((oid,'main'),{}).get('authority','global_curve_proposal'),'command_price_authority':precedence.get((oid,'commanders'),{}).get('authority','global_curve_proposal') if e else '', 'rating_status':'candidate_reviewed' if b.ratings.get(oid,{}).get('manually_assessed') else 'unreviewed_or_exception_see_provenance','scoring_version':b.config['version'],'source_commit':checks['source_commit']}
  snapshot.append(row)
 csvwrite(out/'price_snapshot.csv',snapshot);price_sha=sha(out/'price_snapshot.csv')
 jwrite(out/'scoring_config.json',b.audit_config);jwrite(out/'latest_organizer_overrides.json',latest)
 csvwrite(out/'construction_revision_log.csv',REVISIONS)
 from sequence_checks import OPENING_EXAMPLES,checked_arithmetic
 jwrite(out/'opening_examples.json',OPENING_EXAMPLES);jwrite(out/'sequence_resource_checks.json',checked_arithmetic())
 basecsv=BASE/'recalibrated_point_schedule.csv';baseframe=list(csv.DictReader(basecsv.read_text().splitlines()));basemap={r['oracle_id']:r for r in baseframe};history=[]
 for r in latest:
  oldcol='main_deck_points' if r['zone']=='main' else 'command_zone_points';old=basemap.get(r['oracle_id'],{}).get(oldcol,'0')
  history.append(dict(r,baseline_csv_price=old,interpretation='qualitative anchors retained separately; later exact-zone numerical decision takes precedence'))
 jwrite(out/'price_override_history.json',history)
 checks.update({'price_snapshot_sha256':price_sha,'version':b.config['version'],'status':'season0-proposed_not_activated','cutoff_operator':'>','impact_cutoff':77.5,'team_cap':120,'individual_reference':60,'individual_cap':72,'transfer_limit':12,'generation':'offline; frozen source facts; no new service scoring','baseline_schedule_sha256':sha(basecsv),'source_facts_sha256':sha(HERE/'batch1/research/foundations.json'),'fixed_random_seed':20261020,'seven_card_samples_per_deck':50000})
 jwrite(out/'provenance.json',checks)
 (out/'PRICE_SNAPSHOT.md').write_text(f'''# Frozen effective prices — season0-proposed

Source commit `{checks['source_commit']}`. Snapshot version `{b.config['version']}`. Baseline is the **strictly greater than77.5** recalibration candidate with its existing location exceptions, then the17 later exact-location numerical decisions. These decks do not activate those proposals as league rules.

`price_snapshot.csv`: **{len(snapshot):,} known paper Commander-legal Oracle identities**, including known unpointed zeros. SHA-256 `{price_sha}`. Snapshot excludes officially illegal cards, not their recognition in the underlying full Oracle database. Banned cards are still recognized and rejected by the backend. Ineligible commander prices are blank. Same-identity printings resolve to one Oracle ID. Eligible-partner categories do not imply every pair is valid.

Current Oracle version `{checks['oracle_updated_at']}`; current bulk metadata agrees with the pinned archive. Full archive SHA-256 `{checks['pinned_oracle_sha256']}`. Current rules landing still links the Sept25 text, hash `{checks['rules_sha256']}`; the prior October announcement/CR gap is retained. None of these lists uses the unsupported rulebreaker mechanic. `latest_organizer_overrides.json` and `price_override_history.json` preserve all17 decisions, old ledger numbers and actual baseline CSV numbers separately. The original50 qualitative tiers are unchanged in the source audit, including Chant tier5; its later **numeric3** supersedes its earlier numeric price. No new pricing exceptions were invented to fit these decks.

Prices charge the actual zone: main or command zone, never both. Partner prices each count once; independent decks may repeat cards across teammates. Known unreviewed zeros remain labeled unreviewed, not independently validated weak cards. Unknown names throw errors. Full scoring and conditional combo review use the original offline backend plus the explicit overlay in `pricing.py`. Each deck JSON includes this price checksum, pinned source commit and version. Team cap120, reference60, individual72, unused transfer at most12; no synergy surcharge. All outputs are proposals only.
''')
 ledger=[];legality=[];profiles=[]
 for did,d in DECKS.items():
  deck=decks[did];r=reports[did];cats={b.index.resolve(n):cat for cat,ns in d['categories'].items() for n in ns};cards=[b.index.cards[o] for o in deck['main']]
  physical=[c for c in cards if 'Land' in (c.get('card_faces') or [c])[0]['type_line']];slots=[c for c in cards if 'Land' in (c.get('card_faces') or [c])[0]['type_line'] or cats[c['oracle_id']]=='land_slots'];spells=[c for c in cards if c not in slots];colors=color_counts(b,deck)
  info={'deck_id':did,'team':d['team'],'title':d['title'],'commanders':'; '.join(d['commanders']),'card_count':sum(sum(x.values()) for x in deck.values()),'main_count':sum(deck['main'].values()),'main_points':r['total']-r['command_zone_total'],'command_zone_points':r['command_zone_total'],'total_points':r['total'],'pointed_main_cards':sum(x['zone']=='main' and x['points_each']>0 for x in r['rows']),'physical_land_cards':len(physical),'planned_land_slots_including_mdfc':len(slots),'blue_pitch_cards_in_main':colors['U'],'mean_mana_value_non_land_slots':round(float(np.mean([c['cmc'] for c in spells])),3),'non_land_slots_mv8plus':sum(c['cmc']>=8 for c in spells),'zero_price_main_cards':sum(x['zone']=='main' and x['points_each']==0 for x in r['rows'])}
  profiles.append(info)
  text='Commander\n'+''.join(f'1 {n}\n' for n in d['commanders'])+'\nDeck\n'+''.join(f'1 {n}\n' for n in sorted([b.index.cards[o]['name'] for o in deck['main']]))
  p=out/'decks';p.mkdir(exist_ok=True);(p/f'{did}.txt').write_text(text)
  metadata=dict(info,price_override_history_ref='../price_override_history.json',pricing_precedence_ref='../../pricing.py',price_snapshot_sha256=price_sha,scoring_version=b.config['version'],source_commit=checks['source_commit'],status='season0-proposed',origin='new unplayed 2HG adaptation; no tournament results assigned',source_ids=[x['id'] for x in foundations if x['head']==did])
  jwrite(p/f'{did}.json',{'submitted_deck':deck,'metadata':metadata});jwrite(out/'reports'/f'{did}.json',r)
  for row in r['rows']:
   oid=row['oracle_id'];card=b.index.cards[oid];e=eligibility(card)
   ledger.append(dict(deck_id=did,team=d['team'],role=cats.get(oid,'command_zone'),**row,main_deck_alternative=b.card_price(oid,'main'),command_zone_alternative=b.card_price(oid,'commanders') if e else '',commander_eligibility=e or '',commander_legality=card['legalities'].get('commander'),color_identity=''.join(card['color_identity']),price_snapshot_sha256=price_sha))
  counts=collections.Counter(b.index.cards[o]['name'] for zone in deck.values() for o,q in zone.items() for _ in range(q));ci=set().union(*(set(b.index.cards[o]['color_identity']) for o in deck['commanders']))
  legality.append({'deck_id':did,'cards':info['card_count'],'main_cards':info['main_count'],'commanders':len(deck['commanders']),'singleton_pass':all(v==1 for v in counts.values()),'commander_configuration_pass':r['officially_legal'],'color_identity_pass':all(set(b.index.cards[o]['color_identity'])<=ci for zone in deck.values() for o in zone),'color_identity':''.join(c for c in 'WUBRG' if c in ci),'official_bans_pass':all(b.index.cards[o]['legalities']['commander']=='legal' for zone in deck.values() for o in zone),'unknown_count':0,'oracle_snapshot_sha256':checks['pinned_oracle_sha256'],'price_snapshot_sha256':price_sha,'points':r['total'],'individual_cap':72,'individual_budget_pass':r['within_individual_cap'],'team_budget_pass':teamreports[d['team']]['budget_compliant'],'legality_issues':'; '.join(map(str,r['legality_issues'])),'unsupported_rulebreaker_or_companion':False,'status':'season0-proposed'})
 csvwrite(out/'score_ledger.csv',ledger);csvwrite(out/'legality_report.csv',legality);csvwrite(out/'deck_profiles.csv',profiles)
 teams=[]
 for t,r in teamreports.items():
  teams.append({'team':t,'deck_a':t+'1','deck_b':t+'2','points_a':r['a']['total'],'points_b':r['b']['total'],'total':r['total'],'team_cap':120,'reference_each':60,'individual_cap':72,'points_transferred':r['points_transferred'],'transfer_to':t+'1' if r['a']['total']>60 else t+'2' if r['b']['total']>60 else 'none','unused_team_points':120-r['total'],'no_synergy_surcharge':r['teammate_synergy_adjustment']==0,'budget_pass':r['budget_compliant'],'official_legality_pass':r['both_decks_legal'],'gameplay_approval':False,'status':'season0-proposed'})
  jwrite(out/'reports'/f'team_{t}.json',r)
 csvwrite(out/'teams.csv',teams)
 source_rows=[];source_comps=[];card_diffs=[]
 for x in foundations:
  did=x['head'];source_deck=x['deck'];ss={z:{b.index.resolve(n):int(q) for n,q in v.items()} for z,v in source_deck.items()};sr=b.score(ss);mainset=set(ss['main']);ourset=set(decks[did]['main']);kept=mainset&ourset
  source_rows.append({k:(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v) for k,v in x.items() if k!='deck'})
  source_comps.append({'source_id':x['id'],'deck_id':did,'source_type':x['source_type'],'source_author':x['author'],'source_date':x.get('event_date',x.get('updated_at','')),'source_standing':x.get('standing',''),'source_field':x.get('field_size',''),'source_cards':sum(sum(v.values()) for v in ss.values()),'source_current_points_diagnostic':sr['total'],'source_current_legality':sr['officially_legal'],'source_legality_issues':json.dumps(sr['legality_issues']), 'benchmark_points':reports[did]['total'],'source_minus_benchmark_points':sr['total']-reports[did]['total'],'kept_main_identities':len(kept),'removed_source_main_identities':len(mainset-ourset),'added_benchmark_main_identities':len(ourset-mainset),'overlap_fraction_of_source_main':round(len(kept)/len(mainset),4),'source_deck_url':x['decklist_url']})
  for state,oids in [('retained',kept),('removed',mainset-ourset),('added',ourset-mainset)]:
   for o in sorted(oids,key=lambda o:b.index.cards[o]['name']):card_diffs.append({'deck_id':did,'source_id':x['id'],'change':state,'oracle_id':o,'card_name':b.index.cards[o]['name'],'main_deck_points':b.card_price(o,'main'),'benchmark_role':next((cat for cat,ns in DECKS[did]['categories'].items() if b.index.cards[o]['name'] in ns),''),'note':'Exact comparison, not evidence the change increases measured win rate.'})
 fields=sorted(set().union(*(set(x) for x in source_rows)));csvwrite(out/'sources.csv',source_rows,fields);csvwrite(out/'source_comparison.csv',source_comps);csvwrite(out/'source_card_changes.csv',card_diffs)
 # Preserve exact Oracle plus references rather than copying long copyrighted rule text.
 cr=gzip.open(BASE/'data/comprehensive_rules.gz','rt').read();rulecache=[]
 for cid,t,names,refs,prereq,effect,limitation in CASES:
  for ref in refs:assert re.search(r'^'+re.escape(ref)+r'(?:[. ]|$)',cr,re.M),ref
  rulecache.append({'id':cid,'team':t,'cards':[{'oracle_id':b.index.resolve(n),'name':n,'oracle_text':oracle_text(b.index.cards[b.index.resolve(n)]),'oracle_text_sha256':hashlib.sha256(oracle_text(b.index.cards[b.index.resolve(n)]).encode()).hexdigest(),'url':'https://scryfall.com/search?q=oracleid%3A'+b.index.resolve(n)} for n in names],'comprehensive_rules':refs,'rules_url':checks['rules_url'],'rules_sha256':checks['rules_sha256'],'verification_date':'2026-10-20','required_state_and_controllers':prereq,'operation':effect,'limitations_and_false_positives':limitation,'status':'analyst_controller_checked_conditional_not_judge_certification','invalidated_by':'Oracle/rules/controller or prerequisite changes; recheck after source refresh'})
 (out/'rules_interactions.jsonl').write_text(''.join(json.dumps(x,sort_keys=True,ensure_ascii=False)+'\n' for x in rulecache))
 (out/'rules_interactions.md').write_text('# Conditional rules companion\n\nCurrent [official CR]('+checks['rules_url']+'); [rules landing](https://magic.wizards.com/en/rules). Verified2026-10-20 against the pinned current linked text and Oracle snapshot. 60 shared starting life follows Commander 2HG format; objects/resources remain individual. The prior unresolved Commander-damage editorial discrepancy is not resolved by these deck submissions; see the inherited official verification file. No quoted full CR text or independent judge certification is implied. Exact source texts/hashes and identities appear in JSONL.\n\n'+''.join(f"## {x['id']} — {', '.join(c['name'] for c in x['cards'])}\n\nRequired: {x['required_state_and_controllers']}\n\n{x['operation']}\n\nCaution: {x['limitations_and_false_positives']}\n\nCR {', '.join(x['comprehensive_rules'])}.\n\n" for x in rulecache))
 # Actual limited Monte Carlo diagnostics: independent raw seven-card hands, no mulligans/gameplay.
 opening=[];rng=np.random.default_rng(20261020);N=50000
 for did,d in decks.items():
  ids=list(d['main']);n=len(ids);chosen=np.argsort(rng.random((N,n)),axis=1)[:,:7];cats={b.index.resolve(n):cat for cat,ns in DECKS[did]['categories'].items() for n in ns}
  lands=np.array(['Land' in (b.index.cards[o].get('card_faces') or [b.index.cards[o]])[0]['type_line'] or cats[o]=='land_slots' for o in ids]);blue=np.array(['U' in printed_colors(b.index.cards[o]) for o in ids]);high=np.array([b.index.cards[o]['cmc']>=8 and not lands[i] for i,o in enumerate(ids)]);nl=lands[chosen].sum(1)
  force=b.index.resolve('Force of Will');hasforce=np.any(chosen==ids.index(force),axis=1) if force in ids else np.zeros(N,dtype=bool);blue_n=blue[chosen].sum(1)
  opening.append({'deck_id':did,'seed':20261020,'samples':N,'library_size':n,'planned_land_slots':int(lands.sum()),'blue_cards_in_library':int(blue.sum()),'raw_seven_2to4_land_slots_count':int(((nl>=2)&(nl<=4)).sum()),'raw_seven_2to4_land_slots_fraction':round(float(((nl>=2)&(nl<=4)).mean()),5),'raw_seven_high_mv8plus_count':int((high[chosen].sum(1)>0).sum()),'force_present_samples':int(hasforce.sum()),'force_and_another_blue_samples':int((hasforce&(blue_n>=2)).sum()),'force_support_fraction_given_force':round(float((blue_n[hasforce]>=2).mean()),5) if hasforce.any() else '', 'not_measured':'mulligans, colored-source feasibility, actual draws, play decisions, opponents, win probability or average turn'})
 csvwrite(out/'opening_hand_diagnostics.csv',opening)
 common=set(decks['C1']['main'])&set(decks['C2']['main']);cprofile=f"\nC1/C2 share {len(common)} of their99 main-deck identities; each has {99-len(common)} unique choices. Source MV is Oracle mana value (split cards summed, MDFC front face). The non-land-slot mean is a reveal/casting profile, not the expected value after top selection.\n"
 (out/'deck_construction_profiles.md').write_text('# Construction profiles\n\n'+mdtable(profiles,['deck_id','main_count','physical_land_cards','planned_land_slots_including_mdfc','blue_pitch_cards_in_main','mean_mana_value_non_land_slots','non_land_slots_mv8plus','pointed_main_cards','command_zone_points','total_points'])+cprofile+'\nPhysical land means front face is Land; planned land slots also include the explicit spell/land MDFCs. Otawara retained in a non-land role group still counts as a physical land. Counts include conditional lands and do not certify untapped mana or all required colors. Fetchlands need actual eligible targets; check colored costs when keeping hands. Blue pitch counts use printed color/mana cost, not color identity of lands; hybrid blue qualifies. A blue MDFC cannot both pay a pitch cost and be the same land drop.\n')
 (out/'archetype_lineage.md').write_text('# Archetype lineage and source limitations\n\nTwelve complete archived registrations, two per head, plus six public Moxfield lists were inspected. Ordinary Commander standings do not validate these new 2HG adaptations. Pilot names are not asserted original designers. `sources.csv` records exact event/date/standing/field/player locator, publication author and snapshot hashes. A TopDeck event registration URL plus the player locator identifies the list; no fabricated direct individual permalink is supplied. Public v3 Moxfield list metadata returned200; full primer prose was not obtained (loading page, tested primer endpoint404). These are inspected decklists and original analysis, not claims to have read inaccessible primers. Only factual card/count/author data is committed; raw Moxfield responses remain local and ignored.\n\n'+''.join('## '+did+' — '+DECKS[did]['title']+'\n\n'+LINEAGE[did]+'\n\n'+mdtable([r for r in source_comps if r['deck_id']==did],['source_id','source_author','source_date','source_standing','source_field','source_cards','source_current_points_diagnostic','source_current_legality','kept_main_identities','benchmark_points'])+'\n'+''.join(f"- [{x['id']}: {x.get('title',x.get('event_name','registration'))}]({x['decklist_url']}); {x['author']}; {x.get('event_date',x.get('updated_at',''))}.\n" for x in foundations if x['head']==did)+'\n' for did in DECKS)+'\nExact per-card retained/removed/added records are in `source_card_changes.csv`. Point totals for illegal or incomplete historical sources are diagnostic only, not accepted budget/legal benchmarks. Dawnwaker’s old public list and the explicitly OUTDATED tempo page remain labeled historical; the C2 public list is94cards. No fabricated completion or tournament result is assigned. All six submitted adaptations are independently complete100cards.\n')
 (out/'team_synergy_and_counterplay.md').write_text(SYNERGY)
 premium=[{'deck_id':x['deck_id'],'card':x['card_name'],'zone':x['zone'],'points':x['points_each']} for x in ledger if x['points_each']>0]
 (out/'budget_tradeoffs.md').write_text(TRADEOFFS+PITCH_RISK+'\n## Actual charged cards\n\n'+mdtable(premium,['deck_id','card','zone','points'])+'\n## Allocations\n\n'+mdtable(teams,['team','points_a','points_b','total','points_transferred','transfer_to','unused_team_points']))
 (out/'opening_hands_and_goldfish.md').write_text(GOLDFISH+'\n## Measured raw-hand diagnostics\n\nFixed NumPy seed20261020,50,000 independent random seven-card hands per deck, without replacement within a hand. No draws/mulligans/game outcomes are simulated. Generator takes the first seven indices of a random permutation obtained by independent continuous keys; each seven-card subset is uniform. Fractions are descriptive Monte Carlo diagnostics only. Conditional Force support counts any other blue printed card, not a claim it should be pitched or is still in hand at a later turn. Land slots include MDFCs and conditional lands. Full integer numerators and denominators are in CSV.\n\n'+mdtable(opening,['deck_id','samples','planned_land_slots','blue_cards_in_library','raw_seven_2to4_land_slots_fraction','force_support_fraction_given_force'])+'\nNo expected winning turn, win rate or matchup advantage was measured. Exact sequence feasibility above is conditional desk analysis.\n')
 (out/'organizer_audio_review.md').write_text('# Batch1 spoken review — season0-proposed\n\n'+''.join(f'## Team {t}\n\n{AUDIO[t]}\n\n' for t in 'ABC')+'## Quick comparison\n\n'+mdtable(teams,['team','points_a','points_b','total','points_transferred','budget_pass'])+'\nAll six decks are newly adapted and unplayed. Batch2 is paused for organizer review; no official league rules/prices are activated.\n')
 stress=[('A1','C1','Scheming Symmetry','Force of Will','A1 has Force plus another own blue card at Symmetry window','Counters search spell unless answered; no pooled pitch cards.'),('A1','C2','Doomsday','Aven Mindcensor','A1 can flash2W before search','Restricts search to top4, not an unconditional fail; graveyard selection may remain.'),('B2','A2',"Tormod's Crypt",'Haywire Mite','B2 has own G, Mite untapped activation not needed, no creature-ability suppression; Crypt on battlefield','Exile Crypt in response to bounce/cast-loop window; Ouphe alone would not stop loop.'),('C1','B2','Derevi, Empyrial Tactician','Chain of Vapor','C1 has own U before combat damage','Bounce connecting Derevi to deny its current combat untap; other self-sustaining B1 engines may remain.'),('A1','B2','Preston, the Vanisher','Dress Down','A1 holds1U and timing before new relevant ETBs','Removes creature abilities/ETB triggers temporarily; does not erase already-existing triggers.'),('B2','C1',"Yuriko, the Tiger's Shadow",'Drannith Magistrate','Drannith on battlefield','FAILS to prohibit commander ninjutsu; ability is not casting.'),('A2','B2','Kutzil, Malamet Exemplar','Boseiju, Who Endures','Boseiju in A2 hand with own mana','Boseiju cannot target ordinary Kutzil creature; use Otawara for that eligible target instead.'),('C2','C1','Cover of Darkness','Nanogene Conversion','C2 casts before blockers','FAILS assumed evasion: opposing creatures also become black Yuriko copies; cast after blockers with own Caller instead.')]
 srows=[]
 for a,t,threat,answer,prereq,result in stress:
  assert b.index.resolve(threat) in set(decks[t]['main'])|set(decks[t]['commanders'])
  assert b.index.resolve(answer) in set(decks[a]['main'])|set(decks[a]['commanders'])
  srows.append({'acting_deck':a,'target_deck':t,'threat_or_resource':threat,'response_or_probe':answer,'prerequisites':prereq,'conditional_result':result,'method':'desk_check_not_played_match','automatic_gameplay_certification':False})
 csvwrite(out/'stress_test.csv',srows)
 # Normalize authored Markdown EOF before hashing.
 for f in out.glob('*.md'):f.write_text(f.read_text().rstrip()+'\n')
 # This checksum catalog deliberately excludes itself.
 catalog={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ('artifact_hashes.json','source_candidate_registrations.json') and 'research' not in p.relative_to(out).parts}
 jwrite(out/'artifact_hashes.json',catalog)
 return {'teams':teams,'profiles':profiles,'price_rows':len(snapshot),'ledger_rows':len(ledger),'rules_cases':len(rulecache),'sources':len(foundations),'source_diagnostics':source_comps,'opening':opening}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
 if args.check:
  with tempfile.TemporaryDirectory() as td:
   build(pathlib.Path(td));diff=[]
   for f in pathlib.Path(td).rglob('*'):
    if f.is_file():
     dest=HERE/'batch1'/f.relative_to(td)
     if not dest.exists() or f.read_bytes()!=dest.read_bytes():diff.append(str(f.relative_to(td)))
   if diff:raise SystemExit('Non-reproducible or missing: '+', '.join(diff))
   print('All generated artifacts reproduce byte-for-byte.')
 else:
  result=build(HERE/'batch1');print(json.dumps({k:result[k] for k in ['teams','profiles','price_rows','ledger_rows','rules_cases','sources']},indent=2))
if __name__=='__main__':main()
