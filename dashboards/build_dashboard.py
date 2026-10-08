"""Build offline dashboards and Power BI CSVs from the repository's SQLite DB.

Run from any folder: python dashboards/build_dashboard.py
Dependencies: pandas, numpy, plotly. No database writes or network requests.
"""
from pathlib import Path
import json
import sqlite3
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from config import RISK_FREE_RATE, TRADING_DAYS_PER_YEAR, INITIAL_INVESTMENT

OUT = ROOT / 'dashboards'
EXPORT = OUT / 'powerbi_data'
EXPORT.mkdir(exist_ok=True)
DB = ROOT / 'data/processed/stock_portfolio.db'
with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as conn:
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    holdings = pd.read_sql('SELECT p.*, c.company_name, c.sector FROM Portfolio p JOIN Company_Master c ON p.Ticker=c.ticker ORDER BY p.Ticker', conn)
    prices = pd.read_sql('SELECT s.* FROM Stock_Prices s JOIN Portfolio p ON s.ticker=p.Ticker ORDER BY s.date,s.ticker', conn, parse_dates=['date'])
    sql_daily = pd.read_sql('SELECT * FROM v_portfolio_daily ORDER BY date', conn)

tickers = holdings.Ticker.tolist()
close = prices.pivot(index='date', columns='ticker', values='close')[tickers].ffill()
usd = prices.pivot(index='date', columns='ticker', values='close_usd')[tickers].ffill()
assert close.notna().all().all() and close.index.is_unique
investment = holdings.set_index('Ticker').Investment_Amount.reindex(tickers)
# Exact shares avoid the four-decimal rounding in the DB's Portfolio table.
shares = investment / close.iloc[0]
values = close.mul(shares)
total = values.sum(axis=1)
years = (close.index[-1] - close.index[0]).days / 365.25
returns = close.pct_change().iloc[1:]
port_returns = total.pct_change().iloc[1:]
dd = (total / total.cummax() - 1) * 100

def metrics(s):
    r = s.pct_change().dropna()
    return dict(final=float(s.iloc[-1]), total_return=float((s.iloc[-1]/s.iloc[0]-1)*100),
                cagr=float(((s.iloc[-1]/s.iloc[0])**(1/years)-1)*100),
                volatility=float(r.std()*np.sqrt(TRADING_DAYS_PER_YEAR)*100),
                sharpe=float((r.mean()-RISK_FREE_RATE/TRADING_DAYS_PER_YEAR)/r.std()*np.sqrt(TRADING_DAYS_PER_YEAR)),
                drawdown=float((s/s.cummax()-1).min()*100))

kpi = metrics(total)
stocks = pd.DataFrame([{**metrics(close[t]), 'ticker':t,
    'company_name':holdings.set_index('Ticker').loc[t,'company_name'],
    'sector':holdings.set_index('Ticker').loc[t,'sector'],
    'investment_cad':float(investment[t]), 'shares':float(shares[t]),
    'final_value_cad':float(values[t].iloc[-1]),
    'profit_cad':float(values[t].iloc[-1]-investment[t]),
    'opening_weight_pct':float(investment[t]/investment.sum()*100),
    'ending_weight_pct':float(values[t].iloc[-1]/total.iloc[-1]*100),
    'profit_share_pct':float((values[t].iloc[-1]-investment[t])/(total.iloc[-1]-investment.sum())*100),
    'usd_cagr':metrics(usd[t])['cagr']} for t in tickers])
annual_close = close.groupby(close.index.year).last()
annual = annual_close.pct_change().iloc[1:]*100
port_annual = total.groupby(total.index.year).last().pct_change().iloc[1:]*100
full_years = annual.loc[2011:2025]
consistency = pd.DataFrame({'ticker':tickers,
    'positive_years':(full_years>0).sum().reindex(tickers).values,
    'years_above_portfolio':full_years.gt(port_annual.loc[2011:2025], axis=0).sum().reindex(tickers).values,
    'full_years':len(full_years)})
