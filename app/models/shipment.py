from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(String(32), primary_key=True, index=True)
    origin_hub_id = Column(String(32), ForeignKey("hubs.hub_id"), nullable=False)
    dest_hub_id = Column(String(32), ForeignKey("hubs.hub_id"), nullable=False)
    weight_kg = Column(Float, nullable=False)
    status = Column(String(32), default="CREATED", index=True)  # CREATED, ASSIGNED, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, EXCEPTION_FLAGGED
    priority = Column(String(16), default="STANDARD")  # STANDARD, EXPRESS, HIGH_PRIORITY
    assigned_vehicle_id = Column(String(32), ForeignKey("vehicles.vehicle_id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    current_eta_mins = Column(Integer, default=0)
    exception_reason = Column(String(256), nullable=True)
