import math
from typing import Tuple

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on earth in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(R * c, 2)

def is_point_near_corridor(
    point: Tuple[float, float],
    origin: Tuple[float, float],
    dest: Tuple[float, float],
    tolerance_km: float = 40.0
) -> bool:
    """
    Evaluates whether a point lies within an elliptical corridor buffer between origin and destination.
    """
    dist_total = haversine_distance_km(origin[0], origin[1], dest[0], dest[1])
    dist_to_origin = haversine_distance_km(point[0], point[1], origin[0], origin[1])
    dist_to_dest = haversine_distance_km(point[0], point[1], dest[0], dest[1])

    # In an ideal straight transit, dist_to_origin + dist_to_dest ~= dist_total
    # If the vehicle deviates significantly, this sum exceeds dist_total + tolerance
    return (dist_to_origin + dist_to_dest) <= (dist_total + tolerance_km * 1.5)

def detect_telemetry_anomaly(speed_kmh: float, fuel_pct: float, previous_fuel_pct: float = None) -> str:
    """
    Heuristic rule engine for operational exception detection.
    """
    if speed_kmh > 95.0:
        return "Speeding_Violation"
    if fuel_pct < 10.0:
        return "Low_Fuel_Warning"
    if previous_fuel_pct is not None and (previous_fuel_pct - fuel_pct) > 25.0:
        return "Fuel_Theft_Or_Leak"
    if speed_kmh == 0.0:
        return "Idle_Or_Stationary"
    return "None"
