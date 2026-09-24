"""Step 6 - Load the processed data into SQLite.

Builds three tables in data/processed/stock_portfolio.db:

    Stock_Prices    daily CAD OHLCV, one row per ticker per trading day
    Company_Master  ticker, company, sector, investment amount, allocation
    Portfolio       the holdings: shares, purchase price, investment amount

and then runs SQL/views.sql to create the analysis views that
SQL/kpi_analysis.sql and Power BI read.

The Portfolio table is built from data/processed/metrics/stock_performance_summary.csv
(Step 5), not from the raw allocation spreadsheet. The spreadsheet uses the Toronto
tickers RY.TO / TD.TO while every other table uses RY / TD, so loading it directly
left both banks unable to join - see reports/project_review.md section 5.1. The
spreadsheet is still read, as a cross-check that the investment amounts agree.

Run:  python3 python/load_to_database.py
"""

from __future__ import annotations

import sqlite3
import sys

import pandas as pd

from config import PORTFOLIO, PROCESSED_DIR, PROJECT_ROOT, RAW_DIR

DB_PATH = PROCESSED_DIR / "stock_portfolio.db"
METRICS_DIR = PROCESSED_DIR / "metrics"
VIEWS_SQL = PROJECT_ROOT / "SQL" / "views.sql"


def normalise_ticker(s: pd.Series) -> pd.Series:
    """Drop the exchange suffix so RY.TO and RY are the same key."""
    return s.astype(str).str.strip().str.upper().str.replace(r"\.(TO|US)$", "", regex=True)


def build_portfolio() -> pd.DataFrame:
    """The Portfolio table, with the share counts Step 5 computed."""
    path = METRICS_DIR / "stock_performance_summary.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found - run python/performance_metrics.py first"
        )
    step5 = pd.read_csv(path)

    portfolio = pd.DataFrame(
        {
            "Ticker": normalise_ticker(step5["ticker"]),
            "Number_of_Shares": step5["shares"],
            "Purchase_Price": step5["purchase_price_cad"],
            "Investment_Amount": step5["investment_cad"],
        }
    ).sort_values("Investment_Amount", ascending=False, kind="stable")
    return portfolio.reset_index(drop=True)


def cross_check_allocation(portfolio: pd.DataFrame) -> None:
    """Confirm the loaded amounts still match the scope document's spreadsheet.

    The spreadsheet carries a trailing 'Total' row and the Toronto tickers, so it
    is normalised the same way before comparing rather than loaded as-is.
    """
    raw = pd.read_excel(RAW_DIR / "Stock_Portfolio_Investment_Allocation.xlsx")
    raw = raw.dropna(subset=["Ticker", "Investment (CAD)"])
    raw["Ticker"] = normalise_ticker(raw["Ticker"])

    merged = portfolio.merge(
        raw[["Ticker", "Investment (CAD)"]], on="Ticker", how="outer", indicator=True
    )
    unmatched = merged[merged["_merge"] != "both"]
    if not unmatched.empty:
        raise ValueError(
            "Portfolio and the allocation spreadsheet disagree on tickers:\n"
            f"{unmatched[['Ticker', '_merge']].to_string(index=False)}"
        )
    mismatched = merged[
        (merged["Investment_Amount"] - merged["Investment (CAD)"]).abs() > 1e-6
    ]
    if not mismatched.empty:
        raise ValueError(f"Investment amounts differ:\n{mismatched.to_string(index=False)}")


def check_referential_integrity(conn: sqlite3.Connection) -> None:
    """Fail loudly if a Portfolio ticker cannot reach the other two tables.

    This is the check that would have caught the RY.TO / TD.TO mismatch: the
    joins returned fewer rows rather than raising, so nothing flagged it.
    """
    orphans = pd.read_sql(
        """
        SELECT p.Ticker,
               cm.ticker IS NULL AS missing_from_company_master,
               sp.ticker IS NULL AS missing_from_stock_prices
        FROM Portfolio p
        LEFT JOIN Company_Master cm ON p.Ticker = cm.ticker
        LEFT JOIN (SELECT DISTINCT ticker FROM Stock_Prices) sp ON p.Ticker = sp.ticker
        WHERE cm.ticker IS NULL OR sp.ticker IS NULL
        """,
        conn,
    )
    if not orphans.empty:
        raise ValueError(f"Portfolio tickers that do not join:\n{orphans.to_string(index=False)}")

    joined = pd.read_sql(
        "SELECT COUNT(*) AS n FROM Portfolio p JOIN Company_Master cm ON p.Ticker = cm.ticker",
        conn,
    )["n"].iloc[0]
    expected = len(PORTFOLIO)
    if joined != expected:
        raise ValueError(f"Portfolio JOIN Company_Master returned {joined} rows, expected {expected}")


def main() -> int:
    prices = pd.read_csv(PROCESSED_DIR / "stock_prices_clean.csv")
    companies = pd.read_csv(PROCESSED_DIR / "company_master.csv")
    portfolio = build_portfolio()
    cross_check_allocation(portfolio)

    with sqlite3.connect(DB_PATH) as conn:
        prices.to_sql("Stock_Prices", conn, if_exists="replace", index=False)
        companies.to_sql("Company_Master", conn, if_exists="replace", index=False)
        portfolio.to_sql("Portfolio", conn, if_exists="replace", index=False)

        # Indexes for the columns every analysis query filters or joins on.
        # The composite one serves the as-of lookup in v_portfolio_daily.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON Stock_Prices(ticker)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON Stock_Prices(date)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON Stock_Prices(ticker, date)"
        )

        check_referential_integrity(conn)
        conn.executescript(VIEWS_SQL.read_text())

        print(f"Loaded into {DB_PATH.relative_to(PROCESSED_DIR.parents[1])}:")
        for table in ("Stock_Prices", "Company_Master", "Portfolio"):
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:<16} {n:>7,} rows")
        views = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
            )
        ]
        print(f"  views            {', '.join(views)}")
        print("Referential integrity: all Portfolio tickers join to both tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
