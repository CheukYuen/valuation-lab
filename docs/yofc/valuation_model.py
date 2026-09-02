"""长飞光纤估值实战的最小可复算模型。

金额单位：人民币亿元；每股价值单位：元。
模型只保存文档中明示的事实与假设，不抓取数据，不产生投资建议。
折现率不再按情景直接给定，而是从 `cost_of_capital.py` 的 CAPM 推导取得：三个情景
共用同一个 WACC，经营好坏只通过收入、利润率和资本效率表达，不再在折现率上表达第二次。
"""

from dataclasses import dataclass
from typing import Optional

from cost_of_capital import DERIVED_WACC, wacc as derive_wacc


# 市值权重下的推导结果，约 10.49%；三情景共用。推导与替代口径见 cost_of_capital.py。
WACC = DERIVED_WACC
# 账面权重口径的对照值，约 8.08%。它不是主口径，只用来显示“权重惯例”这一个选择
# 就能覆盖旧版 8.0%–10.5% 的全部区间。
BOOK_WEIGHT_WACC = derive_wacc(weights="book")

NORMALIZED_TAX_RATE = 0.20
REPORTED_H1_TAX_RATE = 0.1623
HKD_TO_CNY = 0.86542

A_SHARES_YI = 4.06338314
H_SHARES_YI = 4.21566794
FULLY_DILUTED_SHARES_YI = A_SHARES_YI + H_SHARES_YI

DEBT = 95.25315837
NON_CONTROLLING_INTEREST_BOOK = 40.15765431
NON_OPERATING_ASSETS = 106.93422726
NECESSARY_CASH_RATE = 0.03

LTM_REVENUE = 176.77
LTM_PARENT_NET_INCOME = 34.43

# EV 桥已把交易性金融资产、长期股权投资等金融资产剔除，因此分母必须同步剔除这些
# 资产对应的投资收益和公允价值变动（第一层，口径一致性要求）。其他收益、资产处置、
# 营业外收支和汇兑损益属于需要逐项判断的正常化调整（第二层），严格核心口径把它们
# 一并剔除只是一种保守选择。两套口径都标 `PARTIAL`，模型同时输出，不宣称唯一正确。
LTM_REPORTED_EBIT = 47.34
LTM_DA = 12.09
LTM_REPORTED_EBITDA = LTM_REPORTED_EBIT + LTM_DA
LTM_CORE_EBIT = 42.86
LTM_CORE_EBITDA = LTM_CORE_EBIT + LTM_DA
PARENT_EQUITY = 163.64
INVESTED_CAPITAL_2026H1 = 192.12
OBSERVED_CAPITAL_TURNOVER = LTM_REVENUE / INVESTED_CAPITAL_2026H1
REVENUE_2026H1 = 98.09

PEER_MEDIAN_PE = 117.2
PEER_MEDIAN_PB = 24.3
A_PRICE_CNY = 379.19
H_PRICE_HKD = 140.80

STUB_DAYS = 129
STUB_YEARS = STUB_DAYS / 365
BALANCE_SHEET_TO_PRICE_DAYS = 55
H2_DAYS = STUB_DAYS + BALANCE_SHEET_TO_PRICE_DAYS


@dataclass(frozen=True)
class Scenario:
    name: str
    revenue_2026: float
    segment_revenue_2026: tuple[float, float, float]
    growth: tuple[float, float, float, float, float]
    ebit_margin: tuple[float, float, float, float, float]
    wacc: float
    terminal_growth: float
    terminal_margin: float
    h2_ebit_margin: float
    capital_turnover: float = OBSERVED_CAPITAL_TURNOVER


SCENARIOS = {
    "bear": Scenario(
        "保守",
        182.0,
        (112.0, 42.0, 28.0),
        (0.00, -0.03, 0.00, 0.02, 0.03),
        (0.20, 0.15, 0.12, 0.10, 0.09),
        WACC,
        0.020,
        0.080,
        0.200,
    ),
    "base": Scenario(
        "基准",
        195.0,
        (120.0, 45.0, 30.0),
        (0.08, 0.06, 0.05, 0.04, 0.03),
        (0.27, 0.24, 0.21, 0.19, 0.18),
        WACC,
        0.025,
        0.160,
        0.270,
    ),
    "bull": Scenario(
        "乐观",
        209.0,
        (128.0, 49.0, 32.0),
        (0.15, 0.12, 0.10, 0.08, 0.06),
        (0.31, 0.29, 0.27, 0.25, 0.23),
        WACC,
        0.030,
        0.210,
        0.310,
    ),
}


