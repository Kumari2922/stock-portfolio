# Exploratory Analysis - Key Findings

**Step 4 of the 5-day roadmap.** Analysis window **17 Sep 2010 - 17 Sep 2026** (4,024 trading days).
Universe: the seven holdings in the scope document's allocation.
**All figures are in CAD**, converted from the USD listings at the Bank of Canada daily USD/CAD rate.
The portfolio convention is **buy and hold** - bought once at the start of the window, never
rebalanced. All returns are **price returns** (no dividends), computed from
`data/processed/stock_prices_clean.csv` by `python/eda.py`.

---

## Summary table

| Ticker | Sector | Cumulative (CAD) | CAGR (CAD) | CAGR (USD) | FX adds | Volatility | Max drawdown |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NVDA | Technology | +122,697% | 56.0% | 53.1% | +2.9 pp | 44.9% | -63.5% |
| TSLA | Consumer Discretionary | +36,664% | 44.7% | 41.9% | +2.7 pp | 56.5% | -71.1% |
| AAPL | Technology | +5,430% | 28.5% | 26.1% | +2.4 pp | 27.8% | -40.8% |
| AMZN | Consumer Discretionary | +4,486% | 27.0% | 24.6% | +2.4 pp | 32.8% | -52.6% |
| MSFT | Technology | +3,377% | 24.8% | 22.5% | +2.3 pp | 26.0% | -34.6% |
| RY | Banking | +758% | 14.4% | 12.2% | +2.2 pp | 17.7% | -34.2% |
| TD | Banking | +621% | 13.1% | 11.0% | +2.1 pp | 18.8% | -36.0% |

Full table, including the USD-denominated comparisons: `data/processed/stock_metrics.csv`.

---

## Finding 1 - Being Canadian helped twice: it added return *and* cut risk

**Evidence.** USD/CAD went from **1.0331 to 1.3988 over the window, a 35.4% rise** (low 0.9449 in
Jul 2011, high 1.4603 in Feb 2025). For an unhedged Canadian holder that added **+2.1 to +2.9
percentage points to every holding's annual return**. It also *reduced* measured risk in all seven
cases - RY's annualised volatility falls from 19.9% in USD to **17.7% in CAD**, and its worst
drawdown from -40.0% to **-34.2%**. See `reports/figures/09_fx_effect_on_risk.png`.

**Business meaning.** The currency is not a rounding error on this portfolio - it is the third
largest driver of the result after stock selection and sector. And the effect is *stabilising*: the
Canadian dollar tends to weaken exactly when risk assets fall, so the CAD value of a US holding
falls less than its USD price does. A Canadian investor in US equities was paid to stay unhedged
over this particular window.

**Limitation.** This is one realisation of a 16-year currency path, not a law. A window in which
CAD strengthened would reverse both effects. Nothing here argues for leaving FX exposure unhedged in
future - it only measures what happened.

---

## Finding 2 - The result rests almost entirely on NVIDIA

**Evidence.** NVDA returned **+122,697%** in CAD, a 56.0% CAGR. Indexed from 100, it ends at
**122,797** against 36,764 for the next-best holding (TSLA) and 721 for the weaker bank (TD) -
**about 170x the TD result**. See `reports/figures/01_indexed_growth.png`.

**Business meaning.** Under buy and hold, a position compounding at 56% a year comes to dominate the
ending portfolio no matter what it started at. NVDA was bought at a 15% weight and ends as the
overwhelming majority of the portfolio's value. Any claim that "this allocation worked" is really a
claim about one holding, and the Step 5 portfolio metrics must report contribution to growth per
stock so that concentration is visible rather than implied.

**Limitation.** NVIDIA's run is a known ex-post outlier, and the tickers were chosen in 2026 with
the outcomes already known. The analysis shows what this allocation *would have produced*, not that
it was a reasonable choice in 2010.

---

## Finding 3 - Buy and hold means the allocation no longer exists

**Evidence.** The scope document's allocation is 20/20/15/15/10/10/10. Because the holdings
compounded at rates between 13.1% and 56.0% a year and were never rebalanced, the ending weights
bear no resemblance to the opening ones: NVDA's index rises to 122,797 while TD's reaches 721, a
ratio of roughly 170 to 1 on positions that started 1.5 to 1.

**Business meaning.** The stated 20% banking allocation describes the portfolio on day one and
essentially nothing afterwards. This is the direct consequence of the buy-and-hold decision, and it
is the single most important framing point for the Step 5 portfolio metrics: "total return" is the
return of a portfolio that drifted into a concentrated NVIDIA position, not of the allocation as
written.

