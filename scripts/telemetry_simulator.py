"""
Real-time Telemetry Simulator
Simulates active vehicle movement along highway corridors and streams live pings to the API.
"""

import time
import random
import requests

API_URL = "http://localhost:8000/api/v1/telemetry/"

HUBS = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639}
]

def run_simulation(duration_seconds=60, ping_delay=0.5):
    print(f"Starting real-time telemetry simulation for {duration_seconds} seconds...")
    print(f"Target API: {API_URL}")

    start_time = time.time()
    pings_sent = 0

    while time.time() - start_time < duration_seconds:
        veh_num = random.randint(1, 50)
        veh_id = f"VEH{veh_num:03d}"
        hub = random.choice(HUBS)

        # Interpolate small movements
        lat = hub["lat"] + random.uniform(-0.8, 0.8)
        lon = hub["lon"] + random.uniform(-0.8, 0.8)
        speed = round(random.uniform(40.0, 85.0), 1)
        fuel = round(random.uniform(25.0, 95.0), 1)

        payload = {
            "vehicle_id": veh_id,
            "latitude": lat,
            "longitude": lon,
            "speed_kmh": speed,
            "fuel_pct": fuel,
            "notes": "Simulated GPS packet"
        }

        try:
            resp = requests.post(API_URL, json=payload, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                anomaly = data.get("anomaly_flag", "None")
                flag_str = f" [ALERT: {anomaly}]" if anomaly != "None" else ""
                print(f"[{pings_sent+1}] Ingested {veh_id} @ ({lat:.3f}, {lon:.3f}) - Speed {speed} km/h{flag_str}")
                pings_sent += 1
            else:
                print(f"Failed ping ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"Connection error: {e}. Is the FastAPI server running on http://localhost:8000?")
            time.sleep(2)

        time.sleep(ping_delay)

    print(f"Simulation completed. Sent {pings_sent} telemetry packets.")

if __name__ == "__main__":
    run_simulation()
