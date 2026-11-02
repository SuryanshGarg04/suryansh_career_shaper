from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ShipmentBase(BaseModel):
    origin_hub_id: str
    dest_hub_id: str
    weight_kg: float = Field(..., gt=0, description="Payload weight in kg")
    priority: str = Field(default="STANDARD", description="STANDARD, EXPRESS, HIGH_PRIORITY")

class ShipmentCreate(ShipmentBase):
    shipment_id: Optional[str] = None

class ShipmentAssign(BaseModel):
    vehicle_id: str

class ShipmentTransition(BaseModel):
    new_status: str
    notes: Optional[str] = None

class ShipmentResponse(ShipmentBase):
    shipment_id: str
    status: str
    assigned_vehicle_id: Optional[str] = None
    created_at: datetime
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    current_eta_mins: int
    exception_reason: Optional[str] = None

    class Config:
        from_attributes = True
