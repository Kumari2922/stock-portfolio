"""Step 5 - Financial performance metrics.

Consumes data/processed/stock_prices_clean.csv and produces the portfolio-level
and stock-level KPIs from the scope document.

Convention (see config.py): CAD, buy-and-hold. Shares are fixed on the first
trading day as investment_cad / close, and never change.

Outputs (data/processed/metrics/):
    portfolio_value_daily.csv       daily value and profit/loss per holding and in total
    portfolio_summary.csv           portfolio KPIs (one row, tidy key/value)
    stock_performance_summary.csv   per-stock return, risk, Sharpe, rank, ...
    portfolio_weights.csv           opening vs ending weight and contribution
    portfolio_sector_summary.csv    sector value, return and contribution

Run:  python3 python/metrics.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    END_DATE,
    INITIAL_INVESTMENT,
    PORTFOLIO,
    PROCESSED_DIR,
    REBALANCING,
    RISK_FREE_RATE,
    START_DATE,
    TRADING_DAYS_PER_YEAR,
)

TICKERS = list(PORTFOLIO)

# Step 5 outputs go in their own subfolder so they stay apart from the
# Step 3/4 tables in data/processed/.
METRICS_DIR = PROCESSED_DIR / "metrics"

# Risk level from annualised volatility of daily CAD returns. The cut-offs are
# a stated assumption, not a standard.
LOW_VOL, HIGH_VOL = 20.0, 35.0


def risk_level(vol_pct: float) -> str:
    if vol_pct < LOW_VOL:
        return "Low"
    if vol_pct < HIGH_VOL:
        return "Medium"
    return "High"


def pl_status(x):
    """'Profit' / 'Loss' / 'Break-even' for a value or a Series of values."""
    if isinstance(x, pd.Series):
        return pd.Series(np.select([x > 0, x < 0], ["Profit", "Loss"], "Break-even"), index=x.index)
    return "Profit" if x > 0 else "Loss" if x < 0 else "Break-even"


def max_drawdown(series: pd.Series) -> tuple[float, pd.Timestamp]:
    dd = series / series.cummax() - 1
    return dd.min() * 100, dd.idxmin()


def sharpe(daily_ret: pd.Series) -> float:
    excess = daily_ret - RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
    return excess.mean() / excess.std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def main() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PROCESSED_DIR / "stock_prices_clean.csv", parse_dates=["date"])
    df = df[df["ticker"].isin(TICKERS)]
    close = df.pivot(index="date", columns="ticker", values="close")[TICKERS].sort_index()
    close = close.loc[START_DATE:END_DATE].ffill()  # 1 missing day for RY/TD/TSLA
    assert close.notna().all().all(), "unfilled gaps in close prices"

    years = (close.index[-1] - close.index[0]).days / 365.25
    invest = pd.Series({t: PORTFOLIO[t][2] for t in TICKERS})
    assert abs(invest.sum() - INITIAL_INVESTMENT) < 1e-6

    # ---- Buy and hold: fixed share counts --------------------------------
    shares = invest / close.iloc[0]
    value = close * shares
    total = value.sum(axis=1)

    out = value.copy()
    out.columns = [f"value_{t}" for t in TICKERS]
    out.insert(0, "portfolio_value", total)
    out["profit_loss_cad"] = total - INITIAL_INVESTMENT
    out["profit_loss_status"] = pl_status(out["profit_loss_cad"])
    for t in TICKERS:
        out[f"profit_loss_{t}"] = value[t] - invest[t]
    out["portfolio_daily_return"] = total.pct_change()
    out["portfolio_drawdown_pct"] = (total / total.cummax() - 1) * 100
    out.index.name = "date"
    out.round(4).to_csv(METRICS_DIR / "portfolio_value_daily.csv")

    # ---- Portfolio KPIs ----------------------------------------------------
    port_ret = total.pct_change().dropna()
    final = total.iloc[-1]
    mdd, mdd_date = max_drawdown(total)
    # Portfolio growth rate: average of the calendar year-end changes
    ye = total.groupby(total.index.year).last()
    ye = pd.concat([pd.Series({close.index[0].year - 1: INITIAL_INVESTMENT}), ye])
    yearly = ye.pct_change().dropna() * 100

    best = (close.iloc[-1] / close.iloc[0] - 1).idxmax()
    worst = (close.iloc[-1] / close.iloc[0] - 1).idxmin()

    kpis = {
        "start_date": close.index[0].date(),
        "end_date": close.index[-1].date(),
        "years": round(years, 2),
        "currency": "CAD",
        "rebalancing": REBALANCING,
        "total_investment_cad": INITIAL_INVESTMENT,
        "current_portfolio_value_cad": round(final, 2),
        "profit_loss_cad": round(final - INITIAL_INVESTMENT, 2),
        "profit_loss_status": pl_status(final - INITIAL_INVESTMENT),
        "total_return_pct": round((final / INITIAL_INVESTMENT - 1) * 100, 2),
        "cagr_pct": round(((final / INITIAL_INVESTMENT) ** (1 / years) - 1) * 100, 2),
        "portfolio_growth_multiple": round(final / INITIAL_INVESTMENT, 2),
        "avg_annual_growth_pct": round(yearly.mean(), 2),
        "annualised_volatility_pct": round(port_ret.std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100, 2),
        "sharpe_ratio": round(sharpe(port_ret), 3),
        "risk_free_rate_pct": RISK_FREE_RATE * 100,
        "max_drawdown_pct": round(mdd, 2),
        "max_drawdown_date": mdd_date.date(),
        "best_stock": best,
        "worst_stock": worst,
        "avg_daily_volume_all_holdings": int(
            df.groupby("date")["volume"].sum().mean()
        ),
    }
    pd.Series(kpis, name="value").rename_axis("metric").to_csv(
        METRICS_DIR / "portfolio_summary.csv"
    )

    # ---- Stock performance summary ----------------------------------------
    rets = close.pct_change().dropna()
    rows = []
    for t in TICKERS:
        cum = (close[t].iloc[-1] / close[t].iloc[0] - 1) * 100
        vol = rets[t].std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
        dd, dd_date = max_drawdown(close[t])
        rows.append(
            {
                "ticker": t,
                "company_name": PORTFOLIO[t][0],
                "sector": PORTFOLIO[t][1],
                "investment_cad": invest[t],
                "shares": round(shares[t], 4),
                "purchase_price_cad": round(close[t].iloc[0], 4),
                "current_price_cad": round(close[t].iloc[-1], 4),
                "current_value_cad": round(value[t].iloc[-1], 2),
                "profit_loss_cad": round(value[t].iloc[-1] - invest[t], 2),
                "profit_loss_status": pl_status(value[t].iloc[-1] - invest[t]),
                "return_pct": round(cum, 2),
                "cagr_pct": round(((1 + cum / 100) ** (1 / years) - 1) * 100, 2),
                "annualised_volatility_pct": round(vol, 2),
                "sharpe_ratio": round(sharpe(rets[t]), 3),
                "max_drawdown_pct": round(dd, 2),
                "max_drawdown_date": dd_date.date(),
                "risk_level": risk_level(vol),
            }
        )
    stocks = pd.DataFrame(rows)
    stocks["return_rank"] = stocks["return_pct"].rank(ascending=False).astype(int)
    stocks["sharpe_rank"] = stocks["sharpe_ratio"].rank(ascending=False).astype(int)
    stocks["risk_rank_1_is_riskiest"] = (
        stocks["annualised_volatility_pct"].rank(ascending=False).astype(int)
    )
    stocks["performance_rank"] = (
        (stocks["return_rank"] + stocks["sharpe_rank"]).rank(method="min").astype(int)
    )
    stocks = stocks.sort_values("performance_rank")
    stocks.to_csv(METRICS_DIR / "stock_performance_summary.csv", index=False)

    # ---- Weights and contribution -----------------------------------------
    gain = value.iloc[-1] - invest
    weights = pd.DataFrame(
        {
            "ticker": TICKERS,
            "opening_weight_pct": (invest / invest.sum() * 100).round(2).values,
            "ending_value_cad": value.iloc[-1].round(2).values,
            "ending_weight_pct": (value.iloc[-1] / final * 100).round(2).values,
            "profit_loss_cad": gain.round(2).values,
            "profit_loss_status": pl_status(gain).values,
            "contribution_to_growth_pct": (gain / gain.sum() * 100).round(2).values,
        }
    ).sort_values("contribution_to_growth_pct", ascending=False)
    weights.to_csv(METRICS_DIR / "portfolio_weights.csv", index=False)

    # ---- Sector view (actual holdings, not equal-weight baskets) ----------
    sec = stocks.groupby("sector").agg(
        investment_cad=("investment_cad", "sum"),
        current_value_cad=("current_value_cad", "sum"),
    )
    sec["profit_loss_cad"] = sec["current_value_cad"] - sec["investment_cad"]
    sec["profit_loss_status"] = pl_status(sec["profit_loss_cad"])
    sec["return_pct"] = (sec["profit_loss_cad"] / sec["investment_cad"] * 100).round(2)
    sec["cagr_pct"] = (((1 + sec["return_pct"] / 100) ** (1 / years) - 1) * 100).round(2)
    sec["ending_weight_pct"] = (sec["current_value_cad"] / final * 100).round(2)
    sec["contribution_to_growth_pct"] = (
        sec["profit_loss_cad"] / sec["profit_loss_cad"].sum() * 100
    ).round(2)
    sec.sort_values("return_pct", ascending=False).round(2).to_csv(
        METRICS_DIR / "portfolio_sector_summary.csv"
    )

    # ---- Console summary ----------------------------------------------------
    pd.set_option("display.width", 200, "display.max_columns", 30)
    print(pd.Series(kpis).to_string())
    print()
    print(stocks[["ticker", "return_pct", "cagr_pct", "annualised_volatility_pct",
                  "sharpe_ratio", "risk_level", "return_rank", "sharpe_rank",
                  "performance_rank"]].to_string(index=False))
    print()
    print(weights.to_string(index=False))
    print()
    print(sec.sort_values("return_pct", ascending=False).to_string())


if __name__ == "__main__":
    main()