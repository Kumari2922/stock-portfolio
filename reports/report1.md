- added what are the kips and business question for this project in that project scope file
-And in raw data folder i added one more small excel of investment data
## Steps 3 & 4 - cleaning and EDA (completed)

- `python/clean_data.py` builds `data/processed/stock_prices_clean.csv` (31,013 rows, 8 tickers) and
  `data/processed/company_master.csv`; it writes `reports/data_quality_report.md` with every check.
- `python/eda.py` builds the metric tables in `data/processed/` and 9 charts in `reports/figures/`.
- Findings are written up in `reports/findings.md`.
- Both open questions are now settled and encoded in `python/config.py`:
  **all prices are converted to CAD** at the Bank of Canada daily USD/CAD rate (two BoC series
  spliced at 2017-01-03, raw responses in `data/raw/`, documented in `data/raw/SOURCES.md`), and the
  portfolio convention is **buy and hold**, never rebalanced.
- The CAD switch is not cosmetic: USD/CAD rose 35.4% over the window, which added 2.1-2.9pp to every
  holding's annual return and *lowered* every volatility and drawdown figure. See Finding 1.

## Project review (24 Sep)

- `reports/project_review.md` reviews Steps 1-10 against the roadmap: status per step, what each
  contributor delivered, and 3 defects found. One is high severity - the `Portfolio` table uses
  `RY.TO`/`TD.TO` while the other tables use `RY`/`TD`, so **every SQL join silently dropped the
  banking sector**.

## Step 6 fix (24 Sep)

- `python/load_to_database.py` rewritten: `Portfolio` is now built from Step 5's
  `stock_performance_summary.csv` (clean tickers, real share counts and purchase prices) instead of
  the raw spreadsheet, and any `.TO`/`.US` suffix is normalised away.
- A referential-integrity check runs after every load and raises if a `Portfolio` ticker fails to
  join, so the failure can no longer be silent.
- Database reloaded. Allocation query 5 -> **7 rows**, sector query 2 -> **3 sectors**
  (Banking 20% restored), `COUNT(*)` 8 -> **7**.
- **Outstanding:** re-run `SQL/portfolio_analysis.sql` so its result comments refresh, and re-check
  the Step 8 dashboard page - it was built while banking was missing.

## Step 7 KPI queries (24 Sep)

- `SQL/views.sql` - 4 reusable views (`v_portfolio_daily`, `v_holdings_current`,
  `v_stock_daily_returns`, `v_stock_annual_returns`), created by the loader so Power BI and the
  analysis queries share one definition of portfolio value.
- `SQL/kpi_analysis.sql` - 16 queries covering **all 13 KPIs and all 10 business questions**, using
  CTEs, CASE, HAVING and window functions (LAG, RANK, DENSE_RANK, ROW_NUMBER, MAX/AVG/SUM OVER).
- Only possible after the Step 6 fix: with share counts loaded, portfolio value is
  `SUM(shares * close)`, and every portfolio KPI follows from it.
- Found a second silent bug: the obvious `GROUP BY date` sum drops holdings on 2011-02-17, which
  inflated volatility 32.79% -> 34.22%. The view carries prices forward instead.
- **Verified: 60 of 60 figures match the pandas metrics.** Write-up in `reports/sql_kpi_report.md`.
