import asyncio
from datetime import datetime
from random import choice

import requests
import yfinance as yf
import pandas as pd
from openbb_terminal.sdk import openbb
import streamlit as st

from typing import Optional
from openbb_terminal.helper_funcs import request

from fredapi import Fred

fred = Fred(api_key='6a118a0ce0c76a5a1d1ad052a65162d6')


def get_put_call_ratio(
    symbol: str,
    window: int = 30,
    start_date: Optional[str] = None,
) -> pd.DataFrame:
    """Gets put call ratio over last time window [Source: AlphaQuery.com]

    Parameters
    ----------
    symbol: str
        Ticker symbol to look for
    window: int, optional
        Window to consider, by default 30
    start_date: Optional[str], optional
        Start date to plot  (e.g., 2021-10-01), by default last 366 days

    Returns
    -------
    pd.DataFrame
        Put call ratio

    Examples
    --------
    >>> from openbb_terminal.sdk import openbb
    >>> pcr_df = openbb.stocks.options.pcr("B")
    """

    if start_date is None:
        start_date = (datetime.now() - timedelta(days=366)).strftime("%Y-%m-%d")

    url = f"https://www.alphaquery.com/data/option-statistic-chart?ticker={symbol}\
        &perType={window}-Day&identifier=put-call-ratio-volume"

    st.write(url)

    r = request(url)
    if r.status_code != 200:
        st.write(r.status_code)
        return pd.DataFrame()

    pcr = pd.DataFrame.from_dict(r.json())
    pcr.rename(columns={"x": "Date", "value": "PCR"}, inplace=True)
    pcr.set_index("Date", inplace=True)
    pcr.index = pd.to_datetime(pcr.index).tz_localize(None)

    return pcr[pcr.index > start_date]


def big_number_formatter(x):
    """The two args are the value and tick position."""
    formatter_thresholds_billion = 1_000_000_000
    formatter_thresholds_trillion = 1_000_000_000_000

    if x < formatter_thresholds_billion:
        return '${:1.1f}M'.format(x * 1e-6)
    elif x < formatter_thresholds_trillion:
        return '${:1.1f}B'.format(x * 1e-9)
    else:
        return '${:1.1f}T'.format(x * 1e-12)


def highlight_percent_returns(cell):
    """
    Highlight negative values as red and positive values as green
    """
    if type(cell) != str and cell < 0:
        return 'color: red'
    else:
        return 'color: green'


def compute_returns(col):
    """
    Compute returns for a given column
    :param col: pandas series
    :return: pandas series
    """
    col = col.dropna()
    latest_price = col.iloc[-1]
    previous_close = col.iloc[-2]
    week_ago_close = col.iloc[-7]
    beginning_close = col.iloc[-30]

    last_day_return = (latest_price / previous_close - 1) * 100
    seven_day_return = (latest_price / week_ago_close - 1) * 100
    thirty_day_return = (latest_price / beginning_close - 1) * 100

    return [latest_price, last_day_return, seven_day_return, thirty_day_return]


def compute_yf_data_returns(yf_data, col_names):
    """
    Compute returns for a given column
    :param yf_data: pandas dataframe
    :param col_names: list of column names
    :return: pandas dataframe
    """
    window = 120
    indices_adj_close = yf_data[col_names]
    returns = indices_adj_close.apply(compute_returns, axis=0).T
    returns.columns = ['Price', 'Latest % return', '7d %', '30d %']
    returns = returns[['Price', 'Latest % return', '7d %', '30d %']]
    return returns


async def fred_series_async(series, name):
    """
    pull data from fred
    :param series: series name
    :param name: human readable name
    :return: pandas series
    """
    return fred.get_series(series).fillna(method='ffill').to_frame(name=name)


