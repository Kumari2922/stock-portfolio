"""Step 4 - Exploratory Data Analysis.

Consumes data/processed/stock_prices_clean.csv (written by clean_data.py) and
produces the four analysis blocks the roadmap asks for - price, return, risk
and relationship analysis - as a set of metric tables in data/processed/ and
charts in reports/figures/.

Run:  python3 python/eda.py
"""

from __future__ import annotations

import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter

import viz_style as vs
from config import (
    CURRENCY,
    END_DATE,
    FIGURES_DIR,
    PORTFOLIO,
    PROCESSED_DIR,
    REBALANCING,
    REPORTS_DIR,
    START_DATE,
    TRADING_DAYS_PER_YEAR,
)

PORTFOLIO_TICKERS = list(PORTFOLIO)
DIVERGING_CMAP = LinearSegmentedColormap.from_list("blue_red", vs.DIVERGING[::-1])
PCT = FuncFormatter(lambda v, _: f"{v:,.0f}%")


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------
def load_clean() -> pd.DataFrame:
    path = PROCESSED_DIR / "stock_prices_clean.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found - run python/clean_data.py first")
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def _spread_labels(values: np.ndarray, min_gap: float) -> np.ndarray:
    """Nudge descending label positions apart so stacked end-labels stay legible.

    `values` must already be sorted high to low, in axis units.
    """
    out = values.astype(float).copy()
    for i in range(1, len(out)):
        if out[i - 1] - out[i] < min_gap:
            out[i] = out[i - 1] - min_gap
    return out


