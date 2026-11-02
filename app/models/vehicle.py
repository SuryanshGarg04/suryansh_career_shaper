from sqlalchemy import Column, String, Float
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(String(32), primary_key=True, index=True)
    plate_number = Column(String(32), unique=True, nullable=False)
    vehicle_type = Column(String(32), nullable=False)  # Heavy_Truck, Medium_Duty, Light_Van, Electric_Van
    max_weight_capacity_kg = Column(Float, nullable=False)
    status = Column(String(32), default="AVAILABLE", index=True)  # AVAILABLE, ASSIGNED, IN_TRANSIT, MAINTENANCE
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)
    fuel_pct = Column(Float, default=100.0)
    assigned_driver_id = Column(String(32), nullable=True)