@st.cache_data(ttl=60*5, show_spinner=False)
def pull_yf_data(ticker_map):
    """
    pull data from yahoo finance
    :param ticker_map: dictionary of tickers
    :return: pandas dataframe
    """
    start_date = '1980-01-01'
    today = datetime.today()
    delta = (today - datetime.strptime(start_date, '%Y-%m-%d')).days
    stock_market_data = yf.download(tickers=list(ticker_map.keys()), period=f'{delta}d', interval='1d')['Adj Close']
    stock_market_data.columns = [ticker_map[ticker] for ticker in list(stock_market_data.columns)]

    # Compute Differentials
    stock_market_data['Growth/Value Ratio'] = stock_market_data['Russell 3000 Growth'] / stock_market_data[
        'Russell 3000 Value']
    stock_market_data['Large-cap/Small-cap Ratio'] = stock_market_data['Russell 1000 Large-Cap'] / stock_market_data[
        'Russell 2000 Small-Cap']
    return stock_market_data


@st.cache_data(ttl=60*5, show_spinner=False)
def pull_fred_data():
    fred_data = pd.DataFrame()
    series_fred = ['DGS10', 'T10Y2Y', 'M2SL']
    series_name = ['10Y', '10Y-2Y', 'M2']
    for s_fred, s_name in zip(series_fred, series_name):
        series_tmp = fred.get_series(s_fred).fillna(method='ffill').to_frame(name=s_name)
        fred_data = fred_data.join(series_tmp, how='outer')
    return fred_data


@st.cache_data(ttl=60*5, show_spinner=False)
def liquidity_condition_index():
    """
    Compute liquidity condition index
    :return: pandas series
    """
    fed_balance_sheet = fred.get_series('WALCL').to_frame(name='FedBal') * 1_000_000  # scale to trillions
    rrp_balance = fred.get_series('RRPONTSYD').to_frame(name='RRP') * 1_000_000_000  # scale to trillions
    tga = fred.get_series('WTREGEN').to_frame(name='TGA') * 1_000_000_000  # scale to trillions

    usd_liquidity_index = fed_balance_sheet.join(rrp_balance, how='outer')
    usd_liquidity_index = usd_liquidity_index.join(tga, how='outer').ffill().dropna()
    usd_liquidity_index['USD Liquidity Index'] = usd_liquidity_index['FedBal'] - usd_liquidity_index['RRP'] - \
                                                 usd_liquidity_index['TGA']

    return usd_liquidity_index


def pull_pcr_data(start_date='2019-01-01'):
    """
    pull put/call ratio data from openbb
    :return: pandas dataframe
    """
    pcr_data = pd.DataFrame()
    windows = [10]
    for w in windows:
        pcr_tmp = get_put_call_ratio('SPY', window=w, start_date=start_date)
        st.dataframe(pcr_tmp)
        pcr_tmp.columns = [f'{w}-Day Volume']
        pcr_data = pcr_data.join(pcr_tmp, how='outer')
    return pcr_data.dropna()


async def get_fast_info(future_ticker):
    """
    Get fast info for a given ticker
    :param future_ticker: ticker
    :return: lazy dictionary
    """
    ticker = yf.Ticker(future_ticker)
    return ticker.fast_info


async def compute_pct_moves(future_tickers):
    """
    Compute percent moves for a given ticker
    :param future_tickers: dictionary of tickers
    :return: list of percent moves
    """
    fast_info_list = []
    tasks = []
    for future_ticker in future_tickers.keys():
        task = asyncio.create_task(get_fast_info(future_ticker))
        tasks.append(task)
        fast_info_list.append({})

    # We use asyncio.as_completed to iterate over the tasks as they complete,
    # since we don't know the order in which they will complete.
    for i, coro in enumerate(asyncio.as_completed(tasks)):
        fast_info = await coro
        fast_info_list[i] = fast_info

    pct_changes = []
    for fast_info in fast_info_list:
        price_change_pct = (fast_info["last_price"] / fast_info["previous_close"] - 1) * 100
        pct_changes.append(price_change_pct)
    return list(zip(pct_changes, list(future_tickers.values())))


