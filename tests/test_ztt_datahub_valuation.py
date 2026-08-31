import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "ztt"))

import ztt_datahub_20260830_valuation as model  # noqa: E402


class ZTTDatahubValuationTests(unittest.TestCase):
    def test_net_cash_uses_cash_equivalents_and_interest_bearing_debt(self):
        self.assertAlmostEqual(model.net_cash_rmb_bn(), 12.815563271, places=9)

    def test_fcff_bridge_charges_capex_and_working_capital(self):
        result = model.dcf()
        first = result["rows"][0]
        self.assertEqual(first["year"], 2026)
        self.assertAlmostEqual(first["fcff"], 3.97395, places=6)
        self.assertAlmostEqual(result["h1_actual_fcff"], -0.816527463, places=9)
        self.assertAlmostEqual(result["h2_fcff"], 4.790477463, places=9)

    def test_base_valuation_is_reproducible(self):
        result = model.dcf()
        self.assertAlmostEqual(result["value_per_share"], 41.748267053, places=9)
        self.assertAlmostEqual(result["upside"], 0.191445978, places=9)
        self.assertAlmostEqual(result["terminal_share"], 0.706106258, places=9)

    def test_three_operating_scenarios_are_reproducible(self):
        results = model.scenario_valuations()
        self.assertEqual(list(results), ["downside", "base", "upside"])
        self.assertAlmostEqual(
            results["downside"]["value_per_share"], 28.504612336, places=9
        )
        self.assertAlmostEqual(
            results["base"]["value_per_share"], 41.748267053, places=9
        )
        self.assertAlmostEqual(
            results["upside"]["value_per_share"], 51.836589241, places=9
        )
        self.assertLess(results["downside"]["upside"], 0)
        self.assertGreater(results["base"]["upside"], 0)

    def test_scenarios_change_operations_not_discount_rates(self):
        results = model.scenario_valuations()
        fcff_2028 = {
            key: result["rows"][2]["fcff"] for key, result in results.items()
        }
        self.assertLess(fcff_2028["downside"], fcff_2028["base"])
        self.assertLess(fcff_2028["base"], fcff_2028["upside"])
        self.assertEqual({result["wacc"] for result in results.values()}, {0.0967})
        self.assertEqual(
            {result["terminal_growth"] for result in results.values()}, {0.02}
        )

    def test_sensitivity_and_consensus_multiples(self):
        table = model.sensitivity()
        self.assertAlmostEqual(table[0.087][0.015], 44.974370520, places=9)
        self.assertAlmostEqual(table[0.107][0.025], 38.669433063, places=9)
        multiples = model.consensus_multiples()
        self.assertAlmostEqual(multiples[2026], 18.638297872, places=9)
        self.assertAlmostEqual(multiples[2028], 12.882352941, places=9)

    def test_invalid_terminal_spread_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "WACC"):
            model.dcf(wacc=0.02, terminal_growth=0.02)


class ZTTDatahubDocumentTests(unittest.TestCase):
    def test_datahub_snapshot_matches_model_inputs(self):
        snapshot = json.loads(
            (ROOT / "docs" / "ztt" / "datahub_20260830_snapshot.json").read_text()
        )
        self.assertEqual(snapshot["quote"]["price_rmb"], model.MARKET.price_rmb)
        self.assertAlmostEqual(
            snapshot["profile"]["total_shares"] / 1e9,
            model.MARKET.shares_bn,
            places=9,
        )
        eps = {
            int(row["period"][-4:]): row["mean_rmb"]
            for row in snapshot["consensus_eps"]["values"]
        }
        self.assertEqual(eps, model.CONSENSUS_EPS_RMB)

    def test_report_keeps_fact_forecast_and_assumption_statuses_visible(self):
        text = (
            ROOT / "docs" / "ztt" / "03-FIBER-TO-ZTT-VALUATION-20260830.md"
        ).read_text()
        for phrase in [
            "下行28.50元、基准41.75元、上行51.84元",
            "41.75元",
            "ACTUAL",
            "BROKER-EST",
            "PROJECT-ASSUMPTION",
            "FCFF =",
            "G.657.A2",
            "现金及现金等价物",
            "敏感性只是附录",
            "当前价格位于下行和基准之间",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
