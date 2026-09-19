import unittest
import numpy as np

from app.simulation.drone import Drone
from app.algorithms.leader_election import LeaderElection
from app.models.schemas import DroneRole, DroneStatus


class TestLeaderElection(unittest.TestCase):
    def setUp(self):
        self.election = LeaderElection(low_battery_threshold=20.0)
        self.target = np.array([100.0, 10.0, 100.0])

    def test_fitness_scoring(self):
        # D1 has 100% battery, closer to target
        d1 = Drone("D1", position=[80.0, 10.0, 80.0], battery=100.0)
        # D2 has 50% battery, further from target
        d2 = Drone("D2", position=[0.0, 10.0, 0.0], battery=50.0)
        # D3 is failed
        d3 = Drone("D3", position=[80.0, 10.0, 80.0], battery=0.0)
        d3.status = DroneStatus.FAILED

        score1 = self.election.calculate_score(d1, self.target)
        score2 = self.election.calculate_score(d2, self.target)
        score3 = self.election.calculate_score(d3, self.target)

        self.assertGreater(score1, score2)
        self.assertEqual(score3, -1.0)

    def test_automatic_replacement_on_failure(self):
        leader = Drone("LEADER", position=[10.0, 10.0, 10.0], role=DroneRole.LEADER, battery=80.0)
        follower1 = Drone("F1", position=[12.0, 10.0, 12.0], role=DroneRole.FOLLOWER, battery=95.0)

        # Currently healthy, should not replace
        self.assertFalse(self.election.should_replace_leader(leader))

        # Leader battery drops to 15% (< 20%)
        leader.battery = 15.0
        self.assertTrue(self.election.should_replace_leader(leader))

        # Elect new leader
        new_leader_id, changed = self.election.elect_leader([leader, follower1], self.target, leader.id)
        self.assertTrue(changed)
        self.assertEqual(new_leader_id, "F1")

    def test_replacement_on_manual_fail(self):
        leader = Drone("LEADER", position=[10.0, 10.0, 10.0], role=DroneRole.LEADER)
        follower = Drone("F1", position=[10.0, 10.0, 10.0], role=DroneRole.FOLLOWER, battery=90.0)

        leader.fail()
        self.assertTrue(self.election.should_replace_leader(leader))

        new_leader_id, changed = self.election.elect_leader([leader, follower], self.target, leader.id)
        self.assertTrue(changed)
        self.assertEqual(new_leader_id, "F1")


if __name__ == "__main__":
    unittest.main()
