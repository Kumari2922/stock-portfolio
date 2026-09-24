-- =====================================================================
-- Step 7 - KPI analysis
-- Stock Portfolio Performance Analysis
--
-- Answers the 13 KPIs and the 10 business questions in
-- "KPIs and Business Questions/Project_Scope_QA.pdf" directly from the
-- database built by python/load_to_database.py.
--
-- Conventions, matching python/config.py:
--   * every price is CAD (converted at the Bank of Canada daily rate)
--   * buy and hold - Portfolio.Number_of_Shares is fixed at purchase
--   * 252 trading days a year; risk-free rate 3.0% for the Sharpe ratio
--   * SHOP is in Stock_Prices but not in Portfolio, so joining to
--     Portfolio restricts every query to the seven holdings
--
-- Reads the views in SQL/views.sql. SQLite has no STDDEV, so the sample
-- standard deviation is computed as
--     SQRT( (SUM(x*x) - n * AVG(x)^2) / (n - 1) )
--
-- Every figure here is cross-checked against data/processed/metrics/ -
-- see reports/sql_kpi_report.md.
-- =====================================================================


-- =====================================================================
-- SECTION A - PORTFOLIO KPIs
-- =====================================================================

-- ---------------------------------------------------------------------
-- A1. Investment, current value, profit/loss, total return
-- KPIs: Total Investment Amount, Current Portfolio Value,
--       Total Return (%), Profit/Loss (CAD).   Business question 3.
-- ---------------------------------------------------------------------
SELECT
    ROUND(SUM(investment_cad), 2)                                  AS total_investment_cad,
    ROUND(SUM(current_value_cad), 2)                               AS current_value_cad,
    ROUND(SUM(profit_loss_cad), 2)                                 AS profit_loss_cad,
    ROUND((SUM(current_value_cad) / SUM(investment_cad) - 1) * 100, 2)
                                                                   AS total_return_pct,
    ROUND(SUM(current_value_cad) / SUM(investment_cad), 2)         AS growth_multiple,
    CASE WHEN SUM(profit_loss_cad) > 0 THEN 'Profit'
         WHEN SUM(profit_loss_cad) < 0 THEN 'Loss'
         ELSE 'Break-even' END                                     AS profit_loss_status
FROM v_holdings_current;


-- ---------------------------------------------------------------------
-- A2. Annualised return (CAGR) of the portfolio
-- KPI: Annualized Return (CAGR)
-- ---------------------------------------------------------------------
WITH span AS (
    SELECT MIN(date) AS d0,
           MAX(date) AS d1,
           (julianday(MAX(date)) - julianday(MIN(date))) / 365.25 AS years
    FROM v_portfolio_daily
)
SELECT
    s.d0                                          AS start_date,
    s.d1                                          AS end_date,
    ROUND(s.years, 2)                             AS years,
    ROUND(v0.portfolio_value, 2)                  AS start_value_cad,
    ROUND(v1.portfolio_value, 2)                  AS end_value_cad,
    ROUND((POW(v1.portfolio_value / v0.portfolio_value, 1.0 / s.years) - 1) * 100, 2)
                                                  AS cagr_pct
FROM span s
JOIN v_portfolio_daily v0 ON v0.date = s.d0
JOIN v_portfolio_daily v1 ON v1.date = s.d1;


-- ---------------------------------------------------------------------
-- A3. Portfolio volatility and Sharpe ratio
-- KPIs: Portfolio Volatility, Sharpe Ratio
-- ---------------------------------------------------------------------
WITH returns AS (
    SELECT portfolio_value / LAG(portfolio_value) OVER (ORDER BY date) - 1 AS r
    FROM v_portfolio_daily
),
stats AS (
    SELECT COUNT(r) AS n, AVG(r) AS mean_r, SUM(r * r) AS sum_sq
    FROM returns WHERE r IS NOT NULL
)
SELECT
    n                                                              AS trading_days,
    ROUND(mean_r * 100, 4)                                         AS mean_daily_return_pct,
    ROUND(SQRT((sum_sq - n * mean_r * mean_r) / (n - 1)) * 100, 4) AS daily_volatility_pct,
    ROUND(SQRT((sum_sq - n * mean_r * mean_r) / (n - 1)) * SQRT(252) * 100, 2)
                                                                   AS annualised_volatility_pct,
    ROUND((mean_r - 0.03 / 252)
          / SQRT((sum_sq - n * mean_r * mean_r) / (n - 1)) * SQRT(252), 3)
                                                                   AS sharpe_ratio
