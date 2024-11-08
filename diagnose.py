import sqlite3
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.cluster import KMeans
import numpy as np

# Load data from the database
def load_data():
    conn = sqlite3.connect("crimes.db")
    query = """
        SELECT Date, Primary_Type AS crime_type, Latitude, Longitude
        FROM filtered_crimes
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """
    data = pd.read_sql_query(query, conn)
    conn.close()

    # Parse dates and add day-related columns
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])  # Drop rows with invalid dates
    data['day_of_week'] = data['Date'].dt.dayofweek
    data['is_weekend'] = data['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)

    return data

# Perform clustering on crime locations
def apply_clustering(data):
    kmeans = KMeans(n_clusters=5, random_state=0)
    data['cluster'] = kmeans.fit_predict(data[['Latitude', 'Longitude']])
    return data

# Encode crime types
def encode_crime_types(data):
    label_encoder = LabelEncoder()
    data['crime_type_encoded'] = label_encoder.fit_transform(data['crime_type'])
    return data

# Train the prediction model
def train_model(data):
    X = data[['day_of_week', 'is_weekend', 'cluster', 'crime_type_encoded']]
    y = data['crime_count'] if 'crime_count' in data else np.ones(len(X))  # Placeholder target variable

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(objective="reg:squarederror", random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"Mean Absolute Error: {mae}")
    return model

# Generate predictions for January 2024
def generate_january_predictions(data, model):
    january_data = pd.DataFrame({
        'day_of_week': range(7),
        'is_weekend': [1 if i >= 5 else 0 for i in range(7)],
    })

    # Expand to cover each cluster and crime type
    clusters = data['cluster'].unique()
    crime_types = data['crime_type_encoded'].unique()
    january_data = january_data.assign(cluster=np.repeat(clusters, len(january_data)),
                                       crime_type_encoded=np.tile(crime_types, len(january_data) * len(clusters) // len(crime_types)))
    
    # Predict crime counts
    january_data['predicted_crimes'] = model.predict(january_data[['day_of_week', 'is_weekend', 'cluster', 'crime_type_encoded']])
    return january_data

# Save predictions to a text file
def save_predictions_to_file(predictions):
    with open("predictions_analysis.txt", "w") as f:
        f.write("CRIME PREDICTION ANALYSIS FOR JANUARY 2024\n")
        f.write("="*40 + "\n\n")

        for index, row in predictions.iterrows():
            f.write(f"Day of Week: {row['day_of_week']}, Cluster: {row['cluster']}, Crime Type Encoded: {row['crime_type_encoded']}\n")
            f.write(f"  Predicted Crimes: {row['predicted_crimes']:.2f}\n")
            f.write("-" * 20 + "\n")

def main():
    data = load_data()
    data = apply_clustering(data)
    data = encode_crime_types(data)

    model = train_model(data)
    january_predictions = generate_january_predictions(data, model)
    save_predictions_to_file(january_predictions)

if __name__ == "__main__":
    main()
