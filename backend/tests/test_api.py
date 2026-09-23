import unittest
import json
from fastapi.testclient import TestClient

from app.main import app


class TestAPIAndWebSocket(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "SwarmIQ Drone Simulator")

    def test_scenario_load_and_mission_controls(self):
        # Load Scenario 1
        res = self.client.post("/api/mission/scenario/1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["drone_count"], 20)

        # Start mission
        res = self.client.post("/api/mission/start")
        self.assertEqual(res.status_code, 200)

        # Pause mission
        res = self.client.post("/api/mission/pause")
        self.assertEqual(res.status_code, 200)

        # Resume mission
        res = self.client.post("/api/mission/resume")
        self.assertEqual(res.status_code, 200)

    def test_metrics_endpoint(self):
        res = self.client.get("/api/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_drones", data)
        self.assertIn("active_drones", data)
        self.assertIn("collision_warnings", data)

    def test_drone_fail_endpoint(self):
        # Load scenario with known drones
        self.client.post("/api/mission/scenario/1")
        res = self.client.post("/api/drone/DRONE_01/fail")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "failed")
        self.assertEqual(data["drone_id"], "DRONE_01")

    def test_websocket_stream(self):
        with self.client.websocket_connect("/ws/simulation") as websocket:
            data = websocket.receive_text()
            snapshot = json.loads(data)
            self.assertEqual(snapshot["type"], "simulation_state")
            self.assertIn("mission", snapshot)
            self.assertIn("drones", snapshot)
            self.assertIn("metrics", snapshot)

    def test_fleet_size_and_formation_changes_across_scenarios(self):
        # Test Scenario 2 (Obstacle Course with 3 obstacles)
        res = self.client.post("/api/mission/scenario/2")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["obstacle_count"], 3)
        self.assertEqual(res.json()["drone_count"], 50)

        # Change fleet size to 20 drones - obstacles MUST be preserved
        res_resize = self.client.post("/api/config/fleet-size", json={"drone_count": 20})
        self.assertEqual(res_resize.status_code, 200)
        self.assertEqual(res_resize.json()["drone_count"], 20)
        self.assertEqual(res_resize.json()["obstacle_count"], 3)

        # Change fleet size to 100 drones - obstacles MUST be preserved
        res_resize_100 = self.client.post("/api/config/fleet-size", json={"drone_count": 100})
        self.assertEqual(res_resize_100.status_code, 200)
        self.assertEqual(res_resize_100.json()["drone_count"], 100)
        self.assertEqual(res_resize_100.json()["obstacle_count"], 3)

        # Change formation across all 4 types - obstacles preserved
        for fmt in ["LINE", "GRID", "CIRCLE", "V"]:
            res_fmt = self.client.post("/api/config/formation", json={"formation": fmt})
            self.assertEqual(res_fmt.status_code, 200)
            self.assertEqual(res_fmt.json()["formation"], fmt)

        # Reset mission - scenario 2 obstacles should be preserved
        res_reset = self.client.post("/api/mission/reset")
        self.assertEqual(res_reset.status_code, 200)
        from app.core.simulation_loop import engine
        self.assertEqual(len(engine.environment.obstacles), 3)


if __name__ == "__main__":
    unittest.main()
