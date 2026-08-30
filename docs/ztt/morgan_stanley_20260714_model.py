#!/usr/bin/env python3
"""摩根士丹利 2026-07-14 中天科技 DCF 可见输入复核。

报告未披露 2027-2037 逐年 FCFF 和终值桥，因此脚本只复核可见资本成本、
经营预测派生值和目标价机械桥，不输出独立 DCF 目标价。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportInputs:
    years: tuple[int, ...] = (2025, 2026, 2027, 2028)
    revenue_rmb_m: tuple[float, ...] = (52_500, 62_480, 72_252, 84_380)
    ebitda_rmb_m: tuple[float, ...] = (4_770, 8_537, 10_773, 13_105)
    modelware_net_income_rmb_m: tuple[float, ...] = (2_902, 6_421, 8_306, 10_282)
    eps_rmb: tuple[float, ...] = (0.85, 1.88, 2.43, 3.01)
    shares_m: float = 3_413
    current_price_rmb: float = 42.85
    reported_market_cap_rmb_m: float = 146_245
    reported_enterprise_value_rmb_m: float = 134_728
    reported_target_price_rmb: float = 53.23
    reported_wacc: float = 0.0967
    risk_free_rate: float = 0.0315
    beta: float = 1.2
    equity_risk_premium: float = 0.045
    china_risk_premium: float = 0.02
    reported_cost_of_equity: float = 0.1055
    after_tax_cost_of_debt: float = 0.0525
    target_debt_to_capital: float = 0.20
    terminal_growth: float = 0.02


INPUTS = ReportInputs()


def cost_of_equity(
    risk_free_rate: float,
    beta: float,
    equity_risk_premium: float,
    china_risk_premium: float,
) -> float:
    return risk_free_rate + beta * equity_risk_premium + china_risk_premium


def visible_wacc(
    cost_of_equity_value: float,
    after_tax_cost_of_debt: float,
    debt_to_capital: float,
) -> float:
    equity_to_capital = 1 - debt_to_capital
    return equity_to_capital * cost_of_equity_value + debt_to_capital * after_tax_cost_of_debt


def growth_rates(values: tuple[float, ...]) -> tuple[float | None, ...]:
    if not values:
        return ()
    return (None,) + tuple(values[i] / values[i - 1] - 1 for i in range(1, len(values)))


def margins(
    numerators: tuple[float, ...], denominators: tuple[float, ...]
) -> tuple[float, ...]:
    if len(numerators) != len(denominators):
        raise ValueError("分子和分母期数必须一致")
    if any(value == 0 for value in denominators):
        raise ValueError("分母不能为零")
    return tuple(n / d for n, d in zip(numerators, denominators))


def implied_share_counts_m(
    net_income_rmb_m: tuple[float, ...], eps_rmb: tuple[float, ...]
) -> tuple[float, ...]:
    return margins(net_income_rmb_m, eps_rmb)


def independent_bridge(inputs: ReportInputs = INPUTS) -> dict[str, object]:
    coe = cost_of_equity(
        inputs.risk_free_rate,
        inputs.beta,
        inputs.equity_risk_premium,
        inputs.china_risk_premium,
    )
    calculated_wacc = visible_wacc(
        coe, inputs.after_tax_cost_of_debt, inputs.target_debt_to_capital
    )
    mechanical_net_cash = (
        inputs.reported_market_cap_rmb_m - inputs.reported_enterprise_value_rmb_m
    )
    target_equity_value = inputs.reported_target_price_rmb * inputs.shares_m
    return {
        "cost_of_equity": coe,
        "visible_wacc": calculated_wacc,
        "wacc_gap": inputs.reported_wacc - calculated_wacc,
        "revenue_growth": growth_rates(inputs.revenue_rmb_m),
        "ebitda_margin": margins(inputs.ebitda_rmb_m, inputs.revenue_rmb_m),
        "net_margin": margins(inputs.modelware_net_income_rmb_m, inputs.revenue_rmb_m),
        "implied_share_counts_m": implied_share_counts_m(
            inputs.modelware_net_income_rmb_m, inputs.eps_rmb
        ),
        "reported_upside": inputs.reported_target_price_rmb / inputs.current_price_rmb - 1,
        "target_equity_value_rmb_m": target_equity_value,
        "mechanical_net_cash_rmb_m": mechanical_net_cash,
        "target_ev_if_net_cash_unchanged_rmb_m": target_equity_value - mechanical_net_cash,
    }


def audit_summary() -> dict[str, str | bool]:
    return {
        "annual_fcff_2027_2037_status": "MISSING",
        "terminal_fcff_status": "MISSING",
        "discount_timing_status": "MISSING",
        "target_net_debt_bridge_status": "MISSING",
        "wacc_visible_formula_status": "PARTIAL",
        "target_price_status": "MISSING",
        "full_target_price_independently_reproducible": False,
    }


def dcf_target_price_from_visible_inputs(inputs: ReportInputs = INPUTS) -> float:
    raise ValueError("报告未披露2027-2037逐年FCFF、终值现金流和目标净债务桥")


def print_model(inputs: ReportInputs = INPUTS) -> None:
    result = independent_bridge(inputs)
    print("摩根士丹利 2026-07-14 中天科技 DCF 可见输入复核")
    print(f"  股权成本：3.15% + 1.2 × 4.5% + 2.0% = {result['cost_of_equity']:.2%}")
    print(f"  可见WACC：80% × 10.55% + 20% × 5.25% = {result['visible_wacc']:.2%}")
    print(f"  报告WACC：{inputs.reported_wacc:.2%}；差异 {result['wacc_gap']:.2%}")
    print(
        "  2026E-2028E收入增速："
        + ", ".join(f"{value:.1%}" for value in result["revenue_growth"][1:])
    )
    print(
        "  2026E-2028E EBITDA利润率："
        + ", ".join(f"{value:.1%}" for value in result["ebitda_margin"][1:])
    )
    print(
        f"  报告目标价 {inputs.reported_target_price_rmb:.2f} 元；"
        f"机械目标股权价值 {result['target_equity_value_rmb_m'] / 100:.2f} 亿元。"
    )
    print("  完整目标价复算状态：MISSING。")


if __name__ == "__main__":
    print_model()
