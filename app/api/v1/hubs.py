from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.hub import Hub
from app.services.geofence import haversine_distance_km

router = APIRouter(prefix="/hubs", tags=["Logistics Hubs"])

@router.get("/")
def list_hubs(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    hubs = db.query(Hub).all()
    return [
        {
            "hub_id": h.hub_id,
            "name": h.name,
            "city": h.city,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "capacity_limit": h.capacity_limit
        }
        for h in hubs
    ]

@router.get("/distance")
def get_hub_distance(origin_hub_id: str, dest_hub_id: str, db: Session = Depends(get_db)):
    h1 = db.query(Hub).filter(Hub.hub_id == origin_hub_id).first()
    h2 = db.query(Hub).filter(Hub.hub_id == dest_hub_id).first()
    if not h1 or not h2:
        return {"error": "One or both hubs not found"}

    dist = haversine_distance_km(h1.latitude, h1.longitude, h2.latitude, h2.longitude)
    return {
        "origin": {"id": h1.hub_id, "city": h1.city},
        "destination": {"id": h2.hub_id, "city": h2.city},
        "distance_km": dist
    }
