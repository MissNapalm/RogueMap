import dask.dataframe as dd
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import sqlite3

# Load data from crimes.db
conn = sqlite3.connect('crimes.db')
query = """
    SELECT * FROM filtered_crimes
"""
df_pd = pd.read_sql(query, conn, index_col='ID')
conn.close()

# Convert Pandas DataFrame to Dask DataFrame
df = dd.from_pandas(df_pd)

# Print column names
print(df.columns)

# Preprocess data
df['Date'] = dd.to_datetime(df['Date'], format='%m/%d/%Y %I:%M:%S %p')
df['Month'] = df['Date'].dt.month
df['Year'] = df['Date'].dt.year

# Encode categorical columns using LabelEncoder
categorical_features = ['Case Number', 'Block', 'IUCR', 'Description', 'Location Description', 'FBI Code', 'Updated On', 'Location']
for feature in categorical_features:
    # Handle missing values
    df[feature] = df[feature].fillna('Unknown')
    
    # Encode the column
    le = LabelEncoder()
    encoded_feature = le.fit_transform(df[feature].compute().values)
    df[feature] = dd.from_pandas(pd.Series(encoded_feature).astype(int))

# Encode the 'Primary Type' column
df['Primary Type'] = df['Primary Type'].fillna('Unknown')
le = LabelEncoder()
encoded_feature = le.fit_transform(df['Primary Type'].compute().values)
df['Primary Type'] = dd.from_pandas(pd.Series(encoded_feature).astype(int))

# Split data into training and testing sets
train_df, test_df = df.random_split([0.8, 0.2], random_state=42)

# Define XGBoost model
xgb_model = xgb.XGBClassifier(objective='multi:softmax', num_class=len(df['Primary Type'].unique().compute()))

# Train model on training data
xgb_model.fit(train_df.drop(['Date', 'Month', 'Year', 'Primary Type'], axis=1).compute(), train_df['Primary Type'].compute())

# Make predictions for November 2024
nov_2024_df = test_df[test_df['Year'] == 2024]
nov_2024_df = nov_2024_df[nov_2024_df['Month'] == 11]
predictions = xgb_model.predict(nov_2024_df.drop(['Date', 'Month', 'Year', 'Primary Type'], axis=1).compute())

# Compare predictions with actual values
accuracy = accuracy_score(nov_2024_df['Primary Type'].compute(), predictions)
print(f"Accuracy: {accuracy:.3f}")

# Print comparison of predictions and actual values to a txt file
with open('comparison.txt', 'w') as f:
    f.write("Predicted vs Actual Crimes for November 2024\n")
    for i, row in nov_2024_df.iterrows():
        f.write(f"Predicted: {predictions[i]}, Actual: {row['Primary Type']}\n")