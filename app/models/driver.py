from sqlalchemy import Column, String, Integer
from app.database import Base

class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    license_no = Column(String(64), unique=True, nullable=False)
    duty_status = Column(String(32), default="ON_DUTY")  # ON_DUTY, OFF_DUTY, RESTING
    duty_hours_today = Column(Integer, default=0)
    assigned_vehicle_id = Column(String(32), nullable=True)
