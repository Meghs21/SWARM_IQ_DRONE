# SwarmIQ – Real-Time Autonomous Multi-Drone Swarm Simulation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-r162-black.svg)](https://threejs.org/)

SwarmIQ is a real-time 3D simulation platform for autonomous multi-drone swarms coordinating in complex dynamic environments without centralized human piloting. The simulation engine runs entirely on the Python backend, driving up to 100+ virtual drones via emergent Boids flocking, 3D A* global path planning, artificial potential fields, formation maintenance, and automated dynamic leader election, streaming telemetry at 25 Hz over WebSockets to a Three.js command center HUD.

---

## Architecture Diagram

```
                              ┌────────────────────────┐
                              │     Mission Manager    │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ Dynamic Leader Election│
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ A* 3D Global Waypoints │ (Leader Only)
                              └───────────┬────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   │                                             │
                   ▼                                             ▼
       ┌──────────────────────┐                      ┌──────────────────────┐
       │ Formation Controller │                      │     Boids Engine     │
       │ (V, Line, Grid, Cir) │                      │ (Sep / Align / Coh)  │
       └───────────┬──────────┘                      └───────────┬──────────┘
                   │                                             │
                   └──────────────────────┬──────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ Local Potential Fields │
                              │ (Static & Dyn Hazards) │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │  Collision Avoidance   │
                              │  (Inter-Drone Repulse) │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │  Kinematics & Battery  │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ WebSocket Stream @25Hz │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │   React Three.js HUD   │
                              └────────────────────────┘
```

---

## Why Each Algorithm is Used

| Algorithm | Role & Scope | Why It Is Used |
| :--- | :--- | :--- |
| **Boids Flocking** | Local Swarm Coordination | Enables emergent flocking behavior without centralized communication overhead. Separation prevents crowding, alignment synchronizes velocity vectors, and cohesion maintains group integrity. |
| **Dynamic Leader Election** | Fleet Hierarchy & Resilience | Multi-criteria fitness function scores active drones based on battery, communication signal, distance to goal, and health. If the leader fails or depletes battery below 20%, an active follower seamlessly assumes command without stopping the mission. |
| **3D A* Path Planning** | Global Obstacle Navigation | Computed **only for the leader**, keeping compute overhead minimal. A* finds an optimal path through voxelized 3D space with obstacle safety inflation, followed by line-of-sight raycast string pulling to produce smooth piecewise waypoints. |
| **Artificial Potential Fields** | Local Obstacle Avoidance | Yields continuous, smooth reactive evasion around static and moving dynamic hazards ($F_{\text{rep}} \propto 1/d^2$), complementing the global A* path without needing full grid replanning each frame. |
| **Formation Controller** | Tactical Geometry | Projects relative offsets for V, Line, Grid, and Circle formations transformed by the leader's 3D heading rotation matrix ($R_{\text{leader}} \mathbf{o}_i$). |
| **Drone-to-Drone Collision Avoidance** | Inter-Agent Safety | Independent hyperbolic repulsive safety envelope guaranteeing collision-free flight and real-time safety metric tracking (warnings, near misses, actual collisions). |

---

## Technology Stack

- **Backend**:
  - Python 3.11
  - FastAPI & Uvicorn (REST API & WebSockets)
  - NumPy & SciPy (Vectorized pairwise distance matrices & kinematics)
  - Pydantic v2 (Data validation & serialization)
  - Python Unittest (Comprehensive 36-test suite)
- **Frontend**:
  - React 18 & Vite
  - Three.js (`InstancedMesh` for 100+ drones in a single draw call)
  - Tailwind CSS & Lucide Icons
  - Real-time WebSocket hook with automatic reconnection
- **Deployment**:
  - Docker & Docker Compose (Multi-stage builds)

---

## Preset Scenarios

SwarmIQ includes 5 pre-configured demonstration scenarios selectable directly from the dashboard:

