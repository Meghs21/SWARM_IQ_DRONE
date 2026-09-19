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


if __name__ == "__main__":
    unittest.main()
