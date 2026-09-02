"""锁住 2026-08-28 反向 DCF 的输出契约。

重点不是“反解出多少”，而是：越界时必须给出可行域天花板与缺口，
单变量解只作为刻度展示。
"""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "yofc"))

import reverse_dcf_20260828 as reverse  # noqa: E402
import valuation_model as vm  # noqa: E402


DOC = ROOT / "docs" / "yofc" / "11-REVERSE-DCF-20260828.md"


class TestYofcReverseDcf20260828(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = reverse.calculate()

    def test_market_value_and_enterprise_value(self):
        self.assertAlmostEqual(self.result["target_equity"], 2337.204081, places=6)
        self.assertAlmostEqual(
            self.result["target_enterprise_value"], 2371.171683, places=6
        )

    def test_headline_gap_to_base_case(self):
        self.assertAlmostEqual(self.result["base_equity_value"], 252.607730, places=6)
        self.assertAlmostEqual(self.result["base_value_per_share"], 30.51, places=2)
        self.assertAlmostEqual(self.result["market_price_per_share"], 282.30, places=2)
        self.assertAlmostEqual(self.result["market_to_base_multiple"], 9.2523, places=4)

    def test_feasibility_ceiling_reports_no_solution_and_gap(self):
        ceiling = self.result["feasibility"]
        self.assertFalse(ceiling["feasible"])
        self.assertAlmostEqual(ceiling["ceiling_equity_value"], 1501.7637, places=4)
        self.assertAlmostEqual(ceiling["ceiling_enterprise_value"], 1507.470536, places=6)
        self.assertAlmostEqual(ceiling["gap_ratio"], -0.35745, places=5)
        self.assertLess(ceiling["ceiling_equity_value"], ceiling["target_equity"])
        # 盒子里其他条件全部保留、只再松开利润率，两种口径都高于 2026H1 报表口径 39.52%。
        # 口径一：显性期与终值利润率同步抬高。
        self.assertAlmostEqual(ceiling["required_margin_in_box"], 0.406724, places=6)
        # 口径二：只抬高显性期，终值固定在盒子上界 25%。
        self.assertAlmostEqual(
            ceiling["required_margin_in_box_terminal_fixed"], 1.021213, places=6
        )
        for key in ("required_margin_in_box", "required_margin_in_box_terminal_fixed"):
            with self.subTest(caliber=key):
                self.assertGreater(ceiling[key], 0.3952)
        # 终值占盒内 EV 八成，所以钉住终值会让所需利润率高得多。
        self.assertGreater(
            ceiling["required_margin_in_box_terminal_fixed"],
            ceiling["required_margin_in_box"],
        )

    def test_three_pricing_calibers_all_outside_feasible_region(self):
        calibers = self.result["calibers"]
        self.assertEqual(
            list(calibers), ["全按 H 股价", "实际 A+H 混合", "全按 A 股价"]
        )
        expected = {
            "全按 H 股价": (1219.554677, 0.713640),
            "实际 A+H 混合": (2337.204081, 1.327909),
            "全按 A 股价": (3496.740014, 1.965200),
        }
        for name, (equity, margin) in expected.items():
            with self.subTest(caliber=name):
                self.assertAlmostEqual(calibers[name]["equity_value"], equity, places=6)
                self.assertAlmostEqual(
                    calibers[name]["implied_constant_margin"], margin, places=6
                )
                # 即使最便宜的 H 股口径也高于严格核心口径 34.57%。
                self.assertGreater(calibers[name]["implied_constant_margin"], 0.3457)

    def test_constant_margin_path_is_closed_form_and_linear(self):
        path = self.result["margin_path"]
        self.assertAlmostEqual(path["intercept"], -78.898496, places=6)
        self.assertAlmostEqual(path["slope"], 1819.478530, places=6)
        self.assertAlmostEqual(path["margin"], 1.327909364, places=9)
        self.assertAlmostEqual(path["residual"], 0.0, places=9)
        # 闭式解必须与线性关系完全一致，而不是近似。
        self.assertAlmostEqual(
            path["intercept"] + path["slope"] * path["margin"],
            self.result["target_equity"],
            places=9,
        )

    def test_growth_path_is_labelled_as_terminal_seam_artifact(self):
        path = self.result["growth_path"]
        self.assertAlmostEqual(path["growth"], 1.204072039, places=9)
        self.assertAlmostEqual(path["result"]["rows"][-1]["revenue"], 10142.93254, places=5)
        # 显性期 FCFF 全程为负，终值占 EV 超过 100%：这不是可信经营世界。
        for row in path["result"]["rows"]:
            self.assertLess(row["fcff"], 0)
        self.assertGreater(path["result"]["terminal_share"], 1.0)
        # 接缝本身：显性期 0.92x vs 终值隐含 0.69x。
        self.assertAlmostEqual(path["explicit_capital_turnover"], 0.92, places=2)
        self.assertAlmostEqual(path["terminal_incremental_turnover"], 0.80, places=2)
        self.assertNotAlmostEqual(
            path["terminal_incremental_turnover"],
            path["explicit_capital_turnover"],
            places=2,
        )

    def test_nci_market_sensitivity_strengthens_conclusion(self):
        nci = self.result["nci_sensitivity"]
        self.assertAlmostEqual(nci["target_enterprise_value"], 2905.268486, places=6)
        self.assertAlmostEqual(nci["target_enterprise_value_ratio"], 0.225246, places=6)
        self.assertAlmostEqual(nci["implied_margin"], 1.621453, places=6)
        # 方向必须是让隐含条件更极端。
        self.assertGreater(
            nci["implied_margin"], self.result["implied_constant_margin"]
        )

    def test_reverse_solutions_reconcile_to_observed_equity(self):
        target = self.result["target_equity"]
        self.assertAlmostEqual(
            self.result["margin_result"]["equity_value"], target, places=6
        )
        self.assertAlmostEqual(
            self.result["growth_result"]["equity_value"], target, places=6
        )


class TestSharedSolver(unittest.TestCase):
    def test_solver_rejects_target_outside_reachable_range(self):
        with self.assertRaises(ValueError):
            vm.solve_monotone(100.0, lambda x: x, 0.0, 10.0)

    def test_solver_rejects_non_monotone_function(self):
        with self.assertRaises(ValueError):
            vm.solve_monotone(0.5, lambda x: (x - 0.5) ** 2 + x * 1e-9, -1.0, 1.0)

    def test_solver_matches_closed_form_margin_solution(self):
        with reverse.pricing_date_timing():
            target = reverse.actual_mixed_equity_value()
            searched = vm.solve_monotone(
                target,
                lambda m: vm.dcf(vm.constant_margin_scenario(m))["equity_value"],
                0.0,
                2.0,
            )
            closed = vm.reverse_constant_margin_for_equity(target)
        self.assertAlmostEqual(searched, closed, places=9)


class TestDocumentContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_doc_leads_with_gap_and_ceiling(self):
        for value in (
            "9.25×",
            "1,501.76",
            "−835.44（−35.7%）",
            "无经济可行解",
            "40.67%",
            "102.12%",
        ):
            self.assertIn(value, self.doc)

    def test_doc_carries_three_calibers(self):
        for value in ("71.36%", "132.79%", "196.52%"):
            self.assertIn(value, self.doc)

    def test_doc_demotes_growth_path(self):
        self.assertIn("终值接缝演示，不作为结论", self.doc)
        self.assertIn("0.80x", self.doc)

    def test_doc_no_longer_claims_bisection_for_margin(self):
        self.assertIn("闭式解", self.doc)
        self.assertNotIn("重复200次", self.doc)


if __name__ == "__main__":
    unittest.main()
