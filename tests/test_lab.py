import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))

from bridge import bridge, fcff, per_share, with_dilution  # noqa: E402
from methods import bank_demo, multiples, spread  # noqa: E402
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


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = json.loads((ROOT / "lab/inputs/bridge.json").read_text())

    def test_default_inputs_reproduce_the_lesson_numbers(self):
        b = bridge(self.params)
        self.assertAlmostEqual(b["nopat"], 16.0)
        self.assertAlmostEqual(b["fcff"], 12.0)
        self.assertAlmostEqual(b["skipped_reinvestment"], 4.0)
        self.assertAlmostEqual(b["equity_value"], 170.0)
        self.assertAlmostEqual(b["per_share_basic"], 17.0)
        self.assertAlmostEqual(b["per_share_float_wrong"], 21.25)

    def test_released_working_capital_adds_cash(self):
        released = copy.deepcopy(self.params)
        released["working_capital_increase"] = -2.0
        self.assertAlmostEqual(fcff(released)["fcff"], 16.0)

    def test_missing_input_is_not_silently_zero(self):
        # 课程纪律：未知不等于零。缺 Capex 必须报错，不能按 0 继续算。
        incomplete = copy.deepcopy(self.params)
        del incomplete["capex"]
        with self.assertRaises(KeyError):
            fcff(incomplete)

    def test_skipping_the_capital_structure_bridge_has_no_fixed_direction(self):
        # DAY-2 反复强调不要背符号。EV÷股本 在净债务公司偏高、净现金公司偏低。
        net_debt = bridge(self.params)
        self.assertGreater(net_debt["net_debt"], 0)
        self.assertGreater(net_debt["ev_per_share"], net_debt["per_share_basic"])

        flipped = copy.deepcopy(self.params)
        flipped["cash"], flipped["debt"] = self.params["debt"], self.params["cash"]
        net_cash = bridge(flipped)
        self.assertLess(net_cash["net_debt"], 0)
        self.assertLess(net_cash["ev_per_share"], net_cash["per_share_basic"])

    def test_the_main_case_has_no_dilution_so_basic_shares_are_correct(self):
        # 课文主线按无稀释处理，17 元是正确答案；脚本不能反过来把它标成错误。
        s = per_share(self.params)
        self.assertAlmostEqual(s["per_share_basic"], s["per_share_diluted"])
        self.assertAlmostEqual(s["per_share_basic"], s["per_share_if_converted"])

    def test_double_counting_a_convertible_lands_below_both_legal_paths(self):
        s = per_share(with_dilution(self.params))
        self.assertLess(s["per_share_double_counted"], s["per_share_diluted"])
        self.assertLess(s["per_share_double_counted"], s["per_share_if_converted"])
        # 两条合法路径不相等，所以材料必须说明自己走的是哪一条
        self.assertNotAlmostEqual(s["per_share_diluted"], s["per_share_if_converted"], places=6)
        # 忽略稀释的方向与重复计算相反，别把"稀释一定让每股变低"当自查规则
        self.assertGreater(s["per_share_basic"], s["per_share_diluted"])

    def test_treasury_shares_cannot_swallow_the_whole_denominator(self):
        broken = copy.deepcopy(self.params)
        broken["treasury_shares"] = broken["total_shares"]
        with self.assertRaises(ValueError):
            per_share(broken)


class MethodsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = json.loads((ROOT / "lab/inputs/methods.json").read_text())

    def test_four_methods_disagree_by_a_visible_margin(self):
        s = spread(self.params)
        self.assertGreater(s["ratio"], 1.0)
        self.assertEqual(len(set(multiples(self.params))), 4)

    def test_treating_deposits_as_debt_breaks_the_bank_valuation(self):
        b = bank_demo(self.params)
        self.assertLess(b["ev_ebitda_with_deposits"], 0)
        self.assertGreater(b["ev_ebitda_without_deposits"], 0)
        self.assertGreater(b["pb"], 0)


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
