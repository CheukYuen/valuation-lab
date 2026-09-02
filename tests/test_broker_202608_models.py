import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "yofc"))

import goldman_20260828_model as goldman  # noqa: E402
import morgan_stanley_20260823_model as morgan_stanley  # noqa: E402
import nomura_20260821_model as nomura  # noqa: E402


class Goldman20260828ModelTests(unittest.TestCase):
    def test_discounted_pe_path_and_implied_fx(self):
        result = goldman.reported_bridge()
        self.assertAlmostEqual(result["undiscounted_2030_value_rmb"], 350.108, places=3)
        self.assertAlmostEqual(result["discounted_target_value_rmb"], 255.995952, places=6)
        self.assertAlmostEqual(result["implied_cny_per_hkd"], 0.876698466, places=9)
        self.assertAlmostEqual(result["replayed_target_price_hkd"], 292.0, places=2)

    def test_visible_capm_inputs_do_not_equal_reported_coe(self):
        result = goldman.independent_bridge()
        self.assertAlmostEqual(result["capm_cost_of_equity"], 0.113, places=6)
        self.assertAlmostEqual(result["cost_of_equity_gap"], 0.003, places=6)
        self.assertAlmostEqual(
            result["capm_target_price_hkd_at_report_implied_fx"],
            289.645173,
            places=6,
        )

    def test_missing_inputs_are_not_presented_as_report_facts(self):
        audit = goldman.audit_summary()
        self.assertTrue(audit["discount_destination_conflict"])
        self.assertEqual(audit["target_multiple_basis_status"], "MISSING")
        self.assertEqual(audit["fx_source_status"], "MISSING")
        self.assertFalse(audit["full_target_price_independently_reproducible"])


class Nomura20260821ModelTests(unittest.TestCase):
    def test_pe_path_and_implied_fx(self):
        reported = nomura.reported_bridge()
        independent = nomura.independent_bridge()
        self.assertAlmostEqual(reported["target_value_rmb"], 231.075, places=3)
        self.assertAlmostEqual(reported["implied_cny_per_hkd"], 0.868703008, places=9)
        self.assertAlmostEqual(independent["replayed_target_price_hkd"], 266.0, places=2)

    def test_peer_and_fx_evidence_remain_incomplete(self):
        audit = nomura.audit_summary()
        self.assertEqual(audit["peer_median_basis_status"], "PARTIAL")
        self.assertEqual(audit["fx_source_status"], "MISSING")
        self.assertEqual(audit["full_annual_forecast_status"], "MISSING")
        self.assertFalse(audit["full_target_price_independently_reproducible"])


class MorganStanley20260823ModelTests(unittest.TestCase):
    def test_capm_and_visible_forecast_derivations(self):
        result = morgan_stanley.independent_bridge()
        self.assertAlmostEqual(result["capm_cost_of_equity"], 0.11, places=6)
        self.assertAlmostEqual(result["revenue_growth"][1], 0.921653651, places=9)
        self.assertAlmostEqual(result["net_margin"][2], 0.369137578, places=9)
        self.assertAlmostEqual(result["implied_share_counts_m"][1], 824.912088, places=6)

    def test_rim_target_price_is_not_fabricated(self):
        audit = morgan_stanley.audit_summary()
        self.assertEqual(audit["target_price_status"], "MISSING")
        self.assertFalse(audit["full_target_price_independently_reproducible"])
        with self.assertRaisesRegex(ValueError, "未披露期初账面价值"):
            morgan_stanley.rim_target_price_from_visible_inputs()

    def test_growth_assumptions_are_separate_from_revenue_forecast(self):
        reported = morgan_stanley.reported_bridge()
        result = morgan_stanley.independent_bridge()
        self.assertAlmostEqual(reported["medium_term_growth"], 0.15, places=6)
        self.assertAlmostEqual(reported["terminal_growth"], 0.02, places=6)
        self.assertNotAlmostEqual(result["revenue_growth"][1], 0.15, places=6)


