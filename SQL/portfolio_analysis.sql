SELECT 
    COUNT(*) AS Total_Stocks,
    SUM(Investment_Amount) AS Total_Invested,
    ROUND(AVG(Investment_Amount), 2) AS Avg_Investment_Per_Stock,
    MAX(Investment_Amount) AS Largest_Position,
    MIN(Investment_Amount) AS Smallest_Position
FROM Portfolio;
