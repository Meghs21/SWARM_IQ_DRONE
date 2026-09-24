# SwarmIQ – Real-Time Autonomous Multi-Drone Swarm Simulation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-r162-black.svg)](https://threejs.org/)

SwarmIQ is a production-grade 3D simulation platform for autonomous multi-drone swarms coordinating in complex, obstacle-dense dynamic environments without human piloting. The simulation engine runs entirely on the Python backend, driving up to **100+ virtual drones** using **6 integrated multi-agent algorithms**: emergent Boids flocking, 3D A* global path planning, Artificial Potential Fields (APF) with tangential curl, dynamic formation maintenance, automated leader election, and hard-core inter-drone collision avoidance. Telemetry is streamed at 25 Hz via WebSockets to a Three.js command center HUD.

---

## Architecture Diagram

```
                               ┌────────────────────────┐
                               │     Mission Manager    │
                               │  (Waypoints & Goal)    │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │ Dynamic Leader Election│
                               │ (Fitness & Heartbeat)  │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │ A* 3D Global Waypoints │ (Leader Only)
                               │  (Raycast Smoothing)   │
                               └───────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
                    ▼                                             ▼
        ┌──────────────────────┐                      ┌──────────────────────┐
        │ Formation Controller │                      │     Boids Engine     │
        │ (V, Circle, Line, Gr)│                      │ (Sep / Align / Coh)  │
        └───────────┬──────────┘                      └───────────┬──────────┘
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │ Local Potential Fields │
                               │ (Repulsion + Curl APF) │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │  Collision Avoidance   │
                               │  (Hyperbolic & Hull)   │
                               └───────────┬────────────┘
                                           │
                                           ▼
                               ┌────────────────────────┐
                               │  Kinematics & Battery  │
                               │ (Newtonian Integration)│
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
                               │ (InstancedMesh Render) │
                               └────────────────────────┘
```

---

## The 6 Core Algorithms Explained

SwarmIQ combines six mathematical algorithms into a layered hierarchical control architecture:

| # | Algorithm | Primary Role | Mathematical Formulation / Implementation |
| :-: | :--- | :--- | :--- |
| **1** | **Boids Flocking (Reynolds Model)** | Local Swarm Coordination | Vectorized computation of **Separation** `F_sep = Σ((r_i - r_j) / d_ij²)`, **Alignment** `F_ali = (1/k)Σ(v_j - v_i)`, and **Cohesion** `F_coh = r_center - r_i`. Operates within a **k-nearest-neighbor graph** for efficient local coordination. |
| **2** | **Dynamic Leader Election** | Fleet Hierarchy & Resilience | Multi-criteria scoring: `Score_i = 0.35B_i + 0.30(1 - d_goal/D) + 0.20S_i + 0.15H_i`. If the leader fails or its battery drops below **20%**, the highest-ranking active follower assumes command without stopping the mission. |
| **3** | **3D A* Path Planning** | Global Obstacle Navigation | Evaluates `f(n) = g(n) + h(n)` across a **voxelized 3D grid** with safety-boundary inflation. Computed only for the active leader, followed by **line-of-sight raycast string pulling** to eliminate unnecessary zigzag waypoints. Followers track formation slots, reducing computational overhead. |
| **4** | **Artificial Potential Fields (APF)** | Local Obstacle Avoidance | Combines attractive goal force `F_att = k_att(x_goal - x)` with repulsive obstacle field `F_rep = k_rep(1/d - 1/d₀)(1/d²)n̂`. Enhanced with a **tangential vortex component** `F_curl = n̂ × û_up` to guide the swarm smoothly around high-rise obstacles and reduce local-minimum trapping. |
| **5** | **Formation Controller** | Tactical Geometry Morphing | Computes relative coordinate offsets according to the leader's 3D heading: `p_i = p_leader + R(θ)o_i`. Supports real-time morphing between **V-Formation, Circle, Line, and Grid**, with dynamic spacing based on swarm size. |
| **6** | **Drone-to-Drone Collision Avoidance & Hard Hull** | Inter-Agent Safety & Zero-Collision | Combines hyperbolic inter-agent repulsion with **dynamic formation-force attenuation**. Formation forces are suppressed when proximity danger is detected. A physical **0.95 m hard-core clearance hull** and relative-velocity damping provide an additional safety layer. The implemented system recorded **zero collisions across all tested scenarios**. |

---
## Interactive Features & Controls

* **Dynamic Swarm Fleet Sizing:** Select **20**, **50**, or **100 drones** on the fly in any scenario. The algorithm automatically recalibrates inter-drone spacing and formation envelopes.
* **Real-Time Formation Morphing:** Seamlessly toggle between **V**, **Circle**, **Line**, and **Grid** formations during active flight.
* **Fault Injection & Self-Healing Swarm:** Inject faults into any follower or click **"Fail Leader"** to trigger immediate real-time decentralized leader re-election while the fleet continues navigating.
* **Goal Arrival Hover & Braking:** When the swarm arrives within the destination threshold, mission telemetry settles at `100% Progress / 0.0m Distance`, and drones execute active exponential deceleration ($-4\vec{v}$) into stable station-keeping formation hover.
* **Camera Controls:** Free-orbit camera, Leader-Follow lock-on mode, Top-Down orthographic tactical view, and First-Person drone view.

