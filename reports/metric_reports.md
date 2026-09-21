# Step 5 - Financial Performance Metrics

**Step 5 of the 5-day roadmap.** Analysis window **17 Sep 2010 - 17 Sep 2026** (16 years).
Universe: the seven holdings in the scope document's allocation (SHOP excluded).
**All figures are in CAD**, converted from the USD listings at the Bank of Canada daily rate.
The portfolio is **buy and hold**: CAD $100,000 invested once on 17 Sep 2010 and never rebalanced.
All returns are **price returns** (no dividends). Produced by `python/performance_metrics.py` from
`data/processed/stock_prices_clean.csv`.

---

## 1. Method

1. **Shares are fixed at purchase.** On 17 Sep 2010 each investment amount is divided by that day's
   CAD close to give a share count. The count never changes.
2. **Portfolio value on any date** is the sum of `shares x close` across the seven holdings.
3. **Volatility** is the standard deviation of daily returns x sqrt(252).
4. **Sharpe ratio** is the mean daily excess return over a 3.0% annual risk-free rate, divided by its
   standard deviation, x sqrt(252). The 3.0% is a stated assumption (`config.py`), not a measured input.
5. **Max drawdown** is the worst peak-to-trough fall of the daily value series.
6. **Risk level** is set from annualised volatility: **Low** below 20%, **Medium** 20-35%,
   **High** above 35%. These cut-offs are an assumption, not a standard.
7. **Performance ranking** is the sum of a stock's return rank and Sharpe rank, re-ranked
   (ties share a rank). The roadmap does not define a ranking method; `return_rank` and
   `sharpe_rank` are kept as separate columns so any other rule can be applied.
8. **Contribution to growth** is each stock's profit divided by total portfolio profit.

---

## 2. Portfolio metrics

| Metric | Value |
| --- | ---: |
| Initial investment | CAD 100,000 |
| Current portfolio value (17 Sep 2026) | CAD 24,743,196 |
| Profit | CAD 24,643,196 |
| Total return | +24,643% (247.4x) |
| CAGR | 41.1% |
| Average calendar-year growth | 48.6% |
| Annualised volatility | 32.8% |
| Sharpe ratio | 1.13 |
| Maximum drawdown | -56.7% (5 Jan 2023) |
| Best stock (return) | NVDA |
| Worst stock (return) | TD |

---

## 3. Stock performance summary

Sorted by performance rank. `Return` is cumulative CAD price return over the window.

| Rank | Ticker | Sector | Return | CAGR | Volatility | Sharpe | Max drawdown | Risk level |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | NVDA | Technology | +122,697% | 56.0% | 44.9% | 1.15 | -63.5% | High |
| 2 | AAPL | Technology | +5,430% | 28.5% | 27.8% | 0.94 | -40.8% | Medium |
| 2 | TSLA | Consumer Disc. | +36,664% | 44.7% | 56.5% | 0.88 | -71.1% | High |
| 4 | MSFT | Technology | +3,377% | 24.8% | 26.0% | 0.87 | -34.6% | Medium |
| 4 | AMZN | Consumer Disc. | +4,486% | 27.0% | 32.8% | 0.80 | -52.6% | Medium |
| 6 | RY | Banking | +758% | 14.4% | 17.7% | 0.68 | -34.2% | Low |
| 7 | TD | Banking | +621% | 13.1% | 18.8% | 0.59 | -36.0% | Low |

Return and volatility agree with Step 4 (`stock_metrics.csv`).

---

## 4. Weights and contribution to growth

| Ticker | Opening weight | Ending weight | Profit (CAD) | Share of total profit |
| --- | ---: | ---: | ---: | ---: |
| NVDA | 15.0% | 74.4% | 18,404,525 | 74.7% |
| TSLA | 10.0% | 14.9% | 3,666,427 | 14.9% |
| AAPL | 20.0% | 4.5% | 1,086,052 | 4.4% |
| MSFT | 20.0% | 2.8% | 675,395 | 2.7% |
| AMZN | 15.0% | 2.8% | 672,919 | 2.7% |
| RY | 10.0% | 0.4% | 75,781 | 0.3% |
| TD | 10.0% | 0.3% | 62,098 | 0.3% |

