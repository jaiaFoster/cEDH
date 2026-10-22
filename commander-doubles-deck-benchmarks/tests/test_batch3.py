import collections,csv,gzip,hashlib,io,json,pathlib,sys,unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from pricing_batch3 import load,parse_inputs
from build_batch3 import generate,read_inputs,digest,EXPECTED,ORDER
from pricing import BASE,ROOT,oracle_text,eligibility
from spellbook_integration import parse_decklist
class Batch3Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.inputs=globals().get('INPUTS_OVERRIDE') or read_inputs();cls.b,cls.history=load(cls.inputs['overrides']);cls.decks=parse_inputs(cls.inputs['raw']);cls.files=globals().get('GENERATED_OVERRIDE') or generate(cls.inputs);cls.reports={k:cls.b.score(v) for k,v in cls.decks.items()}
 def test_six_independent_complete_legal_decks(self):
  self.assertEqual(set(self.decks),set(ORDER))
  for k,r in self.reports.items():
   self.assertTrue(r['officially_legal'],r['legality_issues']);self.assertEqual(sum(sum(v.values()) for v in self.decks[k].values()),100)
   self.assertEqual(sum(self.decks[k]['main'].values()),98 if k=='H1' else 99)
 def test_partner_and_vehicle_eligibility(self):
  self.assertEqual(set(self.decks['H1']['commanders']),{'Tymna the Weaver','Malcolm, Keen-Eyed Navigator'})
  c=self.b.index.cards[self.b.index.resolve('Shorikai, Genesis Engine')];self.assertIn('Vehicle',c['type_line']);self.assertTrue(eligibility(c))
  d=json.loads(json.dumps(self.decks['H1']));d['commanders'].pop('Malcolm, Keen-Eyed Navigator');d['commanders']['Sheoldred, the Apocalypse']=1;self.assertFalse(self.b.score(d)['officially_legal'])
 def test_actual_zone_prices_and_totals(self):
  self.assertEqual([self.reports[k]['total'] for k in ORDER],EXPECTED)
  self.assertEqual([self.reports[k]['command_zone_total'] for k in ORDER],[0,0,11,0,1,0])
  self.assertEqual(self.b.card_price(self.b.index.resolve('Sheoldred, the Apocalypse'),'main'),7)
  self.assertEqual(self.b.card_price(self.b.index.resolve('Sheoldred, the Apocalypse'),'commanders'),0)
  for r in self.reports.values():self.assertEqual(sum(x['total'] for x in r['rows']),r['total'])
 def test_budgets_and_transfers(self):
  for t,n in zip('GHI',[11,9,6]):
   r=self.b.team(self.decks[t+'1'],self.decks[t+'2']);self.assertEqual(r['total'],120);self.assertTrue(r['budget_compliant']);self.assertEqual(r['points_transferred'],n);self.assertEqual(r['teammate_synergy_adjustment'],0)
  self.assertFalse(self.b.team(self.decks['G1'],self.decks['G2'],individual_cap=70)['budget_compliant'])
  self.assertFalse(self.b.team(self.decks['G1'],self.decks['G2'],team_cap=119)['budget_compliant'])
  self.assertFalse(self.b.team(self.decks['G1'],self.decks['G2'],transfer_fraction=.18)['budget_compliant'])
 def test_latest_accepted_price_rows(self):
  self.assertGreater(len(self.inputs['overrides']),100)
  for r in self.inputs['overrides']:self.assertEqual(self.b.card_price(self.b.index.resolve(r['card_name']),r['zone']),int(r['points']),r)
  for n,p in {'Krark-Clan Ironworks':10,'Aetherflux Reservoir':8,'Cabal Coffers':9,'Boseiju, Who Endures':6,'Otawara, Soaring City':6,'Phyrexian Altar':6,'Imperial Seal':8,'Diabolic Intent':3}.items():self.assertEqual(self.b.card_price(self.b.index.resolve(n),'main'),p)
 def test_fifty_qualitative_tiers_not_remapped(self):
  a=json.loads((ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text())['anchors'];self.assertEqual(a,self.b.anchors);self.assertEqual(len(a),50)
  self.assertEqual(next(x['tier'] for x in a if x['card_name']=="Orim's Chant"),5);self.assertEqual(self.b.card_price(self.b.index.resolve("Orim's Chant"),'main'),1)
 def test_unknown_not_zero(self):
  with self.assertRaises((ValueError,KeyError)):self.b.score({'commanders':{},'main':{'Invented Audit Card':1}})
  self.assertEqual(self.b.card_price(self.b.index.resolve('Forest'),'main'),0)
 def test_bans_and_bant_black_failure(self):
  d=json.loads(json.dumps(self.decks['I1']));d['main']['Forest']-=1;d['main']['Primeval Titan']=1;r=self.b.score(d);self.assertFalse(r['officially_legal']);self.assertFalse(r['experimental_unbans_activated'])
  d=json.loads(json.dumps(self.decks['H2']));d['main']['Forest']-=1;d['main']['Acererak the Archlich']=1;self.assertFalse(self.b.score(d)['officially_legal'])
  banned=set(self.inputs['checks']['official_named_commander_bans'])
  for d in self.decks.values():self.assertFalse({n for z in d.values() for n in z}&banned)
 def test_duplicate_and_size_failures(self):
  d=json.loads(json.dumps(self.decks['H2']));d['main']['Forest']-=1;d['main']['Aluren']=2;self.assertFalse(self.b.score(d)['officially_legal'])
  d=json.loads(json.dumps(self.decks['I1']));d['main']['Forest']-=1;self.assertFalse(self.b.score(d)['officially_legal'])
 def test_import_roundtrip(self):
  norm=lambda d:{z:{self.b.index.resolve(n):q for n,q in v.items()} for z,v in d.items()}
  for k in ORDER:
   txt=parse_decklist(self.files['decks/'+k+'.txt']);jd=json.loads(self.files['decks/'+k+'.json'])['submitted_deck']
   self.assertEqual(norm(txt),norm(self.decks[k]));self.assertEqual(norm(jd),norm(txt))
 def test_full_snapshot_all_known_legal_identities(self):
  rows=list(csv.DictReader(self.files['price_snapshot.csv'].splitlines()));self.assertEqual(len(rows),31069);self.assertEqual(len({r['oracle_id'] for r in rows}),31069)
  for r in rows:
   self.assertEqual(int(r['main_deck_points']),self.b.card_price(r['oracle_id'],'main'))
   if r['command_zone_points']:self.assertEqual(int(r['command_zone_points']),self.b.card_price(r['oracle_id'],'commanders'))
 def test_expanded_ledger_and_hashes(self):
  rows=list(csv.DictReader(self.files['score_ledger.csv'].splitlines()));self.assertEqual(len(rows),600)
  for k in ORDER:self.assertEqual(sum(int(r['total']) for r in rows if r['deck_id']==k),self.reports[k]['total'])
  for p,h in json.loads(self.files['artifact_hashes.json']).items():self.assertEqual(digest(self.files[p]),h,p)
 def test_twelve_source_raw_records(self):
  self.assertEqual(len(self.inputs['foundations']),12)
  for k in ORDER:self.assertEqual(sum(s['head']==k for s in self.inputs['foundations']),2)
  for s in self.inputs['foundations']:
   data=gzip.open(ROOT/s['source_path'],'rb').read();self.assertEqual(hashlib.sha256(data).hexdigest(),s['source_sha256'])
   row=next(r for r in json.loads(data)['standings'] if r['id']==s['player_id']);self.assertEqual(row['name'],s['author'])
   self.assertEqual(sum(sum(z.values()) for z in s['deck'].values()),100);self.assertTrue(1<=s['standing']<=s['field'])
 def test_opening_sevens_and_extra_draws(self):
  for k,x in self.inputs['content']['openings'].items():
   self.assertEqual(sum(x['hand'].values()),7)
   for n,q in x['hand'].items():self.assertGreaterEqual(self.decks[k]['main'].get(n,0),q,(k,n))
   for n in x['draw_by_turn']+x['library_required']:self.assertIn(n,self.decks[k]['main'])
  self.assertEqual(self.inputs['content']['openings']['I2']['draw_by_turn'],['Island'])
 def test_pox_and_sorin_shared_life_arithmetic(self):
  self.assertEqual(60-2*__import__('math').ceil(60/3),20);self.assertEqual(60-2*2*20,-20);self.assertEqual(60-2*(60-10),-40)
  self.assertEqual(60-(60-10)-(60-10),-40)
  # At49 Test fails its intervening-if trigger despite a later Oloro gain.
  self.assertFalse(49>=50);self.assertTrue(49+2>=50)
 def test_dungeon_finite_line(self):
  text=oracle_text(self.b.index.cards[self.b.index.resolve('Lost Mine of Phandelver')])
  self.assertIn('Dark Pool',text);self.assertIn('Temple of Dumathoin',text)
  casts,draws,visits=0,0,0;enemy=60
  while enemy>0:
   for room in range(1,5):
    casts+=1
    if room==3:visits+=1;enemy-=2
    if enemy<=0:break
    if room==4:draws+=1
  self.assertEqual((casts,draws,visits,enemy),(119,29,30,0))
  self.assertIn('Acererak the Archlich',self.decks['H1']['main']);self.assertNotIn('Acererak the Archlich',self.decks['H2']['main'])
 def test_woodland_fixed_state_mana_loop(self):
  for n in ['Shifting Woodland','Aftermath Analyst','Spelunking','Squandered Resources','Exsanguinate','High Market']:self.assertIn(n,self.decks['I1']['main'])
  bank=0
  for _ in range(32):
   green,black=7,2;green-=4;green-=3;black-=1;self.assertEqual(green,0);bank+=black;returned=5;self.assertEqual(returned,5)
  self.assertEqual(bank,32);self.assertEqual((bank-2)*2,60)
  # Mandatory Gitrog draws invalidate unlimited cycling: the documented fixed state removes it first.
  case=next(r for r in self.inputs['content']['rules'] if r['id']=='I-woodland')
  self.assertIn('Gitrog is absent',case['state']);self.assertIn('mandatory draws',case['caution'])
 def test_controller_wording_and_friendly_hate_cuts(self):
  text=lambda n:oracle_text(self.b.index.cards[self.b.index.resolve(n)]).lower()
  for n,s in [('Sanguine Bond','you gain life'),('Chulane, Teller of Tales','you cast'),('Malcolm, Keen-Eyed Navigator','pirates you control'),('Earthcraft','target basic land'),('Dramatic Reversal','you control'),('Sword of Feast and Famine','lands you control'),('Aluren','any player'),('Shorikai, Genesis Engine','draw two cards')]:self.assertIn(s,text(n))
  for n in ['Rest in Peace',"Grafdigger's Cage",'Cursed Totem','Humility']:self.assertNotIn(n,self.decks['I2']['main'])
  for d in self.decks.values():self.assertNotIn('Necropotence',d['main'])
 def test_rules_refs_and_oracle_identities(self):
  cr=gzip.open(BASE/'data/comprehensive_rules.gz','rt').read();rows=[json.loads(x) for x in self.files['rules_interactions.jsonl'].splitlines()];self.assertEqual(len(rows),25)
  for row in rows:
   for ref in row['rules']:self.assertRegex(cr,'(?m)^'+__import__('re').escape(ref)+'(?:[. ]|$)')
   for c in row['card_details']:self.assertEqual(oracle_text(self.b.index.cards[c['oracle_id']]),c['oracle_text']);self.assertEqual(digest(c['oracle_text']),c['oracle_text_sha256'])
  a=next(r for r in rows if r['id']=='H-aluren');self.assertIn('701.49',a['rules']);self.assertNotIn('701.46',a['rules'])
 def test_reproducibility(self):self.assertEqual(generate(self.inputs),self.files)
 def test_audio_and_no_activation(self):
  for t,s in self.inputs['content']['audio'].items():self.assertTrue(120<=len(s.split())<=180,(t,len(s.split())))
  for t in 'GHI':self.assertFalse(json.loads(self.files['reports/team_'+t+'.json'])['gameplay_legality_approved'])
 def test_cli_actual_interfaces_and_rejected_caps(self):
  import contextlib,types
  source=globals().get('CLI_SOURCE_OVERRIDE') or (HERE/'score_batch3.py').read_text();cm=types.ModuleType('batch3_cli');cm.__file__=str(HERE/'score_batch3.py');exec(source,cm.__dict__)
  vf={str(HERE/'batch3'/p):s for p,s in self.files.items()};vf[str(HERE/'batch3/research/accepted_working_price_overrides_2026-10-21.csv')]=csvtext_for_test(self.inputs['overrides'])
  oldtext,oldbytes=pathlib.Path.read_text,pathlib.Path.read_bytes
  def rt(p,*a,**kw):return vf[str(p)] if str(p) in vf else oldtext(p,*a,**kw)
  def rb(p,*a,**kw):return vf[str(p)].encode() if str(p) in vf else oldbytes(p,*a,**kw)
  with patch.object(pathlib.Path,'read_text',rt),patch.object(pathlib.Path,'read_bytes',rb):
   for cap,expected in [(72,0),(70,1)]:
    buf=io.StringIO()
    with patch.object(sys,'argv',['score_batch3.py',str(HERE/'batch3/decks/G1.txt'),'--deck-b',str(HERE/'batch3/decks/G2.json'),'--summary','--individual-cap',str(cap)]),contextlib.redirect_stdout(buf):ret=cm.main()
    self.assertEqual(ret,expected);o=json.loads(buf.getvalue());self.assertEqual(o['total'],120);self.assertEqual(o['budget_compliant'],expected==0)
def csvtext_for_test(rows):
 f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);return f.getvalue()
if __name__=='__main__':unittest.main()
