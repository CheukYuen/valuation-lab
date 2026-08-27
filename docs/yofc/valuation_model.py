"""长飞光纤估值实战的最小可复算模型。

金额单位：人民币亿元；每股价值单位：元。
它只保存文档中已明示的假设，不抓取数据，不产生投资建议。
"""

from dataclasses import dataclass
from typing import Optional


TAX_RATE = 0.20
HKD_TO_CNY = 0.86542
VALUATION_SHARES_YI = 8.21905108
ISSUED_SHARES_YI = 8.27905108

DEBT = 95.25315837
NON_CONTROLLING_INTEREST = 40.15765431
NON_OPERATING_ASSETS = 106.93422726
EV_MINUS_EQUITY = DEBT + NON_CONTROLLING_INTEREST - NON_OPERATING_ASSETS

A_PRICE_CNY = 379.19
H_PRICE_HKD = 140.80

STUB_DAYS = 129
STUB_YEARS = STUB_DAYS / 365


@dataclass(frozen=True)
class Scenario:
    name: str
    revenue_2026: float
    segment_revenue_2026: tuple[float, float, float]
    growth: tuple[float, float, float, float, float]
    ebit_margin: tuple[float, float, float, float, float]
    roic: tuple[float, float, float, float, float]
    wacc: float
    terminal_growth: float
    terminal_margin: float
    terminal_roic: float
    stub_fcf_margin: float


SCENARIOS = {
    "bear": Scenario(
        "保守",
        182.0,
        (112.0, 42.0, 28.0),
        (0.00, -0.03, 0.00, 0.02, 0.03),
        (0.20, 0.15, 0.12, 0.10, 0.09),
        (0.18, 0.14, 0.11, 0.10, 0.10),
        0.105,
        0.020,
        0.080,
        0.10,
        0.120,
    ),
    "base": Scenario(
        "基准",
        195.0,
        (120.0, 45.0, 30.0),
        (0.08, 0.06, 0.05, 0.04, 0.03),
        (0.27, 0.24, 0.21, 0.19, 0.18),
        (0.28, 0.25, 0.22, 0.19, 0.17),
        0.090,
        0.025,
        0.160,
        0.12,
        0.1743,
    ),
    "bull": Scenario(
        "乐观",
        209.0,
        (128.0, 49.0, 32.0),
        (0.15, 0.12, 0.10, 0.08, 0.06),
        (0.31, 0.29, 0.27, 0.25, 0.23),
        (0.35, 0.32, 0.29, 0.26, 0.23),
        0.080,
        0.030,
        0.210,
        0.16,
        0.220,
    ),
}


def dcf(
    scenario: Scenario,
    *,
    wacc: Optional[float] = None,
    terminal_growth: Optional[float] = None,
):
    """返回地基现金流、显性期现值、终值现值、EV 与每股价值。"""
    discount_rate = scenario.wacc if wacc is None else wacc
    growth_terminal = scenario.terminal_growth if terminal_growth is None else terminal_growth
    if discount_rate <= growth_terminal:
        raise ValueError("WACC 必须高于终值增长率")

    stub_fcf = scenario.revenue_2026 * scenario.stub_fcf_margin * STUB_YEARS
    stub_pv = stub_fcf / (1 + discount_rate) ** (STUB_YEARS / 2)
    explicit_pv = stub_pv
    rows = []
    revenue = scenario.revenue_2026

    for index, (growth, margin, roic) in enumerate(
        zip(scenario.growth, scenario.ebit_margin, scenario.roic), start=1
    ):
        year = 2026 + index
        revenue *= 1 + growth
        ebit = revenue * margin
        nopat = ebit * (1 - TAX_RATE)
        # 收入收缩时不自动假设投入资本全部释放。
        reinvestment = nopat * max(growth, 0) / roic
        fcff = nopat - reinvestment
        years_from_valuation = 1 + STUB_YEARS + index - 1
        present_value = fcff / (1 + discount_rate) ** years_from_valuation
        explicit_pv += present_value
        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "growth": growth,
                "ebit_margin": margin,
                "nopat": nopat,
                "reinvestment": reinvestment,
                "fcff": fcff,
                "pv": present_value,
            }
        )

    terminal_revenue = revenue * (1 + growth_terminal)
    terminal_nopat = terminal_revenue * scenario.terminal_margin * (1 - TAX_RATE)
    terminal_reinvestment = terminal_nopat * growth_terminal / scenario.terminal_roic
    terminal_fcff = terminal_nopat - terminal_reinvestment
    terminal_value = terminal_fcff / (discount_rate - growth_terminal)
    terminal_time = 5 + STUB_YEARS
    terminal_pv = terminal_value / (1 + discount_rate) ** terminal_time

    enterprise_value = explicit_pv + terminal_pv
    equity_value = enterprise_value - EV_MINUS_EQUITY
    value_per_share_cny = equity_value / VALUATION_SHARES_YI

    return {
        "stub_fcf": stub_fcf,
        "rows": rows,
        "explicit_pv": explicit_pv,
        "terminal_fcff": terminal_fcff,
        "terminal_value": terminal_value,
        "terminal_pv": terminal_pv,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "value_per_share_cny": value_per_share_cny,
        "value_per_share_hkd": value_per_share_cny / HKD_TO_CNY,
        "terminal_share": terminal_pv / enterprise_value,
    }


def reverse_constant_margin(price_cny: float) -> float:
    """在基准收入、ROIC、WACC 和终值增长率下，反解 2027 年起恒定 EBIT 利润率。"""
    target_equity = price_cny * VALUATION_SHARES_YI
    target_ev = target_equity + EV_MINUS_EQUITY
    base = SCENARIOS["base"]

    def enterprise_value(margin: float) -> float:
        constant_margin = (margin,) * 5
        adjusted = Scenario(
            base.name,
            base.revenue_2026,
            base.segment_revenue_2026,
            base.growth,
            constant_margin,
            base.roic,
            base.wacc,
            base.terminal_growth,
            margin,
            base.terminal_roic,
            base.stub_fcf_margin,
        )
        return dcf(adjusted)["enterprise_value"]

    low, high = 0.0, 2.0
    for _ in range(100):
        middle = (low + high) / 2
        if enterprise_value(middle) < target_ev:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def print_model():
    print("长飞光纤 DCF（亿元，每股价值除外）")
    for scenario in SCENARIOS.values():
        result = dcf(scenario)
        print(
            f"{scenario.name}: EV={result['enterprise_value']:.2f}, "
            f"股权价值={result['equity_value']:.2f}, "
            f"A/H等权人民币价值={result['value_per_share_cny']:.2f}, "
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

    h_price_cny = H_PRICE_HKD * HKD_TO_CNY
    print("\n反向 DCF：基准其他假设下的恒定 EBIT 利润率")
    print(f"H股 {H_PRICE_HKD:.2f} 港元（{h_price_cny:.2f} 元）: {reverse_constant_margin(h_price_cny):.2%}")
    print(f"A股 {A_PRICE_CNY:.2f} 元: {reverse_constant_margin(A_PRICE_CNY):.2%}")


if __name__ == "__main__":
    print_model()