def h2_cash_flow(
    scenario: Scenario, tax_rate: float = NORMALIZED_TAX_RATE
) -> dict[str, float]:
    """把 6/30 至年末的 NOPAT、再投资和 FCFF 接到同一投入资本路径。"""
    h2_revenue = scenario.revenue_2026 - REVENUE_2026H1
    h2_nopat = h2_revenue * scenario.h2_ebit_margin * (1 - tax_rate)
    ending_invested_capital = scenario.revenue_2026 / scenario.capital_turnover
    reinvestment = ending_invested_capital - INVESTED_CAPITAL_2026H1
    h2_fcff = h2_nopat - reinvestment
    estimated_gap_fcf = h2_fcff * BALANCE_SHEET_TO_PRICE_DAYS / H2_DAYS
    post_valuation_fcf = h2_fcff * STUB_DAYS / H2_DAYS
    return {
        "h2_revenue": h2_revenue,
        "h2_nopat": h2_nopat,
        "ending_invested_capital": ending_invested_capital,
        "h2_reinvestment": reinvestment,
        "h2_fcff": h2_fcff,
        "estimated_gap_fcf": estimated_gap_fcf,
        "post_valuation_fcf": post_valuation_fcf,
    }


def equity_bridge_adjustment(
    scenario: Scenario, tax_rate: float = NORMALIZED_TAX_RATE
) -> dict[str, float]:
    """返回 EV 减股权价值的净桥接及其组成。"""
    necessary_cash = scenario.revenue_2026 * NECESSARY_CASH_RATE
    excess_non_operating_assets = NON_OPERATING_ASSETS - necessary_cash
    estimated_gap_fcf = h2_cash_flow(scenario, tax_rate)["estimated_gap_fcf"]
    ev_minus_equity = (
        DEBT
        + NON_CONTROLLING_INTEREST_BOOK
        - excess_non_operating_assets
        - estimated_gap_fcf
    )
    return {
        "necessary_cash": necessary_cash,
        "excess_non_operating_assets": excess_non_operating_assets,
        "estimated_gap_fcf": estimated_gap_fcf,
        "ev_minus_equity": ev_minus_equity,
    }


