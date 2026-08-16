#!/usr/bin/env python3
"""反解：不问「值多少」，问「现在的价格要求什么」。

    python3 lab/reverse.py 300                  当前股权市值 300（单位同输入文件）
    python3 lab/reverse.py 300 我的输入.json

这是从零起步最短的一条路。
「这家公司值多少钱」你答不了；
「当前价格要求未来七年每年增长 23%」是一个你能拿历史去查的事实问题。

反解的输出永远不是一个数，而是一条曲线：换一个折现率，要求就变。
任何只给单一反解结果的报告，都隐藏了它对折现率的假设。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mini_dcf import DEFAULT_INPUT, value  # noqa: E402


def solve(target, fn, low, high, iterations=200):
    """求 fn(x) = target。fn 必须单调递增。无解时返回 None，不返回边界值。"""
    try:
        lo_val, hi_val = fn(low), fn(high)
    except ValueError:
        return None
    if lo_val > target or hi_val < target:
        return None
    for _ in range(iterations):
        mid = (low + high) / 2
        if fn(mid) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def equity_at(p, **override):
    q = dict(p)
    q.update(override)
    return value(q)["equity_value"]


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法：python3 lab/reverse.py <当前股权市值> [输入.json]")
    target_equity = float(sys.argv[1])
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_INPUT
    p = json.loads(path.read_text())
    unit = p.get("unit", "亿元")

    base = value(p)
    print(f"输入：{path}")
    print(f"模型基准股权价值   {base['equity_value']:>10.2f} {unit}")
    print(f"当前市场股权价值   {target_equity:>10.2f} {unit}")
    gap = target_equity / base["equity_value"] - 1
    print(f"差距               {gap:>+10.1%}   （正数=市场高于模型，需要更强的假设才能解释）")
    print()

    rates = [p["discount_rate"] + d for d in (-0.02, -0.01, 0.0, 0.01, 0.02)]

    print("① 当前价格要求的显性期年增长（其余输入不变）")
    print(f"   {'折现率':<10}{'要求增长':>12}")
    for r in rates:
        if r <= p["terminal_growth"]:
            print(f"   {r:<10.2%}{'不适用':>12}   折现率不高于永续增长")
            continue
        g = solve(target_equity, lambda x: equity_at(p, growth=x, discount_rate=r), -0.5, 1.0)
        tag = "  <- 基准折现率" if abs(r - p["discount_rate"]) < 1e-12 else ""
        if g is None:
            print(f"   {r:<10.2%}{'无解':>12}   即使 100% 年增长也撑不到这个价格{tag}")
        else:
            print(f"   {r:<10.2%}{g:>12.2%}{tag}")
    print()

    print("② 当前价格要求的起点自由现金流（其余输入不变）")
    print(f"   {'折现率':<10}{'要求起点':>12}   相对现状")
    for r in rates:
        if r <= p["terminal_growth"]:
            print(f"   {r:<10.2%}{'不适用':>12}")
            continue
        f = solve(target_equity, lambda x: equity_at(p, base_fcf=x, discount_rate=r),
                  0.0, p["base_fcf"] * 50)
        tag = "  <- 基准折现率" if abs(r - p["discount_rate"]) < 1e-12 else ""
        if f is None:
            print(f"   {r:<10.2%}{'无解':>12}{tag}")
        else:
            print(f"   {r:<10.2%}{f:>12.2f} {unit}   {f / p['base_fcf'] - 1:>+7.1%}{tag}")
    print()

    print("怎么用这两张表")
    print("  · 每一行都是一个可查证的问题：这家公司历史上做到过这个增长吗？做到过几年？")
    print("  · 表里如果出现「无解」，那说明当前价格无法由这组假设的经济含义解释——")
    print("    这本身就是结论，不要换一组更宽松的假设去凑出一个数。")
    print("  · 同一个价格在不同折现率下要求完全不同。谁给你一个反解结果而不给折现率，")
    print("    谁就是在把自己的假设伪装成市场的观点。")


if __name__ == "__main__":
    main()
