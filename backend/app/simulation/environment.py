"""
Environment Module for SwarmIQ.
Defines static and dynamic obstacles, environment boundaries, and obstacle update logic.
"""

from typing import List, Dict, Any, Optional
import numpy as np

from app.models.schemas import ObstacleType, ObstacleState, Vector3D
from app.core.config import settings


class Obstacle:
    def __init__(
        self,
        obstacle_id: str,
        obstacle_type: ObstacleType,
        position: np.ndarray,
        size: np.ndarray,
        is_dynamic: bool = False,
        velocity: Optional[np.ndarray] = None,
        trajectory_type: Optional[str] = None,
        trajectory_bounds: Optional[tuple] = None,
    ):
        self.id = obstacle_id
        self.type = obstacle_type
        self.position = np.array(position, dtype=np.float64)
        self.size = np.array(size, dtype=np.float64)  # [radius, height, 0] or [sx, sy, sz]
        self.is_dynamic = is_dynamic
        self.velocity = (
            np.array(velocity, dtype=np.float64) if velocity is not None else np.zeros(3, dtype=np.float64)
        )
        self.trajectory_type = trajectory_type
        self.trajectory_bounds = trajectory_bounds
        self.base_position = np.copy(self.position)
        self.time_elapsed: float = 0.0

    def update(self, dt: float) -> None:
        """Update dynamic obstacle movement."""
        if not self.is_dynamic:
            return

        self.time_elapsed += dt

        if self.trajectory_type == "linear":
            self.position += self.velocity * dt
            if self.trajectory_bounds:
                min_b, max_b = self.trajectory_bounds
                # Bounce between bounds on primary moving axis
                for axis in range(3):
                    if self.velocity[axis] != 0:
                        if self.position[axis] < min_b[axis]:
                            self.position[axis] = min_b[axis]
                            self.velocity[axis] *= -1.0
                        elif self.position[axis] > max_b[axis]:
                            self.position[axis] = max_b[axis]
                            self.velocity[axis] *= -1.0

        elif self.trajectory_type == "circle":
            radius = float(self.size[0]) * 3.0
            omega = 0.5  # angular speed rad/s
            self.position[0] = self.base_position[0] + radius * np.cos(omega * self.time_elapsed)
            self.position[2] = self.base_position[2] + radius * np.sin(omega * self.time_elapsed)
            self.velocity[0] = -radius * omega * np.sin(omega * self.time_elapsed)
            self.velocity[2] = radius * omega * np.cos(omega * self.time_elapsed)

    def to_state(self) -> ObstacleState:
        return ObstacleState(
            id=self.id,
            type=self.type,
            position=Vector3D(
                x=round(float(self.position[0]), 2),
                y=round(float(self.position[1]), 2),
                z=round(float(self.position[2]), 2),
            ),
            size=Vector3D(
                x=round(float(self.size[0]), 2),
                y=round(float(self.size[1]), 2),
                z=round(float(self.size[2]), 2),
            ),
            is_dynamic=self.is_dynamic,
            velocity=(
                Vector3D(
                    x=round(float(self.velocity[0]), 2),
                    y=round(float(self.velocity[1]), 2),
                    z=round(float(self.velocity[2]), 2),
                )
                if self.is_dynamic
                else None
            ),
        )


class Environment:
    def __init__(self):
        self.obstacles: List[Obstacle] = []

    def clear_obstacles(self) -> None:
        self.obstacles.clear()

    def add_obstacle(self, obstacle: Obstacle) -> None:
        self.obstacles.append(obstacle)

    def update(self, dt: float) -> None:
        for obs in self.obstacles:
            obs.update(dt)

    def get_obstacle_states(self) -> List[ObstacleState]:
        return [obs.to_state() for obs in self.obstacles]