def dcf(
    scenario: Scenario,
    *,
    wacc: Optional[float] = None,
    terminal_growth: Optional[float] = None,
    terminal_margin: Optional[float] = None,
    tax_rate: float = NORMALIZED_TAX_RATE,
):
    """返回显性期、终值、桥接和每股价值。"""
    discount_rate = scenario.wacc if wacc is None else wacc
    growth_terminal = scenario.terminal_growth if terminal_growth is None else terminal_growth
    margin_terminal = scenario.terminal_margin if terminal_margin is None else terminal_margin
    if discount_rate <= growth_terminal:
        raise ValueError("WACC 必须高于终值增长率")
    if not 0 <= tax_rate < 1:
        raise ValueError("税率必须介于 0 和 1 之间")

    # 先完成整个 H2 的资本滚存，再按 55/184 与 129/184 切分估值日前后现金流。
    # 折现惯例：全模型统一按“现金流发生区间的期末”折现。显性期各年折 STUB_YEARS+t，
    # 终值折 5+STUB_YEARS，残余年份同样折满 STUB_YEARS，不再对残余期单独用期中折现。
    # 期末惯例相对期中惯例系统性偏保守（约半年折现，基准情景约 4.4%），此为已披露选择。
    h2 = h2_cash_flow(scenario, tax_rate)
    stub_fcf = h2["post_valuation_fcf"]
    stub_pv = stub_fcf / (1 + discount_rate) ** STUB_YEARS
    explicit_pv = stub_pv

    # 用已披露 LTM 收入 / 2026H1 投入资本校准资本周转率，再滚存投入资本。
    invested_capital = h2["ending_invested_capital"]
    rows = []
    revenue = scenario.revenue_2026

    for index, (growth, margin) in enumerate(
        zip(scenario.growth, scenario.ebit_margin), start=1
    ):
        year = 2026 + index
        revenue *= 1 + growth
        ebit = revenue * margin
        nopat = ebit * (1 - tax_rate)

        ending_invested_capital = revenue / scenario.capital_turnover
        reinvestment = ending_invested_capital - invested_capital
        average_invested_capital = (invested_capital + ending_invested_capital) / 2
        roic = nopat / average_invested_capital
        fcff = nopat - reinvestment

        years_from_valuation = STUB_YEARS + index
        present_value = fcff / (1 + discount_rate) ** years_from_valuation
        explicit_pv += present_value
        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "growth": growth,
                "ebit_margin": margin,
                "nopat": nopat,
                "starting_invested_capital": invested_capital,
                "ending_invested_capital": ending_invested_capital,
                "reinvestment": reinvestment,
                "roic": roic,
                "fcff": fcff,
                "pv": present_value,
            }
        )
        invested_capital = ending_invested_capital

    # 不默认永久超额回报：终值新增资本回报率与当期 WACC 收敛。
    terminal_roic = discount_rate
    terminal_revenue = revenue * (1 + growth_terminal)
    terminal_nopat = terminal_revenue * margin_terminal * (1 - tax_rate)
    terminal_reinvestment = terminal_nopat * growth_terminal / terminal_roic
    terminal_fcff = terminal_nopat - terminal_reinvestment
    terminal_value = terminal_fcff / (discount_rate - growth_terminal)
    # 终值再投资隐含的增量资本周转率，用于和显性期 0.92x 对照。
    terminal_incremental_turnover = (
        (terminal_revenue - revenue) / terminal_reinvestment
        if terminal_reinvestment
        else float("inf")
    )
    terminal_time = 5 + STUB_YEARS
    terminal_pv = terminal_value / (1 + discount_rate) ** terminal_time

    enterprise_value = explicit_pv + terminal_pv

    # 保留必要经营现金，并把 6/30 资本结构近似滚动至 8/24 定价日。
    bridge = equity_bridge_adjustment(scenario, tax_rate)
    equity_value = enterprise_value - bridge["ev_minus_equity"]
    value_per_share_cny = equity_value / FULLY_DILUTED_SHARES_YI

    return {
        "stub_fcf": stub_fcf,
        **h2,
        "rows": rows,
        "explicit_pv": explicit_pv,
        "terminal_roic": terminal_roic,
        "terminal_reinvestment": terminal_reinvestment,
        "terminal_incremental_turnover": terminal_incremental_turnover,
        "terminal_fcff": terminal_fcff,
        "terminal_value": terminal_value,
        "terminal_pv": terminal_pv,
        "enterprise_value": enterprise_value,
        **bridge,
        "equity_value": equity_value,
        "value_per_share_cny": value_per_share_cny,
        "value_per_share_hkd": value_per_share_cny / HKD_TO_CNY,
        "terminal_share": terminal_pv / enterprise_value,
    }


def actual_combined_market_cap() -> float:
    """按 A、H 两类股份各自价格计算定价日实际混合市值。"""
    h_price_cny = H_PRICE_HKD * HKD_TO_CNY
    return A_SHARES_YI * A_PRICE_CNY + H_SHARES_YI * h_price_cny


def relative_multiples(equity_value: float) -> dict[str, float]:
    """使用基准桥接口径计算长飞自身的 LTM 倍数。

    EV 类倍数使用严格核心 EBIT / EBITDA。它做完了第一层（剔除被 EV 桥减掉的金融
    资产对应的投资收益和公允价值变动，口径一致性要求），也做完了第二层（其他收益、
    资产处置、营业外收支、汇兑损益等需要逐项判断的正常化调整，此处取最保守处理）。
    第二层尚未逐项论证，因此结果为 `PARTIAL`；报表对照口径见
    `reported_caliber_ev_multiples`，两套并列，不宣称哪一套是唯一正确答案。
    """
    enterprise_value = (
        equity_value + equity_bridge_adjustment(SCENARIOS["base"])["ev_minus_equity"]
    )
    return {
        "pe": equity_value / LTM_PARENT_NET_INCOME,
        "pb": equity_value / PARENT_EQUITY,
        "ev_ebit": enterprise_value / LTM_CORE_EBIT,
        "ev_ebitda": enterprise_value / LTM_CORE_EBITDA,
    }


def reported_caliber_ev_multiples(equity_value: float) -> dict[str, float]:
    """报表对照口径：EV 除以未做任何调整的报表 EBIT / EBITDA。

    分子已剔除金融资产、分母仍含其收益，口径不一致会低估倍数；保留它是为了让读者
    看到两层调整各自值多少，同样标 `PARTIAL`。
    """
    enterprise_value = (
        equity_value + equity_bridge_adjustment(SCENARIOS["base"])["ev_minus_equity"]
    )
    return {
        "ev_ebit": enterprise_value / LTM_REPORTED_EBIT,
        "ev_ebitda": enterprise_value / LTM_REPORTED_EBITDA,
    }


