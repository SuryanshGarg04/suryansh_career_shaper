"""
Benchmark & Concurrency Stress Test Suite
Evaluates:
1. High-throughput telemetry ingestion latency (p50, p95, p99)
2. ACID race-condition prevention during concurrent vehicle dispatch attempts
"""

import time
import random
import concurrent.futures
import statistics
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_telemetry_throughput(total_requests=1000, max_workers=20):
    print(f"\n--- Running Benchmark 1: Telemetry Ingestion Throughput ({total_requests} reqs, {max_workers} threads) ---")
    latencies = []

    def send_ping(i):
        payload = {
            "vehicle_id": f"VEH{random.randint(1, 100):03d}",
            "latitude": 28.6139 + random.uniform(-1, 1),
            "longitude": 77.2090 + random.uniform(-1, 1),
            "speed_kmh": round(random.uniform(40, 80), 1),
            "fuel_pct": round(random.uniform(30, 90), 1)
        }
        t0 = time.perf_counter()
        res = requests.post(f"{BASE_URL}/telemetry/", json=payload, timeout=5.0)
        dt = (time.perf_counter() - t0) * 1000.0  # in ms
        return dt, res.status_code

    start_wall = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(send_ping, range(total_requests)))
    total_time = time.perf_counter() - start_wall

    success_count = sum(1 for _, code in results if code == 200)
    latencies = [dt for dt, code in results if code == 200]

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    throughput = success_count / total_time

    print(f"Results:")
    print(f"  Total Requests Processed: {success_count}/{total_requests}")
    print(f"  Elapsed Wall Time:        {total_time:.2f} s")
    print(f"  Calculated Throughput:     {throughput:.1f} requests/sec")
    print(f"  Latency p50:              {p50:.2f} ms")
    print(f"  Latency p95:              {p95:.2f} ms")
    print(f"  Latency p99:              {p99:.2f} ms")
    return throughput, p95

def test_dispatch_race_condition(concurrent_attempts=20):
    print(f"\n--- Running Benchmark 2: Concurrency Lock & Race Condition Prevention ({concurrent_attempts} simultaneous threads) ---")

    # 1. Create a test vehicle
    test_veh_id = f"VEH_RACE_{int(time.time())}"
    requests.post(f"{BASE_URL}/vehicles/", json={
        "vehicle_id": test_veh_id,
        "plate_number": f"DL-LOCK-{random.randint(1000, 9999)}",
        "vehicle_type": "Heavy_Truck",
        "max_weight_capacity_kg": 25000.0
    })

    # 2. Create multiple shipments
    shipment_ids = []
    for i in range(concurrent_attempts):
        res = requests.post(f"{BASE_URL}/shipments/", json={
            "origin_hub_id": "HUB_DEL",
            "dest_hub_id": "HUB_BOM",
            "weight_kg": 5000.0
        })
        if res.status_code == 200:
            shipment_ids.append(res.json()["shipment_id"])

    print(f"Created {len(shipment_ids)} shipments. Attempting simultaneous assignment to {test_veh_id}...")

    # 3. Fire simultaneous assignment threads to the SAME vehicle
    status_codes = []
    def attempt_assignment(s_id):
        res = requests.post(f"{BASE_URL}/shipments/{s_id}/assign", json={"vehicle_id": test_veh_id})
        return res.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_attempts) as executor:
        status_codes = list(executor.map(attempt_assignment, shipment_ids))

    successes = status_codes.count(200)
    conflicts = status_codes.count(409)

    print(f"Assignment Outcomes:")
    print(f"  Successful assignments (200 OK):      {successes} (MUST BE EXACTLY 1)")
    print(f"  Conflict rejections (409 Conflict):    {conflicts}")

    if successes == 1:
        print("  VERIFICATION PASSED: 0% Race conditions detected. Database row-level locking working correctly.")
    else:
        print("  VERIFICATION FAILED: Concurrency violation detected!")

if __name__ == "__main__":
    try:
        # Healthcheck
        res = requests.get(f"{BASE_URL}/analytics/overview", timeout=2.0)
        test_telemetry_throughput(total_requests=500, max_workers=15)
        test_dispatch_race_condition(concurrent_attempts=15)
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        print("Ensure the FastAPI server is running with: uvicorn app.main:app --port 8000")
