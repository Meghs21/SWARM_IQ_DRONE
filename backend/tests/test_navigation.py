import unittest
import numpy as np

from app.simulation.drone import Drone
from app.algorithms.navigation import GoalNavigation
from app.models.schemas import DroneRole, DroneStatus


class TestGoalNavigation(unittest.TestCase):
    def setUp(self):
        self.nav = GoalNavigation(goal_weight=2.0)

    def test_leader_seek_force(self):
        leader = Drone("L1", position=[0.0, 10.0, 0.0], role=DroneRole.LEADER)
        waypoint = np.array([50.0, 10.0, 0.0])

        force = self.nav.compute_leader_steering(leader, waypoint)
        # Should pull strongly toward positive X
        self.assertGreater(force[0], 0.0)
        self.assertAlmostEqual(force[1], 0.0, places=4)
        self.assertAlmostEqual(force[2], 0.0, places=4)

    def test_leader_arrival_slowdown(self):
        # Leader very close to waypoint (2 meters away < 8 meter slowdown radius)
        leader = Drone("L1", position=[48.0, 10.0, 0.0], role=DroneRole.LEADER, velocity=[10.0, 0.0, 0.0])
        waypoint = np.array([50.0, 10.0, 0.0])

        force = self.nav.compute_leader_steering(leader, waypoint, slowdown_radius=8.0)
        # Leader velocity is high (10 m/s) but desired speed at 2m is 12 * (2/8) = 3 m/s
        # Therefore steering force should be braking (negative X)
        self.assertLess(force[0], 0.0)

    def test_returning_drone(self):
        drone = Drone("D1", position=[30.0, 10.0, 30.0])
        drone.home_position = np.array([0.0, 10.0, 0.0])
        drone.status = DroneStatus.RETURNING

        forces = self.nav.compute_returning_drones_steering([drone])
        self.assertIn("D1", forces)
        # Force should direct drone towards (0, 10, 0), so -X and -Z
        self.assertLess(forces["D1"][0], 0.0)
        self.assertLess(forces["D1"][2], 0.0)


if __name__ == "__main__":
    unittest.main()
