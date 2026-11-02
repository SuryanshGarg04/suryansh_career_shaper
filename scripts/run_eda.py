"""
Exploratory Data Analysis (EDA) Script
Processes dataset.csv, generates summary statistics, and outputs visualizations.
Deliverable for HCLTech Career Shaper Programme.
"""

import os
import csv
from collections import Counter, defaultdict

DATASET_PATH = "dataset.csv"
OUTPUT_DIR = "eda_reports"

def run_eda():
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset not found at '{DATASET_PATH}'. Please ensure dataset.csv is in the project root.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Reading {DATASET_PATH} for Exploratory Data Analysis...")

    total_rows = 0
    vehicle_types = Counter()
    status_counts = Counter()
    anomaly_counts = Counter()
    delays = []
    distances = []
    fuels = []
    payloads = []
    payload_by_type = defaultdict(list)

    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            v_type = row["vehicle_type"]
            vehicle_types[v_type] += 1
            status_counts[row["shipment_status"]] += 1
            anomaly_counts[row["anomaly_flag"]] += 1

            d_km = float(row["distance_km"])
            p_kg = float(row["payload_kg"])
            f_l = float(row["fuel_consumed_l"])
            delay = int(row["transit_delay_mins"])

            distances.append(d_km)
            payloads.append(p_kg)
            fuels.append(f_l)
            delays.append(delay)
            payload_by_type[v_type].append(p_kg)

    print("\n" + "="*50)
    print("       LOGISTICS & FLEET DATASET EDA SUMMARY       ")
    print("="*50)
    print(f"Total Transit Records Analyzed: {total_rows:,}")
    print(f"Average Corridor Distance:      {sum(distances)/total_rows:.1f} km (Max: {max(distances):.1f} km)")
    print(f"Average Cargo Payload:          {sum(payloads)/total_rows:,.1f} kg")
    print(f"Average Trip Delay:             {sum(delays)/total_rows:.1f} mins (Anomalous trips only: {sum(d for d in delays if d > 0)/max(1, sum(1 for d in delays if d > 0)):.1f} mins)")
    print(f"Total Fuel Consumed (Diesel):   {sum(fuels):,.1f} Litres")

    print("\n--- Fleet Vehicle Distribution ---")
    for v_type, cnt in vehicle_types.most_common():
        avg_p = sum(payload_by_type[v_type]) / len(payload_by_type[v_type])
        pct = (cnt / total_rows) * 100
        print(f"  {v_type:<14}: {cnt:>5} trips ({pct:>5.1f}%) | Avg Payload: {avg_p:>8.1f} kg")

    print("\n--- Shipment Delivery Status ---")
    for st, cnt in status_counts.most_common():
        pct = (cnt / total_rows) * 100
        print(f"  {st:<14}: {cnt:>5} ({pct:>5.1f}%)")

    print("\n--- Transit Anomaly Frequency ---")
    for anom, cnt in anomaly_counts.most_common():
        pct = (cnt / total_rows) * 100
        print(f"  {anom:<20}: {cnt:>5} ({pct:>5.1f}%)")

    # Generate Text/SVG Summary Artifact
    generate_svg_chart(anomaly_counts, os.path.join(OUTPUT_DIR, "anomaly_distribution.svg"))
    print(f"\nSaved visualization to {OUTPUT_DIR}/anomaly_distribution.svg")
    print("="*50)

def generate_svg_chart(counter_data, filepath):
    """Generates a standalone clean SVG bar chart of anomaly distribution."""
    width = 600
    height = 280
    margin_left = 180
    margin_bottom = 40
    chart_w = width - margin_left - 40
    chart_h = height - margin_bottom - 40

    items = counter_data.most_common(5)
    max_val = max(v for _, v in items) if items else 1
    bar_h = chart_h / (len(items) * 1.5)

    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; font-family:sans-serif;">',
        f'<text x="{width/2}" y="25" fill="#f8fafc" font-size="14" font-weight="bold" text-anchor="middle">Operational Transit Anomalies Frequency</text>'
    ]

    for i, (label, val) in enumerate(items):
        y = 50 + i * (bar_h * 1.5)
        bar_len = (val / max_val) * chart_w
        color = "#ef4444" if label != "None" else "#10b981"

        svg.append(f'<text x="{margin_left - 10}" y="{y + bar_h*0.75}" fill="#cbd5e1" font-size="11" text-anchor="end">{label}</text>')
        svg.append(f'<rect x="{margin_left}" y="{y}" width="{bar_len}" height="{bar_h}" fill="{color}" rx="4"/>')
        svg.append(f'<text x="{margin_left + bar_len + 8}" y="{y + bar_h*0.75}" fill="#f8fafc" font-size="11" font-weight="bold">{val:,}</text>')

    svg.append('</svg>')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    run_eda()
