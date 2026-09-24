# Step 7 - SQL KPI Analysis

**Files:** `SQL/views.sql` (4 reusable views) and `SQL/kpi_analysis.sql` (16 queries).
Both read `data/processed/stock_portfolio.db`, built by `python/load_to_database.py`.

The existing `SQL/portfolio_analysis.sql` covers table counts, date ranges, price min/max and the
static allocation. It does not compute a single KPI from the price series - no return, portfolio
value, CAGR, volatility, Sharpe ratio or drawdown. This file adds that layer. The two are
complementary; nothing in the original file was changed.

---

## 1. Why this is now possible in SQL

Until the Step 6 fix, `Portfolio.Number_of_Shares` was NULL, so SQL could not value the portfolio on
any date - the best it could do was report the static investment amounts. With share counts loaded,
**portfolio value on any day is `SUM(shares x close)`**, and every portfolio-level KPI follows from
that one expression.

---

## 2. Views (`SQL/views.sql`)

Defined once and created by the loader, so Power BI and the analysis queries share the same logic.

| View | Grain | Purpose |
| --- | --- | --- |
| `v_portfolio_daily` | one row per trading day | Portfolio value, carried forward (see 2.1) |
| `v_holdings_current` | one row per holding | Latest price, current value, profit/loss |
| `v_stock_daily_returns` | ticker x day | Close and daily CAD return |
| `v_stock_annual_returns` | ticker x year | Year-end close and calendar-year return |

Each joins to `Portfolio`, which restricts it to the seven holdings - SHOP is in `Stock_Prices` but
not in `Portfolio`, so it is excluded automatically rather than by a filter someone has to remember.

### 2.1 A bug worth recording

The obvious way to write the daily series is:

```sql
SELECT date, SUM(p.Number_of_Shares * sp.close)
FROM Stock_Prices sp JOIN Portfolio p ON p.Ticker = sp.ticker
GROUP BY date;
```

This is wrong. On **2011-02-17** only four of the seven holdings have a quote (RY, TD and TSLA are
missing), so `SUM` silently adds up four positions instead of seven. Portfolio value appears to
collapse and rebound overnight, producing two enormous fake daily returns.

The effect on the KPIs was not subtle:

| Metric | Naive `GROUP BY` | Correct | Python |
| --- | ---: | ---: | ---: |
| Annualised volatility | 34.22% | **32.79%** | 32.79% |
| Sharpe ratio | 1.092 | **1.126** | 1.126 |

`v_portfolio_daily` instead values each holding at its most recent close on or before the date - the
SQL equivalent of a forward fill, which is what `python/performance_metrics.py` does with `.ffill()`.
This is the same class of silent-join defect as the `RY.TO` ticker mismatch in
`reports/project_review.md` section 5.1: the query returns a number, it is just the wrong one.

---

## 3. KPI coverage

All 13 KPIs from the scope document:

| # | KPI | Query |
| ---: | --- | --- |
| 1 | Total Investment Amount | A1 |
| 2 | Current Portfolio Value | A1 |
| 3 | Total Return (%) | A1 |
| 4 | Annualized Return (CAGR) | A2 (portfolio), B1 (per stock) |
| 5 | Profit/Loss (CAD) | A1 (portfolio), B4 (per stock) |
| 6 | Return by Stock (%) | B1 |
| 7 | Portfolio Growth Rate | A5 |
| 8 | Portfolio Volatility | A3 (portfolio), B2 (per stock) |
| 9 | Sharpe Ratio | A3 (portfolio), B2 (per stock) |
| 10 | Maximum Drawdown | A4 (portfolio), B3 (per stock) |
| 11 | Best/Worst Performing Stock | B1 |
| 12 | Sector-wise Return | C1 |
| 13 | Average Daily Trading Volume | D4 |

Business questions 1-10:

| # | Question | Query |
| ---: | --- | --- |
| 1 | Highest return, 2010-2026? | B1 |
| 2 | Highest risk? | B2 |
| 3 | Overall portfolio return? | A1, A2 |
| 4 | Best sector? | C1 |
| 5 | Biggest contributor to growth? | B4 |
| 6 | How prices changed over time? | A5, D1 |
| 7 | Consistent outperformers? | D2 |
| 8 | Effect of major market events? | A4, D3 |
| 9 | Best risk-return balance? | B2, D6 |
| 10 | How allocation affects long-term growth? | B4, C1 |

