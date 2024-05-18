import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime

# Introduction and explanation of MACD
st.title('MACD Analyzer')
st.markdown("""
This application analyzes the Moving Average Convergence Divergence (MACD), which is a trend-following momentum indicator that shows the relationship between two moving averages of a stock's prices.
""")

# Fetch and calculate MACD
def fetch_and_calculate_macd(stock_symbol, start_date=None):
    if start_date is None:
        start_date = datetime.now() - pd.DateOffset(years=3)
    end_date = datetime.now()
    df = yf.download(stock_symbol, start=start_date, end=end_date)
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()  # 12-period EMA
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()  # 26-period EMA
    df['MACD'] = df['EMA12'] - df['EMA26']  # MACD line
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()  # Signal line
    return df

# Input for name
stock_symbol = st.sidebar.text_input('Enter stock symbol', value='AAPL')
st.sidebar.write("""
The MACD is calculated by subtracting the 26-period Exponential Moving Average (EMA) from the 12-period EMA. The result of that subtraction is the MACD line.
""")

# Analyze button
if st.sidebar.button('Analyze'):
    df = fetch_and_calculate_macd(stock_symbol)
    df['Cross'] = ((df['MACD'].shift(1) < df['Signal'].shift(1)) & (df['MACD'] >= df['Signal']) & (df['MACD'] < 0))


    # Performance calculation after cross
    def post_cross_performance(df):
        crosses = df[df['Cross']].index
        performance = []
        for date in crosses:
            end_date_10 = date + pd.DateOffset(days=10)
            end_date_30 = date + pd.DateOffset(days=30)

            window_10 = df.loc[date:end_date_10]
            window_30 = df.loc[date:min(end_date_30, df.index[-1])]

            close_after_10_days = window_10['Close'].iloc[-1] if len(window_10) > 1 else np.nan
            close_after_30_days = window_30['Close'].iloc[-1] if end_date_30 <= df.index[-1] else np.nan

            performance.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Close at Cross': df.at[date, 'Close'],
                'High After Cross': window_10['Close'].max(),
                'Low After Cross': window_10['Close'].min(),
                'Close After 10 Days': close_after_10_days,
                'Close After 30 Days': close_after_30_days,
                'Percentage Change 10 Days': ((close_after_10_days - df.at[date, 'Close']) / df.at[
                    date, 'Close']) * 100 if not np.isnan(close_after_10_days) else np.nan,
                'Percentage Change 30 Days': ((close_after_30_days - df.at[date, 'Close']) / df.at[
                    date, 'Close']) * 100 if not np.isnan(close_after_30_days) else np.nan,
                '10 Days Data Available': 'Yes' if end_date_10 <= df.index[-1] else 'No',
                '30 Days Data Available': 'Yes' if end_date_30 <= df.index[-1] else 'No'
            })
        return pd.DataFrame(performance).sort_values(by='Date', ascending=False).head(5)

    # Assuming df is your DataFrame
    post_cross_data = post_cross_performance(df)


    # Assuming df is your DataFrame
    post_cross_data = post_cross_performance(df)

    # Plotting both price and MACD
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=('Stock Price', 'MACD and Signal Line'))
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='red')), row=2, col=1)
    fig.update_layout(height=600, width=700, title_text="Stock Analysis", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    # Dataframe displaying last 5 MACD crossovers and performance
    if not post_cross_data.empty:
        st.write('Last 5 MACD Crossovers and Subsequent 10-day Performance:')
        st.table(post_cross_data)

st.write("""
### Understanding MACD:
- **MACD Line:** The difference between the 12-period and 26-period exponential moving averages (EMAs).
- **Signal Line:** The 9-period EMA of the MACD line, which acts as a trigger for buy and sell signals.
- **Crossovers:** When the MACD line crosses above the signal line, it is considered a bullish signal, and when it crosses below, it is considered bearish.
""")
