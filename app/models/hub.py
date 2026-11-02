from sqlalchemy import Column, String, Float, Integer
from app.database import Base

class Hub(Base):
    __tablename__ = "hubs"

    hub_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    city = Column(String(64), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity_limit = Column(Integer, default=500)
