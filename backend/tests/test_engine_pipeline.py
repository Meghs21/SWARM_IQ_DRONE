import unittest
import numpy as np

from app.core.simulation_loop import SimulationEngine
from app.models.schemas import MissionStatus, DroneRole, FormationType


class TestEnginePipeline(unittest.TestCase):
    def test_full_pipeline_run(self):
        engine = SimulationEngine()
        engine.load_scenario(2)  # Obstacle course scenario
        engine.start()

        self.assertEqual(engine.mission.status, MissionStatus.RUNNING)
        initial_leader_id = engine.swarm.leader_id
        self.assertIsNotNone(initial_leader_id)

        # Step 25 ticks (1 second of simulation)
        for _ in range(25):
            engine.step(0.04)

        # Leader should have progressed along waypoints
        leader = engine.swarm.get_leader()
        self.assertIsNotNone(leader)
        self.assertGreater(engine.mission.elapsed_time, 0.9)

        # Test mid-flight leader failure
        old_leader_id = leader.id
        leader.fail()

        # Step 5 ticks to trigger election & failover
        for _ in range(5):
            engine.step(0.04)

        new_leader = engine.swarm.get_leader()
        self.assertIsNotNone(new_leader)
        self.assertNotEqual(new_leader.id, old_leader_id)
        self.assertEqual(new_leader.role, DroneRole.LEADER)

        snapshot = engine.get_snapshot()
        self.assertEqual(snapshot.leader_id, new_leader.id)
        self.assertGreater(snapshot.metrics.failed_drones, 0)


if __name__ == "__main__":
    unittest.main()
