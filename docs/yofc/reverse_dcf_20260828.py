#!/usr/bin/env python3
"""长飞光纤 2026-08-28 反向 DCF 的最小可复算脚本。

金额单位：人民币亿元；比率使用小数。市场价格与汇率固定在文档所述时点，
经营、资本效率、WACC 和终值规则复用 valuation_model.py 的基准情景。

本脚本的输出契约：单变量反解只有落在事先声明的可行域内才算“解”。落在域外时，
真正的结论是“无经济可行解 + 域内天花板与缺口”，反解值本身只作为刻度展示。
"""

from contextlib import contextmanager

import valuation_model as vm


PRICE_DATE = "2026-08-28"
A_PRICE_CNY = 422.36
H_PRICE_HKD = 170.30
HKD_TO_CNY = 0.86498

# 2026-06-30 资产负债表到 2026-08-28 收盘为 59 天；定价日到年末为 125 天。
BALANCE_SHEET_TO_PRICE_DAYS = 59
STUB_DAYS = 125
H2_DAYS = BALANCE_SHEET_TO_PRICE_DAYS + STUB_DAYS

# 可行域：每个变量的上界都取“激进但仍可想象”的水平，用途是证伪而不是预测。
# 增速 25%：显著高于基准 8%→3% 路径，接近历史高景气年份的持续扩张速度。
# EBIT 利润率 35%：高于 2026H1 报表口径 39.52% 的严格核心值 34.57%，即把半年高点
#   当成可永久维持的水平；终值 25% 仍远高于基准 16%。
# 资本周转率 1.50x：显著优于历史校准 0.92x，等于假设资本效率结构性改善。
# WACC 7.0% 与终值增长 3.0%：折现率取低、长期增长取高，两端同时最有利。
FEASIBLE_BOX = {
    "growth": 0.25,
    "ebit_margin": 0.35,
    "terminal_margin": 0.25,
    "capital_turnover": 1.50,
    "wacc": 0.070,
    "terminal_growth": 0.030,
}

# 母公司隐含 P/B，用于把账面 NCI 标记到市场口径做敏感性；不进入基准桥接。
NCI_MARKET_MULTIPLE = 14.3


@contextmanager
def pricing_date_timing():
    """临时把通用模型的估值时点切换到 2026-08-28，退出后恢复。"""
    names = (
        "BALANCE_SHEET_TO_PRICE_DAYS",
        "STUB_DAYS",
        "H2_DAYS",
        "STUB_YEARS",
    )
    original = {name: getattr(vm, name) for name in names}
    vm.BALANCE_SHEET_TO_PRICE_DAYS = BALANCE_SHEET_TO_PRICE_DAYS
    vm.STUB_DAYS = STUB_DAYS
    vm.H2_DAYS = H2_DAYS
    vm.STUB_YEARS = STUB_DAYS / 365
    try:
        yield
    finally:
        for name, value in original.items():
            setattr(vm, name, value)


def h_price_cny() -> float:
    return H_PRICE_HKD * HKD_TO_CNY


def actual_mixed_equity_value() -> float:
    """A、H 两类股份分别按各自收盘价计算实际混合股权市值。"""
    return vm.A_SHARES_YI * A_PRICE_CNY + vm.H_SHARES_YI * h_price_cny()


def pricing_calibers() -> dict[str, float]:
    """三个定价口径的股权价值：全按 H 股价、实际混合、全按 A 股价。

    混合市值把两套差异极大的预期混在一起（A 股折人民币价是 H 股的 2.87 倍），
    所以三个口径要并列跑，才能看出结论是否依赖 A/H 结构。
    """
    return {
        "全按 H 股价": h_price_cny() * vm.FULLY_DILUTED_SHARES_YI,
        "实际 A+H 混合": actual_mixed_equity_value(),
        "全按 A 股价": A_PRICE_CNY * vm.FULLY_DILUTED_SHARES_YI,
    }


