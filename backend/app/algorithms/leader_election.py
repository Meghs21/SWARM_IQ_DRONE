"""
Dynamic Leader Election Algorithm for SwarmIQ.
Evaluates multi-factor fitness scores across the fleet and automatically elects
or fails over leaders upon battery depletion or drone failure.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np

from app.core.config import settings
from app.simulation.drone import Drone
from app.models.schemas import DroneRole, DroneStatus


class LeaderElection:
    def __init__(
        self,
        battery_weight: float = settings.battery_weight,
        communication_weight: float = settings.communication_weight,
        distance_weight: float = settings.distance_weight,
        health_weight: float = settings.health_weight,
        low_battery_threshold: float = settings.low_battery_threshold,
    ):
        self.battery_weight = battery_weight
        self.communication_weight = communication_weight
        self.distance_weight = distance_weight
        self.health_weight = health_weight
        self.low_battery_threshold = low_battery_threshold

    def calculate_score(self, drone: Drone, target_position: np.ndarray) -> float:
        """
        Calculate scalar fitness score for leadership:
        score = w_bat * (bat/100) + w_comm * comm + w_dist * (1 / (1 + dist)) + w_health * health
        """
        if drone.status != DroneStatus.ACTIVE:
            return -1.0

        # Health score: 1.0 for active with good battery, 0.0 otherwise
        health_score = 1.0 if drone.battery > self.low_battery_threshold else 0.2

        # Battery normalized [0, 1]
        bat_score = drone.battery / 100.0

        # Distance score: closer to target yields higher score
        dist = float(np.linalg.norm(drone.position - target_position))
        dist_score = 1.0 / (1.0 + dist * 0.05)

        # Comms score
        comm_score = drone.communication_strength

        score = (
            self.battery_weight * bat_score
            + self.communication_weight * comm_score
            + self.distance_weight * dist_score
            + self.health_weight * health_score
        )
        return float(score)

    def should_replace_leader(self, current_leader: Optional[Drone]) -> bool:
        """Check if current leader requires replacement."""
        if current_leader is None:
            return True
        if current_leader.status != DroneStatus.ACTIVE:
            return True
        if current_leader.battery <= self.low_battery_threshold:
            return True
        return False

    def elect_leader(
        self,
        drones: List[Drone],
        target_position: np.ndarray,
        current_leader_id: Optional[str] = None,
    ) -> Tuple[Optional[str], bool]:
        """
        Elect best leader candidate among active drones.
        Returns (new_leader_id, has_changed).
        """
        active_candidates = [
            d for d in drones if d.status == DroneStatus.ACTIVE and d.battery > self.low_battery_threshold
        ]

        if not active_candidates:
            # Fallback to any active drone regardless of battery if all are below threshold
            active_candidates = [d for d in drones if d.status == DroneStatus.ACTIVE]

        if not active_candidates:
            return None, (current_leader_id is not None)

        scores: Dict[str, float] = {}
        for d in active_candidates:
            score = self.calculate_score(d, target_position)
            # Give slight incumbent bonus to avoid jittery thrashing if leader is healthy
            if d.id == current_leader_id:
                score += 0.08
            scores[d.id] = score

        best_id = max(scores, key=scores.get)
        has_changed = (best_id != current_leader_id)

        return best_id, has_changed
