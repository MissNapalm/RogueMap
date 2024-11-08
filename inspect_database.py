import pandas as pd
import sqlite3

def process_data(data):
    # Check if the data frame is empty before processing
    if data.empty:
        print("Data retrieved from database is empty.")
        return data

    # Convert date to datetime and check for parsing issues
    try:
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    except Exception as e:
        print("Error during date conversion:", e)
        return pd.DataFrame()  # Return an empty DataFrame if there's an issue

    # Drop rows where 'Date' could not be parsed
    data.dropna(subset=['Date'], inplace=True)
    
    if data.empty:
        print("Data is empty after date parsing. Check date formats in the database.")
        return data

    # Extract year, month, and day of week as features
    data['year'] = data['Date'].dt.year
    data['month'] = data['Date'].dt.month
    data['day_of_week'] = data['Date'].dt.dayofweek
    data['is_weekend'] = data['day_of_week'].isin([5, 6]).astype(int)
    data['day_of_year'] = data['Date'].dt.dayofyear
    data['quarter'] = data['Date'].dt.quarter

    print("Data processing complete.")
    return data

print("Connecting to the database and retrieving data...")
conn = sqlite3.connect('crimes.db')

query = """
SELECT Date, "Primary Type" AS primary_type, Block
FROM filtered_crimes 
WHERE Date >= '2022-01-01' AND Date < '2024-02-01'
"""

data = pd.read_sql(query, conn)
conn.close()

# Check if any data was retrieved
if data.empty:
    print("No data retrieved from database. Check the database or query.")
else:
    print(f"Retrieved {len(data)} rows from the database.")

print("Processing data...")
data = process_data(data)

# Display the first few rows to confirm
if not data.empty:
    print("Sample of processed data:")
    print(data.head())
