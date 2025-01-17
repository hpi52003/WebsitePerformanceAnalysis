# -*- coding: utf-8 -*-
"""websiteperformanceanalysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1i7Er1WrTQ2D6YHFIif8YJtLZLm6AfyA2
"""

import statsmodels
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Load and process data
@st.cache_data
def load_data():
    data = pd.read_csv("data-export.csv")
    new_header = data.iloc[0]  # grab the first row for the header
    data = data[1:]  # take the data less the header row
    data.columns = new_header  # set the header row as the df header
    data.reset_index(drop=True, inplace=True)

    # Convert columns to appropriate data types
    data['Date + hour (YYYYMMDDHH)'] = pd.to_datetime(data['Date + hour (YYYYMMDDHH)'], format='%Y%m%d%H')
    data['Users'] = pd.to_numeric(data['Users'])
    data['Sessions'] = pd.to_numeric(data['Sessions'])

    return data

def plot_performance(data):
    # Group data by date and sum up the users and sessions
    grouped_data = data.groupby(data['Date + hour (YYYYMMDDHH)']).agg({'Users': 'sum', 'Sessions': 'sum'})

    # Plotting the aggregated users and sessions over time
    st.subheader('Total Users and Sessions Over Time')
    plt.figure(figsize=(14, 7))
    plt.plot(grouped_data.index, grouped_data['Users'], label='Users', color='blue')
    plt.plot(grouped_data.index, grouped_data['Sessions'], label='Sessions', color='green')
    plt.title('Total Users and Sessions Over Time')
    plt.xlabel('Date and Hour')
    plt.ylabel('Count')
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

def plot_scatter_plots(data):
    # Scatter plots for engagement metrics
    st.subheader('Engagement Metrics')
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: average engagement time vs events per session
    axes[0, 0].scatter(data['Average engagement time per session'], data['Events per session'], color='blue')
    axes[0, 0].set_title('Avg Engagement Time vs Events/Session')
    axes[0, 0].set_xlabel('Average Engagement Time per Session')
    axes[0, 0].set_ylabel('Events per Session')
    axes[0, 0].grid(True)  # enable grid

    # Plot 2: average engagement time vs engagement rate
    axes[0, 1].scatter(data['Average engagement time per session'], data['Engagement rate'], color='red')
    axes[0, 1].set_title('Avg Engagement Time vs Engagement Rate')
    axes[0, 1].set_xlabel('Average Engagement Time per Session')
    axes[0, 1].set_ylabel('Engagement Rate')
    axes[0, 1].grid(True)

    # Plot 3: engaged sessions per user vs events per session
    axes[1, 0].scatter(data['Engaged sessions per user'], data['Events per session'], color='green')
    axes[1, 0].set_title('Engaged Sessions/User vs Events/Session')
    axes[1, 0].set_xlabel('Engaged Sessions per User')
    axes[1, 0].set_ylabel('Events per Session')
    axes[1, 0].grid(True)

    # Plot 4: engaged sessions per user vs engagement rate
    axes[1, 1].scatter(data['Engaged sessions per user'], data['Engagement rate'], color='purple')
    axes[1, 1].set_title('Engaged Sessions/User vs Engagement Rate')
    axes[1, 1].set_xlabel('Engaged Sessions per User')
    axes[1, 1].set_ylabel('Engagement Rate')
    axes[1, 1].grid(True)

    plt.tight_layout()
    st.pyplot(fig)

