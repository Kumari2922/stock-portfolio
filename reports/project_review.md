# Project Review - Stock Portfolio Performance Analysis

**Reviewer:** Samir Omer · **Date:** 24 September 2026 · **Scope:** the whole project to date
(roadmap Steps 1-10), reviewed against `team-related/Stock_Portfolio_Analysis_5Day_Roadmap.pdf`
and the scope document `KPIs and Business Questions/Project_Scope_QA.pdf`.

Everything below was verified against the repository at commit `7762cd6` - the code was read and
re-run, and the database was queried directly. Where this report states a number, it was reproduced,
not copied from an earlier document.

---

## 1. Summary

The project is **8 of 10 roadmap steps complete**. The Python side (Steps 2-5) is in good shape and
fully reproducible. The database and SQL layer (Steps 6-7) had **two defects that each silently returned
wrong numbers rather than failing** - a ticker mismatch that dropped the banking sector, and a
portfolio-value join that inflated volatility. Both were **fixed on 24 September**, the database was
reloaded, the missing KPI queries were written, and the loader now fails loudly if the first recurs. The Power BI dashboard (Step 8, page 1) was built
before the fix and still needs re-checking. Steps 9 and 10 have not started.

| | |
| --- | --- |
| Steps complete | 8 of 10 (Step 8 partial: 1 dashboard page of 4) |
| Contributors | 4 (Kumari2922, Samir Omer, Kiran Gill, AshishSachdev) |
| Elapsed | 18 Sep - 24 Sep 2026 (27 commits) |
| Pipeline reproducibility | **Verified** - all three Python stages re-run byte-identically |
| Defects found | 4 (2 high, 2 low) - section 5; **all but the doc drift are fixed** |

---

## 2. What happened, in order

Commit timestamps mix timezones (some commits were made through the GitHub web interface), so the
order below is commit order, not a strict reading of the clock.

| Date | Who | What |
| --- | --- | --- |
| 18 Sep | Kumari2922 | Repo created; first price history added |
| 19 Sep | Kumari2922 | 5-day roadmap PDF and the 3-person sprint deck added |
| 19 Sep | AshishSachdev | Generalised sprint template added |
| 19 Sep | Samir Omer | Repo restructured into the roadmap folder layout; all eight OHLCV CSVs consolidated into `data/raw/` (**Step 2** complete) |
| 19-20 Sep | Kumari2922 | Scope document with KPIs and business questions, plus the CAD $100,000 allocation spreadsheet (**Step 1**) |
| 19 Sep | Samir Omer | **Steps 3-4** - cleaning pipeline, EDA, 9 charts, findings write-up |
| 21 Sep | Kiran Gill | **Step 5** - portfolio and per-stock financial metrics |
| 23 Sep | Kumari2922 | **Step 6** - SQLite database loaded from the processed files |
| 23-24 Sep | Kumari2922 | **Step 7** - SQL analysis queries |
| 24 Sep | Kumari2922 | **Step 8** - Power BI dashboard, page 1 |

### Step-by-step status

| Step | Description | Status | Owner | Evidence |
| ---: | --- | --- | --- | --- |
| 1 | Objective, KPIs, business questions | Done | Kumari2922 | `KPIs and Business Questions/Project_Scope_QA.pdf` |
| 2 | Collect stock data | Done | Kumari2922 / Samir Omer | 8 CSVs in `data/raw/` |
| 3 | Data cleaning | Done | Samir Omer | `python/clean_data.py`, `reports/data_quality_report.md` |
| 4 | Exploratory analysis | Done | Samir Omer | `python/eda.py`, `reports/findings.md`, 9 charts |
| 5 | Financial performance metrics | Done | Kiran Gill | `python/performance_metrics.py`, `reports/metric_reports.md` |
| 6 | SQL database | Done, **defective** | Kumari2922 | `python/load_to_database.py`, `data/processed/stock_portfolio.db` |
| 7 | SQL analysis | Done, **extended** | Kumari2922 / Samir Omer | `SQL/portfolio_analysis.sql`, `SQL/views.sql`, `SQL/kpi_analysis.sql` |
| 8 | Power BI dashboard | **Partial** - 1 page of 4 | Kumari2922 | `reports/stock_portfolio_dashboard.pbix` |
| 9 | Business insights report | **Not started** | - | - |
| 10 | Publish portfolio | Partial - repo exists, README is 2 lines | - | `README.md` |

