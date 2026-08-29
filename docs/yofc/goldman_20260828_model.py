#!/usr/bin/env python3
"""高盛 2026-08-28 长飞光纤折现 P/E 的最小独立复算。

每股收益与每股价值单位为人民币元，目标价单位为港元。脚本只重放
报告第 2-3 页可见输入；未披露的汇率和目标倍数回归样本不会被猜测补齐。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportInputs:
    target_year_eps_rmb: float = 23.98
    target_pe_multiple: float = 14.6
    reported_cost_of_equity: float = 0.11
    discount_years: float = 3.0
    reported_target_price_hkd: float = 292.0
    risk_free_rate: float = 0.035
    beta: float = 1.2
    equity_risk_premium: float = 0.065


INPUTS = ReportInputs()


def discounted_pe_target_rmb(
    eps_rmb: float,
    pe_multiple: float,
    cost_of_equity: float,
    discount_years: float,
) -> float:
    """把目标年度 P/E 对应价值折回目标价时点。"""
    if cost_of_equity <= -1:
        raise ValueError("股权成本必须大于 -100%")
    if discount_years < 0:
        raise ValueError("折现年数不能为负")
    return eps_rmb * pe_multiple / (1 + cost_of_equity) ** discount_years


def capm_cost_of_equity(
    risk_free_rate: float, beta: float, equity_risk_premium: float
) -> float:
    """用 CAPM 可见输入复算股权成本。"""
    return risk_free_rate + beta * equity_risk_premium


def implied_cny_per_hkd(rmb_value: float, hkd_value: float) -> float:
    """由同一价值的人民币与港币列示值反推 1 港元对应人民币。"""
    if hkd_value == 0:
        raise ValueError("港币价值不能为零")
    return rmb_value / hkd_value


def rmb_to_hkd(rmb_value: float, cny_per_hkd: float) -> float:
    """按 1 HKD = x CNY 将人民币换算为港币。"""
    if cny_per_hkd <= 0:
        raise ValueError("汇率必须为正")
    return rmb_value / cny_per_hkd


def reported_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float]:
    """按报告采用的 11% 股权成本重放，并显式反推未披露汇率。"""
    discounted_value_rmb = discounted_pe_target_rmb(
        inputs.target_year_eps_rmb,
        inputs.target_pe_multiple,
        inputs.reported_cost_of_equity,
        inputs.discount_years,
    )
    implied_fx = implied_cny_per_hkd(
        discounted_value_rmb, inputs.reported_target_price_hkd
    )
    return {
        "undiscounted_2030_value_rmb": (
            inputs.target_year_eps_rmb * inputs.target_pe_multiple
        ),
        "discounted_target_value_rmb": discounted_value_rmb,
        "implied_cny_per_hkd": implied_fx,
        "reported_target_price_hkd": inputs.reported_target_price_hkd,
        "replayed_target_price_hkd": rmb_to_hkd(discounted_value_rmb, implied_fx),
    }


def independent_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float]:
    """用可见 CAPM 参数复算 11.3% 股权成本及其估值影响。"""
    capm_coe = capm_cost_of_equity(
        inputs.risk_free_rate, inputs.beta, inputs.equity_risk_premium
    )
    capm_value_rmb = discounted_pe_target_rmb(
        inputs.target_year_eps_rmb,
        inputs.target_pe_multiple,
        capm_coe,
        inputs.discount_years,
    )
    implied_fx = reported_bridge(inputs)["implied_cny_per_hkd"]
    return {
        "capm_cost_of_equity": capm_coe,
        "reported_cost_of_equity": inputs.reported_cost_of_equity,
        "cost_of_equity_gap": capm_coe - inputs.reported_cost_of_equity,
        "capm_discounted_value_rmb": capm_value_rmb,
        "capm_target_price_hkd_at_report_implied_fx": rmb_to_hkd(
            capm_value_rmb, implied_fx
        ),
    }


def audit_summary(inputs: ReportInputs = INPUTS) -> dict[str, float | str | bool]:
    """返回报告内部口径差异和证据缺口。"""
    independent = independent_bridge(inputs)
    return {
        "target_price_status": "PARTIAL",
        "target_multiple_basis_status": "MISSING",
        "fx_source_status": "MISSING",
        "discount_destination_conflict": True,
        "capm_gap_detected": abs(independent["cost_of_equity_gap"]) > 0.0001,
        "cost_of_equity_gap": independent["cost_of_equity_gap"],
        "full_target_price_independently_reproducible": False,
    }


def print_model(inputs: ReportInputs = INPUTS) -> None:
    reported = reported_bridge(inputs)
    independent = independent_bridge(inputs)
    audit = audit_summary(inputs)

    print("高盛 2026-08-28 长飞光纤折现 P/E 复算")
    print("\n一、按报告采用的 11% 股权成本重放")
    print(
        f"  2030E EPS {inputs.target_year_eps_rmb:.2f} × "
        f"{inputs.target_pe_multiple:.1f} = "
        f"{reported['undiscounted_2030_value_rmb']:.2f} 元"
    )
    print(
        f"  折现 {inputs.discount_years:.0f} 年后 "
        f"{reported['discounted_target_value_rmb']:.2f} 元"
    )
    print(
        "  用报告目标价反推 1 HKD = "
        f"{reported['implied_cny_per_hkd']:.6f} CNY，重放 "
        f"{reported['replayed_target_price_hkd']:.2f} 港元"
    )

    print("\n二、独立 CAPM 检查")
    print(
        f"  3.5% + 1.2 × 6.5% = "
        f"{independent['capm_cost_of_equity']:.1%}，"
        f"与报告采用值相差 {independent['cost_of_equity_gap']:.1%}"
    )
    print(
        "  按 11.3% 折现，在报告隐含汇率下为 "
        f"{independent['capm_target_price_hkd_at_report_implied_fx']:.2f} 港元"
    )

    print("\n三、证据边界")
    print(
        "  第2页与第3页折现目标年表述冲突；汇率来源和目标倍数回归样本未披露。"
    )
    print(
        f"  目标价状态 {audit['target_price_status']}，不能称为完整独立复算。"
    )


if __name__ == "__main__":
    print_model()
