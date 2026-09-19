"""
Swarm Coordinator for SwarmIQ.
Maintains drone fleet, spatial matrices, force accumulation, and swarm-level state.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

from app.simulation.drone import Drone
from app.models.schemas import DroneRole, DroneStatus, SimulationMetrics
from app.core.config import settings


class Swarm:
    def __init__(self, drone_count: int = settings.default_drone_count, spawn_center: Optional[np.ndarray] = None):
        self.drones: Dict[str, Drone] = {}
        self.leader_id: Optional[str] = None
        self.spawn_center = (
            np.array(spawn_center, dtype=np.float64)
            if spawn_center is not None
            else np.array([-60.0, 10.0, -60.0], dtype=np.float64)
        )

        # Swarm Metrics tracking
        self.collision_warnings: int = 0
        self.near_misses: int = 0
        self.actual_collisions: int = 0

        self.initialize_drones(drone_count, self.spawn_center)

    def initialize_drones(self, count: int, spawn_center: np.ndarray) -> None:
        """Spawn drones distributed in a jittered grid around spawn center."""
        self.drones.clear()
        self.spawn_center = np.copy(spawn_center)
        self.collision_warnings = 0
        self.near_misses = 0
        self.actual_collisions = 0

        cols = int(np.ceil(np.sqrt(count)))
        spacing = 3.0

        for i in range(count):
            drone_id = f"DRONE_{i+1:02d}"
            col = i % cols
            row = i // cols

            offset = np.array(
                [
                    (col - cols / 2.0) * spacing + np.random.uniform(-0.3, 0.3),
                    np.random.uniform(-0.2, 0.5),
                    (row - cols / 2.0) * spacing + np.random.uniform(-0.3, 0.3),
                ],
                dtype=np.float64,
            )
            pos = self.spawn_center + offset

            drone = Drone(
                drone_id=drone_id,
                position=pos,
                role=DroneRole.FOLLOWER,
                battery=100.0,
            )
            self.drones[drone_id] = drone

        # Designate first active drone as default initial leader
        if self.drones:
            first_id = list(self.drones.keys())[0]
            self.drones[first_id].role = DroneRole.LEADER
            self.leader_id = first_id
            for drone in self.drones.values():
                drone.leader_id = self.leader_id

    def get_leader(self) -> Optional[Drone]:
        if self.leader_id and self.leader_id in self.drones:
            leader = self.drones[self.leader_id]
            if leader.status == DroneStatus.ACTIVE:
                return leader
        return None

    def set_leader(self, new_leader_id: str) -> None:
        if new_leader_id in self.drones:
            # Demote old leader if still active
            if self.leader_id and self.leader_id in self.drones:
                if self.drones[self.leader_id].role == DroneRole.LEADER:
                    self.drones[self.leader_id].role = DroneRole.FOLLOWER

            self.leader_id = new_leader_id
            self.drones[new_leader_id].role = DroneRole.LEADER
            for drone in self.drones.values():
                drone.leader_id = self.leader_id

    def get_active_drones(self) -> List[Drone]:
        return [d for d in self.drones.values() if d.status == DroneStatus.ACTIVE]

    def get_positions_and_velocities(self) -> Tuple[List[str], np.ndarray, np.ndarray]:
        """Return drone IDs, position matrix (N, 3), and velocity matrix (N, 3)."""
        drone_ids = list(self.drones.keys())
        if not drone_ids:
            return [], np.empty((0, 3)), np.empty((0, 3))

        positions = np.array([self.drones[did].position for did in drone_ids], dtype=np.float64)
        velocities = np.array([self.drones[did].velocity for did in drone_ids], dtype=np.float64)
        return drone_ids, positions, velocities

    def update(self, dt: float) -> None:
        """Update each drone forward by dt."""
        for drone in self.drones.values():
            drone.update(dt)

    def get_metrics(self, fps: float = 0.0, update_rate: float = 0.0) -> SimulationMetrics:
        total = len(self.drones)
        active = sum(1 for d in self.drones.values() if d.status == DroneStatus.ACTIVE)
        failed = sum(1 for d in self.drones.values() if d.status == DroneStatus.FAILED)

        batteries = [d.battery for d in self.drones.values()]
        avg_bat = float(np.mean(batteries)) if batteries else 100.0
        min_bat = float(np.min(batteries)) if batteries else 100.0

        leader = self.get_leader()
        leader_bat = float(leader.battery) if leader else 0.0

        return SimulationMetrics(
            total_drones=total,
            active_drones=active,
            failed_drones=failed,
            collision_warnings=self.collision_warnings,
            near_misses=self.near_misses,
            actual_collisions=self.actual_collisions,
            fps=round(fps, 1),
            update_rate=round(update_rate, 1),
            average_battery=round(avg_bat, 1),
            min_battery=round(min_bat, 1),
            leader_battery=round(leader_bat, 1),
        )
