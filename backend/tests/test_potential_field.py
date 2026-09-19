import unittest
import numpy as np

from app.simulation.drone import Drone
from app.simulation.environment import Obstacle
from app.algorithms.potential_field import PotentialField
from app.models.schemas import ObstacleType


class TestPotentialField(unittest.TestCase):
    def setUp(self):
        self.pf = PotentialField(repulsion_weight=4.0, influence_distance=8.0)

    def test_sphere_repulsion_direction(self):
        # Sphere at (0, 10, 0) with radius 3.0
        obs = Obstacle(
            obstacle_id="SPHERE_1",
            obstacle_type=ObstacleType.SPHERE,
            position=[0.0, 10.0, 0.0],
            size=[3.0, 3.0, 3.0],
        )
        # Drone at (4.0, 10, 0) -> surface distance is 4.0 - 3.0 = 1.0m (< 8m)
        drone = Drone("D1", position=[4.0, 10.0, 0.0])

        forces = self.pf.compute_obstacle_repulsion([drone], [obs])
        # Force must push away from sphere (+X)
        self.assertGreater(forces["D1"][0], 0.0)
        self.assertAlmostEqual(forces["D1"][1], 0.0, places=4)
        self.assertAlmostEqual(forces["D1"][2], 0.0, places=4)

    def test_repulsion_inverse_distance_scaling(self):
        obs = Obstacle(
            obstacle_id="SPHERE_1",
            obstacle_type=ObstacleType.SPHERE,
            position=[0.0, 10.0, 0.0],
            size=[3.0, 3.0, 3.0],
        )
        # Drone A is 1m from surface, Drone B is 3m from surface
        drone_near = Drone("D_NEAR", position=[4.0, 10.0, 0.0])
        drone_far = Drone("D_FAR", position=[6.0, 10.0, 0.0])

        forces = self.pf.compute_obstacle_repulsion([drone_near, drone_far], [obs])
        self.assertGreater(np.linalg.norm(forces["D_NEAR"]), np.linalg.norm(forces["D_FAR"]))

    def test_zero_force_outside_influence_distance(self):
        obs = Obstacle(
            obstacle_id="SPHERE_1",
            obstacle_type=ObstacleType.SPHERE,
            position=[0.0, 10.0, 0.0],
            size=[3.0, 3.0, 3.0],
        )
        # Drone at 15.0m from surface (> 8m influence radius)
        drone = Drone("D1", position=[18.0, 10.0, 0.0])
        forces = self.pf.compute_obstacle_repulsion([drone], [obs])
        self.assertAlmostEqual(np.linalg.norm(forces["D1"]), 0.0, places=4)


if __name__ == "__main__":
    unittest.main()
