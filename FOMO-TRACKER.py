import streamlit as st
import requests
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='.*OpenSSL.*')

def get_historical_token_data(token_id='aave', days=15):
    """Fetch historical price and volume data from CoinGecko API with timeout and retries"""
    for attempt in range(3):  # Try up to 3 times
        try:
            # Add delay between attempts
            if attempt > 0:
                time.sleep(2)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': int(start_date.timestamp()),
                'to': int(end_date.timestamp())
            }
            
            # Add timeout to request
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('prices') or not data.get('total_volumes'):
                    st.error("Received empty data from API")
                    return [], []
                    
                prices = [price[1] for price in data['prices']]
                volumes = [volume[1] for volume in data['total_volumes']]
                return prices, volumes
            elif response.status_code == 429:  # Rate limit error
                st.warning("Rate limit reached. Waiting before retry...")
                time.sleep(30)  # Wait longer for rate limit
                continue
            else:
                st.error(f"API Error: Status Code {response.status_code}")
                
        except requests.exceptions.Timeout:
            st.warning(f"Request timed out (attempt {attempt + 1}/3)")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    st.error("Failed to fetch data after multiple attempts")
    return [], []

def calculate_rsi(prices, periods=14):
    """Calculate Relative Strength Index"""
    if len(prices) < periods:
        return 50, 0, 0  # Return default values if not enough data
    
    price_changes = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [max(change, 0) for change in price_changes]
    losses = [abs(min(change, 0)) for change in price_changes]
    
    avg_gain = sum(gains[-periods:]) / periods
    avg_loss = sum(losses[-periods:]) / periods
    
    if avg_loss == 0:
        return 100, avg_gain, avg_loss
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi, avg_gain, avg_loss

def calculate_volume_oscillator(volumes, short_period=5, long_period=15):
    """Calculate volume oscillator"""
    if len(volumes) < long_period:
        return 0
    
    short_ma = np.convolve(volumes, np.ones(short_period), 'valid') / short_period
    long_ma = np.convolve(volumes, np.ones(long_period), 'valid') / long_period
    
    if len(long_ma) == 0:
        return 0
        
    diff = short_ma[-1] - long_ma[-1]
    normalized_diff = (diff / long_ma[-1]) * 100 if long_ma[-1] != 0 else 0
    
    return normalized_diff

def calculate_volume_analysis(volumes):
    """Calculate various volume metrics"""
    if not volumes:
        return {
            'total_volume': 0,
            'average_volume': 0,
            'median_volume': 0,
            'volume_std_dev': 0,
            'volume_volatility': 0,
            'volume_trend': 0,
            'volume_oscillator': 0
        }
    
    volume_metrics = {
        'total_volume': sum(volumes),
        'average_volume': np.mean(volumes),
        'median_volume': np.median(volumes),
        'volume_std_dev': np.std(volumes),
        'volume_volatility': (np.std(volumes) / np.mean(volumes)) * 100 if np.mean(volumes) != 0 else 0,
        'volume_trend': np.polyfit(range(len(volumes)), volumes, 1)[0],
        'volume_oscillator': calculate_volume_oscillator(volumes)
    }
    
    return volume_metrics

def calculate_composite_score(rsi, volume_metrics):
    """Calculate overall trading score"""
    rsi_score = 100 - abs(50 - rsi)
    volume_oscillator = volume_metrics.get('volume_oscillator', 0)
    volume_momentum_score = min(max((volume_oscillator + 10) * 5, 0), 100)
    volume_volatility = volume_metrics.get('volume_volatility', 0)
    volume_volatility_score = 100 - min(volume_volatility, 100)
    
    composite_score = (
        0.4 * rsi_score + 
        0.3 * volume_momentum_score + 
        0.3 * volume_volatility_score
    )
    
    return composite_score

def get_recommendation(composite_score):
    """Get trading recommendation based on composite score"""
    if composite_score > 70:
        return "STRONG BUY", "#00ff00"  # Bright green
    elif composite_score > 55:
        return "BUY", "#90EE90"  # Light green
    elif composite_score > 45:
        return "HOLD", "#FFFF00"  # Yellow
    elif composite_score > 30:
        return "SELL", "#FFA500"  # Orange
    else:
        return "STRONG SELL", "#FF0000"  # Red

def create_candlestick_chart(dates, prices, volumes, token_id):
    """Create an interactive price and volume chart"""
    fig = go.Figure()

    # Add price line
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        name="Price",
        line=dict(color='blue'),
        yaxis="y"
    ))

    # Add volume bars
    fig.add_trace(go.Bar(
        x=dates,
        y=volumes,
        name="Volume",
        yaxis="y2",
        marker=dict(color='rgba(0,0,0,0.2)')
    ))

    # Update layout
    fig.update_layout(
        title=f"{token_id.upper()} Price and Volume",
        yaxis=dict(
            title="Price (USD)",
            side="left",
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis2=dict(
            title="Volume",
            side="right",
            overlaying="y",
            showgrid=False
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        hovermode='x unified',
        height=400,
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def main():
    # Page config
    st.set_page_config(
        page_title="Crypto Trading Indicator",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a1a;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Crypto Trading Indicator Dashboard")

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        token_id = st.selectbox(
            "Select Token",
            ["aave", "uniswap", "chainlink", "ethereum", "bitcoin"]
        )
        days = st.slider("Number of Days", 5, 30, 15)
        if st.button('🔄 Refresh Data'):
            st.experimental_rerun()

    # Main content
    try:
        with st.spinner('Fetching data... Please wait.'):
            prices, volumes = get_historical_token_data(token_id, days)

            if not prices or not volumes:
                st.error("⚠️ No data available. Please try again later or select a different token.")
                st.stop()

            # Calculate indicators
            rsi, avg_gain, avg_loss = calculate_rsi(prices)
            volume_metrics = calculate_volume_analysis(volumes)
            composite_score = calculate_composite_score(rsi, volume_metrics)
            recommendation, color = get_recommendation(composite_score)

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RSI", f"{rsi:.2f}")
            with col2:
                st.metric("Composite Score", f"{composite_score:.2f}")
            with col3:
                st.markdown(f"<h1 style='text-align: center; color: {color};'>{recommendation}</h1>", 
                           unsafe_allow_html=True)

            # Create and display price chart
            dates = [datetime.now() - timedelta(days=i) for i in range(days)][::-1]
            fig_price = create_candlestick_chart(dates, prices, volumes, token_id)
            st.plotly_chart(fig_price, use_container_width=True)

            # Create two columns for additional charts
            col1, col2 = st.columns(2)
            
            with col1:
                # RSI Gauge
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=rsi,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "RSI"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 30], 'color': "lightgreen"},
                            {'range': [30, 70], 'color': "lightgray"},
                            {'range': [70, 100], 'color': "red"}
                        ]
                    }
                ))
                fig_gauge.update_layout(template="plotly_dark")
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col2:
                # Volume Metrics
                volume_data = {
                    'Metric': ['Volatility', 'Momentum', 'Trend'],
                    'Value': [
                        volume_metrics['volume_volatility'],
                        volume_metrics['volume_oscillator'] + 50,
                        volume_metrics['volume_trend'] / 1000000
                    ]
                }
                fig_volume = px.bar(
                    volume_data,
                    x='Metric',
                    y='Value',
                    title="Volume Metrics",
                    template="plotly_dark"
                )
                st.plotly_chart(fig_volume, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")

if __name__ == "__main__":
    main()