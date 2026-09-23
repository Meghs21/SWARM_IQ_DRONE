"""
SwarmIQ Central Simulation Configuration.
Contains all hyperparameters for physics, algorithms, environment, and networking.
"""

from pydantic import BaseModel, Field
from typing import Tuple


class SimulationConfig(BaseModel):
    # Simulation Timing
    tick_rate_hz: int = Field(default=25, description="Simulation ticks per second")
    time_step: float = Field(default=0.04, description="Physics delta time dt in seconds (1/25)")

    # Environment Bounds: [min_x, max_x], [min_y, max_y], [min_z, max_z]
    bounds_x: Tuple[float, float] = (-250.0, 250.0)
    bounds_y: Tuple[float, float] = (0.5, 60.0)  # Drone flight altitude
    bounds_z: Tuple[float, float] = (-250.0, 250.0)

    # Drone Physical Constraints
    default_drone_count: int = 50
    drone_mass: float = 1.0  # kg
    max_speed: float = 12.0  # m/s
    max_acceleration: float = 8.0  # m/s^2
    max_force: float = 10.0  # N

    # Radii & Distances (meters)
    drone_radius: float = 0.4  # physical collision boundary
    safety_radius: float = 2.0  # collision avoidance repulsion triggers
    warning_radius: float = 3.5  # near-miss proximity warning triggers
    communication_range: float = 40.0  # inter-drone mesh comms

    # Boids Parameters
    separation_weight: float = 2.2
    alignment_weight: float = 1.2
    cohesion_weight: float = 1.0
    separation_radius: float = 3.0
    neighbor_radius: float = 12.0

    # Formation Parameters
    formation_weight: float = 1.8
    formation_spacing: float = 3.5  # distance between slots in meters

    # Goal & Navigation Parameters
    goal_weight: float = 2.5
    goal_reached_threshold: float = 3.0  # meters

    # Potential Field Obstacle Avoidance
    obstacle_repulsion_weight: float = 4.0
    obstacle_influence_distance: float = 8.0  # distance where obstacles exert force

    # Leader Election Weights & Thresholds
    battery_weight: float = 0.35
    communication_weight: float = 0.20
    distance_weight: float = 0.30
    health_weight: float = 0.15
    low_battery_threshold: float = 20.0  # triggers leader stepdown & return to base
    critical_battery_threshold: float = 5.0

    # Battery Discharge Rates
    battery_base_drain: float = 0.05  # % per second hovering
    battery_speed_drain: float = 0.04  # % per unit speed per second
    battery_accel_drain: float = 0.02  # % per unit acceleration per second


# Global default configuration instance
settings = SimulationConfig()
