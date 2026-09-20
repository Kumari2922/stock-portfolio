"""Shared configuration for the Stock Portfolio Performance Analysis project.

Every value that the cleaning and analysis steps depend on lives here so the
pipeline can be re-run end to end without editing the scripts themselves.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# --- Analysis window (from Project_Scope_QA.pdf, section 4) ----------------
START_DATE = "2010-09-17"
END_DATE = "2026-09-17"

# --- Reporting currency ----------------------------------------------------
# Every raw price file is a US listing quoted in USD. The project reports in
# CAD, so all prices are converted at the Bank of Canada daily USD/CAD rate
# before any metric is computed. See data/raw/SOURCES.md.
CURRENCY = "CAD"

FX_FILES = {
    # path relative to RAW_DIR: (series column, label)
    "boc_usdcad_noon_IEXE0101.csv": ("IEXE0101", "IEXE0101 (noon)"),
    "boc_usdcad_daily_FXUSDCAD.csv": ("FXUSDCAD", "FXUSDCAD (daily avg)"),
}

# The Bank publishes the pre- and post-2017 methodologies as separate series.
# FXUSDCAD is used from its first observation onward; the legacy noon rate
# covers everything before. The 82-day overlap differs by 0.08% on average.
FX_SPLICE_DATE = "2017-01-03"

# --- Portfolio convention --------------------------------------------------
# Buy and hold: the allocation below is bought once at the start of the
# analysis window and never rebalanced. Share counts are therefore fixed for
# the whole period, and drift in the weights is a result, not an error.
REBALANCING = "buy-and-hold"

# --- Portfolio (from Project_Scope_QA.pdf section 3 /
#     data/raw/Stock_Portfolio_Investment_Allocation.xlsx) -----------------
INITIAL_INVESTMENT = 100_000.0

PORTFOLIO = {
    # ticker: (company name, sector, investment amount CAD, allocation %)
    "AAPL": ("Apple Inc.", "Technology", 20_000.0, 20.0),
    "MSFT": ("Microsoft Corporation", "Technology", 20_000.0, 20.0),
    "NVDA": ("NVIDIA Corporation", "Technology", 15_000.0, 15.0),
    "AMZN": ("Amazon.com, Inc.", "Consumer Discretionary", 15_000.0, 15.0),
    "TSLA": ("Tesla, Inc.", "Consumer Discretionary", 10_000.0, 10.0),
    "RY": ("Royal Bank of Canada", "Banking", 10_000.0, 10.0),
    "TD": ("Toronto-Dominion Bank", "Banking", 10_000.0, 10.0),
}

# Present in data/raw/ but not part of the scoped portfolio. Kept in the clean
# dataset (flagged in_portfolio = False) so it can be used for market context,
# but excluded from every portfolio-level metric.
NON_PORTFOLIO = {
    "SHOP": ("Shopify Inc.", "Technology"),
}

# Tickers whose raw file is the US listing even though the scope document
# names the Toronto listing. Once converted to CAD the two are economically
# equivalent (the listings are linked by arbitrage), but the provenance is
# recorded in the data dictionary either way.
US_LISTED_CANADIAN = {"RY", "TD"}

TRADING_DAYS_PER_YEAR = 252

# Risk-free rate used for the Sharpe ratio. 3.0% annual is a reasonable
# long-run average for short-term government paper over 2010-2026; it is a
# stated assumption, not a measured input.
RISK_FREE_RATE = 0.03