stocks = stocks.merge(consistency, on='ticker')
correlation = returns.corr()

# Meaningful reconciliation: source KPIs, DB rounding, and portfolio membership.
csv_kpi = pd.read_csv(ROOT/'data/processed/metrics/portfolio_summary.csv').set_index('metric').value
assert len(tickers)==7 and 'SHOP' not in tickers
assert abs(total.iloc[0]-INITIAL_INVESTMENT)<1e-7
assert abs(kpi['final']-float(csv_kpi['current_portfolio_value_cad']))<0.02
assert abs(kpi['cagr']-float(csv_kpi['cagr_pct']))<0.01
assert abs(kpi['volatility']-float(csv_kpi['annualised_volatility_pct']))<0.01
assert abs(kpi['drawdown']-float(csv_kpi['max_drawdown_pct']))<0.01
assert np.max(np.abs(total.values-sql_daily.portfolio_value.values))<0.02
assert np.allclose(values.sum(axis=1),total)
assert abs(stocks.ending_weight_pct.sum()-100)<1e-8
assert abs(stocks.profit_share_pct.sum()-100)<1e-8
# Default and single-stock scenarios reproduce their underlying price paths.
ratios = close/close.iloc[0]
assert np.allclose(ratios.mul(investment).sum(axis=1),total)
assert np.allclose(ratios['NVDA']*100000,close['NVDA']/close['NVDA'].iloc[0]*100000)

daily = pd.DataFrame({'date':close.index.strftime('%Y-%m-%d'), 'portfolio_value_cad':total.values,
    'profit_cad':total.values-investment.sum(), 'daily_return':total.pct_change().values,
    'drawdown_pct':dd.values})
daily.to_csv(EXPORT/'portfolio_daily.csv', index=False)
stocks.to_csv(EXPORT/'holdings_summary.csv',index=False)
long = values.rename_axis('date').reset_index().melt(id_vars='date',var_name='ticker',value_name='holding_value_cad')
long['date']=long.date.dt.strftime('%Y-%m-%d')
long.to_csv(EXPORT/'holding_values_daily.csv',index=False)
annual_long=annual.rename_axis('year').reset_index().melt(id_vars='year',var_name='ticker',value_name='annual_return_pct')
annual_long['partial_year']=annual_long.year==2026
annual_long.to_csv(EXPORT/'annual_returns.csv',index=False)
correlation.rename_axis('ticker').reset_index().melt(id_vars='ticker',var_name='other_ticker',value_name='correlation').to_csv(EXPORT/'correlation.csv',index=False)
stocks.groupby('sector')[['investment_cad','final_value_cad','profit_cad']].sum().to_csv(EXPORT/'sector_summary.csv')

COLORS = ['#4169e1','#0d9488','#8b5cf6','#f59e0b','#e55a77','#65873e','#64748b']
color=dict(zip(tickers,COLORS))
figs={}
def finish(key,fig,ylabel='',height=350):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=65,r=25,t=25,b=55),
        font=dict(family='Arial, sans-serif',size=13,color='#26334d'),paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',legend=dict(orientation='h',y=1.14,x=0),
        yaxis_title=ylabel,hovermode='closest')
    figs[key]=json.loads(fig.to_json())

