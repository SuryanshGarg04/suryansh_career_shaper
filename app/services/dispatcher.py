from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.models.hub import Hub
from app.services.fsm import ShipmentLifecycleFSM
from app.services.geofence import haversine_distance_km

class DispatchEngine:
    """
    Automated dispatch and driver-vehicle allocation engine.
    Ensures capacity constraints, optimizes proximity, and prevents race conditions.
    """

    @staticmethod
    def assign_vehicle_to_shipment(db: Session, shipment_id: str, vehicle_id: str) -> Shipment:
        # Check shipment
        shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")

        # Concurrency safety: Lock vehicle record
        # In PostgreSQL: .with_for_update() locks the row until commit
        try:
            vehicle_query = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id)
            if db.bind.dialect.name == "postgresql":
                vehicle_query = vehicle_query.with_for_update()
            vehicle = vehicle_query.first()
        except Exception:
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")

        if vehicle.status != "AVAILABLE":
            raise HTTPException(
                status_code=409,
                detail=f"Vehicle '{vehicle_id}' is currently unavailable (Status: {vehicle.status})"
            )

        if shipment.weight_kg > vehicle.max_weight_capacity_kg:
            raise HTTPException(
                status_code=400,
                detail=f"Cargo weight ({shipment.weight_kg}kg) exceeds vehicle capacity ({vehicle.max_weight_capacity_kg}kg)"
            )

        # Apply FSM transition
        ShipmentLifecycleFSM.transition(shipment, "ASSIGNED")
        shipment.assigned_vehicle_id = vehicle.vehicle_id
        vehicle.status = "ASSIGNED"

        db.commit()
        db.refresh(shipment)
        db.refresh(vehicle)
        return shipment

    @staticmethod
    def find_best_vehicle(db: Session, shipment_id: str) -> Vehicle:
        shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")

        origin_hub = db.query(Hub).filter(Hub.hub_id == shipment.origin_hub_id).first()
        if not origin_hub:
            raise HTTPException(status_code=404, detail="Origin hub not found")

        # Candidate vehicles: Available and sufficient payload capacity
        candidates = db.query(Vehicle).filter(
            Vehicle.status == "AVAILABLE",
            Vehicle.max_weight_capacity_kg >= shipment.weight_kg
        ).all()

        if not candidates:
            raise HTTPException(status_code=404, detail="No available vehicles meet the payload requirements")

        # Sort candidates by proximity to origin hub
        def calculate_distance(veh):
            if veh.current_lat is not None and veh.current_lon is not None:
                return haversine_distance_km(origin_hub.latitude, origin_hub.longitude, veh.current_lat, veh.current_lon)
            return 99999.0

        candidates.sort(key=calculate_distance)
        return candidates[0]
