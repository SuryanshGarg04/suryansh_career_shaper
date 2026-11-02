import asyncio
import logging
from datetime import datetime
from collections import deque
from typing import List, Dict, Any
from app.config import settings
from app.database import SessionLocal
from app.models.telemetry import TelemetryLog
from app.models.vehicle import Vehicle
from app.services.geofence import detect_telemetry_anomaly

logger = logging.getLogger("telemetry_buffer")

class AsyncTelemetryBuffer:
    """
    Decoupled message buffer for high-throughput vehicle telemetry.
    Buffers incoming pings in memory (or Redis Streams) and writes batches to the database.
    """

    def __init__(self):
        self.queue: deque = deque()
        self.latest_vehicle_cache: Dict[str, Dict[str, Any]] = {}
        self._flush_task = None
        self._is_running = False

    def start(self):
        self._is_running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Telemetry buffer worker started.")

    async def stop(self):
        self._is_running = False
        if self._flush_task:
            self._flush_task.cancel()
        await self.flush()
        logger.info("Telemetry buffer flushed and stopped.")

    def add_ping(self, ping_data: Dict[str, Any]) -> str:
        # Determine anomaly
        veh_id = ping_data["vehicle_id"]
        prev_data = self.latest_vehicle_cache.get(veh_id)
        prev_fuel = prev_data.get("fuel_pct") if prev_data else None

        anomaly = detect_telemetry_anomaly(
            speed_kmh=ping_data.get("speed_kmh", 0.0),
            fuel_pct=ping_data.get("fuel_pct", 100.0),
            previous_fuel_pct=prev_fuel
        )

        ping_data["anomaly_flag"] = anomaly
        if not ping_data.get("timestamp"):
            ping_data["timestamp"] = datetime.utcnow()

        # Update in-memory hot cache for sub-millisecond lookups
        self.latest_vehicle_cache[veh_id] = ping_data
        self.queue.append(ping_data)
        return anomaly

    async def _periodic_flush(self):
        while self._is_running:
            try:
                await asyncio.sleep(settings.TELEMETRY_FLUSH_INTERVAL_SECONDS)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in telemetry flush: {e}")

    async def flush(self):
        if not self.queue:
            return

        batch: List[Dict[str, Any]] = []
        while self.queue and len(batch) < settings.TELEMETRY_BUFFER_BATCH_SIZE:
            batch.append(self.queue.popleft())

        if not batch:
            return

        # Execute batched DB writes in thread pool
        await asyncio.to_thread(self._write_batch_to_db, batch)

    def _write_batch_to_db(self, batch: List[Dict[str, Any]]):
        db = SessionLocal()
        try:
            logs = [
                TelemetryLog(
                    timestamp=item["timestamp"],
                    vehicle_id=item["vehicle_id"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    speed_kmh=item["speed_kmh"],
                    fuel_pct=item["fuel_pct"],
                    anomaly_flag=item["anomaly_flag"],
                    notes=item.get("notes")
                )
                for item in batch
            ]
            db.bulk_save_objects(logs)

            # Update vehicle latest coordinates in batch
            for item in batch:
                veh = db.query(Vehicle).filter(Vehicle.vehicle_id == item["vehicle_id"]).first()
                if veh:
                    veh.current_lat = item["latitude"]
                    veh.current_lon = item["longitude"]
                    veh.fuel_pct = item["fuel_pct"]

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to batch insert telemetry logs: {e}")
        finally:
            db.close()

    def get_latest_position(self, vehicle_id: str) -> Dict[str, Any]:
        return self.latest_vehicle_cache.get(vehicle_id)

    def get_all_active_positions(self) -> Dict[str, Dict[str, Any]]:
        return self.latest_vehicle_cache

telemetry_buffer = AsyncTelemetryBuffer()
