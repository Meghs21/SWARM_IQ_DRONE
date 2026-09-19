"""
Simulation Loop and Engine Orchestrator for SwarmIQ.
Integrates the complete hierarchical autonomous swarm pipeline:
Mission -> Leader Election -> A* Path Planning -> Formation & Boids -> Potential Fields & Collision Avoidance -> Kinematics.
"""

import asyncio
import time
from typing import Optional, Callable, List, Dict
import numpy as np

from app.core.config import settings
from app.simulation.swarm import Swarm
from app.simulation.environment import Environment, Obstacle
from app.simulation.mission import MissionManager
from app.algorithms.boids import BoidsEngine
from app.algorithms.navigation import GoalNavigation
from app.algorithms.collision import CollisionAvoidance
from app.algorithms.astar import AStarPlanner
from app.algorithms.potential_field import PotentialField
from app.algorithms.formation import FormationController
from app.algorithms.leader_election import LeaderElection
from app.models.schemas import (
    SimulationSnapshot,
    MissionStatus,
    FormationType,
    ObstacleType,
    Vector3D,
)


class SimulationEngine:
    def __init__(self):
        self.swarm = Swarm(drone_count=settings.default_drone_count)
        self.environment = Environment()
        self.mission = MissionManager()

        # Initialize core algorithm engines
        self.boids = BoidsEngine()
        self.navigation = GoalNavigation()
        self.collision = CollisionAvoidance()
        self.astar = AStarPlanner()
        self.potential_field = PotentialField()
        self.formation = FormationController()
        self.leader_election = LeaderElection()

        self.is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._subscribers: List[Callable[[SimulationSnapshot], None]] = []

        # Performance monitoring
        self.target_fps: float = float(settings.tick_rate_hz)
        self.dt: float = settings.time_step
        self.measured_rate: float = self.target_fps
        self.last_tick_time: float = time.time()
        self.tick_counter: int = 0
        self.rate_timer: float = time.time()

        # Path planning state
        self.replan_needed: bool = True

    def register_subscriber(self, callback: Callable[[SimulationSnapshot], None]) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unregister_subscriber(self, callback: Callable[[SimulationSnapshot], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self.mission.start()
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._run_loop())
            except RuntimeError:
                self._task = None

    def pause(self) -> None:
        self.mission.pause()

    def resume(self) -> None:
        self.mission.resume()

    def reset(
        self,
        drone_count: int = settings.default_drone_count,
        start_pos: Optional[np.ndarray] = None,
        target_pos: Optional[np.ndarray] = None,
        formation: FormationType = FormationType.V,
    ) -> None:
        self.mission.reset(start_pos=start_pos, target_pos=target_pos, formation=formation)
        self.swarm.initialize_drones(
            count=drone_count,
            spawn_center=self.mission.start_position,
        )
        self.environment.clear_obstacles()
        self.replan_needed = True

    def set_formation(self, formation: FormationType) -> None:
        self.mission.formation = formation

    def replan_leader_path(self) -> None:
        """Trigger A* path planner from leader position to destination."""
        leader = self.swarm.get_leader()
        if leader:
            waypoints = self.astar.plan_path(
                leader.position,
                self.mission.target_position,
                self.environment.obstacles,
            )
            self.mission.set_waypoints(waypoints)
            self.replan_needed = False

    async def stop(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run_loop(self) -> None:
        """Main non-blocking async loop maintaining target tick rate."""
        target_interval = 1.0 / self.target_fps
        self.rate_timer = time.time()
        self.tick_counter = 0

        while self.is_running:
            start_time = time.monotonic()

            # Execute single simulation step
            self.step(self.dt)

            # Performance measurement
            self.tick_counter += 1
            now = time.time()
            if now - self.rate_timer >= 1.0:
                self.measured_rate = self.tick_counter / (now - self.rate_timer)
                self.tick_counter = 0
                self.rate_timer = now

            # Broadcast snapshot
            snapshot = self.get_snapshot()
            for sub in list(self._subscribers):
                try:
                    sub(snapshot)
                except Exception:
                    pass

            elapsed = time.monotonic() - start_time
            sleep_time = max(0.001, target_interval - elapsed)
            await asyncio.sleep(sleep_time)

    def step(self, dt: float) -> None:
        """Single deterministic hierarchical simulation tick."""
        # 1. Update dynamic environment
        self.environment.update(dt)

        all_drones = list(self.swarm.drones.values())
        active_drones = [d for d in all_drones if d.status.value in ["ACTIVE", "RETURNING"]]
        returning_drones = [d for d in all_drones if d.status.value == "RETURNING"]

        # 2. Leader election & failover check
        current_leader = self.swarm.get_leader()
        if self.leader_election.should_replace_leader(current_leader):
            new_leader_id, changed = self.leader_election.elect_leader(
                all_drones,
                self.mission.target_position,
                self.swarm.leader_id,
            )
            if changed and new_leader_id:
                self.swarm.set_leader(new_leader_id)
                self.replan_needed = True

        # 3. Global path planning for leader
        if self.replan_needed and self.mission.status == MissionStatus.RUNNING:
            self.replan_leader_path()

        # If mission is running, calculate complete force synthesis
        if self.mission.status == MissionStatus.RUNNING:
            # 4. Calculate Boids forces (Separation, Alignment, Cohesion)
            boids_forces = self.boids.compute_boids_forces(all_drones)

            # 5. Calculate Formation forces
            leader = self.swarm.get_leader()
            target_dir = (
                self.mission.target_position - leader.position if leader is not None else np.array([1.0, 0.0, 1.0])
            )
            formation_forces = self.formation.compute_formation_forces(
                all_drones,
                leader,
                self.mission.formation,
                target_dir=target_dir,
            )

            # 6. Calculate Navigation forces
            nav_forces: Dict[str, np.ndarray] = {d.id: np.zeros(3, dtype=np.float64) for d in all_drones}
            if leader is not None:
                current_wp = self.mission.get_current_waypoint()
                if current_wp is not None:
                    nav_forces[leader.id] = self.navigation.compute_leader_steering(leader, current_wp)

            ret_forces = self.navigation.compute_returning_drones_steering(returning_drones)
            for did, f in ret_forces.items():
                nav_forces[did] = f

            # 7. Calculate Obstacle repulsive potential fields
            obs_forces = self.potential_field.compute_obstacle_repulsion(
                all_drones, self.environment.obstacles
            )

            # 8. Calculate Drone-to-drone collision avoidance & proximity metrics
            col_forces, warnings, near_misses, collisions = self.collision.compute_avoidance_and_metrics(
                all_drones
            )
            self.swarm.collision_warnings += warnings
            self.swarm.near_misses += near_misses
            self.swarm.actual_collisions += collisions

            # 9. Synthesize weighted forces and apply to drones
            for drone in active_drones:
                total_force = (
                    boids_forces.get(drone.id, np.zeros(3))
                    + formation_forces.get(drone.id, np.zeros(3))
                    + nav_forces.get(drone.id, np.zeros(3))
                    + obs_forces.get(drone.id, np.zeros(3))
                    + col_forces.get(drone.id, np.zeros(3))
                )
                drone.apply_force(total_force)

        # 10. Advance drone kinematics and battery
        self.swarm.update(dt)

        # 11. Update mission progression
        leader = self.swarm.get_leader()
        leader_pos = leader.position if leader else None
        self.mission.update(dt, leader_pos)

    def load_scenario(self, scenario_id: int) -> None:
        """Preset scenario initialization."""
        if scenario_id == 1:
            # Scenario 1 - Open Field (20 drones, No obstacles, V formation)
            self.reset(drone_count=20, formation=FormationType.V)
            self.replan_leader_path()

        elif scenario_id == 2:
            # Scenario 2 - Obstacle Course (50 drones, static pillars, A* path)
            self.reset(drone_count=50, formation=FormationType.V)
            # Add static pillars
            self.environment.add_obstacle(
                Obstacle("PILLAR_1", ObstacleType.CYLINDER, [-20.0, 0.0, -20.0], [8.0, 40.0, 0.0])
            )
            self.environment.add_obstacle(
                Obstacle("PILLAR_2", ObstacleType.CYLINDER, [10.0, 0.0, 10.0], [9.0, 40.0, 0.0])
            )
            self.environment.add_obstacle(
                Obstacle("PILLAR_3", ObstacleType.BOX, [0.0, 15.0, 0.0], [12.0, 25.0, 12.0])
            )
            self.replan_leader_path()

        elif scenario_id == 3:
            # Scenario 3 - Dynamic Obstacles (50 drones, moving obstacles)
            self.reset(drone_count=50, formation=FormationType.LINE)
            self.environment.add_obstacle(
                Obstacle(
                    "DYN_SPHERE_1",
                    ObstacleType.SPHERE,
                    [-10.0, 12.0, -10.0],
                    [5.0, 5.0, 5.0],
                    is_dynamic=True,
                    velocity=[3.0, 0.0, -2.0],
                    trajectory_type="linear",
                    trajectory_bounds=([-30.0, 5.0, -30.0], [30.0, 25.0, 30.0]),
                )
            )
            self.environment.add_obstacle(
                Obstacle(
                    "DYN_SPHERE_2",
                    ObstacleType.SPHERE,
                    [15.0, 14.0, 15.0],
                    [6.0, 6.0, 6.0],
                    is_dynamic=True,
                    velocity=[-2.5, 0.0, 2.5],
                    trajectory_type="circle",
                )
            )
            self.replan_leader_path()

        elif scenario_id == 4:
            # Scenario 4 - Leader Failure (50 drones, leader fails during mission)
            self.reset(drone_count=50, formation=FormationType.GRID)
            self.environment.add_obstacle(
                Obstacle("BLOCK_1", ObstacleType.BOX, [-10.0, 10.0, -10.0], [10.0, 20.0, 10.0])
            )
            self.replan_leader_path()

        elif scenario_id == 5:
            # Scenario 5 - Large Swarm (100 drones, complex environment)
            self.reset(drone_count=100, formation=FormationType.CIRCLE)
            self.environment.add_obstacle(
                Obstacle("TOWER_1", ObstacleType.CYLINDER, [-30.0, 0.0, -10.0], [7.0, 45.0, 0.0])
            )
            self.environment.add_obstacle(
                Obstacle("TOWER_2", ObstacleType.CYLINDER, [20.0, 0.0, 20.0], [8.0, 45.0, 0.0])
            )
            self.environment.add_obstacle(
                Obstacle(
                    "PATROL_OBS",
                    ObstacleType.SPHERE,
                    [0.0, 15.0, 0.0],
                    [6.0, 6.0, 6.0],
                    is_dynamic=True,
                    velocity=[2.0, 0.0, 0.0],
                    trajectory_type="circle",
                )
            )
            self.replan_leader_path()

    def get_snapshot(self) -> SimulationSnapshot:
        """Produce full state snapshot for WebSocket broadcasting."""
        waypoints_3d = [
            Vector3D(x=round(float(w[0]), 2), y=round(float(w[1]), 2), z=round(float(w[2]), 2))
            for w in self.mission.waypoints
        ]
        return SimulationSnapshot(
            timestamp=time.time(),
            mission=self.mission.to_state(),
            leader_id=self.swarm.leader_id,
            waypoints=waypoints_3d,
            drones=[d.to_state() for d in self.swarm.drones.values()],
            obstacles=self.environment.get_obstacle_states(),
            metrics=self.swarm.get_metrics(
                fps=self.measured_rate,
                update_rate=self.measured_rate,
            ),
        )


# Global singleton simulation engine instance
engine = SimulationEngine()