FROM stats;


-- ---------------------------------------------------------------------
-- A4. Maximum drawdown of the portfolio
-- KPI: Maximum Drawdown.   Business question 8.
-- ---------------------------------------------------------------------
WITH drawdown AS (
    SELECT date,
           portfolio_value,
           MAX(portfolio_value) OVER (
               ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) AS running_peak
    FROM v_portfolio_daily
)
SELECT
    date                                               AS trough_date,
    ROUND(running_peak, 2)                             AS peak_value_cad,
    ROUND(portfolio_value, 2)                          AS trough_value_cad,
    ROUND((portfolio_value / running_peak - 1) * 100, 2) AS max_drawdown_pct
FROM drawdown
ORDER BY portfolio_value / running_peak ASC
LIMIT 1;


-- ---------------------------------------------------------------------
-- A5. Portfolio growth rate, year by year
-- KPI: Portfolio Growth Rate.   Business question 6.
-- 2010 and 2026 are partial years.
-- ---------------------------------------------------------------------
WITH year_end AS (
    SELECT CAST(STRFTIME('%Y', date) AS INTEGER) AS yr,
           portfolio_value,
           ROW_NUMBER() OVER (PARTITION BY STRFTIME('%Y', date) ORDER BY date DESC) AS rn
    FROM v_portfolio_daily
),
closing AS (SELECT yr, portfolio_value FROM year_end WHERE rn = 1)
SELECT
    yr                                                                  AS year,
    ROUND(portfolio_value, 2)                                           AS year_end_value_cad,
    ROUND(portfolio_value - LAG(portfolio_value) OVER (ORDER BY yr), 2) AS change_cad,
    ROUND((portfolio_value / LAG(portfolio_value) OVER (ORDER BY yr) - 1) * 100, 2)
                                                                        AS growth_pct
FROM closing
ORDER BY yr;


-- =====================================================================
-- SECTION B - STOCK PERFORMANCE
-- =====================================================================

-- ---------------------------------------------------------------------
-- B1. Return by stock, with ranking and best/worst flags
-- KPIs: Return by Stock (%), Best/Worst Performing Stock
-- Business question 1.
-- ---------------------------------------------------------------------
WITH bounds AS (
    SELECT ticker, MIN(date) AS first_date, MAX(date) AS last_date
    FROM v_stock_daily_returns GROUP BY ticker
),
endpoints AS (
    SELECT b.ticker, b.first_date, b.last_date,
           f.close AS first_close, l.close AS last_close,
           (julianday(b.last_date) - julianday(b.first_date)) / 365.25 AS years
    FROM bounds b
    JOIN Stock_Prices f ON f.ticker = b.ticker AND f.date = b.first_date
    JOIN Stock_Prices l ON l.ticker = b.ticker AND l.date = b.last_date
)
SELECT
    e.ticker,
    cm.company_name,
    cm.sector,
    ROUND(e.first_close, 4)                                                AS purchase_price_cad,
    ROUND(e.last_close, 2)                                                 AS current_price_cad,
    ROUND((e.last_close / e.first_close - 1) * 100, 2)                     AS return_pct,
    ROUND((POW(e.last_close / e.first_close, 1.0 / e.years) - 1) * 100, 2) AS cagr_pct,
    DENSE_RANK() OVER (ORDER BY e.last_close / e.first_close DESC)         AS return_rank,
    CASE WHEN e.last_close / e.first_close
              = MAX(e.last_close / e.first_close) OVER () THEN 'Best performer'
         WHEN e.last_close / e.first_close
              = MIN(e.last_close / e.first_close) OVER () THEN 'Worst performer'
         ELSE '' END                                                       AS flag
FROM endpoints e
JOIN Company_Master cm ON cm.ticker = e.ticker
ORDER BY return_pct DESC;


