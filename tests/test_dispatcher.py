from app.services.geofence import haversine_distance_km, detect_telemetry_anomaly

def test_haversine_distance():
    # Delhi to Mumbai distance (~1150 km great circle)
    dist = haversine_distance_km(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1100.0 < dist < 1250.0

def test_telemetry_anomaly_detection():
    # Speeding anomaly
    assert detect_telemetry_anomaly(speed_kmh=110.0, fuel_pct=80.0) == "Speeding_Violation"

    # Low fuel anomaly
    assert detect_telemetry_anomaly(speed_kmh=60.0, fuel_pct=5.0) == "Low_Fuel_Warning"

    # Normal conditions
    assert detect_telemetry_anomaly(speed_kmh=65.0, fuel_pct=75.0) == "None"
