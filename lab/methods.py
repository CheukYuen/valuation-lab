#!/usr/bin/env python3
"""第6课：同一家公司，四种方法。

    python3 lab/methods.py                      使用 lab/inputs/methods.json
    python3 lab/methods.py 我的输入.json

方法之间的差距不是精度问题，而是各自在假设不同的东西。
脚本回答的是「换一个方法，数字会差多少」，不回答「哪个方法是对的」——
后者要看商业模式、可比口径和这次结论的用途。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mini_dcf import value  # noqa: E402  同一套 DCF 公式只写一份

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "inputs" / "methods.json"

REQUIRED = ["net_income", "book_equity", "ebitda", "net_debt",
            "peer_pe", "peer_pb", "peer_ev_ebitda", "dcf"]


def require(p, keys):
    missing = [k for k in keys if k not in p or p[k] is None]
    if missing:
        raise KeyError(f"输入缺少 {missing}；未知不能当作 0")


def multiples(p):
    """同一家公司的四个股权价值。单位与输入一致。"""
    require(p, REQUIRED)
    return {
        "dcf": value(p["dcf"])["equity_value"],
        "pe": p["net_income"] * p["peer_pe"],
        "pb": p["book_equity"] * p["peer_pb"],
        "ev_ebitda": p["ebitda"] * p["peer_ev_ebitda"] - p["net_debt"],
    }


def spread(p):
    """四个结果的离散度。比值越大，说明「用哪个方法」这个选择越有决定权。"""
    values = list(multiples(p).values())
    high, low = max(values), min(values)
    return {"high": high, "low": low, "ratio": high / low if low else float("inf")}


def bank_demo(p):
    """把银行存款当普通有息债务扣除会怎样。对应 cases/00-basics 案例6。
    operating_profit_proxy 是教学用的经营利润代理量，故意误当成 EBITDA；
    两组输出都不是有效银行估值。"""
    b = p["bank"]
    proxy = b["operating_profit_proxy"]
    ex_deposits = b["other_debt"] - b["cash"]
    return {
        "ev_ebitda_with_deposits": proxy * b["peer_ev_ebitda"]
        - (b["deposits"] + ex_deposits),
        "ev_ebitda_without_deposits": proxy * b["peer_ev_ebitda"] - ex_deposits,
        "pe": b["net_income"] * b["peer_pe"],
        "pb": b["book_equity"] * b["peer_pb"],
    }


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    p = json.loads(path.read_text())
    unit = p.get("unit", "亿元")
    m = multiples(p)
    s = spread(p)

    print(f"输入：{path}")
    print()
    print("同一家工业公司的四个股权价值")
    labels = {
        "dcf": ("DCF", "假设未来七年现金流、终值增长和折现率"),
        "pe": ("PE", "假设可比公司的盈利口径和周期位置可对齐"),
        "pb": ("PB", "假设账面净资产反映了投入资本和回报能力"),
        "ev_ebitda": ("EV/EBITDA", "假设资本开支和营运资金差异不影响可比性"),
    }
    for key, (name, note) in labels.items():
        print(f"  {name:<12}{m[key]:>9.2f} {unit}   {note}")
    print()
    print(f"  最高 {s['high']:.2f} / 最低 {s['low']:.2f} = {s['ratio']:.2f} 倍")
    print("  读法：这个倍数不说明谁算错了，它说明「用哪个方法」本身就是一个必须给出理由的选择。")
    print("        材料只报一个方法的结果而不说明为什么选它，等于把这个选择藏了起来。")
    print()

    b = bank_demo(p)
    print("方法错配：把银行存款当成普通有息债务")
    print(f"  EV/EBITDA，存款按债务扣除     {b['ev_ebitda_with_deposits']:>9.2f} {unit}   <- 负值，经济上不成立")
    print(f"  EV/EBITDA，存款不按债务扣除   {b['ev_ebitda_without_deposits']:>9.2f} {unit}")
    print(f"  PE                            {b['pe']:>9.2f} {unit}")
    print(f"  PB                            {b['pb']:>9.2f} {unit}")
    print()
    print("  存款是银行的经营投入，不是等待偿还的融资负债；工业公司式 EV 桥套到银行上，")
    print("  错的不是精度，是量级和符号。机械移出存款只隔离 900 亿元影响，")
    print("  不构成一座正确的银行 EV 桥；两组输出都不是有效银行估值。")
    print()
    print("边界：脚本只演示方法之间的差距和一个已知的错配。40 亿元是经营利润代理量，")
    print("      故意误当成 EBITDA。它不判断哪个倍数合理，也不产出目标价或买卖动作。")


if __name__ == "__main__":
    main()
