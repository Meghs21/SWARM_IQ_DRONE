import unittest
import numpy as np

from app.algorithms.astar import AStarPlanner
from app.simulation.environment import Obstacle
from app.models.schemas import ObstacleType


class TestAStarPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = AStarPlanner(grid_resolution=2.0, safety_margin=2.0)

    def test_direct_path_clear_environment(self):
        start = np.array([-20.0, 10.0, -20.0])
        goal = np.array([20.0, 10.0, 20.0])
        obstacles = []

        waypoints = self.planner.plan_path(start, goal, obstacles)
        self.assertGreaterEqual(len(waypoints), 1)
        np.testing.assert_array_almost_equal(waypoints[-1], goal)

    def test_path_navigates_around_obstacle(self):
        start = np.array([-20.0, 10.0, 0.0])
        goal = np.array([20.0, 10.0, 0.0])

        # Place a tall cylinder obstacle right on the direct path at [0, 0, 0]
        obs = Obstacle(
            obstacle_id="PILLAR_1",
            obstacle_type=ObstacleType.CYLINDER,
            position=[0.0, 0.0, 0.0],
            size=[6.0, 30.0, 0.0],  # radius 6.0, height 30.0
        )
        obstacles = [obs]

        waypoints = self.planner.plan_path(start, goal, obstacles)

        # Path must have intermediate detour waypoints
        self.assertGreater(len(waypoints), 1)
        np.testing.assert_array_almost_equal(waypoints[-1], goal)

        # Verify no waypoint is inside the obstacle (radius 6.0 + margin 2.0 = 8.0)
        for wp in waypoints:
            horizontal_dist = np.hypot(wp[0] - obs.position[0], wp[2] - obs.position[2])
            # Check if waypoint penetrates interior (with slight tolerance)
            self.assertFalse(
                horizontal_dist < 6.0 and obs.position[1] <= wp[1] <= obs.position[1] + obs.size[1],
                f"Waypoint {wp} penetrated obstacle interior!",
            )


if __name__ == "__main__":
    unittest.main()
