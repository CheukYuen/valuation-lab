"""锁住长飞估值模型的主口径与文档引用数字。"""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "yofc"))

import valuation_model as vm  # noqa: E402


DOC_DCF = ROOT / "docs" / "yofc" / "02-FORECAST-AND-DCF.md"
DOC_RELATIVE = ROOT / "docs" / "yofc" / "03-RELATIVE-REVERSE-PEG.md"


class DcfTests(unittest.TestCase):
    def test_headline_values_per_share(self):
        expected = {"bear": 13.47, "base": 36.64, "bull": 69.34}
        for key, value in expected.items():
            with self.subTest(scenario=key):
                self.assertAlmostEqual(
                    vm.dcf(vm.SCENARIOS[key])["value_per_share_cny"], value, places=2
                )

    def test_hkd_conversion_direction(self):
        result = vm.dcf(vm.SCENARIOS["base"])
        self.assertAlmostEqual(
            result["value_per_share_hkd"],
            result["value_per_share_cny"] / vm.HKD_TO_CNY,
            places=6,
        )
        self.assertGreater(result["value_per_share_hkd"], result["value_per_share_cny"])

    def test_terminal_roic_equals_wacc(self):
        for key, scenario in vm.SCENARIOS.items():
            with self.subTest(scenario=key):
                result = vm.dcf(scenario)
                self.assertAlmostEqual(result["terminal_roic"], scenario.wacc, places=10)
                self.assertAlmostEqual(
                    result["terminal_value"],
                    result["terminal_fcff"]
                    / (scenario.wacc - scenario.terminal_growth),
                    places=10,
                )

    def test_terminal_turnover_jump_is_visible(self):
        result = vm.dcf(vm.SCENARIOS["bear"])
        self.assertAlmostEqual(result["terminal_incremental_turnover"], 1.61, places=2)
        self.assertGreater(
            result["terminal_incremental_turnover"],
            vm.SCENARIOS["bear"].capital_turnover,
        )

    def test_input_bounds(self):
        with self.assertRaises(ValueError):
            vm.dcf(vm.SCENARIOS["base"], wacc=0.02)
        with self.assertRaises(ValueError):
            vm.dcf(vm.SCENARIOS["base"], tax_rate=1.0)


class RelativeValuationTests(unittest.TestCase):
    def test_combined_market_cap(self):
        self.assertAlmostEqual(vm.actual_combined_market_cap(), 2054.48, places=1)

    def test_two_ev_calibers(self):
        equity = vm.actual_combined_market_cap()
        core = vm.relative_multiples(equity)
        reported = vm.reported_caliber_ev_multiples(equity)
        self.assertAlmostEqual(core["ev_ebit"], 48.7, places=1)
        self.assertAlmostEqual(core["ev_ebitda"], 38.0, places=1)
        self.assertAlmostEqual(reported["ev_ebit"], 44.1, places=1)
        self.assertAlmostEqual(reported["ev_ebitda"], 35.1, places=1)

    def test_peer_mechanical_values_only_keep_pe_and_pb(self):
        implied = vm.peer_median_implied_values()
        self.assertEqual(set(implied), {"pe", "pb"})
        self.assertAlmostEqual(implied["pe"], 487.40, places=2)
        self.assertAlmostEqual(implied["pb"], 480.30, places=2)


class ReverseDcfTests(unittest.TestCase):
    def test_documented_implied_margins(self):
        self.assertAlmostEqual(
            vm.reverse_constant_margin_for_equity(vm.actual_combined_market_cap()),
            0.9981,
            places=4,
        )
        self.assertAlmostEqual(
            vm.reverse_constant_margin_for_price(vm.A_PRICE_CNY), 1.5053, places=4
        )
        self.assertAlmostEqual(
            vm.reverse_constant_margin_for_price(vm.H_PRICE_HKD * vm.HKD_TO_CNY),
            0.5093,
            places=4,
        )


class DocumentConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dcf_doc = DOC_DCF.read_text(encoding="utf-8")
        cls.relative_doc = DOC_RELATIVE.read_text(encoding="utf-8")

    def test_dcf_doc_keeps_one_terminal_path(self):
        for value in ("13.47", "36.64", "69.34", "1.61x"):
            self.assertIn(value, self.dcf_doc)
        for removed in ("12.03", "39.37", "86.85", "terminal_mode"):
            self.assertNotIn(removed, self.dcf_doc)

    def test_relative_doc_keeps_calibers_without_ev_target_prices(self):
        for value in ("48.7", "38.0", "44.1", "35.1"):
            self.assertIn(value, self.relative_doc)
        for removed in ("533.78", "503.64", "590.00", "545.04"):
            self.assertNotIn(removed, self.relative_doc)


if __name__ == "__main__":
    unittest.main()
