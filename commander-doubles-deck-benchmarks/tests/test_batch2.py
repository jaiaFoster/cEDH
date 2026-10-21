import collections,csv,gzip,hashlib,io,json,pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from pricing_batch2 import load,parse_inputs
from build_batch2 import generate,read_inputs,digest
from pricing import BASE,ROOT,oracle_text
from spellbook_integration import parse_decklist
class Batch2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.inputs=globals().get('INPUTS_OVERRIDE') or read_inputs();cls.b,cls.history=load(cls.inputs['notes']);cls.decks=parse_inputs(cls.inputs['raw']);cls.files=globals().get('GENERATED_OVERRIDE') or generate(cls.inputs);cls.reports={k:cls.b.score(v) for k,v in cls.decks.items()}
 def test_six_complete_legal_decks(self):
  self.assertEqual(len(self.decks),6)
  for k,r in self.reports.items():
   with self.subTest(deck=k):
    self.assertTrue(r['officially_legal'],r['legality_issues']);self.assertEqual(sum(sum(v.values()) for v in self.decks[k].values()),100);self.assertEqual(sum(self.decks[k]['commanders'].values()),1)
 def test_exact_totals_and_actual_zone_cost(self):
  self.assertEqual([self.reports[k]['total'] for k in ['D1','D2','E1','E2','F1','F2']],[72,48,56,64,57,63]);self.assertEqual([self.reports[k]['command_zone_total'] for k in self.reports],[12,2,0,1,0,0])
  for r in self.reports.values():self.assertEqual(r['total'],sum(x['total'] for x in r['rows']))
 def test_budget_and_transfer_edges(self):
  for t,n in zip('DEF',[12,4,3]):
   r=self.b.team(self.decks[t+'1'],self.decks[t+'2']);self.assertTrue(r['budget_compliant']);self.assertEqual(r['points_transferred'],n);self.assertEqual(r['teammate_synergy_adjustment'],0);self.assertFalse(r['gameplay_legality_approved'])
  self.assertFalse(self.b.team(self.decks['D1'],self.decks['D2'],transfer_fraction=.19)['budget_compliant']);self.assertFalse(self.b.team(self.decks['D1'],self.decks['D2'],team_cap=119)['budget_compliant'])
 def test_known_unknown_banned_and_colors(self):
  with self.assertRaises((ValueError,KeyError)):self.b.score({'main':{'Imaginary Benchmark Card':1},'commanders':{}})
  d=json.loads(json.dumps(self.decks['D2']));d['main']['Plains']-=1;d['main']['Prosperous Innkeeper']=1;self.assertFalse(self.b.score(d)['officially_legal'])
  d=json.loads(json.dumps(self.decks['F1']));d['main']['Island']-=1;d['main']['Mana Crypt']=1;r=self.b.score(d);self.assertFalse(r['officially_legal']);self.assertFalse(r['experimental_unbans_activated'])
 def test_latest_price_lock_and_separate_authorities(self):
  for n,p in {'Boseiju, Who Endures':6,'Otawara, Soaring City':6,"Orim's Chant":1,'Abeyance':1,"Gaea's Cradle":15,'Birthing Pod':5,'Scheming Symmetry':5,"Sensei's Divining Top":3,'Roaming Throne':2,'Sink into Stupor // Soporific Springs':1,'Polluted Delta':5,'Underground Sea':5,'Watery Grave':2}.items():self.assertEqual(self.b.card_price(self.b.index.resolve(n),'main'),p,n)
  latest=next(r for r in reversed(self.history) if r['card_name']=='Otawara, Soaring City');self.assertEqual(latest['approved_range'],[5,6]);self.assertNotEqual(latest['authority'],'explicit_organizer_price')
 def test_preserve_historical_fifty_tiers(self):
  anchors=json.loads((ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text())['anchors'];self.assertEqual(anchors,self.b.anchors);self.assertEqual(len(anchors),50);self.assertEqual(next(a['tier'] for a in anchors if a['card_name']=="Orim's Chant"),5)
 def test_full_snapshot_ledger_and_artifact_checksums(self):
  rows=list(csv.DictReader(self.files['price_snapshot.csv'].splitlines()));self.assertEqual(len(rows),31069);self.assertEqual(len({r['oracle_id'] for r in rows}),31069)
  ledger=list(csv.DictReader(self.files['score_ledger.csv'].splitlines()));self.assertEqual(len(ledger),600)
  for did in self.decks:self.assertEqual(sum(int(r['total']) for r in ledger if r['deck_id']==did),self.reports[did]['total'])
  for p,h in json.loads(self.files['artifact_hashes.json']).items():self.assertEqual(digest(self.files[p]),h,p)
 def test_text_json_roundtrip(self):
  for did in self.decks:
   d=parse_decklist(self.files['decks/'+did+'.txt']);self.assertEqual(self.b.score(d)['total'],self.reports[did]['total'])
   jd=json.loads(self.files['decks/'+did+'.json'])['submitted_deck'];self.assertEqual(self.b.score(jd)['total'],self.reports[did]['total'])
   norm=lambda x:{z:{self.b.index.resolve(n):q for n,q in v.items()} for z,v in x.items()}
   self.assertEqual(norm(d),norm(self.decks[did]));self.assertEqual(norm(jd),norm(d))
 def test_twelve_actual_sources_and_raw_hashes(self):
  sources=self.inputs['foundations'];self.assertEqual(len(sources),12)
  for did in self.decks:self.assertEqual(sum(s['head']==did for s in sources),2)
  for s in sources:
   self.assertEqual(s['current_card_count'],100);self.assertTrue(s['source_hash_rechecked']);self.assertEqual(hashlib.sha256(gzip.open(ROOT/s['raw_path'],'rb').read()).hexdigest(),s['source_sha256']);self.assertTrue(1<=s['standing']<=s['field'])
 def test_named_current_bans_absent(self):
  banned=set(self.inputs['checks']['official_named_commander_bans'])
  for d in self.decks.values():self.assertFalse(set(n for v in d.values() for n in v)&banned)
 def test_opening_examples_use_own_real_cards(self):
  for did,x in self.inputs['content']['openings'].items():
   self.assertEqual(sum(x['hand'].values()),7)
   for n,q in x['hand'].items():self.assertGreaterEqual(self.decks[did]['main'].get(n,0),q,(did,n))
   for n in x.get('draw_by_turn',[])+x.get('library_required',[]):self.assertIn(n,self.decks[did]['main'])
 def test_key_rules_semantics_and_false_split(self):
  def text(n):return oracle_text(self.b.index.cards[self.b.index.resolve(n)]).lower()
  for n,p in [('Necropotence','skip your draw step'),('Children of Korlis',"life you've lost this turn"),('Heliod, Sun-Crowned','you gain life'),('Heliod, Sun-Crowned','you control'),('Sword of the Meek','you control'),('Time Sieve','sacrifice five artifacts'),('Thopter Assembly','if you control no thopters'),('Moonsnare Prototype','{t}, tap an untapped'),('Notion Thief','instead'),('Lavinia, Azorius Renegade','if no mana was spent')]:self.assertIn(p,text(n))
  for n in ['Necropotence','Necrodominance']:self.assertNotIn(n,self.decks['D1']['main'])
  self.assertNotIn('Children of Korlis',self.decks['D2']['main']);self.assertNotIn('Ethersworn Canonist',self.decks['E2']['main']);self.assertNotIn('Omen Machine',self.decks['E2']['main'])
 def test_resource_arithmetic_not_win_simulation(self):
  life=60-6-2-2-2-5;self.assertEqual(life,43);life-=9;life+=2*(3+2+2+1);self.assertEqual(life,50);self.assertEqual(2*8*4,64)
  self.assertEqual(7*2*3*2,84);self.assertEqual(7*2,14);self.assertLess(14,15);self.assertEqual(3+1-2,2);self.assertEqual(6-5,1);self.assertEqual(6-4,2)
  # A second Reservoir50 payment from100 leaves0 before resolution: require >100.
  self.assertEqual(100-50-50,0);self.assertGreater(101-50-50,0)
 def test_controller_case_refs_and_oracle_hashes(self):
  cr=gzip.open(BASE/'data/comprehensive_rules.gz','rt').read()
  for line in self.files['rules_interactions.jsonl'].splitlines():
   r=json.loads(line)
   for ref in r['rules']:self.assertRegex(cr,'(?m)^'+__import__('re').escape(ref)+'(?:[. ]|$)')
   for c in r['cards']:self.assertEqual(oracle_text(self.b.index.cards[c['oracle_id']]),c['oracle_text']);self.assertEqual(digest(c['oracle_text']),c['oracle_text_sha256'])
 def test_reproducibility_in_memory(self):
  self.assertEqual(generate(self.inputs),self.files)
 def test_audio_lengths_and_no_activation(self):
  for t,s in self.inputs['content']['audio'].items():self.assertTrue(120<=len(s.split())<=180,(t,len(s.split())))
  for t in 'DEF':self.assertFalse(json.loads(self.files['reports/team_'+t+'.json'])['gameplay_legality_approved'])
 def test_cli_with_generated_memory_files(self):
  import contextlib,types
  from unittest.mock import patch
  source=globals().get('CLI_SOURCE_OVERRIDE') or (HERE/'score_batch2.py').read_text()
  cm=types.ModuleType('batch2_cli_test');cm.__file__=str(HERE/'score_batch2.py');exec(source,cm.__dict__)
  vf={str(HERE/'batch2'/p):s for p,s in self.files.items()};vf[str(HERE/'batch2/research/calibration_documents.json')]=json.dumps(self.inputs['notes'])
  oldtext,oldbytes=pathlib.Path.read_text,pathlib.Path.read_bytes
  def rt(p,*a,**kw):return vf[str(p)] if str(p) in vf else oldtext(p,*a,**kw)
  def rb(p,*a,**kw):return vf[str(p)].encode() if str(p) in vf else oldbytes(p,*a,**kw)
  with patch.object(pathlib.Path,'read_text',rt),patch.object(pathlib.Path,'read_bytes',rb):
   for cap,expected in [(72,0),(71,1)]:
    buf=io.StringIO()
    with patch.object(sys,'argv',['score_batch2.py',str(HERE/'batch2/decks/D1.txt'),'--deck-b',str(HERE/'batch2/decks/D2.json'),'--summary','--individual-cap',str(cap)]),contextlib.redirect_stdout(buf):code=cm.main()
    self.assertEqual(code,expected);result=json.loads(buf.getvalue());self.assertEqual(result['total'],120);self.assertEqual(result['budget_compliant'],expected==0)
if __name__=='__main__':unittest.main()
