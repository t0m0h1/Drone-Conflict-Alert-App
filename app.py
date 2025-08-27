from flask import Flask, render_template, jsonify, request
import requests
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

# Haversine formula to calculate distance between two coordinates (in km)
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # Earth radius in km

# Fetch aircraft from ADSB.lol API
def fetch_aircraft(lat, lon, radius_km=10):
    url = f"https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{radius_km}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        print("Raw API response:", data)

        aircraft_list = data.get('ac', [])
        print(f"Number of aircraft detected: {len(aircraft_list)}")
        return aircraft_list

    except requests.exceptions.RequestException as e:
        print(f"ADSB.lol API request error: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Check aircraft route
@app.route('/check_aircraft', methods=['POST'])
def check_aircraft():
    data = request.json
    try:
        operator_lat = float(data.get('lat'))
        operator_lon = float(data.get('lon'))
        radius_km = float(data.get('radius', 5))
        altitude_limit_ft = float(data.get('alt_limit', 5000))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing lat/lon/radius/alt_limit"}), 400

    aircraft_list = fetch_aircraft(operator_lat, operator_lon, radius_km)
    alerts = []

    for ac in aircraft_list:
        ac_lat = ac.get('lat')
        ac_lon = ac.get('lon')
        ac_alt_ft = ac.get('alt_baro', 0)
        ac_call = ac.get('flight', '').strip() or ac.get('r', 'N/A')

        if ac_lat is None or ac_lon is None:
            continue

        distance = haversine(operator_lat, operator_lon, ac_lat, ac_lon)
        # Alert only if distance < 10km and altitude <= 3000ft
        status = "alert" if distance < 10 and ac_alt_ft <= 3000 else "normal"

        alerts.append({
            "call": ac_call,
            "lat": ac_lat,
            "lon": ac_lon,
            "altitude_ft": ac_alt_ft,
            "distance_km": round(distance, 2),
            "status": status
        })

    # Optional: sort alerts by distance
    alerts.sort(key=lambda x: x['distance_km'])

    return jsonify({"alerts": alerts})

if __name__ == "__main__":
    app.run(debug=True)
