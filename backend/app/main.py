"""
SwarmIQ FastAPI Backend Application.
Serves REST APIs and real-time WebSocket state streaming for the autonomous drone simulation.
"""

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import router as api_router
from app.api.websocket import manager
from app.core.simulation_loop import engine
from app.models.schemas import SimulationSnapshot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("swarmiq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: subscribe WebSocket broadcaster to simulation engine loop
    def ws_snapshot_callback(snapshot: SimulationSnapshot):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.broadcast_snapshot(snapshot))
        except RuntimeError:
            pass

    engine.register_subscriber(ws_snapshot_callback)
    # Start simulation loop
    engine.start()
    logger.info("SwarmIQ Simulation Engine started.")

    yield

    # Shutdown
    await engine.stop()
    logger.info("SwarmIQ Simulation Engine stopped.")


app = FastAPI(
    title="SwarmIQ - Autonomous Multi-Drone Swarm API",
    description="Real-time 3D simulation engine for autonomous multi-drone swarms.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router)


# WebSocket streaming endpoint
@app.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send immediate initial snapshot
    try:
        initial_snapshot = engine.get_snapshot()
        await websocket.send_text(initial_snapshot.model_dump_json())

        while True:
            # Handle incoming client commands over WS if any (e.g. ping/heartbeat)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main.py:app", host="0.0.0.0", port=8000, reload=False)
