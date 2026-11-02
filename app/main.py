from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.router import api_router
from app.services.telemetry_buffer import telemetry_buffer
from app.websocket.manager import ws_manager
from app.models.hub import Hub
from app.models.vehicle import Vehicle

# Pre-defined major logistics hubs
DEFAULT_HUBS = [
    {"hub_id": "HUB_DEL", "name": "Delhi National Logistics Park", "city": "New Delhi", "latitude": 28.6139, "longitude": 77.2090, "capacity_limit": 1000},
    {"hub_id": "HUB_BOM", "name": "Jawaharlal Nehru Port Hub", "city": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "capacity_limit": 1200},
    {"hub_id": "HUB_BLR", "name": "Hosur Tech & Cargo Distribution Center", "city": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946, "capacity_limit": 800},
    {"hub_id": "HUB_HYD", "name": "Rajiv Gandhi Transit Warehouse", "city": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867, "capacity_limit": 750},
    {"hub_id": "HUB_CCU", "name": "Howrah Freight Terminal", "city": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "capacity_limit": 700},
    {"hub_id": "HUB_MAA", "name": "Chennai Port Logistics Facility", "city": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "capacity_limit": 650},
    {"hub_id": "HUB_AMD", "name": "Sardar Patel Freight Corridor", "city": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714, "capacity_limit": 600},
    {"hub_id": "HUB_PNQ", "name": "Chakan Industrial Logistics Node", "city": "Pune", "latitude": 18.5204, "longitude": 73.8567, "capacity_limit": 550},
    {"hub_id": "HUB_JAI", "name": "Jaipur Golden Triangle Hub", "city": "Jaipur", "latitude": 26.9124, "longitude": 75.7873, "capacity_limit": 500},
    {"hub_id": "HUB_LKO", "name": "Lucknow Regional Gateway", "city": "Lucknow", "latitude": 26.8467, "longitude": 80.9462, "capacity_limit": 450}
]

def auto_seed_reference_data():
    """Initializes tables and seeds reference data if not already present."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed Hubs
        if db.query(Hub).count() == 0:
            for h in DEFAULT_HUBS:
                db.add(Hub(**h))
            db.commit()

        # Seed initial vehicles if empty
        if db.query(Vehicle).count() == 0:
            types = [
                ("Heavy_Truck", 28000),
                ("Medium_Duty", 12000),
                ("Light_Van", 3500),
                ("Electric_Van", 2200)
            ]
            for i in range(1, 51):
                v_type, cap = types[i % len(types)]
                hub = DEFAULT_HUBS[i % len(DEFAULT_HUBS)]
                db.add(Vehicle(
                    vehicle_id=f"VEH{i:03d}",
                    plate_number=f"DL-01-FL-{1000+i}",
                    vehicle_type=v_type,
                    max_weight_capacity_kg=cap,
                    status="AVAILABLE",
                    current_lat=hub["latitude"] + 0.05,
                    current_lon=hub["longitude"] + 0.05,
                    fuel_pct=85.0
                ))
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed database and start telemetry buffer worker
    auto_seed_reference_data()
    telemetry_buffer.start()
    yield
    # Shutdown: flush buffer cleanly
    await telemetry_buffer.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-performance distributed backend for real-time fleet telemetry, dispatch optimization, and shipment state machine tracking.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Static Files for UI Dashboard
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def serve_dashboard():
    return FileResponse("app/static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive ping loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