fig=go.Figure(go.Scatter(x=daily.date,y=total,mode='lines',line=dict(color='#4169e1',width=2),name='Portfolio',hovertemplate='%{x}<br>CAD %{y:,.0f}<extra></extra>'))
fig.update_layout(xaxis=dict(rangeslider=dict(visible=True,thickness=.08)),updatemenus=[dict(type='buttons',direction='left',x=1,y=1.15,xanchor='right',buttons=[dict(label='Linear',method='relayout',args=[{'yaxis.type':'linear'}]),dict(label='Log',method='relayout',args=[{'yaxis.type':'log'}])])])
finish('growth',fig,'Value (CAD)',400)
ranked=stocks.sort_values('profit_cad')
finish('profit',go.Figure(go.Bar(x=ranked.profit_cad,y=ranked.ticker,orientation='h',marker_color=[color[t] for t in ranked.ticker],hovertemplate='%{y}<br>CAD %{x:,.0f}<extra></extra>')),'',350)
figs['profit']['layout']['xaxis']={'title':{'text':'Profit (CAD)'}}
fig=go.Figure()
for t in tickers:
    fig.add_trace(go.Scatter(x=daily.date,y=ratios[t]*100,mode='lines',name=t,line=dict(color=color[t],width=2),hovertemplate='%{x}<br>Index %{y:,.1f}<extra>'+t+'</extra>'))
fig.update_yaxes(type='log');finish('indexed',fig,'Growth index, start = 100 (log scale)',420)
finish('annual',go.Figure(go.Heatmap(x=[str(y)+(' YTD' if y==2026 else '') for y in annual.index],y=tickers,z=annual[tickers].T.values,
    zmin=-100,zmax=100,zmid=0,colorscale=[[0,'#c64b60'],[.5,'#f5f7fb'],[1,'#168674']],text=np.round(annual[tickers].T.values,1),texttemplate='%{text}%',textfont=dict(size=11),hovertemplate='%{y} · %{x}<br>%{z:.2f}%<extra></extra>',colorbar=dict(title='%'))),'',420)
fig=go.Figure([go.Bar(name='Positive return',x=stocks.ticker,y=stocks.positive_years,marker_color='#0d9488'),go.Bar(name='Beat portfolio',x=stocks.ticker,y=stocks.years_above_portfolio,marker_color='#4169e1')]);fig.update_layout(barmode='group');fig.update_yaxes(range=[0,15],dtick=3);finish('consistency',fig,'Number of full years (2011–2025)')
fig=go.Figure()
for sector,g in stocks.groupby('sector'):
    sector_color={'Banking':'#0d9488','Technology':'#4169e1','Consumer Discretionary':'#f59e0b'}[sector]
    fig.add_trace(go.Scatter(x=g.volatility,y=g.cagr,mode='markers+text',text=g.ticker,textposition=['bottom right' if t=='TD' else 'top left' if t=='RY' else 'top center' for t in g.ticker],name=sector,marker=dict(size=16,color=sector_color),customdata=g[['ticker','sharpe','drawdown']].values,hovertemplate='%{customdata[0]}<br>Volatility %{x:.2f}%<br>CAGR %{y:.2f}%<br>Sharpe %{customdata[1]:.3f}<br>Drawdown %{customdata[2]:.2f}%<extra></extra>'))