def wide_close(df: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Close prices as a date x ticker matrix, restricted to shared dates."""
    wide = df.pivot(index="date", columns="ticker", values="close")
    return wide.loc[:, [t for t in tickers if t in wide.columns]].dropna(how="any")


# --------------------------------------------------------------------------
# Metric tables
# --------------------------------------------------------------------------
def price_and_return_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker price, return and risk summary over each ticker's own history."""
    rows = []
    for ticker, g in df.groupby("ticker"):
        g = g.sort_values("date")
        close = g["close"]
        rets = g["daily_return"].dropna()
        years = (g["date"].iloc[-1] - g["date"].iloc[0]).days / 365.25

        cumulative = close.iloc[-1] / close.iloc[0] - 1
        cagr = (close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan
        vol = rets.std() * np.sqrt(TRADING_DAYS_PER_YEAR)

        # Same stock measured in its listing currency, so the contribution of
        # USD/CAD movement to the CAD result can be read off directly.
        usd = g["close_usd"]
        rets_usd = usd.pct_change().dropna()
        cumulative_usd = usd.iloc[-1] / usd.iloc[0] - 1
        cagr_usd = (usd.iloc[-1] / usd.iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan
        vol_usd = rets_usd.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        drawdown_usd = usd / usd.cummax() - 1
        fx_move = g["usdcad"].iloc[-1] / g["usdcad"].iloc[0] - 1

        running_max = close.cummax()
        drawdown = close / running_max - 1
        trough = drawdown.idxmin()

        rows.append(
            {
                "ticker": ticker,
                "company_name": g["company_name"].iloc[0],
                "sector": g["sector"].iloc[0],
                "in_portfolio": bool(g["in_portfolio"].iloc[0]),
                "first_date": g["date"].iloc[0].date(),
                "last_date": g["date"].iloc[-1].date(),
                "years_of_history": round(years, 2),
                "trading_days": len(g),
                "first_close_cad": round(close.iloc[0], 4),
                "last_close_cad": round(close.iloc[-1], 2),
                "min_close_cad": round(close.min(), 4),
                "max_close_cad": round(close.max(), 2),
                "cumulative_return_pct": round(100 * cumulative, 2),
                "cagr_pct": round(100 * cagr, 2),
                "cumulative_return_usd_pct": round(100 * cumulative_usd, 2),
                "cagr_usd_pct": round(100 * cagr_usd, 2),
                "fx_move_pct": round(100 * fx_move, 2),
                "fx_share_of_cagr_pp": round(100 * (cagr - cagr_usd), 2),
                "mean_daily_return_pct": round(100 * rets.mean(), 4),
                "daily_volatility_pct": round(100 * rets.std(), 4),
                "annualised_volatility_pct": round(100 * vol, 2),
                "annualised_volatility_usd_pct": round(100 * vol_usd, 2),
                "best_day_pct": round(100 * rets.max(), 2),
                "worst_day_pct": round(100 * rets.min(), 2),
                "positive_days_pct": round(100 * (rets > 0).mean(), 2),
                "max_drawdown_pct": round(100 * drawdown.min(), 2),
                "max_drawdown_usd_pct": round(100 * drawdown_usd.min(), 2),
                "max_drawdown_date": g.loc[trough, "date"].date(),
                "avg_daily_volume": int(g["volume"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("cagr_pct", ascending=False).reset_index(drop=True)


def monthly_returns(df: pd.DataFrame) -> pd.DataFrame:
    m = (
        df.set_index("date")
        .groupby("ticker")["close"]
        .resample("ME")
        .last()
        .reset_index()
    )
    m["monthly_return_pct"] = 100 * m.groupby("ticker")["close"].pct_change()
    m["month"] = m["date"].dt.to_period("M").astype(str)
    return m.dropna(subset=["monthly_return_pct"])[
        ["ticker", "month", "close", "monthly_return_pct"]
    ].reset_index(drop=True)


def annual_returns(df: pd.DataFrame) -> pd.DataFrame:
    a = (
        df.set_index("date")
        .groupby("ticker")["close"]
        .resample("YE")
        .last()
        .reset_index()
    )
    a["year"] = a["date"].dt.year
    a["annual_return_pct"] = 100 * a.groupby("ticker")["close"].pct_change()
    return a.dropna(subset=["annual_return_pct"])[
        ["ticker", "year", "close", "annual_return_pct"]
    ].reset_index(drop=True)


def correlation_matrix(df: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    wide = wide_close(df, tickers)
    return wide.pct_change().dropna().corr()


def sector_summary(df: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    """Equal-weighted sector view across the portfolio holdings only."""
    port = metrics[metrics["in_portfolio"]]
    rows = []
    for sector, g in port.groupby("sector"):
        tickers = sorted(g["ticker"])
        wide = wide_close(df[df["ticker"].isin(tickers)], tickers)
        indexed = wide / wide.iloc[0]
        basket = indexed.mean(axis=1)  # equal-weighted sector basket
        years = (wide.index[-1] - wide.index[0]).days / 365.25
        basket_rets = basket.pct_change().dropna()
        rows.append(
            {
                "sector": sector,
                "tickers": ", ".join(tickers),
                "cumulative_return_pct": round(100 * (basket.iloc[-1] - 1), 2),
                "cagr_pct": round(100 * (basket.iloc[-1] ** (1 / years) - 1), 2),
                "annualised_volatility_pct": round(
                    100 * basket_rets.std() * np.sqrt(TRADING_DAYS_PER_YEAR), 2
                ),
                "max_drawdown_pct": round(100 * (basket / basket.cummax() - 1).min(), 2),
                "avg_daily_volume": int(
                    df[df["ticker"].isin(tickers)].groupby("ticker")["volume"].mean().mean()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("cagr_pct", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def chart_indexed_growth(df: pd.DataFrame) -> None:
    wide = wide_close(df, PORTFOLIO_TICKERS)
    indexed = 100 * wide / wide.iloc[0]

    fig, ax = plt.subplots(figsize=(11, 6))
    for ticker in PORTFOLIO_TICKERS:
        ax.plot(
            indexed.index, indexed[ticker].values, color=vs.TICKER_COLOR[ticker], linewidth=2.0
        )
    # End labels, nudged apart so the clustered finishers stay readable.
    finals = indexed.iloc[-1].sort_values(ascending=False)
    offsets = _spread_labels(np.log10(finals.values), min_gap=0.055)
    for ticker, y in zip(finals.index, offsets):
        ax.annotate(
            f" {ticker}  {finals[ticker]:,.0f}",
            xy=(indexed.index[-1], 10**y),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=vs.TICKER_COLOR[ticker],
        )
    ax.set_yscale("log")
    ax.set_yticks([100, 300, 1000, 3000, 10000, 30000])
    ax.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylabel("CAD index (17 Sep 2010 = 100, log scale)")
    ax.set_xlabel("")
    ax.set_xlim(indexed.index[0], indexed.index[-1] + pd.Timedelta(days=560))
    best, worst = finals.index[0], finals.index[-1]
    ax.set_title(
        f"{best} turned 100 into {finals.iloc[0]:,.0f} in CAD - "
        f"{worst} into {finals.iloc[-1]:,.0f}"
    )
    vs.caption(
        fig,
        "Price-only growth of each holding in CAD, indexed to 100 at the start of the analysis "
        "window. Buy and hold, no rebalancing. Log scale, so equal vertical distance is equal "
        "percentage change. Source: data/processed/stock_prices_clean.csv.",
    )
    fig.savefig(FIGURES_DIR / "01_indexed_growth.png")
    plt.close(fig)


def chart_annual_returns_heatmap(annual: pd.DataFrame) -> None:
    pivot = (
        annual[annual["ticker"].isin(PORTFOLIO_TICKERS)]
        .pivot(index="year", columns="ticker", values="annual_return_pct")
        .reindex(columns=PORTFOLIO_TICKERS)
        .sort_index(ascending=False)
    )
    # Tesla's +743% in 2020 would flatten every other cell on a full-range scale,
    # so the colour is clipped at +/-100% and the true value stays in the label.
    vmax = 100.0
    labels = [f"{y} YTD" if y == pivot.index.max() else str(y) for y in pivot.index]

    fig, ax = plt.subplots(figsize=(8.5, 8))
    ax.grid(False)
    im = ax.imshow(
        pivot.values,
        cmap=DIVERGING_CMAP,
        norm=TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax),
        aspect="auto",
    )
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, fontweight="bold")
    ax.set_yticks(range(len(pivot.index)), labels)
    ax.xaxis.set_ticks_position("top")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    for i, year in enumerate(pivot.index):
        for j, ticker in enumerate(pivot.columns):
            v = pivot.iloc[i, j]
            if pd.isna(v):
                continue
            ax.text(
                j,
                i,
                f"{v:,.0f}",
                ha="center",
                va="center",
                fontsize=8.5,
                color="#ffffff" if abs(v) > 0.7 * vmax else vs.TEXT_PRIMARY,
            )
    cbar = fig.colorbar(im, ax=ax, shrink=0.35, pad=0.03, extend="both")
    cbar.set_label("Annual return (%)", fontsize=9, color=vs.TEXT_SECONDARY)
    cbar.outline.set_visible(False)
    ax.set_title("Calendar-year returns: every holding lost money in 2022", pad=34)
    vs.caption(
        fig,
        "Calendar-year price return in CAD per holding, blue positive / red negative, on the last "
        "close of each year. Colour is clipped at +/-100%; cell labels carry the true value. 2026 "
        "runs to 17 Sep only. Source: data/processed/annual_returns.csv.",
    )
    fig.savefig(FIGURES_DIR / "02_annual_returns_heatmap.png")
    plt.close(fig)


def chart_risk_return(metrics: pd.DataFrame) -> None:
    m = metrics[metrics["in_portfolio"]].copy()

    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.scatter(
        m["annualised_volatility_pct"],
        m["cagr_pct"],
        s=150,
        color=vs.SEQUENTIAL_BLUE,
        edgecolor=vs.SURFACE,
        linewidth=2,
        zorder=3,
    )
    # RY and TD sit almost on top of each other; push TD's label out to the side.
    label_offset = {"TD": (16, -4)}
    for _, r in m.iterrows():
        ax.annotate(
            f"{r['ticker']}",
            xy=(r["annualised_volatility_pct"], r["cagr_pct"]),
            xytext=label_offset.get(r["ticker"], (0, 13)),
            textcoords="offset points",
            ha="left" if r["ticker"] in label_offset else "center",
            fontsize=9.5,
            fontweight="bold",
            color=vs.TEXT_PRIMARY,
        )
    ax.axhline(m["cagr_pct"].mean(), color=vs.TEXT_MUTED, linewidth=1, linestyle=(0, (4, 4)), zorder=1)
    ax.axvline(
        m["annualised_volatility_pct"].mean(),
        color=vs.TEXT_MUTED,
        linewidth=1,
        linestyle=(0, (4, 4)),
        zorder=1,
    )
    ax.annotate(
        "higher return,\nhigher risk",
        xy=(0.98, 0.97),
        xycoords="axes fraction",
        ha="right",
        va="top",
        fontsize=8.5,
        color=vs.TEXT_MUTED,
    )
    ax.margins(x=0.08, y=0.12)
    ax.set_xlabel("Annualised volatility (%)")
    ax.set_ylabel("Annualised CAD return, CAGR (%)")
    ax.xaxis.set_major_formatter(PCT)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_title("Higher returns came with bigger swings - but not proportionally")
    vs.caption(
        fig,
        "Annualised CAD price return against annualised volatility of daily CAD returns, per "
        "holding, over each stock's full window. Dashed lines mark the seven-stock averages. "
        "Source: data/processed/stock_metrics.csv.",
    )
    fig.savefig(FIGURES_DIR / "03_risk_vs_return.png")
    plt.close(fig)


def chart_correlation(corr: pd.DataFrame) -> None:
    order = PORTFOLIO_TICKERS
    c = corr.reindex(index=order, columns=order)

    fig, ax = plt.subplots(figsize=(7.6, 5.9))
    ax.grid(False)
    im = ax.imshow(c.values, cmap=DIVERGING_CMAP, norm=TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1))
    ax.set_xticks(range(len(order)), order, fontweight="bold")
    ax.set_yticks(range(len(order)), order, fontweight="bold")
    ax.xaxis.set_ticks_position("top")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    for i in range(len(order)):
        for j in range(len(order)):
            v = c.iloc[i, j]
            ax.text(
                j,
                i,
                f"{v:.2f}",
                ha="center",
                va="center",
                fontsize=9,
                color="#ffffff" if abs(v) > 0.55 else vs.TEXT_PRIMARY,
            )
    cbar = fig.colorbar(im, ax=ax, shrink=0.45, pad=0.03)
    cbar.set_label("Correlation of daily returns", fontsize=9, color=vs.TEXT_SECONDARY)
    cbar.outline.set_visible(False)
    ax.set_title("The two banks move almost in lockstep", pad=34)
    vs.caption(
        fig,
        "Pearson correlation of daily CAD price returns across the shared trading calendar. "
        "1.00 on the diagonal is each stock with itself. "
        "Source: data/processed/correlation_matrix.csv.",
    )
    fig.savefig(FIGURES_DIR / "04_correlation_matrix.png")
    plt.close(fig)


def chart_rolling_volatility(df: pd.DataFrame) -> None:
    wide = wide_close(df, PORTFOLIO_TICKERS)
    roll = (
        wide.pct_change().rolling(30).std() * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
    ).dropna(how="all")

    fig, axes = plt.subplots(4, 2, figsize=(11, 9), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, ticker in zip(axes, PORTFOLIO_TICKERS):
        for other in PORTFOLIO_TICKERS:
            ax.plot(roll.index, roll[other], color=vs.GRID, linewidth=0.7, zorder=1)
        ax.plot(roll.index, roll[ticker], color=vs.TICKER_COLOR[ticker], linewidth=1.5, zorder=2)
        ax.set_title(ticker, fontsize=10.5, pad=6)
        ax.yaxis.set_major_formatter(PCT)
    for spare in axes[len(PORTFOLIO_TICKERS):]:
        spare.set_visible(False)
    # The bottom-right cell is empty, so the panel above it carries its own date axis.
    axes[len(PORTFOLIO_TICKERS) - 2].tick_params(labelbottom=True)
    axes[0].set_ylim(0, min(200, roll.max().max() * 1.05))
    fig.suptitle(
        "30-day rolling volatility, annualised - each holding against all seven",
        x=0.02,
        ha="left",
        fontsize=13,
        fontweight="bold",
        color=vs.TEXT_PRIMARY,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    vs.caption(
        fig,
        "Standard deviation of daily CAD returns over a trailing 30 trading days, annualised. Grey "
        "lines are the other six holdings, for context. Source: data/processed/stock_prices_clean.csv.",
    )
    fig.savefig(FIGURES_DIR / "05_rolling_volatility.png")
    plt.close(fig)


def chart_max_drawdown(metrics: pd.DataFrame) -> None:
    m = (
        metrics[metrics["in_portfolio"]]
        .sort_values("max_drawdown_pct")
        .reset_index(drop=True)
    )

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.barh(
        m["ticker"],
        m["max_drawdown_pct"],
        color=vs.SEQUENTIAL_BLUE,
        height=0.62,
        zorder=3,
    )
    for i, r in m.iterrows():
        ax.text(
            r["max_drawdown_pct"] - 1.2,
            i,
            f"{r['max_drawdown_pct']:.0f}%  ({r['max_drawdown_date'].year if hasattr(r['max_drawdown_date'], 'year') else str(r['max_drawdown_date'])[:4]})",
            ha="right",
            va="center",
            fontsize=9,
            color=vs.TEXT_PRIMARY,
        )
    ax.invert_yaxis()
    ax.set_xlim(m["max_drawdown_pct"].min() * 1.25, 0)
    ax.xaxis.set_major_formatter(PCT)
    ax.set_xlabel("Peak-to-trough decline (%)")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0, labelsize=10)
    plt.setp(ax.get_yticklabels(), fontweight="bold")
    ax.set_title("Worst peak-to-trough fall, with the year the trough landed")
    vs.caption(
        fig,
        "Largest decline from a running maximum to a subsequent trough, measured on daily CAD "
        "closes within the analysis window. Source: data/processed/stock_metrics.csv.",
    )
    fig.savefig(FIGURES_DIR / "06_max_drawdown.png")
    plt.close(fig)


def chart_sector_growth(df: pd.DataFrame, sectors: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 6))
    for _, row in sectors.iterrows():
        tickers = [t.strip() for t in row["tickers"].split(",")]
        wide = wide_close(df[df["ticker"].isin(tickers)], tickers)
        basket = 100 * (wide / wide.iloc[0]).mean(axis=1)
        color = vs.SECTOR_COLOR[row["sector"]]
        ax.plot(basket.index, basket.values, color=color, linewidth=2.2)
        ax.annotate(
            f" {row['sector']}  {basket.iloc[-1]:,.0f}",
            xy=(basket.index[-1], basket.iloc[-1]),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=color,
        )
    ax.set_yscale("log")
    ax.set_yticks([100, 300, 1000, 3000, 10000, 30000])
    ax.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylabel("Equal-weighted CAD basket (start = 100, log scale)")
    ax.set_xlim(df["date"].min(), df["date"].max() + pd.Timedelta(days=1500))
    top = sectors.iloc[0]
    bottom = sectors.iloc[-1]
    ax.set_title(
        f"{top['sector']} compounded at {top['cagr_pct']:.0f}% a year, "
        f"{bottom['sector'].lower()} at {bottom['cagr_pct']:.0f}%"
    )
    vs.caption(
        fig,
        "Equal-weighted basket of the portfolio holdings in each sector, in CAD, indexed to 100 at "
        "the start of the window and never rebalanced. Sector assignment is manual "
        "(python/config.py). Source: data/processed/sector_summary.csv.",
    )
    fig.savefig(FIGURES_DIR / "07_sector_growth.png")
    plt.close(fig)


def chart_fx_effect(metrics: pd.DataFrame) -> None:
    """Same stocks, measured in USD and in CAD - the gap is the currency."""
    m = (
        metrics[metrics["in_portfolio"]]
        .sort_values("annualised_volatility_pct", ascending=False)
        .reset_index(drop=True)
    )
    panels = [
        ("annualised_volatility_usd_pct", "annualised_volatility_pct", "Annualised volatility (%)"),
        ("max_drawdown_usd_pct", "max_drawdown_pct", "Worst peak-to-trough decline (%)"),
    ]
    usd_color, cad_color = vs.CATEGORICAL[1], vs.CATEGORICAL[0]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), sharey=True)
    for ax, (usd_col, cad_col, label) in zip(axes, panels):
        for i, r in m.iterrows():
            ax.plot(
                [r[usd_col], r[cad_col]],
                [i, i],
                color=vs.GRID,
                linewidth=2.5,
                zorder=1,
                solid_capstyle="round",
            )
        # A surface ring keeps the two marks readable where they nearly coincide.
        ax.scatter(
            m[usd_col], m.index, s=95, color=usd_color, edgecolor=vs.SURFACE,
            linewidth=1.5, zorder=3, label="Measured in USD",
        )
        ax.scatter(
            m[cad_col], m.index, s=95, color=cad_color, edgecolor=vs.SURFACE,
            linewidth=1.5, zorder=4, label="Measured in CAD",
        )
        ax.set_xlabel(label)
        ax.xaxis.set_major_formatter(PCT)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
        ax.margins(x=0.14)
    axes[0].set_yticks(range(len(m)), m["ticker"])
    plt.setp(axes[0].get_yticklabels(), fontweight="bold", fontsize=10)
    axes[0].invert_yaxis()
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.018, 0.925), ncols=2)

    fig.suptitle(
        "Holding in CAD lowered both risk measures for every holding",
        x=0.02,
        ha="left",
        fontsize=13,
        fontweight="bold",
        color=vs.TEXT_PRIMARY,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.885))
    vs.caption(
        fig,
        "The same daily closes measured in their listing currency (USD) and converted to CAD at the "
        "Bank of Canada daily rate. CAD weakens when risk assets fall, which offsets part of the "
        "loss for an unhedged Canadian holder. Source: data/processed/stock_metrics.csv.",
    )
    fig.savefig(FIGURES_DIR / "09_fx_effect_on_risk.png")
    plt.close(fig)


def chart_volume_trend(df: pd.DataFrame) -> None:
    port = df[df["ticker"].isin(PORTFOLIO_TICKERS)].copy()
    port["year"] = port["date"].dt.year
    annual = (
        port.groupby(["year", "ticker"])["volume"].mean().unstack("ticker")
        .reindex(columns=PORTFOLIO_TICKERS)
    )
    annual = annual.loc[2011:2025]  # whole years only

    fig, ax = plt.subplots(figsize=(11, 6))
    for ticker in PORTFOLIO_TICKERS:
        s = annual[ticker] / 1e6
        ax.plot(s.index, s.values, color=vs.TICKER_COLOR[ticker], linewidth=2.0)
        ax.annotate(
            f" {ticker}",
            xy=(s.index[-1], s.iloc[-1]),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=vs.TICKER_COLOR[ticker],
        )
    ax.set_yscale("log")
    ax.set_ylabel("Average daily volume (millions of shares, log scale)")
    ax.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlim(annual.index[0], annual.index[-1] + 1.6)
    ax.set_title("The tech names trade 40-200x the daily share volume of the banks")
    vs.caption(
        fig,
        "Mean daily share volume per calendar year, whole years only (2011-2025). Log scale. RY and "
        "TD show their US listing only, so their true trading activity is understated. "
        "Source: data/processed/stock_prices_clean.csv.",
    )
    fig.savefig(FIGURES_DIR / "08_volume_trend.png")
    plt.close(fig)


# --------------------------------------------------------------------------
def main() -> int:
    vs.apply_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print(
        f"Step 4 - exploratory data analysis ({START_DATE} to {END_DATE}, "
        f"{CURRENCY}, {REBALANCING})"
    )
    df = load_clean()
    print(f"  loaded {len(df):,} clean rows / {df['ticker'].nunique()} tickers")

    metrics = price_and_return_metrics(df)
    monthly = monthly_returns(df)
    annual = annual_returns(df)
    corr = correlation_matrix(df, PORTFOLIO_TICKERS)
    sectors = sector_summary(df, metrics)

    outputs = {
        "stock_metrics.csv": metrics,
        "monthly_returns.csv": monthly,
        "annual_returns.csv": annual,
        "sector_summary.csv": sectors,
    }
    for name, table in outputs.items():
        table.to_csv(PROCESSED_DIR / name, index=False)
        print(f"  wrote data/processed/{name}  ({len(table):,} rows)")
    corr.round(4).to_csv(PROCESSED_DIR / "correlation_matrix.csv")
    print(f"  wrote data/processed/correlation_matrix.csv  ({len(corr)} x {len(corr)})")

    chart_indexed_growth(df)
    chart_annual_returns_heatmap(annual)
    chart_risk_return(metrics)
    chart_correlation(corr)
    chart_rolling_volatility(df)
    chart_max_drawdown(metrics)
    chart_sector_growth(df, sectors)
    chart_volume_trend(df)
    chart_fx_effect(metrics)
    print("  wrote 9 charts -> reports/figures/")

    print("\n--- Stock metrics ---")
    print(
        metrics[
            [
                "ticker",
                "sector",
                "cumulative_return_pct",
                "cagr_pct",
                "cagr_usd_pct",
                "fx_share_of_cagr_pp",
                "annualised_volatility_pct",
                "max_drawdown_pct",
            ]
        ].to_string(index=False)
    )
    print("\n--- Sector summary ---")
    print(sectors.to_string(index=False))
    print("\n--- Correlation of daily returns ---")
    print(corr.round(2).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
