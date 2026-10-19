"""Meaningful source, arithmetic and independent implementation checks."""
import unittest,json,gzip,collections,subprocess
from pathlib import Path
import pandas as pd
from model import load_config,score
class Integrity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cfg=load_config();cls.cs=pd.read_csv('commander_card_scores.csv').fillna('');cls.scores=cls.cs.set_index('oracle_id');cls.ds=json.loads(Path('data/clean/precons.json').read_text());cls.df=pd.read_csv('commander_precon_scores.csv');cls.cards={c['oracle_id']:c for c in (json.loads(l) for l in gzip.open('data/raw/oracle_cards.jsonl.gz','rt')) if c.get('oracle_id')}
 def test_no_missing_or_duplicate_ids(self):
  self.assertTrue(self.cs.oracle_id.is_unique);self.assertEqual(set(self.cs.oracle_id),set(self.cards));self.assertFalse(self.cs.base_points.isna().any());self.assertTrue((self.cs.base_points>=0).all());self.assertTrue((self.cs.base_points%1==0).all())
 def test_every_deck(self):
  keys=[]
  for d in self.ds:
   self.assertEqual(sum(d['counts'].values()),100);self.assertEqual(len(d['expanded_cards']),100);self.assertTrue(all(d['expanded_cards']));self.assertEqual(d['quality_flags'],['duplicate_nonbasic:Mossfire Valley'] if d['name']=='Upgrades Unleashed' else [],d['name']);self.assertTrue(d['commander_ids']);self.assertEqual(collections.Counter(d['expanded_cards']),collections.Counter(d['counts']))
   total=sum(self.scores.loc[o,'base_points']*n for o,n in d['counts'].items());self.assertEqual(total,self.df[self.df.name==d['name']].iloc[0].total_points);keys.append(tuple(sorted(d['counts'].items())))
  self.assertEqual(len(keys),len(set(keys)))
 def test_consistency_all_cards(self):
  for o,c in self.cards.items():self.assertEqual(score(c,self.cfg)['base_points'],self.scores.loc[o,'base_points'])
 def test_printing_year_invariance(self):
  c=next(c for c in self.cards.values() if c['name']=='Sol Ring');other=dict(c,set='future',released_at='2099-01-01',rarity='mythic',edhrec_rank=1);self.assertEqual(score(c,self.cfg),score(other,self.cfg))
 def test_coverage(self):
  c=json.loads(Path('data/clean/coverage_audit.json').read_text());self.assertFalse(c['missing_from_taw']);self.assertFalse(c['missing_from_mtgjson']);q=pd.read_csv('data/clean/deck_quality_audit.csv');self.assertTrue((q['size']==100).all());self.assertTrue(q.unresolved.isna().all())
 def test_unbans_do_not_legalize(self):
  u=pd.read_csv('experimental_unban_review.csv');self.assertFalse(u.legalized.any());self.assertEqual(len(u[u.official_status=='banned']),42);self.assertFalse(set(u[u.official_status=='banned'].oracle_id)-set(self.cs[self.cs.legality=='banned'].oracle_id))
 def test_calculator_engine(self):subprocess.run(['node','test_calculator.js'],check=True)
 def test_html_controls(self):subprocess.run(['node','test_html.js'],check=True)
 def test_game_changers(self):
  gc=json.loads(Path('data/clean/game_changer_reconciliation.json').read_text());self.assertEqual(gc['official_count'],53);self.assertFalse(gc['oracle_only']);self.assertFalse(gc['official_only'])
if __name__=='__main__':unittest.main(verbosity=2)
