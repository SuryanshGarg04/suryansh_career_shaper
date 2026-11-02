"""
Database Seeding Script
Populates the database with 10 Hubs, 250 Vehicles, 100 Drivers, and 200 Initial Shipments.
"""

import sys
import os
import random

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base, SessionLocal
from app.models.hub import Hub
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.main import DEFAULT_HUBS

VEHICLE_TYPES = [
    ("Heavy_Truck", 28000),
    ("Medium_Duty", 12000),
    ("Light_Van", 3500),
    ("Electric_Van", 2200)
]

DRIVER_NAMES = [
    "Rajesh Kumar", "Amit Singh", "Vikram Patel", "Suresh Sharma", "Manoj Verma",
    "Deepak Yadav", "Ramesh Chand", "Anil Gupta", "Sunil Joshi", "Praveen Rao",
    "Dinesh Mehta", "Ashok Tiwari", "Sanjay Chauhan", "Gopal Mishra", "Vijay Thapar"
]

def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Hubs
        print(f"Seeding {len(DEFAULT_HUBS)} logistics hubs...")
        for hub_data in DEFAULT_HUBS:
            if not db.query(Hub).filter(Hub.hub_id == hub_data["hub_id"]).first():
                db.add(Hub(**hub_data))
        db.commit()

        # 2. Seed 250 Vehicles
        print("Seeding 250 commercial vehicles...")
        for i in range(1, 251):
            v_id = f"VEH{i:03d}"
            if not db.query(Vehicle).filter(Vehicle.vehicle_id == v_id).first():
                v_type, cap = VEHICLE_TYPES[i % len(VEHICLE_TYPES)]
                hub = DEFAULT_HUBS[i % len(DEFAULT_HUBS)]
                db.add(Vehicle(
                    vehicle_id=v_id,
                    plate_number=f"DL-01-FL-{2000+i}",
                    vehicle_type=v_type,
                    max_weight_capacity_kg=cap,
                    status="AVAILABLE",
                    current_lat=hub["latitude"] + random.uniform(-0.15, 0.15),
                    current_lon=hub["longitude"] + random.uniform(-0.15, 0.15),
                    fuel_pct=round(random.uniform(40.0, 98.0), 1)
                ))
        db.commit()

        # 3. Seed 100 Drivers
        print("Seeding 100 professional drivers...")
        for i in range(1, 101):
            d_id = f"DRV{i:03d}"
            if not db.query(Driver).filter(Driver.driver_id == d_id).first():
                name = f"{random.choice(DRIVER_NAMES)} ({d_id})"
                db.add(Driver(
                    driver_id=d_id,
                    name=name,
                    license_no=f"DL-COMM-{8000+i}",
                    duty_status="ON_DUTY",
                    duty_hours_today=random.randint(1, 6)
                ))
        db.commit()

        # 4. Seed initial shipments
        print("Seeding 50 initial sample shipments...")
        for i in range(1, 51):
            s_id = f"SHP{10000+i}"
            if not db.query(Shipment).filter(Shipment.shipment_id == s_id).first():
                origin = random.choice(DEFAULT_HUBS)["hub_id"]
                dest = random.choice([h["hub_id"] for h in DEFAULT_HUBS if h["hub_id"] != origin])
                weight = round(random.uniform(300.0, 15000.0), 1)
                db.add(Shipment(
                    shipment_id=s_id,
                    origin_hub_id=origin,
                    dest_hub_id=dest,
                    weight_kg=weight,
                    status="CREATED",
                    priority="STANDARD" if i % 4 != 0 else "EXPRESS",
                    current_eta_mins=random.randint(120, 720)
                ))
        db.commit()

        print("Database seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
