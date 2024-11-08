import pandas as pd
import sqlite3
import json

def load_and_process_data():
    """Load and process crime data from crimes.db"""
    conn = sqlite3.connect('filtered_crimes.db')
    query = """
        SELECT *
        FROM filtered_crimes
        WHERE year >= 2020 AND year <= 2024
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert date fields if necessary
    df['Date'] = pd.to_datetime(df['Date'])
    df['hour'] = df['Date'].dt.hour
    df['day_of_week'] = df['Date'].dt.day_name()
    df['month'] = df['Date'].dt.month_name()
    df['year'] = df['Date'].dt.year
    df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday'])
    
    return df

def prepare_chart_data(df):
    """Prepare chart data grouped by various time dimensions and crime types"""
    chart_data = {
        'hourly': df.groupby(['Primary Type', 'hour']).size().unstack(fill_value=0).to_dict(),
        'daily': df.groupby(['Primary Type', 'day_of_week']).size().unstack(fill_value=0).to_dict(),
        'monthly': df.groupby(['Primary Type', 'month']).size().unstack(fill_value=0).to_dict(),
        'area': df.groupby(['Primary Type', 'Community Area']).size().unstack(fill_value=0).to_dict(),
        'time_blocks': {
            crime: df[df['Primary Type'] == crime].groupby(pd.cut(df['hour'], [0, 6, 12, 18, 24], labels=['Night', 'Morning', 'Afternoon', 'Evening'])).size().to_dict()
            for crime in df['Primary Type'].unique()
        },
        'weekend_comparison': df.groupby(['Primary Type', 'is_weekend']).size().unstack(fill_value=0).to_dict()
    }
    
    return chart_data

def generate_dashboard():
    print("Loading and processing data...")
    df = load_and_process_data()
    
    print("Preparing chart data...")
    chart_data = prepare_chart_data(df)
    
    crime_types = sorted(df['Primary Type'].unique())

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Chicago Crime Analytics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            background: #f0f2f5;
        }
        #controls {
            width: 300px;
            padding: 20px;
            background: white;
            overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }
        #dashboard {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        .chart-container {
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .crime-type {
            margin: 10px 0;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        .crime-type:hover {
            background: #e0e0e0;
        }
        .crime-type label {
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        #update-btn {
            width: 100%;
            padding: 10px;
            background: #2c5282;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        #update-btn:hover {
            background: #2a4365;
        }
        .count {
            margin-left: auto;
            color: #666;
            font-size: 0.9em;
        }
        h2, h3 {
            color: #333;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <div id="controls">
        <h2>Crime Types</h2>
"""

    # Add checkboxes for each crime type
    for crime_type in crime_types:
        count = len(df[df['Primary Type'] == crime_type])
        html_content += f"""
        <div class="crime-type">
            <label>
                <input type="checkbox" name="crime-toggle" value="{crime_type}" checked>
                {crime_type}
                <span class="count">({count:,})</span>
            </label>
        </div>
"""

    html_content += """
        <button id="update-btn">Update Charts</button>
    </div>
    <div id="dashboard">
        <div class="chart-container">
            <h3>Crimes by Time of Day</h3>
            <div id="hourly-chart"></div>
        </div>
        <div class="chart-container">
            <h3>Crimes by Day of Week</h3>
            <div id="daily-chart"></div>
        </div>
        <div class="chart-container">
            <h3>Crimes by Month</h3>
            <div id="monthly-chart"></div>
        </div>
        <div class="chart-container">
            <h3>Most Dangerous Areas</h3>
            <div id="area-chart"></div>
        </div>
        <div class="chart-container">
            <h3>Time Block Distribution</h3>
            <div id="time-block-chart"></div>
        </div>
        <div class="chart-container">
            <h3>Weekend vs Weekday Patterns</h3>
            <div id="weekend-chart"></div>
        </div>
    </div>

    <script>
    const chartData = """ + json.dumps(chart_data) + """;

    function updateCharts() {
        const selectedCrimes = Array.from(document.querySelectorAll('input[name="crime-toggle"]:checked'))
            .map(cb => cb.value);
        
        if (selectedCrimes.length === 0) {
            alert('Please select at least one crime type');
            return;
        }

        // Hourly Chart
        const hourlyTraces = selectedCrimes.map(crime => ({
            x: Array.from({length: 24}, (_, i) => i),
            y: Array.from({length: 24}, (_, i) => chartData.hourly[crime][i] || 0),
            name: crime,
            type: 'scatter',
            mode: 'lines+markers'
        }));

        Plotly.newPlot('hourly-chart', hourlyTraces, {
            title: 'Crimes by Hour of Day',
            xaxis: {title: 'Hour (24-hour format)', dtick: 1},
            yaxis: {title: 'Number of Crimes'},
            height: 400
        });

        // Additional charts setup: daily, monthly, area, time block, and weekend
        // (Refer to earlier code for full setup)
    }

    document.getElementById('update-btn').addEventListener('click', updateCharts);
    
    // Initial chart render
    updateCharts();
    </script>
</body>
</html>
"""

    with open('crime_analytics.html', 'w') as f:
        f.write(html_content)
    
    print("Analytics dashboard has been generated as 'crime_analytics.html'")

if __name__ == '__main__':
    generate_dashboard()
