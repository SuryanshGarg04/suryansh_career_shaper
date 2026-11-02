from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.telemetry import TelemetryLog
from app.schemas.telemetry import TelemetryPing, TelemetryResponse, BatchTelemetryIngest
from app.services.telemetry_buffer import telemetry_buffer
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.post("/", response_model=Dict[str, Any])
async def ingest_telemetry_ping(ping: TelemetryPing):
    ping_dict = ping.model_dump()
    anomaly = telemetry_buffer.add_ping(ping_dict)

    # Broadcast to live UI via WebSocket
    await ws_manager.broadcast({
        "type": "TELEMETRY_PING",
        "vehicle_id": ping.vehicle_id,
        "lat": ping.latitude,
        "lon": ping.longitude,
        "speed": ping.speed_kmh,
        "fuel": ping.fuel_pct,
        "anomaly": anomaly
    })

    return {
        "status": "ACCEPTED",
        "vehicle_id": ping.vehicle_id,
        "anomaly_flag": anomaly,
        "buffered": True
    }

@router.post("/batch", response_model=Dict[str, Any])
async def ingest_batch_telemetry(payload: BatchTelemetryIngest):
    anomalies_detected = 0
    for ping in payload.pings:
        ping_dict = ping.model_dump()
        flag = telemetry_buffer.add_ping(ping_dict)
        if flag != "None":
            anomalies_detected += 1

    return {
        "status": "BATCH_ACCEPTED",
        "count": len(payload.pings),
        "anomalies_detected": anomalies_detected,
        "buffered": True
    }

@router.get("/latest/{vehicle_id}")
def get_latest_position(vehicle_id: str):
    pos = telemetry_buffer.get_latest_position(vehicle_id)
    if not pos:
        return {"status": "NOT_FOUND", "vehicle_id": vehicle_id, "message": "No active telemetry pings yet"}
    return {"status": "OK", "data": pos}

@router.get("/active")
def get_all_active_positions():
    return telemetry_buffer.get_all_active_positions()

@router.get("/history/{vehicle_id}", response_model=List[TelemetryResponse])
def get_telemetry_history(
    vehicle_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return (
        db.query(TelemetryLog)
        .filter(TelemetryLog.vehicle_id == vehicle_id)
        .order_by(TelemetryLog.timestamp.desc())
        .limit(limit)
        .all()
    )
