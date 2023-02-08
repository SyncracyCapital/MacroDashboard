import streamlit as st
import yfinance as yf

from utils import compute_returns, big_number_formatter, highlight_percent_returns

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

st.subheader('Futures (24h %)')
futures_cols = st.columns(len(futures))

for i, future in enumerate(futures_names):
    future_info = yf.Ticker(futures_yf_code[i]).fast_info
    price_change = future_info["last_price"] - future_info["previous_close"]
    price_change_pct = (price_change / future_info["previous_close"]) * 100
    futures_cols[i].metric(label=future, value=f'{future_info["last_price"]:.2f}', delta=f'{price_change_pct:.2f}%')

st.markdown('---')

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
returns.columns = ['Price', '24hr %', '7d %', '30d %']
returns['24h Vol'] = indices_volume.iloc[-1]
returns = returns[['Price', '24h Vol', '24hr %', '7d %', '30d %']]

# Format the table
df_styler_dict = {'Primace': '${:,.2f}',
                  '24h Vol': big_number_formatter,
                  '24hr %': '{:.2f}%',
                  '7d %': '{:.2f}%',
                  '30d %': '{:.2f}%'}

# Indices tables
indices_cols = st.columns(2)

# Major indices table
with indices_cols[0]:
    st.subheader('Major Indices')
    st.dataframe(returns.loc[index_cols[:6]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['24hr %', '7d %', '30d %']),
                 width=500)

with indices_cols[1]:
    st.subheader('Equity Style Indices')
    st.dataframe(returns.loc[index_cols[6:]].style.format(df_styler_dict).applymap(highlight_percent_returns,
                                                                                   subset=['24hr %', '7d %', '30d %']),
                 width=500)

st.markdown('---')
