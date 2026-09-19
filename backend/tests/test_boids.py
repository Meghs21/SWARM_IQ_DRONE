import unittest
import time
import numpy as np

from app.simulation.drone import Drone
from app.algorithms.boids import BoidsEngine


class TestBoidsEngine(unittest.TestCase):
    def setUp(self):
        self.engine = BoidsEngine(
            separation_weight=2.0,
            alignment_weight=1.0,
            cohesion_weight=1.0,
            separation_radius=3.0,
            neighbor_radius=10.0,
        )

    def test_separation(self):
        # Two drones positioned very close (distance 1.0 < 3.0 separation radius)
        d1 = Drone("D1", position=[0.0, 10.0, 0.0])
        d2 = Drone("D2", position=[1.0, 10.0, 0.0])

        forces = self.engine.compute_boids_forces([d1, d2])
        # D1 should be pushed left (-x), D2 pushed right (+x)
        self.assertLess(forces["D1"][0], 0.0)
        self.assertGreater(forces["D2"][0], 0.0)

    def test_alignment(self):
        # D1 moving North, D2 moving North, D3 stationary
        d1 = Drone("D1", position=[0.0, 10.0, 0.0], velocity=[0.0, 0.0, 5.0])
        d2 = Drone("D2", position=[0.0, 10.0, 5.0], velocity=[0.0, 0.0, 5.0])
        d3 = Drone("D3", position=[0.0, 10.0, 2.5], velocity=[0.0, 0.0, 0.0])

        # Test alignment specifically by zeroing separation & cohesion
        align_engine = BoidsEngine(
            separation_weight=0.0,
            alignment_weight=2.0,
            cohesion_weight=0.0,
            separation_radius=1.0,
            neighbor_radius=10.0,
        )
        forces = align_engine.compute_boids_forces([d1, d2, d3])
        # D3 should receive positive Z force to align with D1 and D2
        self.assertGreater(forces["D3"][2], 0.0)

    def test_cohesion(self):
        # D1 and D2 at [10, 10, 10], D3 far off at [2, 10, 2] (within neighbor radius)
        d1 = Drone("D1", position=[8.0, 10.0, 8.0])
        d2 = Drone("D2", position=[8.5, 10.0, 8.5])
        d3 = Drone("D3", position=[3.0, 10.0, 3.0])

        coh_engine = BoidsEngine(
            separation_weight=0.0,
            alignment_weight=0.0,
            cohesion_weight=2.0,
            separation_radius=1.0,
            neighbor_radius=15.0,
        )
        forces = coh_engine.compute_boids_forces([d1, d2, d3])
        # D3 should be steered toward greater X and Z (towards center of flock)
        self.assertGreater(forces["D3"][0], 0.0)
        self.assertGreater(forces["D3"][2], 0.0)

    def test_performance_100_drones(self):
        # Generate 100 drones in a 3D box
        drones = [
            Drone(
                f"DRONE_{i}",
                position=np.random.uniform(-30, 30, 3),
                velocity=np.random.uniform(-2, 2, 3),
            )
            for i in range(100)
        ]
        start = time.time()
        forces = self.engine.compute_boids_forces(drones)
        elapsed_ms = (time.time() - start) * 1000.0

        self.assertEqual(len(forces), 100)
        # Should easily calculate in under 20ms (typically 1-3ms)
        self.assertLess(elapsed_ms, 25.0)


if __name__ == "__main__":
    unittest.main()
