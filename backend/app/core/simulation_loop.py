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
        self.current_scenario: Optional[int] = None

    def register_subscriber(self, callback: Callable[[SimulationSnapshot], None]) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unregister_subscriber(self, callback: Callable[[SimulationSnapshot], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def start(self) -> None:
        self.mission.start()
        if not self.is_running:
            self.is_running = True
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
        clear_obstacles: bool = True,
    ) -> None:
        self.mission.reset(start_pos=start_pos, target_pos=target_pos, formation=formation)
        self.swarm.initialize_drones(
            count=drone_count,
            spawn_center=self.mission.start_position,
            formation=formation,
        )
        if clear_obstacles:
            self.environment.clear_obstacles()
            self.current_scenario = None
        self.formation.persistent_slots.clear()
        self.formation.last_formation = None
        self.replan_needed = True

    def set_drone_count(self, count: int) -> None:
        """Dynamically resize fleet while preserving scenario obstacles and mission progress."""
        if count <= 0:
            return

        leader = self.swarm.get_leader()
        if self.mission.status in [MissionStatus.RUNNING, MissionStatus.PAUSED] and leader is not None:
            current_drones = self.swarm.drones
            if count == len(current_drones):
                return
            if count < len(current_drones):
                followers = [d for d in current_drones.values() if d.id != leader.id]
                followers.sort(key=lambda d: np.linalg.norm(d.position - leader.position))
                kept_followers = followers[: count - 1]
                self.swarm.drones = {leader.id: leader}
                for f in kept_followers:
                    self.swarm.drones[f.id] = f
            else:
                needed = count - len(current_drones)
                existing_indices = set()
                for did in current_drones.keys():
                    try:
                        num = int(did.replace("DRONE_", ""))
                        existing_indices.add(num)
                    except ValueError:
                        pass
                next_idx = 1
                for _ in range(needed):
                    while next_idx in existing_indices:
                        next_idx += 1
                    existing_indices.add(next_idx)
                    drone_id = f"DRONE_{next_idx:02d}"
                    offset = np.random.uniform(-4.0, 4.0, size=3)
                    offset[1] = np.random.uniform(-0.5, 0.5)
                    from app.simulation.drone import Drone
                    from app.models.schemas import DroneRole
                    new_drone = Drone(
                        drone_id=drone_id,
                        position=leader.position + offset,
                        role=DroneRole.FOLLOWER,
                        battery=100.0,
                    )
                    self.swarm.drones[drone_id] = new_drone
            self.formation.persistent_slots.clear()
            self.formation.last_formation = None
        else:
            spawn_center = self.mission.start_position if self.mission else np.array([-60.0, 10.0, -60.0])
            self.swarm.initialize_drones(
                count=count,
                spawn_center=spawn_center,
                formation=self.mission.formation,
            )
            self.formation.persistent_slots.clear()
            self.formation.last_formation = None
            self.replan_needed = True

    def set_formation(self, formation: FormationType) -> None:
        self.mission.formation = formation
        self.formation.persistent_slots.clear()
        self.formation.last_formation = None

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
            # Decouple cohesion when in geometric formation to prevent ring/wing collapse
            cohesion_factor = 0.0 if self.mission.formation is not None else 1.0
            boids_forces = self.boids.compute_boids_forces(all_drones, cohesion_factor=cohesion_factor)

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
                    nav_forces[leader.id] = self.navigation.compute_leader_steering(
                        leader, current_wp, followers=all_drones
                    )

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
                b_force = boids_forces.get(drone.id, np.zeros(3))
                f_force = formation_forces.get(drone.id, np.zeros(3))
                n_force = nav_forces.get(drone.id, np.zeros(3))
                o_force = obs_forces.get(drone.id, np.zeros(3))
                c_force = col_forces.get(drone.id, np.zeros(3))

                # Prioritize obstacle avoidance over formation keeping near obstacles
                o_mag = np.linalg.norm(o_force)
                if o_mag > 1.0:
                    form_attenuation = max(0.05, 1.0 - (o_mag / (settings.max_force * 2.5)))
                    f_force = f_force * form_attenuation

                total_force = b_force + f_force + n_force + o_force + c_force
                drone.apply_force(total_force)

        elif self.mission.status == MissionStatus.COMPLETED:
            # Swarm reached goal: active braking deceleration & station-keeping hover in formation
            leader = self.swarm.get_leader()
            if leader is not None:
                # Decelerate leader to zero at the exact target coordinates
                lead_err = self.mission.target_position - leader.position
                lead_brake = -leader.velocity * 4.0 + lead_err * 2.5
                lead_norm = np.linalg.norm(lead_brake)
                if lead_norm > settings.max_force:
                    lead_brake = (lead_brake / lead_norm) * settings.max_force
                leader.apply_force(lead_brake)
                if np.linalg.norm(lead_err) < 0.25 and np.linalg.norm(leader.velocity) < 0.2:
                    leader.velocity = np.zeros(3, dtype=np.float64)
                    leader.position = np.copy(self.mission.target_position)

            # Followers hover in their assigned formation slots around target
            target_dir = np.array([1.0, 0.0, 1.0])
            formation_forces = self.formation.compute_formation_forces(
                all_drones,
                leader,
                self.mission.formation,
                target_dir=target_dir,
            )
            col_forces, _, _, _ = self.collision.compute_avoidance_and_metrics(all_drones)

            for drone in active_drones:
                if leader is not None and drone.id == leader.id:
                    continue
                f_force = formation_forces.get(drone.id, np.zeros(3))
                c_force = col_forces.get(drone.id, np.zeros(3))
                brake = -drone.velocity * 4.0
                total_force = f_force + c_force + brake
                f_norm = np.linalg.norm(total_force)
                if f_norm > settings.max_force:
                    total_force = (total_force / f_norm) * settings.max_force
                drone.apply_force(total_force)
                if drone.target is not None and np.linalg.norm(drone.position - drone.target) < 0.25 and np.linalg.norm(drone.velocity) < 0.2:
                    drone.velocity = np.zeros(3, dtype=np.float64)

        # 10. Advance drone kinematics and battery
        self.swarm.update(dt)

        # Enforce physical obstacle boundary hulls (prevent passing through)
        if self.environment.obstacles:
            hull_margin = 0.8
            for drone in active_drones:
                for obs in self.environment.obstacles:
                    s_dist, away_vec = self.potential_field._distance_and_direction(drone.position, obs)
                    # If drone penetrates obstacle surface or touches hull margin
                    if s_dist < hull_margin:
                        penetration = hull_margin - s_dist
                        drone.position += away_vec * penetration
                        # Deflect velocity: zero out velocity component heading towards obstacle
                        v_dot = np.dot(drone.velocity, away_vec)
                        if v_dot < 0:
                            drone.velocity -= v_dot * away_vec
                            # Tangential slide along obstacle boundary to maintain forward momentum
                            up_dir = np.array([0.0, 1.0, 0.0])
                            tangent = np.cross(up_dir, away_vec)
                            t_len = np.linalg.norm(tangent)
                            if t_len > 1e-3:
                                tangent = tangent / t_len
                                if np.dot(tangent, drone.velocity) < 0:
                                    tangent = -tangent
                                drone.velocity += tangent * 1.5

        # 11. Update mission progression
        leader = self.swarm.get_leader()
        leader_pos = leader.position if leader else None
        self.mission.update(dt, leader_pos)

    def load_scenario(self, scenario_id: int) -> None:
        """Preset scenario initialization."""
        self.current_scenario = scenario_id
        if scenario_id == 1:
            # Scenario 1 - Open Field (20 drones, No obstacles, V formation)
            self.reset(drone_count=20, formation=FormationType.V, clear_obstacles=True)
            self.current_scenario = 1
            self.replan_leader_path()

        elif scenario_id == 2:
            # Scenario 2 - Obstacle Course (50 drones, static pillars, A* path)
            self.reset(drone_count=50, formation=FormationType.V, clear_obstacles=True)
            self.current_scenario = 2
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
            self.reset(drone_count=50, formation=FormationType.LINE, clear_obstacles=True)
            self.current_scenario = 3
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
            self.reset(drone_count=50, formation=FormationType.GRID, clear_obstacles=True)
            self.current_scenario = 4
            self.environment.add_obstacle(
                Obstacle("BLOCK_1", ObstacleType.BOX, [-10.0, 10.0, -10.0], [10.0, 20.0, 10.0])
            )
            self.replan_leader_path()

        elif scenario_id == 5:
            # Scenario 5 - Large Swarm (100 drones, complex environment)
            self.reset(drone_count=100, formation=FormationType.CIRCLE, clear_obstacles=True)
            self.current_scenario = 5
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