1. **Scenario 1 – Open Field**: 20 drones in a V-formation demonstrating clean flocking and direct waypoint acquisition without obstacles.
2. **Scenario 2 – Obstacle Course**: 50 drones navigating past high-rise pillars and block hazards using 3D A* global path planning.
3. **Scenario 3 – Dynamic Hazards**: 50 drones evading moving, oscillating hazard spheres using continuous local potential fields.
4. **Scenario 4 – Leader Failure**: 50 drones executing a mission where the leader can be faulted mid-flight, demonstrating automatic leader election and seamless mission continuation.
5. **Scenario 5 – Large Swarm**: 100 drones maintaining a circular flocking formation through a high-density hazard field.

---

## Quickstart & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

### 1. Running Locally

#### Backend
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Backend API will be live at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend HUD will be live at `http://localhost:5173`.

---

### 2. Running with Docker Compose

To launch the complete stack with a single command:
```bash
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend REST & WebSocket: `http://localhost:8000`

---

## Testing

Run the automated backend test suite covering kinematics, Boids, A*, collision avoidance, formations, leader election, and WebSocket APIs:

```bash
cd backend
python -m unittest discover -s tests
```

Output:
```text
Ran 36 tests in 1.161s
OK
```

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health and version check |
| `POST` | `/api/mission/create` | Initialize mission with drone count, target, and formation |
| `POST` | `/api/mission/start` | Start simulation engine |
| `POST` | `/api/mission/pause` | Pause active simulation |
| `POST` | `/api/mission/resume` | Resume paused simulation |
| `POST` | `/api/mission/reset` | Reset simulation and re-spawn fleet |
| `GET` | `/api/mission/status` | Current mission progress and active leader ID |
| `GET` | `/api/metrics` | Telemetry counters (warnings, near misses, collisions, battery, FPS) |
| `POST` | `/api/mission/scenario/{id}` | Load preset scenario (1 to 5) |
| `POST` | `/api/config/formation` | Dynamically update formation (`V`, `LINE`, `GRID`, `CIRCLE`) |
| `POST` | `/api/drone/{id}/fail` | Fault injection: manually fail a specific drone or leader |

### WebSocket Endpoint

- **Route**: `/ws/simulation`
- **Rate**: ~25 Hz
- **Payload Format**:
```json
{
  "type": "simulation_state",
  "timestamp": 1726750000.12,
  "mission": {
    "status": "RUNNING",
    "progress": 64.2,
    "target": {"x": 60.0, "y": 15.0, "z": 60.0},
    "distance_to_target": 35.4,
    "elapsed_time": 18.2,
    "formation": "V"
  },
  "leader_id": "DRONE_01",
  "waypoints": [{"x": -20.0, "y": 12.0, "z": -15.0}, {"x": 60.0, "y": 15.0, "z": 60.0}],
  "drones": [
    {
      "id": "DRONE_01",
      "position": {"x": 10.2, "y": 12.1, "z": 8.4},
      "velocity": {"x": 3.2, "y": 0.1, "z": 3.5},
      "battery": 94.2,
      "role": "LEADER",
      "status": "ACTIVE"
    }
  ],
  "metrics": {
    "total_drones": 50,
    "active_drones": 50,
    "failed_drones": 0,
    "collision_warnings": 2,
    "near_misses": 0,
    "actual_collisions": 0,
    "fps": 25.0,
    "average_battery": 96.4
  }
}
```

---

## Performance Optimizations

1. **NumPy Vectorization**: Distance matrices, Boids forces, and safety radii are calculated using broadcasted NumPy operations ($O(N^2)$ computed in $< 2$ms for 100 drones).
2. **Leader-Only A\***: A* 3D path planning runs only for the leader agent. Followers maintain geometric formation relative to the leader, saving massive CPU cycles.
3. **Three.js InstancedMesh**: 100+ follower drones are rendered in a single draw call via `THREE.InstancedMesh` with dynamic transform matrices and status color buffers.
4. **Non-blocking Async Loop**: The physics simulation runs on a decoupled drift-compensated async loop at 25 Hz without blocking FastAPI request handlers.

---

## License

MIT License. Designed and engineered for autonomous swarm simulation research and development.
