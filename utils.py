def compute_returns(col):
    col = col.dropna()
    latest_price = col.iloc[-1]
    previous_close = col.iloc[-2]
    week_ago_close = col.iloc[-7]
    begining_close = col.iloc[0]

    last_day_return = (latest_price / previous_close - 1) * 100
    seven_day_return = (latest_price / week_ago_close - 1) * 100
    thirty_day_return = (latest_price / begining_close - 1) * 100

    return [latest_price, last_day_return, seven_day_return, thirty_day_return]


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
