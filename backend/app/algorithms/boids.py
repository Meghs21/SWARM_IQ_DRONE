"""
Boids Swarming Engine for SwarmIQ.
Implements vectorized Reynolds flocking: Separation, Alignment, and Cohesion.
Optimized for 100+ agents using NumPy pairwise distance calculations.
"""

from typing import Dict, List
import numpy as np

from app.core.config import settings
from app.simulation.drone import Drone
from app.models.schemas import DroneRole


class BoidsEngine:
    def __init__(
        self,
        separation_weight: float = settings.separation_weight,
        alignment_weight: float = settings.alignment_weight,
        cohesion_weight: float = settings.cohesion_weight,
        separation_radius: float = settings.separation_radius,
        neighbor_radius: float = settings.neighbor_radius,
    ):
        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.cohesion_weight = cohesion_weight
        self.separation_radius = separation_radius
        self.neighbor_radius = neighbor_radius

    def compute_boids_forces(
        self, drones: List[Drone], cohesion_factor: float = 1.0
    ) -> Dict[str, np.ndarray]:
        """
        Compute total Boids steering forces for all active drones using vectorized NumPy.
        Returns a mapping from drone_id to 3D force vector np.ndarray.
        """
        active_drones = [d for d in drones if d.status.value in ["ACTIVE", "RETURNING"]]
        n = len(active_drones)
        forces: Dict[str, np.ndarray] = {d.id: np.zeros(3, dtype=np.float64) for d in drones}

        if n <= 1:
            return forces

        drone_ids = [d.id for d in active_drones]
        positions = np.array([d.position for d in active_drones], dtype=np.float64)  # (N, 3)
        velocities = np.array([d.velocity for d in active_drones], dtype=np.float64)  # (N, 3)

        # Pairwise differences: diff[i, j] = pos[i] - pos[j]
        # shape: (N, N, 3)
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]

        # Pairwise distances: dist[i, j]
        # shape: (N, N)
        dist = np.linalg.norm(diff, axis=2)

        # Avoid division by zero on diagonal (self-distance)
        np.fill_diagonal(dist, np.inf)

        # 1. SEPARATION
        # Mask where distance < separation_radius
        sep_mask = dist < self.separation_radius
        # Repulsive force proportional to 1 / (dist^2)
        safe_dist = np.where(sep_mask, np.maximum(0.1, dist), 1.0)
        inv_dist_sq = np.where(sep_mask, 1.0 / (safe_dist**2), 0.0)[:, :, np.newaxis]
        # Force: sum_j (pos_i - pos_j) / dist_ij^2
        f_sep = np.sum(diff * inv_dist_sq, axis=1)  # (N, 3)

        # 2. ALIGNMENT & 3. COHESION
        # Neighbor mask where distance < neighbor_radius
        neighbor_mask = dist < self.neighbor_radius
        neighbor_counts = np.sum(neighbor_mask, axis=1, keepdims=True)  # (N, 1)

        # Alignment: steer towards average velocity of neighbors
        # sum_j vel_j for j in neighbors
        vel_mask = neighbor_mask[:, :, np.newaxis]
        neighbor_vel_sum = np.sum(vel_mask * velocities[np.newaxis, :, :], axis=1)  # (N, 3)

        # Cohesion: steer towards center of mass of neighbors
        neighbor_pos_sum = np.sum(vel_mask * positions[np.newaxis, :, :], axis=1)  # (N, 3)

        # Normalize by neighbor count where neighbors exist
        has_neighbors = (neighbor_counts > 0).squeeze()

        f_align = np.zeros_like(velocities)
        f_coh = np.zeros_like(positions)

        if np.any(has_neighbors):
            valid_counts = np.maximum(1, neighbor_counts)
            avg_vel = neighbor_vel_sum / valid_counts
            avg_pos = neighbor_pos_sum / valid_counts

            # Alignment steering force = avg_vel - current_vel
            f_align = np.where(neighbor_counts > 0, avg_vel - velocities, 0.0)
            # Cohesion steering force = avg_pos - current_pos
            f_coh = np.where(neighbor_counts > 0, avg_pos - positions, 0.0)

        # Combine weighted Boids forces
        total_boids = (
            self.separation_weight * f_sep
            + self.alignment_weight * f_align
            + (self.cohesion_weight * cohesion_factor) * f_coh
        )

        for i, drone in enumerate(active_drones):
            if drone.role == DroneRole.LEADER:
                forces[drone.id] = np.zeros(3, dtype=np.float64)
            else:
                forces[drone.id] = total_boids[i]

        return forces