---

## 3. The two decisions that shaped everything

Two questions were open after Step 2 and were escalated rather than assumed. Both were answered on
19 September and encoded in `python/config.py`, where every later step reads them:

**Currency - all figures in CAD.** Every raw price file is a US listing quoted in USD, while the
scope document denominates the portfolio in CAD. Rather than relabel USD as CAD, a daily USD/CAD
series was added from the Bank of Canada. The Bank changed methodology in 2017 and publishes the
periods as two series, so both were taken and spliced at 2017-01-03; across their 82-day overlap they
agree to **0.081%**, so the splice leaves no step. Raw API responses are stored unedited in
`data/raw/` and documented in `data/raw/SOURCES.md`.

This was not cosmetic. USD/CAD rose **35.4%** over the window (1.0331 to 1.3988), which added
**+2.1 to +2.9 percentage points** to every holding's annual return and, less obviously, *lowered*
every volatility and drawdown figure - the Canadian dollar weakens when risk assets fall, which
cushions an unhedged Canadian holder. It also moved MSFT's worst drawdown into a different episode
(Nov 2022 in USD, Mar 2026 in CAD).

**Convention - buy and hold.** The allocation is bought once on 17 Sep 2010 and never rebalanced.
Share counts are fixed at purchase. Step 5 implemented exactly this, and the consequence turned out
to be the project's central result (section 4).

---

## 4. What the analysis found

Headline portfolio result, reproduced from `data/processed/metrics/portfolio_summary.csv`:

| Metric | Value |
| --- | ---: |
| Initial investment | CAD 100,000 |
| Value at 17 Sep 2026 | CAD 24,743,196 |
| Total return | +24,643% (247.4x) |
| CAGR | 41.1% |
| Annualised volatility | 32.8% |
| Sharpe ratio | 1.13 |
| Maximum drawdown | -56.7% (5 Jan 2023) |

**The result is one stock.** NVDA was bought at a 15% weight and ends at **74.4%** of portfolio
value, producing **74.7% of all profit**. With TSLA it accounts for roughly 90%. The two banks, 20%
of the opening portfolio, end at **0.6% combined**.

**So the allocation being tested stopped existing early on.** The 41.1% CAGR and the 1.13 Sharpe
describe a portfolio that drifted into a concentrated NVIDIA position - not the
20/20/15/15/10/10/10 allocation as written. This is the honest headline, and it should lead the
Step 9 report rather than the 247x multiple.

Supporting results hold up on re-check: 2022 is the only calendar year in which all seven holdings
fell; every holding survived a drawdown of at least 34%; RY and TD correlate at 0.79, so 20% of the
opening portfolio was close to one bet; and technology drove 81.8% of profit.

---

## 5. Review findings

### 5.1 HIGH - the banking sector is silently missing from every SQL result — **FIXED 24 Sep**

`python/load_to_database.py` builds the `Portfolio` table from the raw allocation spreadsheet, which
uses the Toronto tickers **`RY.TO` and `TD.TO`**. `Company_Master` and `Stock_Prices` use **`RY` and
`TD`**, as produced by the cleaning pipeline. Every `JOIN ... ON p.Ticker = c.Ticker` therefore drops
both banks with no error.

Confirmed by querying the committed database directly:

| Query | Rows returned | Rows expected |
| --- | ---: | ---: |
| Allocation by stock (`Portfolio` JOIN `Company_Master`) | **5** | 7 |
| Investment by sector | **2** (Technology, Consumer Discretionary) | 3 |

`SQL/portfolio_analysis.sql` records these same counts in its own result comments (`-- Result: 5 rows
returned`, `-- Result: 2 rows returned`), so the symptom was captured but not noticed. **Banking does
not appear anywhere in the SQL output**, and any Power BI visual sourced from these queries inherits
the omission - worth checking page 1 of the dashboard specifically.

