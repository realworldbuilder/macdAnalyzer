import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.title('Stock MACD and RSI Analysis')

# User input for ticker symbol
ticker = st.text_input('Enter stock ticker:', 'AAPL')

# User input for date range
start_date = st.date_input('Start date', datetime.today() - timedelta(days=365))
end_date = st.date_input('End date', datetime.today())

# Fetch data
data = yf.download(ticker, start=start_date, end=end_date)

# Calculate MACD
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['EMA_12'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    return data

# Calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

# Apply calculations
data = calculate_macd(data)
data = calculate_rsi(data)

# Plotting
fig, (ax1, ax2, ax3) = plt.subplots(3, figsize=(12, 8), sharex=True)

# Price plot
ax1.plot(data['Close'], label='Close Price')
ax1.set_title('Close Price')
ax1.legend()

# MACD plot
ax2.plot(data['MACD'], label='MACD')
ax2.plot(data['Signal_Line'], label='Signal Line')
ax2.set_title('MACD')
ax2.legend()

# RSI plot
ax3.plot(data['RSI'], label='RSI')
ax3.set_title('RSI')
ax3.legend()

# Show plot in Streamlit
st.pyplot(fig)

# Detect crossovers
def detect_crossovers(data):
    data['Crossover'] = np.where((data['MACD'] > data['Signal_Line']) & (data['MACD'].shift(1) <= data['Signal_Line'].shift(1)), 1, 0)
    data['Crossover'] = np.where((data['MACD'] < data['Signal_Line']) & (data['MACD'].shift(1) >= data['Signal_Line'].shift(1)), -1, data['Crossover'])
    return data

data = detect_crossovers(data)

# Performance analysis
def performance_analysis(data):
    crossovers = data[data['Crossover'] != 0]
    results = []

    for index, row in crossovers.iterrows():
        future_data = data.loc[index:]
        if len(future_data) > 30:
            performance_5d = (future_data['Close'].iloc[5] - row['Close']) / row['Close']
            performance_14d = (future_data['Close'].iloc[14] - row['Close']) / row['Close']
            performance_30d = (future_data['Close'].iloc[30] - row['Close']) / row['Close']
            results.append([index, row['Crossover'], performance_5d, performance_14d, performance_30d])