-- ---------------------------------------------------------------------
-- B2. Risk per stock - volatility, risk level, Sharpe ratio
-- KPIs: Portfolio Volatility (per stock), Sharpe Ratio
-- Business questions 2 and 9. Risk-level cut-offs match config.py.
-- ---------------------------------------------------------------------
WITH stats AS (
    SELECT ticker,
           COUNT(daily_return) AS n,
           AVG(daily_return) AS mean_r,
           SUM(daily_return * daily_return) AS sum_sq
    FROM v_stock_daily_returns
    WHERE daily_return IS NOT NULL
    GROUP BY ticker
),
risk AS (
    SELECT ticker, n, mean_r,
           SQRT((sum_sq - n * mean_r * mean_r) / (n - 1)) AS sd
    FROM stats
)
SELECT
    ticker,
    ROUND(sd * SQRT(252) * 100, 2)                                  AS annualised_volatility_pct,
    CASE WHEN sd * SQRT(252) * 100 < 20 THEN 'Low'
         WHEN sd * SQRT(252) * 100 < 35 THEN 'Medium'
         ELSE 'High' END                                            AS risk_level,
    ROUND((mean_r - 0.03 / 252) / sd * SQRT(252), 3)                AS sharpe_ratio,
    DENSE_RANK() OVER (ORDER BY sd DESC)                            AS risk_rank_1_is_riskiest,
    DENSE_RANK() OVER (ORDER BY (mean_r - 0.03 / 252) / sd DESC)    AS sharpe_rank
FROM risk
ORDER BY annualised_volatility_pct DESC;


-- ---------------------------------------------------------------------
-- B3. Maximum drawdown per stock
-- KPI: Maximum Drawdown (per stock)
-- ---------------------------------------------------------------------
WITH drawdown AS (
    SELECT ticker, date,
           close / MAX(close) OVER (
               PARTITION BY ticker ORDER BY date
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) - 1 AS dd
    FROM v_stock_daily_returns
),
worst AS (
    SELECT ticker, date, dd,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY dd ASC) AS rn
    FROM drawdown
)
SELECT ticker,
       ROUND(dd * 100, 2) AS max_drawdown_pct,
       date               AS trough_date
FROM worst
WHERE rn = 1
ORDER BY dd ASC;


-- ---------------------------------------------------------------------
-- B4. Profit/loss, weight drift and contribution to growth
-- KPI: Profit/Loss (CAD).   Business questions 5 and 10.
-- The opening-vs-ending weight gap is what buy-and-hold did to the
-- allocation: NVDA was bought at 15% and ends far above it.
-- ---------------------------------------------------------------------
SELECT
    ticker,
    ROUND(investment_cad, 2)                                              AS investment_cad,
    ROUND(investment_cad / SUM(investment_cad) OVER () * 100, 2)          AS opening_weight_pct,
    ROUND(current_value_cad, 2)                                           AS current_value_cad,
    ROUND(current_value_cad / SUM(current_value_cad) OVER () * 100, 2)    AS ending_weight_pct,
    ROUND(current_value_cad / SUM(current_value_cad) OVER () * 100
          - investment_cad / SUM(investment_cad) OVER () * 100, 2)        AS weight_drift_pp,
    ROUND(profit_loss_cad, 2)                                             AS profit_loss_cad,
    CASE WHEN profit_loss_cad > 0 THEN 'Profit'
         WHEN profit_loss_cad < 0 THEN 'Loss'
         ELSE 'Break-even' END                                            AS profit_loss_status,
    ROUND(profit_loss_cad / SUM(profit_loss_cad) OVER () * 100, 2)        AS contribution_to_growth_pct
FROM v_holdings_current
ORDER BY contribution_to_growth_pct DESC;


-- =====================================================================
-- SECTION C - SECTOR ANALYSIS
-- =====================================================================