def scenario_with_constant_growth(growth: float) -> vm.Scenario:
    base = vm.SCENARIOS["base"]
    return vm.Scenario(
        base.name,
        base.revenue_2026,
        base.segment_revenue_2026,
        (growth,) * 5,
        base.ebit_margin,
        base.wacc,
        base.terminal_growth,
        base.terminal_margin,
        base.h2_ebit_margin,
        base.capital_turnover,
    )


def feasible_box_scenario() -> vm.Scenario:
    """可行域上界对应的情景：所有杠杆同时推到激进角落。"""
    base = vm.SCENARIOS["base"]
    return vm.Scenario(
        "可行域上界",
        base.revenue_2026,
        base.segment_revenue_2026,
        (FEASIBLE_BOX["growth"],) * 5,
        (FEASIBLE_BOX["ebit_margin"],) * 5,
        FEASIBLE_BOX["wacc"],
        FEASIBLE_BOX["terminal_growth"],
        FEASIBLE_BOX["terminal_margin"],
        FEASIBLE_BOX["ebit_margin"],
        FEASIBLE_BOX["capital_turnover"],
    )


def feasibility_ceiling(target_equity: float) -> dict[str, float]:
    """域内最大可达股权价值与缺口；这是单变量反解越界时真正的结论。"""
    box = feasible_box_scenario()
    ceiling = vm.dcf(box)
    # 松开利润率、其余仍按可行域上界，看还需要多高的利润率才能补上缺口。
    # 两种口径必须分开报：终值利润率是否跟着抬高，答案相差一倍以上。
    margin_with_terminal = vm.reverse_constant_margin_for_equity(target_equity, box)
    margin_terminal_fixed = vm.reverse_constant_margin_for_equity(
        target_equity, box, terminal_margin=FEASIBLE_BOX["terminal_margin"]
    )
    return {
        "ceiling_enterprise_value": ceiling["enterprise_value"],
        "ceiling_equity_value": ceiling["equity_value"],
        "target_equity": target_equity,
        "gap": ceiling["equity_value"] - target_equity,
        "gap_ratio": ceiling["equity_value"] / target_equity - 1,
        "feasible": ceiling["equity_value"] >= target_equity,
        # 显性期与终值利润率同时抬高到该水平。
        "required_margin_in_box": margin_with_terminal,
        # 只抬高 2027–2031 年，终值仍保持盒子上界 25%。
        "required_margin_in_box_terminal_fixed": margin_terminal_fixed,
    }


def constant_margin_solution(target_equity: float) -> dict[str, float]:
    """路径一：闭式解。股权价值对恒定 EBIT 利润率是严格一次函数。"""
    intercept, slope = vm.constant_margin_line()
    margin = vm.reverse_constant_margin_for_equity(target_equity)
    result = vm.dcf(vm.constant_margin_scenario(margin))
    return {
        "intercept": intercept,
        "slope": slope,
        "margin": margin,
        "result": result,
        # 闭式解的残差，用来证明线性关系成立而不是近似。
        "residual": result["equity_value"] - target_equity,
    }


def constant_growth_artifact(target_equity: float) -> dict[str, float]:
    """路径二：仅作为终值接缝的演示，不作为“市场隐含增长”的结论。

    显性期按固定资本周转率滚存投入资本，终值改用“新增资本 ROIC = WACC”推导再投资，
    两套规则隐含的增量资本效率不同。价值随增长单调上升，主要来自终值按 2031 年收入
    等比放大，而不是显性期真的创造了现金流——显性期 FCFF 全程为负。
    """
    growth = vm.solve_monotone(
        target_equity,
        lambda value: vm.dcf(scenario_with_constant_growth(value))["equity_value"],
        -0.5,
        2.0,
    )
    result = vm.dcf(scenario_with_constant_growth(growth))
    base_result = vm.dcf(vm.SCENARIOS["base"])
    return {
        "growth": growth,
        "result": result,
        "explicit_capital_turnover": vm.SCENARIOS["base"].capital_turnover,
        "terminal_incremental_turnover": base_result["terminal_incremental_turnover"],
    }


