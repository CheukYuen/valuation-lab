#!/usr/bin/env python3
"""Deterministic first-pass YOFC DCF and reverse-DCF calculation."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT_PATH = ROOT / "valuation-inputs.json"
OUTPUT_PATH = ROOT / "valuation-results.json"


def round_tree(value, digits=8):
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return {key: round_tree(item, digits) for key, item in value.items()}
    if isinstance(value, list):
        return [round_tree(item, digits) for item in value]
    return value


def forward_dcf(scenario, tax_rate, wacc, remaining_fraction):
    years = scenario["years"]
    ebit = [
        revenue * margin
        for revenue, margin in zip(scenario["revenue_bn"], scenario["ebit_margin"])
    ]
    fcff = [
        operating_profit * (1 - tax_rate) + da - capex + wc_effect
        for operating_profit, da, capex, wc_effect in zip(
            ebit,
            scenario["da_bn"],
            scenario["capex_bn"],
            scenario["working_capital_cash_effect_bn"],
        )
    ]

    terminal_fcff = ebit[-1] * (1 - tax_rate) * (
        1 - scenario["terminal_growth"] / scenario["terminal_roic"]
    )
    fcff[-1] = terminal_fcff
    discount_times = [remaining_fraction + index for index in range(len(years))]

    explicit_pv = 0.0
    for index, (cash_flow, discount_time) in enumerate(zip(fcff, discount_times)):
        period_fraction = remaining_fraction if index == 0 else 1.0
        explicit_pv += cash_flow * period_fraction / ((1 + wacc) ** discount_time)

    terminal_value = terminal_fcff * (1 + scenario["terminal_growth"]) / (
        wacc - scenario["terminal_growth"]
    )
    terminal_pv = terminal_value / ((1 + wacc) ** discount_times[-1])
    enterprise_value = explicit_pv + terminal_pv

    return {
        "years": years,
        "ebit_bn": ebit,
        "fcff_bn": fcff,
        "terminal_fcff_bn": terminal_fcff,
        "explicit_period_pv_bn": explicit_pv,
        "terminal_value_at_2032_bn": terminal_value,
        "terminal_value_pv_bn": terminal_pv,
        "terminal_value_share_of_ev": terminal_pv / enterprise_value,
        "enterprise_value_bn": enterprise_value,
    }


def reverse_ev(margin, revenue_bn, assumptions, early_fcff, wacc, remaining_fraction):
    tax_rate = assumptions["normalized_tax_rate"]
    cash_conversion = assumptions["fcff_to_nopat_ratio"]
    terminal_growth = assumptions["terminal_growth"]

    pv = early_fcff[0] * remaining_fraction / ((1 + wacc) ** remaining_fraction)
    pv += early_fcff[1] / ((1 + wacc) ** (remaining_fraction + 1))

    normalized_fcff = revenue_bn * margin * (1 - tax_rate) * cash_conversion
    for year_index in range(2, 7):
        pv += normalized_fcff / ((1 + wacc) ** (remaining_fraction + year_index))

    terminal_value = normalized_fcff * (1 + terminal_growth) / (wacc - terminal_growth)
    pv += terminal_value / ((1 + wacc) ** (remaining_fraction + 6))
    return pv


def solve_bisection(target, value_fn, low, high, iterations=120):
    if value_fn(low) > target or value_fn(high) < target:
        return None
    for _ in range(iterations):
        midpoint = (low + high) / 2
        if value_fn(midpoint) < target:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2


def main():
    data = json.loads(INPUT_PATH.read_text())
    market = data["market"]
    shares = data["shares"]
    capital = data["capital_structure"]
    wacc_inputs = data["wacc"]
    remaining_fraction = data["timing"]["remaining_2026_days"] / data["timing"]["days_in_year"]

    assert shares["a_issued"] + shares["h_issued_and_outstanding"] == shares["total_issued"]
    assert shares["a_issued"] - shares["a_treasury"] == shares["a_outstanding_ex_treasury"]
    assert (
        shares["a_outstanding_ex_treasury"] + shares["h_issued_and_outstanding"]
        == shares["total_outstanding_ex_treasury"]
    )

    a_price = market["a_share"]["close"]
    h_price_cny = market["h_share"]["close"] * market["hkd_cny"]["rate"]
    total_outstanding = shares["total_outstanding_ex_treasury"]

    actual_class_equity = (
        a_price * shares["a_outstanding_ex_treasury"]
        + h_price_cny * shares["h_issued_and_outstanding"]
    ) / 1e9
    a_equivalent_equity = a_price * total_outstanding / 1e9
    h_equivalent_equity = h_price_cny * total_outstanding / 1e9
    equity_values = {
        "actual_class_market_equity_bn": actual_class_equity,
        "a_price_equivalent_total_equity_bn": a_equivalent_equity,
        "h_price_equivalent_total_equity_bn": h_equivalent_equity,
    }

    bridge = (
        capital["interest_bearing_debt_including_lease_liabilities"]
        + capital["minority_interest"]
        - capital["cash_and_cash_equivalents_proxy"]
    )
    market_evs = {name.replace("equity", "ev"): value + bridge for name, value in equity_values.items()}

    cost_of_equity = (
        wacc_inputs["risk_free_rate"]
        + wacc_inputs["beta"] * wacc_inputs["equity_risk_premium"]
    )
    debt = capital["interest_bearing_debt_including_lease_liabilities"]
    computed_wacc = (
        actual_class_equity / (actual_class_equity + debt) * cost_of_equity
        + debt
        / (actual_class_equity + debt)
        * wacc_inputs["pre_tax_cost_of_debt"]
        * (1 - wacc_inputs["normalized_tax_rate"])
    )
    assert abs(computed_wacc - wacc_inputs["base_wacc"]) < 0.0005

    scenario_results = {}
    for name, scenario in data["scenarios"].items():
        rows = {}
        previous_ev = None
        for rate in wacc_inputs["sensitivity"]:
            result = forward_dcf(
                scenario,
                wacc_inputs["normalized_tax_rate"],
                rate,
                remaining_fraction,
            )
            equity_value = result["enterprise_value_bn"] - bridge
            result["equity_value_bn"] = equity_value
            result["equity_value_per_outstanding_share_cny"] = equity_value * 1e9 / total_outstanding
            if previous_ev is not None:
                assert result["enterprise_value_bn"] < previous_ev
            previous_ev = result["enterprise_value_bn"]
            rows[str(rate)] = result
        scenario_results[name] = rows

    base_rate_key = str(wacc_inputs["base_wacc"])
    assert (
        scenario_results["bear"][base_rate_key]["enterprise_value_bn"]
        < scenario_results["base"][base_rate_key]["enterprise_value_bn"]
        < scenario_results["bull"][base_rate_key]["enterprise_value_bn"]
    )

    reverse_assumptions = data["reverse_dcf"]
    bear_base_rate = scenario_results["bear"][base_rate_key]
    early_fcff = bear_base_rate["fcff_bn"][:2]
    reverse_targets = {
        "actual_class_market": market_evs["actual_class_market_ev_bn"],
        "a_price_equivalent": market_evs["a_price_equivalent_total_ev_bn"],
        "h_price_equivalent": market_evs["h_price_equivalent_total_ev_bn"],
    }
    reverse_results = {}
    for rate in wacc_inputs["sensitivity"]:
        margin_results = {}
        for name, target_ev in reverse_targets.items():
            solved_margin = solve_bisection(
                target_ev,
                lambda margin: reverse_ev(
                    margin,
                    reverse_assumptions["steady_revenue_bn"],
                    reverse_assumptions,
                    early_fcff,
                    rate,
                    remaining_fraction,
                ),
                0.0,
                2.0,
            )
            margin_results[name] = solved_margin
        reverse_results[str(rate)] = margin_results

    revenue_solve = {}
    fixed_margin = reverse_assumptions["fixed_margin_for_revenue_solve"]
    base_wacc = wacc_inputs["base_wacc"]
    for name, target_ev in reverse_targets.items():
        solved_revenue = solve_bisection(
            target_ev,
            lambda revenue: reverse_ev(
                fixed_margin,
                revenue,
                reverse_assumptions,
                early_fcff,
                base_wacc,
                remaining_fraction,
            ),
            0.0,
            300.0,
        )
        revenue_solve[name] = solved_revenue

    results = {
        "run": data["run"],
        "checks": {
            "share_reconciliation": "PASS",
            "treasury_shares_excluded": "PASS",
            "wacc_recomputed": "PASS",
            "wacc_monotonicity": "PASS",
            "scenario_order_at_base_wacc": "PASS",
        },
        "market_snapshot": {
            "a_price_cny": a_price,
            "h_price_hkd": market["h_share"]["close"],
            "h_price_cny": h_price_cny,
            "a_h_premium": a_price / h_price_cny - 1,
            "total_outstanding_ex_treasury": total_outstanding,
            **equity_values,
            "ev_bridge_bn": bridge,
            **market_evs,
        },
        "wacc": {
            "cost_of_equity": cost_of_equity,
            "computed_wacc": computed_wacc,
            "model_base_wacc": wacc_inputs["base_wacc"],
        },
        "timing": {"remaining_2026_fraction": remaining_fraction},
        "forward_dcf": scenario_results,
        "reverse_dcf": {
            "steady_revenue_bn": reverse_assumptions["steady_revenue_bn"],
            "implicit_steady_ebit_margin_by_wacc": reverse_results,
            "fixed_margin": fixed_margin,
            "implicit_steady_revenue_bn_at_base_wacc": revenue_solve,
        },
    }
    OUTPUT_PATH.write_text(json.dumps(round_tree(results), ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