### Sector view (actual holdings)

| Sector | Invested | Ending value | Return | CAGR | Ending weight | Share of profit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Technology | 55,000 | 20,220,971 | +36,665% | 44.7% | 81.7% | 81.8% |
| Consumer Discretionary | 25,000 | 4,364,345 | +17,357% | 38.1% | 17.6% | 17.6% |
| Banking | 20,000 | 157,879 | +689% | 13.8% | 0.6% | 0.6% |

---

## 5. Findings

**1. The portfolio result is one stock.** NVDA started at 15% of the portfolio and ends at 74.4%,
producing 74.7% of all profit. NVDA and TSLA together produce about 90%. Any claim that "this
allocation worked" is a claim about NVDA.

**2. The opening allocation no longer exists.** The two banks were 20% of the opening portfolio and
end at 0.6% combined. AAPL and MSFT, the two largest opening positions at 20% each, end at 4.5% and
2.8%. This is the direct consequence of buy and hold, and answers business question 10 (how
allocation affects long-term growth): here, the allocation mattered far less than which stocks were
held.

**3. NVDA also leads on risk-adjusted return.** It ranks first on both raw return and Sharpe ratio
(1.15). TSLA's second place on return reflects a 56.5% volatility, the highest of the seven, and
drops to third on Sharpe. For business question 9 (best risk-return balance), NVDA is best,
followed by AAPL.

**4. The banks were stable but earned the least.** RY and TD carry the lowest volatility (17.7% and
18.8%, "Low" risk) and the lowest Sharpe ratios (0.68 and 0.59). Their -34% to -36% drawdowns both
occurred on 23 Mar 2020.

**5. The portfolio's own risk is lower than its growth stocks'.** Portfolio volatility is 32.8% and
maximum drawdown -56.7%, milder than TSLA (-71.1%) or NVDA (-63.5%) alone, but far deeper than a
diversified portfolio would normally show, because the portfolio became concentrated in NVDA.

**6. Technology is the best-performing sector** (+36,665%, 81.8% of profit), then Consumer
Discretionary, then Banking. Answers business question 4 on the actual holdings; Step 4's sector
baskets are equal-weighted and differ slightly.

---

## 6. Limitations

1. **Concentration hides in the headline.** The 41.1% CAGR and Sharpe of 1.13 describe a portfolio
   that became 74% NVDA, not the 20/20/15/15/10/10/10 allocation as written.
2. **Survivorship bias.** The seven tickers were chosen in 2026 with outcomes already known.
3. **Price returns only.** No dividends, which understates RY and TD most.
4. **Currency is inside every figure.** USD/CAD rose 35.4% over the window; see Step 4, Finding 1.
5. **No benchmark.** Nothing here shows whether the portfolio beat the market.
6. **Assumption-driven labels.** Sharpe depends on the 3% risk-free rate; risk level depends on the
   20% / 35% cut-offs; performance rank depends on the return-plus-Sharpe rule.
7. **Volatility treats up and down moves alike**, so it overstates the risk of stocks that mostly
   rose. Maximum drawdown is the better companion measure.
8. **Business questions 7 and 8** (consistent outperformers, market events) need year-by-year and
   event analysis and are left to Step 7 (SQL) and the final report.

---

## 7. Outputs produced by this step

| File | Contents |
| --- | --- |
| `python/performance_metrics.py` | The script that produces everything below |
| `data/processed/metrics/portfolio_summary.csv` | Portfolio KPIs (one metric per row) |
| `data/processed/metrics/stock_performance_summary.csv` | Per-stock return, risk, Sharpe, risk level, ranks |
| `data/processed/metrics/portfolio_weights.csv` | Opening vs ending weight and contribution to growth |
| `data/processed/metrics/portfolio_sector_summary.csv` | Sector value, return and contribution |
| `data/processed/metrics/portfolio_value_daily.csv` | Daily value and profit/loss per holding and in total, with drawdown |

## Handoff to Step 6

`stock_performance_summary.csv` gives the `Portfolio` table its shares, purchase price and investment
amount (`shares`, `purchase_price_cad`, `investment_cad`). `stock_prices_clean.csv` and
`company_master.csv` load as `Stock_Prices` and `Company_Master`.