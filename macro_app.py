from datetime import datetime

import streamlit as st
import yfinance as yf

import plotly.express as px
from plotly.subplots import make_subplots

from utils import big_number_formatter, highlight_percent_returns, pull_yf_data, \
    pull_fred_data, compute_yf_data_returns, pull_pcr_data, add_recession_periods, fear_greed_data, \
    fix_date_for_psycho_url

from fredapi import Fred

import pandas as pd

SYNCRACY_COLORS = ['#5218F8', '#C218F8', '#F818BE']

fred = Fred(api_key='6a118a0ce0c76a5a1d1ad052a65162d6')

# App configuration
st.set_page_config(
    page_title="The Eye of Syncracy",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# App description markdown
markdown = """<h1 style='font-family: Calibri; text-align: center;'>The Eye of <img 
src="https://images.squarespace-cdn.com/content/v1/63857484f91d71181b02f971/9943adcc-5e69-489f-b4a8-158f20fe0619
/Snycracy_WebLogo.png?format=250w" alt="logo"/></h1> <p style='font-family: Calibri; text-align: center;'><i>The Eye 
of Syncracy, a constant watchful gaze upon the crypto markets. It sees all, the rise and fall of coins, the ebb and 
flow of trading. <br> Beware its all-seeing presence, for it knows the secrets of the market, but reveals them only 
to the select few</i></p>"""

st.markdown(markdown, unsafe_allow_html=True)

# Psychological indicators and volume parameters
today = datetime.today()
ts = pd.Timestamp(str(today))
offset = pd.tseries.offsets.BusinessDay(n=1)
latest_business_day = today - offset

year = fix_date_for_psycho_url(latest_business_day.year)
day = fix_date_for_psycho_url(latest_business_day.day)
month = fix_date_for_psycho_url(latest_business_day.month)
psychological_indicators_and_volume_url = f"https://www.investors.com/wp-content/uploads/{year}/{month}/DailyPsycho_{month}{day}{year[-2:]}.pdf "

st.write('#')
st.write(f"""[Crypto Dashboard](https://syncracycapital-the-eye-of-syncracy-analytics-app-jjgobl.streamlit.app/) | 
            [Psychological Indicators and Volume]({psychological_indicators_and_volume_url})""")
st.markdown('---')

# Futures data
futures = ['ES', 'NQ', 'YM', 'NKD', 'CL', 'GC']
futures_yf_code = [f'{x}=F' for x in futures]
futures_names = ['S&P 500', 'NASDAQ 100', 'Dow Jones', 'Nikkei (JPY)', 'WTI Crude Oil', 'Gold']

st.subheader('Futures (Latest % return)')
futures_cols = st.columns(len(futures))

for i, future in enumerate(futures_names):
    future_info = yf.Ticker(futures_yf_code[i]).fast_info
    price_change_pct = (future_info["last_price"] / future_info["previous_close"] - 1) * 100
    futures_cols[i].metric(label=future, value=f'{future_info["last_price"]:.2f}', delta=f'{price_change_pct:.2f}%')

st.markdown('---')

yf_tickers_to_names_map = {'^IXIC': 'NASDAQ',
                           '^GSPC': 'S&P 500',
                           '^DJI': 'Dow Jones',
                           '^FTSE': 'FTSE (UK)',
                           '^N225': 'Nikkei (JPY)',
                           '^AXJO': 'ASX 200',
                           '^RAG': 'Russell 3000 Growth',
                           '^RAV': 'Russell 3000 Value',
                           '^RUI': 'Russell 1000 Large-Cap',
                           '^RUT': 'Russell 2000 Small-Cap',
                           'ARKK': 'ARKK Innovation ETF',
                           '^VIX': 'VIX',
                           'DX-Y.NYB': 'DXY'}

fred_tickers_to_names_map = {'DGS10': '10Y',
                             'T10Y2Y': '10Y-2Y',
                             'M2SL': 'M2'}

index_cols = ['NASDAQ', 'S&P 500', 'Dow Jones', 'FTSE (UK)', 'Nikkei (JPY)', 'ASX 200', 'Russell 3000 Growth',
              'Russell 3000 Value', 'Russell 1000 Large-Cap', 'Russell 2000 Small-Cap', 'ARKK Innovation ETF']

with st.spinner('Loading Market Data From Yahoo Finance...'):
    stock_market_data = pull_yf_data(yf_tickers_to_names_map)
    stock_market_data.index = stock_market_data.index.tz_localize(None)
    returns = compute_yf_data_returns(stock_market_data)

with st.spinner('Loading Market Data From FRED...'):
    fred_data = pull_fred_data()

with st.spinner('Loading PCR Data From Alpha Query...'):
    pcr_data = pull_pcr_data()

with st.spinner('Loading Fear & Greed Index From CNN...'):
    fear_and_greed_df = fear_greed_data()

# Format the table
df_styler_dict = {'Price': '${:,.2f}',
                  'Vol': big_number_formatter,
                  'Latest % return': '{:.2f}%',
                  '7d %': '{:.2f}%',
                  '30d %': '{:.2f}%'}

# Fear and greed index
st.subheader('Fear & Greed Index')

latest_value, category = st.columns(2)

with latest_value:
    st.metric(label='Latest Value',
              value=int(fear_and_greed_df['fear_metric'].iloc[-1]))

with category:
    st.metric(label='Category',
              value=fear_and_greed_df['rating'].iloc[-1].capitalize())

fear_and_greed_chart = st.columns(1)

with fear_and_greed_chart[0]:
    fig = px.line(fear_and_greed_df['fear_metric'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_layout(showlegend=False, xaxis_title=None)

    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=25, y1=25, yref="y")
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=75, y1=75, yref="y")

    fig.add_annotation(x=0.1, y=22, xref="paper", yref="y",
                       text="Extreme Fear", showarrow=False, font=dict(color="red"))
    fig.add_annotation(x=0.1, y=78, xref="paper", yref="y",
                       text="Extreme Greed", showarrow=False, font=dict(color="red"))
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# Indices tables
indices_cols = st.columns(2)

# Major indices table
with indices_cols[0]:
    st.subheader('Major Indices')
    st.dataframe(returns.loc[index_cols[:6]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['Latest % return', '7d %',
                                                                                           '30d %']),
                 width=1000)

with indices_cols[1]:
    st.subheader('Equity Style Indices')
    st.dataframe(returns.loc[index_cols[6:]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['Latest % return', '7d %',
                                                                                           '30d %']),
                 width=1000)

st.markdown('---')

differential_cols = st.columns(2)

with differential_cols[0]:
    st.subheader('Growth/Value Ratio')
    st.write("""Note: Growth sells off versus Value when rates are rising but then outperforms in
             a recession. The relationship will tell whether market is expecting higher rates or weaker economy - 
             inflation or hard landing""")
    latest_value = round(stock_market_data['Growth/Value Ratio'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['Growth/Value Ratio'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    fig = px.line(stock_market_data['Growth/Value Ratio'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_layout(showlegend=False, xaxis_title=None)
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=1, y1=1, yref="y")
    fig = add_recession_periods(fig, stock_market_data['Growth/Value Ratio'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with differential_cols[1]:
    st.subheader('Large-cap/Small-cap Ratio')
    st.write('Note: Small-Caps sells off relative to Large-Cap going into recession')
    st.markdown('###')  # add space
    st.markdown('###')  # add space
    latest_value = round(stock_market_data['Large-cap/Small-cap Ratio'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['Large-cap/Small-cap Ratio'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    fig = px.line(stock_market_data['Large-cap/Small-cap Ratio'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(dtick=0.1)
    fig.update_layout(showlegend=False, xaxis_title=None)
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=1, y1=1, yref="y")
    fig = add_recession_periods(fig, stock_market_data['Large-cap/Small-cap Ratio'].dropna())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# DXY, 10Y and 10Y-2Y
dxy, ten_year, ten_minus_two = st.columns(3)

with dxy:
    st.subheader('US Dollar Index')
    latest_value = round(stock_market_data['DXY'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['DXY'].dropna().index[-1].strftime('%Y-%m-%d')
    average_value = round(stock_market_data['DXY'].dropna().mean(), 2)
    min_value = round(stock_market_data['DXY'].dropna().min(), 2)
    max_value = round(stock_market_data['DXY'].dropna().max(), 2)
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    st.write(f'Average Value: {average_value}, Min value: {min_value}, Max value: {max_value}')
    fig = px.line(stock_market_data['DXY'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(tickprefix="$")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Price')
    fig = add_recession_periods(fig, stock_market_data['DXY'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with ten_year:
    st.subheader('10-Year Treasury Yield')
    latest_value = round(fred_data['10Y'].dropna().iloc[-1], 2)
    latest_date = fred_data['10Y'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}%')
    st.write('#')
    fig = px.line(fred_data['10Y'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Yield')
    fig = add_recession_periods(fig, fred_data['10Y'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with ten_minus_two:
    st.subheader('10Y - 2Y Spread')
    latest_value = round(fred_data['10Y-2Y'].dropna().iloc[-1], 2)
    latest_date = fred_data['10Y-2Y'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}%')
    st.write('#')
    fig = px.line(fred_data['10Y-2Y'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Spread')
    fig = add_recession_periods(fig, fred_data['10Y-2Y'].dropna())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

vix, put_call_ratio = st.columns(2)

with vix:
    st.subheader('Volatility Index (VIX)')
    latest_value = round(stock_market_data['VIX'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['VIX'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    st.write('#')
    fig = px.line(stock_market_data['VIX'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Spread')
    fig = add_recession_periods(fig, stock_market_data['VIX'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with put_call_ratio:
    st.subheader('Put/Call Ratio (Volume)')
    latest_value_10_day = round(pcr_data['10-Day Volume'].dropna().iloc[-1], 2)
    latest_value_30_day = round(pcr_data['30-Day Volume'].dropna().iloc[-1], 2)
    average_10_day = round(pcr_data['10-Day Volume'].dropna().tail(10).mean(), 2)
    average_30_day = round(pcr_data['30-Day Volume'].dropna().tail(10).mean(), 2)
    latest_date = pcr_data.dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date} - 10-Day: {latest_value_10_day} | 30-Day: {latest_value_30_day}')
    st.write(f'10 Day Average Values - 10-Day: {average_10_day} | 30-Day: {average_30_day}')
    fig = px.line(pcr_data, color_discrete_sequence=SYNCRACY_COLORS)
    fig.update_layout(xaxis_title=None, yaxis_title='Put/Call Ratio')
    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center"))
    fig = add_recession_periods(fig, pcr_data)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

liquidity_col = st.columns(1)
m2 = fred_data['M2'].to_frame(name='M2').join(stock_market_data['S&P 500'],
                                              how='outer').resample('D').first().dropna().pct_change(12).dropna() * 100

with liquidity_col[0]:
    st.subheader('S&P 500 vs M2 (YoY%)')
    latest_value_snp = round(m2['S&P 500'].dropna().iloc[-1], 2)
    latest_value_m2 = round(m2['M2'].dropna().iloc[-1], 2)
    latest_date = m2.dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date} - S&P 500:{latest_value_snp}% | M2:{latest_value_m2}%')

    main_fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig_snp = px.line(m2['S&P 500'])
    fig_snp.update_traces(line=dict(color="#5218fa"))
    fig_snp.update_layout(xaxis_title=None)

    fig_m2 = px.line(m2['M2'])
    fig_m2.update_traces(yaxis="y2")
    fig_m2.update_traces(line=dict(color='#C218F8'))
    fig_m2.update_layout(xaxis_title=None)

    main_fig.add_traces(fig_snp.data + fig_m2.data)  # noqa
    main_fig.update_yaxes(ticksuffix="%")
    main_fig.update_layout(legend=dict(title=None,
                                       orientation="h",
                                       y=1,
                                       yanchor="bottom",
                                       x=0.5,
                                       xanchor="center"))
    main_fig.update_yaxes(showgrid=False, showline=False, zeroline=False)
    main_fig.update_xaxes(showgrid=False, showline=False, zeroline=False)

    main_fig.layout.yaxis.title = "S&P 500 (YoY%)"
    main_fig.layout.yaxis2.title = "M2 (YoY%)"

    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='S&P 500 (YoY%)')
    main_fig = add_recession_periods(main_fig, m2)
    st.plotly_chart(main_fig, use_container_width=True, use_container_height=True)

st.markdown('---')
