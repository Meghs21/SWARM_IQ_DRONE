"""
Mission Manager for SwarmIQ.
Controls mission parameters, waypoints, status lifecycle, and completion metrics.
"""

from typing import List, Optional
import numpy as np

from app.models.schemas import MissionStatus, MissionState, FormationType, Vector3D
from app.core.config import settings


class MissionManager:
    def __init__(
        self,
        start_position: Optional[np.ndarray] = None,
        target_position: Optional[np.ndarray] = None,
        formation: FormationType = FormationType.V,
    ):
        self.status: MissionStatus = MissionStatus.IDLE
        self.start_position = (
            np.array(start_position, dtype=np.float64)
            if start_position is not None
            else np.array([-60.0, 10.0, -60.0], dtype=np.float64)
        )
        self.target_position = (
            np.array(target_position, dtype=np.float64)
            if target_position is not None
            else np.array([60.0, 15.0, 60.0], dtype=np.float64)
        )
        self.formation: FormationType = formation
        self.waypoints: List[np.ndarray] = [np.copy(self.target_position)]
        self.current_waypoint_idx: int = 0
        self.elapsed_time: float = 0.0
        self.initial_distance: float = float(np.linalg.norm(self.target_position - self.start_position))
        self.distance_to_target: float = self.initial_distance
        self.progress: float = 0.0

    def start(self) -> None:
        if self.status in [MissionStatus.IDLE, MissionStatus.INITIALIZING, MissionStatus.PAUSED]:
            self.status = MissionStatus.RUNNING

    def pause(self) -> None:
        if self.status == MissionStatus.RUNNING:
            self.status = MissionStatus.PAUSED

    def resume(self) -> None:
        if self.status == MissionStatus.PAUSED:
            self.status = MissionStatus.RUNNING

    def reset(
        self,
        start_pos: Optional[np.ndarray] = None,
        target_pos: Optional[np.ndarray] = None,
        formation: Optional[FormationType] = None,
    ) -> None:
        self.status = MissionStatus.IDLE
        self.elapsed_time = 0.0
        if start_pos is not None:
            self.start_position = np.array(start_pos, dtype=np.float64)
        if target_pos is not None:
            self.target_position = np.array(target_pos, dtype=np.float64)
        if formation is not None:
            self.formation = formation

        self.initial_distance = float(np.linalg.norm(self.target_position - self.start_position))
        self.distance_to_target = self.initial_distance
        self.progress = 0.0
        self.waypoints = [np.copy(self.target_position)]
        self.current_waypoint_idx = 0

    def set_waypoints(self, waypoints: List[np.ndarray]) -> None:
        if waypoints:
            self.waypoints = [np.array(w, dtype=np.float64) for w in waypoints]
            self.current_waypoint_idx = 0

    def get_current_waypoint(self) -> Optional[np.ndarray]:
        if not self.waypoints or self.current_waypoint_idx >= len(self.waypoints):
            return self.target_position
        return self.waypoints[self.current_waypoint_idx]

    def advance_waypoint_if_reached(self, leader_pos: np.ndarray, threshold: float = 4.0) -> bool:
        """Check if leader reached current waypoint and advance to next."""
        current_wp = self.get_current_waypoint()
        if current_wp is None:
            return False

        dist = float(np.linalg.norm(leader_pos - current_wp))
        if dist < threshold and self.current_waypoint_idx < len(self.waypoints) - 1:
            self.current_waypoint_idx += 1
            return True
        return False

    def update(self, dt: float, leader_pos: Optional[np.ndarray]) -> None:
        if self.status != MissionStatus.RUNNING:
            if self.status == MissionStatus.COMPLETED:
                self.distance_to_target = 0.0
                self.progress = 100.0
            return

        self.elapsed_time += dt

        if leader_pos is not None:
            self.advance_waypoint_if_reached(leader_pos)
            self.distance_to_target = float(np.linalg.norm(self.target_position - leader_pos))

            # Progress calculation: strictly bounded [0, 100]
            dist_traveled = max(0.0, self.initial_distance - self.distance_to_target)
            self.progress = min(100.0, max(0.0, (dist_traveled / max(1.0, self.initial_distance)) * 100.0))

            if self.distance_to_target <= settings.goal_reached_threshold:
                self.progress = 100.0
                self.distance_to_target = 0.0
                self.status = MissionStatus.COMPLETED

    def to_state(self) -> MissionState:
        dist = 0.0 if self.status == MissionStatus.COMPLETED else round(self.distance_to_target, 2)
        prog = 100.0 if self.status == MissionStatus.COMPLETED else round(self.progress, 1)
        return MissionState(
            status=self.status,
            progress=prog,
            target=Vector3D(
                x=round(float(self.target_position[0]), 2),
                y=round(float(self.target_position[1]), 2),
                z=round(float(self.target_position[2]), 2),
            ),
            start_position=Vector3D(
                x=round(float(self.start_position[0]), 2),
                y=round(float(self.start_position[1]), 2),
                z=round(float(self.start_position[2]), 2),
            ),
            distance_to_target=dist,
            elapsed_time=round(self.elapsed_time, 1),
            formation=self.formation,
        )
