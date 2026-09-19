"""
WebSocket Connection Manager for SwarmIQ.
Streams real-time simulation snapshots to connected clients at ~25 Hz.
"""

from typing import List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

from app.models.schemas import SimulationSnapshot

logger = logging.getLogger("swarmiq.ws")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast_snapshot(self, snapshot: SimulationSnapshot) -> None:
        if not self.active_connections:
            return

        # Serialize Pydantic snapshot to JSON
        data_text = snapshot.model_dump_json()

        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(data_text)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
