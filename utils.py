import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
from openbb_terminal.sdk import openbb

from fredapi import Fred

fred = Fred(api_key='6a118a0ce0c76a5a1d1ad052a65162d6')


def big_number_formatter(x):
    """The two args are the value and tick position."""
    formatter_thresholds = 1_000_000_000
    if x < formatter_thresholds:
        return '${:1.1f}M'.format(x * 1e-6)
    else:
        return '${:1.1f}B'.format(x * 1e-9)


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
    begining_close = col.iloc[-30]

    last_day_return = (latest_price / previous_close - 1) * 100
    seven_day_return = (latest_price / week_ago_close - 1) * 100
    thirty_day_return = (latest_price / begining_close - 1) * 100

    return [latest_price, last_day_return, seven_day_return, thirty_day_return]


def compute_yf_data_returns(yf_data):
    """
    Compute returns for a given column
    :param yf_data: pandas dataframe
    :return: pandas dataframe
    """
    col_names = ['NASDAQ', 'S&P 500', 'Dow Jones', 'FTSE (UK)', 'Nikkei (JPY)', 'ASX 200', 'Russell 3000 Growth',
                 'Russell 3000 Value', 'Russell 1000 Large-Cap', 'Russell 2000 Small-Cap', 'ARKK Innovation ETF']
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


def pull_fred_data():
    fred_data = pd.DataFrame()
    series_fred = ['DGS10', 'T10Y2Y', 'M2SL']
    series_name = ['10Y', '10Y-2Y', 'M2']
    for s_fred, s_name in zip(series_fred, series_name):
        series_tmp = fred.get_series(s_fred).fillna(method='ffill').to_frame(name=s_name)
        fred_data = fred_data.join(series_tmp, how='outer')
    return fred_data


def pull_pcr_data(start_date='2021-01-01', rolling=10):
    """
    pull put/call ratio data from openbb
    :return: pandas dataframe
    """
    pcr_data = pd.DataFrame()
    windows = [30, 60, 90]
    for w in windows:
        pcr_tmp = openbb.stocks.options.pcr('SPY', window=w, start_date=start_date)
        pcr_tmp.columns = [f'{w}-Day Volume']
        pcr_data = pcr_data.join(pcr_tmp, how='outer')
    return pcr_data.rolling(rolling).mean().dropna()


# def pull_fred_data_async(ticker_map):
#     """
#     pull data from fred asynchronously
#     :param ticker_map: dictionary of tickers
#     :return: pandas dataframe
#     """
#     tasks = [asyncio.create_task(fred_series_async(s_fred, s_name)) for s_fred, s_name in ticker_map.items()]
#     dataframes = await asyncio.gather(*tasks)
#     fred_data = pd.concat(dataframes, axis=1)
#     return fred_data


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
