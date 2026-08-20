#!/usr/bin/env python3
"""第2课：两座价值桥。EBIT 怎样变成现金，EV 怎样变成每股价值。

    python3 lab/bridge.py                       使用 lab/inputs/bridge.json
    python3 lab/bridge.py 我的输入.json          使用自己的输入

这个脚本只复算「这套定义下的算式」。它不判断输入是否可信，也不计算 EV——
EV 由多期预测与折现得到（第4课 lab/mini_dcf.py），在这里是输入。
先自己写下答案，再运行对答案；数字对上不代表材料可用。
"""

from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "inputs" / "bridge.json"

FLOW = ["ebit", "tax_rate", "depreciation", "capex", "working_capital_increase"]
STRUCTURE = ["ev", "cash", "debt", "lease_liability", "minority_interest", "non_operating_assets"]
DENOMINATOR = ["total_shares", "treasury_shares", "option_dilution",
               "convertible_shares", "convertible_debt", "float_shares"]


def _pad(text, width):
    """按显示宽度补空格：一个中文字符占两列，否则表格会散。"""
    shown = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, width - shown)


def require(p, keys):
    """缺失就报错。未知不等于零：静默填零正是本课要抓的失败模式。"""
    missing = [k for k in keys if k not in p or p[k] is None]
    if missing:
        raise KeyError(f"输入缺少 {missing}；未知不能当作 0，请补证据或显式写 0 并说明依据")


def fcff(p):
    """第一座桥：EBIT -> NOPAT -> FCFF。"""
    require(p, FLOW)
    nopat = p["ebit"] * (1 - p["tax_rate"])
    flow = nopat + p["depreciation"] - p["capex"] - p["working_capital_increase"]
    return {
        "nopat": nopat,
        "fcff": flow,
        # 把 NOPAT 直接当 FCFF 会漏掉的净投入，也就是课文里的 4 亿元
        "skipped_reinvestment": p["capex"] + p["working_capital_increase"] - p["depreciation"],
    }


def equity(p):
    """第二座桥的前半段：EV -> 普通股股权价值。"""
    require(p, STRUCTURE)
    value = (p["ev"] + p["cash"] - p["debt"] - p["lease_liability"]
             - p["minority_interest"] + p["non_operating_assets"])
    return {
        "equity_value": value,
        "net_debt": p["debt"] + p["lease_liability"] - p["cash"],
    }


def per_share(p):
    """第二座桥的后半段：股权价值 -> 每股价值，以及四个错误分母的对照值。"""
    require(p, DENOMINATOR)
    value = equity(p)["equity_value"]
    basic = p["total_shares"] - p["treasury_shares"]
    if basic <= 0:
        raise ValueError(f"扣除库存股后的外部普通股为 {basic}，分母必须为正")
    diluted = basic + p["option_dilution"]
    if_converted_shares = diluted + p["convertible_shares"]
    return {
        "basic_shares": basic,
        "diluted_shares": diluted,
        "if_converted_shares": if_converted_shares,
        # ① 只用基本股数：忽略稀释
        "per_share_basic": value / basic,
        # ② 可转债留在债务里，分母只加期权稀释
        "per_share_diluted": value / diluted,
        # ③ if-converted：把可转债账面金额加回权益，分母同时加转股股份
        "per_share_if_converted": (value + p["convertible_debt"]) / if_converted_shares,
        # ④ 混用②③：扣了债又加了股，同一笔可转债被处理两次
        "per_share_double_counted": value / if_converted_shares,
        # ⑤ 用流通股分摊全体普通股股东的价值
        "per_share_float_wrong": value / p["float_shares"],
        # ⑥ 跳过资本结构桥，直接拿 EV 除以股本
        "ev_per_share": p["ev"] / basic,
    }


def with_dilution(p):
    """把 dilution_variant 覆盖到基准输入上。主线案例没有稀释项，稀释是显式变体。"""
    variant = dict(p)
    variant.update(p.get("dilution_variant", {}))
    return variant