-- ---------------------------------------------------------------------
-- C1. Sector-wise return, weight and contribution
-- KPI: Sector-wise Return.   Business question 4.
-- ---------------------------------------------------------------------
SELECT
    sector,
    COUNT(*)                                                              AS holdings,
    ROUND(SUM(investment_cad), 2)                                         AS invested_cad,
    ROUND(SUM(current_value_cad), 2)                                      AS current_value_cad,
    ROUND(SUM(profit_loss_cad), 2)                                        AS profit_loss_cad,
    ROUND((SUM(current_value_cad) / SUM(investment_cad) - 1) * 100, 2)    AS return_pct,
    ROUND(SUM(investment_cad) / SUM(SUM(investment_cad)) OVER () * 100, 2)
                                                                          AS opening_weight_pct,
    ROUND(SUM(current_value_cad) / SUM(SUM(current_value_cad)) OVER () * 100, 2)
                                                                          AS ending_weight_pct,
    ROUND(SUM(profit_loss_cad) / SUM(SUM(profit_loss_cad)) OVER () * 100, 2)
                                                                          AS contribution_to_growth_pct
FROM v_holdings_current
GROUP BY sector
ORDER BY return_pct DESC;


-- =====================================================================
-- SECTION D - MARKET AND TIME ANALYSIS
-- =====================================================================

-- ---------------------------------------------------------------------
-- D1. Best and worst six months for the portfolio
-- Business question 6.   Drop the final WHERE for the full history.
-- ---------------------------------------------------------------------
WITH month_end AS (
    SELECT STRFTIME('%Y-%m', date) AS month,
           portfolio_value,
           ROW_NUMBER() OVER (PARTITION BY STRFTIME('%Y-%m', date) ORDER BY date DESC) AS rn
    FROM v_portfolio_daily
),
monthly AS (
    SELECT month, portfolio_value,
           (portfolio_value / LAG(portfolio_value) OVER (ORDER BY month) - 1) * 100
               AS monthly_return_pct
    FROM month_end WHERE rn = 1
),
ranked AS (
    SELECT month, portfolio_value, monthly_return_pct,
           RANK() OVER (ORDER BY monthly_return_pct DESC) AS best_rank,
           RANK() OVER (ORDER BY monthly_return_pct ASC)  AS worst_rank
    FROM monthly WHERE monthly_return_pct IS NOT NULL
)
SELECT month,
       ROUND(portfolio_value, 2)                                 AS month_end_value_cad,
       ROUND(monthly_return_pct, 2)                              AS monthly_return_pct,
       CASE WHEN best_rank <= 6 THEN 'Best 6' ELSE 'Worst 6' END AS bucket
FROM ranked
WHERE best_rank <= 6 OR worst_rank <= 6
ORDER BY monthly_return_pct DESC;


-- ---------------------------------------------------------------------
-- D2. Which stocks outperformed consistently
-- Business question 7.
-- ---------------------------------------------------------------------
WITH scored AS (
    SELECT ticker, year, annual_return_pct,
           RANK() OVER (PARTITION BY year ORDER BY annual_return_pct DESC) AS rank_in_year
    FROM v_stock_annual_returns
    WHERE annual_return_pct IS NOT NULL
)
SELECT
    ticker,
    COUNT(*)                                                 AS years_measured,
    SUM(CASE WHEN annual_return_pct > 0 THEN 1 ELSE 0 END)   AS positive_years,
    SUM(CASE WHEN rank_in_year <= 3 THEN 1 ELSE 0 END)       AS years_in_top_3,
    SUM(CASE WHEN rank_in_year = 1 THEN 1 ELSE 0 END)        AS years_ranked_first,
    ROUND(AVG(annual_return_pct), 2)                         AS avg_annual_return_pct,
    ROUND(MIN(annual_return_pct), 2)                         AS worst_year_pct,
    ROUND(MAX(annual_return_pct), 2)                         AS best_year_pct
FROM scored
GROUP BY ticker
ORDER BY years_in_top_3 DESC, avg_annual_return_pct DESC;


-- ---------------------------------------------------------------------
-- D3. Years in which every holding fell - the market-event check
-- Business question 8.
-- HAVING keeps years where all, or all but one, holding was down.
-- ---------------------------------------------------------------------
SELECT
    year,
    COUNT(*)                                               AS holdings,
    SUM(CASE WHEN annual_return_pct < 0 THEN 1 ELSE 0 END) AS holdings_down,
    ROUND(MIN(annual_return_pct), 2)                       AS worst_pct,
    ROUND(MAX(annual_return_pct), 2)                       AS best_pct,
    ROUND(AVG(annual_return_pct), 2)                       AS avg_pct