**Limitation.** Exact ending weights are a Step 5 computation (they need share counts from the
opening CAD investment amounts); the figures above are index levels, which show the drift but are
not themselves position weights.

---

## Finding 4 - Higher return came with higher volatility, but the trade was not linear

**Evidence.** Annualised volatility rises with return across the seven, from 17.7% (RY) to 56.5%
(TSLA). The ordering breaks at the top: **TSLA carried the most risk (56.5%) and returned less than
NVDA** (44.7% vs 56.0% CAGR), which sat at 44.9%.
See `reports/figures/03_risk_vs_return.png`.

**Business meaning.** Volatility alone did not buy return. Ranking these properly needs a
risk-adjusted measure - the Sharpe ratio work in Step 5 - and on these inputs it will not reproduce
the raw return ranking.

**Limitation.** Volatility of daily returns treats upside and downside moves identically, so it
overstates the "risk" of a stock that mostly rose. Max drawdown (Finding 6) is the better companion
measure and is reported alongside.

---

## Finding 5 - 2022 was the only year every holding fell

**Evidence.** Across the 15 complete calendar years (2011-2025), **2022 is the single year in which
all seven holdings posted a negative CAD return** - from -1.7% (RY) to -62.6% (TSLA). In the
next-worst shared year, 2018, four of the seven still rose.
See `reports/figures/02_annual_returns_heatmap.png`.

**Business meaning.** Diversification across these seven names did not protect against a broad
market drawdown; it only protected against single-stock events. This is the concrete answer to
business question 8 ("how did major market events affect the portfolio?"). Note the currency at work
again: in USD the 2022 losses ran from -8.0% to -65.0%, in CAD from -1.7% to -62.6% - a weakening
CAD absorbed part of the fall.

**Limitation.** Calendar-year boundaries are arbitrary. The March 2020 COVID drawdown does not
appear here at all because it reversed within the year - both banks show a positive 2020 despite a
~35% peak-to-trough fall. Annual returns hide intra-year risk, which is why Finding 6 uses daily
drawdowns instead.

---

## Finding 6 - Every holding has survived a drawdown of at least 34%

**Evidence.** Worst peak-to-trough declines in CAD: TSLA -71.1% (trough Jan 2023), NVDA -63.5%
(Oct 2022), AMZN -52.6% (Dec 2022), AAPL -40.8% (Apr 2013), TD -36.0% and RY -34.2% (both
23 Mar 2020), MSFT -34.6% (Mar 2026). See `reports/figures/06_max_drawdown.png`.

**Business meaning.** The headline CAGRs required holding through losses of this size - which is
precisely what buy and hold commits to. Both bank troughs land on the same day, 23 March 2020, while
the growth names cluster in late 2022: a liquidity shock hit the banks, and a rate-driven repricing
hit growth stocks two years later.

**Limitation.** Drawdown is measured on daily closes, so it understates intraday extremes, and it
depends on the window start - a longer history would capture 2008 for RY and TD. Note also that
MSFT's worst CAD drawdown (Mar 2026) falls in a different episode from its worst USD drawdown
(Nov 2022): currency moved which event was worst for a Canadian holder.

---

## Finding 7 - Diversification is weaker than seven names suggests

**Evidence.** Average pairwise correlation of daily CAD returns is **0.39**. Within groups it is far
higher: **RY-TD is 0.79** and the three tech names average 0.51. TSLA is the least correlated
holding with everything else, at 0.31. See `reports/figures/04_correlation_matrix.png`.

**Business meaning.** RY and TD at 0.79 are close to one position held twice - together 20% of the
opening portfolio for roughly one bet on Canadian banking. The portfolio behaves more like three
blocks (tech, consumer, banking) than seven independent holdings.

**Limitation.** Pearson correlation on daily returns measures average co-movement in normal
conditions; correlations typically rise in a crash, so 0.39 understates how much these move together
in exactly the periods that matter. The common CAD conversion also adds a shared FX component to
every series, though the effect is small - the USD-denominated average is 0.42.

---

## Finding 8 - Sector is the dominant explanation of the spread

**Evidence.** Equal-weighted, never-rebalanced sector baskets, indexed from 100:
**Technology 43,935** (46.3% CAGR), **Consumer Discretionary 20,675** (39.6%), **Banking 789**
(13.8%). Banking also ran the lowest volatility (17.2% vs 35.5% and 46.1%) and the shallowest
drawdown (-34.8% vs -53.5% and -69.3%). See `reports/figures/07_sector_growth.png`.

**Business meaning.** This answers business question 4 directly: technology performed best by a wide
margin, and the two banks acted as the portfolio's volatility dampener rather than its growth
engine. The 20% banking allocation bought stability and cost return.