SQL techniques required by the roadmap, all used: `SELECT`, `WHERE`, `GROUP BY`, `HAVING`,
`ORDER BY`, `CASE`, `JOIN`, CTEs, and the window functions `LAG`, `ROW_NUMBER`, `RANK`,
`DENSE_RANK`, `MAX() OVER` (running peak), `AVG() OVER` (moving average) and `SUM() OVER`
(share-of-total). SQLite has no `STDDEV`, so sample standard deviation is computed as
`SQRT((SUM(x*x) - n*AVG(x)^2) / (n-1))`.

---

## 4. Headline results

| Query | Result |
| --- | --- |
| A1 | CAD 100,000 -> **24,743,196**; profit 24,643,196; total return +24,643% (247.4x) |
| A2 | **CAGR 41.12%** over 16.0 years |
| A3 | Volatility **32.79%**, Sharpe **1.126** (3% risk-free rate) |
| A4 | Max drawdown **-56.70%**, trough 5 Jan 2023 (peak 7,434,243 -> 3,218,832) |
| A5 | Best year 2020 (+201%), worst 2022 (-50%) |
| B1 | Best NVDA +122,697% (56.0% CAGR); worst TD +621% (13.1%) |
| B2 | Riskiest TSLA 56.5%; best Sharpe NVDA 1.148; RY and TD the only "Low" risk |
| B3 | Deepest fall TSLA -71.1% (Jan 2023); shallowest RY -34.2% (Mar 2020) |
| B4 | **NVDA 15% -> 74.4% of value**, +59.4pp drift, 74.7% of all profit |
| C1 | Technology +36,665% and 81.8% of profit; Banking +689% and 0.6% |
| D1 | Best month Aug 2020 (+33.3%); worst Dec 2022 (-22.4%) |
| D2 | NVDA top-3 in 9 of 16 years and first in 5; AAPL most consistent (15 positive years of 16) |
| D3 | **2022 is the only year all seven fell** (avg -29.7%) |
| D4 | NVDA averages 473M shares/day, RY 1.2M - a ~400x liquidity gap |
| D6 | **RY-TD 0.786**, the highest pair by far; RY-TSLA 0.239 the lowest |

---

## 5. Verification

Every query was executed and its output compared field by field against the Step 5 outputs in
`data/processed/metrics/`, which are produced independently in pandas.

**60 of 60 cross-checks agree.** One row displays differently: RY's annualised volatility is
`17.685931` in both, which SQLite's `ROUND` renders as 17.69 and Python's `round()` stored as 17.68.
That is a rounding-mode difference in the last displayed digit, not a difference in the computation.

Pairwise correlations agree to within 0.002. The small gap is expected: `correlation_matrix.csv`
uses dates where **all seven** holdings traded, while D6 uses the dates where **each pair** traded,
so pairs involving RY, TD or TSLA have one extra observation.

---

## 6. Notes and limitations

1. **Everything inherits the project-wide limitations** in `reports/findings.md` section 9 - price
   returns only (no dividends), no benchmark, survivorship bias, and currency risk inside every
   figure.
2. **The Sharpe ratio depends on the 3% risk-free rate** hard-coded in the queries to match
   `config.py`. Change both together.
3. **Risk-level cut-offs** (Low < 20%, Medium < 35%) are an assumption, not a standard.
4. **RY and TD volumes in D4 are US-listing only** and understate total trading.
5. **2010 and 2026 are partial years** in A5, D2 and D3.
6. **`v_portfolio_daily` uses a correlated subquery** per holding per day (about 28,000 lookups).
   It runs in well under a second on the `(ticker, date)` index created by the loader, but it is the
   slowest object in the database and worth materialising as a table if the history grows.

## 7. How to run

```bash
python3 python/load_to_database.py     # rebuilds tables, indexes and views
```

Then open `data/processed/stock_portfolio.db` and run `SQL/kpi_analysis.sql`. The views are created
by the loader, so the analysis file can be run whole or query by query.
