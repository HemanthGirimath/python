import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

import matplotlib.pyplot as plt
import io
import base64
from fomo import cleaned_data  # Import the processed data from fomo.py

def generate_web_charts():
    charts = {}
    
    # Chart 1: BTC Price with FOMO Index overlay
    plt.figure(figsize=(15, 8))
    
    # Create primary y-axis for BTC price
    ax1 = plt.gca()
    ax1.plot(cleaned_data['Date'], cleaned_data['BTC / USD'], color='blue', label='BTC Price')
    ax1.set_ylabel('BTC Price (USD)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    # Create secondary y-axis for FOMO Index
    ax2 = ax1.twinx()
    ax2.fill_between(cleaned_data['Date'], cleaned_data['Normalized FOMO Score'], 
                     color='orange', alpha=0.3, label='FOMO Index')
    ax2.set_ylabel('FOMO Index', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax2.set_ylim(0, 100)
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.title('BTC Price with FOMO Index')
    plt.grid(True, alpha=0.3)
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    charts['combined'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Chart 2: FOMO Indicator (0-100)
    plt.figure(figsize=(15, 5))
    plt.plot(cleaned_data['Date'], cleaned_data['Normalized FOMO Score'], 
             color='blue', label='FOMO Score')
    
    # Add reference lines
    plt.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='Overbought (80)')
    plt.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='Oversold (20)')
    
    # Add colored zones
    plt.fill_between(cleaned_data['Date'], 80, 100, color='red', alpha=0.1)
    plt.fill_between(cleaned_data['Date'], 0, 20, color='green', alpha=0.1)
    
    plt.title('FOMO Index (0-100)')
    plt.ylabel('FOMO Score')
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    charts['fomo'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return charts 