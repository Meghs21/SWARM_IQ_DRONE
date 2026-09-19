"""
Collision Avoidance Engine for SwarmIQ.
Detects inter-drone proximity, generates repulsive collision evasion forces,
and tracks collision warnings, near misses, and actual collisions.
"""

from typing import Dict, List, Tuple
import numpy as np

from app.core.config import settings
from app.simulation.drone import Drone


class CollisionAvoidance:
    def __init__(
        self,
        drone_radius: float = settings.drone_radius,
        safety_radius: float = settings.safety_radius,
        warning_radius: float = settings.warning_radius,
        avoidance_weight: float = 3.5,
    ):
        self.drone_radius = drone_radius
        self.safety_radius = safety_radius
        self.warning_radius = warning_radius
        self.avoidance_weight = avoidance_weight

    def compute_avoidance_and_metrics(
        self, drones: List[Drone]
    ) -> Tuple[Dict[str, np.ndarray], int, int, int]:
        """
        Compute evasive repulsive steering forces and count safety events:
        - warnings: dist < warning_radius
        - near_misses: dist < safety_radius
        - collisions: dist < 2 * drone_radius
        Returns (forces_dict, warnings_count, near_misses_count, collisions_count).
        """
        active_drones = [d for d in drones if d.status.value in ["ACTIVE", "RETURNING"]]
        n = len(active_drones)
        forces: Dict[str, np.ndarray] = {d.id: np.zeros(3, dtype=np.float64) for d in drones}

        if n <= 1:
            return forces, 0, 0, 0

        drone_ids = [d.id for d in active_drones]
        positions = np.array([d.position for d in active_drones], dtype=np.float64)

        # diff[i, j] = pos[i] - pos[j]
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        dist = np.linalg.norm(diff, axis=2)
        np.fill_diagonal(dist, np.inf)

        # Count metrics (each pair counted once using upper triangle)
        triu_indices = np.triu_indices(n, k=1)
        pairwise_dist = dist[triu_indices]

        actual_collision_threshold = 2.0 * self.drone_radius
        collisions = int(np.sum(pairwise_dist < actual_collision_threshold))
        near_misses = int(np.sum((pairwise_dist < self.safety_radius) & (pairwise_dist >= actual_collision_threshold)))
        warnings = int(np.sum((pairwise_dist < self.warning_radius) & (pairwise_dist >= self.safety_radius)))

        # Repulsive evasion force for drones within safety radius
        evasion_mask = dist < self.safety_radius

        # Avoid zero division
        safe_dist = np.where(evasion_mask, dist, np.inf)
        # Strong hyperbolic repulsion: (1/dist - 1/r_safe) * (diff / dist)
        repulsion_scale = np.where(
            evasion_mask,
            (1.0 / np.maximum(0.1, safe_dist) - 1.0 / self.safety_radius) / (safe_dist**2),
            0.0,
        )[:, :, np.newaxis]

        f_avoid = np.sum(diff * repulsion_scale, axis=1) * self.avoidance_weight

        # Clamp max collision force
        for i, drone_id in enumerate(drone_ids):
            force = f_avoid[i]
            norm = np.linalg.norm(force)
            if norm > settings.max_force * 1.5:
                force = (force / norm) * (settings.max_force * 1.5)
            forces[drone_id] = force

        return forces, warnings, near_misses, collisions