def nci_market_sensitivity(target_equity: float) -> dict[str, float]:
    """把 NCI 从账面价值改为按母公司隐含 P/B 标记的敏感性。

    方向是抬高目标 EV，因此只会让隐含条件更极端，是加强结论而非威胁结论。
    不写入基准桥接，仅作披露。
    """
    delta = vm.NON_CONTROLLING_INTEREST_BOOK * (NCI_MARKET_MULTIPLE - 1)
    bridge = vm.equity_bridge_adjustment(vm.SCENARIOS["base"])
    base_target_ev = target_equity + bridge["ev_minus_equity"]
    return {
        "nci_book": vm.NON_CONTROLLING_INTEREST_BOOK,
        "nci_marked": vm.NON_CONTROLLING_INTEREST_BOOK * NCI_MARKET_MULTIPLE,
        "delta": delta,
        "target_enterprise_value": base_target_ev + delta,
        "target_enterprise_value_ratio": (base_target_ev + delta) / base_target_ev - 1,
        "implied_margin": vm.reverse_constant_margin_for_equity(target_equity + delta),
    }


def calculate() -> dict[str, object]:
    with pricing_date_timing():
        base_result = vm.dcf(vm.SCENARIOS["base"])
        bridge = vm.equity_bridge_adjustment(vm.SCENARIOS["base"])
        target_equity = actual_mixed_equity_value()

        calibers = {}
        for name, equity in pricing_calibers().items():
            calibers[name] = {
                "equity_value": equity,
                "enterprise_value": equity + bridge["ev_minus_equity"],
                "multiple_of_base": equity / base_result["equity_value"],
                "implied_constant_margin": vm.reverse_constant_margin_for_equity(equity),
            }

        margin_path = constant_margin_solution(target_equity)
        growth_path = constant_growth_artifact(target_equity)
        ceiling = feasibility_ceiling(target_equity)
        nci = nci_market_sensitivity(target_equity)

    return {
        "target_equity": target_equity,
        "target_enterprise_value": target_equity + bridge["ev_minus_equity"],
        "bridge": bridge,
        "base_equity_value": base_result["equity_value"],
        "base_value_per_share": base_result["value_per_share_cny"],
        "market_price_per_share": target_equity / vm.FULLY_DILUTED_SHARES_YI,
        "market_to_base_multiple": target_equity / base_result["equity_value"],
        "calibers": calibers,
        "feasibility": ceiling,
        "margin_path": margin_path,
        "growth_path": growth_path,
        "nci_sensitivity": nci,
        # 兼容旧字段名，便于既有引用继续可读。
        "implied_constant_margin": margin_path["margin"],
        "implied_constant_growth": growth_path["growth"],
        "margin_result": margin_path["result"],
        "growth_result": growth_path["result"],
    }


