"""Regression tests for audited prices/software and verified rule facts.
Rule metadata/arithmetic tests do not implement or certify a Magic rules engine.
"""
import copy,hashlib,json,pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
from audit_backend import AuditBackend,proposed_price
from audit_pipeline import generate
_CONTEXT=globals().get("_CONTEXT")
_FILES=globals().get("_FILES")
if _CONTEXT is None:
    _FILES,_CONTEXT=generate(ROOT,json.loads((HERE/"audit_inputs.json").read_text()))
C=_CONTEXT
B=C["backend"];INDEX=C["index"];FRAME=C["frame"];CONFIG=C["config"]
class AuditTests(unittest.TestCase):
    def test_all_fixture_sizes_and_legality(self):
        for name,pair in C["fixtures"].items():
            for d in pair.values():
                self.assertEqual(sum(d["main"].values())+sum(d["commanders"].values()),100)
                self.assertTrue(B.score(d)["officially_legal"],name)
    def test_exact_50_unique_human_anchors(self):
        aa=C["inputs"]["anchors"]
        self.assertEqual(len(aa),50);self.assertEqual(len({(a["oracle_id"],a["zone"]) for a in aa}),50)
    def test_ring_revision_and_tithe_retained(self):
        aa={a["card_name"]:a["tier"] for a in C["inputs"]["anchors"] if a["zone"]=="main"}
        self.assertEqual(aa["The One Ring"],4);self.assertEqual(aa["Smothering Tithe"],4)
    def test_basic_and_snow_fixing_zero(self):
        for n in ("Plains","Island","Swamp","Mountain","Forest","Wastes","Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp","Snow-Covered Mountain","Snow-Covered Forest","Arcane Signet","Command Tower"):
            self.assertEqual(B.card_price(INDEX.resolve(n),"main"),0,n)
    def test_unknown_is_error(self):
        with self.assertRaises(KeyError):B.score({"main":{"unreal audit card":99},"commanders":{"Isamaru, Hound of Konda":1}})
    def test_banned_not_legalized(self):
        r=B.score({"main":{"Forest":98,"Mana Crypt":1},"commanders":{"Grismold, the Dreadsower":1}})
        self.assertFalse(r["officially_legal"]);self.assertTrue(any(x["experimental_banned"] for x in r["rows"]))
        self.assertFalse(r["experimental_unbans_activated"])
    def test_alternative_command_zone_price(self):
        r=B.score({"main":{"Plains":99},"commanders":{"Kenrith, the Returned King":1}})
        self.assertEqual(r["total"],0)
        self.assertGreaterEqual(B.card_price(INDEX.resolve("Kenrith, the Returned King"),"main"),0)
    def test_98_partner_prices_each(self):
        r=B.score({"main":{"Forest":98},"commanders":{"Thrasios, Triton Hero":1,"Tymna the Weaver":1}})
        self.assertTrue(r["officially_legal"]);self.assertEqual(r["total"],19)
    def test_invalid_partners(self):
        self.assertFalse(B.score({"main":{"Forest":98},"commanders":{"Kinnan, Bonder Prodigy":1,"Tymna the Weaver":1}})["officially_legal"])
    def test_individual_color_identity(self):
        self.assertFalse(B.score({"main":{"Island":99},"commanders":{"Isamaru, Hound of Konda":1}})["officially_legal"])
    def test_both_decks_remain_individual(self):
        a={"main":{"Plains":99},"commanders":{"Isamaru, Hound of Konda":1}}
        b={"main":{"Island":99},"commanders":{"Arcanis the Omnipotent":1}}
        r=B.team(a,b);self.assertTrue(r["both_decks_legal"]);self.assertEqual(r["teammate_synergy_adjustment"],0)
    def test_oracle_identity_printing_independent(self):
        oid=INDEX.resolve("Sol Ring")
        self.assertEqual(B.card_price(oid,"main"),B.card_price(INDEX.resolve("sol ring"),"main"))
    def test_bad_quantity(self):
        for q in (-1,0,True,1.5):
            with self.assertRaises(ValueError):B.score({"main":{"Plains":q},"commanders":{"Isamaru, Hound of Konda":1}})
    def test_human_tier_cannot_silently_conflict(self):
        cfg=copy.deepcopy(CONFIG);cfg["overrides"][INDEX.resolve("Cyclonic Rift")]["main_deck_points"]=1
        with self.assertRaises(ValueError):AuditBackend(INDEX,FRAME,cfg,anchors=C["inputs"]["anchors"])
    def test_negative_bad_price(self):
        cfg=copy.deepcopy(CONFIG);cfg["overrides"][INDEX.resolve("Memnite")]={"main_deck_points":-1}
        with self.assertRaises(ValueError):AuditBackend(INDEX,FRAME,cfg)
    def test_invalid_noncommander_override(self):
        cfg=copy.deepcopy(CONFIG);cfg["overrides"][INDEX.resolve("Sol Ring")]["command_zone_points"]=1
        with self.assertRaises(ValueError):AuditBackend(INDEX,FRAME,cfg)
    def test_curve_monotonic(self):
        for curve in ("existing_tiers","fine_integer","nonlinear"):
            vv=[proposed_price(x/4,75,curve) for x in range(401)]
            self.assertEqual(vv,sorted(vv));self.assertEqual(vv[300],0)
    def test_editable_coefficients(self):
        self.assertNotEqual(proposed_price(95,75,"nonlinear",15,1.5),proposed_price(95,75,"nonlinear",25,1.5))
    def test_invalid_coefficients(self):
        for key in ("nonlinear_scale","nonlinear_power","fine_scale"):
            cfg={**CONFIG,key:float("nan")}
            with self.assertRaises(ValueError):AuditBackend(INDEX,FRAME,cfg)
    def test_bad_budget_values(self):
        for val in (-1,True,float("nan")):
            with self.assertRaises(ValueError):B._policy({**CONFIG,"individual_cap":val})
        for val in (-.1,1.1,True,float("nan")):
            with self.assertRaises(ValueError):B._policy({**CONFIG,"transfer_fraction":val})
    def _budget_fixture(self,a,b):
        cfg=copy.deepcopy(CONFIG)
        cfg["overrides"][INDEX.resolve("Ornithopter")]={"main_deck_points":a}
        cfg["overrides"][INDEX.resolve("Memnite")]={"main_deck_points":b}
        model=AuditBackend(INDEX,FRAME,cfg)
        da={"main":{"Plains":98,"Ornithopter":1},"commanders":{"Isamaru, Hound of Konda":1}}
        db={"main":{"Plains":98,"Memnite":1},"commanders":{"Isamaru, Hound of Konda":1}}
        return model,da,db
    def test_transfer_72_48_accepted(self):
        b,a,d=self._budget_fixture(72,48);r=b.team(a,d)
        self.assertTrue(r["budget_compliant"]);self.assertEqual(r["points_transferred"],12)
    def test_transfer_73_47_rejected(self):
        b,a,d=self._budget_fixture(73,47);r=b.team(a,d)
        self.assertTrue(r["within_team_cap"]);self.assertFalse(r["budget_compliant"])
    def test_transfer_zero_disables_borrowing(self):
        b,a,d=self._budget_fixture(61,59);self.assertFalse(b.team(a,d,transfer_fraction=0)["budget_compliant"])
    def test_combined_cap_not_extra_budget(self):
        b,a,d=self._budget_fixture(72,60);self.assertFalse(b.team(a,d)["budget_compliant"])
    def test_zero_reference(self):
        b,a,d=self._budget_fixture(0,0);self.assertTrue(b.team(a,d,team_cap=0,individual_reference=0,individual_cap=0)["budget_compliant"])
    def test_pairing_candidates_not_certified(self):
        p=C["fixtures"]["T01"];r=B.team(p["a"],p["b"])
        c=next(x for x in r["combo_review_candidates"] if x["id"]=="C01")
        self.assertTrue(c["component_match_only"]);self.assertTrue(c["requires_manual_state_and_controller_verification"])
        self.assertEqual(c["points_adjustment"],0);self.assertFalse(r["gameplay_legality_approved"])
    def test_pairing_orientation_reversible(self):
        p=C["fixtures"]["T01"];r=B.team(p["b"],p["a"])
        self.assertTrue(any(x["id"]=="C01" and x["orientation"]=="reversed" for x in r["combo_review_candidates"]))
    def test_split_bond_false_positive_exposed(self):
        a={"main":{"Swamp":98,"Sanguine Bond":1},"commanders":{"Grismold, the Dreadsower":1}}
        b={"main":{"Swamp":98,"Exquisite Blood":1},"commanders":{"Storrev, Devkarin Lich":1}}
        r=B.team(a,b);c=next(x for x in r["combo_review_candidates"] if x["id"]=="C15")
        self.assertEqual(c["known_controller_assessment"],"false_split_life_loop")
    def test_old_zero_counterexamples(self):
        for t in ("T01","T03"):
            p=C["fixtures"][t];self.assertEqual(C["models"]["old"].team(p["a"],p["b"])["total"],0)
    def test_old_chancellor_cost_not_zero(self):
        p=C["fixtures"]["T02"];self.assertEqual(C["models"]["old"].team(p["a"],p["b"])["total"],2)
    def test_chain_arithmetic_and_gain_ownership(self):
        opposing_pool=60;life_gained_B=0;life_gained_A=0
        for _ in range(30):opposing_pool-=2;life_gained_B+=1
        self.assertEqual((opposing_pool,life_gained_B,life_gained_A),(0,30,0))
    def test_hidetsugu_parity_arithmetic(self):
        self.assertEqual(60-2*(60//2),0);self.assertEqual(59-2*(59//2),1)
    def test_double_yuriko_damage_arithmetic(self):
        self.assertEqual(2*16*2,64)
    def test_rules_metadata_commander_poison(self):
        matrix={x["phrase"]:x for x in C["inputs"]["edge_cases"]}
        self.assertIn("903.10a",matrix["Commander damage"]["rules_citations"])
        self.assertIn("810.8d",matrix["Poison"]["rules_citations"])
        self.assertIn("team21",matrix["Commander damage"]["valuation_or_enforcement"])
    def test_new_rules_outlier_metadata(self):
        matrix={x["phrase"]:x for x in C["inputs"]["edge_cases"]}
        self.assertEqual(matrix["Another opponent"]["examples"],"Breena, the Demagogue")
        self.assertIn("75",matrix["Your starting life total"]["verified_operation"])
    def test_preserved_zero_commander_exploits_still_cost_zero(self):
        for team in ("T08","T09"):
            p=C["fixtures"][team];self.assertEqual(B.team(p["a"],p["b"])["total"],0)
    def test_rules_sensitive_positive_negative_register(self):
        combos={x["id"]:x for x in C["inputs"]["combos"]}
        self.assertEqual(combos["C03"]["status"],"verified_cross_team")
        self.assertTrue(combos["C15"]["status"].startswith("false"))
        self.assertTrue(combos["C17"]["status"].startswith("false"))
        self.assertTrue(combos["C18"]["status"].startswith("false"))
        self.assertTrue(combos["C27"]["status"].startswith("false"))
        self.assertEqual(combos["C13"]["status"],"verified_cross_team")
    def test_all_combo_ids_resolve(self):
        self.assertGreaterEqual(len(C["inputs"]["combos"]),25)
        for c in C["inputs"]["combos"]:
            for zone in ("cards_A","cards_B"):
                for n in c[zone]:self.assertIn(INDEX.resolve(n),INDEX.cards)
    def test_cohort_counts_no_silent_drop(self):
        n=C["benchmarks"].groupby("cohort").size().to_dict()
        self.assertEqual(n["official_precons"],174);self.assertEqual(n["bracket3_declared"],150);self.assertEqual(n["cedh_holdout"],2520)
    def test_default_schedule_contains_only_legal_cards(self):
        import io,pandas as pd
        rows=pd.read_csv(io.StringIO(_FILES["audited_point_schedule.csv"]))
        self.assertTrue(rows.league_card_legal.all());self.assertTrue((rows.commander_legality=="legal").all())
    def test_schedule_id_unique(self):
        self.assertFalse(C["schedule"].oracle_id.duplicated().any())
    def test_schedule_sparse_and_nonnegative_integer(self):
        self.assertLess(C["summary"]["legal_pointed_identities"],500)
        for col in ("main_deck_points","command_zone_points"):
            for n in C["schedule"][col]:self.assertGreaterEqual(n,0);self.assertIsInstance(n,int)
    def test_roundtrip_submitted_json(self):
        p=C["fixtures"]["T01"]["a"]
        self.assertEqual(B.score(p)["total"],B.score(json.loads(json.dumps(p)))["total"])
    def test_exported_submitted_deck_roundtrip(self):
        d=C["fixtures"]["T01"]["a"];r=B.score(d)
        self.assertEqual(B.score(r["submitted_deck"])["total"],r["total"])
    def test_explicit_team_individual_cap_in_subreports(self):
        model,a,b=self._budget_fixture(60,60);r=model.team(a,b,individual_cap=50)
        self.assertFalse(r["a"]["within_individual_cap"]);self.assertFalse(r["b"]["within_individual_cap"])
    def _cli(self,args,memory=None):
        import audit_backend,contextlib,io,os
        from unittest.mock import patch
        memory={} if memory is None else memory
        original_read=pathlib.Path.read_text
        def read(path,*a,**kw):
            key=str(path)
            if key in memory:return memory[key]
            marker="/commander-doubles-final-audit/"
            if marker in key:
                rel=key.split(marker,1)[1]
                if rel in _FILES:return _FILES[rel]
            return original_read(path,*a,**kw)
        def write(path,text,*a,**kw):memory[str(path)]=text;return len(text)
        output=io.StringIO()
        with patch.object(pathlib.Path,"read_text",read),patch.object(pathlib.Path,"write_text",write),patch.object(sys,"argv",["audit_backend.py",*args]),contextlib.redirect_stdout(output):
            audit_backend.cli()
        return json.loads(output.getvalue()),memory
    def test_cli_pair_export_override_roundtrip(self):
        a=str(HERE/"adversarial_decklists/T01_A.txt");b=str(HERE/"adversarial_decklists/T01_B.txt")
        r,memory=self._cli([a,"--deck-b",b,"--export","memory-team.json","--export-overrides","memory-overrides.json"])
        self.assertTrue(r["both_decks_legal"]);self.assertEqual(json.loads(memory["memory-team.json"])["total"],r["total"])
        self.assertIsInstance(json.loads(memory["memory-overrides.json"]),dict)
        again,_=self._cli(["memory-team.json"],memory)
        self.assertEqual(again["total"],r["total"]);self.assertEqual(again["submitted_decks"],r["submitted_decks"])
    def test_cli_unknown_errors(self):
        text="Commander\n1 Isamaru, Hound of Konda\nDeck\n98 Plains\n1 nonexistent audit CLI card\n"
        with self.assertRaises(KeyError):self._cli(["unknown.txt"],{"unknown.txt":text})
    def test_cli_override_import_but_no_legalization(self):
        oid=INDEX.resolve("Mana Crypt")
        memory={"test-deck.json":json.dumps({"main":{"Plains":98,"Mana Crypt":1},"commanders":{"Isamaru, Hound of Konda":1}}),
                "overrides.json":json.dumps({oid:{"main_deck_points":0}})}
        r,_=self._cli(["test-deck.json","--overrides","overrides.json"],memory)
        self.assertFalse(r["officially_legal"]);self.assertEqual(r["total"],0)
    def test_synthetic_rulebreaker_permission_flag(self):
        import audit_backend
        card=copy.deepcopy(INDEX.cards[INDEX.resolve("Talrand, Sky Summoner")])
        card["oracle_id"]="00000000-0000-4000-8000-000000000099"
        card["name"]="Synthetic Rulebreaker Test Fixture"
        card["oracle_text"]="Rulebreaker — Additional deck-construction permission requires manual review."
        ix=audit_backend.OracleIndex(list(INDEX.cards.values())+[card])
        b=AuditBackend(ix,FRAME,CONFIG)
        r=b.score({"main":{"Island":99},"commanders":{card["name"]:1}})
        self.assertFalse(r["officially_legal"]);self.assertIn("unsupported_rulebreaker_permission_requires_manual_review",r["legality_issues"])
    def test_required_artifacts_present(self):
        for n in ("final_audit_executive_summary.md","human_calibration_anchors.json","audited_point_schedule.csv","point_price_changes.csv",
                  "newly_pointed_cards.csv","newly_unpointed_cards.csv","calibration_disagreements.md","card_family_consistency_audit.md",
                  "cutoff_finalization_report.md","proposed_team_budget_analysis.md","official_2hg_rules_verification.md","two_hg_edge_case_matrix.csv",
                  "two_hg_power_outliers.md","team_combo_database.csv","team_combo_rules_analysis.md","proposed_league_legality_policy.md",
                  "experimental_unban_review.md","adversarial_team_archetypes.md","low_point_exploit_report.md","budget_stress_test.csv",
                  "unpointed_high_power_cards.csv","highest_priority_balance_risks.md","updated_cohort_benchmarks.csv","score_distribution_comparison.md",
                  "scoring_config.json","source_provenance.json","README.md"):
            self.assertIn(n,_FILES)
    def test_source_provenance_hashes(self):
        p=json.loads(_FILES["source_provenance.json"])
        for rel,meta in p["inputs"].items():
            if "sha256" in meta:self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),meta["sha256"])
for position,a in enumerate(C["inputs"]["anchors"]):
    def check(self,anchor=a):
        self.assertEqual(B.card_price(anchor["oracle_id"],anchor["zone"]),anchor["proposed_points"])
        bounds={0:(0,0),1:(1,2),2:(3,4),3:(5,7),4:(8,10),5:(11,15)}
        low,high=bounds[anchor["tier"]];self.assertTrue(low<=anchor["proposed_points"]<=high)
    setattr(AuditTests,"test_anchor_"+str(position).zfill(2),check)
def run():
    stream=__import__("io").StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests))
    return {"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),
            "successful":result.wasSuccessful(),"output":stream.getvalue()}
if __name__=="__main__":
    r=run();print(r["output"]);sys.exit(0 if r["successful"] else 1)
