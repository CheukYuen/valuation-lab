import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "ztt"))

import bofa_20260828_model as model  # noqa: E402
import ztt_datahub_20260830_valuation as project_model  # noqa: E402


class BofA20260828ModelTests(unittest.TestCase):
    def test_visible_forecast_derivations(self):
        result = model.visible_bridge()
        self.assertAlmostEqual(result["revenue_growth"][1], 0.319047619, places=9)
        self.assertAlmostEqual(result["ebitda_margin"][1], 0.158495307, places=9)
        self.assertAlmostEqual(result["fcf_to_net_income"][1], 0.471640091, places=9)

    def test_target_price_bridge_is_mechanical_not_dcf_reproduction(self):
        result = model.visible_bridge()
        self.assertAlmostEqual(result["reported_upside"], 0.801552106, places=9)
        self.assertAlmostEqual(result["target_cut"], -0.113233288, places=9)
        self.assertAlmostEqual(result["target_equity_value_rmb_m"], 221838.5, places=2)

    def test_current_price_sotp_closes(self):
        result = model.sotp_bridge()
        self.assertEqual(result["total_net_income_rmb_m"], 10_940)
        self.assertEqual(result["total_valuation_rmb_m"], 123_140)
        self.assertAlmostEqual(result["implied_price_rmb"], 36.08, places=2)
        for reported, calculated in zip(
            (line.valuation_rmb_m for line in model.SOTP_LINES),
            result["calculated_values_rmb_m"],
        ):
            self.assertLess(abs(reported - calculated), 40)

    def test_forecast_is_above_other_visible_benchmarks(self):
        premia = model.forecast_premia()
        self.assertAlmostEqual(premia["net_income_vs_morgan_stanley"][0] - 1, 0.367388257, places=9)
        self.assertAlmostEqual(premia["eps_vs_datahub_consensus"][1] - 1, 0.676855895, places=9)

    def test_missing_long_term_fcff_is_not_fabricated(self):
        audit = model.audit_summary()
        self.assertEqual(audit["annual_fcff_2029_2035_status"], "MISSING")
        self.assertFalse(audit["full_target_price_independently_reproducible"])
        with self.assertRaisesRegex(ValueError, "2029E-2035E逐年FCFF"):
            model.dcf_target_price_from_visible_inputs()

    def test_bofa_parameter_overlay_matches_document(self):
        expected = {"downside": 34.25, "base": 50.78, "upside": 63.43}
        for key, expected_value in expected.items():
            result = project_model.dcf(
                project_model.SCENARIOS[key].forecast,
                wacc=model.INPUTS.wacc,
                terminal_growth=model.INPUTS.terminal_growth,
            )
            self.assertAlmostEqual(result["value_per_share"], expected_value, places=2)


class BofA20260828DocumentTests(unittest.TestCase):
    def test_case_preserves_valuation_boundaries(self):
        text = (ROOT / "docs" / "ztt" / "04-BOFA-20260828-CASE.md").read_text()
        for phrase in [
            "What：",
            "Why：",
            "How：",
            "Data：",
            "MECHANICAL-SENSITIVITY",
            "不是美银目标价复现",
            "当前价格SOTP",
            "MISSING",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