def plot_channel_performance(data):
    # Ensure numeric columns
    data['Users'] = pd.to_numeric(data['Users'], errors='coerce')
    data['Sessions'] = pd.to_numeric(data['Sessions'], errors='coerce')
    data['Engaged sessions'] = pd.to_numeric(data['Engaged sessions'], errors='coerce')
    data['Engagement rate'] = pd.to_numeric(data['Engagement rate'], errors='coerce')
    data['Events per session'] = pd.to_numeric(data['Events per session'], errors='coerce')

    # Drop rows with NaN values in columns of interest
    data = data.dropna(subset=['Users', 'Sessions', 'Engaged sessions', 'Engagement rate', 'Events per session'])

    # Group data by channel and aggregate necessary metrics
    channel_performance = data.groupby('Session primary channel group (Default channel group)').agg({
        'Users': 'sum',
        'Sessions': 'sum',
        'Engaged sessions': 'sum',
        'Engagement rate': 'mean',
        'Events per session': 'mean'
    })

    # Normalize metrics
    channel_performance['Normalized Engagement Rate'] = channel_performance['Engagement rate'] / channel_performance['Engagement rate'].max()
    channel_performance['Normalized Events per Session'] = channel_performance['Events per session'] / channel_performance['Events per session'].max()

    # Plot channel performance metrics
    st.subheader('Channel Performance Metrics')
    fig, ax = plt.subplots(3, 1, figsize=(12, 18))

    # Users and sessions by channel
    ax[0].bar(channel_performance.index, channel_performance['Users'], label='Users', alpha=0.8)
    ax[0].bar(channel_performance.index, channel_performance['Sessions'], label='Sessions', alpha=0.6)
    ax[0].set_title('Users and Sessions by Channel')
    ax[0].set_ylabel('Count')
    ax[0].legend()

    # Normalized engagement rate by channel
    ax[1].bar(channel_performance.index, channel_performance['Normalized Engagement Rate'], color='orange')
    ax[1].set_title('Normalized Engagement Rate by Channel')
    ax[1].set_ylabel('Normalized Rate')

    # Normalized events per session by channel
    ax[2].bar(channel_performance.index, channel_performance['Normalized Events per Session'], color='green')
    ax[2].set_title('Normalized Events per Session by Channel')
    ax[2].set_ylabel('Normalized Count')

    plt.tight_layout()
    st.pyplot(fig)

def plot_time_series_forecast(grouped_data):
    # Time series forecasting using SARIMA
    time_series_data = grouped_data['Sessions'].asfreq('H').fillna(method='ffill')
    seasonal_period = 24

    sarima_model = SARIMAX(time_series_data,
                          order=(1, 1, 1),
                          seasonal_order=(1, 1, 1, seasonal_period))
    sarima_model_fit = sarima_model.fit()

    # Forecast the next 24 hours
    sarima_forecast = sarima_model_fit.forecast(steps=24)

    # Plot the actual data and the SARIMA forecast
    st.subheader('Website Traffic Forecasting with SARIMA')
    plt.figure(figsize=(14, 7))
    plt.plot(time_series_data.index[-168:], time_series_data[-168:], label='Actual Sessions', color='blue')  # last week data
    plt.plot(pd.date_range(time_series_data.index[-1], periods=25, freq='H')[1:], sarima_forecast, label='Forecasted Sessions', color='red')
    plt.title('Website Traffic Forecasting with SARIMA (Sessions)')
    plt.xlabel('Date and Hour')
    plt.ylabel('Sessions')
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

def main():
    st.title("Website Performance Analysis Dashboard")

    # Load data
    data = load_data()

    # Display and plot performance metrics
    st.sidebar.header("Select Visualization")
    option = st.sidebar.selectbox(
        "Choose an option:",
        ["Total Users and Sessions", "Engagement Metrics", "Channel Performance", "Time Series Forecast"]
    )

    if option == "Total Users and Sessions":
        plot_performance(data)
    elif option == "Engagement Metrics":
        plot_scatter_plots(data)
    elif option == "Channel Performance":
        plot_channel_performance(data)
    elif option == "Time Series Forecast":
        grouped_data = data.groupby(data['Date + hour (YYYYMMDDHH)']).agg({'Users': 'sum', 'Sessions': 'sum'})
        plot_time_series_forecast(grouped_data)

if __name__ == "__main__":
    main()
