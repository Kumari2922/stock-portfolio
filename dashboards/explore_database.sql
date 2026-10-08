-- Run SELECTs in DB Browser for SQLite's Execute SQL tab.
-- Open data/processed/stock_portfolio.db first. These queries do not modify it.

-- 1. Tables and views: what is in the database?
SELECT name, type FROM sqlite_master
WHERE type IN ('table', 'view') ORDER BY type, name;

-- 2. The seven holdings. SHOP is intentionally absent.
SELECT * FROM Portfolio ORDER BY Investment_Amount DESC;

-- 3. Daily source rows. close is CAD; close_usd is the original USD close.
SELECT date, ticker, close_usd, usdcad, close, volume
FROM Stock_Prices WHERE ticker = 'NVDA' ORDER BY date LIMIT 10;

-- 4. Join company information to holdings using ticker.
SELECT p.Ticker, c.company_name, c.sector, p.Investment_Amount
FROM Portfolio p JOIN Company_Master c ON c.ticker = p.Ticker;

-- 5. Ending holding values and dollar contribution.
SELECT ticker, investment_cad, current_value_cad, profit_loss_cad,
       100.0 * profit_loss_cad / SUM(profit_loss_cad) OVER () AS profit_share_pct,
       100.0 * current_value_cad / SUM(current_value_cad) OVER () AS ending_weight_pct
FROM v_holdings_current ORDER BY profit_loss_cad DESC;

-- 6. Portfolio values. The view carries missing quotes forward.
SELECT * FROM v_portfolio_daily ORDER BY date DESC LIMIT 10;

-- 7. Sector return uses the actual opening investments.
SELECT sector, SUM(investment_cad) AS invested_cad,
       SUM(current_value_cad) AS ending_value_cad,
       100.0 * SUM(profit_loss_cad) / SUM(investment_cad) AS sector_return_pct
FROM v_holdings_current GROUP BY sector ORDER BY sector_return_pct DESC;

-- 8. Annual returns. First year is NULL; 2026 is partial.
SELECT * FROM v_stock_annual_returns WHERE ticker = 'NVDA' ORDER BY year;
