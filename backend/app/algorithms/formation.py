"""
Formation Controller for SwarmIQ.
Calculates desired formation target slots relative to leader position and heading.
Supports V-formation, Line, Grid, and Circle formations with smooth steering forces.
"""

from typing import Dict, List, Optional
import numpy as np

from app.core.config import settings
from app.simulation.drone import Drone
from app.models.schemas import FormationType, DroneRole, DroneStatus


class FormationController:
    def __init__(
        self,
        formation_spacing: float = settings.formation_spacing,
        formation_weight: float = settings.formation_weight,
    ):
        self.formation_spacing = formation_spacing
        self.formation_weight = formation_weight

    def compute_heading_matrix(self, velocity: np.ndarray, default_dir: np.ndarray) -> np.ndarray:
        """
        Construct horizontal planar rotation matrix aligned with forward heading (XZ plane).
        Prevents awkward pitch tilting during climb/descent.
        """
        speed = np.hypot(velocity[0], velocity[2])
        if speed > 0.5:
            forward = np.array([velocity[0], 0.0, velocity[2]], dtype=np.float64) / speed
        else:
            h_len = np.hypot(default_dir[0], default_dir[2])
            forward = (
                np.array([default_dir[0], 0.0, default_dir[2]], dtype=np.float64) / h_len
                if h_len > 1e-3
                else np.array([0.0, 0.0, 1.0], dtype=np.float64)
            )

        global_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(global_up, forward)
        r_norm = np.linalg.norm(right)
        right = right / r_norm if r_norm > 1e-3 else np.array([1.0, 0.0, 0.0])
        up = global_up

        return np.column_stack((right, up, forward))

    def generate_slot_offsets(self, count: int, formation_type: FormationType) -> List[np.ndarray]:
        """Generate local relative offsets for followers."""
        offsets: List[np.ndarray] = []
        d = self.formation_spacing

        if formation_type == FormationType.V:
            # V-wing formation: alternates left and right wings trailing behind
            for i in range(count):
                wing = 1 if i % 2 == 0 else -1
                rank = (i // 2) + 1
                # right offset = wing * rank * d, forward offset = -rank * d * 1.2
                offsets.append(np.array([wing * rank * d, 0.0, -rank * d * 1.2], dtype=np.float64))

        elif formation_type == FormationType.LINE:
            # Rank formation: line perpendicular to heading
            for i in range(count):
                side = 1 if i % 2 == 0 else -1
                dist = ((i // 2) + 1) * d
                offsets.append(np.array([side * dist, 0.0, -2.0], dtype=np.float64))

        elif formation_type == FormationType.GRID:
            # M x N rectangular grid trailing behind leader
            cols = int(np.ceil(np.sqrt(count)))
            for i in range(count):
                col = i % cols
                row = i // cols
                x_off = (col - (cols - 1) / 2.0) * d
                z_off = -(row + 1) * d
                offsets.append(np.array([x_off, 0.0, z_off], dtype=np.float64))

        elif formation_type == FormationType.CIRCLE:
            # Concentric ring formation around leader
            radius = max(d * 2.2, (count * d) / (2.0 * np.pi))
            angle_step = (2.0 * np.pi) / count if count > 0 else 0
            for i in range(count):
                theta = i * angle_step
                offsets.append(np.array([radius * np.cos(theta), 0.0, radius * np.sin(theta)], dtype=np.float64))

        return offsets

    def compute_formation_forces(
        self,
        drones: List[Drone],
        leader: Optional[Drone],
        formation_type: FormationType,
        target_dir: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        """Compute steering forces pulling followers toward their designated formation slots."""
        forces: Dict[str, np.ndarray] = {d.id: np.zeros(3, dtype=np.float64) for d in drones}

        if leader is None or leader.status != DroneStatus.ACTIVE:
            return forces

        followers = [
            d
            for d in drones
            if d.id != leader.id and d.status.value in ["ACTIVE", "RETURNING"] and d.role == DroneRole.FOLLOWER
        ]
        if not followers:
            return forces

        # Special optimized non-distorting circular slot allocation
        if formation_type == FormationType.CIRCLE:
            d = self.formation_spacing
            count = len(followers)
            radius = max(d * 2.2, (count * d) / (2.0 * np.pi))

            # Sort followers by angular azimuth relative to leader to prevent path crossing
            follower_angles = [
                (f, float(np.arctan2(f.position[2] - leader.position[2], f.position[0] - leader.position[0])))
                for f in followers
            ]
            follower_angles.sort(key=lambda item: item[1])

            angle_step = (2.0 * np.pi) / count if count > 0 else 0
            for idx, (follower, _) in enumerate(follower_angles):
                theta = idx * angle_step
                desired_position = np.array(
                    [
                        leader.position[0] + radius * np.cos(theta),
                        leader.position[1],
                        leader.position[2] + radius * np.sin(theta),
                    ],
                    dtype=np.float64,
                )

                follower.target = desired_position
                to_slot = desired_position - follower.position
                dist = np.linalg.norm(to_slot)

                if dist > 0.05:
                    desired_vel = (to_slot / dist) * min(follower.max_speed, dist * 2.5)
                    steer = desired_vel - follower.velocity
                    steer_norm = np.linalg.norm(steer)
                    if steer_norm > settings.max_force:
                        steer = (steer / steer_norm) * settings.max_force

                    # Higher weighting to overcome Boids cohesion inward pull
                    forces[follower.id] = self.formation_weight * 1.6 * steer

            return forces

        # Heading orientation for directional formations (V, Line, Grid)
        def_dir = target_dir if target_dir is not None else np.array([1.0, 0.0, 1.0])
        rot_matrix = self.compute_heading_matrix(leader.velocity, def_dir)
        offsets = self.generate_slot_offsets(len(followers), formation_type)

        for i, follower in enumerate(followers):
            local_offset = offsets[i]
            world_offset = rot_matrix @ local_offset
            desired_position = leader.position + world_offset

            follower.target = desired_position

            to_slot = desired_position - follower.position
            dist = np.linalg.norm(to_slot)

            if dist > 0.1:
                desired_vel = (to_slot / dist) * min(follower.max_speed, dist * 2.0)
                steer = desired_vel - follower.velocity
                steer_norm = np.linalg.norm(steer)
                if steer_norm > settings.max_force:
                    steer = (steer / steer_norm) * settings.max_force

                forces[follower.id] = self.formation_weight * steer

        return forces