fig.add_trace(go.Scatter(x=[kpi['volatility']],y=[kpi['cagr']],mode='markers+text',text=['Portfolio'],textposition='bottom center',name='Portfolio',marker=dict(symbol='diamond',size=18,color='#16223b')))
fig.update_xaxes(title='Annualised volatility (%)');finish('riskreturn',fig,'CAGR (%)',400)
finish('drawdown',go.Figure(go.Scatter(x=daily.date,y=dd,fill='tozeroy',line=dict(color='#c64b60'),hovertemplate='%{x}<br>%{y:.2f}% below peak<extra></extra>')),'Fall below previous peak (%)',370)
finish('correlation',go.Figure(go.Heatmap(x=tickers,y=tickers,z=correlation.values,zmin=-1,zmax=1,zmid=0,colorscale=[[0,'#c64b60'],[.5,'#f5f7fb'],[1,'#4169e1']],text=np.round(correlation.values,2),texttemplate='%{text}',colorbar=dict(title='r'),hovertemplate='%{x} / %{y}<br>Correlation %{z:.3f}<extra></extra>')),'',400)
fig=go.Figure([go.Bar(name='Opening',x=stocks.ticker,y=stocks.opening_weight_pct,marker_color='#a7b8ef'),go.Bar(name='Ending',x=stocks.ticker,y=stocks.ending_weight_pct,marker_color='#4169e1')]);fig.update_layout(barmode='group');finish('weights',fig,'Portfolio weight (%)')
sector=stocks.groupby('sector')[['investment_cad','final_value_cad','profit_cad']].sum()
fig=go.Figure([go.Bar(name='Opening',x=sector.index,y=sector.investment_cad/investment.sum()*100,marker_color='#a7b8ef'),go.Bar(name='Ending',x=sector.index,y=sector.final_value_cad/total.iloc[-1]*100,marker_color='#4169e1')]);fig.update_layout(barmode='group');finish('sector',fig,'Portfolio weight (%)')
fig=go.Figure([go.Bar(name='USD',x=stocks.ticker,y=stocks.usd_cagr,marker_color='#a7b8ef'),go.Bar(name='CAD',x=stocks.ticker,y=stocks.cagr,marker_color='#4169e1')]);fig.update_layout(barmode='group');finish('fx',fig,'CAGR (%)')
payload=dict(figs=figs, dates=daily.date.tolist(), ratios=np.round(ratios.values,9).tolist(),
    tickers=tickers,weights=(investment/investment.sum()*100).tolist(),baseline=total.tolist(),
    kpi=kpi,years=years,rf=RISK_FREE_RATE, tradingDays=TRADING_DAYS_PER_YEAR)
template=(OUT/'dashboard_template.html').read_text()
cards=''.join(f'<div class="metric"><span>{label}</span><strong>{val}</strong></div>' for label,val in [
    ('Initial investment','CAD $100,000'),('Ending value',f'CAD ${kpi["final"]/1e6:.2f}M'),
    ('Total price return',f'{kpi["total_return"]:,.1f}%'),('Annualised growth (CAGR)',f'{kpi["cagr"]:.2f}%'),
    ('Annualised volatility',f'{kpi["volatility"]:.2f}%'),('Worst drawdown',f'{kpi["drawdown"]:.2f}%')])
table=stocks[['ticker','sector','investment_cad','final_value_cad','total_return','cagr','volatility','sharpe','drawdown']].sort_values('total_return',ascending=False)
table.columns=['Ticker','Sector','Invested CAD','Ending CAD','Total return %','CAGR %','Volatility %','Sharpe','Max drawdown %']
table_html=table.to_html(index=False,float_format=lambda n:f'{n:,.2f}',classes='data-table',border=0)
sector_table=sector.copy()
sector_table['return_pct']=(sector_table.final_value_cad/sector_table.investment_cad-1)*100
sector_table['cagr_pct']=((sector_table.final_value_cad/sector_table.investment_cad)**(1/years)-1)*100
sector_table=sector_table.sort_values('return_pct',ascending=False).reset_index()
sector_table.columns=['Sector','Invested CAD','Ending CAD','Profit CAD','Total return %','CAGR %']
sector_html=sector_table.to_html(index=False,float_format=lambda n:f'{n:,.2f}',classes='data-table',border=0)
html=template.replace('/*PLOTLY*/',get_plotlyjs()).replace('/*DATA*/',json.dumps(payload,separators=(',',':'))).replace('<!--CARDS-->',cards).replace('<!--TABLE-->',table_html).replace('<!--SECTOR_TABLE-->',sector_html)
(OUT/'stock_portfolio_dashboard.html').write_text('\n'.join(line.rstrip() for line in html.splitlines()) + '\n')
checks={'source_commit':'ab14073f1ac3f6d3b1e61cfbb6ae2a726047f610','start':daily.date.iloc[0],'end':daily.date.iloc[-1],
    'trading_days':len(daily),'holdings':tickers,'kpis':kpi,
    'max_sql_csv_difference_cad':float(np.max(np.abs(total.values-sql_daily.portfolio_value.values))),
    'status':'passed','notes':'DB share counts rounded to 4 decimals; dashboard uses exact investment / first close.'}
(OUT/'validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
