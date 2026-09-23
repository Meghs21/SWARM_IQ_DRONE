"""
Pydantic Schemas for SwarmIQ.
Defines data models for REST APIs, WebSockets, and state serialization.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Vector3D(BaseModel):
    x: float
    y: float
    z: float

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]


class DroneRole(str, Enum):
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"


class DroneStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    RETURNING = "RETURNING"
    COMPLETED = "COMPLETED"


class FormationType(str, Enum):
    V = "V"
    LINE = "LINE"
    GRID = "GRID"
    CIRCLE = "CIRCLE"


class MissionStatus(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ObstacleType(str, Enum):
    SPHERE = "SPHERE"
    CYLINDER = "CYLINDER"
    BOX = "BOX"


class ObstacleState(BaseModel):
    id: str
    type: ObstacleType
    position: Vector3D
    size: Vector3D  # radius, height, or (width, height, depth)
    is_dynamic: bool = False
    velocity: Optional[Vector3D] = None


class DroneState(BaseModel):
    id: str
    position: Vector3D
    velocity: Vector3D
    battery: float
    role: DroneRole
    status: DroneStatus
    leader_id: Optional[str] = None
    target: Optional[Vector3D] = None
    communication_strength: float = 1.0


class MissionState(BaseModel):
    status: MissionStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    target: Vector3D
    start_position: Vector3D
    distance_to_target: float = 0.0
    elapsed_time: float = 0.0
    formation: FormationType = FormationType.V


class SimulationMetrics(BaseModel):
    total_drones: int = 0
    active_drones: int = 0
    failed_drones: int = 0
    collision_warnings: int = 0
    near_misses: int = 0
    actual_collisions: int = 0
    fps: float = 0.0
    update_rate: float = 0.0
    average_battery: float = 100.0
    min_battery: float = 100.0
    leader_battery: float = 100.0


class MissionCreateRequest(BaseModel):
    drone_count: int = Field(default=50, ge=1, le=150)
    target: Optional[Vector3D] = Field(default_factory=lambda: Vector3D(x=60.0, y=15.0, z=60.0))
    start_position: Optional[Vector3D] = Field(default_factory=lambda: Vector3D(x=-60.0, y=10.0, z=-60.0))
    formation: FormationType = FormationType.V
    preset_scenario: Optional[str] = None
    enable_dynamic_obstacles: bool = False


class FormationChangeRequest(BaseModel):
    formation: FormationType


class FleetSizeChangeRequest(BaseModel):
    drone_count: int = Field(default=50, ge=1, le=150)


class SimulationSnapshot(BaseModel):
    type: str = "simulation_state"
    timestamp: float
    mission: MissionState
    leader_id: Optional[str] = None
    waypoints: List[Vector3D] = []
    drones: List[DroneState]
    obstacles: List[ObstacleState] = []
    metrics: SimulationMetrics
