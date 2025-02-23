from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from fomo import cleaned_data
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import plotly
from flask_login import LoginManager, login_required, current_user
from auth import auth, login_manager  # Import both auth blueprint and login_manager
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'SamDean*021345sdac'

# Initialize login manager with the app
login_manager.init_app(app)

# Register the authentication blueprint
app.register_blueprint(auth)

# Run calculations once when the app starts
def prepare_data():
    # Ensure that the necessary calculations are done here
    # This is where you would call your functions to prepare cleaned_data
    pass  # Replace with your data preparation logic

def create_price_fomo_chart(moving_average=None):
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add BTC price trace
    fig.add_trace(
        go.Scatter(
            x=cleaned_data['Date'],
            y=cleaned_data['BTC / USD'],
            name="BTC Price",
            line=dict(color='#2962FF')
        ),
        secondary_y=False,
    )

    # Add FOMO index trace with smoothing
    fomo_index = cleaned_data['FOMO Index'].rolling(window=3).mean()  # Smoothing with a moving average
    if moving_average:
        fomo_index = cleaned_data['FOMO Index'].rolling(window=moving_average).mean()

    fig.add_trace(
        go.Scatter(
            x=cleaned_data['Date'],
            y=fomo_index,
            name="FOMO Index",
            line=dict(color='#FF6D00', shape='spline'),  # Spline for smoothness
            mode='lines'
        ),
        secondary_y=True,
    )

    # Add social volume traces with smoothing
    for keyword in ['Social Volume (to the moon)', 'Social Volume (get in)']:
        fig.add_trace(
            go.Scatter(
                x=cleaned_data['Date'],
                y=cleaned_data[f'{keyword} Z-Score'].rolling(window=3).mean(),  # Smoothing with a moving average
                name=f"{keyword} Z-Score",
                line=dict(dash='dash', shape='spline'),  # Spline for smoothness
                mode='lines'
            ),
            secondary_y=False,
        )

    # Update layout
    fig.update_layout(
        title="BTC Price vs FOMO Index and Social Volumes",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=600,
    )

    # Set y-axes titles
    fig.update_yaxes(title_text="BTC Price (USD)", secondary_y=False)
    fig.update_yaxes(title_text="FOMO Index", secondary_y=True)

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_gauge_chart():
    # Get the latest FOMO index value
    current_fomo = cleaned_data['FOMO Index'].iloc[-1]

    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_fomo,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1976D2"},
            'steps': [
                {'range': [0, 20], 'color': 'red'},
                {'range': [20, 80], 'color': 'yellow'},
                {'range': [80, 100], 'color': 'green'}
            ],
        }
    ))

    fig.update_layout(
        title="Current FOMO Index",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def calculate_rsi(data, periods=14):
    # Calculate price changes
    delta = data['BTC / USD'].diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    
    # Calculate RS and RSI
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def create_rsi_chart(filtered_data):
    rsi = calculate_rsi(filtered_data)
    
    fig = go.Figure()
    
    # Add RSI line
    fig.add_trace(
        go.Scatter(
            x=filtered_data['Date'],
            y=rsi,
            name="RSI",
            line=dict(color='#2962FF')
        )
    )
    
    # Add overbought/oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
    
    # Update layout
    fig.update_layout(
        title="Relative Strength Index (RSI)",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)"
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        yaxis=dict(
            title="RSI",
            range=[0, 100],
            gridcolor='rgba(128,128,128,0.2)',
            zerolinecolor='rgba(128,128,128,0.2)'
        ),
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.2)',
            zerolinecolor='rgba(128,128,128,0.2)'
        )
    )
    
    return fig

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/update_chart', methods=['POST'])
def update_chart():
    try:
        data = request.get_json()
        moving_average = int(data.get('moving_average', 0))
        scale_type = data.get('scale_type', 'linear')
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add BTC price trace
        fig.add_trace(
            go.Scatter(
                x=cleaned_data['Date'],
                y=cleaned_data['BTC / USD'],
                name="BTC Price",
                line=dict(color='#2962FF')
            ),
            secondary_y=False,
        )

        # Add FOMO index trace with moving average if selected
        fomo_data = cleaned_data['FOMO Index']
        if moving_average > 0:
            fomo_data = fomo_data.rolling(window=moving_average).mean()
            name = f"FOMO Index ({moving_average}D MA)"
        else:
            name = "FOMO Index"

        fig.add_trace(
            go.Scatter(
                x=cleaned_data['Date'],
                y=fomo_data,
                name=name,
                line=dict(color='#FF6D00', shape='spline'),
                mode='lines'
            ),
            secondary_y=True,
        )

        # Add social volume traces
        for keyword in ['Social Volume (to the moon)', 'Social Volume (get in)']:
            fig.add_trace(
                go.Scatter(
                    x=cleaned_data['Date'],
                    y=cleaned_data[f'{keyword} Z-Score'].rolling(window=3).mean(),
                    name=f"{keyword} Z-Score",
                    line=dict(dash='dash', shape='spline'),
                    mode='lines'
                ),
                secondary_y=False,
            )

        # Update layout
        fig.update_layout(
            title="BTC Price vs FOMO Index and Social Volumes",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=600,
        )

        # Set y-axes titles and scale type for both axes
        fig.update_yaxes(title_text="BTC Price (USD)", secondary_y=False, type=scale_type)
        fig.update_yaxes(title_text="FOMO Index", secondary_y=True, type=scale_type)  # Update FOMO Index scale

        return jsonify({"chart": json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Create the charts
        price_fomo_chart = create_price_fomo_chart()
        gauge_chart = create_gauge_chart()

        # Parse the JSON strings back to objects
        price_fomo_data = json.loads(price_fomo_chart)
        gauge_data = json.loads(gauge_chart)

        # Prepare additional info
        additional_info = {
            'FOMO Index': f"{cleaned_data['FOMO Index'].iloc[-1]:.2f}",
            'Last BTC Price': f"${cleaned_data['BTC / USD'].iloc[-1]:,.2f}"
        }

        return render_template('dashboard.html',
                            price_fomo_chart=price_fomo_data,
                            gauge_chart=gauge_data,
                            additional_info=additional_info,
                            active_page='dashboard')
    except Exception as e:
        print(f"Error in dashboard route: {str(e)}")
        return f"An error occurred: {str(e)}"

@app.route('/export_data', methods=['POST'])
@login_required
def export_data():
    try:
        data = request.get_json()
        moving_average = int(data.get('moving_average', 0))
        date_range = data.get('date_range', '').split(' to ')
        
        # Filter data based on date range
        filtered_data = cleaned_data.copy()
        if len(date_range) == 2:
            # Convert dates to pandas datetime and normalize timezone
            start_date = pd.to_datetime(date_range[0]).tz_localize(None)
            end_date = pd.to_datetime(date_range[1]).tz_localize(None)
            
            # Ensure the DataFrame dates are timezone-naive
            filtered_data['Date'] = filtered_data['Date'].dt.tz_localize(None)
            
            # Apply date filter
            filtered_data = filtered_data[
                (filtered_data['Date'] >= start_date) & 
                (filtered_data['Date'] <= end_date)
            ]

        # Apply moving average if selected
        if moving_average > 0:
            filtered_data['FOMO Index'] = filtered_data['FOMO Index'].rolling(
                window=moving_average).mean()

        # Create CSV in memory
        output = io.StringIO()
        filtered_data.to_csv(output, index=False)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=fomo_data.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html', active_page='analytics')

@app.route('/alerts')
@login_required
def alerts():
    alerts = [
        {'id': 1, 'type': 'FOMO', 'message': 'FOMO Index above 80', 'created_at': '2024-02-23 14:30'},
        {'id': 2, 'type': 'Price', 'message': 'BTC Price increased by 5%', 'created_at': '2024-02-23 13:15'}
    ]
    return render_template('alerts.html', active_page='alerts', alerts=alerts)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', active_page='settings')

@app.route('/refresh_data', methods=['POST'])
@login_required
def refresh_data():
    try:
        data = request.get_json()
        moving_average = int(data.get('moving_average', 0))
        scale_type = data.get('scale_type', 'linear')
        show_indicators = data.get('show_indicators', False)
        date_range = data.get('date_range', '').split(' to ')

        # Create figure with secondary y-axis and RSI subplot
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3] if show_indicators else [1, 0],
            specs=[[{"secondary_y": True}],
                  [{"secondary_y": False}]]
        )

        # Filter data based on date range if provided
        filtered_data = cleaned_data.copy()
        if len(date_range) == 2 and date_range[0] and date_range[1]:
            start_date = pd.to_datetime(date_range[0]).tz_localize(None)
            end_date = pd.to_datetime(date_range[1]).tz_localize(None)
            filtered_data['Date'] = filtered_data['Date'].dt.tz_localize(None)
            filtered_data = filtered_data[
                (filtered_data['Date'] >= start_date) & 
                (filtered_data['Date'] <= end_date)
            ]

        # Add BTC price trace
        fig.add_trace(
            go.Scatter(
                x=filtered_data['Date'],
                y=filtered_data['BTC / USD'],
                name="BTC Price",
                line=dict(color='#2962FF')
            ),
            secondary_y=False,
            row=1, col=1
        )

        # Add FOMO index trace with moving average if selected
        fomo_data = filtered_data['FOMO Index']
        if moving_average > 0:
            fomo_data = fomo_data.rolling(window=moving_average).mean()
            name = f"FOMO Index ({moving_average}D MA)"
        else:
            name = "FOMO Index"

        fig.add_trace(
            go.Scatter(
                x=filtered_data['Date'],
                y=fomo_data,
                name=name,
                line=dict(color='#FF6D00', shape='spline'),
                mode='lines'
            ),
            secondary_y=True,
            row=1, col=1
        )

        # Add RSI trace with visibility control
        rsi = calculate_rsi(filtered_data)
        rsi_trace = go.Scatter(
            x=filtered_data['Date'],
            y=rsi,
            name="RSI",
            line=dict(color='#2962FF'),
            visible=show_indicators
        )
        fig.add_trace(rsi_trace, row=2, col=1)

        # Add overbought/oversold lines with visibility control
        if show_indicators:
            fig.add_hline(
                y=70,
                line_dash="dash",
                line_color="red",
                annotation_text="Overbought (70)",
                row=2
            )
            fig.add_hline(
                y=30,
                line_dash="dash",
                line_color="green",
                annotation_text="Oversold (30)",
                row=2
            )

        # Update layout
        fig.update_layout(
            title="BTC Price vs FOMO Index",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            height=800,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(0,0,0,0.5)"
            ),
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Update main chart axes
        fig.update_yaxes(
            title_text="BTC Price (USD)", 
            secondary_y=False, 
            type=scale_type,
            gridcolor='rgba(128,128,128,0.2)',
            zerolinecolor='rgba(128,128,128,0.2)',
            row=1,
            layer='above traces'  # This ensures grid lines appear above the background
        )
        fig.update_yaxes(
            title_text="FOMO Index", 
            secondary_y=True, 
            type=scale_type,
            gridcolor='rgba(128,128,128,0.2)',
            zerolinecolor='rgba(128,128,128,0.2)',
            row=1,
            layer='above traces'  # This ensures grid lines appear above the background
        )
        fig.update_xaxes(
            gridcolor='rgba(128,128,128,0.2)',
            zerolinecolor='rgba(128,128,128,0.2)',
            row=1,
            layer='above traces'  # This ensures grid lines appear above the background
        )

        # Update RSI axes
        if show_indicators:
            fig.update_yaxes(
                title_text="RSI",
                range=[0, 100],
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.2)',
                row=2,
                visible=True,
                layer='above traces'
            )
            fig.update_xaxes(
                visible=True,
                gridcolor='rgba(128,128,128,0.2)',
                zerolinecolor='rgba(128,128,128,0.2)',
                row=2,
                layer='above traces'
            )
        else:
            fig.update_yaxes(visible=False, row=2)
            fig.update_xaxes(visible=False, row=2)

        # Update gauge chart
        gauge_chart = create_gauge_chart()

        # Get current metrics
        additional_info = {
            'FOMO Index': f"{filtered_data['FOMO Index'].iloc[-1]:.2f}",
            'Last BTC Price': f"${filtered_data['BTC / USD'].iloc[-1]:,.2f}"
        }

        return jsonify({
            "status": "success",
            "chart": json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)),
            "gauge_chart": json.loads(gauge_chart),
            "additional_info": additional_info
        })

    except Exception as e:
        print(f"Error in refresh_data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    prepare_data()  # Call the function to prepare data once
    app.run(debug=True) 