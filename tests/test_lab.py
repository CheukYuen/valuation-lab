import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))

from mini_dcf import value  # noqa: E402
from reverse import solve  # noqa: E402


class MiniDcfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = json.loads((ROOT / "lab/inputs/simple.json").read_text())

    def test_more_fcf_increases_value(self):
        richer = copy.deepcopy(self.params)
        richer["base_fcf"] *= 1.1
        self.assertGreater(value(richer)["equity_value"], value(self.params)["equity_value"])

    def test_more_growth_increases_value(self):
        faster = copy.deepcopy(self.params)
        faster["growth"] += 0.01
        self.assertGreater(value(faster)["equity_value"], value(self.params)["equity_value"])

    def test_higher_wacc_decreases_value(self):
        riskier = copy.deepcopy(self.params)
        riskier["discount_rate"] += 0.01
        self.assertLess(value(riskier)["equity_value"], value(self.params)["equity_value"])

    def test_wacc_must_exceed_terminal_growth(self):
        invalid = copy.deepcopy(self.params)
        invalid["discount_rate"] = invalid["terminal_growth"]
        with self.assertRaises(ValueError):
            value(invalid)

    def test_reverse_solver_recovers_growth(self):
        expected_growth = 0.12

        def equity_at_growth(growth):
            params = copy.deepcopy(self.params)
            params["growth"] = growth
            return value(params)["equity_value"]

        target = equity_at_growth(expected_growth)
        solved = solve(target, equity_at_growth, -0.5, 1.0)
        self.assertIsNotNone(solved)
        self.assertAlmostEqual(solved, expected_growth, places=10)


class FrozenCaseTests(unittest.TestCase):
    EXPECTED = {
        "valuation-inputs.json": "8589477eb52cdb155162a5130c828c3f8f08187cda461612ccddd3b43f29b257",
        "calculate.py": "64d0c404924ea58a5955d077ce7d111d24dbed5d762febefabff41206c53e0af",
    }

    def test_yofc_frozen_files_are_unchanged(self):
        frozen = ROOT / "cases/01-yofc/frozen"
        for name, expected in self.EXPECTED.items():
            digest = hashlib.sha256((frozen / name).read_bytes()).hexdigest()
            self.assertEqual(digest, expected, name)


if __name__ == "__main__":
    unittest.main()
