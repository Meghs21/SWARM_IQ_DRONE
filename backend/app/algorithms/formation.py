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
        Construct 3D orthonormal rotation matrix R = [right, up, forward]
        aligned with forward velocity heading.
        """
        speed = np.linalg.norm(velocity)
        if speed > 0.5:
            forward = velocity / speed
        else:
            default_norm = np.linalg.norm(default_dir)
            forward = default_dir / default_norm if default_norm > 1e-3 else np.array([0.0, 0.0, 1.0])

        # Global up vector
        global_up = np.array([0.0, 1.0, 0.0])

        # Right vector perpendicular to forward and up
        right = np.cross(global_up, forward)
        right_norm = np.linalg.norm(right)
        if right_norm < 1e-3:
            # Forward is pointing straight up or down; pick alternate reference
            right = np.array([1.0, 0.0, 0.0])
        else:
            right = right / right_norm

        up = np.cross(forward, right)
        # Columns: [right, up, forward]
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
            radius = max(d * 1.5, (count * d) / (2.0 * np.pi))
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

        # Heading orientation
        def_dir = target_dir if target_dir is not None else np.array([1.0, 0.0, 1.0])
        rot_matrix = self.compute_heading_matrix(leader.velocity, def_dir)
        offsets = self.generate_slot_offsets(len(followers), formation_type)

        for i, follower in enumerate(followers):
            local_offset = offsets[i]
            # Transform local slot offset by leader heading rotation: world_offset = R * local_offset
            world_offset = rot_matrix @ local_offset
            desired_position = leader.position + world_offset

            # Assign target position to follower for visualization
            follower.target = desired_position

            # Spring-damper formation steering force
            to_slot = desired_position - follower.position
            dist = np.linalg.norm(to_slot)

            if dist > 0.1:
                # Seek slot with velocity damping
                desired_vel = (to_slot / dist) * min(follower.max_speed, dist * 2.0)
                steer = desired_vel - follower.velocity
                steer_norm = np.linalg.norm(steer)
                if steer_norm > settings.max_force:
                    steer = (steer / steer_norm) * settings.max_force

                forces[follower.id] = self.formation_weight * steer

        return forces
