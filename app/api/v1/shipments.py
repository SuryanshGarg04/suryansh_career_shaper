import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.shipment import Shipment
from app.models.hub import Hub
from app.schemas.shipment import (
    ShipmentCreate, ShipmentAssign, ShipmentTransition, ShipmentResponse
)
from app.services.fsm import ShipmentLifecycleFSM
from app.services.dispatcher import DispatchEngine
from app.services.geofence import haversine_distance_km
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.post("/", response_model=ShipmentResponse)
async def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    # Verify hubs
    origin = db.query(Hub).filter(Hub.hub_id == payload.origin_hub_id).first()
    dest = db.query(Hub).filter(Hub.hub_id == payload.dest_hub_id).first()
    if not origin or not dest:
        raise HTTPException(status_code=404, detail="Invalid origin or destination hub ID")

    shipment_id = payload.shipment_id or f"SHP{str(uuid.uuid4())[:8].upper()}"

    # Calculate base ETA from distance
    dist = haversine_distance_km(origin.latitude, origin.longitude, dest.latitude, dest.longitude)
    eta_mins = int((dist / 55.0) * 60)  # Average 55 km/h transit speed

    shipment = Shipment(
        shipment_id=shipment_id,
        origin_hub_id=payload.origin_hub_id,
        dest_hub_id=payload.dest_hub_id,
        weight_kg=payload.weight_kg,
        priority=payload.priority,
        current_eta_mins=eta_mins
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Broadcast event
    await ws_manager.broadcast({
        "type": "SHIPMENT_CREATED",
        "shipment_id": shipment.shipment_id,
        "origin": origin.city,
        "dest": dest.city,
        "weight_kg": shipment.weight_kg
    })

    return shipment

@router.get("/", response_model=List[ShipmentResponse])
def list_shipments(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Shipment)
    if status:
        query = query.filter(Shipment.status == status.upper())
    return query.order_by(Shipment.created_at.desc()).limit(limit).all()

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.post("/{shipment_id}/assign", response_model=ShipmentResponse)
async def assign_vehicle(
    shipment_id: str,
    payload: Optional[ShipmentAssign] = None,
    auto_find: bool = Query(False, description="Auto-find best available vehicle"),
    db: Session = Depends(get_db)
):
    if auto_find:
        best_veh = DispatchEngine.find_best_vehicle(db, shipment_id)
        veh_id = best_veh.vehicle_id
    elif payload and payload.vehicle_id:
        veh_id = payload.vehicle_id
    else:
        raise HTTPException(status_code=400, detail="Must provide vehicle_id or set auto_find=true")

    shipment = DispatchEngine.assign_vehicle_to_shipment(db, shipment_id, veh_id)

    await ws_manager.broadcast({
        "type": "SHIPMENT_ASSIGNED",
        "shipment_id": shipment.shipment_id,
        "vehicle_id": veh_id
    })

    return shipment

@router.post("/{shipment_id}/transition", response_model=ShipmentResponse)
async def transition_shipment(
    shipment_id: str,
    payload: ShipmentTransition,
    db: Session = Depends(get_db)
):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    old_status = shipment.status
    ShipmentLifecycleFSM.transition(shipment, payload.new_status, notes=payload.notes)
    db.commit()
    db.refresh(shipment)

    await ws_manager.broadcast({
        "type": "SHIPMENT_TRANSITIONED",
        "shipment_id": shipment.shipment_id,
        "old_status": old_status,
        "new_status": shipment.status
    })

    return shipment
