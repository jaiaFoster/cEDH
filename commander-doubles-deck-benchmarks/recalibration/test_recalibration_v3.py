"""Issue5 independent arithmetic, authority, identity, rules and freeze regressions."""
import collections,contextlib,copy,csv,gzip,io,json,pathlib,re,subprocess,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import recalibration_v3 as r

class RecalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old,cls.v2,cls.v3,cls.authority,cls.proposals,cls.history=r.build_backends()
        cls.original=r.original_decks();cls.files=r.generate()
        cls.schedule=list(csv.DictReader(io.StringIO(cls.files['candidate_point_schedule_v3.csv'])))
        cls.ledger=list(csv.DictReader(io.StringIO(cls.files['full_card_rescoring_ledger.csv'])))
        cls.decks=list(csv.DictReader(io.StringIO(cls.files['deck_score_changes.csv'])))
        cls.teams=list(csv.DictReader(io.StringIO(cls.files['team_score_changes.csv'])))
        cls.rules=[json.loads(x) for x in cls.files['rules_interactions_v3.jsonl'].splitlines()]
        cls.index=cls.v3.index
    def price(self,name,zone='main',model=None):return (model or self.v3).card_price(self.index.resolve(name),zone)
    def test_166_consolidated_values_consistent_globally(self):
        overlay=r.rows(r.OVERLAY);self.assertEqual(len(overlay),166)
        for row in overlay:
            self.assertEqual(self.price(row['card_name'],row['zone'],self.v2),int(row['points']))
            self.assertEqual(self.price(row['card_name'],row['zone']),int(row['points']))
    def test_earlier_ranges_and_exact_prices_not_silently_overwritten(self):
        for (oid,zone),row in self.authority.items():
            self.assertEqual(self.v2.card_price(oid,zone),self.v3.card_price(oid,zone),row)
            bounds=row.get('approved_range')
            if bounds:
                value=self.v3.card_price(oid,zone)
                if bounds[0] is not None:self.assertGreaterEqual(value,bounds[0])
                if bounds[1] is not None:self.assertLessEqual(value,bounds[1])
        self.assertEqual(self.price('Consecrated Sphinx'),1);self.assertEqual(self.price('Timetwister'),3)
    def test_late_reversals(self):
        for n,p in {'Basalt Monolith':4,'Swan Song':2,'Opposition Agent':6,'Krark-Clan Ironworks':10,'Crop Rotation':6,'Lake of the Dead':6,'Aluren':4,'Tireless Provisioner':1,'Serra Ascendant':1,'Bloodthirsty Conqueror':3,'Enduring Tenacity':4,"Orim's Chant":1,'Unwinding Clock':2,'Land Tax':1}.items():self.assertEqual(self.price(n),p,n)
    def test_lineage_sources_and_within_note_reversals(self):
        for row in csv.DictReader(io.StringIO(self.files['decision_lineage.csv'])):
            self.assertTrue((r.ROOT/row['latest_source']).is_file(),row['latest_source'])
        reverse=list(csv.DictReader(io.StringIO(self.files['decision_reversals.csv'])))
        self.assertEqual(len(reverse),12)
        for row in reverse:self.assertEqual(int(row['effective_points']),self.price(row['card_name'],row['zone']))
    def test_fifty_qualitative_anchors_immutable_and_separate(self):
        anchors=json.loads((r.ROOT/'commander-doubles-final-audit/audit_inputs.json').read_text())['anchors']
        self.assertEqual(len(anchors),50);self.assertEqual(self.v3.anchors,anchors)
        self.assertEqual(next(a['tier'] for a in anchors if a['card_name']=="Orim's Chant"),5)
        self.assertEqual(self.price("Orim's Chant"),1)
        self.assertEqual(next(a['tier'] for a in anchors if a['card_name']=='Derevi, Empyrial Tactician'),0)
        self.assertEqual(self.price('Derevi, Empyrial Tactician','commanders'),2)
    def test_deliberate_free_exceptions(self):
        for n in r.ZERO_MAIN:self.assertEqual(self.price(n),0,n)
        for n in ['Najeela, the Blade-Blossom','Kenrith, the Returned King','Yuriko, the Tiger\'s Shadow','Inalla, Archmage Ritualist','Oloro, Ageless Ascetic']:self.assertEqual(self.price(n,'commanders'),0,n)
    def test_contested_prices_remain_unchanged(self):
        self.assertEqual(self.price('Time Sieve'),8);self.assertEqual(self.price('Winds of Abandon'),5)
        self.assertEqual(self.price('Boseiju, Who Endures'),6);self.assertEqual(self.price('Otawara, Soaring City'),6)
        lines={x['card_name']:x for x in csv.DictReader(io.StringIO(self.files['decision_lineage.csv'])) if x['zone']=='main'}
        self.assertEqual(lines['Boseiju, Who Endures']['precision'],'working_within_organizer_5_to_6')
        self.assertEqual(lines['Reshape']['precision'],'organizer_approximate_around_8')
        self.assertEqual(lines['Cabal Coffers']['precision'],'accepted_assistant_placeholder_8_to_10')
    def test_no_main_command_zone_leak(self):
        self.assertEqual(self.price('Sheoldred, the Apocalypse'),7);self.assertEqual(self.price('Sheoldred, the Apocalypse','commanders'),13)
        self.assertEqual(self.price('Breya, Etherium Shaper'),2);self.assertEqual(self.price('Breya, Etherium Shaper','commanders'),5)
        self.assertEqual(self.price('Chulane, Teller of Tales','commanders'),2)
    def test_proposals_have_no_protected_overlap(self):
        self.assertFalse(set(self.authority)&set(self.proposals))
        for (oid,zone),row in self.proposals.items():
            self.assertTrue(r.legal(self.index.cards[oid]));self.assertGreater(len(row['reason']),30);self.assertTrue(row['anchor'])
    def test_schedule_is_unique_and_prices_match_backend(self):
        keys=[(x['oracle_id'],x['zone']) for x in self.schedule];self.assertEqual(len(keys),len(set(keys)))
        for x in self.schedule:
            self.assertEqual(int(x['proposed_points']),self.v3.card_price(x['oracle_id'],x['zone']))
            self.assertGreaterEqual(int(x['proposed_points']),0)
            self.assertEqual(x['activated'],'False');self.assertEqual(x['status'],'season0-proposed')
    def test_complete_mandatory_identity_union(self):
        pool={x['oracle_id'] for x in self.schedule};old={x['oracle_id'] for x in r.rows(r.PRIOR)}
        ids={self.index.resolve(n) for d in self.original.values() for z in d['deck'].values() for n in z}
        self.assertEqual(len(old),320);self.assertEqual(len(ids),751);self.assertTrue((old|ids)<=pool)
    def test_every_legal_positive_backend_price_exported(self):
        keys={(x['oracle_id'],x['zone']) for x in self.schedule}
        for oid,c in self.index.cards.items():
            if not r.legal(c):continue
            for zone in ['main']+(['commanders'] if r.eligibility(c) else []):
                if self.v3.card_price(oid,zone)>0:self.assertIn((oid,zone),keys,c['name'])
    def test_digital_representative_is_not_digital_identity(self):
        for name in ['Intuition','Pox']:
            oid=self.index.resolve(name);c=self.index.cards[oid];self.assertTrue(c['digital']);self.assertNotIn('paper',c['games']);self.assertTrue(r.legal(c))
            self.assertIn(oid,{x['oracle_id'] for x in self.schedule})
        proof=json.loads((r.HERE/'v3_inputs/identity_paper_examples.json').read_text())
        for row in proof:self.assertIn('paper',row['paper_example']['games']);self.assertEqual(row['oracle_id'],self.index.resolve(row['name']))
    def test18_legal_complete_decks_and1800_entries(self):
        self.assertEqual(len(self.original),18);self.assertEqual(len(self.ledger),1800)
        for did,d in self.original.items():
            score=self.v3.score(d['deck']);self.assertTrue(score['officially_legal'],score['legality_issues'])
            self.assertEqual(sum(sum(z.values()) for z in d['deck'].values()),100)
            self.assertEqual(sum(x['deck_id']==did for x in self.ledger),100)
    def test_sources_frozen_against_base_commit(self):
        paths=[v['path'] for v in self.original.values()]
        paths += [p.with_suffix('.txt') for p in paths]
        paths += [r.OVERLAY,r.PRIOR,r.ROOT/'commander-doubles-final-audit/human_calibration_anchors.json']
        for p in paths:
            blob=subprocess.check_output(['git','show',r.SOURCE_COMMIT+':'+str(p.relative_to(r.ROOT))],cwd=r.ROOT)
            self.assertEqual(blob,p.read_bytes(),p)
    def test_independent_ledger_arithmetic(self):
        for d in self.decks:
            subset=[x for x in self.ledger if x['deck_id']==d['deck_id']]
            for src,target in [('original_points','original_points'),('organizer_v2_points','organizer_v2_points'),('candidate_v3_points','candidate_v3_points')]:self.assertEqual(sum(int(x[src]) for x in subset),int(d[target]))
            self.assertEqual(sum(int(x['candidate_v3_points']) for x in subset if x['zone']=='commanders'),int(d['v3_cz_points']))
    def test_same_price_across_batches_and_physical_copies(self):
        prices=collections.defaultdict(set)
        for x in self.ledger:prices[x['oracle_id'],x['zone']].add((x['organizer_v2_points'],x['candidate_v3_points']))
        self.assertTrue(all(len(p)==1 for p in prices.values()))
    def test_original_teams120_and_all_new_overages_visible(self):
        for x in self.teams:
            self.assertEqual(int(x['original_team']),120);self.assertGreater(int(x['total']),120)
            self.assertEqual(int(x['total']),int(x['head_a'])+int(x['head_b']))
            self.assertEqual(x['budget_compliant'],'False')
            self.assertEqual(int(x['team_overage']),int(x['total'])-120)
        h=next(x for x in self.teams if x['team']=='H' and x['model']=='organizer_v2')
        self.assertEqual(h['within_individual_cap'],'True');self.assertEqual(h['within_team_cap'],'False')
    def test_team_budget_boundaries_and_transfer(self):
        for a,b,good in [(60,60,True),(72,48,True),(48,72,True),(73,47,False),(72,49,False),(61,60,False),(0,0,True),(72,0,True),(71,49,True)]:self.assertEqual(r.budget(a,b)['budget_compliant'],good,(a,b))
        self.assertEqual(r.budget(72,48)['transferrable_points'],12)
        self.assertEqual(r.budget(72,70)['transfer_required'],12);self.assertEqual(r.budget(72,70)['transferrable_points'],0)
    def test_unknown_negative_bool_zone_and_ineligible_fail(self):
        for value in [-1,True,1.2,'1']:
            with self.assertRaises(ValueError):r.checked_points(value)
        with self.assertRaises(KeyError):self.v3.score({'main':{'Invented Recalibration Card':1},'commanders':{}})
        with self.assertRaises(KeyError):r.assign(self.v3,'not-an-oracle-id','main',1)
        with self.assertRaises(ValueError):r.assign(self.v3,self.index.resolve('Forest'),'sideboard',1)
        with self.assertRaises(ValueError):r.assign(self.v3,self.index.resolve('Forest'),'commanders',1)
        for quantity in [-1,0,True,1.5]:
            with self.assertRaises(ValueError):self.v3.score({'main':{'Forest':quantity},'commanders':{}})
    def test_legality_still_independent_of_budget(self):
        for name in ['Primeval Titan','Dockside Extortionist','Mana Crypt']:
            d=copy.deepcopy(self.original['H2']['deck']);d['main'][self.index.resolve('Forest')]-=1;d['main'][name]=1
            result=self.v3.score(d);self.assertFalse(result['officially_legal']);self.assertFalse(result['experimental_unbans_activated'])
        d=copy.deepcopy(self.original['H2']['deck']);d['main'][self.index.resolve('Forest')]-=1;d['main']['Demonic Tutor']=1
        self.assertFalse(self.v3.score(d)['officially_legal'])
    def test_partners_and_color_identity(self):
        d=self.original['H1']['deck'];self.assertEqual(len(d['commanders']),2)
        report=self.v3.score(d);self.assertEqual(report['command_zone_total'],sum(self.price(n,'commanders') for n in d['commanders']))
        d=copy.deepcopy(d);d['commanders'].pop(self.index.resolve('Malcolm, Keen-Eyed Navigator'));d['commanders']['Sheoldred, the Apocalypse']=1
        self.assertFalse(self.v3.score(d)['officially_legal'])
    def test_basic_land_and_mdfc_identity_once(self):
        self.assertEqual(self.price('Forest'),0)
        o=self.index.resolve('Malakir Rebirth');self.assertEqual(o,self.index.resolve('Malakir Mire'))
        self.assertEqual(o,self.index.resolve('Malakir Rebirth // Malakir Mire'))
        for did in self.original:
            self.assertLessEqual(sum(x['deck_id']==did and x['oracle_id']==o for x in self.ledger),1)
        self.assertEqual(len([x for x in self.schedule if x['oracle_id']==o]),1)
        d=copy.deepcopy(self.original['D1']['deck'])
        d['main'][self.index.resolve('Swamp')]-=2
        d['main']['Malakir Rebirth']=1;d['main']['Malakir Mire']=1
        self.assertIn('singleton_limit:Malakir Rebirth // Malakir Mire',self.v3.score(d)['legality_issues'])
    def test_rule_references_and_oracle_hashes(self):
        cr=gzip.open(r.BASE/'data/comprehensive_rules.gz','rt').read()
        self.assertGreaterEqual(len(self.rules),20)
        for case in self.rules:
            for ref in case['rules']:self.assertRegex(cr,'(?m)^'+re.escape(ref)+'(?:[. ]|$)',case['id'])
            for c in case['card_details']:
                self.assertEqual(c['oracle_text'],r.oracle_text(self.index.cards[c['oracle_id']]))
                self.assertEqual(c['oracle_text_sha256'],r.sha(c['oracle_text']))
        proof=json.loads((r.HERE/'v3_inputs/current_rules_verification.json').read_text())
        self.assertTrue(proof['matches_pinned_bytes']);self.assertEqual(proof['sha256'],r.sha(gzip.open(r.BASE/'data/comprehensive_rules.gz','rb').read()))
    def test_rules_sensitive_targeting(self):
        text=lambda n:r.oracle_text(self.index.cards[self.index.resolve(n)])
        self.assertIn("its controller pays {1}",text('Daze'))
        self.assertIn("Target artifact creature's controller",text('Arcum Dagsson'))
        self.assertIn('That player may search their library',text('Arcum Dagsson'))
        self.assertIn('Choose target creature.',text('Malakir Rebirth'));self.assertIn("under its owner's control",text('Malakir Rebirth'))
        self.assertIn("creature you don't control",text('Winds of Abandon'))
        self.assertIn('Sacrifice five artifacts',text('Time Sieve'))
        self.assertIn('you gain life',text('Sanguine Bond'))
    def test_sixty_life_math_and_devotion(self):
        import math
        self.assertEqual(60-2*math.ceil(60/3),20)
        self.assertEqual(60-2*2*math.ceil(60/3),-20)
        self.assertEqual(60-2*(60-10),-40)
        self.assertEqual(60-50,10)
        self.assertFalse(49>=50);self.assertTrue(49+2>=50)
        devotion=3+3+2;payment=2*3+3
        self.assertEqual(2*devotion-payment,7)
    def test_aluren_finite_kill_draw_safety(self):
        cast=draws=visits=0;enemy=60
        while enemy>0:
            for room in range(1,5):
                cast+=1
                if room==3:visits+=1;enemy-=2
                if enemy<=0:break
                if room==4:draws+=1
        self.assertEqual((cast,draws,visits),(119,29,30))
        self.assertEqual(self.price('Aluren'),4);self.assertEqual(self.price('Acererak the Archlich'),0)
    def test_sensitivity_holds_organizer_prices_fixed(self):
        rows=list(csv.DictReader(io.StringIO(self.files['sensitivity_by_deck_v3.csv'])))
        for did in self.original:
            values=[int(x['points']) for x in sorted([x for x in rows if x['deck_id']==did],key=lambda x:int(x['positive_agent_price_shift']))]
            self.assertEqual(values,sorted(values))
            self.assertTrue(all(x['organizer_values_unchanged']=='True' for x in rows))
    def test_artifact_hashes_and_nonactivation(self):
        for path,digest in json.loads(self.files['artifact_hashes_v3.json']).items():self.assertEqual(r.sha(self.files[path]),digest,path)
        for path in ['summary.json','scoring_config_v3.json','source_provenance.json']:self.assertFalse(json.loads(self.files[path])['activated'])
        self.assertEqual(self.v3.team(self.original['H1']['deck'],self.original['H2']['deck'])['teammate_synergy_adjustment'],0)
    def test_deterministic_generation_and_saved_artifacts(self):
        self.assertEqual(r.generate(),self.files)
        for path,text in self.files.items():self.assertEqual((r.HERE/path).read_bytes(),text.encode(),path)
    def test_cli_explicit_model_and_budget_failure(self):
        import score_recalibration_v3 as cli
        args=['score_recalibration_v3.py',str(self.original['H1']['path']),'--deck-b',str(self.original['H2']['path']),'--summary']
        with patch.object(sys,'argv',args),patch.object(cli,'build_backends',return_value=(self.old,self.v2,self.v3,self.authority,self.proposals,self.history)),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(),1)
        result=json.loads(output.getvalue());self.assertFalse(result['activated']);self.assertFalse(result['budget_compliant']);self.assertEqual(result['transferrable_points'],0)

if __name__=='__main__':unittest.main()