def bridge(p):
    """两座桥的合并结果。web/assets/tools.js 的 bridge() 必须逐字段与它一致。"""
    out = dict(fcff(p))
    out.update(equity(p))
    out.update(per_share(p))
    return out


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    p = json.loads(path.read_text())
    unit = p.get("unit", "亿元")
    b = bridge(p)

    print(f"输入：{path}")
    print()
    print("第一座桥：利润怎样变成现金")
    print(f"  EBIT                {p['ebit']:>9.2f} {unit}")
    print(f"  × (1 - 经营税率 {p['tax_rate']:.0%})")
    print(f"  = NOPAT             {b['nopat']:>9.2f} {unit}")
    print(f"  + 折旧              {p['depreciation']:>9.2f} {unit}")
    print(f"  - 资本开支          {p['capex']:>9.2f} {unit}")
    print(f"  - 营运资金增加      {p['working_capital_increase']:>9.2f} {unit}"
          f"   （负数代表释放现金，这一项会变成加）")
    print(f"  = FCFF              {b['fcff']:>9.2f} {unit}")
    print()
    print(f"  把 NOPAT 直接当 FCFF，会漏掉净投入 {b['skipped_reinvestment']:.2f} {unit}"
          f"（= Capex + 营运资金增加 - 折旧）。")
    print("  漏掉不等于扩产是坏事，只说明这一步的现金流桥算错了。")
    print()

    print("第二座桥：企业价值怎样走到每股价值")
    print(f"  EV（输入，不由本脚本计算）      {p['ev']:>9.2f} {unit}")
    print(f"  + 现金                          {p['cash']:>9.2f} {unit}")
    print(f"  - 有息债务                      {p['debt']:>9.2f} {unit}")
    print(f"  - 租赁负债                      {p['lease_liability']:>9.2f} {unit}")
    print(f"  - 少数股东权益                  {p['minority_interest']:>9.2f} {unit}")
    print(f"  + 非经营资产                    {p['non_operating_assets']:>9.2f} {unit}")
    print(f"  = 普通股股权价值                {b['equity_value']:>9.2f} {unit}")
    print(f"  （净债务 {b['net_debt']:+.2f} {unit}"
          f"{'：净债务公司' if b['net_debt'] > 0 else '：净现金公司'}）")
    print()

    correct = b["per_share_basic"]
    print("分母对照：同一个股权价值，三种除法（本组输入没有稀释项）")
    print(f"  {_pad('口径', 30)}{'股数':>8}{'每股':>10}   相对正确分母的偏离")
    for name, shares, value in [
        ("外部普通股（总股本-库存股）", b["basic_shares"], correct),
        ("错误：用流通股当分母", p["float_shares"], b["per_share_float_wrong"]),
        ("错误：跳过资本结构桥，EV ÷ 股本", b["basic_shares"], b["ev_per_share"]),
    ]:
        print(f"  {_pad(name, 30)}{shares:>8.2f}{value:>10.2f}   {value / correct - 1:>+7.1%}")
    print()

    d = bridge(with_dilution(p))
    print("如果这家公司还有期权和可转债（lab/inputs/bridge.json 的 dilution_variant）")
    print(f"  {_pad('处理方式', 34)}{'股数':>8}{'每股':>10}   相对②的偏离")
    reference = d["per_share_diluted"]
    for name, shares, value in [
        ("① 只用基本股数，忽略稀释", d["basic_shares"], d["per_share_basic"]),
        ("② 可转债留在债务里，只加期权稀释", d["diluted_shares"], d["per_share_diluted"]),
        ("③ if-converted：加回可转债", d["if_converted_shares"], d["per_share_if_converted"]),
        ("④ 混用②③：扣了债又加了股", d["if_converted_shares"], d["per_share_double_counted"]),
    ]:
        print(f"  {_pad(name, 34)}{shares:>8.2f}{value:>10.2f}   {value / reference - 1:>+7.1%}")
    print()
    print("  读法一：②和③都是合法路径，结果接近但不相同——差异来自可转债按账面加回还是按转股价值处理。")
    print("          要审的是材料有没有说明自己选了哪条并保持一贯，而不是替作者选一条。")
    print("  读法二：④比②③都低，方向和「漏掉稀释」相反。所以不能靠「稀释一定让每股变低」自查。")
    print("  读法三：上面主线那组没有稀释项，17元就是正确答案；有没有稀释是先要确认的事实，")
    print("          不是所有材料都该套同一个分母。")
    print()

    print("跳过资本结构桥的方向不是固定的：把现金和债务对调")
    for label, cash, debt in [("净债务公司（现金<债务）", p["cash"], p["debt"]),
                              ("净现金公司（现金>债务）", p["debt"], p["cash"])]:
        q = dict(p, cash=cash, debt=debt)
        w = bridge(q)
        gap = w["ev_per_share"] / w["per_share_basic"] - 1
        print(f"  {_pad(label, 26)}现金 {cash:>6.2f} / 债务 {debt:>6.2f}   "
              f"EV÷股本 {w['ev_per_share']:>6.2f}   正确 {w['per_share_basic']:>6.2f}   {gap:>+7.1%}")
    print()

    print("单变量实验对答案（每次只改一个输入，其余不变）")
    experiments = [
        ("Capex 5 -> 12", dict(p, capex=12.0), "fcff"),
        ("营运资金增加 2 -> 释放 2", dict(p, working_capital_increase=-2.0), "fcff"),
        ("外部普通股 10 -> 12.5（总股本 13）", dict(p, total_shares=13.0), "per_share_basic"),
    ]
    for label, q, key in experiments:
        w = bridge(q)
        suffix = unit if key == "fcff" else "元"
        print(f"  {_pad(label, 34)}{key:<16} = {w[key]:>7.2f} {suffix}   （基准 {b[key]:.2f}）")
    print()
    print("边界：脚本复算的是算式，不是事实。输入的税率、折旧、Capex 和股本是否有证据、")
    print("      是否对应同一时点与同一范围，仍要由人按第1课的记录契约逐项验收。")
    print("      本脚本不产出目标价、评级或买卖动作。")


if __name__ == "__main__":
    main()
