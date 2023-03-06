from datetime import datetime

import streamlit as st

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from Market_Overview import yf_tickers_to_names_map
from utils import pull_yf_data, add_recession_periods, compute_rolling_averages, compute_rsi

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

    # Compute moving averages and RSI
    data_with_moving_averages = compute_rolling_averages(stock_market_data['S&P 500'].dropna(),
                                                         col_name='S&P 500', averages=[7, 25, 100])

    data_with_rsi = compute_rsi(data_with_moving_averages['S&P 500'], col_name='S&P 500',
                                periods=[7, 30])

    latest_value = round(stock_market_data['S&P 500'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['S&P 500'].dropna().index[-1].strftime('%Y-%m-%d')

    latest_rsi_values = data_with_rsi.iloc[-1].round(2).to_dict()

    st.write(f'Latest value as of {latest_date}: ${latest_value}')
    st.write(f'Latest RSI values - 7-day: {latest_rsi_values["7-Day RSI"]} 30-day: {latest_rsi_values["30-Day RSI"]}')
    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4],
                        vertical_spacing=0.05)

    # Add traces to top subplot (moving averages)
    color_subset_top_subplot = SYNCRACY_COLORS[:len(data_with_moving_averages.columns)]
    for i, col in enumerate(data_with_moving_averages.columns):
        fig.add_trace(go.Scatter(x=data_with_moving_averages.index,
                                 y=data_with_moving_averages[col],
                                 name=col,
                                 marker_color=color_subset_top_subplot[i]),  # noqa
                      row=1, col=1)

    # Add traces to bottom subplot (RSI)
    color_subset_bottom_subplot = SYNCRACY_COLORS[len(data_with_moving_averages.columns):]
    for i, col in enumerate(data_with_rsi.columns):
        fig.add_trace(go.Scatter(x=data_with_rsi.index,
                                 y=data_with_rsi[col],
                                 name=col,
                                 marker_color=color_subset_bottom_subplot[i]),  # noqa
                      row=2, col=1)

    # Add overbought/oversold lines to RSI subplot
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=30, y1=30, yref="y2")

    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=70, y1=70, yref="y2")

    # Update initial ranges for subplots
    # Update default x-axis range for both subplots
    data_subset = stock_market_data['S&P 500'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])

    # Update y-axis range for top subplot
    fig.update_layout(yaxis1=dict(range=[data_subset.min(), data_subset.max()]),
                      yaxis2=dict(range=[0, 100]))

    # Update legend
    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center",
                                  entrywidth=100))

    # Update margins around the plot to use
    # more of the available space in st.container
    fig.update_layout(
        margin=dict(t=10, b=10)
    )

    # Update subplots y-axis titles
    fig.update_layout(xaxis_title=None, yaxis1_title='S&P 500', yaxis2_title='RSI (7, 30)')

    # Update top subplot y-axis tickprefix
    fig.update_layout(yaxis1_tickprefix="$")

    # Update colors
    fig.update_layout(coloraxis=dict(colorscale=SYNCRACY_COLORS))

    fig = add_recession_periods(fig, stock_market_data['S&P 500'].dropna())
    st.plotly_chart(fig, use_container_width=True)

