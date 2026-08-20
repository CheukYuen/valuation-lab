#!/usr/bin/env python3
"""反解：不问「值多少」，问「现在的价格要求什么」。

    python3 lab/reverse.py 300                  当前股权市值 300（单位同输入文件）
    python3 lab/reverse.py 300 我的输入.json

这是从零起步最短的一条路。
「这家公司值多少钱」你答不了；
「在这组假设下，当前价格要求未来七年每年增长 23%」是一个可以拿历史和经营机制去质证的条件问题。

反解的输出永远不是一个数，而是一条曲线：换一个折现率，要求就变。
只给单一反解结果而不披露折现率，会隐藏模型的重要条件。
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


def required_years(p, target, max_years=80):
    """其余输入不变，找使股权价值达到目标的最小显性期年数。年数是整数。
    无解时返回 None，不返回边界值。"""
    at_one = equity_at(p, years=1)
    at_cap = equity_at(p, years=max_years)
    if at_one > target:
        return {
            "required_years": 1,
            "years_below": 0,
            "equity_below": None,
            "equity_at": at_one,
        }
    if at_cap < target:
        return None
    n = 1
    previous = at_one
    while n <= max_years:
        current = equity_at(p, years=n)
        if current >= target:
            return {
                "required_years": n,
                "years_below": n - 1,
                "equity_below": previous if n > 1 else None,
                "equity_at": current,
            }
        previous = current
        n += 1
    return None


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

    print("③ 当前价格要求的显性期年数（增长、起点、WACC 和永续增长全部不变）")
    years = required_years(p, target_equity)
    if years is None:
        print(f"   无解：即使把显性期拉到 80 年，{p['growth']:.0%} 增长也撑不到这个价格")
    else:
        n = years["required_years"]
        print(f"   需要约 {n} 年")
        if years["equity_below"] is not None:
            print(f"   {years['years_below']:>2d} 年   股权价值 {years['equity_below']:>9.2f} {unit}")
        print(f"   {n:>2d} 年   股权价值 {years['equity_at']:>9.2f} {unit}")
    print()

    print("怎么用这三张表")
    print("  · 每一行都是一个可质证的条件：历史上做到过吗？靠什么做到？能持续几年？")
    print("  · 三条路径是三个不同的经营故事。一次只反解一个变量，不要把一条条件解写成唯一观点。")
    print("  · 表里如果出现「无解」，那说明当前价格无法由这组假设的经济含义解释——")
    print("    先记录这个诊断，并排除对象、单位、EV 桥和搜索范围错误，不要只为凑数放宽假设。")
    print("  · 同一个价格在不同折现率下要求完全不同。谁给你一个反解结果而不给折现率，")
    print("    这份输出就没有完整披露自己的模型条件。")


if __name__ == "__main__":
    main()
