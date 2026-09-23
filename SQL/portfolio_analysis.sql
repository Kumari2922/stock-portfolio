SELECT 
    COUNT(*) AS Total_Stocks,
    SUM(Investment_Amount) AS Total_Invested,
    ROUND(AVG(Investment_Amount), 2) AS Avg_Investment_Per_Stock,
    MAX(Investment_Amount) AS Largest_Position,
    MIN(Investment_Amount) AS Smallest_Position
FROM Portfolio;
-- EXECUTING SELECTION IN 'SQL 1*'
--
-- At line 1:
SELECT 'Stock_Prices' AS table_name, COUNT(*) AS rows FROM Stock_Prices
UNION ALL
SELECT 'Company_Master', COUNT(*) FROM Company_Master
UNION ALL
SELECT 'Portfolio', COUNT(*) FROM Portfolio;
-- Result: 3 rows returned in 42ms
-- EXECUTING ALL IN 'SQL 1*'
--
-- At line 1:
SELECT 'Stock_Prices' AS table_name, COUNT(*) AS rows FROM Stock_Prices
UNION ALL
SELECT 'Company_Master', COUNT(*) FROM Company_Master
UNION ALL
SELECT 'Portfolio', COUNT(*) FROM Portfolio;
-- Result: 3 rows returned in 18ms
-- At line 6:
SELECT 
    Ticker,
    MIN(Close) AS Lowest_Price,
    MAX(Close) AS Highest_Price,
    ROUND(((MAX(Close) - MIN(Close)) / MIN(Close)) * 100, 2) AS Percent_Change
FROM Stock_Prices
GROUP BY Ticker
ORDER BY Percent_Change DESC;
-- Result: 8 rows returned in 35ms
-- EXECUTING ALL IN 'SQL 1*'
--
-- At line 1:
SELECT MIN(Date) AS Earliest, MAX(Date) AS Latest FROM Stock_Prices;
-- Result: 1 rows returned in 41ms
-- EXECUTING ALL IN 'SQL 1*'
--
-- At line 1:
SELECT 
    p.Ticker,
    c.Company_Name,
    c.Sector,
    p.Investment_Amount,
    ROUND(p.Investment_Amount / SUM(p.Investment_Amount) OVER () * 100, 2) AS Percent_of_Portfolio
FROM Portfolio p
JOIN Company_Master c ON p.Ticker = c.Ticker
ORDER BY p.Investment_Amount DESC;
-- Result: 5 rows returned in 29ms
-- EXECUTING ALL IN 'SQL 1*'
--
-- At line 1:
SELECT 
    c.Sector,
    SUM(p.Investment_Amount) AS Total_Investment,
    ROUND(SUM(p.Investment_Amount) / (SELECT SUM(Investment_Amount) FROM Portfolio) * 100, 2) AS Percent_of_Total
FROM Portfolio p
JOIN Company_Master c ON p.Ticker = c.Ticker
GROUP BY c.Sector
ORDER BY Total_Investment DESC;
-- Result: 2 rows returned in 21ms
-- EXECUTING ALL IN 'SQL 1*'
--
-- At line 1:
SELECT 
    Ticker,
    ROUND(AVG(Volume), 0) AS Avg_Daily_Volume,
    MAX(Volume) AS Max_Volume,
    MIN(Volume) AS Min_Volume
FROM Stock_Prices
GROUP BY Ticker
ORDER BY Avg_Daily_Volume DESC;
-- Result: 8 rows returned in 50ms
-- EXECUTING ALL IN 'SQL 1*'
--
-- At line 1:
SELECT 
    COUNT(*) AS Total_Stocks,
    SUM(Investment_Amount) AS Total_Invested,
    ROUND(AVG(Investment_Amount), 2) AS Avg_Investment_Per_Stock,
    MAX(Investment_Amount) AS Largest_Position,
    MIN(Investment_Amount) AS Smallest_Position
FROM Portfolio;
-- Result: 1 rows returned in 23ms