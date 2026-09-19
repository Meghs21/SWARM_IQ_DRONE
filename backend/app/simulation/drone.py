"""
Drone Class and Kinematics Engine for SwarmIQ.
Models single-agent 3D physics, constraints, battery dynamics, and state transitions.
"""

from typing import Optional, Union, List
import numpy as np

from app.models.schemas import DroneRole, DroneStatus, DroneState, Vector3D
from app.core.config import settings


class Drone:
    def __init__(
        self,
        drone_id: str,
        position: Union[np.ndarray, List[float]],
        velocity: Optional[Union[np.ndarray, List[float]]] = None,
        role: DroneRole = DroneRole.FOLLOWER,
        battery: float = 100.0,
        max_speed: Optional[float] = None,
        max_acceleration: Optional[float] = None,
        safety_radius: Optional[float] = None,
        mass: Optional[float] = None,
    ):
        self.id: str = drone_id
        self.position: np.ndarray = np.array(position, dtype=np.float64)
        self.velocity: np.ndarray = (
            np.array(velocity, dtype=np.float64) if velocity is not None else np.zeros(3, dtype=np.float64)
        )
        self.acceleration: np.ndarray = np.zeros(3, dtype=np.float64)
        self.accumulated_force: np.ndarray = np.zeros(3, dtype=np.float64)

        self.role: DroneRole = role
        self.status: DroneStatus = DroneStatus.ACTIVE
        self.battery: float = max(0.0, min(100.0, float(battery)))
        self.target: Optional[np.ndarray] = None
        self.leader_id: Optional[str] = None
        self.communication_strength: float = 1.0

        # Physical parameters
        self.mass: float = mass if mass is not None else settings.drone_mass
        self.max_speed: float = max_speed if max_speed is not None else settings.max_speed
        self.max_acceleration: float = (
            max_acceleration if max_acceleration is not None else settings.max_acceleration
        )
        self.safety_radius: float = safety_radius if safety_radius is not None else settings.safety_radius

        # Base home / launch position for return-to-base
        self.home_position: np.ndarray = np.copy(self.position)

    def apply_force(self, force: np.ndarray) -> None:
        """Accumulate an external steering or interaction force."""
        if self.status != DroneStatus.ACTIVE and self.status != DroneStatus.RETURNING:
            return
        self.accumulated_force += np.asarray(force, dtype=np.float64)

    def update(self, dt: float) -> None:
        """
        Advance drone dynamics by time step dt:
        1. Forces -> Acceleration (clamped)
        2. Velocity integration (clamped to max_speed)
        3. Position integration
        4. Battery consumption
        5. State checks & environmental clamping
        """
        if self.status == DroneStatus.FAILED:
            # Gravity descent if drone has failed
            self.velocity[1] = max(-4.0, self.velocity[1] - 9.81 * dt)
            self.position += self.velocity * dt
            if self.position[1] <= settings.bounds_y[0]:
                self.position[1] = settings.bounds_y[0]
                self.velocity = np.zeros(3, dtype=np.float64)
            return

        # 1. Acceleration: F = m * a -> a = F / m
        raw_accel = self.accumulated_force / self.mass
        accel_norm = np.linalg.norm(raw_accel)
        if accel_norm > self.max_acceleration:
            self.acceleration = (raw_accel / accel_norm) * self.max_acceleration
        else:
            self.acceleration = raw_accel

        # 2. Velocity: v = v + a * dt
        self.velocity += self.acceleration * dt
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
            speed = self.max_speed

        # 3. Position: p = p + v * dt
        self.position += self.velocity * dt

        # Enforce boundary limits
        self._enforce_bounds()

        # 4. Battery drain
        self._update_battery(speed, accel_norm, dt)

        # 5. State transitions based on battery or condition
        self._update_state()

        # Reset accumulated forces for the next frame
        self.accumulated_force = np.zeros(3, dtype=np.float64)

    def _enforce_bounds(self) -> None:
        """Keep drone within simulated flight volume with smooth cushion."""
        min_x, max_x = settings.bounds_x
        min_y, max_y = settings.bounds_y
        min_z, max_z = settings.bounds_z

        if self.position[0] < min_x:
            self.position[0] = min_x
            self.velocity[0] = abs(self.velocity[0]) * 0.5
        elif self.position[0] > max_x:
            self.position[0] = max_x
            self.velocity[0] = -abs(self.velocity[0]) * 0.5

        if self.position[1] < min_y:
            self.position[1] = min_y
            self.velocity[1] = abs(self.velocity[1]) * 0.5
        elif self.position[1] > max_y:
            self.position[1] = max_y
            self.velocity[1] = -abs(self.velocity[1]) * 0.5

        if self.position[2] < min_z:
            self.position[2] = min_z
            self.velocity[2] = abs(self.velocity[2]) * 0.5
        elif self.position[2] > max_z:
            self.position[2] = max_z
            self.velocity[2] = -abs(self.velocity[2]) * 0.5

    def _update_battery(self, speed: float, accel_norm: float, dt: float) -> None:
        """Discharge battery proportionally to hover time, velocity, and acceleration."""
        drain_rate = (
            settings.battery_base_drain
            + settings.battery_speed_drain * (speed / max(1.0, self.max_speed))
            + settings.battery_accel_drain * (accel_norm / max(1.0, self.max_acceleration))
        )
        self.battery = max(0.0, self.battery - drain_rate * dt)

    def _update_state(self) -> None:
        """Trigger behavior change upon reaching critical battery thresholds."""
        if self.battery <= settings.critical_battery_threshold:
            self.status = DroneStatus.FAILED
            self.role = DroneRole.FOLLOWER
        elif self.battery <= settings.low_battery_threshold:
            if self.status == DroneStatus.ACTIVE:
                self.status = DroneStatus.RETURNING
                # Target becomes return-to-base launch position
                self.target = np.copy(self.home_position)

    def fail(self) -> None:
        """Manually trigger drone failure (useful for leader failure scenario)."""
        self.status = DroneStatus.FAILED
        self.battery = 0.0

    def distance_to(self, other_pos: np.ndarray) -> float:
        """Compute Euclidean distance to another 3D position."""
        return float(np.linalg.norm(self.position - other_pos))

    def to_state(self) -> DroneState:
        """Convert runtime drone instance to serializable Pydantic state."""
        return DroneState(
            id=self.id,
            position=Vector3D(
                x=round(float(self.position[0]), 2),
                y=round(float(self.position[1]), 2),
                z=round(float(self.position[2]), 2),
            ),
            velocity=Vector3D(
                x=round(float(self.velocity[0]), 2),
                y=round(float(self.velocity[1]), 2),
                z=round(float(self.velocity[2]), 2),
            ),
            battery=round(self.battery, 1),
            role=self.role,
            status=self.status,
            leader_id=self.leader_id,
            target=(
                Vector3D(
                    x=round(float(self.target[0]), 2),
                    y=round(float(self.target[1]), 2),
                    z=round(float(self.target[2]), 2),
                )
                if self.target is not None
                else None
            ),
            communication_strength=round(self.communication_strength, 2),
        )
