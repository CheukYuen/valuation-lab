"""锁住 docs/yofc/valuation_model.py 的口径与分支。

重点不是复述模型内部实现，而是把文档里公开引用的数字钉住：三情景每股价值、
两套终值口径、两套 EV 倍数口径，以及终值 ROIC 的期间约定。
"""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "yofc"))

import valuation_model as vm  # noqa: E402


DOC_DCF = ROOT / "docs" / "yofc" / "02-FORECAST-AND-DCF.md"
DOC_RELATIVE = ROOT / "docs" / "yofc" / "03-RELATIVE-REVERSE-PEG.md"


class TerminalModeRoicWaccTests(unittest.TestCase):
    """默认口径 ①：终值新增资本 ROIC 与 WACC 收敛。"""

    def test_default_mode_is_roic_wacc(self):
        self.assertEqual(vm.dcf(vm.SCENARIOS["base"])["terminal_mode"], "roic_wacc")

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

    def test_target_roic_equals_wacc(self):
        for key, scenario in vm.SCENARIOS.items():
            with self.subTest(scenario=key):
                self.assertAlmostEqual(
                    vm.dcf(scenario)["terminal_target_roic"], scenario.wacc, places=10
                )

    def test_terminal_value_collapses_to_nopat_over_wacc(self):
        """ROIC=WACC 时 `NOPAT×(1−g/WACC)/(WACC−g)` 恒等于 `NOPAT/WACC`。"""
        for key, scenario in vm.SCENARIOS.items():
            with self.subTest(scenario=key):
                result = vm.dcf(scenario)
                last_revenue = result["rows"][-1]["revenue"]
                terminal_nopat = (
                    last_revenue
                    * (1 + scenario.terminal_growth)
                    * scenario.terminal_margin
                    * (1 - vm.NORMALIZED_TAX_RATE)
                )
                self.assertAlmostEqual(
                    result["terminal_value"], terminal_nopat / scenario.wacc, places=6
                )


class TerminalModeTurnoverTests(unittest.TestCase):
    """口径 ②：终值继续沿用显性期资本周转率。"""

    def test_documented_values_per_share(self):
        expected = {"bear": 12.03, "base": 39.37, "bull": 86.85}
        for key, value in expected.items():
            with self.subTest(scenario=key):
                self.assertAlmostEqual(
                    vm.dcf(vm.SCENARIOS[key], terminal_mode="turnover")[
                        "value_per_share_cny"
                    ],
                    value,
                    places=2,
                )

    def test_incremental_turnover_stays_at_explicit_period_rate(self):
        """口径 ② 的意义就是边界上不再跳变：增量周转率必须等于 0.92x。"""
        for key, scenario in vm.SCENARIOS.items():
            with self.subTest(scenario=key):
                result = vm.dcf(scenario, terminal_mode="turnover")
                self.assertAlmostEqual(
                    result["terminal_incremental_turnover"],
                    scenario.capital_turnover,
                    places=10,
                )

    def test_roic_wacc_mode_does_jump_away_from_explicit_turnover(self):
        """对照组：口径 ① 的增量周转率确实偏离 0.92x，这是文档披露的跳变。"""
        jumps = {
            key: vm.dcf(scenario)["terminal_incremental_turnover"]
            for key, scenario in vm.SCENARIOS.items()
        }
        self.assertAlmostEqual(jumps["bear"], 1.61, places=2)
        self.assertAlmostEqual(jumps["base"], 0.69, places=2)
        self.assertAlmostEqual(jumps["bull"], 0.46, places=2)


