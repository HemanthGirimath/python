from flask import Flask, render_template, request, jsonify, Response
from fomo import cleaned_data
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import plotly
from flask_login import LoginManager, login_required
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

@app.route('/')
def index():
    try:
        price_fomo_chart = create_price_fomo_chart()
        gauge_chart = create_gauge_chart()
        additional_info = {
            "FOMO Index": cleaned_data['FOMO Index'].iloc[-1],
            "Last BTC Price": cleaned_data['BTC / USD'].iloc[-1],
            "Social Volume (to the moon)": cleaned_data['Social Volume (to the moon)'].iloc[-1],
            "Social Volume (get in)": cleaned_data['Social Volume (get in)'].iloc[-1],
        }
        return render_template('index.html', 
                               price_fomo_chart=price_fomo_chart,
                               gauge_chart=gauge_chart,
                               additional_info=additional_info)
    except Exception as e:
        return f"An error occurred: {str(e)}"

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
    # Create the charts
    price_fomo_chart = create_price_fomo_chart()
    
    # Create gauge chart
    gauge_chart = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cleaned_data['FOMO Index'].iloc[-1],  # Get the latest FOMO index value
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Current FOMO Level"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#FF6D00"},
            'steps': [
                {'range': [0, 30], 'color': "green"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "red"}
            ]
        }
    ))

    # Prepare additional info
    additional_info = {
        'FOMO Index': f"{cleaned_data['FOMO Index'].iloc[-1]:.2f}",
        'Last BTC Price': f"${cleaned_data['BTC / USD'].iloc[-1]:,.2f}"
    }

    return render_template('dashboard.html',
                         price_fomo_chart=price_fomo_chart,
                         gauge_chart=json.dumps(gauge_chart, cls=plotly.utils.PlotlyJSONEncoder),
                         additional_info=additional_info)

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

if __name__ == '__main__':
    prepare_data()  # Call the function to prepare data once
    app.run(debug=True) 