def peer_median_implied_values() -> dict[str, float]:
    """机械套用可比公司 P/E、P/B 中位数；只用于展示。"""
    return {
        "pe": LTM_PARENT_NET_INCOME * PEER_MEDIAN_PE / FULLY_DILUTED_SHARES_YI,
        "pb": PARENT_EQUITY * PEER_MEDIAN_PB / FULLY_DILUTED_SHARES_YI,
    }


def solve_monotone(
    target: float,
    fn,
    low: float,
    high: float,
    iterations: int = 200,
    samples: int = 20,
) -> float:
    """二分求 fn(x)=target。全项目唯一的单变量反解入口。

    调用方必须给出确实包含解的区间：先校验端点把目标夹住，再在区间内等距抽样校验
    单调。抽样只是抽样：它能挡住明显的非单调函数，挡不住窄于采样间距的局部回落，
    因此它降低而不是消除“多解时静默返回其中一个根”的风险。
    """
    low_value, high_value = fn(low), fn(high)
    if low_value > high_value:
        raise ValueError("solve_monotone 只接受在区间内单调递增的函数")
    if not low_value <= target <= high_value:
        raise ValueError(
            f"目标 {target:.4f} 不在可达区间 [{low_value:.4f}, {high_value:.4f}] 内"
        )
    previous = low_value
    for step in range(1, samples + 1):
        current = fn(low + (high - low) * step / samples)
        if current < previous:
            raise ValueError("函数在搜索区间内不单调，二分解不唯一")
        previous = current
    for _ in range(iterations):
        middle = (low + high) / 2
        if fn(middle) < target:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def constant_margin_scenario(
    margin: float,
    base: Optional[Scenario] = None,
    terminal_margin: Optional[float] = None,
) -> Scenario:
    """把 2027–2031 年 EBIT 利润率替换为待求常数。

    默认终值利润率同步等于该常数；传入 terminal_margin 则把终值钉死在给定值，
    只松开显性期。两种口径的答案差别很大，必须在结论里说清用的是哪一种。
    """
    reference = SCENARIOS["base"] if base is None else base
    return Scenario(
        reference.name,
        reference.revenue_2026,
        reference.segment_revenue_2026,
        reference.growth,
        (margin,) * 5,
        reference.wacc,
        reference.terminal_growth,
        margin if terminal_margin is None else terminal_margin,
        reference.h2_ebit_margin,
        reference.capital_turnover,
    )


def constant_margin_line(
    base: Optional[Scenario] = None, terminal_margin: Optional[float] = None
) -> tuple[float, float]:
    """返回股权价值对恒定 EBIT 利润率的一次函数 (截距, 斜率)。

    固定收入路径后，EBIT、NOPAT、终值 NOPAT 都与利润率成正比，再投资完全由收入和
    资本周转率决定、与利润率无关，因此股权价值是利润率的严格一次函数。反解不需要
    二分，闭式解即可，且能直接说明“隐含利润率”只是刻度换算而非搜索发现。
    """
    intercept = dcf(constant_margin_scenario(0.0, base, terminal_margin))["equity_value"]
    slope = (
        dcf(constant_margin_scenario(1.0, base, terminal_margin))["equity_value"]
        - intercept
    )
    return intercept, slope


def reverse_constant_margin_for_equity(
    target_equity: float,
    base: Optional[Scenario] = None,
    terminal_margin: Optional[float] = None,
) -> float:
    """固定其他条件，只反解 2027 年起恒定 EBIT 利润率（闭式解）。

    terminal_margin 为 None 时终值利润率同步抬高；给定值时终值保持不变。
    """
    intercept, slope = constant_margin_line(base, terminal_margin)
    return (target_equity - intercept) / slope


def reverse_constant_margin_for_price(price_cny: float) -> float:
    """把单一类别价格假设为全公司每股价格，仅用于 A/H 隐含条件比较。"""
    return reverse_constant_margin_for_equity(price_cny * FULLY_DILUTED_SHARES_YI)


