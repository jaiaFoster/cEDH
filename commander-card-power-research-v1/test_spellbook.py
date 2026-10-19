
from spellbook_integration import *
import unittest
class Tests(unittest.TestCase):
    def test_parse(self):
        d=parse_decklist("Commander\n1 Alpha\nDeck\n2 Beta (SET) 42\n1 Gamma")
        self.assertEqual(d["commanders"],{"Alpha":1})
        self.assertEqual(d["main"],{"Beta":2,"Gamma":1})
    def test_reject_sideboard(self):
        with self.assertRaises(ValueError): parse_decklist("1 Alpha\nSideboard\n1 Beta")
    def test_unknown_not_silent(self):
        with self.assertRaises(KeyError):
            normalize_payload({"main":{"Unknown":1}}, lambda name: {}[name])
    def test_normalize_merge(self):
        p=normalize_payload({"main":{"A":1,"a":2}}, lambda name:"id-a")
        self.assertEqual(p["main"],[{"card":"id-a","quantity":3}])
    def test_pagination(self):
        calls=[]
        def transport(path,payload):
            calls.append(path)
            return {"results":{"included":[{"id":str(len(calls))}]},"next":
                "https://backend.commanderspellbook.com/find-my-combos/?offset=1000" if len(calls)==1 else None}
        r=SpellbookClient("League research/contact",transport=transport).find_combos({})
        self.assertEqual(r["pages"],2)
        self.assertEqual(len(r["categories"]["included"]),2)
    def test_foreign_host(self):
        with self.assertRaises(ValueError):
            SpellbookClient("Test",transport=lambda p,d:{"results":{"included":[]},"next":"https://example.com/"}).find_combos({})
    def test_unresolved(self):
        r=classify_response({"categories":{"included":[{"id":"x","uses":[],
            "easyPrerequisites":None,"produces":[]}]}})
        self.assertEqual(r[0]["status"],"component_complete_unresolved")
        self.assertEqual(r[0]["construction_point_adjustment"],0)
    def test_team_split(self):
        record={"components":[{"oracle_id":"a","quantity":1},{"oracle_id":"b","quantity":1}]}
        r=mark_controller_review([record],{"main":{"a":1}},{"main":{"b":1}})
        self.assertTrue(r[0]["cross_deck_components_required"])
        self.assertEqual(r[0]["team_functionality"],"unverified")
    def test_duplicate_quantity(self):
        u=team_candidates({"main":{"a":1}},{"main":{"a":2}})
        self.assertEqual(u["main"]["a"],3)
    def test_retry(self):
        calls=[]; waits=[]
        def tr(path,payload):
            calls.append(path)
            if len(calls)==1:
                raise urllib.error.HTTPError(API,429,"limited",{"Retry-After":"2"},None)
            return {"results":{"included":[]},"next":None}
        SpellbookClient("Test",transport=tr,sleep=waits.append).find_combos({})
        self.assertEqual(waits,[2.0])
if __name__ == "__main__":
    unittest.main()
