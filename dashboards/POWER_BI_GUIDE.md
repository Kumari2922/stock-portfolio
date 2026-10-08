# Power BI dashboard build kit

The completed interactive dashboards are in `stock_portfolio_dashboard.html`. This kit supplies the same verified data for Power BI Desktop. It is not a new PBIX file. The original one-page `reports/stock_portfolio_dashboard.pbix` was not changed or refreshed.

## Import the prepared data

Open Power BI Desktop and use **Get Data → Text/CSV** for these files in `dashboards/powerbi_data/`. Rename queries exactly as shown:

| File | Query name | Key columns and types |
|---|---|---|
| `holdings_summary.csv` | `Holdings` | ticker Text; investment_cad, final_value_cad, cagr, volatility, sharpe, drawdown Decimal Number |
| `holding_values_daily.csv` | `HoldingValues` | date Date; ticker Text; holding_value_cad Decimal Number |
| `portfolio_daily.csv` | `PortfolioDaily` | date Date; portfolio_value_cad Decimal Number; drawdown_pct Decimal Number |
| `annual_returns.csv` | `AnnualReturns` | year Whole Number; ticker Text; annual_return_pct Decimal Number; partial_year True/False |
| `correlation.csv` | `Correlation` | ticker and other_ticker Text; correlation Decimal Number |
| `sector_summary.csv` | `SectorSummary` | sector Text; value columns Decimal Number |

CSV parsing locale: **English (Canada)** or another locale using a dot decimal separator. Confirm that date columns are Date, not Text. Growth/volatility/drawdown columns in `Holdings` are already percentage points: `41.12` means 41.12%, not 4,112%. Format those source columns as decimal values and label their visuals `%`. DAX ratio measures below are decimals such as `0.4112` and should use Percentage formatting.

Create one-to-many, single-direction relationships:

- `Holdings[ticker]` → `HoldingValues[ticker]`.
- `Holdings[ticker]` → `AnnualReturns[ticker]`.
- `Holdings[ticker]` → `Correlation[ticker]` if you want to filter correlation rows. Do not also relate `other_ticker` to the same table as an active relationship.

Create a `Calendar` table using the DAX below. Mark it as the date table, and relate `Calendar[Date]` to both `HoldingValues[date]` and `PortfolioDaily[date]`, with single-direction filters from Calendar. `PortfolioDaily` is always the whole seven-stock portfolio; a Holdings slicer cannot filter it. Use HoldingValues measures for ticker-responsive value charts.

```dax
Calendar = CALENDAR(MIN(HoldingValues[date]), MAX(HoldingValues[date]))
```

## Add measures

Copy the measures from `measures.dax`, creating one measure at a time in Power BI. Unless noted, they deliberately ignore the Calendar filter so headline cards always describe the whole study. They respond to selected holdings. Put date slicers only on chart pages and title cards “Full-period”. Do not let full-period risk numbers appear to recalculate for a shorter date window.

The supplied holding risk measures are per-stock, full-period values. **Do not average stock volatility, Sharpe, CAGR or drawdown to calculate portfolio risk.** Portfolio volatility and drawdown must come from the portfolio return/value series. The whole-portfolio headline values, verified for this snapshot, are volatility 32.792953%, Sharpe 1.125903 and max drawdown -56.702619%. They must not respond to ticker selections unless recalculated for the selected portfolio.

## Four page layouts

Use a 16:9 canvas, light background, white chart areas and one primary blue series colour. Add the reporting date, CAD convention and dividend exclusion near the top. Use four named pages:

### 1. Portfolio overview

Cards: Initial Investment, Ending Value, Profit, Total Return, CAGR. A daily line chart uses `Calendar[Date]` on the X axis **as the date itself**, not the automatic year hierarchy, and `Holding Value` on Y. A horizontal profit bar uses Holdings ticker and per-holding Profit. A sector allocation chart can use Holdings sector and Ending Value.

Initial investment should equal CAD $100,000 with all seven holdings selected. Ending value should equal CAD $24,743,195.57. Summing daily closes or summing daily portfolio values over time is invalid: a daily portfolio value is a snapshot, not additive across dates.

### 2. Stock performance

Daily line: Calendar date, `Stock Growth Index`, Holdings ticker legend. Heatmap/matrix: Holdings ticker rows, AnnualReturns year columns, annual return values. Use conditional formatting centred on zero. Exclude 2010; mark 2026 as YTD. Add stock table with CAGR, total return, volatility, Sharpe and drawdown.

The indexed line starts each stock at 100 and must be displayed per ticker. It is not an aggregate portfolio index. Source-column CAGR and return values are full-window values, not measures recalculated by the date slicer.

### 3. Risk & resilience

Scatter: ticker as detail, volatility as X, CAGR as Y, Sharpe and max drawdown in tooltip. Use per-ticker MAX or Don't summarise where supported, not SUM across holdings. Whole-portfolio drawdown line uses PortfolioDaily date and drawdown_pct. Correlation matrix uses ticker rows, other_ticker columns and correlation values.

Full portfolio drawdown cards and lines should be labelled “All seven holdings”. Avoid a shared ticker slicer on this page unless it affects only the scatter and matrix. These plots do not prove event causation.

### 4. Allocation & sectors

Clustered bars: ticker on X, opening_weight_pct and ending_weight_pct as values. Sector table: investment, ending value, sector return and share of profit. The opening sector proportions are 55% technology, 25% consumer discretionary, 20% banking. Ending proportions are approximately 81.72%, 17.64%, 0.64%.

The HTML has an implemented allocation scenario tool. Reproducing its scenarios in Power BI would require disconnected weight parameters and measures recalculating daily values from historical prices. That scenario model is not included in this Power BI CSV kit.

## Why the existing report needs correction

Its daily-close line groups dates by year and sums closes. Replace it with daily Holding Value or indexed growth. Its four existing visuals are not a full performance dashboard. Its original connection paths and compressed model could not be confirmed here; use **Transform Data → Data source settings** and inspect the Source steps when you open it locally.

Power BI Desktop supports CSV and ODBC. Reading SQLite directly requires a compatible SQLite ODBC driver. CSV import is the supplied route. CSVs are snapshots: rerun `build_dashboard.py` after updating SQLite, then refresh Power BI. Published reports using local files need an appropriate refresh setup.

Official references:
- https://learn.microsoft.com/power-bi/connect-data/desktop-data-sources
- https://learn.microsoft.com/power-query/connectors/odbc
- https://learn.microsoft.com/power-bi/transform-model/desktop-date-tables
