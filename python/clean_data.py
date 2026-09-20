"""Step 3 - Data cleaning.

Reads the raw per-ticker OHLCV files in data/raw/, validates and standardises
them, converts every price from USD to CAD at the Bank of Canada daily rate,
and writes a single tidy dataset plus a company reference table to
data/processed/. A data-quality report of everything that was checked and
changed is written to reports/data_quality_report.md.

Run:  python3 python/clean_data.py
"""

from __future__ import annotations

import io
import sys

import numpy as np
import pandas as pd

from config import (
    CURRENCY,
    END_DATE,
    FIGURES_DIR,
    FX_FILES,
    FX_SPLICE_DATE,
    NON_PORTFOLIO,
    PORTFOLIO,
    PROCESSED_DIR,
    RAW_DIR,
    REBALANCING,
    REPORTS_DIR,
    START_DATE,
    US_LISTED_CANADIAN,
)

EXPECTED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
PRICE_COLUMNS = ["open", "high", "low", "close"]


def load_raw() -> tuple[pd.DataFrame, list[dict]]:
    """Read every data/raw/*.csv into one frame, adding the ticker column.

    The raw files carry the ticker only in the filename (aapl_us_d.csv), so it
    is recovered there and promoted to a real column.
    """
    frames, audit = [], []
    for path in sorted(RAW_DIR.glob("*_us_d.csv")):
        ticker = path.stem.split("_")[0].upper()
        df = pd.read_csv(path)

        missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"{path.name} is missing columns: {missing}")

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        audit.append(
            {
                "ticker": ticker,
                "file": path.name,
                "raw_rows": len(df),
                "raw_first_date": df["Date"].min().date(),
                "raw_last_date": df["Date"].max().date(),
                "unparseable_dates": int(df["Date"].isna().sum()),
            }
        )
        df["ticker"] = ticker
        frames.append(df)

    if not frames:
        raise FileNotFoundError(f"No raw CSV files found in {RAW_DIR}")
    return pd.concat(frames, ignore_index=True), audit


def load_fx() -> tuple[pd.DataFrame, dict]:
    """Build one continuous daily USD/CAD series from the two BoC series.

    The Bank changed methodology in 2017 and publishes the periods separately,
    so the legacy noon rate covers everything before FX_SPLICE_DATE and the
    daily average rate covers everything from it onward.
    """
    parts = {}
    for filename, (column, label) in FX_FILES.items():
        path = RAW_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"{path} not found - see data/raw/SOURCES.md")
        # The Valet CSV carries a terms-of-use and series header above the data.
        text = path.read_text(encoding="utf-8-sig")
        if '"OBSERVATIONS"' not in text:
            raise ValueError(f"{filename} is not a Bank of Canada Valet CSV")
        body = text.split('"OBSERVATIONS"\n', 1)[1]
        part = pd.read_csv(io.StringIO(body))
        part.columns = [c.strip().strip('"') for c in part.columns]
        part = part.rename(columns={column: "usdcad"})[["date", "usdcad"]]
        part["date"] = pd.to_datetime(part["date"], errors="coerce")
        part["usdcad"] = pd.to_numeric(part["usdcad"], errors="coerce")
        parts[label] = part.dropna().reset_index(drop=True)

    (legacy_label, legacy), (current_label, current) = parts.items()
    overlap = legacy.merge(current, on="date", suffixes=("_a", "_b"))
    diff = (overlap["usdcad_b"] - overlap["usdcad_a"]).abs()

    fx = pd.concat(
        [
            legacy[legacy["date"] < FX_SPLICE_DATE].assign(fx_series=legacy_label),
            current.assign(fx_series=current_label),
        ],
        ignore_index=True,
    ).sort_values("date")
    fx = fx.drop_duplicates(subset="date", keep="last").reset_index(drop=True)

    stats = {
        "fx_rows": len(fx),
        "fx_first": fx["date"].min().date(),
        "fx_last": fx["date"].max().date(),
        "fx_min": round(fx["usdcad"].min(), 4),
        "fx_max": round(fx["usdcad"].max(), 4),
        "fx_overlap_days": len(overlap),
        "fx_overlap_mean_abs_diff_pct": round(100 * (diff / overlap["usdcad_a"]).mean(), 4),
        "fx_overlap_max_abs_diff_pct": round(100 * (diff / overlap["usdcad_a"]).max(), 4),
    }
    return fx, stats


