#!/usr/bin/env python3
"""杰富瑞 2026-07-22 长飞光纤 SOTP 的最小独立复算。

金额单位为人民币百万元（Rmb m），每股价值除外。脚本只重放研报第 5 页
明确列示的输入，并单独展示按公开公式机械复算的结果；缺失的估值桥不会被猜测补齐。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportInputs:
    yofc_shares_m: float = 827.905108
    of_2028_book_value_rmb_m: float = 29_061.0
    of_2028_pb_multiple: float = 3.56
    of_2027_eps_rmb: float = 9.37
    of_2027_pe_multiple: float = 14.1
    reported_of_average_tp_rmb: float = 121.78
    everprox_value_per_share_rmb: float = 8.22
    diversified_value_per_share_rmb: float = 2.74
    reported_sotp_pt_rmb: float = 132.73
    reported_sotp_pt_hkd: float = 153.74
    reported_2026_net_profit_rmb_m: float = 8_702.0
    reported_2026_eps_rmb: float = 11.44


INPUTS = ReportInputs()


def pb_target_per_share(
    book_value_rmb_m: float, pb_multiple: float, shares_m: float
) -> float:
    """用分部账面价值和 P/B 倍数计算每股股权价值。"""
    return book_value_rmb_m * pb_multiple / shares_m


def pe_target_per_share(eps_rmb: float, pe_multiple: float) -> float:
    """用分部 EPS 和 P/E 倍数计算每股股权价值。"""
    return eps_rmb * pe_multiple


def simple_average(*values: float) -> float:
    """返回等权算术平均；至少需要一个值。"""
    if not values:
        raise ValueError("simple_average 至少需要一个值")
    return sum(values) / len(values)


def implied_cny_per_hkd(rmb_value: float, hkd_value: float) -> float:
    """由同一价值的人民币和港币列示值反推 1 港元对应人民币。"""
    return rmb_value / hkd_value


def rmb_to_hkd(rmb_value: float, cny_per_hkd: float) -> float:
    """按 1 HKD = x CNY 把人民币价值换算为港币。"""
    return rmb_value / cny_per_hkd


def implied_share_count_m(net_profit_rmb_m: float, eps_rmb: float) -> float:
    """由归母净利润和 EPS 反推加权平均股数，单位为百万股。"""
    return net_profit_rmb_m / eps_rmb


def reported_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float]:
    """重放研报列示值，不把未披露的平均/折现桥猜成事实。"""
    component_sum_rmb = (
        inputs.reported_of_average_tp_rmb
        + inputs.everprox_value_per_share_rmb
        + inputs.diversified_value_per_share_rmb
    )
    fx = implied_cny_per_hkd(
        inputs.reported_sotp_pt_rmb, inputs.reported_sotp_pt_hkd
    )
    return {
        "reported_of_average_tp_rmb": inputs.reported_of_average_tp_rmb,
        "component_sum_rmb": component_sum_rmb,
        "reported_sotp_pt_rmb": inputs.reported_sotp_pt_rmb,
        "component_rounding_gap_rmb": inputs.reported_sotp_pt_rmb
        - component_sum_rmb,
        "implied_cny_per_hkd": fx,
        "reported_sotp_pt_hkd": rmb_to_hkd(inputs.reported_sotp_pt_rmb, fx),
    }


def independent_bridge(inputs: ReportInputs = INPUTS) -> dict[str, float]:
    """按第 5 页可见输入机械复算 P/B、P/E、简单平均和 SOTP。"""
    pb_tp = pb_target_per_share(
        inputs.of_2028_book_value_rmb_m,
        inputs.of_2028_pb_multiple,
        inputs.yofc_shares_m,
    )
    pe_tp = pe_target_per_share(
        inputs.of_2027_eps_rmb, inputs.of_2027_pe_multiple
    )
    average_tp = simple_average(pb_tp, pe_tp)
    total_rmb = (
        average_tp
        + inputs.everprox_value_per_share_rmb
        + inputs.diversified_value_per_share_rmb
    )
    fx = implied_cny_per_hkd(
        inputs.reported_sotp_pt_rmb, inputs.reported_sotp_pt_hkd
    )
    return {
        "pb_tp_rmb": pb_tp,
        "pe_tp_rmb": pe_tp,
        "simple_average_of_tp_rmb": average_tp,
        "average_bridge_gap_rmb": inputs.reported_of_average_tp_rmb - average_tp,
        "independent_sotp_rmb": total_rmb,
        "independent_sotp_hkd_at_report_implied_fx": rmb_to_hkd(total_rmb, fx),
    }


def audit_summary(inputs: ReportInputs = INPUTS) -> dict[str, float | str | bool]:
    """返回文档和测试共同使用的关键复核状态。"""
    independent = independent_bridge(inputs)
    implied_shares = implied_share_count_m(
        inputs.reported_2026_net_profit_rmb_m, inputs.reported_2026_eps_rmb
    )
    return {
        "average_bridge_status": "MISSING",
        "average_bridge_gap_rmb": independent["average_bridge_gap_rmb"],
        "average_bridge_gap_detected": abs(
            independent["average_bridge_gap_rmb"]
        )
        > 0.01,
        "everprox_upstream_status": "PARTIAL",
        "diversified_upstream_status": "MISSING",
        "implied_2026_share_count_m": implied_shares,
        "reported_period_end_share_count_m": inputs.yofc_shares_m,
        "share_count_gap_m": implied_shares - inputs.yofc_shares_m,
    }


def print_model(inputs: ReportInputs = INPUTS) -> None:
    reported = reported_bridge(inputs)
    independent = independent_bridge(inputs)
    audit = audit_summary(inputs)

    print("杰富瑞 2026-07-22 长飞光纤 SOTP 复算（每股价值）")
    print("\n一、按报告列示值重放")
    print(
        f"  光纤主业平均价值 {reported['reported_of_average_tp_rmb']:.2f} 元"
    )
    print(
        "  + EverProX 8.22 + 多元业务 2.74"
        f" = {reported['component_sum_rmb']:.2f} 元"
    )
    print(
        f"  报告列示 {reported['reported_sotp_pt_rmb']:.2f} 元 / "
        f"{reported['reported_sotp_pt_hkd']:.2f} 港元"
    )
    print(
        f"  组件与报告合计的舍入差 {reported['component_rounding_gap_rmb']:.2f} 元；"
        f"报告隐含 1 HKD = {reported['implied_cny_per_hkd']:.5f} CNY"
    )

    print("\n二、按公开公式独立复算")
    print(f"  P/B 路径 {independent['pb_tp_rmb']:.2f} 元")
    print(f"  P/E 路径 {independent['pe_tp_rmb']:.2f} 元")
    print(f"  简单平均 {independent['simple_average_of_tp_rmb']:.2f} 元")
    print(
        "  报告平均值相对简单平均的缺口 "
        f"{independent['average_bridge_gap_rmb']:.2f} 元，状态 "
        f"{audit['average_bridge_status']}"
    )
    print(
        f"  机械 SOTP {independent['independent_sotp_rmb']:.2f} 元 / "
        f"{independent['independent_sotp_hkd_at_report_implied_fx']:.2f} 港元"
    )

    print("\n三、分母检查")
    print(
        "  2026E 净利润/EPS 隐含股数 "
        f"{audit['implied_2026_share_count_m']:.2f} 百万股；"
        "期末已发行股数 "
        f"{audit['reported_period_end_share_count_m']:.2f} 百万股；"
        f"差额 {audit['share_count_gap_m']:.2f} 百万股"
    )
    print("  单家券商预测，不是公司指引或市场共识。")


if __name__ == "__main__":
    print_model()