FROM v_stock_annual_returns
WHERE annual_return_pct IS NOT NULL
GROUP BY year
HAVING SUM(CASE WHEN annual_return_pct < 0 THEN 1 ELSE 0 END) >= COUNT(*) - 1
ORDER BY avg_pct ASC;


-- ---------------------------------------------------------------------
-- D4. Average daily trading volume, and how it has trended
-- KPI: Average Daily Trading Volume
-- NOTE: RY and TD are the US listings, so their volume covers US trading
-- only and understates total activity. See data/raw/SOURCES.md.
-- ---------------------------------------------------------------------
WITH by_year AS (
    SELECT sp.ticker,
           CAST(STRFTIME('%Y', sp.date) AS INTEGER) AS yr,
           AVG(sp.volume) AS avg_volume
    FROM Stock_Prices sp
    JOIN Portfolio p ON p.Ticker = sp.ticker
    WHERE CAST(STRFTIME('%Y', sp.date) AS INTEGER) BETWEEN 2011 AND 2025  -- whole years only
    GROUP BY sp.ticker, yr
)
SELECT
    ticker,
    ROUND(AVG(avg_volume), 0)                                            AS avg_daily_volume,
    ROUND(MAX(CASE WHEN yr = 2011 THEN avg_volume END), 0)               AS avg_volume_2011,
    ROUND(MAX(CASE WHEN yr = 2025 THEN avg_volume END), 0)               AS avg_volume_2025,
    ROUND((MAX(CASE WHEN yr = 2025 THEN avg_volume END)
           / MAX(CASE WHEN yr = 2011 THEN avg_volume END) - 1) * 100, 2) AS change_pct
FROM by_year
GROUP BY ticker
ORDER BY avg_daily_volume DESC;


-- ---------------------------------------------------------------------
-- D5. 30-day moving average and day-over-day change
-- Window functions on the price series. Last 10 rows for NVDA - change
-- the ticker or drop the filter as needed.
-- ---------------------------------------------------------------------
WITH series AS (
    SELECT ticker, date, close, daily_return,
           AVG(close) OVER (PARTITION BY ticker ORDER BY date
                            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY date DESC)  AS rn_desc
    FROM v_stock_daily_returns
    WHERE ticker = 'NVDA'
)
SELECT
    date,
    ticker,
    ROUND(close, 2)                          AS close_cad,
    ROUND(ma_30, 2)                          AS moving_avg_30d,
    ROUND(daily_return * 100, 2)             AS change_pct,
    CASE WHEN close > ma_30 THEN 'Above 30-day average'
         ELSE 'Below 30-day average' END     AS trend
FROM series
WHERE rn_desc <= 10
ORDER BY date DESC;


-- ---------------------------------------------------------------------
-- D6. Correlation of daily returns between every pair of holdings
-- Business question 9 (diversification / risk-return balance).
-- Pearson r from sums; a < b keeps one row per pair.
-- ---------------------------------------------------------------------
WITH paired AS (
    SELECT a.ticker AS ticker_a, b.ticker AS ticker_b,
           a.daily_return AS x, b.daily_return AS y
    FROM v_stock_daily_returns a
    JOIN v_stock_daily_returns b
      ON a.date = b.date AND a.ticker < b.ticker
    WHERE a.daily_return IS NOT NULL AND b.daily_return IS NOT NULL
)
SELECT
    ticker_a,
    ticker_b,
    COUNT(*) AS observations,
    ROUND(
        (COUNT(*) * SUM(x * y) - SUM(x) * SUM(y))
        / (SQRT(COUNT(*) * SUM(x * x) - SUM(x) * SUM(x))
           * SQRT(COUNT(*) * SUM(y * y) - SUM(y) * SUM(y)))
    , 4) AS correlation
FROM paired
GROUP BY ticker_a, ticker_b
ORDER BY correlation DESC;