**Limitation.** Two of the three sectors contain only two stocks, and Technology's figure is pulled
up by NVIDIA - a "sector" result here is barely distinguishable from a single-stock result. Sector
labels are assigned manually in `python/config.py`, not sourced from a classification standard.

---

## 9. Limitations that apply to everything above

1. **Currency risk is now inside every return.** Converting at the daily rate is correct for a
   Canadian investor, but it means each CAD return blends stock performance with USD/CAD movement.
   The rate ranged from 0.9449 to 1.4603, so the effect is material and should be named whenever a
   CAD figure is quoted. `stock_metrics.csv` carries the USD-denominated columns alongside for
   exactly this reason.
2. **Two FX methodologies.** Pre-2017 figures use the Bank's legacy noon rate (`IEXE0101`),
   post-2017 its daily average rate (`FXUSDCAD`). They are not the same measurement, though across
   their 82-day overlap they agree to within 0.081% on average.
3. **RY and TD are the NYSE listings**, converted to CAD rather than taken from the TSX. The two are
   linked by arbitrage so this is economically equivalent for price, but their **volume** figures
   reflect US trading only and materially understate total activity.
4. **Price returns only.** The source has no dividend-adjusted series. This understates RY and TD
   most - the two highest-yielding holdings - so the gap between banking and tech in Finding 8 is
   somewhat overstated on a total-return basis.
5. **No benchmark.** There is no index series in `data/raw/`, so nothing here establishes whether
   any holding beat the market. Ingesting a benchmark is a Day-4 task and is still outstanding.
6. **Survivorship bias.** The seven tickers were chosen in 2026 with the outcomes known.
7. **SHOP excluded.** `shop_us_d.csv` exists but Shopify is not in the allocation and its history
   starts 2015-05-21 (70.8% window coverage). It is retained in the clean dataset with
   `in_portfolio = False` and appears in no portfolio figure.
8. **2026 is partial**, running to 17 Sep only; it is labelled YTD wherever it appears.
9. **No portfolio-level figures yet.** Portfolio value, total return, profit/loss, Sharpe ratio and
   performance ranking are Step 5 deliverables and are deliberately not computed here.

---

## Outputs produced by this step

| File | Contents |
| --- | --- |
| `data/processed/stock_prices_clean.csv` | Tidy daily OHLCV in CAD, with `close_usd`, `usdcad` and `fx_series` kept for audit |
| `data/processed/company_master.csv` | Ticker, company, sector, investment amount, allocation, listing |
| `data/processed/stock_metrics.csv` | Per-stock price, return and risk summary in CAD *and* USD |
| `data/processed/monthly_returns.csv` | Month-end close and monthly CAD return per ticker |
| `data/processed/annual_returns.csv` | Year-end close and annual CAD return per ticker |
| `data/processed/sector_summary.csv` | Equal-weighted, never-rebalanced sector baskets |
| `data/processed/correlation_matrix.csv` | 7x7 correlation of daily CAD returns |
| `reports/figures/01_indexed_growth.png` | CAD growth of all seven holdings |
| `reports/figures/02_annual_returns_heatmap.png` | Calendar-year CAD returns, year x ticker |
| `reports/figures/03_risk_vs_return.png` | Annualised CAD return vs volatility |
| `reports/figures/04_correlation_matrix.png` | Correlation of daily CAD returns |
| `reports/figures/05_rolling_volatility.png` | 30-day rolling volatility, small multiples |
| `reports/figures/06_max_drawdown.png` | Worst peak-to-trough decline per holding |
| `reports/figures/07_sector_growth.png` | Equal-weighted sector baskets over time |
| `reports/figures/08_volume_trend.png` | Average daily volume per year |
| `reports/figures/09_fx_effect_on_risk.png` | Risk measured in USD vs CAD |

## Handoff to Step 5

`stock_prices_clean.csv` and `company_master.csv` are ready to load into SQLite/PostgreSQL as
`Stock_Prices`, `Company_Master` and `Portfolio`. Both open questions from the previous pass are now
settled and encoded in `python/config.py` as `CURRENCY = "CAD"` and `REBALANCING = "buy-and-hold"`:

- Share counts are fixed at purchase, computed as `investment_cad / close` on **2010-09-17**, and
  never change. Portfolio value on any date is then `sum(shares * close)`.
- Because the portfolio is never rebalanced, Step 5 should report **ending weights alongside opening
  weights** - see Finding 3 - or the total-return figure will be read as a property of an allocation
  that stopped existing early in the window.
