import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Streamlit page configuration
st.set_page_config(layout="wide")

# Title of the app
st.title('Stock MACD and RSI Analysis')

# User input for ticker symbol
ticker = st.text_input('Enter stock ticker:', 'AAPL')

# User input for date range
default_start_date = datetime.today() - timedelta(days=365)
default_end_date = datetime.today()
start_date = st.date_input('Start date', default_start_date)
end_date = st.date_input('End date', default_end_date)

# Fetch stock data
@st.cache
def get_data(ticker, start, end):
    return yf.download(ticker, start=start, end=end)

data = get_data(ticker, start_date, end_date)

# Calculate MACD
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['EMA12'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    return data

# Calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))
    data['RSI'] = RSI
    return data

# Apply calculations
data = calculate_macd(data)
data = calculate_rsi(data)

# Plotly chart
fig = go.Figure()

# Add price trace
fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))

# Add MACD trace
fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], mode='lines', name='MACD'))
fig.add_trace(go.Scatter(x=data.index, y=data['Signal_Line'], mode='lines', name='Signal Line'))

# Add RSI trace
fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI', yaxis='y2'))

# Update layout for dual y-axis
fig.update_layout(
    yaxis2=dict(title='RSI', overlaying='y', side='right'),
    title=f'{ticker} Price, MACD, and RSI',
    xaxis_title='Date',
    yaxis_title='Price',
    autosize=True,
    height=800
)

# Display chart
st.plotly_chart(fig, use_container_width=True)

# Analyze MACD crossovers and stock performance
def macd_crossover_analysis(data):
    crossovers = []
    for i in range(1, len(data)):
        if data['MACD'][i-1] < data['Signal_Line'][i-1] and data['MACD'][i] > data['Signal_Line'][i]:
            crossovers.append((data.index[i], 'Bullish', data['MACD'][i], data['Close'][i]))
        elif data['MACD'][i-1] > data['Signal_Line'][i-1] and data['MACD'][i] < data['Signal_Line'][i]:
            crossovers.append((data.index[i], 'Bearish', data['MACD'][i], data['Close'][i]))
    return crossovers

def stock_performance(data, crossovers, periods=[7, 14, 30]):
    performance = []
    for date, signal, macd_value, price in crossovers:
        row = {'Date': date, 'Signal': signal, 'MACD': macd_value, 'Price': price}
        for period in periods:
            future_date = date + timedelta(days=period)
            if future_date in data.index:
                future_price = data.loc[future_date, 'Close']
                row[f'{period}D Later'] = (future_price - price) / price * 100
            else:
                row[f'{period}D Later'] = np.nan
        performance.append(row)
    return pd.DataFrame(performance)

crossovers = macd_crossover_analysis(data)
performance_df = stock_performance(data, crossovers)

# Display DataFrame
st.subheader('MACD Crossover Performance')
st.dataframe(performance_df)
