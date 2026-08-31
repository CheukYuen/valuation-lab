#!/usr/bin/env python3
"""美银 2026-08-28 中天科技报告的可见估值输入复核。

报告披露 2026E-2028E 经营预测、自由现金流、当前价格 SOTP 拆分以及
DCF 的 WACC/永续增长率，但没有披露 2029E-2035E 逐年现金流、终值基数、
折现时点和目标净现金桥。因此脚本只复核可见数字，不复制造 65 元目标价。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportInputs:
    years: tuple[int, ...] = (2025, 2026, 2027, 2028)
    revenue_rmb_m: tuple[float, ...] = (52_500, 69_250, 83_924, 94_667)
    # 2025A EBITDA由报告第2页的52,500百万元收入和四舍五入后的8.2%利润率派生；
    # 2026E-2028E为报告第1页Key Changes列示值。
    ebitda_rmb_m: tuple[float, ...] = (4_305, 10_975.8, 16_094.1, 18_178.7)
    operating_profit_rmb_m: tuple[float, ...] = (2_916, 9_754, 14_783, 16_760)
    adjusted_net_income_rmb_m: tuple[float, ...] = (2_902, 8_780, 13_099, 14_865)
    eps_rmb: tuple[float, ...] = (0.85, 2.57, 3.84, 4.36)
    cfo_rmb_m: tuple[float, ...] = (4_751, 6_139, 10_352, 13_392)
    fcf_rmb_m: tuple[float, ...] = (3_127, 4_141, 8_093, 10_908)
    shares_m: float = 3_412.9
    report_price_rmb: float = 36.08
    target_price_rmb: float = 65.00
    previous_target_price_rmb: float = 73.30
    wacc: float = 0.09
    terminal_growth: float = 0.03
    beta: float = 0.98


@dataclass(frozen=True)
class SOTPLine:
    name: str
    net_income_rmb_m: float
    implied_current_pe: float
    valuation_rmb_m: float


INPUTS = ReportInputs()
SOTP_LINES = (
    SOTPLine("光通信", 5_720, 14.0, 80_079),
    SOTPLine("海洋", 1_980, 10.0, 19_802),
    SOTPLine("电网", 2_139, 8.0, 17_109),
    SOTPLine("其他", 1_101, 5.6, 6_150),
)

MORGAN_STANLEY = {
    "revenue_rmb_m": (62_480, 72_252, 84_380),
    "ebitda_rmb_m": (8_537, 10_773, 13_105),
    "net_income_rmb_m": (6_421, 8_306, 10_282),
}

DATAHUB_CONSENSUS_EPS = (1.88, 2.29, 2.72)


def growth_rates(values: tuple[float, ...]) -> tuple[float | None, ...]:
    if not values:
        return ()
    return (None,) + tuple(values[index] / values[index - 1] - 1 for index in range(1, len(values)))


def ratios(numerators: tuple[float, ...], denominators: tuple[float, ...]) -> tuple[float, ...]:
    if len(numerators) != len(denominators):
        raise ValueError("分子和分母期数必须一致")
    if any(value == 0 for value in denominators):
        raise ValueError("分母不能为零")
    return tuple(numerator / denominator for numerator, denominator in zip(numerators, denominators))


def visible_bridge(inputs: ReportInputs = INPUTS) -> dict[str, object]:
    target_equity_value = inputs.target_price_rmb * inputs.shares_m
    current_equity_value = inputs.report_price_rmb * inputs.shares_m
    return {
        "revenue_growth": growth_rates(inputs.revenue_rmb_m),
        "ebitda_margin": ratios(inputs.ebitda_rmb_m, inputs.revenue_rmb_m),
        "operating_margin": ratios(inputs.operating_profit_rmb_m, inputs.revenue_rmb_m),
        "net_margin": ratios(inputs.adjusted_net_income_rmb_m, inputs.revenue_rmb_m),
        "fcf_to_net_income": ratios(inputs.fcf_rmb_m, inputs.adjusted_net_income_rmb_m),
        "report_price_pe": tuple(inputs.report_price_rmb / eps for eps in inputs.eps_rmb),
        "target_price_pe": tuple(inputs.target_price_rmb / eps for eps in inputs.eps_rmb),
        "reported_upside": inputs.target_price_rmb / inputs.report_price_rmb - 1,
        "target_cut": inputs.target_price_rmb / inputs.previous_target_price_rmb - 1,
        "current_equity_value_rmb_m": current_equity_value,
        "target_equity_value_rmb_m": target_equity_value,
    }


def forecast_premia() -> dict[str, tuple[float, ...]]:
    bofa_revenue = INPUTS.revenue_rmb_m[1:]
    bofa_ebitda = INPUTS.ebitda_rmb_m[1:]
    bofa_net_income = INPUTS.adjusted_net_income_rmb_m[1:]
    return {
        "revenue_vs_morgan_stanley": ratios(bofa_revenue, MORGAN_STANLEY["revenue_rmb_m"]),
        "ebitda_vs_morgan_stanley": ratios(bofa_ebitda, MORGAN_STANLEY["ebitda_rmb_m"]),
        "net_income_vs_morgan_stanley": ratios(bofa_net_income, MORGAN_STANLEY["net_income_rmb_m"]),
        "eps_vs_datahub_consensus": ratios(INPUTS.eps_rmb[1:], DATAHUB_CONSENSUS_EPS),
    }


def sotp_bridge(lines: tuple[SOTPLine, ...] = SOTP_LINES) -> dict[str, object]:
    total_net_income = sum(line.net_income_rmb_m for line in lines)
    total_valuation = sum(line.valuation_rmb_m for line in lines)
    calculated_values = tuple(line.net_income_rmb_m * line.implied_current_pe for line in lines)
    return {
        "total_net_income_rmb_m": total_net_income,
        "total_valuation_rmb_m": total_valuation,
        "weighted_implied_pe": total_valuation / total_net_income,
        "calculated_values_rmb_m": calculated_values,
        "implied_price_rmb": total_valuation / INPUTS.shares_m,
    }


def audit_summary() -> dict[str, str | bool]:
    return {
        "annual_fcff_2029_2035_status": "MISSING",
        "terminal_fcff_status": "MISSING",
        "discount_timing_status": "MISSING",
        "target_net_cash_bridge_status": "MISSING",
        "current_price_sotp_status": "DERIVED/PARTIAL",
        "target_price_status": "MISSING",
        "full_target_price_independently_reproducible": False,
    }


def dcf_target_price_from_visible_inputs(inputs: ReportInputs = INPUTS) -> float:
    raise ValueError("报告未披露2029E-2035E逐年FCFF、终值现金流和目标净现金桥")


def print_model(inputs: ReportInputs = INPUTS) -> None:
    result = visible_bridge(inputs)
    premia = forecast_premia()
    sotp = sotp_bridge()
    print("美银 2026-08-28 中天科技可见估值输入复核")
    print(f"  报告价 {inputs.report_price_rmb:.2f} 元；目标价 {inputs.target_price_rmb:.2f} 元；机械空间 {result['reported_upside']:+.1%}")
    print(
        "  2026E-2028E EBITDA利润率："
        + ", ".join(f"{value:.1%}" for value in result["ebitda_margin"][1:])
    )
    print(
        "  相对大摩净利润溢价："
        + ", ".join(f"{value - 1:+.1%}" for value in premia["net_income_vs_morgan_stanley"])
    )
    print(f"  当前价格SOTP：{sotp['total_valuation_rmb_m'] / 100:.2f} 亿元，{sotp['implied_price_rmb']:.2f} 元/股")
    print(f"  65元机械目标股权价值：{result['target_equity_value_rmb_m'] / 100:.2f} 亿元")
    print("  完整DCF目标价复算状态：MISSING")


if __name__ == "__main__":
    print_model()