def add_recession_periods(fig, data):
    """
    Add recession periods to a plotly figure
    :param fig: plotly figure
    :param data: pandas dataframe
    :return: plotly figure
    """
    # Add recession periods
    recessions = [['1960-04-01', '1961-02-01'],
                  ['1969-12-01', '1970-11-01'],
                  ['1973-11-01', '1975-03-01'],
                  ['1980-01-01', '1980-07-01'],
                  ['1981-07-01', '1982-11-01'],
                  ['1990-07-01', '1991-03-01'],
                  ['2001-03-01', '2001-11-01'],
                  ['2007-12-01', '2009-06-01'],
                  ['2020-02-01', '2020-04-01']]
    data_start_date = data.index[0]
    for recession in recessions:
        if datetime.strptime(recession[0], '%Y-%m-%d') < data_start_date:
            continue
        else:
            fig.add_vrect(
                x0=recession[0],
                x1=recession[1],
                fillcolor="#FB8BD7",
                opacity=0.4,
                layer="below",
                line_width=0,
            )
    return fig


@st.cache_data(ttl=60*5, show_spinner=False)
def fear_greed_data() -> pd.DataFrame:
    """
    This is very informational
    Takes in url and start date, write something something
    """
    BASE_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    START_DATE = '2021-01-01'

    USER_AGENTS = [
        # Chrome on Windows 10
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        # Firefox on Macos
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.4; rv:100.0) Gecko/20100101 Firefox/100.0",
    ]
    user_agent = choice(USER_AGENTS)
    headers = {
        "User-Agent": user_agent,
    }
    r = requests.get("{}/{}".format(BASE_URL, START_DATE), headers=headers)
    data = r.json()

    fear_greed_index = pd.DataFrame(data['fear_and_greed_historical']['data'])
    fear_greed_index['x'] = pd.to_datetime(fear_greed_index['x'] // 1000, unit='s').dt.strftime('%Y-%m-%d')
    fear_greed_index = fear_greed_index.rename(columns={'x': 'date', 'y': 'fear_metric'})

    fear_greed_index.set_index('date', inplace=True)

    return fear_greed_index.drop_duplicates()


def fix_date_for_psycho_url(number):
    """
    Fix date for psycho url
    :param number: int
    :return: str
    """
    if number < 10:
        return f'0{number}'
    return str(number)


def compute_rolling_averages(data, col_name, averages):
    """
    Compute rolling averages
    :param data: pandas dataframe
    :param col_name: column name
    :param averages: list of averages
    :return: pandas dataframe
    """
    if not isinstance(data, pd.DataFrame):
        data = data.to_frame(name=col_name)

    for average in averages:
        data[f'{average}-Day MA'] = data[col_name].rolling(average).mean()
    return data


def rsi_calculation(df, period, ema=True):
    """
    Calculate RSI
    :param df: pandas dataframe
    :param period: int
    :param ema: bool
    :return: pandas dataframe
    """
    close_delta = df.diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    # Calculate RSI using EMA or SMA (default is EMA)
    if ema:
        # Use exponential moving average
        ma_up = up.ewm(com=period - 1, adjust=True, min_periods=period).mean()
        ma_down = down.ewm(com=period - 1, adjust=True, min_periods=period).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=period, adjust=False).mean()
        ma_down = down.rolling(window=period, adjust=False).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi


def compute_rsi(data, col_name, periods, ema=True):
    """
    Compute RSI
    :param data: pandas dataframe
    :param col_name: column name
    :param periods: list of periods
    :param ema: bool
    :return: pandas dataframe
    """
    if not isinstance(data, pd.DataFrame):
        data = data.to_frame(name=col_name)

    for period in periods:
        data[f'{period}-Day RSI'] = rsi_calculation(data[col_name], period, ema)
    return data[[f'{period}-Day RSI' for period in periods]]