with nasdaq_chart:
    st.subheader('NASDAQ')

    # Compute moving averages and RSI
    data_with_moving_averages = compute_rolling_averages(stock_market_data['NASDAQ'].dropna(),
                                                         col_name='NASDAQ', averages=[7, 25, 100])

    data_with_rsi = compute_rsi(data_with_moving_averages['NASDAQ'], col_name='NASDAQ',
                                periods=[7, 30])

    latest_value = round(stock_market_data['NASDAQ'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['NASDAQ'].dropna().index[-1].strftime('%Y-%m-%d')

    latest_rsi_values = data_with_rsi.iloc[-1].round(2).to_dict()

    st.write(f'Latest value as of {latest_date}: ${latest_value}')
    st.write(f'Latest RSI values - 7-day: {latest_rsi_values["7-Day RSI"]} 30-day: {latest_rsi_values["30-Day RSI"]}')

    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4],
                        vertical_spacing=0.05)

    # Add traces to top subplot (moving averages)
    color_subset_top_subplot = SYNCRACY_COLORS[:len(data_with_moving_averages.columns)]
    for i, col in enumerate(data_with_moving_averages.columns):
        fig.add_trace(go.Scatter(x=data_with_moving_averages.index,
                                 y=data_with_moving_averages[col],
                                 name=col,
                                 marker_color=color_subset_top_subplot[i]),  # noqa
                      row=1, col=1)

    # Add traces to bottom subplot (RSI)
    color_subset_bottom_subplot = SYNCRACY_COLORS[len(data_with_moving_averages.columns):]
    for i, col in enumerate(data_with_rsi.columns):
        fig.add_trace(go.Scatter(x=data_with_rsi.index,
                                 y=data_with_rsi[col],
                                 name=col,
                                 marker_color=color_subset_bottom_subplot[i]),  # noqa
                      row=2, col=1)

    # Add overbought/oversold lines to RSI subplot
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=30, y1=30, yref="y2")

    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=70, y1=70, yref="y2")

    # Update initial ranges for subplots
    # Update default x-axis range for both subplots
    data_subset = stock_market_data['NASDAQ'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])

    # Update y-axis range for top subplot
    fig.update_layout(yaxis1=dict(range=[data_subset.min(), data_subset.max()]),
                      yaxis2=dict(range=[0, 100]))

    # Update legend
    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center",
                                  entrywidth=100))

    # Update margins around the plot to use
    # more of the available space in st.container
    fig.update_layout(
        margin=dict(t=10, b=10)
    )

    # Update subplots y-axis titles
    fig.update_layout(xaxis_title=None, yaxis1_title='NASDAQ', yaxis2_title='RSI (7, 30)')

    # Update top subplot y-axis tickprefix
    fig.update_layout(yaxis1_tickprefix="$")

    # Update colors
    fig.update_layout(coloraxis=dict(colorscale=SYNCRACY_COLORS))

    fig = add_recession_periods(fig, stock_market_data['NASDAQ'].dropna())

    st.plotly_chart(fig, use_container_width=True)

# Create some space between the charts
st.markdown('#')

vix, dxy = st.columns(2)

with vix:
    st.subheader('Volatility Index (VIX)')

    # Compute moving averages and RSI
    data_with_moving_averages = compute_rolling_averages(stock_market_data['VIX'].dropna(),
                                                         col_name='VIX', averages=[7, 25, 100])

    data_with_rsi = compute_rsi(data_with_moving_averages['VIX'], col_name='VIX',
                                periods=[7, 30])

    latest_value = round(stock_market_data['VIX'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['VIX'].dropna().index[-1].strftime('%Y-%m-%d')
    average_value = round(stock_market_data['VIX'].dropna().mean(), 2)
    min_value = round(stock_market_data['VIX'].dropna().min(), 2)
    max_value = round(stock_market_data['VIX'].dropna().max(), 2)

    latest_rsi_values = data_with_rsi.iloc[-1].round(2).to_dict()

    st.write(f'Latest value as of {latest_date}: {latest_value}')
    st.write(f'Average Value: {average_value}, Min value: {min_value}, Max value: {max_value}')
    st.write(f'Latest RSI values - 7-day: {latest_rsi_values["7-Day RSI"]} 30-day: {latest_rsi_values["30-Day RSI"]}')

    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4],
                        vertical_spacing=0.05)

    # Add traces to top subplot (moving averages)
    color_subset_top_subplot = SYNCRACY_COLORS[:len(data_with_moving_averages.columns)]
    for i, col in enumerate(data_with_moving_averages.columns):
        fig.add_trace(go.Scatter(x=data_with_moving_averages.index,
                                 y=data_with_moving_averages[col],
                                 name=col,
                                 marker_color=color_subset_top_subplot[i]),  # noqa
                      row=1, col=1)

    # Add traces to bottom subplot (RSI)
    color_subset_bottom_subplot = SYNCRACY_COLORS[len(data_with_moving_averages.columns):]
    for i, col in enumerate(data_with_rsi.columns):
        fig.add_trace(go.Scatter(x=data_with_rsi.index,
                                 y=data_with_rsi[col],
                                 name=col,
                                 marker_color=color_subset_bottom_subplot[i]),  # noqa
                      row=2, col=1)

    # Add overbought/oversold lines to RSI subplot
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=30, y1=30, yref="y2")

    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=70, y1=70, yref="y2")

    # Update initial ranges for subplots
    # Update default x-axis range for both subplots
    data_subset = stock_market_data['VIX'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])

    # Update y-axis range for top subplot
    fig.update_layout(yaxis1=dict(range=[data_subset.min(), data_subset.max()]),
                      yaxis2=dict(range=[0, 100]))

    # Update legend
    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center",
                                  entrywidth=100))

    # Update margins around the plot to use
    # more of the available space in st.container
    fig.update_layout(
        margin=dict(t=10, b=10)
    )

    # Update subplots y-axis titles
    fig.update_layout(xaxis_title=None, yaxis1_title='VIX', yaxis2_title='RSI (7, 30)')

    # Update top subplot y-axis tickprefix
    fig.update_layout(yaxis1_tickprefix="$")

    # Update colors
    fig.update_layout(coloraxis=dict(colorscale=SYNCRACY_COLORS))

    fig = add_recession_periods(fig, stock_market_data['VIX'].dropna())

    st.plotly_chart(fig, use_container_width=True)

