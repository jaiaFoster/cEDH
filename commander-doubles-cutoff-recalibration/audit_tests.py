"""Regression tests for calibration authority, locations, rules and budget edges."""
import collections,copy,gzip,hashlib,json,pathlib,subprocess,sys,tempfile,unittest
import numpy as np
import pandas as pd
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parent
from recalibrated_backend import load_backend,RecalibratedBackend,load_deck
from audit_backend import proposed_price
from adversarial_inputs import fixture
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b=load_backend();cls.config=json.loads((HERE/'scoring_config.json').read_text());cls.ledger=json.loads((HERE/'calibration_precedence.json').read_text());cls.schedule=pd.read_csv(HERE/'recalibrated_point_schedule.csv');cls.fixtures=json.loads((HERE/'adversarial_decklists/fixtures.json').read_text());cls.cache=[json.loads(l) for l in (HERE/'two_hg_rules_cache.jsonl').read_text().splitlines()]
 def p(self,name,z='main'):return self.b.card_price(self.b.index.resolve(name),z)
 def test_all_fifty_original_qualitative_anchors_preserved(self):
  old=json.loads((ROOT/'commander-doubles-final-audit/human_calibration_anchors.json').read_text());new=json.loads((HERE/'human_calibration_anchors.json').read_text());self.assertEqual(old,new);self.assertEqual(len(new['anchors']),50)
  for a in new['anchors']:
   with self.subTest(card=a['card_name'],zone=a['zone']):
    match=next(x for x in self.ledger['original_50_qualitative_anchors'] if x['oracle_id']==a['oracle_id'] and x['zone']==a['zone']);self.assertEqual(match['tier'],a['tier'])
    if a['tier']==0:self.assertEqual(self.p(a['card_name'],a['zone']),0)
    else:self.assertGreater(self.p(a['card_name'],a['zone']),0)
 def test_latest_direct_prices(self):
  expected={'Scheming Symmetry':0,'Counterspell':0,'Aetherflux Reservoir':1,'Felidar Sovereign':2,'Sorin Markov':5,'Serra Ascendant':1,'Mindslaver':5,'Last Chance':7,"Warrior's Oath":7,"Teferi's Protection":3,'Consecrated Sphinx':1,'Notion Thief':5}
  for n,v in expected.items():
   with self.subTest(card=n):self.assertEqual(self.p(n),v)
 def test_ranges_not_promoted_to_exact_approval(self):
  for r in self.ledger['effective_location_decisions']:
   bounds=r.get('approved_range')
   if bounds:
    p=self.p(r['card_name'],r['zone']);lo,hi=bounds
    if lo is not None:self.assertGreaterEqual(p,lo)
    if hi is not None:self.assertLessEqual(p,hi)
    self.assertNotEqual(r['authority'],'explicit_organizer_price')
 def test_old_band_enforcement_removed(self):
  self.assertNotIn('human_tier_price_intervals',self.config);self.assertFalse(self.ledger['numeric_band_enforcement'])
  # Tier5 numerical choice can differ from old assistant band absent exact organizer constraint.
  cfg=copy.deepcopy(self.config);oid=self.b.index.resolve('Demonic Tutor');cfg['overrides'][oid]['main_deck_points']=16
  b=RecalibratedBackend(self.b.index,pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv'),cfg,anchors=self.b.anchors,precedence=self.b.precedence);self.assertEqual(b.card_price(oid,'main'),16)
 def test_explicit_organizer_conflict_rejected(self):
  cfg=copy.deepcopy(self.config);cfg['overrides'][self.b.index.resolve('Counterspell')]['main_deck_points']=2
  with self.assertRaisesRegex(ValueError,'Explicit organizer'):RecalibratedBackend(self.b.index,pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv'),cfg,anchors=self.b.anchors,precedence=self.b.precedence)
 def test_tier_zero_conflict_rejected(self):
  cfg=copy.deepcopy(self.config);cfg['overrides'][self.b.index.resolve('Kenrith, the Returned King')]['command_zone_points']=1
  with self.assertRaisesRegex(ValueError,'free qualitative'):RecalibratedBackend(self.b.index,pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv'),cfg,anchors=self.b.anchors)
 def test_qualitative_ordering_working_prices(self):
  anchors=json.loads((HERE/'human_calibration_anchors.json').read_text())['anchors']
  for z in ('main','commanders'):
   for a in anchors:
    for b in anchors:
     if a['zone']==b['zone']==z and a['tier']>b['tier']:self.assertGreater(self.p(a['card_name'],z),self.p(b['card_name'],z),(a['card_name'],b['card_name']))
 def test_known_zero_unknown_error(self):
  self.assertEqual(self.p('Plains'),0);self.assertEqual(self.p('Arcane Signet'),0)
  with self.assertRaises(KeyError):self.b.score({'commanders':{'Imaginary Unknown Commander':1},'main':{}})
 def test_all_basics_and_ordinary_fixing_zero(self):
  for c in self.b.index.cards.values():
   if 'Basic Land' in c.get('type_line',''):self.assertEqual(self.b.card_price(c['oracle_id'],'main'),0)
  for n in ['Command Tower','Evolving Wilds','Polluted Delta','Watery Grave']:self.assertEqual(self.p(n),0)
 def test_same_oracle_printing_alias(self):
  self.assertEqual(self.p('Force of Will'),self.b.card_price(self.b.index.resolve('Force of Will'),'main'))
  for c in self.b.index.cards.values():
   if ' // ' in c['name'] and c['oracle_id'] in self.b.ratings:self.assertEqual(self.p(c['name']),self.b.card_price(c['oracle_id'],'main'))
 def test_schedule_matches_backend_all_rows(self):
  self.assertEqual(len(self.schedule.oracle_id.unique()),len(self.schedule))
  for r in self.schedule.to_dict('records'):
   self.assertEqual(self.p(r['card_name']),r['main_deck_points']);self.assertEqual(self.p(r['card_name'],'commanders'),r['command_zone_points']);self.assertTrue(r['league_card_legal'])
   if r['command_zone_points']:self.assertNotEqual(r['commander_eligibility'],'ineligible')
 def test_no_silent_impact_edit(self):
  old=pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv').set_index('oracle_id');new=pd.read_csv(HERE/'full_candidate_reassessment.csv').set_index('oracle_id')
  self.assertTrue(set(old.index)<=set(new.index));self.assertEqual(len(old),9610)
  np.testing.assert_allclose(old.main_deck_impact,new.loc[old.index].main_deck_impact_frozen,equal_nan=True)
  np.testing.assert_allclose(old.command_zone_impact,new.loc[old.index].command_zone_impact_frozen,equal_nan=True)
 def test_main_cz_alternatives(self):
  d=fixture(['Heartless Hidetsugu'],[],['Mountain']);r=self.b.score(d);self.assertEqual(r['total'],12);self.assertEqual(self.p('Heartless Hidetsugu'),8)
 def test_partners_sum_independent(self):
  d=fixture(['Thrasios, Triton Hero','Tymna the Weaver'],[],['Island']);r=self.b.score(d);self.assertTrue(r['officially_legal']);self.assertEqual(r['total'],19)
 def test_invalid_partner_and_color_size_singleton(self):
  d=fixture(['Kinnan, Bonder Prodigy','Magda, Brazen Outlaw'],[],['Forest']);self.assertIn('incompatible_commander_pair',self.b.score(d)['legality_issues'])
  d=fixture(['Isamaru, Hound of Konda'],['Counterspell','Counterspell'],['Plains']);r=self.b.score(d);self.assertFalse(r['officially_legal']);self.assertTrue(any('singleton' in s for s in r['legality_issues']))
  self.assertIn('deck_size_not100',self.b.score({'commanders':{'Isamaru, Hound of Konda':1},'main':{}})['legality_issues'])
 def test_bans_not_legalized(self):
  for n in ['Primeval Titan','Prophet of Kruphix','Golos, Tireless Pilgrim','Rofellos, Llanowar Emissary','Mana Crypt','Jeweled Lotus','Dockside Extortionist']:
   with self.subTest(card=n):
    d=fixture(['Kenrith, the Returned King'],[n],['Plains']);r=self.b.score(d);self.assertFalse(r['officially_legal']);self.assertTrue(any(row['experimental_banned'] for row in r['rows']))
 def test_all_adversarial_fixtures_legal(self):
  self.assertEqual(len(self.fixtures),21)
  for tid,pair in self.fixtures.items():
   for d in pair.values():self.assertTrue(self.b.score(d)['officially_legal'],tid);self.assertEqual(sum(d['main'].values())+sum(d['commanders'].values()),100)
 def test_no_synergy_surcharge_or_automatic_combo_certification(self):
  pair=self.fixtures['T01'];r=self.b.team(pair['a'],pair['b']);self.assertEqual(r['total'],r['a']['total']+r['b']['total']);self.assertEqual(r['teammate_synergy_adjustment'],0)
  self.assertTrue(r['combo_review_candidates'])
  for c in r['combo_review_candidates']:self.assertTrue(c['component_match_only']);self.assertTrue(c['requires_manual_state_and_controller_verification']);self.assertEqual(c['points_adjustment'],0)
 def test_controller_false_positives_remain_false(self):
  for ident in ['C15','C17','C18','C20','C35']:
   r=next(r for r in self.cache if r['id']==ident);self.assertIn('false_',r['status'])
 def test_free_yuriko_exploit_exposed(self):
  pair=self.fixtures['T09'];r=self.b.team(pair['a'],pair['b']);self.assertEqual(r['total'],0);self.assertTrue(r['budget_compliant'])
 def test_budget_edges(self):
  cfg=copy.deepcopy(self.config)
  for n,v in [('Sol Ring',60),('Mana Vault',12),('Demonic Tutor',48),('Chrome Mox',1)]:cfg['overrides'][self.b.index.resolve(n)]={'main_deck_points':v}
  b=RecalibratedBackend(self.b.index,pd.read_csv(ROOT/'commander-top1000-power-ranking/candidate_inventory.csv'),cfg)
  a=fixture(['Kenrith, the Returned King'],['Sol Ring','Mana Vault'],['Plains']);bb=fixture(['Kenrith, the Returned King'],['Demonic Tutor'],['Plains']);r=b.team(a,bb);self.assertEqual(r['total'],120);self.assertTrue(r['budget_compliant']);self.assertEqual(r['points_transferred'],12)
  bb=fixture(['Kenrith, the Returned King'],['Demonic Tutor','Chrome Mox'],['Plains']);self.assertFalse(b.team(a,bb)['budget_compliant'])
  aa=fixture(['Kenrith, the Returned King'],['Sol Ring','Mana Vault','Chrome Mox'],['Plains']);self.assertFalse(b.team(aa,self.fixtures['T09']['a'])['budget_compliant'])
 def test_export_roundtrip(self):
  r=self.b.team(self.fixtures['T01']['a'],self.fixtures['T01']['b'])
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/'team.json';p.write_text(json.dumps(r));aa,bb=load_deck(p),load_deck(p,'b');self.assertEqual(self.b.team(aa,bb)['total'],r['total'])
 def test_curve_monotonic_and_strict_cutoff(self):
  for tau in (70,72.5,75,77.5,80):
   for curve in ('existing_tiers','fine_integer','nonlinear'):
    vals=[proposed_price(s,tau,curve) for s in np.linspace(0,100,401)];self.assertEqual(vals,sorted(vals));self.assertEqual(proposed_price(tau,tau,curve),0);self.assertGreater(proposed_price(tau+.01,tau,curve),0)
 def test_grid_and_boundary_coverage(self):
  f=pd.read_csv(HERE/'cutoff_sensitivity.csv');self.assertEqual(set(f.cutoff),{70,72.5,75,77.5,79.5,80});self.assertEqual(len(f),6*3*4*4)
  b=pd.read_csv(HERE/'cutoff_before_after_boundaries.csv');self.assertTrue(all(n==20 for n in b.groupby(['cutoff','stage','zone','side']).size()))
 def test_cohort_counts(self):
  f=pd.read_csv(HERE/'cohort_score_changes.csv');self.assertEqual(f.cohort.value_counts().to_dict(),{'cedh_holdout':2520,'official_precons':174,'bracket3_declared':150,'adversarial_fixture':42})
 def test_budget_exact_pair_counts(self):
  f=pd.read_csv(HERE/'budget_stress_test.csv');expected={'official_precons':15051,'bracket3_declared':11175,'cedh_holdout':3173940}
  for r in f.to_dict('records'):self.assertEqual(r['all_distinct_pairs'],expected[r['cohort']]);self.assertLessEqual(r['admitted'],r['all_distinct_pairs'])
 def test_cache_source_identity_and_citations(self):
  self.assertEqual(len(self.cache),62)
  for r in self.cache:
   self.assertFalse(r['unresolved_rule_references'],r['id']);self.assertFalse(r['automatic_combo_certification']);self.assertTrue(r['exact_rule_references'])
   for c in r['cards']:
    self.assertEqual(self.b.index.resolve(c['card_name']),c['oracle_id']);self.assertEqual(hashlib.sha256(c['current_oracle_text'].encode()).hexdigest(),c['oracle_text_sha256'])
 def test_rule_sensitive_regressions(self):
  cache={r['id']:r for r in self.cache};self.assertIn('805.8',cache['R48']['exact_rule_references']);self.assertIn('skip',cache['R48']['ruling'].lower());self.assertIn('724.1',cache['R43']['exact_rule_references']);self.assertIn('skip',cache['R45']['ruling'].lower());self.assertIn('not lethal',cache['R50']['ruling']);self.assertIn('compensating',cache['R47']['ruling'])
 def test_arithmetic_simultaneous_versus_sequential(self):
  from rules_arithmetic import simultaneous_half_events,sequential_half_upkeep
  self.assertEqual(simultaneous_half_events(60)['team_life_after'],0)
  self.assertEqual(simultaneous_half_events(61)['team_life_after'],1)
  self.assertEqual(simultaneous_half_events(61,round_up=True)['team_life_after'],-1)
  self.assertEqual(sequential_half_upkeep(60),{'individual_events':[30,15],'team_life_after':15})
 def test_arithmetic_individual_controller_and_shared_pool(self):
  from rules_arithmetic import pay_life,set_single_head_life,sacrifice_possible,card_draws_from_team_step,extra_team_turns,opponent_draw_allowed
  self.assertEqual(pay_life(60,50),10);self.assertEqual(60-50,10)
  self.assertEqual(set_single_head_life(60,10)['team_life_after'],10)
  self.assertFalse(sacrifice_possible('A','B'));self.assertTrue(sacrifice_possible('A','A'))
  self.assertEqual(card_draws_from_team_step(True),(0,0));self.assertEqual(card_draws_from_team_step(),(1,1))
  self.assertEqual(extra_team_turns(2),2);self.assertFalse(opponent_draw_allowed(1,True));self.assertTrue(opponent_draw_allowed(0,True))
  with self.assertRaises(ValueError):pay_life(60,1,cannot_change=True)
 def test_complete_extra_turn_review(self):
  df=pd.read_csv(HERE/'complete_extra_turn_family_review.csv');self.assertTrue(df.explicit_location_review.all());self.assertGreater(len(df),40)
 def test_new_cli_team_export_and_import(self):
  with tempfile.TemporaryDirectory() as td:
   target=pathlib.Path(td)/'report.json';cmd=[sys.executable,str(HERE/'recalibrated_backend.py'),str(HERE/'adversarial_decklists/R14_A.txt'),'--deck-b',str(HERE/'adversarial_decklists/R14_B.txt'),'--team-cap','8','--export',str(target)]
   run=subprocess.run(cmd,text=True,capture_output=True);self.assertEqual(run.returncode,0,run.stderr);r=json.loads(target.read_text());self.assertEqual(r['total'],9);self.assertFalse(r['budget_compliant']);self.assertTrue(any(x['id']=='RC01' for x in r['combo_review_candidates']))
   again=subprocess.run([sys.executable,str(HERE/'recalibrated_backend.py'),str(target)],text=True,capture_output=True);self.assertEqual(again.returncode,0,again.stderr);self.assertEqual(json.loads(again.stdout)['total'],9)
 def test_new_cli_override_import_and_authority_rejection(self):
  with tempfile.TemporaryDirectory() as td:
   f=pathlib.Path(td)/'overrides.json';export=pathlib.Path(td)/'export.json';f.write_text(json.dumps({self.b.index.resolve('Time Sieve'):{'main_deck_points':9}}))
   run=subprocess.run([sys.executable,str(HERE/'recalibrated_backend.py'),str(HERE/'adversarial_decklists/R17_A.txt'),'--overrides',str(f),'--export-overrides',str(export)],text=True,capture_output=True);self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout)['total'],15)
   f.write_text(json.dumps({self.b.index.resolve('Counterspell'):{'main_deck_points':2}}))
   run=subprocess.run([sys.executable,str(HERE/'recalibrated_backend.py'),str(HERE/'adversarial_decklists/R17_A.txt'),'--overrides',str(f)],text=True,capture_output=True);self.assertNotEqual(run.returncode,0);self.assertIn('Explicit organizer price conflict',run.stderr)
 def test_new_cli_unknown_and_individual_cap(self):
  with tempfile.TemporaryDirectory() as td:
   f=pathlib.Path(td)/'unknown.txt';f.write_text('Commander\n1 Isamaru, Hound of Konda\n\nDeck\n1 Completely Invented Unknown Card\n98 Plains\n')
   run=subprocess.run([sys.executable,str(HERE/'recalibrated_backend.py'),str(f)],text=True,capture_output=True);self.assertNotEqual(run.returncode,0);self.assertIn('Unknown',run.stderr)
  run=subprocess.run([sys.executable,str(HERE/'recalibrated_backend.py'),str(HERE/'adversarial_decklists/T13_A.txt'),'--individual-cap','0'],text=True,capture_output=True);self.assertEqual(run.returncode,0,run.stderr);self.assertFalse(json.loads(run.stdout)['within_individual_cap'])
 def test_new_pair_flags_no_controller_certification(self):
  pair=self.fixtures['R17'];r=self.b.team(pair['a'],pair['b']);self.assertEqual(r['total'],14);self.assertFalse(r['gameplay_legality_approved'])
  # Split Tivit/Sieve remains a false candidate even in new pairing rule database.
  a=fixture(['Tivit, Seller of Secrets'],[],['Island']);bb=fixture(['Kenrith, the Returned King'],['Time Sieve'],['Island']);r=self.b.team(a,bb);self.assertTrue(any(c['known_controller_assessment']=='false_split_sacrifice' for c in r['combo_review_candidates']))
 def test_combat_engine_omissions_reviewed(self):
  self.assertEqual(self.p("Nature's Will"),4)
  for n in ['Bear Umbra','Sword of Feast and Famine',"Druids' Repository"]:self.assertEqual(self.p(n),3)
  r=next(r for r in self.cache if r['id']=='R62');self.assertIn('teammate controls trigger',r['ruling']);self.assertIn('equipment',r['ruling']);self.assertEqual(self.b.team(self.fixtures['T08']['a'],self.fixtures['T08']['b'])['total'],4)
 def test_no_activation(self):
  self.assertFalse(self.config['gameplay_policy_activated']);self.assertFalse(self.config['experimental_unbans']);self.assertEqual(self.config['version'],'season0-proposed')
 def test_generated_hashes(self):
  for n,digest in json.loads((HERE/'generated_artifact_hashes.json').read_text()).items():self.assertEqual(hashlib.sha256((HERE/n).read_bytes()).hexdigest(),digest,n)
if __name__=='__main__':unittest.main(verbosity=2)