---

## Preset Scenarios

| Scenario | Fleet Size | Environment | Key Algorithmic Demonstration |
| :--- | :---: | :--- | :--- |
| **1. Open Field** | 20 (up to 100) | Open space, zero obstacles | Pure Boids flocking, clean formation keeping, direct waypoint acquisition. |
| **2. Obstacle Course** | 50 (up to 100) | High-rise static towers & pillars | Leader A\* global 3D path planning, smooth formation obstacle avoidance. |
| **3. Dynamic Hazards** | 50 (up to 100) | Moving oscillating hazard spheres | Real-time APF reactive evasion and kinetic deflection. |
| **4. Narrow Gap / Funnel** | 50 (up to 100) | Funnel corridor & barrier gap | Swarm compression, automatic formation elongation, and squeeze clearance. |
| **5. Urban Canyon** | 100 (up to 100) | Dense skyscraper canyon grid | Maximum density swarm stress-test: A\* navigation, APF curl bypass, and zero-collision hard hull. |

---

## Technology Stack

- **Backend:**
  - Python 3.11
  - FastAPI & Uvicorn (Asynchronous REST API & WebSockets)
  - NumPy & SciPy (Vectorized pairwise distance matrices, spatial partitioning, kinematic integration)
  - Pydantic v2 (Strict schema validation & serialization)
  - Python Unittest (37 automated tests)
- **Frontend:**
  - React 18 & Vite
  - Three.js (`THREE.InstancedMesh` rendering 100+ animated drones in a single draw call at 60 FPS)
  - Tailwind CSS & Lucide Icons
  - Real-time WebSocket hook with exponential reconnect
- **Containerization:**
  - Docker & Docker Compose (Multi-stage production builds)

---

## Quickstart & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

### 1. Running Locally

#### Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Backend API will be live at `http://localhost:8000` (Interactive Swagger docs available at `http://localhost:8000/docs`).

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend command center HUD will be live at `http://localhost:5173`.

---

### 2. Running with Docker Compose

Launch the entire stack (FastAPI backend + React frontend) with a single command:
```bash
docker compose up --build
```
- **Frontend HUD:** `http://localhost:3000`
- **Backend API & WebSockets:** `http://localhost:8000`

---

## Testing

Run the automated backend test suite covering kinematics, Boids, 3D A*, APF, collision avoidance, formation geometries, leader election, and WebSocket streaming:

```bash
cd backend
python -m unittest discover -s tests
```

Output:
```text
Ran 37 tests in 2.947s
OK
```

---

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and version |
| `POST` | `/api/mission/start` | Start simulation engine |
| `POST` | `/api/mission/pause` | Pause active simulation loop |
| `POST` | `/api/mission/resume` | Resume paused simulation loop |
| `POST` | `/api/mission/reset` | Reset simulation and re-spawn fleet |
| `GET` | `/api/mission/status` | Current mission status, leader ID, progress, and distance |
| `GET` | `/api/metrics` | Live metrics (warnings, near misses, collisions, battery, FPS) |
| `POST` | `/api/mission/scenario/{id}` | Load preset scenario (1 to 5) |
| `POST` | `/api/config/formation` | Dynamically update formation (`V`, `LINE`, `GRID`, `CIRCLE`) |
| `POST` | `/api/config/fleet-size` | Dynamically update fleet size (`20`, `50`, `100`) |
| `POST` | `/api/drone/{id}/fail` | Fault injection: manually fail a specific drone or active leader |

### WebSocket Endpoint

- **Route:** `/ws/simulation`
- **Rate:** 25 Hz
- **Payload Schema:**
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
    "collision_warnings": 14,
    "near_misses": 0,
    "actual_collisions": 0,
    "fps": 25.0,
    "average_battery": 96.4
  }
}
```

---

## Safety & Collision Guarantees

Under dense flight and obstacle squeeze conditions, SwarmIQ enforces a three-stage safety hierarchy:
1. **Warning Zone ($d < 2.0\text{ m}$):** Generates telemetry alerts without disturbing steady formation flight.
2. **Near Miss Zone ($d < 1.4\text{ m}$):** Triggers hyperbolic repulsive evasion forces and dynamically attenuates formation holding.
3. **Hard-Core Clearance Hull ($d < 0.95\text{ m}$):** Mathematical boundary buffer ($> 2 \times r_{\text{drone}} = 0.80\text{ m}$) applying elastic displacement and relative velocity damping, guaranteeing **0 actual collisions** across all scenarios.

---

## License

MIT License. Designed and engineered for autonomous swarm simulation research and development.
