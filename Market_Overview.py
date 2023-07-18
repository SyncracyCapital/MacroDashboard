from datetime import datetime

import streamlit as st
import yfinance as yf

import plotly.express as px
from plotly.subplots import make_subplots


from utils import big_number_formatter, highlight_percent_returns, pull_yf_data, \
    pull_fred_data, compute_yf_data_returns, pull_pcr_data, add_recession_periods, fear_greed_data, \
    fix_date_for_psycho_url, liquidity_condition_index

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
st.write(f"""[Crypto Dashboard](https://syncracycapital-the-eye-of-syncracy-analytics-app-vyu0j7.streamlit.app/) |
            [Portfolio Dashboard](https://syncracycapital-portfolioanalytics-portfolio-9twh53.streamlit.app/) | 
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
                           '^HSI': 'Hang Seng (HKD)',
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

index_cols = ['NASDAQ', 'S&P 500', 'Dow Jones', 'FTSE (UK)', 'Nikkei (JPY)', 'ASX 200', 'Hang Seng (HKD)', 'DXY',
              '10Y', 'VIX', 'Russell 3000 Growth', 'Russell 3000 Value', 'Russell 1000 Large-Cap',
              'Russell 2000 Small-Cap', 'ARKK Innovation ETF']


with st.spinner('Loading Market Data From Yahoo Finance...'):
    stock_market_data = pull_yf_data(yf_tickers_to_names_map)
    stock_market_data.index = stock_market_data.index.tz_localize(None)

with st.spinner('Loading Market Data From FRED...'):
    fred_data = pull_fred_data()
    liquidity_index_df = liquidity_condition_index()

# with st.spinner('Loading PCR Data From Alpha Query...'):
#     pcr_data = pull_pcr_data()

with st.spinner('Loading Fear & Greed Index From CNN...'):
    fear_and_greed_df = fear_greed_data()

stock_market_data = stock_market_data.merge(fred_data, how='left', left_index=True, right_index=True)
returns = compute_yf_data_returns(stock_market_data, index_cols)

# Format the table
df_styler_dict = {'Price': '${:,.2f}',
                  'Vol': big_number_formatter,
                  'Latest % return': '{:.2f}%',
                  '7d %': '{:.2f}%',
                  '30d %': '{:.2f}%'}

# Indices tables
indices_cols = st.columns(2)

# Date range for zooming in on the indices chart
zoom_in_date_start = '2020-01-01'
zoom_in_date_end = datetime.today().strftime('%Y-%m-%d')

# Major indices table
with indices_cols[0]:
    st.subheader('Major Indices')
    st.dataframe(returns.loc[index_cols[:8]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['Latest % return',
                                                                                           '7d %',
                                                                                           '30d %']),
                 width=1000)

with indices_cols[1]:
    st.subheader('Equity Style Indices')
    st.dataframe(returns.loc[index_cols[10:]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                    subset=['Latest % return',
                                                                                            '7d %',
                                                                                            '30d %']),
                 width=1000)

index_cols_below = st.columns(2)
with index_cols_below[0]:
    df_styler_dict = {'Price': '{:,.2f}',
                      'Vol': big_number_formatter,
                      'Latest % return': '{:.2f}%',
                      '7d %': '{:.2f}%',
                      '30d %': '{:.2f}%'}
    st.subheader('Economic Indicators')
    st.dataframe(returns.loc[index_cols[8:10]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                     subset=['Latest % return',
                                                                                             '7d %',
                                                                                             '30d %']),
                 width=1000)

st.markdown('---')

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

    data_subset = stock_market_data['Growth/Value Ratio'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])

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

    data_subset = stock_market_data['Large-cap/Small-cap Ratio'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
    fig = add_recession_periods(fig, stock_market_data['Large-cap/Small-cap Ratio'].dropna())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# DXY, 10Y and 10Y-2Y
ten_year, ten_minus_two = st.columns(2)

with ten_year:
    st.subheader('10-Year Treasury Yield')
    latest_value = round(fred_data['10Y'].dropna().iloc[-1], 2)
    latest_date = fred_data['10Y'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}%')
    fig = px.line(fred_data['10Y'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Yield')

    data_subset = fred_data['10Y'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
    fig = add_recession_periods(fig, fred_data['10Y'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with ten_minus_two:
    st.subheader('10Y - 2Y Spread')
    latest_value = round(fred_data['10Y-2Y'].dropna().iloc[-1], 2)
    latest_date = fred_data['10Y-2Y'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}%')
    fig = px.line(fred_data['10Y-2Y'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Spread')

    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y")

    data_subset = fred_data['10Y-2Y'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
    fig = add_recession_periods(fig, fred_data['10Y-2Y'].dropna())
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# put_call_ratio = st.columns(1)

# with put_call_ratio[0]:
#     st.subheader('Put/Call Ratio (Volume)')
#     latest_value_10_day = round(pcr_data['10-Day Volume'].dropna().iloc[-1], 2)
#     average_10_day = round(pcr_data['10-Day Volume'].dropna().tail(10).mean(), 2)
#     latest_date = pcr_data.dropna().index[-1].strftime('%Y-%m-%d')
#     st.write(f'Latest value as of {latest_date} - 10-Day: {latest_value_10_day}')
#     st.write(f'10 Day Average Values - 10-Day: {average_10_day}')
#     fig = px.line(pcr_data, color_discrete_sequence=SYNCRACY_COLORS)
#     fig.update_layout(xaxis_title=None, yaxis_title='Put/Call Ratio')
#     fig.update_layout(legend=dict(title=None,
#                                   orientation="h",
#                                   y=1,
#                                   yanchor="bottom",
#                                   x=0.5,
#                                   xanchor="center"))

#     data_subset = pcr_data.loc[zoom_in_date_start:zoom_in_date_end]
#     fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
#     fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
#     fig = add_recession_periods(fig, pcr_data)
#     st.plotly_chart(fig, use_container_width=True)

# st.markdown('---')

liquidity_col = st.columns(1)
m2 = fred_data['M2'].to_frame(name='M2').join(stock_market_data['S&P 500'],
                                              how='outer').resample('D').first().dropna().pct_change(
    12).dropna() * 100

with liquidity_col[0]:
    st.subheader('S&P 500 vs M2 (YoY%)')
    latest_value_snp = round(m2['S&P 500'].dropna().iloc[-1], 2)
    latest_value_m2 = round(m2['M2'].dropna().iloc[-1], 2)
    latest_date = m2.dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date} - S&P 500: {latest_value_snp}% | M2: {latest_value_m2}%')

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

liquidity_index = st.columns(1)

liquidity_index_df_with_snp = liquidity_index_df.join(stock_market_data['S&P 500'], how='outer').ffill().dropna()

with liquidity_index[0]:
    st.subheader('Liquidity Conditions Index')
    latest_value_liquidity_index = round(liquidity_index_df_with_snp['USD Liquidity Index'].iloc[-1], 2)
    latest_value_snp = round(liquidity_index_df_with_snp['S&P 500'].iloc[-1], 2)
    latest_date = liquidity_index_df_with_snp.index[-1].strftime('%Y-%m-%d')
    st.write(f"""Latest value as of {latest_date}
    S&P 500: ${latest_value_snp} | USD Liquidity Index: {round(latest_value_liquidity_index * 1e-12, 1)}T""")

    main_fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig_snp = px.line(liquidity_index_df_with_snp['S&P 500'])
    fig_snp.update_traces(line=dict(color="#5218fa"))
    fig_snp.update_layout(xaxis_title=None)
    fig_snp.update_yaxes(tickprefix="$")

    fig_liquidity_index = px.line(liquidity_index_df['USD Liquidity Index'])
    fig_liquidity_index.update_traces(yaxis="y2")
    fig_liquidity_index.update_traces(line=dict(color='#C218F8'))
    fig_liquidity_index.update_layout(xaxis_title=None)

    main_fig.add_traces(fig_snp.data + fig_liquidity_index.data)  # noqa
    main_fig.update_layout(legend=dict(title=None,
                                       orientation="h",
                                       y=1,
                                       yanchor="bottom",
                                       x=0.5,
                                       xanchor="center"))
    main_fig.update_yaxes(showgrid=False, showline=False, zeroline=False)
    main_fig.update_xaxes(showgrid=False, showline=False, zeroline=False)

    main_fig.layout.yaxis.title = "S&P 500"
    main_fig.layout.yaxis2.title = "USD Liquidity Index"

    data_subset = liquidity_index_df.loc[zoom_in_date_start:zoom_in_date_end]
    main_fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])

    main_fig.update_yaxes(tickprefix="$")
    main_fig = add_recession_periods(main_fig, liquidity_index_df)
    st.plotly_chart(main_fig, use_container_width=True, use_container_height=True)

st.markdown('---')
