import unittest
import numpy as np

from app.simulation.drone import Drone
from app.models.schemas import DroneRole, DroneStatus


class TestDroneModel(unittest.TestCase):
    def setUp(self):
        self.drone = Drone(
            drone_id="DRONE_01",
            position=[0.0, 10.0, 0.0],
            max_speed=10.0,
            max_acceleration=5.0,
            battery=100.0,
        )

    def test_initialization(self):
        self.assertEqual(self.drone.id, "DRONE_01")
        np.testing.assert_array_equal(self.drone.position, [0.0, 10.0, 0.0])
        self.assertEqual(self.drone.role, DroneRole.FOLLOWER)
        self.assertEqual(self.drone.status, DroneStatus.ACTIVE)
        self.assertEqual(self.drone.battery, 100.0)

    def test_kinematics_and_acceleration_clamping(self):
        # Apply a massive force (1000 N)
        self.drone.apply_force(np.array([1000.0, 0.0, 0.0]))
        self.drone.update(dt=0.1)

        # Acceleration should be clamped to max_acceleration (5.0)
        self.assertAlmostEqual(np.linalg.norm(self.drone.acceleration), 5.0, places=4)
        # Velocity should be 5.0 * 0.1 = 0.5
        self.assertAlmostEqual(self.drone.velocity[0], 0.5, places=4)
        # Position should advance by 0.5 * 0.1 = 0.05
        self.assertAlmostEqual(self.drone.position[0], 0.05, places=4)

    def test_speed_clamping(self):
        # Accumulate speed beyond max_speed
        self.drone.velocity = np.array([20.0, 0.0, 0.0])
        self.drone.apply_force(np.array([5.0, 0.0, 0.0]))
        self.drone.update(dt=0.1)

        # Speed should be clamped to max_speed (10.0)
        speed = np.linalg.norm(self.drone.velocity)
        self.assertLessEqual(speed, 10.0001)

    def test_battery_drain_and_state_transition(self):
        # High speed should drain battery faster than hovering
        initial_battery = self.drone.battery
        self.drone.velocity = np.array([10.0, 0.0, 0.0])
        self.drone.update(dt=1.0)
        self.assertLess(self.drone.battery, initial_battery)

        # Test low battery transition to RETURNING
        self.drone.battery = 19.5
        self.drone.update(dt=0.1)
        self.assertEqual(self.drone.status, DroneStatus.RETURNING)

        # Test critical battery transition to FAILED
        self.drone.battery = 4.0
        self.drone.update(dt=0.1)
        self.assertEqual(self.drone.status, DroneStatus.FAILED)

    def test_manual_fail(self):
        self.drone.fail()
        self.assertEqual(self.drone.status, DroneStatus.FAILED)
        self.assertEqual(self.drone.battery, 0.0)

    def test_to_state_serialization(self):
        state = self.drone.to_state()
        self.assertEqual(state.id, "DRONE_01")
        self.assertEqual(state.position.y, 10.0)
        self.assertEqual(state.status, DroneStatus.ACTIVE)


if __name__ == "__main__":
    unittest.main()
