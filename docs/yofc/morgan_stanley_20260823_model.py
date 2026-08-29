#!/usr/bin/env python3
"""摩根士丹利 2026-08-23 长飞光纤 RIM 可见输入复核。

报告未披露完整剩余收益桥，因此脚本只复核 CAPM、经营预测派生值和 EPS
分母，不输出机械目标价。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportInputs:
    years: tuple[int, ...] = (2025, 2026, 2027, 2028)
    revenue_rmb_m: tuple[float, ...] = (14_252.1, 27_387.6, 34_486.6, 40_004.4)
    ebitda_rmb_m: tuple[float, ...] = (2_792.7, 10_131.1, 15_187.7, 13_964.1)
    modelware_net_income_rmb_m: tuple[float, ...] = (
        813.7,
        7_506.7,
        12_730.3,
        11_435.2,
    )
    eps_rmb: tuple[float, ...] = (1.0, 9.1, 15.4, 13.8)
    reported_target_price_hkd: float = 230.0
    reported_cost_of_equity: float = 0.11
    risk_free_rate: float = 0.03
    beta: float = 1.0
    equity_risk_premium: float = 0.08
    medium_term_growth: float = 0.15
    terminal_growth: float = 0.02


INPUTS = ReportInputs()


def capm_cost_of_equity(
    risk_free_rate: float, beta: float, equity_risk_premium: float
) -> float:
    """用 CAPM 可见输入复算股权成本。"""
    return risk_free_rate + beta * equity_risk_premium


def growth_rates(values: tuple[float, ...]) -> tuple[float | None, ...]:
    """返回从第二期开始的同比增速，首期为 None。"""
    if not values:
        return ()
    return (None,) + tuple(values[i] / values[i - 1] - 1 for i in range(1, len(values)))


def margins(
    numerators: tuple[float, ...], denominators: tuple[float, ...]
) -> tuple[float, ...]:
    """逐期计算利润率。"""
    if len(numerators) != len(denominators):
        raise ValueError("分子和分母期数必须一致")
    if any(value == 0 for value in denominators):
        raise ValueError("分母不能为零")
    return tuple(n / d for n, d in zip(numerators, denominators))


def implied_share_counts_m(
    net_income_rmb_m: tuple[float, ...], eps_rmb: tuple[float, ...]
) -> tuple[float, ...]:
    """由净利润和 EPS 反推各期加权平均股数，单位为百万股。"""
    return margins(net_income_rmb_m, eps_rmb)


def reported_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float | str]:
    """保存报告明示的 RIM 目标价与参数，不补齐缺失现金/权益桥。"""
    return {
        "method": "RIM",
        "reported_target_price_hkd": inputs.reported_target_price_hkd,
        "reported_cost_of_equity": inputs.reported_cost_of_equity,
        "medium_term_growth": inputs.medium_term_growth,
        "terminal_growth": inputs.terminal_growth,
    }


def independent_bridge(
    inputs: ReportInputs = INPUTS,
) -> dict[str, float | tuple[float | None, ...] | tuple[float, ...]]:
    """复核可见 CAPM、增长、利润率和 EPS 分母。"""
    return {
        "capm_cost_of_equity": capm_cost_of_equity(
            inputs.risk_free_rate, inputs.beta, inputs.equity_risk_premium
        ),
        "revenue_growth": growth_rates(inputs.revenue_rmb_m),
        "ebitda_margin": margins(inputs.ebitda_rmb_m, inputs.revenue_rmb_m),
        "net_margin": margins(
            inputs.modelware_net_income_rmb_m, inputs.revenue_rmb_m
        ),
        "implied_share_counts_m": implied_share_counts_m(
            inputs.modelware_net_income_rmb_m, inputs.eps_rmb
        ),
    }


def audit_summary(inputs: ReportInputs = INPUTS) -> dict[str, str | bool]:
    """返回 RIM 完整复算所缺输入。"""
    return {
        "target_price_status": "MISSING",
        "opening_book_value_status": "MISSING",
        "residual_income_series_status": "MISSING",
        "payout_path_status": "MISSING",
        "explicit_horizon_status": "MISSING",
        "terminal_value_bridge_status": "MISSING",
        "fx_source_status": "MISSING",
        "full_target_price_independently_reproducible": False,
    }


def rim_target_price_from_visible_inputs(inputs: ReportInputs = INPUTS) -> float:
    """拒绝用不完整 RIM 输入制造目标价。"""
    raise ValueError(
        "报告未披露期初账面价值、逐年剩余收益、分红路径、显性期和终值桥"
    )


def print_model(inputs: ReportInputs = INPUTS) -> None:
    reported = reported_bridge(inputs)
    independent = independent_bridge(inputs)
    audit = audit_summary(inputs)

    print("摩根士丹利 2026-08-23 长飞光纤 RIM 可见输入复核")
    print(
        f"  CAPM：3.0% + 1.0 × 8.0% = "
        f"{independent['capm_cost_of_equity']:.1%}"
    )
    print(
        "  2026E-2028E 收入增速："
        + ", ".join(
            f"{value:.1%}" for value in independent["revenue_growth"][1:]
        )
    )
    print(
        "  2026E-2028E ModelWare净利率："
        + ", ".join(f"{value:.1%}" for value in independent["net_margin"][1:])
    )
    print(
        "  净利润/EPS隐含股数（2025A-2028E，百万股）："
        + ", ".join(
            f"{value:.2f}" for value in independent["implied_share_counts_m"]
        )
    )
    print(
        f"  报告目标价 {reported['reported_target_price_hkd']:.2f} 港元；"
        f"完整复算状态 {audit['target_price_status']}。"
    )
    print("  中期增长15%和永续增长2%是RIM参数，不是逐年收入预测。")


if __name__ == "__main__":
    print_model()
