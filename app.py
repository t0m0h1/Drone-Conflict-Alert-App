from flask import Flask, render_template, jsonify, request
import requests
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

# Haversine function
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

# Fetch aircraft from ADSB Exchange
def fetch_aircraft(lat, lon, distance_km=10):
    url = f"https://public-api.adsbexchange.com/VirtualRadar/AircraftList.json?lat={lat}&lng={lon}&fDstL={distance_km}"
    headers = {'User-Agent': 'DroneAlertApp/1.0'}  # some APIs require this
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # raise HTTPError for bad responses
        data = response.json()
        return data.get('acList', [])
    except requests.exceptions.JSONDecodeError:
        print(" Received invalid JSON from ADSB Exchange")
        return []
    except requests.exceptions.RequestException as e:
        print(f" Request failed: {e}")
        return []



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_aircraft', methods=['POST'])
def check_aircraft():
    data = request.json
    operator_lat = data.get('lat')
    operator_lon = data.get('lon')
    radius_km = data.get('radius', 2)
    altitude_limit_ft = data.get('alt_limit', 2000)

    aircraft_list = fetch_aircraft(operator_lat, operator_lon)
    alerts = []

    for ac in aircraft_list:
        ac_lat = ac.get('Lat')
        ac_lon = ac.get('Long')
        ac_alt_ft = ac.get('Alt', 0)
        if ac_lat is None or ac_lon is None:
            continue

        distance = haversine(operator_lat, operator_lon, ac_lat, ac_lon)

        if distance <= radius_km or ac_alt_ft <= altitude_limit_ft:
            alerts.append({
                "call": ac.get('Call', 'N/A'),
                "distance_km": round(distance, 2),
                "altitude_ft": ac_alt_ft
            })

    return jsonify({"alerts": alerts})

if __name__ == "__main__":
    app.run(debug=True)
