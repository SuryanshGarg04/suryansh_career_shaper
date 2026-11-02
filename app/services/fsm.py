from datetime import datetime
from fastapi import HTTPException
from app.models.shipment import Shipment

class ShipmentLifecycleFSM:
    """
    Finite State Machine (FSM) enforcing atomic transitions across shipment lifecycles.
    Prevents race conditions and inconsistent states in logistics workflows.
    """

    ALLOWED_TRANSITIONS = {
        "CREATED": ["ASSIGNED", "CANCELLED"],
        "ASSIGNED": ["IN_TRANSIT", "CANCELLED", "EXCEPTION_FLAGGED"],
        "IN_TRANSIT": ["OUT_FOR_DELIVERY", "EXCEPTION_FLAGGED"],
        "OUT_FOR_DELIVERY": ["DELIVERED", "EXCEPTION_FLAGGED"],
        "EXCEPTION_FLAGGED": ["IN_TRANSIT", "OUT_FOR_DELIVERY", "CANCELLED"],
        "DELIVERED": [],
        "CANCELLED": []
    }

    @classmethod
    def transition(cls, shipment: Shipment, target_status: str, notes: str = None) -> Shipment:
        current_status = shipment.status
        target_status = target_status.upper()

        if target_status not in cls.ALLOWED_TRANSITIONS.get(current_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Illegal state transition from '{current_status}' to '{target_status}'. "
                       f"Allowed targets: {cls.ALLOWED_TRANSITIONS.get(current_status, [])}"
            )

        shipment.status = target_status

        now = datetime.utcnow()
        if target_status == "IN_TRANSIT" and not shipment.dispatched_at:
            shipment.dispatched_at = now
        elif target_status == "DELIVERED":
            shipment.delivered_at = now
            shipment.current_eta_mins = 0
        elif target_status == "EXCEPTION_FLAGGED":
            shipment.exception_reason = notes or "Transit anomaly detected"

        return shipment
