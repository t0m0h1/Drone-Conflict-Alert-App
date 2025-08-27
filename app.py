from flask import Flask, render_template, jsonify, request
import requests
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # km

def fetch_aircraft(lat, lon, radius_km=10):
    url = f"https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{radius_km}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('aircraft', [])  # adjust based on actual JSON structure
    except Exception as e:
        print(f" ADSB.lol API error: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_aircraft', methods=['POST'])
def check_aircraft():
    data = request.json
    operator_lat = data.get('lat')
    operator_lon = data.get('lon')
    radius_km = data.get('radius', 5)
    altitude_limit_ft = data.get('alt_limit', 5000)

    aircraft_list = fetch_aircraft(operator_lat, operator_lon, radius_km)
    alerts = []

    for ac in aircraft_list:
        ac_lat = ac.get('lat')
        ac_lon = ac.get('lon')
        ac_alt_ft = ac.get('alt', 0)
        if ac_lat is None or ac_lon is None:
            continue

        distance = haversine(operator_lat, operator_lon, ac_lat, ac_lon)
        status = "alert" if distance <= radius_km or ac_alt_ft <= altitude_limit_ft else "normal"

        alerts.append({
            "call": ac.get('call', 'N/A'),
            "lat": ac_lat,
            "lon": ac_lon,
            "altitude_ft": ac_alt_ft,
            "distance_km": round(distance, 2),
            "status": status
        })

    return jsonify({"alerts": alerts})

if __name__ == "__main__":
    app.run(debug=True)
