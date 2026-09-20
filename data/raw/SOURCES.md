# Raw data sources

Nothing in this folder is edited by hand. Every file is the source response as received;
all transformation happens in `python/clean_data.py`.

## Daily stock prices - `*_us_d.csv`

Eight US-listed daily OHLCV files, `Date,Open,High,Low,Close,Volume`, split-adjusted,
**quoted in USD**. No ticker column - the ticker is recovered from the filename.

| File | Ticker | Coverage |
| --- | --- | --- |
| `aapl_us_d.csv` | AAPL | 2010-09-07 -> 2026-09-17 |
| `msft_us_d.csv` | MSFT | 1986-03-13 -> 2026-09-17 |
| `nvda_us_d.csv` | NVDA | 1999-01-22 -> 2026-09-17 |
| `amzn_us_d.csv` | AMZN | 1997-05-16 -> 2026-09-17 |
| `tsla_us_d.csv` | TSLA | 2010-06-28 -> 2026-09-17 |
| `ry_us_d.csv` | RY | 2005-02-25 -> 2026-09-17 |
| `td_us_d.csv` | TD | 2005-02-25 -> 2026-09-17 |
| `shop_us_d.csv` | SHOP | 2015-05-21 -> 2026-09-17 (not in the portfolio) |

RY and TD are the **NYSE** listings, not the TSX ones. Converted at the daily USD/CAD rate
below they are economically equivalent to the Toronto listings, since the two are linked by
arbitrage; see the note in `reports/data_quality_report.md`.

## USD/CAD exchange rate - Bank of Canada

The project reports in CAD, so every USD price is converted at the Bank of Canada daily rate.
The Bank changed its methodology in 2017 and publishes the two periods as separate series, so
both are stored here and spliced in the pipeline at **2017-01-03**.

| File | Series | Description | Coverage |
| --- | --- | --- | --- |
| `boc_usdcad_noon_IEXE0101.csv` | `IEXE0101` | USD noon rate (legacy) | 2010-09-01 -> 2017-04-28 |
| `boc_usdcad_daily_FXUSDCAD.csv` | `FXUSDCAD` | USD/CAD daily average rate | 2017-01-03 -> 2026-09-18 |

Both retrieved from the Bank of Canada Valet API on 2026-09-19:

```
https://www.bankofcanada.ca/valet/observations/IEXE0101/csv?start_date=2010-09-01&end_date=2017-12-31
https://www.bankofcanada.ca/valet/observations/FXUSDCAD/csv?start_date=2016-01-01
```

The two series overlap for 82 business days (Jan-Apr 2017). Across that overlap they differ by
**0.081% on average** (max 0.78%), so the splice introduces no visible step. Terms of use:
<https://www.bankofcanada.ca/terms/>.

## Portfolio allocation - `Stock_Portfolio_Investment_Allocation.xlsx`

The CAD $100,000 hypothetical allocation from the project scope document. Its contents are
mirrored in `python/config.py` so the pipeline has no spreadsheet dependency at runtime.
