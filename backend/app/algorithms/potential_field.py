"""
Potential Field Navigation for SwarmIQ.
Calculates local repulsive potential fields from static and dynamic obstacles.
Operates seamlessly alongside Boids and global A* waypoints.
"""

from typing import Dict, List, Tuple
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
                # Calculate vector from obstacle surface to drone (signed distance)
                surface_dist, away_dir = self._distance_and_direction(drone.position, obs)

                if surface_dist < self.influence_distance:
                    if surface_dist <= 0.0:
                        # Inside obstacle boundary: emergency escape repulsion
                        scale = settings.max_force * 3.5
                    else:
                        # Non-linear potential field gradient scaling up sharply near surface
                        d_eff = max(0.15, surface_dist)
                        scale = (
                            self.repulsion_weight
                            * (1.0 / d_eff - 1.0 / self.influence_distance)
                            / (d_eff**1.5)
                        )
                        scale = min(scale, settings.max_force * 3.0)

                    # Dynamic obstacles push stronger
                    if obs.is_dynamic:
                        scale *= 1.5

                    total_repulsion += scale * away_dir

            forces[drone.id] = total_repulsion

        return forces

    def _distance_and_direction(self, point: np.ndarray, obs: Obstacle) -> Tuple[float, np.ndarray]:
        """Compute signed distance from point to obstacle surface and unit away vector."""
        if obs.type == ObstacleType.SPHERE:
            diff = point - obs.position
            dist = np.linalg.norm(diff)
            radius = float(obs.size[0])
            surface_dist = dist - radius  # negative if inside
            away_dir = diff / max(1e-4, dist)
            return surface_dist, away_dir

        elif obs.type == ObstacleType.CYLINDER:
            # Cylinder with vertical axis Y
            radius = float(obs.size[0])
            height = float(obs.size[1])

            # Horizontal delta
            h_diff = np.array([point[0] - obs.position[0], 0.0, point[2] - obs.position[2]])
            h_dist = np.linalg.norm(h_diff)
            h_surface_dist = h_dist - radius  # negative if inside radius

            # Vertical bounds
            y_min = obs.position[1]
            y_max = obs.position[1] + height

            if y_min <= point[1] <= y_max:
                # Beside the cylinder
                away_dir = h_diff / max(1e-4, h_dist) if h_dist > 1e-4 else np.array([1.0, 0.0, 0.0])
                return h_surface_dist, away_dir
            elif point[1] > y_max:
                # Above cylinder top
                v_dist = point[1] - y_max
                away_dir = np.array([h_diff[0], v_dist, h_diff[2]])
                total_dist = np.linalg.norm(away_dir)
                return max(0.01, total_dist - radius * 0.5), away_dir / max(1e-4, total_dist)
            else:
                # Below cylinder bottom
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
                signed_dist = -float(margins[min_axis])
                return signed_dist, away_dir
            return dist, vec_to_pt / dist

        return 100.0, np.zeros(3, dtype=np.float64)
