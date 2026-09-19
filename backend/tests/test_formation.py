import unittest
import numpy as np

from app.simulation.drone import Drone
from app.algorithms.formation import FormationController
from app.models.schemas import FormationType, DroneRole


class TestFormationController(unittest.TestCase):
    def setUp(self):
        self.fc = FormationController(formation_spacing=4.0, formation_weight=2.0)

    def test_slot_offsets_generation(self):
        v_slots = self.fc.generate_slot_offsets(4, FormationType.V)
        self.assertEqual(len(v_slots), 4)
        # First follower should be right wing (+X, -Z)
        self.assertGreater(v_slots[0][0], 0.0)
        self.assertLess(v_slots[0][2], 0.0)
        # Second follower should be left wing (-X, -Z)
        self.assertLess(v_slots[1][0], 0.0)
        self.assertLess(v_slots[1][2], 0.0)

        # Circle formation radius
        circle_slots = self.fc.generate_slot_offsets(8, FormationType.CIRCLE)
        self.assertEqual(len(circle_slots), 8)
        radii = [np.hypot(s[0], s[2]) for s in circle_slots]
        # All slots in circle should have identical radius from center
        for r in radii:
            self.assertAlmostEqual(r, radii[0], places=3)

    def test_follower_formation_force(self):
        leader = Drone("LEADER", position=[0.0, 10.0, 0.0], role=DroneRole.LEADER, velocity=[0.0, 0.0, 5.0])
        # Place follower at (0, 10, 0), where its slot in V formation should be behind and to the side
        follower = Drone("F1", position=[0.0, 10.0, 0.0], role=DroneRole.FOLLOWER)

        forces = self.fc.compute_formation_forces([leader, follower], leader, FormationType.V)
        self.assertIn("F1", forces)
        # Should be directed towards the slot (e.g. right wing +X, behind -Z)
        self.assertNotEqual(np.linalg.norm(forces["F1"]), 0.0)


if __name__ == "__main__":
    unittest.main()
