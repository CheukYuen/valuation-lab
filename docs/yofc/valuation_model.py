"""长飞光纤估值实战的最小可复算模型。

金额单位：人民币亿元；每股价值单位：元。
模型只保存文档中明示的事实与假设，不抓取数据，不产生投资建议。
"""

from dataclasses import dataclass
from typing import Optional


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
LTM_EBIT = 47.34
LTM_EBITDA = 59.43
PARENT_EQUITY = 163.64
INVESTED_CAPITAL_2026H1 = 192.12
OBSERVED_CAPITAL_TURNOVER = LTM_REVENUE / INVESTED_CAPITAL_2026H1

PEER_MEDIAN_PE = 117.2
PEER_MEDIAN_PB = 24.3
PEER_MEDIAN_EV_EBIT = 103.9
PEER_MEDIAN_EV_EBITDA = 76.5

A_PRICE_CNY = 379.19
H_PRICE_HKD = 140.80

STUB_DAYS = 129
STUB_YEARS = STUB_DAYS / 365
BALANCE_SHEET_TO_PRICE_DAYS = 55
BALANCE_SHEET_TO_PRICE_YEARS = BALANCE_SHEET_TO_PRICE_DAYS / 365


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
    stub_fcf_margin: float
    capital_turnover: float = OBSERVED_CAPITAL_TURNOVER


SCENARIOS = {
    "bear": Scenario(
        "保守",
        182.0,
        (112.0, 42.0, 28.0),
        (0.00, -0.03, 0.00, 0.02, 0.03),
        (0.20, 0.15, 0.12, 0.10, 0.09),
        0.105,
        0.020,
        0.080,
        0.120,
    ),
    "base": Scenario(
        "基准",
        195.0,
        (120.0, 45.0, 30.0),
        (0.08, 0.06, 0.05, 0.04, 0.03),
        (0.27, 0.24, 0.21, 0.19, 0.18),
        0.090,
        0.025,
        0.160,
        0.1743,
    ),
    "bull": Scenario(
        "乐观",
        209.0,
        (128.0, 49.0, 32.0),
        (0.15, 0.12, 0.10, 0.08, 0.06),
        (0.31, 0.29, 0.27, 0.25, 0.23),
        0.080,
        0.030,
        0.210,
        0.220,
    ),
}