class TerminalRoicPeriodConventionTests(unittest.TestCase):
    """稳定期持续 ROIC 与边界 ROIC 是两个数，期间不能混用。"""

    def test_sustained_roic_uses_same_period_convention(self):
        """`g × 终值NOPAT ÷ (1+g) ÷ 终值再投资`，与显性期同一条期间约定。"""
        expected = {"bear": 0.0589, "base": 0.1178, "bull": 0.1546}
        for key, value in expected.items():
            with self.subTest(scenario=key):
                scenario = vm.SCENARIOS[key]
                result = vm.dcf(scenario, terminal_mode="turnover")
                self.assertAlmostEqual(
                    result["terminal_sustained_roic"], value, places=4
                )
                last_revenue = result["rows"][-1]["revenue"]
                terminal_nopat = (
                    last_revenue
                    * (1 + scenario.terminal_growth)
                    * scenario.terminal_margin
                    * (1 - vm.NORMALIZED_TAX_RATE)
                )
                self.assertAlmostEqual(
                    result["terminal_sustained_roic"],
                    scenario.terminal_growth
                    * terminal_nopat
                    / (1 + scenario.terminal_growth)
                    / result["terminal_reinvestment"],
                    places=10,
                )

    def test_boundary_roic_is_negative_because_terminal_margin_drops(self):
        """终值利润率下调使 NOPAT 减少，边界 ROIC 必为负，不能拿来和 WACC 比。"""
        for key, scenario in vm.SCENARIOS.items():
            with self.subTest(scenario=key):
                result = vm.dcf(scenario, terminal_mode="turnover")
                self.assertLess(scenario.terminal_margin, scenario.ebit_margin[-1])
                self.assertLess(result["terminal_boundary_roic"], 0)
                self.assertNotAlmostEqual(
                    result["terminal_boundary_roic"],
                    result["terminal_sustained_roic"],
                    places=2,
                )

    def test_roic_wacc_mode_sustained_roic_is_wacc_over_one_plus_g(self):
        """已知接缝：口径 ① 用滞后约定，按同期约定复算会低一个 (1+g)。"""
        for key, scenario in vm.SCENARIOS.items():
            with self.subTest(scenario=key):
                result = vm.dcf(scenario)
                self.assertAlmostEqual(
                    result["terminal_sustained_roic"],
                    scenario.wacc / (1 + scenario.terminal_growth),
                    places=10,
                )


class TerminalCashFlowGrowthTests(unittest.TestCase):
    """Gordon 终值成立的前提：终值现金流此后按 g 稳定增长。"""

    def test_perpetuity_replicates_gordon_value(self):
        for mode in ("roic_wacc", "turnover"):
            for key, scenario in vm.SCENARIOS.items():
                with self.subTest(mode=mode, scenario=key):
                    result = vm.dcf(scenario, terminal_mode=mode)
                    g = scenario.terminal_growth
                    wacc = scenario.wacc
                    # 逐年按 g 增长的现金流折现，收敛到闭式解。
                    brute = sum(
                        result["terminal_fcff"]
                        * (1 + g) ** n
                        / (1 + wacc) ** (n + 1)
                        for n in range(4000)
                    )
                    self.assertAlmostEqual(
                        brute, result["terminal_value"], delta=result["terminal_value"] * 1e-6
                    )


class InputValidationTests(unittest.TestCase):
    def test_invalid_terminal_mode_raises(self):
        with self.assertRaises(ValueError):
            vm.dcf(vm.SCENARIOS["base"], terminal_mode="whatever")

    def test_wacc_must_exceed_terminal_growth(self):
        with self.assertRaises(ValueError):
            vm.dcf(vm.SCENARIOS["base"], wacc=0.02)

    def test_tax_rate_bounds(self):
        with self.assertRaises(ValueError):
            vm.dcf(vm.SCENARIOS["base"], tax_rate=1.0)


class EvMultipleCaliberTests(unittest.TestCase):
    """两套 EV 口径并列，任何一套都不得被悄悄换掉。"""

    def test_core_caliber_denominators(self):
        self.assertAlmostEqual(vm.LTM_CORE_EBIT, 42.86, places=2)
        self.assertAlmostEqual(vm.LTM_CORE_EBITDA, 42.86 + 12.09, places=2)
        self.assertAlmostEqual(vm.LTM_REPORTED_EBIT, 47.34, places=2)
        self.assertAlmostEqual(vm.LTM_REPORTED_EBITDA, 47.34 + 12.09, places=2)

    def test_combined_market_cap(self):
        self.assertAlmostEqual(vm.actual_combined_market_cap(), 2054.48, places=1)

    def test_core_caliber_multiples(self):
        multiples = vm.relative_multiples(vm.actual_combined_market_cap())
        self.assertAlmostEqual(multiples["pe"], 59.7, places=1)
        self.assertAlmostEqual(multiples["pb"], 12.6, places=1)
        self.assertAlmostEqual(multiples["ev_ebit"], 48.7, places=1)
        self.assertAlmostEqual(multiples["ev_ebitda"], 38.0, places=1)

    def test_reported_caliber_multiples(self):
        reported = vm.reported_caliber_ev_multiples(vm.actual_combined_market_cap())
        self.assertAlmostEqual(reported["ev_ebit"], 44.1, places=1)
        self.assertAlmostEqual(reported["ev_ebitda"], 35.1, places=1)

    def test_reported_caliber_is_lower_because_denominator_is_larger(self):
        equity = vm.actual_combined_market_cap()
        core = vm.relative_multiples(equity)
        reported = vm.reported_caliber_ev_multiples(equity)
        self.assertGreater(core["ev_ebit"], reported["ev_ebit"])
        self.assertGreater(core["ev_ebitda"], reported["ev_ebitda"])

    def test_single_price_implied_multiples(self):
        h_equity = vm.H_PRICE_HKD * vm.HKD_TO_CNY * vm.FULLY_DILUTED_SHARES_YI
        a_equity = vm.A_PRICE_CNY * vm.FULLY_DILUTED_SHARES_YI
        self.assertAlmostEqual(vm.relative_multiples(h_equity)["ev_ebit"], 24.3, places=1)
        self.assertAlmostEqual(vm.relative_multiples(a_equity)["ev_ebit"], 74.0, places=1)


