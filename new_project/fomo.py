import pandas as pd
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
import io
import base64
import os

# Get the current directory where fomo.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the full path to data.csv
data_path = os.path.join(current_dir, 'data.csv')

# Load and prepare data
data = pd.read_csv(data_path)  # Use the full path
data['Date'] = pd.to_datetime(data['Date'])
cleaned_data = data.dropna()

# Calculate daily percentage change for price
cleaned_data['Price Change'] = cleaned_data['BTC / USD'].pct_change() * 100

# Define window sizes for rolling calculations
SHORT_WINDOW = 24  # 1 day
LONG_WINDOW = 168  # 7 days

def calculate_adaptive_zscore(series, window):
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    return (series - rolling_mean) / rolling_std

# Calculate Price Z-Score
cleaned_data['Price Z-Score'] = calculate_adaptive_zscore(cleaned_data['Price Change'], SHORT_WINDOW)

# Calculate Social Volume Z-Scores using correct column names from CSV
social_volume_columns = [
    'Social Volume (get in)',           # "get in"
    'Social Volume (to the moon)',      # "to the moon"
    'Social Volume (i missed it)'       # "i missed it"
]

# Normalize components to z-scores
def calculate_z_score(series):
    mean = series.mean()
    std_dev = series.std()
    return (series - mean) / std_dev

# Normalize Social Volumes
for col in social_volume_columns:
    cleaned_data[f'{col} Z-Score'] = calculate_z_score(cleaned_data[col])

# Calculate Price Momentum (using correct normalization)
def calculate_price_momentum(data):
    # Calculate daily percentage change
    data['Price Momentum'] = data['BTC / USD'].pct_change() * 100
    
    # Calculate 7-day moving average for price
    data['Price MA7'] = data['BTC / USD'].rolling(window=7).mean()
    
    # Calculate momentum z-score using adaptive window
    data['Price Momentum Z-Score'] = calculate_adaptive_zscore(data['Price Momentum'], SHORT_WINDOW)
    
    # Calculate momentum strength (optional metric)
    data['Momentum Strength'] = data['BTC / USD'] / data['Price MA7']
    
    return data

# Apply price momentum calculations
cleaned_data = calculate_price_momentum(cleaned_data)

# Normalize Price Momentum
cleaned_data['Price Momentum Z-Score'] = calculate_z_score(cleaned_data['Price Momentum'])

# Normalize On-Chain Volumes
cleaned_data['Profit Volume Z-Score'] = calculate_z_score(cleaned_data['Daily On-Chain Transaction Volume in Profit'])
cleaned_data['Loss Volume Z-Score'] = calculate_z_score(cleaned_data['Daily On-Chain Transaction Volume in Loss'])

# Calculate Total Volume and its metrics
cleaned_data['Total Volume'] = (
    cleaned_data['Daily On-Chain Transaction Volume in Profit'] + 
    cleaned_data['Daily On-Chain Transaction Volume in Loss']
)

# Normalize Total Volume
cleaned_data['Total Volume Z-Score'] = calculate_z_score(cleaned_data['Total Volume'])

cleaned_data['Volume MA7'] = cleaned_data['Total Volume'].rolling(window=7).mean()
cleaned_data['Volume Z-Score'] = calculate_adaptive_zscore(cleaned_data['Total Volume'], SHORT_WINDOW)

# Calculate Price/Volume Multiplier
def calculate_price_volume_multiplier(row):
    price_rising = row['Price Z-Score'] > 1
    volume_exceeds = row['Total Volume'] > (row['Volume MA7'] * 1.5)
    return 1.5 if price_rising and volume_exceeds else 1.0

cleaned_data['Price/Volume Multiplier'] = cleaned_data.apply(calculate_price_volume_multiplier, axis=1)