class BrokerCaseDocumentTests(unittest.TestCase):
    def test_each_broker_method_explains_what_why_how_and_data(self):
        cases = [
            "04-JEFFERIES-20260722-CASE.md",
            "06-GOLDMAN-20260828-CASE.md",
            "07-NOMURA-20260821-CASE.md",
            "08-MORGAN-STANLEY-20260823-CASE.md",
        ]
        for name in cases:
            text = (ROOT / "docs" / "yofc" / name).read_text()
            for dimension in ["What：", "Why：", "How：", "Data："]:
                self.assertIn(dimension, text, f"{name} missing {dimension}")

    def test_each_new_case_preserves_method_and_missing_bridges(self):
        required = {
            "06-GOLDMAN-20260828-CASE.md": [
                "折现市盈率",
                "11.3%",
                "discount back to 2030E",
                "PARTIAL",
                "MISSING",
            ],
            "07-NOMURA-20260821-CASE.md": [
                "231.075",
                "WIND H股线缆公司",
                "经营预测边界",
                "MISSING",
            ],
            "08-MORGAN-STANLEY-20260823-CASE.md": [
                "剩余收益模型",
                "期初账面价值",
                "中期增长15%",
                "MISSING",
            ],
        }
        for name, phrases in required.items():
            text = (ROOT / "docs" / "yofc" / name).read_text()
            for phrase in phrases:
                self.assertIn(phrase, text, f"{name} missing {phrase}")

    def test_method_comparison_keeps_targets_separate(self):
        text = (
            ROOT / "docs" / "yofc" / "09-FOUR-BROKER-METHOD-COMPARISON.md"
        ).read_text()
        for phrase in [
            "153.74港元",
            "266港元",
            "230港元",
            "292港元",
            "15.57/35.21/56.75港元",
            "为什么不能平均目标价",
        ]:
            self.assertIn(phrase, text)

    def test_method_comparison_teaches_every_method_before_comparing_outputs(self):
        text = (
            ROOT / "docs" / "yofc" / "09-FOUR-BROKER-METHOD-COMPARISON.md"
        ).read_text()
        required_methods = [
            "SOTP：先拆业务，再加总价值",
            "P/B：为账面资本定价",
            "Forward P/E：为目标年度盈利定价",
            "Discounted P/E：先算远期价格，再折回目标年",
            "RIM：账面价值加超额回报",
            "FCFF DCF：把经营利润转成现金价值",
        ]
        for method in required_methods:
            self.assertIn(method, text)
        self.assertGreaterEqual(text.count("**What：是什么。**"), 6)
        self.assertGreaterEqual(text.count("**Why：为什么用。**"), 6)
        self.assertGreaterEqual(text.count("**How："), 6)
        self.assertGreaterEqual(text.count("**Data：用了什么。**"), 6)

    def test_industry_comparison_covers_required_dimensions_and_boundaries(self):
        text = (
            ROOT / "docs" / "yofc" / "10-FOUR-BROKER-INDUSTRY-COMPARISON.md"
        ).read_text()
        for phrase in [
            "ASP对比",
            "扩产和有效产能",
            "招标与运营商信息",
            "宣布扩产不等于",
            "集采最高限价",
            "HCF空芯光纤",
            "Capex与扩产现金成本",
        ]:
            self.assertIn(phrase, text)

    def test_case_index_and_source_registry_include_all_three_reports(self):
        readme = (ROOT / "docs" / "yofc" / "README.md").read_text()
        sources = (ROOT / "docs" / "yofc" / "DATA-SOURCES.md").read_text()
        for name in ["高盛", "野村", "摩根士丹利"]:
            self.assertIn(name, readme)
            self.assertIn(name, sources)
        for source_id in ["R2", "R3", "R4"]:
            self.assertIn(f"| {source_id} |", sources)


if __name__ == "__main__":
    unittest.main()