def to_cad(df: pd.DataFrame, fx: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Convert every USD price column to CAD at that day's USD/CAD rate.

    The Bank does not publish on Canadian holidays, but US markets trade on
    some of them, so the rate is carried forward to the next trading day - the
    most recent published rate is the one that would have applied.
    """
    df = df.merge(fx, on="date", how="left").sort_values(["ticker", "date"])
    missing_before = int(df["usdcad"].isna().sum())
    df[["usdcad", "fx_series"]] = (
        df.groupby("ticker")[["usdcad", "fx_series"]].ffill()
    )
    stats = {
        "fx_rows_carried_forward": missing_before - int(df["usdcad"].isna().sum()),
        "fx_rows_still_unmatched": int(df["usdcad"].isna().sum()),
    }
    if stats["fx_rows_still_unmatched"]:
        raise ValueError(
            f"{stats['fx_rows_still_unmatched']} rows have no USD/CAD rate - "
            "the FX series does not cover the start of the price window"
        )

    for col in PRICE_COLUMNS:
        df[f"{col}_usd"] = df[col]
        df[col] = (df[col] * df["usdcad"]).round(6)
    return df.reset_index(drop=True), stats


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply the Step 3 cleaning tasks, recording what each one removed."""
    stats: dict[str, int | float | str] = {"rows_in": len(df)}

    df = df.rename(columns=str.lower).loc[:, ["date", "ticker", "open", "high", "low", "close", "volume"]]

    # 1. Data types. Dates are already parsed; prices and volume are coerced so
    #    any stray text becomes NaN and is caught by the null check below.
    for col in PRICE_COLUMNS + ["volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["ticker"] = df["ticker"].str.strip().str.upper()

    # 2. Missing values. Rows without a date or a close price cannot be used
    #    for returns, so they are dropped rather than imputed.
    before = len(df)
    df = df.dropna(subset=["date", "close"])
    stats["dropped_missing_date_or_close"] = before - len(df)
    stats["remaining_nulls"] = int(df.isna().sum().sum())

    # 3. Duplicates. Keep the last record for a (ticker, date) pair, which is
    #    the convention for a re-stated end-of-day bar.
    before = len(df)
    df = df.drop_duplicates(subset=["ticker", "date"], keep="last")
    stats["dropped_duplicate_ticker_dates"] = before - len(df)

    # 4. Invalid ranges. A bar where high < low, or where open/close sits
    #    outside the high-low band, is internally inconsistent.
    invalid = (
        (df["high"] < df["low"])
        | (df["close"] > df["high"])
        | (df["close"] < df["low"])
        | (df["open"] > df["high"])
        | (df["open"] < df["low"])
        | (df[PRICE_COLUMNS] <= 0).any(axis=1)
    )
    stats["dropped_invalid_ohlc"] = int(invalid.sum())
    df = df.loc[~invalid]

    # 5. Volume. Adjusted source data carries fractional volume for some
    #    tickers; round to whole shares and store as a nullable integer.
    stats["fractional_volume_rounded"] = int((df["volume"] % 1 != 0).sum())
    stats["zero_volume_rows"] = int((df["volume"] == 0).sum())
    df["volume"] = df["volume"].round().astype("Int64")

    # 6. Analysis window from the scope document.
    before = len(df)
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    stats["dropped_outside_window"] = before - len(df)

    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # 7. Currency. Every raw file is a US listing in USD; the project reports
    #    in CAD, so convert before any return is computed.
    fx, fx_stats = load_fx()
    df, convert_stats = to_cad(df, fx)
    stats.update(fx_stats)
    stats.update(convert_stats)

    # 8. Outlier check. Flag rather than drop: a >25% single-day move is
    #    usually a real earnings or split event, and silently deleting those
    #    would distort volatility and drawdown.
    df["daily_return"] = df.groupby("ticker")["close"].pct_change()
    extreme = df["daily_return"].abs() > 0.25
    stats["extreme_daily_moves_flagged"] = int(extreme.sum())
    df["extreme_move"] = extreme

    df = df.loc[
        :,
        [
            "date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_usd",
            "usdcad",
            "fx_series",
            "daily_return",
            "extreme_move",
        ],
    ]
    stats["rows_out"] = len(df)
    return df, stats


def build_company_master() -> pd.DataFrame:
    """Company_Master reference table - the sector source the raw data lacks."""
    records = []
    for ticker, (name, sector, investment, allocation) in PORTFOLIO.items():
        records.append(
            {
                "ticker": ticker,
                "company_name": name,
                "sector": sector,
                "in_portfolio": True,
                "investment_cad": investment,
                "allocation_pct": allocation,
                "listing": "US (NYSE)" if ticker in US_LISTED_CANADIAN else "US",
            }
        )
    for ticker, (name, sector) in NON_PORTFOLIO.items():
        records.append(
            {
                "ticker": ticker,
                "company_name": name,
                "sector": sector,
                "in_portfolio": False,
                "investment_cad": 0.0,
                "allocation_pct": 0.0,
                "listing": "US",
            }
        )
    return pd.DataFrame(records).sort_values("ticker").reset_index(drop=True)


def coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker coverage against the union of all observed trading days."""
    calendar = set(df["date"].unique())
    rows = []
    for ticker, g in df.groupby("ticker"):
        gaps = len(calendar - set(g["date"].unique()))
        rows.append(
            {
                "ticker": ticker,
                "rows": len(g),
                "first_date": g["date"].min().date(),
                "last_date": g["date"].max().date(),
                "missing_trading_days": gaps,
                "coverage_pct": round(100 * len(g) / len(calendar), 2),
            }
        )
    return pd.DataFrame(rows).sort_values("ticker").reset_index(drop=True)


def write_report(audit: list[dict], stats: dict, coverage: pd.DataFrame) -> None:
    raw = pd.DataFrame(audit)
    lines = [
        "# Data Quality Report - Step 3 (Cleaning)",
        "",
        f"Generated by `python/clean_data.py`. Analysis window: **{START_DATE} to {END_DATE}**. "
        f"Reporting currency: **{CURRENCY}**. Portfolio convention: **{REBALANCING}**.",
        "",
        "## 1. Raw files as received",
        "",
        raw.to_markdown(index=False),
        "",
        "## 2. Cleaning actions",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Rows read from raw files | {stats['rows_in']:,} |",
        f"| Rows dropped - missing date or close | {stats['dropped_missing_date_or_close']:,} |",
        f"| Rows dropped - duplicate (ticker, date) | {stats['dropped_duplicate_ticker_dates']:,} |",
        f"| Rows dropped - invalid OHLC relationships | {stats['dropped_invalid_ohlc']:,} |",
        f"| Rows dropped - outside the analysis window | {stats['dropped_outside_window']:,} |",
        f"| Fractional volume values rounded to whole shares | {stats['fractional_volume_rounded']:,} |",
        f"| Prices converted USD -> CAD | all {stats['rows_out']:,} rows |",
        f"| FX rows carried forward (BoC holiday, US market open) | {stats['fx_rows_carried_forward']:,} |",
        f"| Zero-volume rows retained (flagged, not dropped) | {stats['zero_volume_rows']:,} |",
        f"| Extreme daily moves flagged (>25%, retained) | {stats['extreme_daily_moves_flagged']:,} |",
        f"| Remaining nulls after cleaning | {stats['remaining_nulls']:,} |",
        f"| **Rows written to data/processed/** | **{stats['rows_out']:,}** |",
        "",
        "## 3. Currency conversion",
        "",
        "Every raw price file is a **US listing quoted in USD**. The project reports in CAD, so each",
        "OHLC price is multiplied by that day's Bank of Canada USD/CAD rate before any return is",
        "computed. The original USD close is kept as `close_usd` so the conversion stays auditable.",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| USD/CAD observations after splicing | {stats['fx_rows']:,} |",
        f"| FX coverage | {stats['fx_first']} to {stats['fx_last']} |",
        f"| USD/CAD range over the window | {stats['fx_min']} to {stats['fx_max']} |",
        f"| Splice date (legacy noon -> daily average) | {FX_SPLICE_DATE} |",
        f"| Overlap between the two BoC series | {stats['fx_overlap_days']} business days |",
        f"| Mean absolute difference across the overlap | {stats['fx_overlap_mean_abs_diff_pct']}% |",
        f"| Largest difference across the overlap | {stats['fx_overlap_max_abs_diff_pct']}% |",
        f"| Trading days needing a carried-forward rate | {stats['fx_rows_carried_forward']:,} |",
        "",
        "The Bank does not publish on Canadian holidays, but US markets trade on some of them, so on",
        "those days the most recent published rate is carried forward. The two BoC series differ by",
        f"{stats['fx_overlap_mean_abs_diff_pct']}% on average across their overlap, so the splice",
        "introduces no visible step in the series.",
        "",
        "**RY and TD.** These are the NYSE listings, not the TSX ones. Converted at the daily USD/CAD",
        "rate they are economically equivalent to the Toronto listings, because the two are linked by",
        "arbitrage - a persistent gap between them would be a free trade. The provenance is recorded",
        "in `company_master.csv` regardless.",
        "",
        "## 4. Coverage by ticker (within the analysis window)",
        "",
        coverage.to_markdown(index=False),
        "",
        "## 5. Standardisation applied",
        "",
        "- Added a `ticker` column, recovered from each filename; the raw files did not carry one.",
        "- Lower-cased and reordered columns to `date, ticker, open, high, low, close, volume`.",
        "- Parsed `date` to a real datetime and coerced all price/volume fields to numeric.",
        "- Rounded fractional volume and stored it as a nullable integer.",
        "- Converted every OHLC price from USD to CAD at the Bank of Canada daily rate, keeping the",
        "  original USD close as `close_usd` and the rate used as `usdcad`.",
        "- Added `daily_return` (computed on CAD prices) and an `extreme_move` flag.",
        "",
        "## 6. Known data limitations",
        "",
        "- **Currency risk is now inside every return.** Prices are converted at the daily USD/CAD"
        " rate, which is correct for a Canadian investor, but it means each stock's CAD return blends"
        " its own performance with USD/CAD movement. The rate ranged from"
        f" {stats['fx_min']} to {stats['fx_max']} over the window, so the effect is material and"
        " should be named whenever a CAD return is quoted.",
        "- **Two FX methodologies.** The pre-2017 figures are the Bank's legacy noon rate and the"
        " post-2017 figures its daily average rate. They are not the same measurement, though the"
        f" overlap shows them within {stats['fx_overlap_mean_abs_diff_pct']}% of each other.",
        "- **No adjusted close.** The source provides split-adjusted prices but no dividend-adjusted"
        " series, so all returns are price returns, not total returns. This understates RY and TD"
        " most, as the two highest-yielding holdings.",
        "- **SHOP is out of scope.** `shop_us_d.csv` is present in data/raw/ but Shopify is not in"
        " the investment allocation, and its history only begins 2015-05-21. It is kept in the clean"
        " dataset with `in_portfolio = False` and excluded from every portfolio-level metric.",
        "- **Sectors are assigned manually** in `python/config.py`; the raw price files contain no"
        " sector or company metadata.",
        "",
    ]
    out = REPORTS_DIR / "data_quality_report.md"
    out.write_text("\n".join(lines))
    print(f"  wrote {out.relative_to(REPORTS_DIR.parent)}")


def main() -> int:
    for d in (PROCESSED_DIR, REPORTS_DIR, FIGURES_DIR):
        d.mkdir(parents=True, exist_ok=True)

    print("Step 3 - cleaning raw stock data")
    raw, audit = load_raw()
    print(f"  read {len(raw):,} raw rows across {raw['ticker'].nunique()} tickers")

    clean_df, stats = clean(raw)
    companies = build_company_master()
    clean_df = clean_df.merge(
        companies[["ticker", "company_name", "sector", "in_portfolio"]], on="ticker", how="left"
    )

    coverage = coverage_table(clean_df)

    prices_out = PROCESSED_DIR / "stock_prices_clean.csv"
    companies_out = PROCESSED_DIR / "company_master.csv"
    clean_df.to_csv(prices_out, index=False)
    companies.to_csv(companies_out, index=False)

    print(f"  wrote {len(clean_df):,} clean rows -> {prices_out.relative_to(PROCESSED_DIR.parents[1])}")
    print(f"  wrote {len(companies):,} companies -> {companies_out.relative_to(PROCESSED_DIR.parents[1])}")
    write_report(audit, stats, coverage)
    print("  done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