# Define a function to identify significant spikes and track sequences
def identify_social_fomo(cleaned_data):
    # Initialize columns for tracking spikes and sequences
    for col in social_volume_columns:
        cleaned_data.loc[:, f'{col} Spike'] = cleaned_data[f'{col} Z-Score'] > 2

    # Initialize a column for Social FOMO
    cleaned_data.loc[:, 'Social FOMO'] = 0.0

    # Iterate through the DataFrame to track sequences
    for i in range(1, len(cleaned_data)):
        if (cleaned_data[social_volume_columns[0]][i] > 0 and
            cleaned_data[social_volume_columns[1]][i] > 0 and
            cleaned_data[social_volume_columns[2]][i] > 0):
            
            if (1 <= (cleaned_data['Date'][i] - cleaned_data['Date'][i-1]).days <= 7):
                price_momentum_z = cleaned_data['Price Momentum Z-Score'][i]
                profit_volume_z = cleaned_data['Profit Volume Z-Score'][i]
                multiplier = 1.5 if price_momentum_z > 1 and profit_volume_z > 2 else 1.0
                
                # Use loc for assignment
                cleaned_data.loc[i, 'Social FOMO'] = (
                    (0.3 * cleaned_data[f'{social_volume_columns[0]} Z-Score'][i]) +
                    (0.4 * cleaned_data[f'{social_volume_columns[1]} Z-Score'][i]) +
                    (0.3 * cleaned_data[f'{social_volume_columns[2]} Z-Score'][i])
                ) * multiplier
            else:
                cleaned_data.loc[i, 'Social FOMO'] = 0

# Call the function to identify social FOMO
identify_social_fomo(cleaned_data)

# Calculate Social FOMO Score with correct weights and column names
cleaned_data['Social FOMO Score'] = cleaned_data['Social FOMO'] * cleaned_data['Price/Volume Multiplier']

# Normalize components to 0-100 range
def normalize_to_100(series, window=LONG_WINDOW):
    rolling_min = series.rolling(window=window).min()
    rolling_max = series.rolling(window=window).max()
    return 100 * (series - rolling_min) / (rolling_max - rolling_min)

cleaned_data['Normalized Price'] = normalize_to_100(cleaned_data['Price Z-Score'])
cleaned_data['Normalized Volume'] = normalize_to_100(cleaned_data['Volume Z-Score'])
cleaned_data['Normalized Social FOMO'] = normalize_to_100(cleaned_data['Social FOMO Score'])

# Calculate final FOMO Index
def calculate_fomo_index(cleaned_data):
    # Calculate Raw FOMO Index using specified weights
    cleaned_data['Raw FOMO Index'] = (
        0.4 * cleaned_data['Price Momentum Z-Score'] +
        0.3 * cleaned_data['Profit Volume Z-Score'] +
        0.2 * cleaned_data['Social FOMO'] +
        0.1 * cleaned_data['Loss Volume Z-Score']
    )

    # Scale to 0-100
    min_fomo = cleaned_data['Raw FOMO Index'].min()
    max_fomo = cleaned_data['Raw FOMO Index'].max()
    cleaned_data['FOMO Index'] = (
        (cleaned_data['Raw FOMO Index'] - min_fomo) / (max_fomo - min_fomo) * 100
    ).fillna(0)  # Fill NaN values with 0

    return cleaned_data

# Apply FOMO Index calculation
cleaned_data = calculate_fomo_index(cleaned_data)

# Print key verification metrics
print("\nKey FOMO Metrics (last 5 periods):")
print(cleaned_data[['Date', 'BTC / USD', 'Price/Volume Multiplier', 
                    'Social FOMO Score', 'FOMO Index']].tail())

# Display the first few rows of the DataFrame
print(cleaned_data.head())

# Calculate Volume Momentum (using total social volume as volume)
cleaned_data['Volume Momentum'] = cleaned_data['Total Volume'].pct_change() * 100

# Calculate 7-day Moving Average for Volume
cleaned_data['Volume MA7'] = cleaned_data['Total Volume'].rolling(window=7).mean()

