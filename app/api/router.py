from fastapi import APIRouter
from app.api.v1 import shipments, telemetry, vehicles, hubs, analytics

api_router = APIRouter()
api_router.include_router(shipments.router)
api_router.include_router(telemetry.router)
api_router.include_router(vehicles.router)
api_router.include_router(hubs.router)
api_router.include_router(analytics.router)
