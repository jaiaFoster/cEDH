import io
import json
import pickle
from pathlib import Path
import unittest

import pandas as pd
from acquire_research import DataOnlyUnpickler
from spellbook_integration import parse_decklist

ROOT = Path(__file__).resolve().parent


class ResearchTests(unittest.TestCase):
    def test_pickle_globals_rejected(self):
        with self.assertRaises(pickle.UnpicklingError):
            DataOnlyUnpickler(io.BytesIO(pickle.dumps(Path("example")))).load()

    def test_commented_commander_section(self):
        self.assertEqual(parse_decklist("# Commander\n1 Alpha\n# Main\n1 Beta")["commanders"], {"Alpha": 1})

    def test_card_identity_and_integer_ratings(self):
        cards = pd.read_csv(ROOT / "card_scoring_candidates.csv")
        self.assertFalse(cards.oracle_id.duplicated().any())
        scores = cards.zarzak_cached_llm.dropna()
        self.assertTrue(((scores >= 0) & (scores <= 100) & (scores % 1 == 0)).all())

    def test_missing_is_not_a_zero_score(self):
        data = pd.read_csv(ROOT / "benchmark_results.csv")
        self.assertTrue(data.loc[~data.complete, "score"].isna().all())
        self.assertTrue((data.covered_cards + data.missing_cards == 100).all())

    def test_all_methods_preserve_deck_coverage(self):
        data = pd.read_csv(ROOT / "benchmark_results.csv")
        self.assertTrue((data.groupby("method").size() == 174).all())
        self.assertFalse(data.duplicated(["deck", "method"]).any())

    def test_additive_deck_totals(self):
        cards = pd.read_csv(ROOT / "card_scoring_candidates.csv").set_index("oracle_id")
        decks = json.loads((ROOT.parent / "commander-league-card-point-calibration/data/clean/precons.json").read_text())
        results = pd.read_csv(ROOT / "benchmark_results.csv")
        scores = results[results.method == "zarzak_cached_llm"].set_index("deck")
        for deck in decks:
            values = [(cards.loc[oid, "zarzak_cached_llm"], qty) for oid, qty in deck["counts"].items()]
            subtotal = sum(value * qty for value, qty in values if pd.notna(value))
            self.assertEqual(subtotal, scores.loc[deck["name"], "known_card_subtotal"])

    def test_live_combo_results_never_change_points(self):
        for path in (ROOT / "data/spellbook").glob("*.json"):
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                for record in data.get("classified", data.get("records", [])):
                    self.assertEqual(record["construction_point_adjustment"], 0)

    def test_basic_control_is_globally_fixed(self):
        cards = pd.read_csv(ROOT / "card_scoring_candidates.csv").set_index("name")
        for name in ("Mountain", "Plains", "Island", "Wastes", "Forest", "Swamp"):
            self.assertEqual(cards.loc[name, "zarzak_basic_equalized"], 30)


if __name__ == "__main__":
    unittest.main()