class PeerMedianMechanicalTests(unittest.TestCase):
    """跨口径机械示意：两组数都要留着，缺一组就会被当成唯一答案。"""

    def test_core_caliber_values(self):
        implied = vm.peer_median_implied_values()
        self.assertAlmostEqual(implied["pe"], 487.40, places=2)
        self.assertAlmostEqual(implied["pb"], 480.30, places=2)
        self.assertAlmostEqual(implied["ev_ebit"], 533.78, places=2)
        self.assertAlmostEqual(implied["ev_ebitda"], 503.64, places=2)

    def test_reported_caliber_values(self):
        implied = vm.peer_median_implied_values_reported_caliber()
        self.assertAlmostEqual(implied["ev_ebit"], 590.00, places=2)
        self.assertAlmostEqual(implied["ev_ebitda"], 545.04, places=2)


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
    """文档里公开引用的数字必须与模型输出一致。"""

    @classmethod
    def setUpClass(cls):
        cls.dcf_doc = DOC_DCF.read_text(encoding="utf-8")
        cls.relative_doc = DOC_RELATIVE.read_text(encoding="utf-8")

    def _assert_in_doc(self, doc, text):
        self.assertIn(text, doc, f"文档中找不到模型输出的数字：{text}")

    def test_headline_and_turnover_values_appear_in_dcf_doc(self):
        for key in ("bear", "base", "bull"):
            scenario = vm.SCENARIOS[key]
            self._assert_in_doc(
                self.dcf_doc, f"{vm.dcf(scenario)['value_per_share_cny']:.2f}"
            )
            self._assert_in_doc(
                self.dcf_doc,
                f"{vm.dcf(scenario, terminal_mode='turnover')['value_per_share_cny']:.2f}",
            )

    def test_sustained_and_boundary_roic_appear_in_dcf_doc(self):
        for key in ("bear", "base", "bull"):
            result = vm.dcf(vm.SCENARIOS[key], terminal_mode="turnover")
            self._assert_in_doc(self.dcf_doc, f"{result['terminal_sustained_roic']:.2%}")
            self._assert_in_doc(
                self.dcf_doc, f"{result['terminal_boundary_roic']:.2%}".replace("-", "−")
            )

    def test_both_ev_calibers_appear_in_relative_doc(self):
        equity = vm.actual_combined_market_cap()
        core = vm.relative_multiples(equity)
        reported = vm.reported_caliber_ev_multiples(equity)
        for value in (core["ev_ebit"], core["ev_ebitda"]):
            self._assert_in_doc(self.relative_doc, f"{value:.1f}")
        for value in (reported["ev_ebit"], reported["ev_ebitda"]):
            self._assert_in_doc(self.relative_doc, f"{value:.1f}")

    def test_peer_mechanical_values_appear_in_relative_doc(self):
        for value in vm.peer_median_implied_values().values():
            self._assert_in_doc(self.relative_doc, f"{value:.2f}")
        for value in vm.peer_median_implied_values_reported_caliber().values():
            self._assert_in_doc(self.relative_doc, f"{value:.2f}")

    def test_relative_doc_marks_both_calibers_partial(self):
        self.assertIn("两个数都标 `PARTIAL`", self.relative_doc)
        self.assertNotIn("与 EV 桥完全一致", self.relative_doc)

    def test_dcf_doc_does_not_reuse_superseded_roic_numbers(self):
        """口径 ② 的持续 ROIC 曾按滞后约定误算为 6.01/12.07/15.92，不得回潮。"""
        for stale in ("6.01%", "12.07%", "15.92%"):
            self.assertNotIn(
                stale, self.dcf_doc, f"文档仍在使用被替换的滞后约定 ROIC：{stale}"
            )


if __name__ == "__main__":
    unittest.main()
