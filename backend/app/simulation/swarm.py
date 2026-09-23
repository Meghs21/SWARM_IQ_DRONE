"""
Swarm Coordinator for SwarmIQ.
Maintains drone fleet, spatial matrices, force accumulation, and swarm-level state.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

from app.simulation.drone import Drone
from app.models.schemas import DroneRole, DroneStatus, SimulationMetrics, FormationType
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

    def initialize_drones(
        self,
        count: int,
        spawn_center: np.ndarray,
        formation: Optional[FormationType] = None,
    ) -> None:
        """Spawn drones distributed either in designated formation geometry or jittered grid."""
        self.drones.clear()
        self.spawn_center = np.copy(spawn_center)
        self.collision_warnings = 0
        self.near_misses = 0
        self.actual_collisions = 0

        if count <= 0:
            self.leader_id = None
            return

        # Designate leader at spawn_center
        leader_id = "DRONE_01"
        self.leader_id = leader_id
        leader = Drone(
            drone_id=leader_id,
            position=np.copy(self.spawn_center),
            role=DroneRole.LEADER,
            battery=100.0,
        )
        self.drones[leader_id] = leader

        follower_count = count - 1
        if follower_count > 60:
            d = max(1.8, settings.formation_spacing * 0.50)
        elif follower_count > 30:
            d = max(2.2, settings.formation_spacing * 0.65)
        else:
            d = settings.formation_spacing

        # Planar forward heading matrix aligned with path (XZ plane)
        def_dir = np.array([1.0, 0.0, 1.0])
        h_len = np.hypot(def_dir[0], def_dir[2])
        fwd = np.array([def_dir[0], 0.0, def_dir[2]], dtype=np.float64) / h_len
        right = np.cross(np.array([0.0, 1.0, 0.0]), fwd)
        rot_mat = np.column_stack((right, np.array([0.0, 1.0, 0.0]), fwd))

        if formation == FormationType.CIRCLE and follower_count > 0:
            radius = max(8.0, (follower_count * d) / (2.0 * np.pi))
            angle_step = (2.0 * np.pi) / follower_count
            for i in range(follower_count):
                drone_id = f"DRONE_{i+2:02d}"
                theta = i * angle_step
                pos = self.spawn_center + np.array(
                    [radius * np.cos(theta), 0.0, radius * np.sin(theta)], dtype=np.float64
                )
                self.drones[drone_id] = Drone(
                    drone_id=drone_id,
                    position=pos,
                    role=DroneRole.FOLLOWER,
                    battery=100.0,
                )

        elif formation == FormationType.V and follower_count > 0:
            for i in range(follower_count):
                drone_id = f"DRONE_{i+2:02d}"
                wing = 1 if i % 2 == 0 else -1
                rank = (i // 2) + 1
                local_off = np.array([wing * rank * d, 0.0, -rank * d * 0.8], dtype=np.float64)
                pos = self.spawn_center + (rot_mat @ local_off)
                self.drones[drone_id] = Drone(
                    drone_id=drone_id,
                    position=pos,
                    role=DroneRole.FOLLOWER,
                    battery=100.0,
                )

        elif formation == FormationType.LINE and follower_count > 0:
            for i in range(follower_count):
                drone_id = f"DRONE_{i+2:02d}"
                side = 1 if i % 2 == 0 else -1
                dist = ((i // 2) + 1) * d
                local_off = np.array([side * dist, 0.0, -2.0], dtype=np.float64)
                pos = self.spawn_center + (rot_mat @ local_off)
                self.drones[drone_id] = Drone(
                    drone_id=drone_id,
                    position=pos,
                    role=DroneRole.FOLLOWER,
                    battery=100.0,
                )

        elif formation == FormationType.GRID and follower_count > 0:
            cols = int(np.ceil(np.sqrt(follower_count)))
            for i in range(follower_count):
                drone_id = f"DRONE_{i+2:02d}"
                col = i % cols
                row = i // cols
                x_off = (col - (cols - 1) / 2.0) * d
                z_off = -(row + 1) * d
                local_off = np.array([x_off, 0.0, z_off], dtype=np.float64)
                pos = self.spawn_center + (rot_mat @ local_off)
                self.drones[drone_id] = Drone(
                    drone_id=drone_id,
                    position=pos,
                    role=DroneRole.FOLLOWER,
                    battery=100.0,
                )

        else:
            # General fallback jittered grid
            cols = int(np.ceil(np.sqrt(count)))
            spacing = 3.0
            self.drones.clear()
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
                    role=DroneRole.FOLLOWER if i > 0 else DroneRole.LEADER,
                    battery=100.0,
                )
                self.drones[drone_id] = drone
            self.leader_id = "DRONE_01"

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