def print_model():
    print("长飞光纤 DCF（亿元，每股价值除外）")
    for scenario in SCENARIOS.values():
        result = dcf(scenario)
        print(
            f"{scenario.name}: EV={result['enterprise_value']:.2f}, "
            f"股权价值={result['equity_value']:.2f}, "
            f"人民币/股={result['value_per_share_cny']:.2f}, "
            f"折港币={result['value_per_share_hkd']:.2f}, "
            f"终值占比={result['terminal_share']:.1%}"
        )

    print("\n基准情景敏感性：WACC × 终值 EBIT 利润率（元/股，中心格为基准）")
    margins = (0.12, 0.14, 0.16, 0.18, 0.20)
    print("WACC \\ 终值利润率  " + "".join(f"{margin:>8.0%}" for margin in margins))
    for offset in (-0.02, -0.01, 0.0, 0.01, 0.02):
        rate = WACC + offset
        values = [
            dcf(SCENARIOS["base"], wacc=rate, terminal_margin=margin)["value_per_share_cny"]
            for margin in margins
        ]
        marker = " ←基准 WACC" if offset == 0.0 else ""
        print(
            f"{rate:>14.2%}  " + "".join(f"{value:>8.2f}" for value in values) + marker
        )

    print("\n账面权重 WACC 对照（不是主口径）")
    for key, scenario in SCENARIOS.items():
        value = dcf(scenario, wacc=BOOK_WEIGHT_WACC)["value_per_share_cny"]
        print(f"{scenario.name} @ {BOOK_WEIGHT_WACC:.2%}: {value:.2f} 元/股")

    print("\n交叉校验：DCF 结果隐含的 LTM 倍数与终值占比")
    for key, scenario in SCENARIOS.items():
        result = dcf(scenario)
        multiples = relative_multiples(result["equity_value"])
        print(
            f"{scenario.name}: EV/EBITDA={multiples['ev_ebitda']:.1f}x, "
            f"EV/EBIT={multiples['ev_ebit']:.1f}x, P/E={multiples['pe']:.1f}x, "
            f"终值占 EV={result['terminal_share']:.1%}"
        )

    reported_tax_value = dcf(
        SCENARIOS["base"], tax_rate=REPORTED_H1_TAX_RATE
    )["value_per_share_cny"]
    print(
        "\n基准税率敏感性: "
        f"正常化 {NORMALIZED_TAX_RATE:.2%}={dcf(SCENARIOS['base'])['value_per_share_cny']:.2f}, "
        f"2026H1 有效税率 {REPORTED_H1_TAX_RATE:.2%}={reported_tax_value:.2f}"
    )

    combined_market_cap = actual_combined_market_cap()
    print("\n长飞自身 LTM 倍数（P/E, P/B, EV/EBIT, EV/EBITDA；EV 类用严格核心口径）")
    valuation_sets = {
        "实际 A+H 混合市值": combined_market_cap,
        "H 股单一价格隐含": H_PRICE_HKD * HKD_TO_CNY * FULLY_DILUTED_SHARES_YI,
        "A 股单一价格隐含": A_PRICE_CNY * FULLY_DILUTED_SHARES_YI,
    }
    for name, equity_value in valuation_sets.items():
        multiples = relative_multiples(equity_value)
        print(name + ": " + ", ".join(f"{value:.1f}x" for value in multiples.values()))

    print("对照：EV 类倍数改用报表口径分母（分子分母不一致，仅供比较）")
    for name, equity_value in valuation_sets.items():
        reported = reported_caliber_ev_multiples(equity_value)
        print(name + ": " + ", ".join(f"{value:.1f}x" for value in reported.values()))

    implied = peer_median_implied_values()
    print(
        "三家可比公司中位数机械套用（P/E、P/B，元/股）: "
        + ", ".join(f"{value:.2f}" for value in implied.values())
    )

    h_price_cny = H_PRICE_HKD * HKD_TO_CNY
    print("\n反向 DCF：基准其他假设下的恒定 EBIT 利润率")
    print(
        f"实际 A+H 混合市值 {combined_market_cap:.2f}: "
        f"{reverse_constant_margin_for_equity(combined_market_cap):.2%}"
    )
    print(
        f"H 股单一价格假设 {H_PRICE_HKD:.2f} 港元（{h_price_cny:.2f} 元）: "
        f"{reverse_constant_margin_for_price(h_price_cny):.2%}"
    )
    print(
        f"A 股单一价格假设 {A_PRICE_CNY:.2f} 元: "
        f"{reverse_constant_margin_for_price(A_PRICE_CNY):.2%}"
    )


if __name__ == "__main__":
    print_model()
