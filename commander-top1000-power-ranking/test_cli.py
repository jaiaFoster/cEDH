"""End-to-end CLI checks against actual archived precon examples; no API calls."""
import json,pathlib,subprocess,sys,tempfile,unittest
HERE=pathlib.Path(__file__).resolve().parent
SCRIPT=HERE/"score_decks.py"
A=HERE/"examples/explorers_of_the_deep.txt"
B=HERE/"examples/necron_dynasties.txt"
def run(*args):
    return subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],text=True,capture_output=True)
class CliTests(unittest.TestCase):
    def test_real_precon_team_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/"team.json"
            p=run(A,"--deck-b",B,"--team-cap",30,"--export",path)
            self.assertEqual(p.returncode,0,p.stderr)
            d=json.loads(path.read_text());self.assertTrue(d["both_decks_legal"])
            self.assertEqual(d["total"],d["a"]["total"]+d["b"]["total"])
            self.assertEqual(d["teammate_synergy_adjustment"],0)
    def test_single_deck_cap(self):
        p=run(A,"--individual-cap",0)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(json.loads(p.stdout)["within_individual_cap"])
    def test_import_point_override(self):
        ordinary=run(A);self.assertEqual(ordinary.returncode,0,ordinary.stderr)
        report=json.loads(ordinary.stdout)
        oid=next(r["oracle_id"] for r in report["rows"] if r["card_name"]=="Sol Ring")
        prior=next(r["points_each"] for r in report["rows"] if r["card_name"]=="Sol Ring")
        with tempfile.TemporaryDirectory() as tmp:
            cfg=json.loads((HERE/"scoring_config.json").read_text());cfg["overrides"]={oid:{"main_deck_points":7}}
            path=pathlib.Path(tmp)/"overrides.json";path.write_text(json.dumps(cfg))
            p=run(A,"--config",path);self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)["total"],report["total"]-prior+7)
    def test_unknown_card_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/"unknown.txt";path.write_text("Commander\n1 Kinnan, Bonder Prodigy\nDeck\n98 Forest\n1 Definitely nonexistent league card\n")
            p=run(path);self.assertNotEqual(p.returncode,0)
            self.assertIn("Unknown or ambiguous card",p.stderr)
if __name__=="__main__":unittest.main()
