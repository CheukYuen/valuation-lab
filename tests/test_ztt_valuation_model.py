import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "ztt"))

import morgan_stanley_20260714_model as model  # noqa: E402


class MorganStanley20260714ModelTests(unittest.TestCase):
    def test_cost_of_equity_closes_but_visible_wacc_does_not(self):
        result = model.independent_bridge()
        self.assertAlmostEqual(result["cost_of_equity"], 0.1055, places=6)
        self.assertAlmostEqual(result["visible_wacc"], 0.0949, places=6)
        self.assertAlmostEqual(result["wacc_gap"], 0.0018, places=6)

    def test_visible_forecast_derivations(self):
        result = model.independent_bridge()
        self.assertAlmostEqual(result["revenue_growth"][1], 0.190095238, places=9)
        self.assertAlmostEqual(result["ebitda_margin"][3], 0.155309315, places=9)
        self.assertAlmostEqual(result["net_margin"][1], 0.102768886, places=9)
        self.assertAlmostEqual(result["implied_share_counts_m"][1], 3415.425532, places=6)

    def test_reported_target_bridge_is_mechanical_not_dcf_reproduction(self):
        result = model.independent_bridge()
        self.assertAlmostEqual(result["reported_upside"], 0.242240373, places=9)
        self.assertAlmostEqual(result["target_equity_value_rmb_m"], 181673.99, places=2)
        self.assertAlmostEqual(result["mechanical_net_cash_rmb_m"], 11517, places=2)

    def test_missing_fcff_is_not_fabricated(self):
        audit = model.audit_summary()
        self.assertEqual(audit["annual_fcff_2027_2037_status"], "MISSING")
        self.assertFalse(audit["full_target_price_independently_reproducible"])
        with self.assertRaisesRegex(ValueError, "逐年FCFF"):
            model.dcf_target_price_from_visible_inputs()


class ZTTDocumentTests(unittest.TestCase):
    def test_case_explains_what_why_how_and_data(self):
        text = (ROOT / "docs" / "ztt" / "01-MORGAN-STANLEY-20260714-CASE.md").read_text()
        for phrase in ["What：", "Why：", "How：", "Data：", "9.49%", "9.67%", "MISSING"]:
            self.assertIn(phrase, text)

    def test_workflow_covers_research_layers_and_evidence_boundaries(self):
        text = (ROOT / "docs" / "FIBER-MINIMUM-VIABLE-RESEARCH-WORKFLOW.md").read_text()
        for phrase in [
            "终端场景/系统变化",
            "行业利润池表",
            "产业链地图",
            "公司利润桥",
            "预期与估值表",
            "证据与验证表",
            "宣布产能不等于",
            "反向DCF",
            "行业观测值可以共用，公司影响函数不能共用",
            "Agent每次运行的状态流",
            "AGENT-ASSUMPTION",
            "停止规则",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
