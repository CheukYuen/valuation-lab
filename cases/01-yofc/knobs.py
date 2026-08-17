#!/usr/bin/env python3
"""在冻结的长飞估值模型上拧旋钮。

    python3 cases/01-yofc/knobs.py

这个脚本不改动 frozen/ 里的任何文件，只在内存里改参数重算。
它复现的是 answer-key.md 里的量化结论——你可以自己验证，不必相信答案。
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE / "frozen"
sys.path.insert(0, str(FROZEN))

from calculate import forward_dcf, reverse_ev, solve_bisection  # noqa: E402

DATA = json.loads((FROZEN / "valuation-inputs.json").read_text())
REMAIN = DATA["timing"]["remaining_2026_days"] / DATA["timing"]["days_in_year"]
CAP = DATA["capital_structure"]
BRIDGE = (CAP["interest_bearing_debt_including_lease_liabilities"]
          + CAP["minority_interest"]
          - CAP["cash_and_cash_equivalents_proxy"])
NONOP = (CAP["trading_financial_assets_excluded_from_base_bridge"]
         + CAP["long_term_equity_investments_excluded_from_base_bridge"]
         + CAP["other_equity_investments_excluded_from_base_bridge"])
MARKET_EQUITY_YI = 1903.996  # A/H 实际分类市场权益，2026-08-14


def equity_yi(scenario, wacc=0.066, tax=0.20):
    """返回普通股权益价值，单位亿元。"""
    ev = forward_dcf(scenario, tax, wacc, REMAIN)["enterprise_value_bn"]
    return (ev - BRIDGE) * 10


def main():
    print("=" * 74)
    print("实验 0 · 三情景基准（WACC 6.6%，税率 20%）")
    print("=" * 74)
    for name in ["bear", "base", "bull"]:
        s = DATA["scenarios"][name]
        r = forward_dcf(s, 0.20, 0.066, REMAIN)
        print(f"  {name:<6}股权 {equity_yi(s):>9.1f} 亿   终值占 EV {r['terminal_value_share_of_ev']:>6.1%}"
              f"   2032 利润率 {s['ebit_margin'][-1]:>6.2%}")
    print(f"  市场   实际分类市场权益 {MARKET_EQUITY_YI:>9.1f} 亿（2026-08-14 A/H 合计）")

    bull = DATA["scenarios"]["bull"]
    b0 = equity_yi(bull)
    print()
    print("=" * 74)
    print("实验 1 · Bull 情景旋钮：哪个假设在决定这个数")
    print("=" * 74)
    rows = [
        ("WACC 6.6% -> 8.0%", equity_yi(bull, wacc=0.08)),
    ]
    s = copy.deepcopy(bull); s["terminal_growth"] = 0.015
    rows.append(("永续增长 2.5% -> 1.5%", equity_yi(s)))
    s = copy.deepcopy(bull); s["ebit_margin"] = bull["ebit_margin"][:-1] + [0.24]
    rows.append(("2032 利润率 28% -> 24%", equity_yi(s)))
    s = copy.deepcopy(bull); s["revenue_bn"] = [x * 1.10 for x in bull["revenue_bn"]]
    rows.append(("整整七年收入全部 +10%", equity_yi(s)))
    s = copy.deepcopy(bull); s["terminal_roic"] = 0.10
    rows.append(("终值 ROIC 12.5% -> 10%", equity_yi(s)))

    print(f"  {'基准':<26}{b0:>9.1f} 亿")
    for label, v in rows:
        print(f"  {label:<26}{v:>9.1f} 亿   {v / b0 - 1:>+7.1%}")
    print()
    print("  注意第 4 行：把辛苦预测的七年收入整体抬高 10%，只值 +10.9%；")
    print("  而研报正文一句不提的折现率动 1.4 个百分点，抹掉 24%。")

    print()
    print("=" * 74)
    print("实验 2 · 把整叠保守选择反过来，结论还站得住吗")
    print("=" * 74)
    print("  原模型的保守选择：税率 20%（券商隐含 15.7%）、年末折现、45.87 亿金融/股权投资不从 EV 扣除")
    print()
    print(f"  {'情景':<8}{'原始':>10}{'税率15.7%':>12}{'+期中折现':>12}{'+扣非经营':>12}")
    for name in ["bear", "base", "bull"]:
        s = DATA["scenarios"][name]
        for w in [0.066, 0.060]:
            e0 = equity_yi(s, wacc=w)
            e1 = equity_yi(s, wacc=w, tax=0.157)
            e2 = e1 * (1 + w) ** 0.5
            e3 = e2 + NONOP * 10
            print(f"  {name + '@' + format(w, '.3f'):<8}{e0:>10.1f}{e1:>12.1f}{e2:>12.1f}{e3:>12.1f}")
    print()
    print(f"  这组已测试的乐观组合（bull@6.0% + 全部反转）仍低于市场 {MARKET_EQUITY_YI:.1f} 亿。")
    print("  该方向在本实验中未翻转，但余量只有约 5%；这不能覆盖尚未测试或无法确认的假设。")

    print()
    print("=" * 74)
    print("实验 3 · 反向 DCF 的现金转化口径（本案例最重要的缺陷）")
    print("=" * 74)
    rev = DATA["reverse_dcf"]
    bear_fcff = forward_dcf(DATA["scenarios"]["bear"], 0.20, 0.066, REMAIN)
    early = bear_fcff["fcff_bn"][:2]
    print("  正向模型自己产出的 FCFF/NOPAT（显性期逐年）：")
    for name in ["bear", "base", "bull"]:
        r = forward_dcf(DATA["scenarios"][name], 0.20, 0.066, REMAIN)
        ratios = [f / (e * 0.8) for f, e in zip(r["fcff_bn"], r["ebit_bn"])]
        print(f"    {name:<6}{[round(x, 2) for x in ratios]}")
    print("  反向模型却把它写死成 0.80。改成与正向一致，市场隐含要求全线下移：")
    print()
    targets = {"H 股等价": 939.873 / 10 + BRIDGE,
               "实际分类": 1903.996 / 10 + BRIDGE,
               "A 股等价": 2919.243 / 10 + BRIDGE}
    print(f"  {'现金转化':>10} " + " ".join(f"{k:>10}" for k in targets))
    for cc in [0.8, 0.9, 1.0, 1.1]:
        r = dict(rev)
        r["fcff_to_nopat_ratio"] = cc
        cells = []
        for target in targets.values():
            m = solve_bisection(
                target,
                lambda margin: reverse_ev(margin, r["steady_revenue_bn"], r, early, 0.066, REMAIN),
                0.0, 3.0)
            cells.append(f"{m * 100:9.1f}%" if m is not None else f"{'无解':>10}")
        mark = "  <- 原模型" if cc == 0.8 else ""
        print(f"  {cc:>10.2f} " + " ".join(cells) + mark)
    print()
    print("  报告里最可引用的那句『H 股要求约 26.4%，处于 Base 20% 与 Bull 28% 之间』")
    print("  是一句跨口径比较：26.4% 出自一套现金转化约定，20%/28% 出自另一套。")


if __name__ == "__main__":
    main()