def print_report() -> None:
    result = calculate()
    print(f"长飞光纤反向 DCF，定价日 {PRICE_DATE}")
    print(f"HKD/CNY 直接汇率: {HKD_TO_CNY:.5f}")

    print("\n[1] 量级校准：反解值全部是这个倍数的机械后果")
    print(
        f"基准情景股权价值: {result['base_equity_value']:.2f} 亿元"
        f"（{result['base_value_per_share']:.2f} 元/股）"
    )
    print(
        f"实际 A+H 混合股权市值: {result['target_equity']:.2f} 亿元"
        f"（{result['market_price_per_share']:.2f} 元/股）"
    )
    print(f"市值 / 基准 DCF: {result['market_to_base_multiple']:.2f}×")
    print(f"目标企业价值 EV: {result['target_enterprise_value']:.2f} 亿元")

    ceiling = result["feasibility"]
    print("\n[2] 可行域天花板：所有杠杆同时推到激进角落")
    print(
        f"盒子: 增速 {FEASIBLE_BOX['growth']:.0%}/年, EBIT 利润率 "
        f"{FEASIBLE_BOX['ebit_margin']:.0%}（终值 {FEASIBLE_BOX['terminal_margin']:.0%}）, "
        f"周转率 {FEASIBLE_BOX['capital_turnover']:.2f}x, WACC "
        f"{FEASIBLE_BOX['wacc']:.1%}, g {FEASIBLE_BOX['terminal_growth']:.1%}"
    )
    print(f"域内最大股权价值: {ceiling['ceiling_equity_value']:.2f} 亿元")
    print(f"目标股权价值: {ceiling['target_equity']:.2f} 亿元")
    print(f"缺口: {ceiling['gap']:.2f} 亿元（{ceiling['gap_ratio']:+.1%}）")
    print(f"判定: {'域内有解' if ceiling['feasible'] else '无经济可行解'}")
    print(
        "即使放宽到该盒子，仍需 EBIT 利润率 "
        f"{ceiling['required_margin_in_box']:.2%}（显性期与终值同步抬高）或 "
        f"{ceiling['required_margin_in_box_terminal_fixed']:.2%}（终值固定在 "
        f"{FEASIBLE_BOX['terminal_margin']:.0%}）才能补上缺口"
    )

    print("\n[3] 三个定价口径的隐含恒定 EBIT 利润率")
    for name, item in result["calibers"].items():
        print(
            f"{name}: 股权 {item['equity_value']:.2f} 亿元, "
            f"EV {item['enterprise_value']:.2f} 亿元, "
            f"隐含利润率 {item['implied_constant_margin']:.2%}, "
            f"基准的 {item['multiple_of_base']:.2f}×"
        )

    margin_path = result["margin_path"]
    print("\n[4] 路径一：恒定 EBIT 利润率（闭式解，无需二分）")
    print(
        f"股权价值 = {margin_path['intercept']:.2f} + "
        f"{margin_path['slope']:.2f} × 恒定 EBIT 利润率"
    )
    print(f"隐含 2027-2031 恒定 EBIT 利润率: {margin_path['margin']:.2%}")
    print(f"闭式解残差: {margin_path['residual']:.2e} 亿元")

    growth_path = result["growth_path"]
    print("\n[5] 路径二：恒定收入增长率（终值接缝演示，不作为结论）")
    print(f"隐含 2027-2031 恒定收入增长率: {growth_path['growth']:.2%}")
    print(f"恒定增长路径 2031E 收入: {growth_path['result']['rows'][-1]['revenue']:.2f} 亿元")
    print(
        f"显性期资本周转率 {growth_path['explicit_capital_turnover']:.2f}x "
        f"vs 基准终值隐含增量周转率 {growth_path['terminal_incremental_turnover']:.2f}x"
    )
    print(
        f"显性期 FCFF 现值合计 {growth_path['result']['explicit_pv']:.2f} 亿元，"
        f"终值占 EV {growth_path['result']['terminal_share']:.2%}"
    )

    nci = result["nci_sensitivity"]
    print("\n[6] NCI 口径敏感性（不进入基准桥接）")
    print(
        f"NCI 账面 {nci['nci_book']:.2f} → 按母公司隐含 P/B {NCI_MARKET_MULTIPLE:.1f}x "
        f"标记为 {nci['nci_marked']:.2f} 亿元"
    )
    print(
        f"目标 EV: {result['target_enterprise_value']:.2f} → "
        f"{nci['target_enterprise_value']:.2f} 亿元"
        f"（{nci['target_enterprise_value_ratio']:+.1%}）"
    )
    print(f"隐含恒定 EBIT 利润率: {nci['implied_margin']:.2%}")


if __name__ == "__main__":
    print_report()
