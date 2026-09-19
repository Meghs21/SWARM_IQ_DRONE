"""
Goal Navigation and Waypoint Following Module for SwarmIQ.
Calculates attractive steering forces toward mission targets and waypoints.
"""

from typing import Dict, List, Optional
import numpy as np

from app.core.config import settings
from app.simulation.drone import Drone
from app.models.schemas import DroneRole, DroneStatus


class GoalNavigation:
    def __init__(self, goal_weight: float = settings.goal_weight):
        self.goal_weight = goal_weight

    def compute_leader_steering(
        self,
        leader: Drone,
        current_waypoint: np.ndarray,
        slowdown_radius: float = 8.0,
    ) -> np.ndarray:
        """
        Compute Reynolds seek/arrival steering force for leader toward current waypoint.
        F_steer = desired_velocity - current_velocity
        """
        if leader.status != DroneStatus.ACTIVE:
            return np.zeros(3, dtype=np.float64)

        to_target = current_waypoint - leader.position
        distance = np.linalg.norm(to_target)

        if distance < 1e-3:
            return -leader.velocity * 0.5  # Brake smoothly at destination

        direction = to_target / distance

        # Arrival behavior: ramp down speed as leader nears the waypoint
        if distance < slowdown_radius:
            desired_speed = leader.max_speed * (distance / slowdown_radius)
        else:
            desired_speed = leader.max_speed

        desired_velocity = direction * desired_speed
        steering_force = desired_velocity - leader.velocity

        # Clamp steering force to max_force
        force_norm = np.linalg.norm(steering_force)
        if force_norm > settings.max_force:
            steering_force = (steering_force / force_norm) * settings.max_force

        return self.goal_weight * steering_force

    def compute_returning_drones_steering(self, returning_drones: List[Drone]) -> Dict[str, np.ndarray]:
        """Compute steering for drones returning to base due to low battery."""
        forces: Dict[str, np.ndarray] = {}
        for drone in returning_drones:
            target = drone.home_position
            to_target = target - drone.position
            dist = np.linalg.norm(to_target)
            if dist < 1.0:
                # Landed at home
                drone.status = DroneStatus.COMPLETED
                forces[drone.id] = -drone.velocity
            else:
                dir_vec = to_target / dist
                desired_vel = dir_vec * min(drone.max_speed * 0.6, dist)
                forces[drone.id] = self.goal_weight * (desired_vel - drone.velocity)
        return forces