with dxy:
    st.subheader('US Dollar Index')

    # Compute moving averages and RSI
    data_with_moving_averages = compute_rolling_averages(stock_market_data['DXY'].dropna(),
                                                         col_name='DXY', averages=[7, 25, 100])

    data_with_rsi = compute_rsi(data_with_moving_averages['DXY'], col_name='DXY',
                                periods=[7, 30])

    latest_value = round(stock_market_data['DXY'].dropna().iloc[-1], 2)
    latest_date = stock_market_data['DXY'].dropna().index[-1].strftime('%Y-%m-%d')
    average_value = round(stock_market_data['DXY'].dropna().mean(), 2)
    min_value = round(stock_market_data['DXY'].dropna().min(), 2)
    max_value = round(stock_market_data['DXY'].dropna().max(), 2)

    latest_rsi_values = data_with_rsi.iloc[-1].round(2).to_dict()

    st.write(f'Latest value as of {latest_date}: ${latest_value}')
    st.write(f'Average Value: {average_value}, Min value: {min_value}, Max value: {max_value}')
    st.write(f'Latest RSI values - 7-day: {latest_rsi_values["7-Day RSI"]} 30-day: {latest_rsi_values["30-Day RSI"]}')

    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4],
                        vertical_spacing=0.05)

    # Add traces to top subplot (moving averages)
    color_subset_top_subplot = SYNCRACY_COLORS[:len(data_with_moving_averages.columns)]
    for i, col in enumerate(data_with_moving_averages.columns):
        fig.add_trace(go.Scatter(x=data_with_moving_averages.index,
                                 y=data_with_moving_averages[col],
                                 name=col,
                                 marker_color=color_subset_top_subplot[i]),  # noqa
                      row=1, col=1)

    # Add traces to bottom subplot (RSI)
    color_subset_bottom_subplot = SYNCRACY_COLORS[len(data_with_moving_averages.columns):]
    for i, col in enumerate(data_with_rsi.columns):
        fig.add_trace(go.Scatter(x=data_with_rsi.index,
                                 y=data_with_rsi[col],
                                 name=col,
                                 marker_color=color_subset_bottom_subplot[i]),  # noqa
                      row=2, col=1)

    # Add overbought/oversold lines to RSI subplot
    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=30, y1=30, yref="y2")

    fig.add_shape(type="line", line_color="red", line_width=3, opacity=1, line_dash="dot",
                  x0=0, x1=1, xref="paper", y0=70, y1=70, yref="y2")

    # Update initial ranges for subplots
    # Update default x-axis range for both subplots
    data_subset = stock_market_data['DXY'].loc[zoom_in_date_start:zoom_in_date_end]
    fig.update_xaxes(type="date", range=[zoom_in_date_start, zoom_in_date_end])

    # Update y-axis range for top subplot
    fig.update_layout(yaxis1=dict(range=[data_subset.min(), data_subset.max()]),
                      yaxis2=dict(range=[0, 100]))

    # Update legend
    fig.update_layout(legend=dict(title=None,
                                  orientation="h",
                                  y=1,
                                  yanchor="bottom",
                                  x=0.5,
                                  xanchor="center",
                                  entrywidth=100))

    # Update margins around the plot to use
    # more of the available space in st.container
    fig.update_layout(
        margin=dict(t=10, b=10)
    )

    # Update subplots y-axis titles
    fig.update_layout(xaxis_title=None, yaxis1_title='DXY', yaxis2_title='RSI (7, 30)')

    # Update top subplot y-axis tickprefix
    fig.update_layout(yaxis1_tickprefix="$")

    # Update colors
    fig.update_layout(coloraxis=dict(colorscale=SYNCRACY_COLORS))

    fig = add_recession_periods(fig, stock_market_data['DXY'].dropna())
    st.plotly_chart(fig, use_container_width=True)
