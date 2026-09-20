- added what are the kips and business question for this project in that project scope file
-And in raw data folder i added one more small excel of investment data
## Steps 3 & 4 - cleaning and EDA (completed)

- `python/clean_data.py` builds `data/processed/stock_prices_clean.csv` (31,013 rows, 8 tickers) and
  `data/processed/company_master.csv`; it writes `reports/data_quality_report.md` with every check.
- `python/eda.py` builds the metric tables in `data/processed/` and 8 charts in `reports/figures/`.
- Findings are written up in `reports/findings.md`.
- Both open questions are now settled and encoded in `python/config.py`:
  **all prices are converted to CAD** at the Bank of Canada daily USD/CAD rate (two BoC series
  spliced at 2017-01-03, raw responses in `data/raw/`, documented in `data/raw/SOURCES.md`), and the
  portfolio convention is **buy and hold**, never rebalanced.
- The CAD switch is not cosmetic: USD/CAD rose 35.4% over the window, which added 2.1-2.9pp to every
  holding's annual return and *lowered* every volatility and drawdown figure. See Finding 1.
