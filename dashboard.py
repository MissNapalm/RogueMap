import sqlite3
import json
from datetime import datetime

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%m/%d/%Y %I:%M:%S %p').year
    except:
        return None

def main():
    # Connect to the database
    conn = sqlite3.connect('crimes.db')
    cursor = conn.cursor()

    # Get distinct crime types
    cursor.execute("""
        SELECT DISTINCT `Primary Type`
        FROM filtered_crimes
        ORDER BY `Primary Type`
    """)
    crime_types = [row[0] for row in cursor.fetchall()]

    # Query to get the required fields including the Arrest column
    cursor.execute("""
        SELECT `Primary Type`, Latitude, Longitude, Date, Block, Description, Arrest
        FROM filtered_crimes
        WHERE Latitude IS NOT NULL 
        AND Longitude IS NOT NULL
    """)
    crimes = cursor.fetchall()
    
    # Process data and add arrest status
    crime_data = {}
    for crime_type in crime_types:
        crime_data[crime_type] = {
            "crimes": [],
            "total_arrests": 0
        }
        for (ptype, lat, lng, date, block, desc, arrest) in crimes:
            if ptype == crime_type:
                crime_data[crime_type]["crimes"].append({
                    "lat": lat,
                    "lng": lng,
                    "date": date,
                    "year": parse_date(date),
                    "block": block,
                    "description": desc,
                    "arrest": "Yes" if arrest == 1 else "No"
                })
                if arrest == 1:
                    crime_data[crime_type]["total_arrests"] += 1

    conn.close()

    html = """
<!DOCTYPE html>
<html>
<head>
    <title>RogueHunter - Crime Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css"/>
    <style>
        body, html { 
            height: 100%; 
            margin: 0; 
            padding: 0;
            font-family: Arial, sans-serif;
        }
        
        /* Navigation Bar */
        .navbar {
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 2rem;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            box-sizing: border-box;
        }

        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav-logo {
            font-size: 1.8rem;
            font-weight: bold;
            color: #cc0000;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-image {
            height: auto;
            width: auto;
            max-height: 50px;
            object-fit: contain;
            vertical-align: middle;
        }

        .nav-logo:hover {
            color: #ff0000;
        }

        .nav-links {
            display: flex;
            gap: 2rem;
        }

        .nav-link {
            color: #333;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: all 0.3s ease;
        }

        .nav-link:hover {
            background-color: #ffeeee;
            color: #cc0000;
        }

        .nav-link.active {
            background-color: #cc0000;
            color: white;
        }

        /* Map Container */
        #container {
            display: flex;
            height: 100vh;
            padding-top: 80px; /* Increased to account for larger logo */
        }

        #map { 
            flex: 1;
            height: calc(100% - 80px); /* Adjusted for larger navbar */
        }

        #controls {
            width: 300px;
            padding: 20px;
            background: #fff;
            overflow-y: auto;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }

        .control-section {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ffcccc;
        }

        .year-filter {
            width: 100%;
            padding: 8px;
            margin-bottom: 15px;
            border: 1px solid #ff3333;
            border-radius: 4px;
            font-size: 14px;
            background-color: #fff;
            color: #333;
        }

        .view-toggle {
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }

        .view-toggle button {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 4px;
            background: #ffcccc;
            color: #cc0000;
            cursor: pointer;
            transition: all 0.2s;
        }

        .view-toggle button.active {
            background: #ff3333;
            color: white;
        }

        .crime-type {
            margin: 10px 0;
            padding: 10px;
            background: #fff;
            border: 1px solid #ffcccc;
            border-radius: 6px;
            transition: background-color 0.2s;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 5px;
        }

        .crime-type:hover {
            background: #fff5f5;
        }

        .crime-type label {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            width: 100%;
            cursor: pointer;
            color: #333;
        }

        .crime-type input[type="checkbox"] {
            flex: 0 0 auto;
            margin-right: 10px;
            accent-color: #ff3333;
        }

        .crime-type-text {
            flex: 1;
            text-align: left;
            white-space: normal;
            word-wrap
        }

        h2, h3 {
            margin-top: 0;
            color: #cc0000;
        }

        .count {
            font-size: 0.9em;
            color: #666;
        }

        .count-row {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-top: 4px;
            padding-top: 4px;
            border-top: 1px solid #ffcccc;
            font-size: 0.85em;
        }

        /* Custom marker cluster styles */
        .marker-cluster-small {
            background-color: rgba(255, 204, 204, 0.6) !important;
        }
        .marker-cluster-small div {
            background-color: rgba(255, 51, 51, 0.6) !important;
            color: white !important;
        }
        .marker-cluster-medium {
            background-color: rgba(255, 153, 153, 0.6) !important;
        }
        .marker-cluster-medium div {
            background-color: rgba(204, 0, 0, 0.6) !important;
            color: white !important;
        }
        .marker-cluster-large {
            background-color: rgba(255, 102, 102, 0.6) !important;
        }
        .marker-cluster-large div {
            background-color: rgba(153, 0, 0, 0.6) !important;
            color: white !important;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="index.html" class="nav-logo">
                <img src="logo.png" alt="RogueHunter Logo" class="logo-image">
                RogueHunter
            </a>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Home</a>
                <a href="crime_map.html" class="nav-link active">Crime Map</a>
                <a href="#" class="nav-link">Statistics</a>
                <a href="#" class="nav-link">About</a>
            </div>
        </div>
    </nav>

    <div id="container">
        <div id="controls">
            <div class="control-section">
                <h2>Filters</h2>
                <select id="yearFilter" class="year-filter">
                    <option value="all">All Years</option>
                    <option value="2020">2020</option>
                    <option value="2021">2021</option>
                    <option value="2022">2022</option>
                    <option value="2023">2023</option>
                    <option value="2024">2024</option>
                </select>
                
                <div class="view-toggle">
                    <button id="pointsView" class="active">Points</button>
                    <button id="heatmapView">Heatmap</button>
                </div>
            </div>
            
            <div class="control-section">
                <h3>Crime Types</h3>
"""

    # Add checkboxes for each crime type with total crime and arrest counts
    for crime_type in crime_types:
        html += f"""
                <div class="crime-type">
                    <label>
                        <input type="checkbox" name="crime-toggle" value="{crime_type}">
                        {crime_type}
                    </label>
                    <div class="count-row">
                        <span class="count" id="{crime_type}_count">Total: -</span>
                        <span class="count" id="{crime_type}_arrest_count">Arrests: -</span>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>
        <div id="map"></div>
    </div>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <script>
        const map = L.map('map').setView([41.8781, -87.6298], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        const crimeData = """ + json.dumps(crime_data) + """;
        const layers = {};
        const heatmaps = {};
        let currentYear = 'all';
        let isHeatmapMode = false;

        function formatPopup(crime, crimeType) {
            return `
                <div class="popup-content">
                    <div class="popup-title">${crimeType}</div>
                    <div class="popup-detail"><strong>Date:</strong> ${crime.date}</div>
                    <div class="popup-detail"><strong>Location:</strong> ${crime.block}</div>
                    <div class="popup-detail"><strong>Details:</strong> ${crime.description || 'Not provided'}</div>
                    <div class="popup-detail"><strong>Arrest Made:</strong> ${crime.arrest}</div>
                </div>
            `;
        }

        function createHeatmapData(crimeType) {
            return crimeData[crimeType]["crimes"]
                .filter(crime => currentYear === 'all' || crime.year === parseInt(currentYear))
                .map(crime => [crime.lat, crime.lng, 1]);
        }

        function updateVisualization() {
            Object.keys(crimeData).forEach(crimeType => {
                const checkbox = document.querySelector(`input[value="${crimeType}"]`);
                if (checkbox.checked) {
                    if (layers[crimeType]) map.removeLayer(layers[crimeType]);
                    if (heatmaps[crimeType]) map.removeLayer(heatmaps[crimeType]);

                    if (isHeatmapMode) {
                        heatmaps[crimeType] = L.heatLayer(createHeatmapData(crimeType), {
                            radius: 30,
                            blur: 20,
                            maxZoom: 15,
                            max: 1.0,
                            gradient: {
                                0.1: '#edf8fb',
                                0.2: '#bfd3e6',
                                0.3: '#9ebcda',
                                0.4: '#8c96c6',
                                0.5: '#8c6bb1',
                                0.6: '#88419d',
                                0.7: '#810f7c',
                                0.8: '#ce1256',
                                0.9: '#ef3b2c',
                                1.0: '#ff0000'
                            }
                        }).addTo(map);
                    } else {
                        layers[crimeType] = L.markerClusterGroup({
                            maxClusterRadius: 50,
                            spiderfyOnMaxZoom: true,
                            showCoverageOnHover: false,
                            zoomToBoundsOnClick: true
                        });

                        crimeData[crimeType]["crimes"]
                            .filter(crime => currentYear === 'all' || crime.year === parseInt(currentYear))
                            .forEach(crime => {
                                L.marker([crime.lat, crime.lng])
                                    .bindPopup(formatPopup(crime, crimeType))
                                    .addTo(layers[crimeType]);
                            });

                        map.addLayer(layers[crimeType]);
                    }
                }

                // Update crime and arrest counts
                const totalCrimes = crimeData[crimeType]["crimes"].filter(crime => 
                    currentYear === 'all' || crime.year === parseInt(currentYear)
                ).length;
                const totalArrests = crimeData[crimeType]["crimes"].filter(crime => 
                    (currentYear === 'all' || crime.year === parseInt(currentYear)) && crime.arrest === "Yes"
                ).length;

                document.getElementById(`${crimeType}_count`).textContent = `Total: ${totalCrimes}`;
                document.getElementById(`${crimeType}_arrest_count`).textContent = `Arrests: ${totalArrests}`;
            });
        }

        document.getElementById('yearFilter').addEventListener('change', function(e) {
            currentYear = e.target.value;
            updateVisualization();
        });

        document.getElementById('pointsView').addEventListener('click', function() {
            if (!isHeatmapMode) return;
            isHeatmapMode = false;
            this.classList.add('active');
            document.getElementById('heatmapView').classList.remove('active');
            updateVisualization();
        });

        document.getElementById('heatmapView').addEventListener('click', function() {
            if (isHeatmapMode) return;
            isHeatmapMode = true;
            this.classList.add('active');
            document.getElementById('pointsView').classList.remove('active');
            updateVisualization();
        });

        document.querySelectorAll('input[name="crime-toggle"]').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const crimeType = this.value;
                if (!this.checked) {
                    if (layers[crimeType]) map.removeLayer(layers[crimeType]);
                    if (heatmaps[crimeType]) map.removeLayer(heatmaps[crimeType]);
                } else {
                    updateVisualization();
                }
            });
        });

        updateVisualization();
    </script>
</body>
</html>
"""

    # Save the generated HTML to a file
    with open('crime_map.html', 'w') as f:
        f.write(html)

    print("\nMap has been generated as 'crime_map.html'")

if __name__ == '__main__':
    main()