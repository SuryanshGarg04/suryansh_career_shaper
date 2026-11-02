from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("/", response_model=List[VehicleResponse])
def list_vehicles(
    status: Optional[str] = Query(None, description="AVAILABLE, ASSIGNED, IN_TRANSIT, MAINTENANCE"),
    vehicle_type: Optional[str] = Query(None, description="Heavy_Truck, Medium_Duty, Light_Van, Electric_Van"),
    db: Session = Depends(get_db)
):
    query = db.query(Vehicle)
    if status:
        query = query.filter(Vehicle.status == status.upper())
    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type == vehicle_type)
    return query.all()

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    veh = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not veh:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return veh

@router.post("/", response_model=VehicleResponse)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    existing = db.query(Vehicle).filter(Vehicle.vehicle_id == payload.vehicle_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle ID already exists")

    veh = Vehicle(
        vehicle_id=payload.vehicle_id,
        plate_number=payload.plate_number,
        vehicle_type=payload.vehicle_type,
        max_weight_capacity_kg=payload.max_weight_capacity_kg,
        status="AVAILABLE"
    )
    db.add(veh)
    db.commit()
    db.refresh(veh)
    return veh