def equity_bridge_adjustment(scenario: Scenario) -> dict[str, float]:
    """返回 EV 减股权价值的净桥接及其组成。"""
    necessary_cash = scenario.revenue_2026 * NECESSARY_CASH_RATE
    excess_non_operating_assets = NON_OPERATING_ASSETS - necessary_cash
    estimated_gap_fcf = (
        scenario.revenue_2026
        * scenario.stub_fcf_margin
        * BALANCE_SHEET_TO_PRICE_YEARS
    )
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
    tax_rate: float = NORMALIZED_TAX_RATE,
):
    """返回显性期、终值、桥接和每股价值。"""
    discount_rate = scenario.wacc if wacc is None else wacc
    growth_terminal = scenario.terminal_growth if terminal_growth is None else terminal_growth
    if discount_rate <= growth_terminal:
        raise ValueError("WACC 必须高于终值增长率")
    if not 0 <= tax_rate < 1:
        raise ValueError("税率必须介于 0 和 1 之间")

    # 估值日后的剩余 2026 年现金流。
    stub_fcf = scenario.revenue_2026 * scenario.stub_fcf_margin * STUB_YEARS
    stub_pv = stub_fcf / (1 + discount_rate) ** (STUB_YEARS / 2)
    explicit_pv = stub_pv

    # 用已披露 LTM 收入 / 2026H1 投入资本校准资本周转率，再滚存投入资本。
    invested_capital = scenario.revenue_2026 / scenario.capital_turnover
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
    terminal_nopat = terminal_revenue * scenario.terminal_margin * (1 - tax_rate)
    terminal_reinvestment = terminal_nopat * growth_terminal / terminal_roic
    terminal_fcff = terminal_nopat - terminal_reinvestment
    terminal_value = terminal_fcff / (discount_rate - growth_terminal)
    terminal_time = 5 + STUB_YEARS
    terminal_pv = terminal_value / (1 + discount_rate) ** terminal_time

    enterprise_value = explicit_pv + terminal_pv

    # 保留必要经营现金，并把 6/30 资本结构近似滚动至 8/24 定价日。
    bridge = equity_bridge_adjustment(scenario)
    equity_value = enterprise_value - bridge["ev_minus_equity"]
    value_per_share_cny = equity_value / FULLY_DILUTED_SHARES_YI

    return {
        "stub_fcf": stub_fcf,
        "rows": rows,
        "explicit_pv": explicit_pv,
        "terminal_roic": terminal_roic,
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
    """使用基准桥接口径计算长飞自身的 LTM 倍数。"""
    enterprise_value = (
        equity_value + equity_bridge_adjustment(SCENARIOS["base"])["ev_minus_equity"]
    )
    return {
        "pe": equity_value / LTM_PARENT_NET_INCOME,
        "pb": equity_value / PARENT_EQUITY,
        "ev_ebit": enterprise_value / LTM_EBIT,
        "ev_ebitda": enterprise_value / LTM_EBITDA,
    }


def peer_median_implied_values() -> dict[str, float]:
    """机械套用三家可比公司中位数；只用于展示，不是估值结论。"""
    bridge = equity_bridge_adjustment(SCENARIOS["base"])["ev_minus_equity"]
    return {
        "pe": LTM_PARENT_NET_INCOME * PEER_MEDIAN_PE / FULLY_DILUTED_SHARES_YI,
        "pb": PARENT_EQUITY * PEER_MEDIAN_PB / FULLY_DILUTED_SHARES_YI,
        "ev_ebit": (
            LTM_EBIT * PEER_MEDIAN_EV_EBIT - bridge
        ) / FULLY_DILUTED_SHARES_YI,
        "ev_ebitda": (
            LTM_EBITDA * PEER_MEDIAN_EV_EBITDA - bridge
        ) / FULLY_DILUTED_SHARES_YI,
    }


def reverse_constant_margin_for_equity(target_equity: float) -> float:
    """固定基准情景其他条件，只反解 2027 年起恒定 EBIT 利润率。"""
    base = SCENARIOS["base"]

    def equity_value(margin: float) -> float:
        adjusted = Scenario(
            base.name,
            base.revenue_2026,
            base.segment_revenue_2026,
            base.growth,
            (margin,) * 5,
            base.wacc,
            base.terminal_growth,
            margin,
            base.stub_fcf_margin,
            base.capital_turnover,
        )
        return dcf(adjusted)["equity_value"]

    low, high = 0.0, 2.0
    for _ in range(100):
        middle = (low + high) / 2
        if equity_value(middle) < target_equity:
            low = middle
        else:
            high = middle
    return (low + high) / 2


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

    print("\n基准情景敏感性（元/股）")
    for wacc in (0.08, 0.09, 0.10):
        values = [
            dcf(SCENARIOS["base"], wacc=wacc, terminal_growth=g)["value_per_share_cny"]
            for g in (0.02, 0.025, 0.03)
        ]
        print(f"WACC {wacc:.1%}: " + ", ".join(f"{value:.2f}" for value in values))

    reported_tax_value = dcf(
        SCENARIOS["base"], tax_rate=REPORTED_H1_TAX_RATE
    )["value_per_share_cny"]
    print(
        "\n基准税率敏感性: "
        f"正常化 {NORMALIZED_TAX_RATE:.2%}={dcf(SCENARIOS['base'])['value_per_share_cny']:.2f}, "
        f"2026H1 有效税率 {REPORTED_H1_TAX_RATE:.2%}={reported_tax_value:.2f}"
    )

    combined_market_cap = actual_combined_market_cap()
    print("\n长飞自身 LTM 倍数（P/E, P/B, EV/EBIT, EV/EBITDA）")
    valuation_sets = {
        "实际 A+H 混合市值": combined_market_cap,
        "H 股单一价格隐含": H_PRICE_HKD * HKD_TO_CNY * FULLY_DILUTED_SHARES_YI,
        "A 股单一价格隐含": A_PRICE_CNY * FULLY_DILUTED_SHARES_YI,
    }
    for name, equity_value in valuation_sets.items():
        multiples = relative_multiples(equity_value)
        print(name + ": " + ", ".join(f"{value:.1f}x" for value in multiples.values()))

    implied = peer_median_implied_values()
    print(
        "三家可比公司中位数机械套用（元/股）: "
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