**Fix applied.** `python/load_to_database.py` was rewritten to build `Portfolio` from
`data/processed/metrics/stock_performance_summary.csv` (Step 5), which already carries clean tickers,
with a `normalise_ticker()` helper that strips any `.TO` / `.US` suffix. The allocation spreadsheet is
still read, now as a cross-check that the investment amounts agree rather than as the source of
record. A `check_referential_integrity()` step runs after every load and raises if any `Portfolio`
ticker fails to join `Company_Master` or `Stock_Prices`, or if the join returns fewer than seven rows
— verified by reintroducing the `.TO` tickers in a scratch copy, where it fires as intended.

After reloading:

| Query | Before | After |
| --- | ---: | ---: |
| Allocation by stock | 5 rows | **7 rows** |
| Investment by sector | 2 sectors | **3 sectors** (Banking, 20.0%, restored) |
| `SELECT COUNT(*) FROM Portfolio` | 8 | **7** |

Indexes on `Stock_Prices(ticker)` and `Stock_Prices(date)` were added in the same pass.

*Still to do:* `SQL/portfolio_analysis.sql` carries the old counts in its tool-generated result
comments (`-- Result: 5 rows returned`, `-- Result: 2 rows returned`). Re-running the file in the SQL
editor will regenerate them. The **Step 8 dashboard still needs checking** — it was built while
banking was missing.

### 5.2 LOW - `Portfolio` carries a junk row and two empty columns — **FIXED 24 Sep**

The same load reads the spreadsheet's trailing **"Total" row**, producing an 8th row with a NULL
ticker and NULL amount. `SELECT COUNT(*) FROM Portfolio` therefore reports **8 stocks, not 7** - and
that query is in the committed SQL file.

`Number_of_Shares` and `Purchase_Price` are loaded as NULL, commented "not available in source data".
They *are* available: Step 5 computes both, and `reports/metric_reports.md` explicitly hands them
over ("`stock_performance_summary.csv` gives the `Portfolio` table its shares, purchase price and
investment amount"). The handoff note was missed.

**Fix applied.** Both were resolved by the same rewrite as 5.1 — sourcing `Portfolio` from the Step 5
output drops the spreadsheet's "Total" row and populates both columns (for example NVDA:
60,035.0605 shares at a CAD 0.2499 purchase price). The `Portfolio` table can now answer share-count
and purchase-price questions in SQL.

### 5.4 HIGH - the SQL layer computed no KPIs, and the obvious fix is wrong — **FIXED 24 Sep**

`SQL/portfolio_analysis.sql` has 13 `SELECT`s, but they cover table counts, date ranges, price
min/max and the static allocation amounts. **Not one KPI from the scope document is computed** - no
return, portfolio value, CAGR, volatility, Sharpe ratio or drawdown. One query labels
`(MAX(Close) - MIN(Close)) / MIN(Close)` as `Percent_Change`, which is the price *range*, not a
return: it ignores chronology, so a stock that fell over the window still reports a large positive
number.

This was partly blocked by 5.2 - with `Number_of_Shares` NULL, SQL could not value the portfolio on
any date. Once shares were loaded, every portfolio KPI follows from `SUM(shares * close)`.

**Fix applied.** Added `SQL/views.sql` (4 reusable views) and `SQL/kpi_analysis.sql` (16 queries)
covering all 13 KPIs and all 10 business questions, using CTEs, `CASE`, `HAVING` and the window
functions `LAG`, `RANK`, `DENSE_RANK`, `ROW_NUMBER`, `MAX() OVER`, `AVG() OVER` and `SUM() OVER`.
`SQL/portfolio_analysis.sql` was left untouched.

**A second silent-join defect was found while writing them.** The natural
`SUM(shares * close) ... GROUP BY date` is wrong: on 2011-02-17 three holdings have no quote, so the
sum adds four positions instead of seven and portfolio value appears to crash and rebound. That
inflated annualised volatility from 32.79% to 34.22% and cut the Sharpe ratio from 1.126 to 1.092.
`v_portfolio_daily` values each holding at its most recent close on or before the date instead - the
SQL equivalent of the `.ffill()` in `performance_metrics.py`. Same failure mode as 5.1: the query
returns a number, it is just the wrong one.

