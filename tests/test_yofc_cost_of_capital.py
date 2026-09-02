"""锁住长飞 WACC 推导的每一项输入，避免折现率再次退回“直接给定的数”。"""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "yofc"))

import cost_of_capital as cc  # noqa: E402

DOC_DCF = ROOT / "docs" / "yofc" / "02-FORECAST-AND-DCF.md"
DOC_SOURCES = ROOT / "docs" / "yofc" / "DATA-SOURCES.md"


class SnapshotTests(unittest.TestCase):
    def test_snapshot_carries_every_series_and_its_request(self):
        snapshot = cc.load_snapshot()
        expected = {
            "sh601869",
            "sh000300",
            "hk06869",
            "hkHSI",
            "sz300308",
            "sz002281",
            "sz300394",
        }
        self.assertEqual(set(snapshot["series"]), expected)
        for code, series in snapshot["series"].items():
            with self.subTest(series=code):
                # 每条序列都要能回到原始请求，否则快照就不是可复核证据。
                self.assertIn("request_param", series)
                self.assertGreater(len(series["close"]), 250)

    def test_a_share_series_is_dividend_adjusted(self):
        snapshot = cc.load_snapshot()
        self.assertEqual(snapshot["series"]["sh601869"]["kline_key"], "qfqweek")
        # H 股与两个指数没有前复权序列，文档已声明这一限制。
        self.assertEqual(snapshot["series"]["hk06869"]["kline_key"], "week")


class BetaRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = cc.own_beta()

    def test_main_beta_and_its_uncertainty(self):
        self.assertAlmostEqual(self.main.beta, 1.0522, places=4)
        self.assertAlmostEqual(self.main.r_squared, 0.0691, places=4)
        self.assertAlmostEqual(self.main.standard_error, 0.2418, places=4)
        self.assertEqual(self.main.observations, 257)

    def test_confidence_interval_is_wide_enough_to_matter(self):
        low, high = self.main.confidence_interval
        self.assertAlmostEqual(low, 0.5783, places=4)
        self.assertAlmostEqual(high, 1.5260, places=4)
        # 置信区间必须宽到足以改变结论，这正是文档要读者记住的事。
        self.assertGreater(cc.wacc(high) - cc.wacc(low), 0.06)

    def test_peer_betas_are_higher_than_the_company_itself(self):
        betas = sorted(item.beta for item in cc.peer_betas())
        self.assertAlmostEqual(cc.peer_median_beta(), 1.6846, places=4)
        for beta in betas:
            self.assertGreater(beta, self.main.beta)

    def test_regression_rejects_too_short_a_window(self):
        with self.assertRaises(ValueError):
            cc.regress_beta("sh601869", "sh000300", weeks=10)


class WaccTests(unittest.TestCase):
    def test_cost_of_debt_and_capital_weights(self):
        self.assertAlmostEqual(cc.pre_tax_cost_of_debt(), 0.026227, places=6)
        self.assertAlmostEqual(cc.market_value_of_equity(), 2054.48, places=1)
        self.assertAlmostEqual(cc.book_value_of_equity(), 203.80, places=2)
        market_debt_weight = cc.DEBT_2026H1 / (
            cc.market_value_of_equity() + cc.DEBT_2026H1
        )
        self.assertAlmostEqual(market_debt_weight, 0.044309, places=6)

    def test_headline_wacc_under_both_weight_conventions(self):
        self.assertAlmostEqual(cc.DERIVED_WACC, 0.104892, places=6)
        self.assertAlmostEqual(cc.wacc(weights="book"), 0.080816, places=6)

    def test_broker_input_range_brackets_the_main_caliber(self):
        low = cc.wacc(risk_free=cc.RISK_FREE_HIGH, equity_risk_premium=cc.EQUITY_RISK_PREMIUM_LOW)
        high = cc.wacc(risk_free=cc.RISK_FREE_LOW, equity_risk_premium=cc.EQUITY_RISK_PREMIUM_HIGH)
        self.assertAlmostEqual(low, 0.099739, places=6)
        self.assertAlmostEqual(high, 0.110044, places=6)
        self.assertLess(low, cc.DERIVED_WACC)
        self.assertLess(cc.DERIVED_WACC, high)

    def test_leverage_is_too_low_for_unlevering_to_matter(self):
        debt_to_equity = cc.DEBT_2026H1 / cc.market_value_of_equity()
        unlevered = cc.unlever(cc.own_beta().beta, debt_to_equity)
        self.assertLess(abs(unlevered / cc.own_beta().beta - 1), 0.04)

    def test_weights_argument_is_validated(self):
        with self.assertRaises(ValueError):
            cc.wacc(weights="target")


class DocumentContractTests(unittest.TestCase):
    def test_data_sources_register_the_price_series(self):
        text = DOC_SOURCES.read_text(encoding="utf-8")
        for marker in ("S19", "S20", "S21", "S22", "beta_20260824_snapshot.json"):
            self.assertIn(marker, text)

    def test_dcf_doc_still_flags_the_two_missing_capm_inputs(self):
        text = DOC_DCF.read_text(encoding="utf-8")
        self.assertIn("无风险利率和股权风险溢价仍然没有独立来源", text)
        self.assertIn("`PARTIAL`", text)


if __name__ == "__main__":
    unittest.main()
