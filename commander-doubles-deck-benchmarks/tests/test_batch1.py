import collections,csv,gzip,hashlib,json,pathlib,re,sys,tempfile,unittest
HERE=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from pricing import load,BASE,ROOT,eligibility,oracle_text
from deck_inputs import DECKS
from build_batch1 import deck_objects,sha
from audit_backend import load_deck
from sequence_checks import OPENING_EXAMPLES,checked_arithmetic
class Batch1(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b,cls.overrides=load();cls.d=deck_objects(cls.b);cls.reports={k:cls.b.score(d) for k,d in cls.d.items()};cls.folder=HERE/'batch1'
 def test_six_complete_legitimate_configurations(self):
  for did,d in self.d.items():
   with self.subTest(deck=did):
    r=self.reports[did];self.assertTrue(r['officially_legal'],r['legality_issues']);self.assertEqual(sum(sum(z.values()) for z in d.values()),100);self.assertEqual(len(d['commanders']),2 if did in ['A1','A2'] else 1)
    names=[self.b.index.cards[o]['name'] for zone in d.values() for o in zone];self.assertEqual(len(names),len(set(names)))
 def test_frozen_points_and_alternative_cz_pricing(self):
  self.assertEqual([self.reports[k]['total'] for k in DECKS],[72,48,55,65,60,60]);self.assertEqual([self.reports[k]['command_zone_total'] for k in DECKS],[11,10,0,0,0,0])
  for r in self.reports.values():self.assertEqual(r['total'],sum(x['points_each']*x['quantity'] for x in r['rows']))
 def test_team_transfers_and_no_synergy_surtax(self):
  for t,transfer in zip('ABC',[12,5,0]):
   r=self.b.team(self.d[t+'1'],self.d[t+'2']);self.assertEqual(r['total'],120);self.assertEqual(r['points_transferred'],transfer);self.assertTrue(r['budget_compliant']);self.assertEqual(r['teammate_synergy_adjustment'],0);self.assertFalse(r['gameplay_legality_approved'])
  self.assertFalse(self.b.team(self.d['A1'],self.d['A2'],transfer_fraction=.19)['budget_compliant']);self.assertFalse(self.b.team(self.d['A1'],self.d['A2'],team_cap=119)['budget_compliant']);self.assertFalse(self.b.team(self.d['A1'],self.d['A2'],individual_cap=71)['budget_compliant'])
 def test_all_seventeen_latest_overrides(self):
  self.assertEqual(len(self.overrides),17)
  for r in self.overrides:self.assertEqual(self.b.card_price(r['oracle_id'],r['zone']),r['working_price'],r['card_name'])
  self.assertEqual(self.b.card_price(self.b.index.resolve("Orim's Chant"),'main'),3)
 def test_all_fifty_qualitative_anchors_retained_distinct(self):
  self.assertEqual(len(self.b.anchors),50);original=json.loads((ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text())['anchors'];self.assertEqual(self.b.anchors,original)
  for a in self.b.anchors:
   if a['tier']==0:self.assertEqual(self.b.card_price(self.b.index.resolve(a['card_name']),a['zone']),0)
  self.assertEqual(next(a['tier'] for a in self.b.anchors if a['card_name']=="Orim's Chant"),5)
 def test_all_explicit_organizer_decisions_and_ranges(self):
  for r in self.b.precedence:
   p=self.b.card_price(r['oracle_id'],r['zone'])
   if r['authority']=='explicit_organizer_price':self.assertEqual(p,r['working_price'])
   if r.get('approved_range'):
    lo,hi=r['approved_range']
    if lo is not None:self.assertGreaterEqual(p,lo)
    if hi is not None:self.assertLessEqual(p,hi)
 def test_import_export_round_trip_all_six(self):
  for did in DECKS:
   for suffix in ['txt','json']:
    imported=load_deck(self.folder/'decks'/f'{did}.{suffix}');normalized={z:{self.b.index.resolve(n):q for n,q in v.items()} for z,v in imported.items()};self.assertEqual(normalized,self.d[did]);self.assertEqual(self.b.score(imported)['total'],self.reports[did]['total'])
 def test_unknown_error_not_zero_and_banned_detection(self):
  with self.assertRaises((ValueError,KeyError)):self.b.score({'main':{'Imaginary League Test Card':1},'commanders':{"Yuriko, the Tiger's Shadow":1}})
  bad=json.loads(json.dumps(self.d['B2']));del bad['main'][self.b.index.resolve('Forest')];bad['main'][self.b.index.resolve('Primeval Titan')]=1;r=self.b.score(bad);self.assertFalse(r['officially_legal']);self.assertTrue(any(x['experimental_banned'] for x in r['rows']));self.assertFalse(r['experimental_unbans_activated'])
 def test_color_singleton_and_commander_failures(self):
  for name in ['Mystic Retrieval','Forest']:
   d=json.loads(json.dumps(self.d['C2']));del d['main'][self.b.index.resolve('Ponder')];d['main'][self.b.index.resolve(name)]=1;self.assertFalse(self.b.score(d)['officially_legal'])
  d=json.loads(json.dumps(self.d['C1']));d['main'][self.b.index.resolve('Ponder')]=2;self.assertFalse(self.b.score(d)['officially_legal'])
  d=json.loads(json.dumps(self.d['A1']));d['commanders']={self.b.index.resolve('Tymna the Weaver'):1,self.b.index.resolve('Najeela, the Blade-Blossom'):1};self.assertFalse(self.b.score(d)['officially_legal'])
 def test_source_minimum_coverage_and_honest_limitations(self):
  fs=json.loads((self.folder/'research/foundations.json').read_text());self.assertEqual(len(fs),18)
  for did in DECKS:
   rows=[x for x in fs if x['head']==did and x['source_type']=='registered_tournament_deck'];self.assertEqual(len(rows),2)
   for x in rows:self.assertEqual(sum(sum(v.values()) for v in x['deck'].values()),100);self.assertTrue(1<=x['standing']<=x['field_size']);self.assertIn('registered pilot',x['author_role'])
  m=next(x for x in fs if x['id']=='C2_M1');self.assertEqual(sum(sum(z.values()) for z in m['deck'].values()),94)
  self.assertIn('OUTDATED',next(x for x in fs if x['id']=='C1_M1')['title'])
 def test_ledger_and_full_legal_zero_database(self):
  ledger=list(csv.DictReader((self.folder/'score_ledger.csv').read_text().splitlines()));self.assertEqual(len(ledger),600)
  self.assertEqual(sum(int(x['quantity']) for x in ledger),600)
  for did in DECKS:self.assertEqual(sum(int(x['total']) for x in ledger if x['deck_id']==did),self.reports[did]['total'])
  snapshot=list(csv.DictReader((self.folder/'price_snapshot.csv').read_text().splitlines()));self.assertEqual(len(snapshot),31069);self.assertEqual(len({x['oracle_id'] for x in snapshot}),len(snapshot))
  self.assertEqual(next(x['main_deck_points'] for x in snapshot if x['card_name']=='Island'),'0')
 def test_oracle_and_snapshot_hashes(self):
  p=json.loads((self.folder/'provenance.json').read_text());self.assertEqual(sha(BASE/'data/oracle_current.jsonl.gz'),p['pinned_oracle_sha256']);self.assertEqual(sha(self.folder/'price_snapshot.csv'),p['price_snapshot_sha256']);self.assertEqual(hashlib.sha256(gzip.open(BASE/'data/comprehensive_rules.gz','rb').read()).hexdigest(),p['rules_sha256'])
 def test_rules_source_identity_and_references(self):
  records=[json.loads(l) for l in (self.folder/'rules_interactions.jsonl').read_text().splitlines()];self.assertEqual(len(records),22);cr=gzip.open(BASE/'data/comprehensive_rules.gz','rt').read()
  for x in records:
   for ref in x['comprehensive_rules']:self.assertRegex(cr,r'(?m)^'+re.escape(ref)+r'(?:[. ]|$)')
   for c in x['cards']:self.assertEqual(oracle_text(self.b.index.cards[c['oracle_id']]),c['oracle_text']);self.assertEqual(hashlib.sha256(c['oracle_text'].encode()).hexdigest(),c['oracle_text_sha256'])
 def test_sensitive_controller_oracle_facts(self):
  def text(n):return oracle_text(self.b.index.cards[self.b.index.resolve(n)])
  for name,phrase in [('Bruse Tarl, Boorish Herder','target creature you control'),('Nanogene Conversion','target creature you control'),('Nanogene Conversion',"Each other creature"),('Scheming Symmetry','Choose two target players'),('Derevi, Empyrial Tactician','target permanent'),('Cursed Totem','Activated abilities of creatures'),('Yuriko, the Tiger\'s Shadow','put that card into your hand'),('Roaming Throne','another creature you control'),('Preston, the Vanisher',"if it wasn't cast"),('Valley Floodcaller','Whenever you cast a noncreature spell')]:self.assertIn(phrase.lower(),text(name).lower())
  self.assertNotIn('activate only as a sorcery',text('Walking Ballista').lower());self.assertNotIn('draw a card',text("Yuriko, the Tiger's Shadow").lower());self.assertIn('0/1',text('Preston, the Vanisher'))
 def test_sequences_own_cards_and_resource_accounting(self):
  for case,heads in OPENING_EXAMPLES.items():
   for did,names in heads.items():
    for n in names:self.assertIn(self.b.index.resolve(n),self.d[did]['main'],(case,did,n))
    self.assertLessEqual(len(names),7)
  r=checked_arithmetic();self.assertEqual(r['double_draco_shared_loss'],64);self.assertEqual(r['nanogene_controller_specific_triggers'],5)
 def test_distinct_yuriko_archetypes(self):
  c1=set(self.d['C1']['main']);c2=set(self.d['C2']['main']);self.assertGreaterEqual(len(c1-c2),20);self.assertIn(self.b.index.resolve('Demonic Consultation'),c1);self.assertNotIn(self.b.index.resolve('Demonic Consultation'),c2);self.assertIn(self.b.index.resolve('Doomsday'),c2);self.assertNotIn(self.b.index.resolve('Doomsday'),c1)
 def test_audio_length_and_artifact_catalog(self):
  from content import AUDIO
  for v in AUDIO.values():self.assertGreaterEqual(len(v.split()),120);self.assertLessEqual(len(v.split()),180)
  for path,digest in json.loads((self.folder/'artifact_hashes.json').read_text()).items():self.assertEqual(sha(self.folder/path),digest,path)
if __name__=='__main__':unittest.main()
