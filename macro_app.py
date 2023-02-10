from datetime import datetime

import streamlit as st
import yfinance as yf

import plotly.express as px

from utils import compute_returns, big_number_formatter, highlight_percent_returns

from fredapi import Fred

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

st.markdown('---')

# Futures data
futures = ['ES', 'NQ', 'YM', 'NKD', 'CL', 'GC']
futures_yf_code = [f'{x}=F' for x in futures]
futures_names = ['S&P 500', 'NASDAQ 100', 'Dow Jones', 'Nikkei (JPY)', 'WTI Crude Oil', 'Gold']

st.subheader('Futures (Latest %)')
futures_cols = st.columns(len(futures))

for i, future in enumerate(futures_names):
    future_info = yf.Ticker(futures_yf_code[i]).fast_info
    price_change_pct = (future_info["last_price"] / future_info["previous_close"] - 1) * 100
    futures_cols[i].metric(label=future, value=f'{future_info["last_price"]:.2f}', delta=f'{price_change_pct:.2f}%')

st.markdown('---')

st.spinner('Loading data...')
# Equity indices data
indices_tickers = ['^IXIC', '^GSPC', '^DJI', '^FTSE', '^N225', '^AXJO', '^RAG', '^RAV', '^RUI', '^RUT', 'ARKK']
index_cols = ['NASDAQ', 'S&P 500', 'Dow Jones', 'FTSE (UK)', 'Nikkei (JPY)', 'ASX 200', 'Russell 3000 Growth',
              'Russell 3000 Value',
              'Russell 1000 Large-Cap', 'Russell 2000 Small-Cap', 'ARKK Innovation ETF']
indices_df = yf.download(tickers=indices_tickers, period="30d", interval="1d")
indices_adj_close = indices_df['Adj Close'][indices_tickers]
indices_volume = indices_df['Volume'][indices_tickers].fillna(method='ffill')
indices_adj_close.columns = index_cols
indices_volume.columns = index_cols

returns = indices_adj_close.apply(compute_returns, axis=0).T
returns.columns = ['Price', 'Latest %', '7d %', '30d %']
returns['Vol'] = indices_volume.iloc[-1]
returns = returns[['Price', 'Latest %', '24hr %', '7d %', '30d %']]

# Equity Style Data
stock_market_start_date = '1980-12-31'
stock_market_end_date = datetime.today().strftime('%Y-%m-%d')
tickers_to_names_map = {'^RAG': 'Russell 3000 Growth',
                        '^RAV': 'Russell 3000 Value',
                        '^RUI': 'Russell 1000 Large-Cap',
                        '^RUT': 'Russell 2000 Small-Cap'}
stock_market_data = yf.download(tickers=list(tickers_to_names_map.keys()), start=stock_market_start_date,
                                end=stock_market_end_date)['Close']
stock_market_data.columns = [tickers_to_names_map[ticker] for ticker in list(stock_market_data.columns)]

# growth/value ratio
stock_market_data['Growth/Value Ratio'] = stock_market_data['Russell 3000 Growth'] / stock_market_data[
    'Russell 3000 Value']

# large-cap/small-cap ratio
stock_market_data['Large-cap/Small-cap Ratio'] = stock_market_data['Russell 1000 Large-Cap'] / stock_market_data[
    'Russell 2000 Small-Cap']

# DXY, 10Y, 10Y-2Y
dxy_df = yf.download(tickers='DX-Y.NYB', start=stock_market_start_date, end=stock_market_end_date)['Close']
ten_year_df = fred.get_series('DGS10').fillna(method='ffill')
ten_minus_two_df = fred.get_series('T10Y2Y').fillna(method='ffill')

# Format the table
df_styler_dict = {'Price': '${:,.2f}',
                  'Vol': big_number_formatter,
                  'Latest %': '{:.2f}%',
                  '7d %': '{:.2f}%',
                  '30d %': '{:.2f}%'}

# Indices tables
indices_cols = st.columns(2)

# Major indices table
with indices_cols[0]:
    st.subheader('Major Indices')
    st.dataframe(returns.loc[index_cols[:6]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['24hr %', '7d %', '30d %']),
                 width=1000)

with indices_cols[1]:
    st.subheader('Equity Style Indices')
    st.dataframe(returns.loc[index_cols[6:]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['24hr %', '7d %', '30d %']),
                 width=1000)

st.markdown('---')

differential_cols = st.columns(2)

with differential_cols[0]:
    st.subheader('Growth/Value Ratio')
    st.write("""Note: Growth sells off versus Value when rates are rising but then outperforms in
             a recession. The relationship will tell whether market is expecting higher rates or weaker economy - 
             inflation or hard landing""")
    fig = px.line(stock_market_data['Growth/Value Ratio'].dropna())
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_layout(showlegend=False, xaxis_title=None)
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=1, y1=1, yref="y")
    st.plotly_chart(fig, use_container_width=True)

with differential_cols[1]:
    st.subheader('Large-cap/Small-cap Ratio')
    fig = px.line(stock_market_data['Large-cap/Small-cap Ratio'].dropna())
    st.write('Note: Small-Caps sells off relative to Large-Cap going into recession')
    st.markdown('###')  # add space
    st.markdown('###')  # add space
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(dtick=0.1)
    fig.update_layout(showlegend=False, xaxis_title=None)
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=1, y1=1, yref="y")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# DXY, 10Y and 10Y-2Y
dxy, ten_year, ten_minus_two = st.columns(3)

with dxy:
    st.subheader('US Dollar Index')
    fig = px.line(dxy_df)
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(tickprefix="$")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Price')
    st.plotly_chart(fig, use_container_width=True)

with ten_year:
    st.subheader('10-Year Treasury Constant Maturity')
    fig = px.line(ten_year_df)
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Yield')
    st.plotly_chart(fig, use_container_width=True)

with ten_minus_two:
    st.subheader('10-Year Minus 2-Year Spread')
    fig = px.line(ten_minus_two_df)
    fig.update_traces(line=dict(color="#5218fa"))
    fig.update_yaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title='Spread')
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')
