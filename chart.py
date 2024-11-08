import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def main():
    # Connect to database
    conn = sqlite3.connect('crimes.db')
    
    # Query to get relevant crimes and their times
    query = """
    SELECT 
        `Primary Type`,
        Date
    FROM filtered_crimes
    WHERE `Primary Type` IN (
        'OFFENSE INVOLVING CHILDREN',
        'CRIMINAL SEXUAL ASSAULT'
    )
    """
    
    # Read data into DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Convert Date string to datetime and extract hour
    df['Hour'] = df['Date'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y %I:%M:%S %p').hour)
    
    # Create separate series for each crime type
    children_crimes = df[df['Primary Type'] == 'OFFENSE INVOLVING CHILDREN']['Hour'].value_counts().sort_index()
    sexual_assault = df[df['Primary Type'] == 'CRIMINAL SEXUAL ASSAULT']['Hour'].value_counts().sort_index()
    
    # Create the plot
    plt.figure(figsize=(15, 8))
    
    # Create line plots with different colors and styles
    plt.plot(children_crimes.index, children_crimes.values, 
             color='#2ecc71', marker='o', linewidth=2, 
             label='Offenses Involving Children')
    plt.plot(sexual_assault.index, sexual_assault.values, 
             color='#e74c3c', marker='o', linewidth=2, 
             label='Criminal Sexual Assault')
    
    # Customize the plot
    plt.title('Distribution of Crimes by Time of Day', fontsize=16, pad=20)
    plt.xlabel('Hour of Day (24-hour format)', fontsize=12)
    plt.ylabel('Number of Incidents', fontsize=12)
    
    # Add grid with custom style
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # Customize legend
    plt.legend(fontsize=10, framealpha=0.9)
    
    # Set x-axis ticks for every hour
    plt.xticks(range(0, 24), [f'{i:02d}:00' for i in range(24)], rotation=45)
    
    # Set background color
    plt.gca().set_facecolor('#f8f9fa')
    plt.gca().patch.set_alpha(0.3)
    
    # Add some padding to the layout
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('crimes_by_time.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print("\nGraph has been saved as 'crimes_by_time.png'")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("\nOffenses Involving Children:")
    print(f"Peak hour: {children_crimes.idxmax():02d}:00 with {children_crimes.max()} incidents")
    print(f"Lowest hour: {children_crimes.idxmin():02d}:00 with {children_crimes.min()} incidents")
    
    print("\nCriminal Sexual Assault:")
    print(f"Peak hour: {sexual_assault.idxmax():02d}:00 with {sexual_assault.max()} incidents")
    print(f"Lowest hour: {sexual_assault.idxmin():02d}:00 with {sexual_assault.min()} incidents")
    
    conn.close()

if __name__ == '__main__':
    main()