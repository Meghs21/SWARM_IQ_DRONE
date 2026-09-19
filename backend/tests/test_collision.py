import unittest
import numpy as np

from app.simulation.drone import Drone
from app.algorithms.collision import CollisionAvoidance


class TestCollisionAvoidance(unittest.TestCase):
    def setUp(self):
        self.avoid = CollisionAvoidance(
            drone_radius=0.4,
            safety_radius=2.0,
            warning_radius=3.5,
            avoidance_weight=3.0,
        )

    def test_evasion_force_within_safety_radius(self):
        # Two drones 1.0m apart (< 2.0m safety radius)
        d1 = Drone("D1", position=[0.0, 10.0, 0.0])
        d2 = Drone("D2", position=[1.0, 10.0, 0.0])

        forces, warnings, near_misses, collisions = self.avoid.compute_avoidance_and_metrics([d1, d2])

        # D1 should be pushed left (-X), D2 pushed right (+X)
        self.assertLess(forces["D1"][0], 0.0)
        self.assertGreater(forces["D2"][0], 0.0)
        # Should be classified as a near miss (dist 1.0 < 2.0 and > 0.8)
        self.assertEqual(near_misses, 1)
        self.assertEqual(collisions, 0)

    def test_safe_distance_zero_force(self):
        # Two drones 5.0m apart (> 3.5m warning radius)
        d1 = Drone("D1", position=[0.0, 10.0, 0.0])
        d2 = Drone("D2", position=[5.0, 10.0, 0.0])

        forces, warnings, near_misses, collisions = self.avoid.compute_avoidance_and_metrics([d1, d2])
        self.assertAlmostEqual(np.linalg.norm(forces["D1"]), 0.0, places=4)
        self.assertEqual(warnings, 0)
        self.assertEqual(near_misses, 0)
        self.assertEqual(collisions, 0)

    def test_warning_and_actual_collision_metrics(self):
        # D1 and D2 in warning zone (2.5m apart)
        d1 = Drone("D1", position=[0.0, 10.0, 0.0])
        d2 = Drone("D2", position=[2.5, 10.0, 0.0])
        _, warnings, _, _ = self.avoid.compute_avoidance_and_metrics([d1, d2])
        self.assertEqual(warnings, 1)

        # D3 and D4 in collision zone (0.5m apart < 2 * 0.4 = 0.8m)
        d3 = Drone("D3", position=[0.0, 20.0, 0.0])
        d4 = Drone("D4", position=[0.5, 20.0, 0.0])
        _, _, _, collisions = self.avoid.compute_avoidance_and_metrics([d3, d4])
        self.assertEqual(collisions, 1)


if __name__ == "__main__":
    unittest.main()
