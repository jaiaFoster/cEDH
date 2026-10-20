import gzip,io,json,pathlib
import pandas as pd
from ranking import *
from backend import SparseBackend
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
index=OracleIndex([json.loads(l) for l in gzip.open(ROOT/"commander-league-card-point-calibration/data/raw/oracle_cards.jsonl.gz","rt")])
frame=pd.read_csv(HERE/"candidate_inventory.csv")
testlog=io.StringIO()

import unittest
class BackendTests(unittest.TestCase):
 def setUp(self):
  self.b=SparseBackend(index,frame)
 def test_basic_cycle_zero(self):
  for n in ("Plains","Island","Swamp","Mountain","Forest","Wastes"):
   self.assertEqual(self.b.card_price(index.resolve(n),"main"),0)
 def test_mox_cycle_equal(self):
  self.assertEqual(len({self.b.card_price(index.resolve(n),"main") for n in ("Mox Emerald","Mox Jet","Mox Pearl","Mox Ruby","Mox Sapphire")}),1)
 def test_partner_98_plus2(self):
  d={"main":{"Forest":98},"commanders":{"Thrasios, Triton Hero":1,"Tymna the Weaver":1}}
  r=self.b.score(d)
  self.assertTrue(r["officially_legal"],r["legality_issues"])
  self.assertEqual(r["total"],r["command_zone_total"])
 def test_single_commander99(self):
  r=self.b.score({"main":{"Forest":99},"commanders":{"Kinnan, Bonder Prodigy":1}})
  self.assertTrue(r["officially_legal"],r["legality_issues"])
 def test_alternative_not_surcharge(self):
  oid=index.resolve("Kinnan, Bonder Prodigy")
  b=SparseBackend(index,frame,{"overrides":{oid:{"main_deck_points":13,"command_zone_points":7}}})
  self.assertEqual(b.score({"main":{"Forest":99},"commanders":{oid:1}})["total"],7)
 def test_unknown_rejected(self):
  with self.assertRaises(KeyError):self.b.score({"main":{"FAKE unknown card":99},"commanders":{"Kinnan, Bonder Prodigy":1}})
 def test_bad_pair_rejected(self):
  r=self.b.score({"main":{"Forest":98},"commanders":{"Kinnan, Bonder Prodigy":1,"Tymna the Weaver":1}})
  self.assertIn("incompatible_commander_pair",r["legality_issues"])
 def test_front_face_eligibility(self):
  self.assertFalse(eligibility(index.cards[index.resolve("Westvale Abbey")]))
  self.assertFalse(eligibility(index.cards[index.resolve("Elbrus, the Binding Blade")]))
 def test_vehicle_grist_eligible(self):
  self.assertTrue(eligibility(index.cards[index.resolve("Shorikai, Genesis Engine")]))
  self.assertTrue(eligibility(index.cards[index.resolve("Grist, the Hunger Tide")]))
 def test_background_conditional(self):
  self.assertEqual(eligibility(index.cards[index.resolve("Candlekeep Sage")]),"conditional_background")
  self.assertTrue(pair_legal(index.cards[index.resolve("Wilson, Refined Grizzly")],index.cards[index.resolve("Candlekeep Sage")]))
  self.assertFalse(pair_legal(index.cards[index.resolve("Thrasios, Triton Hero")],index.cards[index.resolve("Candlekeep Sage")]))
 def test_zone_legality_separate(self):
  r=self.b.score({"main":{"Forest":99},"commanders":{"Rofellos, Llanowar Emissary":1}})
  self.assertFalse(r["officially_legal"])
  self.assertGreater(r["total"],0)
 def test_color_identity_individual(self):
  r=self.b.score({"main":{"Mountain":99},"commanders":{"Kinnan, Bonder Prodigy":1}})
  self.assertTrue(any(x.startswith("outside_commander_color_identity") for x in r["legality_issues"]))
 def test_singleton(self):
  r=self.b.score({"main":{"Forest":97,"Sol Ring":2},"commanders":{"Kinnan, Bonder Prodigy":1}})
  self.assertIn("singleton_limit:Sol Ring",r["legality_issues"])
 def test_team_sum(self):
  d={"main":{"Forest":99},"commanders":{"Kinnan, Bonder Prodigy":1}}
  r=self.b.team(d,d)
  self.assertEqual(r["total"],2*r["a"]["total"])
  self.assertEqual(r["teammate_synergy_adjustment"],0)
 def test_override_validation(self):
  with self.assertRaises(ValueError):SparseBackend(index,frame,{"overrides":{index.resolve("Sol Ring"):{"main_deck_points":-1}}})
 def test_no_invalid_threshold(self):
  with self.assertRaises(ValueError):SparseBackend(index,frame,{"main_threshold":float("nan")})
 def test_oracle_printing_not_omitted(self):
  for n in ("Black Lotus","Mox Diamond","Rofellos, Llanowar Emissary","Time Walk"):
   self.assertIn(index.resolve(n),set(frame.oracle_id))

 def test_token_name_prefers_playable_card(self):
  oid=index.resolve("Ajani's Pridemate")
  self.assertEqual(index.cards[oid]["legalities"]["commander"],"legal")
 def test_ante_word_boundary_does_not_remove_auras(self):
  self.assertIn(index.resolve("Animate Dead"),set(frame.oracle_id))
 def test_current_partner_family(self):
  a=index.cards[index.resolve("Leonardo, the Balance")]
  b=index.cards[index.resolve("Michelangelo, the Heart")]
  self.assertTrue(pair_legal(a,b))
  self.assertFalse(pair_legal(a,index.cards[index.resolve("Thrasios, Triton Hero")]))
 def test_snow_basics_equal_zero(self):
  for n in ("Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp","Snow-Covered Mountain","Snow-Covered Forest"):
   self.assertEqual(self.b.card_price(index.resolve(n),"main"),0)
 def test_unknown_zone_rejected(self):
  with self.assertRaises(ValueError):self.b.card_price(index.resolve("Sol Ring"),"sideboard")
 def test_specialist_delta_nonnegative(self):
  self.assertTrue((frame.specialist_floor_delta>=0).all())
 def test_interchangeable_names_share_singleton(self):
  self.assertEqual(index.resolve("Rick, Steadfast Leader"),index.resolve("Greymond, Avacyn's Stalwart"))
  r=self.b.score({"main":{"Plains":98,"Rick, Steadfast Leader":1},"commanders":{"Greymond, Avacyn's Stalwart":1}})
  self.assertIn("singleton_limit:Greymond, Avacyn's Stalwart",r["legality_issues"])
 def test_zone_specific_evidence(self):
  r=self.b.score({"main":{"Forest":99},"commanders":{"The First Sliver":1}})
  self.assertEqual(next(x for x in r["rows"] if x["zone"]=="commanders")["rating_evidence"],"reviewed_judgment")
 def test_cli_alias_commander_selection(self):
  import tempfile
  from score_decks import load_deck
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/"deck.txt";p.write_text("99 Forest\n1 Esika, God of the Tree // The Prismatic Bridge\n")
   d=load_deck(p,["Esika, God of the Tree"],index.resolve)
   self.assertTrue(self.b.score(d)["officially_legal"])
 def test_configured_caps(self):
  d={"main":{"Forest":99},"commanders":{"Kinnan, Bonder Prodigy":1}}
  b=SparseBackend(index,frame,{"individual_cap":0,"team_cap":0})
  self.assertFalse(b.score(d)["within_individual_cap"])
  self.assertFalse(b.team(d,d)["within_team_cap"])
  self.assertFalse(b.team(d,d)["within_individual_cap"])
 def test_override_nominates_previously_unselected_card(self):
  oid=index.resolve("Grizzly Bears")
  cards=[index.cards[index.resolve(n)] for n in ("Grizzly Bears","Forest","Kinnan, Bonder Prodigy")]
  cfg={"main_threshold":75,"commander_threshold":75,"curve":"tiered","overrides":{oid:{"main_deck_points":7}}}
  ix,ratings,_,_=build_candidates(cards,{},[],[],{},{},cfg["overrides"])
  self.assertIn(oid,set(ratings.oracle_id))
  b=SparseBackend(ix,ratings,cfg)
  row=ratings.set_index("oracle_id").loc[oid]
  self.assertEqual(point_price(oid,"main",row.main_deck_impact,cfg),7)
  self.assertEqual(b.score({"main":{"Forest":98,"Grizzly Bears":1},"commanders":{"Kinnan, Bonder Prodigy":1}})["total"],7)
 def test_unknown_source_card_never_disappears(self):
  import tempfile,datetime
  from data_sources import acquire_local
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);base=root/"commander-league-card-point-calibration/data/raw";base.mkdir(parents=True)
   with gzip.open(base/"oracle_cards.jsonl.gz","wt") as f:
    for n in ("Forest","Kinnan, Bonder Prodigy"):f.write(json.dumps(index.cards[index.resolve(n)])+"\n")
   p=root/"data/tournament_snapshots/topdeck";(p/"normalized").mkdir(parents=True);(p/"raw").mkdir()
   (p/"manifest.json").write_text(json.dumps({"events":{"test":{"normalized_event":"normalized/test.json","raw_snapshot":"raw/test.json.gz"}}}))
   (p/"normalized/test.json").write_text(json.dumps({"name":"cEDH fixture","field_size":16,"start_date_unix":int(datetime.datetime(2026,10,10,tzinfo=datetime.timezone.utc).timestamp()),"start_date_utc":"2026-10-10","pods":[{"status":"Completed"}]}))
   obj={"Mainboard":{"Forest":{"count":99},"Unknown omitted card":{"count":1}},"Commanders":{"Kinnan, Bonder Prodigy":{"count":1}}}
   with gzip.open(p/"raw/test.json.gz","wt") as f:json.dump({"standings":[{"deckObj":obj}]},f)
   result,pools,_=acquire_local(root)
   self.assertEqual(result["exclusions"]["entry_unknown_card"],1)
   self.assertEqual(len(pools["cedh_holdout"]),0)
 def test_doctors_companion_not_changeling(self):
  self.assertTrue(pair_legal(index.cards[index.resolve("Clara Oswald")],index.cards[index.resolve("The Ninth Doctor")]))
  self.assertFalse(pair_legal(index.cards[index.resolve("Clara Oswald")],index.cards[index.resolve("Morophon, the Boundless")]))
 def test_backend_price_matches_exported_schedule(self):
  cfg=json.load(open(HERE/"scoring_config.json"));b=SparseBackend(index,frame,cfg)
  for row in pd.read_csv(HERE/"proposed_point_schedule.csv").to_dict("records"):
   self.assertEqual(b.card_price(row["oracle_id"],"main"),row["main_deck_points"])
   self.assertEqual(b.card_price(row["oracle_id"],"commanders"),row["command_zone_points"])
 def test_top1000_unique(self):
  r=pd.read_csv(HERE/"top_1000_main_deck_cards.csv")
  self.assertEqual(len(r),1000);self.assertTrue(r.oracle_id.is_unique)
 def test_experimental_bans_remain_banned(self):
  rows=pd.read_csv(HERE/"experimental_unban_ranking.csv")
  self.assertEqual(len(rows),42);self.assertFalse(rows.legalized.any())
  self.assertTrue((rows.commander_legality=="banned").all())
 def test_price_monotonicity_and_boundaries(self):
  for curve in ("linear","tiered","quadratic"):
   values=[price(s/4,75,curve) for s in range(401)]
   self.assertEqual(values,sorted(values))
  self.assertEqual([price(s,75) for s in (75,80,80.25,85,85.25)],[0,1,3,3,5])
 def test_backend_tiers_are_instance_specific(self):
  oid=index.resolve("Sol Ring")
  a=SparseBackend(index,frame,{"tier_bands":[[None,2]]})
  b=SparseBackend(index,frame)
  self.assertEqual(a.card_price(oid,"main"),2)
  self.assertEqual(b.card_price(oid,"main"),12)
 def test_noncommander_zone_override_rejected(self):
  with self.assertRaises(ValueError):SparseBackend(index,frame,{"overrides":{index.resolve("Sol Ring"):{"command_zone_points":3}}})
 def test_invalid_tier_configuration_errors(self):
  with self.assertRaises(ValueError):SparseBackend(index,frame,{"tier_bands":[[10,3],[5,1],[None,8]]})
suite=unittest.defaultTestLoader.loadTestsFromTestCase(BackendTests)
test_result=unittest.TextTestRunner(stream=testlog,verbosity=1).run(suite)
print(testlog.getvalue().rstrip())
assert test_result.wasSuccessful()
