#!/usr/bin/env python3
"""中天科技 2026-08-30 数据增强估值。

金额单位：人民币十亿元；每股价值单位：人民币元。

事实层来自 2025 年报、2026 年半年报与 datahub 2026-08-30 快照；
基准情景的 2026E-2028E EBITDA 来自摩根士丹利 2026-07-14 报告。
下行和上行情景以 datahub 一致预期 EPS 区间校准经营偏离幅度；2029E 以后及
折旧摊销、资本开支、营运资金、税率属于本项目情景假设。三种情景使用
同一 WACC 和永续增长率，估值差异只来自经营与现金流路径。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketAndBalanceSheet:
    price_rmb: float = 35.04
    shares_bn: float = 3.412949652
    cash_equivalents_rmb_bn: float = 16.09464149517
    short_term_debt_rmb_bn: float = 1.63152390553
    current_long_term_debt_rmb_bn: float = 0.38274059119
    long_term_debt_rmb_bn: float = 1.11813812446
    lease_liabilities_rmb_bn: float = 0.14667560327


@dataclass(frozen=True)
class ForecastYear:
    year: int
    ebitda_rmb_bn: float
    da_rmb_bn: float
    capex_rmb_bn: float
    delta_nwc_rmb_bn: float


@dataclass(frozen=True)
class DCFInputs:
    tax_rate: float = 0.15
    wacc: float = 0.0967
    terminal_growth: float = 0.02


@dataclass(frozen=True)
class H1Actual:
    operating_profit_rmb_bn: float = 2.84919346732
    da_rmb_bn: float = 0.72388940055
    capex_rmb_bn: float = 0.94257955986
    delta_nwc_rmb_bn: float = 3.01965175078


@dataclass(frozen=True)
class OperatingScenario:
    key: str
    name_cn: str
    thesis: str
    forecast: tuple[ForecastYear, ...]
    switch_conditions: tuple[str, ...]


MARKET = MarketAndBalanceSheet()
DCF_ASSUMPTIONS = DCFInputs()
H1_ACTUAL = H1Actual()

# 2026-06-30 资产负债表到 2026-08-28 价格日相隔 59 天；H2 共 184 天，
# 价格日之后还剩 125 天。2027 年现金流按年中收到，距价格日 306 天。
BALANCE_SHEET_TO_PRICE_DAYS = 59
H2_DAYS = 184
POST_PRICE_H2_DAYS = H2_DAYS - BALANCE_SHEET_TO_PRICE_DAYS
FIRST_FULL_YEAR_MIDPOINT = 306 / 365

# 基准情景：2026E-2028E EBITDA 为 BROKER-EST；2029E-2031E EBITDA 及
# 其余列为 PROJECT-ASSUMPTION。2026E 折旧摊销和 Capex 分别约为 H1 两倍。
BASE_FORECAST = (
    ForecastYear(2026, 8.537, 1.45, 2.00, 1.50),
    ForecastYear(2027, 10.773, 1.55, 2.20, 0.90),
    ForecastYear(2028, 13.105, 1.65, 2.40, 0.80),
    ForecastYear(2029, 14.6776, 1.75, 2.50, 0.80),
    ForecastYear(2030, 15.851808, 1.85, 2.60, 0.70),
    ForecastYear(2031, 16.6443984, 1.95, 2.70, 0.60),
)

# 下行和上行情景的 EBITDA 不是外部预测。2026 年已经披露半年报，因此仅在
# 基准上下偏离 5%；2027 年偏离 15%，2028 年偏离 20%。后两年的幅度大体
# 对应 datahub 一致预期 EPS 最低值/最高值相对均值的区间，但没有把 EPS
# 机械换算成 EBITDA。Capex 和营运资金单独反映固定投入及现金转化差异。
DOWNSIDE_FORECAST = (
    ForecastYear(2026, 8.11015, 1.45, 2.00, 2.20),
    ForecastYear(2027, 9.15705, 1.50, 2.10, 1.40),
    ForecastYear(2028, 10.48400, 1.55, 2.20, 1.20),
    ForecastYear(2029, 11.00820, 1.60, 2.20, 1.00),
    ForecastYear(2030, 11.338446, 1.65, 2.20, 0.90),
    ForecastYear(2031, 11.56521492, 1.70, 2.20, 0.80),
)

UPSIDE_FORECAST = (
    ForecastYear(2026, 8.96385, 1.45, 2.10, 1.20),
    ForecastYear(2027, 12.38895, 1.60, 2.50, 0.90),
    ForecastYear(2028, 15.72600, 1.75, 2.90, 0.80),
    ForecastYear(2029, 17.92764, 1.90, 3.10, 0.70),
    ForecastYear(2030, 19.720404, 2.05, 3.20, 0.60),
    ForecastYear(2031, 20.90362824, 2.20, 3.30, 0.50),
)

SCENARIOS = {
    "downside": OperatingScenario(
        key="downside",
        name_cn="下行",
        thesis="AI光纤订单转化放慢，海洋项目确认延后，营运资金继续占用现金",
        forecast=DOWNSIDE_FORECAST,
        switch_conditions=(
            "光通信量价改善弱于当前预测",
            "海洋业务收入确认继续后移",
            "存货和应收增长持续快于利润",
        ),
    ),
    "base": OperatingScenario(
        key="base",
        name_cn="基准",
        thesis="AI光纤逐步放量，海洋和电网按当前券商经营路径兑现",
        forecast=BASE_FORECAST,
        switch_conditions=(
            "2026E-2028E EBITDA接近大摩当前预测",
            "资本开支和营运资金按项目假设正常化",
        ),
    ),
    "upside": OperatingScenario(
        key="upside",
        name_cn="上行",
        thesis="G.657和MPO订单更快兑现，光通信毛利恢复，海洋和电网同时超预期",
        forecast=UPSIDE_FORECAST,
        switch_conditions=(
            "AI光纤订单和收入转化快于基准",
            "光通信毛利率明显恢复",
            "海洋和电网交付同时强于当前预测",
        ),
    ),
}

# 保留旧名称，默认 DCF 始终代表基准经营情景。
FORECAST = BASE_FORECAST

CONSENSUS_EPS_RMB = {2026: 1.88, 2027: 2.29, 2028: 2.72}


def net_cash_rmb_bn(market: MarketAndBalanceSheet = MARKET) -> float:
    interest_bearing_debt = (
        market.short_term_debt_rmb_bn
        + market.current_long_term_debt_rmb_bn
        + market.long_term_debt_rmb_bn
        + market.lease_liabilities_rmb_bn
    )
    return market.cash_equivalents_rmb_bn - interest_bearing_debt


def fcff(
    row: ForecastYear, tax_rate: float = DCF_ASSUMPTIONS.tax_rate
) -> float:
    """EBITDA 转 FCFF：EBIT 税后 + D&A - Capex - 营运资金增加。"""
    if not 0 <= tax_rate < 1:
        raise ValueError("税率必须介于 0 和 1 之间")
    if row.da_rmb_bn > row.ebitda_rmb_bn:
        raise ValueError("折旧摊销不能高于 EBITDA")
    ebit = row.ebitda_rmb_bn - row.da_rmb_bn
    nopat = ebit * (1 - tax_rate)
    return nopat + row.da_rmb_bn - row.capex_rmb_bn - row.delta_nwc_rmb_bn


def actual_h1_fcff(
    actual: H1Actual = H1_ACTUAL,
    tax_rate: float = DCF_ASSUMPTIONS.tax_rate,
) -> float:
    """以实际报表的营业利润近似 EBIT，计算 2026H1 FCFF 代理值。"""
    return (
        actual.operating_profit_rmb_bn * (1 - tax_rate)
        + actual.da_rmb_bn
        - actual.capex_rmb_bn
        - actual.delta_nwc_rmb_bn
    )


def h2_bridge(
    forecast: tuple[ForecastYear, ...] = FORECAST,
    tax_rate: float = DCF_ASSUMPTIONS.tax_rate,
) -> dict[str, float]:
    if not forecast or forecast[0].year != 2026:
        raise ValueError("首个预测年度必须是 2026")
    full_year_fcff = fcff(forecast[0], tax_rate)
    h1_fcff = actual_h1_fcff(tax_rate=tax_rate)
    h2_fcff = full_year_fcff - h1_fcff
    estimated_gap_fcff = h2_fcff * BALANCE_SHEET_TO_PRICE_DAYS / H2_DAYS
    post_price_fcff = h2_fcff * POST_PRICE_H2_DAYS / H2_DAYS
    return {
        "full_year_fcff": full_year_fcff,
        "h1_actual_fcff": h1_fcff,
        "h2_fcff": h2_fcff,
        "estimated_gap_fcff": estimated_gap_fcff,
        "post_price_fcff": post_price_fcff,
    }


def dcf(
    forecast: tuple[ForecastYear, ...] = FORECAST,
    *,
    wacc: float = DCF_ASSUMPTIONS.wacc,
    terminal_growth: float = DCF_ASSUMPTIONS.terminal_growth,
    tax_rate: float = DCF_ASSUMPTIONS.tax_rate,
    market: MarketAndBalanceSheet = MARKET,
) -> dict[str, object]:
    if not forecast:
        raise ValueError("显性期预测不能为空")
    if wacc <= terminal_growth:
        raise ValueError("WACC 必须高于永续增长率")

    rows: list[dict[str, float | int]] = []
    for row in forecast:
        row_fcff = fcff(row, tax_rate)
        rows.append(
            {
                "year": row.year,
                "ebitda": row.ebitda_rmb_bn,
                "da": row.da_rmb_bn,
                "capex": row.capex_rmb_bn,
                "delta_nwc": row.delta_nwc_rmb_bn,
                "fcff": row_fcff,
            }
        )

    bridge = h2_bridge(forecast, tax_rate)
    stub_discount_time = (POST_PRICE_H2_DAYS / 365) / 2
    stub_pv = bridge["post_price_fcff"] / (1 + wacc) ** stub_discount_time
    explicit_pv = stub_pv
    for index, row in enumerate(rows[1:]):
        discount_time = FIRST_FULL_YEAR_MIDPOINT + index
        present_value = row["fcff"] / (1 + wacc) ** discount_time
        row["pv"] = present_value
        row["discount_time"] = discount_time
        explicit_pv += present_value

    terminal_fcff = rows[-1]["fcff"] * (1 + terminal_growth)
    terminal_value = terminal_fcff / (wacc - terminal_growth)
    terminal_discount_time = 5 + POST_PRICE_H2_DAYS / 365
    terminal_pv = terminal_value / (1 + wacc) ** terminal_discount_time
    enterprise_value = explicit_pv + terminal_pv
    net_cash = net_cash_rmb_bn(market)
    equity_value = enterprise_value + net_cash + bridge["estimated_gap_fcff"]
    value_per_share = equity_value / market.shares_bn
    return {
        "rows": rows,
        **bridge,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
        "tax_rate": tax_rate,
        "stub_pv": stub_pv,
        "explicit_pv": explicit_pv,
        "terminal_fcff": terminal_fcff,
        "terminal_value": terminal_value,
        "terminal_pv": terminal_pv,
        "terminal_share": terminal_pv / enterprise_value,
        "terminal_discount_time": terminal_discount_time,
        "enterprise_value": enterprise_value,
        "net_cash": net_cash,
        "equity_value": equity_value,
        "value_per_share": value_per_share,
        "upside": value_per_share / market.price_rmb - 1,
    }


def sensitivity(
    wacc_values: tuple[float, ...] = (0.087, 0.0967, 0.107),
    growth_values: tuple[float, ...] = (0.015, 0.02, 0.025),
) -> dict[float, dict[float, float]]:
    return {
        wacc: {
            growth: dcf(wacc=wacc, terminal_growth=growth)["value_per_share"]
            for growth in growth_values
        }
        for wacc in wacc_values
    }


def scenario_valuations() -> dict[str, dict[str, object]]:
    """使用同一折现参数，计算三套经营与现金流情景。"""
    return {
        key: {
            "name_cn": scenario.name_cn,
            "thesis": scenario.thesis,
            "switch_conditions": scenario.switch_conditions,
            **dcf(scenario.forecast),
        }
        for key, scenario in SCENARIOS.items()
    }


def consensus_multiples(
    price_rmb: float = MARKET.price_rmb,
) -> dict[int, float]:
    return {year: price_rmb / eps for year, eps in CONSENSUS_EPS_RMB.items()}


def print_model() -> None:
    results = scenario_valuations()
    print("中天科技 2026-08-30 三情景 FCFF DCF")
    for key in ("downside", "base", "upside"):
        result = results[key]
        print(
            f"  {result['name_cn']}：{result['value_per_share']:.2f} 元/股，"
            f"相对 {MARKET.price_rmb:.2f} 元 {result['upside']:+.1%}"
        )
    print("基准情景现金流：")
    for row in results["base"]["rows"]:
        print(
            f"  {row['year']}: EBITDA {row['ebitda']:.2f}, "
            f"Capex {row['capex']:.2f}, ΔNWC {row['delta_nwc']:.2f}, "
            f"FCFF {row['fcff']:.2f} 十亿元"
        )
    base = results["base"]
    print(f"  2026H1 FCFF代理值：{base['h1_actual_fcff']:.2f} 十亿元")
    print(f"  估值日后H2 FCFF：{base['post_price_fcff']:.2f} 十亿元")
    print(f"  净现金：{base['net_cash']:.2f} 十亿元")


if __name__ == "__main__":
    print_model()
