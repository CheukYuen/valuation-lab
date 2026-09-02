"""长飞光纤加权平均资本成本（WACC）的可复算推导。

定价日 2026-08-24。Beta 由 `beta_20260824_snapshot.json` 中的周收盘价回归得到，
脚本本身不联网；无风险利率和股权风险溢价目前只有券商参照值，状态为 `PARTIAL`。
本文件不产生投资建议，只把折现率从“直接给定的数”变成“可以逐项检查的推导”。
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path


SNAPSHOT_PATH = Path(__file__).with_name("beta_20260824_snapshot.json")

# --- CAPM 输入 ---------------------------------------------------------------
# 无风险利率与股权风险溢价：本项目尚未取得可复核的定价日中国 10 年期国债收益率与
# 股权风险溢价原始来源，因此只能落在两家券商的可见输入之间，取值状态为 `PARTIAL`。
# 高盛（R2）：3.5% + 1.2 × 6.5%；摩根士丹利（R4）：3.0% + 1.0 × 8.0%。
RISK_FREE_LOW = 0.030          # R4 可见输入
RISK_FREE_HIGH = 0.035         # R2 可见输入
RISK_FREE_MID = (RISK_FREE_LOW + RISK_FREE_HIGH) / 2
EQUITY_RISK_PREMIUM_LOW = 0.065    # R2 可见输入
EQUITY_RISK_PREMIUM_HIGH = 0.080   # R4 可见输入
EQUITY_RISK_PREMIUM_MID = (EQUITY_RISK_PREMIUM_LOW + EQUITY_RISK_PREMIUM_HIGH) / 2

# --- 债务成本 ---------------------------------------------------------------
# 2026H1 利息费用 1.29 亿元（S1）按半年年化；分母用 2025-12-31 与 2026-06-30 经济债务均值。
# 分子是权责发生制利息费用、分母是全部经济债务（含子公司股权回购款），口径不完全对齐，
# 资本化利息也未逐项检查，因此税前债务成本状态为 `PARTIAL`。
INTEREST_EXPENSE_2026H1 = 1.29
ANNUALIZED_INTEREST_EXPENSE = INTEREST_EXPENSE_2026H1 * 2
DEBT_2025 = 101.49
DEBT_2026H1 = 95.25315837
AVERAGE_DEBT = (DEBT_2025 + DEBT_2026H1) / 2
MARGINAL_TAX_RATE = 0.20  # 与 DCF 正常化税率一致

# --- 资本权重 ---------------------------------------------------------------
# 股权按定价日 A、H 两类股份各自价格计算的实际混合市值；债务与 EV 桥保持同一口径，
# 即使用 95.25 亿元全额经济债务而不是净债务（净债务已通过非经营资产单独加回）。
A_SHARES_YI = 4.06338314
H_SHARES_YI = 4.21566794
A_PRICE_CNY = 379.19
H_PRICE_HKD = 140.80
HKD_TO_CNY = 0.86542
PARENT_EQUITY_BOOK = 163.64
NON_CONTROLLING_INTEREST_BOOK = 40.15765431


@dataclass(frozen=True)
class BetaRegression:
    """单条 Beta 回归结果，含标准误与 95% 置信区间。"""

    name: str
    benchmark: str
    beta: float
    r_squared: float
    standard_error: float
    observations: int
    first_week: str
    last_week: str

    @property
    def confidence_interval(self) -> tuple[float, float]:
        half_width = 1.96 * self.standard_error
        return self.beta - half_width, self.beta + half_width


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _weekly_returns(closes: dict[str, float], dates: list[str]) -> list[float]:
    return [closes[dates[i]] / closes[dates[i - 1]] - 1 for i in range(1, len(dates))]


def regress_beta(
    security: str,
    benchmark: str,
    snapshot: dict | None = None,
    weeks: int | None = None,
) -> BetaRegression:
    """对周收益率做一元最小二乘回归，返回 Beta、R² 和标准误。

    只使用两条序列都有记录的周，避免停牌或假期造成的错位。
    """
    data = load_snapshot() if snapshot is None else snapshot
    series = data["series"]
    security_close = series[security]["close"]
    benchmark_close = series[benchmark]["close"]
    dates = sorted(set(security_close) & set(benchmark_close))
    if weeks is not None:
        dates = dates[-(weeks + 1) :]
    if len(dates) < 30:
        raise ValueError("样本周数过少，回归结果没有意义")

    stock = _weekly_returns(security_close, dates)
    market = _weekly_returns(benchmark_close, dates)
    n = len(stock)
    stock_mean = statistics.mean(stock)
    market_mean = statistics.mean(market)
    covariance = sum(
        (stock[i] - stock_mean) * (market[i] - market_mean) for i in range(n)
    ) / (n - 1)
    market_variance = sum((value - market_mean) ** 2 for value in market) / (n - 1)
    beta = covariance / market_variance
    correlation = covariance / (statistics.stdev(stock) * statistics.stdev(market))
    r_squared = correlation**2
    # OLS 斜率标准误的等价写法：SE(beta) = beta × sqrt((1 − R²) / R² / (n − 2))。
    standard_error = abs(beta) * math.sqrt((1 - r_squared) / r_squared / (n - 2))
    return BetaRegression(
        name=series[security]["name"],
        benchmark=series[benchmark]["name"],
        beta=beta,
        r_squared=r_squared,
        standard_error=standard_error,
        observations=n,
        first_week=dates[1],
        last_week=dates[-1],
    )


PEER_CODES = ("sz300308", "sz002281", "sz300394")


def peer_betas(snapshot: dict | None = None) -> list[BetaRegression]:
    data = load_snapshot() if snapshot is None else snapshot
    return [regress_beta(code, "sh000300", data) for code in PEER_CODES]


def peer_median_beta(snapshot: dict | None = None) -> float:
    return statistics.median(item.beta for item in peer_betas(snapshot))


def own_beta(snapshot: dict | None = None) -> BetaRegression:
    """主口径 Beta：A 股前复权周收益率对沪深300，五年全窗口。"""
    return regress_beta("sh601869", "sh000300", snapshot)


def market_value_of_equity() -> float:
    """定价日 A、H 两类股份各自计价后的实际混合市值。"""
    return A_SHARES_YI * A_PRICE_CNY + H_SHARES_YI * H_PRICE_HKD * HKD_TO_CNY


def book_value_of_equity() -> float:
    """账面权重口径下的股权：归母权益 + 少数股东权益。"""
    return PARENT_EQUITY_BOOK + NON_CONTROLLING_INTEREST_BOOK


def pre_tax_cost_of_debt() -> float:
    return ANNUALIZED_INTEREST_EXPENSE / AVERAGE_DEBT


def cost_of_equity(
    beta: float,
    risk_free: float = RISK_FREE_MID,
    equity_risk_premium: float = EQUITY_RISK_PREMIUM_MID,
) -> float:
    return risk_free + beta * equity_risk_premium


def wacc(
    beta: float | None = None,
    risk_free: float = RISK_FREE_MID,
    equity_risk_premium: float = EQUITY_RISK_PREMIUM_MID,
    *,
    weights: str = "market",
    tax_rate: float = MARGINAL_TAX_RATE,
    debt: float = DEBT_2026H1,
) -> float:
    """按 CAPM 股权成本、税后债务成本和资本权重计算 WACC。

    weights="market" 用定价日市值；weights="book" 用账面权益。两者差异极大，
    必须写明用的是哪一种，不能只报一个数。
    """
    beta_value = own_beta().beta if beta is None else beta
    if weights == "market":
        equity = market_value_of_equity()
    elif weights == "book":
        equity = book_value_of_equity()
    else:
        raise ValueError('weights 只接受 "market" 或 "book"')
    total = equity + debt
    equity_weight = equity / total
    debt_weight = debt / total
    return (
        equity_weight * cost_of_equity(beta_value, risk_free, equity_risk_premium)
        + debt_weight * pre_tax_cost_of_debt() * (1 - tax_rate)
    )


def unlever(beta: float, debt_to_equity: float, tax_rate: float = MARGINAL_TAX_RATE) -> float:
    """Hamada 去杠杆：βU = βL ÷ (1 + (1 − t) × D/E)。"""
    return beta / (1 + (1 - tax_rate) * debt_to_equity)


DERIVED_WACC = wacc()


def print_model() -> None:
    snapshot = load_snapshot()
    print("长飞光纤 WACC 推导（定价日 2026-08-24）")
    print(f"价格快照：{snapshot['_meta']['window']}，取数日 {snapshot['_meta']['fetched_at']}")

    print("\n1. Beta 回归（周收益率，最小二乘）")
    print(f"{'证券':<10}{'基准':<10}{'Beta':>7}{'R²':>7}{'SE':>7}{'95% 置信区间':>16}{'周数':>6}")
    rows = [
        regress_beta("sh601869", "sh000300", snapshot),
        regress_beta("hk06869", "hkHSI", snapshot),
        *peer_betas(snapshot),
    ]
    for row in rows:
        low, high = row.confidence_interval
        security = row.name.split("（")[0]
        benchmark = row.benchmark.split("（")[0]
        print(
            f"{security:<10}{benchmark:<10}{row.beta:>7.3f}"
            f"{row.r_squared:>7.3f}{row.standard_error:>7.3f}"
            f"{f'[{low:.2f}, {high:.2f}]':>16}{row.observations:>6}"
        )

    main = own_beta(snapshot)
    print(f"\n三家可比公司 Beta 中位数：{peer_median_beta(snapshot):.3f}")
    debt_to_equity = DEBT_2026H1 / market_value_of_equity()
    print(
        f"长飞市值口径 D/E = {debt_to_equity:.2%}，去杠杆 Beta = "
        f"{unlever(main.beta, debt_to_equity):.4f}（与原始 Beta 相差不足 4%）"
    )

    print("\n2. 债务成本与资本权重")
    print(
        f"税前债务成本 = {ANNUALIZED_INTEREST_EXPENSE:.2f} ÷ {AVERAGE_DEBT:.2f} = "
        f"{pre_tax_cost_of_debt():.2%}；税后 = {pre_tax_cost_of_debt() * (1 - MARGINAL_TAX_RATE):.2%}"
    )
    market_equity = market_value_of_equity()
    print(
        f"市值权重：股权 {market_equity:.2f}，债务 {DEBT_2026H1:.2f}，"
        f"债务占比 {DEBT_2026H1 / (market_equity + DEBT_2026H1):.2%}"
    )
    book_equity = book_value_of_equity()
    print(
        f"账面权重：股权 {book_equity:.2f}，债务 {DEBT_2026H1:.2f}，"
        f"债务占比 {DEBT_2026H1 / (book_equity + DEBT_2026H1):.2%}"
    )

    print("\n3. 股权成本与 WACC")
    combos = (
        ("R2 可见 rf 3.5%、ERP 6.5%", RISK_FREE_HIGH, EQUITY_RISK_PREMIUM_LOW),
        ("中值 rf 3.25%、ERP 7.25%", RISK_FREE_MID, EQUITY_RISK_PREMIUM_MID),
        ("R4 可见 rf 3.0%、ERP 8.0%", RISK_FREE_LOW, EQUITY_RISK_PREMIUM_HIGH),
    )
    for label, risk_free, premium in combos:
        print(
            f"{label:<28} Ke={cost_of_equity(main.beta, risk_free, premium):.2%}  "
            f"WACC(市值)={wacc(main.beta, risk_free, premium):.2%}  "
            f"WACC(账面)={wacc(main.beta, risk_free, premium, weights='book'):.2%}"
        )

    print("\n4. Beta 不确定性对 WACC 的影响（中值无风险利率与股权风险溢价，市值权重）")
    low, high = main.confidence_interval
    for label, beta in (
        ("置信区间下界", low),
        ("回归点估计", main.beta),
        ("置信区间上界", high),
        ("可比公司中位数", peer_median_beta(snapshot)),
    ):
        print(f"{label:<12} Beta={beta:.3f}  Ke={cost_of_equity(beta):.2%}  WACC={wacc(beta):.2%}")

    print(f"\n模型采用 WACC = {DERIVED_WACC:.4%}（市值权重、回归点估计 Beta、中值无风险利率与股权风险溢价）")


if __name__ == "__main__":
    print_model()
