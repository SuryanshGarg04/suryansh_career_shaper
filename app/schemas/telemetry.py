from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TelemetryPing(BaseModel):
    vehicle_id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed_kmh: float = Field(..., ge=0.0, le=180.0)
    fuel_pct: float = Field(..., ge=0.0, le=100.0)
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None

class TelemetryResponse(TelemetryPing):
    id: int
    timestamp: datetime
    anomaly_flag: str

    class Config:
        from_attributes = True

class BatchTelemetryIngest(BaseModel):
    pings: list[TelemetryPing]
