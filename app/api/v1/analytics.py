from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.models.telemetry import TelemetryLog
from app.services.telemetry_buffer import telemetry_buffer

router = APIRouter(prefix="/analytics", tags=["Analytics & SLAs"])

@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Vehicle count by status
    veh_counts = dict(
        db.query(Vehicle.status, func.count(Vehicle.vehicle_id))
        .group_by(Vehicle.status)
        .all()
    )

    # Shipment count by status
    shipment_counts = dict(
        db.query(Shipment.status, func.count(Shipment.shipment_id))
        .group_by(Shipment.status)
        .all()
    )

    # Telemetry anomalies recorded
    anomaly_counts = dict(
        db.query(TelemetryLog.anomaly_flag, func.count(TelemetryLog.id))
        .filter(TelemetryLog.anomaly_flag != "None")
        .group_by(TelemetryLog.anomaly_flag)
        .all()
    )

    total_logs = db.query(func.count(TelemetryLog.id)).scalar() or 0

    return {
        "fleet_status": {
            "AVAILABLE": veh_counts.get("AVAILABLE", 0),
            "ASSIGNED": veh_counts.get("ASSIGNED", 0),
            "IN_TRANSIT": veh_counts.get("IN_TRANSIT", 0),
            "MAINTENANCE": veh_counts.get("MAINTENANCE", 0),
            "total_vehicles": sum(veh_counts.values())
        },
        "shipment_pipeline": {
            "CREATED": shipment_counts.get("CREATED", 0),
            "ASSIGNED": shipment_counts.get("ASSIGNED", 0),
            "IN_TRANSIT": shipment_counts.get("IN_TRANSIT", 0),
            "OUT_FOR_DELIVERY": shipment_counts.get("OUT_FOR_DELIVERY", 0),
            "DELIVERED": shipment_counts.get("DELIVERED", 0),
            "EXCEPTION_FLAGGED": shipment_counts.get("EXCEPTION_FLAGGED", 0),
            "total_shipments": sum(shipment_counts.values())
        },
        "telemetry_stats": {
            "total_historical_logs": total_logs,
            "buffered_in_memory_queue": len(telemetry_buffer.queue),
            "active_live_tracking_nodes": len(telemetry_buffer.latest_vehicle_cache),
            "active_anomalies_flagged": anomaly_counts
        }
    }

@router.get("/sla")
def get_sla_metrics(db: Session = Depends(get_db)):
    delivered = db.query(Shipment).filter(Shipment.status == "DELIVERED").count()
    exceptions = db.query(Shipment).filter(Shipment.status == "EXCEPTION_FLAGGED").count()
    total_completed = delivered + exceptions

    sla_compliance_pct = round((delivered / total_completed * 100), 2) if total_completed > 0 else 100.0

    return {
        "delivered_on_schedule": delivered,
        "transit_exceptions": exceptions,
        "sla_compliance_pct": sla_compliance_pct,
        "target_sla_pct": 95.0
    }
