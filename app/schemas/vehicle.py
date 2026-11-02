from typing import Optional
from pydantic import BaseModel, Field

class VehicleBase(BaseModel):
    vehicle_id: str
    plate_number: str
    vehicle_type: str
    max_weight_capacity_kg: float = Field(..., gt=0)

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    status: str
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    fuel_pct: float
    assigned_driver_id: Optional[str] = None

    class Config:
        from_attributes = True