# Calculate Social FOMO with weights and multiplier
weights = {
    'Social Volume (to the moon)': 0.3,    # "to the moon"
    'Social Volume (i missed it)': 0.4,    # "i missed it"
    'Social Volume (get in)': 0.3          # "get in"
}

# Calculate base Social FOMO Score
cleaned_data['Base Social FOMO'] = 0
for col, weight in weights.items():
    spike_intensity = cleaned_data[f'{col} Z-Score'] * (cleaned_data[f'{col} Z-Score'] > 1.5)
    cleaned_data['Base Social FOMO'] += spike_intensity * weight

# Apply Price/Volume Multiplier to Social FOMO
cleaned_data['Social FOMO Score'] = cleaned_data['Base Social FOMO'] * cleaned_data['Price/Volume Multiplier']

# Normalize components to 0-100 range
def normalize_to_100(series, window=LONG_WINDOW):
    rolling_min = series.rolling(window=window).min()
    rolling_max = series.rolling(window=window).max()
    return 100 * (series - rolling_min) / (rolling_max - rolling_min)

cleaned_data['Normalized Price'] = normalize_to_100(cleaned_data['Price Z-Score'])
cleaned_data['Normalized Volume'] = normalize_to_100(cleaned_data['Volume Z-Score'])
cleaned_data['Normalized Social FOMO'] = normalize_to_100(cleaned_data['Social FOMO Score'])

# Calculate final FOMO Index using the formula from step 6
cleaned_data['Final FOMO Index'] = (
    0.4 * cleaned_data['Normalized Price'] +
    0.3 * cleaned_data['Normalized Volume'] +
    0.3 * cleaned_data['Normalized Social FOMO']
)

# Fill NaN values with 0
cleaned_data['Final FOMO Index'] = cleaned_data['Final FOMO Index'].fillna(0)

# Display results in logs
print("\nFOMO Score Statistics:")
print(cleaned_data[['Social FOMO Score', 'Final FOMO Index', 'Price/Volume Multiplier']].describe())

# Display recent scores
print("\nRecent FOMO Scores:")
print(cleaned_data[['Date', 'Social FOMO Score', 'Final FOMO Index', 'Price/Volume Multiplier']].tail(10))

# Calculate price changes first
def prepare_price_data(data, price_window=7):
    """
    Prepare price change data for analysis
    """
    analysis = data.copy()
    
    # Calculate future price changes (7 days forward)
    analysis['Future_Price'] = analysis['BTC / USD'].shift(-42)  # 42 periods = 7 days
    analysis['Price_Change_After_Signal'] = (
        (analysis['Future_Price'] - analysis['BTC / USD']) / analysis['BTC / USD'] * 100
    )
    return analysis

def analyze_fomo_signals(data, fomo_threshold=80):
    """
    Analyze FOMO signals and their relationship with price movements
    """
    # Identify FOMO signals using the correct column name
    signals = data[data['FOMO Index'] > fomo_threshold]
    
    print("\nBacktest Results:")
    print(f"Number of FOMO signals: {len(signals)}")
    
    if len(signals) > 0:
        print(f"Average price change after signal: {signals['Price_Change_After_Signal'].mean():.2f}%")
        print(f"Max price change after signal: {signals['Price_Change_After_Signal'].max():.2f}%")
        print(f"Min price change after signal: {signals['Price_Change_After_Signal'].min():.2f}%")
        
        # Display signal dates and corresponding price changes
        print("\nFOMO Signal Dates and Price Changes:")
        print(signals[['Date', 'FOMO Index', 'Price_Change_After_Signal']].to_string())

def analyze_false_positives(data, fomo_threshold=80, price_drop_threshold=-5):
    """
    Analyze false positive signals (FOMO signals followed by price drops)
    """
    signals = data[data['FOMO Index'] > fomo_threshold]
    false_positives = signals[signals['Price_Change_After_Signal'] < price_drop_threshold]
    
    print("\nFalse Positive Analysis:")
    print(f"Total signals: {len(signals)}")
    print(f"False positives: {len(false_positives)}")
    if len(signals) > 0:
        print(f"False positive rate: {(len(false_positives)/len(signals))*100:.2f}%")
        print("\nFalse Positive Dates:")
        print(false_positives[['Date', 'FOMO Index', 'Price_Change_After_Signal']].to_string())

