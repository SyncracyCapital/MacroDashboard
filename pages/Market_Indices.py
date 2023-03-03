from datetime import datetime

import streamlit as st

from Market_Overview import yf_tickers_to_names_map
from utils import pull_yf_data, add_recession_periods, compute_rolling_averages

import plotly.express as px

SYNCRACY_COLORS = ['#5218F8', '#BE18F0', '#F018B6',
                   '#F0184A', '#F05218', '#F0BE18']

with st.spinner('Loading Market Data From Yahoo Finance...'):
    stock_market_data = pull_yf_data(yf_tickers_to_names_map)
    stock_market_data.index = stock_market_data.index.tz_localize(None)

# Date range for zooming in on the indices chart
zoom_in_date_start = '2020-01-01'
zoom_in_date_end = datetime.today().strftime('%Y-%m-%d')

st.title('Market Indices')

snp_chart, nasdaq_chart = st.columns(2)

with snp_chart:
    st.subheader('S&P 500')
    latest_value = round(stock_market_data['S&P 500'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['S&P 500'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    data_with_moving_averages = compute_rolling_averages(stock_market_data['S&P 500'].dropna(),
                                                         col_name='S&P 500', averages=[7, 25, 100])

    fig = px.line(data_with_moving_averages, color_discrete_sequence=SYNCRACY_COLORS)

    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center"))

    fig.update_layout(xaxis_title=None, yaxis_title='S&P 500')
    fig.update_yaxes(tickprefix="$")

    data_subset = stock_market_data['S&P 500'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])

    fig = add_recession_periods(fig, stock_market_data['S&P 500'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with nasdaq_chart:
    st.subheader('NASDAQ')
    latest_value = round(stock_market_data['NASDAQ'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['NASDAQ'].dropna().index[-1].strftime('%Y-%m-%d')
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    data_with_moving_averages = compute_rolling_averages(stock_market_data['NASDAQ'].dropna(),
                                                         col_name='NASDAQ', averages=[7, 25, 100])
    fig = px.line(data_with_moving_averages, color_discrete_sequence=SYNCRACY_COLORS)
    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center"))

    fig.update_layout(xaxis_title=None, yaxis_title='NASDAQ')
    fig.update_yaxes(tickprefix="$")

    data_subset = stock_market_data['NASDAQ'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
    fig = add_recession_periods(fig, stock_market_data['NASDAQ'].dropna())
    st.plotly_chart(fig, use_container_width=True)

vix, dxy = st.columns(2)

with vix:
    st.subheader('Volatility Index (VIX)')
    latest_value = round(stock_market_data['VIX'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['VIX'].dropna().index[-1].strftime('%Y-%m-%d')
    average_value = round(stock_market_data['VIX'].dropna().mean(), 2)
    min_value = round(stock_market_data['VIX'].dropna().min(), 2)
    max_value = round(stock_market_data['VIX'].dropna().max(), 2)
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    st.write(f'Average Value: {average_value}, Min value: {min_value}, Max value: {max_value}')

    data_with_moving_averages = compute_rolling_averages(stock_market_data['VIX'].dropna(),
                                                         col_name='VIX', averages=[7, 25, 100])

    fig = px.line(data_with_moving_averages, color_discrete_sequence=SYNCRACY_COLORS)

    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center"))

    fig.update_layout(xaxis_title=None, yaxis_title='Spread')

    data_subset = stock_market_data['VIX'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
    fig = add_recession_periods(fig, stock_market_data['VIX'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with dxy:
    st.subheader('US Dollar Index')
    latest_value = round(stock_market_data['DXY'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['DXY'].dropna().index[-1].strftime('%Y-%m-%d')
    average_value = round(stock_market_data['DXY'].dropna().mean(), 2)
    min_value = round(stock_market_data['DXY'].dropna().min(), 2)
    max_value = round(stock_market_data['DXY'].dropna().max(), 2)
    st.write(f'Latest value as of {latest_date}: {latest_value}')
    st.write(f'Average Value: {average_value}, Min value: {min_value}, Max value: {max_value}')

    data_with_moving_averages = compute_rolling_averages(stock_market_data['DXY'].dropna(),
                                                         col_name='DXY', averages=[7, 25, 100])
    fig = px.line(data_with_moving_averages, color_discrete_sequence=SYNCRACY_COLORS)

    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center"))

    fig.update_yaxes(tickprefix="$")
    fig.update_layout(xaxis_title=None, yaxis_title='Price')

    data_subset = stock_market_data['DXY'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])
    fig.update_yaxes(range=[data_subset.min(), data_subset.max()])
    fig = add_recession_periods(fig, stock_market_data['DXY'].dropna())
    st.plotly_chart(fig, use_container_width=True)
