"""
Potential Field Navigation for SwarmIQ.
Calculates local repulsive potential fields from static and dynamic obstacles.
Operates seamlessly alongside Boids and global A* waypoints.
"""

from typing import Dict, List
import numpy as np

from app.core.config import settings
from app.simulation.drone import Drone
from app.simulation.environment import Obstacle
from app.models.schemas import ObstacleType, DroneStatus


class PotentialField:
    def __init__(
        self,
        repulsion_weight: float = settings.obstacle_repulsion_weight,
        influence_distance: float = settings.obstacle_influence_distance,
    ):
        self.repulsion_weight = repulsion_weight
        self.influence_distance = influence_distance

    def compute_obstacle_repulsion(
        self, drones: List[Drone], obstacles: List[Obstacle]
    ) -> Dict[str, np.ndarray]:
        """
        Compute repulsive forces exerted by all obstacles on all active drones.
        F_rep = k_rep * (1/d - 1/d0) * (1/d^2) * norm_vec
        """
        forces: Dict[str, np.ndarray] = {d.id: np.zeros(3, dtype=np.float64) for d in drones}
        if not obstacles:
            return forces

        active_drones = [d for d in drones if d.status.value in ["ACTIVE", "RETURNING"]]
        if not active_drones:
            return forces

        for drone in active_drones:
            total_repulsion = np.zeros(3, dtype=np.float64)

            for obs in obstacles:
                # Calculate vector from obstacle surface to drone
                surface_dist, away_dir = self._distance_and_direction(drone.position, obs)

                if surface_dist < self.influence_distance and surface_dist > 0.05:
                    # Non-linear potential field gradient
                    scale = (
                        self.repulsion_weight
                        * (1.0 / surface_dist - 1.0 / self.influence_distance)
                        / (surface_dist**2)
                    )
                    # Dynamic obstacles push slightly stronger in the direction of their velocity
                    if obs.is_dynamic:
                        scale *= 1.4

                    total_repulsion += scale * away_dir

            # Clamp repulsive force to prevent numerical explosion
            force_norm = np.linalg.norm(total_repulsion)
            if force_norm > settings.max_force * 1.5:
                total_repulsion = (total_repulsion / force_norm) * (settings.max_force * 1.5)

            forces[drone.id] = total_repulsion

        return forces

    def _distance_and_direction(self, point: np.ndarray, obs: Obstacle) -> tuple[float, np.ndarray]:
        """Compute shortest distance from point to obstacle surface and unit away vector."""
        if obs.type == ObstacleType.SPHERE:
            diff = point - obs.position
            dist = np.linalg.norm(diff)
            radius = float(obs.size[0])
            surface_dist = max(0.01, dist - radius)
            away_dir = diff / max(1e-4, dist)
            return surface_dist, away_dir

        elif obs.type == ObstacleType.CYLINDER:
            # Cylinder with vertical axis Y
            radius = float(obs.size[0])
            height = float(obs.size[1])

            # Horizontal delta
            h_diff = np.array([point[0] - obs.position[0], 0.0, point[2] - obs.position[2]])
            h_dist = np.linalg.norm(h_diff)
            h_surface_dist = max(0.01, h_dist - radius)

            # Vertical delta
            y_min = obs.position[1]
            y_max = obs.position[1] + height

            if y_min <= point[1] <= y_max:
                # Beside the cylinder
                away_dir = h_diff / max(1e-4, h_dist)
                return h_surface_dist, away_dir
            elif point[1] > y_max:
                # Above cylinder
                v_dist = point[1] - y_max
                away_dir = np.array([h_diff[0], v_dist, h_diff[2]])
                total_dist = np.linalg.norm(away_dir)
                return max(0.01, total_dist - radius * 0.5), away_dir / max(1e-4, total_dist)
            else:
                # Below cylinder
                v_dist = y_min - point[1]
                away_dir = np.array([h_diff[0], -v_dist, h_diff[2]])
                total_dist = np.linalg.norm(away_dir)
                return max(0.01, total_dist - radius * 0.5), away_dir / max(1e-4, total_dist)

        elif obs.type == ObstacleType.BOX:
            half_size = obs.size / 2.0
            diff = point - obs.position
            # Clamped point on box surface
            clamped = np.clip(diff, -half_size, half_size)
            vec_to_pt = diff - clamped
            dist = np.linalg.norm(vec_to_pt)
            if dist < 1e-4:
                # Inside box, push out along shortest axis
                abs_diff = np.abs(diff)
                margins = half_size - abs_diff
                min_axis = int(np.argmin(margins))
                away_dir = np.zeros(3, dtype=np.float64)
                away_dir[min_axis] = np.sign(diff[min_axis]) if diff[min_axis] != 0 else 1.0
                return 0.05, away_dir
            return dist, vec_to_pt / dist

        return 100.0, np.zeros(3, dtype=np.float64)