# Prepare data with price changes
analysis_data = prepare_price_data(cleaned_data)

# Run analyses
analyze_fomo_signals(analysis_data)
analyze_false_positives(analysis_data)

# Set the style for seaborn
sns.set(style="whitegrid")

# Define a function to identify FOMO signals
def identify_fomo_signals(cleaned_data):
    # Initialize a column for FOMO signals
    cleaned_data['FOMO Signal'] = 0

    # Iterate through the DataFrame to identify signals
    for i in range(1, len(cleaned_data)):
        # Print the current FOMO Index for debugging
        print(f"FOMO Index on {cleaned_data['Date'][i]}: {cleaned_data['FOMO Index'][i]}")

        # Check for FOMO spikes
        if cleaned_data['FOMO Index'][i] > 90:
            cleaned_data.loc[i, 'FOMO Signal'] = 1  # Flag as a FOMO signal
            print(f"FOMO Signal flagged on {cleaned_data['Date'][i]} due to FOMO Index > 90")

        # Check for rapid increase in FOMO Index
        if (cleaned_data['FOMO Index'][i] - cleaned_data['FOMO Index'][i - 1]) > 20:
            if (i >= 3 and cleaned_data['FOMO Index'][i - 1] > 70):  # Ensure we have at least 3 days of data
                cleaned_data.loc[i, 'FOMO Signal'] = 1  # Flag as a FOMO signal
                print(f"FOMO Signal flagged on {cleaned_data['Date'][i]} due to rapid increase")

# Call the function to identify FOMO signals
identify_fomo_signals(cleaned_data)

# Print the DataFrame to check flagged signals
print(cleaned_data[['Date', 'FOMO Index', 'FOMO Signal']].tail(10))

# Define a function to backtest FOMO signals
def backtest_fomo_signals(cleaned_data, days_forward=7):
    # Prepare a DataFrame to store backtest results
    backtest_results = []

    # Iterate through the DataFrame to analyze FOMO signals
    for i in range(len(cleaned_data)):
        if cleaned_data['FOMO Signal'][i] == 1:  # If a FOMO signal is flagged
            # Calculate future price change
            future_price = cleaned_data['BTC / USD'].shift(-days_forward)[i]  # Price after 'days_forward'
            current_price = cleaned_data['BTC / USD'][i]
            if future_price is not None:
                price_change = ((future_price - current_price) / current_price) * 100
                backtest_results.append({
                    'Date': cleaned_data['Date'][i],
                    'FOMO Index': cleaned_data['FOMO Index'][i],
                    'Price Change (%)': price_change
                })

    # Convert backtest results to DataFrame
    backtest_df = pd.DataFrame(backtest_results)

    # Print summary of backtest results
    if not backtest_df.empty:
        avg_price_change = backtest_df['Price Change (%)'].mean()
        total_signals = len(backtest_df)
        successful_signals = len(backtest_df[backtest_df['Price Change (%)'] > 0])
        success_rate = (successful_signals / total_signals) * 100

        print("\nBacktest Summary:")
        print(f"Total FOMO Signals: {total_signals}")
        print(f"Successful Signals (Price Increase): {successful_signals} ({success_rate:.2f}%)")
        print(f"Average Price Change After Signal: {avg_price_change:.2f}%")
        
        # Print only the most significant signals
        print("\nSignificant FOMO Signals:")
        print(backtest_df[['Date', 'FOMO Index', 'Price Change (%)']].to_string(index=False))
    else:
        print("\nNo FOMO signals were flagged in the backtest.")

# Run the backtest
backtest_fomo_signals(cleaned_data)

