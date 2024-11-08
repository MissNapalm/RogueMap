import pandas as pd
import sqlite3

# Load the CSV file
data = pd.read_csv('crime_data.csv')

# Filter data for the years 2020 to 2024 and the specified primary types
filtered_data = data[
    (import pandas as pd
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    
    # Load data from crimes.db
    df = pd.read_sql_query("SELECT * FROM crimes", "sqlite:///crimes.db")
    
    # Preprocess data
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    
    # Split data into training and testing sets
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Define XGBoost model
    xgb_model = xgb.XGBClassifier(objective='multi:softmax', num_class=10)
    
    # Train model on training data
    xgb_model.fit(train_df.drop('crime_type', axis=1), train_df['crime_type'])
    
    # Make predictions for November 2024
    nov_2024_df = test_df[test_df['year'] == 2024]
    nov_2024_df = nov_2024_df[nov_2024_df['month'] == 11]
    predictions = xgb_model.predict(nov_2024_df.drop('crime_type', axis=1))
    
    # Compare predictions with actual values
    accuracy = accuracy_score(nov_2024_df['crime_type'], predictions)
    print(f"Accuracy: {accuracy:.3f}")
    
    # Print comparison of predictions and actual values to a txt file
    with open('comparison.txt', 'w') as f:
        f.write("Predicted vs Actual Crimes for November 2024\n")
        for i, row in nov_2024_df.iterrows():
            f.write(f"Predicted: {predictions[i]}, Actual: {row['crime_type']}\n")data['Year'].between(2020, 2024)) & 
    (data['Primary Type'].isin([
        'HOMICIDE', 
        'CRIMINAL SEXUAL ASSAULT', 
        'OFFENSE INVOLVING CHILDREN', 
        'HUMAN TRAFFICKING', 
        'BURGLARY', 
        'ARSON'
    ]))
]

# Connect to (or create) the SQLite database
conn = sqlite3.connect('crimes.db')

# Save filtered data to a new table in the database
filtered_data.to_sql('filtered_crimes', conn, if_exists='replace', index=False)

# Close the connection
conn.close()

print("Data has been filtered and saved to 'crimes.db' in the 'filtered_crimes' table.")
