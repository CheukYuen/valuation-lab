#!/usr/bin/env python3
"""最小 DCF：五个数决定一个价值。

    python3 lab/mini_dcf.py                     使用 lab/inputs/simple.json
    python3 lab/mini_dcf.py 我的输入.json        使用自己的输入

输出不是"这家公司值多少"，而是"哪个假设在决定这个数"。
弹性 = 价值变动百分比 ÷ 输入变动百分比。绝对值越大，这个输入的权力越大。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "inputs" / "simple.json"

# 这五个键是本教学模型的控制杆；真实 DCF 会把它们拆成更细的经营输入。
FIVE = ["base_fcf", "growth", "years", "terminal_growth", "discount_rate"]


def value(p):
    """五个数 -> 企业价值、股权价值、终值占比。"""
    r = p["discount_rate"]
    tg = p["terminal_growth"]
    if r <= tg:
        raise ValueError(f"折现率 {r:.4f} 必须大于永续增长 {tg:.4f}，否则终值公式发散")

    n = int(p["years"])
    flows = [p["base_fcf"] * (1 + p["growth"]) ** t for t in range(1, n + 1)]
    explicit_pv = sum(f / (1 + r) ** t for t, f in enumerate(flows, start=1))

    terminal_value = flows[-1] * (1 + tg) / (r - tg)
    terminal_pv = terminal_value / (1 + r) ** n

    ev = explicit_pv + terminal_pv
    return {
        "flows": flows,
        "explicit_pv": explicit_pv,
        "terminal_value": terminal_value,
        "terminal_pv": terminal_pv,
        "terminal_share": (terminal_pv / ev) if ev else 0.0,
        "enterprise_value": ev,
        "equity_value": ev - p["net_debt"],
    }


def elasticity(p, bump=0.01):
    """每个输入相对上调 bump，看股权价值动多少。返回 (名称, 弹性) 按绝对值排序。"""
    base = value(p)["equity_value"]
    out = []
    for key in FIVE:
        q = dict(p)
        q[key] = p[key] * (1 + bump)
        if key == "years":
            continue  # 年数是整数，单独在下面处理
        try:
            moved = value(q)["equity_value"]
        except ValueError:
            out.append((key, None))
            continue
        out.append((key, (moved / base - 1) / bump))
    return sorted(out, key=lambda kv: -abs(kv[1] if kv[1] is not None else 0))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    p = json.loads(path.read_text())
    unit = p.get("unit", "亿元")

    missing = [k for k in FIVE + ["net_debt"] if k not in p]
    if missing:
        raise SystemExit(f"输入缺少：{missing}")

    v = value(p)

    print(f"输入：{path}")
    print()
    print("五个数")
    print(f"  起点自由现金流      {p['base_fcf']:>10.2f} {unit}")
    print(f"  显性期年增长        {p['growth']:>10.2%}")
    print(f"  显性期年数          {int(p['years']):>10d} 年")
    print(f"  永续增长            {p['terminal_growth']:>10.2%}")
    print(f"  折现率              {p['discount_rate']:>10.2%}")
    print(f"  （净债务）          {p['net_debt']:>10.2f} {unit}")
    print()
    print("结果")
    print(f"  显性期现值          {v['explicit_pv']:>10.2f} {unit}")
    print(f"  终值现值            {v['terminal_pv']:>10.2f} {unit}")
    print(f"  企业价值            {v['enterprise_value']:>10.2f} {unit}")
    print(f"  股权价值            {v['equity_value']:>10.2f} {unit}")
    print(f"  终值占企业价值      {v['terminal_share']:>10.1%}   <- 占比较高时重点检查远期假设，不自动等于模型失效")
    print()
    print("弹性排序（输入 +1%，股权价值变动几个 %）")
    for name, e in elasticity(p):
        bar = "#" * min(40, int(abs(e) * 6))
        print(f"  {name:<18}{e:>8.2f}  {bar}")
    print()
    print("  读法一：起点现金流对『企业价值』的弹性恒为 1.00，它是尺子。这里显示 "
          f"{v['enterprise_value'] / v['equity_value']:.2f}，")
    print("          多出来的部分是净债务的杠杆放大——同一个经营变化，落到股权上会被放大。")
    print("  读法二：弹性绝对值越大，说明本案例的股权价值对该输入越敏感；")
    print("          这是当前输入组合的结果，不能推广成所有公司的固定排序。")
    print()
    print("折现率绝对敏感性（这是关键检查之一，还应检查增长、利润率和终值）")
    for d in [-0.02, -0.01, 0.0, 0.01, 0.02]:
        q = dict(p)
        q["discount_rate"] = p["discount_rate"] + d
        try:
            w = value(q)
        except ValueError:
            print(f"  {q['discount_rate']:>6.2%}   无解（折现率 <= 永续增长）")
            continue
        tag = "  <- 基准" if d == 0 else ""
        print(f"  {q['discount_rate']:>6.2%}   股权价值 {w['equity_value']:>9.2f} {unit}   "
              f"相对基准 {w['equity_value'] / v['equity_value'] - 1:>+7.1%}{tag}")
    print()
    print("年数敏感性（其余不变）")
    for n in [5, 7, 10, 15]:
        q = dict(p)
        q["years"] = n
        w = value(q)
        print(f"  {n:>2d} 年   股权价值 {w['equity_value']:>9.2f} {unit}   终值占比 {w['terminal_share']:>6.1%}")


if __name__ == "__main__":
    main()
