-- =====================================================================
-- Reusable analysis views
-- Created by python/load_to_database.py after the three base tables are
-- loaded. Power BI and SQL/kpi_analysis.sql both read these, so the
-- portfolio-value logic is defined once.
--
-- Conventions (python/config.py): CAD prices, buy and hold, 252 trading
-- days a year. Every view joins to Portfolio, which restricts it to the
-- seven holdings (SHOP is in Stock_Prices but not in Portfolio).
-- =====================================================================

DROP VIEW IF EXISTS v_portfolio_daily;
DROP VIEW IF EXISTS v_holdings_current;
DROP VIEW IF EXISTS v_stock_daily_returns;
DROP VIEW IF EXISTS v_stock_annual_returns;


-- ---------------------------------------------------------------------
-- v_portfolio_daily - portfolio value on every trading day
--
-- Buy and hold, so value = SUM(fixed shares x close). A plain
-- SUM ... GROUP BY date would be wrong: on 2011-02-17 three holdings have
-- no quote, so the sum would silently drop them and show an artificial
-- crash and rebound, which inflates volatility. Instead each holding is
-- valued at its most recent close on or before the date - the SQL
-- equivalent of a forward fill.
-- ---------------------------------------------------------------------
CREATE VIEW v_portfolio_daily AS
WITH calendar AS (
    SELECT DISTINCT sp.date AS date
    FROM Stock_Prices sp
    JOIN Portfolio p ON p.Ticker = sp.ticker
),
grid AS (
    SELECT c.date, p.Ticker, p.Number_of_Shares
    FROM calendar c
    CROSS JOIN Portfolio p
),
valued AS (
    SELECT g.date,
           g.Ticker,
           g.Number_of_Shares * (
               SELECT sp.close
               FROM Stock_Prices sp
               WHERE sp.ticker = g.Ticker AND sp.date <= g.date
               ORDER BY sp.date DESC
               LIMIT 1
           ) AS holding_value
    FROM grid g
)
SELECT date,
       SUM(holding_value) AS portfolio_value
FROM valued
GROUP BY date;


-- ---------------------------------------------------------------------
-- v_holdings_current - one row per holding, valued at the latest close
-- ---------------------------------------------------------------------
CREATE VIEW v_holdings_current AS
WITH latest AS (SELECT MAX(date) AS d FROM Stock_Prices)
SELECT
    p.Ticker                                    AS ticker,
    cm.company_name                             AS company_name,
    cm.sector                                   AS sector,
    p.Investment_Amount                         AS investment_cad,
    p.Number_of_Shares                          AS shares,
    p.Purchase_Price                            AS purchase_price_cad,
    sp.close                                    AS current_price_cad,
    p.Number_of_Shares * sp.close               AS current_value_cad,
    p.Number_of_Shares * sp.close - p.Investment_Amount AS profit_loss_cad
FROM Portfolio p
JOIN Company_Master cm ON cm.ticker = p.Ticker
JOIN Stock_Prices sp   ON sp.ticker = p.Ticker
JOIN latest l          ON sp.date   = l.d;


-- ---------------------------------------------------------------------
-- v_stock_daily_returns - daily CAD return per holding
-- ---------------------------------------------------------------------
CREATE VIEW v_stock_daily_returns AS
SELECT sp.ticker,
       sp.date,
       sp.close,
       sp.close / LAG(sp.close) OVER (PARTITION BY sp.ticker ORDER BY sp.date) - 1
           AS daily_return
FROM Stock_Prices sp
JOIN Portfolio p ON p.Ticker = sp.ticker;


-- ---------------------------------------------------------------------
-- v_stock_annual_returns - calendar-year return per holding
-- The first year of each ticker has no prior year-end, so its return is
-- NULL; 2026 runs to 17 September only.
-- ---------------------------------------------------------------------
CREATE VIEW v_stock_annual_returns AS
WITH year_end AS (
    SELECT sp.ticker,
           CAST(STRFTIME('%Y', sp.date) AS INTEGER) AS yr,
           sp.close,
           ROW_NUMBER() OVER (
               PARTITION BY sp.ticker, STRFTIME('%Y', sp.date) ORDER BY sp.date DESC
           ) AS rn
    FROM Stock_Prices sp
    JOIN Portfolio p ON p.Ticker = sp.ticker
),
closing AS (
    SELECT ticker, yr, close FROM year_end WHERE rn = 1
)
SELECT ticker,
       yr AS year,
       close AS year_end_close,
       (close / LAG(close) OVER (PARTITION BY ticker ORDER BY yr) - 1) * 100
           AS annual_return_pct
FROM closing;
