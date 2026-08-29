#!/usr/bin/env python3
"""野村 2026-08-21 长飞光纤 FY27 P/E 的最小独立复算。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportInputs:
    fy2027_eps_rmb: float = 9.75
    target_pe_multiple: float = 23.7
    reported_target_price_hkd: float = 266.0


INPUTS = ReportInputs()


def pe_target_per_share(eps_rmb: float, pe_multiple: float) -> float:
    """用预测 EPS 和目标 P/E 计算人民币每股价值。"""
    return eps_rmb * pe_multiple


def implied_cny_per_hkd(rmb_value: float, hkd_value: float) -> float:
    """由人民币价值和港币目标价反推 1 港元对应人民币。"""
    if hkd_value == 0:
        raise ValueError("港币目标价不能为零")
    return rmb_value / hkd_value


def rmb_to_hkd(rmb_value: float, cny_per_hkd: float) -> float:
    """按 1 HKD = x CNY 将人民币换算为港币。"""
    if cny_per_hkd <= 0:
        raise ValueError("汇率必须为正")
    return rmb_value / cny_per_hkd


def reported_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float]:
    """保存报告明示目标价，并反推报告未明示的汇率。"""
    target_rmb = pe_target_per_share(
        inputs.fy2027_eps_rmb, inputs.target_pe_multiple
    )
    implied_fx = implied_cny_per_hkd(target_rmb, inputs.reported_target_price_hkd)
    return {
        "target_value_rmb": target_rmb,
        "implied_cny_per_hkd": implied_fx,
        "reported_target_price_hkd": inputs.reported_target_price_hkd,
    }


def independent_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float]:
    """机械复算 P/E 路径；隐含汇率只用于重放，不升级为报告事实。"""
    reported = reported_bridge(inputs)
    return {
        "pe_target_value_rmb": pe_target_per_share(
            inputs.fy2027_eps_rmb, inputs.target_pe_multiple
        ),
        "replayed_target_price_hkd": rmb_to_hkd(
            reported["target_value_rmb"], reported["implied_cny_per_hkd"]
        ),
    }


def audit_summary(inputs: ReportInputs = INPUTS) -> dict[str, str | bool]:
    """返回目标倍数、汇率和经营预测的证据状态。"""
    return {
        "target_price_status": "PARTIAL",
        "peer_median_basis_status": "PARTIAL",
        "fx_source_status": "MISSING",
        "full_annual_forecast_status": "MISSING",
        "full_target_price_independently_reproducible": False,
    }


def print_model(inputs: ReportInputs = INPUTS) -> None:
    reported = reported_bridge(inputs)
    independent = independent_bridge(inputs)
    audit = audit_summary(inputs)

    print("野村 2026-08-21 长飞光纤 FY27 P/E 复算")
    print(
        f"  FY27 EPS {inputs.fy2027_eps_rmb:.2f} 元 × "
        f"{inputs.target_pe_multiple:.1f} 倍 = "
        f"{reported['target_value_rmb']:.3f} 元"
    )
    print(
        "  用报告目标价反推 1 HKD = "
        f"{reported['implied_cny_per_hkd']:.6f} CNY，重放 "
        f"{independent['replayed_target_price_hkd']:.2f} 港元"
    )
    print(
        "  WIND H股线缆公司中位数缺公司名单、取样日和统计明细；"
        f"目标价状态 {audit['target_price_status']}。"
    )


if __name__ == "__main__":
    print_model()
