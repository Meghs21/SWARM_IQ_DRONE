import unittest
import numpy as np

from app.simulation.swarm import Swarm
from app.simulation.environment import Environment, Obstacle
from app.simulation.mission import MissionManager
from app.core.simulation_loop import SimulationEngine
from app.models.schemas import ObstacleType, MissionStatus, DroneRole


class TestSimulationLoop(unittest.TestCase):
    def test_swarm_initialization(self):
        swarm = Swarm(drone_count=25, spawn_center=np.array([0.0, 10.0, 0.0]))
        self.assertEqual(len(swarm.drones), 25)
        self.assertIsNotNone(swarm.leader_id)
        self.assertEqual(swarm.drones[swarm.leader_id].role, DroneRole.LEADER)

        ids, pos, vel = swarm.get_positions_and_velocities()
        self.assertEqual(len(ids), 25)
        self.assertEqual(pos.shape, (25, 3))
        self.assertEqual(vel.shape, (25, 3))

    def test_dynamic_obstacle(self):
        env = Environment()
        obs = Obstacle(
            obstacle_id="OBS_01",
            obstacle_type=ObstacleType.SPHERE,
            position=[0.0, 10.0, 0.0],
            size=[3.0, 3.0, 3.0],
            is_dynamic=True,
            velocity=[2.0, 0.0, 0.0],
            trajectory_type="linear",
            trajectory_bounds=([-10.0, 0.0, -10.0], [10.0, 20.0, 10.0]),
        )
        env.add_obstacle(obs)
        env.update(dt=1.0)
        self.assertAlmostEqual(obs.position[0], 2.0, places=4)

    def test_mission_lifecycle(self):
        mission = MissionManager(
            start_position=np.array([0.0, 10.0, 0.0]),
            target_position=np.array([100.0, 10.0, 0.0]),
        )
        self.assertEqual(mission.status, MissionStatus.IDLE)
        mission.start()
        self.assertEqual(mission.status, MissionStatus.RUNNING)

        # Update when leader is at [50, 10, 0] (halfway)
        mission.update(dt=1.0, leader_pos=np.array([50.0, 10.0, 0.0]))
        self.assertAlmostEqual(mission.progress, 50.0, places=1)

        # Update when leader reaches target
        mission.update(dt=1.0, leader_pos=np.array([99.0, 10.0, 0.0]))
        self.assertEqual(mission.status, MissionStatus.COMPLETED)
        self.assertEqual(mission.progress, 100.0)

    def test_engine_snapshot(self):
        engine = SimulationEngine()
        engine.reset(drone_count=10)
        engine.step(0.04)
        snapshot = engine.get_snapshot()

        self.assertEqual(len(snapshot.drones), 10)
        self.assertIsNotNone(snapshot.timestamp)
        self.assertIsNotNone(snapshot.metrics)
        self.assertEqual(snapshot.metrics.total_drones, 10)


if __name__ == "__main__":
    unittest.main()