**Verification.** Every query was run and compared field by field against the Step 5 pandas outputs:
**60 of 60 cross-checks agree.** Details in `reports/sql_kpi_report.md`.

### 5.3 LOW - documentation drift

- `python/performance_metrics.py` docstring says `Run: python3 python/metrics.py`; the file is
  `performance_metrics.py`.
- `reports/report1.md` said "8 charts"; there are 9 (`09_fx_effect_on_risk.png` was added with the
  CAD re-run). Corrected in this pass.
- `README.md` is still two lines. Step 10 needs the full template from the sprint document.

### What holds up

- **The Python pipeline is reproducible.** `clean_data.py`, `eda.py` and `performance_metrics.py`
  were re-run from the committed state and reproduced every output byte-identically (clean
  `git status` afterwards).
- **The CAD and buy-and-hold decisions propagated correctly.** Step 5 reads `CURRENCY`,
  `REBALANCING`, `RISK_FREE_RATE` and `TRADING_DAYS_PER_YEAR` from `config.py` rather than
  re-deriving them, and its return and volatility figures agree with Step 4's.
- **Assumptions are labelled as assumptions** - the 3% risk-free rate, the 20%/35% risk-level
  cut-offs and the return-plus-Sharpe ranking rule are each stated as choices, with the component
  columns kept so another rule can be applied.
- **Raw data is untouched**, and the USD close and the FX rate used are retained on every row, so
  the currency conversion stays auditable.

---

## 6. Recommended order of work

1. ~~Fix the ticker join (5.1) and reload the database.~~ **Done 24 Sep** - verified by re-running
   the affected queries.
2. ~~Reload `Portfolio` from the Step 5 output (5.2).~~ **Done 24 Sep** in the same change.
3. ~~Add the missing KPI queries (5.4).~~ **Done 24 Sep** - `SQL/views.sql` and
   `SQL/kpi_analysis.sql`, verified against the pandas metrics.
4. **Refresh Step 7 and check Step 8.** Re-run `SQL/portfolio_analysis.sql` in the SQL editor so its
   result comments regenerate, then open the dashboard: page 1 was built while banking was missing
   from every sector and allocation query, so any visual sourced from those needs re-checking. The
   four new views are the cleanest source for pages 2-4.
5. **Finish Step 8** - pages 2-4 (stock performance, risk, sector).
6. **Write Step 9**, leading with the concentration result rather than the 247x multiple.
7. **Step 10** - expand the README to the template and add dashboard screenshots.

## 7. Known limitations carried by the whole project

These are documented in `reports/findings.md` and `reports/metric_reports.md` and are unchanged by
this review. They belong in the Step 9 report:

1. **Survivorship bias** - the seven tickers were chosen in 2026 with the outcomes known.
2. **Price returns only** - no dividends, which understates RY and TD most.
3. **No benchmark** - nothing shows whether the portfolio beat the market; a benchmark series is
   still missing from `data/raw/`.
4. **Currency risk sits inside every return**, by design; USD-denominated columns are kept alongside.
5. **Two FX methodologies** spliced at 2017-01-03 (agreeing to 0.081% across the overlap).
6. **RY and TD are the NYSE listings**; fine for price once converted, but their volume figures
   reflect US trading only and understate total activity.
7. **SHOP is in `data/raw/` but not in the portfolio** - retained with `in_portfolio = False`.
8. **2026 is a partial year**, running to 17 September.

---

## 8. How to reproduce

```bash
pip install -r requirements.txt
python3 python/clean_data.py          # Step 3 - raw -> data/processed/stock_prices_clean.csv
python3 python/eda.py                 # Step 4 - metric tables + 9 charts
python3 python/performance_metrics.py # Step 5 - portfolio KPIs
python3 python/load_to_database.py    # Step 6 - build the SQLite database
```

Run them in this order: Step 6 reads Step 5's output, which reads Step 3's. All four resolve paths
from `config.PROJECT_ROOT`, so they run from any working directory.
